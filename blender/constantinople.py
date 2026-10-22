import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from kit import buildings, constantinople_city as city, constantinople_life as life
from kit import constantinople_monuments as mon
from kit import constantinople_sophia as sophia
from kit import constantinople_terrain as ter
from kit.arles_details import quadriga
from kit.arles_life import amphora_pile, barrel_group, crane, sack_pile
from kit.colisee_terrain import graded_profile, road_blend
from kit.constantinople_materials import build_library, remap
from kit.constantinople_ships import SHIPS
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, save_pixels
from kit.nimes_figures import mule_wagon, pack_beast, person
from kit.nimes_scenery import cloth_stall, pottery_stall
from kit.pantheon_city import cypress_tree, stone_pine
from kit.pantheon_materials import weather
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, haze_volume, render_still, sun_lamp
from kit.terrain import HeightField, grid_mesh, polygon_mask, polyline_distance, remove_faces_inside, value_noise

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "constantinople")
BLEND = os.path.join(CACHE, "work", "constantinople.blend")
SUN_AZIMUTH = 138.0
SUN_ELEVATION = 13.0
SUN_COLOUR = (1.0, 0.76, 0.52)
NEAR_HALF = 1700.0
NEAR_SPACING = 12.0
FAR_HALF = 14000.0
FAR_SPACING = 140.0
HS_BEARING = 122.0
HIPPO_BEARING = 219.5
IRENE_BEARING = 115.0
FORUM_BEARING = 97.0
EYE_CLEARANCE = 2.4
HORN_BEARING = 262.0
DETAIL_CENTRE = Vector((40.0, 60.0))
DETAIL_RADIUS = 330.0
SINK = 0.4
BLOCK_U = 58.0
BLOCK_V = 44.0
STREET = 5.0
MESE_WIDTH = 26.0
MESE_ROAD = 12.0
BAY = 4.2
BAY_KINDS = [("ochre", 2), ("ochre", 3), ("rose", 1), ("rose", 2), ("cream", 2), ("cream", 3), ("blue", 1), ("blue", 2)]
LANDFILL_GEO = [
    [(41.0148, 28.9620), (41.0185, 28.9700), (41.0186, 28.9790), (41.0160, 28.9845), (41.0175, 28.9880),
     (41.0140, 28.9870), (41.0128, 28.9790), (41.0120, 28.9700), (41.0115, 28.9620)],
    [(41.0170, 28.9850), (41.0195, 28.9880), (41.0150, 28.9920), (41.0100, 28.9900), (41.0090, 28.9850),
     (41.0130, 28.9845)],
    [(41.0060, 28.9880), (41.0080, 28.9910), (41.0010, 28.9870), (40.9990, 28.9780), (40.9985, 28.9600),
     (41.0035, 28.9600), (41.0040, 28.9760)],
]


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 24}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


class Frame:
    def __init__(self, x, y, bearing, axis="x"):
        self.origin = Vector((x, y))
        self.theta = math.radians(90.0 - bearing) if axis == "x" else math.radians(-bearing)
        self.u = Vector((math.cos(self.theta), math.sin(self.theta)))
        self.v = Vector((-math.sin(self.theta), math.cos(self.theta)))

    def world(self, u, v):
        return self.origin + self.u * u + self.v * v

    def local(self, point):
        d = Vector((point[0], point[1])) - self.origin
        return d.dot(self.u), d.dot(self.v)

    def matrix(self, u, v, z, turn=0.0, scale=1.0):
        p = self.world(u, v)
        return placement(p.x, p.y, z, self.theta + turn, scale)

    def polygon(self, points):
        return [tuple(self.world(u, v)) for u, v in points]


def geo(latitude, longitude):
    return Vector(ter.local(latitude, longitude))


HS = Frame(*geo(41.008548, 28.979938), HS_BEARING)
BAPTISTERY = (-40.0, -45.0)
BAPTISTERY_R = 6.5
HIPPO = Frame(*(geo(41.0059, 28.9754) + Vector((math.sin(math.radians(HIPPO_BEARING)),
                                                 math.cos(math.radians(HIPPO_BEARING)))) * 30.0), HIPPO_BEARING, "y")
AUG = Frame(*HS.world(-45.0, -75.0), HS_BEARING)
IRENE = Frame(*geo(41.00972, 28.98111), IRENE_BEARING)
MILION = geo(41.00805, 28.9780)
FORUM = Frame(*geo(41.0086, 28.9711), FORUM_BEARING)
MESE = [MILION, Vector((-120.0, 74.0)), Vector((-300.0, 98.0)), FORUM.world(70.0, 0.0)]
ZEUX = Frame(*HIPPO.world(-118.0, -185.0), HIPPO_BEARING, "y")
STOA = Frame(*geo(41.0086, 28.9776), 98.0)


class Scene:
    def __init__(self, tiles, field):
        self.tiles = tiles
        self.field = field
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Constantinople")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.builds = {}
        self.statics = {}
        self.blocked = []
        self.ship_spots = []
        self.surface = None
        self.obstacles = []
        self.solid_rects = []

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.field.sample(x, y))

    def lowest(self, x, y, radius):
        return min(self.ground(x + dx * radius, y + dy * radius) for dx, dy in
                   ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7)))

    def unique(self, group, builder, matrix=None, occlusion=True):
        if not occlusion:
            builder.heights = [10.0] * len(builder.positions)
        self.pending.setdefault(group, []).append((remap(builder), matrix if matrix is not None else Matrix.Identity(4)))
        self.root(group)

    def flush(self, shadowless=()):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(builder, matrix, keep_local=True)
            name = f"{group}_static"
            if name in self.statics:
                name = f"{group}_static_{len(self.statics)}"
            self.statics[name] = unique_object(name, merged, self.collection, self.root(group), self.tiles,
                                               cast_shadow=group not in shadowless)
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True, occlusion=False):
        if matrices:
            self.library.place(key, lambda: remap(build()), self.collection, self.root(group), matrices, cast_shadow,
                               occlusion)

    def add(self, key, matrix, build):
        self.placements.setdefault(key, []).append(matrix)
        self.builds.setdefault(key, build)

    def block(self, polygon):
        self.blocked.append([tuple(p) for p in polygon])

    def obstacle(self, point, radius):
        self.obstacles.append((Vector((point[0], point[1])), radius))

    def clear_of(self, p, margin=0.0):
        if any((p - centre).length < radius + margin for centre, radius in self.obstacles):
            return False
        for frame, u0, u1, v0, v1 in self.solid_rects:
            u, v = frame.local(p)
            if u0 - 3.0 - margin < u < u1 + 3.0 + margin and v0 - 3.0 - margin < v < v1 + 3.0 + margin:
                return False
        return True


def plinth(points, z0, z1, material, colour=None):
    builder = MeshBuilder()
    pts = [Vector((p[0], p[1])) for p in points]
    centre = sum(pts, Vector((0.0, 0.0))) / len(pts)
    sophia.facing_quad(builder, [(p.x, p.y, z1) for p in pts], (0, 0, 1), material, colour=colour)
    for a, b in zip(pts, pts[1:] + pts[:1]):
        mid = (a + b) / 2 - centre
        sophia.facing_quad(builder, [(a.x, a.y, z0), (b.x, b.y, z0), (b.x, b.y, z1), (a.x, a.y, z1)], (mid.x, mid.y, 0.0),
                           material, colour=colour)
    return builder


def rect(frame, u0, u1, v0, v1):
    return frame.polygon([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])


def ellipse(frame, rx, ry, count=40):
    return frame.polygon([(rx * math.cos(math.tau * k / count), ry * math.sin(math.tau * k / count)) for k in range(count)])


def dense(points, step):
    out = [Vector(points[0])]
    for a, b in zip(points[:-1], points[1:]):
        a, b = Vector(a), Vector(b)
        count = max(int(math.ceil((b - a).length / step)), 1)
        for k in range(1, count + 1):
            out.append(a.lerp(b, k / count))
    return out


def polygon_level(field, polygon, quantile=0.5):
    xs = np.array([p[0] for p in polygon])
    ys = np.array([p[1] for p in polygon])
    gx, gy = np.meshgrid(np.linspace(xs.min(), xs.max(), 24), np.linspace(ys.min(), ys.max(), 24))
    inside = polygon_mask(polygon, gx, gy)
    values = field.sample(gx[inside], gy[inside])
    return float(np.quantile(values, quantile))


def flatten_polygon(gx, gy, heights, polygon, level, margin):
    inside = polygon_mask(polygon, gx, gy)
    distance = polyline_distance(list(polygon) + [polygon[0]], gx, gy)
    weight = np.where(inside, 1.0, np.clip(1.0 - distance / max(margin, 1e-3), 0.0, 1.0))
    weight = weight * weight * (3 - 2 * weight)
    return heights * (1 - weight) + level * weight


def site_levels(field):
    levels = {}
    levels["hs"] = polygon_level(field, rect(HS, -100.0, 40.0, -38.0, 38.0), 0.45)
    levels["augusteon"] = levels["hs"]
    levels["irene"] = polygon_level(field, rect(IRENE, -60.0, 30.0, -18.0, 18.0), 0.5)
    obelisk = geo(41.0059, 28.9754)
    levels["track"] = float(field.sample(obelisk.x, obelisk.y)) - 2.5
    levels["forum"] = polygon_level(field, ellipse(FORUM, 62.0, 52.0), 0.5)
    levels["zeuxippus"] = polygon_level(field, rect(ZEUX, -40.0, 40.0, -38.0, 30.0), 0.5)
    levels["stoa"] = polygon_level(field, rect(STOA, -38.0, 38.0, -25.0, 25.0), 0.5)
    return levels


PALACE_TERRACES = [
    ("daphne", (-150.0, -60.0, -160.0, -60.0)),
    ("consistorium", (-150.0, -50.0, -60.0, 20.0)),
    ("magnaura", (-50.0, 40.0, -150.0, -40.0)),
    ("nineteen", (-150.0, -40.0, -30.0, 60.0)),
    ("garden", (-40.0, 60.0, -30.0, 70.0)),
    ("lower", (-150.0, -30.0, 70.0, 170.0)),
    ("boukoleon", (-30.0, 90.0, 80.0, 190.0)),
]


def palace_frame():
    return Frame(*HIPPO.world(-150.0, 20.0), HIPPO_BEARING, "y")


def terrain_edits(field, levels):
    heights = field.heights.copy()
    gx, gy = field.grid_x, field.grid_y
    heights = flatten_polygon(gx, gy, heights, rect(HS, -112.0, 46.0, -50.0, 50.0), levels["hs"] - SINK, 25.0)
    heights = flatten_polygon(gx, gy, heights, rect(IRENE, -70.0, 34.0, -22.0, 22.0), levels["irene"], 25.0)
    heights = flatten_polygon(gx, gy, heights, rect(AUG, -50.0, 80.0, -60.0, 32.0), levels["augusteon"] - SINK, 25.0)
    track = levels["track"]
    outer = rect(HIPPO, -mon.CAVEA_OUTER - 2.0, mon.CAVEA_OUTER + 2.0, -mon.HIPPO_HALF_LENGTH - 2.0, mon.SPHENDONE_Y)
    heights = flatten_polygon(gx, gy, heights, outer, track - 0.25, 0.1)
    curve = [tuple(HIPPO.world((mon.CAVEA_OUTER + 2.0) * math.cos(math.pi * k / 24),
                               mon.SPHENDONE_Y + (mon.CAVEA_OUTER + 2.0) * math.sin(math.pi * k / 24)))
             for k in range(25)]
    heights = flatten_polygon(gx, gy, heights, curve, track - 0.25, 0.1)
    heights = flatten_polygon(gx, gy, heights, ellipse(FORUM, 72.0, 62.0), levels["forum"] - SINK, 30.0)
    heights = flatten_polygon(gx, gy, heights, rect(ZEUX, -42.0, 42.0, -40.0, 32.0), levels["zeuxippus"], 20.0)
    stoa = rect(STOA, -38.0, 38.0, -25.0, 25.0)
    levels["stoa"] = polygon_level(HeightField(heights, field.half_extent), stoa, 0.5)
    heights = flatten_polygon(gx, gy, heights, stoa, levels["stoa"] - SINK, 12.0)
    frame = palace_frame()
    for name, (u0, u1, v0, v1) in PALACE_TERRACES:
        polygon = rect(frame, u0, u1, v0, v1)
        level = polygon_level(HeightField(heights, field.half_extent), polygon, 0.5)
        levels[f"palace_{name}"] = level
        heights = flatten_polygon(gx, gy, heights, polygon, level - SINK, 12.0)
    points, profile = mese_profile(heights, field)
    levels["mese_points"] = points
    levels["mese_levels"] = profile
    heights = road_blend(gx, gy, heights, [tuple(p) for p in points], [z - 0.3 for z in profile], MESE_WIDTH / 2 + 2.0, 18.0)
    field.heights = heights
    return field


def mese_profile(heights, field):
    proxy = HeightField(heights, field.half_extent)
    points, levels = graded_profile([tuple(p) for p in MESE], lambda x, y: float(proxy.sample(x, y)), 0.06, 4.0, 80.0)
    return [Vector(p) for p in points], levels


def land_colour(xs, ys, heights, slope, sea_distance, urban, paved, garden, seed=3):
    shape = xs.shape
    noise = value_noise(shape, 14, seed)
    fine = value_noise(shape, 90, seed + 1, 3)
    grain = value_noise(shape, 260, seed + 2, 2)
    grass = np.dstack([0.30 + 0.08 * noise, 0.50 + 0.1 * noise, 0.17 + 0.05 * fine])
    meadow = np.dstack([0.46 + 0.06 * fine, 0.56 + 0.06 * fine, 0.24 + 0.04 * noise])
    earth = np.dstack([0.62 + 0.06 * grain, 0.50 + 0.05 * grain, 0.36 + 0.04 * grain])
    beaten = np.dstack([0.70 + 0.05 * grain, 0.62 + 0.05 * grain, 0.50 + 0.04 * grain])
    stone = np.dstack([0.84 + 0.04 * grain, 0.80 + 0.04 * grain, 0.72 + 0.03 * grain])
    rock = np.dstack([0.56 + 0.05 * fine, 0.52 + 0.05 * fine, 0.46 + 0.04 * fine])
    colour = grass * (1 - smoothstep((fine - 0.55) / 0.2))[..., None] + meadow * smoothstep((fine - 0.55) / 0.2)[..., None]
    colour = mix(colour, rock, smoothstep((slope - 0.45) / 0.3))
    colour = mix(colour, mix(earth, beaten, smoothstep((grain - 0.5) / 0.2)), urban * (0.75 + 0.25 * smoothstep((noise - 0.3) / 0.4)))
    colour = mix(colour, grass * 1.05, garden)
    colour = mix(colour, stone, paved)
    sand = np.dstack([0.78 + 0.05 * grain, 0.66 + 0.05 * grain, 0.46 + 0.04 * grain])
    beach = np.maximum(smoothstep(1.0 - (sea_distance - 2.0) / 16.0), smoothstep(1.0 - heights / 1.2))
    colour = mix(colour, sand, beach)
    shallow = np.dstack([0.42 + 0.05 * fine, 0.56 + 0.05 * fine, 0.50 + 0.04 * fine])
    deep = np.array([0.04, 0.17, 0.26])
    under = mix(sand, shallow, smoothstep(-heights / 1.5))
    under = mix(under, np.broadcast_to(deep, shallow.shape), smoothstep((-heights - 1.5) / 12.0))
    colour = np.where((heights < 0.0)[..., None], under, colour)
    return np.clip(colour, 0, 1)


def country_colour(xs, ys, heights, slope, seed=21):
    angle = math.radians(23.0)
    u = xs * math.cos(angle) - ys * math.sin(angle)
    v = xs * math.sin(angle) + ys * math.cos(angle)
    parcel = ((np.floor(u / 140.0).astype(np.int64) * 73856093) ^ (np.floor(v / 95.0).astype(np.int64) * 19349663)) % 997 / 997.0
    crops = np.array([[0.34, 0.47, 0.20], [0.55, 0.46, 0.31], [0.44, 0.47, 0.31], [0.40, 0.52, 0.24], [0.49, 0.43, 0.29],
                      [0.31, 0.43, 0.18], [0.60, 0.52, 0.36]])
    fine = value_noise(xs.shape, 180, seed, 3)
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.9 + 0.18 * fine)[..., None]
    edge = (np.abs((u / 140.0) % 1.0 - 0.5) > 0.485) | (np.abs((v / 95.0) % 1.0 - 0.5) > 0.48)
    colour = np.where(edge[..., None], np.array([0.26, 0.36, 0.16]), colour)
    patches = value_noise(xs.shape, 30, seed + 1, 4)
    wood = np.dstack([0.16 + 0.05 * fine, 0.26 + 0.05 * fine, 0.12 + 0.03 * fine])
    woodland = np.clip(smoothstep((patches - 0.56) / 0.08) + smoothstep((slope - 0.12) / 0.1) * 0.8
                       + smoothstep((heights - 120.0) / 80.0) * 0.5, 0, 1)
    colour = mix(colour, wood, woodland)
    shade = 0.82 + 0.18 * smoothstep(1.0 - slope * 3.0)
    return np.clip(colour * shade[..., None], 0, 1)


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def mix(a, b, w):
    w = np.clip(w, 0.0, 1.0)[..., None]
    return a * (1 - w) + b * w


def site_masks(gx, gy, levels):
    paved = np.zeros(gx.shape)
    for polygon in (rect(AUG, -40.0, 40.0, -28.0, 28.0), rect(HS, -100.0, -45.0, -31.0, 31.0), ellipse(FORUM, 62.0, 52.0),
                    rect(HS, -112.0, 46.0, -50.0, 50.0)):
        paved = np.maximum(paved, polygon_mask(polygon, gx, gy) * 0.9)
    distance = polyline_distance([tuple(p) for p in levels["mese_points"]], gx, gy)
    paved = np.maximum(paved, smoothstep((MESE_WIDTH / 2 + 1.0 - distance) / 2.0))
    garden = np.zeros(gx.shape)
    frame = palace_frame()
    for name in ("garden", "lower"):
        u0, u1, v0, v1 = dict(PALACE_TERRACES)[name]
        garden = np.maximum(garden, polygon_mask(rect(frame, u0, u1, v0, v1), gx, gy) * 0.8)
    acropolis = geo(41.0125, 28.9840)
    garden = np.maximum(garden, smoothstep(1.0 - np.hypot(gx - acropolis.x, gy - acropolis.y) / 260.0) * 0.6)
    return paved, garden


def build_terrain(scene, near, far, to_sea, levels):
    root = scene.root("terrain")
    mesh = grid_mesh("terrain", near.heights, NEAR_HALF, skirt_depth=20.0)
    axis = np.linspace(-NEAR_HALF, NEAR_HALF, 2048)
    tx, ty = np.meshgrid(axis, axis)
    th = near.sample(tx, ty)
    gy_, gx_ = np.gradient(th, axis[1] - axis[0])
    slope = np.hypot(gx_, gy_)
    spacing = 2 * NEAR_HALF / (to_sea.shape[0] - 1)
    column = np.clip(np.round((tx + NEAR_HALF) / spacing).astype(int), 0, to_sea.shape[0] - 1)
    row = np.clip(np.round((ty + NEAR_HALF) / spacing).astype(int), 0, to_sea.shape[0] - 1)
    sea_distance = to_sea[row, column]
    urban = smoothstep((sea_distance - 25.0) / 40.0) * 0.9
    paved, garden = site_masks(tx, ty, levels)
    colour = land_colour(tx, ty, th, slope, sea_distance, urban, paved, garden)
    shade = 0.86 + 0.14 * smoothstep(1.0 - slope * 1.5)
    colour *= shade[..., None]
    image = save_pixels("terrain_colour", np.clip(colour, 0, 1), os.path.join(CACHE, "textures", "terrain_colour.jpg"),
                        quality=88)
    mesh.materials.append(baked_material("terrain", image))
    terrain = new_object("terrain_near", mesh, scene.collection, root)
    terrain["cast_shadow"] = False
    scene.terrain_object = terrain
    far_mesh = grid_mesh("terrain_far", far.heights, FAR_HALF, ring=(90000.0, 0.0))
    remove_faces_inside(far_mesh, NEAR_HALF - FAR_SPACING * 0.6)
    axis = np.linspace(-FAR_HALF, FAR_HALF, 2048)
    tx, ty = np.meshgrid(axis, axis)
    th = far.sample(tx, ty)
    gy_, gx_ = np.gradient(th, axis[1] - axis[0])
    slope = np.hypot(gx_, gy_)
    far_sea = th < 0.2
    urban = np.zeros(tx.shape)
    for (cx, cy, r) in far_towns():
        urban = np.maximum(urban, smoothstep(1.0 - np.hypot(tx - cx, ty - cy) / r) * 0.9)
    colour = country_colour(tx, ty, th, slope)
    colour = mix(colour, land_colour(tx, ty, th, slope, np.full(tx.shape, 100.0), np.ones(tx.shape), np.zeros(tx.shape),
                                     np.zeros(tx.shape), 9), urban)
    roofs = np.dstack([0.72 + 0.1 * value_noise(tx.shape, 400, 5, 2), 0.42 + 0.06 * value_noise(tx.shape, 400, 6, 2),
                       0.3 + 0.04 * value_noise(tx.shape, 400, 7, 2)])
    speckle = (value_noise(tx.shape, 700, 8, 1) > 0.55) * urban
    colour = mix(colour, roofs, speckle * 0.8)
    deep = np.array([0.05, 0.18, 0.24])
    colour = np.where(far_sea[..., None], mix(colour, np.broadcast_to(deep, colour.shape), smoothstep(-th / 6.0)), colour)
    image = save_pixels("terrain_far_colour", np.clip(colour, 0, 1), os.path.join(CACHE, "textures", "terrain_far.jpg"),
                        quality=85)
    far_mesh.materials.append(baked_material("terrain_far", image))
    created = new_object("terrain_far", far_mesh, scene.collection, root)
    created["cast_shadow"] = False
    water = MeshBuilder()
    reach = 70000.0
    water.polygon([(-reach, -reach, 0.0), (reach, -reach, 0.0), (reach, reach, 0.0), (-reach, reach, 0.0)], "water")
    unique_object("water", water, scene.collection, root, scene.tiles, cast_shadow=False, ground_occlusion=False)


def far_towns():
    return [(*geo(41.0270, 28.9740), 1100.0), (*geo(40.9900, 29.0270), 1300.0), (*geo(41.0250, 29.0150), 900.0),
            (*geo(41.0300, 28.9500), 600.0)]


def build_sophia(scene, levels):
    z = levels["hs"]
    builder, fountain = sophia.hagia_sophia()
    scene.unique("sophia", builder, HS.matrix(0.0, 0.0, z))
    scene.unique("beams", sophia.light_beams(SUN_AZIMUTH - HS_BEARING, SUN_ELEVATION), HS.matrix(0.0, 0.0, z), False)
    scene.unique("sophia", sophia.baptistery(BAPTISTERY_R), HS.matrix(*BAPTISTERY, z))
    scene.obstacle(HS.world(*BAPTISTERY), BAPTISTERY_R + 1.5)
    scene.unique("sophia", sophia.hagia_irene(), IRENE.matrix(0.0, 0.0, levels["irene"]))
    pave = MeshBuilder()
    sophia.slab_strips(pave, lambda u, v: not (sophia.WEST - 12.0 < u < sophia.EAST + 9.0 and abs(v) < sophia.HALF_W + 1.0)
                       and not (sophia.ATRIUM_WEST - 3.0 < u < sophia.EXONARTHEX and abs(v) < sophia.ATRIUM_HALF + 0.5)
                       and not (v < -40.0 and -92.0 < u < -4.0),
                       -110.0, 44.0, -48.0, 48.0, -0.6, 0.02, 2.0, "travertine", "travertine", sides=True)
    scene.unique("sol", pave, HS.matrix(0.0, 0.0, z))
    scene.block(rect(HS, -114.0, 48.0, -52.0, 52.0))
    scene.block(rect(IRENE, -72.0, 36.0, -24.0, 24.0))
    interior = HS.world(0.0, 0.0)
    scene.interior = Vector((interior.x, interior.y, z))
    scene.fountain = HS.world(*fountain)
    return z


def build_hippodrome(scene, levels):
    track = levels["track"]
    lowest = min(scene.ground(*HIPPO.world(x, y)) for x in (-70.0, 0.0, 70.0) for y in (-220.0, 0.0, 150.0, 250.0))
    depth = max(track - lowest + 4.0, 6.0)
    scene.unique("hippodrome", mon.hippodrome(depth), HIPPO.matrix(0.0, 0.0, track))
    spina_back, spina_front = -130.0, 112.0
    obelisk_y = -30.0
    spina = MeshBuilder()
    mon.spina(spina, spina_back, spina_front, (-110.0, -100.0, -90.0, -62.0, -48.0, obelisk_y, obelisk_y + 36.2, 20.0, 30.0,
                                              obelisk_y + 72.4, 60.0, 90.0))
    scene.unique("hippodrome", spina, HIPPO.matrix(0.0, 0.0, track))
    serpent_y = obelisk_y + 36.2
    walled_y = obelisk_y + 72.4
    scene.unique("hippodrome", mon.obelisk_theodosius(), HIPPO.matrix(0.0, obelisk_y, track + 1.2))
    scene.unique("hippodrome", mon.serpent_column(), HIPPO.matrix(0.0, serpent_y, track + 1.2))
    scene.unique("hippodrome", mon.walled_obelisk(), HIPPO.matrix(0.0, walled_y, track + 1.2))
    for y in (spina_back - 4.0, spina_front + 4.0):
        scene.unique("hippodrome", mon.meta(), HIPPO.matrix(0.0, y, track, math.pi / 2))
    for k, y in enumerate((-110.0, -90.0, -62.0, 20.0, 60.0, 90.0)):
        build = mon.charioteer_statue(k + 1) if k % 2 == 0 else mon.bronze_horse_statue(k)
        scene.unique("hippodrome", build, HIPPO.matrix(0.0, y, track + 1.2, math.pi if k % 3 else 0.0))
    for k, y in enumerate((-100.0, -48.0, 30.0, 100.0)):
        scene.unique("hippodrome", mon.statue_group(30 + k), HIPPO.matrix(2.4 if k % 2 else -2.4, y, track + 1.2,
                                                                          math.pi / 2 if k % 2 else -math.pi / 2))
    kathisma_y = -64.0
    scene.unique("hippodrome", mon.kathisma(), HIPPO.matrix(-(mon.TRACK_HALF + 6.0), kathisma_y, track))
    sand = MeshBuilder()
    y0, y1 = -mon.HIPPO_HALF_LENGTH + 18.0, mon.SPHENDONE_Y
    bands = [-mon.TRACK_HALF, -14.5, -12.0, -8.5, 8.5, 12.0, 14.5, mon.TRACK_HALF]
    tones = [(1.0, 1.0, 1.0), (0.88, 0.86, 0.84), (0.76, 0.72, 0.68), (1.0, 1.0, 1.0), (0.76, 0.72, 0.68), (0.88, 0.86, 0.84),
             (1.0, 1.0, 1.0)]
    for (a, b), tone in zip(zip(bands[:-1], bands[1:]), tones):
        sand.polygon([(a, y0, 0.0), (b, y0, 0.0), (b, y1, 0.0), (a, y1, 0.0)], "sand", color=tone)
    curve = [(-mon.TRACK_HALF * math.cos(math.pi * k / 24), mon.SPHENDONE_Y + mon.TRACK_HALF * math.sin(math.pi * k / 24), 0.0)
             for k in range(25)]
    sand.polygon(curve, "sand")
    scene.unique("sol", sand, HIPPO.matrix(0.0, 0.0, track + 0.02))
    scene.block(rect(HIPPO, -mon.CAVEA_OUTER - 3.0, mon.CAVEA_OUTER + 3.0, -mon.HIPPO_HALF_LENGTH - 2.0, mon.SPHENDONE_Y))
    scene.block([tuple(HIPPO.world((mon.CAVEA_OUTER + 3.0) * math.cos(math.pi * k / 24),
                                   mon.SPHENDONE_Y + (mon.CAVEA_OUTER + 3.0) * math.sin(math.pi * k / 24))) for k in range(25)])
    scene.block(rect(HIPPO, -mon.CAVEA_OUTER - 80.0, -mon.CAVEA_OUTER, kathisma_y - 6.0, kathisma_y + 6.0))
    return track, (obelisk_y, serpent_y, walled_y, kathisma_y)


def build_augusteon(scene, levels):
    z = levels["augusteon"]
    half_u, half_v = 40.0, 28.0
    gap = AUG.local(HS.world(*BAPTISTERY))[0]
    for start, stop in ((-half_u, gap - BAPTISTERY_R - 4.0), (gap + BAPTISTERY_R + 2.0, half_u)):
        scene.unique("augusteon", mon.augusteon_portico(stop - start), AUG.matrix(start, half_v, z, 0.0))
    for u in (half_u, -12.0):
        scene.unique("augusteon", mon.augusteon_portico(28.0), AUG.matrix(u, -half_v, z, math.pi))
    scene.unique("augusteon", mon.augusteon_portico(2 * half_v - 14.0), AUG.matrix(-half_u, -half_v + 7.0, z, math.pi / 2))
    scene.unique("augusteon", mon.senate(), AUG.matrix(half_u + 9.5, 0.0, z))
    column, statue_z = mon.justinian_column()
    column_u = -half_u + 12.0
    scene.unique("augusteon", column, AUG.matrix(column_u, 0.0, z))
    scene.obstacle(AUG.world(column_u, 0.0), 7.8)
    scene.statue_top = Vector((*AUG.world(column_u, 0.0), z + statue_z + 4.0))
    scene.unique("augusteon", mon.chalke(), AUG.matrix(0.0, -half_v - 11.0, z))
    pave = plinth([(-half_u - 7.0, -half_v - 6.0), (half_u + 1.0, -half_v - 6.0), (half_u + 1.0, half_v + 7.0),
                   (-half_u - 7.0, half_v + 7.0)],
                  -0.6, 0.0, "travertine")
    scene.unique("sol", pave, AUG.matrix(0.0, 0.0, z + 0.03))
    direction = (MESE[1] - MESE[0]).normalized()
    turn = math.atan2(direction.y, direction.x)
    milion_z = scene.ground(MILION.x, MILION.y)
    scene.unique("augusteon", mon.milion(), placement(MILION.x, MILION.y, milion_z, turn))
    scene.obstacle(MILION, 11.0)
    scene.milion = Vector((MILION.x, MILION.y, milion_z))
    stoa = STOA.world(0.0, 0.0)
    stoa_z = levels["stoa"]
    scene.unique("augusteon", mon.peristyle_court(72.0, 46.0, 8.0, (1.0, 0.9, 0.8), False), placement(stoa.x, stoa.y, stoa_z, STOA.theta))
    scene.block(rect(STOA, -38.0, 38.0, -25.0, 25.0))
    scene.block(rect(AUG, -half_u - 8.0, half_u + 48.0, -half_v - 30.0, half_v + 8.0))
    scene.block([tuple(MILION + Vector((dx, dy))) for dx, dy in ((-10, -10), (10, -10), (10, 10), (-10, 10))])
    for k, (u, v) in enumerate(((-30.0, 18.0), (-10.0, -20.0), (20.0, 20.0), (25.0, -18.0))):
        scene.unique("augusteon", mon.statue_group(60 + k), AUG.matrix(u, v, z, math.pi * k / 2))
        scene.obstacle(AUG.world(u, v), 2.2)
    zeux = levels["zeuxippus"]
    scene.unique("palace", mon.bath_complex(), ZEUX.matrix(0.0, 0.0, zeux))
    scene.block(rect(ZEUX, -44.0, 44.0, -44.0, 34.0))
    return z


def build_palace(scene, levels, rng):
    frame = palace_frame()
    placements = {
        "daphne": [("hall", (-100.0, -110.0, 60.0, 22.0, 13.0)), ("court", (-100.0, -75.0, 46.0, 34.0)),
                   ("chapel", (-130.0, -140.0))],
        "consistorium": [("hall", (-100.0, -20.0, 70.0, 26.0, 15.0)), ("court", (-90.0, 12.0, 60.0, 14.0))],
        "magnaura": [("hall", (0.0, -100.0, 60.0, 28.0, 16.0)), ("chapel", (20.0, -60.0))],
        "nineteen": [("hall", (-95.0, 25.0, 64.0, 24.0, 14.0)), ("court", (-90.0, 0.0, 40.0, 10.0))],
        "garden": [("chapel", (10.0, 25.0)), ("court", (15.0, 55.0, 40.0, 24.0))],
        "lower": [("court", (-110.0, 120.0, 50.0, 40.0)), ("hall", (-50.0, 140.0, 46.0, 20.0, 11.0))],
        "boukoleon": [("hall", (30.0, 170.0, 70.0, 20.0, 12.0)), ("court", (40.0, 120.0, 50.0, 34.0)),
                      ("chapel", (-10.0, 110.0))],
    }
    tree_spots = []
    beds = MeshBuilder()
    footprints = []
    for name, (u0, u1, v0, v1) in PALACE_TERRACES:
        z = levels[f"palace_{name}"]
        local = []
        for kind, spec in placements.get(name, []):
            u, v = spec[0], spec[1]
            if kind == "hall":
                build = mon.palace_hall(spec[2], spec[3], spec[4], True,
                                        rng.choice([(0.96, 0.8, 0.6), (0.92, 0.66, 0.5), (0.96, 0.86, 0.7)]),
                                        rng.choice(["terracotta_tiles", "lead"]))
                local.append((u - spec[2] / 2, u + spec[2] / 2 + spec[3] * 0.35, v - spec[3] / 2, v + spec[3] / 2))
            elif kind == "court":
                build = mon.peristyle_court(spec[2], spec[3], 6.5, rng.choice([(0.96, 0.76, 0.56), (0.94, 0.84, 0.7)]))
                local.append((u - spec[2] / 2, u + spec[2] / 2, v - spec[3] / 2, v + spec[3] / 2))
                if spec[2] > 26.0 and spec[3] > 26.0:
                    for du in (-1, 1):
                        for dv in (-1, 1):
                            tree_spots.append((frame.world(u + du * (spec[2] / 2 - 10.0), v + dv * (spec[3] / 2 - 10.0)), z,
                                               "tree_cypress_b"))
            else:
                build = mon.domed_chapel(12.0, 9.0)
                local.append((u - 6.0, u + 9.0, v - 6.0, v + 6.0))
            scene.unique("palace", build, frame.matrix(u, v, z, 0.0))
        for rect_ in local:
            scene.solid_rects.append((frame, *rect_))
        footprints += local

        def taken(a, b, c, d, margin=2.0):
            return any(a < r1 + margin and b > r0 - margin and c < r3 + margin and d > r2 - margin for r0, r1, r2, r3 in local)
        cell = 13.0
        for i in range(int((u1 - u0) // cell)):
            for j in range(int((v1 - v0) // cell)):
                a, b = u0 + 1.0 + i * cell + 1.5, u0 + 1.0 + (i + 1) * cell - 1.5
                c, d = v0 + 1.0 + j * cell + 1.5, v0 + 1.0 + (j + 1) * cell - 1.5
                if taken(a, b, c, d) or rng.random() > 0.8:
                    continue
                green = rng.choice([(0.30, 0.48, 0.16), (0.36, 0.52, 0.2), (0.26, 0.44, 0.18)])
                sophia.box(beds, (a, c, z - 0.5), (b, d, z + 0.16), "matte", green)
                sophia.box(beds, (a - 0.25, c - 0.25, z - 0.5), (b + 0.25, d + 0.25, z + 0.1), "matte", (0.62, 0.56, 0.46))
                roll = rng.random()
                if roll < 0.3:
                    tree_spots.append((frame.world((a + b) / 2, (c + d) / 2), z + 0.16, rng.choice(["tree_pine", "tree_olive"])))
                elif roll < 0.55:
                    for corner in ((a + 1.2, c + 1.2), (b - 1.2, d - 1.2)):
                        tree_spots.append((frame.world(*corner), z + 0.16, "tree_cypress"))
        for v_edge in (v0 + 2.2, v1 - 2.2):
            u = u0 + 6.0
            while u < u1 - 6.0:
                if not taken(u - 1.5, u + 1.5, v_edge - 1.5, v_edge + 1.5, 1.0):
                    tree_spots.append((frame.world(u, v_edge), z, "tree_cypress"))
                u += 11.0
        wall = MeshBuilder()
        sophia.box(wall, (u0, v0 - 1.0, z - 12.0), (u1, v0, z + 1.2), "banded")
        sophia.box(wall, (u0, v1, z - 12.0), (u1, v1 + 1.0, z + 1.2), "banded")
        scene.unique("palace", wall, frame.matrix(0.0, 0.0, 0.0))
        pave = plinth([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], -0.6, 0.0, "travertine", (0.82, 0.76, 0.66))
        scene.unique("sol", pave, frame.matrix(0.0, 0.0, z + 0.04))
        scene.block(rect(frame, u0 - 2.0, u1 + 2.0, v0 - 2.0, v1 + 2.0))
    scene.unique("jardins", beds, frame.matrix(0.0, 0.0, 0.04))
    return tree_spots


def shoreline(scene):
    centre = Vector((150.0, 150.0))
    points = []
    for k in range(720):
        a = math.tau * k / 720
        d = Vector((math.cos(a), math.sin(a)))
        r = 30.0
        found = None
        while r < 2400.0:
            p = centre + d * r
            if max(abs(p.x), abs(p.y)) > NEAR_HALF - 20.0:
                break
            if scene.ground(p.x, p.y) < 0.0:
                found = p
                break
            r += 4.0
        points.append(found)
    return points


def build_walls(scene, shore):
    walls = []
    harbours = [shore_point for shore_point, _, _ in scene.harbours.values()]
    previous = None
    for p in shore:
        if p is None:
            previous = None
            continue
        inward = (Vector((150.0, 150.0)) - p).normalized()
        q = p + inward * 14.0
        if previous is not None and (q - previous).length < 60.0 and all((q - h).length > 90.0 for h in harbours):
            walls.append((previous, q))
        previous = q
    frame = palace_frame()
    palace = [(u0 - 40.0, u1 + 40.0, v0 - 40.0, v1 + 40.0) for _, (u0, u1, v0, v1) in PALACE_TERRACES]
    tower_every = 0
    for a, b in walls:
        length = (b - a).length
        if length < 1.0:
            continue
        d = (b - a).normalized()
        z = min(scene.ground(a.x, a.y), scene.ground(b.x, b.y))
        z = max(z, 0.6)
        turn = math.atan2(d.y, d.x)
        scene.unique("murailles", mon.wall_segment(length + 0.6, 4.5, merlons=False), placement(a.x, a.y, z, turn))
        tower_every += 1
        u, v = frame.local(a)
        if tower_every % 16 == 0 and not any(u0 < u < u1 and v0 < v < v1 for u0, u1, v0, v1 in palace):
            scene.unique("murailles", mon.wall_tower(8.0), placement(a.x, a.y, z, turn))
    return len(walls)


CARGO = {"prop_amphorae": lambda: amphora_pile(3, 5, 1), "prop_sacks": lambda: sack_pile(2),
         "prop_barrels": lambda: barrel_group(3)}


def harbour_sites():
    return [(geo(41.0125, 28.9772), 8.0, "prosphorion"), (geo(41.0128, 28.9722), 350.0, "neorion"),
            (geo(41.0050, 28.9770), 175.0, "boukoleon"), (geo(41.0050, 28.9690), 195.0, "julien")]


def march_to_sea(scene, point, direction):
    p = Vector(point)
    for step in range(600):
        q = p + direction * step * 2.0
        if scene.ground(q.x, q.y) < -0.4:
            return q
    return p


def build_harbours(scene, rng):
    moored = []
    root_ships = {}
    for site, bearing, name in harbour_sites():
        outward = Vector((math.sin(math.radians(bearing)), math.cos(math.radians(bearing))))
        shore_point = march_to_sea(scene, site, outward)
        left = Vector((-outward.y, outward.x))
        for side in (-1, 1):
            start = shore_point + left * side * 70.0 - outward * 6.0
            heading = (outward + left * side * 0.25).normalized()
            turn = math.atan2(heading.y, heading.x)
            scene.unique("ports", mon.mole(110.0), placement(start.x, start.y, 0.0, turn))
        quay_turn = math.atan2(left.y, left.x)
        for k in range(-2, 3):
            spot = shore_point - outward * 22.0 + left * k * 40.0
            z = max(scene.ground(spot.x, spot.y), 1.0)
            scene.unique("ports", mon.warehouse(34.0, 12.0, 7.0), placement(spot.x, spot.y, z, quay_turn))
        quay = MeshBuilder()
        quay.box((-90.0, -10.0, -6.0), (90.0, 4.0, 1.4), "col_travertine")
        quay_point = shore_point - outward * 3.0
        scene.unique("sol", quay, placement(quay_point.x, quay_point.y, 0.0, quay_turn))
        scene.block([tuple(shore_point + left * s * 95.0 + outward * o) for s, o in ((-1, -40), (1, -40), (1, 130), (-1, 130))])
        for k in range(16):
            along = rng.uniform(-55.0, 55.0)
            off = rng.uniform(18.0, 95.0)
            spot = shore_point + left * along + outward * off
            if scene.ground(spot.x, spot.y) > -0.9 or not ship_room(scene, spot, 22.0):
                continue
            key = rng.choice(["ship_merchant", "ship_merchant_b", "ship_dromon", "ship_skiff", "ship_skiff_b", "ship_merchant"])
            heading = rng.choice([1, -1]) * outward
            moored.append((key, placement(spot.x, spot.y, 0.0, math.atan2(-heading.x, heading.y) + rng.uniform(-0.2, 0.2))))
        root_ships[name] = (shore_point, outward, left)
        for k in range(3):
            spot = shore_point + left * rng.uniform(-50.0, 50.0) - outward * 8.0
            z = scene.ground(spot.x, spot.y)
            key = rng.choice(list(CARGO))
            scene.add(key, placement(spot.x, spot.y, max(z, 1.4), rng.uniform(0, 6.28)), CARGO[key])
        crane_spot = shore_point - outward * 6.0 + left * 30.0
        scene.unique("ports", crane(), placement(crane_spot.x, crane_spot.y, 1.4, quay_turn))
    return moored, root_ships


def build_open_water_ships(scene, rng):
    out = []
    targets = [(geo(41.0185, 28.9700), 7), (geo(41.0200, 28.9800), 6), (geo(41.0120, 28.9950), 5), (geo(40.9990, 28.9800), 6),
               (geo(41.0205, 28.9745), 6), (geo(41.0195, 28.9640), 5),
               (geo(41.0000, 28.9950), 4), (geo(41.0220, 28.9900), 4)]
    for centre, count in targets:
        for k in range(count):
            spot = centre + Vector((rng.uniform(-180, 180), rng.uniform(-120, 120)))
            if scene.ground(spot.x, spot.y) > -3.0 or not ship_room(scene, spot, 45.0):
                continue
            key = rng.choice(["ship_merchant_sail", "ship_dromon_sail", "ship_grain", "ship_skiff", "ship_merchant",
                              "ship_dromon", "ship_skiff_b"])
            out.append((key, placement(spot.x, spot.y, 0.0, rng.uniform(0, math.tau))))
    return out


def ship_room(scene, spot, distance):
    if any((spot - other).length < distance for other in scene.ship_spots):
        return False
    scene.ship_spots.append(spot)
    return True


def build_forum(scene, levels):
    z = levels["forum"]
    scene.unique("forum", mon.forum_constantine(), FORUM.matrix(0.0, 0.0, z))
    scene.unique("forum", mon.porphyry_column(), FORUM.matrix(0.0, 0.0, z, -math.pi / 2))
    pave = plinth([(62.0 * math.cos(math.tau * k / 40), 52.0 * math.sin(math.tau * k / 40)) for k in range(40)], -0.6, 0.0,
                  "travertine")
    scene.unique("sol", pave, FORUM.matrix(0.0, 0.0, z + 0.04))
    scene.block(ellipse(FORUM, 72.0, 62.0))
    scene.obstacle(FORUM.origin, 6.5)
    return z


def build_mese(scene, levels, rng):
    points = levels["mese_points"]
    profile = levels["mese_levels"]
    ribbon = MeshBuilder()
    half = MESE_WIDTH / 2
    stations = []
    for index, (p, z) in enumerate(zip(points, profile)):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        stations.append((p, z, d, n))
    for (p, z, d, n), (q, z2, d2, n2) in zip(stations[:-1], stations[1:]):
        quad = [(*(p - n * half), z + 0.05), (*(q - n2 * half), z2 + 0.05), (*(q + n2 * half), z2 + 0.05),
                (*(p + n * half), z + 0.05)]
        sophia.facing_quad(ribbon, quad, (0, 0, 1), "travertine")
        for side in (1, -1):
            a, b = p + n * side * half, q + n2 * side * half
            sophia.facing_quad(ribbon, [(a.x, a.y, z - 0.9), (b.x, b.y, z2 - 0.9), (b.x, b.y, z2 + 0.05), (a.x, a.y, z + 0.05)],
                               (n.x * side, n.y * side, 0.0), "travertine")
    scene.unique("sol", ribbon)
    length = sum((b - a).length for a, b in zip(points[:-1], points[1:]))
    bays = {f"bay_{plaster}_{upper}": [] for plaster, upper in BAY_KINDS}
    keys = list(bays)
    runs = {1: [0, None], -1: [0, None]}
    distance = 30.0
    cumulative = [0.0]
    for a, b in zip(points[:-1], points[1:]):
        cumulative.append(cumulative[-1] + (b - a).length)
    stalls = []
    while distance < length - 16.0:
        index = max(i for i, c in enumerate(cumulative) if c <= distance)
        index = min(index, len(points) - 2)
        t = (distance - cumulative[index]) / max(cumulative[index + 1] - cumulative[index], 1e-6)
        p = points[index].lerp(points[index + 1], t)
        z = profile[index] + (profile[index + 1] - profile[index]) * t
        d = (points[index + 1] - points[index]).normalized()
        n = Vector((-d.y, d.x))
        for side in (1, -1):
            base = p + n * side * (MESE_ROAD / 2)
            turn = math.atan2(d.y, d.x) if side > 0 else math.atan2(-d.y, -d.x)
            origin = base if side > 0 else base + d * BAY
            run = runs[side]
            if run[0] <= 0:
                previous = run[1]
                run[1] = rng.choice([k for k in keys if previous is None or k.split("_")[1] != previous.split("_")[1]])
                run[0] = rng.randint(3, 6)
            run[0] -= 1
            bays[run[1]].append(placement(origin.x, origin.y, z, turn))
            if rng.random() < 0.08:
                stalls.append((base - n * side * 0.8 + d * 2.0, z, turn))
        distance += BAY
    for key, matrices in bays.items():
        plaster, upper = key.split("_")[1], int(key.split("_")[2])
        scene.instances("mese", key, lambda plaster=plaster, upper=upper: city.portico_bay(plaster, len(plaster) + upper, upper=upper),
                        matrices, True, True)
    for points_side in (1, -1):
        polygon = [tuple(p + Vector((-(q - p).normalized().y, (q - p).normalized().x)) * points_side * (MESE_ROAD / 2 + 16.5))
                   for p, q in zip(points[:-1], points[1:])]
        polygon += [tuple(p) for p in reversed(points[:-1])]
        scene.block(polygon)
    return stalls, length


def occupancy(scene, rng):
    cell = 2.0
    count = int(2 * NEAR_HALF / cell)
    axis = -NEAR_HALF + (np.arange(count) + 0.5) * cell
    gx, gy = np.meshgrid(axis, axis)
    blocked = scene.field.sample(gx, gy) < 1.2
    for polygon in scene.blocked:
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        c0 = max(int((min(xs) + NEAR_HALF) / cell) - 1, 0)
        c1 = min(int((max(xs) + NEAR_HALF) / cell) + 2, count)
        r0 = max(int((min(ys) + NEAR_HALF) / cell) - 1, 0)
        r1 = min(int((max(ys) + NEAR_HALF) / cell) + 2, count)
        if c1 <= c0 or r1 <= r0:
            continue
        blocked[r0:r1, c0:c1] |= polygon_mask(polygon, gx[r0:r1, c0:c1], gy[r0:r1, c0:c1])
    gy_, gx_ = np.gradient(scene.field.sample(gx, gy), cell)
    blocked |= np.hypot(gx_, gy_) > 0.55
    return blocked, cell, count


def street_angle(x, y):
    p = Vector((x, y))
    mese = min((p - q).length for q in dense(MESE, 20.0))
    if mese < 160.0:
        d = (MESE[2] - MESE[0]).normalized()
        return math.atan2(d.y, d.x)
    if (p - HIPPO.origin).length < 520.0 and p.y < 0.0:
        return HIPPO.theta
    return HS.theta + (0.25 if p.y > 500 else 0.0)


def mark(blocked, cell, count, corners):
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    c0 = max(int((min(xs) + NEAR_HALF) / cell), 0)
    c1 = min(int((max(xs) + NEAR_HALF) / cell) + 2, count)
    r0 = max(int((min(ys) + NEAR_HALF) / cell), 0)
    r1 = min(int((max(ys) + NEAR_HALF) / cell) + 2, count)
    if c1 <= c0 or r1 <= r0:
        return
    axis = -NEAR_HALF + (np.arange(count) + 0.5) * cell
    gx, gy = np.meshgrid(axis[c0:c1], axis[r0:r1])
    blocked[r0:r1, c0:c1] |= polygon_mask(corners, gx, gy)


def build_city(scene, rng, eyes):
    blocked, cell, count = occupancy(scene, rng)
    templates = list(city.HOUSES)
    weights = [3, 3, 3, 2, 1, 2, 1, 1, 2]
    simple = list(city.FAR_HOUSES)
    placed = {key: [] for key in templates + simple}
    footprints = dict(city.FOOTPRINTS, **city.FAR_FOOTPRINTS)
    smoke_spots = []
    tree_spots = []
    churches = 0

    def free_spot(corners):
        for cx, cy in corners:
            column = int((cx + NEAR_HALF) / cell)
            row = int((cy + NEAR_HALF) / cell)
            if not (0 <= column < count and 0 <= row < count) or blocked[row, column]:
                return False
        return True

    def house(x, y, angle, key):
        w, d = footprints[key]
        c, s_ = math.cos(angle), math.sin(angle)
        inset = [(x + c * u - s_ * v, y + s_ * u + c * v) for u, v in ((-w / 2 + 0.8, -d / 2 + 0.8), (w / 2 - 0.8, -d / 2 + 0.8),
                                                                      (w / 2 - 0.8, d / 2 - 0.8), (-w / 2 + 0.8, d / 2 - 0.8))]
        if not free_spot(inset + [(x, y)]):
            return False
        if min((Vector((x, y)) - e).length for e in eyes) < 25.0:
            return False
        corners = [(x + c * u - s_ * v, y + s_ * u + c * v) for u, v in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
        heights = [scene.ground(cx, cy) for cx, cy in corners]
        if max(heights) - min(heights) > 3.2:
            return False
        z = min(heights) + 0.25 * (max(heights) - min(heights))
        placed[key].append(placement(x, y, z, angle))
        mark(blocked, cell, count, inset)
        if rng.random() < 0.03:
            smoke_spots.append(Vector((x, y, z + 12.0)))
        return True

    angles = []
    for x in np.arange(-NEAR_HALF, NEAR_HALF, 100.0):
        for y in np.arange(-NEAR_HALF, NEAR_HALF, 100.0):
            a = street_angle(x, y)
            if all(abs(a - b) > 1e-6 for b in angles):
                angles.append(a)
    reach = NEAR_HALF * 1.45
    for angle in angles:
        axis_u = Vector((math.cos(angle), math.sin(angle)))
        axis_v = Vector((-math.sin(angle), math.cos(angle)))
        for bu in np.arange(-reach, reach, BLOCK_U + STREET):
            for bv in np.arange(-reach, reach, BLOCK_V + STREET):
                centre = axis_u * (bu + BLOCK_U / 2) + axis_v * (bv + BLOCK_V / 2)
                if max(abs(centre.x), abs(centre.y)) > NEAR_HALF - 40.0 or abs(street_angle(centre.x, centre.y) - angle) > 1e-6:
                    continue
                detailed = (centre - DETAIL_CENTRE).length < DETAIL_RADIUS or min((centre - e).length for e in eyes) < 240.0
                roll = rng.random()
                if roll < 0.035:
                    for k in range(rng.randint(3, 6)):
                        p = centre + axis_u * rng.uniform(-20, 20) + axis_v * rng.uniform(-14, 14)
                        if scene.ground(p.x, p.y) > 2.0 and free_spot([(p.x, p.y)]):
                            tree_spots.append(p)
                    continue
                if roll < 0.05:
                    w = rng.choice([10.0, 12.0])
                    if free_spot([tuple(centre + axis_u * du + axis_v * dv) for du in (-w / 2, w / 2) for dv in (-w / 2, w / 2)]):
                        z = scene.lowest(centre.x, centre.y, w / 2)
                        scene.unique("palace", mon.domed_chapel(w, 8.5), placement(centre.x, centre.y, z, angle))
                        mark(blocked, cell, count, [tuple(centre + axis_u * du + axis_v * dv)
                                                    for du, dv in ((-w / 2, -w / 2), (w / 2 + 3, -w / 2), (w / 2 + 3, w / 2), (-w / 2, w / 2))])
                        churches += 1
                sides = [(-axis_v, axis_u, axis_u * bu + axis_v * bv, BLOCK_U, 0.0),
                         (axis_v, axis_u, axis_u * bu + axis_v * (bv + BLOCK_V), BLOCK_U, 0.0),
                         (-axis_u, axis_v, axis_u * bu + axis_v * bv, BLOCK_V, 9.0),
                         (axis_u, axis_v, axis_u * (bu + BLOCK_U) + axis_v * bv, BLOCK_V, 9.0)]
                for outward, along, edge, span, inset in sides:
                    position = inset + rng.uniform(0.0, 1.5)
                    while position < span - inset - 6.0:
                        key = rng.choices(templates, weights)[0] if detailed else rng.choice(simple)
                        w, d = footprints[key]
                        if position + w > span - inset + 0.5:
                            position += 2.0
                            continue
                        point = edge + along * (position + w / 2) - outward * (d / 2)
                        angle_house = math.atan2(outward.x, -outward.y)
                        if house(point.x, point.y, angle_house, key):
                            position += w + (rng.uniform(1.5, 3.0) if rng.random() < 0.18 else 0.0)
                        else:
                            position += 3.0
                for k in range(rng.randint(0, 3 if detailed else 2)):
                    p = centre + axis_u * rng.uniform(-12, 12) + axis_v * rng.uniform(-6, 6)
                    if scene.ground(p.x, p.y) > 2.0 and free_spot([(p.x, p.y)]):
                        tree_spots.append(p)
    builds = dict(city.HOUSES, **city.FAR_HOUSES)
    for key, matrices in placed.items():
        scene.instances("ville", key, builds[key], matrices, key in city.HOUSES, True)
    counts = {key: len(m) for key, m in placed.items()}
    counts["churches"] = churches
    return counts, smoke_spots, tree_spots


def build_far_city(scene, far, rng):
    placed = {key: [] for key in city.FAR_HOUSES}
    keys = list(city.FAR_HOUSES)
    for cx, cy, radius in far_towns():
        count = int(radius * radius / 3000.0)
        for k in range(count):
            r = radius * math.sqrt(rng.random()) * 0.9
            a = rng.uniform(0, math.tau)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if max(abs(x), abs(y)) < NEAR_HALF + 20.0:
                continue
            z = float(far.sample(x, y))
            if z < 1.5:
                continue
            placed[rng.choice(keys)].append(placement(x, y, z - 0.5, rng.uniform(0, math.tau)))
    for key, matrices in placed.items():
        scene.instances("ville_lointaine", key, city.FAR_HOUSES[key], matrices, False, True)
    return {key: len(m) for key, m in placed.items()}


TREES = {
    "tree_cypress": lambda: cypress_tree(2, 14.0),
    "tree_cypress_b": lambda: cypress_tree(5, 10.0),
    "tree_pine": lambda: stone_pine(1, 13.0),
    "tree_olive": lambda: buildings.olive_tree(5.0, 3),
    "tree_oak": lambda: buildings.holm_oak(8.0, 4),
}


def build_trees(scene, rng, spots, palace_spots):
    placed = {key: [] for key in TREES}
    keys = list(TREES)
    weights = [4, 2, 2, 2, 2]
    for p in spots:
        z = scene.ground(p.x, p.y)
        placed[rng.choices(keys, weights)[0]].append(placement(p.x, p.y, z - 0.2, rng.uniform(0, math.tau), rng.uniform(0.85, 1.15)))
    for p, z, key in palace_spots:
        placed[key].append(placement(p.x, p.y, z - 0.1, rng.uniform(0, math.tau), rng.uniform(0.85, 1.15)))
    acropolis = geo(41.0125, 28.9840)
    for k in range(70):
        p = acropolis + Vector((rng.uniform(-220, 220), rng.uniform(-200, 200)))
        if scene.ground(p.x, p.y) < 3.0:
            continue
        placed[rng.choices(keys, weights)[0]].append(placement(p.x, p.y, scene.ground(p.x, p.y) - 0.2, rng.uniform(0, math.tau)))
    for key, matrices in placed.items():
        scene.instances("arbres", key, TREES[key], matrices, True, False)
    return {key: len(m) for key, m in placed.items()}


def viewpoints(scene, levels, hippo_marks):
    points = {}
    hs_z = levels["hs"]
    centre = HS.world(0.0, 0.0)
    points["vue-d-ensemble"] = (Vector((-270.0, -620.0, 195.0)), Vector((centre.x, centre.y, hs_z + 30.0)))
    eye = HS.world(-80.0, -20.0)
    target = HS.world(-5.0, 10.0)
    points["sainte-sophie"] = (Vector((eye.x, eye.y, hs_z + 1.7)), Vector((target.x, target.y, hs_z + 38.0)))
    track = levels["track"]
    eye = HIPPO.world(14.0, 120.0)
    target = HIPPO.world(-24.0, -70.0)
    points["l-hippodrome"] = (Vector((eye.x, eye.y, track + 6.0)), Vector((target.x, target.y, track + 9.0)))
    mese_points = levels["mese_points"]
    mese_levels = levels["mese_levels"]
    index = len(mese_points) // 5
    eye = mese_points[index]
    points["la-mese"] = (Vector((eye.x, eye.y, mese_levels[index] + 1.7)), scene.statue_top)
    shore, outward, left = scene.harbours["prosphorion"]
    heading = (outward - left * 0.25).normalized()
    eye = shore - left * 70.0 - outward * 6.0 + heading * 70.0
    bearing = math.radians(HORN_BEARING)
    target = eye + Vector((math.sin(bearing), math.cos(bearing))) * 500.0
    points["la-corne-d-or"] = (Vector((eye.x, eye.y, 9.0)), Vector((target.x, target.y, 6.0)))
    return points


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))
    new_empty("interior_center", scene.collection, root, Matrix.Translation(scene.interior))


class Surface:
    def __init__(self, objects):
        bpy.context.view_layer.update()
        vertices, triangles, offset = [], [], 0
        for item in objects:
            mesh = item.data
            co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
            mesh.vertices.foreach_get("co", co)
            mesh.calc_loop_triangles()
            tris = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get("vertices", tris)
            matrix = np.array(item.matrix_world)
            co = co.reshape(-1, 3)
            vertices.append(co @ matrix[:3, :3].T + matrix[:3, 3])
            triangles.append(tris.reshape(-1, 3) + offset)
            offset += len(co)
        self.tree = BVHTree.FromPolygons(np.concatenate(vertices).tolist(), np.concatenate(triangles).tolist(),
                                         all_triangles=True)

    def height(self, x, y, hint, reach=3.0):
        hit = self.tree.ray_cast(Vector((x, y, hint + reach)), Vector((0.0, 0.0, -1.0)), reach + 8.0)
        return hint if hit[0] is None else hit[0].z


def ground_route(scene, points, spacing=2.6):
    chain = []
    for p in dense([Vector((p.x, p.y)) for p in points], spacing):
        hint = max(scene.ground(p.x, p.y), 1.5)
        chain.append(Vector((p.x, p.y, scene.surface.height(p.x, p.y, hint))))
    out = [chain[0]]
    for b in chain[1:]:
        refine(scene, out[-1], b, out)
    return out


def refine(scene, a, b, out, depth=0):
    if depth < 5 and (b.to_2d() - a.to_2d()).length > 0.3:
        worst = 0.0
        for t in (0.25, 0.5, 0.75):
            p = a.lerp(b, t)
            worst = max(worst, abs(scene.surface.height(p.x, p.y, max(a.z, b.z)) - p.z))
        if worst > 0.04:
            middle = (a + b) / 2
            middle.z = scene.surface.height(middle.x, middle.y, max(a.z, b.z))
            refine(scene, a, middle, out, depth + 1)
            refine(scene, middle, b, out, depth + 1)
            return
    out.append(b)


def route_problems(name, chain):
    problems = []
    for index, (a, b) in enumerate(zip(chain[:-1], chain[1:])):
        if abs(b.z - a.z) > 0.35:
            problems.append(f"{name} step {index}: {a.z:.2f} to {b.z:.2f} at {a.x:.1f},{a.y:.1f}")
        if (b.to_2d() - a.to_2d()).length > 3.0:
            problems.append(f"{name} gap {index}")
    return problems


def routes(scene, levels, hippo_marks):
    mese = levels["mese_points"]
    start = len(mese) // 8
    stop = len(mese) * 7 // 8

    def offset(points, amount):
        out = []
        for index, p in enumerate(points):
            a = points[max(index - 1, 0)]
            b = points[min(index + 1, len(points) - 1)]
            d = (b - a).normalized()
            out.append(p + Vector((-d.y, d.x)) * amount)
        return out
    harbour = scene.harbours["prosphorion"]
    shore, outward, left = harbour
    return {
        "mese-nord": offset(mese[start:stop], 3.5),
        "mese-sud": list(reversed(offset(mese[start:stop], -3.8))),
        "augusteon": [AUG.world(-34.0, -15.0), AUG.world(34.0, -15.0)],
        "augusteon-travers": [AUG.world(34.0, -18.0), AUG.world(34.0, 20.0)],
        "parvis": [AUG.world(-44.0, 24.0), HS.world(-104.0, -22.0), HS.world(-104.0, 8.0)],
        "atrium": [HS.world(-90.0, 6.1), HS.world(-50.0, 6.1)],
        "hippodrome": [HIPPO.world(24.0, -170.0), HIPPO.world(26.0, 140.0)],
        "quai": [shore + outward * 3.0 - left * 80.0, shore + outward * 3.0 + left * 80.0],
        "forum": [FORUM.world(-50.0, 14.0), FORUM.world(0.0, 12.0), FORUM.world(50.0, 10.0)],
    }


def place_routes(scene, levels, hippo_marks, eyes):
    root = scene.root("life")
    counts = {}
    samples = []
    problems = []
    for name, points in routes(scene, levels, hippo_marks).items():
        chain = ground_route(scene, points)
        problems += route_problems(name, chain)
        problems += [f"{name} crosses an obstacle at {p.x:.1f},{p.y:.1f}" for p in chain if not scene.clear_of(p.to_2d(), 0.4)]
        for point in chain:
            for eye in eyes:
                if (point.to_2d() - eye.to_2d()).length < EYE_CLEARANCE and abs(point.z + 1.6 - eye.z) < 2.5:
                    problems.append(f"{name} passes too close to a camera")
        for index, point in enumerate(chain):
            new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(point))
        for a, b in zip(chain[:-1], chain[1:]):
            steps = max(int((b - a).length / 0.5), 1)
            samples.extend(a.lerp(b, k / steps).to_2d() for k in range(steps))
        counts[name] = len(chain)
    for problem in problems[:40]:
        print("ROUTE", problem, flush=True)
    return counts, samples, problems


FIGURE_WEIGHTS = [("fig_citizen", 3.0), ("fig_citizen_b", 3.0), ("fig_citizen_c", 2.0), ("fig_woman", 3.0), ("fig_woman_b", 2.5),
                  ("fig_noble", 0.8), ("fig_dignitary", 1.0), ("fig_monk", 0.8), ("fig_child", 1.0), ("fig_merchant", 1.2),
                  ("fig_porter", 0.8)]


def pick(rng, weights):
    total = sum(w for _, w in weights)
    roll = rng.random() * total
    for key, w in weights:
        roll -= w
        if roll <= 0:
            return key
    return weights[-1][0]


def build_life(scene, rng, levels, hippo_marks, samples, eyes, targets, stalls):
    tree = KDTree(max(len(samples), 1))
    for index, point in enumerate(samples):
        tree.insert((point.x, point.y, 0.0), index)
    tree.balance()
    sights = [(eye.to_2d(), target.to_2d()) for eye, target in zip(eyes, targets)]

    def free(p, radius=0.75):
        if samples and tree.find_range((p.x, p.y, 0.0), radius):
            return False
        for eye, target in sights:
            span = target - eye
            t = max(0.0, min(1.0, (p - eye).dot(span) / max(span.length_squared, 1e-6)))
            if (p - (eye + span * t)).length < 2.2 and (p - eye).length < 30.0:
                return False
        return all((p - e.to_2d()).length > 2.6 for e in eyes) and scene.clear_of(p, radius * 0.5)

    def group_free(p, facing, length=10.5):
        back = Vector((math.sin(facing), -math.cos(facing)))
        return all(free(p + back * t, 1.2) for t in np.arange(0.0, length, 1.5))

    def figure(p, turn, key=None):
        key = key or pick(rng, FIGURE_WEIGHTS)
        scene.add(key, placement(p.x, p.y, 0.0, turn), life.FIGURES[key])

    placed = 0
    for k in range(115):
        p = AUG.world(rng.uniform(-36.0, 36.0), rng.uniform(-24.0, 24.0))
        if free(p):
            towards = HS.world(-70.0, 0.0) - p
            figure(p, math.atan2(-towards.x, towards.y) + rng.gauss(0, 0.9))
            placed += 1
    gate = HS.world(-104.0, 0.0)
    for k in range(4):
        p = AUG.world(-8.0 + k * 11.0, 10.0 + (k % 2) * 4.0)
        towards = gate - p
        facing = math.atan2(-towards.x, towards.y)
        if group_free(p, facing):
            scene.add("group_procession", placement(p.x, p.y, 0.0, facing), life.procession_group)
    for u in (-74.0, -58.0):
        scene.add("group_procession", HS.matrix(u, -12.0, 0.0, -math.pi / 2), life.procession_group)
        for t in np.arange(0.0, 10.5, 1.0):
            scene.obstacle(HS.world(u - t, -12.0), 1.4)
    for k in range(70):
        p = HS.world(rng.uniform(-92.0, -50.0), rng.uniform(-24.0, 24.0))
        if abs(scene.fountain.x - p.x) < 6.0 and abs(scene.fountain.y - p.y) < 6.0:
            continue
        if free(p):
            towards = HS.world(-30.0, 0.0) - p
            figure(p, math.atan2(-towards.x, towards.y) + rng.gauss(0, 0.5))
            placed += 1
    for u in (-3.6, 3.6):
        for k in range(4):
            p = AUG.world(u, -26.6 + k * 1.25)
            if free(p, 0.5):
                figure(p, AUG.theta + rng.gauss(0, 0.04), "fig_guard")
    for k in range(10):
        p = AUG.world(rng.uniform(30.0, 40.0), rng.uniform(-14.0, 14.0))
        if free(p):
            figure(p, AUG.theta + math.pi / 2, rng.choice(["fig_dignitary", "fig_guard"]))
    mese = levels["mese_points"]
    mese_levels = levels["mese_levels"]
    for k in range(170):
        index = rng.randrange(len(mese) - 1)
        a, b = mese[index], mese[index + 1]
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        p = a.lerp(b, rng.random()) + n * rng.uniform(-MESE_ROAD / 2 + 0.8, MESE_ROAD / 2 - 0.8)
        if free(p):
            figure(p, math.atan2(-d.x, d.y) + (math.pi if rng.random() < 0.5 else 0.0) + rng.gauss(0, 0.3))
            placed += 1
    for k in range(10):
        index = rng.randrange(len(mese) // 6, len(mese) - 2)
        a, b = mese[index], mese[index + 1]
        d = (b - a).normalized()
        p = a + Vector((-d.y, d.x)) * rng.uniform(-0.6, 0.6)
        if free(p, 2.5):
            key = rng.choice(["prop_wagon", "prop_mule", "prop_donkey"])
            build = {"prop_wagon": mule_wagon, "prop_mule": lambda: pack_beast("mule"), "prop_donkey": lambda: pack_beast("donkey")}[key]
            scene.add(key, placement(p.x, p.y, 0.0, math.atan2(-d.x, d.y) + (math.pi if k % 2 else 0.0)), build)
    for p, z, turn in stalls:
        if free(p, 1.4):
            key = "prop_stall_cloth" if rng.random() < 0.5 else "prop_stall_pottery"
            scene.add(key, placement(p.x, p.y, 0.0, turn), cloth_stall if key == "prop_stall_cloth" else pottery_stall)
    for k in range(45):
        p = FORUM.world(rng.uniform(-50.0, 50.0), rng.uniform(-40.0, 40.0))
        if free(p) and (p - FORUM.origin).length > 8.0:
            figure(p, rng.uniform(0, math.tau))
            placed += 1
    track = levels["track"]
    for k in range(10):
        p = HIPPO.world(rng.uniform(-30.0, 30.0), rng.uniform(-200.0, 150.0))
        if abs(HIPPO.local(p)[0]) < 6.0 or not free(p):
            continue
        figure(p, rng.uniform(0, math.tau), rng.choice(["fig_citizen", "fig_porter", "fig_child"]))
    for k, (x, y, colour) in enumerate(((-22.0, -150.0, life.BLUE), (-20.0, 60.0, life.GREEN))):
        scene.add(f"prop_quadriga_{k}", HIPPO.matrix(x, y, track + 0.02, math.pi if k else 0.0),
                  lambda colour=colour, k=k: quadriga(colour, "gallop", 40 + k))
    for name, (shore, outward, left) in scene.harbours.items():
        for k in range(18):
            p = shore - outward * rng.uniform(4.0, 14.0) + left * rng.uniform(-80.0, 80.0)
            if scene.ground(p.x, p.y) < 0.8 or not free(p):
                continue
            figure(p, rng.uniform(0, math.tau), rng.choice(["fig_porter", "fig_sailor", "fig_sailor", "fig_merchant", "fig_citizen"]))
    frame = palace_frame()
    for k in range(40):
        name, (u0, u1, v0, v1) = PALACE_TERRACES[k % len(PALACE_TERRACES)]
        p = frame.world(rng.uniform(u0 + 4, u1 - 4), rng.uniform(v0 + 4, v1 - 4))
        if free(p):
            figure(p, rng.uniform(0, math.tau), rng.choice(["fig_guard", "fig_dignitary", "fig_noble", "fig_citizen", "fig_monk"]))
    return placed


def hippodrome_crowds(scene, levels, hippo_marks):
    track = levels["track"]
    blocks = {"crowd_blue": [], "crowd_green": [], "crowd_mixed": []}
    kathisma_y = hippo_marks[3]
    for side in (1, -1):
        for k, y in enumerate(range(-170, 150, 10)):
            if side < 0 and abs(y - kathisma_y) < 22:
                continue
            key = "crowd_blue" if (side > 0 and y < 0) or (side < 0 and y > 40) else "crowd_green" if abs(y) < 120 else "crowd_mixed"
            for tier, row in ((0, (k * 3) % 10), (1, mon.WALKWAY_ROW + (k * 7 + 3) % 10)):
                if (k * 7 + (side > 0) * 3 + tier * 2) % 5 in ((0, 2) if tier == 0 else (0, 2, 4)):
                    continue
                x = side * (mon.TRACK_HALF + 1.2 + mon.row_offset(row))
                z = track + mon.row_z(row)
                blocks[key].append(HIPPO.matrix(x, y + 5.0, z, math.pi / 2 if side > 0 else -math.pi / 2))
    builds = {"crowd_blue": lambda: life.crowd_block(3, life.BLUE, 4, 9.5, mon.SEAT_DEPTH, mon.SEAT_RISE),
              "crowd_green": lambda: life.crowd_block(5, life.GREEN, 4, 9.5, mon.SEAT_DEPTH, mon.SEAT_RISE),
              "crowd_mixed": lambda: life.crowd_block(7, None, 4, 9.5, mon.SEAT_DEPTH, mon.SEAT_RISE, 0.5)}
    for key, matrices in blocks.items():
        scene.instances("vie", key, builds[key], matrices, False, False)
    return {key: len(m) for key, m in blocks.items()}


def ground_placements(scene):
    for key in list(scene.placements):
        grounded = []
        for matrix in scene.placements[key]:
            location = matrix.translation
            if location.z != 0.0:
                grounded.append(matrix)
                continue
            hint = scene.ground(location.x, location.y)
            z = scene.standing.height(location.x, location.y, hint + 2.0, 3.0)
            grounded.append(Matrix.Translation((0.0, 0.0, z)) @ matrix)
        scene.placements[key] = grounded


def place_life(scene):
    counts = {}
    for key, matrices in scene.placements.items():
        group = "vie" if key.startswith(("fig_", "group_")) else "props"
        scene.instances(group, key, scene.builds[key], matrices, False, False)
        counts[key] = len(matrices)
    root = scene.root("life")
    for index, (key, spec) in enumerate(life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda spec=spec: remap(person(spec)), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return counts


def place_ships(scene, moored, open_water):
    grouped = {}
    for key, matrix in moored + open_water:
        grouped.setdefault(key, []).append(matrix)
    for key, matrices in grouped.items():
        scene.instances("navires", key, SHIPS[key], matrices, True, False)
    return {key: len(m) for key, m in grouped.items()}


def atmosphere(scene, smoke_spots, levels, rng):
    root = scene.root("life")
    rng.shuffle(smoke_spots)
    smokes = smoke_spots[:9]
    doors = HS.world(-47.0, 0.0)
    smokes.append(Vector((doors.x, doors.y, levels["hs"] + 2.5)))
    for name, (shore, outward, left) in scene.harbours.items():
        p = shore - outward * 20.0
        smokes.append(Vector((p.x, p.y, scene.ground(p.x, p.y) + 9.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [Vector((*HS.world(0, 0), levels["hs"] + 75.0)), Vector((*HIPPO.world(0, 0), levels["track"] + 50.0))]
    for name, (shore, outward, left) in scene.harbours.items():
        p = shore + outward * 60.0
        flocks.append(Vector((p.x, p.y, 28.0)))
    for index, point in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation(point))
    return len(smokes), len(flocks)


def weathering(scene):
    for name, obj in scene.statics.items():
        if name.startswith(("beams", "jardins")):
            continue
        if name.startswith(("sol", "water")):
            weather(obj, 0.16, seed=len(name), scale=5.0, grime=0.0, ground=0.0)
            continue
        weather(obj, 0.12, seed=len(name) * 3, scale=6.0)


def render_previews(options, views):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(views) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, float(options.get("sky", 0.45)), aerosol=float(options.get("aerosol", 0.2)))
    lamp = sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, float(options.get("sun", 7.0)), SUN_COLOUR, 0.6)
    lamp.data.shadow_maximum_resolution = float(options.get("shadow", 0.03))
    haze_volume(stage, 40000.0, 900.0, float(options.get("haze", 0.00001)), (0.74, 0.82, 0.96), 0.4)
    configure_render(1280, 720, options["samples"], exposure=float(options.get("exposure", -0.2)), volumetric_end=30000.0)
    bpy.context.scene.view_settings.look = options.get("look", "AgX - Punchy")
    bpy.context.scene.eevee.shadow_pool_size = options.get("pool", "2048")
    lenses = {"vue-d-ensemble": 30.0, "sainte-sophie": 18.0, "l-hippodrome": 24.0, "la-mese": 22.0, "la-corne-d-or": 26.0,
              "interieur": 16.0}
    timings = {}
    for name in names:
        eye, target = views[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=lenses.get(name, 26.0))
        rig.data.clip_start = max(0.2, (eye - target).length / 400.0, eye.z / 120.0)
        rig.data.clip_end = 90000.0
        bpy.context.scene.eevee.taa_render_samples = min(options["samples"], 16) if name == "vue-d-ensemble" else options["samples"]
        path = os.path.join(CACHE, "previews", f"{name}.png")
        timings[name] = round(render_still(rig, path), 1)
        print(f"PREVIEW {name} {timings[name]} s", flush=True)
    return timings


def main():
    options = arguments()
    if options.get("reuse") == "1":
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        stored = json.loads(bpy.context.scene.get("preview_points", "{}"))
        views = {key: (Vector(eye), Vector(target)) for key, (eye, target) in stored.items()}
        print("PREVIEWS", json.dumps(render_previews(options, views)), flush=True)
        return
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tiles, credits = build_library(CACHE)
    dem = ter.load_dem(CACHE)
    landfill = [[tuple(geo(*p)) for p in polygon] for polygon in LANDFILL_GEO]
    near, _, to_sea = ter.condition(dem, NEAR_HALF, NEAR_SPACING, landfill)
    far, _ = ter.far_field(dem, FAR_HALF, FAR_SPACING)
    del dem
    levels = site_levels(near)
    near = terrain_edits(near, levels)
    print("LEVELS", json.dumps({k: round(v, 2) for k, v in levels.items() if isinstance(v, float)}), flush=True)
    scene = Scene(tiles, near)
    rng = random.Random(562)
    build_terrain(scene, near, far, to_sea, levels)
    print("TERRAIN", round(time.perf_counter() - started, 1), flush=True)
    build_sophia(scene, levels)
    track, hippo_marks = build_hippodrome(scene, levels)
    build_augusteon(scene, levels)
    palace_trees = build_palace(scene, levels, rng)
    build_forum(scene, levels)
    stalls, mese_length = build_mese(scene, levels, rng)
    shore = shoreline(scene)
    moored, scene.harbours = build_harbours(scene, rng)
    wall_count = build_walls(scene, shore)
    open_water = build_open_water_ships(scene, rng)
    print("MONUMENTS", round(time.perf_counter() - started, 1), flush=True)
    points = viewpoints(scene, levels, hippo_marks)
    eyes = [eye for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    targets = [target for key, (_, target) in points.items() if key != "vue-d-ensemble"]
    city_counts, smoke_spots, tree_spots = build_city(scene, rng, [e.to_2d() for e in eyes])
    far_counts = build_far_city(scene, far, rng)
    tree_counts = build_trees(scene, rng, tree_spots, palace_trees)
    ship_counts = place_ships(scene, moored, open_water)
    print("CITY", round(time.perf_counter() - started, 1), flush=True)
    scene.flush(shadowless=("sol", "beams", "jardins"))
    for name, obj in scene.statics.items():
        if name.startswith("beams"):
            obj.visible_shadow = False
    place_markers(scene, points)
    walkable = [obj for name, obj in scene.statics.items() if name.startswith(("sol", "sophia", "augusteon", "forum"))]
    walkable.append(scene.terrain_object)
    scene.surface = Surface(walkable)
    standing = [obj for name, obj in scene.statics.items() if name.startswith(("sol", "augusteon", "sophia", "hippodrome",
                                                                                 "forum", "ports", "jardins"))]
    standing.append(scene.terrain_object)
    scene.standing = Surface(standing)
    route_counts, samples, problems = place_routes(scene, levels, hippo_marks, eyes)
    life_count = build_life(scene, rng, levels, hippo_marks, samples, eyes, targets, stalls)
    crowd_counts = hippodrome_crowds(scene, levels, hippo_marks)
    ground_placements(scene)
    life_counts = place_life(scene)
    smoke_count, flock_count = atmosphere(scene, smoke_spots, levels, rng)
    weathering(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "constantinople.glb")
    export_seconds = export_glb(glb, roots)
    report = {"sun": [SUN_AZIMUTH, SUN_ELEVATION], "levels": {k: round(v, 2) for k, v in levels.items() if isinstance(v, float)},
              "routes": route_counts, "route_problems": problems, "city": city_counts, "far_city": far_counts,
              "trees": tree_counts, "ships": ship_counts, "walls": wall_count, "life": life_counts, "crowds": crowd_counts,
              "street_figures": life_count, "smoke": smoke_count, "flocks": flock_count, "mese_length": round(mese_length, 1),
              "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
              "elevation_source": [ter.DEM_URL.format(tile) for tile in ter.DEM_TILES], "elevation_licence": ter.DEM_LICENCE,
              "texture_credits": credits,
              "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]] for key, (eye, target) in points.items()},
              "interior_center": [round(v, 2) for v in scene.interior]}
    views = dict(points)
    views["interieur"] = (scene.interior + Vector((0.0, 0.0, 1.7)) + Vector((*HS.u * -20.0, 0.0)),
                          scene.interior + Vector((*HS.u * 24.0, 16.0)))
    column_eye = AUG.world(-75.0, -35.0)
    views["colonne"] = (Vector((column_eye.x, column_eye.y, levels["augusteon"] + 12.0)), scene.statue_top - Vector((0, 0, 12.0)))
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)] for key, (eye, target) in views.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("BUILD", round(time.perf_counter() - started, 1), flush=True)
    report["previews"] = render_previews(options, views)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("glb_bytes", "previews", "total_seconds", "routes")}), flush=True)


if __name__ == "__main__":
    main()

import json
import math
import os
import random
import sys
import time
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from kit import alexandrie_monuments as amon
from kit import halicarnasse_city as city
from kit import halicarnasse_houses as houses
from kit import halicarnasse_life as life
from kit import halicarnasse_mausoleum as maus
from kit import halicarnasse_terrain as ter
from kit import halicarnasse_theatre as theatre
from kit.colisee_monuments import simple_column, temple, unit_column
from kit.colisee_terrain import graded_profile, road_blend
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.halicarnasse_materials import build_library, remap
from kit.materials import baked_material, save_pixels
from kit.pantheon_city import cypress_tree, stone_pine
from kit.pantheon_materials import weather
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, haze_volume, render_still, sun_lamp
from kit.terrain import HeightField, grid_mesh, point_in_polygon, polygon_mask, polyline_distance, remove_faces_inside, value_noise

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "halicarnasse")
BLEND = os.path.join(CACHE, "work", "halicarnasse.blend")
SUN_AZIMUTH = 255.0
SUN_ELEVATION = 17.0
SUN_COLOUR = (1.0, 0.80, 0.56)
NEAR_HALF = 1700.0
NEAR_SPACING = 10.0
FAR_HALF = 26000.0
FAR_SPACING = 200.0
TERRACE = (-121.0, 121.0, -56.0, 49.0)
STREET_WIDTH = 15.0
STREET_ROAD = 9.0
AGORA = (-125.0, 15.0, 110.0, 172.0)
THEATRE_DIRECTION = Vector((0.36, -0.93)).normalized()
DETAIL_RADIUS = 380.0
BLOCK_U = 46.0
BLOCK_V = 34.0
STREET = 6.0
EYE_CLEARANCE = 2.4
COLUMN_KEYS = {"simple": lambda: simple_column()(), "ionic": lambda: unit_column("ionic")(),
               "doric_half": theatre.doric_half}
WALL_LINE = [(-430.0, -575.0), (-560.0, -330.0), (-760.0, -60.0), (-930.0, 230.0), (-1150.0, 520.0), (-1020.0, 820.0),
             (-760.0, 1110.0), (-420.0, 1230.0), (-60.0, 1180.0), (240.0, 1010.0), (430.0, 640.0), (520.0, 260.0),
             (560.0, -150.0)]
MYNDOS = (-1150.0, 520.0)


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 16}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def geo(latitude, longitude):
    return Vector(ter.local(latitude, longitude))


MAUSOLEUM = geo(37.0378, 27.4242)
THEATRE = geo(37.0404, 27.4218)
ARES = geo(37.0445, 27.4215)
STREET_Y = MAUSOLEUM.y + TERRACE[3] + 16.0


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def mix(a, b, w):
    w = np.clip(w, 0.0, 1.0)[..., None]
    return a * (1 - w) + b * w


def rect(cx, cy, x0, x1, y0, y1):
    return [(cx + x0, cy + y0), (cx + x1, cy + y0), (cx + x1, cy + y1), (cx + x0, cy + y1)]


def rotated_rect(centre, angle, hx, hy):
    c, s = math.cos(angle), math.sin(angle)
    return [(centre[0] + c * u - s * v, centre[1] + s * u + c * v) for u, v in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


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
    return float(np.quantile(field.sample(gx[inside], gy[inside]), quantile))


def flatten_polygon(gx, gy, heights, polygon, level, margin):
    inside = polygon_mask(polygon, gx, gy)
    distance = polyline_distance(list(polygon) + [polygon[0]], gx, gy)
    weight = np.where(inside, 1.0, np.clip(1.0 - distance / max(margin, 1e-3), 0.0, 1.0))
    weight = weight * weight * (3 - 2 * weight)
    return heights * (1 - weight) + level * weight


class Scene:
    def __init__(self, tiles, field):
        self.tiles = tiles
        self.field = field
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Halicarnasse")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.builds = {}
        self.statics = {}
        self.blocked = []
        self.obstacles = []
        self.columns = {}
        self.ship_spots = []
        self.surface = None
        self.standing = None

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.field.sample(x, y))

    def lowest(self, x, y, radius):
        return min(self.ground(x + dx * radius, y + dy * radius) for dx, dy in
                   ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7)))

    def unique(self, group, builder, matrix=None):
        self.pending.setdefault(group, []).append((remap(builder), matrix if matrix is not None else Matrix.Identity(4)))
        self.root(group)

    def flush(self, shadowless=()):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(builder, matrix, keep_local=True)
            name = f"{group}_static"
            self.statics[name] = unique_object(name, merged, self.collection, self.root(group), self.tiles,
                                               cast_shadow=group not in shadowless)
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True, occlusion=False):
        if matrices:
            self.library.place(key, lambda: remap(build()), self.collection, self.root(group), matrices, cast_shadow, occlusion)

    def add(self, key, matrix, build):
        self.placements.setdefault(key, []).append(matrix)
        self.builds.setdefault(key, build)

    def add_columns(self, order, matrix, frames):
        self.columns.setdefault(order, []).extend(matrix @ f for f in frames)

    def block(self, polygon):
        self.blocked.append([tuple(p) for p in polygon])

    def obstacle(self, point, radius):
        self.obstacles.append((Vector((point[0], point[1])), radius))

    def in_house(self, p):
        grid, cell, count = self.houses
        column, row = int((p.x + NEAR_HALF) / cell), int((p.y + NEAR_HALF) / cell)
        return 0 <= column < count and 0 <= row < count and bool(grid[row, column])

    def clear_of(self, p, margin=0.0):
        return all((p - centre).length >= radius + margin for centre, radius in self.obstacles)


def march(scene, start, direction, limit=900.0, below=0.0):
    p = Vector(start)
    d = Vector(direction).normalized()
    for k in range(int(limit / 2.0)):
        q = p + d * k * 2.0
        if scene.ground(q.x, q.y) < below:
            return q
    return None


def land_centroid(field, x0, x1, y0, y1, level=2.0):
    gx, gy = np.meshgrid(np.linspace(x0, x1, 60), np.linspace(y0, y1, 60))
    heights = field.sample(gx, gy)
    mask = heights > level
    return Vector((float(gx[mask].mean()), float(gy[mask].mean())))


def site_plan(field):
    plan = {}
    plan["terrace"] = rect(MAUSOLEUM.x, MAUSOLEUM.y, *TERRACE)
    plan["terrace_level"] = polygon_level(field, plan["terrace"], 0.45)
    agora = rect(0.0, 0.0, AGORA[0], AGORA[1], AGORA[2], AGORA[3])
    plan["agora"] = agora
    plan["agora_level"] = max(polygon_level(field, agora, 0.4), 3.0)
    peninsula = land_centroid(field, 260.0, 520.0, -520.0, -250.0, 3.0)
    plan["palace"] = peninsula
    plan["palace_level"] = polygon_level(field, rotated_rect(peninsula, 0.0, 30.0, 22.0), 0.6)
    plan["ares_level"] = polygon_level(field, rotated_rect(ARES, 0.0, 16.0, 24.0), 0.5)
    plan["theatre_floor"] = float(field.sample(THEATRE.x, THEATRE.y)) - 1.0
    return plan


def carve_theatre(gx, gy, heights, floor):
    d = THEATRE_DIRECTION
    dx = gx - THEATRE.x
    dy = gy - THEATRE.y
    forward = dx * d.x + dy * d.y
    side = np.abs(-dx * d.y + dy * d.x)
    distance = np.hypot(dx, dy)
    rows = np.clip((distance - city.THEATRE_ORCHESTRA - 1.4) / city.THEATRE_DEPTH, 0.0, city.THEATRE_ROWS)
    seats = floor + 0.2 + rows * city.THEATRE_RISE - 0.5
    top = floor + city.theatre_top()
    profile = np.where(distance > city.THEATRE_RADIUS + 1.0, top, seats)
    cavea = (forward < distance * 0.26) | (distance < city.THEATRE_ORCHESTRA + 1.5)
    stage = (forward >= 0.0) & (forward < 34.0) & (side < 30.0)
    target = np.where(cavea, profile, floor - 0.3)
    reach = np.where(cavea, distance - city.THEATRE_RADIUS - 2.0, np.maximum(side - 30.0, forward - 34.0))
    weight = np.clip(1.0 - reach / 14.0, 0.0, 1.0)
    weight = np.where(cavea | stage, np.where(reach < 0.0, 1.0, weight), weight)
    weight = weight * weight * (3 - 2 * weight)
    behind = cavea & (distance > city.THEATRE_RADIUS + 1.0)
    target = np.where(behind, np.maximum(heights, top), target)
    return heights * (1 - weight) + target * weight


def street_points():
    return [Vector((MYNDOS[0] + 30.0, MYNDOS[1] - 40.0)), Vector((-900.0, STREET_Y + 60.0)), Vector((-560.0, STREET_Y)),
            Vector((MAUSOLEUM.x, STREET_Y)), Vector((200.0, STREET_Y)), Vector((420.0, STREET_Y - 30.0))]


def terrain_edits(field, plan):
    heights = field.heights.copy()
    gx, gy = field.grid_x, field.grid_y
    proxy = HeightField(heights, field.half_extent)
    points, profile = graded_profile([tuple(p) for p in street_points()], lambda x, y: float(proxy.sample(x, y)), 0.08, 4.0, 60.0)
    plan["street_points"] = [Vector(p) for p in points]
    plan["street_levels"] = [max(z, 1.6) for z in profile]
    heights = road_blend(gx, gy, heights, [tuple(p) for p in points], [z - 0.25 for z in plan["street_levels"]],
                         STREET_WIDTH / 2 + 1.5, 12.0)
    heights = flatten_polygon(gx, gy, heights, plan["terrace"], plan["terrace_level"] - 0.3, 7.0)
    heights = flatten_polygon(gx, gy, heights, plan["agora"], plan["agora_level"] - 0.3, 10.0)
    heights = flatten_polygon(gx, gy, heights, rotated_rect(plan["palace"], 0.0, 40.0, 30.0), plan["palace_level"] - 0.3, 8.0)
    heights = flatten_polygon(gx, gy, heights, rotated_rect(ARES, 0.0, 19.0, 27.0), plan["ares_level"] - 0.3, 10.0)
    heights = carve_theatre(gx, gy, heights, plan["theatre_floor"])
    field.heights = heights
    return field


def quay_line(field, plan):
    raw = []
    for x in np.arange(-164.0, 252.0, 6.0):
        for k in range(200):
            y = 240.0 - k * 2.0
            if float(field.sample(x, y)) < 0.0:
                raw.append(Vector((x, y)))
                break
    raw = [p for p in raw if p.y > -140.0]
    ys = np.array([p.y for p in raw])
    padded = np.pad(ys, 3, mode="edge")
    median = np.array([np.median(padded[k:k + 7]) for k in range(len(ys))])
    smooth = np.convolve(np.pad(median, 2, mode="edge"), np.ones(5) / 5.0, mode="valid")
    line = [Vector((p.x, float(y) - 1.0)) for p, y in zip(raw, smooth)]
    plan["quay"] = line
    plan["port_eye"] = line[len(line) * 3 // 4] + Vector((0.0, 4.0))
    return line


def apply_quay(field, line):
    heights = field.heights
    gx, gy = field.grid_x, field.grid_y
    inland = [(p.x, p.y + 5.0) for p in line]
    distance = polyline_distance(inland, gx, gy)
    on_land = heights > -0.4
    weight = np.clip(1.0 - (distance - 5.0) / 12.0, 0.0, 1.0) * on_land
    weight = weight * weight * (3 - 2 * weight)
    field.heights = np.where(weight > 0, np.maximum(heights * (1 - weight) + 1.45 * weight, np.minimum(heights, 1.45)), heights)
    return field


def land_colour(xs, ys, heights, slope, sea_distance, urban, paved, seed=3):
    shape = xs.shape
    noise = value_noise(shape, 14, seed)
    fine = value_noise(shape, 90, seed + 1, 3)
    grain = value_noise(shape, 260, seed + 2, 2)
    patches = value_noise(shape, 40, seed + 4, 4)
    straw = np.dstack([0.66 + 0.06 * noise, 0.52 + 0.06 * noise, 0.28 + 0.05 * fine])
    earth = np.dstack([0.58 + 0.06 * grain, 0.40 + 0.05 * grain, 0.24 + 0.04 * grain])
    maquis = np.dstack([0.16 + 0.05 * fine, 0.26 + 0.06 * fine, 0.10 + 0.04 * noise])
    rock = np.dstack([0.66 + 0.05 * fine, 0.60 + 0.05 * fine, 0.50 + 0.04 * fine])
    beaten = np.dstack([0.78 + 0.05 * grain, 0.66 + 0.05 * grain, 0.50 + 0.04 * grain])
    stone = np.dstack([0.90 + 0.04 * grain, 0.86 + 0.04 * grain, 0.78 + 0.03 * grain])
    colour = mix(straw, earth, smoothstep((noise - 0.45) / 0.3) * 0.6)
    colour = mix(colour, maquis, smoothstep((patches - 0.40) / 0.14) * (0.45 + 0.5 * smoothstep((heights - 20.0) / 30.0)))
    colour = mix(colour, rock, smoothstep((slope - 0.38) / 0.3) * 0.5)
    colour = mix(colour, beaten, urban * (0.7 + 0.3 * smoothstep((noise - 0.3) / 0.4)))
    colour = mix(colour, stone, paved)
    sand = np.dstack([0.90 + 0.04 * grain, 0.80 + 0.04 * grain, 0.60 + 0.04 * grain])
    beach = np.maximum(smoothstep(1.0 - (sea_distance - 2.0) / 10.0), smoothstep(1.0 - heights / 1.0)) * (1 - paved)
    colour = mix(colour, sand, beach)
    shallow = np.dstack([0.36 + 0.05 * fine, 0.70 + 0.05 * fine, 0.66 + 0.04 * fine])
    deep = np.array([0.03, 0.16, 0.34])
    under = mix(sand, shallow, smoothstep(-heights / 1.8))
    under = mix(under, np.broadcast_to(deep, shallow.shape), smoothstep((-heights - 2.0) / 14.0))
    colour = np.where((heights < 0.0)[..., None], under, colour)
    return np.clip(colour, 0, 1)


def build_terrain(scene, near, far, to_sea, plan):
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
    wall = [tuple(p) for p in WALL_LINE]
    inside = polygon_mask(wall + [(560.0, -600.0), (-430.0, -600.0)], tx, ty)
    urban = inside * smoothstep((sea_distance - 4.0) / 30.0) * (1 - smoothstep((th - 70.0) / 30.0)) * 0.85
    paved = np.zeros(tx.shape)
    for polygon in (plan["terrace"], plan["agora"]):
        paved = np.maximum(paved, polygon_mask(polygon, tx, ty) * 0.9)
    street = polyline_distance([tuple(p) for p in plan["street_points"]], tx, ty)
    paved = np.maximum(paved, smoothstep((STREET_WIDTH / 2 + 1.0 - street) / 2.0))
    quay = polyline_distance([(p.x, p.y + 5.0) for p in plan["quay"]], tx, ty)
    paved = np.maximum(paved, smoothstep((7.0 - quay) / 2.0) * (th > -0.2))
    colour = land_colour(tx, ty, th, slope, sea_distance, urban, paved)
    shade = 0.84 + 0.16 * smoothstep(1.0 - slope * 1.5)
    colour *= shade[..., None]
    image = save_pixels("terrain_colour", np.clip(colour, 0, 1), os.path.join(CACHE, "textures", "terrain_colour_v2.jpg"), quality=88)
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
    colour = land_colour(tx, ty, th, slope * 1.2, np.full(tx.shape, 100.0), np.zeros(tx.shape), np.zeros(tx.shape), 9)
    colour = np.where((th < 0.2)[..., None], mix(colour, np.broadcast_to(np.array([0.03, 0.15, 0.32]), colour.shape),
                                                 smoothstep(-th / 6.0)), colour)
    image = save_pixels("terrain_far_colour", np.clip(colour, 0, 1), os.path.join(CACHE, "textures", "terrain_far_v2.jpg"), quality=85)
    far_mesh.materials.append(baked_material("terrain_far", image))
    created = new_object("terrain_far", far_mesh, scene.collection, root)
    created["cast_shadow"] = False
    water = MeshBuilder()
    reach = 70000.0
    water.polygon([(-reach, -reach, 0.0), (reach, -reach, 0.0), (reach, reach, 0.0), (-reach, reach, 0.0)], "water")
    unique_object("water", water, scene.collection, root, scene.tiles, cast_shadow=False, ground_occlusion=False)


def plinth(points, z0, z1, material, colour=None):
    builder = MeshBuilder()
    builder.prism([tuple(p) for p in points], z0, z1, material, bottom=False)
    if colour is not None:
        builder.tint(0, colour)
    return builder


def build_mausoleum(scene, plan):
    z = plan["terrace_level"]
    m = MAUSOLEUM
    builder, top = maus.mausoleum()
    scene.unique("mausolee", builder, placement(m.x, m.y, z))
    scene.instances("mausolee", "maus_column", maus.pteron_column, [placement(m.x, m.y, z) @ f for f in maus.column_frames()])
    scene.instances("mausolee", "maus_lion", maus.lion, [placement(m.x, m.y, z) @ f @ Matrix.Scale(1.4, 4) for f in maus.lion_frames()])
    for tier, scale in ((0, 1.6), (1, 2.0)):
        frames = maus.statue_frames(tier, 2.2 if tier == 0 else 2.6, 0.5)
        for index, matrices in frames.items():
            scene.instances("mausolee", f"maus_statue_{tier}_{index}", lambda index=index, scale=scale: maus.statue(index, scale),
                            [placement(m.x, m.y, z) @ f for f in matrices])
    scene.unique("mausolee", maus.quadriga(), placement(m.x, m.y, z + top, math.pi / 2))
    scene.quadriga = Vector((m.x, m.y, z + top + 2.5))
    scene.maus_z = z
    scene.obstacle(m, 24.0)
    x0, x1, y0, y1 = TERRACE
    pave = plinth(rect(m.x, m.y, x0, x1, y0, y1), -0.8, 0.0, "travertine", (0.96, 0.92, 0.84))
    scene.unique("sol", pave, Matrix.Translation((0.0, 0.0, z + 0.02)))
    wall_height = 3.4
    low = min(scene.ground(m.x + x, m.y + y0 - 12.0) for x in np.linspace(x0, x1, 12))
    south = city.terrace_wall(x1 - x0, wall_height, foot=min(low - z - 2.0, -6.0), thickness=2.2)
    scene.unique("terrasse", south, placement(m.x + x0, m.y + y0 - 1.1, z))
    gap = 9.0
    north = city.terrace_wall((x1 - x0) / 2 - gap, wall_height, foot=-4.0)
    scene.unique("terrasse", north, placement(m.x + x0, m.y + y1 + 0.8, z))
    scene.unique("terrasse", north, placement(m.x + gap, m.y + y1 + 0.8, z))
    side = city.terrace_wall(y1 - y0 + 2.0, wall_height, foot=min(low - z - 2.0, -6.0))
    scene.unique("terrasse", side, placement(m.x + x0 - 0.8, m.y + y0 - 1.0, z, math.pi / 2))
    scene.unique("terrasse", side, placement(m.x + x1 + 0.8, m.y + y0 - 1.0, z, math.pi / 2))
    gate, frames = city.propylon(14.0, 8.0, 6.2)
    gate_matrix = placement(m.x, m.y + y1 + 0.8, z)
    scene.unique("terrasse", gate, gate_matrix)
    scene.add_columns("ionic", gate_matrix, frames)
    for dx in (-26.0, 26.0):
        scene.unique("terrasse", city.stele(2.0, 0.8), placement(m.x + dx, m.y + y1 - 4.0, z, math.pi))
        scene.obstacle((m.x + dx, m.y + y1 - 4.0), 1.2)
    rng = random.Random(8)
    for k in range(26):
        side_x = rng.choice([-1, 1])
        x = side_x * rng.uniform(34.0, x1 - 6.0)
        y = rng.choice([y0 + 4.0, y1 - 4.0])
        scene.add("shrub_oleander", placement(m.x + x, m.y + y, z, rng.uniform(0, math.tau), rng.uniform(0.8, 1.2)),
                  lambda: city.oleander(2.0, 3))
        scene.obstacle((m.x + x, m.y + y), 1.6)
    for x in np.arange(x0 + 8.0, x1 - 4.0, 16.0):
        if abs(x) < 30.0:
            continue
        for y in (y0 + 9.0, y1 - 9.0):
            scene.add("tree_cypress", placement(m.x + x, m.y + y, z - 0.1, rng.uniform(0, 6.28)), lambda: cypress_tree(2, 12.0))
            scene.obstacle((m.x + x, m.y + y), 1.4)
    scene.block([(m.x + x0 - 4.0, m.y + y0 - 4.0), (m.x + x1 + 4.0, m.y + y0 - 4.0), (m.x + x1 + 4.0, m.y + y1 + 6.0),
                 (m.x + x0 - 4.0, m.y + y1 + 6.0)])
    return z


def build_street(scene, plan):
    points = plan["street_points"]
    profile = plan["street_levels"]
    ribbon = MeshBuilder()
    half = STREET_WIDTH / 2
    stations = []
    for index, (p, z) in enumerate(zip(points, profile)):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        d = (b - a).normalized()
        stations.append((p, z, Vector((-d.y, d.x))))
    for (p, z, n), (q, z2, n2) in zip(stations[:-1], stations[1:]):
        for lo, hi, material, lift, colour in ((-half, -STREET_ROAD / 2, "travertine", 0.18, (0.98, 0.94, 0.86)),
                                               (-STREET_ROAD / 2, STREET_ROAD / 2, "granite_grey", 0.05, (0.92, 0.88, 0.82)),
                                               (STREET_ROAD / 2, half, "travertine", 0.18, (0.98, 0.94, 0.86))):
            quad = [(*(p + n * lo), z + lift), (*(q + n2 * lo), z2 + lift), (*(q + n2 * hi), z2 + lift), (*(p + n * hi), z + lift)]
            ribbon.oriented(quad, (0, 0, 1), material)
            ribbon.tint(len(ribbon.polygons) - 1, colour)
        for side in (1, -1):
            a, b = p + n * side * half, q + n2 * side * half
            ribbon.oriented([(a.x, a.y, z - 1.2), (b.x, b.y, z2 - 1.2), (b.x, b.y, z2 + 0.18), (a.x, a.y, z + 0.18)],
                            (n.x * side, n.y * side, 0.0), "travertine")
            a, b = p + n * side * STREET_ROAD / 2, q + n2 * side * STREET_ROAD / 2
            ribbon.oriented([(a.x, a.y, z + 0.05), (b.x, b.y, z2 + 0.05), (b.x, b.y, z2 + 0.18), (a.x, a.y, z + 0.18)],
                            (-n.x * side, -n.y * side, 0.0), "travertine")
    scene.unique("sol", ribbon)
    for a, b in zip(points[:-1], points[1:]):
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        scene.block([tuple(a - n * (half + 1.5)), tuple(b - n * (half + 1.5)), tuple(b + n * (half + 1.5)), tuple(a + n * (half + 1.5))])
    gate_dir = (points[1] - points[0]).normalized()
    gate_z = min(scene.ground(*points[0]), profile[0])
    scene.unique("murailles", city.city_gate(), placement(points[0].x, points[0].y, gate_z - 0.2,
                                                          math.atan2(-gate_dir.x, gate_dir.y)))


def build_agora(scene, plan):
    z = plan["agora_level"]
    x0, x1, y0, y1 = AGORA
    pave = plinth(rect(0.0, 0.0, x0, x1, y0, y1), -1.0, 0.0, "travertine", (0.94, 0.90, 0.82))
    scene.unique("sol", pave, Matrix.Translation((0.0, 0.0, z + 0.02)))
    stoa, frames = amon.emporion_stoa(x1 - x0 - 4.0, 12.0, 7.0, 4)
    matrix = placement((x0 + x1) / 2, y1 - 12.5, z)
    scene.unique("agora", stoa, matrix)
    scene.add_columns("simple", matrix, frames)
    side, frames = amon.emporion_stoa(y1 - y0 - 18.0, 9.0, 6.0, 9)
    matrix = placement(x0 + 0.5, (y0 + y1) / 2 - 6.0, z, -math.pi / 2)
    for y in np.arange(y0 + 3.0, y1 - 14.0, 4.0):
        scene.obstacle((x0 + 5.0, y), 4.6)
    scene.unique("agora", side, matrix)
    scene.add_columns("simple", matrix, frames)
    scene.unique("agora", city.stele(2.6, 1.0), placement(x1 - 22.0, y1 - 16.0, z, 0.0))
    scene.obstacle((x1 - 22.0, y1 - 16.0), 1.4)
    scene.unique("agora", city.stele(2.2, 0.8), placement(x0 + 30.0, y1 - 16.0, z, 0.0))
    scene.obstacle((x0 + 30.0, y1 - 16.0), 1.4)
    rng = random.Random(21)
    stall_spots = []
    for row in range(2):
        for k in range(7):
            x = x0 + 22.0 + k * 13.0 + rng.uniform(-1.5, 1.5)
            y = y0 + 16.0 + row * 14.0 + rng.uniform(-1.0, 1.0)
            key = rng.choice(["prop_awning_a", "prop_awning_b", "prop_awning_c"])
            stall_spots.append((Vector((x, y)), key))
            scene.obstacle((x, y), 3.4)
    colours = {"prop_awning_a": ((0.86, 0.20, 0.14), (0.96, 0.84, 0.50)), "prop_awning_b": ((0.18, 0.36, 0.70), (0.96, 0.94, 0.88)),
               "prop_awning_c": ((0.92, 0.66, 0.18), (0.34, 0.56, 0.30))}
    for p, key in stall_spots:
        scene.add(key, placement(p.x, p.y, z, rng.choice([0.0, math.pi]) + rng.uniform(-0.1, 0.1)),
                  lambda key=key: city.awning(5.0, 3.6, colours[key]))
    scene.block(rect(0.0, 0.0, x0 - 4.0, x1 + 4.0, y0 - 2.0, y1 + 4.0))
    return z


def build_quays(scene, plan, rng):
    line = plan["quay"]
    segments = 0
    for a, b in zip(line[:-1], line[1:]):
        length = (b - a).length
        if length < 0.5 or length > 30.0:
            continue
        d = (b - a).normalized()
        turn = math.atan2(d.y, d.x)
        builder = city.quay(length + 0.4, 9.0, 1.5, -5.0)
        scene.unique("port", builder, placement(b.x + d.x * 0.2, b.y + d.y * 0.2, 0.0, turn + math.pi))
        segments += 1
    for k, x in enumerate(np.arange(line[0].x + 30.0, line[-1].x - 30.0, 42.0)):
        hit = march(scene, (x, 240.0), (0.0, -1.0), 400.0, 0.0)
        if hit is None:
            continue
        spot = hit + Vector((0.0, 22.0))
        z = scene.ground(spot.x, spot.y)
        if AGORA[0] - 24.0 < spot.x < AGORA[1] + 24.0:
            continue
        scene.unique("port", amon.warehouse(34.0, 12.0, 7.0, k), placement(spot.x, spot.y, z - 0.2, 0.0))
        scene.block(rotated_rect(spot, 0.0, 19.0, 8.0))
    return segments


def build_harbour_ships(scene, plan, rng):
    out = []
    line = plan["quay"]
    for p in line[4:-4:7]:
        spot = p + Vector((rng.uniform(-2.0, 2.0), -rng.uniform(6.5, 8.0)))
        if scene.ground(spot.x, spot.y) > -1.2 or (spot - plan["port_eye"]).length < 16.0 or not ship_room(scene, spot, 13.0):
            continue
        key = rng.choice(["ship_merchant", "ship_merchant_b", "ship_merchant", "ship_fishing", "ship_freighter"])
        out.append((key, placement(spot.x, spot.y, 0.0, math.pi / 2 * rng.choice([1, -1]) + rng.uniform(-0.08, 0.08))))
    for k in range(40):
        spot = Vector((rng.uniform(-200.0, 280.0), rng.uniform(-560.0, -60.0)))
        if scene.ground(spot.x, spot.y) > -3.0 or (spot - plan["port_eye"]).length < 45.0 or not ship_room(scene, spot, 36.0):
            continue
        key = rng.choice(["ship_merchant", "ship_freighter", "ship_fishing", "ship_merchant_b", "ship_fishing_sail"])
        out.append((key, placement(spot.x, spot.y, 0.0, rng.uniform(0, math.tau))))
    palace = plan["palace"]
    for k, dy in enumerate((22.0, -14.0)):
        hit = march(scene, palace + Vector((0.0, dy)), (-1.0, 0.0), 300.0, -2.5)
        spot = hit + Vector((-8.0, 0.0)) if hit is not None else None
        if spot is not None and ship_room(scene, spot, 24.0):
            out.append(("ship_galley", placement(spot.x, spot.y, 0.0, 0.05 * k)))
    for spot, heading in ((Vector((-200.0, -1500.0)), 0.6), (Vector((600.0, -2100.0)), -0.4), (Vector((-900.0, -2600.0)), 1.2),
                          (Vector((180.0, -900.0)), 0.2), (Vector((1500.0, -1300.0)), -1.0)):
        if scene.ground(spot.x, spot.y) < -4.0:
            out.append((rng.choice(["ship_merchant_set", "ship_freighter_set", "ship_fishing_sail"]),
                        placement(spot.x, spot.y, 0.0, heading)))
    return out


def ship_room(scene, spot, distance):
    if any((spot - other).length < distance for other in scene.ship_spots):
        return False
    scene.ship_spots.append(spot)
    return True


def build_palace(scene, plan):
    centre = plan["palace"]
    z = plan["palace_level"]
    builder, frames = city.palace()
    matrix = placement(centre.x, centre.y, z)
    scene.unique("palais", builder, matrix)
    scene.add_columns("simple", matrix, frames)
    scene.block(rotated_rect(centre, 0.0, 42.0, 32.0))
    return z


def build_theatre(scene, plan):
    floor = plan["theatre_floor"]
    d = THEATRE_DIRECTION
    turn = math.atan2(-d.x, d.y)
    builder, frames = city.greek_theatre()
    matrix = placement(THEATRE.x, THEATRE.y, floor, turn)
    scene.unique("theatre", builder, matrix)
    scene.add_columns("doric_half", matrix, frames)
    scene.theatre_matrix = matrix
    scene.block([tuple(THEATRE + Vector((math.cos(a), math.sin(a))) * (city.THEATRE_RADIUS + 6.0)) for a in np.linspace(0, math.tau, 24)])
    scene.block([tuple(matrix @ Vector((x, y, 0.0)))[:2] for x, y in ((-26.0, 0.0), (26.0, 0.0), (26.0, 26.0), (-26.0, 26.0))])
    return floor


def build_sanctuaries(scene, plan):
    z = plan["ares_level"]
    builder = MeshBuilder()
    city.temple_terrace(builder, 18.0, 26.0, 0.0)
    scene.unique("sanctuaires", builder, placement(ARES.x, ARES.y, z))
    temple_builder, frames = temple(13.0, 24.0, 2.4, 8.6, 0.86, 6, "ionic")
    matrix = placement(ARES.x, ARES.y, z, math.pi)
    scene.unique("sanctuaires", temple_builder, matrix)
    scene.add_columns("ionic", matrix, frames.get("ionic", []))
    scene.block(rotated_rect(ARES, 0.0, 22.0, 30.0))
    start = Vector((-520.0, -420.0))
    shore = march(scene, start, (1.0, 0.0), 500.0, 0.0)
    if shore is None:
        shore = Vector((-340.0, -420.0))
    spot = shore - Vector((12.0, 0.0))
    fz = max(scene.ground(spot.x, spot.y), 1.6)
    house, frames = city.fountain_house()
    matrix = placement(spot.x, spot.y, fz, math.pi / 2)
    scene.unique("sanctuaires", house, matrix)
    scene.add_columns("simple", matrix, frames)
    scene.salmacis = Vector((spot.x, spot.y, fz))
    scene.obstacle(spot + Vector((-1.5, 0.0)), 8.5)
    scene.block(rotated_rect(spot, 0.0, 12.0, 10.0))
    shrine_spot = spot + Vector((-40.0, 14.0))
    sz = scene.ground(shrine_spot.x, shrine_spot.y)
    base = MeshBuilder()
    city.temple_terrace(base, 8.0, 12.0, 0.0)
    scene.unique("sanctuaires", base, placement(shrine_spot.x, shrine_spot.y, sz + 0.6))
    shrine, frames = temple(8.0, 13.0, 1.4, 5.6, 0.56, 4, "ionic")
    matrix = placement(shrine_spot.x, shrine_spot.y, sz + 0.6, -math.pi / 2)
    scene.unique("sanctuaires", shrine, matrix)
    scene.add_columns("ionic", matrix, frames.get("ionic", []))
    scene.block(rotated_rect(shrine_spot, 0.0, 12.0, 14.0))
    plan["salmacis"] = scene.salmacis
    plan["shrine"] = Vector((shrine_spot.x, shrine_spot.y, sz + 0.6))


def build_walls(scene):
    pieces = []
    towers = []
    count = 0
    for a, b in zip(WALL_LINE[:-1], WALL_LINE[1:]):
        a, b = Vector(a), Vector(b)
        length = (b - a).length
        steps = max(int(length / 12.0), 1)
        d = (b - a).normalized()
        turn = math.atan2(d.y, d.x)
        for k in range(steps):
            p = a + d * (length * k / steps)
            q = a + d * (length * (k + 1) / steps)
            if (p - Vector(MYNDOS)).length < 14.0 or (q - Vector(MYNDOS)).length < 14.0:
                continue
            z0, z1 = scene.ground(p.x, p.y), scene.ground(q.x, q.y)
            if max(z0, z1) < 0.5:
                continue
            z = min(z0, z1)
            pieces.append(placement(p.x, p.y, z, turn, ((q - p).length / 12.0 + 0.02, 1.0, 1.0)))
            count += 1
            if count % 9 == 0:
                towers.append(placement(p.x, p.y, min(z0, scene.lowest(p.x, p.y, 5.0)), turn))
    scene.instances("murailles", "wall_run", lambda: city.wall_run(12.0), pieces, True, False)
    scene.instances("murailles", "wall_tower", lambda: city.wall_tower(), towers, True, False)
    return len(pieces), len(towers)


def occupancy(scene):
    cell = 2.0
    count = int(2 * NEAR_HALF / cell)
    axis = -NEAR_HALF + (np.arange(count) + 0.5) * cell
    gx, gy = np.meshgrid(axis, axis)
    blocked = scene.field.sample(gx, gy) < 1.6
    inside = polygon_mask([tuple(p) for p in WALL_LINE] + [(560.0, -600.0), (-430.0, -600.0)], gx, gy)
    blocked |= ~inside
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
    blocked |= np.hypot(gx_, gy_) > 0.5
    return blocked, cell, count


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
    blocked, cell, count = occupancy(scene)
    scene.houses = (np.zeros_like(blocked), cell, count)
    templates = list(houses.HOUSES)
    weights = [3, 2, 3, 2, 1, 2, 2, 3]
    simple = list(houses.FAR_HOUSES)
    placed = {key: [] for key in templates + simple}
    footprints = houses.FOOTPRINTS
    smoke_spots = []
    tree_spots = []
    centre = Vector((MAUSOLEUM.x, MAUSOLEUM.y - 100.0))

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
        if min((Vector((x, y)) - e).length for e in eyes) < 22.0:
            return False
        corners = [(x + c * u - s_ * v, y + s_ * u + c * v) for u, v in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
        heights = [scene.ground(cx, cy) for cx, cy in corners + [(x, y)] +
                   [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(corners, corners[1:] + corners[:1])]]
        if max(heights) - min(heights) > 3.6:
            return False
        z = max(heights) - 0.15
        placed[key].append(placement(x, y, z, angle))
        mark(blocked, cell, count, inset)
        mark(scene.houses[0], cell, count, corners)
        if rng.random() < 0.025:
            smoke_spots.append(Vector((x, y, z + 9.0)))
        return True

    angle = 0.0
    axis_u = Vector((1.0, 0.0))
    axis_v = Vector((0.0, 1.0))
    reach = NEAR_HALF
    for bu in np.arange(-reach, reach, BLOCK_U + STREET):
        for bv in np.arange(-reach, reach, BLOCK_V + STREET):
            middle = axis_u * (bu + BLOCK_U / 2) + axis_v * (bv + BLOCK_V / 2)
            if max(abs(middle.x), abs(middle.y)) > NEAR_HALF - 40.0:
                continue
            detailed = (middle - centre).length < DETAIL_RADIUS or min((middle - e).length for e in eyes) < 200.0
            if rng.random() < 0.06:
                for k in range(rng.randint(3, 6)):
                    p = middle + axis_u * rng.uniform(-18, 18) + axis_v * rng.uniform(-12, 12)
                    if scene.ground(p.x, p.y) > 2.0 and free_spot([(p.x, p.y)]):
                        tree_spots.append(p)
                continue
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
                    turn = math.atan2(outward.x, -outward.y)
                    if house(point.x, point.y, turn, key):
                        position += w + (rng.uniform(1.5, 3.0) if rng.random() < 0.2 else 0.0)
                    else:
                        position += 3.0
            for k in range(rng.randint(0, 3)):
                p = middle + axis_u * rng.uniform(-12, 12) + axis_v * rng.uniform(-6, 6)
                if scene.ground(p.x, p.y) > 2.0 and free_spot([(p.x, p.y)]):
                    tree_spots.append(p)
    builds = dict(houses.HOUSES, **houses.FAR_HOUSES)
    for key, matrices in placed.items():
        scene.instances("ville", key, builds[key], matrices, key in houses.HOUSES, True)
    return {key: len(m) for key, m in placed.items()}, smoke_spots, tree_spots


TREES = {
    "tree_olive": lambda: city.olive(1, 5.5),
    "tree_olive_b": lambda: city.olive(4, 4.6),
    "tree_olive_far": lambda: city.olive(9, 5.0, False),
    "tree_cypress": lambda: cypress_tree(2, 12.0),
    "tree_pine": lambda: stone_pine(1, 13.0),
    "tree_pine_b": lambda: stone_pine(5, 10.0),
    "shrub_maquis": lambda: city.maquis(2, 1.6),
    "shrub_maquis_far": lambda: city.maquis(11, 2.0, False),
}


def build_vegetation(scene, rng, spots, eyes, attempts=2600):
    placed = {key: [] for key in TREES}
    for p in spots:
        if rng.random() < 0.45:
            continue
        key = rng.choices(["tree_olive", "tree_olive_b", "tree_cypress", "tree_pine"], [2, 2, 4, 2])[0]
        placed[key].append(placement(p.x, p.y, scene.lowest(p.x, p.y, 1.0) - 0.25, rng.uniform(0, math.tau), rng.uniform(0.85, 1.15)))
    wall = [tuple(p) for p in WALL_LINE] + [(560.0, -600.0), (-430.0, -600.0)]
    blocked = scene.blocked

    def clear(p):
        return not any(point_in_polygon(p.x, p.y, polygon) for polygon in blocked)

    def put(key, q, sink=0.3, low=0.85, high=1.15):
        placed[key].append(placement(q.x, q.y, scene.lowest(q.x, q.y, 1.2) - sink, rng.uniform(0, math.tau), rng.uniform(low, high)))
    for attempt in range(attempts):
        p = Vector((rng.uniform(-NEAR_HALF + 30.0, NEAR_HALF - 30.0), rng.uniform(-NEAR_HALF + 30.0, NEAR_HALF - 30.0)))
        z = scene.ground(p.x, p.y)
        if z < 2.5:
            continue
        if point_in_polygon(p.x, p.y, wall) and rng.random() < 0.8:
            continue
        if not clear(p) or min((p - e).length for e in eyes) < 6.0:
            continue
        near = (p - MAUSOLEUM.to_2d()).length < 400.0
        slope = abs(scene.ground(p.x + 3.0, p.y) - scene.ground(p.x - 3.0, p.y)) + abs(scene.ground(p.x, p.y + 3.0) - scene.ground(p.x, p.y - 3.0))
        roll = rng.random()
        if z < 50.0 and slope < 3.0 and roll < 0.35:
            grove = rng.choice(["tree_olive", "tree_olive_b"]) if near else "tree_olive_far"
            for i in range(2):
                for j in range(2):
                    q = p + Vector((i * 9.0 + rng.uniform(-1.5, 1.5), j * 9.0 + rng.uniform(-1.5, 1.5)))
                    if scene.ground(q.x, q.y) > 2.5 and clear(q):
                        put(grove, q, 0.25, 0.85, 1.1)
        elif roll < 0.47:
            put(rng.choice(["tree_pine", "tree_pine_b"]), p, 0.3, 0.8, 1.2)
        elif roll < 0.55:
            put("tree_cypress", p, 0.3, 0.8, 1.15)
        else:
            for k in range(rng.randint(2, 5)):
                q = p + Vector((rng.uniform(-10.0, 10.0), rng.uniform(-10.0, 10.0)))
                if scene.ground(q.x, q.y) > 2.0 and clear(q):
                    put("shrub_maquis" if near else "shrub_maquis_far", q, 0.3, 0.7, 1.3)
    for key, matrices in placed.items():
        scene.instances("vegetation", key, TREES[key], matrices, not key.startswith("shrub"), False)
    return {key: len(m) for key, m in placed.items()}


def viewpoints(scene, plan):
    points = {}
    m = MAUSOLEUM
    z = scene.maus_z
    points["vue-d-ensemble"] = (Vector((-60.0, -720.0, 95.0)), Vector((-160.0, 330.0, 22.0)))
    points["le-mausolee"] = (Vector((m.x - 56.0, m.y + 36.0, z + 1.7)), Vector((m.x - 6.0, m.y + 4.0, z + 18.0)))
    points["le-quadrige"] = (Vector((m.x + 14.0, m.y + 18.0, z + 43.5)), scene.quadriga + Vector((-1.5, 0.0, 0.8)))
    salmacis = plan["salmacis"]
    eye = Vector((salmacis.x + 60.0, salmacis.y - 80.0))
    while scene.ground(eye.x, eye.y) > -3.0:
        eye.x += 2.0
    towards = Vector((m.x, m.y)) - eye
    fountain = salmacis.to_2d() - eye
    axis = (towards.normalized() + fountain.normalized()).normalized()
    points["le-port"] = (Vector((eye.x, eye.y, 9.0)), Vector((eye.x + axis.x * 400.0, eye.y + axis.y * 400.0, 3.0)))
    top = scene.theatre_matrix @ Vector((-6.0, -(city.THEATRE_RADIUS - 1.0), city.theatre_top() + 1.8))
    points["le-theatre"] = (top, Vector((m.x, m.y, z + 12.0)))
    return points


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))


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
        self.tree = BVHTree.FromPolygons(np.concatenate(vertices).tolist(), np.concatenate(triangles).tolist(), all_triangles=True)

    def height(self, x, y, hint, reach=3.0):
        hit = self.tree.ray_cast(Vector((x, y, hint + reach)), Vector((0.0, 0.0, -1.0)), reach + 8.0)
        return hint if hit[0] is None else hit[0].z


def ground_route(scene, points, spacing=2.0):
    chain = []
    for p in dense([Vector((p.x, p.y)) for p in points], spacing):
        hint = max(scene.ground(p.x, p.y), 1.5)
        chain.append(Vector((p.x, p.y, scene.surface.height(p.x, p.y, hint, 4.0))))
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


def routes(scene, plan):
    m = MAUSOLEUM
    x0, x1, y0, y1 = TERRACE
    street = plan["street_points"]
    i0, i1 = len(street) // 5, len(street) * 4 // 5

    def offset(i, distance):
        d = (street[min(i + 1, len(street) - 1)] - street[max(i - 1, 0)]).normalized()
        return street[i] + Vector((-d.y, d.x)) * distance
    quay = plan["quay"]
    return {
        "terrasse-sud": [m + Vector((-90.0, y0 + 16.0)), m + Vector((90.0, y0 + 16.0))],
        "terrasse-ouest": [m + Vector((-78.0, y0 + 12.0)), m + Vector((-78.0, y1 - 14.0))],
        "terrasse-nord": [m + Vector((80.0, y1 - 16.0)), m + Vector((-80.0, y1 - 16.0))],
        "grande-rue": [offset(i, 2.5) for i in range(i0, i1)],
        "grande-rue-retour": [offset(i, -2.8) for i in reversed(range(i0, i1))],
        "quai-ouest": [p + Vector((0.0, 4.5)) for p in quay[3:len(quay) * 3 // 4 - 2]],
        "quai-est": [p + Vector((0.0, 4.5)) for p in quay[len(quay) * 3 // 4 + 2:-3]],
        "agora": [Vector((AGORA[0] + 16.0, AGORA[2] + 8.0)), Vector((AGORA[1] - 10.0, AGORA[2] + 8.0))],
    }


def place_routes(scene, plan, eyes):
    root = scene.root("life")
    counts = {}
    samples = []
    problems = []
    for name, points in routes(scene, plan).items():
        chain = ground_route(scene, points)
        problems += route_problems(name, chain)
        problems += [f"{name} crosses an obstacle at {p.x:.1f},{p.y:.1f}" for p in chain if not scene.clear_of(p.to_2d(), 0.4)]
        problems += [f"{name} crosses a house at {p.x:.1f},{p.y:.1f}" for p in chain if scene.in_house(p)]
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


CROWD = [("fig_greek", 3.0), ("fig_greek_b", 3.0), ("fig_greek_c", 2.0), ("fig_lady", 2.5), ("fig_lady_b", 1.5),
         ("fig_lady_c", 2.0), ("fig_roman", 0.8), ("fig_child", 1.0)]
HARBOUR = [("fig_docker", 3.0), ("fig_sack", 2.0), ("fig_sailor", 3.0), ("fig_greek", 1.0), ("fig_greek_c", 1.0)]


def pick(rng, weights):
    total = sum(w for _, w in weights)
    roll = rng.random() * total
    for key, w in weights:
        roll -= w
        if roll <= 0:
            return key
    return weights[-1][0]


def build_life(scene, rng, plan, samples, eyes, targets):
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
            if (p - (eye + span * t)).length < 2.2 and (p - eye).length < 26.0:
                return False
        return all((p - e.to_2d()).length > 2.6 for e in eyes) and scene.clear_of(p, radius * 0.5)

    def put(p, turn, key, build=None, radius=0.6):
        scene.add(key, placement(p.x, p.y, 0.0, turn), build or life.FIGURES.get(key) or life.GROUPS[key])
        scene.obstacle(p, radius)

    m = MAUSOLEUM
    x0, x1, y0, y1 = TERRACE
    placed = 0
    for key, offset in (("group_guide", Vector((-34.0, 20.0))), ("group_guide_b", Vector((26.0, -27.0))),
                        ("group_guide", Vector((-12.0, 26.0)))):
        p = m + offset
        towards = m - p
        if free(p, 2.5):
            put(p, math.atan2(-towards.x, towards.y) + math.pi, key, radius=2.6)
    p = m + Vector((-70.0, 14.0))
    if free(p, 3.0):
        put(p, -math.pi / 2, "group_escort", radius=3.5)
    for k in range(120):
        p = m + Vector((rng.uniform(x0 + 6.0, x1 - 6.0), rng.uniform(y0 + 6.0, y1 - 6.0)))
        if abs(p.x - m.x) < 24.0 and abs(p.y - m.y) < 21.0:
            continue
        if free(p):
            towards = m - p
            put(p, math.atan2(-towards.x, towards.y) + rng.gauss(0, 0.8), pick(rng, CROWD))
            placed += 1
    for k in range(5):
        p = m + Vector((rng.uniform(x0 + 10.0, x1 - 10.0), rng.uniform(y0 + 8.0, y1 - 8.0)))
        if (abs(p.x - m.x) > 26.0 or abs(p.y - m.y) > 23.0) and free(p, 1.6):
            put(p, rng.uniform(0, math.tau), rng.choice(["group_talk", "group_talk_b"]), radius=1.6)
    street = plan["street_points"]
    for k in range(120):
        index = rng.randrange(len(street) - 1)
        a, b = street[index], street[index + 1]
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        p = a.lerp(b, rng.random()) + n * rng.uniform(-STREET_WIDTH / 2 + 0.8, STREET_WIDTH / 2 - 0.8)
        if free(p):
            put(p, math.atan2(-d.x, d.y) + (math.pi if rng.random() < 0.5 else 0.0) + rng.gauss(0, 0.3), pick(rng, CROWD))
            placed += 1
    for k in range(8):
        index = rng.randrange(len(street) - 1)
        a, b = street[index], street[index + 1]
        d = (b - a).normalized()
        p = a.lerp(b, rng.random()) + Vector((-d.y, d.x)) * rng.uniform(-1.0, 1.0)
        if free(p, 2.2):
            put(p, math.atan2(-d.x, d.y) + (math.pi if k % 2 else 0.0), rng.choice(["prop_mule", "prop_donkey"]), radius=1.6)
    ax0, ax1, ay0, ay1 = AGORA
    for k in range(80):
        p = Vector((rng.uniform(ax0 + 4.0, ax1 - 4.0), rng.uniform(ay0 + 4.0, ay1 - 16.0)))
        if free(p):
            put(p, rng.uniform(0, math.tau), pick(rng, CROWD))
            placed += 1
    for k in range(6):
        p = Vector((rng.uniform(ax0 + 6.0, ax1 - 6.0), rng.uniform(ay0 + 6.0, ay1 - 18.0)))
        if free(p, 1.5):
            put(p, rng.uniform(0, math.tau), rng.choice(["group_market", "group_talk"]), radius=1.6)
    quay = plan["quay"]
    for k in range(110):
        a = quay[rng.randrange(len(quay))]
        p = a + Vector((rng.uniform(-3.0, 3.0), rng.uniform(1.5, 8.5)))
        if scene.ground(p.x, p.y) < 1.0 or not free(p):
            continue
        put(p, rng.uniform(0, math.tau), pick(rng, HARBOUR))
        placed += 1
    for k in range(10):
        a = quay[rng.randrange(len(quay))]
        p = a + Vector((rng.uniform(-3.0, 3.0), rng.uniform(3.0, 7.0)))
        if scene.ground(p.x, p.y) > 1.0 and free(p, 2.0):
            key = rng.choice(["group_dock", "group_porters", "prop_amphorae", "prop_sacks", "prop_amphorae"])
            put(p, rng.choice([0.0, math.pi]) + rng.uniform(-0.3, 0.3), key, radius=2.0)
    salmacis = plan["salmacis"]
    for k in range(16):
        p = salmacis.to_2d() + Vector((rng.uniform(5.5, 10.0), rng.uniform(-9.0, 9.0)))
        if scene.ground(p.x, p.y) > 1.0 and free(p):
            put(p, rng.uniform(0, math.tau), pick(rng, CROWD))
    p = salmacis.to_2d() + Vector((6.0, 14.0))
    if scene.ground(p.x, p.y) > 0.8 and free(p, 1.8):
        put(p, 0.0, "group_fishers", radius=1.8)
    shrine = plan["shrine"].to_2d()
    for k in range(6):
        p = shrine + Vector((rng.uniform(-8.0, 8.0), rng.uniform(-12.0, -8.0)))
        if free(p):
            put(p, rng.uniform(0, math.tau), pick(rng, CROWD))
    centre = THEATRE
    for k in range(10):
        p = centre + THEATRE_DIRECTION * rng.uniform(-4.0, 6.0) + Vector((-THEATRE_DIRECTION.y, THEATRE_DIRECTION.x)) * rng.uniform(-6, 6)
        if free(p):
            put(p, rng.uniform(0, math.tau), pick(rng, CROWD))
    return placed


def ground_placements(scene):
    for key in list(scene.placements):
        grounded = []
        for matrix in scene.placements[key]:
            location = matrix.translation
            if location.z != 0.0:
                grounded.append(matrix)
                continue
            hint = scene.ground(location.x, location.y)
            z = scene.standing.height(location.x, location.y, hint + 3.0, 3.0)
            grounded.append(Matrix.Translation((0.0, 0.0, z)) @ matrix)
        scene.placements[key] = grounded


def place_life(scene):
    counts = {}
    for key, matrices in scene.placements.items():
        group = "vie" if key.startswith(("fig_", "group_")) else "props"
        shadow = key.startswith(("tree_", "prop_awning", "group_", "fig_"))
        scene.instances(group, key, scene.builds[key], matrices, shadow, False)
        counts[key] = len(matrices)
    root = scene.root("life")
    for index, (key, build) in enumerate(life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return counts


def place_ships(scene, ships):
    grouped = {}
    for key, matrix in ships:
        grouped.setdefault(key, []).append(matrix)
    for key, matrices in grouped.items():
        scene.instances("navires", key, life.SHIPS[key], matrices, True, False)
    return {key: len(m) for key, m in grouped.items()}


def place_columns(scene):
    counts = {}
    for order, frames in scene.columns.items():
        scene.instances("colonnes", f"column_{order}", COLUMN_KEYS[order], frames)
        counts[order] = len(frames)
    return counts


def atmosphere(scene, smoke_spots, plan, rng):
    root = scene.root("life")
    rng.shuffle(smoke_spots)
    smokes = smoke_spots[:8]
    for p in plan["quay"][2::max(len(plan["quay"]) // 3, 1)][:3]:
        smokes.append(Vector((p.x, p.y + 26.0, scene.ground(p.x, p.y + 26.0) + 8.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [Vector((MAUSOLEUM.x, MAUSOLEUM.y, scene.maus_z + 70.0)), Vector((60.0, -250.0, 30.0)),
              Vector((THEATRE.x, THEATRE.y, plan["theatre_floor"] + 50.0)), Vector((-300.0, -500.0, 26.0))]
    for index, point in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation(point))
    return len(smokes), len(flocks)


def weathering(scene):
    for key, mesh in scene.library.meshes.items():
        stand_in = types.SimpleNamespace(data=mesh, matrix_world=Matrix.Identity(4))
        if key.startswith(("house_", "far_")):
            weather(stand_in, 0.2, seed=len(key) * 7, scale=3.0, grime=0.35, ground=-0.2)
        elif key.startswith(("column_", "maus_column", "wall_")):
            weather(stand_in, 0.14, seed=len(key) * 5, scale=4.0, grime=0.2, ground=0.0)
        elif key.startswith(("maus_statue", "maus_lion")):
            weather(stand_in, 0.08, seed=len(key) * 3, scale=1.5)
    for name, obj in scene.statics.items():
        if name.startswith(("sol", "water")):
            weather(obj, 0.14, seed=len(name), scale=5.0, grime=0.0, ground=0.0)
            continue
        weather(obj, 0.12, seed=len(name) * 3, scale=6.0)


def render_previews(options, views):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(views) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, float(options.get("sky", 0.5)), aerosol=float(options.get("aerosol", 0.25)))
    lamp = sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, float(options.get("sun", 6.5)), SUN_COLOUR, 0.6)
    lamp.data.shadow_maximum_resolution = float(options.get("shadow", 0.03))
    haze_volume(stage, 40000.0, 900.0, float(options.get("haze", 0.000008)), (0.80, 0.86, 0.96), 0.4)
    configure_render(int(options.get("width", 1280)), int(options.get("height", 720)), options["samples"],
                     exposure=float(options.get("exposure", -0.1)), volumetric_end=30000.0)
    bpy.context.scene.view_settings.look = options.get("look", "AgX - Punchy")
    bpy.context.scene.eevee.shadow_pool_size = options.get("pool", "1024")
    lenses = {"vue-d-ensemble": 35.0, "le-mausolee": 24.0, "le-quadrige": 40.0, "le-port": 26.0, "le-theatre": 30.0}
    timings = {}
    for name in names:
        eye, target = views[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=lenses.get(name, 26.0))
        rig.data.clip_start = max(0.2, (eye - target).length / 400.0, eye.z / 200.0)
        rig.data.clip_end = 90000.0
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
    near, _, to_sea = ter.condition(dem, NEAR_HALF, NEAR_SPACING)
    far, _ = ter.far_field(dem, FAR_HALF, FAR_SPACING)
    del dem
    plan = site_plan(near)
    near = terrain_edits(near, plan)
    quay_line(near, plan)
    near = apply_quay(near, plan["quay"])
    print("PLAN", json.dumps({k: (round(v, 2) if isinstance(v, float) else None) for k, v in plan.items() if isinstance(v, float)}),
          flush=True)
    scene = Scene(tiles, near)
    rng = random.Random(377)
    build_terrain(scene, near, far, to_sea, plan)
    print("TERRAIN", round(time.perf_counter() - started, 1), flush=True)
    build_mausoleum(scene, plan)
    build_street(scene, plan)
    build_agora(scene, plan)
    quay_segments = build_quays(scene, plan, rng)
    build_palace(scene, plan)
    build_theatre(scene, plan)
    build_sanctuaries(scene, plan)
    wall_counts = build_walls(scene)
    print("MONUMENTS", round(time.perf_counter() - started, 1), flush=True)
    points = viewpoints(scene, plan)
    eyes = [eye for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    targets = [target for key, (_, target) in points.items() if key != "vue-d-ensemble"]
    city_counts, smoke_spots, tree_spots = build_city(scene, rng, [e.to_2d() for e in eyes])
    vegetation_counts = build_vegetation(scene, rng, tree_spots, [e.to_2d() for e in eyes])
    ship_counts = place_ships(scene, build_harbour_ships(scene, plan, rng))
    column_counts = place_columns(scene)
    print("CITY", round(time.perf_counter() - started, 1), flush=True)
    scene.flush(shadowless=("sol",))
    place_markers(scene, points)
    walkable = [obj for name, obj in scene.statics.items() if name.startswith(("sol", "port"))]
    walkable.append(scene.terrain_object)
    scene.surface = Surface(walkable)
    standing = [obj for name, obj in scene.statics.items() if name.startswith(("sol", "port", "agora", "terrasse", "theatre",
                                                                                 "sanctuaires", "palais"))]
    standing.append(scene.terrain_object)
    scene.standing = Surface(standing)
    route_counts, samples, problems = place_routes(scene, plan, eyes)
    figure_count = build_life(scene, rng, plan, samples, eyes, targets)
    ground_placements(scene)
    life_counts = place_life(scene)
    smoke_count, flock_count = atmosphere(scene, smoke_spots, plan, rng)
    weathering(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "halicarnasse.glb")
    export_seconds = export_glb(glb, roots)
    report = {"sun": [SUN_AZIMUTH, SUN_ELEVATION], "plan": {k: round(v, 2) for k, v in plan.items() if isinstance(v, float)},
              "routes": route_counts, "route_problems": problems, "city": city_counts, "vegetation": vegetation_counts,
              "ships": ship_counts, "walls": wall_counts, "quay_segments": quay_segments, "columns": column_counts,
              "life": life_counts, "street_figures": figure_count, "smoke": smoke_count, "flocks": flock_count,
              "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
              "elevation_source": [ter.DEM_URL.format(tile) for tile in ter.DEM_TILES], "elevation_licence": ter.DEM_LICENCE,
              "texture_credits": credits,
              "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]] for key, (eye, target) in points.items()},
              "salmacis": [round(v, 2) for v in plan["salmacis"]], "palace": [round(v, 2) for v in plan["palace"]]}
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)] for key, (eye, target) in points.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("BUILD", round(time.perf_counter() - started, 1), flush=True)
    report["previews"] = render_previews(options, points)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("glb_bytes", "previews", "total_seconds", "routes")}), flush=True)


if __name__ == "__main__":
    main()

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

from kit import colisee_amphitheatre as amp
from kit import colisee_city
from kit import colisee_fora as fora
from kit import colisee_life as life
from kit import colisee_materials
from kit import colisee_monuments as mon
from kit import colisee_terrain as ter
from kit import pantheon_city as city
from kit.arles_crowds import spectator
from kit.arles_monuments import strip_normals
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, principled_material, save_pixels
from kit.nimes_figures import WALKERS, Look, coarse, person
from kit.pantheon_detail import seller
from kit.pantheon_materials import build_library, weather
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, haze_volume, render_still, sun_lamp
from kit.terrain import HeightField, grid_mesh, polyline_distance, remove_faces_inside, value_noise

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "colisee")
BLEND = os.path.join(CACHE, "work", "colisee.blend")
DATUM = 21.0
NEAR_HALF = 1000.0
NEAR_SPACING = 12.5
FAR_HALF = 6000.0
FAR_SPACING = 100.0
OUTER_HALF = 39000.0
OUTER_SPACING = 1000.0
COL_BEARING = 112.0
COL_ANGLE = math.radians(90.0 - COL_BEARING)
COL = Matrix.Rotation(COL_ANGLE, 4, "Z")
FORUM_CENTRE = Vector((-560.0, 245.0))
FORUM_BEARING = 299.0
U_DIR = Vector((math.sin(math.radians(FORUM_BEARING)), math.cos(math.radians(FORUM_BEARING))))
V_DIR = Vector((math.sin(math.radians(FORUM_BEARING + 90.0)), math.cos(math.radians(FORUM_BEARING + 90.0))))
FORUM_LEVEL = 13.5
ARCH_LEVEL = 31.0
META_LEVEL = 21.5
VESTIBULE_LEVEL = 29.5
SUN_AZIMUTH = 268.0
SUN_ELEVATION = 37.0
SUN_COLOUR = (1.0, 0.78, 0.55)
META = Vector((-126.0, 22.0))
COLOSSUS = Vector((-171.0, 103.0))
VESTIBULE_ANGLE = math.radians(-4.0)
LUDUS = Vector((195.0, -60.0))
TITUS_BATHS = Vector((175.0, 235.0))
TRAJAN_SITE = Vector((335.0, 440.0))
CLAUDIUM = Vector((170.0, -390.0))
PEACE_F = (-80.0, 133.0)
PEACE_HALF = (67.5, 55.0)
HORREA_F = (-212.0, 58.0)
JUPITER = Vector((-818.0, 148.0))
FLAVIA = Vector((-490.0, -110.0))
TIBERIANA = Vector((-610.0, -10.0))
EYE_CLEARANCE = 2.4
PALACE_BEARING = 30.0
CIRCUS = Vector((-578.0, -474.0))
CIRCUS_BEARING = 125.0
AQUEDUCT = [(980.0, -470.0), (700.0, -452.0), (450.0, -428.0), (268.0, -402.0)]
FORA = {
    "iulium": (120.0, 104.0, FORUM_BEARING, 37.5, 80.0, FORUM_LEVEL + 1.0),
    "augustum": (102.0, 204.0, FORUM_BEARING - 270.0, 62.5, 59.0, FORUM_LEVEL + 2.5),
    "nerva": (10.0, 136.0, FORUM_BEARING - 270.0, 22.5, 60.0, FORUM_LEVEL + 1.5),
    "traiani": (315.0, 240.0, FORUM_BEARING, 105.0, 90.0, FORUM_LEVEL + 3.5),
}
GARDENS = [(FLAVIA.x + 120.0, FLAVIA.y - 160.0, 120.0), (CLAUDIUM.x, CLAUDIUM.y - 160.0, 140.0),
           (TITUS_BATHS.x - 120.0, TITUS_BATHS.y + 60.0, 90.0), (-760.0, 260.0, 90.0), (420.0, -480.0, 160.0),
           (650.0, 400.0, 220.0), (-150.0, 330.0, 70.0), (60.0, 360.0, 80.0)]
ROAD_PROFILES = {}


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 16}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def forum(u, v):
    point = FORUM_CENTRE + U_DIR * u + V_DIR * v
    return Vector((point.x, point.y))


def heading(direction):
    return math.atan2(direction.y, direction.x) - math.pi / 2


def forum_face(fu, fv):
    return heading(U_DIR * fu + V_DIR * fv)


def bearing_angle(bearing):
    return math.radians(90.0 - bearing) - math.pi / 2


def col_world(point):
    return COL @ Vector(point)


SACRA_F = [(58.0, 24.0), (-40.0, 24.0), (-62.0, 24.0), (-96.0, 34.0), (-125.0, 26.0), (-160.0, 10.0), (-210.0, -8.0),
           (-260.0, -27.0), (-321.0, -43.0)]


def sacra_via():
    points = [forum(u, v) for u, v in SACRA_F[:6]]
    arch = forum(*SACRA_F[-1])
    through = (META - arch).normalized()
    approach = [arch - through * 72.0, arch - through * 13.0, arch]
    beyond = [arch + through * 30.0, arch + through * 75.0, META + Vector((-17.0, 4.0))]
    return points + approach + beyond, len(points) + 2


def sacra_levels():
    points, arch_index = sacra_via()
    lengths = [0.0]
    for a, b in zip(points[:-1], points[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    levels = []
    for index, length in enumerate(lengths):
        if index <= arch_index:
            start = lengths[2]
            t = max(0.0, (length - start) / (lengths[arch_index] - start))
            levels.append(FORUM_LEVEL + (ARCH_LEVEL - FORUM_LEVEL) * t ** 1.3)
        else:
            t = (length - lengths[arch_index]) / (lengths[-1] - lengths[arch_index])
            levels.append(ARCH_LEVEL + (META_LEVEL - ARCH_LEVEL) * t)
    return points, levels


OTHER_ROADS = {
    "labicana": [Vector(v) for v in ((118.0, -14.0), (215.0, -8.0), (330.0, -55.0), (520.0, -200.0), (760.0, -300.0),
                                     (1000.0, -380.0))],
    "triumphalis": [Vector(v) for v in ((-130.0, -40.0), (-175.0, -150.0), (-225.0, -300.0), (-265.0, -450.0),
                                        (-295.0, -590.0), (-315.0, -720.0))],
    "caelius": [Vector(v) for v in ((-20.0, -105.0), (20.0, -200.0), (80.0, -280.0), (110.0, -300.0))],
    "oppius": [Vector(v) for v in ((40.0, 110.0), (90.0, 170.0), (120.0, 200.0))],
    "argiletum": [Vector(v) for v in (tuple(forum(10.0, 196.0)), tuple(forum(25.0, 270.0)), tuple(forum(80.0, 420.0)),
                                      tuple(forum(100.0, 600.0)))],
    "subura": [Vector(v) for v in ((-60.0, 120.0), (-120.0, 260.0), (-170.0, 420.0), (-230.0, 640.0),
                                   (-270.0, 900.0))],
    "vicus_tuscus": [Vector(v) for v in (tuple(forum(-50.0, -50.0)), tuple(forum(-42.0, -120.0)),
                                         tuple(forum(-60.0, -260.0)))],
}


def colosseum_distance(xs, ys, d_offset):
    local_x = xs * math.cos(-COL_ANGLE) - ys * math.sin(-COL_ANGLE)
    local_y = xs * math.sin(-COL_ANGLE) + ys * math.cos(-COL_ANGLE)
    radius = np.hypot(local_x / (amp.A + d_offset), local_y / (amp.B + d_offset))
    return (radius - 1.0) * (amp.B + d_offset)


def rect_distance(xs, ys, cx, cy, hx, hy, angle):
    local_x = (xs - cx) * math.cos(-angle) - (ys - cy) * math.sin(-angle)
    local_y = (xs - cx) * math.sin(-angle) + (ys - cy) * math.cos(-angle)
    return np.maximum(np.abs(local_x) - hx, np.abs(local_y) - hy)


FORUM_ANGLE = math.atan2(U_DIR.y, U_DIR.x)


LEVELS = {}


def flat_sites():
    flavia_centre = FLAVIA + (Matrix.Rotation(bearing_angle(PALACE_BEARING), 2) @ Vector((85.0, -40.0)))
    return {
        "flavia": (flavia_centre, 136.0, 124.0, bearing_angle(PALACE_BEARING)),
        "tiberiana": (TIBERIANA, 76.0, 56.0, bearing_angle(330.0)),
        "baths": (TITUS_BATHS, 63.0, 56.0, bearing_angle(202.0)),
        "trajan": (TRAJAN_SITE, 111.0, 101.0, bearing_angle(210.0)),
        "claudium": (CLAUDIUM, 93.0, 101.0, bearing_angle(22.0)),
        "horrea": (forum(*HORREA_F), 31.0, 22.0, FORUM_ANGLE),
        "jupiter": (JUPITER, 32.0, 36.0, bearing_angle(160.0)),
        "circus": (CIRCUS, 72.0, 302.0, bearing_angle(CIRCUS_BEARING)),
    }


def site_level(name):
    return LEVELS[name] - DATUM


def fora_rect(name):
    u, v, bearing, hx, hy, level = FORA[name]
    p = forum(u, v)
    return p, hx, hy, bearing_angle(bearing), level


def terrain_edits(xs, ys, heights):
    heights = ter.ridge(xs, ys, heights, [(-230.0, 150.0), (-150.0, 260.0), (-60.0, 360.0), (40.0, 420.0)], 34.0, 70.0)
    heights = ter.blend_to(heights, colosseum_distance(xs, ys, 80.0), DATUM, 120.0)
    heights = ter.blend_to(heights, rect_distance(xs, ys, *forum(2.0, -4.0), 116.0, 80.0, FORUM_ANGLE), FORUM_LEVEL,
                           40.0)
    for name in FORA:
        p, hx, hy, angle, level = fora_rect(name)
        heights = ter.blend_to(heights, rect_distance(xs, ys, p.x, p.y, hx, hy, angle), level, 25.0)
    peace = forum(*PEACE_F)
    heights = ter.blend_to(heights, rect_distance(xs, ys, peace.x, peace.y, *PEACE_HALF, FORUM_ANGLE),
                           FORUM_LEVEL + 2.0, 30.0)
    points, levels = sacra_levels()
    heights = ter.road_blend(xs, ys, heights, [tuple(p) for p in points], levels, 10.0, 45.0)
    heights = ter.blend_to(heights, rect_distance(xs, ys, COLOSSUS.x, COLOSSUS.y, 60.0, 50.0, VESTIBULE_ANGLE),
                           VESTIBULE_LEVEL, 25.0)
    heights = ter.blend_to(heights, np.hypot(xs - META.x, ys - META.y) - 18.0, META_LEVEL, 20.0)
    heights = ter.blend_to(heights, rect_distance(xs, ys, LUDUS.x, LUDUS.y, 62.0, 46.0, COL_ANGLE), DATUM + 1.0, 90.0)
    for name, (centre, hx, hy, angle) in flat_sites().items():
        if name not in LEVELS:
            inside = rect_distance(xs, ys, centre.x, centre.y, hx, hy, angle) < 0
            LEVELS[name] = float(np.median(heights[inside])) if inside.any() else float(heights.mean())
        margin = 30.0 if name == "circus" else 14.0
        heights = ter.blend_to(heights, rect_distance(xs, ys, centre.x, centre.y, hx, hy, angle), LEVELS[name], margin)
    if not ROAD_PROFILES:
        field = HeightField(heights, float(xs.max()))
        for name, road in OTHER_ROADS.items():
            ROAD_PROFILES[name] = ter.graded_profile([tuple(p) for p in road], field.sample)
    for name, (dense, levels) in ROAD_PROFILES.items():
        heights = ter.road_blend(xs, ys, heights, dense, levels, 10.0, 60.0)
    heights = ter.blend_to(heights, colosseum_distance(xs, ys, 72.0), DATUM, 20.0)
    return heights


class Scene:
    def __init__(self, tiles, field):
        self.tiles = tiles
        self.field = field
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Colisee")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.statics = {}
        self.builds = {}
        self.extra_trees = []
        self.worksites = []
        self.obstacles = []

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.field.sample(x, y)) - DATUM

    def ground_far(self, x, y):
        if max(abs(x), abs(y)) < NEAR_HALF - 5.0:
            return self.ground(x, y)
        return float(self.far.sample(x, y)) - DATUM

    def lowest(self, x, y, radius):
        return min(self.ground(x + dx, y + dy) for dx, dy in ((0, 0), (radius, 0), (-radius, 0), (0, radius),
                                                              (0, -radius), (radius * 0.7, radius * 0.7),
                                                              (-radius * 0.7, -radius * 0.7), (radius * 0.7, -radius * 0.7),
                                                              (-radius * 0.7, radius * 0.7)))

    def unique(self, group, builder, matrix=None, occlusion=True):
        if not occlusion:
            builder.heights = [10.0] * len(builder.positions)
        self.pending.setdefault(group, []).append((builder, matrix if matrix is not None else Matrix.Identity(4)))
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

    def instances(self, group, key, build, matrices, cast_shadow=True, occlusion=True):
        if matrices:
            self.library.place(key, build, self.collection, self.root(group), matrices, cast_shadow, occlusion)

    def add(self, key, matrix, build=None):
        self.placements.setdefault(key, []).append(matrix)
        if build is not None:
            self.builds.setdefault(key, build)


def extra_materials(tiles, credits):
    principled_material("arena_sand", (0.66, 0.45, 0.25), 0.96)
    tiles["arena_sand"] = 3.0
    principled_material("velum_linen", (0.92, 0.88, 0.78), 0.9)
    tiles["velum_linen"] = 4.0
    colisee_materials.colisee_library(CACHE, tiles, credits)
    colisee_materials.paving_library(CACHE, tiles, credits)
    colisee_materials.facade_library(CACHE, tiles)
    principled_material("col_bronze_patina", (0.45, 0.33, 0.20), 0.45, 1.0)
    for name in ("travertine", "brick", "marble_paving", "bronze_tiles"):
        strip_normals(name)


def terrain_objects(scene, near, far):
    root = scene.root("terrain")
    heights = near.heights - DATUM
    mesh = grid_mesh("terrain", heights, NEAR_HALF)
    axis = np.linspace(-NEAR_HALF, NEAR_HALF, 1024)
    tx, ty = np.meshgrid(axis, axis)
    th = near.sample(tx, ty)
    gy, gx = np.gradient(th, axis[1] - axis[0])
    slope = np.hypot(gx, gy)
    paved = np.zeros(tx.shape)
    paved = np.maximum(paved, (rect_distance(tx, ty, *forum(2.0, -4.0), 112.0, 76.0, FORUM_ANGLE) < 0) * 0.8)
    paved = np.maximum(paved, (colosseum_distance(tx, ty, 70.0) < 0) * 0.9)
    points, _ = sacra_levels()
    paved = np.maximum(paved, (polyline_distance([tuple(p) for p in points], tx, ty) < 9.0) * 0.9)
    for road in OTHER_ROADS.values():
        paved = np.maximum(paved, (polyline_distance([tuple(p) for p in road], tx, ty) < 7.0) * 0.8)
    garden = np.zeros(tx.shape)
    for gx, gy, radius in GARDENS:
        garden = np.maximum(garden, np.clip(1.0 - (np.hypot(tx - gx, ty - gy) - radius * 0.7) / (radius * 0.3), 0, 1))
    colour = ter.ground_colour(tx, ty, th, slope, paved, garden=garden)
    image = save_pixels("terrain_colour", colour,
                        os.path.join(CACHE, "textures", "terrain_colour.jpg"), quality=88)
    mesh.materials.append(baked_material("terrain", image))
    created = new_object("terrain_near", mesh, scene.collection, root)
    created["cast_shadow"] = False
    scene.terrain_object = created
    far_heights = far.heights - DATUM
    far_mesh = grid_mesh("terrain_far", far_heights, FAR_HALF)
    remove_faces_inside(far_mesh, NEAR_HALF - FAR_SPACING * 0.5)
    axis = np.linspace(-FAR_HALF, FAR_HALF, 1024)
    tx, ty = np.meshgrid(axis, axis)
    th = far.sample(tx, ty)
    gy, gx = np.gradient(th, axis[1] - axis[0])
    slope = np.hypot(gx, gy)
    distance = np.hypot(tx, ty)
    urban = np.clip(1.0 - (distance - 1600.0) / 900.0, 0.0, 1.0)
    noise = value_noise(tx.shape, 90, 23, octaves=3)
    roofs = np.dstack([0.60 + 0.12 * noise, 0.42 + 0.08 * noise, 0.33 + 0.05 * noise])
    country = ter.ground_colour(tx, ty, th, slope, np.zeros(tx.shape), seed=29)
    colour = country * (1 - urban[..., None] * 0.8) + roofs * urban[..., None] * 0.8
    river = polyline_distance([tuple(ter.FRAME.to_local(*p)) for p in city.RIVER_GEO], tx, ty) < 55.0
    colour[river] = (0.22, 0.30, 0.28)
    image = save_pixels("terrain_far_colour", colour, os.path.join(CACHE, "textures", "terrain_far_colour.jpg"), quality=85)
    far_mesh.materials.append(baked_material("terrain_far", image))
    created = new_object("terrain_far", far_mesh, scene.collection, root)
    created["cast_shadow"] = False
    sample, scene.outer_url = ter.tinitaly_outer(os.path.join(CACHE, "src", "tinitaly_outer.tif"))
    axis = np.linspace(-OUTER_HALF, OUTER_HALF, int(round(2 * OUTER_HALF / OUTER_SPACING)) + 1)
    tx, ty = np.meshgrid(axis, axis)
    reach = np.maximum(np.abs(tx), np.abs(ty))
    th = sample(tx, ty) - DATUM - 6.0 * np.clip(1.0 - (reach - FAR_HALF) / 3000.0, 0.0, 1.0)
    outer = grid_mesh("terrain_outer", th, OUTER_HALF, ring=(90000.0, 0.0))
    remove_faces_inside(outer, FAR_HALF - OUTER_SPACING * 0.5)
    axis = np.linspace(-OUTER_HALF, OUTER_HALF, 512)
    tx, ty = np.meshgrid(axis, axis)
    th = sample(tx, ty)
    gy, gx = np.gradient(th, axis[1] - axis[0])
    colour = ter.ground_colour(tx, ty, th, np.hypot(gx, gy) * 3.0, np.zeros(tx.shape), seed=31)
    colour[th < 0.5] = (0.2, 0.28, 0.31)
    image = save_pixels("terrain_outer_colour", colour, os.path.join(CACHE, "textures", "terrain_outer_colour.jpg"),
                        quality=85)
    outer.materials.append(baked_material("terrain_outer", image))
    created = new_object("terrain_outer", outer, scene.collection, root)
    created["cast_shadow"] = False


def tiber(scene):
    points = [Vector((*ter.FRAME.to_local(*p), 0.0)) for p in city.RIVER_GEO]
    builder = MeshBuilder()
    lefts, rights = [], []
    for index, point in enumerate(points):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        direction = (b - a).normalized()
        side = Vector((-direction.y, direction.x, 0.0))
        level = min(scene.ground_far(*(point + side * 30.0).xy), scene.ground_far(*(point - side * 30.0).xy),
                    scene.ground_far(point.x, point.y)) + 0.3
        lefts.append(point + side * 52.0 + Vector((0.0, 0.0, level)))
        rights.append(point - side * 52.0 + Vector((0.0, 0.0, level)))
    builder.surface([lefts, rights], "water", facing=(0, 0, 1))
    scene.unique("sol", builder, occlusion=False)


def road_ribbon(scene, points, width, levels=None, material="col_basalt", tint=(0.95, 0.95, 0.95), lift=0.08, step=3.0):
    dense = []
    dense_levels = []
    for index, (a, b) in enumerate(zip(points[:-1], points[1:])):
        count = max(int((b - a).length / step), 1)
        for k in range(count):
            t = k / count
            dense.append(a.lerp(b, t))
            if levels is not None:
                dense_levels.append(levels[index] + (levels[index + 1] - levels[index]) * t)
    dense.append(points[-1])
    if levels is not None:
        dense_levels.append(levels[-1])
    builder = MeshBuilder()
    lefts, rights = [], []
    for index, point in enumerate(dense):
        a = dense[max(index - 1, 0)]
        b = dense[min(index + 1, len(dense) - 1)]
        direction = (b - a).normalized()
        side = Vector((-direction.y, direction.x)) * width / 2
        for target, offset in ((lefts, side), (rights, -side)):
            p = point + offset
            z = scene.ground(p.x, p.y) + lift
            target.append(Vector((p.x, p.y, z)))
    builder.surface([lefts, rights], material, facing=(0, 0, 1))
    builder.tint(0, tint)
    return builder


def build_colosseum(scene, rng):
    angles, width, kappas = amp.bay_frames()
    frames = [COL @ amp.frame(t) for t in angles]
    index, means = amp.classes(kappas, 3)
    for c, kappa in enumerate(means):
        chosen = [frames[k] for k in range(amp.BAYS) if index[k] == c and k not in (20, 60)]
        scene.instances("colisee", f"col_bay_{c}", lambda kappa=kappa: amp.bay(width * 1.004, kappa), chosen)
    scene.instances("colisee", "col_bay_gate", lambda: amp.bay(width * 1.004, means[0], porch=True),
                    [frames[20], frames[60]])
    scene.instances("colisee", "col_window", amp.attic_window, [frames[k] for k in range(amp.BAYS) if k % 2],
                    cast_shadow=False)
    scene.instances("colisee", "col_clipeus", amp.clipeus, [frames[k] for k in range(amp.BAYS) if k % 2 == 0],
                    cast_shadow=False)
    statue_frames = {"col_statue_a": [], "col_statue_b": []}
    for k, f in enumerate(frames):
        for level, z in ((0, 11.6), (1, 23.4)):
            key = "col_statue_a" if (k + level) % 2 else "col_statue_b"
            statue_frames[key].append(f @ placement(0.0, -1.2, z + 0.4, 0.0, 1.75))
    looks = {"col_statue_a": Look("white", hem=0.12, toga="white", arms="toga_gesture", mono=(0.95, 0.93, 0.89),
                                  material=mon.MARBLE, seed=301),
             "col_statue_b": Look("white", hem=0.03, palla="white", female=True, sleeves="long", arms="hip",
                                  mono=(0.95, 0.93, 0.89), material=mon.MARBLE, seed=302)}
    def statue(look):
        builder = coarse(lambda: person(look), 0.3)
        builder.box((-0.2, -0.18, -0.4 / 1.75), (0.2, 0.18, 0.0), mon.MARBLE, bottom=False)
        return builder
    for key, matrices in statue_frames.items():
        scene.instances("colisee", key, lambda look=looks[key]: statue(look), matrices, cast_shadow=False)
    for k in range(14, 42):
        number = amp.bay_number(k)
        if number is None:
            continue
        letters, _ = mon.inscription(amp.numeral(number), 0.36, material=amp.TRAV, depth=0.03)
        letters.tint(0, (0.5, 0.46, 0.4))
        scene.unique("colisee", letters, frames[k] @ mon.facing_text_matrix(Vector((0.0, 0.13, 7.95)), (0, 1, 0)))
    scene.unique("colisee_cavea", amp.cavea(angles), COL)
    scene.instances("colisee", "col_portico_column", mon.simple_column(amp.TRAV),
                    [COL @ f @ Matrix.Diagonal((0.72, 0.72, 11.0 / mon.UNIT, 1.0)) for f in amp.portico_frames()])
    scene.unique("colisee_cavea", amp.portico_roof(), COL)
    scene.unique("sol", amp.arena_floor(), COL, occlusion=False)
    doors, spots = amp.trapdoors()
    scene.unique("sol", doors, COL, occlusion=False)
    south = 3 * math.pi / 2
    north = math.pi / 2
    scene.unique("colisee_cavea", amp.pulvinar(), COL @ amp.frame(south, 0.0, 0.0))
    scene.unique("colisee_cavea", amp.podium_doors(), COL)
    scene.unique("colisee_cavea", amp.pulvinar(8.0), COL @ amp.frame(north, 0.0, 0.0))
    scene.unique("velarium", amp.velarium(angles, [amp.frame(t) for t in angles]), COL, occlusion=False)
    scene.unique("sol", amp.ground_ring(), COL, occlusion=False)
    scene.instances("colisee", "col_cippus", amp.cippus, [COL @ f for f in amp.cippi_frames()], cast_shadow=False)
    return angles, width, kappas, index, frames, spots


def build_crowd(scene, angles, width, kappas, index, near_eye):
    pool = amp.near_pool()
    variants = {}
    for k, t in enumerate(angles):
        f_local = amp.frame(t)
        if (f_local.translation - near_eye).to_2d().length < 58.0:
            builder = amp.crowd_block(width, kappas[k], 700 + k, near=near_eye, near_radius=8.0, frame_matrix=f_local,
                                      pool=pool)
            scene.unique("foule_proche", builder, COL @ f_local, occlusion=False)
            continue
        key = f"crowd_{index[k]}_{k % 2}"
        variants.setdefault(key, (index[k], k % 2, []))[2].append(COL @ f_local)
    means = {}
    for k, kappa in enumerate(kappas):
        means.setdefault(index[k], []).append(kappa)
    for key, (c, v, matrices) in variants.items():
        kappa = sum(means[c]) / len(means[c])
        scene.instances("foule", key, lambda kappa=kappa, c=c, v=v: amp.crowd_block(width, kappa, 40 + 7 * c + v),
                        matrices, cast_shadow=False, occlusion=False)
    return sum(len(v[2]) for v in variants.values())


def build_arena_life(scene, spots, near_eye):
    def put(key, x, y, turn, build=None, z=amp.FLOOR):
        scene.add(key, COL @ placement(x, y, z, turn), build)
    put("fig_murmillo", 3.4, -11.0, 0.15, life.murmillo)
    put("fig_thraex", 3.8, -9.1, math.pi + 0.1, life.thraex)
    put("fig_referee", 6.0, -10.4, math.pi / 2 + 0.4, life.referee)
    put("fig_retiarius", -15.0, 4.0, -0.5, life.retiarius)
    put("fig_secutor", -13.6, 5.4, math.pi - 0.6, life.secutor)
    put("fig_referee", -16.6, 6.2, -1.2, life.referee)
    for k, (x, y, turn) in enumerate(((-28.0, -8.0, 1.2), (-26.5, -9.4, 1.0), (24.0, 12.0, -2.0))):
        put("fig_attendant", x, y, turn, life.attendant)
    put("prop_organ", 9.0, 22.6, math.pi, life.organ)
    for x in (12.0, 13.4, 6.0):
        put("fig_cornicen", x, 22.4, math.pi + 0.1, life.cornicen)
    x, y = spots[9]
    put("prop_cage", x, y, 0.0, life.cage, z=amp.FLOOR - 0.3)
    put("prop_lion", x, y + 0.1, 0.0, life.lion, z=amp.FLOOR + 0.03)
    south = 3 * math.pi / 2
    pulvinar = amp.frame(south, 0.0, 0.0)
    put_matrix = lambda key, local, build: scene.add(key, COL @ pulvinar @ local, build)
    put_matrix("fig_emperor", placement(0.0, 1.6, 4.4, math.pi), life.emperor)
    for x in (-3.6, 3.6):
        put_matrix("fig_praetorian", placement(x, 4.6, 4.4, math.pi), life.praetorian)
    for x in (-1.8, 1.9):
        put_matrix("fig_senator", placement(x, 3.2, 4.4, math.pi + 0.2 * x), lambda: life.senator(11))
    rng = random.Random(4)
    for k in range(18):
        t = south + rng.uniform(-0.55, 0.55)
        if abs(t - south) < 0.16:
            continue
        d = rng.uniform(1.2, 5.0)
        z = 3.6 if d < 1.8 else (3.9 if d < 3.2 else 4.2)
        point = amp.oval(t, d, z)
        if (point - near_eye).to_2d().length < 2.2:
            continue
        key = "fig_senator_gesture" if k % 3 == 0 else "fig_senator"
        build = (lambda: life.senator(14, True)) if k % 3 == 0 else (lambda: life.senator(11))
        turn = math.atan2(-amp.normal(t).x, amp.normal(t).y) + math.pi + rng.uniform(-0.6, 0.6)
        scene.add(key, COL @ placement(point.x, point.y, z, turn), build)
    angles, _ = amp.even_angles(26, amp.OUTER - 0.6)
    for k, t in enumerate(angles):
        if k % 2:
            continue
        point = amp.oval(t, amp.OUTER - 0.9, amp.FACADE_TOP)
        turn = math.atan2(-amp.normal(t).x, amp.normal(t).y) + (math.pi if k % 4 else 0.0)
        scene.add("fig_sailor", COL @ placement(point.x, point.y, point.z, turn), life.sailor)


STREET_LOOKS = {
    "fig_toga": Look("white", hem=0.12, skin=0, hair=0, toga="white", arms="toga", seed=401),
    "fig_toga_b": Look("white", hem=0.12, skin=1, hair=2, toga="white", arms="toga_gesture", seed=402),
    "fig_matron": Look("woad", hem=0.03, skin=0, hair=0, palla="rose", veil=True, female=True, sleeves="long",
                       arms="hip", scale=0.93, seed=403),
    "fig_woman": Look("weld", hem=0.04, skin=1, hair=1, palla="madder", female=True, sleeves="long", arms="down",
                      scale=0.93, seed=404),
    "fig_plebs": Look("brown", hem=0.55, skin=2, hair=1, belt="dark", arms="gesture", seed=405),
    "fig_plebs_b": Look("ochre", hem=0.55, skin=1, hair=3, belt="brown", cloak="madder", arms="down", seed=406),
    "fig_child": Look("white", hem=0.5, skin=0, hair=1, scale=0.64, belt="madder", stripe="madder", child=True,
                      seed=407),
    "fig_stranger": Look("green", hem=0.3, skin=2, hair=3, cloak="woad", hood="brown", arms="staff", carry="staff",
                         seed=408),
}
STREET_WEIGHTS = [("fig_toga", 3.0), ("fig_toga_b", 1.5), ("fig_matron", 2.0), ("fig_woman", 1.5), ("fig_plebs", 3.0),
                  ("fig_plebs_b", 2.0), ("fig_child", 1.0), ("fig_stranger", 0.7)]


def pick(rng, weights):
    total = sum(w for _, w in weights)
    roll = rng.random() * total
    for key, weight in weights:
        roll -= weight
        if roll <= 0:
            return key
    return weights[-1][0]


def street_figure(scene, rng, x, y, turn, eyes):
    key = pick(rng, STREET_WEIGHTS)
    near = min((Vector((x, y)) - eye).length for eye in eyes) < 60.0
    look = STREET_LOOKS[key]
    if near:
        scene.add(key, placement(x, y, 0.0, turn), lambda look=look: person(look))
    else:
        scene.add(key + "_far", placement(x, y, 0.0, turn), lambda look=look: coarse(lambda: person(look), 0.38))


def build_monuments(scene, rng):
    zf = FORUM_LEVEL - DATUM
    columns = {"corinthian": [], "ionic": [], "tuscan": []}

    def fmat(u, v, z, fu, fv):
        p = forum(u, v)
        return placement(p.x, p.y, z, forum_face(fu, fv))

    def temple_at(group, builder_columns, matrix):
        builder, frames = builder_columns
        scene.unique(group, builder, matrix)
        for order, items in frames.items():
            columns[order].extend(matrix @ f for f in items)
    scene.unique("forum", mon.rostra(), fmat(66.0, 0.0, zf, -1, 0))
    face = Vector((-1.0, 0.45)).normalized()
    temple_at("forum", mon.temple(22.5, 40.0, 7.0, 11.0, 1.43, 6, "ionic", pronaos=3),
              fmat(92.0, -34.0, zf, face.x, face.y))
    temple_at("forum", mon.temple(22.0, 33.0, 4.5, 14.2, 1.45, 6, "corinthian", pronaos=2), fmat(100.0, -6.0, zf, -1, 0))
    temple_at("forum", mon.temple(25.0, 14.0, 4.5, 13.0, 1.4, 6, "corinthian", pronaos=1, back_wall=False),
              fmat(95.0, 22.0, zf, -1, 0))
    cella = MeshBuilder()
    cella.box((-22.5, -12.0, -1.0), (22.5, 12.0, 4.5), mon.MARBLE, bottom=False)
    cella.box((-22.0, -11.5, 4.5), (22.0, 11.5, 20.0), mon.MARBLE, bottom=False)
    mon.gable_roof(cella, -22.5, 22.5, 12.2, 20.0, 24.5, mon.TILES, along_axis="x", imbrex=False)
    scene.unique("forum", cella, fmat(113.0, 22.0, zf, -1, 0))
    scene.unique("forum", mon.tabularium(), fmat(128.0, 4.0, zf + 3.0, -1, 0))
    scene.unique("forum", mon.curia(), fmat(46.0, 50.0, zf + 0.3, 0, -1))
    builder, bays = mon.basilica_paulli()
    matrix = fmat(-12.0, 47.0, zf, 0, -1)
    scene.unique("forum", builder, matrix)
    arcade = []
    for local, step in bays:
        arcade.append(matrix @ local @ Matrix.Diagonal((step / 6.0, 1.0, 1.0, 1.0)))
    scene.instances("forum", "paulli_bay", lambda: mon.arcade_bay(6.0, 7.0, shops=True, material=mon.MARBLE), arcade)
    builder, bays = mon.basilica_julia()
    matrix = fmat(5.0, -50.0, zf, 0, 1)
    scene.unique("forum", builder, matrix)
    scene.instances("forum", "julia_bay", lambda: mon.arcade_bay(5.6, 16.5, material=mon.MARBLE),
                    [matrix @ local @ Matrix.Diagonal((step / 5.6, 1.0, 1.0, 1.0)) for local, step in bays])
    temple_at("forum", mon.temple(30.0, 50.0, 7.0, 12.5, 1.45, 8, "corinthian", peripteral=True, pronaos=3),
              fmat(-67.0, -52.0, zf, 0, 1))
    temple_at("forum", mon.temple(26.0, 30.0, 3.5, 11.0, 1.2, 6, "corinthian", pronaos=2), fmat(-75.0, 5.0, zf, 1, 0))
    scene.unique("forum", mon.hall(20.0, 13.0, 7.5, mon.MARBLE), fmat(-104.0, 20.0, zf, 0, -1))
    temple_at("forum", mon.round_temple(), fmat(-100.0, -30.0, zf, 1, 0))
    vestals, vestal_columns = mon.court(46.0, 14.0, 7.0, basin=(30.0, 4.0))
    for x, y, w, d in ((0.0, 15.0, 70.0, 12.0), (0.0, -15.0, 70.0, 12.0), (31.0, 0.0, 8.0, 18.0),
                       (-31.0, 0.0, 8.0, 18.0)):
        vestals.merge(mon.hall(w, d, 10.0, mon.BRICK, roof="gable", windows=4), placement(x, y, 0.0,
                                                                                       0.0 if w > d else math.pi / 2))
    vm = fmat(-142.0, -42.0, zf, 1, 0)
    scene.unique("forum", vestals, vm)
    scene.instances("forum", "vestal_column", mon.simple_column(), [vm @ f for f in vestal_columns])
    for k in range(3):
        u = -40.0 + 40.0 * k
        base = MeshBuilder()
        base.box((-1.2, -1.6, 0.0), (1.2, 1.6, 2.4), mon.MARBLE, bottom=False)
        statue = person(Look("white", hem=0.12, toga="white", arms="toga_gesture", mono=(1.0, 1.0, 1.0),
                             material=mon.BRONZE, seed=500 + k))
        base.merge(statue, placement(0.0, 0.0, 2.4, 0.0, 1.35))
        scene.unique("forum", base, fmat(u, -11.0, zf, 0, 1))
    for k, u in enumerate((-52.0, -36.0, -20.0, 28.0, 44.0)):
        base = MeshBuilder()
        base.box((-1.6, -1.2, 0.0), (1.6, 1.2, 2.2), mon.MARBLE, bottom=False)
        statue = person(Look("white", hem=0.12, toga="white", arms="toga_gesture" if k % 2 else "toga",
                             mono=(1.0, 1.0, 1.0), material=mon.PATINA, seed=520 + k))
        base.merge(statue, placement(0.0, 0.0, 2.2, 0.0, 1.3))
        scene.unique("forum", base, fmat(u, 20.0, zf, 0, -1))
        scene.obstacles.append((forum(u, 20.0), 2.6))
    for k in range(3):
        scene.obstacles.append((forum(-40.0 + 40.0 * k, -11.0), 2.6))
    curtius = MeshBuilder()
    for x0, y0, x1, y1 in ((-5.0, -4.5, 5.0, -4.0), (-5.0, 4.0, 5.0, 4.5), (-5.0, -4.0, -4.5, 4.0), (4.5, -4.0, 5.0, 4.0)):
        curtius.box((x0, y0, -0.3), (x1, y1, 0.9), mon.MARBLE, bottom=False)
    curtius.box((-4.5, -4.0, -0.3), (4.5, 4.0, 0.05), mon.TRAV, bottom=False)
    curtius.tint(len(curtius.polygons) - 5, (0.62, 0.58, 0.52))
    curtius.box((-0.8, -0.6, 0.05), (0.8, 0.6, 1.1), mon.MARBLE, bottom=False)
    scene.unique("forum", curtius, fmat(-15.0, -6.0, zf + 0.1, 1, 0))
    scene.obstacles.append((forum(-15.0, -6.0), 7.5))
    paving = MeshBuilder()
    corners = [forum(-58.0, -24.0), forum(-58.0, 30.0), forum(58.0, 30.0), forum(58.0, -24.0)]
    uvs = [((p - FORUM_CENTRE).dot(V_DIR), (p - FORUM_CENTRE).dot(U_DIR)) for p in corners]
    paving.polygon([(p.x, p.y, zf + 0.1) for p in corners], "col_slabs", uvs=uvs)
    paving.tint(0, (0.97, 0.96, 0.94))
    scene.unique("sol", paving, occlusion=False)
    for order, matrices in columns.items():
        if matrices:
            scene.instances("forum", f"forum_{order}", mon.unit_column(order, "low"), matrices)
    temple_at("collines", mon.temple(53.0, 62.0, 4.0, 14.8, 2.1, 6, "corinthian", peripteral=True, pronaos=3, gilt=True),
              placement(JUPITER.x, JUPITER.y, site_level("jupiter"), bearing_angle(160.0)))
    for order, matrices in columns.items():
        matrices.clear()
    points, levels = sacra_levels()
    scene.unique("sol", road_ribbon(scene, points, 9.0), occlusion=False)
    sacra_porticoes(scene, points, levels)
    for name, road in OTHER_ROADS.items():
        scene.unique("sol", road_ribbon(scene, road, 7.0, tint=(0.9, 0.88, 0.86)), occlusion=False)
    arch_index = sacra_via()[1]
    arch_point = points[arch_index]
    direction = (points[arch_index + 1] - points[arch_index - 1]).normalized()
    arch_matrix = placement(arch_point.x, arch_point.y, ARCH_LEVEL - DATUM, heading(direction))
    scene.unique("arc", mon.arch_of_titus(), arch_matrix)
    scene.obstacles.append((arch_point, 9.5))
    scene.unique("velia", mon.meta_sudans(), placement(META.x, META.y, META_LEVEL - DATUM))
    scene.obstacles.append((META, 11.0))
    vz = VESTIBULE_LEVEL - DATUM
    portico, frames = mon.portico_ring(120.0, 100.0, height=7.5, depth=7.0, spacing=4.2)
    retaining = MeshBuilder()
    retaining.box((-60.6, -50.6, -14.0), (60.6, 50.6, -0.4), mon.BRICK, bottom=False, top=False)
    retaining.box((-53.0, -43.0, -0.6), (53.0, 43.0, 0.1), mon.TRAV, bottom=False)
    vestibule = placement(COLOSSUS.x, COLOSSUS.y, vz, VESTIBULE_ANGLE)
    scene.unique("velia", portico, vestibule)
    scene.unique("velia", retaining, vestibule)
    scene.instances("velia", "vestibule_column", mon.simple_column(), [vestibule @ f for f in frames])
    scene.unique("velia", mon.colossus(), placement(COLOSSUS.x, COLOSSUS.y, vz, bearing_angle(225.0)))
    horrea = mon.hall(60.0, 42.0, 14.0, mon.BRICK, roof="gable", windows=8)
    hp = forum(*HORREA_F)
    scene.unique("velia", horrea, placement(hp.x, hp.y, site_level("horrea"), FORUM_ANGLE))
    return arch_matrix, direction


def sacra_porticoes(scene, points, levels):
    arch_index = sacra_via()[1]
    frames = []
    builder = MeshBuilder()
    for index in range(5, arch_index - 1):
        a, b = points[index], points[index + 1]
        span = (b - a).length
        d = (b - a) / span
        side = Vector((-d.y, d.x))
        count = int(span / 4.0)
        for k in range(1, count):
            t = k / count
            for sign in (-1, 1):
                p = a.lerp(b, t) + side * sign * 8.0
                z = levels[index] + (levels[index + 1] - levels[index]) * t - DATUM
                frames.append(mon.column_frame(p.x, p.y, z, 0.55, 5.6))
        for sign in (-1, 1):
            local = MeshBuilder()
            za = levels[index] - DATUM
            zb = levels[index + 1] - DATUM
            corners = []
            for offset, height in ((7.6, 5.6), (13.5, 6.8)):
                for p, z in ((a, za), (b, zb)):
                    corners.append(Vector((p.x, p.y, z)) + Vector((*(side * sign * offset), height)))
            local.oriented([corners[0], corners[1], corners[3], corners[2]], (0, 0, 1), mon.TILES)
            first = len(local.polygons)
            local.oriented([corners[0] - Vector((0, 0, 0.05)), corners[1] - Vector((0, 0, 0.05)),
                            corners[3] - Vector((0, 0, 0.05)), corners[2] - Vector((0, 0, 0.05))], (0, 0, -1), "matte")
            local.tint(first, (0.42, 0.32, 0.22))
            local.oriented([corners[0], corners[1], corners[1] - Vector((0, 0, 0.7)), corners[0] - Vector((0, 0, 0.7))],
                           Vector((*(-side * sign), 0.0)), mon.MARBLE)
            back = [Vector((p.x, p.y, z)) + Vector((*(side * sign * 13.5), 0.0)) for p, z in ((a, za), (b, zb))]
            local.oriented([back[0] - Vector((0, 0, 4.0)), back[1] - Vector((0, 0, 4.0)), back[1] + Vector((0, 0, 6.8)),
                            back[0] + Vector((0, 0, 6.8))], Vector((*(-side * sign), 0.0)), mon.PLASTER)
            for k in range(1, max(int(span / 5.0), 1)):
                door = back[0].lerp(back[1], k / max(int(span / 5.0), 1)) - Vector((*(side * sign * 0.03), 0.0))
                along = Vector((*(d * 1.1), 0.0))
                local.oriented([door - along, door + along, door + along + Vector((0, 0, 3.0)),
                                door - along + Vector((0, 0, 3.0))], Vector((*(-side * sign), 0.0)), mon.VOID)
            floor = [Vector((p.x, p.y, z + 0.25)) + Vector((*(side * sign * offset), 0.0)) for offset in (4.5, 13.5)
                     for p, z in ((a, za), (b, zb))]
            first = len(local.polygons)
            local.oriented([floor[0], floor[1], floor[3], floor[2]], (0, 0, 1), mon.TRAV)
            local.oriented([floor[0] - Vector((0, 0, 0.4)), floor[1] - Vector((0, 0, 0.4)), floor[1], floor[0]],
                           Vector((*(-side * sign), 0.0)), mon.TRAV)
            local.tint(first, (0.86, 0.8, 0.72))
            builder.merge(local)
    scene.unique("velia", builder)
    scene.instances("velia", "sacra_column", mon.simple_column(), frames)


def build_hills(scene, rng):
    court_columns = []

    def at(name, bearing, lift=0.0):
        point = flat_sites()[name][0] if name != "flavia" else FLAVIA
        return placement(point.x, point.y, site_level(name) + lift, bearing_angle(bearing))

    flavia = MeshBuilder()
    flavia.merge(mon.hall(34.0, 47.0, 30.0, mon.PLASTER, roof="gable", windows=4), placement(0.0, 52.0, 0.0))
    flavia.merge(mon.hall(16.0, 32.0, 20.0, mon.PLASTER, roof="gable"), placement(-28.0, 50.0, 0.0))
    flavia.merge(mon.hall(16.0, 32.0, 24.0, mon.PLASTER, roof="vault"), placement(28.0, 50.0, 0.0))
    peristyle, frames = mon.court(52.0, 46.0, 7.0, basin=(20.0, 20.0))
    flavia.merge(peristyle, placement(0.0, 0.0, 0.0))
    court_columns += [(placement(0.0, 0.0, 0.0), frames[::2])]
    flavia.merge(mon.hall(34.0, 30.0, 22.0, mon.PLASTER, roof="vault", windows=3), placement(0.0, -48.0, 0.0))
    for side in (-1, 1):
        flavia.merge(mon.hall(14.0, 26.0, 9.0, mon.PLASTER, roof="gable"), placement(side * 30.0, -48.0, 0.0))
    upper, frames2 = mon.court(62.0, 56.0, 7.0, basin=(26.0, 26.0))
    flavia.merge(upper, placement(88.0, -20.0, 0.0))
    court_columns += [(placement(88.0, -20.0, 0.0), frames2[::2])]
    for x, y, w, d, h in ((88.0, 26.0, 70.0, 16.0, 14.0), (128.0, -20.0, 12.0, 70.0, 16.0),
                          (88.0, -66.0, 70.0, 16.0, 18.0), (52.0, -78.0, 20.0, 20.0, 20.0)):
        flavia.merge(mon.hall(w, d, h, mon.PLASTER, roof="gable"), placement(x, y, 0.0))
    lower, frames3 = mon.court(48.0, 38.0, 6.0, basin=(16.0, 12.0))
    flavia.merge(lower, placement(88.0, -110.0, 0.0))
    court_columns += [(placement(88.0, -110.0, 0.0), frames3[::2])]
    flavia.merge(mon.hall(80.0, 20.0, 14.0, mon.PLASTER, roof="vault", windows=6), placement(88.0, -142.0, 0.0))
    stadium, frames4 = mon.court(150.0, 44.0, 7.0, basin=None)
    flavia.merge(stadium, placement(175.0, -40.0, 0.0, math.pi / 2))
    court_columns += [(placement(175.0, -40.0, 0.0, math.pi / 2), frames4[::3])]
    for x, y, w, d, h, roof in ((-36.0, 0.0, 14.0, 50.0, 11.0, "gable"), (36.0, 0.0, 14.0, 50.0, 11.0, "gable"),
                                (88.0, 52.0, 66.0, 34.0, 15.0, "gable"), (130.0, 52.0, 24.0, 30.0, 20.0, "vault"),
                                (55.0, -110.0, 18.0, 40.0, 12.0, "gable"), (121.0, -110.0, 18.0, 40.0, 12.0, "gable"),
                                (205.0, 30.0, 20.0, 40.0, 14.0, "gable"), (-30.0, -80.0, 22.0, 20.0, 9.0, "gable")):
        flavia.merge(mon.hall(w, d, h, mon.PLASTER, roof=roof, windows=3), placement(x, y, 0.0))
    flavia.box((-45.0, -160.0, -24.0), (215.0, 80.0, -0.3), mon.BRICK, bottom=False, top=True)
    flavia.paint(mon.BRICK, (0.92, 0.82, 0.74))
    flavia.paint(mon.PLASTER, mon.STUCCO_TINT)
    palace = at("flavia", PALACE_BEARING, 0.0)
    for x, y in ((-14.0, 14.0), (14.0, 14.0), (-14.0, -14.0), (14.0, -14.0), (70.0, 0.0), (106.0, 0.0), (70.0, -40.0),
                 (106.0, -40.0), (175.0, -100.0), (175.0, -70.0), (175.0, -10.0), (175.0, 20.0), (162.0, -40.0),
                 (188.0, -40.0)):
        scene.extra_trees.append(("tree_cypress" if (x + y) % 3 else "tree_pine_b", palace @ placement(x, y, 0.1, x,
                                                                                                    0.7)))
    scene.unique("collines", flavia, palace)
    for local, frames in court_columns:
        for f in frames:
            court_columns_world = palace @ local @ f
            scene.add("palace_column", court_columns_world, mon.simple_column())
    tiberiana = MeshBuilder()
    tiberiana.box((-75.0, -55.0, -18.0), (75.0, 55.0, 0.2), mon.BRICK, bottom=False)
    garden, frames5 = mon.court(70.0, 40.0, 6.5, basin=(40.0, 6.0))
    tiberiana.merge(garden, placement(-20.0, 0.0, 0.2))
    for x, y, w, d, h in ((45.0, 0.0, 34.0, 80.0, 16.0), (-20.0, 40.0, 100.0, 14.0, 12.0)):
        tiberiana.merge(mon.hall(w, d, h, mon.PLASTER, roof="gable", windows=5), placement(x, y, 0.2))
    tm = at("tiberiana", 330.0, 0.0)
    for x0, y0, x1, y1, nx, ny in ((-75.0, 57.0, 75.0, 57.0, 0.0, 1.0), (77.0, -55.0, 77.0, 57.0, 1.0, 0.0)):
        outside = [tm @ Vector((x0 + (x1 - x0) * t + nx * 8.0, y0 + (y1 - y0) * t + ny * 8.0, 0.0))
                   for t in (0.1, 0.3, 0.5, 0.7, 0.9)]
        drop = site_level("tiberiana") - min(scene.ground(q.x, q.y) for q in outside)
        if drop > 2.0:
            wall = MeshBuilder()
            span = math.hypot(x1 - x0, y1 - y0)
            mon.wall_run(wall, x0, y0, x1, y1, drop + 1.4, 3.0, mon.BRICK, max(int(span / 9.0), 1))
            tiberiana.merge(wall, Matrix.Translation((0.0, 0.0, -drop)))
    tiberiana.paint(mon.PLASTER, mon.STUCCO_TINT)
    scene.unique("collines", tiberiana, tm)
    for f in frames5:
        scene.add("palace_column", tm @ placement(-20.0, 0.0, 0.2) @ f, mon.simple_column())
    baths = MeshBuilder()
    baths.box((-62.0, -55.0, -14.0), (62.0, 55.0, 0.3), mon.BRICK, bottom=False)
    baths.merge(mon.hall(40.0, 26.0, 26.0, mon.PLASTER, roof="vault", windows=4), placement(0.0, 0.0, 0.3))
    baths.merge(mon.hall(24.0, 24.0, 22.0, mon.PLASTER, roof="dome", windows=2), placement(0.0, -30.0, 0.3))
    for side in (-1, 1):
        palaestra, frames6 = mon.court(30.0, 36.0, 6.0, basin=None, garden=False)
        baths.merge(palaestra, placement(side * 40.0, 10.0, 0.3))
        baths.merge(mon.hall(22.0, 40.0, 16.0, mon.PLASTER, roof="vault"), placement(side * 22.0, 30.0, 0.3))
    for k in range(14):
        baths.box((-30.0, -55.0 - 1.4 * (14 - k), -14.0), (30.0, -55.0 - 1.4 * (13 - k), 0.3 - (13 - k) * 0.9), mon.TRAV,
                  bottom=False)
    baths.paint(mon.PLASTER, mon.STUCCO_TINT)
    bm = at("baths", 202.0, 0.0)
    scene.unique("collines", baths, bm)
    site = MeshBuilder()
    site.box((-110.0, -100.0, -12.0), (110.0, 100.0, 0.2), mon.BRICK, bottom=False)
    site_walls = ((-80.0, -60.0, 80.0, -60.0, 14.0, 9), (-80.0, 60.0, 80.0, 60.0, 9.0, 0),
                  (-80.0, -60.0, -80.0, 60.0, 18.0, 6), (80.0, -60.0, 80.0, 20.0, 6.0, 0),
                  (-30.0, -20.0, 30.0, -20.0, 22.0, 3), (-30.0, 20.0, 30.0, 20.0, 12.0, 0),
                  (-100.0, 95.0, 100.0, 95.0, 5.0, 0))
    for x0, y0, x1, y1, h, arches in site_walls:
        mon.wall_run(site, x0, y0, x1, y1, h, 2.6, mon.BRICK, arches)
    centring = MeshBuilder()
    for k in range(9):
        angle = math.pi * k / 8
        centring.box((-0.12, -30.0, 22.0 + 9.0 * math.sin(angle) - 0.12), (0.12, 30.0, 22.0 + 9.0 * math.sin(angle)),
                     "matte")
    site.merge(centring, placement(0.0, 0.0, 0.0, math.pi / 2))
    tm2 = at("trajan", 210.0, 0.0)
    scene.unique("collines", site, tm2)
    for local in (placement(-60.0, -70.0, 0.2, 0.3), placement(10.0, -30.0, 0.2, 2.0), placement(60.0, 40.0, 0.2, 1.2)):
        scene.add("crane", tm2 @ local, mon.construction_crane)
    for local in (placement(0.0, -63.0, 0.2), placement(-83.0, 0.0, 0.2, math.pi / 2), placement(0.0, -23.0, 0.2)):
        scene.add("scaffold", tm2 @ local, lambda: mon.scaffold(40.0, 16.0))
    heaps = (placement(-40.0, -80.0, 0.2, 0.4), placement(40.0, -80.0, 0.2, -0.3), placement(0.0, 75.0, 0.2, 1.4),
             placement(-55.0, 30.0, 0.2, 0.9))
    for local in heaps:
        scene.add("material_heap", tm2 @ local, mon.material_heap)
    busy = [Vector(v) for v in ((-60.0, -70.0), (10.0, -30.0), (60.0, 40.0), (0.0, -63.0), (-83.0, 0.0), (0.0, -23.0))]
    busy += [local.translation.to_2d() for local in heaps]
    scene.worksites.append((tm2, 95.0, 85.0, [w[:4] for w in site_walls], busy))
    build_aqueduct(scene)
    claud = MeshBuilder()
    claud.box((-92.0, -100.0, -16.0), (92.0, 100.0, 0.3), mon.BRICK, bottom=False)
    mon.wall_run(claud, -92.0, 100.0, 92.0, 100.0, 0.3, 4.0, mon.BRICK, 12)
    garden2, frames7 = mon.court(150.0, 160.0, 6.0, basin=None)
    claud.merge(garden2, placement(0.0, 0.0, 0.3))
    temple, temple_cols = mon.temple(24.0, 40.0, 4.0, 12.0, 1.3, 6, "corinthian", pronaos=2)
    claud.merge(temple, placement(0.0, -20.0, 0.3))
    cm = at("claudium", 22.0, 0.0)
    scene.unique("collines", claud, cm)
    for f in temple_cols["corinthian"]:
        scene.add("palace_column", cm @ placement(0.0, -20.0, 0.3) @ f, mon.simple_column())
    for f in frames7[::3]:
        scene.add("palace_column", cm @ placement(0.0, 0.0, 0.3) @ f, mon.simple_column())
    ludus = MeshBuilder()
    ludus.box((-58.0, -42.0, -4.0), (58.0, 42.0, 0.2), mon.TRAV, bottom=False)
    for x, y, w, d in ((0.0, 37.0, 116.0, 10.0), (0.0, -37.0, 116.0, 10.0), (53.0, 0.0, 10.0, 64.0),
                       (-53.0, 0.0, 10.0, 64.0)):
        ludus.merge(mon.hall(w, d, 9.0, mon.BRICK, roof="gable", windows=10 if w > d else 6),
                    placement(x, y, 0.2, 0.0 if w > d else 0.0))
    arena = MeshBuilder()
    rows = []
    for k in range(9):
        scale = 1.0 + 0.05 * k
        rows.append([Vector((31.5 * scale * math.cos(a), 21.0 * scale * math.sin(a) + 0.0 * k, 0.2 + 0.4 * k))
                     for a in [2 * math.pi * j / 48 for j in range(48)]])
    arena.surface(rows, mon.TRAV, closed=True, facing=(0, 0, 1))
    arena.polygon([(31.5 * math.cos(a), 21.0 * math.sin(a), 0.22) for a in [2 * math.pi * j / 48 for j in range(48)]],
                  "arena_sand")
    ludus.merge(arena, Matrix.Identity(4))
    lm = placement(LUDUS.x, LUDUS.y, DATUM + 1.0 - DATUM, COL_ANGLE)
    scene.unique("collines", ludus, lm)
    for k, (x, y, turn) in enumerate(((-6.0, 2.0, 0.3), (-4.6, 3.4, 3.3), (8.0, -5.0, 1.0), (9.4, -4.0, 4.1),
                                      (0.0, -10.0, 1.6))):
        key = ("fig_murmillo", "fig_thraex", "fig_retiarius", "fig_secutor", "fig_referee")[k]
        build = (life.murmillo, life.thraex, life.retiarius, life.secutor, life.referee)[k]
        scene.add(key, lm @ placement(x, y, 0.22, turn), build)
    peace, peace_frames = mon.portico_ring(PEACE_HALF[0] * 2, PEACE_HALF[1] * 2, height=8.0, depth=7.0, spacing=4.4)
    pm = placement(*forum(*PEACE_F), FORUM_LEVEL + 2.0 - DATUM, FORUM_ANGLE)
    garden3 = MeshBuilder()
    for k in range(6):
        garden3.box((-50.0 + 20.0 * k - 3.0, -40.0, 0.4), (-50.0 + 20.0 * k + 3.0, 40.0, 0.6), "matte")
        garden3.tint(len(garden3.polygons) - 5, (0.38, 0.48, 0.26))
        garden3.box((-50.0 + 20.0 * k - 0.6, -40.0, 0.4), (-50.0 + 20.0 * k + 0.6, 40.0, 0.62), mon.WATER)
    garden3.merge(mon.temple(34.0, 30.0, 2.5, 14.0, 1.5, 6, "corinthian", back_wall=True)[0],
                  placement(0.0, -46.0, 0.4, math.pi))
    scene.unique("collines", peace, pm)
    scene.unique("collines", garden3, pm)
    scene.instances("palatin", "peace_column", mon.simple_column(), [pm @ f for f in peace_frames], cast_shadow=False)
    return {"palace": palace, "baths": bm, "site": tm2, "claudium": cm, "ludus": lm, "peace": pm}


def fora_matrix(name):
    p, _, _, angle, level = fora_rect(name)
    return placement(p.x, p.y, level - DATUM, angle)


def build_fora(scene):
    corinthian, simple = [], []
    for name, build in (("iulium", fora.forum_iulium), ("augustum", fora.forum_augustum),
                        ("nerva", fora.forum_transitorium)):
        builder, frames = build()
        matrix = fora_matrix(name)
        scene.unique("fora", builder, matrix)
        corinthian += [matrix @ f for f in frames["corinthian"]]
        simple += [matrix @ f for f in frames["simple"]]
    scene.instances("fora", "fora_corinthian", mon.simple_column(), corinthian)
    scene.instances("fora", "fora_column", mon.simple_column(), simple)
    builder, walls, cranes, scaffolds, heaps = fora.trajan_worksite()
    matrix = fora_matrix("traiani")
    scene.unique("fora", builder, matrix)
    for local in cranes:
        scene.add("crane", matrix @ local, mon.construction_crane)
    for local in scaffolds:
        scene.add("scaffold", matrix @ local, lambda: mon.scaffold(40.0, 16.0))
    for local in heaps:
        scene.add("material_heap", matrix @ local, mon.material_heap)
    busy = [local.translation.to_2d() for local in cranes + scaffolds + heaps]
    scene.worksites.append((matrix, 95.0, 80.0, walls, busy))
    circus = placement(CIRCUS.x, CIRCUS.y, site_level("circus"), bearing_angle(CIRCUS_BEARING))
    scene.unique("circus", fora.circus_maximus(), circus)


def build_aqueduct(scene):
    samples = ter.densify(AQUEDUCT, 6.0)
    top = max(scene.ground(x, y) for x, y in samples) + 7.0
    builder = MeshBuilder()
    dense = ter.densify(AQUEDUCT, 36.0)
    for a, b in zip(dense[:-1], dense[1:]):
        a, b = Vector(a), Vector(b)
        length = (b - a).length
        base = min(scene.ground(*a.lerp(b, t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)) - 0.3
        segment = fora.aqueduct_segment(length + 0.4, top - base, max(int(round(length / 7.2)), 1))
        middle = (a + b) / 2
        builder.merge(segment, placement(middle.x, middle.y, base, math.atan2(b.y - a.y, b.x - a.x)))
    scene.unique("collines", builder)


class Zones:
    def __init__(self):
        self.tests = []
        self.mask = None
        self.spacing = 2.0

    def rect(self, cx, cy, hx, hy, angle):
        self.tests.append(lambda x, y: rect_distance(x, y, cx, cy, hx, hy, angle) < 0)

    def circle(self, cx, cy, radius):
        self.tests.append(lambda x, y: np.hypot(x - cx, y - cy) < radius)

    def corridor(self, points, width):
        flat = [tuple(p) for p in points]
        self.tests.append(lambda x, y: polyline_distance(flat, x, y) < width)

    def rasterise(self):
        axis = np.arange(-NEAR_HALF, NEAR_HALF + self.spacing, self.spacing)
        grid_x, grid_y = np.meshgrid(axis, axis)
        self.mask = np.zeros(grid_x.shape, dtype=bool)
        for test in self.tests:
            self.mask |= test(grid_x, grid_y)

    def blocked(self, x, y):
        column = int(round((x + NEAR_HALF) / self.spacing))
        row = int(round((y + NEAR_HALF) / self.spacing))
        if not (0 <= row < self.mask.shape[0] and 0 <= column < self.mask.shape[1]):
            return False
        return bool(self.mask[row, column])


def build_zones(points_of_view):
    zones = Zones()
    zones.tests.append(lambda x, y: colosseum_distance(x, y, 86.0) < 0)
    zones.rect(*forum(10.0, -2.0), 160.0, 92.0, FORUM_ANGLE)
    zones.rect(COLOSSUS.x, COLOSSUS.y, 72.0, 62.0, VESTIBULE_ANGLE)
    zones.circle(META.x, META.y, 34.0)
    centre, hx, hy, angle = flat_sites()["flavia"]
    zones.rect(centre.x, centre.y, hx + 20.0, hy + 20.0, angle)
    zones.rect(TIBERIANA.x, TIBERIANA.y, 90.0, 70.0, bearing_angle(330.0))
    zones.rect(TITUS_BATHS.x, TITUS_BATHS.y, 78.0, 85.0, bearing_angle(202.0))
    zones.rect(TRAJAN_SITE.x, TRAJAN_SITE.y, 122.0, 112.0, bearing_angle(210.0))
    zones.rect(CLAUDIUM.x, CLAUDIUM.y, 104.0, 112.0, bearing_angle(22.0))
    zones.rect(LUDUS.x, LUDUS.y, 72.0, 56.0, COL_ANGLE)
    peace = forum(*PEACE_F)
    zones.rect(peace.x, peace.y, PEACE_HALF[0] + 12.0, PEACE_HALF[1] + 12.0, FORUM_ANGLE)
    for name in FORA:
        p, hx, hy, angle, _ = fora_rect(name)
        zones.rect(p.x, p.y, hx + 10.0, hy + 10.0, angle)
    zones.rect(CIRCUS.x, CIRCUS.y, 82.0, 312.0, bearing_angle(CIRCUS_BEARING))
    zones.corridor(AQUEDUCT, 9.0)
    horrea = forum(*HORREA_F)
    zones.rect(horrea.x, horrea.y, 40.0, 30.0, FORUM_ANGLE)
    zones.circle(JUPITER.x, JUPITER.y, 60.0)
    points, _ = sacra_levels()
    zones.corridor(points, 16.0)
    for road in OTHER_ROADS.values():
        zones.corridor(road, 8.0)
    zones.corridor([tuple(ter.FRAME.to_local(*p)) for p in city.RIVER_GEO], 75.0)
    for eye, target in points_of_view:
        zones.corridor([eye.to_2d(), target.to_2d()], 14.0)
    zones.rasterise()
    return zones


FOOTPRINTS = {"insula_court_a": (30.0, 24.0, False), "insula_court_b": (27.0, 22.0, False),
              "insula_block_a": (20.0, 12.0, True), "insula_block_b": (24.0, 13.0, True), "domus_low": (16.0, 11.0, True)}


def build_city(scene, zones, rng):
    keys = list(colisee_city.INSULAE)
    weights = np.array([0.24, 0.2, 0.22, 0.2, 0.14])
    frames = {key: [] for key in keys}
    spots = []
    district = 300.0
    step = 30.0
    limit = NEAR_HALF - 25.0
    cells = int(math.ceil(limit / district))
    for di in range(-cells, cells):
        for dj in range(-cells, cells):
            cx, cy = (di + 0.5) * district, (dj + 0.5) * district
            angle = math.radians(rng.uniform(0.0, 25.0))
            ca, sa = math.cos(angle), math.sin(angle)
            ox, oy = rng.uniform(-step / 2, step / 2), rng.uniform(-step / 2, step / 2)
            for i in range(-6, 7):
                for j in range(-6, 7):
                    lx, ly = i * step + ox, j * step + oy
                    x, y = cx + lx * ca - ly * sa, cy + lx * sa + ly * ca
                    size = step - rng.uniform(4.0, 6.0)
                    half = size / 2
                    corners = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx in (-half, half)
                               for dy in (-half, half)]
                    if any(abs(px - cx) > district / 2 - 1.0 or abs(py - cy) > district / 2 - 1.0 for px, py in corners):
                        continue
                    if abs(x) > limit or abs(y) > limit or rng.random() < 0.04:
                        continue
                    if zones.blocked(x, y) or any(zones.blocked(px, py) for px, py in corners):
                        continue
                    heights = [scene.ground(px, py) for px, py in corners]
                    if max(heights) - min(heights) > 7.0:
                        continue
                    z = min(heights)
                    key = keys[int(rng.choice(len(keys), p=weights / weights.sum()))]
                    fx, fy, paired = FOOTPRINTS[key]
                    turn = angle + math.pi / 2 * int(rng.integers(4))
                    lift = rng.uniform(0.8, 1.3)
                    base = placement(x, y, z, turn)
                    if paired:
                        for side in (-1, 1):
                            frames[key].append(base @ placement(0.0, side * size / 4, 0.0, 0.0 if side < 0 else math.pi,
                                                                (size / fx, size / 2 / fy, lift * rng.uniform(0.9, 1.1))))
                    else:
                        frames[key].append(base @ placement(0.0, 0.0, 0.0, 0.0, (size / fx, size / fy, lift)))
                    spots.append((x, y, z, key))
    for key, matrices in frames.items():
        scene.instances("ville", key, colisee_city.INSULAE[key], matrices)
    grid_angle = math.radians(18.0)
    far = []
    far_rng = random.Random(41)
    for _ in range(7000):
        x, y = far_rng.uniform(-2600, 2600), far_rng.uniform(-2600, 2600)
        r = math.hypot(x, y)
        if max(abs(x), abs(y)) < NEAR_HALF + 10 or r > 2600 * far_rng.uniform(0.75, 1.0):
            continue
        river = float(polyline_distance([tuple(ter.FRAME.to_local(*p)) for p in city.RIVER_GEO], np.array([[x]]),
                                        np.array([[y]]))[0, 0])
        if river < 90.0:
            continue
        z = float(scene.far.sample(x, y)) - DATUM
        far.append(placement(x, y, z - 2.0, grid_angle + far_rng.choice([0.0, math.pi / 2]),
                             (far_rng.uniform(14, 28), far_rng.uniform(10, 20), far_rng.uniform(8, 16))))
    scene.instances("ville_lointaine", "far_block", far_block, far, cast_shadow=False)
    return spots, {key: len(m) for key, m in frames.items()}, len(far)


def far_block():
    builder = MeshBuilder()
    builder.box((-0.5, -0.5, 0.0), (0.5, 0.5, 1.0), "plaster", bottom=False, top=False)
    builder.tint(0, (0.95, 0.86, 0.74))
    for side in (-1, 1):
        builder.oriented([(-0.52, side * 0.52, 1.0), (0.52, side * 0.52, 1.0), (0.52, 0.0, 1.18), (-0.52, 0.0, 1.18)],
                         (0, side, 1), mon.TILES)
    for x, facing in ((-0.5, -1), (0.5, 1)):
        builder.oriented([(x, -0.5, 1.0), (x, 0.5, 1.0), (x, 0.0, 1.18)], (facing, 0, 0), "plaster")
    return builder


def build_trees(scene, zones, rng, spots):
    frames = {key: [] for key in city.TREES}
    houses = KDTree(max(len(spots), 1))
    for index, (x, y, _, _) in enumerate(spots):
        houses.insert((x, y, 0.0), index)
    houses.balance()
    gardens = GARDENS
    near_keys = ["tree_pine", "tree_pine_b", "tree_cypress", "tree_plane", "tree_oak"]
    weights = [0.3, 0.2, 0.25, 0.12, 0.13]
    attempts = 0
    placed = 0
    while placed < 460 and attempts < 12000:
        attempts += 1
        in_garden = rng.random() < 0.8
        if in_garden:
            gx, gy, radius = gardens[int(rng.integers(len(gardens)))]
            angle = rng.uniform(0, 2 * math.pi)
            reach = radius * math.sqrt(rng.random())
            x, y = gx + reach * math.cos(angle), gy + reach * math.sin(angle)
        else:
            x, y = rng.uniform(-NEAR_HALF + 20, NEAR_HALF - 20), rng.uniform(-NEAR_HALF + 20, NEAR_HALF - 20)
        if zones.blocked(x, y) or houses.find_range((x, y, 0.0), 15.0):
            continue
        key = near_keys[int(rng.choice(5, p=weights))]
        if not in_garden:
            key = ("tree_cypress", "tree_plane", "tree_oak")[int(rng.integers(3))]
        if math.hypot(x, y) > 650.0:
            key = city.FAR[key]
        frames[key].append(placement(x, y, scene.lowest(x, y, 1.5) - 0.3, rng.uniform(0, 2 * math.pi),
                                     rng.uniform(0.8, 1.15)))
        placed += 1
    for k in range(40):
        angle = rng.uniform(0, 2 * math.pi)
        x, y = COLOSSUS.x + 42 * math.cos(angle) * rng.uniform(0.2, 1.0), COLOSSUS.y + 32 * math.sin(angle) * rng.uniform(
            0.2, 1.0)
        if math.hypot(x - COLOSSUS.x, y - COLOSSUS.y) < 12.0:
            continue
        frames["tree_cypress" if k % 3 else "tree_plane"].append(
            placement(x, y, VESTIBULE_LEVEL - DATUM, rng.uniform(0, 6.28), rng.uniform(0.55, 0.75)))
    for key, matrix in scene.extra_trees:
        frames[key].append(matrix)
    for key, matrices in frames.items():
        far_key = key.startswith("tree_far")
        name = key
        scene.instances("vegetation", name, city.TREES[key], matrices, cast_shadow=not far_key, occlusion=False)
    return {key: len(m) for key, m in frames.items()}


def viewpoints(scene, arch_matrix, direction, angles):
    pts = {}
    t_e = 3 * math.pi / 2 + 0.26
    eye = amp.oval(t_e, 1.1, 5.6)
    pts["l-arene"] = (col_world(eye), col_world((4.0, -10.0, 4.2)))
    numbered = [k for k in range(14, 42) if amp.bay_number(k) is not None]
    t_f = angles[min(numbered, key=lambda k: abs(angles[k] - (math.pi - 0.36)))]
    facade_eye = col_world(amp.oval(t_f, amp.OUTER + 70.0, 0.0))
    facade_target = col_world(amp.oval(t_f, amp.OUTER, 26.0))
    facade_eye.z = scene.ground(facade_eye.x, facade_eye.y) + 1.7
    pts["la-facade"] = (facade_eye, facade_target)
    zf = FORUM_LEVEL - DATUM
    eye_f = forum(78.0, -10.0)
    target_f = forum(-40.0, 2.0)
    pts["le-forum"] = (Vector((eye_f.x, eye_f.y, zf + 11.0)), Vector((target_f.x, target_f.y, zf + 2.0)))
    arch = arch_matrix.translation
    road_eye = arch.to_2d() - direction * 38.0
    eye_z = scene.ground(road_eye.x, road_eye.y) + 1.75
    pts["la-voie-sacree"] = (Vector((road_eye.x, road_eye.y, eye_z)), Vector((arch.x, arch.y, arch.z + 7.0)))
    pts["vue-d-ensemble"] = (Vector((-780.0, -620.0, 300.0)), Vector((-260.0, 90.0, 0.0)))
    return pts


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
        self.tree = BVHTree.FromPolygons(np.concatenate(vertices).tolist(), np.concatenate(triangles).tolist(),
                                         all_triangles=True)

    def height(self, x, y, hint, reach=3.0):
        hit = self.tree.ray_cast(Vector((x, y, hint + reach)), Vector((0.0, 0.0, -1.0)), reach + 8.0)
        return hint if hit[0] is None else hit[0].z


def resample(points, spacing):
    out = [Vector(points[0])]
    for a, b in zip(points[:-1], points[1:]):
        a, b = Vector(a), Vector(b)
        count = max(int(math.ceil((b - a).length / spacing - 1e-6)), 1)
        for k in range(1, count + 1):
            out.append(a.lerp(b, k / count))
    return out


def ground_route(scene, points, spacing=2.6):
    chain = []
    for p in resample([Vector((p.x, p.y)) for p in points], spacing):
        hint = scene.ground(p.x, p.y)
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


def routes(arch_matrix, direction):
    sacra, _ = sacra_levels()
    arch = arch_matrix.translation.to_2d()
    dense = [p.to_2d() for p in resample(sacra[2:], 2.0)]

    def offset(points, amount):
        result = []
        for index, p in enumerate(points):
            a = points[max(index - 1, 0)]
            b = points[min(index + 1, len(points) - 1)]
            d = (b - a).normalized()
            along = abs((p - arch).dot(direction))
            lateral = 1.4 + (abs(amount) - 1.4) * min(max((along - 8.0) / 12.0, 0.0), 1.0)
            result.append(p + Vector((-d.y, d.x)) * math.copysign(lateral, amount))
        return result
    ring_north = [col_world(amp.oval(t, amp.OUTER + 9.0, 0.0)).to_2d() for t in np.linspace(0.25, math.pi - 0.25, 24)]
    ring_south = [col_world(amp.oval(t, amp.OUTER + 9.0, 0.0)).to_2d() for t in np.linspace(math.pi + 0.25,
                                                                                            2 * math.pi - 0.3, 24)]
    return {
        "voie-sacree-nord": offset(dense, 3.0),
        "voie-sacree-sud": offset(dense, -3.2)[::-1],
        "forum-long": [forum(50.0, 10.0), forum(-50.0, 12.0)],
        "forum-travers": [forum(20.0, -20.0), forum(0.0, 25.0)],
        "forum-sud": [forum(45.0, -18.0), forum(-45.0, -19.0)],
        "anneau-nord": ring_north,
        "anneau-sud": ring_south,
        "labicana": [p + Vector((0.0, 2.0)) for p in OTHER_ROADS["labicana"][:4]],
        "triomphale": [p + Vector((2.0, 0.0)) for p in OTHER_ROADS["triumphalis"][:4]],
        "oppius": [col_world(amp.oval(math.pi / 2 - 0.3, amp.OUTER + 16.0, 0.0)).to_2d()] + OTHER_ROADS["oppius"],
    }


def route_problems(name, chain):
    problems = []
    for index, (a, b) in enumerate(zip(chain[:-1], chain[1:])):
        if abs(b.z - a.z) > 0.35:
            problems.append(f"{name} step {index}: {a.z:.2f} to {b.z:.2f} at {a.x:.1f},{a.y:.1f}")
    j = 0
    for i, a in enumerate(chain):
        j = max(j, i)
        while j < len(chain) and (chain[j].to_2d() - a.to_2d()).length < 2.5:
            j += 1
        if j >= len(chain):
            break
        run = (chain[j].to_2d() - a.to_2d()).length
        grade = abs(chain[j].z - a.z) / run
        if grade > 0.15:
            problems.append(f"{name} grade {grade:.2f} at {i} ({a.x:.1f},{a.y:.1f},{a.z:.2f})")
    return problems


def place_routes(scene, arch_matrix, direction, eyes):
    root = scene.root("life")
    counts = {}
    samples = []
    problems = []
    for name, points in routes(arch_matrix, direction).items():
        chain = ground_route(scene, points)
        problems += route_problems(name, chain)
        for point in chain:
            for eye in eyes:
                if (point.to_2d() - eye.to_2d()).length < EYE_CLEARANCE and abs(point.z + 1.6 - eye.z) < 2.5:
                    raise ValueError(f"route {name} passes too close to a camera")
        for index, point in enumerate(chain):
            new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(point))
        for a, b in zip(chain[:-1], chain[1:]):
            steps = max(int((b - a).length / 0.5), 1)
            samples.extend(a.lerp(b, k / steps).to_2d() for k in range(steps))
        counts[name] = len(chain)
    for problem in problems:
        print("ROUTE", problem, flush=True)
    if problems:
        raise ValueError(f"{len(problems)} route problems")
    return counts, samples


def build_street_life(scene, rng, eyes, targets, route_samples, arch_matrix, direction):
    tree = KDTree(len(route_samples))
    for index, point in enumerate(route_samples):
        tree.insert((point.x, point.y, 0.0), index)
    tree.balance()
    eye2d = [eye.to_2d() for eye in eyes]

    sights = [(eye.to_2d(), target.to_2d()) for eye, target in zip(eyes, targets)]

    def free(x, y, radius=0.7):
        if tree.find_range((x, y, 0.0), radius):
            return False
        point = Vector((x, y))
        if any((point - centre).length < reach for centre, reach in scene.obstacles):
            return False
        for eye, target in sights:
            span = target - eye
            t = max(0.0, min(1.0, (point - eye).dot(span) / span.length_squared))
            if (point - (eye + span * t)).length < 2.2 and (point - eye).length < 30.0:
                return False
        return all((point - e).length > 2.6 for e in eye2d)
    placed = 0
    for k in range(120):
        t = rng.uniform(0, 2 * math.pi)
        d = amp.OUTER + rng.uniform(2.5, 16.0)
        p = col_world(amp.oval(t, d, 0.0))
        if not free(p.x, p.y):
            continue
        inward = col_world(amp.oval(t, amp.OUTER, 0.0)) - p
        turn = heading(inward.to_2d()) + rng.normal(0, 0.8)
        street_figure(scene, rng, p.x, p.y, turn, eye2d)
        placed += 1
    for gate_t in (math.pi / 2, 3 * math.pi / 2, 0.0, math.pi):
        for k in range(18):
            d = amp.OUTER + rng.uniform(1.6, 9.0)
            t = gate_t + rng.normal(0, 0.05)
            p = col_world(amp.oval(t, d, 0.0))
            if not free(p.x, p.y, 0.6):
                continue
            inward = col_world(amp.oval(t, amp.OUTER, 0.0)) - p
            street_figure(scene, rng, p.x, p.y, heading(inward.to_2d()) + rng.normal(0, 0.3), eye2d)
            placed += 1
    sacra, _ = sacra_levels()
    for k in range(60):
        index = int(rng.integers(len(sacra) - 1))
        a, b = sacra[index], sacra[index + 1]
        p = a.lerp(b, rng.random())
        d = (b - a).normalized()
        p = p + Vector((-d.y, d.x)) * rng.uniform(-4.2, 4.2)
        if not free(p.x, p.y):
            continue
        street_figure(scene, rng, p.x, p.y, heading(d) + (math.pi if rng.random() < 0.4 else 0.0) + rng.normal(0, 0.3),
                      eye2d)
        placed += 1
    for k in range(45):
        p = forum(rng.uniform(-55.0, 55.0), rng.uniform(-22.0, 28.0))
        if not free(p.x, p.y):
            continue
        street_figure(scene, rng, p.x, p.y, rng.uniform(0, 2 * math.pi), eye2d)
        placed += 1
    for k in range(18):
        p = forum(rng.uniform(-40.0, 50.0), rng.uniform(-23.5, -22.0))
        if free(p.x, p.y):
            scene.add("fig_toga", placement(p.x, p.y, 0.0, forum_face(0, 1) + rng.normal(0, 0.5)),
                      lambda: person(STREET_LOOKS["fig_toga"]))
    for k in range(10):
        t = rng.uniform(0, 2 * math.pi)
        p = col_world(amp.oval(t, amp.OUTER + rng.uniform(12.0, 16.5), 0.0))
        if free(p.x, p.y, 1.2):
            scene.add("fig_seller", placement(p.x, p.y, 0.0, rng.uniform(0, 6.28)), lambda: seller(187))
    south = col_world(amp.oval(3 * math.pi / 2, amp.OUTER + 6.0, 0.0))
    for k in range(6):
        p = south + Vector((rng.uniform(-6, 6), rng.uniform(-3, 3), 0.0))
        if free(p.x, p.y):
            scene.add("fig_guard", placement(p.x, p.y, 0.0, rng.uniform(0, 6.28)), life.guard)
    for k in range(6):
        p = arch_matrix.translation.to_2d() + direction * rng.uniform(-60, -20) + Vector((rng.uniform(-3, 3),
                                                                                         rng.uniform(-3, 3)))
        if free(p.x, p.y):
            scene.add("fig_lictor", placement(p.x, p.y, 0.0, heading(direction)), life.lictor)
    worker = lambda: coarse(lambda: person(Look("ochre", hem=0.55, skin=2, hair=1, belt="brown", arms="shoulder",
                                                 exomis=True, seed=601)), 0.5)
    for matrix, hx, hy, walls, busy in scene.worksites:
        for k in range(22):
            local = Vector((rng.uniform(-hx, hx), rng.uniform(-hy, hy)))
            near_wall = False
            for x0, y0, x1, y1 in walls:
                a, b = Vector((x0, y0)), Vector((x1, y1))
                t = max(0.0, min(1.0, (local - a).dot(b - a) / max((b - a).length_squared, 1e-9)))
                near_wall = near_wall or (local - a.lerp(b, t)).length < 3.4
            if near_wall or any((local - spot).length < 5.0 for spot in busy):
                continue
            world = matrix @ Vector((local.x, local.y, 0.0))
            scene.add("fig_worker", placement(world.x, world.y, 0.0, rng.uniform(0, 6.28)), worker)
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
            z = scene.standing.height(location.x, location.y, hint + 1.0, 3.0)
            grounded.append(Matrix.Translation((0.0, 0.0, z)) @ matrix)
        scene.placements[key] = grounded


def place_life(scene):
    counts = {}
    for key, matrices in scene.placements.items():
        build = scene.builds[key]
        group = "vie" if key.startswith(("fig_", "prop_")) else "chantier_vie"
        if key == "palace_column":
            group = "palatin"
        scene.instances(group, key, build, matrices, cast_shadow=not key.endswith("_far") and key != "palace_column",
                        occlusion=key in ("palace_column", "crane", "scaffold", "material_heap"))
        counts[key] = len(matrices)
    root = scene.root("life")
    for index, (key, spec) in enumerate(WALKERS.items()):
        mesh = scene.library.mesh(key, lambda spec=spec: person(spec), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return counts


def atmosphere(scene, spots, rng):
    root = scene.root("life")
    chosen = [s for s in spots if 250.0 < math.hypot(s[0], s[1]) < 800.0]
    rng.shuffle(chosen)
    smokes = [Vector((x, y, z + 20.0)) for x, y, z, _ in chosen[:8]]
    smokes.append(Vector((TRAJAN_SITE.x - 60.0, TRAJAN_SITE.y + 50.0, scene.ground(TRAJAN_SITE.x, TRAJAN_SITE.y) + 4.0)))
    vesta = forum(-100.0, -30.0)
    smokes.append(Vector((vesta.x, vesta.y, FORUM_LEVEL - DATUM + 18.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [Vector((0.0, 0.0, 85.0)), Vector((*forum(0.0, 0.0), 40.0)), Vector((FLAVIA.x, FLAVIA.y, 90.0)),
              Vector((COLOSSUS.x, COLOSSUS.y, 60.0)), Vector((TITUS_BATHS.x, TITUS_BATHS.y, 70.0))]
    for index, point in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation(point))
    return len(smokes), len(flocks)


def weathering(scene):
    done = set()
    for obj in scene.roots["colisee"].children_recursive:
        if obj.type == "MESH" and obj.data.name.startswith("col_bay") and obj.data.name not in done:
            done.add(obj.data.name)
            weather(obj, 0.1, seed=7, scale=5.0, grime=0.16, ground=0.0)
    for name, obj in scene.statics.items():
        if name.startswith(("sol", "velarium", "eau", "arene", "foule")):
            continue
        weather(obj, 0.12, seed=len(name), scale=6.0, grime=0.08, ground=0.0)


def preview_world(strength, saturation):
    world = evening_world(SUN_AZIMUTH, SUN_ELEVATION, strength, aerosol=0.5)
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    sky = next(node for node in nodes if node.type == "TEX_SKY")
    grey = nodes.new("ShaderNodeHueSaturation")
    grey.inputs["Saturation"].default_value = saturation
    links.new(sky.outputs["Color"], grey.inputs["Color"])
    warm = nodes.new("ShaderNodeMix")
    warm.data_type = "RGBA"
    warm.blend_type = "MULTIPLY"
    warm.inputs["Factor"].default_value = 1.0
    links.new(grey.outputs["Color"], warm.inputs[6])
    warm.inputs[7].default_value = (1.0, 0.9, 0.78, 1.0)
    lighting = nodes.new("ShaderNodeBackground")
    links.new(warm.outputs[2], lighting.inputs["Color"])
    lighting.inputs["Strength"].default_value = strength
    path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    links.new(lighting.outputs["Background"], mix.inputs[1])
    links.new(nodes["Background"].outputs["Background"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["World Output"].inputs["Surface"])
    return world


def render_previews(options, views):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(views) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    preview_world(float(options.get("sky", 0.12)), float(options.get("saturation", 0.45)))
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, float(options.get("sun", 6.5)), SUN_COLOUR, 0.6)
    haze_volume(stage, 45000.0, 1400.0, float(options.get("haze", 0.00004)), (0.95, 0.85, 0.72), 0.3)
    configure_render(1280, 720, options["samples"], exposure=float(options.get("exposure", 0.0)), volumetric_end=45000.0)
    lenses = {"aerial": 28.0, "arene": 24.0, "facade": 26.0, "forum": 28.0, "voie": 28.0}
    timings = {}
    for name in names:
        eye, target = views[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=lenses.get(name, 28.0))
        rig.data.clip_start = 0.2
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
    extra_materials(tiles, credits)
    near, far, dem_url = ter.build_fields(CACHE, terrain_edits, NEAR_HALF, NEAR_SPACING, FAR_HALF, FAR_SPACING)
    scene = Scene(tiles, near)
    scene.far = far
    rng = np.random.default_rng(107)
    terrain_objects(scene, near, far)
    tiber(scene)
    angles, width, kappas, index, frames, spots = build_colosseum(scene, rng)
    arch_matrix, direction = build_monuments(scene, rng)
    build_fora(scene)
    hills = build_hills(scene, rng)
    points = viewpoints(scene, arch_matrix, direction, angles)
    place_markers(scene, points)
    eyes = [eye for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    near_eye = COL.inverted() @ points["l-arene"][0]
    crowd_bays = build_crowd(scene, angles, width, kappas, index, near_eye)
    build_arena_life(scene, spots, near_eye)
    zones = build_zones([(eye, target) for key, (eye, target) in points.items() if key != "vue-d-ensemble"])
    city_spots, city_counts, far_count = build_city(scene, zones, rng)
    tree_counts = build_trees(scene, zones, rng, city_spots)
    scene.flush(shadowless=("sol", "arene", "foule_proche", "eau"))
    walkable = [obj for name, obj in scene.statics.items() if name.startswith(("sol", "forum"))]
    walkable.append(scene.terrain_object)
    scene.surface = Surface(walkable)
    standing = [obj for name, obj in scene.statics.items() if not name.startswith(("velarium", "foule", "eau"))]
    standing.append(scene.terrain_object)
    scene.standing = Surface(standing)
    route_counts, samples = place_routes(scene, arch_matrix, direction, eyes)
    targets = [target for key, (_, target) in points.items() if key != "vue-d-ensemble"]
    street_count = build_street_life(scene, rng, eyes, targets, samples, arch_matrix, direction)
    ground_placements(scene)
    life_counts = place_life(scene)
    smoke_count, flock_count = atmosphere(scene, city_spots, random.Random(5))
    weathering(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "colisee.glb")
    export_seconds = export_glb(glb, roots)
    report = {"datum_metres": DATUM, "sun": [SUN_AZIMUTH, SUN_ELEVATION], "colosseum_bearing": COL_BEARING,
              "bay_width": width, "crowd_bays_instanced": crowd_bays, "city": city_counts, "far_blocks": far_count,
              "trees": tree_counts, "routes": route_counts, "street_figures": street_count, "life": life_counts,
              "smoke": smoke_count, "flocks": flock_count, "statistics": statistics, "glb_bytes": os.path.getsize(glb),
              "export_seconds": round(export_seconds, 1), "elevation_source": dem_url,
              "elevation_licence": ter.TINITALY_LICENCE, "outer_elevation_source": scene.outer_url,
              "texture_credits": credits,
              "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                          for key, (eye, target) in points.items()}}
    views = {"aerial": points["vue-d-ensemble"], "arene": points["l-arene"], "facade": points["la-facade"],
             "forum": points["le-forum"], "voie": points["la-voie-sacree"]}
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)] for key, (eye, target) in views.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    report["previews"] = render_previews(options, views)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("glb_bytes", "previews", "total_seconds", "routes")}),
          flush=True)


if __name__ == "__main__":
    main()

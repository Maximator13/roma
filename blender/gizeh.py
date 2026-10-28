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

from kit import gizeh_life as glife
from kit import gizeh_monuments as gmon
from kit import gizeh_plan as plan
from kit import gizeh_graffiti as ggraffiti
from kit import gizeh_terrain as gterrain
from kit import gizeh_weather as gweather
from kit import nimes_detail
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.gizeh_materials import build_library, remap
from kit.gizeh_sphinx import sphinx
from kit.materials import baked_material, save_pixels
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, render_still, sun_lamp

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "gizeh")
BLEND = os.path.join(CACHE, "work", "gizeh.blend")
SUN_AZIMUTH = 110.0
SUN_ELEVATION = 14.0
NEAR_TILES = (-1500.0, -1500.0, 1600.0, 2, 8.0, 2048)
MID_TILE = (-9000.0, -15000.0, 32000.0, 120.0, 2048)
FAR_TILE = (-88000.0, -88000.0, 176000.0, 1600.0, 1024)
LENS = 28.0
WALKABLE = ("terrain", "sphinx_court", "causeways", "temples")
SX = plan.SPHINX["x"]
SY = plan.SPHINX["y"]
FLOOR = plan.SPHINX["floor"]
WATER = plan.LEVELS["water"]


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 24}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


class Surface:
    def __init__(self, objects):
        bpy.context.view_layer.update()
        vertices = []
        triangles = []
        offset = 0
        for item in objects:
            mesh = item.data
            co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
            mesh.vertices.foreach_get("co", co)
            mesh.calc_loop_triangles()
            tris = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get("vertices", tris)
            matrix = np.array(item.matrix_world)
            co = co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
            vertices.append(co)
            triangles.append(tris.reshape(-1, 3) + offset)
            offset += len(co)
        self.tree = BVHTree.FromPolygons(np.concatenate(vertices).tolist(), np.concatenate(triangles).tolist(),
                                         all_triangles=True)

    def height(self, x, y, top=260.0, fallback=0.0):
        hit = self.tree.ray_cast(Vector((x, y, top)), Vector((0.0, 0.0, -1.0)), top + 200.0)
        return fallback if hit[0] is None else hit[0].z


class Scene:
    def __init__(self, tiles, terrain):
        self.tiles = tiles
        self.terrain = terrain
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Gizeh")
        self.roots = {}
        self.pending = {}
        self.surface = None
        self.routes = {}
        self.route_samples = []
        self.footprints = []
        self.occupied = []
        self.stair_end = 0.0
        self.altar = None

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.terrain.height(x, y))

    def footing(self, x, y, radius):
        samples = [self.ground(x + dx, y + dy) for dx, dy in ((0, 0), (radius, 0), (-radius, 0), (0, radius),
                                                               (0, -radius))]
        return min(samples)

    def unique(self, group, builder, matrix=None):
        self.pending.setdefault(group, []).append((builder, matrix if matrix is not None else Matrix.Identity(4)))
        self.root(group)

    def flush(self, cast_shadow=None):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(remap(builder), matrix, keep_local=True)
            created = unique_object(f"{group}_static.{len(self.roots[group].children):02d}", merged, self.collection,
                                    self.root(group), self.tiles)
            if cast_shadow is not None and group in cast_shadow:
                created["cast_shadow"] = cast_shadow[group]
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True):
        if not matrices:
            return None
        return self.library.place(key, lambda: remap(build()), self.collection, self.root(group), matrices,
                                  cast_shadow, False)

    def free(self, x, y, radius):
        return all(math.hypot(x - ox, y - oy) > radius + r for ox, oy, r in self.occupied)

    def claim(self, x, y, radius):
        self.occupied.append((x, y, radius))


def build_pyramids(scene):
    for item in plan.GREAT:
        level = scene.terrain.levels[item["key"]]
        scene.unique("pyramids", gmon.great_pyramid(item), Matrix.Translation((item["x"], item["y"], level - 0.3)))
        scene.footprints.append((item["x"], item["y"], item["half_x"], item["half_y"], 0.0, 0.3))
        scene.claim(item["x"], item["y"], item["half_x"] * 1.42 + 6.0)
    for item in plan.QUEENS_EAST + plan.QUEENS_SOUTH:
        level = scene.terrain.levels[item["key"]]
        if item["state"] == "ruined":
            builder = gmon.ruined_pyramid(item)
        elif item["state"] == "stepped":
            builder = gmon.stepped_pyramid(item)
        else:
            builder = gmon.cased_queen(item)
        scene.unique("queens", builder, Matrix.Translation((item["x"], item["y"], level - 0.2)))
        scene.footprints.append((item["x"], item["y"], item["half_x"], item["half_y"], 0.0, 0.25))
        scene.claim(item["x"], item["y"], item["half_x"] * 1.42 + 6.0)


def build_sphinx(scene):
    scene.unique("sphinx", sphinx(), Matrix.Translation((SX, SY, FLOOR)))
    rock, rims = gmon.enclosure(scene.ground)
    scene.unique("enclosure", rock)
    scene.unique("enclosure", gmon.retaining_walls(rims))
    court, stair_end = gmon.stairs_and_terrace(scene.ground)
    scene.stair_end = stair_end
    scene.unique("sphinx_court", court)
    altar_x = plan.PIT["x1"] - 9.0
    scene.altar = Vector((altar_x, SY, FLOOR + 0.12))
    scene.unique("sphinx_court", gmon.altar(), Matrix.Translation(scene.altar))
    dream = gmon.dream_stele()
    scene.unique("sphinx_court", dream, Matrix.Translation((SX + 14.6, SY, FLOOR)) @ Matrix.Rotation(math.pi / 2, 4,
                                                                                                   "Z"))
    scene.unique("sphinx_court", gmon.dream_chapel(SX + 14.6, SY, FLOOR))
    for y, height in ((SY - 8.6, 2.2), (SY + 8.6, 1.9), (SY - 11.8, 1.6)):
        greek = gmon.stele(0.9, height, 0.22, "greek_stele")
        scene.unique("sphinx_court", greek, Matrix.Translation((plan.PIT["x1"] - 1.4, y, FLOOR + 0.12))
                     @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    scene.claim(SX, SY, 60.0)
    scene.claim(SX + 92.0, SY, 48.0)


def build_temples(scene):
    ground = scene.ground
    scene.unique("temples", gmon.khufu_temple(ground))
    scene.unique("temples", gmon.khafre_temple(ground))
    scene.unique("temples", gmon.valley_temple(ground))
    scene.unique("temples", gmon.small_temple(ground, plan.MENKAURE_TEMPLE, 61))
    scene.unique("temples", gmon.small_temple(ground, plan.MENKAURE_VALLEY, 67))
    scene.unique("temples", gmon.isis_temple(ground))
    k = plan.KHENTKAWES
    scene.unique("temples", gmon.khentkawes(), Matrix.Translation((k["x"], k["y"], scene.footing(k["x"], k["y"],
                                                                                                  k["half"]))))
    scene.unique("temples", gmon.crow_wall(ground))
    for box in (plan.KHUFU_TEMPLE, plan.KHAFRE_TEMPLE, plan.MENKAURE_TEMPLE, plan.KHAFRE_VALLEY):
        cx, cy = (box["x0"] + box["x1"]) / 2, (box["y0"] + box["y1"]) / 2
        scene.claim(cx, cy, math.hypot(box["x1"] - box["x0"], box["y1"] - box["y0"]) / 2 + 4.0)
        scene.footprints.append((cx, cy, (box["x1"] - box["x0"]) / 2, (box["y1"] - box["y0"]) / 2, 0.0, 0.18))
    scene.claim(k["x"], k["y"], k["half"] * 1.42 + 4.0)
    scene.claim(plan.ISIS["x"] + 4.0, plan.ISIS["y"], 18.0)
    w = plan.CROW_WALL
    for x in np.arange(w["x0"], w["x1"], 12.0):
        scene.claim(x, w["y"], 9.0)
    scene.unique("distant", gmon.placed_distant(ground))
    scene.unique("distant", gmon.far_landscape(ground))
    k = plan.KHUFU
    scene.unique("graffiti", ggraffiti.graffiti(k, scene.terrain.levels["khufu"] - 0.3))


def build_causeways(scene):
    specs = {"khafre": (5.2, 1.2, (0.3, 1.8), "limestone", "paving", None),
             "khufu": (6.0, 1.4, (0.0, 1.4), "limestone", "basalt", None),
             "menkaure": (4.6, 1.0, (0.2, 1.1), "limestone", "paving", (0.92, 0.84, 0.70))}
    scene.causeway_paths = {}
    for key, (width, wall, heights, material, deck, tint) in specs.items():
        builder, path = gmon.causeway(plan.CAUSEWAYS[key], scene.ground, width, wall, heights, material,
                                      sum(map(ord, key)) % 97, deck, tint)
        scene.unique("causeways", builder)
        scene.causeway_paths[key] = path
        for (x, y), _ in path[::2]:
            scene.claim(x, y, width / 2 + 2.0)


def build_mastabas(scene):
    rng = random.Random(17)
    templates = {"mastaba_a": lambda: gmon.mastaba(24.0, 11.0, 6.0, 1, "limestone", 1.8),
                 "mastaba_b": lambda: gmon.mastaba(20.0, 9.5, 5.0, 2, "core_stone", 1.4),
                 "mastaba_c": lambda: gmon.mastaba(30.0, 13.0, 7.0, 3, "limestone", 2.6),
                 "mastaba_twin": lambda: gmon.mastaba(52.0, 22.0, 8.0, 4, "limestone", 2.2)}
    placed = {key: [] for key in templates}
    f = plan.WEST_FIELD
    for x in np.arange(f["x0"] + 12.0, f["x1"] - 8.0, 26.0):
        for y in np.arange(f["y0"] + 18.0, f["y1"] - 14.0, 40.0):
            if rng.random() < 0.12:
                continue
            key = rng.choice(["mastaba_a", "mastaba_a", "mastaba_b", "mastaba_c"])
            px, py = x + rng.uniform(-2.0, 2.0), y + rng.uniform(-3.0, 3.0)
            if not scene.free(px, py, 14.0):
                continue
            z = scene.footing(px, py, 9.0)
            placed[key].append(Matrix.Translation((px, py, z)) @ Matrix.Rotation(rng.uniform(-0.02, 0.02), 4, "Z"))
            scene.claim(px, py, 15.0)
            scene.footprints.append((px, py, 6.0, 13.0, 0.0, 0.15))
    f = plan.EAST_FIELD
    for x in np.arange(f["x0"] + 22.0, f["x1"] - 10.0, 46.0):
        for y in np.arange(f["y0"] + 30.0, f["y1"] - 20.0, 62.0):
            px, py = x + rng.uniform(-2.0, 2.0), y
            if not scene.free(px, py, 26.0):
                continue
            z = scene.footing(px, py, 14.0)
            placed["mastaba_twin"].append(Matrix.Translation((px, py, z)))
            scene.claim(px, py, 28.0)
    for key, matrices in placed.items():
        scene.instances("mastabas", key, templates[key], matrices)
    return {key: len(v) for key, v in placed.items()}


def place_house(scene, rng, placed, keys, x, y):
    z = scene.footing(x, y, 4.5)
    if z < WATER + 0.4 or not scene.free(x, y, 6.0):
        return False
    if any(math.hypot(x - px, y - py) < 6.5 for px, py in scene.village_lanes):
        return False
    roll = rng.random()
    key = "dovecote" if roll < 0.08 else "granaries" if roll < 0.15 else rng.choice(keys)
    heading = rng.choice((0.0, math.pi / 2, math.pi, -math.pi / 2)) + rng.uniform(-0.12, 0.12)
    placed[key].append(Matrix.Translation((x, y, z + 0.05)) @ Matrix.Rotation(heading, 4, "Z"))
    scene.claim(x, y, 6.0)
    scene.footprints.append((x, y, 5.0, 5.0, heading, 0.2))
    return True


def build_village(scene):
    rng = random.Random(29)
    v = plan.VILLAGE
    placed = {key: [] for key in glife.HOUSES}
    keys = ["house_a", "house_b", "house_c", "house_d", "house_e", "house_f", "house_g", "house_c"]
    for mound, limit in [(v, 96)] + [(h, 18) for h in plan.HAMLETS]:
        count = 0
        for attempt in range(900):
            if count >= limit:
                break
            r = mound["radius"] * math.sqrt(rng.random()) * 0.78
            angle = rng.uniform(0, math.tau)
            x, y = mound["x"] + r * math.cos(angle), mound["y"] + r * math.sin(angle)
            if place_house(scene, rng, placed, keys, x, y):
                count += 1
    for key, matrices in placed.items():
        scene.instances("village", key, glife.HOUSES[key], matrices)
    return {key: len(v) for key, v in placed.items()}


def tree_spots(scene):
    rng = random.Random(31)
    spots = []
    v = plan.VILLAGE
    for k in range(110):
        r = v["radius"] * (0.3 + 0.9 * math.sqrt(rng.random()))
        angle = rng.uniform(0, math.tau)
        spots.append(("palm", v["x"] + r * math.cos(angle), v["y"] + r * math.sin(angle)))
    for points, half in zip(plan.CANALS, plan.CANAL_HALF):
        for x, y in plan.resample_line(points, 26.0):
            if abs(x) > 2600.0 or abs(y) > 2600.0:
                continue
            for side in (-1, 1):
                if rng.random() < 0.5:
                    spots.append(("palm" if rng.random() < 0.8 else "sycamore", x + side * (half + rng.uniform(9, 16)),
                                  y + rng.uniform(-8, 8)))
    for k in range(120):
        x = rng.uniform(900.0, 4200.0)
        y = rng.uniform(-2600.0, 2600.0)
        if scene.terrain.sample("flood", x, y) < 0.9:
            continue
        cluster = rng.randrange(1, 5)
        for c in range(cluster):
            spots.append(("palm" if rng.random() < 0.85 else "sycamore", x + rng.uniform(-14, 14),
                          y + rng.uniform(-14, 14)))
    for x0, x1, y0, y1 in plan.BASINS:
        for k in range(6):
            spots.append(("palm", rng.uniform(x0 - 18, x1 + 18), rng.choice((y0 - 14, y1 + 14))))
    for k in range(90):
        y = rng.uniform(-1500.0, 1400.0)
        x = float(plan.edge_x(y)) + rng.uniform(-30.0, 60.0)
        spots.append((rng.choice(["acacia", "tamarisk", "tamarisk"]), x, y))
    for x, y in plan.resample_line(plan.NILE[3:7], 60.0):
        for side in (-1, 1):
            if rng.random() < 0.3:
                spots.append(("palm", x + side * (plan.NILE_HALF + rng.uniform(40, 120)), y + rng.uniform(-20, 20)))
    return spots


def build_rocks(scene):
    rng = random.Random(53)
    placed = {key: [] for key in glife.ROCKS}
    keys = list(glife.ROCKS)
    for k in range(5200):
        if sum(len(v) for v in placed.values()) >= 520:
            break
        x = rng.uniform(-1400.0, 900.0)
        y = rng.uniform(-1400.0, 1300.0)
        if scene.terrain.sample("flood", x, y) > 0.05 or not scene.free(x, y, 2.5):
            continue
        if any(math.hypot(x - px, y - py) < 6.0 for px, py in scene.village_lanes):
            continue
        near = math.hypot(x - 380.0, y - 0.0) < 700.0
        if not near and rng.random() < 0.55:
            continue
        key = keys[rng.randrange(len(keys))]
        z = scene.ground(x, y) - 0.12
        placed[key].append(Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
                           @ Matrix.Scale(rng.uniform(0.6, 1.5), 4))
    for key, matrices in placed.items():
        scene.instances("rocks", key, glife.ROCKS[key], matrices, cast_shadow=False)
    return {key: len(v) for key, v in placed.items()}


def build_trees(scene):
    rng = random.Random(37)
    placed = {key: [] for key in glife.TREES}
    for kind, x, y in tree_spots(scene):
        if math.hypot(x - SX, y - SY) > 2000.0 or not scene.free(x, y, 3.0):
            continue
        if scene.terrain.sample("canal", x, y) < 2.5 or scene.terrain.sample("nile", x, y) < plan.NILE_HALF + 25:
            continue
        if any(math.hypot(x - px, y - py) < 5.0 for px, py in scene.village_lanes):
            continue
        key = f"palm_{rng.randrange(3)}" if kind == "palm" else kind
        z = scene.ground(x, y) - 0.15
        if z < WATER - 1.5 or (kind != "palm" and z < WATER + 0.2):
            continue
        scale = rng.uniform(0.8, 1.2)
        placed[key].append(Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
                           @ Matrix.Scale(scale, 4))
        scene.claim(x, y, 2.5)
    for key, matrices in placed.items():
        scene.instances("trees", key, glife.TREES[key], matrices, cast_shadow=key != "tamarisk")
    return {key: len(v) for key, v in placed.items()}


def build_ships(scene):
    rng = random.Random(43)
    grouped = {}
    line = plan.resample_line(plan.NILE, 400.0)
    keys = ["barge_set", "barge_set_b", "barge_furled", "merchant_set", "merchant_brailed", "fishing", "fishing_sail",
            "barge_set", "fishing", "galley", "barge_furled", "merchant_set", "fishing_sail"]
    stations = [p for p in line if -4000.0 < p[1] < 4400.0]
    for k, (x, y) in enumerate(stations):
        index = line.index((x, y))
        nx, ny = line[min(index + 1, len(line) - 1)]
        heading = math.atan2(ny - y, nx - x) - math.pi / 2
        for j in range(2 if k % 2 == 0 else 1):
            key = keys[(k * 2 + j) % len(keys)]
            offset = rng.uniform(-plan.NILE_HALF * 0.6, plan.NILE_HALF * 0.6)
            px = x + offset * math.cos(heading + math.pi / 2 + math.pi / 2)
            py = y + rng.uniform(-120.0, 120.0)
            if abs(px - x) > plan.NILE_HALF - 60:
                continue
            flip = math.pi if rng.random() < 0.5 else 0.0
            grouped.setdefault(key, []).append(Matrix.Translation((px, py, WATER))
                                               @ Matrix.Rotation(heading + flip, 4, "Z"))
    placed = 0
    for attempt in range(600):
        if placed >= 26:
            break
        x, y = rng.uniform(830.0, 1700.0), rng.uniform(-900.0, 1300.0)
        if scene.terrain.sample("height", x, y) > WATER - 0.6 or not scene.free(x, y, 8.0):
            continue
        key = rng.choice(["skiff", "skiff", "fishing", "fishing_sail", "skiff"])
        grouped.setdefault(key, []).append(Matrix.Translation((x, y, WATER))
                                           @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z"))
        scene.claim(x, y, 8.0)
        placed += 1
    for key, matrices in grouped.items():
        scene.instances("ships", f"ship_{key}", glife.SHIPS[key], matrices)
    return {key: len(v) for key, v in grouped.items()}


def near_tiles():
    x0, y0, size, count, spacing, resolution = NEAR_TILES
    for i in range(count):
        for j in range(count):
            yield f"{i}{j}", x0 + i * size, y0 + j * size, size, spacing, resolution


def footprint_mask(scene):
    if not scene.footprints:
        return None
    items = np.array(scene.footprints, dtype=np.float64)

    def mask(gx, gy):
        result = np.zeros(gx.shape)
        for cx, cy, half_x, half_y, angle, strength in items:
            c, s = math.cos(angle), math.sin(angle)
            reach = max(half_x, half_y) * 1.5 + 12.0
            rows = np.where((np.abs(gy[:, 0] - cy) < reach))[0]
            columns = np.where((np.abs(gx[0, :] - cx) < reach))[0]
            if len(rows) == 0 or len(columns) == 0:
                continue
            sub_x = gx[np.ix_(rows, columns)] - cx
            sub_y = gy[np.ix_(rows, columns)] - cy
            u = np.abs(sub_x * c + sub_y * s) - half_x
            v = np.abs(-sub_x * s + sub_y * c) - half_y
            outside = np.hypot(np.maximum(u, 0.0), np.maximum(v, 0.0))
            value = strength * np.clip(1.0 - outside / 7.0, 0.0, 1.0)
            block = result[np.ix_(rows, columns)]
            result[np.ix_(rows, columns)] = np.maximum(block, value)
        return result
    return mask


def terrain_object(scene, name, mesh, image):
    material = baked_material(name, image)
    mesh.materials.append(material)
    created = new_object(name, mesh, scene.collection, scene.root("terrain"))
    created["cast_shadow"] = False
    return created


def build_terrain(scene):
    terrain = scene.terrain
    textures = os.path.join(CACHE, "textures")
    footprints = footprint_mask(scene)
    for key, x0, y0, size, spacing, resolution in near_tiles():
        colour = gterrain.bake_tile(terrain, x0, y0, size, resolution, footprints)
        image = save_pixels(f"terrain_{key}", colour, os.path.join(textures, f"terrain_{key}.jpg"), quality=90)
        terrain_object(scene, f"terrain_{key}", gterrain.grid_tile(f"terrain_{key}", terrain, x0, y0, size, spacing,
                                                                   drown=WATER - 0.1), image)
    x0, y0, size, count, _, _ = NEAR_TILES
    near_hole = (x0, y0, x0 + size * count, y0 + size * count)
    mx, my, msize, mspacing, mres = MID_TILE
    colour = gterrain.bake_tile(terrain, mx, my, msize, mres)
    image = save_pixels("terrain_mid", colour, os.path.join(textures, "terrain_mid.jpg"), quality=88)
    terrain_object(scene, "terrain_mid", gterrain.grid_tile("terrain_mid", terrain, mx, my, msize, mspacing,
                                                            near_hole, WATER - 0.1), image)
    fx, fy, fsize, fspacing, fres = FAR_TILE
    colour = gterrain.bake_tile(terrain, fx, fy, fsize, fres)
    image = save_pixels("terrain_far", colour, os.path.join(textures, "terrain_far.jpg"), quality=86)
    terrain_object(scene, "terrain_far", gterrain.grid_tile("terrain_far", terrain, fx, fy, fsize, fspacing,
                                                            (mx, my, mx + msize, my + msize), WATER - 0.1), image)


def build_water(scene):
    terrain = scene.terrain
    root = scene.root("water")
    colour = ((0.66, 0.45, 0.22), (0.46, 0.30, 0.15))
    near = (-1000.0, -3000.0, 3000.0, 3000.0)
    middle = (-2000.0, -26000.0, 14000.0, 30000.0)
    pieces = [
        gterrain.water_mesh("water_flood", terrain, near, 200.0, WATER, colour),
        gterrain.water_mesh("water_flood_mid", terrain, middle, 1000.0, WATER, colour, hole=near),
        gterrain.water_mesh("water_flood_far", terrain, (-90000.0, -90000.0, 90000.0, 90000.0), 8000.0, WATER,
                            colour, hole=middle),
    ]
    for mesh in pieces:
        print("WATER", mesh.name, len(mesh.polygons), flush=True)
        if len(mesh.polygons) == 0:
            continue
        mesh.materials.append(bpy.data.materials["water"])
        created = new_object(mesh.name, mesh, scene.collection, root)
        created["cast_shadow"] = False


def build_surface(scene):
    objects = []
    for name in WALKABLE:
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in [root] + list(root.children_recursive):
            if item.type != "MESH" or item.name.startswith(("terrain_far", "terrain_mid")):
                continue
            objects.append(item)
    scene.surface = Surface(objects)


def resample(points, spacing):
    result = []
    for a, b in zip(points[:-1], points[1:]):
        length = (b - a).length
        steps = max(int(math.ceil(length / spacing)), 1)
        for k in range(steps):
            result.append(a.lerp(b, k / steps))
    result.append(points[-1])
    return result


def add_route(scene, name, points, top=None):
    root = scene.root("life")
    chain = []
    for point in resample([Vector((p[0], p[1], 0.0)) for p in points], 2.5):
        ceiling = top(point) if top else 260.0
        z = scene.surface.height(point.x, point.y, ceiling, scene.ground(point.x, point.y))
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        previous = refined[-1]
        middle = (previous + following) / 2
        ceiling = top(middle) if top else 260.0
        middle.z = scene.surface.height(middle.x, middle.y, ceiling, previous.z)
        if abs(middle.z - (previous.z + following.z) / 2) > 0.04:
            refined.append(middle)
        refined.append(following)
    for index, point in enumerate(refined):
        new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(point))
    scene.routes[name] = refined
    scene.route_samples.extend(point.to_2d() for point in resample(refined, 0.8))
    return len(refined)


def route_report(scene):
    report = {}
    for name, points in scene.routes.items():
        worst = 0.0
        longest = 0.0
        for a, b in zip(points[:-1], points[1:]):
            worst = max(worst, abs(b.z - a.z))
            longest = max(longest, (b - a).length)
        report[name] = {"points": len(points), "max_step": round(worst, 2), "max_spacing": round(longest, 2),
                        "z_range": [round(min(p.z for p in points), 2), round(max(p.z for p in points), 2)]}
    return report


def build_routes(scene):
    counts = {}
    path = [p for p, _ in scene.causeway_paths["khafre"]]
    counts["chaussee"] = add_route(scene, "chaussee", path[1:-1], lambda p: scene.ground(p.x, p.y) + 6.0)
    top = scene.stair_end
    sphinx_route = [(top + 9.0, SY - 1.0), (top + 1.0, SY - 1.0), (plan.PIT["x1"] - 2.0, SY - 1.0),
                    (plan.PIT["x1"] - 6.0, SY + 5.0), (SX + 40.0, SY + 13.5), (SX + 10.0, SY + 15.5),
                    (SX - 20.0, SY + 15.5), (SX - 40.0, SY + 12.0)]
    counts["sphinx"] = add_route(scene, "sphinx", sphinx_route, lambda p: 32.0)
    counts["plateau_est"] = add_route(scene, "plateau_est", [(1040.0, -70.0)] + plan.TRACKS[0][:3]
                                      + [(top + 30.0, SY + 4.0), (top + 10.0, SY + 2.0)])
    k = plan.KHUFU
    e = k["x"] + k["half_x"] + 7.0
    n = k["y"] + k["half_y"] + 7.0
    temple = plan.KHUFU_TEMPLE
    counts["grande_pyramide"] = add_route(scene, "grande_pyramide",
                                          [(e, k["y"] - 105.0), (e, k["y"] - 40.0), (e, temple["y0"] - 5.0)])
    counts["pyramide_nord"] = add_route(scene, "pyramide_nord",
                                        [(e, temple["y1"] + 6.0), (e, n), (k["x"] + 40.0, n), (k["x"] - 60.0, n + 1.0)])
    counts["reines"] = add_route(scene, "reines", [(592.0, 140.0), (592.0, 192.0), (590.0, 245.0), (588.0, 300.0),
                                                   (580.0, 335.0)])
    v = plan.VILLAGE
    lane = [(v["x"] - 140.0, v["y"] + 15.0), (v["x"] - 90.0, v["y"] + 5.0), (v["x"], v["y"]),
            (v["x"] + 80.0, v["y"] - 30.0), (v["x"] + 140.0, v["y"] - 20.0)]
    counts["village"] = add_route(scene, "village", lane)
    dyke = [(1473.0, -600.0), (1433.0, 200.0), (1373.0, 550.0)]
    counts["digue"] = add_route(scene, "digue", dyke)
    return counts


def village_lanes():
    v = plan.VILLAGE
    lane = [(v["x"] - 180.0, v["y"] + 20.0), (v["x"] - 90.0, v["y"] + 5.0), (v["x"], v["y"]),
            (v["x"] + 80.0, v["y"] - 30.0), (v["x"] + 170.0, v["y"] - 20.0)]
    points = plan.resample_line(lane, 4.0) + plan.resample_line(plan.TRACKS[0], 4.0)
    points += plan.resample_line(plan.TRACKS[1][:3], 4.0) + plan.resample_line(plan.TRACKS[2][:3], 4.0)
    return points


def clear_of_routes(scene, x, y, radius):
    point = Vector((x, y))
    return all((point - sample).length > radius for sample in scene.route_samples[::2])


def populate(scene, eyes):
    rng = random.Random(131)
    placed = {}

    def settle(x, y, spread):
        best = None
        for attempt in range(12):
            px = x + (rng.uniform(-6.0, 6.0) if attempt else 0.0)
            py = y + (rng.uniform(-6.0, 6.0) if attempt else 0.0)
            samples = [scene.surface.height(px + dx, py + dy, 260.0, scene.ground(px + dx, py + dy))
                       for dx, dy in ((0, 0), (spread, 0), (-spread, 0), (0, spread), (0, -spread))]
            spread_z = max(samples) - min(samples)
            if best is None or spread_z < best[0]:
                best = (spread_z, px, py, sorted(samples)[2])
            if spread_z < 0.08:
                break
        return best[1], best[2], best[3] - 0.02

    def put(key, x, y, heading, radius=1.4, z=None, check=True, lean=0.0):
        if z is None:
            x, y, height = settle(x, y, max(radius, 1.0))
        else:
            height = z
        if check and not clear_of_routes(scene, x, y, radius):
            return False
        if check and min((Vector((x, y)) - eye).length for eye in eyes) < 9.0:
            return False
        if z is None and height < WATER + 0.15:
            return False
        placed.setdefault(key, []).append(Matrix.Translation((x, y, height)) @ Matrix.Rotation(heading, 4, "Z")
                                          @ Matrix.Rotation(-lean, 4, "X"))
        return True

    k = plan.KHUFU
    base = scene.terrain.levels["khufu"] - 0.3
    corner = Vector((k["x"] + k["half_x"], k["y"] + k["half_y"]))
    for index, h in enumerate((2.2, 6.5, 11.0, 17.5)):
        t = 1.0 - h / k["height"]
        x = k["x"] + k["half_x"] * t + 0.03
        y = k["y"] + k["half_y"] * t - 1.2 - index * 0.4
        put("climber" if index % 2 == 0 else "climber_b", x, y, math.pi / 2 + rng.uniform(-0.15, 0.15), z=base + h,
            check=False, lean=math.radians(rng.uniform(14.0, 20.0)))
    put("guide_group", corner.x + 12.0, corner.y + 4.0, 2.4)
    put("visitors", corner.x + 15.0, corner.y - 18.0, 1.9)
    put("visitors_b", k["x"] + 12.0, k["y"] + k["half_y"] + 18.0, math.pi)
    put("camels", k["x"] - 40.0, k["y"] + k["half_y"] + 30.0, 0.6, 3.0)
    put("guards", k["x"] + k["half_x"] + 20.0, k["y"] - 60.0, -math.pi / 2)
    altar = scene.altar
    put("priests", altar.x + 0.0, altar.y - 2.4, math.pi / 2 + 0.0, z=altar.z, check=False)
    top = scene.stair_end
    put("guards", top + 3.0, SY + 9.0, math.pi / 2, z=plan.TERRACE["top"], check=False)
    put("visitors", top + 4.0, SY + 12.0, math.pi / 2 + 0.5, z=plan.TERRACE["top"], check=False)
    put("visitors_b", plan.PIT["x1"] - 16.0, SY + 9.0, math.pi / 2 + 0.4)
    put("guide_group", SX + 44.0, SY - 14.0, math.pi / 2 + 0.6)
    put("litter", top + 40.0, SY + 20.0, math.pi / 2 + 0.2, 3.0)
    put("donkey_driver", top + 60.0, SY - 18.0, math.pi / 2, 2.0)
    for x, y, key, heading in ((585.0, 172.0, "visitors", 1.4), (600.0, 214.0, "fig_roman", 2.0),
                               (606.0, 262.0, "water_carriers", 3.0), (575.0, 216.0, "priests", -math.pi / 2)):
        put(key, x, y, heading)
    for x, y, key, heading in ((420.0, -40.0, "camel_train", 1.9), (300.0, -10.0, "donkey_driver", 1.8),
                               (250.0, 470.0, "visitors", 0.0), (60.0, 150.0, "camels", 0.4),
                               (-250.0, -150.0, "goats", 0.0), (820.0, -260.0, "camel_train", 2.6),
                               (520.0, -330.0, "donkey_driver", 1.6), (-140.0, 440.0, "fig_villager", 0.5),
                               (180.0, -120.0, "guards", 1.0), (-60.0, 160.0, "visitors_b", 2.0)):
        put(key, x, y, heading, 3.0)
    v = plan.VILLAGE
    for k in range(26):
        r = v["radius"] * math.sqrt(rng.random())
        angle = rng.uniform(0, math.tau)
        x, y = v["x"] + r * math.cos(angle), v["y"] + r * math.sin(angle)
        if not scene.free(x, y, 1.5):
            continue
        key = rng.choice(["fig_villager", "fig_woman", "water_carriers", "donkey", "goats", "fig_villager",
                          "fig_woman", "cattle"])
        if put(key, x, y, rng.uniform(0, math.tau), 1.6):
            scene.claim(x, y, 2.0)
    canal = plan.CANALS[0]
    for index, (x, y) in enumerate(plan.resample_line(canal, 90.0)[3:20]):
        side = -1 if index % 2 else 1
        px = x + side * (plan.CANAL_HALF[0] + 3.5)
        key = ["shaduf", "hoeing", "cattle", "saqiya", "hoeing", "water_carriers", "goats"][index % 7]
        heading = 0.0 if side > 0 else math.pi
        if key == "shaduf":
            heading = math.pi if side > 0 else 0.0
        put(key, px if key == "shaduf" else px + side * 12.0, y, heading, 3.0)
    for k in range(30):
        x = rng.uniform(820.0, 2400.0)
        y = rng.uniform(-900.0, 1300.0)
        if scene.terrain.sample("flood", x, y) < 0.95 or scene.terrain.sample("canal", x, y) < 6.0:
            continue
        if not scene.free(x, y, 6.0):
            continue
        key = rng.choice(["hoeing", "hoeing", "cattle", "goats", "water_carriers", "fig_villager"])
        put(key, x, y, rng.uniform(0, math.tau), 3.0)
    counts = {}
    for key, matrices in placed.items():
        scene.instances("life", key, glife.LIFE[key], matrices, cast_shadow=True)
        counts[key] = len(matrices)
    return counts


def place_effects(scene):
    root = scene.root("life")
    smokes = [scene.altar + Vector((0.0, 0.0, 1.4))]
    v = plan.VILLAGE
    for dx, dy in ((-60.0, 40.0), (70.0, -50.0), (20.0, 110.0), (-110.0, -60.0)):
        x, y = v["x"] + dx, v["y"] + dy
        smokes.append(Vector((x, y, scene.ground(x, y) + 4.0)))
    smokes.append(Vector((60.0 + 6.0, 150.0, scene.ground(66.0, 150.0) + 1.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(Vector((1500.0, 300.0)), 45.0), (Vector((2400.0, -600.0)), 60.0), (Vector((900.0, 700.0)), 35.0),
              (Vector((300.0, 200.0)), 190.0), (Vector((-150.0, -250.0)), 120.0), (Vector((7200.0, 0.0)), 40.0)]
    for index, (point, height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root,
                  Matrix.Translation((point.x, point.y, scene.ground(point.x, point.y) + height)))
    for index, (key, build) in enumerate(glife.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke": len(smokes), "birds": len(flocks), "walkers": len(glife.WALKERS)}


def weather_all(scene):
    done = set()
    patina = {"pyramids": 1.0, "queens": 0.8, "sphinx": 0.7, "enclosure": 0.5}
    for name, root in scene.roots.items():
        if name in ("terrain", "water", "markers", "life", "trees", "ships", "rocks", "graffiti", "distant"):
            continue
        for item in root.children_recursive:
            if item.type != "MESH" or item.data.name in done:
                continue
            mesh = item.data
            done.add(mesh.name)
            seed = sum(ord(character) for character in mesh.name) % 97
            heights = None
            if item.parent is root:
                co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
                mesh.vertices.foreach_get("co", co)
                co = co.reshape(-1, 3)
                heights = co[:, 2] - scene.terrain.height(co[:, 0], co[:, 1])
            gweather.weather(mesh, heights, seed, 2.4 if name in ("pyramids", "queens") else 1.6,
                             patina.get(name, 0.35))
            if name in ("temples", "village", "mastabas", "enclosure", "sphinx") and len(
                    mesh.vertices) < 60000:
                nimes_detail.occlusion(mesh, seed)


def viewpoints(scene):
    points = {}
    kh = plan.KHUFU
    level = scene.terrain.levels["khufu"]
    points["vue-d-ensemble"] = (Vector((1350.0, -1200.0, 130.0)), Vector((557.0, -170.0, 45.0)))
    eye = Vector((kh["x"] + kh["half_x"] + 17.0, kh["y"] + kh["half_y"] + 19.0))
    points["la-grande-pyramide"] = (Vector((eye.x, eye.y, max(scene.ground(eye.x, eye.y), level - 0.15) + 1.6)),
                                    Vector((kh["x"] + 70.0, kh["y"] + 62.0, level + 22.0)))
    top = scene.stair_end
    points["le-sphinx"] = (Vector((top + 12.0, SY - 4.0, plan.TERRACE["top"] + 4.0)),
                           Vector((SX + 10.0, SY - 2.0, FLOOR + 8.0)))
    eye = Vector((600.0, 150.0))
    points["les-pyramides-de-la-reine"] = (Vector((eye.x, eye.y, scene.ground(eye.x, eye.y) + 1.7)),
                                          Vector((470.0, 330.0, scene.terrain.levels["g1b"] + 25.0)))
    eye = Vector((420.0, 260.0))
    points["le-plateau"] = (Vector((eye.x, eye.y, scene.ground(eye.x, eye.y) + 80.0)), Vector((-200.0, -380.0, 50.0)))
    return points


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))


def render_previews(options, points):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(points) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.28, aerosol=0.3)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 6.0, (1.0, 0.76, 0.50), 0.8)
    bounce = sun_lamp(stage, 330.0, 15.0, 1.4, (1.0, 0.78, 0.52), 20.0)
    bounce.data.use_shadow = False
    configure_render(int(options.get("width", 1280)), int(options.get("height", 720)), options["samples"],
                     exposure=0.0)
    view = bpy.context.scene.view_settings
    try:
        view.view_transform = "Khronos PBR Neutral"
        view.look = "None"
    except TypeError:
        view.look = "AgX - Punchy"
    timings = {}
    for name in names:
        eye, target = points[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=LENS, clip_end=180000.0)
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
        if options.get("views"):
            with open(options["views"], encoding="utf8") as handle:
                extra = json.load(handle)
            views.update({key: (Vector(eye), Vector(target)) for key, (eye, target) in extra.items()})
        print("PREVIEWS", json.dumps(render_previews(options, views)), flush=True)
        return
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tiles, credits = build_library(CACHE)
    ggraffiti.graffiti_material(CACHE)
    tiles["graffiti"] = 1.0
    dem = gterrain.load_dem(CACHE)
    terrain = gterrain.Terrain(dem)
    del dem
    print("FIELDS", round(time.perf_counter() - started, 1), json.dumps({k: round(v, 2) for k, v in
                                                                         terrain.levels.items()}), flush=True)
    scene = Scene(tiles, terrain)
    scene.village_lanes = village_lanes()
    build_pyramids(scene)
    build_sphinx(scene)
    build_temples(scene)
    build_causeways(scene)
    mastaba_counts = build_mastabas(scene)
    village_counts = build_village(scene)
    tree_counts = build_trees(scene)
    rock_counts = build_rocks(scene)
    ship_counts = build_ships(scene)
    scene.flush({"graffiti": False, "distant": False})
    print("MONUMENTS", round(time.perf_counter() - started, 1), flush=True)
    build_terrain(scene)
    build_water(scene)
    print("TERRAIN", round(time.perf_counter() - started, 1), flush=True)
    build_surface(scene)
    points = viewpoints(scene)
    place_markers(scene, points)
    route_counts = build_routes(scene)
    eyes = [eye.to_2d() for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    life_counts = populate(scene, eyes)
    effects = place_effects(scene)
    weather_all(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "gizeh.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION], "levels": {k: round(v, 2) for k, v in terrain.levels.items()},
        "counts": {"mastabas": mastaba_counts, "village": village_counts, "trees": tree_counts, "rocks": rock_counts, "ships": ship_counts,
                   "routes": route_counts, "life": life_counts, "effects": effects},
        "route_checks": route_report(scene),
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "build_seconds": round(time.perf_counter() - started, 1), "terrain_source": gterrain.SOURCE,
        "texture_credits": credits,
        "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                    for key, (eye, target) in points.items()},
    }
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in points.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("BUILD", round(time.perf_counter() - started, 1), flush=True)
    print("PREVIEWS", json.dumps(render_previews(options, points)), flush=True)


main()

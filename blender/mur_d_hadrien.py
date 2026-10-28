import hashlib
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

from kit import mur_d_hadrien_fort as fort
from kit import mur_d_hadrien_life as hlife
from kit import mur_d_hadrien_plan as plan
from kit import mur_d_hadrien_terrain as hterrain
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, save_pixels
from kit.pompei_terrain import smoothstep, world_noise
from kit.mur_d_hadrien_materials import build_library, remap
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, render_still, sun_lamp

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "mur-d-hadrien")
BLEND = os.path.join(CACHE, "work", "mur-d-hadrien.blend")
SUN_AZIMUTH = 245.0
SUN_ELEVATION = 17.0
LENS = 28.0
WALKABLE = ("terrain", "vallum", "walls")


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 16}
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

    def height(self, x, y, top=900.0, fallback=0.0):
        hit = self.tree.ray_cast(Vector((x, y, top)), Vector((0.0, 0.0, -1.0)), top + 400.0)
        return fallback if hit[0] is None else hit[0].z


class Scene:
    def __init__(self, tiles, terrain):
        self.tiles = tiles
        self.terrain = terrain
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("MurDHadrien")
        self.roots = {}
        self.pending = {}
        self.ground_surface = None
        self.surface = None
        self.routes = {}
        self.route_samples = []
        self.occupied = []
        self.smokes = []
        self.wall_points = []
        self.wall_stations = []
        self.features = {}

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        if self.ground_surface is not None:
            return self.ground_surface.height(x, y, 900.0, float(self.terrain.height(x, y)))
        return float(self.terrain.height(x, y))

    def top(self, x, y):
        return float(self.terrain.ground(x, y)) + 3.0

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


def south_gate():
    return plan.fort_point(plan.STREET_U, -plan.FORT["half_v"])


def crossing_station():
    gate = south_gate() + Vector((0.0, -1.0))
    direction = Vector((-math.sin(plan.FORT["angle"]), -math.cos(plan.FORT["angle"])))
    best = None
    for k in range(0, 400):
        p = gate + direction * k * 0.5
        distance, station, _ = plan.polyline_distance(plan.VALLUM_SMOOTH, np.array([p.x]), np.array([p.y]))
        if best is None or distance[0] < best[0]:
            best = (float(distance[0]), float(station[0]))
    return best[1]


def tracks(crossing):
    centre, _ = plan.along(plan.VALLUM_SMOOTH, crossing)
    gate_s = south_gate()
    fp = plan.fort_point
    hu, hv = plan.FORT["half_u"], plan.FORT["half_v"]
    south = [tuple(fp(plan.STREET_U, -hv - 2.0)), tuple(gate_s.lerp(centre, 0.5) + Vector((-2.0, 0.0))),
             tuple(centre), (centre.x - 25.0, centre.y - 120.0), (centre.x - 70.0, centre.y - 330.0),
             (centre.x - 60.0, centre.y - 700.0), (centre.x - 110.0, centre.y - 1100.0)]
    east = [tuple(fp(hu + 2.0, 0.0)), tuple(fp(hu + 45.0, 4.0)), (190.0, 38.0), (226.0, 46.0)]
    north = [tuple(fp(plan.STREET_U, hv + 2.0)), tuple(fp(plan.STREET_U - 6.0, hv + 40.0)), (-30.0, 190.0),
             (-70.0, 330.0), (-150.0, 520.0)]
    west = [tuple(fp(-hu - 2.0, 0.0)), (-160.0, -38.0), (-260.0, -62.0), (-360.0, -88.0),
            (plan.MILECASTLE_37[0] + 3.0, plan.MILECASTLE_37[1] - 22.0)]
    return {"sud": plan.chaikin(south, 2), "est": plan.chaikin(east, 2), "nord": plan.chaikin(north, 2),
            "ouest": plan.chaikin(west, 2)}


def cached_bake(name, spec, bake):
    sources = [hterrain.__file__, plan.__file__]
    text = "".join(open(path, encoding="utf8").read() for path in sources)
    key = hashlib.md5(repr((text, name, spec)).encode("utf8")).hexdigest()[:16]
    path = os.path.join(CACHE, "work", f"bake_{name}_{key}.npy")
    if os.path.exists(path):
        return np.load(path).astype(np.float64)
    colour = bake()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, colour.astype(np.float16))
    return colour


def build_terrain(scene):
    terrain = scene.terrain
    root = scene.root("terrain")
    textures = os.path.join(CACHE, "textures")
    tiles = [("terrain_core_west", plan.CORE_WEST, None, True, True),
             ("terrain_core_east", plan.CORE_EAST, None, True, True), ("terrain_near", plan.NEAR, plan.CORE, False, True),
             ("terrain_mid", plan.MID, plan.NEAR, False, False), ("terrain_far", plan.FAR, plan.MID, False, False)]
    for name, (x0, y0, w, h, spacing, resolution), hole, detail, near in tiles:
        colour = cached_bake(name, (x0, y0, w, h, resolution), lambda: hterrain.bake_tile(
            terrain, x0, y0, w, h, resolution, detail, near))
        image = save_pixels(name, colour, os.path.join(textures, f"{name}.jpg"), quality=88)
        material = baked_material(name, image)
        hole_rect = None if hole is None else (hole[0], hole[1], hole[0] + hole[2], hole[1] + hole[3])
        mesh = hterrain.tile_mesh(name, terrain, x0, y0, w, h, spacing, hole_rect, sink=2.0)
        mesh.materials.append(material)
        created = new_object(name, mesh, scene.collection, root)
        created["cast_shadow"] = False
        print("TILE", name, len(mesh.polygons), flush=True)


def build_water(scene):
    root = scene.root("water")
    for name, lake in scene.terrain.lakes.items():
        mesh = hterrain.water_plane(f"water_{name}", scene.terrain, lake["box"], lake["level"], 12.0, scene.terrain.lake_masks[name])
        if len(mesh.polygons) == 0:
            continue
        mesh.materials.append(bpy.data.materials["water"])
        created = new_object(mesh.name, mesh, scene.collection, root)
        created["cast_shadow"] = False


def build_vallum(scene, crossing):
    mesh = hterrain.vallum_strip(scene.terrain, plan.VALLUM_SMOOTH, crossing)
    mesh.materials.append(bpy.data.materials["ground_vallum"])
    created = new_object("vallum_strip", mesh, scene.collection, scene.root("vallum"))
    created["cast_shadow"] = False


def ground_surface(scene):
    objects = [item for item in scene.root("terrain").children if item.name.startswith(("terrain_core", "terrain_near"))]
    scene.ground_surface = Surface(objects)


def frames_of(points):
    result = []
    count = len(points)
    for index, (x, y) in enumerate(points):
        a = Vector(points[max(index - 1, 0)])
        b = Vector(points[min(index + 1, count - 1)])
        tangent = (b - a).normalized()
        result.append((Vector((x, y)), tangent, Vector((-tangent.y, tangent.x))))
    return result


def wall_stations(scene, points, outward=1.0, closed=False):
    frames = frames_of(points)
    centre = []
    rows = []
    for p, tangent, left in frames:
        n = left * outward
        samples = [scene.ground(*(p + n * o)) for o in (-1.5, -0.6, 0.4, 1.3)]
        inner = scene.ground(*(p - n * 1.6))
        rows.append((min(samples + [inner]), inner, max(samples)))
        centre.append(scene.ground(*p))
    centre = np.array(centre)
    window = 7
    padded = np.pad(centre, window // 2, mode="wrap" if closed else "edge")
    smooth = np.convolve(padded, np.ones(window) / window, mode="valid")
    stations = []
    for (p, _, _), (low, inner, high), s in zip(frames, rows, smooth):
        walk = max(s, high - 0.8) + fort.WALK
        stations.append((p.x, p.y, low - 0.8, inner, walk))
    return stations


def arc_lengths(points):
    return np.array(plan.stations(points))


def split_runs(stations, lengths, gaps):
    def blend(a, b, t):
        return tuple(x + (y - x) * t for x, y in zip(a, b))

    def inside(s):
        return any(a <= s <= b for a, b in gaps)
    runs = []
    current = []
    for index, (station, s) in enumerate(zip(stations, lengths)):
        if inside(s):
            if current:
                previous_s = lengths[index - 1]
                edge = min(a for a, b in gaps if a <= s <= b)
                current.append(blend(stations[index - 1], station, (edge - previous_s) / max(s - previous_s, 1e-6)))
                if len(current) > 1:
                    runs.append(current)
            current = []
            continue
        if not current and index > 0 and inside(lengths[index - 1]):
            previous_s = lengths[index - 1]
            edge = max(b for a, b in gaps if a <= previous_s <= b)
            current.append(blend(stations[index - 1], station, (edge - previous_s) / max(s - previous_s, 1e-6)))
        current.append(station)
    if len(current) > 1:
        runs.append(current)
    return runs


def wall_frame(points, lengths, s):
    index = int(np.clip(np.searchsorted(lengths, s), 1, len(points) - 1))
    a = Vector(points[index - 1])
    b = Vector(points[index])
    t = (s - lengths[index - 1]) / max(lengths[index] - lengths[index - 1], 1e-6)
    p = a.lerp(b, t)
    tangent = (Vector(points[min(index + 2, len(points) - 1)]) - Vector(points[max(index - 3, 0)])).normalized()
    return p, tangent


def frame_matrix(p, tangent, z, outward=1.0):
    x_axis = Vector((tangent.x, tangent.y, 0.0)) * outward
    y_axis = Vector((-tangent.y, tangent.x, 0.0)) * outward
    matrix = Matrix((x_axis, y_axis, Vector((0.0, 0.0, 1.0)))).transposed().to_4x4()
    matrix.translation = Vector((p.x, p.y, z))
    return matrix


def footprint_ground(scene, matrix, x0, x1, y0, y1):
    values = []
    for u in np.linspace(x0, x1, 4):
        for v in np.linspace(y0, y1, 4):
            w = matrix @ Vector((u, v, 0.0))
            values.append(scene.ground(w.x, w.y))
    return min(values), max(values), float(np.mean(values))


def build_walls(scene):
    points = scene.wall_points
    lengths = arc_lengths(points)
    stations = wall_stations(scene, points)
    scene.wall_stations = stations
    walk_at = lambda s: float(np.interp(s, lengths, [st[4] for st in stations]))
    north_gate = plan.fort_point(plan.STREET_U, plan.FORT["half_v"])
    s_north = plan.nearest_station(points, north_gate.x, north_gate.y)
    s_mc37 = plan.nearest_station(points, *plan.MILECASTLE_37)
    milecastles = [s_mc37 + k * plan.ROMAN_MILE for k in range(-3, 4)]
    milecastles = [s for s in milecastles if 40.0 < s < lengths[-1] - 40.0]
    turrets = []
    for s in milecastles + [milecastles[0] - plan.ROMAN_MILE]:
        for k in (1, 2):
            t = s + k * plan.ROMAN_MILE / 3
            if 30.0 < t < lengths[-1] - 30.0 and abs(t - s_north) > 140.0:
                turrets.append(t)
    gaps = [(s_north - 7.0, s_north + 7.0)] + [(s - 2.2, s + 2.2) for s in milecastles]
    builder = MeshBuilder()
    runs = split_runs(stations, lengths, gaps)
    for run in runs:
        fort.wall_run(builder, run)
    p, tangent = wall_frame(points, lengths, s_north)
    z = scene.ground(p.x, p.y)
    scene.features["north_gate"] = (p, tangent, z)
    gate = fort.gate(depth_below=6.0)
    builder.merge(gate, frame_matrix(p, tangent, z))
    for index, s in enumerate(milecastles):
        p, tangent = wall_frame(points, lengths, s)
        walk = walk_at(s)
        matrix = frame_matrix(p, tangent, walk - fort.WALK)
        low, high, _ = footprint_ground(scene, matrix, -8.8, 8.8, -14.0, 1.0)
        depth = walk - fort.WALK - low + 1.0
        builder.merge(fort.milecastle(depth_below=max(depth, 2.0)), matrix)
        scene.features.setdefault("milecastles", []).append((p, tangent, walk - fort.WALK, s))
        scene.claim(p.x - tangent.y * -7.0, p.y + tangent.x * -7.0, 13.0)
    for s in turrets:
        p, tangent = wall_frame(points, lengths, s)
        walk = walk_at(s)
        matrix = frame_matrix(p, tangent, walk - fort.WALK)
        low, high, _ = footprint_ground(scene, matrix, -3.0, 3.0, -4.8, 1.0)
        builder.merge(fort.turret(depth_below=max(walk - fort.WALK - low + 1.0, 2.0)), matrix)
        scene.features.setdefault("turrets", []).append((p, tangent, walk - fort.WALK, s))
    scene.unique("walls", builder)
    scene.features["wall_lengths"] = lengths
    scene.features["s_mc37"] = s_mc37
    scene.features["s_north"] = s_north
    return {"wall_length": round(float(lengths[-1]), 1), "milecastles": len(milecastles), "turrets": len(turrets)}


def fort_open_ring(inset=0.0):
    ring = plan.fort_ring(inset)
    path = ring[7:] + ring[:7]
    return plan.resample_line(path, 3.0)


def build_fort(scene):
    f = plan.FORT
    hu, hv = f["half_u"], f["half_v"]
    points = fort_open_ring()
    lengths = arc_lengths(points)
    stations = wall_stations(scene, points, outward=-1.0)
    gate_points = {"sud": plan.fort_point(plan.STREET_U, -hv), "est": plan.fort_point(hu, 0.0),
                   "ouest": plan.fort_point(-hu, 0.0)}
    gate_s = {key: plan.nearest_station(points, p.x, p.y) for key, p in gate_points.items()}
    gaps = [(s - 7.0, s + 7.0) for s in gate_s.values()]
    builder = MeshBuilder()
    runs = split_runs(stations, lengths, gaps)
    for index, run in enumerate(runs):
        fort.wall_run(builder, run, outward=-1.0, cap_start=index > 0, cap_end=index < len(runs) - 1)
    for key, s in gate_s.items():
        p, tangent = wall_frame(points, lengths, s)
        z = scene.ground(p.x, p.y)
        builder.merge(fort.gate(depth_below=6.0), frame_matrix(p, tangent, z, outward=-1.0))
        scene.features[f"gate_{key}"] = (p, tangent, z)
    walk_of = lambda s: float(np.interp(s, lengths, [st[4] for st in stations]))
    towers = []
    for u in (-48.0, 62.0):
        towers.append(plan.fort_point(u, -hv))
    for v in (-27.0, 27.0):
        towers.append(plan.fort_point(hu, v))
        towers.append(plan.fort_point(-hu, v))
    for corner in plan.fort_ring()[3::7]:
        towers.append(Vector(corner))
    for p in towers:
        s = plan.nearest_station(points, p.x, p.y)
        q, tangent = wall_frame(points, lengths, s)
        walk = walk_of(s)
        builder.merge(fort.tower(walk=fort.WALK, depth_below=6.0), frame_matrix(q, tangent, walk - fort.WALK, -1.0))
    wall_points = scene.wall_points
    wall_lengths = scene.features["wall_lengths"]
    for u in (-48.0, 62.0):
        p = plan.fort_point(u, hv)
        s = plan.nearest_station(wall_points, p.x, p.y)
        q, tangent = wall_frame(wall_points, wall_lengths, s)
        walk = float(np.interp(s, wall_lengths, [st[4] for st in scene.wall_stations]))
        builder.merge(fort.tower(walk=fort.WALK, depth_below=6.0), frame_matrix(q, tangent, walk - fort.WALK))
    scene.unique("walls", builder)
    rampart = MeshBuilder()
    ring = plan.resample_line(plan.fort_ring() + [plan.fort_ring()[0]], 3.0)
    ring_lengths = arc_lengths(ring)
    ring_stations = wall_stations(scene, ring, outward=-1.0, closed=True)
    all_gates = dict(gate_points)
    all_gates["nord"] = plan.fort_point(plan.STREET_U, hv)
    ring_gaps = [(plan.nearest_station(ring, p.x, p.y) - 10.5, plan.nearest_station(ring, p.x, p.y) + 10.5)
                 for p in all_gates.values()]
    for run in split_runs(ring_stations, ring_lengths, ring_gaps):
        fort.rampart_run(rampart, run, outward=-1.0)
    scene.unique("rampart", rampart)
    return {"fort_gates": len(gate_s) + 1, "towers": len(towers) + 2}


def fort_matrix(u, v, rotation=0.0, z=0.0):
    p = plan.fort_point(u, v)
    return Matrix.Translation((p.x, p.y, z)) @ Matrix.Rotation(plan.FORT["angle"] + rotation, 4, "Z")


def bounds(builder):
    xs = [p[0] for p in builder.positions]
    ys = [p[1] for p in builder.positions]
    return min(xs), max(xs), min(ys), max(ys)


def seat(scene, builder, u, v, rotation=0.0):
    matrix = fort_matrix(u, v, rotation)
    x0, x1, y0, y1 = bounds(builder)
    low, high, mean = footprint_ground(scene, matrix, x0 + 0.5, x1 - 0.5, y0 + 0.5, y1 - 0.5)
    floor = min(high + 0.08, low + 2.2)
    return fort_matrix(u, v, rotation, floor), floor


def build_interior(scene):
    f = plan.FORT
    placed = {}
    for key, u, v, rotation in (("principia", -1.0, 0.0, 0.0),):
        builder = fort.principia()
        matrix, floor = seat(scene, builder, u, v, rotation)
        scene.unique("fort_buildings", builder, matrix)
        scene.features["principia"] = (plan.fort_point(u, v), floor)
    for v in (20.0, 31.0):
        builder = fort.granary()
        matrix, floor = seat(scene, builder, -13.0, v)
        scene.unique("fort_buildings", builder, matrix)
    scene.features["granaries"] = plan.fort_point(0.0, 25.0)
    builder = fort.courtyard_building(36.0, 24.0, 16.0, 10.0, 4.6, fort.TILE, door_side=1)
    matrix, floor = seat(scene, builder, -2.0, -28.0)
    scene.unique("fort_buildings", builder, matrix)
    scene.features["praetorium"] = (plan.fort_point(-2.0, -28.0), floor)
    builder = fort.courtyard_building(18.0, 26.0, 8.0, 14.0, 4.0, fort.SLAB, door_side=1)
    matrix, floor = seat(scene, builder, -33.0, 0.0)
    scene.unique("fort_buildings", builder, matrix)
    builder = fort.latrine()
    matrix, floor = seat(scene, builder, 73.0, -39.0)
    scene.unique("fort_buildings", builder, matrix)
    barracks = {"barrack_long": [], "barrack_short": [], "barrack_west": []}
    templates = {"barrack_long": lambda: fort.barrack(51.0, seed=1), "barrack_short": lambda: fort.barrack(37.0, seed=2),
                 "barrack_west": lambda: fort.barrack(35.0, seed=3)}
    sizes = {key: bounds(build()) for key, build in templates.items()}
    rows = [(27.0, 9.0, 0.0, "barrack_long"), (27.0, 21.5, 0.0, "barrack_long"), (27.0, 34.0, 0.0, "barrack_long"),
            (78.0, -9.0, math.pi, "barrack_long"), (78.0, -21.5, math.pi, "barrack_long"),
            (64.0, -34.0, math.pi, "barrack_short"),
            (-73.0, 4.0, math.pi / 2, "barrack_west"), (-54.0, 4.0, math.pi / 2, "barrack_west"),
            (-73.0, -4.0, -math.pi / 2, "barrack_west"), (-54.0, -4.0, -math.pi / 2, "barrack_west")]
    hearths = []
    for u, v, rotation, key in rows:
        matrix = fort_matrix(u, v, rotation)
        x0, x1, y0, y1 = sizes[key]
        low, high, mean = footprint_ground(scene, matrix, x0 + 0.5, x1 - 0.5, y0 + 0.5, y1 - 0.5)
        floor = min(high + 0.08, low + 2.2)
        matrix = fort_matrix(u, v, rotation, floor)
        barracks[key].append(matrix)
        hearths.append(matrix @ Vector((x1 - 6.5, -0.5, 6.4)))
        hearths.append(matrix @ Vector((x1 * 0.35, 0.0, 5.2)))
    for key, matrices in barracks.items():
        scene.instances("fort_buildings", key, templates[key], matrices)
    rng = random.Random(5)
    scene.smokes.extend(rng.sample(hearths, 7))
    praetorium, floor = scene.features["praetorium"]
    scene.smokes.append(Vector((praetorium.x, praetorium.y, floor + 7.0)))
    return {"barracks": sum(len(v) for v in barracks.values())}


def build_outside(scene, crossing):
    rng = random.Random(9)
    camp = []
    tents = []
    for k in range(6):
        x = 70.0 + (k % 3) * 9.0 + rng.uniform(-1.0, 1.0)
        y = -68.0 - (k // 3) * 8.0 + rng.uniform(-1.0, 1.0)
        z = scene.ground(x, y)
        tents.append(Matrix.Translation((x, y, z - 0.05)) @ Matrix.Rotation(plan.FORT["angle"] + rng.uniform(-0.1, 0.1),
                                                                             4, "Z"))
        scene.claim(x, y, 3.0)
    scene.instances("camp", "tent", fort.tent, tents)
    scene.features["camp"] = Vector((80.0, -74.0))
    stacks = []
    for x, y in ((100.0, -58.0), (104.0, -63.0), (-180.0, -40.0), (-176.0, -45.0), (-300.0, -66.0),
                 (55.0, -84.0)):
        z = scene.ground(x, y)
        stacks.append(Matrix.Translation((x, y, z - 0.05)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z"))
        scene.claim(x, y, 2.0)
    scene.instances("camp", "stone_stack", fort.stone_stack, stacks)
    peat = []
    for x, y in ((118.0, -86.0), (123.0, -84.0), (-120.0, -60.0)):
        z = scene.ground(x, y)
        peat.append(Matrix.Translation((x, y, z - 0.05)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z"))
        scene.claim(x, y, 2.0)
    scene.instances("camp", "peat_stack", fort.peat_stack, peat)
    scene.smokes.append(Vector((92.0, -80.0, scene.ground(92.0, -80.0) + 0.6)))
    return {"tents": len(tents), "stone_stacks": len(stacks), "peat_stacks": len(peat)}


def kd_of(points):
    tree = KDTree(len(points))
    for index, (x, y) in enumerate(points):
        tree.insert((x, y, 0.0), index)
    tree.balance()
    return tree


def build_props(scene, eyes):
    rng = random.Random(77)
    wall_tree = kd_of(scene.wall_points)
    vallum_tree = kd_of(plan.resample_line(plan.VALLUM_SMOOTH, 3.0))
    track_tree = kd_of([p for points in scene.track_lines for p in plan.resample_line(points, 2.0)])
    terrain = scene.terrain
    placed = {key: [] for key in hlife.PROPS}
    for k in range(26000):
        if sum(len(v) for v in placed.values()) > 9000:
            break
        near_eye = eyes[rng.randrange(len(eyes))]
        if rng.random() < 0.7:
            reach = 140.0 * math.sqrt(rng.random()) + 4.0
            angle = rng.uniform(0, math.tau)
            x = near_eye.x + reach * math.cos(angle)
            y = near_eye.y + reach * math.sin(angle)
        else:
            x = rng.uniform(-1100.0, 800.0)
            y = rng.uniform(-550.0, 430.0)
        u, v = plan.fort_local(x, y)
        if abs(u) < plan.FORT["half_u"] + 18.0 and abs(v) < plan.FORT["half_v"] + 18.0:
            continue
        if vallum_tree.find((x, y, 0.0))[2] < 25.0 or wall_tree.find((x, y, 0.0))[2] < 6.0:
            continue
        if track_tree.find((x, y, 0.0))[2] < 4.0 or not scene.free(x, y, 1.0):
            continue
        h = float(terrain.height(x, y))
        if any(h < lake["level"] + 0.3 and lake["box"][0] < x < lake["box"][2] and lake["box"][1] < y < lake["box"][3]
               for lake in terrain.lakes.values()):
            continue
        gx = (terrain.height(x + 2.0, y) - terrain.height(x - 2.0, y)) / 4.0
        gy = (terrain.height(x, y + 2.0) - terrain.height(x, y - 2.0)) / 4.0
        slope = math.hypot(gx, gy)
        relief = h - float(np.mean(terrain.height(np.array([x + 15, x - 15, x, x]), np.array([y, y, y + 15, y - 15]))))
        heath = float(smoothstep((world_noise(x, y, 260.0, 3, 4) - 0.5) / 0.14)) + float(smoothstep((slope - 0.18) / 0.15))
        if slope > 0.55:
            key = rng.choice(["boulder", "boulder_b"])
        elif slope > 0.3 and rng.random() < 0.5:
            key = rng.choice(["boulder", "boulder_b", "heather", "heather_b"])
        elif rng.random() < 0.006 and relief < 0.0:
            key = "rowan"
        elif rng.random() < min(heath, 1.0) * 0.8:
            key = rng.choice(["heather", "heather_b"])
        else:
            key = rng.choice(["tussock", "tussock_b"])
        z = scene.ground(x, y) - (0.25 if key.startswith("boulder") else 0.05)
        scale = rng.uniform(0.7, 1.4) if not key.startswith("boulder") else rng.uniform(0.5, 2.2)
        placed[key].append(Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, "Z")
                           @ Matrix.Scale(scale, 4))
    for key, matrices in placed.items():
        scene.instances("props", key, hlife.PROPS[key], matrices, cast_shadow=key in ("rowan", "boulder", "boulder_b"))
    return {key: len(v) for key, v in placed.items()}


def build_surface(scene):
    objects = []
    for name in WALKABLE:
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in root.children_recursive:
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
        ceiling = top(point) if top else scene.top(point.x, point.y)
        z = scene.surface.height(point.x, point.y, ceiling, scene.ground(point.x, point.y))
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        previous = refined[-1]
        middle = (previous + following) / 2
        ceiling = top(middle) if top else scene.top(middle.x, middle.y)
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


def build_routes(scene, track_paths):
    counts = {}
    centre = plan.fort_point(plan.STREET_U, 0.0)
    hv = plan.FORT["half_v"]
    south = [tuple(centre), tuple(plan.fort_point(plan.STREET_U, -hv + 4.0))] + track_paths["sud"][:12]
    counts["porte_sud"] = add_route(scene, "porte_sud", south)
    east = [tuple(centre)] + track_paths["est"]
    counts["via_praetoria"] = add_route(scene, "via_praetoria", east)
    north = [tuple(plan.fort_point(plan.STREET_U, -20.0)), tuple(plan.fort_point(plan.STREET_U, hv - 4.0))]
    north += track_paths["nord"][:9]
    counts["porte_nord"] = add_route(scene, "porte_nord", north)
    counts["chemin_ouest"] = add_route(scene, "chemin_ouest", track_paths["ouest"])
    lengths = scene.features["wall_lengths"]
    s0 = scene.features["s_mc37"] + 12.0
    s1 = plan.nearest_station(scene.wall_points, *plan.fort_point(-plan.FORT["half_u"] + 9.0, plan.FORT["half_v"])) - 14.0
    walk = []
    for s in np.arange(s0, s1, 3.0):
        p, tangent = wall_frame(scene.wall_points, lengths, s)
        left = Vector((-tangent.y, tangent.x))
        q = p - left * 0.32
        walk.append((q.x, q.y))
    counts["chemin_de_ronde"] = add_route(scene, "chemin_de_ronde", walk, lambda p: 900.0)
    return counts


def clear_of_routes(scene, x, y, radius):
    point = Vector((x, y))
    return all((point - sample).length > radius for sample in scene.route_samples[::2])


def populate(scene, eyes):
    rng = random.Random(131)
    placed = {}

    def settle(x, y, spread):
        best = None
        for attempt in range(10):
            px = x + (rng.uniform(-3.0, 3.0) if attempt else 0.0)
            py = y + (rng.uniform(-3.0, 3.0) if attempt else 0.0)
            samples = [scene.surface.height(px + dx, py + dy, scene.top(px, py), scene.ground(px + dx, py + dy))
                       for dx, dy in ((0, 0), (spread, 0), (-spread, 0), (0, spread), (0, -spread))]
            spread_z = max(samples) - min(samples)
            if best is None or spread_z < best[0]:
                best = (spread_z, px, py, sorted(samples)[2])
            if spread_z < 0.1:
                break
        return best[1], best[2], best[3] - 0.03

    def put(key, x, y, heading, radius=0.8, z=None, check=True):
        if z is None:
            x, y, height = settle(x, y, max(radius, 0.6))
        else:
            height = z
        if check and not clear_of_routes(scene, x, y, radius):
            return False
        if check and min((Vector((x, y)) - eye).length for eye in eyes) < 5.0:
            return False
        placed.setdefault(key, []).append(Matrix.Translation((x, y, height)) @ Matrix.Rotation(heading, 4, "Z"))
        return True

    a = plan.FORT["angle"]
    lengths = scene.features["wall_lengths"]
    s_mc = scene.features["s_mc37"]
    for k, s in enumerate((s_mc - 160.0, s_mc + 60.0, s_mc + 172.0, s_mc + 200.0, s_mc + 330.0, s_mc - 420.0, s_mc + 560.0,
                           s_mc + 900.0, s_mc + 1200.0)):
        p, tangent = wall_frame(scene.wall_points, lengths, s)
        left = Vector((-tangent.y, tangent.x))
        q = p - left * 0.1
        z = scene.surface.height(q.x, q.y, 900.0, 0.0)
        heading = math.atan2(-left.x, left.y)
        put(["sentry", "sentry_b", "sentry_c"][k % 3], q.x, q.y, heading + rng.uniform(-0.4, 0.4), z=z, check=False)
    for key, value in scene.features.items():
        if key.startswith("gate_") or key == "north_gate":
            p, tangent, z = value
            out = Vector((-tangent.y, tangent.x)) * (1.0 if key == "north_gate" else -1.0)
            q = p - out * 6.0 + tangent * 6.5
            put("guards", q.x, q.y, math.atan2(-out.x, out.y), 1.4, check=False)
    p, tangent, z = scene.features["north_gate"]
    out = Vector((-tangent.y, tangent.x))
    for k, key in enumerate(("sentry_b", "centurion", "sentry", "sentry_c")):
        q = p + out * (9.0 + 3.2 * k) + tangent * (1.2 if k % 2 else -1.2)
        put(key, q.x, q.y, math.atan2(-out.x, out.y) + rng.uniform(-0.2, 0.2), check=False)
    centre = plan.fort_point(plan.STREET_U, 0.0)
    for key, du, dv, heading in (("centurion", -4.0, 6.0, 0.6), ("soldier_talk", -5.5, 7.5, -2.2),
                                  ("soldier_rest", -3.0, 8.4, 2.9), ("soldier_rest", 8.0, -14.0, 1.0),
                                  ("soldier_talk", 9.0, -12.5, -2.0), ("worker_stone", 6.0, 30.0, 0.0),
                                  ("soldier_rest", 30.0, 15.0, 1.6), ("soldier_talk", 31.5, 16.0, -1.6),
                                  ("soldier_rest", 40.0, -15.5, 0.0), ("worker_pick", -60.0, 44.0, 2.0),
                                  ("soldier_talk", -48.0, -18.0, 0.4), ("soldier_rest", 55.0, 28.0, 0.0)):
        p = plan.fort_point(plan.STREET_U + du, dv)
        put(key, p.x, p.y, a + heading, check=False)
    hu, hv = plan.FORT["half_u"], plan.FORT["half_v"]
    for k, (u, v, inward) in enumerate(((-68.0, -hv, (0.0, 1.0)), (-25.0, -hv, (0.0, 1.0)), (42.0, -hv, (0.0, 1.0)),
                                        (hu, -15.0, (-1.0, 0.0)), (hu, 15.0, (-1.0, 0.0)), (-hu, 15.0, (1.0, 0.0)))):
        q = plan.fort_point(u + inward[0] * 0.35, v + inward[1] * 0.35)
        z = scene.surface.height(q.x, q.y, 900.0, 0.0)
        out = plan.fort_point(u - inward[0], v - inward[1]) - plan.fort_point(u, v)
        put(["sentry", "sentry_b", "sentry_c"][k % 3], q.x, q.y, math.atan2(-out.x, out.y) + rng.uniform(-0.3, 0.3),
            z=z, check=False)
    for k in range(14):
        if k % 2:
            u, v = plan.STREET_U + rng.choice((-2.5, 2.5)), rng.uniform(-36.0, 36.0)
        else:
            u, v = rng.uniform(26.0, 80.0), rng.choice((-2.5, 2.5))
        p = plan.fort_point(u, v)
        put(rng.choice(["soldier_rest", "soldier_talk", "worker_stone", "sentry", "worker_pick"]), p.x, p.y,
            rng.uniform(0, math.tau), check=False)
    camp = scene.features["camp"]
    put("builders", camp.x + 14.0, camp.y + 8.0, 0.5, 2.5, check=False)
    put("builders", -178.0, -52.0, 1.2, 2.5, check=False)
    put("worker_stone", -296.0, -72.0, 2.0, check=False)
    put("worker_pick", -304.0, -60.0, 0.4, check=False)
    put("centurion", -186.0, -48.0, 2.6, check=False)
    put("supply_cart", *(Vector(scene.track_lines[0][14][:2]) + Vector((4.0, 0.0))), 0.4 + math.pi, 3.0, check=False)
    put("horse", camp.x - 12.0, camp.y - 2.0, 1.0, 1.4, check=False)
    put("soldier_rest", camp.x - 13.2, camp.y - 1.2, 2.4, check=False)
    put("sheep", -220.0, 260.0, 0.3, 6.0, check=False)
    put("briton", -210.0, 252.0, 1.2, check=False)
    put("sheep", 260.0, -320.0, 1.0, 6.0, check=False)
    put("cattle", -500.0, -420.0, 2.0, 7.0, check=False)
    put("cattle", 420.0, 250.0, 0.5, 7.0, check=False)
    put("briton", 405.0, 240.0, 2.0, check=False)
    for k in range(10):
        x = rng.uniform(-900.0, 700.0)
        y = rng.uniform(-500.0, -200.0)
        put(rng.choice(["sheep", "cattle"]), x, y, rng.uniform(0, math.tau), 7.0)
    for p, tangent, z0, s in scene.features.get("milecastles", []):
        left = Vector((-tangent.y, tangent.x))
        q = p - left * 7.0 + tangent * 4.0
        put("soldier_rest", q.x, q.y, math.atan2(-left.x, left.y), check=False)
    counts = {}
    for key, matrices in placed.items():
        scene.instances("life", key, hlife.LIFE[key], matrices, cast_shadow=True)
        counts[key] = len(matrices)
    return counts


def place_effects(scene):
    root = scene.root("life")
    for index, point in enumerate(scene.smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(Vector((-2250.0, -780.0)), 40.0), (Vector((120.0, 960.0)), 35.0), (Vector((-600.0, -60.0)), 70.0),
              (Vector((150.0, 150.0)), 90.0), (Vector((-1800.0, 900.0)), 50.0), (Vector((400.0, -400.0)), 60.0)]
    for index, (point, height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root,
                  Matrix.Translation((point.x, point.y, float(scene.terrain.height(point.x, point.y)) + height)))
    for index, (key, build) in enumerate(hlife.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke": len(scene.smokes), "birds": len(flocks), "walkers": len(hlife.WALKERS)}


def viewpoints(scene):
    points = {}
    t = scene.terrain
    fort_z = scene.features["principia"][1]
    points["vue-d-ensemble"] = (Vector((-2620.0, -1180.0, float(t.height(-2620.0, -1180.0)) + 190.0)),
                                Vector((-200.0, 10.0, fort_z - 30.0)))
    lengths = scene.features["wall_lengths"]
    s_mc = scene.features["s_mc37"]
    walks = [st[4] for st in scene.wall_stations]
    p, tangent = wall_frame(scene.wall_points, lengths, s_mc + 150.0)
    left = Vector((-tangent.y, tangent.x))
    eye = p - left * 0.5
    walk = float(np.interp(s_mc + 150.0, lengths, walks))
    q, tangent_q = wall_frame(scene.wall_points, lengths, s_mc + 380.0)
    q = q + Vector((-tangent_q.y, tangent_q.x)) * 14.0
    points["le-mur"] = (Vector((eye.x, eye.y, walk + 1.75)),
                        Vector((q.x, q.y, float(np.interp(s_mc + 380.0, lengths, walks)) - 5.0)))
    c = plan.fort_point(0.0, 0.0)
    points["le-fort"] = (Vector((c.x + 150.0, c.y - 210.0, fort_z + 120.0)), Vector((c.x - 5.0, c.y + 5.0, fort_z)))
    p, tangent, z = scene.features["north_gate"]
    out = Vector((-tangent.y, tangent.x))
    eye = p + out * 30.0 + tangent * 9.0
    points["la-porte-nord"] = (Vector((eye.x, eye.y, scene.ground(eye.x, eye.y) + 1.7)), Vector((p.x, p.y, z + 4.5)))
    crossing, direction = plan.along(plan.VALLUM_SMOOTH, scene.crossing)
    normal = Vector((direction.y, -direction.x))
    eye = crossing - direction * 50.0 + normal * 58.0
    target = crossing + direction * 8.0 - normal * 28.0
    points["le-vallum"] = (Vector((eye.x, eye.y, scene.ground(eye.x, eye.y) + 15.0)),
                           Vector((target.x, target.y, scene.ground(target.x, target.y) + 1.0)))
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
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.24, aerosol=0.8)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 4.2, (1.0, 0.80, 0.58), 0.8)
    bounce = sun_lamp(stage, 40.0, 30.0, 0.5, (0.70, 0.80, 1.0), 25.0)
    bounce.data.use_shadow = False
    for material in bpy.data.materials:
        if material.name.startswith(("terrain", "ground")) and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    node.inputs["Specular IOR Level"].default_value = 0.15
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
        rig = camera(stage, f"cam_{name}", eye, target, lens=LENS, clip_end=120000.0)
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
    terrain = hterrain.Terrain(CACHE)
    print("TERRAIN_FIT", round(terrain.fit_score, 2), terrain.cop_shift, round(time.perf_counter() - started, 1),
          flush=True)
    wall = hterrain.wall_line(terrain)
    crossing = crossing_station()
    terrain.edit(wall, crossing)
    scene = Scene(tiles, terrain)
    scene.crossing = crossing
    scene.wall_points = wall
    track_paths = tracks(crossing)
    hterrain.TRACKS[:] = [(points, 2.6) for points in track_paths.values()]
    scene.track_lines = list(track_paths.values())
    print("EDITED", {k: round(v["level"], 2) for k, v in terrain.lakes.items()}, round(time.perf_counter() - started, 1),
          flush=True)
    build_terrain(scene)
    build_water(scene)
    build_vallum(scene, crossing)
    print("TERRAIN", round(time.perf_counter() - started, 1), flush=True)
    ground_surface(scene)
    wall_counts = build_walls(scene)
    fort_counts = build_fort(scene)
    interior = build_interior(scene)
    outside = build_outside(scene, crossing)
    scene.flush({"rampart": False})
    print("MONUMENTS", round(time.perf_counter() - started, 1), flush=True)
    build_surface(scene)
    points = viewpoints(scene)
    place_markers(scene, points)
    eyes = [eye.to_2d() for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    prop_counts = build_props(scene, eyes + [Vector((0.0, 0.0))])
    route_counts = build_routes(scene, track_paths)
    life_counts = populate(scene, eyes)
    effects = place_effects(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "mur-d-hadrien.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION], "lakes": terrain.lakes, "copernicus_fit": [terrain.fit_score,
                                                                                         list(terrain.cop_shift)],
        "counts": {"walls": wall_counts, "fort": fort_counts, "interior": interior, "outside": outside,
                   "props": prop_counts, "routes": route_counts, "life": life_counts, "effects": effects},
        "route_checks": route_report(scene),
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "build_seconds": round(time.perf_counter() - started, 1), "terrain_source": hterrain.SOURCE,
        "texture_credits": credits,
        "structures": {kind: [[round(p.x, 1), round(p.y, 1), round(z, 1)] for p, _, z, _ in scene.features.get(kind, [])]
                       for kind in ("milecastles", "turrets")},
        "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                    for key, (eye, target) in points.items()},
    }
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1, default=float)
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in points.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("BUILD", round(time.perf_counter() - started, 1), flush=True)
    print("PREVIEWS", json.dumps(render_previews(options, points)), flush=True)


main()

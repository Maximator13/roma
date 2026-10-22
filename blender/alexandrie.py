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

from kit import alexandrie_city as city
from kit import alexandrie_life as alife
from kit import alexandrie_monuments as mon
from kit import alexandrie_pharos as pharos
from kit import alexandrie_plan as plan
from kit import alexandrie_ships as ships
from kit import alexandrie_terrain as aterrain
from kit import alexandrie_weather as aweather
from kit import colisee_monuments as cmon
from kit import nimes_detail, nimes_figures
from kit.alexandrie_materials import build_library, remap
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, save_pixels
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, render_still, sun_lamp
from kit.terrain import point_in_polygon

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "alexandrie")
BLEND = os.path.join(CACHE, "work", "alexandrie.blend")
SUN_AZIMUTH = 291.0
SUN_ELEVATION = 12.0
NEAR_TILES = (-3500.0, -1900.0, 2300.0, 2)
MID_TILE = (-8000.0, -7000.0, 13800.0, 60.0)
FAR_TILE = (-60000.0, -60000.0, 120000.0, 750.0)
LENS = 27.8
GRID_ANGLE = math.atan2(plan.D.y, plan.D.x)
HEPTA_BRIDGES = plan.HEPTASTADION_BRIDGES
NEAR_DETAIL = (-1400.0, 600.0, 40.0)
WALKABLE = ("terrain", "quays", "heptastadion", "caesareum", "streets", "pharos_court", "pharos", "emporion")
COLUMN_KEYS = {"simple": lambda: mon.simple_column()(), "ionic": lambda: mon.unit_column("ionic")(),
               "corinthian": lambda: mon.unit_column("corinthian")()}


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

    def height(self, x, y, hint, reach=3.0):
        hit = self.tree.ray_cast(Vector((x, y, hint + reach)), Vector((0.0, 0.0, -1.0)), reach + 8.0)
        return hint if hit[0] is None else hit[0].z


class Scene:
    def __init__(self, tiles, terrain):
        self.tiles = tiles
        self.terrain = terrain
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Alexandrie")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.surface = None
        self.routes = {}
        self.route_samples = []
        self.footprints = []
        self.columns = {}
        self.chunks = []
        self.market = []
        self.palms = {True: [], False: []}
        self.coast = None
        self.hepta_frame = None
        self.hepta_length = 0.0
        self.caesareum_frame = None
        self.island_rocks = []

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.terrain.height(x, y))

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

    def add_palms(self, matrices, detail):
        self.palms[detail].extend(matrices)

    def place_palms(self):
        rng = random.Random(3)
        for detail, matrices in self.palms.items():
            buckets = {k: [] for k in range(3)}
            for matrix in matrices:
                scale = rng.uniform(0.8, 1.2)
                buckets[rng.randrange(3)].append(matrix @ Matrix.Scale(scale, 4))
            for k, items in buckets.items():
                label = "palm" if detail else "palm_far"
                self.instances("palms", f"{label}_{k}", lambda k=k, detail=detail: city.date_palm(11.0 + 2.5 * k,
                                                                                                    20 + k, detail),
                               items)

    def instances(self, group, key, build, matrices, cast_shadow=True):
        if not matrices:
            return None
        return self.library.place(key, lambda: remap(build()), self.collection, self.root(group), matrices,
                                  cast_shadow, False)


def near_tiles():
    x0, y0, size, count = NEAR_TILES
    for i in range(count):
        for j in range(count):
            yield f"{i}{j}", x0 + i * size, y0 + j * size, size


def build_terrain(scene):
    terrain = scene.terrain
    root = scene.root("terrain")
    textures = os.path.join(CACHE, "textures")
    footprints = footprint_mask(scene)
    for key, x0, y0, size in near_tiles():
        colour = aterrain.bake_tile(terrain, x0, y0, size, 1024, footprints)
        image = save_pixels(f"terrain_{key}", colour, os.path.join(textures, f"terrain_{key}.jpg"), quality=90)
        material = baked_material(f"terrain_{key}", image)
        mesh = aterrain.grid_tile(f"terrain_{key}", terrain, x0, y0, size, 20.0)
        mesh.materials.append(material)
        created = new_object(f"terrain_{key}", mesh, scene.collection, root)
        created["cast_shadow"] = False
    x0, y0, size, count = NEAR_TILES
    near_hole = (x0, y0, x0 + size * count, y0 + size * count)
    mx, my, msize, mspacing = MID_TILE
    colour = aterrain.bake_tile(terrain, mx, my, msize, 1024, footprints)
    image = save_pixels("terrain_mid", colour, os.path.join(textures, "terrain_mid.jpg"), quality=88)
    material = baked_material("terrain_mid", image)
    mesh = aterrain.grid_tile("terrain_mid", terrain, mx, my, msize, mspacing, near_hole)
    mesh.materials.append(material)
    created = new_object("terrain_mid", mesh, scene.collection, root)
    created["cast_shadow"] = False
    fx, fy, fsize, fspacing = FAR_TILE
    colour = aterrain.bake_tile(terrain, fx, fy, fsize, 1024)
    image = save_pixels("terrain_far", colour, os.path.join(textures, "terrain_far.jpg"), quality=86)
    material = baked_material("terrain_far", image)
    mesh = aterrain.grid_tile("terrain_far", terrain, fx, fy, fsize, fspacing, (mx, my, mx + msize, my + msize))
    mesh.materials.append(material)
    created = new_object("terrain_far", mesh, scene.collection, root)
    created["cast_shadow"] = False


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
            value = strength * np.clip(1.0 - outside / 6.0, 0.0, 1.0)
            block = result[np.ix_(rows, columns)]
            result[np.ix_(rows, columns)] = np.maximum(block, value)
        return result
    return mask


def build_water(scene):
    terrain = scene.terrain
    root = scene.root("water")
    spec = aterrain.NEAR_FIELD
    near = (spec["x0"], spec["y0"], spec["x0"] + spec["width"], spec["y0"] + spec["height"])
    pieces = [aterrain.water_mesh("water_near", terrain, near, 100.0, 25.0),
              aterrain.water_mesh("water_far", terrain, (-60000.0, -60000.0, 60000.0, 60000.0), 2000.0, 2000.0,
                                  hole=near, refine=False)]
    for mesh in pieces:
        mesh.materials.append(bpy.data.materials["water"])
        created = new_object(mesh.name, mesh, scene.collection, root)
        created["cast_shadow"] = False
    ring = MeshBuilder()
    reach = 60000.0
    outer = 200000.0
    for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        ring.polygon([(ax * reach, ay * reach, 0.0), (bx * reach, by * reach, 0.0), (bx * outer, by * outer, 0.0),
                      (ax * outer, ay * outer, 0.0)], "water", color=(0.05, 0.27, 0.48))
    created = unique_object("water_horizon", ring, scene.collection, root, scene.tiles, cast_shadow=False,
                            ground_occlusion=False)
    return created


def pharos_frame(scene):
    return Matrix.Translation((plan.PHAROS.x, plan.PHAROS.y, pharos.GROUND))


def build_pharos(scene):
    frame = pharos_frame(scene)
    scene.unique("pharos", pharos.tower(), frame)
    scene.unique("pharos", pharos.ramp(), frame)
    scene.unique("pharos_gilt", pharos.tritons_and_statue(), frame)
    scene.unique("pharos_court", pharos.enclosure(), frame)
    scene.unique("pharos_court", pharos.platform(), frame)
    beacon = frame @ pharos.beacon_position()
    new_empty("beacon", scene.collection, scene.root("life"), Matrix.Translation(beacon))
    scene.footprints.append((plan.PHAROS.x, plan.PHAROS.y, 64.0, 64.0, 0.0, 0.25))
    return beacon


def grid_frame(scene, t, n, z=None, turn=0.0, lift=0.0):
    p = plan.grid_point(t, n)
    height = scene.ground(p.x, p.y) if z is None else z
    return Matrix.Translation((p.x, p.y, height + lift)) @ Matrix.Rotation(GRID_ANGLE + turn, 4, "Z")


class Coast:
    def __init__(self):
        self.polygon = plan.mainland()
        self.ts = np.arange(-4600.0, 3600.0, 20.0)
        values = []
        for t in self.ts:
            n = 0.0
            while n < 1600.0 and point_in_polygon(*plan.grid_point(t, n), self.polygon):
                n += 20.0
            low = n - 20.0
            for _ in range(5):
                middle = (low + n) / 2
                if point_in_polygon(*plan.grid_point(t, middle), self.polygon):
                    low = middle
                else:
                    n = middle
            values.append(low)
        self.ns = np.array(values)

    def n(self, t):
        return float(np.interp(t, self.ts, self.ns))


def is_water(scene, x, y, margin=12.0):
    return float(scene.terrain.sample("shore", x, y)) < -margin


def add_columns(scene, group, frames_by_order):
    for order, frames in frames_by_order.items():
        if frames:
            scene.columns.setdefault((group, order), []).extend(frames)


def place_columns(scene):
    merged = {}
    for (group, order), frames in scene.columns.items():
        merged.setdefault(order, []).extend(frames)
    for order, frames in merged.items():
        scene.instances("columns", f"column_{order}", COLUMN_KEYS[order], frames)


def build_heptastadion(scene):
    start, end = plan.HEPTASTADION
    axis = (end - start)
    length = axis.length
    axis.normalize()
    frame = Matrix.Translation((start.x, start.y, 0.0)) @ Matrix.Rotation(math.atan2(axis.y, axis.x) - math.pi / 2,
                                                                         4, "Z")
    scene.unique("heptastadion", mon.heptastadion(length, plan.HEPTASTADION_WIDTH, HEPTA_BRIDGES), frame)
    flat = []
    bridge = []
    for y0, y1, top, kind in mon.aqueduct_runs(length, HEPTA_BRIDGES):
        span = y1 - y0
        count = max(int(round(span / 40.0)), 1)
        size = span / count
        for k in range(count):
            local = (Matrix.Translation((8.6, y0 + k * size, 0.0)) @ Matrix.Diagonal((1.0, size / 40.0, 1.0, 1.0)))
            (bridge if kind == "bridge" else flat).append(frame @ local)
    scene.instances("heptastadion", "aqueduct_flat", lambda: mon.aqueduct(40.0, 6.4, -0.5, 9), flat)
    scene.instances("heptastadion", "aqueduct_bridge", lambda: mon.aqueduct(40.0, 6.4, 5.4, 9), bridge)
    scene.hepta_frame = frame
    scene.hepta_length = length
    return frame, length


def path_offset(points, offset):
    result = []
    for index, point in enumerate(points):
        a = Vector(points[max(index - 1, 0)])
        b = Vector(points[min(index + 1, len(points) - 1)])
        direction = (b - a).normalized()
        right = Vector((direction.y, -direction.x))
        result.append(Vector(point[:2]) + right * offset)
    return result


def resample(points, spacing):
    out = [Vector(points[0])]
    for start, end in zip(points[:-1], points[1:]):
        a, b = Vector(start), Vector(end)
        count = max(int(math.ceil((b - a).length / spacing - 1e-6)), 1)
        for k in range(1, count + 1):
            out.append(a + (b - a) * (k / count))
    return out


def land_runs(ring):
    runs = []
    current = []
    for a, b in zip(ring[:-1], ring[1:]):
        a, b = Vector(a), Vector(b)
        middle = (a + b) / 2
        d = (b - a).normalized()
        probe = middle + Vector((d.y, -d.x)) * 4.0
        if plan.is_land(probe.x, probe.y):
            if not current:
                current = [tuple(a)]
            current.append(tuple(b))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return runs


def build_quays(scene):
    lines = [list(plan.MAINLAND_SEA[plan.QUAY_RANGE[0]:plan.QUAY_RANGE[1]]),
             mon.oriented_ring(list(plan.ANTIRHODOS), True), plan.lake_port_line()]
    for polygon in plan.water_cuts():
        lines.extend(land_runs(mon.oriented_ring(list(polygon), False)))
    bollards = []
    widths = [52.0, 14.0, 24.0] + [16.0] * (len(lines) - 3)
    for line, width in zip(lines, widths):
        scene.unique("quays", mon.quay(line))
        scene.unique("quays", mon.apron(line, width))
        dense = resample([Vector((p[0], p[1])) for p in line], 18.0)
        for point in path_offset([tuple(p) for p in dense], 1.3)[1:-1]:
            bollards.append(Matrix.Translation((point.x, point.y, plan.QUAY_TOP + 0.06)))
    scene.instances("quays", "bollard", mon.bollard, bollards, cast_shadow=False)
    scene.quay_lines = lines


def coast_frame(scene, t, inset, turn=math.pi):
    n = scene.coast.n(t) - inset
    return grid_frame(scene, t, n, turn=turn), n


def build_harbour(scene):
    shed = mon.ship_shed(8.2, 40.0, 7.0)
    for k in range(18):
        t = -1150.0 + k * 8.2
        n = scene.coast.n(t)
        p = plan.grid_point(t, n - 20.0)
        scene.unique("harbour", shed, Matrix.Translation((p.x, p.y, 0.0)) @ Matrix.Rotation(GRID_ANGLE, 4, "Z"))
        scene.footprints.append((p.x, p.y, 4.2, 22.0, GRID_ANGLE, 0.35))
    for k in range(8):
        t = -930.0 + k * 66.0
        frame, n = coast_frame(scene, t, 42.0)
        scene.unique("harbour", mon.warehouse(60.0, 16.0, 8.0 + k % 3, k), frame)
        p = frame.translation
        scene.footprints.append((p.x, p.y, 31.0, 9.0, GRID_ANGLE, 0.45))
    stoa_t = -225.0
    frame, n = coast_frame(scene, stoa_t, 50.0)
    builder, frames = mon.emporion_stoa(230.0, 14.0, 8.0)
    scene.unique("emporion", builder, frame)
    add_columns(scene, "emporion", {"simple": [frame @ f for f in frames]})
    p = frame.translation
    scene.footprints.append((p.x, p.y, 116.0, 8.0, GRID_ANGLE, 0.45))
    poseidion_t = -430.0
    n = scene.coast.n(poseidion_t) - 40.0
    frame = grid_frame(scene, poseidion_t, n)
    temple, frames = ccolumns_temple(12.0, 21.0, 2.4, 7.2, 0.75, 4, "ionic")
    scene.unique("harbour", temple, frame)
    add_columns(scene, "harbour", {"ionic": [frame @ f for f in frames]})
    timonium = Vector((-1300.0, 196.0))
    mole_start = Vector((-1240.0, 135.0))
    direction = (timonium - mole_start)
    length = direction.length
    direction.normalize()
    mole_frame = Matrix.Translation((mole_start.x, mole_start.y, 0.0)) @ Matrix.Rotation(
        math.atan2(direction.y, direction.x) - math.pi / 2, 4, "Z")
    scene.unique("quays", mon.mole(length + 10.0, 12.0), mole_frame)
    villa, frames = mon.villa(24.0, 15.0, 8.0, 5)
    villa_frame = Matrix.Translation((timonium.x, timonium.y, 1.9)) @ Matrix.Rotation(math.atan2(direction.y,
                                                                                                 direction.x), 4, "Z")
    scene.unique("harbour", villa, villa_frame)
    add_columns(scene, "harbour", {"simple": [villa_frame @ f for f in frames]})
    royal_moles = [((-190.0, 505.0), (-335.0, 525.0)), ((-335.0, 525.0), (-330.0, 690.0)),
                   ((-100.0, 790.0), (-250.0, 760.0))]
    for a, b in royal_moles:
        a, b = Vector(a), Vector(b)
        d = (b - a)
        frame = Matrix.Translation((a.x, a.y, 0.0)) @ Matrix.Rotation(math.atan2(d.y, d.x) - math.pi / 2, 4, "Z")
        scene.unique("quays", mon.mole(d.length, 9.0), frame)
    kib = plan.KIBOTOS
    for k, (dt, dn) in enumerate(((-150.0, -60.0), (150.0, -60.0), (-150.0, 30.0), (150.0, 30.0))):
        frame = grid_frame(scene, kib["t"] + dt, kib["n"] + dn, turn=math.pi / 2 if dt < 0 else -math.pi / 2)
        scene.unique("harbour", mon.warehouse(50.0, 15.0, 8.0, 20 + k), frame)
        p = frame.translation
        scene.footprints.append((p.x, p.y, 8.0, 25.0, GRID_ANGLE, 0.45))
    site = plan.SITES["lake_port"]
    for k in range(4):
        t = site["t"] - 180.0 + k * 120.0
        n = plan.lake_n(t) + 40.0
        frame = grid_frame(scene, t, n)
        scene.unique("harbour", mon.warehouse(56.0, 15.0, 7.5, 40 + k), frame)
        p = frame.translation
        scene.footprints.append((p.x, p.y, 28.0, 8.0, GRID_ANGLE, 0.45))


def ccolumns_temple(width, length, podium, height, diameter, front, order, peripteral=False):
    builder, frames = cmon.temple(width, length, podium, height, diameter, front, order, peripteral=peripteral)
    return builder, frames.get(order, [])


def build_caesareum(scene):
    site = plan.SITES["caesareum"]
    frame = grid_frame(scene, site["t"], site["n"])
    wall, frames = mon.temenos(150.0, 120.0, 8.0, 7.0, 4.0, gate=16.0, outer=(1.0, 0.92, 0.80))
    mon.painted(wall, (1.0, 0.96, 0.9), lambda: wall.box((-67.0, -52.0, -0.8), (67.0, 52.0, 0.36), "paving",
                                                         bottom=False))
    scene.unique("caesareum", wall, frame)
    engaged = [mon.column_frame(x, 60.05, -0.2, 0.7, 8.6) for x in np.arange(-73.0, 73.5, 4.0) if abs(x) > 10.5]
    add_columns(scene, "caesareum", {"simple": [frame @ f for f in frames + engaged]})
    temple, frames = ccolumns_temple(22.0, 38.0, 5.2, 12.5, 1.15, 6, "corinthian", peripteral=True)
    temple_frame = frame @ Matrix.Translation((0.0, -14.0, 0.0))
    scene.unique("caesareum", temple, temple_frame)
    add_columns(scene, "caesareum", {"corinthian": [temple_frame @ f for f in frames]})
    gate, frames = mon.propylon(17.0, 9.0, 9.5)
    gate_frame = frame @ Matrix.Translation((0.0, 60.0, 0.0))
    scene.unique("caesareum", gate, gate_frame)
    add_columns(scene, "caesareum", {"corinthian": [gate_frame @ f for f in frames]})
    coast = scene.coast.n(site["t"])
    plaza_depth = coast - site["n"] - 60.0 - 8.0 - 12.0
    plaza = MeshBuilder()
    mon.painted(plaza, (1.0, 0.97, 0.92), lambda: plaza.box((-75.0, 60.0, -3.0), (75.0, 60.0 + plaza_depth, 0.12),
                                                           "paving", bottom=False))
    drop = frame.translation.z + 0.12 - (plan.QUAY_TOP + 0.07)
    steps = max(int(drop / 0.28), 1)
    for k in range(steps):
        top = 0.12 - drop * (k + 1) / (steps + 1)
        y0 = 60.0 + plaza_depth + k * 12.0 / steps
        mon.painted(plaza, (1.0, 0.96, 0.9), lambda y0=y0, top=top: plaza.box((-30.0, y0, -3.0), (30.0, y0 + 12.0 / steps,
                                                                                            top), "limestone",
                                                                               bottom=False))
    scene.unique("caesareum", plaza, frame)
    obelisks = [frame @ Matrix.Translation((x, 86.0, 0.12)) @ Matrix.Rotation(0.0, 4, "Z") for x in (-14.0, 14.0)]
    statues = [frame @ placement(x, 66.5, 0.12, math.pi) for x in (-30.0, -20.0, 20.0, 30.0)]
    scene.instances("caesareum", "honorific", lambda: nimes_figures.honorific_statue(True), statues)
    for index, matrix in enumerate(obelisks):
        scene.unique("caesareum", mon.obelisk(21.0, seed=index), matrix)
    scene.caesareum_frame = frame
    p = frame.translation
    scene.footprints.append((p.x, p.y, 76.0, 61.0, GRID_ANGLE, 0.4))
    trees = []
    palms = []
    rng = random.Random(5)
    for k in range(26):
        x = rng.uniform(-62.0, 62.0)
        y = rng.uniform(-50.0, 48.0)
        if abs(x) < 16.0 and -36.0 < y < 12.0:
            continue
        if abs(x) < 10.0 and y > 30.0:
            continue
        (palms if rng.random() < 0.6 else trees).append(frame @ placement(x, y, 0.4, rng.uniform(0, 6.28)))
    scene.add_palms(palms, detail=True)
    scene.instances("caesareum", "grove_tree", lambda: city.broad_tree(9.0, 4, (0.26, 0.44, 0.16)), trees)


def build_theatre(scene):
    site = plan.SITES["theatre"]
    frame = grid_frame(scene, site["t"], site["n"] - 20.0)
    builder, frames = mon.theatre()
    scene.unique("monuments", builder, frame)
    add_columns(scene, "monuments", {"simple": [frame @ f for f in frames]})
    p = frame.translation
    scene.footprints.append((p.x, p.y, 48.0, 30.0, GRID_ANGLE, 0.35))


PALACES = [dict(width=72.0, depth=58.0, storeys=2, hall=False), dict(width=60.0, depth=50.0, storeys=1, hall=True),
           dict(width=54.0, depth=44.0, storeys=2, hall=False), dict(width=84.0, depth=64.0, storeys=1, hall=True)]


def build_palaces(scene):
    rng = random.Random(11)
    placements = {k: [] for k in range(len(PALACES))}
    gardens = []
    taken = []

    def free(t, n, radius):
        return all(math.hypot(t - a, n - b) > radius + r for a, b, r in taken)

    candidates = []
    for t in np.arange(240.0, 2120.0, 22.0):
        coast = scene.coast.n(t)
        for n in np.arange(270.0, coast - 50.0, 22.0):
            candidates.append((t + rng.uniform(-8, 8), n + rng.uniform(-8, 8)))
    rng.shuffle(candidates)
    for t, n in candidates:
        variant = rng.choice((0, 0, 1, 2, 2, 3))
        spec = PALACES[variant]
        radius = math.hypot(spec["width"], spec["depth"]) / 2 + 6.0
        if n + radius * 0.7 > scene.coast.n(t) - 45.0 or not free(t, n, radius + rng.uniform(0.0, 8.0)):
            continue
        p = plan.grid_point(t, n)
        if plan.in_site(p.x, p.y, pad=radius):
            continue
        taken.append((t, n, radius))
        if rng.random() < 0.08:
            gardens.append((t, n))
            continue
        turn = rng.choice((0.0, math.pi / 2, math.pi, -math.pi / 2))
        turn = 0.0 if turn in (0.0, math.pi) else turn
        frame = grid_frame(scene, t, n, turn=turn)
        placements[variant].append(frame)
        half = (spec["width"] / 2, spec["depth"] / 2) if turn in (0.0, math.pi) else (spec["depth"] / 2,
                                                                                      spec["width"] / 2)
        scene.footprints.append((p.x, p.y, half[0], half[1], GRID_ANGLE, 0.45))
        for k in range(3):
            angle = rng.uniform(0, 6.28)
            gardens.append((t + math.cos(angle) * radius, n + math.sin(angle) * radius))
    centre = (Vector(plan.ANTIRHODOS[0]) + Vector(plan.ANTIRHODOS[4])) / 2
    axis = (Vector(plan.ANTIRHODOS[4]) - Vector(plan.ANTIRHODOS[0])).normalized()
    antirhodos = Matrix.Translation((centre.x, centre.y, scene.ground(centre.x, centre.y))) @ Matrix.Rotation(
        math.atan2(axis.y, axis.x), 4, "Z") @ Matrix.Diagonal((0.95, 0.68, 1.0, 1.0))
    placements[1].append(antirhodos)
    island_palms = []
    for k in range(60):
        x = rng.uniform(-1170.0, -900.0)
        y = rng.uniform(210.0, 490.0)
        if not point_in_polygon(x, y, plan.ANTIRHODOS) or scene.terrain.sample("shore", x, y) < 16.0:
            continue
        if (Vector((x, y)) - centre).length < 34.0:
            continue
        island_palms.append(Matrix.Translation((x, y, scene.ground(x, y))) @ Matrix.Rotation(rng.uniform(0, 6.28), 4,
                                                                                             "Z"))
    scene.add_palms(island_palms[:14], detail=False)
    for variant, frames in placements.items():
        spec = PALACES[variant]
        builder, _, _ = mon.palace(spec["width"], spec["depth"], variant + 3, spec["storeys"], spec["hall"])
        scene.instances("palaces", f"palace_{variant}", lambda builder=builder: builder, frames)
    shrines = 0
    for t, n in list(gardens):
        if shrines >= 16 or rng.random() < 0.55:
            continue
        p = plan.grid_point(t, n)
        if plan.in_site(p.x, p.y, pad=30.0) or n > scene.coast.n(t) - 60.0 or not free(t, n, -14.0):
            continue
        kind = rng.choice(("temple", "tholos", "stoa"))
        frame = grid_frame(scene, t, n, turn=rng.choice((0.0, math.pi / 2, math.pi, -math.pi / 2)))
        if kind == "temple":
            builder, frames = cmon.temple(13.0, 22.0, 2.6, 8.0, 0.8, 4, "ionic")
            scene.unique("palaces", builder, frame)
            add_columns(scene, "palaces", {"ionic": [frame @ f for f in frames["ionic"]]})
        elif kind == "tholos":
            builder, frames = cmon.round_temple(6.5, 2.4, 14, 7.0, 0.55)
            scene.unique("palaces", builder, frame)
            add_columns(scene, "palaces", {"simple": [frame @ f for f in frames["corinthian"]]})
        else:
            builder, frames = mon.emporion_stoa(70.0, 10.0, 6.5, shrines)
            scene.unique("palaces", builder, frame)
            add_columns(scene, "palaces", {"simple": [frame @ f for f in frames]})
        scene.footprints.append((p.x, p.y, 16.0, 16.0, GRID_ANGLE, 0.35))
        shrines += 1
    palms = []
    trees = []
    shrubs = []
    for t, n in gardens:
        for k in range(rng.randrange(3, 8)):
            x = t + rng.uniform(-28.0, 28.0)
            y = n + rng.uniform(-24.0, 24.0)
            if not free(x, y, -2.0) and rng.random() < 0.9:
                continue
            p = plan.grid_point(x, y)
            if not plan.is_land(p.x, p.y) or scene.terrain.sample("shore", p.x, p.y) < 15.0:
                continue
            z = scene.ground(p.x, p.y)
            matrix = Matrix.Translation((p.x, p.y, z)) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z")
            roll = rng.random()
            if roll < 0.5:
                palms.append(matrix)
            elif roll < 0.82:
                trees.append(matrix)
            else:
                shrubs.append(matrix)
    scene.add_palms(palms, detail=False)
    scene.instances("palaces", "garden_tree", lambda: city.broad_tree(8.0, 7, (0.28, 0.46, 0.18)), trees)
    scene.instances("palaces", "garden_shrub", lambda: city.shrub(1.8, 3), shrubs, cast_shadow=False)


def build_gymnasium(scene):
    site = plan.SITES["gymnasium"]
    frame = grid_frame(scene, site["t"], site["n"])
    wall, frames = mon.temenos(site["width"] - 20.0, site["depth"] - 20.0, 7.0, 8.0, 4.4, gate=14.0,
                               outer=(1.0, 0.88, 0.72))
    scene.unique("monuments", wall, frame)
    add_columns(scene, "monuments", {"simple": [frame @ f for f in frames]})
    sand = MeshBuilder()
    mon.painted(sand, (0.95, 0.84, 0.62), lambda: sand.box((-100.0, -80.0, -0.5), (100.0, 80.0, 0.42), "matte",
                                                           bottom=False))
    scene.unique("monuments", sand, frame)
    p = frame.translation
    scene.footprints.append((p.x, p.y, site["width"] / 2 - 10.0, site["depth"] / 2 - 10.0, GRID_ANGLE, 0.35))


def build_paneion(scene):
    site = plan.SITES["paneion"]
    frame = grid_frame(scene, site["t"], site["n"])
    builder, frames = mon.paneion()
    scene.unique("monuments", builder, frame)
    add_columns(scene, "monuments", {"ionic": [frame @ f for f in frames]})


def build_serapeum(scene):
    site = plan.SITES["serapeum"]
    frame = grid_frame(scene, site["t"], site["n"], turn=math.pi)
    wall, frames = mon.temenos(site["width"], site["depth"], 8.0, 7.0, 4.4, gate=16.0, outer=(1.0, 0.94, 0.84))
    scene.unique("monuments", wall, frame)
    add_columns(scene, "monuments", {"simple": [frame @ f for f in frames]})
    temple, frames = ccolumns_temple(24.0, 42.0, 4.0, 12.0, 1.2, 6, "corinthian", peripteral=True)
    scene.unique("monuments", temple, frame @ Matrix.Translation((0.0, -10.0, 0.0)))
    add_columns(scene, "monuments", {"simple": [frame @ Matrix.Translation((0.0, -10.0, 0.0)) @ f
                                                for f in frames]})
    p = frame.translation
    scene.footprints.append((p.x, p.y, site["width"] / 2, site["depth"] / 2, GRID_ANGLE, 0.4))


def build_island(scene):
    a = Vector((-2700.0, 1010.0))
    z = scene.ground(a.x, a.y)
    frame = Matrix.Translation((a.x, a.y, z)) @ Matrix.Rotation(math.radians(36.0) + math.pi, 4, "Z")
    builder, frames = mon.isis_shrine()
    scene.unique("island", builder, frame)
    add_columns(scene, "island", {order: [frame @ f for f in values] for order, values in frames.items()})
    scene.footprints.append((a.x, a.y, 24.0, 22.0, math.radians(36.0), 0.4))
    hamlet = []
    rng = random.Random(23)
    for k in range(9):
        p = Vector((-2900.0 - k * 75.0 + rng.uniform(-15, 15), 880.0 - k * 55.0 + rng.uniform(-15, 15)))
        if scene.terrain.sample("shore", p.x, p.y) < 25.0:
            continue
        hamlet.append(Matrix.Translation((p.x, p.y, scene.ground(p.x, p.y))) @ Matrix.Rotation(
            math.radians(36.0) + rng.choice((0.0, math.pi)), 4, "Z"))
        scene.footprints.append((p.x, p.y, 12.0, 10.0, math.radians(36.0), 0.4))
    scene.instances("island", "hamlet", lambda: city.house_chunk(901, True, 26.0, 22.0, ()), hamlet)
    palms = []
    shrubs = []
    for k in range(70):
        p = Vector((rng.uniform(-4600.0, -2450.0), rng.uniform(-300.0, 1300.0)))
        shore = scene.terrain.sample("shore", p.x, p.y)
        if shore < 12.0 or not point_in_polygon(p.x, p.y, plan.PHAROS_ISLAND):
            continue
        matrix = Matrix.Translation((p.x, p.y, scene.ground(p.x, p.y))) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z")
        (palms if rng.random() < 0.3 else shrubs).append(matrix)
    scene.add_palms(palms, detail=False)
    scene.instances("island", "scrub", lambda: city.shrub(1.4, 9, (0.42, 0.48, 0.26)), shrubs, cast_shadow=False)
    palms = []
    boulders = []
    scrub = []
    for k in range(140):
        p = Vector((rng.uniform(-2720.0, -2400.0), rng.uniform(1080.0, 1340.0)))
        shore = scene.terrain.sample("shore", p.x, p.y)
        if shore < -2.0 or not point_in_polygon(p.x, p.y, plan.PHAROS_ISLAND):
            continue
        matrix = Matrix.Translation((p.x, p.y, scene.ground(p.x, p.y))) @ Matrix.Rotation(
            rng.uniform(0, 6.28), 4, "Z") @ Matrix.Scale(rng.uniform(0.6, 1.3), 4)
        if shore < 22.0 or rng.random() < 0.25:
            boulders.append(matrix)
        elif rng.random() < 0.8:
            scrub.append(matrix)
        else:
            palms.append(matrix)
    scene.instances("island", "land_rock", lambda: mon.land_rock(4), boulders, cast_shadow=False)
    scene.instances("island", "scrub_b", lambda: city.shrub(1.1, 13, (0.46, 0.50, 0.28)), scrub, cast_shadow=False)
    scene.add_palms(palms, detail=True)
    rocks = pharos_frame(scene) @ Matrix.Translation((0.0, 0.0, -pharos.GROUND))
    scene.unique("pharos_court", mon.lighthouse_rocks(3), rocks)
    start = Vector((-2450.0, 1296.0))
    end = plan.PHAROS.to_2d() + Vector((0.0, -62.0))
    d = end - start
    frame = Matrix.Translation((start.x, start.y, 0.0)) @ Matrix.Rotation(math.atan2(d.y, d.x) - math.pi / 2, 4, "Z")
    scene.unique("quays", mon.mole(d.length + 4.0, 10.0, top=pharos.GROUND), frame)


def build_walls(scene):
    points = [Vector(p) for p in plan.city_wall()]
    dense = resample(points, 40.0)
    segments = []
    towers = []
    distance = 0.0
    for a, b in zip(dense[:-1], dense[1:]):
        middle = (a + b) / 2
        distance += (b - a).length
        if not plan.is_land(a.x, a.y) or not plan.is_land(b.x, b.y):
            continue
        if scene.terrain.sample("shore", middle.x, middle.y) < 30.0:
            continue
        d = b - a
        z = min(scene.ground(a.x, a.y), scene.ground(b.x, b.y))
        segments.append(Matrix.Translation((a.x, a.y, z)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
                        @ Matrix.Diagonal((d.length / 40.0, 1.0, 1.0, 1.0)))
        if int(distance / 40.0) % 3 == 0:
            towers.append(Matrix.Translation((a.x, a.y, z)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
    scene.instances("walls", "wall_segment", lambda: mon.city_wall_segment(40.0), segments, cast_shadow=False)
    scene.instances("walls", "wall_tower", mon.city_tower, towers, cast_shadow=False)
    gates = []
    for t in plan.CITY_T:
        frame = grid_frame(scene, t, 0.0, turn=math.pi / 2)
        gates.append(frame)
    scene.instances("walls", "city_gate", mon.city_gate, gates, cast_shadow=False)


def chunk_allowed(scene, t, n, half_t, half_n):
    if t - half_t < plan.CITY_T[0] + 30.0 or t + half_t > plan.CITY_T[1] - 30.0:
        return False
    if n - half_n < plan.lake_n(t) + 190.0:
        return False
    coast = min(scene.coast.n(t - half_t), scene.coast.n(t + half_t), scene.coast.n(t))
    if n + half_n > coast - 46.0:
        return False
    if plan.in_royal(t, n - half_n) or plan.in_royal(t, n + half_n):
        return False
    p = plan.grid_point(t, n)
    if plan.in_site(p.x, p.y, pad=half_t + 14.0):
        return False
    if abs(t - plan.CANAL_T) < half_t + 30.0 and n < plan.KIBOTOS["n"] + 160.0:
        return False
    for corner in ((-half_t, -half_n), (half_t, -half_n), (half_t, half_n), (-half_t, half_n)):
        c = plan.grid_point(t + corner[0], n + corner[1])
        if not plan.is_land(c.x, c.y):
            return False
    return True


def build_city(scene):
    rng = random.Random(41)
    width, depth = city.CHUNK
    lane = 9.0
    detailed = {k: [] for k in range(6)}
    simple = {k: [] for k in range(6)}
    t_lo, t_hi, n_lo = NEAR_DETAIL
    for i in range(-11, 10):
        for j in range(-6, 6):
            t0 = i * plan.BLOCK_T + (15.0 if i == 0 else 4.0)
            t1 = (i + 1) * plan.BLOCK_T - (15.0 if i == -1 else 4.0)
            n0 = j * plan.BLOCK_N + (15.0 + 6.5 if j == 0 else 4.0)
            n1 = (j + 1) * plan.BLOCK_N - (15.0 + 6.5 if j == -1 else 4.0)
            count_t = max(int((t1 - t0 + lane) / (width + lane)), 1)
            count_n = max(int((n1 - n0 + lane) / (depth + lane)), 1)
            used_t = count_t * width + (count_t - 1) * lane
            used_n = count_n * depth + (count_n - 1) * lane
            for a in range(count_t):
                for b in range(count_n):
                    t = t0 + (t1 - t0 - used_t) / 2 + width / 2 + a * (width + lane)
                    n = n0 + (n1 - n0 - used_n) / 2 + depth / 2 + b * (depth + lane)
                    if not chunk_allowed(scene, t, n, width / 2, depth / 2):
                        continue
                    variant = rng.randrange(6)
                    turn = rng.choice((0.0, math.pi))
                    frame = grid_frame(scene, t, n, turn=turn)
                    near = t_lo < t < t_hi and n > n_lo
                    (detailed[variant] if near else simple[variant % 3]).append(frame)
                    p = frame.translation
                    scene.footprints.append((p.x, p.y, width / 2, depth / 2, GRID_ANGLE, 0.55))
                    scene.chunks.append((t, n))
    for variant in range(6):
        scene.instances("city", f"chunk_{variant}", lambda variant=variant: city.house_chunk(300 + variant, True),
                        detailed[variant])
        scene.instances("city", f"chunk_far_{variant}", lambda variant=variant: city.house_chunk(300 + variant, False),
                        simple[variant], cast_shadow=False)
    return sum(len(v) for v in detailed.values()), sum(len(v) for v in simple.values())


def street_ok(scene, t, n, margin=20.0):
    p = plan.grid_point(t, n)
    if not plan.is_land(p.x, p.y) or scene.terrain.sample("shore", p.x, p.y) < margin:
        return False
    if plan.in_site(p.x, p.y, pad=6.0):
        return False
    if n < plan.lake_n(t) + 180.0:
        return False
    if abs(t - plan.CANAL_T) < 30.0 and n < plan.KIBOTOS["n"]:
        return False
    return True


def near_colonnade(frame):
    p = frame.translation
    return (Vector((p.x, p.y)) - Vector((-900.0, 0.0))).length < 900.0


def build_streets(scene):
    colonnades = {0: [], 1: []}
    slabs = []
    for t in np.arange(plan.CITY_T[0] + 40.0, plan.CITY_T[1] - 40.0, 24.0):
        if abs(t) < 30.0:
            continue
        for side in (-1, 1):
            n = side * 15.6
            if not street_ok(scene, t, n) or plan.in_royal(t, n):
                continue
            colonnades[int(t / 24.0) % 2].append(grid_frame(scene, t, n, turn=0.0 if side > 0 else math.pi))
    for t in np.arange(plan.CITY_T[0] + 50.0, plan.CITY_T[1] - 50.0, 100.0):
        if street_ok(scene, t, 0.0):
            slabs.append(grid_frame(scene, t, 0.0))
    n_top = scene.coast.n(0.0) - 60.0
    for n in np.arange(plan.lake_n(0.0) + 200.0, n_top, 24.0):
        if abs(n) < 30.0:
            continue
        for side in (-1, 1):
            t = side * 15.6
            if not street_ok(scene, t, n) or plan.in_royal(t, n):
                continue
            turn = -math.pi / 2 if side > 0 else math.pi / 2
            colonnades[int(n / 24.0) % 2].append(grid_frame(scene, t, n, turn=turn))
    for n in np.arange(plan.lake_n(0.0) + 210.0, n_top, 100.0):
        if street_ok(scene, 0.0, n):
            slabs.append(grid_frame(scene, 0.0, n, turn=math.pi / 2))
    far = []
    for variant, frames in colonnades.items():
        near = [f for f in frames if near_colonnade(f)]
        far.extend(f for f in frames if not near_colonnade(f))
        scene.instances("streets", f"colonnade_{variant}", lambda variant=variant: city.colonnade(24.0, 6.4, 5.5, 6,
                                                                                                variant), near)
    scene.instances("streets", "colonnade_far", lambda: city.colonnade(24.0, 6.4, 5.5, 6, 0, detail=False), far,
                    cast_shadow=False)
    scene.instances("streets", "street_slab", lambda: city.street_slab(100.4, 30.0), slabs, cast_shadow=False)
    market = []
    rng = random.Random(77)
    for k in range(40):
        t = rng.uniform(-420.0, 420.0)
        side = rng.choice((-1, 1))
        n = side * rng.uniform(9.5, 12.5)
        rng.random()
        if abs(t) < 18.0 or not street_ok(scene, t, n):
            continue
        market.append(grid_frame(scene, t, n, turn=0.0 if side > 0 else math.pi))
    for variant in range(3):
        scene.instances("streets", f"awning_{variant}", lambda variant=variant: mon.market_awning(5.5, 3.6, variant),
                        market[variant::3])
    scene.market = market


def build_necropolis(scene):
    rng = random.Random(61)
    tombs = {0: [], 1: [], 2: []}
    palms = []
    for k in range(260):
        t = rng.uniform(plan.CITY_T[0] - 1700.0, plan.CITY_T[0] - 120.0)
        n = rng.uniform(plan.lake_n(t) + 120.0, scene.coast.n(t) - 80.0)
        p = plan.grid_point(t, n)
        if not plan.is_land(p.x, p.y) or point_in_polygon(p.x, p.y, plan.kibotos_polygon()):
            continue
        frame = grid_frame(scene, t, n, turn=rng.uniform(-0.1, 0.1))
        if rng.random() < 0.18:
            palms.append(frame)
        else:
            tombs[k % 3].append(frame)
    for variant, frames in tombs.items():
        scene.instances("necropolis", f"tomb_{variant}", lambda variant=variant: mon.tomb(variant), frames,
                        cast_shadow=False)
    scene.add_palms(palms, detail=False)


def build_countryside(scene):
    rng = random.Random(83)
    palms = []
    trees = []
    for k in range(320):
        t = rng.uniform(plan.CITY_T[1] + 80.0, plan.CITY_T[1] + 4200.0)
        n = rng.uniform(plan.lake_n(t) - 40.0, scene.coast.n(t) - 70.0)
        p = plan.grid_point(t, n)
        if scene.terrain.sample("shore", p.x, p.y) < 20.0:
            continue
        frame = grid_frame(scene, t, n, turn=rng.uniform(0, 6.28))
        (palms if rng.random() < 0.8 else trees).append(frame)
    for k in range(120):
        t = rng.uniform(-2500.0, 2600.0)
        n = plan.lake_n(t) + rng.uniform(15.0, 130.0)
        p = plan.grid_point(t, n)
        if scene.terrain.sample("shore", p.x, p.y) < 10.0 or plan.in_site(p.x, p.y, 10.0):
            continue
        palms.append(grid_frame(scene, t, n, turn=rng.uniform(0, 6.28)))
    for k in range(60):
        n = rng.uniform(plan.lake_n(plan.CANAL_T) + 60.0, plan.KIBOTOS["n"] - 120.0)
        t = plan.CANAL_T + rng.choice((-1, 1)) * rng.uniform(18.0, 26.0)
        palms.append(grid_frame(scene, t, n, turn=rng.uniform(0, 6.28)))
    scene.add_palms(palms, detail=False)
    scene.instances("countryside", "sycamore", lambda: city.broad_tree(10.0, 19, (0.30, 0.44, 0.18), 7), trees,
                    cast_shadow=False)


def ship_spots(scene):
    rng = random.Random(97)
    spots = []

    def add(key, x, y, heading, check=True):
        if check and not is_water(scene, x, y, 18.0):
            return
        for other in spots:
            if (Vector((x, y)) - Vector(other[1][:2])).length < 34.0:
                return
        spots.append((key, (x, y), heading))

    harbour = [("merchant_brailed", 9), ("carrier_furled", 5), ("galley", 3), ("lighter", 6), ("fishing", 4),
               ("merchant_brailed_b", 6)]
    for key, count in harbour:
        placed = 0
        tries = 0
        while placed < count and tries < 400:
            tries += 1
            x = rng.uniform(-1950.0, -350.0)
            y = rng.uniform(220.0, 1150.0)
            if y > 1260.0 - (x + 1950.0) * 0.05:
                continue
            if scene.terrain.sample("reef", x, y) < 80.0:
                continue
            before = len(spots)
            heading = rng.uniform(0, 6.28)
            add(key, x, y, heading if key in ("lighter", "fishing") else rng.gauss(0.0, 0.25))
            placed += len(spots) - before
    add("state_galley", -980.0, 590.0, math.radians(200.0))
    for k in range(7):
        x = rng.uniform(-2260.0, -1900.0)
        y = rng.uniform(980.0, 1320.0)
        if scene.terrain.sample("reef", x, y) < 60.0 or (Vector((x, y)) - plan.PHAROS.to_2d()).length < 160.0:
            continue
        key = rng.choice(["carrier_furled", "merchant_brailed", "merchant_brailed_b", "galley", "carrier_furled"])
        rng.uniform(0, 6.28)
        add(key, x, y, rng.gauss(0.0, 0.25))
    for k in range(8):
        x = rng.uniform(-2180.0, -1480.0)
        y = rng.uniform(560.0, 1180.0)
        if scene.terrain.sample("reef", x, y) < 60.0:
            continue
        key = rng.choice(["merchant_brailed", "carrier_furled", "merchant_brailed_b", "merchant_brailed", "galley",
                          "carrier_furled"])
        rng.uniform(0, 6.28)
        add(key, x, y, rng.gauss(0.0, 0.25))
    for k in range(7):
        t = -980.0 + k * 75.0
        n = scene.coast.n(t) + 6.5
        p = plan.grid_point(t, n)
        add("merchant_brailed" if k % 2 else "merchant_brailed_b", p.x, p.y,
            GRID_ANGLE - math.pi / 2 + (0.0 if k % 2 else math.pi), check=False)
    entering = [("carrier_set", -1900.0, 1650.0), ("merchant_set", -1600.0, 1900.0), ("merchant_set", -2050.0, 2200.0),
                ("fishing_sail", -1450.0, 1500.0), ("carrier_set", -800.0, 2600.0), ("merchant_set", -2600.0, 2700.0)]
    for key, x, y in entering:
        add(key, x, y, math.radians(180.0 + rng.uniform(-15.0, 15.0)))
    hepta = scene.hepta_frame
    for k in range(8):
        local = Vector((-rng.uniform(70.0, 330.0), rng.uniform(120.0, scene.hepta_length - 150.0), 0.0))
        p = hepta @ local
        key = rng.choice(["merchant_brailed", "carrier_furled", "lighter", "merchant_brailed_b", "merchant_brailed"])
        rng.uniform(0, 6.28)
        add(key, p.x, p.y, rng.uniform(0, 6.28) if key == "lighter" else rng.gauss(0.0, 0.25))
    for k in range(6):
        x = rng.uniform(-4300.0, -2500.0)
        y = rng.uniform(-900.0, 400.0)
        if point_in_polygon(x, y, plan.PHAROS_ISLAND):
            continue
        key = rng.choice(["merchant_brailed", "carrier_furled", "merchant_brailed", "fishing", "merchant_brailed_b"])
        rng.uniform(0, 6.28)
        add(key, x, y, rng.uniform(0, 6.28) if key == "fishing" else rng.gauss(0.0, 0.25))
    for k in range(10):
        t = rng.uniform(-2400.0, 1400.0)
        n = plan.lake_n(t) - rng.uniform(80.0, 900.0)
        p = plan.grid_point(t, n)
        add(rng.choice(["barge_set", "barge_set", "fishing", "barge_set"]), p.x, p.y,
            GRID_ANGLE + rng.choice((0.0, math.pi)) + rng.uniform(-0.4, 0.4))
    bridge_y = scene.hepta_length * HEPTA_BRIDGES[1] - 7.0
    boat = scene.hepta_frame @ Vector((-plan.HEPTASTADION_WIDTH / 2 - 3.0, bridge_y - 0.6, 0.0))
    axis = scene.hepta_frame.to_3x3() @ Vector((1.0, 0.0, 0.0))
    spots[:] = [spot for spot in spots if (Vector(spot[1]) - boat.to_2d()).length > 30.0]
    spots.append(("lighter", (boat.x, boat.y), math.atan2(axis.y, axis.x) - math.pi / 2 + 0.15))
    return spots


SHIP_BUILDS = {
    "merchant_brailed": lambda: ships.merchant(1, "brailed"),
    "merchant_brailed_b": lambda: ships.merchant(4, "brailed", 18.0, 5.6),
    "merchant_set": lambda: ships.merchant(2, "set"),
    "merchant_set_b": lambda: ships.merchant(5, "set", 19.0, 5.8),
    "carrier_furled": lambda: ships.grain_carrier(3, "furled"),
    "carrier_set": lambda: ships.grain_carrier(6, "set"),
    "galley": lambda: ships.galley(7),
    "state_galley": lambda: ships.galley(8, 42.0, 5.8, state=True),
    "lighter": lambda: ships.lighter(9),
    "fishing": lambda: ships.fishing_boat(10),
    "fishing_sail": lambda: ships.fishing_boat(11, sail=True),
    "barge_set": lambda: ships.nile_barge(12, sail="set"),
    "barge_furled": lambda: ships.nile_barge(13, sail="furled"),
}


def build_ships(scene):
    spots = ship_spots(scene)
    grouped = {}
    for key, (x, y), heading in spots:
        grouped.setdefault(key, []).append(Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(heading, 4, "Z"))
    for key, matrices in grouped.items():
        scene.instances("ships", f"ship_{key}", SHIP_BUILDS[key], matrices)
    return {key: len(v) for key, v in grouped.items()}


def build_reef_rocks(scene):
    rng = random.Random(29)
    rocks = []
    for reef in plan.REEFS:
        for point in resample([Vector(p) for p in reef], 70.0):
            if rng.random() < 0.6:
                x = point.x + rng.uniform(-20.0, 20.0)
                y = point.y + rng.uniform(-20.0, 20.0)
                rocks.append(Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z"))
    scene.instances("water", "reef_rock", lambda: mon.reef_rock(2), rocks, cast_shadow=False)


def build_surface(scene):
    objects = []
    for name in WALKABLE:
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in [root] + list(root.children_recursive):
            if item.type != "MESH" or item.name.startswith("terrain_far") or item.name.startswith("terrain_mid"):
                continue
            if item.name.startswith(("column_", "aqueduct", "bollard", "awning", "colonnade", "grove_tree", "garden")):
                continue
            objects.append(item)
    scene.surface = Surface(objects)


def add_route(scene, name, points, hint, reach=4.0):
    root = scene.root("life")
    chain = []
    for point in resample([Vector((p[0], p[1], 0.0)) for p in points], 2.6):
        z = scene.surface.height(point.x, point.y, hint(point), reach)
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        previous = refined[-1]
        middle = (previous + following) / 2
        middle.z = scene.surface.height(middle.x, middle.y, max(previous.z, following.z), 2.0)
        if abs(middle.z - (previous.z + following.z) / 2) > 0.05:
            refined.append(middle)
        refined.append(following)
    for index, point in enumerate(refined):
        new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(point))
    scene.routes[name] = refined
    scene.route_samples.extend(point.to_2d() for point in resample(refined, 0.6))
    return len(refined)


def route_report(scene):
    report = {}
    for name, points in scene.routes.items():
        worst = 0.0
        longest = 0.0
        where = None
        for a, b in zip(points[:-1], points[1:]):
            if abs(b.z - a.z) > worst:
                worst = abs(b.z - a.z)
                where = [round(a.x, 1), round(a.y, 1), round(a.z, 2), round(b.z, 2)]
            longest = max(longest, (b - a).length)
        report[name] = {"points": len(points), "max_step": round(worst, 2), "max_spacing": round(longest, 2),
                        "worst_at": where, "z_range": [round(min(p.z for p in points), 2),
                                                       round(max(p.z for p in points), 2)]}
    return report


def build_routes(scene):
    counts = {}
    west = [Vector(p) for p in ((-1720.0, -45.0), (-1480.0, 0.0), (-1345.0, 29.0))]
    east = [Vector(p) for p in ((-1152.0, 66.0), (-1010.0, 62.0), (-860.0, 66.0))]
    for name, line in (("quai_ouest", west), ("quai_est", east)):
        walk = path_offset([tuple(p) for p in resample(line, 20.0)], 4.5)
        counts[name] = add_route(scene, name, walk, lambda p: plan.QUAY_TOP + 0.6, 2.0)
    frame = scene.hepta_frame
    length = scene.hepta_length
    hepta = [frame @ Vector((-3.0, y, 0.0)) for y in np.arange(-10.0, length + 10.0, 20.0)]
    counts["heptastade"] = add_route(scene, "heptastade", hepta, lambda p: 7.0, 8.0)
    c = scene.caesareum_frame
    ces = [c @ Vector((x, y, 0.0)) for x, y in ((-40.0, 116.0), (-26.0, 106.0), (-6.0, 92.0), (0.0, 75.0),
                                                 (0.0, 48.0),
                                                 (-24.0, 30.0), (-30.0, -20.0), (-24.0, -45.0), (0.0, -48.0),
                                                 (24.0, -45.0), (30.0, -20.0), (24.0, 30.0), (0.0, 48.0))]
    base = c.translation.z
    counts["cesareum"] = add_route(scene, "cesareum", ces, lambda p: base + 1.0, 2.5)
    canopic = [plan.grid_point(t, -6.0) for t in np.arange(-400.0, 400.0, 20.0)]
    counts["canopique"] = add_route(scene, "canopique", canopic, lambda p: scene.ground(p.x, p.y) + 2.0, 5.0)
    pf = pharos_frame(scene)
    court = [pf @ Vector((x, y, 0.0)) for x, y in ((0.0, -66.0), (0.0, -55.0), (-12.0, -48.0), (-30.0, -36.0),
                                                   (-36.0, 0.0), (-30.0, 30.0), (0.0, 38.0), (30.0, 30.0),
                                                   (36.0, 0.0), (28.0, -36.0), (12.0, -48.0))]
    counts["phare"] = add_route(scene, "phare", court, lambda p: pharos.GROUND + 0.5, 2.5)
    return counts


def clear_of_routes(scene, x, y, radius):
    point = Vector((x, y))
    return all((point - sample).length > radius for sample in scene.route_samples[::2])


def ground_on_surface(scene, x, y, hint):
    return scene.surface.height(x, y, hint, 6.0)


def populate(scene, eyes):
    rng = random.Random(131)
    placed = {}

    def put(key, x, y, heading, hint, radius=1.4):
        if not clear_of_routes(scene, x, y, radius):
            return
        if min((Vector((x, y)) - eye).length for eye in eyes) < 26.0:
            return
        z = ground_on_surface(scene, x, y, hint)
        placed.setdefault(key, []).append(Matrix.Translation((x, y, z)) @ Matrix.Rotation(heading, 4, "Z"))

    quay_keys = ["dock_gang", "dock_gang", "scale_table", "dock_gang", "conversation", "conversation_b",
                 "amphora_stack", "amphora_stack", "camel_train", "fig_docker", "fig_sack", "fig_greek", "fig_egyptian",
                 "conversation_c", "fig_lady", "fisher_pair"]
    for t in np.arange(-1100.0, -110.0, 9.0):
        n = scene.coast.n(t)
        for k in range(2):
            if rng.random() < 0.72:
                continue
            inset = rng.uniform(2.5, 22.0)
            p = plan.grid_point(t + rng.uniform(-3.0, 3.0), n - inset)
            key = rng.choice(quay_keys)
            put(key, p.x, p.y, GRID_ANGLE + rng.uniform(-math.pi, math.pi), plan.QUAY_TOP + 1.5,
                2.6 if "gang" in key or "table" in key or "camel" in key else 1.3)
    c = scene.caesareum_frame
    for k in range(40):
        x = rng.uniform(-70.0, 70.0)
        y = rng.uniform(64.0, 140.0)
        if abs(abs(x) - 14.0) < 6.0 and abs(y - 86.0) < 6.0:
            continue
        p = c @ Vector((x, y, 0.0))
        put(rng.choice(["conversation", "conversation_b", "fig_greek", "fig_greek_b", "fig_lady", "fig_lady_b",
                        "fig_child", "conversation_c"]), p.x, p.y, rng.uniform(0, 6.28), c.translation.z + 2.0)
    for x in (-6.0, 6.0):
        p = c @ Vector((x, 66.0, 0.0))
        put("guards", p.x, p.y, GRID_ANGLE + math.pi, c.translation.z + 2.0, 0.5)
    frame = scene.hepta_frame
    axis = frame.to_3x3() @ Vector((0.0, 1.0, 0.0))
    along = math.atan2(axis.y, axis.x) - math.pi / 2
    for k in range(52):
        y = rng.uniform(20.0, scene.hepta_length - 20.0) if k < 36 else rng.uniform(
            scene.hepta_length * HEPTA_BRIDGES[1] + 30.0, scene.hepta_length * HEPTA_BRIDGES[1] + 92.0)
        x = rng.choice((-8.6, -8.6, 4.5, 2.0))
        p = frame @ Vector((x, y, 0.0))
        key = rng.choice(["donkey_driver", "fig_docker", "fig_greek", "fig_egyptian", "fisher_pair", "fig_lady",
                          "ox_cart", "conversation_c", "fig_sack", "camel_train"])
        if key == "fisher_pair":
            put(key, p.x, p.y, along - math.pi / 2, 7.0)
        else:
            put(key, p.x, p.y, along + rng.choice((0.0, math.pi)), 7.0, 2.0)
    for frame in scene.market:
        for k in range(rng.randrange(1, 4)):
            local = frame @ Vector((rng.uniform(-3.0, 3.0), rng.uniform(-4.5, -2.6) * rng.choice((1, -1)), 0.0))
            put(rng.choice(["fig_greek", "fig_lady", "fig_egyptian", "conversation_c", "fig_child", "fig_lady_b",
                            "fig_greek_b"]), local.x, local.y, rng.uniform(0, 6.28), frame.translation.z + 2.0)
    pf = pharos_frame(scene)
    for x, y, key in ((-30.0, -40.0, "conversation_c"), (24.0, -44.0, "guards"), (40.0, 20.0, "conversation_c"),
                      (-6.0, -60.0, "guards")):
        p = pf @ Vector((x, y, 0.0))
        put(key, p.x, p.y, rng.uniform(0, 6.28), pharos.GROUND + 2.0, 0.5)
    counts = {}
    for key, matrices in placed.items():
        scene.instances("life", key, alife.LIFE[key], matrices, cast_shadow=True)
        counts[key] = len(matrices)
    return counts


def place_effects(scene):
    root = scene.root("life")
    rng = random.Random(7)
    smokes = []
    for k in range(40):
        if len(smokes) >= 7:
            break
        t, n = rng.choice(scene.chunks)
        p = plan.grid_point(t + rng.uniform(-20, 20), n + rng.uniform(-20, 20))
        if any((p - q.to_2d()).length < 250.0 for q in smokes):
            continue
        smokes.append(Vector((p.x, p.y, scene.ground(p.x, p.y) + 14.0)))
    kib = plan.grid_point(plan.KIBOTOS["t"] + 150.0, plan.KIBOTOS["n"] - 120.0)
    smokes.append(Vector((kib.x, kib.y, scene.ground(kib.x, kib.y) + 11.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(Vector((-1300.0, 700.0)), 45.0), (Vector((-2250.0, 1250.0)), 70.0), (Vector((-700.0, 300.0)), 38.0),
              (Vector((-2000.0, 500.0)), 30.0), (Vector((-400.0, 900.0)), 55.0)]
    for index, (point, height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation((point.x, point.y, height)))
    for index, (key, build) in enumerate(alife.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke": len(smokes), "birds": len(flocks), "walkers": len(alife.WALKERS)}


def weather_all(scene):
    done = set()
    for name, root in scene.roots.items():
        if name in ("terrain", "water", "markers"):
            continue
        for item in root.children_recursive:
            if item.type != "MESH" or item.data.name in done:
                continue
            mesh = item.data
            done.add(mesh.name)
            seed = sum(ord(character) for character in mesh.name) % 97
            heights = None
            world_z = None
            if item.parent is root and not item.name.startswith("walker"):
                co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
                mesh.vertices.foreach_get("co", co)
                co = co.reshape(-1, 3)
                heights = co[:, 2] - scene.terrain.height(co[:, 0], co[:, 1])
                world_z = co[:, 2]
            foliage = name in ("palms", "palaces", "countryside", "island", "caesareum")
            aweather.weather(mesh, heights, world_z, seed, foliage)
            if name in ("city", "palaces", "harbour", "pharos", "pharos_court", "caesareum", "monuments", "streets",
                        "emporion", "island") and len(mesh.vertices) < 60000:
                nimes_detail.occlusion(mesh, seed)


def viewpoints(scene):
    p = plan.PHAROS
    points = {}
    points["vue-d-ensemble"] = (Vector((-1900.0, 2600.0, 450.0)), Vector((-1600.0, 150.0, 0.0)))
    eye = p + Vector((-165.0, -95.0))
    points["le-phare"] = (Vector((eye.x, eye.y, max(scene.ground(eye.x, eye.y), 0.0) + 14.0)),
                          Vector((p.x, p.y, 58.0)))
    points["le-grand-port"] = (Vector((p.x + 6.5, p.y - 9.0, pharos.GROUND + pharos.OCTAGON_TOP + 3.2)),
                               Vector((-1250.0, 520.0, -40.0)))
    frame = scene.hepta_frame
    bridge = scene.hepta_length * HEPTA_BRIDGES[1]
    eye = frame @ Vector((-52.0, bridge + 58.0, 0.0))
    target = frame @ Vector((-8.0, bridge - 4.0, 0.0))
    points["l-heptastade"] = (Vector((eye.x, eye.y, 6.0)), Vector((target.x, target.y, 3.2)))
    c = scene.caesareum_frame
    eye = c @ Vector((24.0, 128.0, 0.0))
    target = c @ Vector((-4.0, 60.0, 0.0))
    points["le-cesareum"] = (Vector((eye.x, eye.y, c.translation.z + 5.5)),
                             Vector((target.x, target.y, c.translation.z + 13.0)))
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
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.8, aerosol=0.6)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 4.6, (1.0, 0.78, 0.55), 0.8)
    configure_render(1280, 720, options["samples"], exposure=0.0)
    view = bpy.context.scene.view_settings
    for look in ("AgX - Punchy", "Punchy"):
        try:
            view.look = look
            break
        except TypeError:
            continue
    timings = {}
    for name in names:
        eye, target = points[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=LENS, clip_end=150000.0)
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
    terrain = aterrain.Terrain()
    print("FIELDS", round(time.perf_counter() - started, 1), flush=True)
    scene = Scene(tiles, terrain)
    scene.coast = Coast()
    beacon = build_pharos(scene)
    build_heptastadion(scene)
    build_quays(scene)
    build_harbour(scene)
    build_caesareum(scene)
    build_theatre(scene)
    build_palaces(scene)
    build_gymnasium(scene)
    build_paneion(scene)
    build_serapeum(scene)
    build_island(scene)
    build_walls(scene)
    chunk_counts = build_city(scene)
    build_streets(scene)
    build_necropolis(scene)
    build_countryside(scene)
    print("CITY", chunk_counts, round(time.perf_counter() - started, 1), flush=True)
    ship_counts = build_ships(scene)
    build_reef_rocks(scene)
    scene.place_palms()
    place_columns(scene)
    scene.flush()
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
    glb = os.path.join(CACHE, "alexandrie.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION], "beacon": [round(v, 2) for v in beacon],
        "pharos_height": round(pharos.total_height(), 1),
        "counts": {"chunks": chunk_counts, "ships": ship_counts, "routes": route_counts, "life": life_counts,
                   "effects": effects, "figures_estimate": sum(life_counts.values())},
        "route_checks": route_report(scene),
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "build_seconds": round(time.perf_counter() - started, 1), "terrain_source": aterrain.SOURCE,
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

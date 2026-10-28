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

from kit import alexandrie_monuments as amon
from kit import alexandrie_ships as ships
from kit import alexandrie_weather as aweather
from kit import ephese_artemision as art
from kit import ephese_city as city
from kit import ephese_flora as flora
from kit import ephese_gate as egate
from kit import ephese_life as elife
from kit import ephese_terrain as et
from kit import nimes_detail, nimes_figures
from kit.ephese_materials import build_library, remap
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, principled_material, save_pixels
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, render_still, sun_lamp
from kit.terrain import point_in_polygon

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "ephese")
BLEND = os.path.join(CACHE, "work", "ephese.blend")
SUN_AZIMUTH = 245.0
SUN_ELEVATION = 34.0
LENS = 30.0
TEMPLE = Vector((0.0, -11.0))
TEMPLE_ANGLE = -math.pi / 2
GROUND = et.SANCTUARY_LEVEL
ALTAR = Vector((-112.0, -11.0))
GATE = Vector((-270.0, -11.0))
CORE = (-400.0, -256.0, 256.0, 256.0)
INNER = (-3680.0, -2208.0, 800.0, 1216.0)
SPLIT_X = -1440.0
NEAR = (et.NEAR["x0"], et.NEAR["y0"], et.NEAR["x1"], et.NEAR["y1"])
FAR = (-et.FAR_HALF, -et.FAR_HALF, et.FAR_HALF, et.FAR_HALF)
MAGNESIAN = Vector((-1528.0, -1665.0))
KORESSOS = Vector((-1790.0, -432.0))
STREET_A = Vector((-2690.0, -705.0))
STREET_B = Vector((-2010.0, -933.0))
STADIUM = Vector((-1905.0, -330.0))
VEDIUS = Vector((-1686.0, -144.0))
LOWER_CITY = [(-2780.0, -500.0), (-2450.0, -470.0), (-2050.0, -450.0), (-1830.0, -480.0), (-1845.0, -760.0),
              (-1885.0, -880.0), (-1990.0, -1050.0), (-2150.0, -1130.0), (-2500.0, -1080.0), (-2700.0, -985.0),
              (-2860.0, -860.0)]
UPPER_CITY = [(-2150.0, -1130.0), (-1990.0, -1060.0), (-1880.0, -1150.0), (-1700.0, -1350.0), (-1580.0, -1560.0),
              (-1610.0, -1690.0), (-1760.0, -1660.0), (-1900.0, -1500.0), (-2060.0, -1350.0), (-2180.0, -1220.0)]
WALL_SOUTH = [(-3060.0, -830.0), (-3150.0, -1000.0), (-3200.0, -1160.0), (-3100.0, -1190.0), (-3000.0, -1220.0),
              (-2900.0, -1270.0), (-2800.0, -1310.0), (-2700.0, -1500.0), (-2620.0, -1800.0), (-2500.0, -1890.0),
              (-2400.0, -1890.0), (-2300.0, -1960.0), (-2200.0, -2030.0), (-2100.0, -2130.0), (-2000.0, -2270.0),
              (-1900.0, -2360.0), (-1800.0, -2380.0), (-1700.0, -2250.0), (-1620.0, -2000.0), (-1560.0, -1780.0),
              (-1540.0, -1690.0)]
WALL_EAST = [(-1515.0, -1640.0), (-1450.0, -1560.0), (-1400.0, -1420.0), (-1360.0, -1300.0), (-1360.0, -1100.0),
             (-1390.0, -900.0), (-1350.0, -800.0), (-1290.0, -700.0), (-1310.0, -600.0), (-1420.0, -520.0),
             (-1600.0, -450.0), (-1770.0, -425.0)]
WALL_NORTH = [(-1810.0, -437.0), (-2100.0, -445.0), (-2400.0, -455.0), (-2650.0, -485.0), (-2800.0, -525.0)]
CIRCUIT = WALL_SOUTH + WALL_EAST + WALL_NORTH
WALKABLE = ("terrain", "sanctuary_ground", "harbour", "streets", "roads")
LENSES = {"l-artemision": 35.0, "la-statue-d-artemis": 40.0, "la-voie-sacree": 40.0}
CLOSE_ZONES = [((-50.0, 0.0), 330.0), ((-1528.0, -1665.0), 300.0), ((-2874.0, -644.0), 380.0)]
ARTEMIS_SCALE = 1.5


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

    def height(self, x, y, below=None):
        top = 900.0 if below is None else below
        hit = self.tree.ray_cast(Vector((x, y, top)), Vector((0.0, 0.0, -1.0)), top + 200.0)
        return None if hit[0] is None else hit[0].z


class Scene:
    def __init__(self, tiles, land):
        self.tiles = tiles
        self.land = land
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Ephese")
        self.roots = {}
        self.pending = {}
        self.surface = None
        self.routes = {}
        self.route_samples = []
        self.footprints = []
        self.columns = {}
        self.blocked = []
        self.smokes = []
        self.trees = {}
        self.altar_smoke = None
        self.chunks = []

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        x0, y0, x1, y1 = NEAR
        if x0 + 1 < x < x1 - 1 and y0 + 1 < y < y1 - 1:
            return float(self.land.near.sample(x, y))
        return float(self.land.far.sample(x, y))

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

    def add_columns(self, kind, frames):
        self.columns.setdefault(kind, []).extend(frames)

    def add_trees(self, kind, matrices):
        self.trees.setdefault(kind, []).extend(matrices)

    def block(self, x, y, radius):
        self.blocked.append((x, y, radius))

    def free(self, x, y, radius=0.0):
        return all(math.hypot(x - bx, y - by) > br + radius for bx, by, br in self.blocked)


def frame_at(scene, x, y, angle=0.0, z=None, lift=0.0):
    height = scene.ground(x, y) if z is None else z
    return Matrix.Translation((x, y, height + lift)) @ Matrix.Rotation(angle, 4, "Z")


def temple_frame():
    return Matrix.Translation((TEMPLE.x, TEMPLE.y, GROUND)) @ Matrix.Rotation(TEMPLE_ANGLE, 4, "Z")


def altar_frame():
    return Matrix.Translation((ALTAR.x, ALTAR.y, GROUND)) @ Matrix.Rotation(math.pi / 2, 4, "Z")


def resample(points, spacing):
    out = [Vector(points[0])]
    for start, end in zip(points[:-1], points[1:]):
        a, b = Vector(start), Vector(end)
        count = max(int(math.ceil((b - a).length / spacing - 1e-6)), 1)
        for k in range(1, count + 1):
            out.append(a + (b - a) * (k / count))
    return out


def path_offset(points, offset):
    result = []
    for index, point in enumerate(points):
        a = Vector(points[max(index - 1, 0)][:2])
        b = Vector(points[min(index + 1, len(points) - 1)][:2])
        direction = (b - a).normalized()
        right = Vector((direction.y, -direction.x))
        result.append(Vector(point[:2]) + right * offset)
    return result


def build_sanctuary(scene):
    tf = temple_frame()
    scene.unique("artemision", art.temple(), tf)
    for key, frames in art.column_frames().items():
        world = [tf @ f for f in frames]
        if key == "plain":
            scene.add_columns("ionic_full", world)
        else:
            scene.instances("artemision", f"column_{key}", lambda k=int(key[-1]): art.ionic_column(caelata=True, seed=k),
                            world)
    naiskos = tf @ Matrix.Translation((0.0, art.STATUE_Y, art.Z0))
    scene.unique("artemision", art.naiskos(), naiskos)
    small = [naiskos @ Matrix.Translation((x, y, 1.0)) for x in (-3.6, 3.6) for y in (-3.4, 3.6)]
    scene.instances("artemision", "naiskos_column", art.naiskos_column, small)
    statue = naiskos @ Matrix.Translation((0.0, 1.2, 1.0)) @ Matrix.Scale(ARTEMIS_SCALE, 4)
    scene.unique("statue", art.artemis_statue(), statue)
    lamps = [tf @ Matrix.Translation((x, y, art.Z0)) for x in (-6.5, 6.5) for y in (art.STATUE_Y - 9.0,
                                                                                    art.STATUE_Y - 18.0)]
    scene.instances("artemision", "lampstand", art.lampstand, lamps, cast_shadow=False)
    af = altar_frame()
    court, frames, smoke, base = art.altar_court()
    scene.unique("altar", court, af)
    scene.add_columns("ionic_mid", [af @ f for f in frames])
    scene.altar_smoke = af @ smoke
    scene.altar_floor = GROUND + base
    pf = Matrix.Translation((GATE.x, GATE.y, GROUND)) @ Matrix.Rotation(-math.pi / 2, 4, "Z")
    gate, frames = art.propylon()
    scene.unique("sanctuary", gate, pf)
    scene.add_columns("ionic_mid", [pf @ f for f in frames])
    x0, x1, y0, y1 = et.SANCTUARY
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    segments = []
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        a, b = Vector((ax, ay)), Vector((bx, by))
        count = max(int((b - a).length / 40.0), 1)
        for k in range(count):
            p = a + (b - a) * (k / count)
            q = a + (b - a) * ((k + 1) / count)
            middle = (p + q) / 2
            if abs(middle.x - GATE.x) < 2.0 and abs(middle.y - GATE.y) < 26.0:
                for p2, q2 in ((p, Vector((p.x, GATE.y - 12.0))), (Vector((p.x, GATE.y + 12.0)), q)):
                    if (q2 - p2).length > 1.0 and (p2.y - GATE.y) * (q2.y - GATE.y) > 0:
                        segments.append((p2, q2))
                continue
            segments.append((p, q))
    frames = []
    for p, q in segments:
        d = q - p
        frames.append(Matrix.Translation((p.x, p.y, GROUND)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
                      @ Matrix.Diagonal((d.length / 40.0, 1.0, 1.0, 1.0)))
    scene.instances("sanctuary", "peribolos", lambda: art.peribolos_segment(40.0), frames, cast_shadow=True)
    ground = MeshBuilder()
    art.painted(ground, (0.97, 0.94, 0.88), lambda: ground.box((-137.0, -60.0, GROUND - 0.6), (75.0, 38.0,
                                                                                              GROUND + 0.05),
                                                              art.POLYGONAL, bottom=False))
    art.painted(ground, (0.98, 0.95, 0.88), lambda: ground.box((GATE.x - 8.0, GATE.y - 8.0, GROUND - 0.6),
                                                              (-137.0, GATE.y + 8.0, GROUND + 0.04), "paving",
                                                              bottom=False))
    scene.unique("sanctuary_ground", ground)
    statues = []
    for x in np.arange(-252.0, -145.0, 12.0):
        statues.append(Matrix.Translation((x, GATE.y + 9.5, GROUND + 0.04)))
        statues.append(Matrix.Translation((x, GATE.y - 9.5, GROUND + 0.04)) @ Matrix.Rotation(math.pi, 4, "Z"))
    for y in (-52.0, -44.0, 22.0, 30.0):
        statues.append(Matrix.Translation((-72.0, y, GROUND + 0.05)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    bronze = statues[0::2]
    marble = statues[1::2]
    scene.instances("sanctuary", "honorific_bronze", lambda: nimes_figures.honorific_statue(True), bronze)
    scene.instances("sanctuary", "honorific_marble", lambda: nimes_figures.honorific_statue(False), marble)
    for x, y, r in ((0.0, -11.0, 72.0), (ALTAR.x, ALTAR.y, 26.0)):
        scene.block(x, y, r)
    rng = random.Random(9)
    grove = []
    for k in range(160):
        x = rng.uniform(x0 + 8.0, x1 - 8.0)
        y = rng.uniform(y0 + 8.0, y1 - 8.0)
        if abs(y - GATE.y) < 14.0 and x < -130.0:
            continue
        if -140.0 < x < 80.0 and -64.0 < y < 42.0:
            continue
        if x > 60.0 or rng.random() < 0.35:
            grove.append((x, y))
    for x, y in grove:
        matrix = frame_at(scene, x, y, rng.uniform(0, 6.28))
        kind = rng.random()
        scene.add_trees("cypress" if kind < 0.45 else ("plane" if kind < 0.8 else "olive"), [matrix])
    for k in range(int((x1 - x0) / 9.0)):
        x = x0 + 4.0 + k * 9.0
        for y in (y0 - 6.0, y1 + 6.0):
            if rng.random() < 0.7:
                scene.add_trees("cypress", [frame_at(scene, x + rng.uniform(-1, 1), y, rng.uniform(0, 6.28))])
    votive = []
    for k in range(60):
        x = rng.uniform(-250.0, 150.0)
        y = rng.uniform(-140.0, 120.0)
        if -140.0 < x < 80.0 and -64.0 < y < 42.0:
            continue
        if abs(y - GATE.y) < 12.0 or not scene.free(x, y, 4.0):
            continue
        votive.append(frame_at(scene, x, y, rng.choice((0.0, math.pi / 2, math.pi, -math.pi / 2)), z=GROUND))
        scene.block(x, y, 3.0)
    scene.instances("sanctuary", "votive_bronze", lambda: nimes_figures.honorific_statue(True), votive[0::3])
    scene.instances("sanctuary", "votive_altar", art.votive_altar, votive[1::3], cast_shadow=False)
    scene.instances("sanctuary", "votive_stele", art.votive_stele, votive[2::3], cast_shadow=False)
    hamlet = []
    roads = [Vector(p) for p in et.SACRED_WAY[-8:]] + [Vector(p) for p in et.NORTH_ROAD[-5:]]
    for k in range(400):
        if len(hamlet) >= 12:
            break
        x = rng.uniform(-470.0, -300.0)
        y = rng.uniform(-150.0, 110.0)
        if min((Vector((x, y)) - r).length for r in resample(roads, 10.0)) < 24.0 or not scene.free(x, y, 18.0):
            continue
        scene.block(x, y, 14.0)
        hamlet.append(frame_at(scene, x, y, rng.choice((0.0, math.pi / 2)), z=GROUND - 0.2))
        scene.footprints.append((x, y, 12.0, 9.0, 0.0, 0.5))
        scene.chunks.append(Vector((x, y, GROUND)))
    scene.instances("sanctuary", "hamlet_house", lambda: city.terrace_chunk(930, True, 24.0, 18.0, plinth=3.0),
                    hamlet)
    scene.footprints.append(((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, 0.0, 0.0))


def build_walls(scene):
    frames = []
    towers = []
    for line in (WALL_SOUTH, WALL_EAST, WALL_NORTH):
        dense = resample([Vector(p) for p in line], 24.0)
        distance = 0.0
        for a, b in zip(dense[:-1], dense[1:]):
            d = b - a
            distance += d.length
            z = min(scene.ground(a.x, a.y), scene.ground(b.x, b.y))
            frames.append(Matrix.Translation((a.x, a.y, z)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
                          @ Matrix.Diagonal(((d.length + 0.6) / 24.0, 1.0, 1.0, 1.0)))
            if int(distance / 24.0) % 5 == 0:
                towers.append(Matrix.Translation((a.x, a.y, scene.ground(a.x, a.y) - 1.0)) @ Matrix.Rotation(
                    math.atan2(d.y, d.x), 4, "Z"))
    scene.instances("walls", "city_wall", lambda: wall_segment(24.0), frames, cast_shadow=False)
    scene.instances("walls", "city_tower", tower, towers, cast_shadow=False)
    for point, nxt, road in ((MAGNESIAN, Vector(et.SACRED_WAY[1]), "sacred"),
                             (KORESSOS, Vector(et.NORTH_ROAD[1]), "north")):
        d = nxt - point
        level = scene.land.roads[road][1][0] + 0.02
        frame = frame_at(scene, point.x, point.y, math.atan2(d.y, d.x) - math.pi / 2, z=level)
        scene.unique("city", egate.magnesian_gate(), frame)
        scene.block(point.x, point.y, 22.0)


def wall_segment(length):
    builder = MeshBuilder()
    city.painted(builder, (0.92, 0.86, 0.74), lambda: builder.box((0.0, -2.2, -9.0), (length, 2.2, 8.0), city.STONE,
                                                                  bottom=False))
    for k in range(int(length / 2.6)):
        x = 1.3 + k * 2.6
        city.painted(builder, (0.92, 0.86, 0.74), lambda x=x: builder.box((x - 0.65, 1.5, 8.0), (x + 0.65, 2.2, 9.2),
                                                                         city.STONE, bottom=False))
    return builder


def tower():
    return amon.city_tower(9.0, 13.0)


def street_length():
    d = (STREET_B - STREET_A).normalized()
    reach = (Vector(et.THEATRE) - STREET_A).dot(d)
    return reach - 27.0


def street_frame(t, n=0.0):
    d = (STREET_B - STREET_A).normalized()
    normal = Vector((-d.y, d.x))
    return STREET_A + d * t + normal * n, math.atan2(d.y, d.x)


def build_harbour_city(scene):
    tframe = Matrix.Translation((et.THEATRE[0], et.THEATRE[1], et.THEATRE_LEVEL)) @ Matrix.Rotation(
        et.THEATRE_AXIS - math.pi / 2, 4, "Z")
    builder, frames = city.theatre()
    scene.unique("city_monuments", builder, tframe)
    scene.add_columns("ionic_lite", [tframe @ f for f in frames])
    scene.block(et.THEATRE[0], et.THEATRE[1], 88.0)
    scene.footprints.append((et.THEATRE[0], et.THEATRE[1], 75.0, 60.0, et.THEATRE_AXIS, 0.6))
    length = (STREET_B - STREET_A).length
    total = street_length()
    count = int(round(total / 12.0))
    seg = total / count
    raw = []
    for k in range(count + 1):
        heights = []
        for dt in (-3.0, 0.0, 3.0):
            for n in (-6.5, 0.0, 6.5):
                q = street_frame(min(max(k * seg + dt, 0.0), total), n)[0]
                heights.append(scene.ground(q.x, q.y))
        raw.append(max(heights) - 0.08)
    joints = []
    for k in range(count + 1):
        window = raw[max(k - 1, 0):k + 2]
        joints.append(max(sum(window) / len(window), raw[k]))
    for k in range(count):
        point, angle = street_frame((k + 0.5) * seg)
        rise = joints[k + 1] - joints[k]
        z = (joints[k] + joints[k + 1]) / 2
        scene.unique("streets", city.street(math.hypot(seg, rise) + 0.4, 11.0),
                     Matrix.Translation((point.x, point.y, z)) @ Matrix.Rotation(angle, 4, "Z")
                     @ Matrix.Rotation(-math.atan2(rise, seg), 4, "Y"))
        if k * seg > (STREET_B - STREET_A).length:
            scene.block(point.x, point.y, 16.0)
    point, angle = street_frame(-6.0)
    scene.unique("city_monuments", city.harbour_gate(), frame_at(scene, point.x, point.y, angle + math.pi / 2,
                                                                 lift=-0.3))
    for t, n, w, d, seed in ((340.0, 95.0, 160.0, 110.0, 3), (140.0, 110.0, 120.0, 90.0, 4)):
        point, angle = street_frame(t, n)
        frame = frame_at(scene, point.x, point.y, angle, lift=-0.2)
        if seed == 3:
            scene.unique("city_monuments", city.bath_complex(w, d, seed), frame)
        else:
            scene.unique("city_monuments", city.palaestra(w, d), frame)
        scene.block(point.x, point.y, max(w, d) * 0.62)
        scene.footprints.append((point.x, point.y, w / 2, d / 2, angle, 0.5))
    point, angle = street_frame(560.0, -80.0)
    frame = frame_at(scene, point.x, point.y, angle, lift=-0.2)
    scene.unique("city_monuments", city.palaestra(100.0, 90.0, 6.5), frame)
    scene.block(point.x, point.y, 70.0)
    scene.footprints.append((point.x, point.y, 50.0, 45.0, angle, 0.5))
    vf = frame_at(scene, VEDIUS.x, VEDIUS.y, 0.0, lift=-0.2)
    scene.unique("city_monuments", city.vedius_gymnasium(), vf)
    scene.block(VEDIUS.x, VEDIUS.y, 95.0)
    scene.footprints.append((VEDIUS.x, VEDIUS.y, 72.0, 75.0, 0.0, 0.5))
    sf = Matrix.Translation((STADIUM.x, STADIUM.y, 2.6))
    scene.unique("city_monuments", city.stadium(), sf)
    scene.block(STADIUM.x, STADIUM.y, 130.0)
    scene.footprints.append((STADIUM.x, STADIUM.y, 125.0, 40.0, 0.0, 0.5))
    temples = [(-1900.0, -1390.0, 0.6, 0), (-2160.0, -1180.0, 0.3, 1), (-1640.0, -1560.0, 2.2, 2)]
    for x, y, angle, seed in temples:
        building, frames = city.small_temple(16.0 + seed * 2.0, 28.0, seed)
        frame = frame_at(scene, x, y, angle, z=max(scene.ground(x + dx, y + dy) for dx in (-15, 15)
                                                   for dy in (-15, 15)) - 0.2)
        terrace = MeshBuilder()
        city.painted(terrace, (0.92, 0.86, 0.74), lambda: terrace.box((-24.0, -30.0, -12.0), (24.0, 30.0, 0.1),
                                                                      city.STONE, bottom=False))
        scene.unique("city_monuments", terrace, frame)
        scene.unique("city_monuments", building, frame)
        scene.add_columns("unit_ionic", [frame @ f for f in frames])
        scene.block(x, y, 36.0)
        scene.footprints.append((x, y, 24.0, 30.0, angle, 0.5))
    agora_point, angle = street_frame(length + 30.0, -140.0)
    af = frame_at(scene, agora_point.x, agora_point.y, angle, lift=-0.2)
    scene.unique("city_monuments", city.palaestra(110.0, 110.0, 7.5), af)
    scene.block(agora_point.x, agora_point.y, 78.0)
    scene.footprints.append((agora_point.x, agora_point.y, 55.0, 55.0, angle, 0.5))


def chunk_ok(scene, x, y, angle, hw, hd):
    if not scene.free(x, y, max(hw, hd) * 0.8):
        return None
    c, s = math.cos(angle), math.sin(angle)
    heights = []
    for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd), (0.0, 0.0)):
        px = x + u * c - v * s
        py = y + u * s + v * c
        if not (point_in_polygon(px, py, LOWER_CITY) or point_in_polygon(px, py, UPPER_CITY)):
            return None
        if scene.ground(px, py) < 0.6:
            return None
        heights.append(scene.ground(px, py))
    if max(heights) - min(heights) > 7.5:
        return None
    if point_in_polygon(x, y, et.basin_polygon(60.0)):
        return None
    return max(heights) - 0.3


def build_city(scene):
    rng = random.Random(41)
    d = (STREET_B - STREET_A).normalized()
    angle = math.atan2(d.y, d.x)
    normal = Vector((-d.y, d.x))
    width, depth, lane = 46.0, 38.0, 8.0
    detailed = {k: [] for k in range(5)}
    simple = {k: [] for k in range(5)}
    small = {k: [] for k in range(4)}
    for i in range(-14, 40):
        for j in range(-26, 12):
            t = i * (width + lane)
            n = j * (depth + lane) + depth / 2 + 8.0 if j >= 0 else j * (depth + lane) - depth / 2 + depth + lane - 8.0
            p = STREET_A + d * t + normal * n
            if abs(n) < depth / 2 + 7.0:
                continue
            z = chunk_ok(scene, p.x, p.y, angle, width / 2, depth / 2)
            if z is None:
                for k2 in range(2):
                    for k3 in range(2):
                        q = p + d * ((k2 - 0.5) * (width / 2 + lane / 2)) + normal * ((k3 - 0.5) * (depth / 2 + 4.0))
                        z2 = chunk_ok(scene, q.x, q.y, angle, width / 4 - 1.0, depth / 4 - 1.0)
                        if z2 is not None and rng.random() < 0.85:
                            small[rng.randrange(4)].append(Matrix.Translation((q.x, q.y, z2)) @ Matrix.Rotation(
                                angle + rng.choice((0.0, math.pi)), 4, "Z"))
                            scene.footprints.append((q.x, q.y, width / 4, depth / 4, angle, 0.55))
                            scene.chunks.append(Vector((q.x, q.y, z2)))
                continue
            facing = 0.0 if n > 0 else math.pi
            near = (p - Vector((-2700.0, -760.0))).length < 520.0 or (p - Vector((-2000.0, -1000.0))).length < 260.0
            variant = rng.randrange(5)
            frame = Matrix.Translation((p.x, p.y, z)) @ Matrix.Rotation(angle + facing, 4, "Z")
            (detailed if near else simple)[variant].append(frame)
            scene.footprints.append((p.x, p.y, width / 2, depth / 2, angle, 0.55))
            scene.chunks.append(Vector((p.x, p.y, z)))
    for variant in range(5):
        scene.instances("city", f"chunk_{variant}", lambda v=variant: city.terrace_chunk(300 + v, True, width, depth),
                        detailed[variant])
        scene.instances("city", f"chunk_far_{variant}", lambda v=variant: city.terrace_chunk(300 + v, False, width,
                                                                                            depth),
                        simple[variant], cast_shadow=False)
    for variant in range(4):
        scene.instances("city", f"chunk_small_{variant}", lambda v=variant: city.terrace_chunk(
            320 + v, False, width / 2 - 2.0, depth / 2 - 2.0, plinth=9.0), small[variant], cast_shadow=False)
    return {"detailed": sum(len(v) for v in detailed.values()), "simple": sum(len(v) for v in simple.values()),
            "small": sum(len(v) for v in small.values())}


def build_harbour(scene):
    basin = et.basin_polygon()
    ring = amon.oriented_ring([tuple(p) for p in basin], False)
    scene.unique("harbour", amon.quay(ring))
    scene.unique("harbour", amon.apron(ring, 26.0, et.QUAY_TOP - 0.035))
    rng = random.Random(23)
    stalls = []
    for point in path_offset([tuple(p) for p in resample([Vector(p) for p in ring], 34.0)], 0.0)[1:-1]:
        if rng.random() < 0.3:
            continue
        inward = (Vector(et.BASIN_CENTRE) - point).normalized()
        q = point - inward * 16.0
        if scene.ground(q.x, q.y) < 1.0:
            continue
        stalls.append(Matrix.Translation((q.x, q.y, et.QUAY_TOP - 0.03)) @ Matrix.Rotation(
            math.atan2(inward.y, inward.x) - math.pi / 2, 4, "Z"))
    scene.instances("harbour", "awning", lambda: city.awning(1), stalls, cast_shadow=True)
    bollards = []
    for point in path_offset([tuple(p) for p in resample([Vector(p) for p in ring], 16.0)], 1.3)[1:-1]:
        bollards.append(Matrix.Translation((point.x, point.y, et.QUAY_TOP + 0.06)))
    scene.instances("harbour", "bollard", amon.bollard, bollards, cast_shadow=False)
    basin_angle = et.basin_frame()
    for corner in et.basin_polygon(13.0):
        pad = MeshBuilder()
        city.painted(pad, (1.0, 0.97, 0.9), lambda: pad.box((-13.0, -13.0, -2.0), (13.0, 13.0, et.QUAY_TOP - 0.03),
                                                            city.PAVING, bottom=False))
        scene.unique("harbour", pad, Matrix.Translation((corner[0], corner[1], 0.0)) @ Matrix.Rotation(basin_angle, 4,
                                                                                                    "Z"))
    channel = [Vector(p) for p in et.CHANNEL]
    for side, width in ((1, 14.0), (-1, 9.0)):
        line = path_offset([tuple(p) for p in channel], side * 27.0)
        stop = len(line) if side > 0 else 3
        for a, b in zip(line[:stop - 1], line[1:stop]):
            dvec = b - a
            frame = Matrix.Translation((a.x, a.y, 0.0)) @ Matrix.Rotation(math.atan2(dvec.y, dvec.x) - math.pi / 2, 4,
                                                                         "Z")
            scene.unique("harbour", amon.mole(dvec.length + 2.0, width, et.QUAY_TOP), frame)
    angle = et.basin_frame()
    bx, by = et.BASIN_CENTRE
    for k, (u, v, turn) in enumerate(((-60.0, 162.0, 0.0), (40.0, 162.0, 0.0), (140.0, 165.0, 0.0),
                                      (-60.0, -162.0, math.pi), (40.0, -162.0, math.pi), (140.0, -160.0, math.pi))):
        c, s = math.cos(angle), math.sin(angle)
        x = bx + u * c - v * s
        y = by + u * s + v * c
        frame = Matrix.Translation((x, y, et.QUAY_TOP - 0.1)) @ Matrix.Rotation(angle + turn, 4, "Z")
        scene.unique("harbour", amon.warehouse(70.0, 18.0, 8.5 + k % 2, k), frame)
        scene.block(x, y, 40.0)
        scene.footprints.append((x, y, 35.0, 9.0, angle, 0.5))
    scene.quay_ring = ring


SHIP_BUILDS = {
    "merchant_brailed": lambda: ships.merchant(1, "brailed"),
    "merchant_brailed_b": lambda: ships.merchant(4, "brailed", 18.0, 5.6),
    "merchant_set": lambda: ships.merchant(2, "set"),
    "carrier_furled": lambda: ships.grain_carrier(3, "furled"),
    "carrier_set": lambda: ships.grain_carrier(6, "set", 32.0, 9.0),
    "galley": lambda: ships.galley(7),
    "lighter": lambda: ships.lighter(9),
    "fishing": lambda: ships.fishing_boat(10),
    "fishing_sail": lambda: ships.fishing_boat(11, sail=True),
}


def build_ships(scene):
    rng = random.Random(97)
    spots = []

    def add(key, x, y, heading, depth=1.6, gap=30.0):
        if scene.ground(x, y) > -depth:
            return False
        if any((Vector((x, y)) - Vector(o[1])).length < gap for o in spots):
            return False
        spots.append((key, (x, y), heading))
        return True

    angle = et.basin_frame()
    c, s = math.cos(angle), math.sin(angle)
    bx, by = et.BASIN_CENTRE
    berths = [(-120.0, 95.0), (-40.0, 98.0), (40.0, 96.0), (120.0, 92.0), (-110.0, -95.0), (-20.0, -97.0),
              (70.0, -95.0), (0.0, 20.0), (-70.0, -30.0), (100.0, 10.0)]
    keys = ["merchant_brailed", "carrier_furled", "merchant_brailed_b", "merchant_brailed", "carrier_furled",
            "merchant_brailed_b", "merchant_brailed", "lighter", "lighter", "galley"]
    for (u, v), key in zip(berths, keys):
        x = bx + u * c - v * s
        y = by + u * s + v * c
        heading = angle - math.pi / 2 + (0.0 if abs(v) > 50 else rng.uniform(0, 6.28))
        add(key, x, y, heading if abs(v) <= 50 else heading + (0.0 if v > 0 else math.pi))
    moored = ["merchant_brailed", "merchant_brailed_b", "carrier_furled", "merchant_brailed", "merchant_brailed_b",
              "lighter", "merchant_brailed", "carrier_furled", "merchant_brailed_b", "lighter", "merchant_brailed",
              "merchant_brailed_b"]
    for k, key in enumerate(moored):
        side = 1 if k % 2 == 0 else -1
        u = -155.0 + (k // 2) * 52.0 + (12.0 if side < 0 else 0.0)
        v = side * (96.0 if key != "lighter" else 104.0)
        x = bx + u * c - v * s
        y = by + u * s + v * c
        add(key, x, y, angle + (math.pi if side > 0 else 0.0), gap=14.0)
    channel = resample([Vector(p) for p in et.CHANNEL], 30.0)
    for index, key in ((12, "merchant_set"), (40, "lighter"), (62, "galley"), (78, "merchant_brailed")):
        if index >= len(channel) - 1:
            continue
        a, b = channel[index], channel[index + 1]
        dvec = b - a
        add(key, a.x, a.y, math.atan2(dvec.y, dvec.x) - math.pi / 2 + (math.pi if index % 2 else 0.0))
    for k in range(40):
        if sum(1 for o in spots if o[0] in ("carrier_set", "merchant_set", "fishing_sail")) > 9:
            break
        x = rng.uniform(-7600.0, -5450.0)
        y = rng.uniform(-1800.0, 1600.0)
        add(rng.choice(["carrier_set", "merchant_set", "merchant_set", "fishing_sail"]), x, y,
            math.radians(rng.uniform(-110.0, -70.0)), 3.0)
    river = resample(et.RIVER_PATH, 120.0)
    for index in (6, 14, 21, 27):
        if index < len(river) - 1:
            a, b = river[index], river[index + 1]
            dvec = b - a
            add("fishing", a.x, a.y, math.atan2(dvec.y, dvec.x) - math.pi / 2, 0.8)
    for cx, cy, rx, ry, turn in et.MARSHES[:6]:
        add("fishing", cx + rng.uniform(-30, 30), cy + rng.uniform(-15, 15), rng.uniform(0, 6.28), 0.3)
    grouped = {}
    for key, (x, y), heading in spots:
        grouped.setdefault(key, []).append(Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(heading, 4, "Z"))
    for key, matrices in grouped.items():
        scene.instances("ships", f"ship_{key}", SHIP_BUILDS[key], matrices)
    return {key: len(v) for key, v in grouped.items()}


def build_countryside(scene):
    rng = random.Random(83)
    land = scene.land
    farms = []
    for k in range(400):
        if len(farms) >= 30:
            break
        x = rng.uniform(-4400.0, 1400.0)
        y = rng.uniform(-400.0, 2100.0) if rng.random() < 0.7 else rng.uniform(-2600.0, -400.0)
        if scene.ground(x, y) < 0.9 or float(land.masks["marsh"].sample(x, y)) < 2.2:
            continue
        if float(land.masks["river"].sample(x, y)) < 80.0 or float(land.relief.sample(x, y)) > 4.0:
            continue
        if not scene.free(x, y, 60.0) or point_in_polygon(x, y, CIRCUIT):
            continue
        x0, x1, y0, y1 = et.SANCTUARY
        if x0 - 60 < x < x1 + 60 and y0 - 60 < y < y1 + 60:
            continue
        farms.append((x, y))
        scene.block(x, y, 30.0)
    frames = {k: [] for k in range(3)}
    for index, (x, y) in enumerate(farms):
        z = min(scene.ground(x + dx, y + dy) for dx in (-9, 9) for dy in (-5, 15))
        frame = frame_at(scene, x, y, math.radians(17.0) + rng.choice((0.0, math.pi / 2)), z=z)
        frames[index % 3].append(frame)
        scene.footprints.append((x, y, 14.0, 14.0, math.radians(17.0), 0.35))
        scene.chunks.append(Vector((x, y, z)))
        for k in range(rng.randrange(8, 18)):
            u = rng.uniform(-50.0, 50.0)
            v = rng.uniform(18.0, 70.0) * rng.choice((-1, 1))
            px, py = x + u, y + v
            if scene.ground(px, py) > 0.8 and scene.free(px, py, 2.0):
                scene.add_trees("olive", [frame_at(scene, px, py, rng.uniform(0, 6.28))])
    for variant, matrices in frames.items():
        scene.instances("countryside", f"farm_{variant}", lambda v=variant: city.farmstead(v), matrices)
    for points, spacing, kind in ((et.SACRED_WAY, 28.0, "plane"), (et.NORTH_ROAD, 30.0, "plane")):
        for p in path_offset([tuple(q) for q in resample([Vector(q) for q in points], spacing)], 13.0)[2:-3]:
            if rng.random() < 0.55 and scene.free(p.x, p.y, 3.0):
                scene.add_trees(kind if rng.random() < 0.7 else "cypress", [frame_at(scene, p.x, p.y,
                                                                                     rng.uniform(0, 6.28))])
    for p in resample(et.RIVER_PATH, 26.0):
        for side in (-1, 1):
            if rng.random() < 0.5:
                continue
            q = p + Vector((rng.uniform(-6, 6), side * rng.uniform(32.0, 46.0)))
            if scene.ground(q.x, q.y) > 0.3:
                scene.add_trees("poplar", [frame_at(scene, q.x, q.y, rng.uniform(0, 6.28))])
    hills = []
    for k in range(4500):
        x = rng.uniform(NEAR[0] + 50.0, NEAR[2] - 50.0)
        y = rng.uniform(NEAR[1] + 50.0, NEAR[3] - 50.0)
        relief = float(land.relief.sample(x, y))
        h = scene.ground(x, y)
        if relief < 9.0 or h < 6.0:
            continue
        if point_in_polygon(x, y, UPPER_CITY) or point_in_polygon(x, y, LOWER_CITY) or not scene.free(x, y, 10.0):
            continue
        hills.append((x, y, h))
    for x, y, h in hills:
        roll = rng.random()
        matrix = frame_at(scene, x, y, rng.uniform(0, 6.28)) @ Matrix.Scale(rng.uniform(0.8, 1.2), 4)
        if roll < 0.32:
            scene.add_trees("pine", [matrix])
        elif roll < 0.78:
            scene.add_trees("maquis", [matrix])
        elif roll < 0.9:
            scene.add_trees("olive", [matrix])
    reeds = []
    for k in range(5000):
        x = rng.uniform(-4800.0, 1300.0)
        y = rng.uniform(-1200.0, 2200.0)
        marsh = float(land.masks["marsh"].sample(x, y))
        river = float(land.masks["river"].sample(x, y))
        h = scene.ground(x, y)
        if not ((0.85 < marsh < 1.35 and -0.5 < h < 0.6) or (20.0 < river < 34.0 and -0.4 < h < 0.8)):
            continue
        reeds.append(Matrix.Translation((x, y, max(h, -0.2))) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z"))
    for cx, cy, rx, ry, turn in et.MARSHES[-2:]:
        for k in range(900):
            x = cx + rng.uniform(-1.6, 1.6) * rx
            y = cy + rng.uniform(-1.6, 1.6) * ry
            marsh = float(land.masks["marsh"].sample(x, y))
            h = scene.ground(x, y)
            if 0.8 < marsh < 1.5 and -0.5 < h < 0.9:
                reeds.insert(0, Matrix.Translation((x, y, max(h, -0.2))) @ Matrix.Rotation(rng.uniform(0, 6.28), 4,
                                                                                            "Z"))
    scene.instances("countryside", "reed_bed", lambda: city.reed_bed(3, 5), reeds[:1100], cast_shadow=False)
    tombs = {k: [] for k in range(3)}
    heroa = []
    for points in (et.SACRED_WAY[:12], et.NORTH_ROAD[:6]):
        dense = resample([Vector(q) for q in points], 22.0)
        for side in (-1, 1):
            for p in path_offset([tuple(q) for q in dense], side * rng.uniform(15.0, 18.0))[1:-1]:
                if rng.random() < 0.45 or not scene.free(p.x, p.y, 4.0):
                    continue
                if point_in_polygon(p.x, p.y, UPPER_CITY) or point_in_polygon(p.x, p.y, LOWER_CITY):
                    continue
                matrix = frame_at(scene, p.x, p.y, rng.uniform(-0.2, 0.2) + (0.0 if side > 0 else math.pi))
                if rng.random() < 0.12:
                    heroa.append(matrix)
                else:
                    tombs[rng.randrange(3)].append(matrix)
                if rng.random() < 0.3:
                    scene.add_trees("cypress", [frame_at(scene, p.x + rng.uniform(-5, 5), p.y + rng.uniform(-5, 5),
                                                         0.0)])
    for variant, matrices in tombs.items():
        scene.instances("countryside", f"tomb_{variant}", lambda v=variant: city.tomb(v), matrices, cast_shadow=False)
    scene.instances("countryside", "heroon", city.heroon, heroa)
    village = []
    for k in range(200):
        if len(village) >= 22:
            break
        x = rng.uniform(150.0, 700.0)
        y = rng.uniform(150.0, 700.0)
        h = scene.ground(x, y)
        heights = [scene.ground(x + dx, y + dy) for dx in (-9, 9) for dy in (-7, 7)]
        if max(heights) - min(heights) > 5.0 or not scene.free(x, y, 16.0):
            continue
        scene.block(x, y, 12.0)
        village.append(Matrix.Translation((x, y, max(heights) - 0.3)) @ Matrix.Rotation(rng.uniform(-0.3, 0.3) + 0.3,
                                                                                         4, "Z"))
        scene.footprints.append((x, y, 11.0, 9.0, 0.3, 0.45))
        scene.chunks.append(Vector((x, y, h)))
    scene.instances("countryside", "village_house", lambda: city.terrace_chunk(910, False, 20.0, 16.0, plinth=6.0),
                    village, cast_shadow=False)
    huts = []
    for cx, cy, rx, ry, turn in et.MARSHES:
        x = cx + rx * 1.4
        y = cy
        if scene.ground(x, y) > 0.4 and scene.free(x, y, 10.0):
            huts.append(frame_at(scene, x, y, turn))
    scene.instances("countryside", "fishing_hut", city.fishing_hut, huts)
    return {"farms": len(farms), "hills": len(hills), "reeds": min(len(reeds), 1100), "village": len(village)}


TREE_BUILDS = {
    "olive_close": [lambda: flora.close_olive(3)],
    "pine_close": [lambda: flora.close_pine(5)],
    "plane_close": [lambda: flora.close_plane(6)],
    "cypress": [lambda: city.cypress(11.0, 1), lambda: city.cypress(14.0, 2)],
    "plane": [lambda: city.plane(1), lambda: city.plane(2)],
    "olive": [lambda: city.olive(1), lambda: city.olive(2)],
    "poplar": [lambda: city.poplar(1)],
    "pine": [lambda: city.pine(11.0, 1), lambda: city.pine(9.0, 2)],
    "maquis": [lambda: city.maquis(1), lambda: city.maquis(2)],
}


def close_to_views(point):
    return any(math.hypot(point.x - cx, point.y - cy) < radius for (cx, cy), radius in CLOSE_ZONES)


def place_trees(scene):
    counts = {}
    for kind in ("olive", "pine", "plane"):
        matrices = scene.trees.get(kind, [])
        near = [m for m in matrices if close_to_views(m.translation)]
        scene.trees[kind] = [m for m in matrices if not close_to_views(m.translation)]
        scene.trees[f"{kind}_close"] = near
    for kind, matrices in scene.trees.items():
        builds = TREE_BUILDS[kind]
        buckets = [[] for _ in builds]
        for index, matrix in enumerate(matrices):
            buckets[index % len(builds)].append(matrix)
        for index, (build, bucket) in enumerate(zip(builds, buckets)):
            scene.instances("vegetation", f"{kind}_{index}", build, bucket,
                            cast_shadow=kind not in ("maquis",))
        counts[kind] = len(matrices)
    return counts


COLUMN_BUILDS = {
    "ionic_full": lambda: art.ionic_column(),
    "ionic_lite": lambda: lite_column(),
    "ionic_mid": lambda: art.ionic_mid(),
    "unit_ionic": lambda: amon.unit_column("ionic")(),
}


def lite_column():
    builder = MeshBuilder()
    d = art.D
    art.painted(builder, art.WHITE, lambda: builder.box((-0.68 * d, -0.68 * d, 0.0), (0.68 * d, 0.68 * d, 0.2 * d),
                                                       art.MARBLE, bottom=False))
    art.painted(builder, art.WHITE, lambda: builder.lathe([(0.6 * d, 0.2 * d), (0.62 * d, 0.38 * d), (0.5 * d, 0.5 * d),
                                                           (0.5 * d, art.H * 0.6), (0.43 * d, art.H - 0.6 * d),
                                                           (0.56 * d, art.H - 0.4 * d)], 10, art.MARBLE, caps=False))
    art.painted(builder, art.WHITE, lambda: builder.box((-0.75 * d, -0.5 * d, art.H - 0.45 * d),
                                                       (0.75 * d, 0.5 * d, art.H - 0.15 * d), art.MARBLE))
    art.painted(builder, art.WHITE, lambda: builder.box((-0.6 * d, -0.6 * d, art.H - 0.15 * d),
                                                       (0.6 * d, 0.6 * d, art.H), art.MARBLE))
    return builder


def place_columns(scene):
    counts = {}
    for kind, frames in scene.columns.items():
        scene.instances("columns", kind, COLUMN_BUILDS[kind], frames)
        counts[kind] = len(frames)
    return counts


def footprint_mask(scene):
    items = np.array(scene.footprints, dtype=np.float64)

    def mask(gx, gy):
        result = np.zeros(gx.shape)
        for cx, cy, half_x, half_y, angle, strength in items:
            if strength <= 0.0:
                continue
            c, s = math.cos(angle), math.sin(angle)
            reach = max(half_x, half_y) * 1.5 + 12.0
            rows = np.where(np.abs(gy[:, 0] - cy) < reach)[0]
            columns = np.where(np.abs(gx[0, :] - cx) < reach)[0]
            if len(rows) == 0 or len(columns) == 0:
                continue
            sub_x = gx[np.ix_(rows, columns)] - cx
            sub_y = gy[np.ix_(rows, columns)] - cy
            u = np.abs(sub_x * c + sub_y * s) - half_x
            v = np.abs(-sub_x * s + sub_y * c) - half_y
            outside = np.hypot(np.maximum(u, 0.0), np.maximum(v, 0.0))
            value = strength * np.clip(1.0 - outside / 8.0, 0.0, 1.0)
            block = result[np.ix_(rows, columns)]
            result[np.ix_(rows, columns)] = np.maximum(block, value)
        city_zone = np.zeros(gx.shape)
        for polygon in (LOWER_CITY, UPPER_CITY):
            city_zone = np.maximum(city_zone, et.polygon_mask(polygon, gx, gy) * 0.35)
        return np.maximum(result, city_zone)
    return mask


def bake(scene, name, rect, resolution, far=False, mask=None):
    x0, y0, x1, y1 = rect
    ax = x0 + (np.arange(resolution) + 0.5) * (x1 - x0) / resolution
    ay = y0 + (np.arange(resolution) + 0.5) * (y1 - y0) / resolution
    gx, gy = np.meshgrid(ax, ay)
    if far:
        colour = et.colour_far(scene.land, gx, gy)
    else:
        colour = et.colour_near(scene.land, gx, gy, mask, town=lambda x, y: et.polygon_mask(CIRCUIT, x, y) * 1.0)
    image = save_pixels(name, colour, os.path.join(CACHE, "textures", f"{name}.jpg"), quality=90)
    return baked_material(name, image)


def lowered(sample, rect, amount):
    x0, y0, x1, y1 = rect

    def inner(gx, gy):
        heights = sample(gx, gy)
        inside = (gx > x0 + 0.5) & (gx < x1 - 0.5) & (gy > y0 + 0.5) & (gy < y1 - 0.5)
        return heights - inside * amount
    return inner


def shrink(rect, margin):
    return (rect[0] + margin, rect[1] + margin, rect[2] - margin, rect[3] - margin)


def build_terrain(scene):
    land = scene.land
    root = scene.root("terrain")
    mask = footprint_mask(scene)
    near = land.near.sample
    pieces = [
        ("terrain_core", CORE, 8.0, near, None, CORE, 2048),
        ("terrain_west", (INNER[0], INNER[1], SPLIT_X, INNER[3]), 16.0, lowered(near, CORE, 0.4),
         [shrink(CORE, 16.0)], (INNER[0], INNER[1], SPLIT_X, INNER[3]), 2048),
        ("terrain_east", (SPLIT_X, INNER[1], INNER[2], INNER[3]), 16.0, lowered(near, CORE, 0.4),
         [shrink(CORE, 16.0)], (SPLIT_X, INNER[1], INNER[2], INNER[3]), 2048),
        ("terrain_mid", NEAR, 32.0, lowered(near, INNER, 0.6), [shrink(INNER, 32.0)], NEAR, 2048),
    ]
    stats = {}
    for name, rect, spacing, sample, hole, uv, resolution in pieces:
        material = bake(scene, name, uv, resolution, mask=mask)
        mesh = et.sampled_grid(name, sample, *rect, spacing, hole=hole, skirt=6.0 if hole is None else 0.0,
                               uv_rect=uv)
        mesh.materials.append(material)
        created = new_object(name, mesh, scene.collection, root)
        created["cast_shadow"] = False
        stats[name] = len(mesh.polygons)
    material = bake(scene, "terrain_far", FAR, 1024, far=True)
    far_sample = lowered(lambda gx, gy: land.far.sample(gx, gy), NEAR, 1.5)
    mesh = et.sampled_grid("terrain_far", far_sample, *FAR, et.FAR_SPACING, hole=[shrink(NEAR, et.FAR_SPACING)],
                           skirt=0.0, uv_rect=FAR)
    mesh.materials.append(material)
    created = new_object("terrain_far", mesh, scene.collection, root)
    created["cast_shadow"] = False
    stats["terrain_far"] = len(mesh.polygons)
    horizon(scene, root)
    return stats


def horizon(scene, root):
    dem = scene.dem_sample
    reach = 90000.0
    step = 3000.0
    builder_v = []
    faces = []
    colours = []
    axis = np.arange(-reach, reach + 1.0, step)
    gx, gy = np.meshgrid(axis, axis)
    inside_crop = (np.abs(gx) < 16000.0) & (np.abs(gy) < 16000.0)
    raw = dem(gx, gy)
    sea = ((gx < -9000.0) & (raw < 1.0)) | ((gx < -40000.0) & (np.abs(gy) < 80000.0) & (gx < -20000.0 - gy * 0.1))
    heights = np.where(sea, -30.0, np.maximum(raw, 8.0) * 0.9)
    heights = np.where(inside_crop, -40.0, heights)
    rows, columns = gx.shape
    for j in range(rows):
        for i in range(columns):
            builder_v.append((gx[j, i], gy[j, i], heights[j, i]))
            colours.append((0.12, 0.30, 0.42) if sea[j, i] else (0.46, 0.50, 0.34))
    for j in range(rows - 1):
        for i in range(columns - 1):
            cx = (gx[j, i] + gx[j, i + 1]) / 2
            cy = (gy[j, i] + gy[j + 1, i]) / 2
            if abs(cx) < 15000.0 and abs(cy) < 15000.0:
                continue
            a = j * columns + i
            faces.append((a, a + 1, a + columns + 1, a + columns))
    mesh = bpy.data.meshes.new("terrain_horizon_far")
    mesh.from_pydata(builder_v, [], faces)
    material = principled_material("terrain_horizon_far", (1.0, 1.0, 1.0), 0.95)
    mesh.materials.append(material)
    attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    rgba = np.column_stack([np.array(colours), np.ones(len(colours))])[loops]
    attribute.data.foreach_set("color_srgb", rgba.astype(np.float32).ravel())
    mesh.color_attributes.active_color = attribute
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", (np.array(builder_v)[loops][:, :2] / 3000.0).astype(np.float32).ravel())
    mesh.update()
    created = new_object("terrain_horizon_far", mesh, scene.collection, root)
    created["cast_shadow"] = False


def water_colour(scene):
    land = scene.land

    def colour(x, y, depth):
        river = land.masks["river"].sample(np.clip(x, NEAR[0], NEAR[2]), np.clip(y, NEAR[1], NEAR[3]))
        marsh = land.masks["marsh"].sample(np.clip(x, NEAR[0], NEAR[2]), np.clip(y, NEAR[1], NEAR[3]))
        inside = (x > NEAR[0]) & (x < NEAR[2]) & (y > NEAR[1]) & (y < NEAR[3])
        deep = np.array([0.05, 0.22, 0.42])
        shallow = np.array([0.12, 0.42, 0.52])
        green = np.array([0.24, 0.40, 0.34])
        t = np.clip(-depth / 6.0, 0.0, 1.0)[:, None]
        rgb = shallow * (1 - t) + deep * t
        fresh = (inside & ((river < 40.0) | (marsh < 1.4)))[:, None]
        return np.where(fresh, green, rgb)
    return colour


def build_water(scene):
    root = scene.root("water")
    colour = water_colour(scene)
    near = et.water_grid("water_near", scene.land.near.sample, *NEAR, 16.0, colour=colour)
    far = et.water_grid("water_far", lambda gx, gy: scene.land.far.sample(gx, gy), *FAR, 160.0, hole=NEAR,
                        colour=colour)
    for mesh in (near, far):
        mesh.materials.append(bpy.data.materials["water"])
        created = new_object(mesh.name, mesh, scene.collection, root)
        created["cast_shadow"] = False
    ring = MeshBuilder()
    inner = et.FAR_HALF
    outer = 90000.0
    for y0, y1 in ((-outer, outer),):
        quad = [(-outer, y0, -0.02), (-inner, y0, -0.02), (-inner, y1, -0.02), (-outer, y1, -0.02)]
        ring.oriented(quad, (0, 0, 1), "water")
        ring.tint(len(ring.polygons) - 1, (0.05, 0.28, 0.48))
    unique_object("water_horizon", ring, scene.collection, root, scene.tiles, cast_shadow=False,
                  ground_occlusion=False)
    return {"near": len(near.polygons), "far": len(far.polygons)}


def road_height(scene, point):
    z = scene.surface.height(point.x, point.y) if scene.surface is not None else None
    return scene.ground(point.x, point.y) if z is None else z


def build_roads(scene):
    terrain = [item for item in scene.roots["terrain"].children if item.type == "MESH"
               and not item.name.startswith(("terrain_far", "terrain_horizon"))]
    probe = Surface(terrain)
    counts = {}
    for name, width, limit in (("sacred", 8.0, GATE.x - 6.0), ("north", 7.0, GATE.x - 6.0)):
        dense, levels = scene.land.roads[name]
        points = [Vector((p[0], p[1], level)) for p, level in zip(dense, levels) if p[0] < limit]
        points = resample(points, 6.0)
        rows = []
        kerbs = []
        for index, point in enumerate(points):
            a = points[max(index - 1, 0)]
            b = points[min(index + 1, len(points) - 1)]
            direction = (b - a).to_2d().normalized()
            right = Vector((direction.y, -direction.x))
            row = []
            for offset in (-0.5, -0.25, 0.0, 0.25, 0.5):
                q = point.to_2d() + right * offset * width
                ground = probe.height(q.x, q.y)
                z = max(point.z, ground if ground is not None else point.z) + 0.12
                row.append((q.x, q.y, z))
            rows.append(row)
            kerbs.append((point.to_2d(), right, row))
        paved = 16
        builder = MeshBuilder()
        builder.surface(rows[paved - 1:], "ground_gravel", smooth=True, facing=(0, 0, 1))
        builder.tint(0, (1.0, 0.98, 0.94))
        first = len(builder.polygons)
        builder.surface(rows[:paved], "paving", smooth=True, facing=(0, 0, 1))
        builder.tint(first, (0.96, 0.93, 0.86))
        for sign in (-1.0, 1.0):
            top = []
            face = []
            for centre, right, row in kerbs[:paved]:
                edge = Vector(row[0] if sign < 0 else row[-1])
                outer = edge.to_2d() + right * sign * 0.6
                top.append([(edge.x, edge.y, edge.z + 0.18), (outer.x, outer.y, edge.z + 0.18)])
                face.append([(edge.x, edge.y, edge.z - 0.02), (edge.x, edge.y, edge.z + 0.18)])
            first = len(builder.polygons)
            builder.surface(top, "paving", facing=(0, 0, 1))
            builder.surface(face, "paving")
            builder.tint(first, (0.90, 0.87, 0.80))
        created = unique_object(f"road_{name}", builder, scene.collection, scene.root("roads"), scene.tiles,
                                cast_shadow=False, ground_occlusion=False)
        created["cast_shadow"] = False
        counts[name] = len(rows)
    return counts


def build_surface(scene):
    objects = []
    for name in WALKABLE:
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in [root] + list(root.children_recursive):
            if item.type != "MESH" or item.name.startswith(("terrain_far", "terrain_mid", "terrain_horizon")):
                continue
            if item.name.startswith(("bollard", "awning")) or item.name.startswith("group_"):
                continue
            objects.append(item)
    scene.surface = Surface(objects)


def add_route(scene, name, points, below=None):
    root = scene.root("life")
    chain = []
    for point in resample([Vector((p[0], p[1], 0.0)) for p in points], 2.5):
        z = scene.surface.height(point.x, point.y, below)
        if z is None:
            continue
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        previous = refined[-1]
        middle = (previous + following) / 2
        z = scene.surface.height(middle.x, middle.y, below)
        if z is not None and abs(z - (previous.z + following.z) / 2) > 0.04:
            refined.append(Vector((middle.x, middle.y, z)))
        refined.append(following)
    for index, point in enumerate(refined):
        new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(point))
    scene.routes[name] = refined
    scene.route_samples.extend(point.to_2d() for point in resample(refined, 1.0))
    return len(refined)


def route_report(scene):
    report = {}
    for name, points in scene.routes.items():
        worst = 0.0
        longest = 0.0
        where = None
        for a, b in zip(points[:-1], points[1:]):
            if abs(b.z - a.z) > worst:
                where = [round(a.x, 1), round(a.y, 1), round(a.z, 2), round(b.z, 2)]
            worst = max(worst, abs(b.z - a.z))
            longest = max(longest, (b - a).length)
        report[name] = {"points": len(points), "max_step": round(worst, 2), "worst_at": where,
                        "max_spacing": round(longest, 2),
                        "z_range": [round(min(p.z for p in points), 2), round(max(p.z for p in points), 2)]}
    return report


def build_routes(scene):
    counts = {}
    loop = [(GATE.x + 8.0, GATE.y - 3.0), (-150.0, GATE.y - 3.0), (-140.0, -48.0), (-80.0, -52.0), (65.0, -52.0),
            (72.0, -11.0), (65.0, 30.0), (-80.0, 31.0), (-140.0, 28.0), (-150.0, GATE.y + 3.0),
            (GATE.x + 10.0, GATE.y + 3.0)]
    counts["sanctuaire"] = add_route(scene, "sanctuaire", loop, below=GROUND + 3.0)
    dense, levels = scene.land.roads["sacred"]
    way = path_offset(dense, 2.0)
    way = [p for p in way if not (p.x > GATE.x - 3.0)]
    way.append(Vector((GATE.x - 4.0, GATE.y - 2.0)))
    counts["voie"] = add_route(scene, "voie", [(p.x, p.y) for p in way[3:]])
    dense, levels = scene.land.roads["north"]
    north = [p for p in path_offset(dense, -2.0) if p.x < GATE.x - 6.0]
    counts["nord"] = add_route(scene, "nord", [(p.x, p.y) for p in north[2:]])
    grown = et.basin_polygon(9.0)
    quay = [grown[3], grown[2], grown[1]]
    counts["quai"] = add_route(scene, "quai", quay, below=et.QUAY_TOP + 3.0)
    length = street_length()
    street = [street_frame(t, 2.5)[0] for t in np.arange(10.0, length - 6.0, 20.0)]
    counts["rue"] = add_route(scene, "rue", [(p.x, p.y) for p in street])
    return counts


def clear_of_routes(scene, x, y, radius):
    point = Vector((x, y))
    return all((point - sample).length > radius for sample in scene.route_samples[::2])


def populate(scene, eyes):
    rng = random.Random(131)
    placed = {}

    def put(key, x, y, heading, below=None, radius=1.4, check=True, level=None):
        if check and not clear_of_routes(scene, x, y, radius):
            return False
        if min((Vector((x, y)) - eye).length for eye in eyes) < 9.0:
            return False
        z = scene.surface.height(x, y, below) if level is None else level
        if z is None:
            return False
        placed.setdefault(key, []).append(Matrix.Translation((x, y, z)) @ Matrix.Rotation(heading, 4, "Z"))
        return True

    sanctuary_keys = ["pilgrims", "pilgrims_b", "pilgrims_c", "family", "conversation", "conversation_b",
                      "conversation_c", "fig_greek", "fig_greek_b", "fig_lady", "fig_lady_b", "fig_toga", "fig_toga_b",
                      "fig_child", "offering", "reader", "fig_priestess", "fig_ephebe"]
    for k in range(110):
        x = rng.uniform(-255.0, 70.0)
        y = rng.uniform(-75.0, 55.0)
        if -68.0 < x < 68.0 and -47.0 < y < 25.0:
            continue
        if -134.0 < x < -88.0 and -33.0 < y < 11.0:
            continue
        key = rng.choice(sanctuary_keys)
        put(key, x, y, rng.uniform(0, 6.28), GROUND + 3.0, 2.2 if key.startswith(("pil", "fam", "off", "conv")) else 1.2)
    for k in range(26):
        x = rng.uniform(-262.0, 160.0)
        y = rng.uniform(-150.0, 150.0)
        if abs(y - GATE.y) < 70.0 and x < 80.0:
            continue
        put(rng.choice(sanctuary_keys), x, y, rng.uniform(0, 6.28), GROUND + 3.0, 2.0)
    for x, y, key in ((-252.0, 20.0, "vendor"), (-238.0, -40.0, "vendor_b"), (-226.0, 26.0, "vendor_b"),
                      (-212.0, -38.0, "vendor"), (-300.0, -40.0, "vendor"), (-318.0, 12.0, "vendor_b")):
        put(key, x, y, math.pi / 2 if y > GATE.y else -math.pi / 2, None, 3.0)
    put("procession", -84.0, GATE.y + 0.5, math.pi / 2, GROUND + 3.0, 0.0, check=False)
    start = Vector(et.SACRED_WAY[1])
    along = (start - MAGNESIAN).normalized()
    right = Vector((along.y, -along.x))
    heading = math.atan2(along.y, along.x) + math.pi / 2
    for distance, offset, key, turn in ((30.0, 0.0, "procession", math.pi), (16.0, 4.6, "pilgrims", math.pi),
                                        (44.0, -4.4, "donkey_driver", 0.0), (68.0, 3.8, "ox_cart", math.pi),
                                        (12.0, -4.8, "family", 0.0), (38.0, -5.2, "pilgrims_c", 0.0),
                                        (24.0, -5.5, "conversation_c", 0.0), (56.0, -3.0, "fig_toga", math.pi)):
        p = MAGNESIAN + along * distance + right * offset
        put(key, p.x, p.y, heading + turn, None, 0.0, check=False)
    put("proconsul", -205.0, GATE.y + 6.0, -math.pi / 2, GROUND + 3.0, 0.0, check=False)
    af = altar_frame()
    for local, heading, key in (((0.0, 9.0), math.pi, "sacrifice"), ((-9.0, 12.0), 0.3, "pilgrims_b"),
                                ((9.0, 13.0), -0.4, "conversation_c"), ((-11.0, 4.0), 1.2, "fig_priestess"),
                                ((10.0, 3.0), -1.0, "fig_ephebe")):
        p = af @ Vector((local[0], local[1], 0.0))
        put(key, p.x, p.y, heading + math.pi / 2, None, 0.0, check=False, level=scene.altar_floor + 0.03)
    dense, levels = scene.land.roads["sacred"]
    way_keys = ["pilgrims", "pilgrims_b", "pilgrims_c", "donkey_driver", "ox_cart", "family", "fig_greek",
                "fig_lady", "fig_docker", "conversation_c", "fig_toga"]
    for k in range(70):
        index = rng.randrange(4, len(dense) - 4)
        a, b = Vector(dense[index]), Vector(dense[index + 1])
        dvec = (b - a).normalized()
        side = rng.choice((-1, 1))
        p = a + Vector((dvec.y, -dvec.x)) * side * rng.uniform(4.0, 7.0)
        if p.x > GATE.x - 6.0:
            continue
        put(rng.choice(way_keys), p.x, p.y, math.atan2(dvec.y, dvec.x) - math.pi / 2 + (0.0 if rng.random() < 0.5
                                                                                        else math.pi), None, 2.0)
    dense, levels = scene.land.roads["north"]
    for k in range(30):
        index = rng.randrange(3, len(dense) - 3)
        a, b = Vector(dense[index]), Vector(dense[index + 1])
        dvec = (b - a).normalized()
        p = a + Vector((dvec.y, -dvec.x)) * rng.choice((-1, 1)) * rng.uniform(4.0, 7.0)
        if p.x > GATE.x - 6.0:
            continue
        put(rng.choice(way_keys), p.x, p.y, math.atan2(dvec.y, dvec.x) - math.pi / 2, None, 2.0)
    quay_keys = ["dock_gang", "dock_gang", "scale_table", "conversation", "amphora_stack", "amphora_stack",
                 "fig_docker", "fig_sack", "fig_greek", "fig_lady", "fisher_pair", "porters_line", "sack_pile",
                 "fig_toga"]
    for point in resample([Vector(p) for p in scene.quay_ring], 7.0):
        if rng.random() < 0.55:
            continue
        inward = Vector(et.BASIN_CENTRE) - point
        inward.normalize()
        q = point - inward * rng.uniform(4.0, 20.0)
        key = rng.choice(quay_keys)
        put(key, q.x, q.y, rng.uniform(0, 6.28), et.QUAY_TOP + 2.0, 2.6 if "gang" in key or "table" in key else 1.3)
    length = street_length()
    for k in range(70):
        point, angle = street_frame(rng.uniform(15.0, length - 15.0), rng.choice((-1, 1)) * rng.uniform(1.0, 5.0))
        put(rng.choice(["fig_greek", "fig_lady", "fig_toga", "conversation_c", "fig_docker", "donkey_driver",
                        "fig_lady_b", "fig_greek_b", "family"]), point.x, point.y, angle + rng.choice((0.0, math.pi))
            - math.pi / 2, None, 1.4)
    for k in range(18):
        x = rng.uniform(-3500.0, 1200.0)
        y = rng.uniform(-300.0, 2000.0)
        if scene.ground(x, y) < 1.0 or not scene.free(x, y, 30.0):
            continue
        if float(scene.land.masks["marsh"].sample(x, y)) < 2.0 or float(scene.land.relief.sample(x, y)) > 4.0:
            continue
        put(rng.choice(["ploughman", "shepherd", "ploughman"]), x, y, rng.uniform(0, 6.28), None, 4.0)
    counts = {}
    for key, matrices in placed.items():
        scene.instances("life", key, elife.LIFE[key], matrices,
                        cast_shadow=key not in ("amphora_stack", "sack_pile", "ploughman", "shepherd"))
        counts[key] = len(matrices)
    return counts


def place_effects(scene):
    root = scene.root("life")
    rng = random.Random(7)
    smokes = [scene.altar_smoke + Vector((0.0, 0.0, 0.6))]
    candidates = list(scene.chunks)
    rng.shuffle(candidates)
    for point in candidates:
        if len(smokes) >= 9:
            break
        if any((point.to_2d() - q.to_2d()).length < 300.0 for q in smokes):
            continue
        smokes.append(Vector((point.x, point.y, point.z + 13.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [((-1500.0, 600.0), 40.0), ((0.0, -11.0), 70.0), ((-2900.0, -640.0), 45.0), ((-800.0, 1600.0), 35.0),
              ((-3600.0, 300.0), 30.0), ((-2300.0, -1600.0), 260.0)]
    for index, ((x, y), height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation((x, y, scene.ground(x, y) + height)))
    for index, (key, build) in enumerate(elife.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke": len(smokes), "birds": len(flocks), "walkers": len(elife.WALKERS)}


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
                ground = np.array([scene.ground(x, y) for x, y in co[:, :2]]) if len(co) < 400000 else co[:, 2]
                heights = co[:, 2] - ground
                world_z = co[:, 2]
            foliage = name in ("vegetation", "countryside", "sanctuary")
            aweather.weather(mesh, heights, world_z, seed, foliage)
            if name in ("city", "city_monuments", "harbour", "artemision", "altar", "sanctuary", "streets",
                        "countryside") and len(mesh.vertices) < 80000:
                nimes_detail.occlusion(mesh, seed)


def viewpoints(scene):
    points = {}
    points["vue-d-ensemble"] = (Vector((520.0, -360.0, 260.0)), Vector((-446.0, -101.0, 55.0)))
    tf = temple_frame()
    points["l-artemision"] = (Vector((-175.0, -26.0, GROUND + 14.0)), Vector((-40.0, -11.0, GROUND + 11.0)))
    eye = tf @ Vector((0.0, -14.0, art.Z0 + 1.7))
    target = tf @ Vector((0.0, art.STATUE_Y + 1.2, art.Z0 + 4.5))
    points["la-statue-d-artemis"] = (eye, target)
    bx, by = et.BASIN_CENTRE
    points["le-port"] = (Vector((bx - 240.0, by + 70.0, 58.0)), Vector((et.THEATRE[0], et.THEATRE[1], 14.0)))
    start = Vector(et.SACRED_WAY[1])
    along = (start - MAGNESIAN).normalized()
    right = Vector((along.y, -along.x))
    eye2 = MAGNESIAN + along * 52.0 + right * 8.0
    aim = MAGNESIAN + along * 27.0
    points["la-voie-sacree"] = (Vector((eye2.x, eye2.y, road_height(scene, eye2) + 1.7)),
                                Vector((aim.x, aim.y, road_height(scene, aim) + 2.0)))
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
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.7, aerosol=0.28)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 3.2, (1.0, 0.90, 0.76), 0.6)
    configure_render(1280, 720, options["samples"], exposure=-0.1)
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
        rig = camera(stage, f"cam_{name}", eye, target, lens=LENSES.get(name, LENS), clip_end=150000.0)
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
    dem = et.load_dem(CACHE)
    land = et.Landscape(dem)
    print("FIELDS", round(time.perf_counter() - started, 1), flush=True)
    scene = Scene(tiles, land)
    scene.dem_sample = et.dem_sampler(dem)
    build_sanctuary(scene)
    build_walls(scene)
    build_harbour_city(scene)
    build_harbour(scene)
    chunk_counts = build_city(scene)
    countryside = build_countryside(scene)
    print("CITY", chunk_counts, countryside, round(time.perf_counter() - started, 1), flush=True)
    ship_counts = build_ships(scene)
    tree_counts = place_trees(scene)
    column_counts = place_columns(scene)
    scene.flush()
    terrain_stats = build_terrain(scene)
    water_stats = build_water(scene)
    road_counts = build_roads(scene)
    print("TERRAIN", terrain_stats, water_stats, road_counts, round(time.perf_counter() - started, 1), flush=True)
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
    glb = os.path.join(CACHE, "ephese.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION],
        "counts": {"chunks": chunk_counts, "countryside": countryside, "ships": ship_counts, "trees": tree_counts,
                   "columns": column_counts, "routes": route_counts, "life": life_counts, "effects": effects},
        "route_checks": route_report(scene), "terrain": terrain_stats, "water": water_stats,
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "meshes": {key: len(mesh.polygons) for key, mesh in scene.library.meshes.items()},
        "build_seconds": round(time.perf_counter() - started, 1), "terrain_source": et.SOURCE,
        "terrain_licence": et.DEM_LICENCE, "texture_credits": credits,
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

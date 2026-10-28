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
from kit import nimes_detail
from kit import olympie_life as olife
from kit import rhodes_city as city
from kit import rhodes_colossus as colossus
from kit import rhodes_life as life
from kit import rhodes_monuments as mon
from kit import rhodes_plan as plan
from kit import rhodes_terrain as rterrain
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, save_pixels
from kit.rhodes_materials import build_library, remap
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, haze_volume,
                       render_still, sun_lamp)
from kit.terrain import point_in_polygon

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "rhodes")
BLEND = os.path.join(CACHE, "work", "rhodes.blend")
SUN_AZIMUTH = 104.0
SUN_ELEVATION = 25.0
NEAR_TILES = (-1900.0, -2100.0, 1750.0, 2, 10.0, 2048)
MID_TILE = (-9000.0, -9000.0, 18000.0, 90.0, 1024)
FAR_TILE = (-34000.0, -34000.0, 68000.0, 800.0, 512)
LENS = 30.0
WALKABLE = ("terrain", "sanctuary", "acropolis", "quays", "avenue", "stadium")
DETAIL_ZONES = [((-1250.0, -900.0), (-700.0, -250.0)), ((-950.0, -560.0), (900.0, -340.0)),
                ((60.0, -320.0), (1400.0, 950.0))]


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
        self.collection = ensure_collection("Rhodes")
        self.roots = {}
        self.pending = {}
        self.columns = {}
        self.footprints = []
        self.blocked = []
        self.routes = {}
        self.route_samples = []
        self.chunks = []
        self.marks = {}
        self.surface = None
        self.vegetation = {}
        self.statues = {}
        self.avenue = (-930.0, 860.0)
        self.solid = []
        self.avenue_props = []

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.terrain.height(x, y))

    def unique(self, group, builder, matrix=None):
        self.pending.setdefault(group, []).append((builder, matrix if matrix is not None else Matrix.Identity(4)))
        self.root(group)

    def flush(self):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(remap(builder), matrix, keep_local=True)
            unique_object(f"{group}_static.{len(self.roots[group].children):02d}", merged, self.collection,
                          self.root(group), self.tiles)
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True):
        if not matrices:
            return None
        return self.library.place(key, lambda: remap(build()), self.collection, self.root(group), matrices,
                                  cast_shadow, False)

    def column(self, key, matrix):
        self.columns.setdefault(key, []).append(matrix)

    def plant(self, key, matrix):
        self.vegetation.setdefault(key, []).append(matrix)

    def footprint(self, x, y, hx, hy, angle=0.0, strength=0.35):
        self.footprints.append((x, y, hx, hy, angle, strength))
        self.blocked.append((x, y, hx, hy, angle))

    def free(self, x, y, margin=0.0):
        for cx, cy, hx, hy, angle in self.blocked:
            c, s = math.cos(angle), math.sin(angle)
            u = (x - cx) * c + (y - cy) * s
            v = -(x - cx) * s + (y - cy) * c
            if abs(u) < hx + margin and abs(v) < hy + margin:
                return False
        return True


def frame(x, y, z, angle=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle, 4, "Z")


def add_columns(scene, base, columns, z=0.0):
    for key, x, y in columns:
        scene.column(key, base @ Matrix.Translation((x, y, z)))


def statue_kinds():
    return [lambda: olife.bronze_statue("draped", 3, 1.5, 1.1, "bronze"),
            lambda: olife.bronze_statue("roman", 4, 1.6, 1.1, "bronze"),
            lambda: olife.bronze_statue("athlete", 5, 1.4, 1.1, "bronze"),
            lambda: olife.bronze_statue("draped", 6, 1.5, 1.05, "marble")]


def build_sanctuary(scene):
    level = plan.SANCTUARY["level"]
    cx, cy = plan.SANCTUARY["centre"]
    hx, hy = plan.SANCTUARY["half"]
    scene.unique("sanctuary", mon.terrace(hx, hy, 14.0, 1.0, 1.8, gaps=(("east", -610.0 - cy, 5.0),)),
                 frame(cx, cy, level))
    scene.footprint(cx, cy, hx + 2.0, hy + 2.0, 0.0, 0.15)
    stair_z = level
    stair_x = cx + hx + 1.8
    run = 16.0
    for _ in range(4):
        drop = max(stair_z - scene.ground(stair_x + run, -610.0) - 0.2, 1.0)
        run = max(16.0, drop / 0.6)
    scene.unique("sanctuary", mon.stair(9.0, drop, run, max(int(drop / 0.24), 1), (1.0, 0.88, 0.70)),
                 frame(stair_x, -610.0, stair_z, -math.pi / 2))
    scene.footprint(stair_x + run / 2, -610.0, run / 2, 6.0, 0.0, 0.2)
    t = plan.TEMPLE
    builder, columns, built, apex = mon.pythion()
    base = frame(t.x, t.y, level + 3 * 0.36 + 0.06)
    scene.unique("sanctuary", builder, base)
    add_columns(scene, base, columns)
    scene.blocked.append((t.x, t.y, built.length / 2 + 2.0, built.width / 2 + 2.0, 0.0))
    scene.unique("sanctuary", mon.altar(), frame(t.x + 30.0, t.y, level, math.pi / 2))
    scene.blocked.append((t.x + 30.0, t.y, 4.0, 7.0, 0.0))
    scene.solid.append((t.x + 30.0, t.y, 5.2, 8.2, 0.0))
    scene.solid.append((t.x, t.y, built.length / 2 + 2.0, built.width / 2 + 2.0, 0.0))
    stoa_builder, stoa_columns = mon.stoa_building(96.0, 10.0, 5.3, 3.0, mon.OCHRE)
    stoa_frame = frame(cx - hx + 6.0, cy, level + 0.62, -math.pi / 2)
    scene.unique("sanctuary", stoa_builder, stoa_frame)
    add_columns(scene, stoa_frame, stoa_columns)
    scene.blocked.append((cx - hx + 6.0, cy, 6.0, 49.0, 0.0))
    stoa_builder, stoa_columns = mon.stoa_building(70.0, 9.0, 5.3, 3.0, (1.0, 0.9, 0.7))
    stoa_frame = frame(cx + 4.0, cy + hy - 5.5, level + 0.62, math.pi)
    scene.unique("sanctuary", stoa_builder, stoa_frame)
    add_columns(scene, stoa_frame, stoa_columns)
    scene.blocked.append((cx + 4.0, cy + hy - 5.5, 36.0, 6.0, 0.0))
    gate_builder, gate_columns = mon.propylon(14.0, 8.0, 6.6)
    gate_frame = frame(cx + hx - 4.0, -610.0, level, math.pi / 2)
    scene.unique("sanctuary", gate_builder, gate_frame)
    add_columns(scene, gate_frame, gate_columns, 0.4)
    c = plan.COLOSSUS
    statue_frame = frame(c.x, c.y, level, plan.COLOSSUS_FALL)
    parts, marks = colossus.colossus()
    for name, part in parts.items():
        scene.unique("colossus" if name != "debris" else "colossus_debris", part, statue_frame)
    scene.marks = {key: statue_frame @ value for key, value in marks.items()}
    scene.marks["frame"] = statue_frame
    assert 0.9 < scene.marks["thumb"].z - level < 1.5, scene.marks["thumb"]
    scene.blocked.append((c.x + 17.0, c.y, 26.0, 16.0, plan.COLOSSUS_FALL))
    rng = random.Random(17)
    weeds = []
    for k in range(70):
        edge = rng.uniform(-9.4, 9.4)
        side = rng.choice((-1, 1))
        u, v = (edge, side * rng.uniform(9.0, 9.8)) if rng.random() < 0.5 else (side * rng.uniform(9.0, 9.8), edge)
        weeds.append((u, v))
    for k in range(60):
        weeds.append((rng.uniform(10.0, 40.0), rng.choice((-1, 1)) * rng.uniform(4.5, 9.0)))
    for u, v in weeds:
        if 2.0 < u < 18.0 and -16.0 < v < -6.0:
            continue
        p = statue_frame @ Vector((u, v, 0.0))
        scene.plant("weed", frame(p.x, p.y, level + 0.04, rng.uniform(0, 6.28)) @ Matrix.Scale(rng.uniform(0.6, 1.3), 4))
    statues = statue_kinds()
    spots = [(t.x + 22.0, t.y + 13.0, math.pi / 2), (t.x + 22.0, t.y - 13.0, math.pi / 2),
             (t.x + 38.0, t.y + 18.0, math.pi), (t.x + 38.0, t.y - 18.0, 0.0), (c.x - 6.0, c.y + 18.0, -math.pi / 2),
             (c.x + 2.0, c.y + 19.0, -math.pi / 2), (cx + 30.0, cy + hy - 16.0, -math.pi / 2),
             (cx + 18.0, cy + hy - 16.0, -math.pi / 2)]
    for index, (x, y, angle) in enumerate(spots):
        scene.statues.setdefault(index % len(statues), []).append(frame(x, y, level, angle))
        scene.solid.append((x, y, 2.4, 2.4, 0.0))
        scene.blocked.append((x, y, 1.2, 1.2, 0.0))
    bases = [frame(t.x + 50.0, t.y + 22.0, level, math.pi / 2), frame(cx - 30.0, cy + hy - 18.0, level, 0.0)]
    scene.instances("sanctuary", "honorific_bases", lambda: mon.honorific_bases(5, 3), bases)
    rng = random.Random(19)
    tour = sanctuary_tour(scene)
    for k in range(40):
        x = rng.uniform(cx - hx + 14.0, cx + hx - 4.0)
        y = rng.uniform(cy - hy + 4.0, cy + hy - 14.0)
        if not scene.free(x, y, 5.0) or near_polyline(tour, x, y, 5.0):
            continue
        if rng.random() < 0.6:
            scene.plant("cypress", frame(x, y, level, rng.uniform(0, 6.28)))
        else:
            scene.plant("olive", frame(x, y, level, rng.uniform(0, 6.28)))
        scene.blocked.append((x, y, 2.0, 2.0, 0.0))


def build_athena(scene):
    level = plan.ATHENA["level"]
    cx, cy = plan.ATHENA["centre"]
    hx, hy = plan.ATHENA["half"]
    scene.unique("acropolis", mon.terrace(hx, hy, 14.0, 1.0, 1.6), frame(cx, cy, level))
    builder, columns, built, apex = mon.athena()
    base = frame(cx, cy, level + 3 * 0.36 + 0.06)
    scene.unique("acropolis", builder, base)
    add_columns(scene, base, columns)
    scene.footprint(cx, cy, hx + 2.0, hy + 2.0, 0.0, 0.15)
    scene.unique("acropolis", mon.altar(7.0, 3.6, 1.6), frame(cx + hx - 6.0, cy, level, math.pi / 2))


def build_stadium(scene):
    y0, y1 = plan.STADIUM_Y
    scene.unique("stadium", mon.stadium(), frame(plan.STADIUM_AXIS_X, y1, plan.STADIUM_LEVEL))
    scene.footprint(plan.STADIUM_AXIS_X, (y0 + y1) / 2, 28.0, 112.0, 0.0, 0.2)
    rng = random.Random(23)
    blocks = []
    for k in range(10):
        side = rng.choice((-1, 1))
        row = rng.randrange(1, 10)
        x = plan.STADIUM_AXIS_X + side * (plan.STADIUM_HALF + (row + 0.5) * plan.STADIUM_ROW[0])
        y = rng.uniform(y0 + 20.0, y1 - 10.0)
        blocks.append(frame(x, y, plan.STADIUM_LEVEL + (row + 1) * plan.STADIUM_ROW[1],
                            side * math.pi / 2))
    scene.instances("life", "spectators", life.LIFE["spectators"], blocks)
    o = plan.ODEON
    scene.unique("stadium", mon.odeon(), frame(o["centre"][0], o["centre"][1], o["level"]))
    scene.footprint(o["centre"][0], o["centre"][1], o["radius"] + 2.0, o["radius"] + 2.0, 0.0, 0.2)


def harbour_ring(polygon):
    return amon.oriented_ring(list(polygon), False)


def land_runs(scene, ring):
    runs = []
    current = []
    for a, b in zip(ring[:-1], ring[1:]):
        a, b = Vector(a), Vector(b)
        middle = (a + b) / 2
        d = (b - a).normalized()
        probe = middle + Vector((d.y, -d.x)) * 6.0
        if scene.ground(probe.x, probe.y) > 0.4:
            if not current:
                current = [tuple(a)]
            current.append(tuple(b))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return runs


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


def build_harbours(scene):
    scene.quay_lines = []
    bollards = []
    for name, polygon in plan.HARBOURS.items():
        for line in land_runs(scene, harbour_ring(polygon)):
            scene.unique("quays", amon.quay(line))
            scene.unique("quays", amon.apron(line, 16.0, plan.QUAY_TOP + 0.065))
            scene.quay_lines.append((name, line))
            dense = resample([Vector((p[0], p[1])) for p in line], 16.0)
            for point in path_offset([tuple(p) for p in dense], 1.3)[1:-1]:
                bollards.append(Matrix.Translation((point.x, point.y, plan.QUAY_TOP + 0.07)))
    scene.instances("quays", "bollard", amon.bollard, bollards, cast_shadow=False)
    towers = []
    for name, spec in plan.MOLES.items():
        points = [Vector(p) for p in spec["points"]]
        for a, b in zip(points[:-1], points[1:]):
            d = b - a
            base = Matrix.Translation((a.x, a.y, 0.0)) @ Matrix.Rotation(math.atan2(d.y, d.x) - math.pi / 2, 4, "Z")
            scene.unique("quays", amon.mole(d.length, spec["width"], plan.QUAY_TOP + 0.3, -6.0), base)
        head = points[-1]
        d = points[-1] - points[-2]
        towers.append(frame(head.x, head.y, plan.QUAY_TOP + 0.3, math.atan2(d.y, d.x)))
    scene.instances("quays", "harbour_tower", mon.harbour_tower, towers)
    shed_frames = []
    hauled = []
    for k in range(5):
        y = 330.0 + k * 66.0
        x = scene_shore_x(scene, y, 150.0, 300.0) - 22.0
        shed = frame(x, y, plan.QUAY_TOP - 0.4, -math.pi / 2)
        shed_frames.append(shed)
        scene.footprint(x, y, 22.0, 31.0, 0.0, 0.4)
        for bay in ((1, 6), (3,), (2, 7), (5,), (4,))[k]:
            bx = -31.5 + (bay + 0.5) * 7.0
            slope = 2.7 / 46.0
            hauled.append(shed @ Matrix.Translation((bx, -2.0, -1.2 + 24.0 * slope + 0.9))
                          @ Matrix.Rotation(math.atan(slope), 4, "X"))
    scene.instances("harbour", "ship_sheds", lambda: mon.ship_shed_row(9, 7.0, 40.0, 6.5), shed_frames)
    scene.instances("harbour", "galley_hauled", SHIP_BUILDS["galley"], hauled)
    houses = []
    rng = random.Random(31)
    for name, line in scene.quay_lines:
        if name == "mandraki":
            continue
        dense = resample([Vector(p) for p in line], 56.0)
        for a, b in zip(dense[:-1], dense[1:]):
            d = b - a
            if d.length < 30.0:
                continue
            middle = (a + b) / 2
            normal = Vector((d.y, -d.x)).normalized()
            centre = middle + normal * 27.0
            if scene.ground(centre.x, centre.y) < 0.8 or not scene.free(centre.x, centre.y, 6.0):
                continue
            angle = math.atan2(d.y, d.x)
            houses.append((frame(centre.x, centre.y, scene.ground(centre.x, centre.y) + 0.05, angle + math.pi),
                           rng.randrange(4)))
            scene.footprint(centre.x, centre.y, 25.0, 8.5, angle, 0.45)
    for variant in range(4):
        scene.instances("harbour", f"warehouse_{variant}", lambda variant=variant: mon.warehouse(48.0, 15.0, 8.0,
                                                                                                  variant),
                        [f for f, v in houses if v == variant])


def scene_shore_x(scene, y, x0, x1):
    for x in np.arange(x1, x0, -2.0):
        if scene.ground(x, y) > 0.5:
            return float(x)
    return x0


def build_agora(scene):
    a = plan.AGORA
    cx, cy = a["centre"]
    hx, hy = a["half"]
    level = scene.ground(cx, cy)
    plaza = MeshBuilder()
    mon.painted(plaza, (1.0, 0.96, 0.88), lambda: plaza.box((-hx, -hy, -1.5), (hx, hy, 0.1), "paving", bottom=False))
    scene.unique("avenue", plaza, frame(cx, cy, level))
    for side, length, offset, angle in ((-1, 2 * hx, (0.0, -hy + 6.0), 0.0), (1, 2 * hx, (0.0, hy - 6.0), math.pi),
                                        (0, 2 * hy - 24.0, (-hx + 6.0, 0.0), -math.pi / 2)):
        builder, columns = mon.stoa_building(length, 10.0, 5.3, 3.0, mon.OCHRE if side else (1.0, 0.9, 0.72))
        base = frame(cx + offset[0], cy + offset[1], level + 0.6, angle)
        scene.unique("avenue", builder, base)
        add_columns(scene, base, columns)
    scene.footprint(cx, cy, hx + 2.0, hy + 2.0, 0.0, 0.3)
    for k in range(6):
        scene.statues.setdefault(k % 4, []).append(frame(cx - 50.0 + k * 20.0, cy + 8.0, level + 0.1, math.pi))
    gx, gy = plan.GYMNASIUM["centre"]
    level = scene.ground(gx, gy)
    builder, columns = mon.stoa_building(2 * plan.GYMNASIUM["half"][0], 12.0, 5.3, 3.2, (1.0, 0.92, 0.76))
    for offset, angle in (((0.0, -plan.GYMNASIUM["half"][1] + 7.0), 0.0), ((0.0, plan.GYMNASIUM["half"][1] - 7.0),
                                                                          math.pi)):
        base = frame(gx + offset[0], gy + offset[1], level + 0.6, angle)
        scene.unique("avenue", builder, base)
        add_columns(scene, base, columns)
    sand = MeshBuilder()
    mon.painted(sand, (0.95, 0.82, 0.58), lambda: sand.box((-58.0, -38.0, -1.5), (58.0, 38.0, 0.12), "matte",
                                                           bottom=False))
    scene.unique("avenue", sand, frame(gx, gy, level))
    scene.footprint(gx, gy, plan.GYMNASIUM["half"][0] + 2.0, plan.GYMNASIUM["half"][1] + 2.0, 0.0, 0.3)


def strip_z(scene, x):
    x0, x1 = scene.avenue
    xs = list(np.arange(x0, x1, 5.0)) + [x1]
    index = min(max(int((x - x0) // 5.0), 0), len(xs) - 2)
    xa, xb = xs[index], xs[index + 1]
    t = min(max((x - xa) / (xb - xa), 0.0), 1.0)
    return (scene.ground(xa, plan.AVENUE_Y) * (1 - t) + scene.ground(xb, plan.AVENUE_Y) * t) + 0.14


def avenue_strip(scene, x0, x1, y, width):
    builder = MeshBuilder()
    xs = list(np.arange(x0, x1, 5.0)) + [x1]
    half = width / 2
    for xa, xb in zip(xs[:-1], xs[1:]):
        za = scene.ground(xa, y) + 0.14
        zb = scene.ground(xb, y) + 0.14
        builder.oriented([(xa, y - half, za), (xb, y - half, zb), (xb, y + half, zb), (xa, y + half, za)], (0, 0, 1),
                         "paving")
        for side in (-1, 1):
            inner = y + side * half
            outer = y + side * (half + 0.7)
            builder.oriented([(xa, inner, za + 0.16), (xb, inner, zb + 0.16), (xb, outer, zb + 0.16),
                              (xa, outer, za + 0.16)], (0, 0, 1), "limestone")
            builder.oriented([(xa, inner, za - 0.05), (xb, inner, zb - 0.05), (xb, inner, zb + 0.16),
                              (xa, inner, za + 0.16)], (0, -side, 0), "limestone")
            builder.oriented([(xa, outer, za - 2.0), (xb, outer, zb - 2.0), (xb, outer, zb + 0.16),
                              (xa, outer, za + 0.16)], (0, side, 0), "limestone")
    builder.tint(0, (1.0, 0.95, 0.86))
    return builder


def build_avenue(scene):
    x0, x1 = scene.avenue
    y = plan.AVENUE_Y
    scene.unique("avenue", avenue_strip(scene, x0, x1, y, plan.AVENUE), Matrix.Identity(4))
    porticoes = []
    awnings = []
    rng = random.Random(43)
    lines = plan.street_lines_x()
    for xa, xb in zip(lines[:-1], lines[1:]):
        start = max(xa + plan.street_width_x(xa) / 2, x0)
        end = min(xb - plan.street_width_x(xb) / 2, x1)
        if end - start < 20.0:
            continue
        count = max(int(round((end - start) / 23.5)), 1)
        length = (end - start) / count
        public = {side: rng.random() < 0.3 or abs(xa - 50.0) < 1.0 for side in (-1, 1)}
        for k in range(count):
            x = start + length * (k + 0.5)
            if plan.in_site(x, y, 4.0):
                continue
            for side in (-1, 1):
                if not public[side]:
                    continue
                py = y + side * (plan.AVENUE / 2 + 1.2)
                pz = max(scene.ground(x - length / 2, py), scene.ground(x + length / 2, py), scene.ground(x, py)) + 0.05
                porticoes.append(frame(x, py, pz, 0.0 if side > 0 else math.pi) @ Matrix.Diagonal(
                    (length / 23.5, 1.0, 1.0, 1.0)))
                scene.blocked.append((x, py + side * 3.0, length / 2, 3.5, 0.0))
    scene.avenue_props = []
    for x in np.arange(x0 + 40.0, x1 - 20.0, 48.0):
        if plan.in_site(x, y, 6.0):
            continue
        side = rng.choice((-1, 1))
        py = y + side * (plan.AVENUE / 2 - 1.4)
        scene.statues.setdefault(rng.randrange(4), []).append(frame(x, py, strip_z(scene, x),
                                                                    math.pi if side > 0 else 0.0))
        scene.blocked.append((x, py, 1.2, 1.2, 0.0))
        scene.avenue_props.append((x, py, 1.0))
        scene.solid.append((x, py, 2.2, 2.2, 0.0))
    spots = list(np.arange(-300.0, 300.0, 24.0)) + [x for x in np.arange(x0 + 100.0, x1 - 100.0, 90.0)
                                                      if not -320.0 < x < 320.0 and rng.random() > 0.35]
    for index, x in enumerate(spots):
        if plan.in_site(x, y, 10.0) or not x0 < x - 2.0 < x + 15.0 < x1:
            continue
        side = 1 if index % 2 else -1
        py = y + side * (plan.AVENUE / 2 - 3.0)
        centre = x + 6.3 * side
        if any(abs(px - centre) < 9.6 and (py0 - y) * side > 0 for px, py0, half in scene.avenue_props):
            continue
        awnings.append(frame(x, py, strip_z(scene, centre), 0.0 if side > 0 else math.pi))
        scene.blocked.append((centre, py, 8.5, 2.0, 0.0))
        scene.avenue_props.append((centre, py - side * 0.2, 8.4))
        scene.solid.append((centre, py - side * 0.2, 8.4 + 1.2, 1.8 + 1.2, 0.0))
    scene.instances("avenue", "portico", lambda: city.portico(23.5), porticoes)
    for variant in range(2):
        scene.instances("avenue", f"awning_{variant}", lambda variant=variant: mon.awning_row(4, variant),
                        awnings[variant::2])


def in_detail_zone(x, y):
    return any(a[0] < x < b[0] and a[1] < y < b[1] for a, b in DETAIL_ZONES)


def chunk_allowed(scene, x, y, hx, hy, check_free=True):
    corners = [(x - hx, y - hy), (x + hx, y - hy), (x + hx, y + hy), (x - hx, y + hy), (x, y)]
    for cx, cy in corners:
        if not plan.built_mask(np.array(cx), np.array(cy)):
            return None
        if plan.is_harbour_water(cx, cy):
            return None
    heights = [scene.ground(cx, cy) for cx, cy in corners]
    if min(heights) < 1.2 or max(heights) - min(heights) > 4.5:
        return None
    if min(float(scene.terrain.sample("shore", cx, cy)) for cx, cy in corners) < 18.0:
        return None
    if plan.in_site(x, y, max(hx, hy) + 6.0):
        return None
    if check_free and not scene.free(x, y, max(hx, hy) - 4.0):
        return None
    return max(heights) - 0.3


AVENUE_CHUNK = (46.0, 32.0)


def build_city(scene):
    rng = random.Random(41)
    detailed = {k: [] for k in range(5)}
    avenue = {k: [] for k in range(3)}
    simple = {k: [] for k in range(3)}
    gardens = []
    xs = plan.street_lines_x()
    ys = plan.street_lines_y()
    x0, x1 = scene.avenue
    for xa, xb in zip(xs[:-1], xs[1:]):
        for ya, yb in zip(ys[:-1], ys[1:]):
            inner_x0 = xa + plan.street_width_x(xa) / 2
            inner_x1 = xb - plan.street_width_x(xb) / 2
            inner_y0 = ya + plan.street_width_y(ya) / 2
            inner_y1 = yb - plan.street_width_y(yb) / 2
            on_avenue = x0 - 20.0 < (inner_x0 + inner_x1) / 2 < x1 + 20.0 and plan.AVENUE_Y in (ya, yb)
            if on_avenue and ya == plan.AVENUE_Y:
                inner_y0 += 6.6
            elif on_avenue:
                inner_y1 -= 6.6
            width = inner_x1 - inner_x0
            count = max(int(round(width / city.CHUNK[0])), 1)
            size = AVENUE_CHUNK if on_avenue else city.CHUNK
            hx, hy = size[0] / 2, size[1] / 2
            for k in range(count):
                x = inner_x0 + width * (k + 0.5) / count
                y = (inner_y0 + inner_y1) / 2
                z = chunk_allowed(scene, x, y, hx, hy, not on_avenue)
                if z is None:
                    continue
                if not on_avenue and rng.random() < 0.05:
                    gardens.append((x, y, z))
                    continue
                if on_avenue:
                    turn = 0.0 if y > plan.AVENUE_Y else math.pi
                else:
                    turn = rng.choice((0.0, math.pi))
                matrix = frame(x, y, z + 0.05, turn)
                if on_avenue:
                    avenue[rng.randrange(3)].append(matrix)
                elif in_detail_zone(x, y):
                    detailed[rng.randrange(5)].append(matrix)
                else:
                    simple[rng.randrange(3)].append(matrix)
                scene.footprint(x, y, hx, hy, 0.0, 0.5)
                scene.chunks.append((x, y, z))
    for variant, frames in detailed.items():
        scene.instances("city", f"chunk_{variant}", lambda variant=variant: city.house_chunk(500 + variant, True),
                        frames)
    for variant, frames in avenue.items():
        scene.instances("city", f"chunk_avenue_{variant}",
                        lambda variant=variant: city.house_chunk(520 + variant, True, AVENUE_CHUNK[0],
                                                                 AVENUE_CHUNK[1]), frames)
    for variant, frames in simple.items():
        scene.instances("city", f"chunk_far_{variant}", lambda variant=variant: city.house_chunk(540 + variant, False),
                        frames, cast_shadow=False)
    for x, y, z in gardens:
        for k in range(rng.randrange(4, 9)):
            px = x + rng.uniform(-city.CHUNK[0] / 2 + 3.0, city.CHUNK[0] / 2 - 3.0)
            py = y + rng.uniform(-city.CHUNK[1] / 2 + 3.0, city.CHUNK[1] / 2 - 3.0)
            scene.plant(rng.choice(["olive", "olive", "cypress", "pine"]), frame(px, py, scene.ground(px, py),
                                                                              rng.uniform(0, 6.28)))
    return {"detailed": sum(len(v) for v in detailed.values()), "avenue": sum(len(v) for v in avenue.values()),
            "simple": sum(len(v) for v in simple.values()), "gardens": len(gardens)}


def build_walls(scene):
    segments = []
    towers = []
    points = [Vector((float(plan.west_wall_x(y)), y)) for y in np.arange(-1750.0, 640.0, 40.0)]
    points = [Vector((1330.0, -1750.0))] + [Vector((x, -1750.0)) for x in np.arange(1290.0, -1500.0, -40.0)] + points
    dense = resample(points, 40.0)
    distance = 0.0
    for a, b in zip(dense[:-1], dense[1:]):
        distance += (b - a).length
        middle = (a + b) / 2
        if scene.ground(middle.x, middle.y) < 1.5 or plan.is_harbour_water(middle.x, middle.y):
            continue
        if abs(middle.x - plan.AVENUE_X) < 12.0 and middle.y < -1700.0:
            continue
        d = b - a
        z = min(scene.ground(a.x, a.y), scene.ground(b.x, b.y), scene.ground(middle.x, middle.y))
        segments.append(Matrix.Translation((a.x, a.y, z)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
                        @ Matrix.Diagonal((d.length / 40.0, 1.0, 1.0, 1.0)))
        if int(distance / 40.0) % 3 == 0:
            towers.append(Matrix.Translation((a.x, a.y, z)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
    scene.instances("walls", "wall_segment", lambda: amon.city_wall_segment(40.0, 10.0, 4.2), segments,
                    cast_shadow=False)
    scene.instances("walls", "wall_tower", lambda: amon.city_tower(9.0, 15.0), towers, cast_shadow=False)
    gate_x = plan.AVENUE_X
    scene.instances("walls", "city_gate", amon.city_gate, [frame(gate_x, -1750.0, scene.ground(gate_x, -1750.0),
                                                                 0.0)], cast_shadow=False)
    return {"segments": len(segments), "towers": len(towers)}


def build_vegetation(scene):
    rng = random.Random(61)
    for k in range(5200):
        x = rng.uniform(-1800.0, 1500.0)
        y = rng.uniform(-2100.0, 1100.0)
        shore = float(scene.terrain.sample("shore", x, y))
        if shore < 12.0:
            continue
        inside_city = bool(plan.built_mask(np.array(x), np.array(y)))
        acropolis = bool(plan.acropolis_zone(np.array(x), np.array(y))) and x > float(plan.west_wall_x(y)) - 400.0
        if inside_city:
            continue
        if plan.in_site(x, y, 8.0) or not scene.free(x, y, 3.0):
            continue
        slope = float(scene.terrain.sample("slope", x, y))
        z = scene.terrain.lowest(x, y, 1.5)
        matrix = frame(x, y, z, rng.uniform(0, 6.28)) @ Matrix.Scale(rng.uniform(0.8, 1.2), 4)
        near = in_detail_zone(x, y) or acropolis or (abs(x + 1100.0) < 500.0 and abs(y + 600.0) < 500.0)
        roll = rng.random()
        if acropolis:
            key = "pine" if roll < 0.45 else ("cypress" if roll < 0.6 else ("olive" if roll < 0.8 else "shrub"))
        elif slope > 0.35:
            key = "pine" if roll < 0.6 else "shrub"
        else:
            key = "olive" if roll < 0.55 else ("pine" if roll < 0.7 else ("shrub" if roll < 0.92 else "cypress"))
        if not near:
            key = {"pine": "far_pine", "olive": "far_olive", "cypress": "far_cypress", "shrub": "shrub"}[key]
        scene.plant(key, matrix)
    for x, y, z in scene.chunks[::23]:
        scene.plant("cypress", frame(x + 18.0, y + 20.0, scene.ground(x + 18.0, y + 20.0), 0.0))


def cypress(height=14.0, seed=0):
    builder = olife.poplar(height, seed)
    builder.paint("matte", (0.48, 0.62, 0.48))
    return builder


VEGETATION = {
    "pine": lambda: olife.pine(13.0, 3),
    "olive": lambda: olife.olive_tree(6.0, 5),
    "cypress": lambda: cypress(15.0, 7),
    "shrub": lambda: olife.shrub(1.6, 9, (0.30, 0.42, 0.18)),
    "weed": lambda: olife.shrub(0.5, 21, (0.34, 0.38, 0.17)),
    "far_pine": lambda: olife.far_pine(12.0, 11),
    "far_olive": lambda: olife.far_olive(5.5, 13),
    "far_cypress": lambda: cypress(13.0, 15),
}


def place_vegetation(scene):
    counts = {}
    for key, matrices in scene.vegetation.items():
        shadow = key in ("pine", "olive", "cypress")
        scene.instances("vegetation", key, VEGETATION[key], matrices, cast_shadow=shadow)
        counts[key] = len(matrices)
    return counts


def place_statues(scene):
    kinds = statue_kinds()
    for key, matrices in scene.statues.items():
        scene.instances("statues", f"statue_{key}", kinds[key], matrices)
    return {key: len(v) for key, v in scene.statues.items()}


def place_columns(scene):
    counts = {}
    for key, matrices in scene.columns.items():
        scene.instances("columns", f"column_{key}", mon.COLUMN_BUILDS[key], matrices)
        counts[key] = len(matrices)
    return counts


SHIP_BUILDS = {
    "merchant_brailed": lambda: ships.merchant(21, "brailed"),
    "merchant_brailed_b": lambda: ships.merchant(24, "brailed", 18.0, 5.6),
    "merchant_set": lambda: ships.merchant(22, "set"),
    "carrier_furled": lambda: ships.grain_carrier(23, "furled", 30.0, 8.6),
    "carrier_set": lambda: ships.grain_carrier(26, "set", 30.0, 8.6),
    "galley": lambda: ships.galley(27, 30.0, 4.6),
    "lighter": lambda: ships.lighter(29),
    "fishing": lambda: ships.fishing_boat(30),
    "fishing_sail": lambda: ships.fishing_boat(31, sail=True),
}


def build_ships(scene):
    rng = random.Random(97)
    spots = []

    def add(key, x, y, heading, clearance=16.0):
        if scene.ground(x, y) > -2.0 or float(scene.terrain.sample("shore", x, y)) > -clearance:
            return False
        for _, (ox, oy), _ in spots:
            if math.hypot(ox - x, oy - y) < 30.0:
                return False
        spots.append((key, (x, y), heading))
        return True

    for name, line in scene.quay_lines:
        dense = resample([Vector(p) for p in line], 42.0)
        for a, b in zip(dense[:-1], dense[1:]):
            if rng.random() < 0.3:
                continue
            d = (b - a)
            if d.length < 20.0:
                continue
            normal = Vector((-d.y, d.x)).normalized()
            middle = (a + b) / 2 + normal * 7.0
            if name == "mandraki":
                key = rng.choice(["fishing", "lighter", "fishing_sail", "merchant_brailed"])
            else:
                key = rng.choice(["merchant_brailed", "merchant_brailed_b", "carrier_furled", "lighter",
                                  "merchant_brailed"])
            add(key, middle.x, middle.y, math.atan2(d.y, d.x) + rng.choice((0.0, math.pi)), 4.0)
    for name, polygon, count in (("mandraki", plan.MANDRAKI, 6), ("inner", plan.INNER_PORT, 4),
                                 ("great", plan.GREAT_PORT, 10)):
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        placed = 0
        for k in range(300):
            if placed >= count:
                break
            x = rng.uniform(min(xs), max(xs))
            y = rng.uniform(min(ys), max(ys))
            if not point_in_polygon(x, y, polygon):
                continue
            key = rng.choice(["fishing", "lighter", "fishing"] if name == "mandraki" else
                             ["merchant_brailed", "carrier_furled", "merchant_brailed_b", "lighter", "fishing"])
            placed += add(key, x, y, rng.uniform(0, 6.28), 18.0)
    for key, x, y, heading in (("carrier_set", 1500.0, 900.0, 200.0), ("merchant_set", 900.0, 1400.0, 215.0),
                               ("merchant_set", 2100.0, 300.0, 250.0), ("fishing_sail", 700.0, 1100.0, 120.0),
                               ("carrier_set", 2600.0, 1700.0, 225.0), ("fishing_sail", -300.0, 1500.0, 80.0),
                               ("merchant_brailed", 1200.0, 600.0, 180.0), ("galley", 290.0, 560.0, 165.0),
                               ("fishing_sail", -1700.0, 0.0, 10.0)):
        add(key, x, y, math.radians(heading), 30.0)
    grouped = {}
    for key, (x, y), heading in spots:
        grouped.setdefault(key, []).append(Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(heading, 4, "Z"))
    for key, matrices in grouped.items():
        scene.instances("ships", f"ship_{key}", SHIP_BUILDS[key], matrices)
    return {key: len(v) for key, v in grouped.items()}


def near_tiles():
    x0, y0, size, count, spacing, resolution = NEAR_TILES
    for i in range(count):
        for j in range(count):
            yield f"{i}{j}", x0 + i * size, y0 + j * size, size


def footprint_mask(scene):
    items = np.array(scene.footprints, dtype=np.float64)

    def mask(gx, gy):
        result = np.zeros(gx.shape)
        for cx, cy, half_x, half_y, angle, strength in items:
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
            value = strength * np.clip(1.0 - outside / 5.0, 0.0, 1.0)
            block = result[np.ix_(rows, columns)]
            result[np.ix_(rows, columns)] = np.maximum(block, value)
        return result
    return mask if len(items) else None


def build_terrain(scene):
    terrain = scene.terrain
    root = scene.root("terrain")
    textures = os.path.join(CACHE, "textures")
    footprints = footprint_mask(scene)
    x0, y0, size, count, spacing, resolution = NEAR_TILES
    for key, tx, ty, tsize in near_tiles():
        colour = rterrain.bake_tile(terrain, tx, ty, tsize, resolution, footprints)
        image = save_pixels(f"terrain_{key}", colour, os.path.join(textures, f"terrain_{key}.jpg"), quality=88)
        mesh = rterrain.grid_tile(f"terrain_{key}", terrain, tx, ty, tsize, spacing)
        mesh.materials.append(baked_material(f"terrain_{key}", image))
        new_object(f"terrain_{key}", mesh, scene.collection, root)["cast_shadow"] = False
    hole = (x0, y0, x0 + size * count, y0 + size * count)
    mx, my, msize, mspacing, mres = MID_TILE
    colour = rterrain.bake_tile(terrain, mx, my, msize, mres, None)
    image = save_pixels("terrain_mid", colour, os.path.join(textures, "terrain_mid.jpg"), quality=86)
    mesh = rterrain.grid_tile("terrain_mid", terrain, mx, my, msize, mspacing, hole, -40.0)
    mesh.materials.append(baked_material("terrain_mid", image))
    new_object("terrain_mid", mesh, scene.collection, root)["cast_shadow"] = False
    fx, fy, fsize, fspacing, fres = FAR_TILE
    colour = rterrain.bake_tile(terrain, fx, fy, fsize, fres, None)
    image = save_pixels("terrain_far", colour, os.path.join(textures, "terrain_far.jpg"), quality=84)
    mesh = rterrain.grid_tile("terrain_far", terrain, fx, fy, fsize, fspacing, (mx, my, mx + msize, my + msize), -60.0)
    mesh.materials.append(baked_material("terrain_far", image))
    new_object("terrain_far", mesh, scene.collection, root)["cast_shadow"] = False


def build_water(scene):
    terrain = scene.terrain
    root = scene.root("water")
    near = (-9000.0, -9000.0, 9000.0, 9000.0)
    pieces = [rterrain.water_mesh("water_near", terrain, near, 300.0, 25.0),
              rterrain.water_mesh("water_far", terrain, (-60000.0, -60000.0, 60000.0, 60000.0), 3000.0, 3000.0,
                                  hole=near, refine=False)]
    for mesh in pieces:
        mesh.materials.append(bpy.data.materials["water"])
        new_object(mesh.name, mesh, scene.collection, root)["cast_shadow"] = False
    ring = MeshBuilder()
    reach = 60000.0
    outer = 200000.0
    for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        ring.polygon([(ax * reach, ay * reach, 0.0), (bx * reach, by * reach, 0.0), (bx * outer, by * outer, 0.0),
                      (ax * outer, ay * outer, 0.0)], "water", color=(0.02, 0.22, 0.50))
    unique_object("water_horizon", ring, scene.collection, root, scene.tiles, cast_shadow=False,
                  ground_occlusion=False)


def build_surface(scene):
    objects = []
    for name in WALKABLE:
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in [root] + list(root.children_recursive):
            if item.type != "MESH" or item.name.startswith(("terrain_far", "terrain_mid")):
                continue
            if item.name.startswith(("column_", "bollard", "portico", "statue", "awning", "honorific", "avenue_statue",
                                     "agora_statue", "harbour_tower")):
                continue
            objects.append(item)
    scene.surface = Surface(objects)


COLOSSUS_ZONE = (-12.0, 45.0, 19.0)
MAX_STEP = 0.2


def refine(scene, a, b, clamp):
    if (b - a).to_2d().length <= 0.6:
        return [b]
    middle = (a + b) / 2
    middle.z = clamp(scene.surface.height(middle.x, middle.y, max(a.z, b.z), 2.0))
    if abs(b.z - a.z) > 0.12 or abs(middle.z - (a.z + b.z) / 2) > 0.03:
        return refine(scene, a, middle, clamp) + refine(scene, middle, b, clamp)
    return [b]


def add_route(scene, name, points, hint, reach=4.0, clamp=lambda z: z):
    root = scene.root("life")
    chain = []
    for point in resample([Vector((p[0], p[1], 0.0)) for p in points], 2.6):
        z = clamp(scene.surface.height(point.x, point.y, hint(point), reach))
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        refined.extend(refine(scene, refined[-1], following, clamp))
    inverse = scene.marks["frame"].inverted()
    for point in refined:
        local = inverse @ point
        low, high, half = COLOSSUS_ZONE
        assert not (low < local.x < high and abs(local.y) < half), (name, tuple(point))
        for cx, cy, hx, hy, angle in scene.solid:
            c, s = math.cos(angle), math.sin(angle)
            u = (point.x - cx) * c + (point.y - cy) * s
            v = -(point.x - cx) * s + (point.y - cy) * c
            assert not (abs(u) < hx and abs(v) < hy), (name, tuple(point), (cx, cy))
    for a, b in zip(refined[:-1], refined[1:]):
        assert abs(b.z - a.z) <= MAX_STEP, (name, tuple(a), tuple(b))
        assert (b - a).length <= 3.0, (name, tuple(a), tuple(b))
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


def sanctuary_tour(scene):
    f = scene.marks["frame"]
    t = plan.TEMPLE
    tour = [Vector((t.x - 10.0, t.y - 17.0, 0.0)), Vector((t.x + 24.0, t.y - 17.0, 0.0)),
            Vector((t.x + 40.0, t.y - 14.0, 0.0)), Vector((t.x + 40.0, t.y + 14.0, 0.0)),
            Vector((t.x + 46.0, t.y + 24.0, 0.0))]
    loop = ((47.0, -21.0), (49.0, 8.0), (48.0, 21.0), (36.0, 22.0), (14.0, 24.0), (-16.0, 22.0), (-16.0, -24.0),
            (8.0, -24.0), (30.0, -23.0), (46.0, -22.0))
    tour += [f @ Vector((u, v, 0.0)) for u, v in loop]
    return [Vector((p.x, p.y, 0.0)) for p in tour]


def near_polyline(points, x, y, radius):
    p = Vector((x, y))
    for a, b in zip(points[:-1], points[1:]):
        a, b = a.to_2d(), b.to_2d()
        d = b - a
        t = min(max((p - a).dot(d) / max(d.length_squared, 1e-9), 0.0), 1.0)
        if (a + d * t - p).length < radius:
            return True
    return False


def quay_walk(scene):
    apron = plan.QUAY_TOP + 0.065
    best = []
    for name, candidate in scene.quay_lines:
        if name != "great":
            continue
        walk = path_offset([tuple(p) for p in resample([Vector(p) for p in candidate], 2.0)], 8.0)
        run = []
        for p in walk:
            z = scene.surface.height(p.x, p.y, apron + 0.6, 2.0)
            if abs(z - apron) < 0.3 and scene.free(p.x, p.y, 0.8):
                run.append(p)
                if len(run) > len(best):
                    best = list(run)
            else:
                run = []
    return best[:200]


def build_routes(scene):
    counts = {}
    level = plan.SANCTUARY["level"]
    tour = sanctuary_tour(scene)
    counts["sanctuaire"] = add_route(scene, "sanctuaire", tour, lambda p: level + 0.5, 2.0)
    line = [(x, plan.AVENUE_Y + 1.0) for x in np.arange(-420.0, 420.0, 20.0)]
    counts["avenue"] = add_route(scene, "avenue", line, lambda p: scene.ground(p.x, p.y) + 1.5, 5.0)
    apron = plan.QUAY_TOP + 0.065
    counts["quai"] = add_route(scene, "quai", quay_walk(scene), lambda p: apron + 0.6, 2.0,
                               lambda z: apron if abs(z - apron) < 0.3 else z)
    y0, y1 = plan.STADIUM_Y
    track = [(plan.STADIUM_AXIS_X - 6.0, y) for y in np.arange(y0 + 10.0, y1 - 5.0, 10.0)]
    counts["stade"] = add_route(scene, "stade", track, lambda p: plan.STADIUM_LEVEL + 0.5, 2.0)
    return counts


GROUPS = ("guide_party", "thumb_embrace", "citizens", "citizens_b", "students", "offering", "dock_gang", "sailors",
          "donkey_driver", "scale_table")


def embrace_spot(scene):
    root = scene.marks["thumb_root"]
    tip = scene.marks["thumb_tip"]
    axis = Vector((tip.x - root.x, tip.y - root.y)).normalized()
    across = Vector((-axis.y, axis.x))
    if across.dot((scene.marks["wrist"] - root).to_2d()) < 0:
        across = -across
    middle = scene.marks["thumb"].to_2d()
    spot = middle + across * 0.55
    return Vector((spot.x, spot.y, 0.0)), math.atan2(across.x, -across.y)


def clear_of_routes(scene, x, y, radius):
    point = Vector((x, y))
    return all((point - sample).length > radius for sample in scene.route_samples[::2])


def populate(scene, eyes):
    rng = random.Random(131)
    placed = {}

    def put(key, x, y, heading, hint, radius=1.4, check_eyes=True):
        if key in GROUPS:
            radius = max(radius, 3.0)
        if not clear_of_routes(scene, x, y, radius):
            return False
        if check_eyes and min((Vector((x, y)) - eye).length for eye in eyes) < 9.0:
            return False
        z = scene.surface.height(x, y, hint, 6.0)
        placed.setdefault(key, []).append(Matrix.Translation((x, y, z)) @ Matrix.Rotation(heading, 4, "Z"))
        return True

    level = plan.SANCTUARY["level"]
    f = scene.marks["frame"]
    spot, heading = embrace_spot(scene)
    assert put("thumb_embrace", spot.x, spot.y, heading, level + 1.0, 0.3, False)
    guide = f @ Vector((22.0, -12.0, 0.0))
    assert put("guide_party", guide.x, guide.y, plan.COLOSSUS_FALL, level + 1.0, 0.5, False)
    for x, y in ((34.0, -15.0), (-12.0, 14.0), (26.0, 16.0), (48.0, -6.0)):
        p = f @ Vector((x, y, 0.0))
        put(rng.choice(["citizens", "citizens_b", "students"]), p.x, p.y, rng.uniform(0, 6.28), level + 1.0, 1.0)
    t = plan.TEMPLE
    put("offering", t.x + 26.0, t.y - 3.0, math.pi / 2, level + 1.0, 1.0)
    for k in range(10):
        x = rng.uniform(t.x - 10.0, t.x + 55.0)
        y = rng.uniform(t.y - 20.0, t.y + 50.0)
        if scene.free(x, y, 1.0):
            put(rng.choice(["fig_rhodian", "fig_roman", "citizens_b", "fig_woman"]), x, y, rng.uniform(0, 6.28),
                level + 1.0)
    x0, x1 = scene.avenue
    busy = 0
    for k in range(600):
        if busy >= 95:
            break
        x = rng.uniform(-300.0, 300.0)
        y = plan.AVENUE_Y + rng.choice((-1, 1)) * rng.uniform(1.5, 6.6)
        if not scene.free(x, y, 0.4):
            continue
        busy += put(rng.choice(["citizens", "citizens_b", "fig_rhodian", "fig_woman", "students", "fig_roman",
                                "donkey_driver", "fig_rhodian", "fig_woman", "fig_porter"]), x, y,
                    rng.uniform(0, 6.28), strip_z(scene, x) + 1.0)
    for k in range(40):
        x = rng.uniform(x0 + 20.0, x1 - 20.0)
        y = plan.AVENUE_Y + rng.choice((-1, 1)) * rng.uniform(2.0, 6.0)
        if -320.0 < x < 320.0 or not scene.free(x, y, 0.5):
            continue
        put(rng.choice(["citizens", "citizens_b", "fig_rhodian", "fig_woman", "students", "fig_roman",
                        "donkey_driver"]), x, y, rng.uniform(0, 6.28), strip_z(scene, x) + 1.0)
    for name, line in scene.quay_lines:
        dense = resample([Vector(p) for p in line], 9.0)
        for point in path_offset([tuple(p) for p in dense], 7.0)[1:-1]:
            if rng.random() < 0.72:
                continue
            key = rng.choice(["dock_gang", "sailors", "amphora_stack", "fig_sailor", "fig_porter", "sack_pile",
                              "scale_table", "citizens_b"])
            put(key, point.x + rng.uniform(-2, 2), point.y + rng.uniform(-2, 2), rng.uniform(0, 6.28),
                plan.QUAY_TOP + 1.0, 2.4)
    for k in range(30):
        x, y, z = rng.choice(scene.chunks)
        px, py = x + rng.choice((-1, 1)) * (city.CHUNK[0] / 2 + 2.0), y + rng.uniform(-15.0, 15.0)
        if in_detail_zone(px, py):
            put(rng.choice(["fig_rhodian", "fig_woman", "citizens_b"]), px, py, rng.uniform(0, 6.28),
                scene.ground(px, py) + 1.0)
    counts = {}
    for key, matrices in placed.items():
        scene.instances("life", key, life.LIFE[key], matrices)
        counts[key] = len(matrices)
    return counts


def place_effects(scene):
    root = scene.root("life")
    rng = random.Random(7)
    smokes = []
    t = plan.TEMPLE
    smokes.append(Vector((t.x + 30.0, t.y, plan.SANCTUARY["level"] + 2.4)))
    for k in range(60):
        if len(smokes) >= 8:
            break
        x, y, z = rng.choice(scene.chunks)
        if any((Vector((x, y)) - q.to_2d()).length < 350.0 for q in smokes):
            continue
        smokes.append(Vector((x + rng.uniform(-12, 12), y + rng.uniform(-12, 12), z + 11.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(Vector((400.0, 450.0)), 40.0), (Vector((1000.0, -150.0)), 55.0), (Vector((-1150.0, -560.0)), 120.0),
              (Vector((-300.0, -300.0)), 80.0), (Vector((1500.0, 600.0)), 30.0)]
    for index, (point, height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation((point.x, point.y, height)))
    for index, (key, build) in enumerate(life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke": len(smokes), "birds": len(flocks), "walkers": len(life.WALKERS)}


def mark_small(scene):
    for name in ("life", "quays", "vegetation"):
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in root.children_recursive:
            key = item.name.split(".")[0]
            if key in ("bollard", "shrub", "weed", "amphora_stack", "sack_pile") or key.startswith("group_shrub"):
                item["cast_shadow"] = False


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
            foliage = name == "vegetation"
            aweather.weather(mesh, heights, world_z, seed, foliage)
            if name in ("city", "harbour", "sanctuary", "acropolis", "avenue", "stadium", "quays") and len(
                    mesh.vertices) < 80000:
                nimes_detail.occlusion(mesh, seed)


def viewpoints(scene):
    points = {}
    level = plan.SANCTUARY["level"]
    f = scene.marks["frame"]
    points["vue-d-ensemble"] = (Vector((600.0, 2300.0, 380.0)), Vector((-1100.0, -600.0, 70.0)))
    eye = f @ Vector((-4.0, -22.0, 0.0))
    target = f @ Vector((16.0, 2.0, 0.0))
    points["le-colosse-a-terre"] = (Vector((eye.x, eye.y, level + 1.7)), Vector((target.x, target.y, level + 6.0)))
    spot, heading = embrace_spot(scene)
    thumb = scene.marks["thumb"]
    across = (spot.to_2d() - thumb.to_2d()).normalized()
    axis = Vector((-across.y, across.x))
    eye = thumb.to_2d() + across * 5.5 + axis * 2.5
    points["le-pouce"] = (Vector((eye.x, eye.y, level + 1.6)), Vector((thumb.x, thumb.y, thumb.z + 0.2)))
    points["le-port"] = (Vector((360.0, 700.0, 22.0)), Vector((200.0, 420.0, 6.0)))
    points["l-acropole"] = (Vector((-1012.0, -742.0, 96.0)), Vector((-1168.0, -628.0, 80.0)))
    ax = 300.0
    points["la-ville"] = (Vector((ax, plan.AVENUE_Y + 2.0, strip_z(scene, ax) + 5.0)),
                          Vector((-900.0, plan.AVENUE_Y, scene.ground(-900.0, plan.AVENUE_Y) + 30.0)))
    return points


LENSES = {"vue-d-ensemble": 45.0, "le-colosse-a-terre": 24.0, "l-acropole": 35.0, "le-pouce": 28.0}


def extra_views(scene):
    level = plan.SANCTUARY["level"]
    thumb = scene.marks["thumb"]
    f = scene.marks["frame"]
    side = (f.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
    along = (f.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    knee = scene.marks["knee"]
    face = scene.marks["face"]
    out = scene.marks["face_out"] - face
    out = Vector((out.x, out.y, 0.0)).normalized()
    return {
        "x-caverne": (knee + along * -3.5 + side * 5.0 + Vector((0.0, 0.0, 1.2)), knee + along * 6.0),
        "x-visage": (face + out * 9.0 + along * 2.0 + Vector((0.0, 0.0, 1.5)), face),
        "x-piedestal": (f @ Vector((-26.0, -24.0, 0.0)) + Vector((0, 0, 1.7)), f @ Vector((0.0, 0.0, 15.0))),
        "x-approche": (Vector((1100.0, 260.0, 16.0)), Vector((900.0, -200.0, 6.0))),
    }


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
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.5, aerosol=0.15)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 6.0, (1.0, 0.88, 0.72), 0.6)
    if options.get("haze", "1") == "1":
        haze_volume(stage, 9000.0, 600.0, 0.000005, (0.78, 0.86, 0.96), 0.3)
    configure_render(1280, 720, options["samples"], exposure=float(options.get("exposure", "0.0")),
                     volumetric_end=14000.0)
    view = bpy.context.scene.view_settings
    for transform in ("Khronos PBR Neutral", "AgX"):
        try:
            view.view_transform = transform
            break
        except TypeError:
            continue
    try:
        view.look = "None"
    except TypeError:
        pass
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
    terrain = rterrain.Terrain(CACHE, plan)
    print("FIELDS", round(time.perf_counter() - started, 1), flush=True)
    scene = Scene(tiles, terrain)
    build_sanctuary(scene)
    build_athena(scene)
    build_stadium(scene)
    build_harbours(scene)
    build_agora(scene)
    build_avenue(scene)
    chunk_counts = build_city(scene)
    wall_counts = build_walls(scene)
    build_vegetation(scene)
    print("CITY", chunk_counts, round(time.perf_counter() - started, 1), flush=True)
    ship_counts = build_ships(scene)
    column_counts = place_columns(scene)
    place_statues(scene)
    vegetation_counts = place_vegetation(scene)
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
    mark_small(scene)
    weather_all(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "rhodes.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION],
        "counts": {"chunks": chunk_counts, "walls": wall_counts, "ships": ship_counts, "columns": column_counts,
                   "vegetation": vegetation_counts, "routes": route_counts, "life": life_counts, "effects": effects},
        "route_checks": route_report(scene),
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "build_seconds": round(time.perf_counter() - started, 1), "terrain_source": rterrain.SOURCE,
        "texture_credits": credits,
        "colossus": {key: [round(v, 2) for v in value] for key, value in scene.marks.items() if key != "frame"},
        "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                    for key, (eye, target) in points.items()},
    }
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    views = dict(points)
    views.update(extra_views(scene))
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in views.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("BUILD", round(time.perf_counter() - started, 1), flush=True)
    print("PREVIEWS", json.dumps(render_previews(options, points)), flush=True)


main()

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

from kit import alexandrie_weather as aweather
from kit import nimes_detail
from kit import olympie_doric as doric
from kit import olympie_life as life
from kit import olympie_monuments as mon
from kit import olympie_plan as plan
from kit import olympie_terrain as oterrain
from kit import olympie_zeus as zeus
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, save_pixels
from kit.nimes_figures import Look, person
from kit.olympie_materials import build_library, remap
from kit.stage import camera, configure_render, evening_world, export_glb, group_statistics, haze_volume, render_still, \
    sun_lamp

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "olympie")
BLEND = os.path.join(CACHE, "work", "olympie.blend")
SUN_AZIMUTH = 250.0
SUN_ELEVATION = 40.0
LENS = 27.8
CORE = (-760.0, -620.0, 1220.0, 890.0, 3.5, 2048)
NEAR = (-760.0, -700.0, 1520.0, 1520.0, 8.0, 2048)
MIDDLE = (-7000.0, -7000.0, 14000.0, 14000.0, 80.0, 2048)
FAR = (-34000.0, -34000.0, 68000.0, 68000.0, 400.0, 1024)
WALKABLE = ("terrain", "crypt_floor")
TEMPLE_Z = plan.ALTIS_LEVEL + zeus.GROUND_TO_STYLOBATE + 0.12
STATUE_KEYS = ("statue_athlete", "statue_draped", "statue_roman", "statue_athlete_b", "statue_zeus")


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
        self.collection = ensure_collection("Olympie")
        self.roots = {}
        self.pending = {}
        self.columns = {}
        self.placed = {}
        self.footprints = []
        self.blocked = []
        self.surface = None
        self.routes = {}
        self.route_samples = []

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return float(self.terrain.height(x, y))

    def lowest(self, x, y, radius):
        points = [(x + dx, y + dy) for dx in (-radius, 0.0, radius) for dy in (-radius, 0.0, radius)]
        return min(self.ground(px, py) for px, py in points)

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

    def column(self, key, matrix):
        self.columns.setdefault(key, []).append(matrix)

    def add(self, key, matrix):
        self.placed.setdefault(key, []).append(matrix)

    def footprint(self, x, y, half_x, half_y, angle=0.0, strength=0.3, block=True):
        self.footprints.append((x, y, half_x, half_y, angle, strength))
        if block:
            self.blocked.append((x, y, half_x + 1.5, half_y + 1.5, angle))

    def free(self, x, y, margin=0.0):
        for cx, cy, hx, hy, angle in self.blocked:
            c, s = math.cos(angle), math.sin(angle)
            dx, dy = x - cx, y - cy
            u = dx * c + dy * s
            v = -dx * s + dy * c
            if abs(u) < hx + margin and abs(v) < hy + margin:
                return False
        return True


def frame_at(x, y, z, rotation=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rotation, 4, "Z")


def add_columns(scene, frame, columns, default_rotation=0.0):
    for item in columns:
        key, x, y, z = item[:4]
        extra = item[4:]
        rotation = default_rotation
        scale = (1.0, 1.0, 1.0)
        if key == "philippeion":
            rotation = extra[0] + math.pi / 2
        elif len(extra) == 2:
            scale = (extra[0], extra[0], extra[1])
        matrix = frame @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(rotation, 4, "Z") @ Matrix.Diagonal(
            (*scale, 1.0)).to_4x4()
        scene.column(key, matrix)


COLUMN_BUILDS = {
    "zeus_ext": lambda: doric.doric_column(2.25, 10.53, "plaster", 20, "high"),
    "zeus_antis": lambda: doric.doric_column(1.95, 9.93, "plaster", 20, "high"),
    "zeus_in_low": lambda: doric.doric_column(1.4, 6.8, "plaster", 20, "medium", colour=(0.5, 0.47, 0.43)),
    "zeus_in_up": lambda: doric.doric_column(1.0, 4.95, "plaster", 16, "medium", colour=(0.42, 0.40, 0.37)),
    "heraion_a": lambda: doric.doric_column(1.28, 5.22, "limestone", 16, "medium", top_ratio=0.72, capital=0.5),
    "heraion_b": lambda: doric.doric_column(1.12, 5.22, "plaster", 20, "medium", top_ratio=0.8, capital=0.4),
    "heraion_oak": lambda: doric.doric_column(1.1, 5.22, "matte", 0, "low", colour=(0.42, 0.30, 0.20)),
    "metroon": lambda: doric.doric_column(0.86, 4.7, "plaster", 20, "medium"),
    "treasury": lambda: doric.doric_column(0.7, 4.4, "plaster", 20, "medium"),
    "stoa_doric": lambda: doric.doric_column(0.78, 5.3, "plaster", 20, "medium"),
    "stoa_inner": lambda: doric.doric_column(0.62, 6.4, "plaster", 0, "low"),
    "ionic_outer": lambda: doric.simple_ionic(0.56, 5.0, "plaster"),
    "ionic_small": lambda: doric.simple_ionic(0.6, 5.0, "marble"),
    "stoa_plain": lambda: doric.doric_column(0.78, 5.3, "plaster", 0, "low"),
    "philippeion": lambda: doric.ionic_column(0.78, 6.3, "marble", "high"),
    "brick_pier": lambda: doric.doric_column(0.6, 4.6, "plaster", 0, "low", colour=(0.92, 0.84, 0.70)),
}
COLUMN_GROUP = {"zeus_ext": "zeus", "zeus_antis": "zeus", "zeus_in_low": "zeus", "zeus_in_up": "zeus"}


def place_columns(scene):
    counts = {}
    for key, matrices in scene.columns.items():
        group = COLUMN_GROUP.get(key, "columns")
        scene.instances(group, f"column_{key}", COLUMN_BUILDS[key], matrices, True)
        counts[key] = len(matrices)
    return counts


def build_zeus(scene):
    temple = zeus.layout()
    frame = Matrix.Translation((plan.ZEUS.x, plan.ZEUS.y, TEMPLE_Z))
    exterior, apex, (eave_x, eave_y) = zeus.exterior(temple)
    scene.unique("zeus", exterior, frame)
    scene.unique("zeus", zeus.naos(temple), frame)
    for x, y in temple.column_positions():
        scene.column("zeus_ext", frame @ Matrix.Translation((x, y, 0.0)))
    for x, y, z in zeus.antis_columns():
        scene.column("zeus_antis", frame @ Matrix.Translation((x, y, z)))
    lower, upper = zeus.interior_columns()
    for x, y, z in lower:
        scene.column("zeus_in_low", frame @ Matrix.Translation((x, y, z)))
    for x, y, z in upper:
        scene.column("zeus_in_up", frame @ Matrix.Translation((x, y, z)))
    base_x = (zeus.BASE_X[0] + zeus.BASE_X[1]) / 2
    scene.unique("zeus_statue", zeus.statue_base(), frame @ Matrix.Translation((base_x, 0.0, zeus.CELLA_FLOOR)))
    statue_frame = frame @ Matrix.Translation((base_x - 0.6, 0.0, zeus.CELLA_FLOOR + 1.08)) @ Matrix.Rotation(
        -math.pi / 2, 4, "Z")
    scene.unique("zeus_statue", zeus.statue(), statue_frame)
    face = temple.half_x + 0.42 * temple.d + 0.34
    east = zeus.pediment_group(True, eave_y, temple.roof_rise * 0.92)
    west = zeus.pediment_group(False, eave_y, temple.roof_rise * 0.92)
    scene.unique("zeus", east, frame @ Matrix.Translation((face, 0.0, temple.geison_top)) @ Matrix.Rotation(
        -math.pi / 2, 4, "Z"))
    scene.unique("zeus", west, frame @ Matrix.Translation((-face, 0.0, temple.geison_top)) @ Matrix.Rotation(
        math.pi / 2, 4, "Z"))
    scene.unique("zeus", zeus.nike(1.7), frame @ Matrix.Translation((eave_x - 0.6, 0.0, apex + 0.2))
                 @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            scene.unique("zeus", zeus.cauldron(1.1), frame @ Matrix.Translation(
                (sx * (eave_x - 0.9), sy * (eave_y - 0.9), temple.geison_top - 0.05)))
    for x, y, z in zeus.lamp_positions():
        scene.unique("zeus_lamps", zeus.oil_lamp(), frame @ Matrix.Translation((x, y, z)))
    scene.unique("zeus", zeus.furnishings(), frame)
    for y, cuirass in ((-4.4, True), (4.4, False)):
        scene.unique("zeus", zeus.emperor(7 if cuirass else 8, cuirass),
                     frame @ Matrix.Translation((18.6, y, zeus.CELLA_FLOOR)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    scene.footprint(plan.ZEUS.x, plan.ZEUS.y, 34.5, 15.5, 0.0, 0.45)
    scene.blocked.append((plan.ZEUS.x + 41.0, plan.ZEUS.y, 8.0, 4.0, 0.0))
    return temple, frame, apex


def build_altis(scene):
    z = plan.ALTIS_LEVEL + 0.82
    builder, columns, temple = mon.heraion()
    frame = frame_at(plan.HERAION.x, plan.HERAION.y, z)
    scene.unique("altis", builder, frame)
    add_columns(scene, frame, columns)
    scene.footprint(plan.HERAION.x, plan.HERAION.y, 26.5, 10.5)
    builder, columns, temple = mon.metroon()
    frame = frame_at(plan.METROON.x, plan.METROON.y, plan.ALTIS_LEVEL + 0.66)
    scene.unique("altis", builder, frame)
    add_columns(scene, frame, columns)
    scene.footprint(plan.METROON.x, plan.METROON.y, 11.5, 6.0)
    builder, columns = mon.treasury_row(*plan.TREASURY_X)
    frame = frame_at(0.0, plan.TREASURY_FRONT, plan.TERRACE_LEVEL)
    scene.unique("altis", builder, frame)
    add_columns(scene, frame, columns)
    scene.footprint((plan.TREASURY_X[0] + plan.TREASURY_X[1]) / 2, plan.TREASURY_FRONT + 7.0,
                    (plan.TREASURY_X[1] - plan.TREASURY_X[0]) / 2 + 6.0, 8.0)
    builder, columns = mon.philippeion()
    frame = frame_at(plan.PHILIPPEION.x, plan.PHILIPPEION.y, plan.ALTIS_LEVEL + 1.2)
    scene.unique("altis", builder, frame)
    add_columns(scene, frame, columns)
    for k, angle in enumerate((-0.5, 0.0, 0.5)):
        look = Look((1.0, 1.0, 1.0), hem=0.5 if k != 1 else 0.1, skin=0, hair=1, palla=(1.0, 1.0, 1.0) if k == 1 else None,
                    cloak=(1.0, 1.0, 1.0) if k != 1 else None, arms="olym_spear", mono=(1.0, 1.0, 1.0),
                    material="bronze_gilt", seed=300 + k)
        statue = MeshBuilder()
        statue.merge(person(look), Matrix.Scale(1.25, 4))
        offset = Vector((-math.cos(angle) * 3.2, math.sin(angle) * 3.2, 1.0))
        base = MeshBuilder()
        base.box((-0.7, -0.7, 0.0), (0.7, 0.7, 1.0), "marble", bottom=False)
        scene.unique("altis", base, frame @ Matrix.Translation((offset.x, offset.y, 0.0)))
        scene.unique("altis", statue, frame @ Matrix.Translation(offset) @ Matrix.Rotation(-math.pi / 2 + angle, 4,
                                                                                              "Z"))
    scene.footprint(plan.PHILIPPEION.x, plan.PHILIPPEION.y, 8.5, 8.5)
    builder, niches = mon.nymphaeum()
    frame = frame_at(plan.NYMPHAEUM.x, plan.NYMPHAEUM.y, plan.ALTIS_LEVEL)
    scene.unique("altis", builder, frame)
    for k, (x, y, z, heading) in enumerate(niches):
        scene.add("niche_statue" if k % 2 else "niche_statue_b",
                  frame @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(heading + math.pi / 2, 4, "Z"))
    scene.footprint(plan.NYMPHAEUM.x, plan.NYMPHAEUM.y + 2.0, 13.0, 9.0)
    stoa, columns = mon.stoa(plan.ECHO_STOA[2] - plan.ECHO_STOA[1], 12.5, 5.3, 2.2, inner=True,
                             wall_colour=(0.92, 0.78, 0.56),
                             panels=[(0.62, 0.20, 0.14), (0.24, 0.36, 0.56), (0.86, 0.66, 0.30), (0.30, 0.46, 0.30)])
    sx = plan.ECHO_STOA[0] + 6.25
    sy = (plan.ECHO_STOA[1] + plan.ECHO_STOA[2]) / 2
    frame = frame_at(sx, sy, plan.ALTIS_LEVEL + 0.6, math.pi / 2)
    scene.unique("altis", stoa, frame)
    add_columns(scene, frame, columns)
    scene.footprint(sx, sy, 7.0, (plan.ECHO_STOA[2] - plan.ECHO_STOA[1]) / 2 + 1.0)
    pelopion = mon.pelopion()
    scene.unique("altis", pelopion, frame_at(plan.PELOPION.x, plan.PELOPION.y, plan.ALTIS_LEVEL))
    scene.footprint(plan.PELOPION.x, plan.PELOPION.y, 18.0, 15.0, 0.0, 0.15)
    scene.unique("altar", mon.great_altar(), frame_at(plan.GREAT_ALTAR.x, plan.GREAT_ALTAR.y, plan.ALTIS_LEVEL))
    scene.footprint(plan.GREAT_ALTAR.x, plan.GREAT_ALTAR.y - 2.0, 7.5, 6.5, 0.0, 0.2)
    gates = [((-80.0, -52.0), 6.0), ((40.0, -52.0), 5.0), ((-104.0, 30.0), 5.0)]
    wall = mon.altis_wall(plan.ALTIS_WALL, gates=gates)
    scene.unique("altis", wall, frame_at(0.0, 0.0, plan.ALTIS_LEVEL))
    wall = mon.altis_wall(plan.ALTIS_WALL_WEST, gates=gates)
    scene.unique("altis", wall, frame_at(0.0, 0.0, plan.ALTIS_LEVEL))
    scene.unique("altis", life.nike_paionios(), frame_at(plan.NIKE_PAIONIOS.x, plan.NIKE_PAIONIOS.y,
                                                         plan.ALTIS_LEVEL, math.pi / 2 - 0.3))
    scene.footprint(plan.NIKE_PAIONIOS.x, plan.NIKE_PAIONIOS.y, 2.0, 2.0)
    builder = mon.prytaneion()
    scene.unique("outer", builder, frame_at(plan.PRYTANEION.x, plan.PRYTANEION.y, plan.ALTIS_LEVEL))
    scene.footprint(plan.PRYTANEION.x, plan.PRYTANEION.y, 16.5, 16.5)
    channel = []
    for k in range(18):
        x = plan.NYMPHAEUM.x + 6.0 + k * 22.0
        y = plan.NYMPHAEUM.y + 16.0 + k * 3.0
        channel.append((x, y, scene.ground(x, y) + 0.2))
    scene.unique("altis", mon.aqueduct_channel(channel), Matrix.Identity(4))


def build_zanes(scene):
    for k, (x, y) in enumerate(plan.ZANES):
        scene.add("statue_zeus", frame_at(x, y, plan.ALTIS_LEVEL, math.pi))
        scene.blocked.append((x, y, 1.2, 1.2, 0.0))
    for y in (plan.STADIUM_AXIS_Y - 4.6, plan.STADIUM_AXIS_Y + 4.6):
        scene.add("statue_zeus", frame_at(plan.CRYPT_WEST - 2.5, y, plan.ALTIS_LEVEL, math.pi / 2))


def build_stadium(scene):
    x0, x1, y0, y1 = plan.ARENA
    frame = frame_at(plan.CRYPT_WEST, plan.STADIUM_AXIS_Y, plan.ARENA_LEVEL)
    scene.unique("stadium", mon.crypt(plan.CRYPT_EAST - plan.CRYPT_WEST), frame)
    floor = MeshBuilder()
    floor.box((-1.0, -1.85, -0.05), (plan.CRYPT_EAST - plan.CRYPT_WEST + 0.5, 1.85, 0.0), "paving", bottom=False)
    low = plan.ALTIS_LEVEL - plan.ARENA_LEVEL + 0.03
    ramp = floor.points([(-9.0, -1.85, low), (-1.0, -1.85, 0.0), (-1.0, 1.85, 0.0), (-9.0, 1.85, low)])
    floor.face(ramp, "paving")
    scene.unique("crypt_floor", floor, frame)
    scene.unique("stadium", mon.stadium_fittings(plan.ARENA), frame_at(0.0, 0.0, plan.ARENA_LEVEL))
    seat = mon.judges_seat()
    sx = x0 + 10.1 + 192.27 * 0.62
    sy = y0 - 7.0
    scene.unique("stadium", seat, frame_at(sx, sy, scene.ground(sx, sy) - 0.2, math.pi))
    scene.blocked.append((sx, sy, 8.0, 4.0, 0.0))
    ax = sx
    ay = y1 + 6.0
    scene.unique("stadium", mon.demeter_altar(), frame_at(ax, ay, scene.lowest(ax, ay, 1.5) + 0.2))
    scene.blocked.append((ax, ay, 3.0, 3.0, 0.0))
    return (sx, sy), (ax, ay)


def river_clearance(footprints):
    worst = math.inf
    for cx, cy, hx, hy, angle, _ in footprints:
        c, s = math.cos(angle), math.sin(angle)
        u = np.linspace(-hx, hx, 24)
        v = np.linspace(-hy, hy, 24)
        gu, gv = np.meshgrid(u, v)
        xs = cx + gu * c - gv * s
        ys = cy + gu * s + gv * c
        distance, _ = oterrain.polyline_measure(plan.KLADEOS, xs.ravel(), ys.ravel())
        worst = min(worst, float(distance.min()))
    return worst


def build_outer(scene):
    first = len(scene.footprints)
    builder, columns = mon.leonidaion()
    z = scene.lowest(plan.LEONIDAION.x, plan.LEONIDAION.y, 30.0)
    frame = frame_at(plan.LEONIDAION.x, plan.LEONIDAION.y, z)
    scene.unique("outer", builder, frame)
    add_columns(scene, frame, columns)
    scene.footprint(plan.LEONIDAION.x, plan.LEONIDAION.y, 41.0, 38.0)
    builder = mon.workshop()
    frame = frame_at(plan.WORKSHOP.x, plan.WORKSHOP.y, scene.lowest(plan.WORKSHOP.x, plan.WORKSHOP.y, 10.0), math.pi / 2)
    scene.unique("outer", builder, frame)
    scene.footprint(plan.WORKSHOP.x, plan.WORKSHOP.y, 16.5, 8.0)
    builder, columns = mon.palaestra()
    frame = frame_at(plan.PALAESTRA.x, plan.PALAESTRA.y, scene.lowest(plan.PALAESTRA.x, plan.PALAESTRA.y, 30.0))
    scene.unique("outer", builder, frame)
    add_columns(scene, frame, columns)
    scene.footprint(plan.PALAESTRA.x, plan.PALAESTRA.y, 34.0, 34.0)
    gx0, gx1 = plan.GYMNASIUM_X
    gy0, gy1 = plan.GYMNASIUM_Y
    length = gy1 - gy0
    for x, rotation in ((gx1 - 6.0, math.pi / 2), (gx0 + 6.0, -math.pi / 2)):
        stoa, columns = mon.stoa(length, 11.0, 5.3, 2.6, inner=True, wall_colour=(0.94, 0.86, 0.70),
                                 colonnade_key="stoa_plain")
        cy = (gy0 + gy1) / 2
        frame = frame_at(x, cy, scene.lowest(x, cy, 8.0) + 0.1, rotation)
        scene.unique("outer", stoa, frame)
        add_columns(scene, frame, columns)
        scene.footprint(x, cy, 6.5, length / 2 + 1.0)
    builder = mon.bouleuterion()[0]
    bz = scene.lowest(plan.BOULEUTERION.x, plan.BOULEUTERION.y, 16.0)
    frame = frame_at(plan.BOULEUTERION.x, plan.BOULEUTERION.y, bz)
    scene.unique("outer", builder, frame)
    add_columns(scene, frame, mon.bouleuterion()[1])
    scene.footprint(plan.BOULEUTERION.x - 2.0, plan.BOULEUTERION.y, 22.0, 22.0)
    x0, x1, y = plan.SOUTH_STOA
    stoa, columns = mon.stoa(x1 - x0, 11.0, 5.4, 2.4, inner=True, wall_colour=(0.92, 0.80, 0.58),
                             colonnade_key="stoa_plain")
    sx = (x0 + x1) / 2
    frame = frame_at(sx, y, scene.lowest(sx, y, 10.0) + 0.1, math.pi)
    scene.unique("outer", stoa, frame)
    add_columns(scene, frame, columns)
    scene.footprint(sx, y, (x1 - x0) / 2 + 1.0, 6.5)
    builder = mon.kladeos_baths()
    frame = frame_at(plan.KLADEOS_BATHS.x, plan.KLADEOS_BATHS.y,
                     scene.lowest(plan.KLADEOS_BATHS.x, plan.KLADEOS_BATHS.y, 12.0), math.pi / 2)
    scene.unique("outer", builder, frame)
    scene.footprint(plan.KLADEOS_BATHS.x, plan.KLADEOS_BATHS.y, 12.0, 21.0)
    builder, columns = mon.nero_house()
    frame = frame_at(plan.NERO_HOUSE.x, plan.NERO_HOUSE.y, scene.lowest(plan.NERO_HOUSE.x, plan.NERO_HOUSE.y, 24.0))
    scene.unique("outer", builder, frame)
    add_columns(scene, frame, columns)
    scene.footprint(plan.NERO_HOUSE.x + 4.0, plan.NERO_HOUSE.y, 37.0, 21.0)
    clearance = river_clearance(scene.footprints[first:])
    assert clearance >= 12.0, f"building within {clearance:.1f} m of the Kladeos axis"
    return clearance


def segment_distance(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def in_sight(p, sights, margin):
    return any(segment_distance(p, a, b) < margin for a, b in sights)


def nearest_route_heading(scene, p, rng):
    target = min(scene.route_samples[::3], key=lambda sample: (sample - p).length_squared)
    direction = target - p
    return math.atan2(direction.y, direction.x) - math.pi / 2 + rng.uniform(-0.26, 0.26)


def statue_forest(scene, eyes, sights):
    rng = random.Random(17)
    spots = []
    rows = [((-60.0, -40.0), (30.0, -40.0)), ((48.0, -34.0), (110.0, 20.0)), ((50.0, 30.0), (100.0, 100.0)),
            ((-70.0, 30.0), (-70.0, 80.0)), ((-30.0, 32.0), (20.0, 32.0)), ((20.0, 60.0), (40.0, 100.0)),
            ((-90.0, -30.0), (-90.0, 60.0)), ((60.0, -45.0), (115.0, -45.0))]
    for (ax, ay), (bx, by) in rows:
        a = Vector((ax, ay))
        b = Vector((bx, by))
        count = int((b - a).length / 4.2)
        for k in range(count + 1):
            p = a.lerp(b, k / max(count, 1)) + Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)))
            near = min((p - eye).length for eye in eyes) < 16.0
            if (scene.free(p.x, p.y, 1.0) and rng.random() < 0.55 and not near and clear_of_routes(scene, p.x, p.y, 2.0)
                    and not in_sight(p, sights, 5.0)):
                spots.append(p)
    for p in spots:
        key = rng.choice(STATUE_KEYS[:4])
        heading = nearest_route_heading(scene, p, rng)
        scene.add(key, frame_at(p.x, p.y, scene.ground(p.x, p.y), heading))
        scene.blocked.append((p.x, p.y, 1.0, 1.0, 0.0))
    return len(spots)


def in_ellipse(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1.0


def build_camps(scene):
    rng = random.Random(23)
    camps = [(60.0, -225.0, 230.0, 62.0, 34), (525.0, 110.0, 105.0, 115.0, 18), (-330.0, 60.0, 62.0, 135.0, 16)]
    centres = []
    for cx, cy, rx, ry, count in camps:
        tries = 0
        found = 0
        while found < count and tries < 4000:
            tries += 1
            x = rng.uniform(cx - rx * 1.15, cx + rx * 1.15)
            y = rng.uniform(cy - ry * 1.15, cy + ry * 1.15)
            edge = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if edge > 0.75 + 0.6 * rng.random():
                continue
            if any(math.hypot(x - px, y - py) < 26.0 for px, py in centres):
                continue
            centres.append((x, y))
            found += 1
    candidates = []
    for px, py in centres:
        size = rng.randint(5, 15)
        local = []
        tries = 0
        while len(local) < size and tries < 200:
            tries += 1
            angle = rng.uniform(0.0, math.tau)
            radius = rng.uniform(3.0, 6.0 + size * 0.9)
            x = px + math.cos(angle) * radius
            y = py + math.sin(angle) * radius * 0.8
            if any(math.hypot(x - qx, y - qy) < 5.6 for qx, qy, _, _ in local):
                continue
            local.append((x, y, px, py))
        candidates.extend(local)
    xs = np.array([c[0] for c in candidates])
    ys = np.array([c[1] for c in candidates])
    kladeos, _ = oterrain.polyline_measure(plan.KLADEOS, xs, ys)
    alpheios, _ = oterrain.polyline_measure(plan.ALPHEIOS, xs, ys)
    tents = {}
    count = 0
    for (jx, jy, px, py), dk, da in zip(candidates, kladeos, alpheios):
        if dk < 22.0 or da < 140.0 or not scene.free(jx, jy, 2.0):
            continue
        kind = rng.random()
        z = scene.lowest(jx, jy, 1.6)
        heading = math.atan2(py - jy, px - jx) - math.pi / 2 + rng.uniform(-0.25, 0.25)
        if kind < 0.7:
            key = f"tent_{rng.randrange(6)}"
        elif kind < 0.8:
            key = f"booth_{rng.randrange(3)}"
        elif kind < 0.85:
            key = "campfire"
        elif kind < 0.89:
            key = "horses"
        else:
            key = rng.choice(["camp_group", "camp_worker"])
        quadrant = (2 if jx > 150.0 else 0) + (1 if jy > -40.0 else 0)
        tents.setdefault(f"{key}@{quadrant}", []).append(frame_at(jx, jy, z, heading))
        count += 1
    return tents, count


def vegetation(scene, eyes, sights):
    rng = random.Random(29)
    placed = {}

    def put(key, x, y, scale, sink=0.3):
        point = Vector((x, y))
        if min((point - eye).length for eye in eyes) < 14.0 or in_sight(point, sights, 15.0):
            return
        z = scene.lowest(x, y, 0.8) - sink
        placed.setdefault(key, []).append(frame_at(x, y, z, rng.uniform(0, math.tau)) @ Matrix.Scale(scale, 4))

    attempts = 0
    while attempts < 2600:
        attempts += 1
        x = rng.uniform(-100.0, 124.0)
        y = rng.uniform(-50.0, 136.0)
        if not scene.free(x, y, 3.0):
            continue
        roll = rng.random()
        if roll < 0.055:
            put(f"plane_{rng.randrange(3)}", x, y, rng.uniform(0.85, 1.15))
            scene.blocked.append((x, y, 3.0, 3.0, 0.0))
        elif roll < 0.1:
            put(f"olive_{rng.randrange(3)}", x, y, rng.uniform(0.85, 1.2))
            scene.blocked.append((x, y, 2.0, 2.0, 0.0))
        elif roll < 0.12:
            put("poplar", x, y, rng.uniform(0.85, 1.1))
            scene.blocked.append((x, y, 2.0, 2.0, 0.0))
    put("olive_0", plan.OLIVE_CROWN.x, plan.OLIVE_CROWN.y, 1.35)
    scene.blocked.append((plan.OLIVE_CROWN.x, plan.OLIVE_CROWN.y, 3.0, 3.0, 0.0))
    for k in range(9):
        a = math.tau * k / 9
        put(f"plane_{k % 3}", plan.PELOPION.x + math.cos(a) * 8.0, plan.PELOPION.y + 2.0 + math.sin(a) * 6.0,
            rng.uniform(0.7, 0.95))
    spacing = 7.75
    for gx in np.arange(plan.KRONOS.x - 220.0, plan.KRONOS.x + 220.0, spacing):
        for gy in np.arange(plan.KRONOS.y - 220.0, plan.KRONOS.y + 220.0, spacing):
            x = gx + rng.uniform(-3.0, 3.0)
            y = gy + rng.uniform(-3.0, 3.0)
            reach = 220.0 * (0.78 + 0.3 * math.sin(math.atan2(y - plan.KRONOS.y, x - plan.KRONOS.x) * 3.0 + 0.7)
                             + 0.12 * math.sin(gx * 0.05 + gy * 0.031))
            flank = math.hypot(x - oterrain.KRONION_FLANK[0], y - oterrain.KRONION_FLANK[1])
            outside = math.hypot(x - plan.KRONOS.x, y - plan.KRONOS.y) > reach and flank > oterrain.KRONION_FLANK[2]
            if outside or y < 150.0 + 14.0 * rng.random():
                continue
            if rng.random() < 0.18:
                continue
            if not scene.free(x, y, 2.0) or in_ellipse(x, y, 274.0, 146.0, 150.0, 70.0):
                continue
            close = math.hypot(x - 40.0, y - 150.0) < 150.0
            key = f"pine_{rng.randrange(3)}" if close else "pine_mid"
            put(key, x, y, rng.uniform(0.8, 1.3), 0.5)
    for k in range(80):
        s = rng.uniform(0.0, oterrain.KLADEOS_STATIONS[-1])
        p, d = plan.along(plan.KLADEOS, s)
        side = Vector((-d.y, d.x)) * rng.choice((-1, 1)) * rng.uniform(9.0, 16.0)
        q = p + side
        if not scene.free(q.x, q.y, 1.0):
            continue
        if rng.random() < 0.6:
            put("poplar", q.x, q.y, rng.uniform(0.75, 1.05))
        else:
            put(f"plane_{rng.randrange(3)}", q.x, q.y, rng.uniform(0.7, 1.0))
    reeds = []
    for k in range(260):
        s = rng.uniform(0.0, oterrain.KLADEOS_STATIONS[-1])
        p, d = plan.along(plan.KLADEOS, s)
        q = p + Vector((-d.y, d.x)) * rng.choice((-1, 1)) * rng.uniform(5.0, 8.5)
        reeds.append((q.x, q.y))
    for k in range(380):
        s = rng.uniform(1500.0, 5200.0)
        p, d = plan.along(plan.ALPHEIOS, s)
        q = p + Vector((-d.y, d.x)) * rng.choice((-1, 1)) * rng.uniform(24.0, 40.0)
        reeds.append((q.x, q.y))
    for x, y in reeds:
        placed.setdefault("reeds", []).append(frame_at(x, y, scene.ground(x, y) - 0.1, rng.uniform(0, math.tau)))
    for k in range(130):
        s = rng.uniform(1200.0, 5600.0)
        p, d = plan.along(plan.ALPHEIOS, s)
        q = p + Vector((-d.y, d.x)) * rng.choice((-1, 1)) * rng.uniform(120.0, 200.0)
        if abs(q.x) < 760 and abs(q.y + 0) < 760 and not scene.free(q.x, q.y, 3.0):
            continue
        put("poplar" if rng.random() < 0.5 else f"plane_{rng.randrange(3)}", q.x, q.y, rng.uniform(0.8, 1.1))
    orchards = [(-520.0, -160.0, 160.0, 90.0), (300.0, -320.0, 200.0, 70.0), (-420.0, 300.0, 120.0, 100.0),
                (620.0, -120.0, 120.0, 100.0)]
    for cx, cy, rx, ry in orchards:
        for x in np.arange(cx - rx, cx + rx, 11.0):
            for y in np.arange(cy - ry, cy + ry, 11.0):
                if not in_ellipse(x, y, cx, cy, rx, ry) or not scene.free(x, y, 3.0):
                    continue
                if rng.random() < 0.5:
                    put("far_olive", x + rng.uniform(-1, 1), y + rng.uniform(-1, 1), rng.uniform(0.7, 1.0), 0.2)
    far = 0
    while far < 900:
        x = rng.uniform(-2600.0, 2600.0)
        y = rng.uniform(-2400.0, 2600.0)
        if abs(x) < 700 and -700 < y < 820:
            continue
        h = scene.ground(x, y)
        if h < 50.0:
            continue
        far += 1
        placed.setdefault("far_pine", []).append(frame_at(x, y, h - 0.6, rng.uniform(0, math.tau))
                                                 @ Matrix.Scale(rng.uniform(0.8, 1.3), 4))
    for k in range(460):
        x = rng.uniform(-740.0, 740.0)
        y = rng.uniform(-680.0, 800.0)
        if abs(x - 80) < 360 and -260 < y < 300:
            continue
        h = scene.ground(x, y)
        if h < 48.0 or math.hypot(x - plan.KRONOS.x, y - plan.KRONOS.y) < 230.0:
            continue
        put("pine_mid", x, y, rng.uniform(0.8, 1.2), 0.5)
    return placed


TREE_BUILDS = {
    "plane_0": lambda: life.plane_tree(17.0, 1), "plane_1": lambda: life.plane_tree(15.0, 2),
    "plane_2": lambda: life.plane_tree(19.0, 3), "olive_0": lambda: life.olive_tree(5.5, 4),
    "olive_1": lambda: life.olive_tree(4.6, 5), "olive_2": lambda: life.olive_tree(6.0, 6),
    "poplar": lambda: life.poplar(19.0, 7), "pine_0": lambda: life.pine(14.0, 8),
    "pine_1": lambda: life.pine(12.0, 9), "pine_2": lambda: life.pine(16.0, 10),
    "far_pine": lambda: life.far_pine(13.0, 11), "reeds": lambda: life.reeds(12),
    "far_olive": lambda: life.far_olive(5.0, 13), "pine_mid": lambda: life.pine_mid(13.0, 14),
}
NO_SHADOW = {"reeds", "far_pine", "far_olive", "pine_mid"}


def place_vegetation(scene, placed):
    counts = {}
    for key, matrices in placed.items():
        scene.instances("vegetation", key, TREE_BUILDS[key], matrices, key not in NO_SHADOW)
        counts[key] = len(matrices)
    return counts


def build_terrain(scene):
    terrain = scene.terrain
    root = scene.root("terrain")
    textures = os.path.join(CACHE, "textures")
    footprints = footprint_mask(scene)
    tiles = [("terrain_core", CORE, None), ("terrain_near", NEAR, CORE), ("terrain_mid", MIDDLE, NEAR),
             ("terrain_far", FAR, MIDDLE)]
    for name, (x0, y0, w, h, spacing, resolution), hole in tiles:
        size = max(w, h)
        colour = cached_bake(scene, name, (x0, y0, size, resolution), lambda: oterrain.bake_tile(
            terrain, x0, y0, size, resolution, footprints if name != "terrain_far" else None,
            detail=name in ("terrain_core", "terrain_near")))
        image = save_pixels(name, colour, os.path.join(textures, f"{name}.jpg"), quality=90)
        material = baked_material(name, image)
        hole_rect = None if hole is None else (hole[0], hole[1], hole[0] + hole[2], hole[1] + hole[3])
        mesh = tile_mesh(name, terrain, x0, y0, w, h, size, spacing, hole_rect)
        mesh.materials.append(material)
        created = new_object(name, mesh, scene.collection, root)
        created["cast_shadow"] = False


def cached_bake(scene, name, spec, bake):
    with open(oterrain.__file__, encoding="utf8") as handle:
        source = handle.read()
    footprints = [tuple(round(value, 2) for value in item) for item in scene.footprints] if name != "terrain_far" else []
    key = hashlib.md5(repr((source, name, spec, footprints)).encode("utf8")).hexdigest()[:16]
    path = os.path.join(CACHE, "work", f"bake_{name}_{key}.npy")
    if os.path.exists(path):
        return np.load(path).astype(np.float64)
    colour = bake()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, colour.astype(np.float16))
    return colour


def tile_mesh(name, terrain, x0, y0, width, height, size, spacing, hole):
    nx = int(round(width / spacing)) + 1
    ny = int(round(height / spacing)) + 1
    xs = x0 + np.arange(nx) * spacing
    ys = y0 + np.arange(ny) * spacing
    gx, gy = np.meshgrid(xs, ys)
    heights = terrain.height(gx, gy)
    if name == "terrain_core":
        trench = (gx > plan.CRYPT_WEST - 1.0) & (gx < plan.CRYPT_EAST - 1.0) & (np.abs(gy - plan.STADIUM_AXIS_Y) < 3.6)
        heights = np.where(trench, np.minimum(heights, plan.ARENA_LEVEL - 0.6), heights)
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        inside = (gx > hx0 + 0.01) & (gx < hx1 - 0.01) & (gy > hy0 + 0.01) & (gy < hy1 - 0.01)
        heights = np.where(inside, heights - 2.0, heights)
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(nx * ny).reshape(ny, nx)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(),
                             index[1:, :-1].ravel()])
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        cx = vertices[quads, 0]
        cy = vertices[quads, 1]
        inside = ((cx >= hx0 - 0.01) & (cx <= hx1 + 0.01) & (cy >= hy0 - 0.01) & (cy <= hy1 + 0.01)).all(axis=1)
        quads = quads[~inside]
    used = np.unique(quads)
    remap_index = np.full(nx * ny, -1, dtype=np.int64)
    remap_index[used] = np.arange(len(used))
    vertices = vertices[used]
    quads = remap_index[quads]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], quads.tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(quads))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    uv = np.column_stack([(vertices[:, 0] - x0) / size, (vertices[:, 1] - y0) / size])
    uv_layer.data.foreach_set("uv", uv[loops].astype(np.float32).ravel())
    mesh.update()
    return mesh


def footprint_mask(scene):
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
            value = strength * np.clip(1.0 - outside / 5.0, 0.0, 1.0)
            block = result[np.ix_(rows, columns)]
            result[np.ix_(rows, columns)] = np.maximum(block, value)
        return result
    return mask


def build_water(scene):
    terrain = scene.terrain
    root = scene.root("water")
    levels = terrain.river_level(oterrain.ALPHEIOS_STATIONS)
    meshes = [oterrain.water_strip("water_alpheios", plan.ALPHEIOS, levels, 28.0, 8.0),
              oterrain.water_strip("water_kladeos", plan.KLADEOS, plan.KLADEOS_LEVELS, 6.6, 4.0),
              oterrain.water_plane("water_sea", -34000.0, -34000.0, 34000.0, 34000.0, 0.0, terrain, 1000.0, 0.5)]
    for mesh in meshes:
        mesh.materials.append(bpy.data.materials["water"])
        created = new_object(mesh.name, mesh, scene.collection, root)
        created["cast_shadow"] = False


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
    result = [Vector(points[0])]
    for a, b in zip(points[:-1], points[1:]):
        a = Vector(a)
        b = Vector(b)
        steps = max(int(math.ceil((b - a).length / spacing)), 1)
        for k in range(1, steps + 1):
            result.append(a.lerp(b, k / steps))
    return result


def add_route(scene, name, points):
    root = scene.root("life")
    chain = []
    for point in resample([Vector((p[0], p[1], 0.0)) for p in points], 2.5):
        z = scene.surface.height(point.x, point.y, scene.ground(point.x, point.y) + 2.0, 4.0)
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        previous = refined[-1]
        middle = (previous + following) / 2
        middle.z = scene.surface.height(middle.x, middle.y, max(previous.z, following.z) + 1.0, 3.0)
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
        where = None
        for a, b in zip(points[:-1], points[1:]):
            if abs(b.z - a.z) > worst:
                worst = abs(b.z - a.z)
                where = [round(b.x, 1), round(b.y, 1)]
            longest = max(longest, (b - a).length)
        report[name] = {"points": len(points), "max_step": round(worst, 2), "max_spacing": round(longest, 2),
                        "worst_at": where}
    return report


def build_routes(scene):
    counts = {}
    routes = {
        "procession": [(-96.0, -66.0), (-82.0, -52.0), (-62.0, -36.0), (-20.0, -26.0), (36.0, -24.0), (54.0, -8.0),
                       (58.0, 30.0), (62.0, 70.0), (84.0, 110.0), (112.0, 122.0), (126.0, 130.0), (130.0, 139.0),
                       (131.0, 146.0), (150.0, 146.0), (166.0, 146.0), (190.0, 144.0)],
        "temple": [(-44.0, -22.0), (44.0, -22.0), (50.0, 0.0), (44.0, 22.0), (-44.0, 22.0), (-50.0, 0.0),
                   (-44.0, -22.0)],
        "heraion": [(-84.0, 76.0), (-60.0, 100.0), (-10.0, 103.0), (14.0, 112.0), (24.0, 128.0)],
        "camp": [(-40.0, -150.0), (20.0, -190.0), (100.0, -215.0), (200.0, -230.0), (260.0, -250.0)],
        "stade": [(186.0, 132.5), (240.0, 132.0), (300.0, 132.0), (360.0, 132.5)],
    }
    for name, points in routes.items():
        counts[name] = add_route(scene, name, points)
    return counts


def clear_of_routes(scene, x, y, radius):
    point = Vector((x, y))
    return all((point - sample).length > radius for sample in scene.route_samples[::2])


def populate(scene, eyes, seat, altar):
    rng = random.Random(131)
    placed = {}

    def put(key, x, y, heading, radius=1.4, check=True):
        if check and (not clear_of_routes(scene, x, y, radius) or not scene.free(x, y, 0.0)):
            return False
        if min((Vector((x, y)) - eye).length for eye in eyes) < 3.0:
            return False
        z = scene.surface.height(x, y, scene.ground(x, y) + 2.0, 6.0)
        placed.setdefault(key, []).append(frame_at(x, y, z, heading))
        return True

    altis_keys = ["conversation", "conversation_b", "conversation_c", "fig_greek", "fig_greek_b", "fig_roman",
                  "fig_maiden", "fig_athlete", "guide_group"]
    tries = 0
    count = 0
    while count < 82 and tries < 3000:
        tries += 1
        x = rng.uniform(-100.0, 124.0)
        y = rng.uniform(-48.0, 136.0)
        if put(rng.choice(altis_keys), x, y, rng.uniform(0, math.tau), 1.6):
            count += 1
    for x, y, key, heading in ((52.0, -14.0, "guide_group", math.pi / 2), (-56.0, 4.0, "guide_group", -math.pi / 2),
                               (-60.0, 96.0, "guide_group", 0.0), (60.0, 118.0, "guide_group", math.pi / 2),
                               (plan.GREAT_ALTAR.x - 2.0, plan.GREAT_ALTAR.y - 10.0, "sacrifice", 0.0),
                               (-70.0, -64.0, "governor", math.pi * 0.8), (40.0, -30.0, "conversation_b", 0.0)):
        put(key, x, y, heading, 2.0, False)
    put("race", 212.0, plan.STADIUM_AXIS_Y - 1.0, math.pi, 2.0, False)
    put("race_b", 236.0, plan.STADIUM_AXIS_Y + 3.0, math.pi, 2.0, False)
    x0 = plan.ARENA[0]
    for x, side in ((x0 + 3.0, -1), (x0 + 7.5, 1), (x0 + 24.0, 1)):
        put("athletes", x, plan.STADIUM_AXIS_Y + side * 12.5, rng.uniform(0, math.tau), 2.0, False)
    put("judges", seat[0], seat[1] + 0.8, 0.0, 2.0, False)
    put("fig_maiden", altar[0], altar[1] - 2.4, math.pi, 1.0, False)
    for x in np.arange(-160.0, -130.0, 6.0):
        put("athletes", x + rng.uniform(-2, 2), plan.PALAESTRA.y + rng.uniform(-18, 18), rng.uniform(0, math.tau),
            2.0, False)
    for k in range(6):
        put("athletes", rng.uniform(-164.0, -128.0), rng.uniform(120.0, 290.0), rng.uniform(0, math.tau), 2.0, False)
        put("runners", rng.uniform(-164.0, -130.0), rng.uniform(120.0, 290.0), rng.choice((0.0, math.pi)), 2.0, False)
    counts = {}
    for key, matrices in placed.items():
        scene.instances("life", key, life.LIFE[key], matrices, True)
        counts[key] = len(matrices)
    return counts


def spectators(scene):
    rng = random.Random(77)
    x0, x1, y0, y1 = plan.ARENA
    blocks = []
    for side, base_y, heading in ((-1, y0 - 3.6, 0.0), (1, y1 + 3.6, math.pi)):
        for x in np.arange(x0 + 6.0, x1 - 4.0, 4.4):
            for row in range(3):
                if rng.random() < 0.14 + row * 0.1:
                    continue
                y = base_y + side * row * 2.15
                if not scene.free(x, y, 0.5) or not clear_of_routes(scene, x, y - side * 1.2, 3.2):
                    continue
                z0 = scene.ground(x, y)
                z1 = scene.ground(x, y + side * 2.2)
                blocks.append((x, y, z0, (z1 - z0) / 3.0, heading))
    for y in np.arange(y0 + 3.0, y1 - 2.0, 4.4):
        for row in range(3):
            x = x1 + 2.4 + row * 2.15
            z0 = scene.ground(x, y)
            z1 = scene.ground(x + 2.2, y)
            blocks.append((x, y, z0, (z1 - z0) / 3.0, math.pi / 2))
    variants = {}
    for x, y, z, rise, heading in blocks:
        level = int(np.clip(round(rise / 0.06), 0, 5))
        near = x < x0 + 24.0 and abs(y - plan.STADIUM_AXIS_Y) < 30.0
        key = f"crowd_{'near' if near else 'far'}_{level}_0"
        variants.setdefault(key, []).append(frame_at(x, y, z - 0.05, heading))
    counts = {}
    for key, matrices in variants.items():
        _, kind, level, seed = key.split("_")
        if kind == "near":
            build = (lambda level=int(level), seed=int(seed): life.spectator_block(seed * 7 + level, 3, 7, 0.62,
                                                                                   level * 0.06))
        else:
            build = (lambda level=int(level), seed=int(seed): life.simple_block(seed * 7 + level, 3, 7, 0.62,
                                                                                level * 0.06))
        scene.instances("crowd", key, build, matrices, True)
        counts[key] = len(matrices)
    return counts


def place_statues(scene):
    builds = {
        "statue_athlete": lambda: life.bronze_statue("athlete", 1),
        "statue_athlete_b": lambda: life.bronze_statue("athlete", 2, 1.6),
        "statue_draped": lambda: life.bronze_statue("draped", 3),
        "statue_roman": lambda: life.bronze_statue("roman", 4, 1.5, 1.15, "marble"),
        "statue_zeus": lambda: life.bronze_statue("zeus", 5, 1.7, 1.25),
        "statue_equestrian": lambda: life.equestrian(6),
        "niche_statue": lambda: niche_figure(7, False),
        "niche_statue_b": lambda: niche_figure(8, True),
    }
    counts = {}
    for key, matrices in scene.placed.items():
        scene.instances("statues", key, builds[key], matrices, True)
        counts[key] = len(matrices)
    return counts


def niche_figure(seed, female):
    if female:
        look = life.maiden(seed, (0.96, 0.94, 0.90), (0.92, 0.88, 0.80), "hip")
    else:
        look = life.roman(seed, "toga")
    look.material = "marble"
    builder = MeshBuilder()
    builder.box((-0.45, -0.4, 0.0), (0.45, 0.4, 0.35), "marble", bottom=False)
    builder.merge(person(look), Matrix.Translation((0.0, 0.0, 0.35)) @ Matrix.Scale(1.2, 4))
    return builder


def place_camps(scene, tents):
    builds = {f"tent_{k}": (lambda k=k: life.tent(k, 3.0 + (k % 3) * 0.5, 2.3 + (k % 2) * 0.4, 2.0 + (k % 2) * 0.3))
              for k in range(6)}
    builds.update({f"booth_{k}": (lambda k=k: life.booth(k)) for k in range(3)})
    builds["campfire"] = lambda: life.campfire(3)
    builds["horses"] = lambda: life.tethered_horses(4)
    counts = {}
    for key, matrices in tents.items():
        base, quadrant = key.split("@")
        build = builds.get(base) or life.LIFE[base]
        mesh = scene.library.mesh(base, lambda build=build: remap(build()), False)
        group = new_empty(f"group_{base}_q{quadrant}", scene.collection, scene.root("camps"))
        group["cast_shadow"] = True
        for index, matrix in enumerate(matrices):
            created = new_object(f"{base}_q{quadrant}.{index:05d}", mesh, scene.collection, group, matrix)
            created["cast_shadow"] = True
        counts[base] = counts.get(base, 0) + len(matrices)
    return counts


def place_effects(scene, tents):
    root = scene.root("life")
    smokes = [Vector((plan.GREAT_ALTAR.x, plan.GREAT_ALTAR.y, plan.ALTIS_LEVEL + 6.9)),
              Vector((plan.KLADEOS_BATHS.x + 6.0, plan.KLADEOS_BATHS.y - 14.0, plan.ALTIS_LEVEL + 9.0))]
    fires = [matrix for key, matrices in sorted(tents.items()) if key.startswith("campfire@") for matrix in matrices]
    rng = random.Random(5)
    for matrix in rng.sample(fires, min(5, len(fires))):
        p = matrix.translation
        smokes.append(Vector((p.x, p.y, p.z + 1.4)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(Vector((60.0, 300.0)), 110.0), (Vector((-20.0, 60.0)), 62.0), (Vector((-200.0, -300.0)), 48.0),
              (Vector((300.0, 40.0)), 75.0), (Vector((-260.0, 200.0)), 58.0)]
    for index, (point, height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation((point.x, point.y, height)))
    for index, (key, build) in enumerate(life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke": len(smokes), "birds": len(flocks), "walkers": len(life.WALKERS)}


def weather_all(scene):
    done = set()
    for name, root in scene.roots.items():
        if name in ("terrain", "water", "markers", "life", "crowd", "altar", "zeus_lamps"):
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
            aweather.weather(mesh, heights, None, seed, name == "vegetation")
            if name in ("altis", "outer", "stadium") and len(mesh.vertices) < 90000:
                nimes_detail.occlusion(mesh, seed)


def viewpoints(scene, temple_frame):
    points = {}
    points["vue-d-ensemble"] = (Vector((-300.0, -380.0, 110.0)), Vector((30.0, 90.0, 45.0)))
    points["le-temple-de-zeus"] = (Vector((56.0, -46.0, plan.ALTIS_LEVEL + 1.7)),
                                   Vector((10.0, -4.0, plan.ALTIS_LEVEL + 12.0)))
    eye = temple_frame @ Vector((13.6, 1.0, zeus.CELLA_FLOOR + 3.4))
    target = temple_frame @ Vector((-8.5, 0.0, 5.8))
    points["la-statue-de-zeus"] = (eye, target)
    points["le-stade"] = (Vector((183.0, plan.STADIUM_AXIS_Y + 3.0, plan.ARENA_LEVEL + 2.4)),
                          Vector((330.0, plan.STADIUM_AXIS_Y - 2.0, plan.ARENA_LEVEL + 4.0)))
    points["l-altis"] = (Vector((60.0, 10.0, plan.ALTIS_LEVEL + 16.0)), Vector((-10.0, 170.0, plan.ALTIS_LEVEL + 20.0)))
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
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.5, aerosol=0.15)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 5.0, (1.0, 0.86, 0.66), 0.6)
    if options.get("haze", "1") == "1":
        haze_volume(stage, 9000.0, 300.0, 0.000006, (0.86, 0.80, 0.70), 0.25)
    configure_render(1280, 720, options["samples"], exposure=-0.25, volumetric_end=12000.0)
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
    terrain = oterrain.Terrain(CACHE)
    summit = terrain.height(plan.KRONOS.x, plan.KRONOS.y) - plan.ALTIS_LEVEL
    print("FIELDS", round(time.perf_counter() - started, 1), "KRONION", round(summit, 1), flush=True)
    scene = Scene(tiles, terrain)
    temple, temple_frame, apex = build_zeus(scene)
    print("ZEUS", round(time.perf_counter() - started, 1), flush=True)
    build_altis(scene)
    build_zanes(scene)
    print("ALTIS", round(time.perf_counter() - started, 1), flush=True)
    seat, altar = build_stadium(scene)
    build_outer(scene)
    print("OUTER", round(time.perf_counter() - started, 1), flush=True)
    tents, tent_count = build_camps(scene)
    print("MONUMENTS", round(time.perf_counter() - started, 1), flush=True)
    column_counts = place_columns(scene)
    scene.flush({"crypt_floor": False, "zeus_lamps": False})
    build_terrain(scene)
    build_water(scene)
    print("TERRAIN", round(time.perf_counter() - started, 1), flush=True)
    build_surface(scene)
    points = viewpoints(scene, temple_frame)
    place_markers(scene, points)
    route_counts = build_routes(scene)
    eyes = [eye.to_2d() for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    sights = [(points[key][0].to_2d(), points[key][1].to_2d()) for key in ("le-temple-de-zeus", "l-altis")]
    statue_count = statue_forest(scene, eyes + [points["vue-d-ensemble"][0].to_2d()], sights)
    life_counts = populate(scene, eyes, seat, altar)
    crowd_counts = spectators(scene)
    plants = vegetation(scene, eyes, sights)
    plant_counts = place_vegetation(scene, plants)
    statue_counts = place_statues(scene)
    camp_counts = place_camps(scene, tents)
    effects = place_effects(scene, tents)
    print("LIFE", round(time.perf_counter() - started, 1), flush=True)
    weather_all(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "olympie.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION],
        "counts": {"columns": column_counts, "routes": route_counts, "life": life_counts, "crowd": crowd_counts,
                   "plants": plant_counts, "statues": statue_counts, "statue_spots": statue_count,
                   "camps": camp_counts, "camp_items": tent_count, "effects": effects},
        "route_checks": route_report(scene),
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "build_seconds": round(time.perf_counter() - started, 1), "terrain_source": oterrain.SOURCE,
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

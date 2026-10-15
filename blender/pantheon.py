import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector

from kit import pantheon_architecture as arch
from kit import pantheon_city as city
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.life import LEATHER
from kit.nimes_figures import WALKERS, Look, person
from kit.pantheon_materials import build_library, weather
from kit.stage import (camera, configure_render, export_glb, group_statistics, haze_volume, render_still, sun_lamp)

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "pantheon")
BLEND = os.path.join(CACHE, "work", "pantheon.blend")
AXIS = math.radians(5.5)
W = Matrix.Rotation(AXIS, 4, "Z")
LATITUDE = city.ORIGIN[0]
DATE = (129, 4, 21)
SHADOWLESS = {"rotonde_sol", "porche_sol", "place_sol", "ville_eau"}
OCCLUSION_FLOOR = 0.55
OCCLUSION_DECADES = 2.2
BAKED = ("rotonde", "rotonde_sol", "porche", "porche_sol")
P = arch.PIAZZA
F = arch.PORTICO_FLOOR


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 24}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def solar_noon(year, month, day, latitude):
    if month <= 2:
        year -= 1
        month += 12
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + 0.5 - 1524.5
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    centre = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m) + (0.019993 - 0.000101 * t) * math.sin(2 * m)
              + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    longitude = math.radians(l0 + centre - 0.00569 - 0.00478 * math.sin(omega))
    obliquity = 23 + (26 + (21.448 - 46.815 * t - 0.00059 * t * t + 0.001813 * t ** 3) / 60) / 60
    obliquity += 0.00256 * math.cos(omega)
    declination = math.degrees(math.asin(math.sin(math.radians(obliquity)) * math.sin(longitude)))
    return {"julian_day": jd, "declination": round(declination, 3), "obliquity": round(obliquity, 3),
            "elevation": round(90.0 - latitude + declination, 3), "azimuth": 180.0}


class Scene:
    def __init__(self, tiles):
        self.tiles = tiles
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Pantheon")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.statics = {}

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def unique(self, group, builder, matrix=None, occlusion=True):
        if not occlusion:
            builder.heights = [10.0] * len(builder.positions)
        self.pending.setdefault(group, []).append((builder, matrix if matrix is not None else Matrix.Identity(4)))
        self.root(group)

    def flush(self):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(builder, matrix, keep_local=True)
            self.statics[group] = unique_object(f"{group}_static", merged, self.collection, self.root(group), self.tiles,
                                                cast_shadow=group not in SHADOWLESS)
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True, occlusion=True):
        if matrices:
            self.library.place(key, build, self.collection, self.root(group), matrices, cast_shadow, occlusion)

    def add(self, key, matrix):
        self.placements.setdefault(key, []).append(matrix)


def axis(point):
    return W @ Vector(point)


def build_architecture(scene):
    walls, floor, columns, statues, aediculae, small_statues, dome_info = arch.interior()
    scene.unique("rotonde", walls, W)
    scene.unique("rotonde_sol", floor, W, occlusion=False)
    builds = {
        "column_giallo": lambda: arch.roman_column(arch.INNER_D, arch.ORDER_TOP, "giallo", flutes=24),
        "column_pavonazzetto": lambda: arch.roman_column(arch.INNER_D, arch.ORDER_TOP, "pavonazzetto", flutes=24),
        "aedicula_triangular": lambda: arch.aedicula(False, "giallo"),
        "aedicula_segmental": lambda: arch.aedicula(True, "porphyry"),
        "porch_grey": lambda: arch.roman_column(arch.PORCH_D, arch.PORCH_COLUMN, "granite_grey", segments=20),
        "porch_rose": lambda: arch.roman_column(arch.PORCH_D, arch.PORCH_COLUMN, "granite_rose", segments=20),
        "portico_column": lambda: arch.roman_column(arch.PORTICO_D, arch.PORTICO_COLUMN, "granite_grey", detail="low",
                                                    segments=8),
    }
    scene.instances("rotonde", "column_giallo", builds["column_giallo"], [W @ frame for frame in columns["giallo"]])
    scene.instances("rotonde", "column_pavonazzetto", builds["column_pavonazzetto"],
                    [W @ frame for frame in columns["pavonazzetto"]])
    for key, frames in aediculae.items():
        scene.instances("rotonde", key, builds[key], [W @ frame for frame in frames])
    for index, frame in enumerate(statues):
        scene.add("statue_colossal_a" if index % 2 else "statue_colossal_b", W @ frame @ Matrix.Scale(2.25, 4))
    for index, frame in enumerate(small_statues):
        scene.add("statue_small_a" if index % 2 else "statue_small_b", W @ frame @ Matrix.Scale(1.1, 4))
    outside = MeshBuilder()
    arch.exterior_dome(outside)
    scene.unique("exterieur", outside, W)
    porch, porch_floor, porch_columns, porch_statues = arch.porch()
    scene.unique("porche", porch, W)
    scene.unique("porche_sol", porch_floor, W, occlusion=False)
    letters, inscription_info = arch.inscription_builder()
    scene.unique("porche", letters, W, occlusion=False)
    for key, frames in porch_columns.items():
        scene.instances("porche", key, builds[key], [W @ frame for frame in frames])
    for frame in porch_statues:
        scene.add("statue_colossal_a", W @ frame @ Matrix.Scale(2.0, 4))
    square, square_floor, portico_frames = arch.piazza()
    scene.unique("place", square, W)
    scene.unique("place_sol", square_floor, W, occlusion=False)
    scene.instances("place", "portico_column", builds["portico_column"], [W @ frame for frame in portico_frames])
    spots = [(frame.translation.x, frame.translation.y, arch.INNER_D / 2) for frames in columns.values() for frame in frames]
    spots += [(frame.translation.x, frame.translation.y, arch.PORCH_D / 2) for frames in porch_columns.values()
              for frame in frames]
    spots += [(frame.translation.x, frame.translation.y, arch.PORTICO_D / 2) for frame in portico_frames]
    return {"dome": dome_info, "inscription": inscription_info, "portico_columns": len(portico_frames)}, spots


def build_city(scene, rng):
    terrain_root = scene.root("terrain")
    city.terrain(scene.collection, terrain_root, CACHE, new_object)
    scene.unique("ville_eau", city.river(), occlusion=False)
    names = []
    for name, builder, matrix in city.monuments(W):
        scene.unique("ville", builder, matrix)
        names.append(name)
    zones = city.site_zones(AXIS)
    insulae = city.insula_frames(zones, rng)
    for key, frames in insulae.items():
        scene.instances("ville", key, city.INSULAE[key], frames, cast_shadow=True)
    trees = city.tree_frames(zones, rng)
    for key, frames in trees.items():
        scene.instances("vegetation", key, city.TREES[key], frames, cast_shadow=not key.startswith("tree_far"),
                        occlusion=False)
    return insulae, {"monuments": names, "insulae": {key: len(value) for key, value in insulae.items()},
                     "trees": {key: len(value) for key, value in trees.items()}}


def markers():
    niche_eye = arch.polar(9.5, math.radians(60.0), 1.7)
    niche_target = arch.polar(20.6, math.radians(79.0), 5.6)
    local = {
        "le-porche": ((-3.5, 41.0, 1.7), (-6.0, 30.0, 12.0)),
        "la-rotonde": ((0.0, 9.0, 1.7), (0.0, -1.5, arch.OCULUS_HEIGHT)),
        "l-oculus": ((-2.0, 5.0, 1.7), (2.0, 24.0, 4.5)),
        "les-niches": (tuple(niche_eye), tuple(niche_target)),
        "vue-d-ensemble": ((150.0, 265.0, 150.0), (0.0, 30.0, 8.0)),
    }
    return {key: (axis(eye), axis(target)) for key, (eye, target) in local.items()}


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))


def sunbeam(scene, sun):
    elevation = math.radians(sun["elevation"])
    direction = Vector((0.0, math.cos(elevation), -math.sin(elevation)))
    origin = Vector((0.0, 0.0, arch.OCULUS_HEIGHT))
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, location, normal, _, obj, _ = bpy.context.scene.ray_cast(depsgraph, origin + direction * 0.5, direction,
                                                                  distance=200.0)
    run = 1.0 / math.tan(elevation)
    drop = arch.R / run
    analytic = Vector((0.0, arch.R, arch.OCULUS_HEIGHT - drop))
    target = location if hit else analytic
    root = scene.root("markers")
    new_empty("oculus", scene.collection, root, Matrix.Translation(origin))
    new_empty("sunbeam_target", scene.collection, root, Matrix.Translation(target))
    door_axis = axis((0.0, arch.R, 0.0))
    return {"hit": bool(hit), "object": obj.name if hit else None, "target": [round(v, 3) for v in target],
            "normal": [round(v, 3) for v in normal] if hit else None,
            "plain_wall_point": [round(v, 3) for v in analytic],
            "east_of_door_axis_metres": round(analytic.x - door_axis.x, 3),
            "ray_length": round((target - origin).length, 2)}


def resample(points, spacing=2.5):
    out = [Vector(points[0])]
    for start, end in zip(points[:-1], points[1:]):
        a, b = Vector(start), Vector(end)
        count = max(int(math.ceil((b - a).length / spacing)), 1)
        for k in range(1, count + 1):
            out.append(a.lerp(b, k / count))
    return out


def routes():
    steps = [(0.0, 47.1 - arch.STEP_TREAD * (j - 1), P + arch.STEP_RISE * j) for j in range(1, 7)]
    arc = [tuple(arch.polar(17.0, math.radians(a), 0.0)) for a in list(range(105, 336, 10)) + [25, 35]]
    return {
        "place-ouest": [(-18.0, 58.0, P), (-18.0, 158.0, P)],
        "place-est": [(17.0, 156.0, P), (17.0, 60.0, P)],
        "place-diagonale": [(-25.0, 150.0, P), (-2.0, 72.0, P)],
        "portique-ouest": [(-34.6, 34.0, F), (-34.6, 168.6, F), (-20.0, 168.6, F)],
        "portique-est": [(34.6, 34.0, F), (34.6, 168.6, F), (20.0, 168.6, F)],
        "entree": [(0.0, 82.0, P), (0.0, 47.6, P)] + steps + [(0.0, arch.PORCH_EDGE, 0.0), (0.0, 36.0, 0.0),
                                                               (0.6, 30.9, 0.0), (0.6, 24.0, 0.0), (0.0, 12.0, 0.0)],
        "place-centre": [(-9.0, 150.0, P), (-9.0, 100.0, P), (8.0, 64.0, P)],
        "porche-ouest": [(-8.9, 32.6, 0.0), (-8.9, 44.9, 0.0)],
        "rotonde": arc,
    }


def place_routes(scene, spots):
    root = scene.root("life")
    lengths = {}
    for name, points in routes().items():
        sampled = resample(points)
        for point in sampled:
            for x, y, radius in spots:
                if math.hypot(point.x - x, point.y - y) < radius + 0.6:
                    raise ValueError(f"route {name} passes {math.hypot(point.x - x, point.y - y):.2f} m from column {x:.2f} {y:.2f}")
        for index, point in enumerate(sampled):
            new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(axis(point)))
        lengths[name] = len(sampled)
    return lengths


CROWD = {
    "fig_toga": Look("white", hem=0.12, skin=0, hair=0, toga="white", arms="toga", scale=0.95, seed=101),
    "fig_toga_gesture": Look("white", hem=0.12, skin=1, hair=2, toga="white", arms="toga_gesture", carry="scroll",
                             scale=0.95, seed=102),
    "fig_toga_praetexta": Look("white", hem=0.12, skin=0, hair=3, toga="white", praetexta="purple", arms="toga",
                               scale=0.95, seed=103),
    "fig_matron": Look("woad", hem=0.03, skin=0, hair=0, palla="rose", veil=True, female=True, sleeves="long", arms="hip",
                       scale=0.9, seed=104),
    "fig_matron_madder": Look("weld", hem=0.03, skin=1, hair=1, palla="madder", veil=True, female=True, sleeves="long",
                              arms="down", scale=0.9, seed=105),
    "fig_woman": Look("rose", hem=0.04, skin=1, hair=1, palla="green", female=True, sleeves="long", arms="down",
                      scale=0.9, seed=106),
    "fig_basket": Look("madder", hem=0.04, skin=2, hair=0, palla="undyed", female=True, sleeves="long", arms="head",
                       carry="basket", scale=0.9, seed=107),
    "fig_child": Look("white", hem=0.5, skin=0, hair=1, scale=0.62, belt="madder", stripe="madder", child=True, seed=108),
    "fig_girl": Look("weld", hem=0.05, skin=1, hair=1, female=True, sleeves="long", child=True, scale=0.66, seed=109),
    "fig_worker": Look("ochre", hem=0.55, skin=2, hair=1, belt=LEATHER, arms="down", hat=(0.8, 0.68, 0.42), scale=0.95,
                       seed=110),
    "fig_merchant": Look("grey", hem=0.55, skin=1, hair=0, apron="undyed", arms="gesture", belt="brown", scale=0.95,
                         seed=111),
    "fig_elder": Look("undyed", hem=0.12, skin=0, hair=2, cloak="brown", carry="staff", arms="staff", scale=0.94,
                      seed=112),
}
FESTIVE = [("fig_toga", 3), ("fig_toga_gesture", 1.5), ("fig_toga_praetexta", 0.6), ("fig_matron", 2),
           ("fig_matron_madder", 1.5), ("fig_woman", 2), ("fig_basket", 0.8), ("fig_child", 1.2), ("fig_girl", 1),
           ("fig_worker", 1.2), ("fig_merchant", 0.6), ("fig_elder", 0.8)]
STATUES = {
    "statue_colossal_a": Look("white", hem=0.12, toga="white", arms="toga_gesture", mono=(0.97, 0.95, 0.91),
                              material="marble_white", seed=131),
    "statue_colossal_b": Look("white", hem=0.03, palla="white", veil=True, female=True, sleeves="long", arms="hip",
                              mono=(0.97, 0.95, 0.91), material="marble_white", seed=132),
    "statue_small_a": Look("white", hem=0.12, toga="white", arms="toga", mono=(0.96, 0.94, 0.9), material="marble_white",
                           seed=133),
    "statue_small_b": Look("white", hem=0.03, palla="white", female=True, sleeves="long", arms="down",
                           mono=(0.96, 0.94, 0.9), material="marble_white", seed=134),
}


def pick(rng, weights):
    total = sum(weight for _, weight in weights)
    roll = rng.random() * total
    for key, weight in weights:
        roll -= weight
        if roll <= 0:
            return key
    return weights[-1][0]


def segment_distance(point, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy) / max(dx * dx + dy * dy, 1e-9)))
    return math.hypot(point[0] - ax - t * dx, point[1] - ay - t * dy)


def crowd_area(scene, rng, count, sample, z_of, clear, face=None, cluster=(1, 4)):
    placed = 0
    attempts = 0
    while placed < count and attempts < count * 60:
        attempts += 1
        x, y = sample()
        if not clear(x, y):
            continue
        size = int(rng.integers(cluster[0], cluster[1] + 1))
        heading = face(x, y) if face is not None else rng.uniform(0, 2 * math.pi)
        for member in range(size):
            angle = 2 * math.pi * member / size + rng.uniform(-0.3, 0.3)
            radius = rng.uniform(0.55, 0.9) if size > 1 else 0.0
            px, py = x + radius * math.cos(angle), y + radius * math.sin(angle)
            if not clear(px, py):
                continue
            turn = math.atan2(-(x - px), y - py) if size > 1 else heading
            scene.add(pick(rng, FESTIVE), W @ placement(px, py, z_of(px, py), turn + rng.uniform(-0.35, 0.35)))
            placed += 1
    return placed


def build_life(scene, rng, points):
    lines = [((eye.x, eye.y), (target.x, target.y)) for eye, target in
             ((W.inverted() @ eye, W.inverted() @ target) for key, (eye, target) in points.items()
              if key in ("le-porche", "la-rotonde", "les-niches"))]
    eyes = [(eye.x, eye.y) for eye in (W.inverted() @ value[0] for value in points.values())]
    cones = [((eye.x, eye.y), math.atan2(target.y - eye.y, target.x - eye.x)) for eye, target in
             ((W.inverted() @ value[0], W.inverted() @ value[1]) for value in points.values())]
    route_lines = [points_list for points_list in routes().values()]

    def open_space(x, y, width=1.6):
        if any(segment_distance((x, y), a, b) < width for a, b in lines):
            return False
        if any(math.hypot(x - ex, y - ey) < 3.0 for ex, ey in eyes):
            return False
        for (ex, ey), heading in cones:
            if math.hypot(x - ex, y - ey) < 10.0 and abs(math.remainder(math.atan2(y - ey, x - ex) - heading,
                                                                       2 * math.pi)) < math.radians(30.0):
                return False
        for line in route_lines:
            for a, b in zip(line[:-1], line[1:]):
                if segment_distance((x, y), a[:2], b[:2]) < 0.9:
                    return False
        return True
    porch_columns = [(x, y) for x in arch.FRONT_X for y in (arch.ROWS[0],)] + [(x, y) for x in arch.INNER_X
                                                                               for y in arch.ROWS[1:]]
    counts = {}
    counts["place"] = crowd_area(scene, rng, 110, lambda: (rng.uniform(-27.0, 27.0), rng.uniform(50.0, 160.0)),
                                 lambda x, y: P, open_space,
                                 lambda x, y: math.atan2(x, 44.0 - y) + rng.uniform(-1.2, 1.2),
                                 (1, 5))
    counts["portiques"] = crowd_area(scene, rng, 18, lambda: (float(rng.choice([-1, 1])) * rng.uniform(33.2, 36.8),
                                                              rng.uniform(36.0, 160.0)), lambda x, y: F, open_space)
    counts["porche"] = crowd_area(
        scene, rng, 22, lambda: (rng.uniform(-15.5, 15.5), rng.uniform(32.6, 44.6)), lambda x, y: 0.0,
        lambda x, y: open_space(x, y) and min(math.hypot(x - cx, y - cy) for cx, cy in porch_columns) > 1.25
        and not (abs(abs(x) - 11.125) < 2.4 and y < 33.0), None, (1, 3))
    stair = 0
    for j in (2, 4, 5):
        for _ in range(2):
            x = rng.uniform(-14.0, 14.0)
            if abs(x) < 1.2 or min(abs(x - column) for column in arch.FRONT_X) < 0.5:
                continue
            y = 47.1 - arch.STEP_TREAD * (j - 1) - 0.15
            scene.add(pick(rng, FESTIVE), W @ placement(x, y, P + arch.STEP_RISE * j, math.pi + rng.uniform(-0.4, 0.4)))
            stair += 1
    counts["marches"] = stair

    def rotunda_sample():
        radius = math.sqrt(rng.uniform(4.0 ** 2, 17.0 ** 2))
        angle = rng.uniform(0, 2 * math.pi)
        return radius * math.sin(angle), radius * math.cos(angle)
    counts["rotonde"] = crowd_area(scene, rng, 32, rotunda_sample, lambda x, y: 0.0,
                                   lambda x, y: open_space(x, y) and math.hypot(x, y) < 17.5,
                                   lambda x, y: math.atan2(x, -y) + rng.uniform(-0.8, 0.8), (1, 3))
    for x, y in ((1.8, 26.0), (-1.2, 27.5), (2.9, 23.0)):
        scene.add(pick(rng, FESTIVE), W @ placement(x, y, 0.0, math.pi + rng.uniform(-0.5, 0.5)))
    counts["passage"] = 3
    builds = {key: (lambda spec=spec: person(spec)) for key, spec in {**CROWD, **STATUES}.items()}
    placed = {}
    for key, matrices in scene.placements.items():
        group = "statues" if key.startswith("statue") else "foule"
        scene.instances(group, key, builds[key], matrices, cast_shadow=True, occlusion=key.startswith("statue"))
        placed[key] = len(matrices)
    root = scene.root("life")
    for index, (key, spec) in enumerate(WALKERS.items()):
        mesh = scene.library.mesh(key, lambda spec=spec: person(spec), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    triangles = {key: scene.library.builders[key].triangle_count() for key in list(CROWD)[:3] + list(WALKERS)[:2]
                 if key in scene.library.builders}
    return counts, placed, triangles


def place_atmosphere(scene, insulae, rng):
    root = scene.root("life")
    smokes = city.smoke_points(insulae, rng)
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    px, py = city.SITES["stagnum"]
    mx, my = city.SITES["mausoleum_augusti"]
    flocks = [Vector((0.0, 0.0, 78.0)), axis((0.0, 110.0, 38.0)), Vector((px, py, 32.0)), Vector((mx, my, 70.0)),
              axis((0.0, -90.0, 45.0))]
    for index, point in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation(point))
    return len(smokes), len(flocks)


def weathering(scene):
    settings = {"exterieur": (0.14, 0.18), "porche": (0.08, 0.12), "place": (0.1, 0.16), "ville": (0.16, 0.0),
                "rotonde": (0.05, 0.0), "place_sol": (0.07, 0.0), "porche_sol": (0.06, 0.0)}
    for group, (strength, grime) in settings.items():
        if group in scene.statics:
            weather(scene.statics[group], strength, seed=len(group), scale=6.0, grime=grime, ground=P)


def smoothed(obj, values, cell=0.9):
    mesh = obj.data
    vertex_index = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex_index)
    coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coordinates)
    cells = np.floor(coordinates.reshape(-1, 3)[vertex_index] / cell).astype(np.int64) + 4096
    keys = (cells[:, 0] * 8192 + cells[:, 1]) * 8192 + cells[:, 2]
    unique, inverse = np.unique(keys, return_inverse=True)
    sums = np.bincount(inverse, weights=values, minlength=len(unique))
    counts = np.bincount(inverse, minlength=len(unique)).astype(np.float64)
    total = np.zeros(len(values))
    weight = np.zeros(len(values))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                probe = keys + (dx * 8192 + dy) * 8192 + dz
                position = np.clip(np.searchsorted(unique, probe), 0, len(unique) - 1)
                found = unique[position] == probe
                total += np.where(found, sums[position], 0.0)
                weight += np.where(found, counts[position], 0.0)
    return total / np.maximum(weight, 1.0)


def bake_occlusion(scene, names, samples=16, distance=60.0):
    context = bpy.context
    previous = context.scene.render.engine
    context.scene.render.engine = "CYCLES"
    context.scene.cycles.samples = samples
    context.scene.cycles.device = "CPU"
    context.scene.cycles.use_adaptive_sampling = False
    if context.scene.world is None:
        context.scene.world = bpy.data.worlds.new("Bake")
    context.scene.world.light_settings.distance = distance
    report = {}
    for name in names:
        obj = scene.statics[name]
        mesh = obj.data
        target = mesh.color_attributes.new("AO", "FLOAT_COLOR", "CORNER")
        mesh.color_attributes.active_color = target
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
        values = np.empty(len(mesh.loops) * 4, dtype=np.float32)
        mesh.color_attributes["AO"].data.foreach_get("color", values)
        occlusion = smoothed(obj, values.reshape(-1, 4)[:, 0])
        factor = np.clip(OCCLUSION_FLOOR + (1.0 - OCCLUSION_FLOOR) * (np.log10(occlusion + 1e-3) + 3.0) / OCCLUSION_DECADES,
                         OCCLUSION_FLOOR, 1.0)
        colours = np.empty(len(mesh.loops) * 4, dtype=np.float32)
        base = mesh.color_attributes["Col"]
        base.data.foreach_get("color_srgb", colours)
        colours = colours.reshape(-1, 4)
        colours[:, :3] *= factor[:, None]
        base.data.foreach_set("color_srgb", np.clip(colours, 0, 1).ravel())
        mesh.color_attributes.remove(mesh.color_attributes["AO"])
        mesh.color_attributes.active_color = mesh.color_attributes["Col"]
        report[name] = {"loops": len(occlusion), "percentiles": [round(float(v), 4) for v in
                                                                 np.percentile(occlusion, (5, 25, 50, 75, 95))]}
        print("BAKE", name, json.dumps(report[name]), flush=True)
    context.scene.render.engine = previous
    return report


def dust(stage):
    mesh = bpy.data.meshes.new("Dust")
    builder_vertices = []
    faces = []
    segments = 32
    for k in range(segments):
        angle = 2 * math.pi * k / segments
        builder_vertices.append((arch.R * math.cos(angle), arch.R * math.sin(angle), 0.05))
        builder_vertices.append((arch.R * math.cos(angle), arch.R * math.sin(angle), 42.5))
    for k in range(segments):
        a, b = 2 * k, 2 * ((k + 1) % segments)
        faces.append((a, b, b + 1, a + 1))
    faces.append(tuple(2 * k for k in reversed(range(segments))))
    faces.append(tuple(2 * k + 1 for k in range(segments)))
    mesh.from_pydata(builder_vertices, [], faces)
    material = bpy.data.materials.new("Dust")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Density"].default_value = float(os.environ.get("DUST", "0.003"))
    volume.inputs["Color"].default_value = (1.0, 0.92, 0.8, 1.0)
    volume.inputs["Anisotropy"].default_value = 0.35
    material.node_tree.links.new(volume.outputs[0], nodes["Material Output"].inputs["Volume"])
    mesh.materials.append(material)
    return new_object("Dust", mesh, stage)


def noon_world(sun, strength, saturation):
    world = bpy.data.worlds.new("NoonSky")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.sun_threshold = 0.0
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    background = nodes["Background"]
    sky = nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(sun["elevation"])
    sky.sun_rotation = math.radians(sun["azimuth"]) % math.tau
    sky.sun_disc = False
    sky.altitude = 60.0
    sky.aerosol_density = 0.8
    links.new(sky.outputs["Color"], background.inputs["Color"])
    background.inputs["Strength"].default_value = strength
    grey = nodes.new("ShaderNodeHueSaturation")
    grey.inputs["Saturation"].default_value = saturation
    links.new(sky.outputs["Color"], grey.inputs["Color"])
    lighting = nodes.new("ShaderNodeBackground")
    lighting.name = "Lighting"
    links.new(grey.outputs["Color"], lighting.inputs["Color"])
    lighting.inputs["Strength"].default_value = strength
    path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    links.new(lighting.outputs["Background"], mix.inputs[1])
    links.new(background.outputs["Background"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["World Output"].inputs["Surface"])
    return world


def render_previews(options, views, sun):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(views) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    world = noon_world(sun, float(options.get("sky", 0.05)), float(options.get("saturation", 0.55)))
    sun_lamp(stage, sun["azimuth"], sun["elevation"], float(options.get("sun", 5.5)), (1.0, 0.97, 0.92), 0.53)
    haze_volume(stage, 6000.0, 500.0, 0.000025, (0.80, 0.86, 0.95), 0.35)
    room = dust(stage)
    configure_render(1280, 720, options["samples"], exposure=0.0, volumetric_end=6000.0)
    gloom = float(options.get("inside_sky", 0.3))
    settings = {"aerial": (30.0, 0.0, False, 1.0), "porche": (16.0, 0.6, False, 1.0), "place": (22.0, 0.0, False, 1.0),
                "facade": (24.0, 0.0, False, 1.0), "rotonde": (17.0, 0.9, True, 1.0), "oculus": (20.0, 0.9, True, gloom),
                "niches": (20.0, 0.9, True, 0.7), "abside": (15.0, 0.9, True, 0.7),
                "entree": (22.0, 0.9, True, gloom), "porte": (22.0, 0.3, True, 1.0)}
    timings = {}
    for name in names:
        eye, target = views[name]
        lens, exposure, inside, sky = settings[name]
        room.hide_render = not inside
        world.node_tree.nodes["Lighting"].inputs["Strength"].default_value = float(options.get("sky", 0.05)) * sky
        bpy.context.scene.view_settings.exposure = exposure + float(options.get("exposure", 0.0))
        bpy.context.scene.eevee.use_raytracing = True
        bpy.context.scene.eevee.taa_render_samples = options["samples"] * (3 if inside else 1)
        rig = camera(stage, f"cam_{name}", eye, target, lens=lens)
        rig.data.clip_start = 0.1 if inside else rig.data.clip_start
        path = os.path.join(CACHE, "previews", f"{name}.png")
        timings[name] = round(render_still(rig, path), 1)
        print(f"PREVIEW {name} {timings[name]} s", flush=True)
    return timings


def preview_views(points):
    views = {
        "aerial": points["vue-d-ensemble"],
        "porche": points["le-porche"],
        "rotonde": points["la-rotonde"],
        "oculus": points["l-oculus"],
        "niches": points["les-niches"],
        "place": (axis((-14.0, 70.0, P + 1.7)), axis((4.0, 36.0, 9.0))),
        "entree": (axis((-1.0, 6.0, 1.7)), axis((-1.0, 30.0, 5.0))),
        "porte": (axis((0.5, 26.0, 1.7)), axis((0.5, 60.0, 4.0))),
        "facade": (axis((5.0, 96.0, P + 1.7)), axis((0.0, 44.0, 16.5))),
        "abside": (axis((4.0, 15.0, 1.7)), axis((-3.0, -21.0, 13.5))),
    }
    return views


def main():
    options = arguments()
    sun = solar_noon(*DATE, LATITUDE)
    if options.get("reuse") == "1":
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        stored = json.loads(bpy.context.scene.get("preview_points", "{}"))
        views = {key: (Vector(eye), Vector(target)) for key, (eye, target) in stored.items()}
        print("PREVIEWS", json.dumps(render_previews(options, views, sun)), flush=True)
        return
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tiles, credits = build_library(CACHE)
    scene = Scene(tiles)
    rng = np.random.default_rng(129)
    info, spots = build_architecture(scene)
    insulae, city_counts = build_city(scene, rng)
    scene.flush()
    weathering(scene)
    baked = bake_occlusion(scene, BAKED, int(options.get("bake", 1024)))
    points = markers()
    place_markers(scene, points)
    beam = sunbeam(scene, sun)
    route_counts = place_routes(scene, spots)
    life_counts, placed, triangles = build_life(scene, rng, points)
    smoke_count, flock_count = place_atmosphere(scene, insulae, rng)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "pantheon.glb")
    export_seconds = export_glb(glb, roots)
    report = {"sun": sun, "sunbeam": beam, "architecture": info, "occlusion": baked, "city": city_counts, "routes": route_counts,
              "life": {"areas": life_counts, "instances": placed, "figure_triangles": triangles, "smoke": smoke_count,
                       "flocks": flock_count, "walkers": list(WALKERS)},
              "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
              "texture_credits": credits,
              "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                          for key, (eye, target) in points.items()}}
    views = preview_views(points)
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)] for key, (eye, target) in views.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    report["previews"] = render_previews(options, views, sun)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("sun", "sunbeam", "glb_bytes", "previews", "total_seconds")}),
          flush=True)


if __name__ == "__main__":
    main()

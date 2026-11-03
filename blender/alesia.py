import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix

from kit.alesia_figures import TROOPS
from kit.alesia_terrain import (SOURCE, Relief, build_far_ground, build_ground, build_rivers, grid_sampler,
                                prepare_ground)
from kit.alesia_works import (CAMPS, CIRCONVALLATION, CONTREVALLATION, LEATHER_TENT, Line, Painter, agger, camp_tents,
                              east_camp, hut, oppidum_gates, oppidum_huts, oppidum_wall, plateau_rim,
                              relief_camp, retranchements, shelter, tower, tower_matrices, trap_matrices,
                              trap_patch, water_ditch)
from kit.cannes_camps import tent
from kit.geometry import MATTE, MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, \
    unique_object
from kit.materials import principled_material
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, render_still,
                       sun_lamp, triangles_of)
from kit.terrain import GeoFrame

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "alesia")
ORIGIN = (47.5366, 4.5039)
EXTENT = (-6510.0, 4500.0, -4500.0, 4500.0)
SPACING = 30.0
FAR_HALF = 20000.0
FAR_SPACING = 300.0
TEMPLATE_DEPTH = -1000.0
PLAIN_WATER_LEVEL = 243.0
TREE_SPACING = 26.0
TREE_LIMIT = 9000
SUN = (230.0, 26.0)


def options():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    result = {"previews": "all", "samples": 12}
    for item in argv:
        key, _, value = item.partition("=")
        result[key] = int(value) if value.isdigit() else value
    return result


def tree():
    builder = MeshBuilder()
    first = len(builder.polygons)
    builder.lathe([(0.4, -0.5), (4.0, 5.0), (0.0, 10.5)], 5, MATTE, smooth=True, caps=False)
    builder.tint(first, (0.24, 0.31, 0.15))
    return builder


def tree_matrices(texture, height_at, avoid, seed=23):
    tx, ty, woods = texture
    rng = np.random.default_rng(seed)
    xs = np.arange(tx[0] + 10, tx[-1] - 10, TREE_SPACING)
    ys = np.arange(ty[-1] + 10, ty[0] - 10, TREE_SPACING)
    gx, gy = np.meshgrid(xs, ys)
    gx = gx + rng.uniform(-9, 9, gx.shape)
    gy = gy + rng.uniform(-9, 9, gy.shape)
    column = np.clip(np.rint((gx - tx[0]) / (tx[-1] - tx[0]) * (len(tx) - 1)).astype(int), 0, len(tx) - 1)
    row = np.clip(np.rint((ty[0] - gy) / (ty[0] - ty[-1]) * (len(ty) - 1)).astype(int), 0, len(ty) - 1)
    density = woods[row, column]
    keep = (density > 0.5) & (rng.random(gx.shape) < density * 0.9)
    points = np.column_stack([gx[keep], gy[keep]])
    points = points[[not avoid(x, y) for x, y in points]]
    if len(points) > TREE_LIMIT:
        points = points[rng.choice(len(points), TREE_LIMIT, replace=False)]
    return [placement(x, y, height_at(x, y) - 0.3, rng.uniform(0, math.tau), rng.uniform(0.75, 1.3))
            for x, y in points]


def build_troops(collection, parent):
    group = new_empty("troops", collection, parent)
    report = {}
    for kind, (near, far) in TROOPS.items():
        for suffix, build in (("", near), ("_far", far)):
            name = f"troop_{kind}{suffix}"
            created = unique_object(name, build(), collection, group, {}, ground_occlusion=False)
            created.location.z = TEMPLATE_DEPTH
            report[name] = triangles_of(created.data)
    return report


def build_works(lines, height_at, collection, parent, library):
    rim = plateau_rim(height_at)
    gates = oppidum_gates(rim)
    walls = MeshBuilder()
    for line in lines.values():
        walls.merge(agger(line, height_at))
    walls.merge(retranchements(lines, height_at))
    walls.merge(oppidum_wall(rim, height_at, gates))
    east_wall, east_shelters, east_curve = east_camp(rim, height_at)
    walls.merge(east_wall)
    relief_bank, relief_shelters, relief_ring = relief_camp(height_at)
    walls.merge(relief_bank)
    unique_object("fortifications", walls, collection, parent, {}, ground_occlusion=False)
    towers = [matrix for line in lines.values() for matrix in tower_matrices(line, height_at)]
    library.place("tour", tower, collection, parent, towers, cast_shadow=False, ground_occlusion=False)
    library.place("tente_romaine", lambda: tent().tint(0, LEATHER_TENT), collection, parent, camp_tents(height_at),
                  cast_shadow=False, ground_occlusion=False)
    library.place("abri_gaulois", shelter, collection, parent, east_shelters + relief_shelters, cast_shadow=False,
                  ground_occlusion=False)
    huts = oppidum_huts(rim, height_at)
    library.place("maison_gauloise", hut, collection, parent, huts, cast_shadow=False, ground_occlusion=False)
    traps = trap_matrices(lines, height_at)
    library.place("pieges", trap_patch, collection, parent, traps, cast_shadow=False, ground_occlusion=False)
    water = water_ditch(lines["contrevallation"], height_at, PLAIN_WATER_LEVEL)
    return {"rim": rim, "gates": gates, "east_curve": east_curve, "relief_ring": relief_ring, "water": water,
            "counts": {"towers": len(towers), "huts": len(huts), "shelters": len(east_shelters) + len(relief_shelters),
                       "trap_patches": len(traps), "water_quads": len(water[1])}}


def lineup(collection, height_at):
    shown = []
    x0, y0 = -2620.0, 120.0
    for row, suffix in enumerate(("", "_far")):
        for index, kind in enumerate(TROOPS):
            if kind == "armee":
                continue
            source = bpy.data.objects[f"troop_{kind}{suffix}"]
            copy = new_object(f"preview_{kind}{suffix}", source.data, collection)
            x, y = x0 + index * 3.0, y0 + row * 6.0
            copy.matrix_world = Matrix.Translation((x, y, height_at(x, y))) @ Matrix.Rotation(math.radians(180), 4, "Z")
            shown.append(copy)
    return shown


def render_previews(settings, views, height_at):
    if settings["previews"] == "none":
        return {}
    stage = ensure_collection("Stage")
    evening_world(*SUN, 0.35, aerosol=0.6)
    sun_lamp(stage, *SUN, 4.0, (1.0, 0.94, 0.84), 0.6)
    lineup(stage, height_at)
    configure_render(int(settings.get("width", 1280)), int(settings.get("height", 720)), settings["samples"])
    view = bpy.context.scene.view_settings
    view.view_transform = "Khronos PBR Neutral"
    view.look = "None"
    wanted = list(views) if settings["previews"] == "all" else settings["previews"].split(",")
    timings = {}
    for name in wanted:
        eye, target, lens = views[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=lens, clip_end=90000.0)
        timings[name] = round(render_still(rig, os.path.join(CACHE, "previews", f"{name}.png")), 1)
        print(f"PREVIEW {name} {timings[name]} s", flush=True)
    return timings


def main():
    settings = options()
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    principled_material("matte", color=(1.0, 1.0, 1.0), roughness=0.88)
    frame = GeoFrame(*ORIGIN)
    relief = Relief(frame, CACHE)
    collection = ensure_collection("Alesia")
    root = new_empty("alesia", collection)
    xs, ys, heights, rivers, river_distance = prepare_ground(relief, EXTENT, SPACING)
    print("TERRAIN", round(time.perf_counter() - started, 1), "s", len(rivers), "rivers", flush=True)
    height_at = grid_sampler(xs, ys, heights)
    lines = {"contrevallation": Line("contrevallation", CONTREVALLATION, True),
             "circonvallation": Line("circonvallation", CIRCONVALLATION, False)}
    library = TemplateLibrary({})
    works = build_works(lines, height_at, collection, root, library)
    print("WORKS", round(time.perf_counter() - started, 1), "s", flush=True)
    painter = Painter(lines, works["rim"], works["east_curve"], works["relief_ring"])
    texture_path = os.path.join(CACHE, "work", "alesia_ground.jpg")
    ground, texture = build_ground(xs, ys, heights, river_distance, EXTENT, texture_path, [painter], collection,
                                   new_object)
    ground.parent = root
    print("GROUND", round(time.perf_counter() - started, 1), "s", flush=True)
    build_far_ground(relief, EXTENT, FAR_HALF, FAR_SPACING, collection, new_object).parent = root
    build_rivers(rivers, works["water"], collection, new_object).parent = root
    def avoid(x, y):
        for line in lines.values():
            distance = np.min(np.hypot(line.path[:, 0] - x, line.path[:, 1] - y))
            if distance < 60.0:
                return True
        return False

    trees = tree_matrices(texture, height_at, avoid)
    library.place("arbre", tree, collection, root, trees, cast_shadow=False, ground_occlusion=False)
    troops = build_troops(collection, root)
    statistics = group_statistics([root])
    glb = os.path.join(CACHE, "alesia.glb")
    export_seconds = export_glb(glb, [root])
    views = {
        "ouverture": ((-7600.0, -1200.0, 1350.0), (-200.0, 300.0, 300.0), 32.0),
        "vue_tactique": ((-300.0, -7600.0, 7300.0), (-300.0, 0.0, 250.0), 35.0),
        "plaine": ((-2630.0, -330.0, height_at(-2630.0, -330.0) + 9.0), (-2950.0, -120.0, 236.0), 30.0),
        "rea": ((-1950.0, 1250.0, height_at(-1950.0, 1250.0) + 60.0), (-2450.0, 1800.0, 300.0), 32.0),
        "oppidum": ((1200.0, -1300.0, 560.0), (0.0, 150.0, 390.0), 32.0),
        "figurines": ((-2607.0, 104.0, height_at(-2607.0, 104.0) + 2.6), (-2607.0, 123.0, height_at(-2607.0, 123.0) + 0.9),
                      32.0),
    }
    timings = render_previews(settings, views, height_at)
    report = {
        "origin": ORIGIN,
        "extent": EXTENT,
        "relief": SOURCE,
        "relief_urls": relief.urls,
        "height_range": [float(heights.min()), float(heights.max())],
        "rivers": [{"start": river.path[0].tolist(), "end": river.path[-1].tolist(), "points": len(river.path),
                    "width": [float(river.width.min()), float(river.width.max())]} for river in rivers],
        "line_lengths": {name: line.length for name, line in lines.items()},
        "camps": {name: {"centre": camp["centre"], "size": camp["size"],
                         "height": height_at(*camp["centre"])} for name, camp in CAMPS.items()},
        "oppidum_rim_points": len(works["rim"]),
        "works": works["counts"],
        "trees": len(trees),
        "troop_triangles": troops,
        "statistics": statistics,
        "export_seconds": export_seconds,
        "preview_seconds": timings,
        "total_seconds": time.perf_counter() - started,
        "glb_bytes": os.path.getsize(glb),
    }
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1, ensure_ascii=False)
    print("REPORT", json.dumps({key: report[key] for key in ("height_range", "line_lengths", "glb_bytes",
                                                             "total_seconds", "works", "trees")}), flush=True)
    print("TROOPS", json.dumps(troops), flush=True)


if __name__ == "__main__":
    main()

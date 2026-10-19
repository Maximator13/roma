import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np

from kit.cannes_camps import CAMPS, citadel, rampart, tent, tent_rows
from kit.cannes_figures import TROOPS
from kit.cannes_terrain import (TINITALY_LICENCE, Relief, River, build_far_ground, build_ground, build_water)
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, unique_object
from kit.materials import principled_material
from kit.stage import export_glb, group_statistics, triangles_of
from kit.terrain import GeoFrame

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "cannes")
DEM_CACHE = os.path.join(PROJECT, ".cache", "geo", "tinitaly-cannes.tif")
ORIGIN = (41.3150, 16.1950)
CANNAE = (41.2967, 16.1518)
EXTENT = (-5400.0, 3800.0, -3600.0, 3200.0)
SPACING = 25.0
FAR_HALF = 16000.0
FAR_SPACING = 400.0
RIVER_WIDTH = 34.0
RIVER_DEPTH = 1.6
RIVER_COURSE = [(-6200, -3150), (-5400, -2750), (-4600, -2250), (-4150, -1850), (-3800, -1450), (-3450, -1050),
                (-2900, -760), (-2450, -430), (-2000, -180), (-1800, 150), (-1650, 480), (-1200, 720), (-950, 1050),
                (-650, 1380), (-250, 1600), (300, 2000), (900, 2550), (1500, 3100), (2100, 3700), (2700, 4300)]
TEMPLATE_DEPTH = -1000.0


def grid_sampler(xs, ys, heights):
    def height_at(x, y):
        column = min(max((x - xs[0]) / (xs[1] - xs[0]), 0.0), len(xs) - 1.001)
        row = min(max((y - ys[0]) / (ys[1] - ys[0]), 0.0), len(ys) - 1.001)
        c0, r0 = int(column), int(row)
        fx, fy = column - c0, row - r0
        top = heights[r0, c0] * (1 - fx) + heights[r0, c0 + 1] * fx
        bottom = heights[r0 + 1, c0] * (1 - fx) + heights[r0 + 1, c0 + 1] * fx
        return float(top * (1 - fy) + bottom * fy)
    return height_at


def build_camps(collection, parent, library, height_at):
    for name, camp in CAMPS.items():
        works = MeshBuilder()
        rampart(works, camp["centre"], camp["size"], camp["angle"], height_at)
        unique_object(name, works, collection, parent, {}, ground_occlusion=False)
        matrices = tent_rows(camp["centre"], camp["size"], camp["angle"], camp["spacing"], 24.0, height_at,
                             seed=len(name), jitter=camp["jitter"], fill=camp["fill"])
        colour = camp["colour"]
        library.place(f"tent_{name}", lambda colour=colour: tent().tint(0, colour), collection, parent, matrices,
                      cast_shadow=False, ground_occlusion=False)


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


def main():
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    principled_material("matte", color=(1.0, 1.0, 1.0), roughness=0.88)
    frame = GeoFrame(*ORIGIN)
    relief = Relief(frame, DEM_CACHE)
    river = River(RIVER_COURSE, relief, RIVER_WIDTH, RIVER_DEPTH)
    collection = ensure_collection("Cannes")
    root = new_empty("cannes", collection)
    texture_path = os.path.join(CACHE, "work", "cannes_ground.jpg")
    ground, heights, xs, ys = build_ground(relief, river, EXTENT, SPACING, texture_path, collection, new_object)
    ground.parent = root
    build_far_ground(relief, EXTENT, FAR_HALF, FAR_SPACING, collection, new_object).parent = root
    for water in build_water(river, FAR_HALF, collection, new_object):
        water.parent = root
    height_at = grid_sampler(xs, ys, heights)
    library = TemplateLibrary({})
    build_camps(collection, root, library, height_at)
    cannae = frame.to_local(*CANNAE)
    unique_object("cannae", citadel(cannae, height_at), collection, root, {}, ground_occlusion=False)
    troops = build_troops(collection, root)
    statistics = group_statistics([root])
    glb = os.path.join(CACHE, "cannes.glb")
    export_seconds = export_glb(glb, [root])
    report = {
        "origin": ORIGIN,
        "cannae_local": cannae,
        "extent": EXTENT,
        "relief": TINITALY_LICENCE,
        "height_range": [float(heights.min()), float(heights.max())],
        "river_level_range": [float(river.level.min()), float(river.level.max())],
        "troop_triangles": troops,
        "statistics": statistics,
        "export_seconds": export_seconds,
        "total_seconds": time.perf_counter() - started,
        "glb_bytes": os.path.getsize(glb),
    }
    with open(os.path.join(CACHE, "report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("cannae_local", "height_range", "river_level_range",
                                                             "glb_bytes", "total_seconds")}), flush=True)
    print("TROOPS", json.dumps(troops), flush=True)


if __name__ == "__main__":
    main()

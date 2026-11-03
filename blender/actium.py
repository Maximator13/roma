import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
from mathutils import Matrix

from kit.actium_ships import SPECS, TROOPS
from kit.actium_sites import APOLLO, CAMPS, STRAIT_TOWERS, temple, tower
from kit.actium_terrain import SEA_SURFACE, SOURCE, Relief, build_far_ground, build_ground, build_sea
from kit.cannes_camps import LEATHER_TENT, rampart, tent, tent_rows
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, unique_object
from kit.materials import principled_material
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, render_still,
                       sun_lamp, triangles_of)
from kit.terrain import GeoFrame

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "actium")
ORIGIN = (38.950, 20.758)
EXTENT = (-9000.0, 6000.0, -6000.0, 10000.0)
SPACING = 30.0
FAR_HALF = 22000.0
FAR_SPACING = 250.0
SEA_HALF = 40000.0
TEMPLATE_DEPTH = -1000.0
SUN = (130.0, 49.0)


def options():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    result = {"previews": "all", "samples": 16}
    for item in argv:
        key, _, value = item.partition("=")
        result[key] = int(value) if value.isdigit() else value
    return result


def build_sites(collection, parent, library, relief):
    placed = {}
    for name, camp in CAMPS.items():
        centre = relief.nearest_land(*camp["anchor"])
        works = MeshBuilder()
        rampart(works, centre, camp["size"], camp["angle"], relief.height_at)
        unique_object(name, works, collection, parent, {}, ground_occlusion=False)
        matrices = tent_rows(centre, camp["size"], camp["angle"], camp["spacing"], 24.0, relief.height_at,
                             seed=len(name), jitter=0.0, fill=camp["fill"])
        library.place(f"tent_{name}", lambda: tent().tint(0, LEATHER_TENT), collection, parent, matrices,
                      cast_shadow=False, ground_occlusion=False)
        placed[name] = centre
    for index, anchor in enumerate(STRAIT_TOWERS):
        x, y = relief.nearest_land(*anchor, radius=300.0)
        unique_object(f"tour_detroit_{index}", tower(x, y, relief.height_at(x, y)), collection, parent, {},
                      ground_occlusion=False)
        placed[f"tour_detroit_{index}"] = (x, y)
    x, y = relief.nearest_land(*APOLLO, radius=500.0, highest=True)
    unique_object("sanctuaire_apollon", temple(x, y, relief.height_at(x, y), 0.35), collection, parent, {},
                  ground_occlusion=False)
    placed["sanctuaire_apollon"] = (x, y)
    return placed


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


def lineup(collection):
    shown = []
    kinds = list(SPECS)
    for row, suffix in enumerate(("", "_far")):
        for index, kind in enumerate(kinds):
            source = bpy.data.objects[f"troop_{kind}{suffix}"]
            copy = new_object(f"preview_{kind}{suffix}", source.data, collection)
            copy.matrix_world = Matrix.Translation((-3600.0 + index * 45.0, -2500.0 - row * 100.0, SEA_SURFACE)) \
                @ Matrix.Rotation(math.radians(35), 4, "Z")
            shown.append(copy)
    return shown


def render_previews(settings, views):
    if settings["previews"] == "none":
        return {}
    stage = ensure_collection("Stage")
    evening_world(*SUN, 0.35, aerosol=0.6)
    sun_lamp(stage, *SUN, 4.0, (1.0, 0.94, 0.84), 0.6)
    lineup(stage)
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
    collection = ensure_collection("Actium")
    root = new_empty("actium", collection)
    texture_path = os.path.join(CACHE, "work", "actium_ground.png")
    ground, heights, land = build_ground(relief, EXTENT, SPACING, texture_path, collection, new_object)
    ground.parent = root
    build_far_ground(relief, EXTENT, FAR_HALF, FAR_SPACING, collection, new_object).parent = root
    build_sea(relief, EXTENT, SEA_HALF, collection, new_object).parent = root
    library = TemplateLibrary({})
    sites = build_sites(collection, root, library, relief)
    troops = build_troops(collection, root)
    statistics = group_statistics([root])
    glb = os.path.join(CACHE, "actium.glb")
    export_seconds = export_glb(glb, [root])
    camp = sites["camp_octavien"]
    views = {
        "aube_sur_le_detroit": ((camp[0] + 300.0, camp[1] - 1500.0, 650.0), (-600.0, -1500.0, 0.0), 30.0),
        "le_detroit": ((-2600.0, -2600.0, 260.0), (250.0, 700.0, 0.0), 40.0),
        "vue_tactique": ((-2400.0, -9000.0, 5200.0), (-2000.0, -2000.0, 0.0), 35.0),
        "maquettes": ((-3465.0, -2330.0, 14.0), (-3465.0, -2540.0, 3.0), 28.0),
        "decere": ((-3575.0, -2440.0, 6.0), (-3600.0, -2500.0, 3.5), 28.0),
        "liburne": ((-3350.0, -2468.0, 3.5), (-3330.0, -2500.0, 1.5), 28.0),
        "maquettes_haut": ((-3465.0, -2380.0, 170.0), (-3465.0, -2560.0, 0.0), 28.0),
        "camp_octavien": ((camp[0] - 900.0, camp[1] - 900.0, 420.0), (camp[0], camp[1], 60.0), 35.0),
        "apollon": ((sites["sanctuaire_apollon"][0] - 260.0, sites["sanctuaire_apollon"][1] - 200.0, 70.0),
                    (*sites["sanctuaire_apollon"], 5.0), 40.0),
    }
    timings = render_previews(settings, views)
    report = {
        "origin": ORIGIN,
        "extent": EXTENT,
        "relief": SOURCE,
        "land_height_range": [float(heights[land].min()), float(heights[land].max())],
        "sea_surface": SEA_SURFACE,
        "sites": sites,
        "troop_triangles": troops,
        "statistics": statistics,
        "export_seconds": export_seconds,
        "preview_seconds": timings,
        "total_seconds": time.perf_counter() - started,
        "glb_bytes": os.path.getsize(glb),
    }
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("land_height_range", "glb_bytes", "total_seconds")}),
          flush=True)
    print("TROOPS", json.dumps(troops), flush=True)


if __name__ == "__main__":
    main()

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

from kit.cannes_figures import TROOPS
from kit.geometry import TemplateLibrary, ensure_collection, new_empty, new_object, placement
from kit.materials import principled_material
from kit.stage import camera, configure_render, evening_world, haze_volume, render_still, sun_lamp

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(PROJECT, ".cache", "cards", "renders")
WIDTH = 960
HEIGHT = 1344
SAMPLES = int(os.environ.get("CARD_SAMPLES", "64"))


def block(kind, columns, rows, spacing_x, spacing_y, origin=(0.0, 0.0), facing=0.0, jitter=0.12, seed=1):
    generator = random.Random(seed)
    matrices = []
    for row in range(rows):
        for column in range(columns):
            x = origin[0] + (column - (columns - 1) / 2) * spacing_x + generator.uniform(-jitter, jitter)
            y = origin[1] - row * spacing_y + generator.uniform(-jitter, jitter)
            turn = facing + generator.uniform(-0.12, 0.12)
            matrices.append(placement(x, y, 0.0, turn))
    return kind, matrices


def scatter(kind, count, width, depth, origin=(0.0, 0.0), facing=0.0, seed=1):
    generator = random.Random(seed)
    matrices = []
    for _ in range(count):
        x = origin[0] + generator.uniform(-width / 2, width / 2)
        y = origin[1] - generator.uniform(0.0, depth)
        matrices.append(placement(x, y, 0.0, facing + generator.uniform(-0.35, 0.35)))
    return kind, matrices


VIGNETTES = {
    "velites": {
        "groups": [scatter("velite", 26, 11.0, 12.0, origin=(0.0, -1.0), seed=3)],
        "camera": ((0.6, 3.4, 1.05), (-0.2, -3.0, 1.35), 34.0),
        "sun": (55.0, 16.0),
    },
    "hastats": {
        "groups": [block("hastatus", 9, 7, 1.0, 1.35, seed=4), block("princeps", 9, 6, 1.0, 1.35, origin=(0.0, -14.0), seed=5)],
        "camera": ((2.2, 2.4, 1.5), (-0.6, -4.0, 1.4), 30.0),
        "sun": (40.0, 18.0),
    },
    "triaires": {
        "groups": [block("triarius", 7, 5, 1.05, 1.4, seed=6)],
        "camera": ((1.8, 2.2, 0.9), (-0.3, -3.0, 2.0), 28.0),
        "sun": (60.0, 12.0),
    },
    "cavaliers-numides": {
        "groups": [scatter("numide", 11, 9.0, 16.0, origin=(0.0, -1.5), facing=0.35, seed=7)],
        "camera": ((1.2, 4.2, 1.1), (-0.4, -5.0, 1.9), 32.0),
        "sun": (70.0, 14.0),
    },
    "cannes": {
        "groups": [
            block("hastatus", 24, 8, 1.0, 1.3, origin=(-6.0, -6.0), seed=8),
            block("velite", 18, 2, 1.8, 2.0, origin=(-6.0, 0.0), seed=9),
            block("celte", 22, 6, 1.1, 1.3, origin=(-4.0, -22.0), facing=math.pi, seed=10),
            block("ibere", 12, 6, 1.1, 1.3, origin=(18.0, -24.0), facing=math.pi, seed=11),
        ],
        "camera": ((14.0, 12.0, 7.5), (-6.0, -14.0, 1.0), 30.0),
        "sun": (200.0, 9.0),
        "haze": True,
    },
}


def ground(collection):
    mesh = bpy.data.meshes.new("Ground")
    size = 1500.0
    mesh.from_pydata([(-size, -size, 0.0), (size, -size, 0.0), (size, size, 0.0), (-size, size, 0.0)], [], [(0, 1, 2, 3)])
    material = principled_material("ground", color=(0.50, 0.40, 0.24), roughness=0.95, vertex_color=False)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 8.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.30, 0.27, 0.13, 1.0)
    ramp.color_ramp.elements[1].color = (0.62, 0.48, 0.28, 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    mesh.materials.append(material)
    return new_object("Ground", mesh, collection)


def render(name, setup):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    principled_material("matte", color=(1.0, 1.0, 1.0), roughness=0.85)
    collection = ensure_collection("Card")
    root = new_empty("card", collection)
    ground(collection)
    library = TemplateLibrary({})
    for kind, matrices in setup["groups"]:
        near = TROOPS[kind][0]
        library.place(kind, near, collection, root, matrices, ground_occlusion=False)
    azimuth, elevation = setup["sun"]
    evening_world(azimuth, elevation, 0.14, aerosol=0.8)
    sun_lamp(collection, azimuth, elevation, 6.5, (1.0, 0.74, 0.48), angle_degrees=1.0)
    if setup.get("haze"):
        haze_volume(collection, 300.0, 40.0, 0.0012, (1.0, 0.78, 0.5), 1.5)
    configure_render(WIDTH, HEIGHT, SAMPLES, exposure=0.0, volumetric_end=400.0 if setup.get("haze") else 0.0)
    location, target, lens = setup["camera"]
    rig = camera(collection, f"camera_{name}", location, target, lens=lens, clip_end=4000.0)
    seconds = render_still(rig, os.path.join(OUTPUT, f"{name}.png"))
    print("RENDERED", name, round(seconds, 1), flush=True)


def main():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = values or list(VIGNETTES)
    for name in names:
        render(name, VIGNETTES[name])


if __name__ == "__main__":
    main()

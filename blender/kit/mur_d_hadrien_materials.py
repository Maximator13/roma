import os

import bpy
import numpy as np

from .gizeh_materials import blocks
from .materials import generated_image, linear_color, principled_material
from .olympie_materials import tile_pixels
from .pont_materials import height_normal, periodic_noise

VERSION = "v5"
TILES = {"sandstone": 1.8, "ashlar": 3.0, "roof_slab": 3.0, "terracotta_tiles": 3.2, "ground_turf": 3.0,
         "ground_vallum": 4.0, "timber": 2.0}
PLAIN = {
    "matte": dict(color=(1.0, 1.0, 1.0), roughness=0.86),
    "water": dict(color=(0.06, 0.12, 0.13), roughness=0.08),
    "iron": dict(color=(0.55, 0.56, 0.58), roughness=0.38, metallic=0.85),
    "shadow_void": dict(color=(0.05, 0.045, 0.04), roughness=1.0),
}
RENAME = {"weathered_ashlar": "sandstone", "lens_ashlar": "ashlar", "stone": "sandstone", "limestone": "sandstone",
          "roof_tiles": "terracotta_tiles", "roof_flat": "terracotta_tiles", "plank_wood": "timber",
          "dark_wood": "timber", "bark": "timber", "garden_green": "ground_turf", "paving": "ashlar",
          "plaster": "sandstone", "plaster_white": "sandstone", "plaster_ochre": "sandstone"}


def remap(builder):
    builder.materials = [RENAME.get(name, name) for name in builder.materials]
    merged = []
    index_of = {}
    remapped = []
    for name in builder.materials:
        if name not in index_of:
            index_of[name] = len(merged)
            merged.append(name)
        remapped.append(index_of[name])
    builder.polygon_materials = [remapped[index] for index in builder.polygon_materials]
    builder.materials = merged
    return builder


def masonry_pixels(size, courses, lengths, base, seed, mortar_width=2.0, tone_spread=0.045):
    rng = np.random.default_rng(seed)
    index, edge, count = blocks(size, courses, lengths, seed, 1.0)
    tones = rng.normal(1.0, tone_spread, count)
    warm = rng.normal(0.02, 0.025, count)
    grain = periodic_noise(size, 1.1, seed + 1)
    speck = rng.random((size, size))
    colour = np.array(base)[None, None, :] * (tones[index] * (0.88 + 0.18 * grain) * (0.96 + 0.06 * speck))[..., None]
    colour[..., 0] *= 1.0 + warm[index]
    colour[..., 2] *= 1.0 - warm[index]
    face = np.clip(edge / 6.0, 0.0, 1.0)
    joint = edge < mortar_width
    mortar = np.array([0.70, 0.66, 0.56]) * (0.9 + 0.1 * grain)[..., None]
    colour = np.where(joint[..., None], mortar, colour * (0.86 + 0.14 * face)[..., None])
    lichen = np.clip((periodic_noise(size, 1.6, seed + 2) - 0.7) * 4.0, 0, 1) * 0.12
    colour = colour * (1 - lichen[..., None]) + np.array([0.66, 0.68, 0.52]) * lichen[..., None]
    height = np.where(joint, 0.0, 0.4 + 0.6 * face) + 0.1 * grain
    return np.clip(colour, 0, 1), height_normal(height, 4.0)


def facing_pixels(size=1024, seed=31):
    return masonry_pixels(size, 12, (80, 170), (0.72, 0.65, 0.53), seed)


def ashlar_pixels(size=1024, seed=37):
    return masonry_pixels(size, 6, (180, 380), (0.79, 0.72, 0.60), seed, 2.5, 0.05)


def slab_pixels(size=512, seed=41):
    rng = np.random.default_rng(seed)
    index, edge, count = blocks(size, 9, (30, 80), seed, 1.0)
    tones = rng.normal(1.0, 0.1, count)
    grain = periodic_noise(size, 1.3, seed + 1)
    base = np.array([0.50, 0.48, 0.44])
    colour = base[None, None, :] * (tones[index] * (0.85 + 0.25 * grain))[..., None]
    rows = np.linspace(0, 9, size, endpoint=False)[:, None] % 1.0
    overlap = np.clip(1.0 - rows / 0.12, 0, 1)
    colour *= (1.0 - 0.35 * overlap)[..., None]
    colour *= np.where(edge < 1.5, 0.6, 1.0)[..., None]
    moss = np.clip((periodic_noise(size, 1.8, seed + 3) - 0.62) * 3.0, 0, 1)
    colour = colour * (1 - 0.5 * moss[..., None]) + np.array([0.46, 0.50, 0.24]) * 0.5 * moss[..., None]
    return np.clip(colour, 0, 1)


def turf_pixels(size=512, seed=43):
    grain = periodic_noise(size, 0.9, seed)
    blades = periodic_noise(size, 0.4, seed + 1, stretch=(0.3, 1.0))
    patches = periodic_noise(size, 1.8, seed + 2)
    green = np.array([0.40, 0.48, 0.20])
    straw = np.array([0.66, 0.62, 0.34])
    colour = green[None, None, :] * (1 - patches[..., None] * 0.5) + straw[None, None, :] * patches[..., None] * 0.5
    colour *= (0.8 + 0.3 * grain * blades)[..., None]
    return np.clip(colour, 0, 1)


def vallum_pixels(size=512, seed=47):
    grain = periodic_noise(size, 0.8, seed)
    clods = periodic_noise(size, 1.4, seed + 1)
    turf = turf_pixels(size, seed + 2)
    earth = np.array([0.56, 0.46, 0.34])[None, None, :] * (0.8 + 0.35 * grain)[..., None]
    weight = np.clip((clods - 0.2) * 2.0, 0, 1)[..., None]
    return np.clip(turf * weight + earth * (1 - weight), 0, 1)


def timber_pixels(size=256, seed=53):
    v = periodic_noise(size, 1.2, seed, stretch=(0.08, 2.0))
    planks = (np.arange(size)[None, :] % (size // 8)) < 2
    colour = np.array([0.56, 0.42, 0.28])[None, None, :] * (0.8 + 0.3 * v)[..., None]
    colour = np.where(planks[..., None], colour * 0.6, colour)
    return np.clip(colour, 0, 1)


def build_library(cache_dir):
    folder = os.path.join(cache_dir, "textures")
    os.makedirs(folder, exist_ok=True)
    tiles = dict(TILES)
    pairs = {"sandstone": (facing_pixels, 0.86, 0.8), "ashlar": (ashlar_pixels, 0.8, 0.7)}
    for name, (build, roughness, strength) in pairs.items():
        cache = {}

        def pair(build=build, cache=cache):
            if "value" not in cache:
                cache["value"] = build()
            return cache["value"]
        colour = generated_image(name, os.path.join(folder, f"{name}_{VERSION}.jpg"), lambda: pair()[0])
        normal = generated_image(f"{name}_normal", os.path.join(folder, f"{name}_normal_{VERSION}.jpg"),
                                 lambda: pair()[1][::2, ::2], colorspace="Non-Color", quality=95)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, colour, normal, strength)
    singles = {"roof_slab": (slab_pixels, 0.82), "ground_turf": (turf_pixels, 0.95),
               "ground_vallum": (vallum_pixels, 0.95), "timber": (timber_pixels, 0.8),
               "terracotta_tiles": (lambda: tile_pixels((0.76, 0.36, 0.20)), 0.74)}
    for name, (build, roughness) in singles.items():
        image = generated_image(name, os.path.join(folder, f"{name}_{VERSION}.jpg"), build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, image)
    for name, spec in PLAIN.items():
        color = spec["color"] if name in ("matte", "water") else linear_color(spec["color"])
        principled_material(name, color, spec["roughness"], spec.get("metallic", 0.0), vertex_color=name != "water")
        tiles[name] = 2.0
    return tiles, {"textures": "generated procedurally for this scene, no external source"}

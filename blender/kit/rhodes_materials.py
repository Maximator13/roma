import math
import os

import numpy as np

from . import alexandrie_materials
from .materials import generated_image, linear_color, principled_material
from .pont_materials import height_normal, periodic_noise
from .terrain import value_noise

RENAME = dict(alexandrie_materials.RENAME)
RENAME.update({"bronze": "bronze_statue", "col_bronze_patina": "bronze_statue", "lens_smooth": "marble",
               "weathered_ashlar": "limestone", "lens_ashlar": "limestone", "travertine": "limestone",
               "marble_white": "marble", "stucco": "stucco", "brick": "plaster"})


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


def clean_roof_pixels(size=512, seed=9):
    u = (np.arange(size) + 0.5) / size
    channels = 6
    phase = (u * channels) % 1.0
    imbrex = np.clip(1.0 - np.abs(phase - 0.82) / 0.13, 0, 1)
    gutter = np.clip(1.0 - np.abs(phase - 0.6) / 0.08, 0, 1)
    v = (np.arange(size) + 0.5) / size
    course = (v * 5) % 1.0
    lip = np.clip(1.0 - course / 0.06, 0, 1)
    rng = np.random.default_rng(seed)
    tile_tone = rng.uniform(0.84, 1.14, (5, channels))
    tone = tile_tone[(v * 5).astype(int) % 5][:, (u * channels).astype(int) % channels]
    shade = (1.0 + 0.2 * np.sqrt(imbrex)[None, :] - 0.3 * gutter[None, :]) * (1.0 - 0.25 * lip[:, None]) * tone
    base = np.array([0.80, 0.40, 0.24])
    grain = value_noise((size, size), 24, seed + 1, 3)
    colour = base[None, None, :] * (shade * (0.9 + 0.2 * grain))[..., None]
    lichen = np.clip((value_noise((size, size), 7, seed + 4, 3) - 0.62) * 4.0, 0, 1) * (1.0 - imbrex[None, :] * 0.6)
    colour = colour * (1 - 0.35 * lichen[..., None]) + np.array([0.62, 0.58, 0.40]) * 0.35 * lichen[..., None]
    dirt = np.clip(gutter[None, :] * 0.6 + lip[:, None] * 0.3, 0, 1)
    colour *= (1.0 - 0.25 * dirt)[..., None]
    return np.clip(colour, 0, 1)


def wave_noise(size, count, low, high, seed, stretch=1.0):
    rng = np.random.default_rng(seed)
    u = np.arange(size) / size
    gu, gv = np.meshgrid(u, u)
    field = np.zeros((size, size))
    for k in range(count):
        fx = int(rng.integers(low, high + 1)) * rng.choice((-1, 1))
        fy = int(round(rng.integers(low, high + 1) * stretch)) * rng.choice((-1, 1))
        amplitude = 1.0 / max(1.0, math.hypot(fx, fy)) ** 0.8
        field += amplitude * np.sin(2 * math.pi * (fx * gu + fy * gv) + rng.uniform(0, 2 * math.pi))
    field -= field.min()
    return field / max(field.max(), 1e-9)


def fbm(size, seed, octaves, stretch=(1.0, 1.0)):
    field = np.zeros((size, size))
    total = 0.0
    for k, beta in enumerate(octaves):
        weight = 0.6 ** k
        field += weight * periodic_noise(size, beta, seed + 17 * k, stretch)
        total += weight
    return field / total


def blend(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + np.asarray(other) * weight


def patina_pixels(size=1024, seed=5):
    broad = fbm(size, seed, (1.8, 1.4))
    mid = fbm(size, seed + 1, (1.3, 1.0, 0.8))
    fine = periodic_noise(size, 0.6, seed + 2)
    runoff = fbm(size, seed + 3, (1.4, 1.0), (1.0, 6.0))
    colour = np.array([0.26, 0.17, 0.09])[None, None, :] * (0.85 + 0.3 * fine)[..., None]
    colour = blend(colour, np.array([0.34, 0.21, 0.10]), np.clip((mid - 0.56) * 4.0, 0, 1) * 0.6)
    colour = blend(colour, np.array([0.14, 0.22, 0.16]), np.clip((broad - 0.46) * 3.5, 0, 1) * 0.85)
    colour = blend(colour, np.array([0.22, 0.36, 0.28]), np.clip((mid * 0.5 + broad * 0.5 - 0.56) * 4.0, 0, 1) * 0.7)
    streaks = np.clip((runoff - 0.6) * 4.5, 0, 1) * (0.55 + 0.45 * np.clip((broad - 0.35) * 3.0, 0, 1))
    colour = blend(colour, np.array([0.38, 0.58, 0.48]) * (0.9 + 0.2 * fine)[..., None], streaks * 0.85)
    speck = np.clip((fine - 0.78) * 6.0, 0, 1) * np.clip((mid - 0.45) * 4.0, 0, 1)
    colour = blend(colour, np.array([0.46, 0.64, 0.54]), speck * 0.6)
    return np.clip(colour, 0, 1)


def patina_normal(size=1024, seed=5):
    pits = periodic_noise(size, 0.5, seed + 7)
    dents = periodic_noise(size, 1.8, seed + 8)
    return height_normal(pits * 0.6 + dents * 3.0, 2.5)


def rust_pixels(size=256, seed=11):
    broad = wave_noise(size, 30, 1, 6, seed)
    fine = wave_noise(size, 60, 8, 30, seed + 1)
    orange = np.array([0.46, 0.22, 0.10])
    dark = np.array([0.18, 0.10, 0.07])
    t = np.clip(broad * 1.2 - 0.15, 0, 1)
    colour = dark[None, None, :] * (1 - t[..., None]) + orange[None, None, :] * t[..., None]
    return np.clip(colour * (0.8 + 0.4 * fine)[..., None], 0, 1)


def stucco_pixels(size=512, seed=13):
    broad = periodic_noise(size, 1.5, seed)
    fine = periodic_noise(size, 0.5, seed + 1)
    base = np.array([0.96, 0.93, 0.86])
    colour = base[None, None, :] * (0.94 + 0.06 * broad + 0.04 * fine)[..., None]
    return np.clip(colour, 0, 1)


def build_library(cache_dir):
    tiles, credits = alexandrie_materials.build_library(cache_dir)
    texture_dir = os.path.join(cache_dir, "textures")
    roof = generated_image("rhodes_roof", os.path.join(texture_dir, "rhodes_roof_v1.jpg"), clean_roof_pixels)
    principled_material("terracotta_tiles", (0.8, 0.8, 0.8), 0.74, 0.0, roof)
    tiles["terracotta_tiles"] = 3.2
    patina = generated_image("bronze_patina", os.path.join(texture_dir, "bronze_patina_v5.jpg"), patina_pixels)
    bumps = generated_image("bronze_patina_normal", os.path.join(texture_dir, "bronze_patina_normal_v3.jpg"),
                            patina_normal, colorspace="Non-Color")
    principled_material("bronze_patina", (0.8, 0.8, 0.8), 0.55, 0.25, patina, bumps, 0.7)
    principled_material("ballast_stone", (1.0, 1.0, 1.0), 0.9, 0.0)
    tiles["bronze_patina"] = 6.0
    principled_material("bronze_statue", (0.8, 0.8, 0.8), 0.5, 0.45, patina, bumps, 0.4)
    tiles["bronze_statue"] = 0.9
    rust = generated_image("iron_rust", os.path.join(texture_dir, "iron_rust_v2.jpg"), rust_pixels)
    principled_material("iron_rust", (0.8, 0.8, 0.8), 0.85, 0.2, rust)
    tiles["iron_rust"] = 1.0
    stucco = generated_image("stucco", os.path.join(texture_dir, "rhodes_stucco_v1.jpg"), stucco_pixels)
    principled_material("stucco", (0.8, 0.8, 0.8), 0.7, 0.0, stucco)
    tiles["stucco"] = 4.0
    principled_material("bronze_gilt", linear_color((0.95, 0.72, 0.30)), 0.3, 1.0)
    return tiles, credits

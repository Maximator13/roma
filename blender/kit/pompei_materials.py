import math
import os

import numpy as np

from .materials import (generated_image, linear_color, poly_haven_asset, principled_material, recolored,
                        smooth_stone_pixels)
from .terrain import value_noise

TEXTURED = {
    "plaster": dict(asset="plastered_wall", color=(0.95, 0.92, 0.86), contrast=0.32, roughness=0.9, normal=0.0,
                    tile=2.4),
    "stone": dict(asset="sandstone_blocks_08", color=(0.66, 0.62, 0.55), contrast=0.5, roughness=0.85, normal=0.0),
    "sidewalk": dict(asset="rock_embedded_floor", color=(0.55, 0.52, 0.47), contrast=0.5, roughness=0.92,
                     normal=0.0, tile=2.5),
    "paving": dict(asset="rectangular_paving", color=(0.86, 0.83, 0.77), contrast=0.5, roughness=0.8, normal=0.0,
                   tile=7.0),
}
PLAIN = {
    "matte": dict(color=(1.0, 1.0, 1.0), roughness=0.88),
    "water": dict(color=(0.10, 0.20, 0.24), roughness=0.08),
    "bronze": dict(color=(0.24, 0.20, 0.13), roughness=0.45, metallic=0.85),
    "shadow_void": dict(color=(0.05, 0.045, 0.04), roughness=1.0),
}
RENAME = {"weathered_ashlar": "stone", "lens_ashlar": "stone", "lens_smooth": "marble", "lens_fluted": "marble",
          "frieze_rinceau": "marble", "roof_flat": "terracotta_tiles", "roof_tiles": "terracotta_tiles",
          "bronze_gilt": "bronze", "arena_sand": "sidewalk", "velum_linen": "matte", "plank_wood": "matte",
          "arles_stone": "stone", "dark_wood": "matte", "paving_stone": "paving"}
PUMICE = np.array([0.74, 0.72, 0.66])
POMPEIAN_RED = np.array([0.60, 0.13, 0.09])
CINNABAR = np.array([0.70, 0.16, 0.10])
OCHRE = np.array([0.82, 0.62, 0.24])
BLACK = np.array([0.07, 0.065, 0.06])
CREAM = np.array([0.90, 0.86, 0.76])


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


def lapilli(size, density, seed, small=1.2, large=3.2):
    rng = np.random.default_rng(seed)
    cover = np.zeros((size, size))
    count = int(size * size * density / (math.pi * ((small + large) / 2) ** 2))
    xs = rng.uniform(0, size, count)
    ys = rng.uniform(0, size, count)
    radii = rng.uniform(small, large, count)
    tones = rng.uniform(0.75, 1.0, count)
    reach = int(math.ceil(large)) + 1
    offsets = np.arange(-reach, reach + 1)
    for x, y, r, tone in zip(xs, ys, radii, tones):
        rows = (int(y) + offsets) % size
        columns = (int(x) + offsets) % size
        dy = (int(y) + offsets - y)[:, None]
        dx = (int(x) + offsets - x)[None, :]
        blob = np.clip(1.2 - np.hypot(dx * 0.9, dy * 1.1) / r, 0, 1) * tone
        block = cover[np.ix_(rows, columns)]
        cover[np.ix_(rows, columns)] = np.maximum(block, blob)
    return cover


def voronoi_cells(size, cells, seed):
    rng = np.random.default_rng(seed)
    points = rng.uniform(0, size, (cells, 2))
    tiled = np.concatenate([points + np.array([dx, dy]) * size for dx in (-1, 0, 1) for dy in (-1, 0, 1)])
    axis = np.arange(size) + 0.5
    gx, gy = np.meshgrid(axis, axis)
    first = np.full((size, size), np.inf)
    second = np.full((size, size), np.inf)
    owner = np.zeros((size, size), dtype=int)
    for index, (px, py) in enumerate(tiled):
        distance = np.hypot(gx - px, gy - py)
        closer = distance < first
        second = np.where(closer, first, np.minimum(second, distance))
        owner = np.where(closer, index % cells, owner)
        first = np.where(closer, distance, first)
    return owner, second - first


def basalt_pixels(size=512, seed=5):
    owner, edge = voronoi_cells(size, 70, seed)
    rng = np.random.default_rng(seed)
    tone = rng.uniform(0.82, 1.12, 70)[owner]
    grain = value_noise((size, size), 40, seed + 1, 3)
    base = np.array([0.33, 0.33, 0.31])
    colour = base[None, None, :] * (tone * (0.86 + 0.28 * grain))[..., None]
    joint = np.clip(1.0 - edge / 5.0, 0, 1)
    colour *= (1.0 - 0.55 * joint)[..., None]
    v = (np.arange(size) + 0.5) / size
    rut = np.zeros(size)
    for centre in (0.5 - 0.152, 0.5 + 0.152):
        rut = np.maximum(rut, np.clip(1.0 - np.abs(v - centre) / 0.03, 0, 1))
    polish = rut[None, :]
    colour = colour * (1.0 - 0.25 * polish)[..., None] + np.array([0.05, 0.05, 0.05]) * polish[..., None]
    edges = np.clip(1.0 - np.minimum(v, 1 - v) / 0.16, 0, 1)[None, :]
    drift = value_noise((size, size), 6, seed + 2, 3)
    pile = np.clip((edges * 0.45 + drift * 0.5 - 0.45) * 2.0, 0, 1)
    cover = np.maximum(lapilli(size, 0.12, seed + 3, 1.0, 2.6) * 0.85, pile * (0.7 + 0.2 * grain))
    cover = np.maximum(cover, joint * 0.45 * (drift > 0.5))
    pumice = PUMICE[None, None, :] * (0.88 + 0.16 * grain)[..., None]
    return np.clip(colour * (1 - cover[..., None]) + pumice * cover[..., None], 0, 1)


def roof_pixels(size=512, seed=9):
    u = (np.arange(size) + 0.5) / size
    channels = 6
    phase = (u * channels) % 1.0
    imbrex = np.clip(1.0 - np.abs(phase - 0.82) / 0.13, 0, 1)
    gutter = np.clip(1.0 - np.abs(phase - 0.6) / 0.08, 0, 1)
    v = (np.arange(size) + 0.5) / size
    course = (v * 5) % 1.0
    lip = np.clip(1.0 - course / 0.06, 0, 1)
    rng = np.random.default_rng(seed)
    tile_tone = rng.uniform(0.85, 1.12, (5, channels))
    tone = tile_tone[(v * 5).astype(int) % 5][:, (u * channels).astype(int) % channels]
    shade = (1.0 + 0.16 * np.sqrt(imbrex)[None, :] - 0.25 * gutter[None, :]) * (1.0 - 0.22 * lip[:, None]) * tone
    base = np.array([0.66, 0.36, 0.24])
    grain = value_noise((size, size), 24, seed + 1, 3)
    colour = base[None, None, :] * (shade * (0.9 + 0.2 * grain))[..., None]
    drift = value_noise((size, size), 5, seed + 2, 3)
    settled = np.clip(gutter[None, :] * 0.8 + lip[:, None] * 0.5 + (drift - 0.55) * 1.4, 0, 1)
    cover = np.maximum(lapilli(size, 0.16, seed + 3, 0.9, 2.4) * 0.9, settled * (0.6 + 0.25 * grain))
    cover *= np.clip(1.0 - imbrex[None, :] * 0.6, 0, 1)
    pumice = PUMICE[None, None, :] * (0.85 + 0.2 * grain)[..., None]
    return np.clip(colour * (1 - cover[..., None]) + pumice * cover[..., None], 0, 1)


def rect(image, x0, y0, x1, y1, colour, width, height):
    c0, c1 = int(x0 * width), int(x1 * width)
    r0, r1 = int(y0 * height), int(y1 * height)
    image[r0:r1, c0:c1] = colour


def frame_lines(image, x0, y0, x1, y1, colour, thickness, width, height):
    t = thickness
    rect(image, x0, y0, x1, y0 + t, colour, width, height)
    rect(image, x0, y1 - t, x1, y1, colour, width, height)
    rect(image, x0, y0, x0 + t * height / width, y1, colour, width, height)
    rect(image, x1 - t * height / width, y0, x1, y1, colour, width, height)


def vignette(image, cx, cy, radius, seed, width, height):
    rng = np.random.default_rng(seed)
    gx, gy = np.meshgrid((np.arange(width) + 0.5) / width, (np.arange(height) + 0.5) / height)
    for _ in range(3):
        ox, oy = rng.uniform(-0.4, 0.4) * radius, rng.uniform(-0.3, 0.6) * radius
        shape = np.hypot((gx - cx - ox) / (radius * 0.35 * width / height), (gy - cy - oy) / (radius * 0.9)) < 1.0
        image[shape] = rng.choice([CREAM, OCHRE, np.array([0.30, 0.42, 0.40]), np.array([0.85, 0.70, 0.55])])


def fresco_pixels(width=1024, height=1024, seed=13):
    image = np.zeros((height, width, 3))
    z = (np.arange(height) + 0.5) / height
    image[:] = CREAM
    dado = z < 0.22
    marble = value_noise((height, width), 10, seed, 4)
    veins = np.abs(np.sin(marble * 30.0))
    image[dado] = (BLACK * 0.6 + np.array([0.20, 0.10, 0.08]) * 0.4)
    splash = dado[:, None] & (veins < 0.18)
    image[splash] = np.array([0.55, 0.35, 0.22])
    rect(image, 0.0, 0.215, 1.0, 0.235, OCHRE * 0.8, width, height)
    for index, (x0, x1, colour) in enumerate(((0.0, 0.08, BLACK), (0.08, 0.42, POMPEIAN_RED), (0.42, 0.58, BLACK),
                                              (0.58, 0.92, CINNABAR), (0.92, 1.0, BLACK))):
        rect(image, x0, 0.235, x1, 0.74, colour, width, height)
        if colour is not BLACK:
            frame_lines(image, x0 + 0.02, 0.27, x1 - 0.02, 0.71, OCHRE, 0.006, width, height)
            frame_lines(image, x0 + 0.035, 0.285, x1 - 0.035, 0.695, CREAM * 0.9, 0.003, width, height)
            vignette(image, (x0 + x1) / 2, 0.49, 0.06, seed + index, width, height)
        else:
            rect(image, (x0 + x1) / 2 - 0.004, 0.26, (x0 + x1) / 2 + 0.004, 0.72, OCHRE * 0.9, width, height)
            for level in (0.36, 0.5, 0.64):
                rect(image, (x0 + x1) / 2 - 0.02, level, (x0 + x1) / 2 + 0.02, level + 0.012, CREAM * 0.85, width,
                     height)
    rect(image, 0.0, 0.74, 1.0, 0.8, BLACK, width, height)
    cupids = (np.sin(np.arange(width) / width * 2 * math.pi * 6) > 0.6)
    for column in np.nonzero(cupids)[0][::3]:
        image[int(0.755 * height):int(0.785 * height), column:column + 2] = np.array([0.75, 0.55, 0.35])
    rect(image, 0.0, 0.8, 1.0, 1.0, CREAM, width, height)
    for x in (0.1, 0.3, 0.5, 0.7, 0.9):
        rect(image, x - 0.003, 0.82, x + 0.003, 0.97, POMPEIAN_RED * 0.9, width, height)
        rect(image, x - 0.06, 0.95, x + 0.06, 0.955, OCHRE, width, height)
    grain = value_noise((height, width), 30, seed + 7, 3)
    return np.clip(image * (0.9 + 0.16 * grain)[..., None], 0, 1)


def build_library(cache_dir):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    texture_dir = os.path.join(cache_dir, "textures")
    os.makedirs(texture_dir, exist_ok=True)
    credits = {}
    tiles = {}
    for name, spec in TEXTURED.items():
        diffuse, normal, width_metres = poly_haven_asset(spec["asset"], source_dir, credits)
        signature = "".join(f"{round(value * 100):02d}" for value in (*spec["color"], spec["contrast"]))
        base = recolored(diffuse, spec["color"], spec["contrast"], os.path.join(texture_dir, f"{name}_{signature}.jpg"),
                         name)
        principled_material(name, linear_color(spec["color"]), spec["roughness"], 0.0, base)
        tiles[name] = spec.get("tile", width_metres)
    for name, spec in PLAIN.items():
        principled_material(name, linear_color(spec["color"]), spec["roughness"], spec.get("metallic", 0.0))
        tiles[name] = 2.0
    generated = {
        "basalt": (basalt_pixels, 4.0, 0.7),
        "terracotta_tiles": (roof_pixels, 3.2, 0.8),
        "fresco": (fresco_pixels, 4.0, 0.75),
        "marble": (lambda: smooth_stone_pixels((0.92, 0.90, 0.86)), 2.5, 0.45),
    }
    for name, (build, tile, roughness) in generated.items():
        image = generated_image(name, os.path.join(texture_dir, f"{name}_v2.jpg"), build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, image)
        tiles[name] = tile
    return tiles, credits

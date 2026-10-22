import os

import numpy as np

import bpy

from .materials import (generated_image, image_pixels, linear_color, poly_haven_asset, principled_material, recolored,
                        save_pixels, smooth_stone_pixels)
from .pantheon_materials import normalise
from .pompei_materials import roof_pixels
from .pont_materials import height_normal, luminance, periodic_noise
from .terrain import value_noise

LIMESTONE_TILE = 6.0
LIMESTONE_COURSES = 9
TEXTURED = {
    "plaster": dict(asset="plastered_wall", color=(0.97, 0.95, 0.91), contrast=0.3, roughness=0.88, tile=2.6),
    "paving": dict(asset="rectangular_paving", color=(1.0, 0.86, 0.64), contrast=0.5, roughness=0.8, tile=6.0),
}
PLAIN = {
    "matte": dict(color=(1.0, 1.0, 1.0), roughness=0.86),
    "water": dict(color=(1.0, 1.0, 1.0), roughness=0.06),
    "bronze_gilt": dict(color=(0.90, 0.55, 0.14), roughness=0.42, metallic=1.0),
    "shadow_void": dict(color=(0.05, 0.045, 0.04), roughness=1.0),
}
RENAME = {"weathered_ashlar": "limestone", "lens_ashlar": "limestone", "stone": "limestone", "lens_smooth": "marble",
          "lens_fluted": "marble", "frieze_rinceau": "marble", "roof_flat": "terracotta_tiles",
          "roof_tiles": "terracotta_tiles", "bronze": "bronze_gilt", "arena_sand": "paving", "velum_linen": "matte",
          "plank_wood": "matte", "dark_wood": "matte", "sidewalk": "paving", "floor_sheltered": "paving",
          "basalt": "paving", "paving_stone": "paving", "crustae": "marble", "fresco": "plaster",
          "river_water": "water", "garden_green": "matte", "arles_stone": "limestone", "marble_white": "marble",
          "travertine": "limestone", "brick": "plaster", "stucco": "plaster", "granite_grey": "granite",
          "col_bronze_patina": "bronze_gilt", "col_slabs": "paving"}


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


def granite_pixels(size=512, seed=17):
    rng = np.random.default_rng(seed)
    base = np.array([0.74, 0.47, 0.42])
    field = value_noise((size, size), 6, seed, 3)
    colour = base[None, None, :] * (0.9 + 0.2 * field[..., None])
    count = size * size // 9
    xs = rng.integers(0, size, count)
    ys = rng.integers(0, size, count)
    tones = rng.choice(4, count, p=[0.45, 0.3, 0.15, 0.1])
    palette = np.array([[0.86, 0.58, 0.52], [0.30, 0.24, 0.22], [0.92, 0.88, 0.84], [0.56, 0.33, 0.30]])
    for dx in (0, 1):
        for dy in (0, 1):
            colour[(ys + dy) % size, (xs + dx) % size] = palette[tones]
    return np.clip(colour, 0, 1)


def glyph_pixels(width=256, height=1024, seed=23):
    rng = np.random.default_rng(seed)
    colour = np.tile(granite_pixels(512, seed + 1), (2, 1, 1))[:height, :width].copy()
    carve = np.zeros((height, width))
    columns = (width * 0.3, width * 0.5, width * 0.7)
    for cx in columns:
        y = 30
        while y < height - 40:
            kind = rng.integers(0, 6)
            h = rng.integers(14, 30)
            w = rng.integers(10, 24)
            x0 = int(cx - w / 2)
            if kind == 0:
                carve[y:y + h, x0:x0 + 3] = 1
                carve[y:y + 3, x0:x0 + w] = 1
            elif kind == 1:
                yy, xx = np.ogrid[:h, :w]
                ring = np.abs(np.hypot((yy - h / 2) / (h / 2), (xx - w / 2) / (w / 2)) - 0.75) < 0.22
                carve[y:y + h, x0:x0 + w][ring] = 1
            elif kind == 2:
                for k in range(3):
                    carve[y + k * h // 3:y + k * h // 3 + 3, x0:x0 + w] = 1
            elif kind == 3:
                carve[y:y + h, x0 + w // 2:x0 + w // 2 + 3] = 1
                carve[y + h // 2:y + h // 2 + 3, x0:x0 + w] = 1
            elif kind == 4:
                for k in range(w):
                    row = int(y + h - 1 - k * h / max(w, 1))
                    carve[max(row, y):max(row, y) + 3, x0 + k] = 1
            else:
                carve[y:y + h, x0:x0 + w] = 0.6
                carve[y + 3:y + h - 3, x0 + 3:x0 + w - 3] = 0
            y += h + rng.integers(6, 14)
        carve[:, int(cx - 20):int(cx - 18)] = 0.7
    shade = 1.0 - 0.45 * carve
    return np.clip(colour * shade[..., None], 0, 1)


def drafted_ashlar(source, size=1024, seed=37):
    rng = np.random.default_rng(seed)
    scale = size / LIMESTONE_TILE
    edges = np.linspace(0, size, LIMESTONE_COURSES + 1).astype(int)
    grain = normalise(luminance(source))
    grain = np.tile(grain, (size // grain.shape[0] + 1, size // grain.shape[1] + 1))[:size, :size]
    colour = np.zeros((size, size, 3))
    height = np.zeros((size, size))
    base = np.array([0.95, 0.91, 0.82])
    margin = max(int(0.07 * scale), 3)
    joint = 2
    for row in range(LIMESTONE_COURSES):
        y0, y1 = edges[row], edges[row + 1]
        x = int(rng.integers(0, size))
        start = x
        while x < start + size:
            length = int(rng.uniform(1.0, 2.1) * scale)
            length = min(length, start + size - x)
            if start + size - x - length < 0.5 * scale:
                length = start + size - x
            columns = np.arange(x, x + length) % size
            tone = rng.normal(1.0, 0.045)
            warmth = np.array([1.0, 1.0 - abs(rng.normal(0.0, 0.012)), 1.0 - abs(rng.normal(0.0, 0.03))])
            ly = np.arange(y1 - y0)[:, None]
            lx = np.arange(length)[None, :]
            edge = np.minimum(np.minimum(lx, length - 1 - lx), np.minimum(ly, y1 - y0 - 1 - ly))
            drafted = edge < margin
            block = grain[y0:y1][:, columns]
            shade = (0.9 + 0.16 * block) * np.where(drafted, 1.05, 1.0) * np.where(edge < joint, 0.62, 1.0)
            colour[y0:y1][:, columns] = shade[..., None] * base * tone * warmth
            boss = np.clip((edge - margin) / (margin * 2.0), 0.0, 1.0)
            height[y0:y1][:, columns] = np.where(edge < joint, 0.0, 0.35 + 0.25 * boss + 0.08 * block)
            x += length
    streaks = periodic_noise(size, 1.3, seed + 1, stretch=(0.2, 4.0))
    grime = periodic_noise(size, 1.8, seed + 2)
    colour *= (0.93 + 0.1 * grime)[..., None]
    colour *= (0.95 + 0.08 * streaks)[..., None]
    return np.clip(colour, 0, 1), height_normal(height, 7.0)


def limestone_material(cache_dir, texture_dir, credits):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    colour_path = os.path.join(texture_dir, "limestone_drafted_v1.jpg")
    normal_path = os.path.join(texture_dir, "limestone_drafted_normal_v1.jpg")
    if not (os.path.exists(colour_path) and os.path.exists(normal_path)):
        diffuse, _, _ = poly_haven_asset("sandstone_blocks_08", source_dir, credits)
        image, pixels = image_pixels(diffuse)
        bpy.data.images.remove(image)
        colour, normal = drafted_ashlar(pixels[..., :3])
        save_pixels("limestone_drafted", colour, colour_path, quality=92)
        save_pixels("limestone_drafted_normal", normal, normal_path, quality=95, colorspace="Non-Color")
    else:
        poly_haven_asset("sandstone_blocks_08", source_dir, credits)
    base = bpy.data.images.load(colour_path, check_existing=True)
    normal = bpy.data.images.load(normal_path, check_existing=True)
    principled_material("limestone", (0.85, 0.82, 0.75), 0.74, 0.0, base, normal, 0.9)


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
    limestone_material(cache_dir, texture_dir, credits)
    tiles["limestone"] = LIMESTONE_TILE
    for name, spec in PLAIN.items():
        color = spec["color"] if name in ("bronze_gilt", "water", "matte") else linear_color(spec["color"])
        principled_material(name, color, spec["roughness"], spec.get("metallic", 0.0))
        tiles[name] = 2.0
    generated = {
        "terracotta_tiles": (roof_pixels, 3.2, 0.78),
        "marble": (lambda: smooth_stone_pixels((0.97, 0.96, 0.93)), 2.5, 0.38),
        "granite": (granite_pixels, 1.6, 0.42),
        "granite_glyphs": (glyph_pixels, 1.0, 0.45),
    }
    for name, (build, tile, roughness) in generated.items():
        image = generated_image(name, os.path.join(texture_dir, f"{name}_v1.jpg"), build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, image)
        tiles[name] = tile
    return tiles, credits

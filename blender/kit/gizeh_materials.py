import os

import bpy
import numpy as np

from .alexandrie_materials import glyph_pixels, granite_pixels
from .materials import image_pixels, linear_color, poly_haven_asset, principled_material, recolored, save_pixels
from .pantheon_materials import normalise
from .pont_materials import height_normal, luminance, periodic_noise

VERSION = "v8"
TILES = {"casing": 6.0, "casing_granite": 6.0, "granite_rough": 6.0, "core_stone": 6.0, "limestone": 6.0,
         "sphinx_rock": 8.0, "restoration": 3.0, "mudbrick": 3.0, "paving": 6.0, "basalt": 5.0, "plaster": 2.6,
         "granite_glyphs": 1.0, "greek_stele": 1.0}
PLAIN = {
    "matte": dict(color=(1.0, 1.0, 1.0), roughness=0.86),
    "water": dict(color=(1.0, 1.0, 1.0), roughness=0.5),
    "bronze_gilt": dict(color=(0.90, 0.62, 0.20), roughness=0.36, metallic=1.0),
    "shadow_void": dict(color=(0.05, 0.045, 0.04), roughness=1.0),
}
RENAME = {"weathered_ashlar": "limestone", "lens_ashlar": "limestone", "stone": "limestone", "lens_smooth": "casing",
          "marble": "casing", "lens_fluted": "casing", "frieze_rinceau": "casing", "roof_flat": "mudbrick",
          "roof_tiles": "mudbrick", "terracotta_tiles": "mudbrick", "bronze": "bronze_gilt", "arena_sand": "paving",
          "velum_linen": "matte", "plank_wood": "matte", "dark_wood": "matte", "sidewalk": "paving",
          "paving_stone": "paving", "granite": "casing_granite", "river_water": "water", "brick": "mudbrick",
          "stucco": "plaster", "fresco": "plaster", "garden_green": "matte"}


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


def tiled(values, size):
    reps = (size // values.shape[0] + 1, size // values.shape[1] + 1) + (1,) * (values.ndim - 2)
    return np.tile(values, reps)[:size, :size]


def blocks(size, courses, length_range, seed, scale, irregular=False):
    rng = np.random.default_rng(seed)
    edges = np.linspace(0, size, courses + 1).astype(int)
    if irregular:
        runs = np.cumsum(rng.uniform(0.6, 1.1, courses))
        edges = np.concatenate([[0], np.round(runs / runs[-1] * size)]).astype(int)
    index = np.zeros((size, size), dtype=np.int64)
    edge = np.zeros((size, size))
    counter = 0
    for row in range(courses):
        y0, y1 = edges[row], edges[row + 1]
        x = int(rng.integers(0, size))
        start = x
        while x < start + size:
            length = int(rng.uniform(*length_range) * scale)
            length = min(length, start + size - x)
            if start + size - x - length < length_range[0] * scale * 0.5:
                length = start + size - x
            columns = np.arange(x, x + length) % size
            ly = np.arange(y1 - y0)[:, None]
            lx = np.arange(length)[None, :]
            distance = np.minimum(np.minimum(lx, length - 1 - lx), np.minimum(ly, y1 - y0 - 1 - ly))
            index[y0:y1][:, columns] = counter
            edge[y0:y1][:, columns] = distance
            counter += 1
            x += length
    return index, edge, counter


def casing_pixels(grain, size=1024, seed=5):
    rng = np.random.default_rng(seed)
    scale = size / TILES["casing"]
    index, edge, count = blocks(size, 6, (1.3, 2.6), seed, scale)
    tones = rng.normal(1.0, 0.009, count)
    warmth = rng.normal(0.0, 0.006, count)
    base = np.array([0.88, 0.79, 0.62])
    texture = 0.975 + 0.025 * normalise(tiled(grain, size))
    colour = base[None, None, :] * (tones[index] * texture)[..., None]
    colour[..., 2] *= 1.0 - np.abs(warmth[index])
    joint = edge < 1.5
    colour *= np.where(joint, 0.88, 1.0)[..., None]
    pits = periodic_noise(size, 0.6, seed + 3)
    colour *= (1.0 - 0.12 * np.clip((pits - 0.82) / 0.1, 0, 1))[..., None]
    streaks = periodic_noise(size, 1.5, seed + 4, stretch=(0.15, 3.0))
    colour *= (0.985 + 0.02 * streaks)[..., None]
    height = np.where(joint, 0.0, 0.5 + 0.06 * texture)
    return np.clip(colour, 0, 1), height_normal(height, 3.0)


def granite_course_pixels(size=1024, seed=7):
    scale = size / TILES["casing_granite"]
    index, edge, _ = blocks(size, 6, (1.4, 2.8), seed, scale)
    granite = tiled(granite_pixels(512, seed), size)
    colour = granite * np.where(edge < 1.5, 0.6, 1.0)[..., None]
    return np.clip(colour * np.array([0.76, 0.62, 0.58]), 0, 1)


def rough_granite_pixels(size=1024, seed=9):
    rng = np.random.default_rng(seed)
    scale = size / TILES["granite_rough"]
    index, edge, count = blocks(size, 5, (1.2, 2.4), seed, scale)
    raw = tiled(granite_pixels(512, seed + 1), size)
    grey = raw.mean(axis=2, keepdims=True)
    granite = (raw * 0.45 + grey * 0.55) * np.array([0.72, 0.58, 0.56])
    boss = np.clip(edge / (0.35 * scale), 0.0, 1.0)
    bump = periodic_noise(size, 1.2, seed + 2)
    height = boss * (0.7 + 0.3 * bump) + 0.05 * rng.normal(0, 1, (size, size))
    shade = 0.68 + 0.32 * boss
    colour = granite * shade[..., None] * np.where(edge < 2.0, 0.5, 1.0)[..., None]
    tones = rng.normal(1.0, 0.05, count)
    colour *= tones[index][..., None]
    return np.clip(colour, 0, 1), height_normal(height, 9.0)


def core_pixels(grain, size=1024, seed=11):
    rng = np.random.default_rng(seed)
    scale = size / TILES["core_stone"]
    index, edge, count = blocks(size, 7, (0.8, 1.8), seed, scale, irregular=True)
    base = np.array([0.80, 0.67, 0.48])
    texture = normalise(tiled(grain, size))
    tones = rng.normal(1.0, 0.05, count)
    wobble = periodic_noise(size, 1.4, seed + 1)
    chips = periodic_noise(size, 0.35, seed + 5)
    rounded = np.clip((edge + wobble * 0.14 * scale - chips * 0.06 * scale) / (0.12 * scale), 0.0, 1.0)
    colour = base[None, None, :] * (tones[index] * (0.82 + 0.26 * texture))[..., None]
    colour *= (0.62 + 0.38 * rounded)[..., None]
    pits = periodic_noise(size, 0.5, seed + 2)
    colour *= (1.0 - 0.2 * np.clip((pits - 0.75) / 0.1, 0, 1))[..., None]
    height = rounded * (0.8 + 0.2 * texture)
    return np.clip(colour, 0, 1), height_normal(height, 10.0)


def sphinx_rock_pixels(grain, size=1024, seed=13):
    v = np.linspace(0, 1, size, endpoint=False)[:, None]
    wobble = periodic_noise(size, 1.6, seed, stretch=(4.0, 0.5))
    phase = (v * 9.0 + 0.6 * wobble) % 1.0
    hard = (np.clip(np.sin(phase * np.pi * 2) * 1.6, -1, 1) * 0.5 + 0.5) * 0.6 + 0.2
    soft = np.array([0.90, 0.70, 0.46])
    harder = np.array([0.88, 0.78, 0.60])
    texture = normalise(tiled(grain, size))
    colour = soft[None, None, :] * (1 - hard[..., None]) + harder[None, None, :] * hard[..., None]
    colour *= (0.82 + 0.26 * texture)[..., None]
    pockets = periodic_noise(size, 0.9, seed + 2, stretch=(2.5, 1.0))
    holes = np.clip((pockets - 0.7) / 0.15, 0, 1) * (1 - hard)
    colour *= (1.0 - 0.35 * holes)[..., None]
    height = hard * 0.6 + 0.25 * texture - 0.4 * holes
    return np.clip(colour, 0, 1), height_normal(height, 8.0)


def restoration_pixels(grain, size=1024, seed=15):
    rng = np.random.default_rng(seed)
    scale = size / TILES["restoration"]
    index, edge, count = blocks(size, 7, (0.35, 0.8), seed, scale)
    tones = rng.normal(1.0, 0.06, count)
    base = np.array([0.88, 0.78, 0.60])
    texture = normalise(tiled(grain, size))
    colour = base[None, None, :] * (tones[index] * (0.86 + 0.2 * texture))[..., None]
    colour *= np.where(edge < 2.5, 0.62, 1.0)[..., None]
    return np.clip(colour, 0, 1)


def mudbrick_pixels(size=1024, seed=17):
    rng = np.random.default_rng(seed)
    scale = size / TILES["mudbrick"]
    courses = int(round(TILES["mudbrick"] / 0.13))
    index, edge, count = blocks(size, courses, (0.33, 0.38), seed, scale)
    tones = rng.normal(1.0, 0.07, count)
    base = np.array([0.62, 0.50, 0.40])
    straw = periodic_noise(size, 0.4, seed + 1)
    colour = base[None, None, :] * (tones[index] * (0.9 + 0.16 * straw))[..., None]
    mortar = edge < 2.0
    colour = np.where(mortar[..., None], np.array([0.72, 0.63, 0.50]), colour)
    wash = periodic_noise(size, 2.0, seed + 2)
    colour *= (0.9 + 0.16 * wash)[..., None]
    return np.clip(colour, 0, 1)


def basalt_pixels(size=1024, seed=19):
    rng = np.random.default_rng(seed)
    scale = size / TILES["basalt"]
    index, edge, count = blocks(size, 5, (0.7, 1.6), seed, scale)
    tones = rng.normal(1.0, 0.08, count)
    base = np.array([0.24, 0.24, 0.25])
    speck = rng.random((size, size))
    colour = base[None, None, :] * (tones[index] * (0.9 + 0.2 * speck))[..., None]
    colour *= np.where(edge < 2.0, 0.55, 1.0)[..., None]
    dust = periodic_noise(size, 1.8, seed + 1)
    colour = colour * (1 - 0.3 * dust[..., None]) + np.array([0.78, 0.66, 0.48]) * 0.3 * dust[..., None]
    return np.clip(colour, 0, 1)


def stele_pixels(size=512, seed=21):
    rng = np.random.default_rng(seed)
    colour = np.ones((size, size, 3)) * np.array([0.90, 0.85, 0.74])
    colour *= (0.92 + 0.1 * periodic_noise(size, 1.5, seed))[..., None]
    carve = np.zeros((size, size))
    y = 40
    while y < size - 40:
        x = 34
        height = 16
        while x < size - 40:
            kind = rng.integers(0, 5)
            width = int(rng.integers(8, 14))
            if kind == 0:
                carve[y:y + height, x:x + 2] = 1
                carve[y:y + 2, x:x + width] = 1
            elif kind == 1:
                carve[y:y + height, x:x + 2] = 1
                carve[y:y + height, x + width - 2:x + width] = 1
                carve[y + height // 2:y + height // 2 + 2, x:x + width] = 1
            elif kind == 2:
                yy, xx = np.ogrid[:height, :width]
                ring = np.abs(np.hypot((yy - height / 2) / (height / 2), (xx - width / 2) / (width / 2)) - 0.8) < 0.25
                carve[y:y + height, x:x + width][ring] = 1
            elif kind == 3:
                for k in range(width):
                    row = int(y + k * height / width)
                    carve[row:row + 2, x + k] = 1
            else:
                carve[y:y + 2, x:x + width] = 1
                carve[y + height - 2:y + height, x:x + width] = 1
                carve[y:y + height, x + width // 2:x + width // 2 + 2] = 1
            x += width + int(rng.integers(4, 8))
        y += height + 10
    colour *= (1.0 - 0.45 * carve)[..., None]
    return np.clip(colour, 0, 1)


def cached(name, path, build, colorspace="sRGB", quality=92):
    if os.path.exists(path):
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = colorspace
        return image
    return save_pixels(name, build(), path, quality=quality, colorspace=colorspace)


def cached_pair(name, folder, build):
    colour_path = os.path.join(folder, f"{name}_{VERSION}.jpg")
    normal_path = os.path.join(folder, f"{name}_normal_{VERSION}.jpg")
    if not (os.path.exists(colour_path) and os.path.exists(normal_path)):
        colour, normal = build()
        save_pixels(name, colour, colour_path, quality=92)
        small = normal[::2, ::2]
        save_pixels(f"{name}_normal", small, normal_path, quality=95, colorspace="Non-Color")
    base = bpy.data.images.load(colour_path, check_existing=True)
    normal = bpy.data.images.load(normal_path, check_existing=True)
    normal.colorspace_settings.name = "Non-Color"
    return base, normal


def build_library(cache_dir):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    folder = os.path.join(cache_dir, "textures")
    os.makedirs(folder, exist_ok=True)
    credits = {}
    diffuse, _, _ = poly_haven_asset("sandstone_blocks_08", source_dir, credits)
    image, pixels = image_pixels(diffuse)
    grain = luminance(pixels[..., :3])
    bpy.data.images.remove(image)
    pairs = {
        "casing": (lambda: casing_pixels(grain), 0.82, 0.5),
        "granite_rough": (rough_granite_pixels, 0.55, 1.0),
        "core_stone": (lambda: core_pixels(grain), 0.85, 1.0),
        "sphinx_rock": (lambda: sphinx_rock_pixels(grain), 0.85, 1.0),
    }
    for name, (build, roughness, strength) in pairs.items():
        base, normal = cached_pair(name, folder, build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, base, normal, strength)
    singles = {
        "casing_granite": (granite_course_pixels, 0.4),
        "restoration": (lambda: restoration_pixels(grain), 0.85),
        "mudbrick": (mudbrick_pixels, 0.92),
        "basalt": (basalt_pixels, 0.6),
        "greek_stele": (stele_pixels, 0.7),
        "granite_glyphs": (glyph_pixels, 0.45),
    }
    for name, (build, roughness) in singles.items():
        image = cached(name, os.path.join(folder, f"{name}_{VERSION}.jpg"), build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, image)
    textured = {
        "plaster": dict(asset="plastered_wall", color=(0.97, 0.95, 0.91), contrast=0.3, roughness=0.9),
        "paving": dict(asset="rectangular_paving", color=(0.86, 0.78, 0.64), contrast=0.5, roughness=0.8),
        "limestone": dict(asset="sandstone_blocks_08", color=(0.90, 0.80, 0.62), contrast=0.55, roughness=0.8),
    }
    for name, spec in textured.items():
        source, _, _ = poly_haven_asset(spec["asset"], source_dir, credits)
        signature = "".join(f"{round(value * 100):02d}" for value in (*spec["color"], spec["contrast"]))
        base = recolored(source, spec["color"], spec["contrast"], os.path.join(folder, f"{name}_{signature}.jpg"),
                         name)
        principled_material(name, linear_color(spec["color"]), spec["roughness"], 0.0, base)
    for name, spec in PLAIN.items():
        color = spec["color"] if name in ("water", "matte") else linear_color(spec["color"])
        principled_material(name, color, spec["roughness"], spec.get("metallic", 0.0))
    tiles = dict(TILES)
    for name in PLAIN:
        tiles[name] = 2.0
    return tiles, credits

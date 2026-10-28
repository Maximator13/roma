import math
import os

import bpy
import numpy as np

from .alexandrie_materials import limestone_material
from .constantinople_materials import build_library as constantinople_library
from .materials import linear_color, principled_material, save_pixels
from .pantheon_materials import cached
from .pont_materials import height_normal, periodic_noise

FRIEZE_TILE = 4.0
FRIEZE_WIDTH = 2048
FRIEZE_HEIGHT = 256
VERSION = "v2"
RENAME = {"lens_ashlar": "limestone", "weathered_ashlar": "limestone", "stone": "limestone", "arles_stone": "limestone",
          "lens_smooth": "marble_white", "lens_fluted": "marble_white", "frieze_rinceau": "marble_white",
          "marble": "marble_white", "roof_flat": "terracotta_tiles", "roof_tiles": "terracotta_tiles",
          "plank_wood": "matte", "dark_wood": "matte", "velum_linen": "matte", "arena_sand": "sand",
          "paving": "travertine", "paving_stone": "travertine", "sidewalk": "travertine", "bark": "matte",
          "basalt": "granite_grey", "fresco": "plaster", "crustae": "floor_sectile", "granite": "granite_grey",
          "col_bronze_patina": "bronze", "col_slabs": "travertine", "garden_green": "matte", "river_water": "water",
          "granite_glyphs": "granite_grey", "floor_sheltered": "travertine", "brick": "plaster"}
BLUE_GROUND = np.array([0.13, 0.30, 0.62])
FLESH_GREEK = np.array([0.66, 0.38, 0.24])
FLESH_AMAZON = np.array([0.92, 0.76, 0.62])
CLOTHS = np.array([[0.74, 0.16, 0.12], [0.86, 0.66, 0.22], [0.36, 0.52, 0.30], [0.52, 0.22, 0.42], [0.92, 0.88, 0.80],
                   [0.80, 0.36, 0.18]])
HORSE = np.array([[0.62, 0.42, 0.26], [0.86, 0.80, 0.70], [0.40, 0.28, 0.20]])


def disc(canvas, height, cx, cy, rx, ry, colour, lift, angle=0.0):
    h, w = height.shape
    reach = int(max(rx, ry)) + 2
    y0, y1 = max(int(cy) - reach, 0), min(int(cy) + reach + 1, h)
    if y1 <= y0:
        return
    xs = np.arange(int(cx) - reach, int(cx) + reach + 1)
    ys = np.arange(y0, y1)
    gx, gy = np.meshgrid(xs, ys)
    c, s = math.cos(angle), math.sin(angle)
    u = (gx - cx) * c + (gy - cy) * s
    v = -(gx - cx) * s + (gy - cy) * c
    r = (u / max(rx, 0.5)) ** 2 + (v / max(ry, 0.5)) ** 2
    inside = r < 1.0
    columns = gx % w
    rows = gy
    canvas[rows[inside], columns[inside]] = colour
    dome = lift * np.sqrt(np.clip(1.0 - r, 0.0, 1.0))
    height[rows[inside], columns[inside]] = np.maximum(height[rows[inside], columns[inside]], dome[inside])


def limb(canvas, height, a, b, width, colour, lift):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    disc(canvas, height, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, length / 2 + width * 0.3, width, colour, lift, angle)


def warrior(canvas, height, x, base, scale, rng, amazon, facing, mounted):
    flesh = FLESH_AMAZON if amazon else FLESH_GREEK
    cloth = CLOTHS[rng.integers(len(CLOTHS))]
    lift = 1.0
    hip = (x, base - 92 * scale)
    if mounted:
        coat = HORSE[rng.integers(len(HORSE))]
        disc(canvas, height, x, base - 64 * scale, 52 * scale, 22 * scale, coat, 0.9)
        limb(canvas, height, (x + facing * 44 * scale, base - 76 * scale), (x + facing * 70 * scale, base - 118 * scale),
             12 * scale, coat, 0.9)
        disc(canvas, height, x + facing * 78 * scale, base - 122 * scale, 15 * scale, 9 * scale, coat, 0.95,
             -0.6 * facing)
        for dx, kick in ((-36, -1), (-24, 1), (30, 1), (44, -1)):
            limb(canvas, height, (x + facing * dx * scale, base - 50 * scale),
                 (x + facing * (dx + kick * 16) * scale, base - 6 * scale), 5 * scale, coat, 0.8)
        limb(canvas, height, (x - facing * 50 * scale, base - 70 * scale), (x - facing * 70 * scale, base - 50 * scale),
             5 * scale, coat * 0.7, 0.7)
        hip = (x - facing * 4 * scale, base - 92 * scale)
    shoulder = (hip[0] + facing * 10 * scale, hip[1] - 52 * scale)
    disc(canvas, height, (hip[0] + shoulder[0]) / 2, (hip[1] + shoulder[1]) / 2, 13 * scale, 30 * scale, cloth, lift,
         0.2 * facing)
    disc(canvas, height, shoulder[0] + facing * 4 * scale, shoulder[1] - 18 * scale, 10 * scale, 11 * scale, flesh, lift)
    if amazon:
        disc(canvas, height, shoulder[0] + facing * 2 * scale, shoulder[1] - 25 * scale, 11 * scale, 7 * scale,
             CLOTHS[3], lift)
    else:
        disc(canvas, height, shoulder[0] + facing * 2 * scale, shoulder[1] - 26 * scale, 12 * scale, 8 * scale,
             np.array([0.78, 0.62, 0.28]), lift)
    if not mounted:
        stride = rng.uniform(0.6, 1.0)
        limb(canvas, height, hip, (hip[0] + facing * 34 * stride * scale, base), 7 * scale, flesh, lift)
        limb(canvas, height, hip, (hip[0] - facing * 30 * stride * scale, base), 7 * scale, flesh, lift)
        disc(canvas, height, hip[0], hip[1] + 8 * scale, 18 * scale, 14 * scale, cloth, lift)
    else:
        limb(canvas, height, hip, (hip[0] + facing * 14 * scale, hip[1] + 34 * scale), 7 * scale, flesh, lift)
    raise_arm = (shoulder[0] + facing * 40 * scale, shoulder[1] - 34 * scale * rng.uniform(0.3, 1.0))
    limb(canvas, height, shoulder, raise_arm, 5 * scale, flesh, lift)
    limb(canvas, height, raise_arm, (raise_arm[0] + facing * 30 * scale, raise_arm[1] - 24 * scale), 2 * scale,
         np.array([0.62, 0.58, 0.52]), 1.0)
    if rng.random() < 0.7:
        disc(canvas, height, shoulder[0] - facing * 16 * scale, shoulder[1] + 10 * scale, 22 * scale, 22 * scale,
             np.array([0.86, 0.62, 0.20]) if not amazon else np.array([0.70, 0.18, 0.14]), 1.1)
    cape = (shoulder[0] - facing * 30 * scale, shoulder[1] + 26 * scale)
    if rng.random() < 0.5:
        limb(canvas, height, shoulder, cape, 9 * scale, CLOTHS[rng.integers(len(CLOTHS))], 0.8)


def frieze_pixels(seed=31):
    rng = np.random.default_rng(seed)
    w, h = FRIEZE_WIDTH, FRIEZE_HEIGHT
    noise = periodic_noise(w, 0.8, seed + 1)[:h]
    canvas = np.zeros((h, w, 3))
    canvas[:] = BLUE_GROUND
    canvas *= (0.92 + 0.12 * noise)[..., None]
    height = np.zeros((h, w))
    base = h - 26
    x = 30.0
    k = 0
    while x < w - 40:
        amazon = k % 2 == 1
        mounted = rng.random() < 0.28
        facing = 1 if (k // 2) % 2 == 0 else -1
        if amazon:
            facing = -facing
        warrior(canvas, height, x, base, 1.0 if not mounted else 0.88, rng, amazon, facing, mounted)
        x += rng.uniform(70, 96) if not mounted else rng.uniform(118, 140)
        k += 1
    canvas[:14] = np.array([0.94, 0.90, 0.80])
    canvas[14:20] = np.array([0.74, 0.20, 0.14])
    canvas[h - 18:] = np.array([0.94, 0.90, 0.80])
    for x0 in range(0, w, 32):
        canvas[2:12, x0 + 4:x0 + 20] = np.array([0.86, 0.66, 0.24])
    height[:14] = 0.6
    height[h - 18:] = 0.6
    patina = periodic_noise(w, 1.7, seed + 3)[:h]
    canvas *= (0.86 + 0.16 * patina)[..., None]
    return np.clip(canvas[::-1], 0, 1), height_normal(height[::-1], 5.0)


def build_library(cache_dir):
    tiles, credits = constantinople_library(cache_dir)
    texture_dir = os.path.join(cache_dir, "textures")
    limestone_material(cache_dir, texture_dir, credits)
    tiles["limestone"] = 6.0
    colour_path = os.path.join(texture_dir, f"frieze_amazon_{VERSION}.jpg")
    normal_path = os.path.join(texture_dir, f"frieze_amazon_normal_{VERSION}.jpg")
    if os.path.exists(colour_path) and os.path.exists(normal_path):
        colour = cached("frieze_amazon", colour_path, None)
        normal = cached("frieze_amazon_normal", normal_path, None, "Non-Color")
    else:
        pixels, normals = frieze_pixels()
        colour = save_pixels("frieze_amazon", pixels, colour_path, quality=92)
        normal = save_pixels("frieze_amazon_normal", normals, normal_path, quality=94, colorspace="Non-Color")
    principled_material("frieze", (1.0, 1.0, 1.0), 0.55, 0.0, colour, normal, 1.0)
    tiles["frieze"] = 1.0
    principled_material("stucco_polished", linear_color((0.97, 0.94, 0.88)), 0.18, 0.0)
    tiles["stucco_polished"] = 2.0
    principled_material("water", linear_color((0.04, 0.26, 0.42)), 0.05, 0.0)
    bpy.data.materials["water"].use_backface_culling = True
    return tiles, credits


def remap(builder):
    names = [RENAME.get(name, name) for name in builder.materials]
    names = [name if name in bpy.data.materials or name == "shadow_void" else "matte" for name in names]
    merged = []
    index_of = {}
    lookup = []
    for name in names:
        if name not in index_of:
            index_of[name] = len(merged)
            merged.append(name)
        lookup.append(index_of[name])
    builder.polygon_materials = [lookup[index] for index in builder.polygon_materials]
    builder.materials = merged
    return builder

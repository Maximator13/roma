import os

import numpy as np

from .materials import principled_material, save_pixels
from .pantheon_materials import ambient_colour, cached, normalise
from .pont_materials import height_normal, luminance, periodic_noise

SIZE = 1024
ASHLAR_TILE = 4.8
COURSE = 0.6
HONEY = np.array([0.92, 0.82, 0.66])


def ashlar(source, seed=73):
    generator = np.random.default_rng(seed)
    scale = SIZE / ASHLAR_TILE
    course = int(round(COURSE * scale))
    rows = SIZE // course
    colour = np.zeros((SIZE, SIZE, 3))
    height = np.zeros((SIZE, SIZE))
    joint = max(int(scale * 0.01), 2)
    detail = normalise(luminance(source))
    for row in range(rows):
        y0 = row * course
        y1 = SIZE if row == rows - 1 else y0 + course
        x = int(generator.integers(0, SIZE))
        start = x
        while x < start + SIZE:
            length = int(generator.uniform(1.1, 2.4) * scale)
            length = min(length, start + SIZE - x)
            columns = np.arange(x, x + length) % SIZE
            ox, oy = generator.integers(0, SIZE, 2)
            block = np.roll(np.roll(detail, -oy, 0), -ox, 1)[y0:y1][:, columns]
            tone = generator.normal(1.0, 0.06)
            warmth = np.array([1.0, 1.0 - generator.normal(0.0, 0.015), 1.0 - generator.normal(0.0, 0.03)])
            pits = (block < 0.18) * 0.25
            shade = (0.82 + 0.3 * block - pits)[..., None] * HONEY * tone * warmth
            colour[y0:y1][:, columns] = shade
            local_y = np.arange(y1 - y0)[:, None]
            local_x = np.arange(length)[None, :]
            edge = np.minimum(np.minimum(local_x, length - 1 - local_x), np.minimum(local_y, y1 - y0 - 1 - local_y))
            height[y0:y1][:, columns] = np.clip(edge / (joint * 2.5), 0, 1) ** 0.5 - pits * 0.6
            x += length
    streaks = periodic_noise(SIZE, 1.4, seed + 1, stretch=(0.15, 4.0))
    grime = periodic_noise(SIZE, 1.9, seed + 2)
    colour *= (0.9 + 0.14 * grime)[..., None]
    colour *= (0.94 + 0.1 * streaks)[..., None]
    colour *= (1.0 - 0.4 * (height < 0.18))[..., None]
    return np.clip(colour, 0, 1), height_normal(height, 5.0)


def colisee_library(cache_dir, tiles, credits):
    texture_dir = os.path.join(cache_dir, "textures")
    colour_path = os.path.join(texture_dir, "col_travertine_v2.jpg")
    normal_path = os.path.join(texture_dir, "col_travertine_normal_v2.jpg")
    if os.path.exists(colour_path) and os.path.exists(normal_path):
        colour = cached("col_travertine", colour_path, None)
        normal = cached("col_travertine_normal", normal_path, None, "Non-Color")
    else:
        source = ambient_colour("Travertine009", os.path.join(cache_dir, "src", "ambientcg"), credits)
        pixels, normals = ashlar(source)
        colour = save_pixels("col_travertine", pixels, colour_path, quality=90)
        normal = save_pixels("col_travertine_normal", normals, normal_path, quality=94, colorspace="Non-Color")
    principled_material("col_travertine", (1.0, 1.0, 1.0), 0.78, 0.0, colour, normal, 0.8)
    tiles["col_travertine"] = ASHLAR_TILE

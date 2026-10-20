import os

import numpy as np

from .materials import principled_material, save_pixels
from .pantheon_materials import ambient_colour, cached, normalise, smoothstep, voronoi
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


BASALT_TILE = 4.8
SLAB_TILE = 6.0


def basalt(seed=83):
    generator = np.random.default_rng(seed)
    cells = int((BASALT_TILE / 0.6) ** 2)
    first, second, owner = voronoi(cells, seed)
    dark = np.array([0.30, 0.31, 0.33])
    light = np.array([0.40, 0.40, 0.41])
    mix = generator.random(cells)
    tones = dark[None, :] * (1 - mix[:, None]) + light[None, :] * mix[:, None]
    tones *= generator.normal(1.0, 0.05, cells)[:, None]
    colour = tones[owner]
    grain = periodic_noise(SIZE, 0.6, seed + 1)
    wear = periodic_noise(SIZE, 1.6, seed + 2)
    edge = second - first
    joint = 1.0 - smoothstep(edge, 0.0, 6.0)
    bevel = 1.0 - smoothstep(edge, 0.0, 22.0)
    colour = colour * (0.9 + 0.16 * grain)[..., None] * (1.0 - 0.18 * bevel)[..., None]
    colour = colour * (1.0 + 0.12 * smoothstep(wear, 0.55, 0.9))[..., None]
    soil = np.array([0.24, 0.21, 0.17]) * (0.85 + 0.3 * grain)[..., None]
    colour = colour * (1.0 - joint[..., None]) + soil * joint[..., None]
    return np.clip(colour, 0, 1)


def slabs(source, seed=91):
    generator = np.random.default_rng(seed)
    scale = SIZE / SLAB_TILE
    row_height = int(round(1.5 * scale))
    rows = SIZE // row_height
    detail = normalise(luminance(source))
    colour = np.zeros((SIZE, SIZE, 3))
    edges = np.zeros((SIZE, SIZE))
    base = np.array([0.86, 0.82, 0.74])
    for row in range(rows):
        y0 = row * row_height
        y1 = SIZE if row == rows - 1 else y0 + row_height
        x = int(generator.integers(0, SIZE))
        start = x
        while x < start + SIZE:
            length = int(generator.uniform(2.2, 3.4) * scale)
            length = min(length, start + SIZE - x)
            columns = np.arange(x, x + length) % SIZE
            ox, oy = generator.integers(0, SIZE, 2)
            block = np.roll(np.roll(detail, -oy, 0), -ox, 1)[y0:y1][:, columns]
            tone = generator.normal(1.0, 0.05)
            warmth = np.array([1.0, 1.0 - generator.normal(0.0, 0.02), 1.0 - generator.normal(0.01, 0.03)])
            colour[y0:y1][:, columns] = (0.84 + 0.22 * block)[..., None] * base * tone * warmth
            local_y = np.arange(y1 - y0)[:, None]
            local_x = np.arange(length)[None, :]
            edges[y0:y1][:, columns] = np.minimum(np.minimum(local_x, length - 1 - local_x),
                                                  np.minimum(local_y, y1 - y0 - 1 - local_y))
            x += length
    grime = periodic_noise(SIZE, 1.8, seed + 1)
    colour *= (0.9 + 0.14 * grime)[..., None]
    colour *= (1.0 - 0.5 * (edges < 2.5))[..., None]
    colour *= (1.0 - 0.1 * np.clip(1.0 - edges / 14.0, 0, 1))[..., None]
    return np.clip(colour, 0, 1)


def paving_library(cache_dir, tiles, credits):
    texture_dir = os.path.join(cache_dir, "textures")
    basalt_path = os.path.join(texture_dir, "col_basalt_v1.jpg")
    image = cached("col_basalt", basalt_path, basalt, quality=90)
    principled_material("col_basalt", (1.0, 1.0, 1.0), 0.7, 0.0, image)
    tiles["col_basalt"] = BASALT_TILE
    slab_path = os.path.join(texture_dir, "col_slabs_v1.jpg")
    if os.path.exists(slab_path):
        image = cached("col_slabs", slab_path, None, quality=90)
    else:
        source = ambient_colour("Travertine009", os.path.join(cache_dir, "src", "ambientcg"), credits)
        image = save_pixels("col_slabs", slabs(source), slab_path, quality=90)
    principled_material("col_slabs", (1.0, 1.0, 1.0), 0.75, 0.0, image)
    tiles["col_slabs"] = SLAB_TILE


FACADE_TILE = 12.0


def facade(brick=False, seed=101):
    generator = np.random.default_rng(seed)
    scale = SIZE / FACADE_TILE
    ys, xs = np.mgrid[0:SIZE, 0:SIZE]
    grain = periodic_noise(SIZE, 1.2, seed + 1)
    fine = periodic_noise(SIZE, 0.5, seed + 2)
    if brick:
        base = np.array([0.66, 0.42, 0.31])
        colour = base * (0.86 + 0.2 * grain)[..., None] * (0.92 + 0.12 * fine)[..., None]
        mortar = (ys % int(round(0.3 * scale))) < 2
        colour[mortar] *= 1.12
    else:
        colour = np.ones((SIZE, SIZE, 3)) * (0.9 + 0.12 * grain)[..., None] * (0.95 + 0.07 * fine)[..., None]
    floor = int(round(3.0 * scale))
    band = (ys % floor) < max(int(0.12 * scale), 2)
    colour[band] *= 0.82
    width, height = int(round(1.1 * scale)), int(round(1.5 * scale))
    wood = np.array([0.4, 0.27, 0.17])
    for row in range(4):
        for column in range(4):
            x0 = int(round((column * 3.0 + 0.95) * scale))
            y0 = int(round((row * 3.0 + 0.8) * scale))
            frame = max(int(0.12 * scale), 2)
            trim = np.array([0.88, 0.84, 0.76]) if brick else np.array([0.82, 0.78, 0.7])
            colour[y0 - frame:y0 + height + frame, x0 - frame:x0 + width + frame] = trim
            kind = generator.random()
            if kind < 0.15:
                colour[y0:y0 + height, x0:x0 + width] = wood * generator.uniform(0.8, 1.15)
                colour[y0:y0 + height, x0 + width // 2 - 1:x0 + width // 2 + 1] *= 0.6
            else:
                colour[y0:y0 + height, x0:x0 + width] = np.array([0.1, 0.085, 0.075])
                if kind < 0.35:
                    leaf = width // 2
                    tone = wood * generator.uniform(0.8, 1.15)
                    colour[y0:y0 + height, x0 - frame - leaf:x0 - frame] = tone
                    colour[y0:y0 + height, x0 + width + frame:x0 + width + frame + leaf] = tone
            streak = np.clip(1.0 - (np.arange(int(1.2 * scale)) / (1.2 * scale)), 0, 1)[:, None]
            below = slice(y0 - frame - int(1.2 * scale), y0 - frame)
            if below.start > 0:
                colour[below, x0:x0 + width] *= (1.0 - 0.12 * streak[::-1])[..., None]
    return np.clip(colour, 0, 1)


def facade_library(cache_dir, tiles):
    texture_dir = os.path.join(cache_dir, "textures")
    for name, brick in (("col_facade", False), ("col_facade_brick", True)):
        image = cached(name, os.path.join(texture_dir, f"{name}_v2.jpg"), lambda brick=brick: facade(brick), quality=88)
        principled_material(name, (1.0, 1.0, 1.0), 0.9, 0.0, image)
        tiles[name] = FACADE_TILE

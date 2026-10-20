import math
import os

import numpy as np

from .materials import (generated_image, image_pixels, linear_color, poly_haven_asset, principled_material,
                        recolored, save_pixels, smooth_stone_pixels)
from .terrain import value_noise

TEXTURED = {
    "plaster": dict(asset="plastered_wall", color=(0.86, 0.83, 0.77), contrast=0.36, roughness=0.9, normal=0.0,
                    tile=2.4),
    "stone": dict(asset="sandstone_blocks_08", color=(0.62, 0.58, 0.51), contrast=0.55, roughness=0.85, normal=0.0),
    "sidewalk": dict(asset="rock_embedded_floor", color=(0.52, 0.49, 0.44), contrast=0.5, roughness=0.92,
                     normal=0.0, tile=2.5, pumice=0.35),
    "paving": dict(asset="rectangular_paving", color=(0.80, 0.77, 0.70), contrast=0.55, roughness=0.8, normal=0.0,
                   tile=7.0, pumice=0.4),
    "floor_sheltered": dict(asset="rock_embedded_floor", color=(0.62, 0.58, 0.52), contrast=0.45, roughness=0.9,
                            normal=0.0, tile=2.5, pumice=0.08),
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
PUMICE = np.array([0.63, 0.60, 0.54])
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


def tile_noise(size, cells, seed, octaves=3):
    rng = np.random.default_rng(seed)
    total = np.zeros((size, size))
    norm = 0.0
    amplitude = 1.0
    for octave in range(octaves):
        count = cells * 2 ** octave
        lattice = rng.random((count, count))
        axis = (np.arange(size) + 0.5) / size * count
        i0 = np.floor(axis).astype(int) % count
        i1 = (i0 + 1) % count
        f = axis - np.floor(axis)
        f = f * f * (3 - 2 * f)
        rows = lattice[i0] * (1 - f)[:, None] + lattice[i1] * f[:, None]
        total += amplitude * (rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :])
        norm += amplitude
        amplitude *= 0.5
    return total / norm


def pumice_cover(size, coverage, seed, clast_px):
    drift = tile_noise(size, 4, seed, 3)
    speck = lapilli(size, 0.18 + 0.3 * coverage, seed + 1, clast_px * 0.5, clast_px * 1.25)
    dense = lapilli(size, 1.6, seed + 3, clast_px * 0.6, clast_px * 1.5)
    threshold = np.quantile(drift, 1.0 - coverage)
    mask = np.clip((drift - threshold) * 14.0 + 0.3, 0, 1)
    return np.clip(np.maximum(speck * 0.85, np.minimum(dense * 1.15, 1.0) * mask), 0, 1)


def pumice_overlay(pixels, coverage, seed, tile):
    size = min(pixels.shape[0], pixels.shape[1])
    rgb = pixels[:size, :size, :3]
    clast_px = max(1.2, 0.018 * size / tile)
    cover = pumice_cover(size, coverage, seed, clast_px)
    tone = 0.84 + 0.22 * tile_noise(size, 24, seed + 2, 2)
    pumice = PUMICE[None, None, :] * tone[..., None]
    return np.clip(rgb * (1 - cover[..., None]) + pumice * cover[..., None], 0, 1)


def pumiced(image, name, path, coverage, seed, tile):
    if os.path.exists(path):
        return image_pixels(path)[0]
    source = image.filepath_raw or image.filepath
    _, pixels = image_pixels(source)
    return save_pixels(name, pumice_overlay(pixels, coverage, seed, tile), path)


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
    owner, edge = voronoi_cells(size, 140, seed)
    rng = np.random.default_rng(seed)
    tone = rng.uniform(0.80, 1.15, 140)[owner]
    grain = value_noise((size, size), 40, seed + 1, 3)
    base = np.array([0.24, 0.235, 0.22])
    colour = base[None, None, :] * (tone * (0.86 + 0.28 * grain))[..., None]
    joint = np.clip(1.0 - edge / 5.0, 0, 1)
    colour *= (1.0 - 0.55 * joint)[..., None]
    v = (np.arange(size) + 0.5) / size
    rut = np.zeros(size)
    for centre in (0.5 - 0.152, 0.5 + 0.152):
        rut = np.maximum(rut, np.clip(1.0 - np.abs(v - centre) / 0.03, 0, 1))
    polish = rut[None, :]
    colour = colour * (1.0 - 0.4 * polish)[..., None] + np.array([0.03, 0.03, 0.03]) * polish[..., None]
    edges = np.clip(1.0 - np.minimum(v, 1 - v) / 0.16, 0, 1)[None, :]
    drift = tile_noise(size, 4, seed + 2, 3)
    pile = np.clip((edges * 0.5 + drift * 0.6 - 0.42) * 2.4, 0, 1)
    cover = np.maximum(pumice_cover(size, 0.3, seed + 3, 2.2) * (1.0 - 0.35 * polish), pile * (0.55 + 0.2 * grain))
    cover = np.maximum(cover, joint * 0.45)
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
    cover = np.maximum(pumice_cover(size, 0.4, seed + 3, 2.0), settled * (0.5 + 0.25 * grain))
    cover *= np.clip(1.0 - imbrex[None, :] * 0.45, 0, 1)
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


def stroke(image, gx, gy, a, b, thickness, colour):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
    image[np.hypot(gx - ax - t * dx, gy - ay - t * dy) < thickness] = colour


def vignette(image, cx, cy, radius, seed, width, height):
    rng = np.random.default_rng(seed)
    gx, gy = np.meshgrid((np.arange(width) + 0.5) / height, (np.arange(height) + 0.5) / height)
    cx = cx * width / height
    dark = np.array([0.30, 0.22, 0.18])
    skin = np.array([0.72, 0.50, 0.34])
    drapery = OCHRE * 0.95 if rng.random() < 0.6 else np.array([0.36, 0.44, 0.40])
    tilt = math.radians(rng.uniform(25.0, 55.0)) * (1 if rng.random() < 0.5 else -1)
    ux, uy = math.sin(tilt), math.cos(tilt)
    size = radius * 1.6
    hip = (cx - ux * size * 0.25, cy - uy * size * 0.25)
    neck = (cx + ux * size * 0.3, cy + uy * size * 0.3)
    stroke(image, gx, gy, (hip[0] - ux * size * 0.45 + uy * size * 0.3, hip[1] - uy * size * 0.45 - ux * size * 0.3),
           (neck[0] - uy * size * 0.35, neck[1] + ux * size * 0.35), size * 0.1, drapery)
    stroke(image, gx, gy, hip, neck, size * 0.07, skin)
    for spread in (0.1, -0.25):
        stroke(image, gx, gy, hip, (hip[0] - ux * size * 0.5 + uy * spread * size,
                                    hip[1] - uy * size * 0.5 - ux * spread * size), size * 0.04, skin)
    for side in (-1, 1):
        stroke(image, gx, gy, neck, (neck[0] + uy * side * size * 0.32 + ux * size * 0.12,
                                     neck[1] - ux * side * size * 0.32 + uy * size * 0.12), size * 0.03, skin)
    head = np.hypot(gx - neck[0] - ux * size * 0.12, gy - neck[1] - uy * size * 0.12) < size * 0.08
    image[head] = skin
    hair = np.hypot(gx - neck[0] - ux * size * 0.16, gy - neck[1] - uy * size * 0.16) < size * 0.05
    image[hair] = dark
    stroke(image, gx, gy, (hip[0] + uy * size * 0.04, hip[1] - ux * size * 0.04),
           (neck[0] + uy * size * 0.04, neck[1] - ux * size * 0.04), size * 0.025, dark)


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
            vignette(image, (x0 + x1) / 2, 0.49, min(0.05, (x1 - x0) * 0.15), seed + index, width, height)
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


MARBLES = [np.array([0.70, 0.74, 0.66]), np.array([0.78, 0.66, 0.42]), np.array([0.86, 0.82, 0.78]),
           np.array([0.30, 0.26, 0.24]), np.array([0.58, 0.32, 0.24]), np.array([0.55, 0.58, 0.50])]


def crustae_pixels(size=512, seed=21):
    cells = 50
    owner, edge = voronoi_cells(size, cells, seed)
    rng = np.random.default_rng(seed)
    kinds = rng.integers(0, len(MARBLES), cells)
    colour = np.stack(MARBLES)[kinds[owner]]
    tone = rng.uniform(0.88, 1.08, cells)[owner]
    grain = tile_noise(size, 16, seed + 1, 3)
    veins = np.abs(np.sin(tile_noise(size, 6, seed + 2, 4) * 26.0 + owner * 0.7))
    vein_colour = np.where((kinds[owner] == 2)[..., None], np.array([0.52, 0.40, 0.50])[None, None, :], colour * 0.72)
    colour = colour * (tone * (0.92 + 0.12 * grain))[..., None]
    colour = np.where((veins < 0.08)[..., None], vein_colour, colour)
    mortar = np.clip(1.0 - (edge - size * 0.006) / 1.2, 0, 1)
    colour = colour * (1 - mortar[..., None]) + np.array([0.80, 0.77, 0.70]) * mortar[..., None]
    return np.clip(colour, 0, 1)


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
        tile = spec.get("tile", width_metres)
        if spec.get("pumice"):
            coverage = spec["pumice"]
            path = os.path.join(texture_dir, f"{name}_{signature}_p{round(coverage * 100):02d}.jpg")
            base = pumiced(base, f"{name}_pumice", path, coverage, len(name) * 7, tile)
        principled_material(name, linear_color(spec["color"]), spec["roughness"], 0.0, base)
        tiles[name] = tile
    for name, spec in PLAIN.items():
        principled_material(name, linear_color(spec["color"]), spec["roughness"], spec.get("metallic", 0.0))
        tiles[name] = 2.0
    generated = {
        "basalt": (basalt_pixels, 4.0, 0.88),
        "terracotta_tiles": (roof_pixels, 3.2, 0.8),
        "fresco": (fresco_pixels, 4.0, 0.75),
        "marble": (lambda: smooth_stone_pixels((0.84, 0.82, 0.78)), 2.5, 0.45),
        "crustae": (crustae_pixels, 1.0, 0.35),
    }
    for name, (build, tile, roughness) in generated.items():
        image = generated_image(name, os.path.join(texture_dir, f"{name}_v5.jpg"), build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, image)
        tiles[name] = tile
    return tiles, credits

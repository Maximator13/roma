import math
import os

import bpy
import numpy as np

from .materials import (image_pixels, linear_color, poly_haven_asset, principled_material, save_pixels,
                        srgb_to_linear)

MOLASSE = (0.80, 0.72, 0.56)
LIMESTONE = (0.74, 0.72, 0.66)
COURSE = 0.64
STONE_TILE = 5.12
ROCK_TILE = 4.0
FOLIAGE_TILE = 1.6
WATER_TILE = 9.0
TOOL_TILE = 2.4
GROUND_TILE = 4.0
GROUND_BASE = (0.74, 0.72, 0.66)
VERSION = "v8"


def periodic_noise(size, beta, seed, stretch=(1.0, 1.0)):
    generator = np.random.default_rng(seed)
    white = generator.normal(0.0, 1.0, (size, size))
    spectrum = np.fft.fft2(white)
    fy = np.fft.fftfreq(size)[:, None] * size / stretch[1]
    fx = np.fft.fftfreq(size)[None, :] * size / stretch[0]
    radius = np.hypot(fx, fy)
    radius[0, 0] = 1.0
    spectrum *= radius ** -beta
    spectrum[0, 0] = 0.0
    field = np.real(np.fft.ifft2(spectrum))
    field -= field.min()
    return field / max(field.max(), 1e-9)


def resample(pixels, size):
    height, width = pixels.shape[:2]
    rows = (np.arange(size) * height / size).astype(int)
    columns = (np.arange(size) * width / size).astype(int)
    return pixels[rows][:, columns]


def luminance(pixels):
    return pixels[..., 0] * 0.2126 + pixels[..., 1] * 0.7152 + pixels[..., 2] * 0.0722


def height_normal(height, strength):
    gradient_y = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / 2
    gradient_x = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / 2
    normal = np.dstack([-gradient_x * strength, -gradient_y * strength, np.ones_like(height)])
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    return normal * 0.5 + 0.5


def course_layout(courses, width_metres, seed):
    generator = np.random.default_rng(seed)
    blocks = []
    for course in range(courses):
        offset = generator.uniform(0, width_metres)
        lengths = []
        remaining = width_metres
        while remaining > 2.6:
            length = generator.uniform(0.95, 2.05)
            lengths.append(length)
            remaining -= length
        if remaining > 1.4:
            lengths.append(remaining)
        else:
            lengths[-1] += remaining
        start = offset
        for length in lengths:
            blocks.append((course, start % width_metres, length))
            start += length
    return blocks


def ashlar_pixels(grain, seed=5, size=1024):
    generator = np.random.default_rng(seed)
    courses = int(round(STONE_TILE / COURSE))
    scale = size / STONE_TILE
    blocks = course_layout(courses, STONE_TILE, seed)
    rows = np.arange(size)[:, None] / scale
    columns = np.arange(size)[None, :] / scale
    tone = np.ones((size, size, 3))
    height = np.zeros((size, size))
    edge = np.full((size, size), 9.0)
    rects = []
    for course, start, length in blocks:
        y0 = course * COURSE
        y1 = y0 + COURSE
        inside_y = (rows >= y0) & (rows < y1)
        local_x = (columns - start) % STONE_TILE
        inside = inside_y & (local_x < length)
        distance = np.minimum(np.minimum(local_x, length - local_x), np.minimum(rows - y0, y1 - rows))
        value = generator.normal(1.0, 0.05)
        warmth = generator.normal(0.0, 0.035)
        block_tone = np.array([value * (1 + warmth), value, value * (1 - warmth * 1.6)])
        fade = 1.0 - 0.06 * (rows - y0) / COURSE
        mask = np.broadcast_to(inside, (size, size))
        tone[mask] = (block_tone[None, None, :] * np.broadcast_to(fade[..., None], (size, size, 1)))[mask]
        pillow = np.clip(distance / 0.09, 0, 1) ** 0.5
        height = np.where(mask, pillow * (0.8 + 0.2 * generator.random()), height)
        edge = np.where(mask, distance, edge)
        if start + length <= STONE_TILE:
            rects.append((start / STONE_TILE, y0 / STONE_TILE, (start + length) / STONE_TILE, y1 / STONE_TILE))
    coarse = periodic_noise(size, 1.6, seed + 1)
    fine = periodic_noise(size, 0.9, seed + 2)
    detail = luminance(resample(grain, size))
    detail = detail / max(float(detail.mean()), 1e-4)
    shells = generator.random((size, size)) > 0.9965
    base = np.array(MOLASSE)
    colour = base[None, None, :] * tone
    colour *= (0.86 + 0.14 * np.clip(detail, 0.4, 1.6))[..., None]
    colour *= (0.93 + 0.12 * coarse)[..., None]
    colour *= (0.97 + 0.06 * fine)[..., None]
    colour = np.where(shells[..., None], np.minimum(colour * 1.25 + 0.05, 1.0), colour)
    joint = np.clip(1.0 - edge / 0.018, 0, 1)
    wear = np.clip(1.0 - edge / 0.07, 0, 1) * (0.5 + 0.5 * fine)
    colour *= (1.0 - 0.36 * joint)[..., None]
    colour *= (1.0 - 0.08 * wear)[..., None]
    for _ in range(46):
        x = generator.uniform(0, size)
        course = generator.integers(1, courses + 1)
        top = min(course * COURSE * scale, size - 1)
        length = generator.uniform(0.3, 2.4) * scale
        width = generator.uniform(2.0, 9.0)
        strength = generator.uniform(0.05, 0.2)
        dark = generator.random() < 0.72
        ys = np.arange(int(max(top - length, 0)), int(top))
        if len(ys) == 0:
            continue
        along = np.clip((top - ys) / length, 0.0, 1.0)
        wobble = x + 3.0 * np.sin(ys / 23.0 + x)
        xs = np.arange(size)
        offsets = (xs[None, :] - wobble[:, None] + size / 2) % size - size / 2
        profile = np.exp(-(offsets / width) ** 2) * (1 - along[:, None]) ** 1.3 * strength
        if dark:
            colour[ys] *= (1.0 - profile * 1.6)[..., None]
        else:
            colour[ys] = colour[ys] * (1 - profile[..., None] * 2.5) + np.array([0.93, 0.92, 0.87]) * profile[..., None] * 2.5
    for course in generator.choice(np.arange(1, courses), 3, replace=False):
        y = int(course * COURSE * scale)
        crust = periodic_noise(size, 1.2, seed + 10 + int(course))[0] > 0.45
        for drip in range(0, 18):
            band = np.clip(1.0 - drip / 18.0, 0, 1)
            row = y - drip
            if row < 0:
                break
            keep = crust & (fine[row] > 0.35 + 0.6 * (1 - band))
            colour[row, keep] = colour[row, keep] * (1 - 0.6 * band) + np.array([0.92, 0.91, 0.86]) * 0.6 * band
    lichen = (periodic_noise(size, 1.3, seed + 4) > 0.8) & (fine > 0.55)
    colour = np.where(lichen[..., None], colour * np.array([0.78, 0.78, 0.74]), colour)
    height = height * (0.85 + 0.15 * fine) + 0.12 * (detail - 1.0) * (height > 0)
    return np.clip(colour, 0, 1), height_normal(height, 7.0), rects


def tool_mark_pixels(seed=8, size=512):
    scale = size / TOOL_TILE
    rows = np.arange(size)[:, None] / scale
    columns = np.arange(size)[None, :] / scale
    band = 0.3
    index = np.floor(rows / band)
    direction = np.where(index % 2 == 0, 1.0, -1.0)
    phase = (columns + direction * (rows % band) * 1.1) / 0.06
    grooves = 0.5 + 0.5 * np.sin(phase * 2 * math.pi)
    noise = periodic_noise(size, 1.1, seed)
    broad = periodic_noise(size, 1.7, seed + 1)
    seam = np.clip(1.0 - np.abs((rows % band) - band / 2) / (band / 2), 0, 1) ** 3
    beds = 0.5 + 0.5 * np.sin(rows * 2 * math.pi / 0.8 + 3.0 * periodic_noise(size, 1.5, seed + 2))
    height = grooves * 0.5 * (0.5 + 0.5 * noise) - seam * 0.4 + noise * 0.35
    value = (0.82 + 0.22 * grooves * (0.6 + 0.4 * noise) - 0.12 * seam) * (0.95 + 0.05 * beds)
    colour = np.array(MOLASSE)[None, None, :] * value[..., None]
    weather = np.clip((broad - 0.45) * 2.5, 0, 1) * 0.35
    colour = colour * (1 - weather[..., None]) + np.array([0.52, 0.5, 0.45]) * weather[..., None]
    return np.clip(colour, 0, 1), height_normal(height, 5.0)


def foliage_pixels(seed=12, size=512):
    clumps = periodic_noise(size, 1.25, seed)
    leaves = periodic_noise(size, 0.55, seed + 1)
    value = 0.62 + 0.55 * clumps + 0.3 * (leaves - 0.5)
    gaps = (clumps < 0.28) & (leaves < 0.45)
    value = np.where(gaps, value * 0.45, value)
    colour = np.dstack([value * 0.96, value, value * 0.9])
    height = clumps + 0.4 * leaves
    return np.clip(colour, 0, 1), height_normal(height, 9.0)


def water_normal_pixels(seed=21, size=512):
    swell = periodic_noise(size, 1.9, seed, (2.5, 1.0))
    ripple = periodic_noise(size, 1.2, seed + 1, (1.6, 1.0))
    return height_normal(swell * 3.0 + ripple * 0.8, 6.0)


def cached_image(name, path, build, colorspace="sRGB", quality=92):
    if os.path.exists(path):
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = colorspace
        return image
    return save_pixels(name, build(), path, quality=quality, colorspace=colorspace)


def recolour(source, target, contrast):
    _, pixels = image_pixels(source)
    light = luminance(pixels)
    ratio = 1.0 + (light / max(float(light.mean()), 1e-4) - 1.0) * contrast
    return np.dstack([np.clip(target[c] * ratio, 0, 1) for c in range(3)])


def build_pont_library(cache_dir):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    texture_dir = os.path.join(cache_dir, "textures")
    os.makedirs(texture_dir, exist_ok=True)
    credits = {}
    tiles = {}
    grain_diffuse, _, _ = poly_haven_asset("old_sandstone_02", source_dir, credits)
    rock_diffuse, _, _ = poly_haven_asset("dry_riverbed_rock", source_dir, credits)
    base_path = os.path.join(texture_dir, f"molasse_{VERSION}.jpg")
    normal_path = os.path.join(texture_dir, f"molasse_normal_{VERSION}.jpg")
    rect_path = os.path.join(texture_dir, f"molasse_rects_{VERSION}.npy")
    if not (os.path.exists(base_path) and os.path.exists(normal_path) and os.path.exists(rect_path)):
        _, grain = image_pixels(grain_diffuse)
        colour, normal, rects = ashlar_pixels(grain[..., :3])
        save_pixels("molasse_base", colour, base_path, quality=93)
        save_pixels("molasse_normal", resample(normal, 512), normal_path, quality=95, colorspace="Non-Color")
        np.save(rect_path, np.array(rects))
    base = bpy.data.images.load(base_path, check_existing=True)
    normal = bpy.data.images.load(normal_path, check_existing=True)
    normal.colorspace_settings.name = "Non-Color"
    principled_material("molasse", linear_color(MOLASSE), 0.86, 0.0, base, normal, 0.9)
    tiles["molasse"] = STONE_TILE
    rects = [tuple(rect) for rect in np.load(rect_path)]
    rock_path = os.path.join(texture_dir, f"urgonian_{VERSION}.jpg")
    rock = cached_image("urgonian", rock_path, lambda: resample(recolour(rock_diffuse, LIMESTONE, 0.75), 512))
    principled_material("urgonian", linear_color(LIMESTONE), 0.9, 0.0, rock)
    tiles["urgonian"] = ROCK_TILE
    tool_base = os.path.join(texture_dir, f"quarry_face_{VERSION}.jpg")
    tool_normal = os.path.join(texture_dir, f"quarry_face_normal_{VERSION}.jpg")
    if not (os.path.exists(tool_base) and os.path.exists(tool_normal)):
        colour, normal_pixels = tool_mark_pixels()
        save_pixels("quarry_face_base", colour, tool_base, quality=92)
        save_pixels("quarry_face_normal", resample(normal_pixels, 256), tool_normal, quality=95, colorspace="Non-Color")
    quarry_base = bpy.data.images.load(tool_base, check_existing=True)
    quarry_normal = bpy.data.images.load(tool_normal, check_existing=True)
    quarry_normal.colorspace_settings.name = "Non-Color"
    principled_material("quarry_face", linear_color(MOLASSE), 0.9, 0.0, quarry_base, quarry_normal, 1.0)
    tiles["quarry_face"] = TOOL_TILE
    soil_diffuse, soil_normal, _ = poly_haven_asset("dry_ground_rocks", source_dir, credits)
    ground_base = os.path.join(texture_dir, "ground_v10.jpg")
    ground_normal = os.path.join(texture_dir, "ground_normal_v10.jpg")
    if not (os.path.exists(ground_base) and os.path.exists(ground_normal)):
        save_pixels("ground_base", resample(recolour(soil_diffuse, GROUND_BASE, 0.55), 512), ground_base, quality=90)
        _, normal_pixels = image_pixels(soil_normal)
        save_pixels("ground_normal", resample(normal_pixels[..., :3], 256), ground_normal, quality=93,
                    colorspace="Non-Color")
    ground_image = bpy.data.images.load(ground_base, check_existing=True)
    ground_normal_image = bpy.data.images.load(ground_normal, check_existing=True)
    ground_normal_image.colorspace_settings.name = "Non-Color"
    principled_material("ground", linear_color(GROUND_BASE), 0.95, 0.0, ground_image, ground_normal_image, 0.8)
    tiles["ground"] = GROUND_TILE
    leaf_base = os.path.join(texture_dir, f"foliage_{VERSION}.jpg")
    leaf_normal = os.path.join(texture_dir, f"foliage_normal_{VERSION}.jpg")
    if not (os.path.exists(leaf_base) and os.path.exists(leaf_normal)):
        colour, normal_pixels = foliage_pixels()
        save_pixels("foliage_base", colour, leaf_base, quality=90)
        save_pixels("foliage_normal", resample(normal_pixels, 256), leaf_normal, quality=93, colorspace="Non-Color")
    foliage = bpy.data.images.load(leaf_base, check_existing=True)
    foliage_normal = bpy.data.images.load(leaf_normal, check_existing=True)
    foliage_normal.colorspace_settings.name = "Non-Color"
    principled_material("foliage", (1.0, 1.0, 1.0), 0.92, 0.0, foliage, foliage_normal, 0.7)
    tiles["foliage"] = FOLIAGE_TILE
    water_path = os.path.join(texture_dir, f"water_normal_{VERSION}.jpg")
    water = cached_image("water_normal", water_path, lambda: resample(water_normal_pixels(), 256), colorspace="Non-Color", quality=95)
    principled_material("river", linear_color((0.55, 0.68, 0.62)), 0.15, 0.0, None, water, 0.35)
    tiles["river"] = WATER_TILE
    for name, colour, roughness in (("matte", (1.0, 1.0, 1.0), 0.88), ("cloth", (1.0, 1.0, 1.0), 0.95),
                                    ("skin", (1.0, 1.0, 1.0), 0.6), ("lime_wash", (1.0, 1.0, 1.0), 0.8)):
        principled_material(name, colour, roughness, 0.0)
        tiles[name] = 2.0
    return tiles, credits, rects


def linear(colour):
    return tuple(srgb_to_linear(component) for component in colour)

import os

import bpy
import numpy as np

from . import alexandrie_materials as amat
from .materials import linear_color, principled_material, save_pixels
from .pantheon_materials import ambient_colour, normalise, smoothstep, voronoi
from .pont_materials import height_normal, luminance, periodic_noise

MARBLE_TILE = 3.2
ASHLAR_TILE = 4.8
ASHLAR_COURSES = 6
POLYGONAL_TILE = 9.0
KNOWN = {"plaster", "paving", "limestone", "matte", "water", "bronze_gilt", "shadow_void", "terracotta_tiles",
         "marble", "granite", "granite_glyphs", "marble_ashlar", "paving_polygonal", "ground_gravel"}
RENAME = dict(amat.RENAME)
RENAME.update({"foliage": "matte", "bark": "matte", "reed": "matte", "foliage_dark": "matte",
               "foliage_olive": "matte", "foliage_plane": "matte", "foliage_cypress": "matte", "urgonian": "limestone",
               "plaster_grey": "plaster", "plaster_white": "plaster", "plaster_ochre": "plaster"})


def remap(builder):
    builder.materials = [RENAME.get(name, name) for name in builder.materials]
    builder.materials = [name if name in KNOWN else "matte" for name in builder.materials]
    return amat.remap(builder)


def warm_marble(source, seed=41):
    size = source.shape[0]
    t = normalise(luminance(source))
    base = np.array([0.985, 0.955, 0.90])
    vein = np.array([0.80, 0.78, 0.76])
    colour = base[None, None, :] * (0.93 + 0.07 * t[..., None]) * (1.0 - 0.18 * (1.0 - t[..., None]) ** 3)
    colour = colour * (1.0 - 0.1 * (1.0 - t[..., None]) ** 6) + vein * 0.0
    grime = periodic_noise(size, 1.7, seed)
    honey = np.array([1.0, 0.95, 0.84])
    amount = smoothstep(grime, 0.45, 0.9)[..., None] * 0.35
    colour = colour * (1.0 - amount) + colour * honey * amount
    return np.clip(colour * (0.96 + 0.06 * periodic_noise(size, 2.2, seed + 1))[..., None], 0, 1)


def marble_ashlar(source, seed=43):
    rng = np.random.default_rng(seed)
    size = source.shape[0]
    scale = size / ASHLAR_TILE
    edges = np.linspace(0, size, ASHLAR_COURSES + 1).astype(int)
    grain = normalise(luminance(source))
    colour = np.zeros((size, size, 3))
    height = np.zeros((size, size))
    base = np.array([0.97, 0.94, 0.88])
    for row in range(ASHLAR_COURSES):
        y0, y1 = edges[row], edges[row + 1]
        x = int(rng.integers(0, size))
        start = x
        while x < start + size:
            length = int(rng.uniform(1.2, 2.4) * scale)
            length = min(length, start + size - x)
            if start + size - x - length < 0.6 * scale:
                length = start + size - x
            columns = np.arange(x, x + length) % size
            tone = rng.normal(1.0, 0.03)
            warmth = np.array([1.0, 1.0 - abs(rng.normal(0.0, 0.01)), 1.0 - abs(rng.normal(0.0, 0.025))])
            ly = np.arange(y1 - y0)[:, None]
            lx = np.arange(length)[None, :]
            edge = np.minimum(np.minimum(lx, length - 1 - lx), np.minimum(ly, y1 - y0 - 1 - ly))
            block = grain[y0:y1][:, columns]
            shade = (0.93 + 0.09 * block) * np.where(edge < 2, 0.66, 1.0) * np.where(edge < 5, 0.96, 1.0)
            colour[y0:y1][:, columns] = shade[..., None] * base * tone * warmth
            height[y0:y1][:, columns] = np.where(edge < 2, 0.0, 0.5 + 0.05 * block)
            x += length
    grime = periodic_noise(size, 1.6, seed + 1, stretch=(0.3, 3.0))
    colour *= (0.92 + 0.1 * grime)[..., None]
    return np.clip(colour, 0, 1), height_normal(height, 5.0)


def polygonal_paving(source, seed=47):
    rng = np.random.default_rng(seed)
    first, second, owner = voronoi(150, seed)
    size = first.shape[0]
    tones = rng.normal(1.0, 0.05, 150)
    warm = rng.random(150) < 0.3
    base = np.array([0.90, 0.86, 0.78])
    stone = base[None, None, :] * tones[owner][..., None]
    stone = np.where(warm[owner][..., None], stone * np.array([1.0, 0.95, 0.86]), stone)
    texture = 0.9 + 0.12 * normalise(luminance(source))[:size, :size]
    stone *= texture[..., None]
    gap = second - first
    joint = 1.0 - smoothstep(gap, 0.0, 3.0)
    dirt = np.array([0.42, 0.38, 0.32])
    colour = stone * (1.0 - joint[..., None]) + dirt * joint[..., None]
    wear = periodic_noise(size, 1.8, seed + 3)
    colour *= (0.93 + 0.1 * wear)[..., None]
    relief = smoothstep(gap, 0.0, 5.0)
    return np.clip(colour, 0, 1), height_normal(relief, 3.0)


def gravel_pixels(size=512, seed=53):
    rng = np.random.default_rng(seed)
    base = np.array([0.82, 0.70, 0.52])
    broad = periodic_noise(size, 1.6, seed)
    fine = periodic_noise(size, 0.6, seed + 1)
    colour = base[None, None, :] * (0.86 + 0.18 * broad[..., None]) * (0.94 + 0.1 * fine[..., None])
    count = size * size // 60
    xs = rng.integers(0, size, count)
    ys = rng.integers(0, size, count)
    tones = rng.uniform(0.7, 1.15, count)
    for dx in (0, 1):
        for dy in (0, 1):
            colour[(ys + dy) % size, (xs + dx) % size] *= tones[:, None]
    return np.clip(colour, 0, 1)


def ephese_textures(cache_dir, texture_dir, credits):
    source = None
    paths = {key: os.path.join(texture_dir, f"{key}_e1.jpg") for key in ("marble", "marble_ashlar",
                                                                         "marble_ashlar_normal", "polygonal",
                                                                         "polygonal_normal")}
    if not all(os.path.exists(path) for path in paths.values()):
        source = ambient_colour("Marble021", os.path.join(cache_dir, "src", "ambientcg"), credits)
        save_pixels("marble_e", warm_marble(source), paths["marble"], quality=92)
        colour, normal = marble_ashlar(source)
        save_pixels("marble_ashlar_e", colour, paths["marble_ashlar"], quality=92)
        save_pixels("marble_ashlar_normal_e", normal, paths["marble_ashlar_normal"], quality=95,
                    colorspace="Non-Color")
        colour, normal = polygonal_paving(source)
        save_pixels("polygonal_e", colour, paths["polygonal"], quality=92)
        save_pixels("polygonal_normal_e", normal, paths["polygonal_normal"], quality=95, colorspace="Non-Color")
    else:
        ambient_colour("Marble021", os.path.join(cache_dir, "src", "ambientcg"), credits)
    images = {}
    for key, path in paths.items():
        image = bpy.data.images.load(path, check_existing=True)
        if key.endswith("normal"):
            image.colorspace_settings.name = "Non-Color"
        images[key] = image
    return images


def build_library(cache_dir):
    tiles, credits = amat.build_library(cache_dir)
    texture_dir = os.path.join(cache_dir, "textures")
    images = ephese_textures(cache_dir, texture_dir, credits)
    principled_material("marble", linear_color((0.97, 0.95, 0.91)), 0.42, 0.0, images["marble"])
    tiles["marble"] = MARBLE_TILE
    principled_material("marble_ashlar", linear_color((0.95, 0.93, 0.88)), 0.55, 0.0, images["marble_ashlar"],
                        images["marble_ashlar_normal"], 0.8)
    tiles["marble_ashlar"] = ASHLAR_TILE
    principled_material("paving_polygonal", linear_color((0.9, 0.86, 0.78)), 0.78, 0.0, images["polygonal"],
                        images["polygonal_normal"], 0.7)
    tiles["paving_polygonal"] = POLYGONAL_TILE
    gravel_path = os.path.join(texture_dir, "gravel_e1.jpg")
    if not os.path.exists(gravel_path):
        save_pixels("gravel_e", gravel_pixels(), gravel_path, quality=90)
    gravel = bpy.data.images.load(gravel_path, check_existing=True)
    principled_material("ground_gravel", linear_color((0.82, 0.70, 0.52)), 0.92, 0.0, gravel)
    tiles["ground_gravel"] = 6.0
    water = bpy.data.materials.get("water")
    if water is not None and water.node_tree is not None:
        for node in water.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Roughness"].default_value = 0.45
                node.inputs["Specular IOR Level"].default_value = 0.22
    return tiles, credits

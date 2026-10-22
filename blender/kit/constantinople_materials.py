import os

import bpy
import numpy as np

from .colisee_materials import colisee_library
from .materials import linear_color, principled_material, save_pixels
from .pantheon_materials import build_library as pantheon_library
from .pantheon_materials import cached
from .pont_materials import height_normal, periodic_noise

SIZE = 1024
BANDED_TILE = 4.4
LEAD_TILE = 2.4
GOLD_TILE = 1.2
SAND_TILE = 4.0
VERSIONS = {"lead": "v6", "sand": "v6"}
RENAME = {"lens_ashlar": "col_travertine", "weathered_ashlar": "col_travertine", "stone": "col_travertine",
          "lens_smooth": "marble_white", "lens_fluted": "marble_white", "frieze_rinceau": "marble_white",
          "marble": "marble_white", "roof_flat": "terracotta_tiles", "roof_tiles": "terracotta_tiles",
          "plank_wood": "matte", "dark_wood": "matte", "velum_linen": "matte", "arena_sand": "sand",
          "paving": "travertine", "paving_stone": "travertine", "sidewalk": "travertine", "arles_stone": "col_travertine",
          "bark": "matte", "basalt": "granite_grey", "fresco": "plaster", "crustae": "floor_sectile"}


def banded(seed=7):
    generator = np.random.default_rng(seed)
    scale = SIZE / BANDED_TILE
    colour = np.zeros((SIZE, SIZE, 3))
    height = np.zeros((SIZE, SIZE))
    mortar = np.array([0.86, 0.74, 0.66])
    stone = np.array([0.90, 0.84, 0.70])
    rows = []
    y = 0.0
    for course in range(6):
        rows.append((y, 0.28, "stone"))
        y += 0.28
    for course in range(5):
        rows.append((y, 0.1, "brick"))
        y += 0.1
    factor = BANDED_TILE / y
    fine = periodic_noise(SIZE, 0.7, seed + 1)
    coarse = periodic_noise(SIZE, 1.8, seed + 2)
    colour[:] = mortar
    for start, size, kind in rows:
        y0 = int(round(start * factor * scale))
        y1 = int(round((start + size) * factor * scale))
        joint = max(2, int(round((0.035 if kind == "brick" else 0.018) * factor * scale)))
        x = generator.uniform(0, SIZE)
        end = x + SIZE
        while x < end:
            length = (generator.uniform(0.25, 0.4) if kind == "brick" else generator.uniform(0.5, 1.1)) * scale
            columns = np.arange(int(x), int(x + length) - 2) % SIZE
            value = generator.normal(1.0, 0.06 if kind == "stone" else 0.1)
            if kind == "brick":
                hue = generator.normal(0.0, 1.0)
                tone = np.array([0.72 + 0.05 * hue, 0.36 + 0.04 * hue, 0.22 + 0.015 * hue]) * value
            else:
                tone = stone * value * np.array([1.0, 1.0 - abs(generator.normal(0, 0.02)), 1.0 - abs(generator.normal(0, 0.04))])
            rows_px = np.arange(y0, max(y1 - joint, y0 + 1))
            colour[np.ix_(rows_px, columns)] = tone
            height[np.ix_(rows_px, columns)] = 1.0
            x += length
    colour *= (0.9 + 0.16 * fine)[..., None]
    colour *= (0.92 + 0.12 * coarse)[..., None]
    return np.clip(colour, 0, 1), height_normal(height * 0.7 + 0.3 * fine, 4.0)


def lead(seed=11):
    fine = periodic_noise(SIZE // 2, 0.8, seed)
    coarse = periodic_noise(SIZE // 2, 1.9, seed + 1)
    size = SIZE // 2
    u = (np.arange(size) + 0.5) / size
    seam = np.clip(1.0 - np.abs((u * 3) % 1.0 - 0.5) / 0.03, 0, 1)
    lap = np.clip(1.0 - np.abs((u * 2) % 1.0 - 0.05) / 0.025, 0, 1)
    base = np.array([0.48, 0.48, 0.47])
    value = (0.86 + 0.2 * coarse + 0.06 * fine)[..., None]
    colour = base[None, None, :] * value
    colour *= (1.0 + 0.12 * seam[None, :, None])
    colour *= (1.0 - 0.18 * lap[:, None, None])
    height = seam[None, :] * 0.8 - lap[:, None] * 0.4 + 0.1 * fine
    return np.clip(colour, 0, 1), height_normal(height, 3.0)


def gold_mosaic(seed=13):
    generator = np.random.default_rng(seed)
    cells = 96
    pixel = SIZE / cells
    jitter = generator.normal(0.0, 1.0, (cells, cells))
    gold = np.array([0.98, 0.76, 0.34])
    tone = gold[None, None, :] * (1.0 + 0.1 * jitter[..., None])
    tone[..., 2] *= 1.0 + 0.2 * generator.normal(0.0, 1.0, (cells, cells))
    silver = generator.random((cells, cells)) < 0.025
    tone[silver] = np.array([0.86, 0.86, 0.82])
    index = (np.arange(SIZE) / pixel).astype(int)
    colour = tone[index][:, index]
    local = (np.arange(SIZE) % pixel) / pixel
    edge = np.minimum(local, 1 - local)
    grout = np.clip(1.0 - np.minimum(edge[:, None], edge[None, :]) / 0.12, 0, 1)
    colour *= (1.0 - 0.55 * grout)[..., None]
    height = 1.0 - grout
    return np.clip(colour, 0, 1), height_normal(height, 2.0)


def sand(seed=17):
    fine = periodic_noise(SIZE // 2, 0.6, seed)
    coarse = periodic_noise(SIZE // 2, 1.7, seed + 1)
    base = np.array([0.74, 0.56, 0.36])
    colour = base[None, None, :] * (0.84 + 0.2 * coarse + 0.1 * fine)[..., None]
    return np.clip(colour, 0, 1)


def emissive(name, colour, strength, base=(0.9, 0.9, 0.9)):
    material = principled_material(name, linear_color(base), 0.4, 0.0, vertex_color=False)
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Emission Color"].default_value = (*linear_color(colour), 1.0)
    shader.inputs["Emission Strength"].default_value = strength
    return material


def glow(material, colour, strength):
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Emission Color"].default_value = (*linear_color(colour), 1.0)
    shader.inputs["Emission Strength"].default_value = strength


def build_library(cache_dir):
    tiles, credits = pantheon_library(cache_dir)
    colisee_library(cache_dir, tiles, credits)
    texture_dir = os.path.join(cache_dir, "textures")

    def path(name):
        return os.path.join(texture_dir, f"cp_{name}_{VERSIONS.get(name.replace('_normal', ''), 'v5')}.jpg")
    for name, build, tile, roughness, metallic, normal_strength in (
            ("banded", banded, BANDED_TILE, 0.86, 0.0, 0.8), ("lead", lead, LEAD_TILE, 0.75, 0.0, 0.6),
            ("gold_mosaic", gold_mosaic, GOLD_TILE, 0.45, 0.35, 0.7)):
        if os.path.exists(path(name)) and os.path.exists(path(f"{name}_normal")):
            colour = cached(name, path(name), None)
            normal = cached(f"{name}_normal", path(f"{name}_normal"), None, "Non-Color")
        else:
            pixels, normals = build()
            colour = save_pixels(name, pixels, path(name), quality=92)
            normal = save_pixels(f"{name}_normal", normals, path(f"{name}_normal"), quality=94, colorspace="Non-Color")
        principled_material(name, (1.0, 1.0, 1.0), roughness, metallic, colour, normal, normal_strength)
        tiles[name] = tile
    glow(bpy.data.materials["gold_mosaic"], (1.0, 0.74, 0.34), 0.15)
    principled_material("sand", (1.0, 1.0, 1.0), 0.95, 0.0, cached("sand", path("sand"), sand))
    tiles["sand"] = SAND_TILE
    principled_material("water", linear_color((0.05, 0.24, 0.36)), 0.06, 0.0)
    bpy.data.materials["water"].use_backface_culling = True
    principled_material("pool", linear_color((0.10, 0.26, 0.30)), 0.05, 0.0)
    beam = emissive("light_beam", (1.0, 0.86, 0.6), 1.1, (1.0, 0.9, 0.75))
    beam_shader = next(node for node in beam.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    beam_shader.inputs["Alpha"].default_value = 0.045
    beam.surface_render_method = "BLENDED"
    beam.use_backface_culling = False
    principled_material("silver", (0.86, 0.86, 0.84), 0.22, 1.0)
    principled_material("glass_dark", linear_color((0.16, 0.19, 0.22)), 0.12, 0.0)
    emissive("glass_lit", (1.0, 0.9, 0.72), 2.2)
    emissive("flame", (1.0, 0.7, 0.3), 6.0, (1.0, 0.8, 0.5))
    for name in ("pool", "silver", "glass_dark", "glass_lit", "flame", "light_beam"):
        tiles[name] = 2.0
    return tiles, credits


def remap(builder):
    names = [RENAME.get(name, name) for name in builder.materials]
    names = [name if name in bpy.data.materials else "matte" for name in names]
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

import os

import numpy as np

from .alexandrie_materials import limestone_material
from .materials import generated_image, linear_color, poly_haven_asset, principled_material, recolored
from .pont_materials import height_normal, periodic_noise
from .terrain import value_noise

TEXTURED = {
    "plaster": dict(asset="plastered_wall", color=(0.98, 0.95, 0.89), contrast=0.34, roughness=0.86, tile=2.4),
    "paving": dict(asset="rectangular_paving", color=(0.93, 0.88, 0.78), contrast=0.5, roughness=0.8, tile=5.0),
}
PLAIN = {
    "matte": dict(color=(1.0, 1.0, 1.0), roughness=0.86),
    "water": dict(color=(0.10, 0.30, 0.36), roughness=0.06),
    "bronze_gilt": dict(color=(0.86, 0.50, 0.09), roughness=0.36, metallic=1.0),
    "bronze": dict(color=(0.20, 0.11, 0.05), roughness=0.5, metallic=1.0),
    "ivory": dict(color=(0.96, 0.89, 0.74), roughness=0.32),
    "dark_stone": dict(color=(0.035, 0.033, 0.032), roughness=0.07),
    "oil": dict(color=(0.02, 0.018, 0.015), roughness=0.05),
    "gold_glow": dict(color=(0.86, 0.50, 0.09), roughness=0.32, metallic=1.0),
}
GLOW = {"bronze_gilt": ((0.95, 0.62, 0.2), 0.1), "gold_glow": ((0.98, 0.70, 0.30), 0.18)}
RENAME = {"weathered_ashlar": "limestone", "lens_ashlar": "limestone", "stone": "limestone", "lens_smooth": "marble",
          "lens_fluted": "plaster", "frieze_rinceau": "marble", "roof_flat": "terracotta_tiles",
          "roof_tiles": "terracotta_tiles", "arena_sand": "paving", "velum_linen": "matte", "plank_wood": "matte",
          "dark_wood": "matte", "sidewalk": "paving", "floor_sheltered": "paving", "basalt": "paving",
          "paving_stone": "paving", "crustae": "marble", "fresco": "plaster", "river_water": "water", "sea": "water",
          "garden_green": "matte", "arles_stone": "limestone", "marble_white": "marble", "travertine": "limestone",
          "stucco": "plaster", "granite": "marble", "granite_grey": "marble", "col_bronze_patina": "bronze",
          "col_slabs": "paving", "bark": "matte", "shadow_void": "shadow_void"}


def glow(material, colour, strength):
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Emission Color"].default_value = (*linear_color(colour), 1.0)
    shader.inputs["Emission Strength"].default_value = strength


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


def tile_pixels(base, size=512, seed=9, channels=6, courses=5):
    u = (np.arange(size) + 0.5) / size
    phase = (u * channels) % 1.0
    imbrex = np.clip(1.0 - np.abs(phase - 0.82) / 0.13, 0, 1)
    gutter = np.clip(1.0 - np.abs(phase - 0.6) / 0.08, 0, 1)
    v = (np.arange(size) + 0.5) / size
    course = (v * courses) % 1.0
    lip = np.clip(1.0 - course / 0.06, 0, 1)
    rng = np.random.default_rng(seed)
    tile_tone = rng.uniform(0.84, 1.12, (courses, channels))
    tone = tile_tone[(v * courses).astype(int) % courses][:, (u * channels).astype(int) % channels]
    shade = (1.0 + 0.16 * np.sqrt(imbrex)[None, :] - 0.3 * gutter[None, :]) * (1.0 - 0.24 * lip[:, None]) * tone
    grain = value_noise((size, size), 24, seed + 1, 3)
    lichen = np.clip((value_noise((size, size), 7, seed + 2, 3) - 0.62) * 3.0, 0, 1) * 0.35
    colour = np.array(base)[None, None, :] * (shade * (0.9 + 0.2 * grain))[..., None]
    grey = np.array([0.55, 0.53, 0.47])[None, None, :] * (0.9 + 0.2 * grain)[..., None]
    return np.clip(colour * (1 - lichen[..., None]) + grey * lichen[..., None], 0, 1)


def marble_pixels(size=512, seed=5):
    base = np.array([0.95, 0.93, 0.88])
    veins = periodic_noise(size, 1.6, seed, stretch=(0.35, 2.4))
    ridge = 1.0 - np.abs(veins - 0.5) * 2.0
    vein = np.clip((ridge - 0.86) * 6.0, 0, 1)
    cloud = periodic_noise(size, 1.9, seed + 1)
    tone = 0.95 + 0.07 * cloud - 0.16 * vein
    warm = np.dstack([tone, tone * 0.995, tone * (0.97 + 0.03 * cloud)])
    return np.clip(base[None, None, :] * warm, 0, 1)


def brick_pixels(size=512, seed=21):
    rng = np.random.default_rng(seed)
    rows = 14
    brick_h = size // rows
    colour = np.zeros((size, size, 3))
    height = np.zeros((size, size))
    grain = periodic_noise(size, 1.2, seed + 1)
    mortar = np.array([0.82, 0.77, 0.67])
    for row in range(rows):
        y0 = row * brick_h
        y1 = size if row == rows - 1 else y0 + brick_h
        offset = (row % 2) * size // 8
        x = -offset
        while x < size:
            length = int(rng.uniform(0.2, 0.3) * size)
            tone = np.array([0.70, 0.36, 0.22]) * rng.uniform(0.82, 1.12)
            tone[1] *= rng.uniform(0.9, 1.1)
            columns = np.arange(x, x + length) % size
            ly = np.arange(y1 - y0)[:, None]
            lx = np.arange(length)[None, :]
            edge = np.minimum(np.minimum(lx, length - 1 - lx), np.minimum(ly, y1 - y0 - 1 - ly))
            joint = edge < 3
            block = grain[y0:y1][:, columns]
            shade = 0.88 + 0.22 * block
            pixels = np.where(joint[..., None], mortar[None, None, :] * shade[..., None],
                              tone[None, None, :] * shade[..., None])
            colour[y0:y1][:, columns] = pixels
            height[y0:y1][:, columns] = np.where(joint, 0.0, 0.6 + 0.2 * block)
            x += length
    return np.clip(colour, 0, 1), height_normal(height, 5.0)


def build_library(cache_dir):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    texture_dir = os.path.join(cache_dir, "textures")
    os.makedirs(texture_dir, exist_ok=True)
    credits = {}
    tiles = {}
    for name, spec in TEXTURED.items():
        diffuse, _, width_metres = poly_haven_asset(spec["asset"], source_dir, credits)
        signature = "".join(f"{round(value * 100):02d}" for value in (*spec["color"], spec["contrast"]))
        base = recolored(diffuse, spec["color"], spec["contrast"], os.path.join(texture_dir, f"{name}_{signature}.jpg"),
                         name)
        principled_material(name, linear_color(spec["color"]), spec["roughness"], 0.0, base)
        tiles[name] = spec.get("tile", width_metres)
    limestone_material(cache_dir, texture_dir, credits)
    tiles["limestone"] = 6.0
    for name, spec in PLAIN.items():
        linear = name in ("bronze_gilt", "bronze", "water", "matte", "gold_glow")
        color = spec["color"] if linear else linear_color(spec["color"])
        material = principled_material(name, color, spec["roughness"], spec.get("metallic", 0.0),
                                       vertex_color=name != "water")
        if name in GLOW:
            glow(material, *GLOW[name])
        if name == "oil":
            shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
            shader.inputs["Specular IOR Level"].default_value = 0.2
        tiles[name] = 2.0
    flame = principled_material("flame", linear_color((1.0, 0.8, 0.5)), 0.4, 0.0, vertex_color=False)
    glow(flame, (1.0, 0.68, 0.28), 4.0)
    tiles["flame"] = 2.0
    generated = {
        "terracotta_tiles": (lambda: tile_pixels((0.74, 0.37, 0.22)), 3.2, 0.74),
        "marble": (marble_pixels, 2.4, 0.34),
    }
    for name, (build, tile, roughness) in generated.items():
        image = generated_image(name, os.path.join(texture_dir, f"olympie_{name}_v1.jpg"), build)
        principled_material(name, (0.8, 0.8, 0.8), roughness, 0.0, image)
        tiles[name] = tile
    brick_colour = os.path.join(texture_dir, "olympie_brick_v1.jpg")
    brick_normal = os.path.join(texture_dir, "olympie_brick_normal_v1.jpg")
    pair = {}

    def brick_pair():
        if "value" not in pair:
            pair["value"] = brick_pixels()
        return pair["value"]
    colour = generated_image("brick", brick_colour, lambda: brick_pair()[0])
    normal = generated_image("brick_normal", brick_normal, lambda: brick_pair()[1], colorspace="Non-Color", quality=95)
    principled_material("brick", (0.7, 0.4, 0.3), 0.85, 0.0, colour, normal, 0.8)
    tiles["brick"] = 1.6
    principled_material("shadow_void", linear_color((0.05, 0.045, 0.04)), 1.0)
    tiles["shadow_void"] = 2.0
    return tiles, credits

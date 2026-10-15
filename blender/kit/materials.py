import json
import math
import os
import urllib.request

import bpy
import numpy as np

POLY_HAVEN_FILES = "https://api.polyhaven.com/files/{}"
POLY_HAVEN_INFO = "https://api.polyhaven.com/info/{}"
POLY_HAVEN_LICENCE = "CC0 1.0 (https://polyhaven.com/license)"
USER_AGENT = {"User-Agent": "roma-scene-builder/1.0"}

TEXTURED = {
    "lens_ashlar": dict(asset="sandstone_blocks_08", color=(0.89, 0.86, 0.79), contrast=0.42, roughness=0.62,
                        normal=0.0),
    "weathered_ashlar": dict(asset="sandstone_blocks_08", color=(0.80, 0.73, 0.60), contrast=0.5, roughness=0.8,
                             normal=0.12),
    "plaster": dict(asset="yellow_plaster", color=(0.93, 0.91, 0.86), contrast=0.3, roughness=0.88, normal=0.0),
    "arena_sand": dict(asset="sand_01", color=(0.84, 0.72, 0.53), contrast=0.45, roughness=0.95, normal=0.0,
                       tile=3.0),
    "paving": dict(asset="rectangular_paving", color=(0.86, 0.80, 0.68), contrast=0.62, roughness=0.8,
                   normal=0.25, tile=8.0),
}

PLAIN = {
    "bronze_gilt": dict(color=(0.93, 0.70, 0.33), roughness=0.2, metallic=1.0, linear=True),
    "bronze": dict(color=(0.30, 0.19, 0.10), roughness=0.4, metallic=1.0, linear=True),
    "water": dict(color=(0.16, 0.30, 0.30), roughness=0.05),
    "roof_tiles": dict(color=(0.70, 0.40, 0.27), roughness=0.75),
    "velum_linen": dict(color=(0.92, 0.87, 0.76), roughness=0.9, double_sided=True),
    "shadow_void": dict(color=(0.05, 0.045, 0.04), roughness=1.0),
    "matte": dict(color=(1.0, 1.0, 1.0), roughness=0.88),
}

DOUBLE_SIDED = {"velum_linen", "roof_flat"}


def srgb_to_linear(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def linear_color(color):
    return tuple(srgb_to_linear(component) for component in color)


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    request = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def fetch_json(url, path):
    download(url, path)
    with open(path, encoding="utf8") as handle:
        return json.load(handle)


def poly_haven_asset(asset_id, source_dir, credits):
    info = fetch_json(POLY_HAVEN_INFO.format(asset_id), os.path.join(source_dir, f"{asset_id}.info.json"))
    files = fetch_json(POLY_HAVEN_FILES.format(asset_id), os.path.join(source_dir, f"{asset_id}.files.json"))
    diffuse_url = files["Diffuse"]["1k"]["jpg"]["url"]
    normal_url = files["nor_gl"]["1k"]["jpg"]["url"]
    diffuse = download(diffuse_url, os.path.join(source_dir, f"{asset_id}_diff_1k.jpg"))
    normal = download(normal_url, os.path.join(source_dir, f"{asset_id}_nor_gl_1k.jpg"))
    width_metres = info.get("dimensions", [2000, 2000])[0] / 1000.0
    credits[asset_id] = {
        "name": info.get("name", asset_id),
        "authors": sorted(info.get("authors", {}).keys()),
        "page": f"https://polyhaven.com/a/{asset_id}",
        "files": [diffuse_url, normal_url],
        "licence": POLY_HAVEN_LICENCE,
        "width_metres": width_metres,
    }
    return diffuse, normal, width_metres


def image_pixels(path):
    image = bpy.data.images.load(path, check_existing=True)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return image, pixels.reshape(height, width, 4)


def save_pixels(name, pixels, path, file_format="JPEG", quality=90, colorspace="sRGB"):
    height, width = pixels.shape[:2]
    if pixels.shape[2] == 3:
        pixels = np.concatenate([pixels, np.ones((height, width, 1), dtype=pixels.dtype)], axis=2)
    image = bpy.data.images.get(name)
    if image is not None:
        bpy.data.images.remove(image)
    image = bpy.data.images.new(name, width, height, alpha=False)
    image.colorspace_settings.name = colorspace
    image.pixels.foreach_set(np.ascontiguousarray(pixels, dtype=np.float32).ravel())
    image.filepath_raw = path
    image.file_format = file_format
    image.save(filepath=path, quality=quality)
    return image


def recolored(source, target, contrast, path, name):
    if os.path.exists(path):
        return bpy.data.images.load(path, check_existing=True)
    source_image, pixels = image_pixels(source)
    luminance = pixels[..., 0] * 0.2126 + pixels[..., 1] * 0.7152 + pixels[..., 2] * 0.0722
    ratio = 1.0 + (luminance / max(float(luminance.mean()), 1e-4) - 1.0) * contrast
    result = np.ones_like(pixels)
    for channel in range(3):
        result[..., channel] = np.clip(target[channel] * ratio, 0.0, 1.0)
    bpy.data.images.remove(source_image)
    return save_pixels(name, result, path)


def height_to_normal(height, strength):
    gradient_y, gradient_x = np.gradient(height)
    normal = np.dstack([-gradient_x * strength, gradient_y * strength, np.ones_like(height)])
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    return normal * 0.5 + 0.5


def color_socket(sockets, name):
    return next(socket for socket in sockets if socket.name == name and socket.type == "RGBA")


def principled_material(name, color=(0.8, 0.8, 0.8), roughness=0.5, metallic=0.0, base_image=None,
                        normal_image=None, normal_strength=1.0, vertex_color=True):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = name not in DOUBLE_SIDED
    material.use_backface_culling_shadow = False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    material.diffuse_color = (*color, 1.0)
    base_socket = None
    if base_image is not None:
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = base_image
        base_socket = texture.outputs["Color"]
    if vertex_color:
        attribute = nodes.new("ShaderNodeVertexColor")
        multiply = nodes.new("ShaderNodeMix")
        multiply.data_type = "RGBA"
        multiply.blend_type = "MULTIPLY"
        multiply.inputs["Factor"].default_value = 1.0
        first = color_socket(multiply.inputs, "A")
        if base_socket is not None:
            links.new(base_socket, first)
        else:
            first.default_value = (*color, 1.0)
        links.new(attribute.outputs["Color"], color_socket(multiply.inputs, "B"))
        base_socket = color_socket(multiply.outputs, "Result")
    if base_socket is not None:
        links.new(base_socket, shader.inputs["Base Color"])
    if normal_image is not None:
        normal_image.colorspace_settings.name = "Non-Color"
        normal_texture = nodes.new("ShaderNodeTexImage")
        normal_texture.image = normal_image
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = normal_strength
        links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    return material


def generated_image(name, path, build, colorspace="sRGB", quality=92):
    if os.path.exists(path):
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = colorspace
        return image
    return save_pixels(name, build(), path, quality=quality, colorspace=colorspace)


def smooth_stone_pixels(color, size=512, seed=3):
    generator = np.random.default_rng(seed)
    coarse = generator.random((9, 9))
    coarse[-1, :] = coarse[0, :]
    coarse[:, -1] = coarse[:, 0]
    axis = np.linspace(0, 8, size, endpoint=False)
    index = axis.astype(int)
    fraction = axis - index
    rows = coarse[index] * (1 - fraction)[:, None] + coarse[(index + 1) % 9] * fraction[:, None]
    field = rows[:, index] * (1 - fraction)[None, :] + rows[:, (index + 1) % 9] * fraction[None, :]
    grain = generator.normal(0.0, 1.0, (size, size))
    variation = 1.0 + (field - 0.5) * 0.06 + grain * 0.012
    return np.dstack([np.clip(color[channel] * variation, 0, 1) for channel in range(3)])


def roof_flat_pixels(color, size=256):
    u = np.linspace(0, 1, size, endpoint=False)
    channels = 8
    phase = (u * channels) % 1.0
    ridge = np.clip(1.0 - np.abs(phase - 0.8) / 0.12, 0, 1)
    gutter = np.clip(1.0 - np.abs(phase - 0.62) / 0.06, 0, 1)
    tone = 1.0 + 0.12 * ridge - 0.22 * gutter
    v = np.linspace(0, 1, size, endpoint=False)
    courses = 1.0 - 0.1 * np.clip(1.0 - np.abs((v * 6) % 1.0 - 0.02) / 0.04, 0, 1)
    pattern = tone[None, :] * courses[:, None]
    return np.dstack([np.clip(color[channel] * pattern, 0, 1) for channel in range(3)])


def fluting_pixels(flutes=24, width=512, height=64):
    u = np.linspace(0, 1, width, endpoint=False)
    phase = (u * flutes) % 1.0
    depth = np.where(phase < 0.16, 0.0, np.sin(np.pi * (phase - 0.16) / 0.84))
    height_field = np.tile(-depth[None, :], (height, 1))
    return height_to_normal(height_field, 6.0)


def stamp(field, x, y, radius, amplitude=1.0, stretch=(1.0, 1.0), wrap=True):
    height, width = field.shape
    reach = int(math.ceil(radius * 2.2 * max(stretch)))
    rows = np.arange(int(y) - reach, int(y) + reach + 1)
    columns = np.arange(int(x) - reach, int(x) + reach + 1)
    rows = rows[(rows >= 0) & (rows < height)]
    if len(rows) == 0:
        return
    dx = (columns[None, :] - x) / stretch[0]
    dy = (rows[:, None] - y) / stretch[1]
    bump = amplitude * np.exp(-(dx * dx + dy * dy) / (radius * radius))
    wrapped = columns % width if wrap else np.clip(columns, 0, width - 1)
    block = field[np.ix_(rows, wrapped)]
    field[np.ix_(rows, wrapped)] = np.maximum(block, bump)


def rinceau_height(width=1024, height=128, periods=4):
    field = np.zeros((height, width))
    period = width / periods
    middle = height / 2
    swing = 0.2 * height
    for x in np.arange(0, width, 1.5):
        stamp(field, x, middle + swing * math.sin(2 * math.pi * x / period), 3.4, 0.8)
    for k in range(2 * periods):
        side = 1 if k % 2 == 0 else -1
        crest_x = period / 4 + k * period / 2
        center = (crest_x + side * 0.06 * period, middle - side * 0.1 * height)
        radius = 0.27 * height
        start = math.atan2(side, 0.15 * side)
        turn = -side
        steps = 140
        for step in range(steps):
            t = 2.5 * math.pi * step / steps
            r = radius * (1 - t / (2.9 * math.pi))
            px = center[0] + r * math.cos(start + turn * t) * 1.35
            py = center[1] + r * math.sin(start + turn * t)
            stamp(field, px, py, 2.8 - 1.2 * step / steps, 0.75)
        stamp(field, center[0], center[1], 5.0, 1.0)
        for leaf in range(3):
            angle = start + turn * (0.6 + leaf * 0.9)
            lx = crest_x + math.cos(angle) * 0.1 * period - side * (leaf - 1) * 0.07 * period
            ly = middle + side * swing * 0.8 + math.sin(angle) * 0.08 * height
            stamp(field, lx, min(max(ly, 10), height - 10), 4.5, 0.6, (2.2, 0.8))
    for row in (5, height - 6):
        field[row - 2:row + 3, :] = np.maximum(field[row - 2:row + 3, :], 0.7)
    return field


def frieze_images(texture_dir, color):
    height_path = os.path.join(texture_dir, "frieze_rinceau_v1.jpg")
    normal_path = os.path.join(texture_dir, "frieze_rinceau_normal_v1.jpg")
    if not (os.path.exists(height_path) and os.path.exists(normal_path)):
        field = rinceau_height()
        shade = 0.72 + 0.28 * field
        save_pixels("frieze_rinceau", np.dstack([np.clip(color[c] * shade, 0, 1) for c in range(3)]), height_path,
                    quality=92)
        save_pixels("frieze_rinceau_normal", height_to_normal(field, 2.5), normal_path, quality=95,
                    colorspace="Non-Color")
    base = bpy.data.images.load(height_path, check_existing=True)
    normal = bpy.data.images.load(normal_path, check_existing=True)
    normal.colorspace_settings.name = "Non-Color"
    return base, normal


def build_library(cache_dir):
    source_dir = os.path.join(cache_dir, "src", "polyhaven")
    texture_dir = os.path.join(cache_dir, "textures")
    os.makedirs(texture_dir, exist_ok=True)
    credits = {}
    tile_sizes = {}
    for name, spec in TEXTURED.items():
        diffuse, normal, width_metres = poly_haven_asset(spec["asset"], source_dir, credits)
        signature = "".join(f"{round(value * 100):02d}" for value in (*spec["color"], spec["contrast"]))
        base_path = os.path.join(texture_dir, f"{name}_{signature}.jpg")
        base = recolored(diffuse, spec["color"], spec["contrast"], base_path, name)
        normal_image = bpy.data.images.load(normal, check_existing=True) if spec["normal"] > 0 else None
        principled_material(name, linear_color(spec["color"]), spec["roughness"], 0.0, base, normal_image,
                            spec["normal"])
        tile_sizes[name] = spec.get("tile", width_metres)
    for name, spec in PLAIN.items():
        color = spec["color"] if spec.get("linear") else linear_color(spec["color"])
        principled_material(name, color, spec["roughness"], spec.get("metallic", 0.0))
        tile_sizes[name] = 2.0
    smooth_color = (0.91, 0.88, 0.81)
    smooth = generated_image("lens_smooth", os.path.join(texture_dir, "lens_smooth_v2.jpg"),
                             lambda: smooth_stone_pixels(smooth_color))
    principled_material("lens_smooth", linear_color(smooth_color), 0.55, 0.0, smooth)
    tile_sizes["lens_smooth"] = 3.0
    fluting = generated_image("lens_fluting_normal", os.path.join(texture_dir, "lens_fluting_normal.jpg"),
                              fluting_pixels, colorspace="Non-Color", quality=95)
    principled_material("lens_fluted", linear_color(smooth_color), 0.55, 0.0, smooth, fluting, 1.0)
    tile_sizes["lens_fluted"] = 2 * math.pi * 0.41
    roof_color = PLAIN["roof_tiles"]["color"]
    roof = generated_image("roof_flat", os.path.join(texture_dir, "roof_flat.jpg"),
                           lambda: roof_flat_pixels(roof_color))
    principled_material("roof_flat", linear_color(roof_color), 0.78, 0.0, roof)
    tile_sizes["roof_flat"] = 3.6
    principled_material("terracotta_tiles", linear_color(roof_color), 0.78, 0.0, roof)
    tile_sizes["terracotta_tiles"] = 3.6
    frieze, frieze_normal = frieze_images(texture_dir, smooth_color)
    principled_material("frieze_rinceau", linear_color(smooth_color), 0.55, 0.0, frieze, frieze_normal, 1.0)
    tile_sizes["frieze_rinceau"] = 1.0
    return tile_sizes, credits


def baked_material(name, color_image, roughness=0.95, normal_image=None, normal_strength=1.0):
    return principled_material(name, roughness=roughness, base_image=color_image, normal_image=normal_image,
                               normal_strength=normal_strength, vertex_color=False)

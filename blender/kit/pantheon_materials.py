import math
import os
import zipfile

import bpy
import numpy as np

from .materials import download, image_pixels, linear_color, principled_material, roof_flat_pixels, save_pixels
from .pont_materials import height_normal, luminance, periodic_noise

AMBIENT_ZIP = "https://ambientcg.com/get?file={}_1K-JPG.zip"
AMBIENT_PAGE = "https://ambientcg.com/view?id={}"
AMBIENT_LICENCE = "CC0 1.0 (https://docs.ambientcg.com/license/)"
VERSION = "v4"
REVISION = {"pavonazzetto": "v6", "floor_sectile": "v6", "marble_paving": "v5"}
MARBLE_TILE = 2.4
SIZE = 1024
SECTILE_CELL = 2.96
PAVING_TILE = 3.6
BRICK_TILE = 1.2
BRONZE_TILE = 2.4


def ambient_colour(asset_id, source_dir, credits):
    archive = download(AMBIENT_ZIP.format(asset_id), os.path.join(source_dir, f"{asset_id}.zip"))
    folder = os.path.join(source_dir, "extracted")
    member = f"{asset_id}_1K-JPG_Color.jpg"
    target = os.path.join(folder, member)
    if not os.path.exists(target):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extract(member, folder)
    credits[asset_id] = {"name": asset_id, "authors": ["ambientCG (Lennart Demes)"], "page": AMBIENT_PAGE.format(asset_id),
                         "files": [AMBIENT_ZIP.format(asset_id)], "licence": AMBIENT_LICENCE}
    image, pixels = image_pixels(target)
    colour = np.array(pixels[..., :3])
    bpy.data.images.remove(image)
    return colour


def normalise(values, low=1.0, high=99.0):
    a, b = np.percentile(values, (low, high))
    return np.clip((values - a) / max(b - a, 1e-6), 0.0, 1.0)


def blend(dark, light, t):
    t = t[..., None]
    return np.asarray(dark)[None, None, :] * (1.0 - t) + np.asarray(light)[None, None, :] * t


def smoothstep(values, low, high):
    t = np.clip((values - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def patina(seed, amount=0.07):
    return (1.0 - amount + 2.0 * amount * periodic_noise(SIZE, 1.8, seed))[..., None]


def marble_white(source):
    tone = np.clip(source * np.array([0.985, 0.97, 0.94]), 0, 1)
    return np.clip(tone * patina(31, 0.05), 0, 1)


def zoomed(values, factor=2):
    size = values.shape[0] // factor
    return np.kron(values[:size, :size], np.ones((factor, factor)))


def softened(values, passes=2):
    for _ in range(passes):
        values = (values + np.roll(values, 1, 0) + np.roll(values, -1, 0) + np.roll(values, 1, 1) + np.roll(values, -1, 1)) / 5
    return values


def giallo(source):
    t = normalise(luminance(source)) ** 0.7
    colour = blend((0.60, 0.40, 0.19), (0.90, 0.79, 0.54), t)
    return np.clip(colour * patina(32, 0.06), 0, 1)


def voronoi(cells, seed):
    generator = np.random.default_rng(seed)
    points = generator.uniform(0, SIZE, (cells, 2))
    weights = generator.uniform(0.0, 14.0, cells)
    ys, xs = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    first = np.full((SIZE, SIZE), np.inf, dtype=np.float32)
    second = np.full((SIZE, SIZE), np.inf, dtype=np.float32)
    owner = np.zeros((SIZE, SIZE), dtype=np.int32)
    for index, (px, py) in enumerate(points):
        dx = np.abs(xs - px)
        dy = np.abs(ys - py)
        distance = np.hypot(np.minimum(dx, SIZE - dx), np.minimum(dy, SIZE - dy)) - weights[index]
        closer = distance < first
        second = np.where(closer, first, np.minimum(second, distance))
        owner = np.where(closer, index, owner)
        first = np.where(closer, distance, first)
    return first, second, owner


def pavonazzetto(source, cells=420, seed=94):
    generator = np.random.default_rng(seed + 1)
    first, second, owner = voronoi(cells, seed)
    tones = generator.normal(1.0, 0.035, cells)
    violet = generator.random(cells) < 0.14
    clast = np.array([0.93, 0.91, 0.87])[None, None, :] * tones[owner][..., None]
    clast = np.where(violet[owner][..., None], clast * np.array([0.82, 0.72, 0.8]), clast)
    clast *= (0.9 + 0.1 * normalise(luminance(source)))[..., None]
    edge = second - first
    width = 1.4 + 2.8 * periodic_noise(SIZE, 1.2, seed + 2)
    vein = 1.0 - smoothstep(edge, 0.0, width)
    halo = 1.0 - smoothstep(edge, 0.0, width * 5.0)
    tinted = clast * (1.0 - 0.45 * halo[..., None]) + np.array([0.6, 0.45, 0.58]) * 0.45 * halo[..., None]
    colour = tinted * (1.0 - vein[..., None]) + np.array([0.42, 0.28, 0.40]) * vein[..., None]
    return np.clip(colour * patina(33, 0.04), 0, 1)


def porphyry(granite):
    t = normalise(luminance(granite))
    colour = blend((0.34, 0.09, 0.10), (0.60, 0.23, 0.23), t ** 1.1)
    speckle = smoothstep(t, 0.9, 0.97)
    return np.clip(colour * (1.0 - speckle[..., None]) + np.array([0.84, 0.68, 0.64]) * speckle[..., None], 0, 1)


def granite_grey(granite):
    t = normalise(luminance(granite)) ** 1.1
    return np.clip(blend((0.13, 0.13, 0.14), (0.86, 0.85, 0.83), t) * patina(34, 0.05), 0, 1)


def granite_rose(granite):
    t = normalise(luminance(granite))
    warm = blend((0.16, 0.10, 0.10), (0.88, 0.60, 0.52), t ** 0.9)
    return np.clip(warm * 0.75 + granite * np.array([1.05, 0.82, 0.76]) * 0.25, 0, 1)


def paving(travertine, seed=41, tile=PAVING_TILE, size=0.9):
    generator = np.random.default_rng(seed)
    scale = SIZE / tile
    slab = int(round(size * scale))
    rows = SIZE // slab
    colour = np.zeros((SIZE, SIZE, 3))
    height = np.zeros((SIZE, SIZE))
    joint = max(int(scale * 0.012), 2)
    y_axis = np.arange(SIZE)
    for row in range(rows):
        y0, y1 = row * slab, (row + 1) * slab if row < rows - 1 else SIZE
        offset = int(generator.integers(0, slab)) if row % 2 else 0
        starts = list(range(-offset, SIZE, slab))
        for start in starts:
            columns = np.arange(start, start + slab) % SIZE
            ox, oy = generator.integers(0, SIZE, 2)
            source = np.roll(np.roll(travertine, -oy, 0), -ox, 1)
            if generator.random() < 0.5:
                source = np.transpose(source, (1, 0, 2))
            block = source[y0:y1][:, columns]
            tone = generator.normal(1.0, 0.045) * np.array([1.0, 1.0 - generator.normal(0, 0.01), 1.0 - generator.normal(0.02, 0.02)])
            colour[np.ix_(y_axis[y0:y1], columns)] = block * tone
            local_y = (y_axis[y0:y1] - y0)[:, None]
            local_x = np.arange(slab)[None, :]
            edge = np.minimum(np.minimum(local_x, slab - 1 - local_x), np.minimum(local_y, y1 - y0 - 1 - local_y))
            height[np.ix_(y_axis[y0:y1], columns)] = np.clip(edge / (joint * 2.5), 0, 1) ** 0.5
    grit = periodic_noise(SIZE, 0.7, seed + 1)
    grime = periodic_noise(SIZE, 1.9, seed + 2)
    colour *= (0.93 + 0.1 * grime)[..., None]
    colour *= (1.0 - 0.45 * (height < 0.2))[..., None]
    colour *= (0.97 + 0.05 * grit)[..., None]
    detail = luminance(travertine)
    return np.clip(colour, 0, 1), height_normal(height * 1.0 + 0.15 * normalise(detail), 6.0)


def brick(seed=51):
    generator = np.random.default_rng(seed)
    scale = SIZE / BRICK_TILE
    course = 0.06
    courses = int(round(BRICK_TILE / course))
    pixel_course = SIZE / courses
    colour = np.zeros((SIZE, SIZE, 3))
    height = np.zeros((SIZE, SIZE))
    mortar = np.array([0.74, 0.70, 0.62])
    fine = periodic_noise(SIZE, 0.6, seed + 1)
    coarse = periodic_noise(SIZE, 1.6, seed + 2)
    for row in range(courses):
        y0 = int(round(row * pixel_course))
        y1 = int(round((row + 1) * pixel_course))
        brick_bottom = y0 + int(round(pixel_course * 0.24))
        colour[y0:y1] = mortar
        start = generator.uniform(0, SIZE)
        position = 0.0
        while position < SIZE:
            length = generator.uniform(0.22, 0.42) * scale
            gap = 0.012 * scale
            left = start + position
            columns = (np.arange(int(left), int(left + length - gap)) % SIZE)
            hue = generator.normal(0.0, 1.0)
            value = generator.normal(1.0, 0.09)
            tone = np.array([0.66 + 0.05 * hue, 0.37 + 0.035 * hue, 0.24 + 0.01 * hue]) * value
            if generator.random() < 0.12:
                tone = np.array([0.80, 0.60, 0.42]) * value
            colour[np.ix_(np.arange(brick_bottom, y1), columns)] = tone
            height[np.ix_(np.arange(brick_bottom, y1), columns)] = 1.0
            position += length
    colour *= (0.88 + 0.2 * fine)[..., None]
    colour *= (0.9 + 0.14 * coarse)[..., None]
    return np.clip(colour, 0, 1), height_normal(height * 0.8 + 0.2 * fine, 5.0)


def lime(base, seed, amount=0.08):
    coarse = periodic_noise(SIZE, 1.9, seed)
    fine = periodic_noise(SIZE, 0.8, seed + 1)
    value = 1.0 - amount + 2 * amount * coarse + 0.03 * (fine - 0.5)
    return np.clip(np.array(base)[None, None, :] * value[..., None], 0, 1)


def bronze_tiles(seed=61):
    generator = np.random.default_rng(seed)
    columns = 4
    rows = 3
    width = SIZE // columns
    height_px = SIZE // rows
    colour = np.zeros((SIZE, SIZE, 3))
    height = np.zeros((SIZE, SIZE))
    for row in range(rows):
        for column in range(columns):
            x0 = column * width + (width // 2 if row % 2 else 0)
            xs = np.arange(x0, x0 + width) % SIZE
            ys = np.arange(row * height_px, (row + 1) * height_px if row < rows - 1 else SIZE)
            local_y = (ys - ys[0])[:, None] / len(ys)
            local_x = (np.arange(width)[None, :] + 0.5) / width
            shade = generator.normal(1.0, 0.06)
            warm = np.array([0.66, 0.46, 0.24]) * shade
            ramp = 0.82 + 0.18 * local_y
            colour[np.ix_(ys, xs)] = warm[None, None, :] * ramp[..., None]
            ridge = np.exp(-((local_x - 0.5) / 0.08) ** 2)
            height[np.ix_(ys, xs)] = 0.6 * local_y + 0.9 * ridge
            colour[np.ix_(ys, xs)] *= (1.0 + 0.12 * ridge)[..., None]
    streak = periodic_noise(SIZE, 1.4, seed + 1, (0.25, 1.0))
    colour *= (0.9 + 0.16 * streak)[..., None]
    return np.clip(colour, 0, 1), height_normal(height, 4.0)


def sectile(pieces):
    scale = SIZE / (2 * SECTILE_CELL)
    ys, xs = np.mgrid[0:SIZE, 0:SIZE]
    u = xs / scale
    v = ys / scale
    cell_u = np.floor(u / SECTILE_CELL)
    cell_v = np.floor(v / SECTILE_CELL)
    lu = u - cell_u * SECTILE_CELL - SECTILE_CELL / 2
    lv = v - cell_v * SECTILE_CELL - SECTILE_CELL / 2
    odd = ((cell_u + cell_v) % 2).astype(bool)
    square = np.maximum(np.abs(lu), np.abs(lv))
    radius = np.hypot(lu, lv)
    band = SECTILE_CELL / 2 - 0.16
    colour = pieces["giallo"].copy()
    inner = square < band
    joints = np.abs(square - band) < 0.008
    first_inner = inner & ~odd
    second_inner = inner & odd
    colour[first_inner] = pieces["granite_grey"][first_inner]
    colour[second_inner] = pieces["pavonazzetto"][second_inner]
    disc = first_inner & (radius < 1.02)
    ring = first_inner & (np.abs(radius - 1.07) < 0.05)
    colour[ring] = pieces["giallo"][ring]
    colour[disc] = pieces["porphyry"][disc]
    small = second_inner & (square < 0.82)
    colour[small] = pieces["granite_rose"][small]
    joints |= np.abs(radius - 1.02) < 0.006
    joints |= first_inner & (np.abs(radius - 1.12) < 0.006)
    joints |= second_inner & (np.abs(square - 0.82) < 0.006)
    colour[joints] *= 0.55
    wear = periodic_noise(SIZE, 1.7, 71)
    colour *= (0.95 + 0.07 * wear)[..., None]
    return np.clip(colour, 0, 1)


def cached(name, path, build, colorspace="sRGB", quality=92):
    if os.path.exists(path):
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = colorspace
        return image
    return save_pixels(name, build(), path, quality=quality, colorspace=colorspace)


TEXTURED = {
    "marble_white": (0.42, 0.0, 2.4),
    "giallo": (0.32, 0.0, 1.8),
    "pavonazzetto": (0.32, 0.0, 2.0),
    "porphyry": (0.28, 0.0, 0.9),
    "granite_grey": (0.42, 0.0, 1.6),
    "granite_rose": (0.42, 0.0, 1.6),
    "travertine": (0.8, 0.0, PAVING_TILE),
    "marble_paving": (0.36, 0.0, MARBLE_TILE),
    "brick": (0.9, 0.0, BRICK_TILE),
    "stucco": (0.86, 0.0, 4.0),
    "plaster": (0.88, 0.0, 4.0),
    "bronze_tiles": (0.4, 1.0, BRONZE_TILE),
    "floor_sectile": (0.36, 0.0, 2 * SECTILE_CELL),
    "terracotta_tiles": (0.78, 0.0, 3.6),
}
NORMALS = {"travertine": 0.7, "brick": 0.9, "bronze_tiles": 0.8, "marble_paving": 0.5}
PLAIN = {
    "bronze": ((0.42, 0.26, 0.11), 0.36, 1.0),
    "bronze_gilt": ((0.86, 0.63, 0.29), 0.26, 1.0),
    "bronze_letters": ((0.46, 0.30, 0.12), 0.42, 0.55),
    "water": ((0.08, 0.15, 0.15), 0.06, 0.0),
    "matte": ((1.0, 1.0, 1.0), 0.88, 0.0),
    "shadow_void": ((0.05, 0.045, 0.04), 1.0, 0.0),
}


def build_library(cache_dir):
    source_dir = os.path.join(cache_dir, "src", "ambientcg")
    texture_dir = os.path.join(cache_dir, "textures")
    os.makedirs(texture_dir, exist_ok=True)
    credits = {}

    def path(name):
        return os.path.join(texture_dir, f"{name}_{REVISION.get(name.removesuffix('_normal'), VERSION)}.jpg")

    loaded = {}

    def sources():
        if not loaded:
            loaded["marble_white"] = ambient_colour("Marble021", source_dir, credits)
            loaded["veined"] = ambient_colour("Marble014", source_dir, credits)
            loaded["granite"] = ambient_colour("Granite001A", source_dir, credits)
            loaded["travertine"] = ambient_colour("Travertine009", source_dir, credits)
        return loaded

    for asset in ("Marble021", "Marble014", "Granite001A", "Travertine009"):
        credits[asset] = {"name": asset, "authors": ["ambientCG (Lennart Demes)"], "page": AMBIENT_PAGE.format(asset),
                          "files": [AMBIENT_ZIP.format(asset)], "licence": AMBIENT_LICENCE}
    builders = {
        "marble_white": lambda: marble_white(sources()["marble_white"]),
        "giallo": lambda: giallo(sources()["veined"]),
        "pavonazzetto": lambda: pavonazzetto(sources()["marble_white"]),
        "porphyry": lambda: porphyry(sources()["granite"]),
        "granite_grey": lambda: granite_grey(sources()["granite"]),
        "granite_rose": lambda: granite_rose(sources()["granite"]),
        "stucco": lambda: lime((0.86, 0.84, 0.79), 81, 0.07),
        "plaster": lambda: lime((0.95, 0.92, 0.86), 82, 0.06),
        "terracotta_tiles": lambda: roof_flat_pixels((0.70, 0.40, 0.27), SIZE // 2),
    }
    images = {}
    arrays = {}
    for name, build in builders.items():
        def remember(name=name, build=build):
            arrays[name] = build()
            return arrays[name]
        images[name] = cached(name, path(name), remember)
    normal_images = {}
    for name, build in (("travertine", lambda: paving(sources()["travertine"])), ("brick", brick),
                        ("bronze_tiles", bronze_tiles),
                        ("marble_paving", lambda: paving(marble_white(sources()["marble_white"]), 43, MARBLE_TILE, 1.2))):
        if os.path.exists(path(name)) and os.path.exists(path(f"{name}_normal")):
            images[name] = cached(name, path(name), None)
            normal_images[name] = cached(f"{name}_normal", path(f"{name}_normal"), None, "Non-Color")
            continue
        colour, normal = build()
        images[name] = save_pixels(name, colour, path(name), quality=92)
        normal_images[name] = save_pixels(f"{name}_normal", normal, path(f"{name}_normal"), quality=95,
                                          colorspace="Non-Color")

    def piece(name):
        if name not in arrays:
            _, pixels = image_pixels(path(name))
            arrays[name] = np.array(pixels[..., :3])
        return arrays[name]
    images["floor_sectile"] = cached("floor_sectile", path("floor_sectile"),
                                     lambda: sectile({key: piece(key) for key in ("giallo", "granite_grey", "pavonazzetto",
                                                                                   "porphyry", "granite_rose")}))
    tiles = {}
    for name, (roughness, metallic, tile) in TEXTURED.items():
        principled_material(name, (1.0, 1.0, 1.0), roughness, metallic, images[name], normal_images.get(name),
                            NORMALS.get(name, 1.0))
        tiles[name] = tile
    for name, (colour, roughness, metallic) in PLAIN.items():
        principled_material(name, colour if metallic else linear_color(colour), roughness, metallic)
        tiles[name] = 2.0
    bpy.data.materials["water"].use_backface_culling = True
    return tiles, credits


def weather(obj, strength=0.1, seed=0, scale=7.0, grime=0.0, ground=0.0):
    mesh = obj.data
    attribute = mesh.color_attributes.get("Col")
    if attribute is None or len(mesh.loops) == 0:
        return
    vertex_index = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vertex_index)
    coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coordinates)
    coordinates = coordinates.reshape(-1, 3)
    matrix = np.array(obj.matrix_world)
    world = coordinates @ matrix[:3, :3].T + matrix[:3, 3]
    points = world[vertex_index]
    generator = np.random.default_rng(seed)
    value = np.zeros(len(points))
    total = 0.0
    for octave in range(4):
        direction = generator.normal(size=3)
        direction[2] *= 1.6
        direction /= np.linalg.norm(direction)
        frequency = 2 ** octave / scale
        weight = 0.55 ** octave
        value += weight * np.sin(points @ direction * frequency * 2 * math.pi + generator.uniform(0, 6.28))
        total += weight
    value = value / total * 0.5 + 0.5
    factor = 1.0 - strength * value
    if grime > 0:
        factor *= 1.0 - grime * np.clip(1.0 - (points[:, 2] - ground) / 3.0, 0.0, 1.0)
    colours = np.empty(len(mesh.loops) * 4, dtype=np.float32)
    attribute.data.foreach_get("color_srgb", colours)
    colours = colours.reshape(-1, 4)
    colours[:, :3] *= factor[:, None]
    attribute.data.foreach_set("color_srgb", np.clip(colours, 0, 1).ravel())

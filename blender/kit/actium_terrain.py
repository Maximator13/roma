import math
import os

import bmesh
import bpy
import numpy as np

from .materials import baked_material, download, principled_material
from .pompei_terrain import blur, chamfer_distance, minimum_filter, smoothstep, world_noise
from .pont_terrain import grid_mesh

DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/Copernicus_DSM_COG_10_{0}_DEM.tif"
TILES = {(38, 20): "N38_00_E020_00", (39, 20): "N39_00_E020_00", (38, 21): "N38_00_E021_00",
         (39, 21): "N39_00_E021_00"}
SOURCE = {
    "name": "Copernicus DEM GLO-30, tiles N38 and N39, E020 and E021",
    "urls": [DEM_URL.format(tile) for tile in TILES.values()],
    "licence": ("Copernicus DEM licence, free use with attribution: produced using Copernicus WorldDEM-30 (c) DLR e.V. "
                "2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European "
                "Union and ESA; all rights reserved"),
    "processing": ("two-pass minimum filter and blur on land only, which levels the buildings of modern Preveza, Aktio "
                   "and the airport into the ground, keeps the coastline, sea clamped to 0, land raised 2 m (at "
                   "least 3 m) above the model sea level, ground flat at 0 over the water and cut out by the "
                   "texture alpha"),
}
STEP = 1.0 / 3600.0
MOSAIC = (39.25, 20.40, 1800, 2520)
SEA_SURFACE = 0.5
LAND_LIFT = 2.0
LAND_FLOOR = 3.0
SHORE_DROP = -12.0
LAND_LEVEL = 0.05
SHORE_SLOPE = 40.0
SEA_BLOCK = 20
SEA_CELL = 200.0
SEA_FAR_CELL = 2000.0
FAR_REACH = 23000.0


def load_tile(path):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    width, height = image.size
    pixels = np.empty(width * height * image.channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    grid = pixels.reshape(height, width, image.channels)[::-1, :, 0].astype(np.float64)
    bpy.data.images.remove(image)
    return grid


def load_dem(cache_dir):
    cached = os.path.join(cache_dir, "src", "dem", "actium_mosaic_v1.npy")
    if os.path.exists(cached):
        return np.load(cached)
    north, west, rows, columns = MOSAIC
    mosaic = np.zeros((rows, columns))
    for (latitude, longitude), tile in TILES.items():
        path = download(DEM_URL.format(tile), os.path.join(cache_dir, "src", "dem", f"glo30_{tile}.tif"))
        grid = load_tile(path)
        size = grid.shape[0]
        tile_north = latitude + 1
        r_start = int(round((north - tile_north) / STEP))
        c_start = int(round((longitude - west) / STEP))
        r0, r1 = max(0, r_start), min(rows, r_start + size)
        c0, c1 = max(0, c_start), min(columns, c_start + grid.shape[1])
        if r0 < r1 and c0 < c1:
            mosaic[r0:r1, c0:c1] = grid[r0 - r_start:r1 - r_start, c0 - c_start:c1 - c_start]
    np.save(cached, mosaic)
    return mosaic


def clean(mosaic):
    land = mosaic > LAND_LEVEL
    lowered = minimum_filter(np.where(land, mosaic, np.inf), 2)
    lowered = np.where(np.isfinite(lowered), lowered, mosaic)
    smoothed = blur(np.where(land, lowered, 0.0), 2)
    return np.where(land, np.maximum(smoothed, 0.3), 0.0), land.astype(np.float64)


class Relief:
    def __init__(self, frame, cache_dir):
        self.frame = frame
        self.heights, self.land = clean(load_dem(cache_dir))

    def bilinear(self, grid, xs, ys):
        north, west, rows, columns = MOSAIC
        latitude, longitude = self.frame.to_geo(np.asarray(xs, np.float64), np.asarray(ys, np.float64))
        row = np.clip((north - latitude) / STEP - 0.5, 0, rows - 1.001)
        column = np.clip((longitude - west) / STEP - 0.5, 0, columns - 1.001)
        r0 = row.astype(int)
        c0 = column.astype(int)
        fy = row - r0
        fx = column - c0
        top = grid[r0, c0] * (1 - fx) + grid[r0, c0 + 1] * fx
        bottom = grid[r0 + 1, c0] * (1 - fx) + grid[r0 + 1, c0 + 1] * fx
        return top * (1 - fy) + bottom * fy

    def sample(self, xs, ys):
        share = self.bilinear(self.land, xs, ys)
        land = share > 0.5
        raw = self.bilinear(self.heights, xs, ys)
        shore = SEA_SURFACE + (share - 0.5) * SHORE_SLOPE
        coast = np.maximum(raw + LAND_LIFT, np.minimum(LAND_FLOOR, shore))
        return np.where(land, coast, np.maximum(shore, SHORE_DROP)), land

    def height_at(self, x, y):
        height, land = self.sample(np.array([x]), np.array([y]))
        return float(height[0])

    def nearest_land(self, x, y, radius=600.0, step=20.0, highest=False):
        offsets = np.arange(-radius, radius + step / 2, step)
        gx, gy = np.meshgrid(x + offsets, y + offsets)
        heights, land = self.sample(gx, gy)
        distance = np.hypot(gx - x, gy - y)
        score = np.where(land & (distance <= radius), -heights if highest else distance, np.inf)
        index = np.unravel_index(np.argmin(score), score.shape)
        return float(gx[index]), float(gy[index])


def mix(colour, other, weight):
    return colour * (1 - weight[..., None]) + np.asarray(other) * weight[..., None]


def ground_pixels(relief, texture_x, texture_y):
    gx, gy = np.meshgrid(texture_x, texture_y)
    raw = relief.bilinear(relief.heights, gx, gy)
    land = relief.bilinear(relief.land, gx, gy) > 0.5
    spacing = abs(texture_x[1] - texture_x[0])
    dy, dx = np.gradient(raw, spacing)
    slope = np.hypot(dx, dy)
    coast = chamfer_distance(~land, spacing, 40)
    shape = raw.shape
    parcels = world_noise(gx, gy, 420.0, 11, octaves=3, persistence=0.55)
    scrub = world_noise(gx, gy, 260.0, 12, octaves=4, persistence=0.6)
    grain = world_noise(gx, gy, 40.0, 13, octaves=3, persistence=0.6)
    dry = np.array([0.66, 0.58, 0.38])
    stubble = np.array([0.72, 0.62, 0.43])
    maquis = np.array([0.32, 0.35, 0.21])
    oak = np.array([0.23, 0.28, 0.16])
    sand = np.array([0.82, 0.76, 0.60])
    marsh = np.array([0.47, 0.46, 0.34])
    rock = np.array([0.60, 0.57, 0.50])
    colour = mix(np.broadcast_to(dry, shape + (3,)).copy(), stubble, smoothstep((parcels - 0.45) / 0.15))
    hills = smoothstep((raw - 15.0) / 60.0)
    colour = mix(colour, maquis, smoothstep((scrub - 0.62 + 0.25 * hills) / 0.1) * (0.45 + 0.45 * hills))
    colour = mix(colour, oak, hills * smoothstep((scrub - 0.45) / 0.15) * 0.75)
    colour = mix(colour, marsh, smoothstep((3.0 - raw) / 2.0) * smoothstep((300.0 - coast) / 250.0) * 0.7)
    colour = mix(colour, rock, smoothstep((slope - 0.35) / 0.25) * 0.8)
    colour = mix(colour, sand, smoothstep((45.0 - coast) / 30.0) * smoothstep((8.0 - raw) / 4.0))
    colour *= (0.82 + 0.3 * grain)[..., None]
    return np.clip(colour, 0, 1)


def add_sea_blocks(mesh, xs, ys, blocks, uv):
    rows, columns = blocks.shape
    shape = (len(ys) - 1, len(xs) - 1)
    edges_y = [min(row * SEA_BLOCK, shape[0]) for row in range(rows + 1)]
    edges_x = [min(column * SEA_BLOCK, shape[1]) for column in range(columns + 1)]
    mesh_data = bmesh.new()
    mesh_data.from_mesh(mesh)
    layer = mesh_data.loops.layers.uv.active
    for row in range(rows):
        for column in range(columns):
            if blocks[row, column]:
                continue
            x0, x1 = xs[edges_x[column]], xs[edges_x[column + 1]]
            y0, y1 = ys[edges_y[row]], ys[edges_y[row + 1]]
            corners = [mesh_data.verts.new((x, y, 0.0)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            face = mesh_data.faces.new(corners)
            face.smooth = True
            for loop in face.loops:
                u, v = uv(np.array([loop.vert.co.x]), np.array([loop.vert.co.y]))[0]
                loop[layer].uv = (u, v)
    bmesh.ops.triangulate(mesh_data, faces=mesh_data.faces[:])
    mesh_data.to_mesh(mesh)
    mesh_data.free()


def masked_material(name, path, pixels, alpha):
    height, width = alpha.shape
    rgba = np.concatenate([pixels, alpha[..., None]], axis=2)[::-1]
    image = bpy.data.images.new(name, width, height, alpha=True)
    image.pixels.foreach_set(np.ascontiguousarray(rgba, dtype=np.float32).ravel())
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    image.alpha_mode = "STRAIGHT"
    material = baked_material(name, image, roughness=0.96)
    nodes = material.node_tree.nodes
    texture = next(node for node in nodes if node.type == "TEX_IMAGE")
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    clip = nodes.new("ShaderNodeMath")
    clip.operation = "ROUND"
    material.node_tree.links.new(texture.outputs["Alpha"], clip.inputs[0])
    material.node_tree.links.new(clip.outputs[0], shader.inputs["Alpha"])
    material.surface_render_method = "DITHERED"
    return material


def build_ground(relief, extent, spacing, texture_path, collection, new_object):
    x0, x1, y0, y1 = extent
    xs = np.arange(x0, x1 + spacing / 2, spacing)
    ys = np.arange(y0, y1 + spacing / 2, spacing)
    gx, gy = np.meshgrid(xs, ys)
    heights, land = relief.sample(gx, gy)
    heights = np.where(land, heights, 0.0)
    cells = land[:-1, :-1] | land[1:, :-1] | land[:-1, 1:] | land[1:, 1:]
    rows = -(-cells.shape[0] // SEA_BLOCK)
    columns = -(-cells.shape[1] // SEA_BLOCK)
    padded = np.zeros((rows * SEA_BLOCK, columns * SEA_BLOCK), dtype=bool)
    padded[:cells.shape[0], :cells.shape[1]] = cells
    blocks = padded.reshape(rows, SEA_BLOCK, columns, SEA_BLOCK).any(axis=(1, 3))
    keep = np.repeat(np.repeat(blocks, SEA_BLOCK, axis=0), SEA_BLOCK, axis=1)[:cells.shape[0], :cells.shape[1]]
    width = 2048
    height = int(round(width * (y1 - y0) / (x1 - x0)))
    texture_x = np.linspace(x0, x1, width)
    texture_y = np.linspace(y1, y0, height)
    pixels = ground_pixels(relief, texture_x, texture_y)
    tx, ty = np.meshgrid(texture_x, texture_y)
    alpha = np.clip((relief.bilinear(relief.land, tx, ty) - 0.5) * 6.0 + 0.5, 0.0, 1.0)
    material = masked_material("actium_ground", texture_path, pixels, alpha)
    uv = lambda vx, vy: np.column_stack([(vx - x0) / (x1 - x0), (vy - y0) / (y1 - y0)])
    mesh = grid_mesh("ground", xs, ys, heights, keep=keep, uv=uv)
    add_sea_blocks(mesh, xs, ys, blocks, uv)
    mesh.materials.append(material)
    ground = new_object("ground", mesh, collection)
    ground["cast_shadow"] = False
    return ground, heights, land


def build_far_ground(relief, extent, half, spacing, collection, new_object):
    x0, x1, y0, y1 = extent
    xs = np.arange(-half, half + spacing / 2, spacing)
    ys = np.arange(-half, half + spacing / 2, spacing)
    gx, gy = np.meshgrid(xs, ys)
    heights, land = relief.sample(gx, gy)
    heights = np.where(land, heights - 3.0, SHORE_DROP)
    cx = gx[:-1, :-1] + spacing / 2
    cy = gy[:-1, :-1] + spacing / 2
    outside = ~((cx > x0 + spacing) & (cx < x1 - spacing) & (cy > y0 + spacing) & (cy < y1 - spacing))
    keep = outside & (land[:-1, :-1] | land[1:, :-1] | land[:-1, 1:] | land[1:, 1:])
    low = np.array([0.62, 0.56, 0.38])
    high = np.array([0.36, 0.38, 0.25])
    colours = mix(np.broadcast_to(low, gx.shape + (3,)).copy(), high, smoothstep((heights - 40.0) / 300.0))
    mesh = grid_mesh("ground_far", xs, ys, heights, keep=keep, colours=colours)
    mesh.materials.append(principled_material("actium_far", color=(1.0, 1.0, 1.0), roughness=0.97))
    far = new_object("ground_far", mesh, collection)
    far["cast_shadow"] = False
    return far


def water_cells(relief, x0, x1, y0, y1, size, probes=5):
    xs = np.arange(x0, x1, size)
    ys = np.arange(y0, y1, size)
    offsets = (np.arange(probes) + 0.5) / probes * size
    gx, gy = np.meshgrid(xs, ys)
    water = np.zeros(gx.shape, dtype=bool)
    for ox in offsets:
        for oy in offsets:
            heights, land = relief.sample(gx + ox, gy + oy)
            water |= ~land
    return [(x, y, size) for x, y, wet in zip(gx.ravel(), gy.ravel(), water.ravel()) if wet]


def build_sea(relief, extent, half, collection, new_object):
    x0, x1, y0, y1 = extent
    snap = lambda value, up: (math.ceil if up else math.floor)(value / SEA_FAR_CELL) * SEA_FAR_CELL
    inner = (snap(x0, False), snap(x1, True), snap(y0, False), snap(y1, True))
    cells = water_cells(relief, *inner, SEA_CELL)
    coarse = np.arange(-half, half, SEA_FAR_CELL)
    for x in coarse:
        for y in coarse:
            if x + SEA_FAR_CELL > inner[0] and x < inner[1] and y + SEA_FAR_CELL > inner[2] and y < inner[3]:
                continue
            reaches_land = abs(x + SEA_FAR_CELL / 2) < FAR_REACH and abs(y + SEA_FAR_CELL / 2) < FAR_REACH
            if not reaches_land or water_cells(relief, x, x + SEA_FAR_CELL, y, y + SEA_FAR_CELL, SEA_FAR_CELL, 9):
                cells.append((x, y, SEA_FAR_CELL))
    vertices = []
    faces = []
    for x, y, size in cells:
        start = len(vertices)
        vertices += [(x, y, SEA_SURFACE), (x + size, y, SEA_SURFACE), (x + size, y + size, SEA_SURFACE),
                     (x, y + size, SEA_SURFACE)]
        faces.append((start, start + 1, start + 2, start + 3))
    material = principled_material("sea", color=(0.05, 0.15, 0.19), roughness=0.2, vertex_color=False)
    mesh = bpy.data.meshes.new("sea")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    sea = new_object("sea", mesh, collection)
    sea["cast_shadow"] = False
    return sea

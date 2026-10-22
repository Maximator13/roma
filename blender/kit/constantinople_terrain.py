import math
import os

import bpy
import numpy as np

from .terrain import GeoFrame, HeightField, polygon_mask

DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/Copernicus_DSM_COG_10_{0}_DEM.tif"
DEM_TILES = ("N41_00_E028_00", "N40_00_E028_00", "N41_00_E029_00", "N40_00_E029_00")
DEM_LICENCE = ("Copernicus DEM GLO-30 (ESA, Copernicus programme), free licence with attribution: produced using "
               "Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 "
               "provided under COPERNICUS by the European Union and ESA")
STEP = 1.0 / 3600.0
CROP = (41.17, 28.78, 1260, 1440)
ORIGIN = (41.0075, 28.9775)
FRAME = GeoFrame(*ORIGIN)


def local(latitude, longitude):
    return FRAME.to_local(latitude, longitude)


def tile_grid(path):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    width, height = image.size
    pixels = np.empty(width * height * image.channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    grid = pixels.reshape(height, width, image.channels)[::-1, :, 0].astype(np.float32)
    bpy.data.images.remove(image)
    return grid


def load_dem(cache_dir):
    cached = os.path.join(cache_dir, "src", "dem", "istanbul_crop_v1.npy")
    if os.path.exists(cached):
        return np.load(cached)
    north, west, rows, columns = CROP
    mosaic = np.zeros((rows, columns), dtype=np.float32)
    from .materials import download
    for tile in DEM_TILES:
        path = download(DEM_URL.format(tile), os.path.join(cache_dir, "src", "dem", f"glo30_{tile}.tif"))
        grid = tile_grid(path)
        tile_north = int(tile[1:3]) + 1
        tile_west = int(tile[8:11])
        size = grid.shape[0]
        r0 = int(round((tile_north - north) / STEP))
        c0 = int(round((west - tile_west) / STEP))
        source_columns = np.arange(columns) + c0
        valid = (source_columns >= 0) & (source_columns < grid.shape[1])
        for row in range(rows):
            source_row = row + r0
            if 0 <= source_row < size:
                mosaic[row, valid] = grid[source_row, source_columns[valid]]
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    np.save(cached, mosaic)
    return mosaic


def dem_sampler(dem):
    north, west, rows, columns = CROP

    def sample(xs, ys):
        latitude, longitude = FRAME.to_geo(np.asarray(xs, np.float64), np.asarray(ys, np.float64))
        row = np.clip((north - latitude) / STEP - 0.5, 0, rows - 1.001)
        column = np.clip((longitude - west) / STEP - 0.5, 0, columns - 1.001)
        r0 = row.astype(int)
        c0 = column.astype(int)
        fy = row - r0
        fx = column - c0
        top = dem[r0, c0] * (1 - fx) + dem[r0, c0 + 1] * fx
        bottom = dem[r0 + 1, c0] * (1 - fx) + dem[r0 + 1, c0 + 1] * fx
        return top * (1 - fy) + bottom * fy
    return sample


def shifted(values, dy, dx):
    padded = np.pad(values, 1, mode="edge")
    rows, columns = values.shape
    return padded[1 + dy:1 + dy + rows, 1 + dx:1 + dx + columns]


def minimum_filter(values, passes):
    for _ in range(passes):
        values = np.minimum.reduce([shifted(values, dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
    return values


def blur(values, passes):
    for _ in range(passes):
        values = (shifted(values, -1, 0) + shifted(values, 1, 0) + shifted(values, 0, -1) + shifted(values, 0, 1)
                  + 4 * values) / 8
    return values


def chamfer(mask, spacing, iterations):
    distance = np.where(mask, 0.0, np.inf)
    diagonal = spacing * math.sqrt(2)
    for _ in range(iterations):
        candidates = [distance]
        for dy, dx, step in ((-1, 0, spacing), (1, 0, spacing), (0, -1, spacing), (0, 1, spacing),
                             (-1, -1, diagonal), (-1, 1, diagonal), (1, -1, diagonal), (1, 1, diagonal)):
            candidates.append(shifted(distance, dy, dx) + step)
        distance = np.minimum.reduce(candidates)
    return distance


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def connected_sea(raw, seeds):
    sea = raw <= 1.2
    reach = np.zeros(sea.shape, dtype=bool)
    for row, column in seeds:
        reach[row, column] = sea[row, column]
    for _ in range(200):
        grown = reach
        for _ in range(20):
            grown = sea & (grown | shifted(grown, -1, 0) | shifted(grown, 1, 0) | shifted(grown, 0, -1)
                           | shifted(grown, 0, 1))
        if np.array_equal(grown, reach):
            break
        reach = grown
    return reach


def condition(dem, half, spacing, landfill):
    sample = dem_sampler(dem)
    count = int(round(2 * half / spacing)) + 1
    axis = np.linspace(-half, half, count)
    gx, gy = np.meshgrid(axis, axis)
    raw = sample(gx, gy)
    passes = max(1, int(round(45.0 / spacing)))
    ground = blur(minimum_filter(raw, passes), passes + 2)
    seeds = [(0, count // 2), (count - 1, count - 1), (count // 2, count - 1), (count - 1, count // 2)]
    modern_sea = connected_sea(raw, [(r, c) for r, c in seeds])
    land_distance = chamfer(modern_sea, spacing, int(160.0 / spacing) + 2)
    fill = np.zeros(gx.shape, dtype=bool)
    for polygon in landfill:
        fill |= polygon_mask(polygon, gx, gy)
    ancient_sea = modern_sea | (fill & (land_distance < 140.0) & (ground < 9.0))
    shore = blur(np.where(ancient_sea, -1.0, 1.0), 3)
    ancient_sea = shore < 0.0
    to_land = chamfer(~ancient_sea, spacing, int(400.0 / spacing) + 2)
    to_sea = chamfer(ancient_sea, spacing, int(240.0 / spacing) + 2)
    to_land = np.minimum(to_land, 400.0)
    to_sea = np.minimum(to_sea, 240.0)
    coastal = np.minimum(np.maximum(ground, 0.0), 1.2 + to_sea * 0.12)
    land = np.where(to_sea < 60.0, np.maximum(coastal, ground * smoothstep(to_sea / 60.0)), ground)
    land = np.maximum(land, 0.6 + to_sea * 0.02)
    bed = -1.2 - 0.11 * to_land - 0.0004 * to_land * to_land
    heights = np.where(ancient_sea, np.maximum(bed, -42.0), land)
    heights = blur(heights, 1)
    return HeightField(heights, half), ancient_sea, to_sea


def far_field(dem, half, spacing):
    sample = dem_sampler(dem)
    count = int(round(2 * half / spacing)) + 1
    axis = np.linspace(-half, half, count)
    gx, gy = np.meshgrid(axis, axis)
    raw = sample(gx, gy)
    latitude, longitude = FRAME.to_geo(gx, gy)
    north, west, rows, columns = CROP
    inside = (latitude < north - 0.002) & (latitude > north - rows * STEP + 0.002) & (longitude > west + 0.002) & (
        longitude < west + columns * STEP - 0.002)
    passes = max(1, int(round(60.0 / spacing)))
    ground = blur(minimum_filter(raw, passes), 2)
    sea = (raw <= 1.2) | ~inside
    to_land = chamfer(~sea, spacing, 30)
    heights = np.where(sea, np.maximum(-2.0 - to_land * 0.05, -40.0), np.maximum(ground, 0.8))
    return HeightField(heights, half), sea

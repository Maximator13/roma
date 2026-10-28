import math
import os

import numpy as np

from .constantinople_terrain import blur, chamfer, minimum_filter, shifted, smoothstep, tile_grid
from .materials import download
from .terrain import GeoFrame, HeightField, polygon_mask

DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/Copernicus_DSM_COG_10_{0}_DEM.tif"
DEM_TILES = ("N37_00_E027_00", "N36_00_E027_00")
DEM_LICENCE = ("Copernicus DEM GLO-30 (ESA, Copernicus programme), free licence with attribution: produced using "
               "Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 "
               "provided under COPERNICUS by the European Union and ESA")
STEP = 1.0 / 3600.0
CROP = (37.32, 27.0, 2160, 3240)
ORIGIN = (37.035, 27.426)
FRAME = GeoFrame(*ORIGIN)
MODERN_MOLES = [
    [(-300.0, -238.0), (-90.0, -246.0), (-80.0, -322.0), (-300.0, -330.0)],
    [(0.0, -326.0), (215.0, -322.0), (215.0, -384.0), (0.0, -388.0)],
]


def local(latitude, longitude):
    return FRAME.to_local(latitude, longitude)


def load_dem(cache_dir):
    cached = os.path.join(cache_dir, "src", "dem", "bodrum_crop_v1.npy")
    if os.path.exists(cached):
        return np.load(cached)
    north, west, rows, columns = CROP
    mosaic = np.zeros((rows, columns), dtype=np.float32)
    for tile in DEM_TILES:
        path = download(DEM_URL.format(tile), os.path.join(cache_dir, "src", "dem", f"glo30_{tile}.tif"))
        grid = tile_grid(path)
        tile_north = int(tile[1:3]) + 1
        tile_west = int(tile[8:11])
        r0 = int(round((tile_north - north) / STEP))
        c0 = int(round((west - tile_west) / STEP))
        source_columns = np.arange(columns) + c0
        valid = (source_columns >= 0) & (source_columns < grid.shape[1])
        for row in range(rows):
            source_row = row + r0
            if 0 <= source_row < grid.shape[0]:
                mosaic[row, valid] = grid[source_row, source_columns[valid]]
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    np.save(cached, mosaic)
    return mosaic


def sampler(dem):
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


def maximum_filter(values, passes):
    for _ in range(passes):
        values = np.maximum.reduce([shifted(values, dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
    return values


def grow_sea(sea, seeds):
    reach = np.zeros(sea.shape, dtype=bool)
    for row, column in seeds:
        reach[row, column] = sea[row, column]
    for _ in range(400):
        grown = reach
        for _ in range(20):
            grown = sea & (grown | shifted(grown, -1, 0) | shifted(grown, 1, 0) | shifted(grown, 0, -1)
                           | shifted(grown, 0, 1))
        if np.array_equal(grown, reach):
            break
        reach = grown
    return reach


def condition(dem, half, spacing):
    sample = sampler(dem)
    count = int(round(2 * half / spacing)) + 1
    axis = np.linspace(-half, half, count)
    gx, gy = np.meshgrid(axis, axis)
    raw = sample(gx, gy)
    moles = np.zeros(gx.shape, dtype=bool)
    for polygon in MODERN_MOLES:
        moles |= polygon_mask(polygon, gx, gy)
    passes = max(1, int(round(24.0 / spacing)))
    ground = blur(maximum_filter(minimum_filter(raw, passes), passes), 2)
    wet = (raw <= 0.6) | moles
    seeds = [(0, c) for c in range(0, count, max(count // 12, 1))]
    sea = grow_sea(wet, seeds)
    shore = blur(np.where(sea, -1.0, 1.0), 2)
    sea = shore < 0.0
    to_land = np.minimum(chamfer(~sea, spacing, int(500.0 / spacing) + 2), 500.0)
    to_sea = np.minimum(chamfer(sea, spacing, int(260.0 / spacing) + 2), 260.0)
    coastal = np.minimum(np.maximum(ground, 0.0), 0.9 + to_sea * 0.16)
    land = np.where(to_sea < 50.0, np.maximum(coastal, ground * smoothstep(to_sea / 50.0)), ground)
    land = np.maximum(land, 0.7 + to_sea * 0.025)
    bed = -0.9 - 0.16 * to_land - 0.0005 * to_land * to_land
    heights = np.where(sea, np.maximum(bed, -60.0), land)
    heights = blur(heights, 1)
    return HeightField(heights, half), sea, to_sea


def far_field(dem, half, spacing):
    sample = sampler(dem)
    count = int(round(2 * half / spacing)) + 1
    axis = np.linspace(-half, half, count)
    gx, gy = np.meshgrid(axis, axis)
    raw = sample(gx, gy)
    latitude, longitude = FRAME.to_geo(gx, gy)
    north, west, rows, columns = CROP
    inside = ((latitude < north - 0.002) & (latitude > north - rows * STEP + 0.002) & (longitude > west + 0.002)
              & (longitude < west + columns * STEP - 0.002))
    passes = max(1, int(round(50.0 / spacing)))
    ground = blur(minimum_filter(raw, passes), 2)
    sea = (raw <= 0.6) | ~inside
    to_land = chamfer(~sea, spacing, 40)
    heights = np.where(sea, np.maximum(-3.0 - to_land * 0.06, -80.0), np.maximum(ground, 1.0))
    return HeightField(heights, half), sea


def flatten(gx, gy, heights, polygon, level, margin):
    from .terrain import polyline_distance
    inside = polygon_mask(polygon, gx, gy)
    distance = polyline_distance(list(polygon) + [polygon[0]], gx, gy)
    weight = np.where(inside, 1.0, np.clip(1.0 - distance / max(margin, 1e-3), 0.0, 1.0))
    weight = weight * weight * (3 - 2 * weight)
    return heights * (1 - weight) + level * weight


def carve(gx, gy, heights, centre, facing, radius, orchestra, floor, rise, margin=10.0):
    dx = gx - centre[0]
    dy = gy - centre[1]
    distance = np.hypot(dx, dy)
    forward = dx * math.cos(facing) + dy * math.sin(facing)
    side = np.abs(-dx * math.sin(facing) + dy * math.cos(facing))
    seats = floor + np.clip(distance - orchestra, 0.0, None) * rise
    profile = np.where(forward > 0.0, floor, seats)
    reach = np.where(forward > 0.0, np.maximum(side, forward * 1.6), distance)
    weight = np.clip(1.0 - (reach - radius) / margin, 0.0, 1.0)
    weight = weight * weight * (3 - 2 * weight)
    carved = np.minimum(heights, profile - 0.4)
    return heights * (1 - weight) + carved * weight

import math
import os

import bpy
import numpy as np

from .materials import download
from .terrain import GeoFrame, polygon_mask, value_noise

DEM_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N40_00_E014_00_DEM/"
           "Copernicus_DSM_COG_10_N40_00_E014_00_DEM.tif")
DEM_LICENCE = ("Copernicus DEM GLO-30 (ESA, Copernicus programme), free licence with attribution: produced using "
               "Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 "
               "provided under COPERNICUS by the European Union and ESA")
DEM_ORIGIN = (41.0, 14.0)
DEM_STEP = 1.0 / 3600.0
VESUVIUS = (40.8213963, 14.4261967)
RIM_RADIUS = 1100.0
RIM_HEIGHT = 1190.0
FLOOR_HEIGHT = 1105.0
CAP_RADIUS = 3300.0
BLEND_INNER = 2900.0
BLEND_OUTER = 3700.0
SHORE_SHIFT = 1000.0
SEA_FLOOR = -4.0


class Field:
    def __init__(self, x0, y0, spacing, heights):
        self.x0 = x0
        self.y0 = y0
        self.spacing = spacing
        self.heights = heights
        rows, columns = heights.shape
        self.xs = x0 + np.arange(columns) * spacing
        self.ys = y0 + np.arange(rows) * spacing
        self.grid_x, self.grid_y = np.meshgrid(self.xs, self.ys)

    def sample(self, x, y):
        rows, columns = self.heights.shape
        column = np.clip((np.asarray(x, dtype=np.float64) - self.x0) / self.spacing, 0, columns - 1.001)
        row = np.clip((np.asarray(y, dtype=np.float64) - self.y0) / self.spacing, 0, rows - 1.001)
        c0 = np.floor(column).astype(int)
        r0 = np.floor(row).astype(int)
        fx = column - c0
        fy = row - r0
        h = self.heights
        lower = h[r0, c0] * (1 - fx) + h[r0, c0 + 1] * fx
        upper = h[r0 + 1, c0] * (1 - fx) + h[r0 + 1, c0 + 1] * fx
        result = lower * (1 - fy) + upper * fy
        return float(result) if np.ndim(result) == 0 else result


def load_dem(cache_dir):
    path = download(DEM_URL, os.path.join(cache_dir, "src", "dem", "glo30_N40_E014.tif"))
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    width, height = image.size
    pixels = np.empty(width * height * image.channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    grid = pixels.reshape(height, width, image.channels)[::-1, :, 0].astype(np.float64)
    bpy.data.images.remove(image)
    return grid


def resample(dem, frame, xs, ys):
    latitude, longitude = frame.to_geo(xs, ys)
    rows = (DEM_ORIGIN[0] - latitude) / DEM_STEP
    columns = (longitude - DEM_ORIGIN[1]) / DEM_STEP
    limit = dem.shape[0] - 1.001
    rows = np.clip(rows, 0, limit)
    columns = np.clip(columns, 0, limit)
    r0 = rows.astype(int)
    c0 = columns.astype(int)
    fy = rows - r0
    fx = columns - c0
    top = dem[r0, c0] * (1 - fx) + dem[r0, c0 + 1] * fx
    bottom = dem[r0 + 1, c0] * (1 - fx) + dem[r0 + 1, c0 + 1] * fx
    return top * (1 - fy) + bottom * fy


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


def chamfer_distance(mask, spacing, iterations):
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


def vesuvius_cap(dx, dy, edge):
    radius = np.hypot(dx, dy)
    angle = np.arctan2(dy, dx)
    rim = RIM_HEIGHT + 40.0 * np.sin(2 * angle + 1.1) + 18.0 * np.sin(5 * angle + 0.4)
    inner = radius / RIM_RADIUS
    floor = FLOOR_HEIGHT + (rim - 22.0 - FLOOR_HEIGHT) * inner ** 3
    lip = rim - 22.0 + 22.0 * smoothstep((inner - 0.8) / 0.2)
    summit = np.where(inner < 0.8, floor, lip)
    t = np.clip((radius - RIM_RADIUS) / (CAP_RADIUS - RIM_RADIUS), 0.0, 1.0)
    shoulder = 1.0 - (1.0 - t) ** 1.6
    flank = rim + (edge - rim) * shoulder
    wobble = 0.5 + 0.5 * np.sin(angle * 3 + 0.7)
    streaks = world_noise(angle * 1400.0 + 9000.0, radius * 0.06, 40.0, 17, 3)
    gullies = (streaks - 0.5) * 2.0 + 0.25 * np.sin(angle * (31 + 8 * wobble))
    depth = 34.0 * np.sin(np.pi * t) * np.clip(gullies, -1.0, 0.35)
    return np.where(radius < RIM_RADIUS, summit, flank + depth)


def ring_heights(field_heights, xs, ys, vx, vy, radius, count=360):
    angles = np.linspace(-math.pi, math.pi, count, endpoint=False)
    px = vx + radius * np.cos(angles)
    py = vy + radius * np.sin(angles)
    spacing = xs[1] - xs[0]
    columns = np.clip((px - xs[0]) / spacing, 0, len(xs) - 1.001).astype(int)
    rows = np.clip((py - ys[0]) / spacing, 0, len(ys) - 1.001).astype(int)
    values = field_heights[rows, columns]
    for _ in range(12):
        values = (np.roll(values, 1) + np.roll(values, -1) + 2 * values) / 4
    return angles, values


def condition(frame, dem, x0, y0, size, spacing, town_polygon, town_centre):
    count = int(round(size / spacing)) + 1
    xs = x0 + np.arange(count) * spacing
    ys = y0 + np.arange(count) * spacing
    grid_x, grid_y = np.meshgrid(xs, ys)
    raw = resample(dem, frame, grid_x, grid_y)
    ground = blur(minimum_filter(raw, 2), 3)
    inside = polygon_mask(town_polygon, grid_x, grid_y)
    town_distance = chamfer_distance(inside, spacing, 12)
    town_weight = smoothstep(1.0 - town_distance / 75.0)
    excavated = blur(raw, 6) - 1.5
    heights = ground * (1 - town_weight) + excavated * town_weight
    centre_distance = np.hypot(grid_x - town_centre[0], grid_y - town_centre[1])
    deposit = np.clip(5.0 - 3.5 * centre_distance / 6000.0, 1.5, 5.0)
    plain = smoothstep((60.0 - heights) / 30.0) * smoothstep((town_distance - 20.0) / 90.0)
    heights = heights - deposit * plain
    sea = raw <= 0.5
    reach = np.zeros(sea.shape, dtype=bool)
    reach[:, 0] = sea[:, 0]
    for _ in range(40):
        grown = reach
        for _ in range(25):
            grown = sea & (grown | shifted(grown, -1, 0) | shifted(grown, 1, 0) | shifted(grown, 0, -1)
                           | shifted(grown, 0, 1))
        if np.array_equal(grown, reach):
            break
        reach = grown
    modern_sea = reach
    coast_distance = chamfer_distance(modern_sea, spacing, int(SHORE_SHIFT * 1.6 / spacing))
    along = np.abs(grid_y - town_centre[1])
    shift = SHORE_SHIFT * (1.0 - 0.55 * smoothstep((along - 3500.0) / 5000.0))
    ancient_sea = modern_sea | ((coast_distance < shift) & (raw < 14.0))
    shore_distance = np.minimum(chamfer_distance(~ancient_sea, spacing, 40), 2000.0)
    land_distance = np.minimum(chamfer_distance(ancient_sea, spacing, 14), 2000.0)
    vx, vy = frame.to_local(*VESUVIUS)
    angles, edge_values = ring_heights(heights, xs, ys, vx, vy, CAP_RADIUS)
    dx, dy = grid_x - vx, grid_y - vy
    radius = np.hypot(dx, dy)
    edge = np.interp(np.arctan2(dy, dx), angles, edge_values, period=2 * math.pi)
    volcano = vesuvius_cap(dx, dy, edge)
    noise = value_noise(grid_x.shape, 24, 41, 4) - 0.5
    volcano = volcano + noise * 24.0 * smoothstep((radius - RIM_RADIUS) / 500.0)
    weight = smoothstep((BLEND_OUTER - radius) / (BLEND_OUTER - BLEND_INNER))
    heights = heights * (1 - weight) + volcano * weight
    signed = blur(np.where(ancient_sea, -shore_distance, land_distance), 14)
    ancient_sea = signed < 0.0
    ramp = 0.3 + np.maximum(signed, 0.0) * 0.025
    land = np.where(heights < ramp + 3.0, np.minimum(np.maximum(heights, 0.3), ramp), heights)
    heights = np.where(ancient_sea, np.maximum(signed * 0.02, -40.0), land)
    beach = smoothstep(1.0 - signed / 110.0) * (~ancient_sea)
    masks = {"inside": inside, "sea": ancient_sea, "beach": beach, "town_weight": town_weight,
             "volcano": weight, "volcano_radius": radius, "town_distance": town_distance}
    return Field(x0, y0, spacing, heights), masks, (vx, vy)


def vent_position(frame):
    vx, vy = frame.to_local(*VESUVIUS)
    return vx, vy, FLOOR_HEIGHT + 4.0


def frame_for(latitude, longitude):
    return GeoFrame(latitude, longitude)


def lattice(ix, iy, seed):
    value = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((value ^ (value >> 16)) & 0xFFFF) / 65535.0


def world_noise(xs, ys, scale, seed, octaves=4, persistence=0.5):
    total = np.zeros(np.shape(xs))
    amplitude = 1.0
    norm = 0.0
    for octave in range(octaves):
        fx = np.asarray(xs, dtype=np.float64) / scale * 2 ** octave
        fy = np.asarray(ys, dtype=np.float64) / scale * 2 ** octave
        ix = np.floor(fx).astype(np.int64)
        iy = np.floor(fy).astype(np.int64)
        tx = smoothstep(fx - ix)
        ty = smoothstep(fy - iy)
        s = seed + octave * 101
        a = lattice(ix, iy, s)
        b = lattice(ix + 1, iy, s)
        c = lattice(ix, iy + 1, s)
        d = lattice(ix + 1, iy + 1, s)
        total += amplitude * ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
        norm += amplitude
        amplitude *= persistence
    return total / norm

import math
import os

import bpy
import numpy as np

from . import olympie_plan as plan
from .materials import download
from .pompei_terrain import blur, minimum_filter, world_noise

DEM_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N37_00_E021_00_DEM/"
           "Copernicus_DSM_COG_10_N37_00_E021_00_DEM.tif")
SOURCE = {
    "name": "Copernicus DEM GLO-30, tile N37 E021",
    "url": DEM_URL,
    "licence": ("Copernicus DEM licence, free use with attribution: produced using Copernicus WorldDEM-30 (c) DLR e.V. "
                "2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European "
                "Union and ESA"),
    "processing": ("minimum filter and blur to remove canopy, ancient ground levelled around the Altis, river beds carved, "
                   "Kronion summit raised back to about 80 m above the Altis after the canopy filter flattened it"),
}
DEM_NORTH = 38.0
DEM_WEST = 21.0
STEP = 1.0 / 3600.0
CROP = (37.96, 21.24, 2200, 2700)
FINE = (-760.0, -700.0, 1520.0, 2.0)
MID = (-7000.0, -7000.0, 14000.0, 20.0)
FAR = (-34000.0, -34000.0, 68000.0, 200.0)
KRONION_TOP = (112.0, 305.0)
KRONION_FLANK = (5.0, 225.0, 95.0)


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def load_dem(cache_dir):
    cached = os.path.join(cache_dir, "src", "dem", "olympia_crop_v2.npy")
    if os.path.exists(cached):
        return np.load(cached)
    path = download(DEM_URL, os.path.join(cache_dir, "src", "dem", "glo30_N37_E021.tif"))
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    width, height = image.size
    pixels = np.empty(width * height * image.channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    grid = pixels.reshape(height, width, image.channels)[::-1, :, 0].astype(np.float64)
    bpy.data.images.remove(image)
    north, west, rows, columns = CROP
    r0 = int(round((DEM_NORTH - north) / STEP))
    c0 = int(round((west - DEM_WEST) / STEP))
    crop = grid[r0:r0 + rows, c0:c0 + columns]
    land = crop > 1.0
    cleaned = blur(minimum_filter(crop, 1), 2)
    cleaned = np.where(land, cleaned, np.minimum(crop, cleaned))
    np.save(cached, cleaned)
    return cleaned


def dem_sampler(dem):
    north, west, rows, columns = CROP

    def sample(xs, ys):
        latitude, longitude = plan.FRAME.to_geo(np.asarray(xs, np.float64), np.asarray(ys, np.float64))
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


def polyline_measure(points, xs, ys, reach=None):
    xs = np.asarray(xs, np.float64)
    ys = np.asarray(ys, np.float64)
    best = np.full(xs.shape, np.inf)
    station = np.zeros(xs.shape)
    total = 0.0
    if reach is not None and xs.size:
        bx0, bx1 = float(xs.min()) - reach, float(xs.max()) + reach
        by0, by1 = float(ys.min()) - reach, float(ys.max()) + reach
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        dx, dy = bx - ax, by - ay
        length_squared = dx * dx + dy * dy
        length = math.sqrt(length_squared)
        if reach is not None and (max(ax, bx) < bx0 or min(ax, bx) > bx1 or max(ay, by) < by0 or min(ay, by) > by1):
            total += length
            continue
        t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / length_squared, 0.0, 1.0)
        distance = np.hypot(xs - (ax + t * dx), ys - (ay + t * dy))
        closer = distance < best
        best = np.where(closer, distance, best)
        station = np.where(closer, total + t * length, station)
        total += length
    return best, station


def stations(points):
    result = [0.0]
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        result.append(result[-1] + math.hypot(bx - ax, by - ay))
    return np.array(result)


KLADEOS_STATIONS = stations(plan.KLADEOS)
ALPHEIOS_STATIONS = stations(plan.ALPHEIOS)


def kladeos_level(station):
    return np.interp(station, KLADEOS_STATIONS, plan.KLADEOS_LEVELS)


def box_distance(xs, ys, x0, x1, y0, y1, west_scale=1.0):
    dx = np.maximum(x0 - xs, 0.0) * west_scale + np.maximum(xs - x1, 0.0)
    dy = np.maximum(np.maximum(y0 - ys, ys - y1), 0.0)
    return np.hypot(dx, dy)


def stadium_bank(xs, ys):
    x0, x1, y0, y1 = plan.ARENA
    d_south = box_distance(xs, ys, x0, x1, y0, y1, 1.7)
    crest = 25.0
    height = np.where(d_south <= crest, 7.6 * smoothstep(d_south / 6.0) * 0.25 + 7.6 * np.clip(d_south / crest, 0, 1) * 0.75,
                      7.6 - (d_south - crest) * 0.42)
    inside = d_south <= 0.0
    return np.where(inside, -50.0, plan.ARENA_LEVEL + height), inside


def crypt_mask(xs, ys):
    return (xs > plan.CRYPT_WEST - 3.0) & (xs < plan.CRYPT_EAST + 1.0) & (np.abs(ys - plan.STADIUM_AXIS_Y) < 2.9)


class Terrain:
    def __init__(self, cache_dir):
        self.dem = load_dem(cache_dir)
        self.base = dem_sampler(self.dem)
        self.river_stations = np.arange(0.0, ALPHEIOS_STATIONS[-1] + 25.0, 25.0)
        points = [plan.along(plan.ALPHEIOS, s)[0] for s in self.river_stations]
        floor = self.base(np.array([p.x for p in points]), np.array([p.y for p in points])) - 1.4
        floor = np.maximum.accumulate(floor)
        kernel = np.ones(15) / 15.0
        floor = np.convolve(np.pad(floor, 7, mode="edge"), kernel, mode="valid")
        near = np.array([abs(p.x) < 1300.0 for p in points])
        blend = np.array([smoothstep((abs(p.x) - 1300.0) / 900.0) for p in points])
        self.river_levels = np.where(near, plan.ALPHEIOS_LEVEL, plan.ALPHEIOS_LEVEL * (1 - blend)
                                     + np.maximum(floor, plan.ALPHEIOS_LEVEL) * blend)
        self.fields = []
        for spec in (FINE, MID, FAR):
            x0, y0, size, spacing = spec
            count = int(round(size / spacing)) + 1
            axis_x = x0 + np.arange(count) * spacing
            axis_y = y0 + np.arange(count) * spacing
            gx, gy = np.meshgrid(axis_x, axis_y)
            self.fields.append((x0, y0, spacing, count, self.compose(gx, gy)))

    def compose(self, xs, ys):
        base = self.base(xs, ys)
        north_rise = smoothstep((ys - 150.0) / 140.0)
        site = box_distance(xs, ys, -250.0, 440.0, -230.0, 175.0)
        weight = 1.0 - smoothstep(site / 160.0)
        designed = (plan.ALTIS_LEVEL - 0.011 * np.maximum(-ys - 60.0, 0.0) - 0.004 * np.maximum(-xs - 120.0, 0.0)
                    + 0.006 * np.maximum(xs - 200.0, 0.0) * (ys > -100))
        designed += (world_noise(xs, ys, 70.0, 5, 3) - 0.5) * 0.5 * smoothstep((np.hypot(xs - 40, ys - 40) - 240) / 80)
        summit = 36.0 * np.exp(-((xs - KRONION_TOP[0]) / 85.0) ** 2 / 2 - ((ys - KRONION_TOP[1]) / 75.0) ** 2 / 2)
        base = base + summit * smoothstep((ys - 172.0) / 40.0)
        hill = np.maximum(base, designed)
        designed = designed * (1 - north_rise) + hill * north_rise
        heights = base * (1 - weight) + designed * weight
        terrace = box_distance(xs, ys, plan.TREASURY_X[0] - 12.0, plan.TREASURY_X[1] + 3.0, plan.TREASURY_FRONT,
                               plan.TREASURY_FRONT + 24.0)
        north_of_front = ys >= plan.TREASURY_FRONT
        terrace_height = np.where(terrace <= 0.0, plan.TERRACE_LEVEL,
                                  plan.TERRACE_LEVEL + np.maximum(terrace - 0.0, 0.0) * 0.18)
        heights = np.where(north_of_front & (terrace <= 0.0), plan.TERRACE_LEVEL, heights)
        rise = north_of_front & (terrace > 0.0) & (terrace < 40.0) & (ys > plan.TREASURY_FRONT + 10.0)
        heights = np.where(rise, np.maximum(heights, terrace_height), heights)
        bank, arena = stadium_bank(xs, ys)
        heights = np.maximum(heights, np.where(bank > 0, bank, -100.0))
        heights = np.where(arena, plan.ARENA_LEVEL, heights)
        heights = np.where(crypt_mask(xs, ys), plan.ARENA_LEVEL - 0.05, heights)
        distance, station = polyline_measure(plan.KLADEOS, xs, ys, 80.0)
        level = kladeos_level(station)
        channel = level - 0.9 + 1.2 * smoothstep((distance - 3.0) / 5.0) + 0.16 * np.maximum(distance - 8.0, 0.0)
        heights = np.where(distance < 60.0, np.minimum(heights, channel), heights)
        distance, station = polyline_measure(plan.ALPHEIOS, xs, ys, 300.0)
        level = self.river_level(station)
        braid = (world_noise(xs, ys, 45.0, 13, 3) - 0.5) * 1.2
        bed = np.where(distance < 26.0, level - 1.6 + 1.85 * smoothstep((distance - 12.0) / 14.0),
                       level + 0.25 + braid * smoothstep((distance - 30.0) / 30.0) * (distance < 120.0)
                       + 0.06 * np.maximum(distance - 120.0, 0.0))
        heights = np.where(distance < 260.0, np.minimum(heights, bed), heights)
        sea = base < 0.6
        heights = np.where(sea, np.minimum(heights, base - 3.0 * smoothstep((0.6 - base) / 1.2) - 0.5), heights)
        return heights

    def river_level(self, station):
        return np.interp(station, self.river_stations, self.river_levels)

    def height(self, x, y):
        xs = np.asarray(x, np.float64)
        ys = np.asarray(y, np.float64)
        result = np.full(xs.shape, np.nan)
        for x0, y0, spacing, count, values in self.fields:
            column = (xs - x0) / spacing
            row = (ys - y0) / spacing
            inside = (column >= 0) & (column <= count - 1.001) & (row >= 0) & (row <= count - 1.001) & np.isnan(result)
            if not inside.any():
                continue
            c = np.clip(column, 0, count - 1.001)
            r = np.clip(row, 0, count - 1.001)
            c0 = c.astype(int)
            r0 = r.astype(int)
            fx = c - c0
            fy = r - r0
            lower = values[r0, c0] * (1 - fx) + values[r0, c0 + 1] * fx
            upper = values[r0 + 1, c0] * (1 - fx) + values[r0 + 1, c0 + 1] * fx
            result = np.where(inside, lower * (1 - fy) + upper * fy, result)
        result = np.where(np.isnan(result), self.compose(xs, ys), result)
        return float(result) if np.ndim(result) == 0 else result


def mix(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + other * weight


def land_colour(gx, gy, terrain, footprints=None, detail=True):
    heights = terrain.height(gx, gy)
    spacing = max(float(gx[0, 1] - gx[0, 0]), 0.1)
    step = max(1, int(round(6.0 / spacing)))
    coarse = heights[::step, ::step]
    gy_, gx_ = np.gradient(coarse, spacing * step)
    slope = blur(np.hypot(gx_, gy_), 3)
    slope = np.repeat(np.repeat(slope, step, axis=0), step, axis=1)[:heights.shape[0], :heights.shape[1]]
    noise = world_noise(gx, gy, 600.0, 3, 4)
    fine = world_noise(gx, gy, 35.0, 4, 3)
    grain = world_noise(gx, gy, 6.0, 5, 2) if detail else np.full(gx.shape, 0.5)
    angle = math.radians(14.0)
    u = gx * math.cos(angle) - gy * math.sin(angle)
    v = gx * math.sin(angle) + gy * math.cos(angle)
    parcel_u = np.floor(u / 120.0).astype(np.int64)
    parcel_v = np.floor(v / 70.0).astype(np.int64)
    parcel = ((parcel_u * 73856093) ^ (parcel_v * 19349663)) % 1000 / 1000.0
    crops = np.array([[0.88, 0.66, 0.30], [0.80, 0.58, 0.24], [0.50, 0.58, 0.20], [0.78, 0.56, 0.26],
                      [0.42, 0.54, 0.18], [0.90, 0.72, 0.34], [0.72, 0.46, 0.24]])
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.88 + 0.22 * fine)[..., None]
    orchard = (parcel > 0.62) & (parcel < 0.8)
    dots = (np.sin(u * 2 * math.pi / 9.0) * np.sin(v * 2 * math.pi / 9.0)) > 0.7
    colour = np.where((orchard & dots)[..., None], colour * np.array([0.7, 0.78, 0.62]), colour)
    hedge = 0.015 + 0.03 * fine
    edge = (np.abs((u / 120.0) % 1.0 - 0.5) > 0.5 - hedge) | (np.abs((v / 70.0) % 1.0 - 0.5) > 0.5 - hedge * 1.6)
    edge &= world_noise(gx, gy, 50.0, 47, 2) > 0.3
    colour = np.where(edge[..., None], np.array([0.24, 0.34, 0.14]) * (0.8 + 0.3 * grain[..., None]), colour)
    pine = np.dstack([0.13 + 0.06 * fine, 0.24 + 0.08 * fine, 0.10 + 0.04 * fine])
    scrub = np.dstack([0.42 + 0.08 * fine, 0.42 + 0.06 * fine, 0.24 + 0.04 * fine])
    hill = smoothstep((heights - 55.0) / 40.0) * (0.55 + 0.45 * noise)
    hill = np.maximum(hill, smoothstep((slope - 0.14) / 0.12))
    upland = mix(scrub, pine, smoothstep((fine - 0.35) / 0.25) * 0.85 + smoothstep((heights - 120.0) / 200.0) * 0.4)
    colour = mix(colour, upland, hill)
    rock = np.array([0.66, 0.62, 0.54]) * (0.85 + 0.25 * noise[..., None])
    colour = mix(colour, rock, smoothstep((slope - 0.75) / 0.3) * (fine > 0.4))
    kronos = np.hypot(gx - plan.KRONOS.x, (gy - plan.KRONOS.y) * 1.2)
    woods = smoothstep((world_noise(gx, gy, 40.0, 29, 3) - 0.36) / 0.2)
    canopy = np.array([0.20, 0.28, 0.14]) * (0.8 + 0.35 * grain[..., None]) * (0.85 + 0.25 * fine[..., None])
    flank = np.hypot(gx - KRONION_FLANK[0], gy - KRONION_FLANK[1])
    wooded = np.maximum(smoothstep((235.0 - kronos) / 40.0), smoothstep((KRONION_FLANK[2] - flank) / 25.0))
    wooded = wooded * smoothstep((gy - 152.0) / 14.0) * (0.8 + 0.2 * woods)
    distance, station = polyline_measure(plan.KLADEOS, gx, gy, 80.0)
    level = kladeos_level(station)
    gravel = np.array([0.78, 0.70, 0.56]) * (0.88 + 0.2 * grain[..., None])
    wet = np.array([0.30, 0.44, 0.40]) * (0.9 + 0.2 * grain[..., None])
    reeds = np.dstack([0.36 + 0.08 * fine, 0.46 + 0.08 * fine, 0.20 + 0.04 * fine])
    colour = mix(colour, reeds, smoothstep((16.0 - distance) / 6.0) * (fine > 0.3))
    colour = mix(colour, gravel, smoothstep((7.0 - distance) / 2.0))
    colour = mix(colour, wet, smoothstep((level + 0.1 - heights) / 0.4) * (distance < 14.0))
    a_distance, a_station = polyline_measure(plan.ALPHEIOS, gx, gy, 300.0)
    a_level = terrain.river_level(a_station)
    shingle = np.array([0.78, 0.70, 0.56]) * (0.86 + 0.22 * grain[..., None]) * (0.9 + 0.14 * fine[..., None])
    reach = 38.0 + 70.0 * world_noise(gx, gy, 260.0, 37, 3)
    islands = smoothstep((world_noise(gx, gy, 55.0, 41, 3) - 0.62) / 0.08)
    colour = mix(colour, reeds * 0.9, smoothstep((reach + 35.0 - a_distance) / 25.0) * (fine > 0.45))
    colour = mix(colour, shingle, smoothstep((reach - a_distance) / 3.0))
    colour = mix(colour, reeds * 0.85, islands * smoothstep((reach - a_distance) / 12.0) * (a_distance > 30.0))
    colour = mix(colour, wet, smoothstep((a_level + 0.15 - heights) / 0.5) * (a_distance < 40.0))
    seabed = np.array([0.20, 0.30, 0.28])
    colour = mix(colour, np.array([0.86, 0.80, 0.64]), smoothstep((2.5 - heights) / 1.5))
    colour = mix(colour, seabed, smoothstep((0.2 - heights) / 1.5))
    site = box_distance(gx, gy, -230.0, 420.0, -200.0, 170.0)
    trodden = np.dstack([0.70 + 0.06 * fine, 0.54 + 0.05 * fine, 0.33 + 0.04 * fine]) * (0.9 + 0.16 * grain[..., None])
    dry_grass = np.dstack([0.60 + 0.08 * fine, 0.58 + 0.06 * fine, 0.22 + 0.05 * fine]) * (0.9 + 0.14 * grain[..., None])
    patches = smoothstep((world_noise(gx, gy, 22.0, 17, 3) - 0.46) / 0.12)
    ground = mix(trodden, dry_grass, 0.25 + patches * 0.65)
    colour = mix(colour, ground, (1 - smoothstep(site / 70.0)) * (heights > a_level + 0.4))
    colour = mix(colour, canopy, wooded)
    altis = box_distance(gx, gy, -104.0, 126.0, -52.0, 140.0)
    sanctuary = np.dstack([0.66 + 0.05 * fine, 0.50 + 0.05 * fine, 0.31 + 0.04 * fine]) * (0.9 + 0.14 * grain[..., None])
    grove = np.dstack([0.36 + 0.06 * fine, 0.44 + 0.06 * fine, 0.18 + 0.04 * fine])
    sacred = mix(sanctuary, grove, smoothstep((world_noise(gx, gy, 16.0, 23, 3) - 0.58) / 0.1) * 0.45)
    colour = mix(colour, sacred, 1 - smoothstep(altis / 6.0))
    x0, x1, y0, y1 = plan.ARENA
    arena = box_distance(gx, gy, x0, x1, y0, y1)
    clay = np.dstack([0.82 + 0.04 * fine, 0.60 + 0.04 * fine, 0.38 + 0.03 * fine]) * (0.94 + 0.1 * grain[..., None])
    bank_grass = np.dstack([0.72 + 0.06 * fine, 0.60 + 0.05 * fine, 0.38 + 0.04 * fine]) * (0.88 + 0.2 * grain[..., None])
    bank = smoothstep((40.0 - box_distance(gx, gy, x0, x1, y0, y1, 1.7)) / 8.0) * (arena > 0.5)
    colour = mix(colour, bank_grass, bank)
    colour = mix(colour, clay, 1 - smoothstep(arena / 0.8))
    lane = np.abs(gy - plan.STADIUM_AXIS_Y) < 15.0
    lines = (np.abs((gx - x0 - 10.1) % 192.27) < 0.25) & lane & (arena <= 0.0)
    colour = np.where(lines[..., None], np.array([0.94, 0.92, 0.86]), colour)
    for points, width in (([(-100.0, -42.0), (-20.0, -42.0), (40.0, -30.0), (60.0, 0.0), (90.0, 60.0), (126.0, 120.0),
                            (140.0, 146.0)], 4.5),
                          ([(-150.0, -60.0), (-104.0, -48.0)], 4.0),
                          ([(-96.0, -60.0), (-96.0, -220.0)], 4.0),
                          ([(60.0, 0.0), (100.0, -60.0), (180.0, -140.0), (300.0, -200.0)], 5.0),
                          ([(-40.0, 40.0), (-40.0, 100.0)], 3.0),
                          ([(40.0, 40.0), (40.0, 100.0)], 3.0),
                          ([(-230.0, -40.0), (-104.0, -40.0)], 3.5)):
        d, _ = polyline_measure(points, gx, gy)
        path = np.dstack([0.88 + 0.04 * fine, 0.80 + 0.04 * fine, 0.62 + 0.03 * fine]) * (0.95 + 0.1 * grain[..., None])
        colour = mix(colour, path, smoothstep((width - d) / 1.5) * 0.85)
    camps = []
    for cx, cy, rx, ry in ((60.0, -220.0, 230.0, 60.0), (520.0, 110.0, 110.0, 120.0), (-330.0, 60.0, 70.0, 140.0)):
        camps.append(1 - smoothstep(np.hypot((gx - cx) / rx, (gy - cy) / ry) - 0.7))
    trampled = smoothstep((world_noise(gx, gy, 30.0, 53, 3) - 0.4) / 0.2)
    colour = mix(colour, trodden * 0.96, np.maximum.reduce(camps) * (0.25 + 0.4 * trampled))
    if footprints is not None:
        colour *= (1.0 - 0.3 * footprints)[..., None]
    return np.clip(colour, 0.0, 1.0)


def grid_tile(name, terrain, x0, y0, size, spacing, hole=None):
    count = int(round(size / spacing)) + 1
    xs = x0 + np.arange(count) * spacing
    ys = y0 + np.arange(count) * spacing
    gx, gy = np.meshgrid(xs, ys)
    heights = terrain.height(gx, gy)
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(count * count).reshape(count, count)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(),
                             index[1:, :-1].ravel()])
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        cx = vertices[quads, 0]
        cy = vertices[quads, 1]
        inside = ((cx >= hx0 - 0.01) & (cx <= hx1 + 0.01) & (cy >= hy0 - 0.01) & (cy <= hy1 + 0.01)).all(axis=1)
        quads = quads[~inside]
    used = np.unique(quads)
    remap = np.full(count * count, -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    vertices = vertices[used]
    quads = remap[quads]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], quads.tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(quads))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    uv = np.column_stack([(vertices[:, 0] - x0) / size, (vertices[:, 1] - y0) / size])
    uv_layer.data.foreach_set("uv", uv[loops].astype(np.float32).ravel())
    mesh.update()
    return mesh


def bake_tile(terrain, x0, y0, size, resolution, footprints=None, detail=True):
    axis_x = x0 + (np.arange(resolution) + 0.5) * size / resolution
    axis_y = y0 + (np.arange(resolution) + 0.5) * size / resolution
    gx, gy = np.meshgrid(axis_x, axis_y)
    mask = footprints(gx, gy) if footprints is not None else None
    return land_colour(gx, gy, terrain, mask, detail)


def water_strip(name, points, levels, half_width, step=6.0):
    from mathutils import Vector
    vertices = []
    faces = []
    total = stations(points)
    length = total[-1]
    samples = np.arange(0.0, length + step, step)
    previous = None
    for s in samples:
        s = min(s, length)
        position, direction = plan.along(points, s)
        side = Vector((-direction.y, direction.x))
        z = float(np.interp(s, total, levels))
        left = position + side * half_width
        right = position - side * half_width
        vertices.extend([(left.x, left.y, z), (right.x, right.y, z)])
        if previous is not None:
            a = previous
            faces.append((a + 1, a, a + 2, a + 3))
        previous = len(vertices) - 2
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv = np.array(vertices)[:, :2] / 50.0
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    uv_layer.data.foreach_set("uv", uv[loops].astype(np.float32).ravel())
    mesh.update()
    return mesh


def water_plane(name, x0, y0, x1, y1, z, terrain, cell, below=0.3):
    xs = np.arange(x0, x1, cell)
    ys = np.arange(y0, y1, cell)
    gx, gy = np.meshgrid(xs, ys)
    qx = gx.ravel()
    qy = gy.ravel()
    corners_x = np.column_stack([qx, qx + cell, qx + cell, qx])
    corners_y = np.column_stack([qy, qy, qy + cell, qy + cell])
    lowest = terrain.height(corners_x, corners_y).min(axis=1)
    keep = lowest < z + below
    corners_x = corners_x[keep]
    corners_y = corners_y[keep]
    count = len(corners_x)
    vertices = np.column_stack([corners_x.ravel(), corners_y.ravel(), np.full(count * 4, z)])
    faces = np.arange(count * 4).reshape(count, 4)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", (vertices[:, :2] / 50.0).astype(np.float32).ravel())
    mesh.update()
    return mesh

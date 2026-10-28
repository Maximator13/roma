import math
import os
import struct

import bmesh
import bpy
import numpy as np

from . import mur_d_hadrien_plan as plan
from .materials import download
from .pompei_terrain import Field, blur, chamfer_distance, minimum_filter, smoothstep, world_noise
from .terrain import GeoFrame

EA_COVERAGE = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"
EA_URL = ("https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs?service=WCS"
          "&version=2.0.1&request=GetCoverage&CoverageId={}&format=image/tiff&subset=E({:.0f},{:.0f})"
          "&subset=N({:.0f},{:.0f})&SCALEFACTOR=0.5")
COP_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/"
           "Copernicus_DSM_COG_10_{0}_DEM.tif")
COP_TILES = {(55, -3): "N55_00_W003_00", (54, -3): "N54_00_W003_00", (55, -2): "N55_00_W002_00",
             (54, -2): "N54_00_W002_00"}
COP_TOP = 55.45
COP_BOTTOM = 54.55
COP_LEFT = -3.0
COP_RIGHT = -1.6
LAT_STEP = 1.0 / 3600.0
LON_STEP = 1.0 / 2400.0
SOURCE = {
    "near": {"name": "Environment Agency, LiDAR Composite DTM 1 m (2022), resampled to 2 m through the WCS service",
             "url": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs",
             "licence": "Open Government Licence v3.0",
             "attribution": "Contains Environment Agency information (c) Environment Agency and/or database right"},
    "far": {"name": "Copernicus DEM GLO-30, tiles N54 and N55, W003 and W002",
            "url": COP_URL.format("N55_00_W003_00"),
            "licence": "Copernicus DEM licence, free use with attribution",
            "attribution": ("produced using Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and "
                            "Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA")},
    "monuments": {"name": "Historic England, National Heritage List for England, scheduled monuments 1010964, "
                          "1010965, 1010966, 1010972 and 1018585 (course of the Wall and of the vallum)",
                  "url": ("https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/"
                          "National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/6"),
                  "licence": "Open Government Licence v3.0",
                  "attribution": ("(c) Historic England 2026. Contains Ordnance Survey data (c) Crown copyright and "
                                  "database right 2026")},
}
FRAME = GeoFrame(*plan.ORIGIN_GEO)


def read_tiff(path):
    with open(path, "rb") as handle:
        data = handle.read()
    order = ">" if data[:2] == b"MM" else "<"
    offset = struct.unpack(order + "I", data[4:8])[0]
    count = struct.unpack(order + "H", data[offset:offset + 2])[0]
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8}
    formats = {3: "H", 4: "I", 12: "d", 16: "Q", 11: "f"}
    tags = {}
    for index in range(count):
        entry = data[offset + 2 + 12 * index:offset + 14 + 12 * index]
        tag, kind, number = struct.unpack(order + "HHI", entry[:8])
        size = sizes.get(kind, 1) * number
        raw = entry[8:8 + size] if size <= 4 else data[struct.unpack(order + "I", entry[8:12])[0]:][:size]
        if kind in formats:
            tags[tag] = struct.unpack(order + formats[kind] * number, raw)
    width, height = tags[256][0], tags[257][0]
    grid = np.zeros((height, width), np.float32)
    if 322 in tags:
        tile_w, tile_h = tags[322][0], tags[323][0]
        across = (width + tile_w - 1) // tile_w
        for k, (start, length) in enumerate(zip(tags[324], tags[325])):
            tile = np.frombuffer(data[start:start + length], dtype=order + "f4").reshape(tile_h, tile_w)
            row, column = divmod(k, across)
            y0, x0 = row * tile_h, column * tile_w
            grid[y0:y0 + tile_h, x0:x0 + tile_w] = tile[:min(tile_h, height - y0), :min(tile_w, width - x0)]
    else:
        rows_per_strip = tags.get(278, (height,))[0]
        for k, (start, length) in enumerate(zip(tags[273], tags[279])):
            strip = np.frombuffer(data[start:start + length], dtype=order + "f4").reshape(-1, width)
            grid[k * rows_per_strip:k * rows_per_strip + strip.shape[0]] = strip
    return grid


def load_ea(cache_dir):
    x0, y0, x1, y1 = plan.EA_BOX
    e0, n0 = plan.ORIGIN_OSGB
    url = EA_URL.format(EA_COVERAGE, e0 + x0, e0 + x1, n0 + y0, n0 + y1)
    path = download(url, os.path.join(cache_dir, "src", "dem", "ea_dtm_2m_v1.tif"))
    grid = read_tiff(path)[::-1].astype(np.float64)
    bad = grid < -100.0
    if bad.any():
        grid[bad] = np.median(grid[~bad])
    return grid


def load_cop(cache_dir):
    cached = os.path.join(cache_dir, "src", "dem", "cop_crop_v1.npy")
    if os.path.exists(cached):
        return np.load(cached).astype(np.float64)
    rows = int(round((COP_TOP - COP_BOTTOM) / LAT_STEP))
    columns = int(round((COP_RIGHT - COP_LEFT) / LON_STEP))
    mosaic = np.zeros((rows, columns), np.float32)
    for (lat, lon), name in COP_TILES.items():
        path = download(COP_URL.format(name), os.path.join(cache_dir, "src", "dem", f"glo30_{name}.tif"))
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = "Non-Color"
        width, height = image.size
        pixels = np.empty(width * height * image.channels, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        tile = pixels.reshape(height, width, image.channels)[::-1, :, 0].copy()
        bpy.data.images.remove(image)
        lat_step = 1.0 / height
        lon_step = 1.0 / width
        top = lat + 1
        r = np.arange(rows)
        c = np.arange(columns)
        lat_of = COP_TOP - (r + 0.5) * LAT_STEP
        lon_of = COP_LEFT + (c + 0.5) * LON_STEP
        rows_in = (lat_of < top) & (lat_of >= lat)
        cols_in = (lon_of >= lon) & (lon_of < lon + 1)
        if not rows_in.any() or not cols_in.any():
            continue
        tile_rows = np.clip(((top - lat_of[rows_in]) / lat_step).astype(int), 0, height - 1)
        tile_cols = np.clip(((lon_of[cols_in] - lon) / lon_step).astype(int), 0, width - 1)
        mosaic[np.ix_(np.where(rows_in)[0], np.where(cols_in)[0])] = tile[np.ix_(tile_rows, tile_cols)]
    cleaned = blur(minimum_filter(mosaic.astype(np.float64), 1), 1)
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    np.save(cached, cleaned.astype(np.float32))
    return cleaned


def flood(mask, seed_row, seed_column):
    reach = np.zeros(mask.shape, dtype=bool)
    reach[seed_row, seed_column] = True
    for _ in range(400):
        grown = reach.copy()
        grown[1:, :] |= reach[:-1, :]
        grown[:-1, :] |= reach[1:, :]
        grown[:, 1:] |= reach[:, :-1]
        grown[:, :-1] |= reach[:, 1:]
        grown &= mask
        if np.array_equal(grown, reach):
            break
        reach = grown
    return reach


def vallum_profile(d, crossing):
    a = np.abs(d)
    ditch = -3.0 * smoothstep((3.6 - a) / 2.4)
    mound = 1.9 * np.where(np.abs(a - 16.5) < 3.2, np.cos(np.clip((a - 16.5) / 3.2, -1, 1) * math.pi / 2) ** 2, 0.0)
    return (ditch + mound) * (1.0 - crossing)


class Terrain:
    def __init__(self, cache_dir):
        self.ea_raw = load_ea(cache_dir)
        x0, y0, _, _ = plan.EA_BOX
        self.ea_x0 = x0 + 1.0
        self.ea_y0 = y0 + 1.0
        self.raw = Field(self.ea_x0, self.ea_y0, 2.0, self.ea_raw)
        self.cop = load_cop(cache_dir)
        self.cop_shift = (0.0, 0.0, 0.0)
        self.cop_angle = 0.0
        self.fit_cop()
        self.edited = self.raw
        self.lakes = {}
        self.wall = None
        self.crossing = None

    def cop_raw(self, x, y, angle=None, shift=None):
        angle = self.cop_angle if angle is None else angle
        sx, sy, _ = self.cop_shift if shift is None else shift
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        c, s = math.cos(angle), math.sin(angle)
        xr = x * c - y * s + sx
        yr = x * s + y * c + sy
        latitude, longitude = FRAME.to_geo(xr, yr)
        rows = np.clip((COP_TOP - latitude) / LAT_STEP - 0.5, 0, self.cop.shape[0] - 1.001)
        columns = np.clip((longitude - COP_LEFT) / LON_STEP - 0.5, 0, self.cop.shape[1] - 1.001)
        r0 = rows.astype(int)
        c0 = columns.astype(int)
        fy = rows - r0
        fx = columns - c0
        dem = self.cop
        top = dem[r0, c0] * (1 - fx) + dem[r0, c0 + 1] * fx
        bottom = dem[r0 + 1, c0] * (1 - fx) + dem[r0 + 1, c0 + 1] * fx
        return top * (1 - fy) + bottom * fy

    def cop_height(self, x, y):
        return self.cop_raw(x, y) + self.cop_shift[2]

    def fit_cop(self):
        xs, ys = np.meshgrid(np.arange(-2800.0, 1800.0, 40.0), np.arange(-1600.0, 2000.0, 40.0))
        target = self.raw.sample(xs, ys)
        best = None
        for angle in (math.radians(-0.27), 0.0, math.radians(0.27)):
            for sx in np.arange(-90.0, 91.0, 15.0):
                for sy in np.arange(-90.0, 91.0, 15.0):
                    values = self.cop_raw(xs, ys, angle, (sx, sy, 0.0))
                    difference = target - values
                    offset = float(np.median(difference))
                    score = float(np.mean(np.abs(difference - offset)))
                    if best is None or score < best[0]:
                        best = (score, angle, sx, sy, offset)
        self.fit_score = best[0]
        self.cop_angle = best[1]
        self.cop_shift = (best[2], best[3], best[4])

    def edit(self, wall_points, crossing_station):
        self.wall = wall_points
        self.crossing = crossing_station
        heights = self.ea_raw.copy()
        rows, columns = heights.shape
        gx, gy = np.meshgrid(self.ea_x0 + np.arange(columns) * 2.0, self.ea_y0 + np.arange(rows) * 2.0)
        smooth = blur(heights, 14)
        u, v = plan.fort_local(gx, gy)
        f = plan.FORT
        outside = np.hypot(np.maximum(np.abs(u) - f["half_u"], 0.0), np.maximum(np.abs(v) - f["half_v"], 0.0))
        weight = smoothstep((8.0 - outside) / 7.0)
        heights = heights * (1 - weight) + smooth * weight
        pads = [plan.MILECASTLE_37, plan.TURRET_37A, plan.TURRET_37B]
        light = blur(self.ea_raw, 8)
        for px, py in pads:
            w = smoothstep((22.0 - np.hypot(gx - px, gy - py)) / 10.0)
            heights = heights * (1 - w) + light * w
        self.pre_vallum = heights.copy()
        distance, station, side = plan.polyline_distance(plan.VALLUM_SMOOTH, gx, gy)
        cross = smoothstep((9.0 - np.abs(station - crossing_station)) / 3.0)
        carve = smoothstep((20.5 - distance) / 3.0) * (4.0 * (1.0 - cross) + 0.7 * cross)
        heights = heights - carve
        self.lakes = {}
        self.lake_masks = {}
        self.lake_shores = {}
        for name, spec in plan.LAKES.items():
            sx, sy = spec["seed"]
            r = int(round((sy - self.ea_y0) / 2.0))
            c = int(round((sx - self.ea_x0) / 2.0))
            level = float(np.median(self.ea_raw[r - 8:r + 9, c - 8:c + 9]))
            bx0, by0, bx1, by1 = spec["box"]
            inside = (gx > bx0) & (gx < bx1) & (gy > by0) & (gy < by1)
            low = inside & (self.ea_raw < level + 0.12)
            if spec.get("north", False):
                sub = np.where(inside.any(axis=0))[0], np.where(inside.any(axis=1))[0]
                c0, c1 = sub[0].min(), sub[0].max() + 1
                r0, r1 = sub[1].min(), sub[1].max() + 1
                _, _, side = plan.polyline_distance(wall_points, gx[r0:r1, c0:c1], gy[r0:r1, c0:c1])
                north = np.zeros(low.shape, dtype=bool)
                north[r0:r1, c0:c1] = side > 0
                low &= north
            mask = flood(low, r, c)
            soft = blur(mask.astype(np.float64), 3)
            heights = np.where(soft > 0.02, np.minimum(heights, level - 1.6 * np.clip(soft * 2.0, 0, 1) + 0.02),
                               heights)
            self.lakes[name] = dict(level=level + 0.12, box=spec["box"], area=float(mask.sum() * 4.0))
            self.lake_masks[name] = Field(self.ea_x0, self.ea_y0, 2.0, soft)
            self.lake_shores[name] = Field(self.ea_x0, self.ea_y0, 2.0, blur(mask.astype(np.float64), 14))
        self.edited = Field(self.ea_x0, self.ea_y0, 2.0, heights)
        self.pre_vallum_field = Field(self.ea_x0, self.ea_y0, 2.0, self.pre_vallum)

    def ea_weight(self, x, y):
        x0, y0, x1, y1 = plan.EA_BOX
        d = np.minimum.reduce([x - x0, x1 - x, y - y0, y1 - y])
        return smoothstep((d - 20.0) / 260.0)

    def height(self, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        result = self.cop_height(x, y)
        w = self.ea_weight(x, y)
        if np.any(w > 0):
            near = self.edited.sample(x, y)
            result = result * (1 - w) + near * w
        return float(result) if np.ndim(result) == 0 else result

    def ground(self, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        result = self.cop_height(x, y)
        w = self.ea_weight(x, y)
        if np.any(w > 0):
            near = self.pre_vallum_field.sample(x, y)
            result = result * (1 - w) + near * w
        return float(result) if np.ndim(result) == 0 else result

    def raw_height(self, x, y):
        return self.raw.sample(x, y)


def trace(terrain, guide, low, high, prior, pull):
    points = plan.resample_line(plan.chaikin(guide, 1), 4.0)
    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])
    tx = np.gradient(xs)
    ty = np.gradient(ys)
    norm = np.hypot(tx, ty)
    nx, ny = ty / norm, -tx / norm
    offsets = np.arange(low, high + 0.1, 1.0)
    px = xs[:, None] + nx[:, None] * offsets[None, :]
    py = ys[:, None] + ny[:, None] * offsets[None, :]
    score = terrain.raw_height(px, py) - pull * np.abs(offsets[None, :] - prior)
    chosen = offsets[np.argmax(score, axis=1)]
    padded = np.pad(chosen, 6, mode="edge")
    chosen = np.median(np.lib.stride_tricks.sliding_window_view(padded, 13), axis=1)
    for _ in range(6):
        padded = np.pad(chosen, 1, mode="edge")
        chosen = (padded[:-2] + 2 * padded[1:-1] + padded[2:]) / 4
    return [(float(x + a * chosen[i]), float(y + b * chosen[i])) for i, (x, y, a, b) in
            enumerate(zip(xs, ys, nx, ny))]


def wall_line(terrain):
    f = plan.FORT
    west_join = plan.fort_point(-f["half_u"] + f["radius"], f["half_v"])
    east_join = plan.fort_point(f["half_u"] - f["radius"], f["half_v"])
    west = trace(terrain, plan.WALL_GUIDE + [(west_join.x - 30.0, west_join.y - 4.0)], -10.0, 26.0, 9.0, 0.06)
    kept = []
    for p in west:
        if p[0] < west_join.x - 14.0 and (not kept or p[0] > kept[-1][0] + 0.5):
            kept.append(p)
    west = kept
    east = trace(terrain, [(east_join.x + 30.0, east_join.y + 9.0)] + plan.WALL_EAST, -10.0, 22.0, 6.0, 0.08)
    east = [p for p in east if not (p[0] < east_join.x + 14.0 and p[1] < east_join.y + 30.0)]
    north = plan.resample_line([tuple(west_join), tuple(east_join)], 4.0)
    line = west + north + east
    return plan.resample_line(plan.chaikin(line, 1), 3.0)


def line_distance(points, x0, y0, step, shape, reach):
    rows, columns = shape
    mask = np.zeros(shape, dtype=bool)
    dense = plan.resample_line(points, step * 0.5)
    for x, y in dense:
        c = int(round((x - x0) / step))
        r = int(round((y - y0) / step))
        if 0 <= r < rows and 0 <= c < columns:
            mask[r, c] = True
    if not mask.any():
        return np.full(shape, reach)
    return np.minimum(chamfer_distance(mask, step, int(reach / step) + 2), reach)


def mix(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + np.asarray(other) * weight


TRACKS = []


def land_colour(terrain, gx, gy, step, detail=True, near=True):
    heights = terrain.height(gx, gy)
    gy_slope, gx_slope = np.gradient(heights, step)
    slope = np.hypot(gx_slope, gy_slope)
    relief = heights - blur(heights, max(2, int(18.0 / step)))
    noise = world_noise(gx, gy, 260.0, 3, 4)
    patches = world_noise(gx, gy, 70.0, 7, 3)
    fine = world_noise(gx, gy, 9.0, 4, 3)
    grain = world_noise(gx, gy, 1.6, 5, 2) if detail else np.full(gx.shape, 0.5)
    clumps = world_noise(gx, gy, 3.5, 21, 2) if detail else np.full(gx.shape, 0.5)
    grass = np.dstack([0.36 + 0.08 * fine, 0.45 + 0.07 * fine, 0.16 + 0.04 * fine]) * (0.8 + 0.3 * clumps)[..., None]
    bents = np.dstack([0.62 + 0.06 * fine, 0.56 + 0.05 * fine, 0.30 + 0.04 * fine]) * (0.85 + 0.2 * clumps)[..., None]
    colour = mix(grass, bents, smoothstep((patches - 0.48) / 0.3) * 0.6)
    rushes = np.dstack([0.22 + 0.05 * grain, 0.32 + 0.05 * grain, 0.12 + 0.03 * grain])
    wet = smoothstep((-relief - 0.4) / 1.2) * smoothstep((0.12 - slope) / 0.08)
    colour = mix(colour, rushes, wet * (0.45 + 0.5 * fine))
    heather = np.dstack([0.46 + 0.08 * fine, 0.28 + 0.05 * fine, 0.40 + 0.07 * fine])
    heather_brown = np.dstack([0.36 + 0.05 * fine, 0.27 + 0.04 * fine, 0.20 + 0.03 * fine])
    heath = smoothstep((noise - 0.5) / 0.14) * smoothstep((relief + 0.2) / 1.0)
    heath = np.maximum(heath, smoothstep((slope - 0.18) / 0.15) * 0.8)
    heath_colour = mix(heather_brown, heather, smoothstep((world_noise(gx, gy, 24.0, 13, 3) - 0.42) / 0.12))
    colour = mix(colour, heath_colour, heath * (0.55 + 0.45 * patches))
    bracken = np.dstack([0.46 + 0.06 * fine, 0.48 + 0.05 * fine, 0.20 + 0.03 * fine])
    colour = mix(colour, bracken, smoothstep((world_noise(gx, gy, 45.0, 17, 3) - 0.66) / 0.12) * 0.5)
    rock = np.dstack([0.33 + 0.08 * grain, 0.34 + 0.08 * grain, 0.36 + 0.08 * grain])
    lichen = np.dstack([0.58 + 0.06 * grain, 0.60 + 0.05 * grain, 0.50 + 0.04 * grain])
    rock = mix(rock, lichen, smoothstep((fine - 0.62) / 0.1) * 0.6)
    cliff = smoothstep((slope - 0.55) / 0.35)
    colour = mix(colour, rock, cliff)
    scree = smoothstep((slope - 0.32) / 0.2) * (1 - cliff) * smoothstep((fine - 0.45) / 0.2)
    colour = mix(colour, np.array([0.47, 0.46, 0.44]) * (0.85 + 0.3 * grain)[..., None], scree * 0.7)
    for name, lake in terrain.lakes.items():
        bx0, by0, bx1, by1 = lake["box"]
        if gx.max() < bx0 - 60 or gx.min() > bx1 + 60 or gy.max() < by0 - 60 or gy.min() > by1 + 60:
            continue
        water = smoothstep((terrain.lake_masks[name].sample(gx, gy) - 0.3) / 0.4)
        shore = smoothstep((terrain.lake_shores[name].sample(gx, gy) - 0.03) / 0.2) * (1 - water)
        colour = mix(colour, np.array([0.58, 0.56, 0.26]) * (0.85 + 0.3 * fine)[..., None], shore * 0.8)
        colour = mix(colour, np.array([0.62, 0.42, 0.20]), shore * smoothstep((patches - 0.6) / 0.1) * 0.5)
        colour = mix(colour, np.array([0.12, 0.13, 0.12]), water)
    if near and terrain.wall is not None:
        x0, y0 = float(gx[0, 0]), float(gy[0, 0])
        distance, station, side = plan.polyline_distance(plan.VALLUM_SMOOTH, gx, gy)
        turf = np.dstack([0.46 + 0.06 * fine, 0.46 + 0.05 * fine, 0.24 + 0.04 * fine])
        colour = mix(colour, turf, smoothstep((23.0 - distance) / 4.0) * 0.7)
        wall_d = line_distance(terrain.wall, x0, y0, step, gx.shape, 40.0)
        trodden = np.dstack([0.44 + 0.06 * grain, 0.38 + 0.05 * grain, 0.25 + 0.04 * grain])
        colour = mix(colour, trodden, smoothstep((7.0 - wall_d) / 4.0) * (0.55 + 0.35 * grain))
        colour = mix(colour, np.array([0.52, 0.47, 0.36]) * (0.85 + 0.3 * grain)[..., None],
                     smoothstep((3.4 - wall_d) / 1.5) * 0.8)
        u, v = plan.fort_local(gx, gy)
        f = plan.FORT
        outside = np.hypot(np.maximum(np.abs(u) - f["half_u"], 0.0), np.maximum(np.abs(v) - f["half_v"], 0.0))
        inner = (np.abs(u) < f["half_u"]) & (np.abs(v) < f["half_v"])
        gravel = np.dstack([0.54 + 0.06 * grain, 0.49 + 0.05 * grain, 0.39 + 0.05 * grain])
        colour = mix(colour, trodden, smoothstep((30.0 - outside) / 26.0) * (0.35 + 0.45 * fine) * (1 - inner))
        streets = ((np.abs(u - plan.STREET_U) < 3.6) | (np.abs(v) < 3.6) | (np.abs(u) > f["half_u"] - 13.0)
                   | (np.abs(v) > f["half_v"] - 13.0)) & inner
        colour = mix(colour, gravel, streets.astype(np.float64) * 0.95)
        yard = inner & ~streets
        colour = mix(colour, np.array([0.42, 0.44, 0.24]) * (0.85 + 0.3 * grain)[..., None], yard * 0.85)
        for points, width in TRACKS:
            d, _, _ = plan.polyline_distance(points, gx, gy)
            colour = mix(colour, trodden * 0.92, smoothstep((width - d) / 1.6) * (0.6 + 0.3 * grain))
            colour = mix(colour, np.array([0.44, 0.38, 0.28]),
                         smoothstep((0.7 - np.abs(d - width * 0.45)) / 0.5) * 0.4 * (step < 2.0))
    shade = 0.9 + 0.16 * smoothstep((relief + 0.6) / 1.6)
    colour *= shade[..., None]
    colour *= (0.94 + 0.1 * noise)[..., None]
    return np.clip(colour, 0.0, 1.0)


def bake_tile(terrain, x0, y0, width, height, resolution, detail=True, near=True):
    rx, ry = resolution
    axis_x = x0 + (np.arange(rx) + 0.5) * width / rx
    axis_y = y0 + (np.arange(ry) + 0.5) * height / ry
    gx, gy = np.meshgrid(axis_x, axis_y)
    return land_colour(terrain, gx, gy, width / rx, detail, near)


def tile_mesh(name, terrain, x0, y0, width, height, spacing, hole=None, sink=0.0):
    nx = int(round(width / spacing)) + 1
    ny = int(round(height / spacing)) + 1
    xs = x0 + np.arange(nx) * width / (nx - 1)
    ys = y0 + np.arange(ny) * height / (ny - 1)
    gx, gy = np.meshgrid(xs, ys)
    heights = terrain.height(gx, gy)
    index = np.arange(nx * ny).reshape(ny, nx)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(),
                             index[1:, :-1].ravel()])
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        inside_v = (gx > hx0 + 0.01) & (gx < hx1 - 0.01) & (gy > hy0 + 0.01) & (gy < hy1 - 0.01)
        heights = np.where(inside_v, heights - sink, heights)
        cx = gx.ravel()[quads]
        cy = gy.ravel()[quads]
        inside = ((cx >= hx0 - 0.01) & (cx <= hx1 + 0.01) & (cy >= hy0 - 0.01) & (cy <= hy1 + 0.01)).all(axis=1)
        quads = quads[~inside]
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    used = np.unique(quads)
    remap = np.full(nx * ny, -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    vertices = vertices[used]
    quads = remap[quads]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], quads.tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(quads))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    uv = np.column_stack([(vertices[:, 0] - x0) / width, (vertices[:, 1] - y0) / height])
    uv_layer.data.foreach_set("uv", uv[loops].astype(np.float32).ravel())
    mesh.update()
    return mesh


def water_plane(name, terrain, box, level, cell, mask):
    x0, y0, x1, y1 = box
    xs = np.arange(x0, x1, cell)
    ys = np.arange(y0, y1, cell)
    gx, gy = np.meshgrid(xs, ys)
    qx = gx.ravel()
    qy = gy.ravel()
    probes = np.max([mask.sample(qx + cell * a, qy + cell * b) for a, b in
                     ((0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9))], axis=0)
    keep = probes > 0.02
    qx, qy = qx[keep], qy[keep]
    count = len(qx)
    vertices = np.column_stack([np.column_stack([qx, qx + cell, qx + cell, qx]).ravel(),
                                np.column_stack([qy, qy, qy + cell, qy + cell]).ravel(), np.full(count * 4, level)])
    faces = np.arange(count * 4).reshape(count, 4)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.uv_layers.new(name="UVMap").data.foreach_set(
        "uv", (vertices[faces.ravel()][:, :2] / 50.0).astype(np.float32).ravel())
    mesh.update()
    bpy.context.view_layer.update()
    work = bmesh.new()
    work.from_mesh(mesh)
    bmesh.ops.remove_doubles(work, verts=work.verts, dist=0.01)
    work.to_mesh(mesh)
    work.free()
    return mesh


def vallum_strip(terrain, points, crossing_station, spacing_near=3.0, spacing_far=8.0):
    offsets = [-24.0, -21.0, -19.7, -18.4, -17.4, -16.5, -15.6, -14.6, -13.3, -10.0, -6.0, -3.6, -2.4, -1.2, 1.2,
               2.4, 3.6, 6.0, 10.0, 13.3, 14.6, 15.6, 16.5, 17.4, 18.4, 19.7, 21.0, 24.0]
    total = plan.stations(points)
    samples = []
    s = 0.0
    while s < total[-1]:
        position, _ = plan.along(points, s)
        near = abs(position.x) < 900 and abs(position.y) < 600
        samples.append(s)
        s += spacing_near if near else spacing_far
    samples.append(total[-1])
    vertices = []
    colours = []
    for s in samples:
        position, direction = plan.along(points, s)
        normal = np.array([direction.y, -direction.x])
        cross = float(smoothstep((9.0 - abs(s - crossing_station)) / 3.0))
        for o in offsets:
            x = position.x + normal[0] * o
            y = position.y + normal[1] * o
            g = float(terrain.ground(x, y))
            a = abs(o)
            if a >= 23.9:
                z = g - 0.35
            elif a > 20.0:
                z = g + 0.06
            else:
                z = g + float(vallum_profile(np.array(o), cross)) + 0.06
            vertices.append((x, y, z))
            if a < 3.7 and cross < 0.5:
                tone = (0.80, 0.70, 0.58) if a > 1.1 else (0.66, 0.58, 0.50)
            elif 13.0 < a < 20.0 and cross < 0.5:
                tone = (0.95, 0.92, 0.74)
            elif cross >= 0.5 and a < 8.0:
                tone = (0.82, 0.70, 0.54)
            else:
                tone = (0.82, 0.92, 0.66)
            colours.append(tone)
    count = len(offsets)
    faces = []
    for i in range(len(samples) - 1):
        for j in range(count - 1):
            a = i * count + j
            faces.append((a, a + 1, a + count + 1, a + count))
    mesh = bpy.data.meshes.new("vallum")
    mesh.from_pydata(vertices, [], faces)
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    xy = np.array(vertices)[:, :2]
    mesh.uv_layers.new(name="UVMap").data.foreach_set("uv", (xy[loops] / 4.0).astype(np.float32).ravel())
    attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    rgba = np.column_stack([np.array(colours)[loops], np.ones(len(loops))])
    attribute.data.foreach_set("color_srgb", rgba.astype(np.float32).ravel())
    mesh.color_attributes.active_color = attribute
    mesh.update()
    return mesh

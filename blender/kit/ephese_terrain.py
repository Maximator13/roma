import math
import os

import bpy
import numpy as np

from .colisee_terrain import graded_profile, road_blend
from .constantinople_terrain import blur, minimum_filter
from .terrain import GeoFrame, point_in_polygon, polygon_mask, polyline_distance, value_noise

DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/Copernicus_DSM_COG_10_{0}_DEM.tif"
DEM_TILES = ("N37_00_E027_00", "N38_00_E027_00")
DEM_LICENCE = ("Copernicus DEM GLO-30 (ESA, Copernicus programme), free licence with attribution: produced using "
               "Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 "
               "provided under COPERNICUS by the European Union and ESA")
SOURCE = ("Copernicus DEM GLO-30 (tiles N37 E027 and N38 E027), modern delta removed by hand: coast, harbour channel, "
          "lagoons, marshes and Cayster bed restored after Kraft et al. 2007 and Stock et al. 2013 (approximate)")
STEP = 1.0 / 3600.0
CROP = (38.10, 27.12, 1080, 1620)
ORIGIN = (37.9498, 27.3637)
FRAME = GeoFrame(*ORIGIN)

NEAR = dict(x0=-5600.0, y0=-2880.0, x1=1600.0, y1=2240.0, spacing=16.0)
THEATRE_LEVEL = 4.5
FAR_HALF = 16000.0
FAR_SPACING = 160.0
SANCTUARY_LEVEL = 2.4
QUAY_TOP = 1.7
BASIN_CENTRE = (-2874.0, -644.0)
BASIN_SIZE = (360.0, 230.0)
STREET_START = (-2005.0, -935.0)
COAST = [(-4700.0, -1500.0), (-4980.0, -1050.0), (-5150.0, -560.0), (-5230.0, 0.0), (-5050.0, 700.0),
         (-4650.0, 1350.0), (-4380.0, 2000.0), (-4300.0, 2700.0), (-4650.0, 3500.0), (-5300.0, 4300.0),
         (-6200.0, 5200.0)]
CHANNEL = [(-3040.0, -575.0), (-3400.0, -545.0), (-3900.0, -520.0), (-4400.0, -505.0), (-4900.0, -500.0),
           (-5450.0, -500.0)]
RIVER = [(1400.0, 2050.0), (1000.0, 1780.0), (560.0, 1620.0), (120.0, 1560.0), (-400.0, 1640.0), (-950.0, 1560.0),
         (-1500.0, 1420.0), (-2050.0, 1460.0), (-2600.0, 1600.0), (-3150.0, 1650.0), (-3700.0, 1820.0),
         (-4200.0, 1950.0), (-4700.0, 2050.0)]
MARSHES = [(-1150.0, 420.0, 230.0, 110.0, 0.4), (-750.0, 760.0, 180.0, 90.0, -0.3), (-2150.0, 380.0, 260.0, 120.0, 0.2),
           (-1650.0, 820.0, 200.0, 80.0, 0.1), (-3700.0, -120.0, 330.0, 150.0, 0.25), (-4200.0, 380.0, 380.0, 170.0, -0.2),
           (-3350.0, 520.0, 220.0, 110.0, 0.5), (-420.0, 520.0, 150.0, 70.0, 0.6), (-2650.0, 950.0, 240.0, 90.0, -0.1),
           (-3950.0, -980.0, 260.0, 120.0, 0.3), (-90.0, 290.0, 190.0, 55.0, 0.05), (250.0, 235.0, 110.0, 65.0, 0.5)]
SANCTUARY = (-270.0, 170.0, -165.0, 165.0)
SACRED_WAY = [(-1528.0, -1665.0), (-1420.0, -1688.0), (-1290.0, -1694.0), (-1160.0, -1687.0), (-1030.0, -1690.0), (-880.0, -1665.0), (-740.0, -1580.0), (-640.0, -1420.0),
              (-590.0, -1220.0), (-575.0, -1000.0), (-585.0, -800.0), (-565.0, -600.0), (-505.0, -400.0),
              (-425.0, -230.0), (-335.0, -95.0), (-270.0, -18.0), (-232.0, 0.0)]
NORTH_ROAD = [(-1800.0, -440.0), (-1700.0, -330.0), (-1560.0, -150.0), (-1300.0, -70.0), (-1000.0, -40.0),
              (-700.0, -20.0), (-450.0, -6.0), (-232.0, 0.0)]
THEATRE = (-1840.0, -990.0)
THEATRE_AXIS = math.atan2(-228.0, 680.0)
THEATRE_RADIUS = 72.0
FLATS = [(-1905.0, -330.0, 120.0, 42.0, 0.0, 2.6, 40.0)]


def local(latitude, longitude):
    return FRAME.to_local(latitude, longitude)


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


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
    cached = os.path.join(cache_dir, "src", "dem", "ephesus_crop_v1.npy")
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


class Field:
    def __init__(self, x0, y0, spacing, values):
        self.x0 = x0
        self.y0 = y0
        self.spacing = spacing
        self.values = values
        rows, columns = values.shape
        self.xs = x0 + np.arange(columns) * spacing
        self.ys = y0 + np.arange(rows) * spacing
        self.grid_x, self.grid_y = np.meshgrid(self.xs, self.ys)

    def sample(self, x, y):
        rows, columns = self.values.shape
        column = np.clip((np.asarray(x, dtype=np.float64) - self.x0) / self.spacing, 0, columns - 1.001)
        row = np.clip((np.asarray(y, dtype=np.float64) - self.y0) / self.spacing, 0, rows - 1.001)
        c0 = np.floor(column).astype(int)
        r0 = np.floor(row).astype(int)
        fx = column - c0
        fy = row - r0
        v = self.values
        lower = v[r0, c0] * (1 - fx) + v[r0, c0 + 1] * fx
        upper = v[r0 + 1, c0] * (1 - fx) + v[r0 + 1, c0 + 1] * fx
        result = lower * (1 - fy) + upper * fy
        return float(result) if np.ndim(result) == 0 else result


def meander(points, amplitude, wavelength, seed=3):
    rng = np.random.default_rng(seed)
    dense = []
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        length = math.hypot(bx - ax, by - ay)
        count = max(int(length / 25.0), 1)
        for k in range(count):
            t = k / count
            dense.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    dense.append(points[-1])
    out = []
    travelled = 0.0
    phase = rng.uniform(0, 6.28)
    for index, (x, y) in enumerate(dense):
        a = dense[max(index - 1, 0)]
        b = dense[min(index + 1, len(dense) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        norm = math.hypot(dx, dy) or 1.0
        if index:
            travelled += math.hypot(x - dense[index - 1][0], y - dense[index - 1][1])
        swing = amplitude * math.sin(travelled / wavelength * math.tau + phase) * (0.7 + 0.3 * math.sin(travelled / 900.0))
        out.append((x - dy / norm * swing, y + dx / norm * swing))
    return out


RIVER_PATH = meander(RIVER, 55.0, 520.0)


def sea_polygon():
    return COAST + [(-60000.0, 60000.0), (-60000.0, -60000.0)]


def basin_frame():
    sx, sy = STREET_START
    bx, by = BASIN_CENTRE
    angle = math.atan2(sy - by, sx - bx)
    return angle


def basin_polygon(grow=0.0):
    angle = basin_frame()
    c, s = math.cos(angle), math.sin(angle)
    hx, hy = BASIN_SIZE[0] / 2 + grow, BASIN_SIZE[1] / 2 + grow
    bx, by = BASIN_CENTRE
    return [(bx + c * u - s * v, by + s * u + c * v) for u, v in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def ellipse_value(gx, gy, cx, cy, rx, ry, angle):
    c, s = math.cos(angle), math.sin(angle)
    u = (gx - cx) * c + (gy - cy) * s
    v = -(gx - cx) * s + (gy - cy) * c
    return np.hypot(u / rx, v / ry)


def rect_distance(gx, gy, polygon):
    inside = polygon_mask(polygon, gx, gy)
    distance = polyline_distance(list(polygon) + [polygon[0]], gx, gy)
    return np.where(inside, -distance, distance)


class Landscape:
    def __init__(self, dem):
        self.sample_dem = dem_sampler(dem)
        spec = NEAR
        columns = int(round((spec["x1"] - spec["x0"]) / spec["spacing"])) + 1
        rows = int(round((spec["y1"] - spec["y0"]) / spec["spacing"])) + 1
        xs = spec["x0"] + np.arange(columns) * spec["spacing"]
        ys = spec["y0"] + np.arange(rows) * spec["spacing"]
        gx, gy = np.meshgrid(xs, ys)
        self.masks = self.mask_fields()
        heights = self.compose(gx, gy, self.sample_dem(gx, gy), spec["spacing"])
        self.near = Field(spec["x0"], spec["y0"], spec["spacing"], heights)
        self.roads = {}
        for name, points in (("sacred", SACRED_WAY), ("north", NORTH_ROAD)):
            dense, levels = graded_profile(points, lambda x, y: self.near.sample(x, y), 0.05, 6.0, 90.0)
            levels = [max(z, 0.9) + 0.05 for z in levels]
            self.roads[name] = (dense, levels)
            heights = road_blend(gx, gy, heights, dense, levels, 5.0, 14.0)
        self.near.values = heights
        count = int(round(2 * FAR_HALF / FAR_SPACING)) + 1
        axis = np.linspace(-FAR_HALF, FAR_HALF, count)
        fx, fy = np.meshgrid(axis, axis)
        far = self.compose(fx, fy, self.sample_dem(fx, fy), FAR_SPACING, far=True)
        self.far = Field(-FAR_HALF, -FAR_HALF, FAR_SPACING, far)

    def mask_fields(self):
        spacing = 8.0
        x0, y0, x1, y1 = NEAR["x0"] - 40.0, NEAR["y0"] - 40.0, NEAR["x1"] + 40.0, NEAR["y1"] + 40.0
        xs = np.arange(x0, x1 + spacing, spacing)
        ys = np.arange(y0, y1 + spacing, spacing)
        gx, gy = np.meshgrid(xs, ys)
        fields = {}
        coast = polyline_distance(COAST, gx, gy)
        sea = polygon_mask(sea_polygon(), gx, gy)
        fields["coast"] = Field(x0, y0, spacing, np.where(sea, -coast, coast))
        fields["channel"] = Field(x0, y0, spacing, polyline_distance(CHANNEL, gx, gy))
        fields["river"] = Field(x0, y0, spacing, polyline_distance(RIVER_PATH, gx, gy))
        fields["basin"] = Field(x0, y0, spacing, rect_distance(gx, gy, basin_polygon()))
        marsh = np.full(gx.shape, 9.0)
        for cx, cy, rx, ry, angle in MARSHES:
            marsh = np.minimum(marsh, ellipse_value(gx, gy, cx, cy, rx, ry, angle))
        noise = value_noise(gx.shape, 60, 11, 3)
        fields["marsh"] = Field(x0, y0, spacing, marsh + (noise - 0.5) * 0.5)
        x_a, x_b, y_a, y_b = SANCTUARY
        fields["sanctuary"] = Field(x0, y0, spacing, rect_distance(gx, gy, [(x_a, y_a), (x_b, y_a), (x_b, y_b),
                                                                             (x_a, y_b)]))
        fields["roads"] = Field(x0, y0, spacing, np.minimum(polyline_distance(SACRED_WAY, gx, gy),
                                                            polyline_distance(NORTH_ROAD, gx, gy)))
        fields["theatre"] = Field(x0, y0, spacing, np.hypot(gx - THEATRE[0], gy - THEATRE[1]))
        return fields

    def field(self, name, gx, gy, default):
        x0, y0, x1, y1 = NEAR["x0"] - 40.0, NEAR["y0"] - 40.0, NEAR["x1"] + 40.0, NEAR["y1"] + 40.0
        inside = (gx > x0) & (gx < x1) & (gy > y0) & (gy < y1)
        values = self.masks[name].sample(gx, gy)
        return np.where(inside, values, default)

    def coast_distance(self, gx, gy):
        x0, y0, x1, y1 = NEAR["x0"] - 40.0, NEAR["y0"] - 40.0, NEAR["x1"] + 40.0, NEAR["y1"] + 40.0
        inside = (gx > x0) & (gx < x1) & (gy > y0) & (gy < y1)
        if inside.all():
            return self.masks["coast"].sample(gx, gy)
        coast = polyline_distance(COAST, gx, gy)
        sea = polygon_mask(sea_polygon(), gx, gy)
        return np.where(sea, -coast, coast)

    def compose(self, gx, gy, raw, spacing, far=False):
        passes = max(1, int(round(36.0 / spacing)))
        ground = blur(minimum_filter(raw, passes), passes + 2)
        reach = max(2, int(round(320.0 / spacing)))
        base = blur(minimum_filter(ground, reach), reach)
        relief = ground - base
        noise = value_noise(gx.shape, max(int(gx.shape[1] / 30), 4), 5, 3)
        d = self.coast_distance(gx, gy)
        plain = 0.55 + 2.1 * smoothstep(d / 5200.0) + 0.35 * (noise - 0.5)
        hill = smoothstep((relief - 6.0) / 14.0)
        land = np.maximum(plain, ground - 5.0 * (1.0 - hill))
        beach = 0.2 + np.maximum(d, 0.0) * 0.01
        land = np.where(hill < 0.5, np.minimum(land, beach), land)
        bed = np.maximum(-0.7 + d * 0.011, -26.0)
        sea_land = (d < 0) & (ground > 12.0)
        heights = np.where((d >= 0) | sea_land, land, bed)
        if not far:
            self.relief = Field(gx[0, 0], gy[0, 0], spacing, relief)
        if far:
            deep = np.maximum(-3.0 - np.maximum(-d, 0.0) * 0.004, -40.0)
            heights = np.where(raw < 0.6, np.minimum(heights, deep), heights)
            return heights
        channel = self.field("channel", gx, gy, 999.0)
        heights = np.where(channel < 60.0, np.minimum(heights, 1.2 + (channel - 30.0) * 0.02), heights)
        heights = np.minimum(heights, np.where(channel < 19.0, -2.8, 1.0e5))
        heights = np.minimum(heights, -2.8 + smoothstep((channel - 17.0) / 12.0) * 4.0 + (channel >= 29.0) * 1.0e5)
        river = self.field("river", gx, gy, 999.0)
        bank = -1.9 + smoothstep((river - 16.0) / 18.0) * 2.8
        heights = np.where(river < 34.0, np.minimum(heights, bank), heights)
        marsh = self.field("marsh", gx, gy, 9.0)
        pool = -0.55 + smoothstep((marsh - 0.75) / 0.35) * 1.0
        lowland = hill < 0.4
        heights = np.where(lowland & (marsh < 1.1), np.minimum(heights, pool), heights)
        heights = np.where(lowland & (marsh >= 1.1) & (marsh < 1.8),
                           np.minimum(heights, 0.45 + (marsh - 1.1) * 1.4), heights)
        basin = self.field("basin", gx, gy, 999.0)
        quay = np.where(basin < 0.0, -4.2, QUAY_TOP)
        weight = smoothstep(1.0 - (basin - 40.0) / 50.0)
        heights = np.where(basin < 40.0, quay, heights * (1 - weight) + QUAY_TOP * weight)
        sanctuary = self.field("sanctuary", gx, gy, 999.0)
        weight = smoothstep(1.0 - sanctuary / 70.0)
        heights = heights * (1 - weight) + SANCTUARY_LEVEL * weight
        for cx, cy, hx, hy, angle, level, margin in FLATS:
            c, sn = math.cos(angle), math.sin(angle)
            u = np.abs((gx - cx) * c + (gy - cy) * sn) - hx
            v = np.abs(-(gx - cx) * sn + (gy - cy) * c) - hy
            outside = np.hypot(np.maximum(u, 0.0), np.maximum(v, 0.0))
            weight = smoothstep(1.0 - outside / margin)
            heights = heights * (1 - weight) + level * weight
        theatre = self.field("theatre", gx, gy, 999.0)
        angle = np.arctan2(gy - THEATRE[1], gx - THEATRE[0])
        east = np.cos(angle - THEATRE_AXIS) > -0.05
        level = THEATRE_LEVEL
        seat = level + np.clip((theatre - 12.0) / (THEATRE_RADIUS - 12.0), 0.0, 1.0) * 19.0 - 0.8
        heights = np.where((theatre < THEATRE_RADIUS + 2.0) & east, np.minimum(heights, seat), heights)
        weight = smoothstep(1.0 - (theatre - 36.0) / 60.0) * ~east
        heights = heights * (1 - weight) + level * weight
        heights = np.where((theatre < 16.0), level, heights)
        return heights

    def height(self, x, y):
        return self.near.sample(x, y)

    def is_water(self, x, y, depth=0.6):
        return self.near.sample(x, y) < -depth

    def classify(self, gx, gy, heights, slope):
        coast = self.field("coast", gx, gy, 999.0)
        return {
            "coast": coast,
            "channel": self.field("channel", gx, gy, 999.0),
            "river": self.field("river", gx, gy, 999.0),
            "marsh": self.field("marsh", gx, gy, 9.0),
            "basin": self.field("basin", gx, gy, 999.0),
            "sanctuary": self.field("sanctuary", gx, gy, 999.0),
            "roads": self.field("roads", gx, gy, 999.0),
            "theatre": self.field("theatre", gx, gy, 999.0),
        }


def mix(a, b, w):
    w = np.clip(w, 0.0, 1.0)[..., None]
    return a * (1 - w) + b * w


def colour_near(landscape, gx, gy, city_mask, seed=7, town=None):
    heights = landscape.near.sample(gx, gy)
    step = gx[0, 1] - gx[0, 0]
    gy_, gx_ = np.gradient(heights, step)
    slope = np.hypot(gx_, gy_)
    m = landscape.classify(gx, gy, heights, slope)
    shape = gx.shape
    broad = value_noise(shape, 18, seed, 4)
    fine = value_noise(shape, 140, seed + 1, 3)
    grain = value_noise(shape, 420, seed + 2, 2)
    angle = math.radians(17.0)
    u = gx * math.cos(angle) - gy * math.sin(angle)
    v = gx * math.sin(angle) + gy * math.cos(angle)
    wu = u + (broad - 0.5) * 70.0
    wv = v + (fine - 0.5) * 16.0
    strip = np.floor(wv / 46.0).astype(np.int64)
    offset = (strip * 73856093) % 997 / 997.0
    span = 70.0 + offset * 120.0
    along = (wu + offset * 400.0) / span
    cell = np.floor(along).astype(np.int64)
    parcel = ((cell * 19349663) ^ (strip * 83492791)) % 997 / 997.0
    crops = np.array([[0.70, 0.60, 0.32], [0.76, 0.66, 0.38], [0.48, 0.52, 0.24], [0.60, 0.50, 0.32],
                      [0.54, 0.54, 0.28], [0.66, 0.54, 0.34], [0.44, 0.50, 0.22], [0.72, 0.64, 0.40]])
    fields = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.9 + 0.2 * fine)[..., None]
    meadow = np.dstack([0.56 + 0.08 * broad, 0.56 + 0.07 * fine, 0.26 + 0.05 * broad])
    fallow = smoothstep((0.4 - parcel) / 0.02)
    fields = mix(fields, meadow, fallow)
    hedge = np.maximum(smoothstep((np.abs(along % 1.0 - 0.5) - 0.46) / 0.04),
                       smoothstep((np.abs((wv / 46.0) % 1.0 - 0.5) - 0.45) / 0.05))
    fields = mix(fields, np.array([0.34, 0.40, 0.20]), hedge * 0.55 * smoothstep((grain - 0.25) / 0.3))
    farmed = smoothstep((broad - 0.3) / 0.1) * smoothstep((m["coast"] - 400.0) / 300.0)
    if town is not None:
        farmed = farmed * (1.0 - town(gx, gy))
    colour = mix(meadow, fields, farmed)
    garrigue = np.dstack([0.50 + 0.08 * fine, 0.52 + 0.07 * fine, 0.30 + 0.05 * fine])
    rock = np.dstack([0.70 + 0.06 * grain, 0.64 + 0.05 * grain, 0.52 + 0.05 * grain])
    pine = np.dstack([0.30 + 0.05 * fine, 0.40 + 0.06 * fine, 0.20 + 0.04 * fine])
    hill = smoothstep((landscape.relief.sample(gx, gy) - 7.0) / 14.0) * smoothstep((heights - 3.0) / 6.0)
    hillside = mix(garrigue, pine, smoothstep((broad - 0.45) / 0.2) * 0.55 + smoothstep((fine - 0.55) / 0.15) * 0.2)
    hillside = mix(hillside, rock, smoothstep((slope - 0.6) / 0.35) * 0.8 + smoothstep((grain - 0.8) / 0.1) * 0.35)
    colour = mix(colour, hillside, hill)
    marsh_green = np.dstack([0.34 + 0.06 * fine, 0.46 + 0.06 * fine, 0.20 + 0.04 * grain])
    reed = np.dstack([0.56 + 0.06 * grain, 0.58 + 0.05 * grain, 0.32 + 0.04 * grain])
    mud = np.dstack([0.36 + 0.04 * grain, 0.34 + 0.04 * grain, 0.26 + 0.03 * grain])
    wet = smoothstep((2.0 - m["marsh"]) / 0.9) * (1 - hill)
    colour = mix(colour, mix(marsh_green, reed, smoothstep((grain - 0.5) / 0.15)), wet)
    colour = mix(colour, mud, smoothstep((1.05 - m["marsh"]) / 0.15) * (1 - hill))
    banks = np.minimum(m["river"], m["channel"])
    colour = mix(colour, mix(marsh_green, reed, 0.4), smoothstep(1.0 - (banks - 20.0) / 40.0) * (1 - hill))
    sand = np.dstack([0.86 + 0.04 * grain, 0.76 + 0.04 * grain, 0.56 + 0.04 * grain])
    colour = mix(colour, sand, smoothstep(1.0 - np.abs(m["coast"]) / 90.0) * (1 - hill * 0.7))
    earth = np.dstack([0.70 + 0.05 * grain, 0.58 + 0.05 * grain, 0.42 + 0.04 * grain])
    beaten = np.dstack([0.80 + 0.04 * grain, 0.70 + 0.04 * grain, 0.54 + 0.04 * grain])
    colour = mix(colour, mix(earth, beaten, smoothstep((grain - 0.45) / 0.2)), city_mask(gx, gy))
    colour = mix(colour, beaten, smoothstep(1.0 - (m["roads"] - 5.0) / 4.0))
    colour = mix(colour, earth, smoothstep(1.0 - (m["roads"] - 9.0) / 10.0) * 0.5)
    yard = np.dstack([0.84 + 0.04 * grain, 0.78 + 0.04 * grain, 0.64 + 0.04 * grain])
    colour = mix(colour, yard, smoothstep(1.0 - (m["basin"] - 30.0) / 30.0))
    lawn = np.dstack([0.50 + 0.07 * fine, 0.56 + 0.06 * fine, 0.30 + 0.05 * grain])
    trodden = np.dstack([0.74 + 0.05 * grain, 0.66 + 0.05 * grain, 0.50 + 0.04 * grain])
    lawn = mix(lawn, trodden, smoothstep((broad - 0.55) / 0.15) * 0.6 + smoothstep((grain - 0.7) / 0.15) * 0.3)
    colour = mix(colour, lawn, smoothstep(-m["sanctuary"] / 30.0) * 0.85)
    shallow = np.dstack([0.56 + 0.05 * fine, 0.60 + 0.05 * fine, 0.46 + 0.04 * fine])
    deep = np.array([0.05, 0.18, 0.26])
    under = mix(mud, shallow, smoothstep(-heights / 1.2))
    under = mix(under, np.broadcast_to(deep, shallow.shape), smoothstep((-heights - 1.2) / 10.0))
    colour = np.where((heights < 0.0)[..., None], under, colour)
    shade = 0.84 + 0.16 * smoothstep(1.0 - slope * 1.6)
    return np.clip(colour * shade[..., None], 0, 1)


def colour_far(landscape, gx, gy, seed=21):
    heights = landscape.far.sample(gx, gy)
    step = gx[0, 1] - gx[0, 0]
    gy_, gx_ = np.gradient(heights, step)
    slope = np.hypot(gx_, gy_)
    shape = gx.shape
    fine = value_noise(shape, 200, seed, 3)
    patches = value_noise(shape, 40, seed + 1, 4)
    angle = math.radians(17.0)
    u = gx * math.cos(angle) - gy * math.sin(angle)
    v = gx * math.sin(angle) + gy * math.cos(angle)
    parcel = ((np.floor(u / 160.0).astype(np.int64) * 73856093) ^ (np.floor(v / 110.0).astype(np.int64) * 19349663)) % 997 / 997.0
    crops = np.array([[0.56, 0.54, 0.28], [0.66, 0.60, 0.34], [0.50, 0.52, 0.26], [0.60, 0.52, 0.32], [0.52, 0.54, 0.28]])
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.9 + 0.18 * fine)[..., None]
    garrigue = np.dstack([0.48 + 0.08 * fine, 0.50 + 0.07 * fine, 0.30 + 0.05 * fine])
    wood = np.dstack([0.28 + 0.05 * fine, 0.38 + 0.06 * fine, 0.20 + 0.04 * fine])
    rock = np.dstack([0.68 + 0.06 * fine, 0.62 + 0.05 * fine, 0.52 + 0.05 * fine])
    hill = smoothstep((heights - 12.0) / 30.0)
    hillside = mix(garrigue, wood, smoothstep((patches - 0.45) / 0.2) * 0.6)
    hillside = mix(hillside, rock, smoothstep((slope - 0.55) / 0.35) * 0.8)
    colour = mix(colour, hillside, hill)
    sand = np.dstack([0.84 + 0.04 * fine, 0.74 + 0.04 * fine, 0.56 + 0.04 * fine])
    colour = mix(colour, sand, smoothstep(1.0 - heights / 1.2) * (heights > -0.2))
    deep = np.array([0.05, 0.18, 0.27])
    colour = np.where((heights < 0.0)[..., None], mix(sand * 0.8, np.broadcast_to(deep, colour.shape),
                                                       smoothstep(-heights / 6.0)), colour)
    return np.clip(colour * (0.84 + 0.16 * smoothstep(1.0 - slope * 2.0))[..., None], 0, 1)


def grid_mesh(name, field, x0, y0, x1, y1, hole=None, skirt=6.0):
    spacing = field.spacing
    xs = np.arange(x0, x1 + spacing * 0.5, spacing)
    ys = np.arange(y0, y1 + spacing * 0.5, spacing)
    gx, gy = np.meshgrid(xs, ys)
    heights = field.sample(gx, gy)
    rows, columns = gx.shape
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(rows * columns).reshape(rows, columns)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(), index[1:, :-1].ravel()])
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        cx = (gx[:-1, :-1] + gx[:-1, 1:]) / 2
        cy = (gy[:-1, :-1] + gy[1:, :-1]) / 2
        keep = ~((cx > hx0) & (cx < hx1) & (cy > hy0) & (cy < hy1))
        quads = quads[keep.ravel()]
    faces = quads.tolist()
    vertex_list = vertices.tolist()
    uvs = np.column_stack([(gx.ravel() - x0) / (x1 - x0), (gy.ravel() - y0) / (y1 - y0)]).tolist()
    if skirt > 0:
        border = (list(index[0, :]) + list(index[1:, -1]) + list(index[-1, -2::-1]) + list(index[-2:0:-1, 0]))
        start = len(vertex_list)
        for vertex in border:
            x, y, z = vertex_list[vertex]
            vertex_list.append([x, y, z - skirt])
            uvs.append(uvs[vertex])
        count = len(border)
        for position in range(count):
            following = (position + 1) % count
            faces.append([border[following], border[position], start + position, start + following])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertex_list, [], faces)
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    layer = mesh.uv_layers.new(name="UVMap")
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    layer.data.foreach_set("uv", np.asarray(uvs, dtype=np.float32)[loops].ravel())
    mesh.update()
    return mesh


def far_mesh(name, field, hole, reach=90000.0):
    mesh = grid_mesh(name, field, -FAR_HALF, -FAR_HALF, FAR_HALF, FAR_HALF, hole, skirt=0.0)
    return mesh


def inside(point, polygon):
    return point_in_polygon(point[0], point[1], polygon)


def sampled_grid(name, sample, x0, y0, x1, y1, spacing, hole=None, skirt=6.0, uv_rect=None):
    xs = np.arange(x0, x1 + spacing * 0.5, spacing)
    ys = np.arange(y0, y1 + spacing * 0.5, spacing)
    gx, gy = np.meshgrid(xs, ys)
    heights = sample(gx, gy)
    rows, columns = gx.shape
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(rows * columns).reshape(rows, columns)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(),
                             index[1:, :-1].ravel()])
    if hole is not None:
        cx = (gx[:-1, :-1] + gx[:-1, 1:]) / 2
        cy = (gy[:-1, :-1] + gy[1:, :-1]) / 2
        keep = np.ones(cx.shape, dtype=bool)
        for hx0, hy0, hx1, hy1 in hole:
            keep &= ~((cx > hx0) & (cx < hx1) & (cy > hy0) & (cy < hy1))
        quads = quads[keep.ravel()]
    used = np.unique(quads)
    remap = np.full(rows * columns, -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    vertex_list = vertices[used].tolist()
    faces = remap[quads].tolist()
    ux0, uy0, ux1, uy1 = uv_rect if uv_rect is not None else (x0, y0, x1, y1)
    uvs = np.column_stack([(vertices[used, 0] - ux0) / (ux1 - ux0), (vertices[used, 1] - uy0) / (uy1 - uy0)]).tolist()
    if skirt > 0 and hole is None:
        border = [remap[v] for v in (list(index[0, :]) + list(index[1:, -1]) + list(index[-1, -2::-1])
                                     + list(index[-2:0:-1, 0]))]
        start = len(vertex_list)
        for vertex in border:
            x, y, z = vertex_list[vertex]
            vertex_list.append([x, y, z - skirt])
            uvs.append(uvs[vertex])
        count = len(border)
        for position in range(count):
            following = (position + 1) % count
            faces.append([border[following], border[position], start + position, start + following])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertex_list, [], faces)
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    layer = mesh.uv_layers.new(name="UVMap")
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    layer.data.foreach_set("uv", np.asarray(uvs, dtype=np.float32)[loops].ravel())
    mesh.update()
    return mesh


def water_grid(name, sample, x0, y0, x1, y1, spacing, hole=None, colour=None):
    xs = np.arange(x0, x1, spacing)
    ys = np.arange(y0, y1, spacing)
    gx, gy = np.meshgrid(xs, ys)
    qx, qy = gx.ravel(), gy.ravel()
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        outside = (qx + spacing <= hx0 + 0.01) | (qx >= hx1 - 0.01) | (qy + spacing <= hy0 + 0.01) | (qy >= hy1 - 0.01)
        qx, qy = qx[outside], qy[outside]
    cx = np.column_stack([qx, qx + spacing, qx + spacing, qx])
    cy = np.column_stack([qy, qy, qy + spacing, qy + spacing])
    depth = sample(cx, cy)
    keep = depth.min(axis=1) < 0.05
    cx, cy, depth = cx[keep], cy[keep], depth[keep]
    count = len(cx)
    vertices = np.column_stack([cx.ravel(), cy.ravel(), np.zeros(count * 4)])
    faces = np.arange(count * 4).reshape(count, 4)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    layer = mesh.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", (vertices[:, :2] / 50.0).astype(np.float32).ravel())
    rgb = colour(cx.ravel(), cy.ravel(), depth.ravel())
    attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attribute.data.foreach_set("color_srgb", np.column_stack([rgb, np.ones(count * 4)]).astype(np.float32).ravel())
    mesh.color_attributes.active_color = attribute
    mesh.update()
    return mesh

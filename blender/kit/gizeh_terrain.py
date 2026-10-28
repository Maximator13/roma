import math
import os

import bpy
import numpy as np

from . import gizeh_plan as plan
from .materials import download
from .pompei_terrain import Field, blur, minimum_filter, smoothstep, world_noise
from .terrain import GeoFrame

ORIGIN = (29.9761, 31.1308)
DEM_TILES = {29: "N29_00_E031_00", 30: "N30_00_E031_00"}
DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/Copernicus_DSM_COG_10_{0}_DEM.tif"
DEM_STEP = 1.0 / 3600.0
DEM_TOP = 31.0
DEM_LEFT = 31.0
SOURCE = ("Copernicus DEM GLO-30 (ESA, programme Copernicus), tuiles N29 E031 et N30 E031, licence gratuite avec "
          "mention : produced using Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space "
          "GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA ; pyramides, villages et ville "
          "modernes retires du relief, plaine alluviale, canaux et Nil antiques redessines a la main")
FRAME = GeoFrame(*ORIGIN)
BASE = dict(x0=-16020.0, y0=-21000.0, width=42000.0, height=38000.0, spacing=30.0)
NEAR = dict(x0=-2100.0, y0=-1900.0, width=4200.0, height=3800.0, spacing=3.0)
FAR = dict(x0=-90000.0, y0=-90000.0, width=180000.0, height=180000.0, spacing=300.0)
FLOOD = plan.LEVELS["flood"]
CANAL = plan.LEVELS["canal"]
BASIN = plan.LEVELS["basin"]
NILE = plan.LEVELS["nile"]


def load_dem(cache_dir):
    rows = []
    for latitude in (30, 29):
        name = DEM_TILES[latitude]
        path = download(DEM_URL.format(name), os.path.join(cache_dir, "src", "dem", f"glo30_{name}.tif"))
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = "Non-Color"
        width, height = image.size
        pixels = np.empty(width * height * image.channels, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        rows.append(pixels.reshape(height, width, image.channels)[::-1, :, 0].copy())
        bpy.data.images.remove(image)
    return np.vstack(rows)


def resample(dem, xs, ys):
    latitude, longitude = FRAME.to_geo(xs, ys)
    rows = np.clip((DEM_TOP - latitude) / DEM_STEP, 0, dem.shape[0] - 1.001)
    columns = np.clip((longitude - DEM_LEFT) / DEM_STEP, 0, dem.shape[1] - 1.001)
    r0 = rows.astype(int)
    c0 = columns.astype(int)
    fy = rows - r0
    fx = columns - c0
    top = dem[r0, c0] * (1 - fx) + dem[r0, c0 + 1] * fx
    bottom = dem[r0 + 1, c0] * (1 - fx) + dem[r0 + 1, c0 + 1] * fx
    return top * (1 - fy) + bottom * fy


def local(latitude, longitude):
    return FRAME.to_local(latitude, longitude)


def grid(spec):
    columns = int(round(spec["width"] / spec["spacing"])) + 1
    rows = int(round(spec["height"] / spec["spacing"])) + 1
    xs = spec["x0"] + np.arange(columns) * spec["spacing"]
    ys = spec["y0"] + np.arange(rows) * spec["spacing"]
    return np.meshgrid(xs, ys)


def square_distance(gx, gy, item, margin=0.0):
    return np.maximum(np.abs(gx - item["x"]) - item["half_x"], np.abs(gy - item["y"]) - item["half_y"]) - margin


def remove_pyramids(gx, gy, ground, levels):
    for item in plan.ALL_PYRAMIDS:
        d = square_distance(gx, gy, item)
        weight = smoothstep((70.0 - d) / 45.0)
        ground = ground * (1 - weight) + levels[item["key"]] * weight
    return ground


def nile_profile(gx, gy, surface):
    distance, _ = plan.polyline_distance(plan.NILE, gx, gy)
    half = plan.NILE_HALF
    depth = 1.2 + 6.5 * smoothstep((half - distance) / 160.0)
    channel = NILE - depth
    bank = smoothstep((distance - half) / 70.0)
    shaped = np.where(distance < half, channel, NILE - 1.2 + (surface - NILE + 1.2) * bank)
    island = plan.ISLAND
    c, s = math.cos(island["angle"]), math.sin(island["angle"])
    u = (gx - island["x"]) * c + (gy - island["y"]) * s
    v = -(gx - island["x"]) * s + (gy - island["y"]) * c
    radius = np.hypot(u / island["a"], v / island["b"])
    raised = NILE + 0.9 - 3.0 * np.clip(radius - 0.8, 0.0, 1.0)
    shaped = np.where(radius < 1.1, np.maximum(shaped, raised), shaped)
    return np.where(distance < half + 80.0, shaped, surface), distance


def canal_profile(gx, gy, surface):
    nearest = np.full(gx.shape, np.inf)
    for points, half in zip(plan.CANALS, plan.CANAL_HALF):
        distance, _ = plan.polyline_distance(points, gx, gy)
        bed = CANAL - 1.4 * smoothstep((half - distance) / (half * 0.7)) - 0.25
        dyke = FLOOD + 1.1 * smoothstep((6.5 - np.abs(distance - half - 6.0)) / 3.0)
        shaped = np.where(distance < half, bed, np.maximum(surface, dyke))
        bank = (distance >= half) & (distance < half + 2.0)
        shaped = np.where(bank, CANAL + 0.35 + (distance - half) * 0.4, shaped)
        surface = np.where(distance < half + 12.0, shaped, surface)
        nearest = np.minimum(nearest, distance - half)
    for x0, x1, y0, y1 in plan.BASINS:
        d = plan.box_distance(gx, gy, x0, x1, y0, y1)
        bed = BASIN - 0.45 - 0.2 * smoothstep(-d / 30.0)
        dyke = FLOOD + 0.9 * np.exp(-((d - 3.5) / 2.2) ** 2)
        surface = np.where(d < 0.0, bed, np.where(d < 12.0, np.maximum(surface, dyke), surface))
        nearest = np.minimum(nearest, d)
    return surface, nearest


class Terrain:
    def __init__(self, dem):
        bx, by = grid(BASE)
        raw = resample(dem, bx, by)
        ground = blur(minimum_filter(raw, 2), 2)
        self.levels = {}
        for item in plan.ALL_PYRAMIDS:
            d = square_distance(bx, by, item)
            ring = (d > 60.0) & (d < 120.0)
            self.levels[item["key"]] = float(np.median(ground[ring]))
        ground = remove_pyramids(bx, by, ground, self.levels)
        self.base = self.compose(bx, by, ground, BASE)
        fx, fy = grid(FAR)
        far_raw = resample(dem, fx, fy)
        far_ground = blur(minimum_filter(far_raw, 1), 1)
        self.far = self.compose(fx, fy, far_ground, FAR)
        nx, ny = grid(NEAR)
        near_ground = self.base["desert"].sample(nx, ny)
        self.near = self.compose(nx, ny, near_ground, NEAR, detail=True)
        self.specs = [(NEAR, self.near), (BASE, self.base)]

    def compose(self, gx, gy, ground, spec, detail=False):
        edge = smoothstep((gx - plan.edge_x(gy)) / 140.0)
        low = smoothstep((30.0 - ground) / 6.0)
        flood = edge * low
        noise = world_noise(gx, gy, 260.0, 3, 3) - 0.5
        plain = FLOOD - 0.7 + 0.5 * noise
        desert = ground
        if detail:
            ripples = world_noise(gx, gy, 40.0, 9, 3) - 0.5
            desert = desert + 0.6 * ripples * (1 - flood)
            desert = self.monument_ground(gx, gy, desert)
        heights = desert * (1 - flood) + plain * flood
        lobes = 70.0 * (world_noise(gx, gy, 120.0, 23, 2) - 0.5)
        village = np.zeros(gx.shape)
        for mound in [plan.VILLAGE] + plan.HAMLETS:
            reach = mound["radius"] + lobes * mound["radius"] / plan.VILLAGE["radius"]
            village = np.maximum(village, smoothstep((reach + 30.0 - np.hypot(gx - mound["x"], gy - mound["y"]))
                                                     / 70.0))
        heights = heights + 2.2 * village * flood
        for points in plan.TRACKS[:3]:
            distance, _ = plan.polyline_distance(points, gx, gy)
            dyke = FLOOD + 1.0 * smoothstep((6.0 - distance) / 3.5)
            heights = np.where(distance < 7.0, np.maximum(heights, dyke), heights)
        heights, canal = canal_profile(gx, gy, heights)
        heights, nile = nile_profile(gx, gy, heights)
        fields = {"height": heights, "flood": flood, "canal": canal, "nile": nile, "desert": desert,
                  "village": village}
        return {key: Field(spec["x0"], spec["y0"], spec["spacing"], value) for key, value in fields.items()}

    def monument_ground(self, gx, gy, ground):
        for item in plan.GREAT + plan.QUEENS_EAST + plan.QUEENS_SOUTH:
            level = self.levels[item["key"]]
            d = square_distance(gx, gy, item)
            reach = 34.0 if item in plan.GREAT else 14.0
            weight = smoothstep((reach - d) / (reach * 0.6))
            ground = ground * (1 - weight) + (level - 0.15) * weight
        sphinx = plan.SPHINX
        pit = plan.PIT
        d_pit = plan.box_distance(gx, gy, pit["x0"], pit["x1"], pit["y0"], pit["y1"])
        rim = sphinx["rim"] + 0.5 * (world_noise(gx, gy, 30.0, 17, 2) - 0.5)
        around = smoothstep((95.0 - d_pit) / 70.0)
        ground = np.where(d_pit > 0.0, np.maximum(ground, ground * (1 - around) + rim * around), ground)
        ground = np.where(d_pit <= 7.5, sphinx["floor"] - 0.05, ground)
        terrace = plan.TERRACE
        d_terrace = plan.box_distance(gx, gy, terrace["x0"], terrace["x1"], terrace["y0"], terrace["y1"])
        slope = smoothstep((160.0 - np.maximum(d_terrace, 0.0)) / 160.0)
        mound = FLOOD + (terrace["top"] - 0.25 - FLOOD) * slope
        ground = np.where((d_terrace > -1.0) & (d_pit > 7.5), np.maximum(ground, mound), ground)
        ground = np.where((d_terrace <= 0.0) & (d_pit > 7.5), terrace["top"] - 0.3, ground)
        dy = np.abs(gy - sphinx["y"])
        cut = (gx > pit["x1"] - 0.5) & (gx < plan.STAIR_END + 7.0) & (dy < plan.STAIR["width"] / 2 + 14.0)
        inner = dy < plan.STAIR["width"] / 2 + 8.0
        lowered = np.where(inner, sphinx["floor"] - 0.1, plan.stair_fill(gx, gy) - 1.0)
        ground = np.where(cut, np.minimum(ground, lowered), ground)
        valley = plan.KHAFRE_VALLEY
        d_valley = plan.box_distance(gx, gy, valley["x0"], valley["x1"], valley["y0"], valley["y1"])
        ground = np.maximum(ground, sphinx["floor"] + 5.5 * smoothstep((24.0 - d_valley) / 30.0))
        return ground

    def field(self, x, y):
        for spec, fields in self.specs:
            margin = 2 * spec["spacing"]
            if (spec["x0"] + margin < x < spec["x0"] + spec["width"] - margin
                    and spec["y0"] + margin < y < spec["y0"] + spec["height"] - margin):
                return fields
        return self.far

    def sample(self, name, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        if np.ndim(x) == 0:
            return float(self.field(float(x), float(y))[name].sample(x, y))
        result = self.far[name].sample(x, y)
        for spec, fields in reversed(self.specs):
            margin = 2 * spec["spacing"]
            inside = ((x > spec["x0"] + margin) & (x < spec["x0"] + spec["width"] - margin)
                      & (y > spec["y0"] + margin) & (y < spec["y0"] + spec["height"] - margin))
            if inside.any():
                result = np.where(inside, fields[name].sample(x, y), result)
        return result

    def height(self, x, y):
        return self.sample("height", x, y)


def mix(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + np.asarray(other) * weight


def field_colours(gx, gy, fine):
    angle = math.radians(8.0)
    u = gx * math.cos(angle) - gy * math.sin(angle)
    v = gx * math.sin(angle) + gy * math.cos(angle)
    pu = np.floor(u / 62.0).astype(np.int64)
    pv = np.floor(v / 30.0 + 0.37 * pu).astype(np.int64)
    parcel = (((pu * 73856093) ^ (pv * 19349663)) % 1009) / 1009.0
    crops = np.array([[0.36, 0.52, 0.16], [0.42, 0.56, 0.18], [0.30, 0.46, 0.14], [0.48, 0.58, 0.22],
                      [0.28, 0.42, 0.14], [0.54, 0.58, 0.26], [0.50, 0.40, 0.26], [0.30, 0.50, 0.20],
                      [0.40, 0.52, 0.36], [0.62, 0.52, 0.32], [0.38, 0.50, 0.18]])
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.88 + 0.22 * fine)[..., None]
    rows = np.abs(((u * 2.2) % 1.0) - 0.5) < 0.12
    colour = colour * np.where(rows, 0.93, 1.0)[..., None]
    du = np.abs((u / 62.0) % 1.0 - 0.5)
    dv = np.abs((v / 30.0 + 0.37 * pu) % 1.0 - 0.5)
    ridge = (du > 0.484) | (dv > 0.47)
    colour = np.where(ridge[..., None], np.array([0.46, 0.40, 0.28]) * (0.9 + 0.2 * fine)[..., None], colour)
    return colour


def land_colour(terrain, gx, gy, step, footprints=None):
    heights = terrain.sample("height", gx, gy)
    flood = terrain.sample("flood", gx, gy)
    canal = terrain.sample("canal", gx, gy)
    nile = terrain.sample("nile", gx, gy)
    village = terrain.sample("village", gx, gy)
    gy_slope, gx_slope = np.gradient(heights, step)
    slope = np.hypot(gx_slope, gy_slope)
    noise = world_noise(gx, gy, 220.0, 3, 4)
    fine = world_noise(gx, gy, 18.0, 4, 3)
    grain = world_noise(gx, gy, 2.2, 5, 2)
    speck = world_noise(gx, gy, 0.7, 6, 1)
    sand = np.dstack([0.90 + 0.05 * fine, 0.72 + 0.05 * fine, 0.46 + 0.04 * fine])
    sand = mix(sand, np.array([0.95, 0.80, 0.56]), smoothstep((noise - 0.55) / 0.2) * 0.6)
    gravel = np.dstack([0.70 + 0.06 * grain, 0.56 + 0.05 * grain, 0.38 + 0.04 * grain])
    desert = mix(sand, gravel, smoothstep((world_noise(gx, gy, 90.0, 11, 3) - 0.5) / 0.18) * 0.55)
    desert = desert * (0.94 + 0.12 * grain)[..., None]
    desert = desert * (0.97 + 0.06 * speck)[..., None]
    strata = 0.5 + 0.5 * np.sin(heights * 2.1 + 3.0 * fine)
    rock = np.dstack([0.84 - 0.12 * strata, 0.72 - 0.12 * strata, 0.52 - 0.1 * strata])
    rock = rock * (0.9 + 0.18 * grain)[..., None]
    desert = mix(desert, rock, smoothstep((slope - 0.32) / 0.3))
    x_range = (float(gx.min()), float(gx.max()))
    y_range = (float(gy.min()), float(gy.max()))

    def near(points, reach):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return (step < 3.0 and min(xs) - reach < x_range[1] and max(xs) + reach > x_range[0]
                and min(ys) - reach < y_range[1] and max(ys) + reach > y_range[0])

    for item in plan.ALL_PYRAMIDS:
        if not near([(item["x"], item["y"])], item["half_x"] + 30.0):
            continue
        d = np.maximum(np.abs(gx - item["x"]) - item["half_x"], np.abs(gy - item["y"]) - item["half_y"])
        apron = smoothstep((20.0 - d) / 16.0) * (d > -1.0)
        debris = np.dstack([0.94 + 0.04 * grain, 0.88 + 0.04 * grain, 0.76 + 0.04 * grain])
        desert = mix(desert, debris, apron * (0.55 + 0.4 * speck))
        drift = smoothstep((6.0 - np.abs(d - 1.5)) / 6.0) * smoothstep((fine - 0.35) / 0.3)
        desert = mix(desert, np.array([0.93, 0.76, 0.50]), drift * 0.7)
    tracks = [points for points in plan.TRACKS if near(points, 10.0)]
    for points in tracks:
        d, _ = plan.polyline_distance(points, gx, gy)
        track = smoothstep((3.2 - d) / 1.6)
        desert = mix(desert, np.array([0.80, 0.66, 0.46]) * (0.92 + 0.12 * grain)[..., None], track * 0.65)
        desert = mix(desert, np.array([0.70, 0.56, 0.38]), smoothstep((0.9 - np.abs(d - 1.4)) / 0.5) * 0.25)
    pit = plan.PIT
    d_pit = plan.box_distance(gx, gy, pit["x0"], pit["x1"], pit["y0"], pit["y1"])
    floor = np.dstack([0.86 + 0.05 * grain, 0.76 + 0.05 * grain, 0.58 + 0.04 * grain])
    desert = mix(desert, floor, smoothstep((2.0 - d_pit) / 4.0))
    fields = field_colours(gx, gy, fine)
    mud = np.dstack([0.34 + 0.05 * fine, 0.27 + 0.04 * fine, 0.20 + 0.03 * fine])
    fields = mix(fields, mud, smoothstep((noise - 0.72) / 0.1) * 0.6)
    groves = smoothstep((world_noise(gx, gy, 140.0, 21, 3) - 0.62) / 0.08)
    fields = mix(fields, np.array([0.20, 0.32, 0.12]), groves * 0.7)
    kom = np.dstack([0.58 + 0.05 * fine, 0.46 + 0.04 * fine, 0.32 + 0.03 * fine])
    fields = mix(fields, kom, smoothstep((village - 0.25) / 0.4) * (0.55 + 0.35 * fine))
    for points in tracks:
        d, _ = plan.polyline_distance(points, gx, gy)
        fields = mix(fields, np.array([0.62, 0.52, 0.38]), smoothstep((2.6 - d) / 1.2) * 0.85)
    bank = smoothstep((4.0 - canal) / 4.0) * (canal > -0.5)
    fields = mix(fields, np.array([0.30, 0.42, 0.18]), bank * 0.9)
    wet = smoothstep((0.5 - canal) / 1.5)
    fields = mix(fields, np.array([0.20, 0.18, 0.14]) if step < 3.0 else np.array([0.26, 0.38, 0.36]), wet)
    margin = smoothstep(1.0 - np.abs(flood - 0.5) / 0.5)
    fields = mix(fields, np.array([0.70, 0.58, 0.40]), margin * 0.6)
    colour = mix(desert, fields, smoothstep((flood - 0.35) / 0.3))
    silt = np.dstack([0.24 + 0.04 * fine, 0.20 + 0.03 * fine, 0.14 + 0.02 * fine])
    colour = mix(colour, silt, smoothstep((plan.LEVELS["water"] + 0.15 - heights) / 0.5))
    reeds = smoothstep((plan.NILE_HALF + 45.0 - nile) / 30.0) * (nile > plan.NILE_HALF - 15.0)
    colour = mix(colour, np.array([0.34, 0.46, 0.20]) * (0.85 + 0.3 * fine)[..., None], reeds)
    river = smoothstep((plan.NILE_HALF - nile) / 20.0)
    colour = mix(colour, np.array([0.18, 0.16, 0.13]), river)
    if footprints is not None:
        colour *= (1.0 - 0.32 * footprints)[..., None]
    colour *= (0.95 + 0.08 * noise)[..., None]
    return np.clip(colour, 0.0, 1.0)


def bake_tile(terrain, x0, y0, size, resolution, footprints=None):
    step = size / resolution
    axis_x = x0 + (np.arange(resolution) + 0.5) * step
    axis_y = y0 + (np.arange(resolution) + 0.5) * step
    gx, gy = np.meshgrid(axis_x, axis_y)
    mask = footprints(gx, gy) if footprints is not None else None
    return land_colour(terrain, gx, gy, step, mask)


def submerged(heights, level, reach=2):
    wet = heights < level
    padded = np.pad(wet, reach, constant_values=False)
    count = wet.shape[0]
    result = np.ones_like(wet)
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            result &= padded[reach + dy:reach + dy + count, reach + dx:reach + dx + wet.shape[1]]
    return result


def grid_tile(name, terrain, x0, y0, size, spacing, hole=None, drown=None):
    count = int(round(size / spacing)) + 1
    xs = x0 + np.arange(count) * spacing
    ys = y0 + np.arange(count) * spacing
    gx, gy = np.meshgrid(xs, ys)
    heights = terrain.height(gx, gy)
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(count * count).reshape(count, count)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(),
                             index[1:, :-1].ravel()])
    if drown is not None:
        hidden = submerged(heights, drown).ravel()
        quads = quads[~hidden[quads].all(axis=1)]
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


def water_mesh(name, terrain, region, cell, level, colour, hole=None):
    probe = (np.arange(9) + 0.5) / 9.0
    x0, y0, x1, y1 = region
    xs = np.arange(x0, x1, cell)
    ys = np.arange(y0, y1, cell)
    qx, qy = np.meshgrid(xs, ys)
    qx, qy = qx.ravel(), qy.ravel()
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        outside = (qx + cell <= hx0 + 0.01) | (qx >= hx1 - 0.01) | (qy + cell <= hy0 + 0.01) | (qy >= hy1 - 0.01)
        qx, qy = qx[outside], qy[outside]
    px, py = np.meshgrid(probe, probe)
    sx = qx[:, None] + np.concatenate([[0.0, 1.0, 1.0, 0.0], px.ravel()])[None, :] * cell
    sy = qy[:, None] + np.concatenate([[0.0, 0.0, 1.0, 1.0], py.ravel()])[None, :] * cell
    bed = terrain.height(sx, sy)
    keep = bed.min(axis=1) < level - 0.02
    cx, cy = sx[keep][:, :4], sy[keep][:, :4]
    count = len(cx)
    vertices = np.column_stack([cx.ravel(), cy.ravel(), np.full(count * 4, level)])
    faces = np.arange(count * 4).reshape(count, 4)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", (vertices[:, :2] / 50.0).astype(np.float32).ravel())
    depth = np.clip(level - terrain.height(vertices[:, 0], vertices[:, 1]), 0.0, 8.0)
    river, _ = plan.polyline_distance(plan.NILE, vertices[:, 0], vertices[:, 1])
    channel = smoothstep((plan.NILE_HALF + 250.0 - river) / 500.0)
    shade = np.maximum(np.clip(depth / 5.0, 0.0, 1.0), channel)[:, None]
    rgb = np.asarray(colour[0]) * (1 - shade) + np.asarray(colour[1]) * shade
    attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attribute.data.foreach_set("color_srgb", np.column_stack([rgb, np.ones(count * 4)]).astype(np.float32).ravel())
    mesh.color_attributes.active_color = attribute
    mesh.update()
    return mesh

import math
import os

import bpy
import numpy as np

from .constantinople_terrain import blur, chamfer, minimum_filter, shifted, smoothstep
from .materials import download
from .pompei_terrain import world_noise
from .terrain import GeoFrame, HeightField, polygon_mask, polyline_distance

DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{0}_DEM/Copernicus_DSM_COG_10_{0}_DEM.tif"
DEM_TILES = ("N36_00_E028_00", "N36_00_E027_00")
DEM_LICENCE = ("Copernicus DEM GLO-30 (ESA, Copernicus programme), free licence with attribution: produced using "
               "Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 "
               "provided under COPERNICUS by the European Union and ESA")
SOURCE = {"name": "Copernicus DEM GLO-30, tiles N36 E028 and N36 E027",
          "url": DEM_URL.format(DEM_TILES[0]), "licence": DEM_LICENCE,
          "processing": ("minimum filter and blur to remove the modern town and trees, ancient harbour basins and "
                         "moles redrawn by hand, sanctuary, stadium and odeon terraces levelled")}
STEP = 1.0 / 3600.0
CROP = (36.99, 27.70, 3100, 3300)
ORIGIN = (36.4458, 28.2236)
FRAME = GeoFrame(*ORIGIN)
NEAR_HALF = 3400.0
NEAR_SPACING = 5.0
FAR_HALF = 34000.0
FAR_SPACING = 100.0


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
    cached = os.path.join(cache_dir, "src", "dem", "rhodes_crop_v2.npy")
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


def connected_sea(raw, seeds, level=0.8):
    sea = raw <= level
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


def grid(half, spacing):
    count = int(round(2 * half / spacing)) + 1
    axis = np.linspace(-half, half, count)
    return np.meshgrid(axis, axis)


def box_weight(gx, gy, cx, cy, hx, hy, margin):
    outside = np.maximum(np.abs(gx - cx) - hx, np.abs(gy - cy) - hy)
    return smoothstep(1.0 - outside / margin)


def disc_weight(gx, gy, cx, cy, radius, margin):
    return smoothstep(1.0 - (np.hypot(gx - cx, gy - cy) - radius) / margin)


def flatten(ground, weight, level):
    return ground * (1 - weight) + level * weight


def condition(dem, plan, half, spacing):
    sample = dem_sampler(dem)
    gx, gy = grid(half, spacing)
    count = gx.shape[0]
    raw = sample(gx, gy)
    passes = max(1, int(round(35.0 / spacing)))
    ground = blur(minimum_filter(raw, passes), passes + 3)
    seeds = [(count - 1, count - 1), (count - 1, count // 2), (count // 2, count - 1), (count - 1, 0)]
    modern_sea = connected_sea(raw, seeds)
    fill = np.zeros(gx.shape, dtype=bool)
    for polygon in list(plan.HARBOURS.values()) + plan.SEA_FILLS:
        fill |= polygon_mask(polygon, gx, gy)
    carve = np.zeros(gx.shape, dtype=bool)
    for polygon in plan.MOLE_CUTS:
        carve |= polygon_mask(polygon, gx, gy)
    ancient_sea = (modern_sea | fill) & ~carve
    shore = blur(np.where(ancient_sea, -1.0, 1.0), 2)
    ancient_sea = shore < 0.0
    to_land = np.minimum(chamfer(~ancient_sea, spacing, int(600.0 / spacing) + 2), 600.0)
    to_sea = np.minimum(chamfer(ancient_sea, spacing, int(300.0 / spacing) + 2), 300.0)
    ground = plan.shape_ground(gx, gy, ground)
    harbour = np.full(gx.shape, np.inf)
    for polygon in plan.HARBOURS.values():
        harbour = np.minimum(harbour, polyline_distance(list(polygon) + [polygon[0]], gx, gy))
    quay_zone = smoothstep(1.0 - (harbour - 30.0) / 30.0)
    coastal = np.minimum(np.maximum(ground, 0.0), 0.9 + to_sea * 0.16)
    land = np.where(to_sea < 60.0, np.maximum(coastal, ground * smoothstep(to_sea / 60.0)), ground)
    land = np.maximum(land, 0.7 + to_sea * 0.02)
    quay_level = plan.QUAY_TOP - 0.06 + np.maximum(to_sea - 30.0, 0.0) * 0.05
    land = land * (1 - quay_zone) + np.minimum(land, quay_level) * quay_zone
    bed = -1.2 - 0.09 * to_land - 0.0004 * to_land * to_land
    harbour_bed = np.minimum(bed, -3.0 - 0.02 * to_land)
    inside_harbour = fill & ~carve
    bed = np.where(inside_harbour, np.maximum(harbour_bed, -9.0), bed)
    heights = np.where(ancient_sea, np.maximum(bed, -70.0), land)
    heights = blur(heights, 1)
    heights = plan.shape_after(gx, gy, heights)
    signed = np.where(ancient_sea, -to_land, to_sea)
    return HeightField(heights, half), HeightField(signed, half), raw


def far_field(dem, half, spacing):
    sample = dem_sampler(dem)
    gx, gy = grid(half, spacing)
    raw = sample(gx, gy)
    latitude, longitude = FRAME.to_geo(gx, gy)
    north, west, rows, columns = CROP
    inside = ((latitude < north - 0.003) & (latitude > north - rows * STEP + 0.003) & (longitude > west + 0.003)
              & (longitude < west + columns * STEP - 0.003))
    ground = blur(minimum_filter(raw, 1), 2)
    sea = (raw <= 0.8) | ~inside
    to_land = chamfer(~sea, spacing, 40)
    heights = np.where(sea, np.maximum(-3.0 - to_land * 0.06, -80.0), np.maximum(ground, 0.8))
    signed = np.where(sea, -np.minimum(to_land, 4000.0), np.minimum(chamfer(sea, spacing, 30), 3000.0))
    return HeightField(heights, half), HeightField(signed, half)


class Terrain:
    def __init__(self, cache_dir, plan):
        dem = load_dem(cache_dir)
        self.plan = plan
        self.near, self.shore, self.raw = condition(dem, plan, NEAR_HALF, NEAR_SPACING)
        self.far, self.far_shore = far_field(dem, FAR_HALF, FAR_SPACING)
        reach = np.maximum(np.abs(self.far.grid_x), np.abs(self.far.grid_y))
        weight = smoothstep((NEAR_HALF - 300.0 - reach) / 600.0)
        self.far.heights = self.far.heights * (1 - weight) + self.near.sample(self.far.grid_x,
                                                                            self.far.grid_y) * weight
        self.slope_field = HeightField(self.near.slope(), NEAR_HALF)
        self.bound = NEAR_HALF - 20.0

    def inside(self, x, y):
        return (np.abs(x) < self.bound) & (np.abs(y) < self.bound)

    def blend(self, near, far, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        if np.ndim(x) == 0:
            return near.sample(x, y) if self.inside(x, y) else far.sample(x, y)
        inside = self.inside(x, y)
        result = far.sample(x, y)
        if inside.any():
            result = np.where(inside, near.sample(x, y), result)
        return result

    def height(self, x, y):
        return self.blend(self.near, self.far, x, y)

    def sample(self, name, x, y):
        if name == "shore":
            return self.blend(self.shore, self.far_shore, x, y)
        if name == "slope":
            return self.slope_field.sample(x, y)
        return self.height(x, y)

    def lowest(self, x, y, radius):
        points = [(x, y)] + [(x + radius * math.cos(a), y + radius * math.sin(a)) for a in np.linspace(0, 6.28, 9)]
        return min(float(self.height(px, py)) for px, py in points)

    def highest(self, x, y, radius):
        points = [(x, y)] + [(x + radius * math.cos(a), y + radius * math.sin(a)) for a in np.linspace(0, 6.28, 9)]
        return max(float(self.height(px, py)) for px, py in points)


def mix(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + other * weight


def flat(shape, rgb):
    return np.broadcast_to(np.array(rgb, dtype=np.float64), shape + (3,)).copy()


def land_colour(gx, gy, terrain, footprints=None):
    plan = terrain.plan
    shape = gx.shape
    heights = terrain.height(gx, gy)
    shore = terrain.sample("shore", gx, gy)
    slope = terrain.sample("slope", gx, gy)
    broad = world_noise(gx, gy, 260.0, 3, 4)
    mid = world_noise(gx, gy, 45.0, 4, 3)
    fine = world_noise(gx, gy, 7.0, 5, 2)
    soil = np.dstack([0.78 + 0.08 * fine, 0.58 + 0.07 * fine, 0.38 + 0.05 * fine])
    soil = mix(soil, np.array([0.70, 0.40, 0.24]), smoothstep((broad - 0.55) / 0.2) * 0.55)
    scrub = np.dstack([0.40 + 0.08 * fine, 0.44 + 0.08 * fine, 0.20 + 0.05 * fine])
    scrub = mix(scrub, np.array([0.55, 0.55, 0.30]), smoothstep((broad - 0.5) / 0.2) * 0.6)
    dark_scrub = np.dstack([0.24 + 0.05 * fine, 0.31 + 0.06 * fine, 0.15 + 0.04 * fine])
    scrub = mix(scrub, dark_scrub, smoothstep((mid - 0.55) / 0.15))
    cover = smoothstep((mid * 0.6 + broad * 0.6 - 0.48) / 0.18)
    colour = mix(soil, scrub, cover * 0.85)
    rock = np.dstack([0.50 + 0.06 * fine, 0.44 + 0.05 * fine, 0.34 + 0.05 * fine])
    rock = mix(rock, np.array([0.38, 0.34, 0.28]), smoothstep((mid - 0.5) / 0.15) * 0.8)
    rock = mix(rock, np.array([0.30, 0.36, 0.20]), smoothstep((fine - 0.5) / 0.08) * 0.85)
    colour = mix(colour, rock, smoothstep((slope - 0.45) / 0.35))
    u = gx * math.cos(0.18) - gy * math.sin(0.18)
    v = gx * math.sin(0.18) + gy * math.cos(0.18)
    parcel = ((np.floor(u / 120.0).astype(np.int64) * 73856093) ^ (np.floor(v / 80.0).astype(np.int64) * 19349663))
    parcel = parcel % 1000 / 1000.0
    crops = np.array([[0.58, 0.60, 0.26], [0.80, 0.66, 0.36], [0.42, 0.54, 0.20], [0.72, 0.56, 0.30],
                      [0.50, 0.58, 0.24], [0.84, 0.72, 0.44]])
    fields = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.86 + 0.24 * fine)[..., None]
    rows = np.abs(((u / 6.0) % 1.0) - 0.5) < 0.18
    olive = (parcel > 0.55) & rows
    fields = np.where(olive[..., None], fields * 0.72, fields)
    farmland = (slope < 0.25) & (heights > 3.0)
    outside = ~plan.city_mask(gx, gy)
    colour = np.where((farmland & outside)[..., None], mix(colour, fields, 0.75), colour)
    city = plan.built_mask(gx, gy)
    city_ground = np.dstack([0.80 + 0.06 * fine, 0.68 + 0.06 * fine, 0.52 + 0.05 * fine])
    city_ground = mix(city_ground, np.array([0.62, 0.52, 0.40]), smoothstep((mid - 0.6) / 0.15) * 0.4)
    streets = plan.street_mask(gx, gy)
    street_colour = np.dstack([0.92 + 0.05 * fine, 0.86 + 0.05 * fine, 0.72 + 0.05 * fine])
    city_ground = np.where(streets[..., None], street_colour, city_ground)
    colour = np.where(city[..., None], mix(colour, city_ground, 0.92), colour)
    paved = plan.paved_mask(gx, gy)
    paving = np.dstack([0.94 + 0.04 * fine, 0.90 + 0.04 * fine, 0.80 + 0.04 * fine])
    colour = mix(colour, paving, paved)
    track = plan.track_mask(gx, gy)
    colour = mix(colour, np.dstack([0.90 + 0.04 * fine, 0.74 + 0.04 * fine, 0.52 + 0.04 * fine]), track)
    beach = smoothstep(1.0 - shore / 22.0) * (shore > -1.0)
    sand = np.dstack([0.93 + 0.04 * fine, 0.84 + 0.04 * fine, 0.64 + 0.04 * fine])
    pebbles = mix(sand, sand * 0.78, smoothstep((fine - 0.6) / 0.1))
    colour = mix(colour, pebbles, beach * (1.0 - plan.harbour_weight(gx, gy)))
    quay = plan.harbour_weight(gx, gy) * (shore > -1.0) * smoothstep(1.0 - (shore - 26.0) / 8.0)
    colour = mix(colour, np.dstack([0.84 + 0.04 * fine, 0.79 + 0.04 * fine, 0.68 + 0.04 * fine]), quay)
    depth = np.clip(-shore, 0.0, 600.0)
    bed_shallow = np.dstack([0.66 + 0.06 * fine, 0.70 + 0.05 * fine, 0.58 + 0.05 * fine])
    bed_mid = np.array([0.20, 0.42, 0.42])
    bed_deep = np.array([0.05, 0.14, 0.22])
    bed = mix(bed_shallow, bed_mid, smoothstep(depth / 60.0))
    bed = mix(bed, bed_deep, smoothstep((depth - 60.0) / 300.0))
    weed = smoothstep((mid - 0.55) / 0.12) * smoothstep((depth - 6.0) / 20.0) * 0.6
    bed = mix(bed, np.array([0.16, 0.26, 0.14]), weed)
    colour = np.where((shore < -1.0)[..., None], bed, colour)
    if footprints is not None:
        colour *= (1.0 - 0.35 * footprints)[..., None]
    colour *= (0.93 + 0.12 * broad)[..., None]
    return np.clip(colour, 0.0, 1.0)


def grid_tile(name, terrain, x0, y0, size, spacing, hole=None, cull_depth=-30.0):
    count = int(round(size / spacing)) + 1
    xs = x0 + np.arange(count) * spacing
    ys = y0 + np.arange(count) * spacing
    gx, gy = np.meshgrid(xs, ys)
    heights = terrain.height(gx, gy)
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(count * count).reshape(count, count)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(),
                             index[1:, :-1].ravel()])
    keep = heights.ravel()[quads].max(axis=1) > cull_depth
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        cx = vertices[quads, 0]
        cy = vertices[quads, 1]
        inside = ((cx >= hx0 - 0.01) & (cx <= hx1 + 0.01) & (cy >= hy0 - 0.01) & (cy <= hy1 + 0.01)).all(axis=1)
        keep &= ~inside
    quads = quads[keep]
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


def bake_tile(terrain, x0, y0, size, resolution, footprints=None):
    axis_x = x0 + (np.arange(resolution) + 0.5) * size / resolution
    axis_y = y0 + (np.arange(resolution) + 0.5) * size / resolution
    gx, gy = np.meshgrid(axis_x, axis_y)
    mask = footprints(gx, gy) if footprints is not None else None
    return land_colour(gx, gy, terrain, mask)


def water_colour(shore, noise):
    depth = np.clip(-shore, 0.0, 6000.0)
    shallow = np.array([0.10, 0.66, 0.68])
    lagoon = np.array([0.05, 0.50, 0.62])
    open_sea = np.array([0.03, 0.32, 0.60])
    deep = np.array([0.02, 0.20, 0.48])
    colour = mix(flat(shore.shape, shallow), lagoon, smoothstep(depth / 40.0))
    colour = mix(colour, open_sea, smoothstep((depth - 40.0) / 300.0))
    colour = mix(colour, deep, smoothstep((depth - 400.0) / 3000.0))
    colour *= (0.94 + 0.12 * noise)[..., None]
    surf = smoothstep(1.0 - depth / 3.0) * 0.35
    return mix(colour, np.array([0.45, 0.78, 0.80]), surf)


def water_mesh(name, terrain, region, cell, fine, hole=None, refine=True):
    x0, y0, x1, y1 = region
    xs = np.arange(x0, x1, cell)
    ys = np.arange(y0, y1, cell)
    qx, qy = [a.ravel() for a in np.meshgrid(xs, ys)]
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        outside = (qx + cell <= hx0 + 0.01) | (qx >= hx1 - 0.01) | (qy + cell <= hy0 + 0.01) | (qy >= hy1 - 0.01)
        qx, qy = qx[outside], qy[outside]
    centre_shore = terrain.sample("shore", qx + cell / 2, qy + cell / 2)
    keep = centre_shore < cell * 0.75 + 20.0
    qx, qy, centre_shore = qx[keep], qy[keep], centre_shore[keep]
    corners = []
    sizes = []
    if refine:
        split = np.abs(centre_shore) < cell * 0.75 + 60.0
        steps = int(round(cell / fine))
        for i in range(steps):
            for j in range(steps):
                corners.append(np.column_stack([qx[split] + i * fine, qy[split] + j * fine]))
                sizes.append(np.full(split.sum(), fine))
        corners.append(np.column_stack([qx[~split], qy[~split]]))
        sizes.append(np.full((~split).sum(), cell))
    else:
        corners.append(np.column_stack([qx, qy]))
        sizes.append(np.full(len(qx), cell))
    origin = np.vstack(corners)
    size = np.concatenate(sizes)
    cx = np.column_stack([origin[:, 0], origin[:, 0] + size, origin[:, 0] + size, origin[:, 0]])
    cy = np.column_stack([origin[:, 1], origin[:, 1], origin[:, 1] + size, origin[:, 1] + size])
    corner_height = terrain.height(cx, cy)
    keep = corner_height.min(axis=1) < 0.25
    cx, cy = cx[keep], cy[keep]
    corner_shore = terrain.sample("shore", cx, cy)
    noise = world_noise(cx, cy, 90.0, 31, 3)
    colour = water_colour(corner_shore, noise)
    count = len(cx)
    vertices = np.column_stack([cx.ravel(), cy.ravel(), np.zeros(count * 4)])
    faces = np.arange(count * 4).reshape(count, 4)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", (vertices[:, :2] / 50.0).astype(np.float32).ravel())
    attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    rgba = np.column_stack([colour.reshape(-1, 3), np.ones(count * 4)])
    attribute.data.foreach_set("color_srgb", rgba.astype(np.float32).ravel())
    mesh.color_attributes.active_color = attribute
    mesh.update()
    return mesh

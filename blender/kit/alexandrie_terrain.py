import math

import bpy
import numpy as np

from . import alexandrie_plan as plan
from .pompei_terrain import Field, smoothstep, world_noise
from .terrain import polygon_mask

NEAR_FIELD = dict(x0=-6000.0, y0=-6000.0, width=12000.0, height=10000.0, spacing=10.0)
SOURCE = ("Relief restitue a la main d'apres la cote antique publiee (Goiran et al. 2009, Goddio et al. 1998, "
          "plan de Mahmoud Bey el-Falaki 1872), redessine et non copie ; le DSM Copernicus GLO-30 n'est pas utilise "
          "car il mesure la ville moderne et ses immeubles, et non le sol antique")


def segments(polylines, closed):
    starts = []
    ends = []
    for points, close in zip(polylines, closed):
        array = np.asarray(points, dtype=np.float64)
        if close:
            array = np.vstack([array, array[:1]])
        starts.append(array[:-1])
        ends.append(array[1:])
    return np.vstack(starts), np.vstack(ends)


def segment_distance(gx, gy, starts, ends, reach=None):
    distance = np.full(gx.shape, np.inf)
    lo_x, hi_x = gx.min(), gx.max()
    lo_y, hi_y = gy.min(), gy.max()
    for (x0, y0), (x1, y1) in zip(starts, ends):
        if reach is not None:
            if max(x0, x1) < lo_x - reach or min(x0, x1) > hi_x + reach:
                continue
            if max(y0, y1) < lo_y - reach or min(y0, y1) > hi_y + reach:
                continue
        dx, dy = x1 - x0, y1 - y0
        length_squared = max(dx * dx + dy * dy, 1e-9)
        t = np.clip(((gx - x0) * dx + (gy - y0) * dy) / length_squared, 0.0, 1.0)
        np.minimum(distance, np.hypot(gx - (x0 + t * dx), gy - (y0 + t * dy)), out=distance)
    if reach is not None:
        distance = np.minimum(distance, reach)
    return distance


def land_mask(gx, gy):
    land = np.zeros(gx.shape, dtype=bool)
    for polygon in plan.land_polygons():
        land |= polygon_mask(polygon, gx, gy)
    for polygon in plan.water_cuts():
        land &= ~polygon_mask(polygon, gx, gy)
    return land


def signed_distance(gx, gy, reach):
    polygons = plan.land_polygons() + plan.water_cuts()
    starts, ends = segments(polygons, [True] * len(polygons))
    distance = segment_distance(gx, gy, starts, ends, reach)
    return np.where(land_mask(gx, gy), distance, -distance)


class Geography:
    def __init__(self, spec, reach):
        self.spec = spec
        columns = int(round(spec["width"] / spec["spacing"])) + 1
        rows = int(round(spec["height"] / spec["spacing"])) + 1
        xs = spec["x0"] + np.arange(columns) * spec["spacing"]
        ys = spec["y0"] + np.arange(rows) * spec["spacing"]
        gx, gy = np.meshgrid(xs, ys)
        self.fields = {}
        shore = signed_distance(gx, gy, reach)
        self.add("shore", shore)
        quay_starts, quay_ends = segments(plan.quay_lines(), [False] * len(plan.quay_lines()))
        self.add("quay", segment_distance(gx, gy, quay_starts, quay_ends, 200.0))
        reef_starts, reef_ends = segments(plan.REEFS, [False] * len(plan.REEFS))
        self.add("reef", segment_distance(gx, gy, reef_starts, reef_ends, 400.0))
        self.add("height", compose_heights(gx, gy, shore, self.fields["quay"].heights))

    def add(self, name, values):
        self.fields[name] = Field(self.spec["x0"], self.spec["y0"], self.spec["spacing"], values)

    def sample(self, name, x, y):
        return self.fields[name].sample(x, y)


def hills(gx, gy):
    t = (gx - plan.C0.x) * plan.D.x + (gy - plan.C0.y) * plan.D.y
    n = (gx - plan.C0.x) * plan.N.x + (gy - plan.C0.y) * plan.N.y
    serapeum = plan.SITES["serapeum"]
    rise = 11.0 * np.exp(-((t - serapeum["t"]) ** 2 + (n - serapeum["n"]) ** 2) / (2 * 170.0 ** 2))
    ridge = 2.2 * np.exp(-((n - 150.0) / 700.0) ** 2) * smoothstep((t + 3600.0) / 800.0) * smoothstep(
        (3600.0 - t) / 800.0)
    royal = 1.5 * smoothstep((t - 200.0) / 300.0) * smoothstep((n - 200.0) / 200.0) * smoothstep((2400.0 - t) / 300.0)
    south = n - plan.lake_n(0.0) + 5200.0
    dunes = np.where(south < 0, 6.0 * smoothstep(-south / 2500.0) * (0.5 + 0.5 * np.sin(t / 900.0 + n / 1300.0)),
                     0.0)
    return rise + ridge + royal + dunes


def compose_heights(gx, gy, shore, quay):
    noise = world_noise(gx, gy, 600.0, 7, 4) - 0.5
    land = 1.5 + 2.4 * smoothstep(shore / 400.0) + 1.4 * noise + hills(gx, gy)
    land = np.maximum(land, 0.9)
    sea = np.maximum(0.5 + shore * 0.1, -18.0 + 4.0 * noise)
    rising = 0.5 + (land - 0.5) * smoothstep(shore / 50.0)
    heights = np.where(shore < 0, sea, rising)
    weight = np.where(shore >= 0, smoothstep(1.0 - (quay - 40.0) / 18.0), smoothstep(1.0 - (quay - 4.0) / 14.0))
    quay_level = np.where(shore >= 0, plan.QUAY_TOP - 0.04, -4.5)
    heights = heights * (1 - weight) + quay_level * weight
    return heights


def mix(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + other * weight


def street_mask(t, n, width_main=30.0, width=9.0):
    near_t = np.abs(((t + plan.BLOCK_T / 2) % plan.BLOCK_T) - plan.BLOCK_T / 2)
    near_n = np.abs(((n + plan.BLOCK_N / 2) % plan.BLOCK_N) - plan.BLOCK_N / 2)
    main = (np.abs(t) < width_main / 2) | (np.abs(n) < width_main / 2)
    return (near_t < width / 2) | (near_n < width / 2) | main


def land_colour(gx, gy, geography, footprints=None):
    shore = geography.sample("shore", gx, gy)
    heights = geography.sample("height", gx, gy)
    quay = geography.sample("quay", gx, gy)
    noise = world_noise(gx, gy, 300.0, 3, 4)
    fine = world_noise(gx, gy, 30.0, 4, 3)
    grain = world_noise(gx, gy, 5.0, 5, 2)
    t = (gx - plan.C0.x) * plan.D.x + (gy - plan.C0.y) * plan.D.y
    n = (gx - plan.C0.x) * plan.N.x + (gy - plan.C0.y) * plan.N.y
    lake_gap = n - lake_profile(t)
    angle = math.radians(23.0)
    u = gx * math.cos(angle) - gy * math.sin(angle)
    v = gx * math.sin(angle) + gy * math.cos(angle)
    parcel_u = np.floor(u / 140.0).astype(np.int64)
    parcel_v = np.floor(v / 90.0).astype(np.int64)
    parcel = ((parcel_u * 73856093) ^ (parcel_v * 19349663)) % 1000 / 1000.0
    crops = np.array([[0.56, 0.62, 0.24], [0.74, 0.64, 0.33], [0.40, 0.54, 0.20], [0.66, 0.60, 0.30],
                      [0.48, 0.58, 0.22], [0.80, 0.70, 0.40], [0.34, 0.47, 0.18]])
    fields = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.86 + 0.24 * fine)[..., None]
    ditch = (np.abs((u / 140.0) % 1.0 - 0.5) > 0.49) | (np.abs((v / 90.0) % 1.0 - 0.5) > 0.485)
    fields = np.where(ditch[..., None], np.array([0.26, 0.40, 0.16]), fields)
    sand = np.dstack([0.90 + 0.05 * grain, 0.78 + 0.05 * grain, 0.56 + 0.04 * grain])
    dust = np.dstack([0.80 + 0.06 * fine, 0.70 + 0.05 * fine, 0.54 + 0.04 * fine])
    colour = mix(fields, dust, smoothstep((0.45 - noise) / 0.12) * 0.6)
    city = ((t > plan.CITY_T[0] - 60.0) & (t < plan.CITY_T[1] + 60.0) & (n < plan.CITY_N[1])
            & (lake_gap > 120.0))
    city_ground = np.dstack([0.84 + 0.05 * fine, 0.75 + 0.05 * fine, 0.60 + 0.05 * fine])
    city_ground = mix(city_ground, np.array([0.70, 0.62, 0.50]), smoothstep((grain - 0.55) / 0.2) * 0.4)
    streets = street_mask(t, n)
    city_ground = np.where(streets[..., None], np.array([0.92, 0.86, 0.74]) * (0.95 + 0.08 * grain)[..., None],
                           city_ground)
    royal = (t > plan.ROYAL_T[0]) & (t < plan.ROYAL_T[1]) & (n > plan.ROYAL_N)
    gardens = np.dstack([0.30 + 0.08 * fine, 0.46 + 0.08 * fine, 0.18 + 0.05 * fine])
    groves = np.dstack([0.30 + 0.05 * fine, 0.38 + 0.05 * fine, 0.16 + 0.04 * fine])
    earth = np.dstack([0.78 + 0.05 * fine, 0.68 + 0.05 * fine, 0.50 + 0.04 * fine])
    patches = world_noise(gx, gy, 110.0, 12, 3)
    lawn = mix(earth, groves, smoothstep((patches - 0.52) / 0.12) * 0.7)
    city_ground = np.where(royal[..., None], lawn, city_ground)
    colour = np.where(city[..., None], city_ground, colour)
    necropolis = (t < plan.CITY_T[0]) & (t > plan.CITY_T[0] - 1600.0) & (lake_gap > 100.0)
    tombs = np.dstack([0.82 + 0.05 * fine, 0.76 + 0.05 * fine, 0.62 + 0.05 * fine])
    colour = np.where(necropolis[..., None], mix(tombs, gardens, smoothstep((fine - 0.6) / 0.1) * 0.6), colour)
    island = n > plan.CITY_N[1]
    scrub = np.dstack([0.80 + 0.06 * fine, 0.74 + 0.05 * fine, 0.58 + 0.05 * fine])
    scrub = mix(scrub, np.array([0.56, 0.58, 0.36]), smoothstep((noise - 0.45) / 0.25) * 0.45)
    colour = np.where((island & ~city)[..., None], scrub, colour)
    reed = np.dstack([0.42 + 0.06 * fine, 0.50 + 0.06 * fine, 0.24 + 0.04 * fine])
    lake_edge = smoothstep(1.0 - lake_gap / 90.0) * (shore > 0)
    colour = mix(colour, reed, lake_edge * smoothstep((fine - 0.3) / 0.2))
    beach = smoothstep(1.0 - shore / 45.0) * (shore > -30.0) * smoothstep((quay - 25.0) / 20.0) * (lake_gap > 60.0)
    rock = np.dstack([0.70 + 0.08 * grain, 0.66 + 0.07 * grain, 0.56 + 0.06 * grain])
    rock = mix(rock, rock * 0.62, smoothstep((fine - 0.62) / 0.08))
    rocky = (n > plan.CITY_N[1]) * smoothstep((world_noise(gx, gy, 140.0, 21, 3) - 0.36) / 0.22)
    sand = mix(sand, rock, rocky)
    colour = mix(colour, sand, beach)
    wet = smoothstep(1.0 - (shore + 6.0) / 8.0)
    colour = mix(colour, sand * np.array([0.72, 0.68, 0.62]), wet)
    stone = np.dstack([0.86 + 0.04 * grain, 0.82 + 0.04 * grain, 0.72 + 0.04 * grain])
    colour = mix(colour, stone, smoothstep(1.0 - (quay - 38.0) / 10.0) * (shore > -2.0))
    south = n - lake_profile(t) + 5200.0
    desert = np.dstack([0.88 + 0.05 * noise, 0.76 + 0.05 * noise, 0.54 + 0.05 * noise])
    colour = np.where((south < 300.0)[..., None], mix(colour, desert, smoothstep(-south / 600.0 + 0.5)), colour)
    if footprints is not None:
        colour *= (1.0 - 0.35 * footprints)[..., None]
    colour *= (0.94 + 0.1 * noise)[..., None]
    rise = np.clip((heights - 1.5) / 12.0, 0.0, 1.0)
    colour *= (1.0 + 0.05 * rise)[..., None]
    return np.clip(colour, 0.0, 1.0)


def lake_profile(t):
    return -1600.0 - 70.0 * np.sin(t / 900.0 + 0.6) - 0.00012 * np.maximum(t - 2600.0, 0.0) ** 2


def water_colour(shore, reef, lake, noise, quay):
    deep = np.array([0.06, 0.30, 0.52])
    open_sea = np.array([0.07, 0.36, 0.58])
    shallow = np.array([0.14, 0.58, 0.62])
    lagoon = np.array([0.44, 0.62, 0.62])
    depth = np.clip(-shore, 0.0, 4000.0)
    colour = mix(np.broadcast_to(shallow, shore.shape + (3,)).copy(), open_sea, smoothstep(depth / 260.0))
    colour = mix(colour, deep, smoothstep((depth - 600.0) / 2500.0))
    colour = np.where(lake[..., None], mix(lagoon, lagoon * 0.9, noise), colour)
    foam = smoothstep(1.0 - reef / 30.0) * smoothstep((noise - 0.38) / 0.22) * 0.95
    surf = smoothstep(1.0 - (-shore) / 14.0) * (shore < 6.0) * 0.55 * smoothstep((quay - 20.0) / 30.0)
    colour = mix(colour, np.array([0.92, 0.95, 0.95]), np.maximum(foam, surf * (~lake)))
    return colour


FAR_FIELD = dict(x0=-60000.0, y0=-60000.0, width=120000.0, height=120000.0, spacing=300.0)


class Terrain:
    def __init__(self):
        self.near = Geography(NEAR_FIELD, 4000.0)
        self.far = Geography(FAR_FIELD, 30000.0)
        spec = NEAR_FIELD
        margin = 2 * spec["spacing"]
        self.bounds = (spec["x0"] + margin, spec["y0"] + margin, spec["x0"] + spec["width"] - margin,
                       spec["y0"] + spec["height"] - margin)

    def sample(self, name, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        x0, y0, x1, y1 = self.bounds
        inside = (x > x0) & (x < x1) & (y > y0) & (y < y1)
        if np.ndim(x) == 0:
            return self.near.sample(name, x, y) if inside else self.far.sample(name, x, y)
        result = self.far.sample(name, x, y)
        if inside.any():
            result = np.where(inside, self.near.sample(name, x, y), result)
        return result

    def height(self, x, y):
        return self.sample("height", x, y)


def grid_tile(name, terrain, x0, y0, size, spacing, hole=None, cull_depth=-6.0):
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


def water_quads(x0, y0, x1, y1, cell):
    xs = np.arange(x0, x1, cell)
    ys = np.arange(y0, y1, cell)
    gx, gy = np.meshgrid(xs, ys)
    return gx.ravel(), gy.ravel()


def water_mesh(name, terrain, region, cell, fine, hole=None, refine=True):
    x0, y0, x1, y1 = region
    qx, qy = water_quads(x0, y0, x1, y1, cell)
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
        centre_reef = terrain.sample("reef", qx + cell / 2, qy + cell / 2)
        split = (np.abs(centre_shore) < cell * 0.75 + 70.0) | (centre_reef < cell * 0.75 + 60.0)
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
    corner_shore = terrain.sample("shore", cx, cy)
    keep = corner_shore.min(axis=1) < 6.0
    cx, cy, corner_shore = cx[keep], cy[keep], corner_shore[keep]
    reef = terrain.sample("reef", cx, cy)
    quay = terrain.sample("quay", cx, cy)
    t = (cx - plan.C0.x) * plan.D.x + (cy - plan.C0.y) * plan.D.y
    n = (cx - plan.C0.x) * plan.N.x + (cy - plan.C0.y) * plan.N.y
    lake = n < lake_profile(t) + 40.0
    noise = world_noise(cx, cy, 60.0, 31, 3)
    colour = water_colour(corner_shore, reef, lake, noise, quay)
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

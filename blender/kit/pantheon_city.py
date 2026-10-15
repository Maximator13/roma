import math
import os
import random

import numpy as np
from mathutils import Matrix, Vector

from .buildings import block_house, courtyard_house, gable_ends, trunk
from .geometry import MeshBuilder, placement
from .materials import baked_material, save_pixels
from .orders import gable_roof
from .pont_materials import periodic_noise
from .terrain import GeoFrame, grid_mesh, polyline_distance

ORIGIN = (41.89861, 12.47683)
BASE = -1.8
NEAR = 1000.0
HALF = 3200.0
SAMPLES = 129
FRAME = GeoFrame(*ORIGIN)

RIVER_GEO = [(41.9205, 12.4660), (41.9145, 12.4705), (41.9113, 12.4719), (41.9067, 12.4727), (41.9047, 12.4714),
             (41.9023, 12.4700), (41.9016, 12.4665), (41.8985, 12.4646), (41.8956, 12.4650), (41.8937, 12.4682),
             (41.8925, 12.4708), (41.8915, 12.4733), (41.8906, 12.4775), (41.8886, 12.4796), (41.8850, 12.4790),
             (41.8805, 12.4720), (41.8760, 12.4690)]
HILLS_GEO = [
    ("capitolium", 41.8933, 12.4828, 30.0, 150.0, 120.0),
    ("palatium", 41.8892, 12.4875, 32.0, 230.0, 190.0),
    ("quirinalis", 41.9000, 12.4880, 40.0, 330.0, 200.0),
    ("viminalis", 41.8985, 12.4985, 40.0, 260.0, 220.0),
    ("esquilinus", 41.8950, 12.5050, 42.0, 420.0, 330.0),
    ("pincius", 41.9115, 12.4810, 44.0, 380.0, 300.0),
    ("ianiculum", 41.8880, 12.4600, 72.0, 260.0, 720.0),
    ("vaticanus", 41.9040, 12.4500, 40.0, 450.0, 320.0),
    ("mons_marius", 41.9250, 12.4500, 125.0, 420.0, 700.0),
    ("aventinus", 41.8830, 12.4800, 34.0, 240.0, 220.0),
    ("caelius", 41.8865, 12.4960, 34.0, 300.0, 220.0),
]
SITES_GEO = {
    "mausoleum_augusti": (41.9061, 12.4763),
    "stadium": (41.8992, 12.4731),
    "theatrum_pompei": (41.8953, 12.4718),
    "saepta": (41.8975, 12.4785),
    "thermae_neronis": (41.8992, 12.4745),
    "stagnum": (41.8975, 12.4740),
    "capitolium_temple": (41.8929, 12.4823),
    "columna_traiani": (41.8958, 12.4843),
    "amphitheatrum": (41.8902, 12.4922),
    "templum_matidiae": (41.8996, 12.4785),
    "iseum": (41.8975, 12.4800),
    "area_sacra": (41.8955, 12.4768),
    "porticus_minucia": (41.8952, 12.4780),
    "theatrum_balbi": (41.8943, 12.4772),
    "circus_flaminius": (41.8930, 12.4775),
    "theatrum_marcelli": (41.8918, 12.4799),
}
SMOKE_HEIGHT = {"insula_court_a": 15.0, "insula_court_b": 18.0, "insula_block_a": 12.0, "insula_block_b": 16.0,
                "domus_low": 7.0}


def local(latitude, longitude):
    return FRAME.to_local(latitude, longitude)


RIVER = [local(*point) for point in RIVER_GEO]
HILLS = [(name, *local(lat, lon), height, sx, sy) for name, lat, lon, height, sx, sy in HILLS_GEO]
SITES = {name: local(*value) for name, value in SITES_GEO.items()}


def river_distance(x, y):
    return polyline_distance(RIVER, np.asarray(x, dtype=float), np.asarray(y, dtype=float))


def relief(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    height = np.full(x.shape, BASE)
    for _, hx, hy, rise, sx, sy in HILLS:
        height = height + rise * np.exp(-(((x - hx) / sx) ** 2 + ((y - hy) / sy) ** 2))
    distance = river_distance(x, y)
    bank = np.clip((distance - 42.0) / 40.0, 0.0, 1.0)
    bank = bank * bank * (3 - 2 * bank)
    return height * bank + (BASE - 7.5) * (1.0 - bank)


def terrain_colour(grid_x, grid_y, heights, seed=5):
    shape = grid_x.shape
    noise = periodic_noise(shape[0], 1.6, seed)
    fine = periodic_noise(shape[0], 0.8, seed + 1)
    distance = np.hypot(grid_x, grid_y)
    urban = np.clip(1.0 - (distance - 900.0) / 500.0, 0.0, 1.0)
    rise = np.clip((heights - BASE - 6.0) / 30.0, 0.0, 1.0)
    fields = np.dstack([0.56 + 0.12 * noise, 0.54 + 0.08 * noise, 0.34 + 0.04 * fine])
    green = np.dstack([0.30 + 0.06 * fine, 0.36 + 0.07 * noise, 0.20 + 0.03 * fine])
    city = np.dstack([0.52 + 0.05 * fine, 0.48 + 0.04 * fine, 0.42 + 0.04 * noise])
    parcel = ((np.floor(grid_x / 140.0) * 7 + np.floor(grid_y / 90.0) * 13) % 5) / 5.0
    fields = fields * (0.86 + 0.24 * parcel[..., None])
    colour = fields * (1 - rise[..., None]) + green * rise[..., None]
    city_mix = urban * (1.0 - 0.7 * rise)
    colour = colour * (1 - city_mix[..., None]) + city * city_mix[..., None]
    lanes = (np.abs(((grid_x + 17.0) % 34.0) - 17.0) > 14.5) | (np.abs(((grid_y + 17.0) % 34.0) - 17.0) > 14.5)
    colour = np.where((lanes & (urban > 0.5))[..., None], colour * 0.9, colour)
    water = river_distance(grid_x, grid_y)
    banks = np.clip(1.0 - (water - 45.0) / 35.0, 0.0, 1.0)
    colour = colour * (1 - banks[..., None]) + np.array([0.36, 0.38, 0.26]) * banks[..., None]
    colour *= (0.93 + 0.1 * noise)[..., None]
    return np.clip(colour, 0, 1)


GRID = {}


def terrain_grid():
    if "heights" not in GRID:
        axis = np.linspace(-HALF, HALF, SAMPLES)
        grid_x, grid_y = np.meshgrid(axis, axis)
        GRID["heights"] = relief(grid_x, grid_y)
    return GRID["heights"]


def ground(x, y):
    heights = terrain_grid()
    step = 2 * HALF / (SAMPLES - 1)
    u = min(max((x + HALF) / step, 0.0), SAMPLES - 1.001)
    v = min(max((y + HALF) / step, 0.0), SAMPLES - 1.001)
    i, j = int(u), int(v)
    fu, fv = u - i, v - j
    return float(heights[j, i] * (1 - fu) * (1 - fv) + heights[j, i + 1] * fu * (1 - fv)
                 + heights[j + 1, i] * (1 - fu) * fv + heights[j + 1, i + 1] * fu * fv)


def terrain(collection, parent, cache_dir, new_object):
    heights = terrain_grid()
    mesh = grid_mesh("terrain", heights, HALF, ring=(24000.0, 80.0))
    texture_axis = np.linspace(-HALF, HALF, 1024)
    tx, ty = np.meshgrid(texture_axis, texture_axis)
    colour = terrain_colour(tx, ty, relief(tx, ty))
    image = save_pixels("terrain_colour", colour, os.path.join(cache_dir, "textures", "terrain_colour.jpg"), quality=88)
    material = baked_material("terrain", image)
    mesh.materials.append(material)
    created = new_object("terrain", mesh, collection, parent)
    created["cast_shadow"] = False
    return created


def river():
    builder = MeshBuilder()
    points = [Vector((x, y, 0.0)) for x, y in RIVER]
    lefts, rights = [], []
    for index, point in enumerate(points):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        direction = (b - a).normalized()
        side = Vector((-direction.y, direction.x, 0.0))
        lefts.append(point + side * 64.0 + Vector((0.0, 0.0, BASE - 4.0)))
        rights.append(point - side * 64.0 + Vector((0.0, 0.0, BASE - 4.0)))
    builder.surface([lefts, rights], "water", facing=(0, 0, 1))
    return builder


def hall(builder, cx, cy, sx, sy, height, material, roof="terracotta_tiles", along="x", ground=BASE):
    builder.box((cx - sx / 2, cy - sy / 2, ground - 2.0), (cx + sx / 2, cy + sy / 2, height), material, bottom=False,
                top=False)
    roof_builder = MeshBuilder()
    if along == "x":
        rise = sy / 2 * 0.4
        gable_roof(roof_builder, -sx / 2 - 0.4, sx / 2 + 0.4, sy / 2 + 0.4, height, height + rise, roof, along_axis="x",
                   imbrex=False)
        gable_ends(roof_builder, -sx / 2, sx / 2, sy / 2, height, height + rise, material, along_axis="x")
    else:
        rise = sx / 2 * 0.4
        gable_roof(roof_builder, -sy / 2 - 0.4, sy / 2 + 0.4, sx / 2 + 0.4, height, height + rise, roof, along_axis="y",
                   imbrex=False)
        gable_ends(roof_builder, -sy / 2, sy / 2, sx / 2, height, height + rise, material, along_axis="y")
    builder.merge(roof_builder, placement(cx, cy, 0.0))


def neptune_and_agrippa():
    builder = MeshBuilder()
    hall(builder, 0.0, -36.5, 45.0, 19.0, 24.0, "brick")
    hall(builder, 0.0, -72.0, 60.0, 44.0, 27.0, "brick", along="y")
    for side in (-1, 1):
        hall(builder, side * 46.0, -88.0, 30.0, 80.0, 14.0, "brick", along="y")
    hall(builder, 0.0, -122.0, 64.0, 30.0, 18.0, "brick")
    hall(builder, 0.0, -150.0, 110.0, 24.0, 11.0, "plaster_ochre")
    return builder


def ring_lathe(builder, profile, material, segments, start=0.0, sweep=2 * math.pi, ellipse=None):
    scale = None
    if ellipse is not None:
        ratio = ellipse

        def scale(angle):
            return 1.0 / math.sqrt(math.cos(angle) ** 2 + (math.sin(angle) * ratio) ** 2)
    builder.lathe(profile, segments, material, smooth=True, start=start, sweep=sweep, caps=False, radius_scale=scale)


def stadium():
    builder = MeshBuilder()
    half_x, half_y = 53.0, 137.0
    north = half_y - half_x
    path = [(-half_x, -half_y), (half_x, -half_y), (half_x, north)]
    path += [(half_x * math.cos(math.pi * k / 10), north + half_x * math.sin(math.pi * k / 10)) for k in range(1, 10)]
    path += [(-half_x, north)]
    profile = [(-30.0, BASE - 1.0), (0.0, BASE - 1.0), (0.0, 17.0), (-5.0, 17.0), (-30.0, 3.0)]
    builder.sweep([(x, y, 0.0) for x, y in path], profile, "brick", closed=True)
    first = len(builder.polygons)
    builder.box((-23.0, -half_y + 30.0, BASE - 0.4), (23.0, north, BASE + 0.05), "matte", bottom=False)
    builder.tint(first, (0.72, 0.62, 0.46))
    return builder


def theatre():
    builder = MeshBuilder()
    ring_lathe(builder, [(80.0, BASE - 1.0), (80.0, 27.0), (24.0, 2.0)], "brick", 40, math.pi / 2, math.pi)
    for y in (-1, 1):
        builder.oriented([Vector((0.0, y * 80.0, BASE - 1.0)), Vector((0.0, y * 80.0, 27.0)), Vector((0.0, y * 24.0, 2.0)),
                          Vector((0.0, y * 24.0, BASE - 1.0))], (1, 0, 0), "brick")
    builder.box((4.0, -70.0, BASE - 1.0), (14.0, 70.0, 25.0), "plaster_cream")
    builder.merge(courtyard_house(175.0, 135.0, 155.0, 115.0, 10.0, "plaster_cream", court_material="garden_green"),
                  placement(102.0, 0.0, BASE))
    return builder


def mausoleum():
    builder = MeshBuilder()
    builder.lathe([(44.0, BASE - 1.0), (44.0, 11.0), (41.0, 11.6)], 48, "marble_white", smooth=True, caps=False)
    first = len(builder.polygons)
    builder.lathe([(41.0, 11.6), (30.0, 18.0), (21.0, 25.0)], 48, "matte", smooth=True, caps=False)
    builder.tint(first, (0.34, 0.40, 0.22))
    builder.lathe([(21.0, 25.0), (18.5, 25.0), (18.5, 33.0), (17.0, 33.5)], 40, "marble_white", smooth=True, caps=False)
    first = len(builder.polygons)
    builder.lathe([(17.0, 33.5), (8.0, 40.0), (0.0, 42.0)], 32, "matte", smooth=True, caps=False)
    builder.tint(first, (0.32, 0.38, 0.21))
    builder.lathe([(1.4, 41.5), (1.4, 46.0), (0.0, 46.0)], 10, "bronze", smooth=True, caps=False)
    return builder


def capitoline_temple():
    builder = MeshBuilder()
    builder.box((-27.0, -31.0, -6.0), (27.0, 31.0, 4.5), "plaster", bottom=False)
    builder.box((-21.0, -26.0, 4.5), (21.0, 14.0, 24.0), "marble_white", bottom=False, top=False)
    for x in range(6):
        column_x = -20.0 + 8.0 * x
        for y in (16.0, 22.0, 28.0):
            builder.lathe([(1.0, 4.5), (0.85, 23.0)], 8, "marble_white", smooth=True, caps=False,
                          matrix=placement(column_x, y, 0.0))
    builder.box((-22.0, -27.0, 23.0), (22.0, 30.0, 25.5), "marble_white")
    rise = 22.0 * 0.38
    gable_roof(builder, -27.0, 30.0, 22.5, 25.5, 25.5 + rise, "bronze_gilt", along_axis="y", imbrex=False)
    gable_ends(builder, -27.0, 30.0, 22.0, 25.5, 25.5 + rise, "marble_white", along_axis="y")
    return builder


def trajan():
    builder = MeshBuilder()
    builder.box((-2.8, -2.8, -1.0), (2.8, 2.8, 5.4), "marble_white", bottom=False)
    builder.lathe([(2.0, 5.4), (1.85, 6.0), (1.85, 33.0), (2.3, 34.0), (2.3, 35.0), (1.0, 35.2), (1.0, 37.5), (0.0, 38.2)],
                  16, "marble_white", smooth=True, caps=False)
    builder.lathe([(0.45, 37.5), (0.45, 40.5), (0.0, 41.0)], 8, "bronze_gilt", smooth=True, caps=False)
    hall(builder, -10.0, 58.0, 160.0, 56.0, 26.0, "marble_white", roof="bronze_gilt")
    return builder


def colosseum():
    builder = MeshBuilder()
    ring_lathe(builder, [(94.0, BASE - 2.0), (94.0, 48.0), (88.0, 48.0), (84.0, 36.0), (46.0, 5.0)], "travertine", 72,
               ellipse=94.0 / 78.0)
    first = len(builder.polygons)
    ring_lathe(builder, [(46.0, 5.0), (46.0, 0.5)], "travertine", 48, ellipse=46.0 / 30.0)
    builder.tint(first, (0.8, 0.78, 0.74))
    return builder


INSULAE = {
    "insula_court_a": lambda: courtyard_house(30.0, 24.0, 11.0, 8.0, 15.0, "plaster_ochre", court_material="plaster_grey"),
    "insula_court_b": lambda: courtyard_house(27.0, 22.0, 9.0, 7.0, 18.0, "brick", court_material="plaster_grey"),
    "insula_block_a": lambda: block_house(20.0, 12.0, 12.0, "plaster_rose", shops=5, windows=5),
    "insula_block_b": lambda: block_house(24.0, 13.0, 16.0, "brick", shops=6, windows=6),
    "domus_low": lambda: block_house(16.0, 11.0, 7.0, "plaster_cream", shops=2, windows=3),
}


def unrotate(x, y, angle):
    return x * math.cos(-angle) - y * math.sin(-angle), x * math.sin(-angle) + y * math.cos(-angle)


class Zones:
    def __init__(self, axis_angle):
        self.angle = axis_angle
        self.rects = []
        self.circles = []

    def rect(self, cx, cy, hx, hy, angle=0.0):
        self.rects.append((cx, cy, hx, hy, angle))

    def circle(self, cx, cy, radius):
        self.circles.append((cx, cy, radius))

    def blocked(self, x, y):
        for cx, cy, hx, hy, angle in self.rects:
            u, v = unrotate(x - cx, y - cy, angle)
            if abs(u) < hx and abs(v) < hy:
                return True
        return any(math.hypot(x - cx, y - cy) < radius for cx, cy, radius in self.circles)


def site_zones(axis_angle):
    zones = Zones(axis_angle)
    zones.rect(0.0, 10.0, 52.0, 178.0, axis_angle)
    zones.rect(0.0, -95.0, 70.0, 75.0, axis_angle)
    sx, sy = SITES["saepta"]
    zones.rect(sx, sy, 68.0, 165.0)
    nx, ny = SITES["thermae_neronis"]
    zones.rect(nx, ny, 66.0, 100.0)
    dx, dy = SITES["stadium"]
    zones.rect(dx, dy, 62.0, 146.0)
    tx, ty = SITES["theatrum_pompei"]
    zones.circle(tx, ty, 88.0)
    zones.rect(tx + 102.0, ty, 94.0, 74.0)
    px, py = SITES["stagnum"]
    zones.rect(px, py, 82.0, 56.0)
    zones.circle(*SITES["mausoleum_augusti"], 80.0)
    zones.circle(*SITES["capitolium_temple"], 70.0)
    cx, cy = SITES["columna_traiani"]
    zones.rect(cx - 10.0, cy + 40.0, 95.0, 50.0)
    for name, (hx, hy, angle) in CAMPUS.items():
        x, y = SITES[name]
        zones.rect(x, y, hx + 8.0, hy + 8.0, math.radians(angle))
    zones.circle(*SITES["amphitheatrum"], 110.0)
    return zones


def insula_frames(zones, rng, radius=780.0, step=34.0):
    frames = {key: [] for key in INSULAE}
    keys = list(INSULAE)
    weights = np.array([0.26, 0.2, 0.22, 0.2, 0.12])
    count = int(radius / step)
    for i in range(-count, count + 1):
        for j in range(-count, count + 1):
            x = i * step + rng.uniform(-3.0, 3.0)
            y = j * step + rng.uniform(-3.0, 3.0)
            reach = radius * (0.85 + 0.3 * rng.random())
            if math.hypot(x, y) > reach or rng.random() > 0.8 or zones.blocked(x, y):
                continue
            if float(river_distance(x, y)) < 78.0:
                continue
            corners = relief([x - 12, x + 12, x - 12, x + 12, x], [y - 12, y - 12, y + 12, y + 12, y])
            if corners.max() - corners.min() > 6.0 or corners.max() > BASE + 26.0:
                continue
            key = keys[int(rng.choice(len(keys), p=weights / weights.sum()))]
            turn = (math.pi / 2 if rng.random() < 0.4 else 0.0) + math.radians(rng.uniform(-2.5, 2.5))
            frames[key].append(placement(x, y, float(corners.min()), turn))
    return frames


def shade_crown(builder, first, dark, light):
    heights = [sum(builder.positions[index][2] for index in builder.polygons[polygon]) / len(builder.polygons[polygon])
               for polygon in range(first, len(builder.polygons))]
    if not heights:
        return
    low, high = min(heights), max(heights)
    for offset, height in enumerate(heights):
        t = (height - low) / max(high - low, 1e-6)
        builder.polygon_colors[first + offset] = tuple(d + (l - d) * t for d, l in zip(dark, light))


def blob(builder, center, radius, height, seed, segments=8, flat=0.3):
    generator = random.Random(seed)
    phase = generator.uniform(0, 6.28)
    x, y, z = center
    profile = [(0.0, -height * (0.5 - flat)), (radius * 0.8, -height * 0.32), (radius, height * 0.02),
               (radius * 0.86, height * 0.26), (radius * 0.5, height * 0.44), (0.0, height * 0.5)]
    builder.lathe(profile, segments, "matte", smooth=True, matrix=placement(x, y, z),
                  radius_scale=lambda angle: 1.0 + 0.16 * math.sin(3 * angle + phase) + 0.07 * math.sin(7 * angle + phase))


def stone_pine(seed=1, height=14.0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    lean = (generator.uniform(-1.2, 1.2), generator.uniform(-1.2, 1.2))
    trunk(builder, height * 0.72, 0.28, lean)
    top = Vector((lean[0], lean[1], height * 0.78))
    first = len(builder.polygons)
    blob(builder, top, height * 0.32, height * 0.18, seed, 10, 0.35)
    for k in range(4):
        angle = 2 * math.pi * k / 4 + generator.uniform(-0.4, 0.4)
        offset = Vector((math.cos(angle), math.sin(angle), 0.0)) * height * 0.2
        blob(builder, top + offset + Vector((0.0, 0.0, generator.uniform(-1.4, 0.4))), height * 0.17, height * 0.12,
             seed + k + 1, 8, 0.35)
    shade_crown(builder, first, (0.13, 0.19, 0.10), (0.30, 0.40, 0.20))
    return builder


def cypress_tree(seed=2, height=13.0):
    builder = MeshBuilder()
    trunk(builder, 1.2, 0.16)
    generator = random.Random(seed)
    phase = generator.uniform(0, 6.28)
    radius = height * 0.09
    first = len(builder.polygons)
    builder.lathe([(0.0, 0.6), (radius * 0.75, height * 0.08), (radius, height * 0.24), (radius * 0.92, height * 0.45),
                   (radius * 0.7, height * 0.66), (radius * 0.4, height * 0.84), (radius * 0.12, height * 0.96),
                   (0.0, height)], 10, "matte", smooth=True,
                  radius_scale=lambda angle: 1.0 + 0.1 * math.sin(4 * angle + phase) + 0.05 * math.sin(9 * angle))
    shade_crown(builder, first, (0.10, 0.15, 0.08), (0.22, 0.30, 0.15))
    return builder


def broadleaf(seed=3, height=15.0, tint=((0.17, 0.24, 0.10), (0.42, 0.52, 0.24))):
    builder = MeshBuilder()
    generator = random.Random(seed)
    trunk(builder, height * 0.5, 0.36, (generator.uniform(-0.5, 0.5), generator.uniform(-0.5, 0.5)))
    first = len(builder.polygons)
    radius = height * 0.3
    blob(builder, (0.0, 0.0, height * 0.66), radius, height * 0.5, seed, 9, 0.15)
    for k in range(5):
        angle = 2 * math.pi * k / 5 + generator.uniform(-0.3, 0.3)
        reach = radius * generator.uniform(0.55, 0.8)
        blob(builder, (math.cos(angle) * reach, math.sin(angle) * reach, height * generator.uniform(0.5, 0.78)),
             radius * generator.uniform(0.5, 0.7), height * 0.32, seed + k + 1, 7, 0.15)
    shade_crown(builder, first, *tint)
    return builder


def far_tree(kind, seed):
    builder = MeshBuilder()
    phase = random.Random(seed).uniform(0, 6.28)
    if kind == "cypress":
        builder.lathe([(0.0, 0.0), (1.1, 2.0), (1.0, 6.5), (0.0, 12.5)], 5, "matte", smooth=True)
        shade_crown(builder, 0, (0.10, 0.15, 0.08), (0.22, 0.30, 0.15))
        return builder
    height = 13.0 if kind == "pine" else 12.0
    builder.lathe([(0.35, -0.5), (0.22, height * (0.72 if kind == "pine" else 0.5))], 3, "bark", smooth=True, caps=False)
    first = len(builder.polygons)
    radius = height * (0.36 if kind == "pine" else 0.34)
    thick = height * (0.2 if kind == "pine" else 0.5)
    centre = height * (0.8 if kind == "pine" else 0.66)
    builder.lathe([(0.0, centre - thick * 0.45), (radius, centre - thick * 0.1), (radius * 0.8, centre + thick * 0.3),
                   (0.0, centre + thick * 0.5)], 6, "matte", smooth=True,
                  radius_scale=lambda angle: 1.0 + 0.12 * math.sin(3 * angle + phase))
    tint = ((0.13, 0.19, 0.10), (0.30, 0.40, 0.20)) if kind == "pine" else ((0.15, 0.21, 0.09), (0.36, 0.45, 0.21))
    shade_crown(builder, first, *tint)
    return builder


TREES = {
    "tree_pine": lambda: stone_pine(1),
    "tree_pine_b": lambda: stone_pine(7, 11.0),
    "tree_cypress": lambda: cypress_tree(2),
    "tree_plane": lambda: broadleaf(3),
    "tree_oak": lambda: broadleaf(9, 10.0, ((0.12, 0.17, 0.08), (0.30, 0.37, 0.18))),
    "tree_far_pine": lambda: far_tree("pine", 11),
    "tree_far_broad": lambda: far_tree("broad", 12),
    "tree_far_cypress": lambda: far_tree("cypress", 13),
}
FAR = {"tree_pine": "tree_far_pine", "tree_pine_b": "tree_far_pine", "tree_cypress": "tree_far_cypress",
       "tree_plane": "tree_far_broad", "tree_oak": "tree_far_broad"}


def tree_frames(zones, rng):
    frames = {key: [] for key in TREES}

    def plant(key, x, y, scale=(0.8, 1.2)):
        if math.hypot(x, y) > NEAR:
            key = FAR[key]
        frames[key].append(placement(x, y, ground(x, y) - 0.3, rng.uniform(0, 2 * math.pi), rng.uniform(*scale)))
    px, py = SITES["stagnum"]
    for index in range(70):
        angle = rng.uniform(0, 2 * math.pi)
        x = px + math.cos(angle) * rng.uniform(70.0, 95.0)
        y = py + math.sin(angle) * rng.uniform(48.0, 70.0)
        plant(["tree_pine", "tree_plane", "tree_cypress", "tree_pine_b"][index % 4], x, y)
    mx, my = SITES["mausoleum_augusti"]
    for index in range(24):
        angle = 2 * math.pi * index / 24
        plant("tree_cypress", mx + math.cos(angle) * 31.0, my + math.sin(angle) * 31.0, (0.9, 1.0))
    for index in range(90):
        x = mx + rng.uniform(-260.0, 260.0)
        y = my + rng.uniform(-200.0, 260.0)
        if math.hypot(x - mx, y - my) < 60.0 or float(river_distance(x, y)) < 60.0:
            continue
        plant(["tree_pine", "tree_oak", "tree_cypress", "tree_plane"][index % 4], x, y)
    for name, hx, hy, rise, sx, sy in HILLS:
        if rise < 30.0:
            continue
        for index in range(int((36 + rise * 0.6) * 0.5)):
            x = hx + rng.normal(0, sx * 0.55)
            y = hy + rng.normal(0, sy * 0.55)
            if math.hypot(x, y) < 700.0 or float(river_distance(x, y)) < 60.0 or zones.blocked(x, y):
                continue
            plant(["tree_pine", "tree_oak", "tree_pine_b", "tree_cypress"][index % 4], x, y, (0.7, 1.3))
    distances = np.cumsum([0.0] + [math.dist(a, b) for a, b in zip(RIVER[:-1], RIVER[1:])])
    for along in np.arange(20.0, distances[-1], 26.0):
        segment = int(np.searchsorted(distances, along)) - 1
        segment = min(max(segment, 0), len(RIVER) - 2)
        t = (along - distances[segment]) / max(distances[segment + 1] - distances[segment], 1e-6)
        a, b = Vector(RIVER[segment]), Vector(RIVER[segment + 1])
        point = a.lerp(b, t)
        side = Vector((-(b - a).y, (b - a).x)).normalized() * (1 if rng.random() < 0.5 else -1)
        spot = point + side * rng.uniform(58.0, 72.0)
        if rng.random() < 0.65 and not zones.blocked(spot.x, spot.y):
            plant("tree_plane" if rng.random() < 0.6 else "tree_pine_b", spot.x, spot.y)
    return frames


def temple(width, depth, height, front=8, podium=3.5, roof="terracotta_tiles", material="marble_white"):
    builder = MeshBuilder()
    builder.box((-width / 2, -depth / 2, -1.0), (width / 2, depth / 2, podium), "travertine", bottom=False)
    porch = width * 0.75
    builder.box((-width / 2 + 1.2, -depth / 2 + 1.2, podium), (width / 2 - 1.2, depth / 2 - porch, podium + height),
                material, bottom=False, top=False)
    radius = width / front * 0.28
    for k in range(front):
        x = -width / 2 + width * (k + 0.5) / front
        for y in (depth / 2 - radius * 2.2, depth / 2 - porch * 0.55):
            builder.lathe([(radius, podium), (radius * 0.86, podium + height)], 8, material, smooth=True, caps=False,
                          matrix=placement(x, y, 0.0))
    eave = podium + height + width * 0.09
    builder.box((-width / 2, -depth / 2 + 1.0, podium + height), (width / 2, depth / 2, eave), material)
    rise = width / 2 * 0.42
    gable_roof(builder, -depth / 2 + 1.0, depth / 2 + 0.4, width / 2 + 0.4, eave, eave + rise, roof, along_axis="y",
               imbrex=False)
    gable_ends(builder, -depth / 2 + 1.0, depth / 2, width / 2, eave, eave + rise, material, along_axis="y")
    return builder


def half_theatre(radius, height, inner):
    builder = MeshBuilder()
    ring_lathe(builder, [(radius, -1.0), (radius, height), (inner, 3.0)], "travertine", 32, math.pi / 2, math.pi)
    for y in (-1, 1):
        builder.oriented([Vector((0.0, y * radius, -1.0)), Vector((0.0, y * radius, height)),
                          Vector((0.0, y * inner, 3.0)), Vector((0.0, y * inner, -1.0))], (1, 0, 0), "travertine")
    builder.box((3.0, -radius * 0.85, -1.0), (11.0, radius * 0.85, height - 2.0), "plaster_cream")
    return builder


def obelisk(height):
    builder = MeshBuilder()
    base = height * 0.055
    builder.box((-base * 1.6, -base * 1.6, -0.5), (base * 1.6, base * 1.6, 1.6), "marble_white")
    builder.lathe([(base * 1.41, 1.6), (base * 1.0, 1.6 + height), (0.0, 1.6 + height * 1.06)], 4, "granite_rose",
                  smooth=False, caps=False, matrix=Matrix.Rotation(math.pi / 4, 4, "Z"))
    return builder


def campus_buildings():
    built = {}
    matidia = courtyard_house(76.0, 96.0, 64.0, 84.0, 9.0, "plaster_cream", court_material="travertine")
    matidia.merge(temple(26.0, 40.0, 15.0), placement(0.0, -6.0, 0.0))
    built["templum_matidiae"] = matidia
    iseum = courtyard_house(70.0, 220.0, 58.0, 208.0, 9.0, "plaster_cream", court_material="travertine")
    iseum.merge(temple(16.0, 24.0, 11.0, front=6), placement(0.0, 80.0, 0.0))
    for y in (-30.0, 30.0):
        iseum.merge(obelisk(12.0), placement(0.0, y, 0.0))
    built["iseum"] = iseum
    sacra = MeshBuilder()
    sacra.box((-34.0, -26.0, -0.6), (34.0, 26.0, 0.1), "travertine", bottom=False)
    for x, size in ((-22.0, (12.0, 20.0)), (8.0, (11.0, 18.0)), (24.0, (12.0, 22.0))):
        sacra.merge(temple(size[0], size[1], 8.0, front=4, podium=2.5), placement(x, -2.0, 0.0))
    sacra.lathe([(7.5, 0.0), (7.5, 2.5), (6.2, 2.5), (6.2, 11.0), (6.6, 11.5), (0.0, 15.0)], 16, "marble_white",
                smooth=True, caps=False, matrix=placement(-6.0, -4.0, 0.0))
    built["area_sacra"] = sacra
    minucia = courtyard_house(120.0, 66.0, 104.0, 50.0, 9.0, "plaster_cream", court_material="travertine")
    minucia.merge(temple(14.0, 22.0, 10.0, front=6), placement(0.0, 0.0, 0.0))
    built["porticus_minucia"] = minucia
    balbi = half_theatre(46.0, 22.0, 14.0)
    balbi.merge(courtyard_house(60.0, 80.0, 46.0, 66.0, 9.0, "plaster_cream", court_material="travertine"),
                placement(44.0, 0.0, 0.0))
    built["theatrum_balbi"] = balbi
    built["circus_flaminius"] = courtyard_house(300.0, 100.0, 288.0, 88.0, 6.0, "plaster_cream",
                                                court_material="travertine")
    built["theatrum_marcelli"] = half_theatre(66.0, 32.0, 18.0)
    return built


CAMPUS = {"templum_matidiae": (38.0, 48.0, 0.0), "iseum": (35.0, 110.0, 0.0), "area_sacra": (34.0, 26.0, 0.0),
          "porticus_minucia": (60.0, 33.0, 0.0), "theatrum_balbi": (74.0, 46.0, 0.0),
          "circus_flaminius": (150.0, 50.0, -12.0), "theatrum_marcelli": (66.0, 66.0, 225.0)}


def monuments(axis_matrix):
    placed = []
    placed.append(("neptune_agrippa", neptune_and_agrippa(), axis_matrix @ Matrix.Identity(4)))
    sx, sy = SITES["saepta"]
    placed.append(("saepta", courtyard_house(124.0, 310.0, 100.0, 286.0, 14.0, "plaster_cream",
                                             court_material="travertine"), placement(sx, sy, BASE)))
    nx, ny = SITES["thermae_neronis"]
    baths = courtyard_house(120.0, 190.0, 64.0, 110.0, 14.0, "brick", court_material="travertine")
    hall(baths, 0.0, 0.0, 52.0, 36.0, 26.0, "brick")
    placed.append(("thermae_neronis", baths, placement(nx, ny, BASE)))
    dx, dy = SITES["stadium"]
    placed.append(("stadium", stadium(), placement(dx, dy, 0.0)))
    tx, ty = SITES["theatrum_pompei"]
    placed.append(("theatrum_pompei", theatre(), placement(tx, ty, 0.0)))
    mx, my = SITES["mausoleum_augusti"]
    placed.append(("mausoleum_augusti", mausoleum(), placement(mx, my, 0.0)))
    cx, cy = SITES["capitolium_temple"]
    placed.append(("capitolium", capitoline_temple(), placement(cx, cy, float(relief([cx], [cy])[0]))))
    jx, jy = SITES["columna_traiani"]
    placed.append(("forum_traiani", trajan(), placement(jx, jy, float(relief([jx], [jy])[0]))))
    ax, ay = SITES["amphitheatrum"]
    placed.append(("amphitheatrum", colosseum(), placement(ax, ay, float(relief([ax], [ay])[0]))))
    px, py = SITES["stagnum"]
    pool = MeshBuilder()
    pool.box((-62.0, -38.0, BASE - 0.5), (62.0, 38.0, BASE + 0.45), "marble_white", bottom=False)
    pool.oriented([Vector((-60.0, -36.0, BASE + 0.3)), Vector((60.0, -36.0, BASE + 0.3)), Vector((60.0, 36.0, BASE + 0.3)),
                   Vector((-60.0, 36.0, BASE + 0.3))], (0, 0, 1), "water")
    placed.append(("stagnum", pool, placement(px, py, 0.0)))
    for name, builder in campus_buildings().items():
        x, y = SITES[name]
        placed.append((name, builder, placement(x, y, ground(x, y), math.radians(CAMPUS[name][2]))))
    return placed


def smoke_points(insulae, rng, count=9):
    candidates = [(frame.translation.x, frame.translation.y, frame.translation.z + SMOKE_HEIGHT[key] + 2.0)
                  for key, frames in insulae.items() for frame in frames]
    candidates = [point for point in candidates if 140.0 < math.hypot(point[0], point[1]) < 520.0]
    chosen = rng.choice(len(candidates), min(count, len(candidates)), replace=False)
    return [Vector(candidates[index]) for index in sorted(chosen)]

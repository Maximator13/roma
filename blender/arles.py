import json
import math
import os
import random
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from kit import arles_crowds, arles_details, arles_life, arles_monuments, buildings, monuments, urban
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, build_library, save_pixels
from kit.orders import column
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, haze_volume,
                       render_still, sun_lamp)
from kit.terrain import (ETALAB_LICENCE, RGE_ALTI_LAYER, GeoFrame, HeightField, ellipse_distance, fetch_lambert_grid,
                         grid_mesh, local_heights, point_in_polygon, polyline_distance,
                         rectangle_distance, remove_faces_inside, value_noise)

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "arles")
BLEND = os.path.join(CACHE, "work", "arles.blend")
ORIGIN = (43.67697, 4.62747)
GRID = math.radians(10.0)
TRINQUETAILLE_GRID = math.radians(45.0)
HALF = 1500.0
SPACING = 15.0
FAR_HALF = 12000.0
FAR_SPACING = 200.0
TEXTURE = 2048
SUN_AZIMUTH = 288.0
SUN_ELEVATION = 14.0
WATER = 1.0
QUAY = 3.2
BANK = 3.5
CIRCUS_LEVEL = 3.6
PITCH = 70.0
SITE_HAZE = tuple(((channel / 255.0 + 0.055) / 1.055) ** 2.4 for channel in (0xC9, 0xD6, 0xE6))
STREET = 7.0
U_OFFSET = 52.0
V_OFFSET = -40.0
WFS = "https://data.geopf.fr/wfs/ows"

SITES = {
    "forum": (0.0, 0.0),
    "theatre": (215.0, -54.0),
    "arena": (279.0, 86.0),
    "gate": (404.0, -97.0),
    "mourgues": (398.0, -168.0),
    "circus_remains": (-821.0, -479.0),
}
ARENA_BEARING = 164.0
ARENA_AXES = (68.0, 53.5)
WALL_TRACE = [(95.0, 325.0), (210.0, 290.0), (330.0, 240.0), (425.0, 160.0), (448.0, 40.0), (425.0, -55.0),
              (404.0, -97.0), (401.0, -135.0), (398.0, -168.0), (300.0, -200.0), (150.0, -215.0), (0.0, -222.0),
              (-150.0, -212.0), (-330.0, -158.0), (-480.0, -92.0), (-575.0, -40.0)]
SECONDARY_GATES = [(441.0, 70.0), (-330.0, -158.0)]
ROADS = {
    "aurelia": [(404.0, -97.0), (520.0, -128.0), (700.0, -176.0), (950.0, -240.0), (1490.0, -380.0)],
    "ernaginum": [(441.0, 70.0), (620.0, 170.0), (900.0, 420.0), (1200.0, 700.0), (1490.0, 960.0)],
    "circus": [(-330.0, -158.0), (-420.0, -190.0), (-520.0, -215.0)],
    "nemausus": [(-600.0, 420.0), (-820.0, 650.0), (-1100.0, 960.0), (-1490.0, 1330.0)],
}


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 24}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def rotate(x, y, angle):
    return x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)


def to_grid(x, y, angle=GRID):
    return rotate(x, y, -angle)


def from_grid(u, v, angle=GRID):
    return rotate(u, v, angle)


def fetch_hydro(frame, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        south, west = frame.to_geo(-3200.0, -3200.0)
        north, east = frame.to_geo(3200.0, 3200.0)
        url = (f"{WFS}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:surface_hydrographique"
               f"&BBOX={south},{west},{north},{east},urn:ogc:def:crs:EPSG::4326&OUTPUTFORMAT=application/json"
               f"&COUNT=5000")
        request = urllib.request.Request(url, headers={"User-Agent": "roma-scene-builder/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
        with open(path, "wb") as handle:
            handle.write(data)
        with open(path + ".meta.json", "w", encoding="utf8") as handle:
            json.dump({"url": url, "source": "IGN BD TOPO V3, surface_hydrographique", "licence": ETALAB_LICENCE},
                      handle, indent=1)
    with open(path, encoding="utf8") as handle:
        collection = json.load(handle)
    features = []
    for feature in collection["features"]:
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        rings = []
        for polygon in polygons:
            for ring in polygon:
                rings.append([frame.to_local(point[1], point[0]) for point in ring])
        features.append((feature["properties"].get("nature"), rings))
    return features


def scanline_mask(ring, axis_x, axis_y, mask):
    points = np.asarray(ring, dtype=np.float64)
    a = points
    b = np.roll(points, -1, axis=0)
    for (x0, y0), (x1, y1) in zip(a, b):
        if y0 == y1:
            continue
        low, high = (y0, y1) if y0 < y1 else (y1, y0)
        first = int(np.searchsorted(axis_y, low, side="right"))
        last = int(np.searchsorted(axis_y, high, side="right"))
        if first >= last:
            continue
        rows = np.arange(first, last)
        crossings = x0 + (axis_y[rows] - y0) * (x1 - x0) / (y1 - y0)
        stops = np.searchsorted(axis_x, crossings, side="left")
        for row, stop in zip(rows, stops):
            if stop > 0:
                mask[row, :stop] ^= True


def rings_mask(features, natures, grid_x, grid_y):
    axis_x = grid_x[0, :]
    axis_y = grid_y[:, 0]
    mask = np.zeros(grid_x.shape, dtype=bool)
    for nature, rings in features:
        if nature not in natures:
            continue
        for ring in rings:
            xs = [point[0] for point in ring]
            ys = [point[1] for point in ring]
            if max(xs) < axis_x[0] or min(xs) > axis_x[-1] or max(ys) < axis_y[0] or min(ys) > axis_y[-1]:
                continue
            scanline_mask(ring, axis_x, axis_y, mask)
    return mask


def fast_polygon(ring, grid_x, grid_y):
    mask = np.zeros(grid_x.shape, dtype=bool)
    scanline_mask(ring, grid_x[0, :], grid_y[:, 0], mask)
    return mask


def shifted(array, dr, dc, fill):
    out = np.full(array.shape, fill, dtype=array.dtype)
    rows, columns = array.shape
    out[max(dr, 0):rows + min(dr, 0), max(dc, 0):columns + min(dc, 0)] = \
        array[max(-dr, 0):rows + min(-dr, 0), max(-dc, 0):columns + min(-dc, 0)]
    return out


def window_filter(array, radius, reducer, fill):
    result = array.copy()
    for offset in range(-radius, radius + 1):
        result = reducer(result, shifted(array, offset, 0, fill))
    rows = result.copy()
    for offset in range(-radius, radius + 1):
        rows = reducer(rows, shifted(result, 0, offset, fill))
    return rows


def grow(mask, steps):
    out = mask.copy()
    for _ in range(steps):
        out = out | shifted(out, 1, 0, False) | shifted(out, -1, 0, False) | shifted(out, 0, 1, False) | \
            shifted(out, 0, -1, False)
    return out


def surface_height(field, x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    column = np.clip((x + field.half_extent) / field.spacing, 0, field.samples - 1.000001)
    row = np.clip((y + field.half_extent) / field.spacing, 0, field.samples - 1.000001)
    c0 = np.floor(column).astype(int)
    r0 = np.floor(row).astype(int)
    fx = column - c0
    fy = row - r0
    h = field.heights
    h00, h01, h10, h11 = h[r0, c0], h[r0, c0 + 1], h[r0 + 1, c0], h[r0 + 1, c0 + 1]
    value = np.where(fx >= fy, h00 + fx * (h01 - h00) + fy * (h11 - h01), h00 + fy * (h10 - h00) + fx * (h11 - h10))
    return float(value) if np.ndim(value) == 0 else value


def bank_lines(features):
    axis = np.linspace(-HALF, HALF, 1201)
    grid_x, grid_y = np.meshgrid(axis, axis)
    water = rings_mask(features, ("Ecoulement naturel",), grid_x, grid_y)
    left, right = [], []
    for row in range(0, 1201, 4):
        y = axis[row]
        if abs(y) > HALF - 60:
            continue
        xs = axis[water[row] & (axis > -1400) & (axis < 450)]
        if len(xs) == 0:
            continue
        left.append((float(xs.max()), float(y)))
        right.append((float(xs.min()), float(y)))
    return left, right, water, axis


def polyline_point(points, distance):
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        if distance <= length:
            t = distance / max(length, 1e-9)
            return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), ((x1 - x0) / length, (y1 - y0) / length)
        distance -= length
    (x0, y0), (x1, y1) = points[-2], points[-1]
    length = math.hypot(x1 - x0, y1 - y0)
    return points[-1], ((x1 - x0) / length, (y1 - y0) / length)


def polyline_length(points):
    return sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]))


def segment_of(points, y_low, y_high):
    return [point for point in points if y_low <= point[1] <= y_high]


def smooth_line(points, passes=3):
    out = list(points)
    for _ in range(passes):
        out = [out[0]] + [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4)
                          for a, b, c in zip(out[:-2], out[1:-1], out[2:])] + [out[-1]]
    return out


def offset_line(points, distance):
    out = []
    for index, (x, y) in enumerate(points):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        out.append((x - dy / length * distance, y + dx / length * distance))
    return out


def city_polygon(left_bank):
    north = WALL_TRACE[0]
    south = WALL_TRACE[-1]
    river = [point for point in left_bank if south[1] - 5 < point[1] < north[1] + 5]
    river.sort(key=lambda point: point[1])
    return WALL_TRACE + [(x + 6.0, y) for x, y in river]


class Circus:
    def __init__(self, center, angle):
        self.center = center
        self.angle = angle

    def local(self, x, y):
        return rotate(x - self.center[0], y - self.center[1], -self.angle)

    def world(self, x, y):
        wx, wy = rotate(x, y, self.angle)
        return self.center[0] + wx, self.center[1] + wy


def place_circus(left_bank, water, axis):
    lower = [point for point in left_bank if -560 < point[1] < -150]
    xs = np.array([point[0] for point in lower])
    ys = np.array([point[1] for point in lower])
    slope = np.polyfit(ys, xs, 1)[0]
    direction = Vector((slope, 1.0)).normalized()
    angle = math.atan2(-direction.x, direction.y)
    remains = Vector(SITES["circus_remains"])
    normal = Vector((direction.y, -direction.x))
    step = 0
    while True:
        center = remains + direction * 165.0 + normal * step
        circus = Circus((center.x, center.y), angle)
        clear = True
        for local_x in (-60.0, 0.0, 60.0):
            for local_y in np.linspace(-235.0, 235.0, 25):
                wx, wy = circus.world(local_x, local_y)
                column = int(round((wx + HALF) / (axis[1] - axis[0])))
                row = int(round((wy + HALF) / (axis[1] - axis[0])))
                if 0 <= row < water.shape[0] and 0 <= column < water.shape[1] and water[row, column]:
                    clear = False
        if clear or step > 200:
            return circus, step
        step += 5.0


class Exclusions:
    def __init__(self):
        self.shapes = []

    def circle(self, x, y, radius):
        self.shapes.append(lambda px, py: math.hypot(px - x, py - y) < radius)

    def rectangle(self, x, y, half_u, half_v, angle):
        def test(px, py):
            u, v = rotate(px - x, py - y, -angle)
            return abs(u) < half_u and abs(v) < half_v
        self.shapes.append(test)

    def ellipse(self, x, y, semi_major, semi_minor, bearing_degrees):
        angle = math.radians(90.0 - bearing_degrees)

        def test(px, py):
            u, v = rotate(px - x, py - y, -angle)
            return (u / semi_major) ** 2 + (v / semi_minor) ** 2 < 1.0
        self.shapes.append(test)

    def corridor(self, a, b, width):
        ax, ay = a
        bx, by = b

        def test(px, py):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-9)))
            return math.hypot(px - ax - t * dx, py - ay - t * dy) < width
        self.shapes.append(test)

    def polyline(self, points, width):
        for a, b in zip(points[:-1], points[1:]):
            self.corridor(a, b, width)

    def blocked(self, x, y):
        return any(shape(x, y) for shape in self.shapes)


class Scene:
    def __init__(self, tiles, field, datum):
        self.tiles = tiles
        self.field = field
        self.datum = datum
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Arles")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.route_count = 0
        self.route_points = 0
        self.paved = []
        self.rng = random.Random(29)
        self.lanes = {}
        self.skipped = 0
        self.houses = {}
        self.arena_bays = []
        self.arena_west_t = 0.0
        self.circus_bays = []
        self.proedria = []

    def house(self, key, matrices):
        self.houses.setdefault(key, []).extend(matrices)

    def place_houses(self):
        for key, matrices in self.houses.items():
            build = (lambda key=key: socle_builder(key[6:])) if key.startswith("socle_") else HOUSES[key]
            self.instances("city", key, build, matrices, cast_shadow=not key.startswith("socle_"))

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return surface_height(self.field, x, y) - self.datum

    def floor(self, x, y):
        for points, half_width in self.paved:
            for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
                dx, dy = x1 - x0, y1 - y0
                t = ((x - x0) * dx + (y - y0) * dy) / max(dx * dx + dy * dy, 1e-9)
                if -1e-6 <= t <= 1.0 + 1e-6 and math.hypot(x - x0 - t * dx, y - y0 - t * dy) < half_width - 0.05:
                    return self.ground(x, y) + 0.1
        return self.ground(x, y) + 0.03

    def avoid_routes(self, polylines, cell=4.0, reach=3.0):
        self.lanes = {}
        for points in polylines:
            for a, b in zip(points[:-1], points[1:]):
                for i in range(int(math.floor((min(a[0], b[0]) - reach) / cell)),
                               int(math.floor((max(a[0], b[0]) + reach) / cell)) + 1):
                    for j in range(int(math.floor((min(a[1], b[1]) - reach) / cell)),
                                   int(math.floor((max(a[1], b[1]) + reach) / cell)) + 1):
                        self.lanes.setdefault((i, j), []).append((tuple(a[:2]), tuple(b[:2])))

    def near_route(self, x, y, clearance, cell=4.0):
        for (ax, ay), (bx, by) in self.lanes.get((int(math.floor(x / cell)), int(math.floor(y / cell))), ()):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / max(dx * dx + dy * dy, 1e-9)))
            if math.hypot(x - ax - t * dx, y - ay - t * dy) < clearance:
                return True
        return False

    def unique(self, group, builder, matrix, occlusion=True):
        if not occlusion:
            builder.heights = [10.0] * len(builder.positions)
        self.pending.setdefault(group, []).append((builder, matrix))
        self.root(group)

    def flush(self):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(builder, matrix, keep_local=True)
            created = unique_object(f"{group}_static", merged, self.collection, self.root(group), self.tiles)
            if group in ("ground", "roads", "water", "port_low"):
                created["cast_shadow"] = False
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True, occlusion=True, merge=False):
        if not matrices:
            return None
        if merge:
            builder = build()
            for matrix in matrices:
                self.unique(group, builder, matrix, occlusion)
            return None
        return self.library.place(key, build, self.collection, self.root(group), matrices, cast_shadow, occlusion)

    def add(self, key, matrix):
        if key.startswith(MOBILE) and not key.startswith(ROUTE_EXEMPT):
            clearance = next(value for prefix, value in CLEARANCE.items() if key.startswith(prefix))
            point = matrix.translation
            if self.near_route(point.x, point.y, clearance):
                self.skipped += 1
                return False
        if key.startswith("fig_") and not key.startswith("fig_seated"):
            matrix = matrix @ Matrix.Scale(self.rng.uniform(0.94, 1.06), 4)
        self.placements.setdefault(key, []).append(matrix)
        return True


def build_terrain(features):
    frame = GeoFrame(*ORIGIN)
    near = fetch_lambert_grid(frame, 1650.0, 5.0, RGE_ALTI_LAYER, os.path.join(CACHE, "src", "rge_alti_l93_5m.bil"))
    far = fetch_lambert_grid(frame, 12200.0, 100.0, RGE_ALTI_LAYER,
                             os.path.join(CACHE, "src", "rge_alti_l93_100m.bil"))
    field = HeightField(local_heights(frame, HALF, SPACING, near), HALF)
    far_field = HeightField(local_heights(frame, FAR_HALF, FAR_SPACING, far), FAR_HALF)
    return field, far_field, [near[2], far[2]]


def clean_terrain(field, features, city):
    gx, gy = field.grid_x, field.grid_y
    river = rings_mask(features, ("Ecoulement naturel",), gx, gy)
    canal = rings_mask(features, ("Canal", "Réservoir-bassin", "Réservoir-bassin d'orage", "Retenue"), gx, gy) & ~river
    field.infill(grow(canal, 1), 600)
    keep = fast_polygon(city, gx, gy)
    keep = grow(keep, 4)
    land = np.where(river, np.nan, field.heights)
    filled = np.where(river, np.nanmedian(land), field.heights)
    radius = 4
    opened = window_filter(window_filter(filled, radius, np.minimum, np.inf), radius, np.maximum, -np.inf)
    lowered = np.minimum(field.heights, opened + 0.6)
    weight = (~keep).astype(float)
    field.heights = np.where(river, field.heights, field.heights * (1 - weight) + lowered * weight)
    return river


def carve_river(field, river, bank_left, bank_right, city, port_zones):
    gx, gy = field.grid_x, field.grid_y
    depth_steps = np.zeros(river.shape)
    inner = river.copy()
    for step in range(5):
        inner = inner & shifted(inner, 1, 0, True) & shifted(inner, -1, 0, True) & shifted(inner, 0, 1, True) & \
            shifted(inner, 0, -1, True)
        depth_steps += inner
    bed = WATER - 1.6 - depth_steps * 0.9
    distance = np.minimum(polyline_distance(bank_left, gx, gy), polyline_distance(bank_right, gx, gy))
    land = ~river
    inside = fast_polygon(city, gx, gy)
    natural = np.minimum(field.heights, BANK + distance * 0.025)
    blend = np.clip(1.0 - (distance - 40.0) / 60.0, 0.0, 1.0) * (~inside)
    heights = np.where(land, field.heights * (1 - blend) + natural * blend, bed)
    for line in port_zones:
        d = polyline_distance(line, gx, gy)
        weight = np.clip(1.0 - (d - 30.0) / 45.0, 0.0, 1.0) * land
        weight = weight * weight * (3 - 2 * weight)
        heights = heights * (1 - weight) + QUAY * weight
    field.heights = heights
    return distance


def flatten_sites(field, circus):
    ax, ay = SITES["arena"]
    a, b = ARENA_AXES
    ring = [field.sample(x, y) for grow in (3.0, 5.0, 7.0, 10.0) for x, y in arena_ring(grow, 48)]
    arena_level = float(np.median(ring))
    arena_area = ellipse_distance(ax, ay, a + APRON, b + APRON, math.radians(-ARENA_BEARING))
    field.flatten(arena_area, arena_level, 0.01)
    tx, ty = SITES["theatre"]
    theatre_level = float(np.median([field.sample(tx + r * math.cos(t), ty + r * math.sin(t))
                                     for r in (0.0, 10.0, 20.0) for t in np.linspace(0, 6.28, 12)]))
    theatre = theatre_area()
    field.flatten(lambda x, y: np.maximum(theatre(x, y), 12.0 - arena_area(x, y)), theatre_level, 12.0)
    forum_level = float(field.sample(*from_grid(30.0, 0.0)))
    base = rectangle_distance(*from_grid(2.4, 0.0), 42.6, 31.2, GRID)
    north = rectangle_distance(*from_grid(-5.0, 38.7), 50.0, 7.5, GRID)
    west = rectangle_distance(*from_grid(-47.7, 7.5), 7.5, 38.7, GRID)
    field.flatten(lambda x, y: np.maximum(np.minimum(north(x, y), west(x, y)), -base(x, y)), forum_level - 4.5, 25.0)
    pad = rectangle_distance(*from_grid(10.0, -7.5), 50.0, 38.7, GRID)
    field.flatten(pad, forum_level, 0.5)
    gx, gy = SITES["gate"]
    gate_level = field.sample(gx, gy)
    field.flatten(lambda x, y: np.hypot(x - gx, y - gy) - 30.0, gate_level, 25.0)
    cx, cy = circus.center
    field.flatten(rectangle_distance(cx, cy, 62.0, 240.0, circus.angle), CIRCUS_LEVEL, 35.0)
    return {"theatre": theatre_level, "arena": arena_level, "forum": forum_level, "gate": gate_level}


def street_distance(u, v):
    du = np.abs(((u - U_OFFSET + PITCH / 2) % PITCH) - PITCH / 2)
    dv = np.abs(((v - V_OFFSET + PITCH / 2) % PITCH) - PITCH / 2)
    return np.minimum(du, dv)


def sun_shadow(field, grid_x, grid_y, heights, steps=32, reach=1200.0):
    azimuth = math.radians(SUN_AZIMUTH)
    direction = (math.sin(azimuth), math.cos(azimuth))
    slope = math.tan(math.radians(SUN_ELEVATION))
    clearance = np.full(heights.shape, np.inf)
    for step in range(1, steps + 1):
        distance = reach * (step / steps) ** 1.6
        ahead = field.sample(grid_x + direction[0] * distance, grid_y + direction[1] * distance)
        clearance = np.minimum(clearance, heights + distance * slope - ahead)
    return np.clip(clearance / 6.0 + 0.5, 0.0, 1.0)


def terrain_colour(grid_x, grid_y, heights, slope, river, city, roads, bank_distance, seed, shadow=None, far=False,
                   port=None):
    u = grid_x * math.cos(GRID) + grid_y * math.sin(GRID)
    v = -grid_x * math.sin(GRID) + grid_y * math.cos(GRID)
    shape = grid_x.shape
    noise = value_noise(shape, 14, seed, 5)
    fine = value_noise(shape, 90, seed + 1, 3)
    size_u, size_v = 120.0, 70.0
    parcel_u = np.floor(u / size_u).astype(np.int64)
    parcel_v = np.floor(v / size_v).astype(np.int64)
    parcel = ((parcel_u * 73856093) ^ (parcel_v * 19349663)) % 1000 / 1000.0
    crops = np.array([[0.78, 0.68, 0.42], [0.80, 0.70, 0.45], [0.72, 0.64, 0.43], [0.58, 0.58, 0.37],
                      [0.63, 0.61, 0.40], [0.69, 0.64, 0.45], [0.76, 0.68, 0.46], [0.55, 0.56, 0.35]])
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)]
    colour = colour * (0.9 + 0.2 * fine[..., None]) * 0.75 + np.array([0.70, 0.64, 0.44]) * 0.25
    rows = np.sin(v * 2 * math.pi / 2.4) > 0.25
    vine = (parcel > 0.43) & (parcel < 0.55)
    colour = np.where(vine[..., None], np.array([0.58, 0.51, 0.37]), colour)
    colour = np.where((vine & rows)[..., None], np.array([0.36, 0.42, 0.24]), colour)
    edge = (np.abs((u / size_u) % 1.0 - 0.5) > 0.492) | (np.abs((v / size_v) % 1.0 - 0.5) > 0.487)
    colour = np.where(edge[..., None], np.array([0.45, 0.47, 0.30]), colour)
    colour = colour * 0.7 + np.array([0.72, 0.65, 0.43]) * 0.3
    level = heights - WATER
    marsh = np.clip(1.0 - (level - 0.9) / 0.9, 0.0, 1.0) * np.clip((fine - 0.2) * 3, 0.3, 1.0)
    east = ((grid_x - 850.0) / 430.0) ** 2 + ((grid_y + 170.0) / 400.0) ** 2
    south = ((grid_x + 250.0) / 650.0) ** 2 + ((grid_y + 600.0) / 330.0) ** 2
    lowland = np.clip((1.0 - np.minimum(east, south)) / 0.4, 0.0, 1.0) * (0.7 + 0.25 * noise)
    marsh = np.maximum(marsh, lowland)
    marsh_colour = np.dstack([0.36 + 0.06 * fine, 0.41 + 0.05 * fine, 0.26 + 0.03 * fine])
    pools = (level < 0.35) & (noise > 0.45)
    marsh_colour = np.where(pools[..., None], np.array([0.24, 0.29, 0.26]), marsh_colour)
    colour = colour * (1 - marsh[..., None]) + marsh_colour * marsh[..., None]
    rock = np.clip((slope - 0.12) / 0.1, 0, 1) * np.clip((level - 6.0) / 6.0, 0, 1)
    garrigue = np.dstack([0.42 + 0.1 * fine, 0.43 + 0.08 * fine, 0.30 + 0.05 * fine])
    garrigue = np.where((fine > 0.62)[..., None], np.array([0.76, 0.72, 0.62]), garrigue)
    colour = colour * (1 - rock[..., None]) + garrigue * rock[..., None]
    if far:
        crau = np.clip((grid_x - 3500.0) / 1500.0, 0, 1) * np.clip((-grid_y + 3000.0) / 2500.0, 0, 1)
        crau_colour = np.dstack([0.70 + 0.06 * fine, 0.66 + 0.05 * fine, 0.52 + 0.04 * fine])
        colour = colour * (1 - crau[..., None]) + crau_colour * crau[..., None]
        hills = np.clip((heights - 40.0) / 60.0, 0, 1)
        hill_colour = np.dstack([0.46 + 0.12 * fine, 0.47 + 0.1 * fine, 0.36 + 0.08 * fine])
        hill_colour = np.where((fine > 0.6)[..., None], np.array([0.78, 0.75, 0.66]), hill_colour)
        colour = colour * (1 - hills[..., None]) + hill_colour * hills[..., None]
    sand = np.clip(1.0 - (bank_distance - 4.0) / 14.0, 0, 1) * (~river)
    colour = colour * (1 - sand[..., None]) + np.array([0.64, 0.57, 0.44]) * sand[..., None]
    urban_colour = np.dstack([0.75 + 0.06 * fine, 0.67 + 0.05 * fine, 0.53 + 0.04 * fine])
    colour = colour * (1 - city[..., None]) + urban_colour * city[..., None]
    if port is not None:
        trodden = np.clip(1.0 - (port - 45.0) / 30.0, 0, 1) * (~river)
        earth = np.dstack([0.60 + 0.08 * fine, 0.53 + 0.07 * fine, 0.41 + 0.05 * fine])
        earth = np.where((noise > 0.62)[..., None], earth * 0.88, earth)
        colour = colour * (1 - trodden[..., None]) + earth * trodden[..., None]
    lanes = np.clip(1.0 - (street_distance(u, v) - 2.8) / 1.4, 0, 1) * city
    colour = colour * (1 - lanes[..., None]) + np.array([0.79, 0.74, 0.65]) * lanes[..., None]
    road = np.clip(1.0 - (roads - 3.0) / 2.5, 0, 1)
    colour = colour * (1 - road[..., None]) + np.array([0.78, 0.72, 0.60]) * road[..., None]
    water_colour = np.dstack([0.33 + 0.03 * noise, 0.34 + 0.03 * noise, 0.27 + 0.02 * noise])
    colour = np.where(river[..., None], water_colour, colour)
    colour *= (0.94 + 0.12 * noise)[..., None]
    if shadow is not None:
        colour *= (0.72 + 0.28 * shadow)[..., None]
    return np.clip(colour, 0, 1)


def road_distance_grid(xs, ys):
    return np.min([polyline_distance(points, xs, ys) for points in ROADS.values()], axis=0)


def terrain_objects(scene, far_field, features, city, banks, port_zones):
    field = scene.field
    axis = np.linspace(-HALF, HALF, TEXTURE)
    grid_x, grid_y = np.meshgrid(axis, axis)
    colour = terrain_bake(scene, features, city, banks, port_zones, grid_x, grid_y, 11)
    half_tile = HALF / 2
    middle = (field.samples - 1) // 2
    pixels = TEXTURE // 2
    tiles = []
    for row_index, (r0, cy) in enumerate(((0, -half_tile), (middle, half_tile))):
        for column_index, (c0, cx) in enumerate(((0, -half_tile), (middle, half_tile))):
            name = f"terrain_{row_index}{column_index}"
            tile_colour = colour[row_index * pixels:(row_index + 1) * pixels,
                                 column_index * pixels:(column_index + 1) * pixels]
            image = save_pixels(name, tile_colour, os.path.join(CACHE, "textures", f"{name}.jpg"), quality=86)
            material = baked_material(name, image)
            material.use_backface_culling = True
            sub = field.heights[r0:r0 + middle + 1, c0:c0 + middle + 1] - scene.datum
            mesh = grid_mesh(name, sub, half_tile, skirt_depth=20.0)
            mesh.materials.append(material)
            tiles.append(new_object(name, mesh, scene.collection, scene.root("terrain"),
                                    Matrix.Translation((cx, cy, 0.0))))
    detail_terrain(scene, features, city, banks, port_zones, tiles)
    far_resolution = 1024
    far_axis = np.linspace(-FAR_HALF, FAR_HALF, far_resolution)
    far_x, far_y = np.meshgrid(far_axis, far_axis)
    far_river = rings_mask(features, ("Ecoulement naturel",), far_x, far_y)
    far_heights = far_field.sample(far_x, far_y)
    far_gradient_y, far_gradient_x = np.gradient(far_heights, far_axis[1] - far_axis[0])
    far_colour = terrain_colour(far_x, far_y, far_heights, np.hypot(far_gradient_x, far_gradient_y), far_river,
                                np.zeros(far_x.shape), np.full(far_x.shape, 1e6), np.full(far_x.shape, 1e6), 23,
                                far=True)
    far_image = save_pixels("terrain_far", far_colour, os.path.join(CACHE, "textures", "terrain_far.jpg"), quality=84)
    far_material = baked_material("terrain_far", far_image)
    far_cells = rings_mask(features, ("Ecoulement naturel",), far_field.grid_x, far_field.grid_y)
    far_field.heights = np.where(far_cells, np.minimum(far_field.heights, WATER - 0.6), far_field.heights)
    band = (np.abs(far_field.grid_x) < HALF + FAR_SPACING) & (np.abs(far_field.grid_y) < HALF + FAR_SPACING)
    far_field.heights = np.where(band, far_field.heights - 3.0, far_field.heights)
    far_mesh = grid_mesh("terrain_far", far_field.heights - scene.datum, FAR_HALF, ring=(40000.0, 125.0))
    remove_faces_inside(far_mesh, HALF - FAR_SPACING * 0.25)
    far_mesh.materials.append(far_material)
    far_object = new_object("terrain_far", far_mesh, scene.collection, scene.root("terrain"))
    far_object["cast_shadow"] = False


def water_object(scene, river):
    cells = grow(river, 2)
    builder = MeshBuilder()
    rows, columns = river.shape
    axis = np.linspace(-HALF, HALF, rows)
    depth = np.zeros(river.shape)
    inner = river.copy()
    for _ in range(6):
        inner = inner & shifted(inner, 1, 0, True) & shifted(inner, -1, 0, True) & shifted(inner, 0, 1, True) & \
            shifted(inner, 0, -1, True)
        depth += inner
    z = WATER - scene.datum
    index = {}
    for r in range(rows):
        for c in range(columns):
            if cells[max(r - 1, 0):r + 1, max(c - 1, 0):c + 1].any():
                index[(r, c)] = builder.point((axis[c], axis[r], z))
    shades = {}
    for (r, c), vertex in index.items():
        t = min(depth[r, c] / 6.0, 1.0)
        shades[vertex] = (0.96 - 0.16 * t, 0.97 - 0.12 * t, 0.9 - 0.08 * t)
    for r in range(rows - 1):
        for c in range(columns - 1):
            if not cells[r, c]:
                continue
            quad = [index.get((r, c)), index.get((r, c + 1)), index.get((r + 1, c + 1)), index.get((r + 1, c))]
            if None in quad:
                continue
            builder.face(quad, "river_water")
            builder.polygon_colors[-1] = shades[quad[0]]
    mesh = builder.to_mesh("river_water", scene.tiles, ground_occlusion=False)
    created = new_object("river_water", mesh, scene.collection, scene.root("water"))
    created["cast_shadow"] = False
    return int(river.sum())


def road_strip(scene, points, width, step=2.5, lift=0.1, tone=(0.86, 0.81, 0.72)):
    offsets = [-1.0, -0.5, 0.0, 0.5, 1.0]
    rows = [[] for _ in offsets]
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        count = max(int(math.ceil(length / step)), 1)
        last = (x1, y1) == tuple(points[-1])
        for k in range(count + (1 if last else 0)):
            x, y = x0 + dx * length * k / count, y0 + dy * length * k / count
            if abs(x) > HALF - 5 or abs(y) > HALF - 5:
                continue
            for offset, target in zip(offsets, rows):
                px, py = x - dy * offset * width / 2, y + dx * offset * width / 2
                target.append((px, py, scene.ground(px, py) + lift))
    builder = MeshBuilder()
    if len(rows[0]) < 2:
        return builder
    builder.surface(rows, "arena_sand", facing=(0, 0, 1))
    builder.tint(0, tone)
    return builder


def build_roads(scene, main_streets):
    scene.paved = [(points, 2.75) for points in ROADS.values()] + [(points, 2.5) for points in main_streets]
    for name, points in ROADS.items():
        scene.unique("roads", road_strip(scene, points, 5.5), Matrix.Identity(4), occlusion=False)
    for points in main_streets:
        scene.unique("roads", road_strip(scene, points, 5.0, tone=(0.95, 0.92, 0.86)), Matrix.Identity(4),
                     occlusion=False)


def site_frame(scene, x, y, angle, z=None):
    return placement(x, y, scene.ground(x, y) if z is None else z, angle)


def build_forum(scene, levels):
    origin = placement(*SITES["forum"], levels["forum"] - scene.datum, GRID)
    scene.unique("forum", arles_monuments.forum_base(), origin)
    column_frames = []
    for length, frame in arles_monuments.forum_wings():
        wing = origin @ frame
        scene.unique("forum", monuments.portico_wing(length, 8.0, 6.4), wing)
        doors = MeshBuilder()
        door_xs = [float(x) for x in np.arange(-length / 2 + 4.0, length / 2 - 3.0, 6.5)]
        for x in door_xs:
            arles_monuments.wooden_door(doors, x, -7.98, 0.45, 2.0, 3.1, facing=1)
        scene.unique("forum", doors, wing)
        scene.unique("forum", arles_details.portico_ornament(length, 8.0, 6.4, doors=door_xs), wing)
        column_frames.extend(wing @ local for local in monuments.portico_columns(length - 1.0, 3.0, 6.4))
    scene.instances("forum", "forum_column", lambda: column("corinthian", 0.66, 6.4, "medium"), column_frames)
    temple_builder, temple_columns, height, diameter = arles_monuments.temple()
    temple_frame = origin @ placement(-17.0, 0.0, 0.0, -math.pi / 2)
    scene.unique("forum", temple_builder, temple_frame)
    scene.instances("forum", "temple_column", lambda: column("corinthian", diameter, height, "medium"),
                    [temple_frame @ frame for frame in temple_columns], merge=True)
    scene.unique("forum", buildings.altar(3.0, 2.2, 1.4), origin @ placement(1.5, 0.0, 0.02, math.pi / 2))
    for index, x in enumerate((-2.0, 8.0, 18.0, 28.0)):
        for side in (-1, 1):
            kind = "statue_bronze" if (index + side) % 3 else "statue_marble"
            scene.add(kind, origin @ placement(x, side * 19.0, 0.02, 0.0 if side < 0 else math.pi))
    return origin, temple_frame


def build_theatre(scene, levels):
    tx, ty = SITES["theatre"]
    origin = placement(tx, ty, levels["theatre"] - scene.datum, GRID - math.pi / 2)
    cavea, portico, top_z = arles_monuments.theatre_cavea()
    scene.unique("theatre", cavea, origin)
    count = 27
    frames = arles_monuments.ring_frames(arles_monuments.CAVEA, math.pi, math.pi, count)
    width = 2 * arles_monuments.CAVEA * math.sin(math.pi / count / 2) * 1.02
    scene.instances("theatre", "theatre_bay", lambda: arles_monuments.theatre_bay(width),
                    [origin @ frame for frame in frames])
    scene.instances("theatre", "theatre_portico_column", lambda: column("tuscan", 0.42, 3.4, "low"),
                    [origin @ frame for frame in portico], merge=True)
    stage, column_frames, statues, level_heights = arles_monuments.theatre_stage()
    scene.unique("theatre", stage, origin)
    for level, frames_of_level in column_frames.items():
        height = level_heights[level][1]
        tint = arles_monuments.LEVEL_MARBLES[level]
        scene.instances("theatre", f"scaena_column_{level}",
                        lambda height=height, tint=tint: column("corinthian", 0.62 if height > 5 else 0.5, height,
                                                                "low").tint(0, tint),
                        [origin @ frame for frame in frames_of_level])
    sculpted = {}
    for kind, frame in statues:
        if kind not in sculpted:
            sculpted[kind] = arles_life.statue(kind)
        scale = Matrix.Scale(2.1, 4) if kind == "augustus" else Matrix.Identity(4)
        scene.unique("theatre", sculpted[kind], origin @ frame @ scale)
    seats_builder, seats = arles_details.bisellia(16.0, 0.35, arles_monuments.cuneus_ranges())
    scene.unique("theatre", seats_builder, origin)
    scene.proedria = [origin @ placement(x, y, z, turn) for x, y, z, turn in seats]
    court = origin @ placement(0.0, 50.0, 0.0)
    for length, frame in ((60.0, placement(0.0, -25.0, 0.0, 0.0)), (60.0, placement(0.0, 25.0, 0.0, math.pi)),
                          (44.0, placement(30.0, 0.0, 0.0, math.pi / 2)),
                          (44.0, placement(-30.0, 0.0, 0.0, -math.pi / 2))):
        wing = court @ frame
        scene.unique("theatre", monuments.portico_wing(length, 5.0, 4.6), wing)
        scene.instances("theatre", "court_column", lambda: column("tuscan", 0.48, 4.6, "low"),
                        [wing @ local for local in monuments.portico_columns(length - 1.0, 3.4, 4.6)], merge=True)
    garden = MeshBuilder()
    first = len(garden.polygons)
    garden.box((-24.0, -19.0, -0.5), (24.0, 19.0, 0.06), "paving", bottom=False)
    garden.tint(first, (0.95, 0.9, 0.82))
    for bx in (-12.0, 12.0):
        for by in (-9.5, 9.5):
            garden.box((bx - 8.5, by - 5.5, 0.0), (bx + 8.5, by + 5.5, 0.2), "garden_green", bottom=False)
            for k in range(4):
                sx = bx + (-7.0 if k % 2 else 7.0)
                sy = by + (-4.0 if k < 2 else 4.0)
                buildings.garden_shrub(garden, sx, sy, 1.5, k + int(bx + by), "foliage_dark")
    first = len(garden.polygons)
    garden.box((-6.0, -2.6, -0.1), (6.0, 2.6, 0.5), buildings.ASHLAR, bottom=False)
    garden.tint(first, (0.86, 0.83, 0.78))
    first = len(garden.polygons)
    garden.box((-5.6, -2.2, 0.3), (5.6, 2.2, 0.38), "matte", bottom=False)
    garden.tint(first, (0.24, 0.3, 0.3))
    scene.unique("theatre", garden, court)
    return origin, top_z


def ellipse_point(a, b, t):
    return a * math.cos(t), b * math.sin(t)


def arena_frame(scene, levels):
    cx, cy = SITES["arena"]
    angle = math.radians(90.0 - ARENA_BEARING)
    return cx, cy, angle, levels["arena"] - scene.datum


def build_arena(scene, levels):
    cx, cy, angle, z = arena_frame(scene, levels)
    a, b = ARENA_AXES
    angles, perimeter = buildings.ellipse_arc_angles(a, b, 60)
    bay_width = perimeter / 60
    frames = []
    for t in angles:
        px, py = ellipse_point(a, b, t)
        nx, ny = math.cos(t) / a, math.sin(t) / b
        rotation = math.atan2(ny, nx) - math.pi / 2
        wx, wy = rotate(px, py, angle)
        frames.append(placement(cx + wx, cy + wy, z, rotation + angle))
    scene.instances("arena", "arena_bay", lambda: arles_monuments.arena_bay(bay_width * 1.01), frames)
    cavea = buildings.amphitheatre_cavea(34.5, 20.0, a - 6.3, b - 6.3, arles_monuments.ATTIC_TOP - 1.0)
    arles_crowds.crowd_carpet(arles_monuments.weather(cavea, 29, low=4.0), 31, 4.0, 15.0)
    scene.unique("arena", cavea, placement(cx, cy, z, angle))
    scene.unique("arena", urban.velum(a - 1.0, b - 1.0, 34.5, 20.0, arles_monuments.MAST_TOP - 2.0,
                                      arles_monuments.ATTIC_TOP + 0.4, angles), placement(cx, cy, z, angle),
                 occlusion=False)
    ring = arena_ring(APRON + 2.0, 110)
    terrace_walls(scene, ring + ring[:1], z, (cx, cy))
    west = min(range(60), key=lambda index: frames[index].translation.x)
    scene.arena_bays = frames
    scene.arena_west_t = angles[west]
    return frames[west], angles[west]


def wall_pieces(points, step):
    pieces = []
    travelled = 0.0
    for a, b in zip(points[:-1], points[1:]):
        a, b = Vector((*a, 0.0)), Vector((*b, 0.0))
        length = (b - a).length
        n = max(int(round(length / step)), 1)
        for k in range(n):
            start = a + (b - a) * (k / n)
            end = a + (b - a) * ((k + 1) / n)
            pieces.append((start, end, travelled + length * (k + 0.5) / n))
        travelled += length
    return pieces


def build_walls(scene, levels):
    pieces = wall_pieces(WALL_TRACE, 5.0)
    holes = [(SITES["gate"], 24.0)] + [(gate, 14.5) for gate in SECONDARY_GATES]
    frames = []
    towers = []
    next_tower = 40.0
    for start, end, along in pieces:
        middle = (start + end) / 2
        if any((Vector((*center, 0.0)) - middle).length < width for center, width in holes):
            continue
        direction = (end - start).normalized()
        normal = Vector((-direction.y, direction.x, 0.0))
        rotation = math.atan2(normal.y, normal.x) - math.pi / 2
        z = max(scene.ground(point.x, point.y) for point in (start, middle, end)) - 0.3
        frames.append(placement(middle.x, middle.y, z, rotation, ((end - start).length / 5.0 + 0.02, 1.0, 1.0)))
        if along >= next_tower and not any((Vector((*center, 0.0)) - middle).length < width + 14.0
                                           for center, width in holes):
            centre = middle + normal * 3.0
            samples = [scene.ground(middle.x, middle.y)] + [
                scene.ground(centre.x + 5.5 * math.cos(k * math.pi / 3), centre.y + 5.5 * math.sin(k * math.pi / 3))
                for k in range(6)]
            towers.append(placement(middle.x, middle.y, max(samples) - 0.3, rotation))
            next_tower = along + 62.0
    scene.instances("walls", "wall_curtain", lambda: arles_monuments.weather(
        buildings.curtain_wall(5.0, 2.2, 7.6, 8.0, arles_monuments.ROUGH), 31), frames)
    scene.instances("walls", "wall_tower", lambda: arles_monuments.weather(
        buildings.round_tower(5.5, 13.5, 3.0, 8.0, arles_monuments.ROUGH, 14), 37), towers)
    gx, gy = SITES["gate"]
    outward = Vector((ROADS["aurelia"][1][0] - gx, ROADS["aurelia"][1][1] - gy)).normalized()
    gate_angle = math.atan2(-outward.x, outward.y)
    gate_frame = placement(gx, gy, levels["gate"] - scene.datum, gate_angle)
    scene.unique("gates", arles_details.recast(arles_monuments.augustus_gate(),
                                               {"paving": (arles_monuments.ASHLAR, (0.9, 0.88, 0.84))}), gate_frame)
    gate_frames = {"auguste": gate_frame}
    for index, ((x, y), road) in enumerate(zip(SECONDARY_GATES, (ROADS["ernaginum"], ROADS["circus"]))):
        heading = Vector((road[1][0] - road[0][0], road[1][1] - road[0][1])).normalized()
        gate_frames[f"secondary_{index}"] = placement(x, y, scene.ground(x, y) - 0.1, math.atan2(-heading.x,
                                                                                                 heading.y))
    scene.instances("gates", "gate_secondary", lambda: arles_monuments.weather(
        buildings.secondary_gate(arles_monuments.ROUGH), 41),
        [gate_frames[f"secondary_{index}"] for index in range(len(SECONDARY_GATES))])
    return gate_frames, {"curtain_pieces": len(frames), "towers": len(towers)}


def build_circus(scene, circus):
    origin = placement(circus.center[0], circus.center[1], CIRCUS_LEVEL - scene.datum, circus.angle)
    parts, bay_frames, statue_frames, top = arles_monuments.circus()
    for name, builder in parts.items():
        scene.unique("circus", builder, origin, occlusion=name != "track")
    scene.instances("circus", "circus_bay", lambda: arles_monuments.circus_bay(4.6, top),
                    [origin @ frame for frame in bay_frames])
    scene.circus_bays = [(origin @ frame, frame) for frame in bay_frames]
    for index, frame in enumerate(statue_frames):
        scene.add("statue_bronze" if index % 2 else "statue_marble", origin @ frame)
    return origin


ROW_VARIANTS = 4
HOUSES = {f"row_{index}": (lambda index=index: urban.row_template(index + 51)) for index in range(ROW_VARIANTS)}
HOUSES.update({f"row_tabernae_{index}": (lambda index=index: urban.row_template(151 + index, tabernae=True))
               for index in range(2)})
PLASTERED = {"matte": ("plaster", None)}
HOUSES.update({
    "domus_a": lambda: arles_details.recast(urban.domus(61, 32.0, 30.0, 13.0, 12.0, 6.5, "plaster_white"), PLASTERED),
    "domus_b": lambda: arles_details.recast(urban.domus(62, 28.0, 32.0, 11.0, 14.0, 6.0, "plaster_ochre"), PLASTERED),
    "domus_c": lambda: arles_details.recast(urban.domus(63, 30.0, 28.0, 12.0, 11.0, 6.8, "plaster_rose"), PLASTERED),
    "house_single_a": lambda: arles_details.recast(urban.single_house(71), PLASTERED),
    "house_single_b": lambda: arles_details.recast(urban.single_house(72, 12.0, 8.0), PLASTERED),
    "kitchen_garden": lambda: arles_details.recast(urban.kitchen_garden(81), PLASTERED),
    "horreum_long": lambda: arles_monuments.horreum(42.0, 14.0, 7.0, 3, portico=True, wall="plaster_cream"),
    "horreum_short": lambda: arles_monuments.horreum(28.0, 12.0, 6.5, 4, True, wall="plaster_ochre"),
})


def relief(scene, x, y, radius):
    probe = [scene.ground(x + dx, y + dy) for dx in (-radius, radius) for dy in (-radius, radius)]
    return probe, max(probe) - min(probe)


def build_city(scene, exclusions, city, rng):
    placements = {key: [] for key in HOUSES}
    rows_dense = []
    depth = 11.0
    corners = [to_grid(x, y) for x, y in city]
    u_min, u_max = min(u for u, _ in corners), max(u for u, _ in corners)
    v_min, v_max = min(v for _, v in corners), max(v for _, v in corners)

    socles = {}

    def accept(x, y):
        return point_in_polygon(x, y, city) and not exclusions.blocked(x, y)

    for bi in range(int((u_min - U_OFFSET) // PITCH) - 1, int((u_max - U_OFFSET) // PITCH) + 1):
        for bj in range(int((v_min - V_OFFSET) // PITCH) - 1, int((v_max - V_OFFSET) // PITCH) + 1):
            u0 = U_OFFSET + bi * PITCH + STREET / 2
            v0 = V_OFFSET + bj * PITCH + STREET / 2
            span = PITCH - STREET
            rows = [
                (u0 + span * 0.25, v0 + 0.6 + depth / 2, 0.0), (u0 + span * 0.75, v0 + 0.6 + depth / 2, 0.0),
                (u0 + span * 0.25, v0 + span - 0.6 - depth / 2, math.pi),
                (u0 + span * 0.75, v0 + span - 0.6 - depth / 2, math.pi),
                (u0 + 0.6 + depth / 2, v0 + span / 2, -math.pi / 2),
                (u0 + span - 0.6 - depth / 2, v0 + span / 2, math.pi / 2),
            ]
            for cu, cv, turn in rows:
                main = abs(cv - V_OFFSET) < 12 or abs(cu - U_OFFSET) < 12
                key = f"row_tabernae_{rng.integers(0, 2)}" if (main or rng.random() < 0.18) else \
                    f"row_{rng.integers(0, ROW_VARIANTS)}"
                x, y = from_grid(cu, cv)
                z = seat_on_ground(scene, key, x, y, GRID + turn, accept, socles)
                if z is None:
                    continue
                placements[key].append(placement(x, y, z, GRID + turn))
                rows_dense.append((x, y, z, key))
            x, y = from_grid(u0 + span / 2, v0 + span / 2)
            roll = rng.random()
            key = "domus_a" if roll < 0.35 else "domus_b" if roll < 0.65 else "domus_c" if roll < 0.9 else \
                "kitchen_garden"
            angle = GRID + rng.integers(0, 4) * math.pi / 2
            z = seat_on_ground(scene, key, x, y, angle, accept, socles)
            if z is not None:
                placements[key].append(placement(x, y, z, angle))
    for key, matrices in placements.items():
        scene.house(key, matrices)
    place_socles(scene, "city", socles)
    return {key: len(matrices) for key, matrices in placements.items()}, rows_dense


def build_trinquetaille(scene, right_bank, exclusions, rng):
    placements = {"domus_a": [], "domus_b": [], "domus_c": [], "row_0": [], "row_1": [], "row_tabernae_0": [],
                  "house_single_a": [], "kitchen_garden": [], "horreum_long": [], "horreum_short": []}
    bank = [point for point in right_bank if -260 < point[1] < 470]
    bank_line = smooth_line(bank)
    occupied = []
    grove = []
    socles = {}

    def accept(x, y):
        return not exclusions.blocked(x, y)

    for u in np.arange(-900.0, 900.0, 46.0):
        for v in np.arange(-900.0, 900.0, 46.0):
            ju, jv = rng.uniform(-3.5, 3.5), rng.uniform(-3.5, 3.5)
            x, y = rotate(u + ju, v + jv, TRINQUETAILLE_GRID)
            x += -700.0
            y += 180.0
            if abs(x) > HALF - 40 or abs(y) > HALF - 40:
                continue
            nearest = min(math.hypot(x - bx, y - by) for bx, by in bank_line)
            side = min(bank_line, key=lambda point: math.hypot(x - point[0], y - point[1]))
            if x > side[0] - 20.0 or nearest > 330.0 or nearest < 80.0:
                continue
            if rng.random() < 0.12:
                continue
            north = y > 230.0
            if north and nearest < 200.0 and rng.random() < 0.22:
                key = "horreum_short"
            else:
                roll = rng.random()
                key = ("domus_a" if roll < 0.28 else "domus_b" if roll < 0.5 else "domus_c" if roll < 0.68 else
                       "row_tabernae_0" if roll < 0.76 else f"row_{rng.integers(0, 2)}" if roll < 0.86 else
                       "kitchen_garden" if roll < 0.93 else "house_single_a")
            if key.startswith("horreum"):
                angle = TRINQUETAILLE_GRID + rng.integers(0, 2) * math.pi
            else:
                angle = TRINQUETAILLE_GRID + rng.integers(0, 4) * math.pi / 2
            if rng.random() < 0.12 and not key.startswith("horreum"):
                if not exclusions.blocked(x, y):
                    for _ in range(3):
                        grove.append((x + rng.uniform(-12, 12), y + rng.uniform(-12, 12)))
                continue
            z = seat_on_ground(scene, key, x, y, angle, accept, socles)
            if z is None:
                continue
            placements[key].append(placement(x, y, z, angle))
            occupied.append((x, y))
    for key, matrices in placements.items():
        scene.house(key, matrices)
    place_socles(scene, "trinquetaille", socles)
    return {key: len(value) for key, value in placements.items()}, occupied, grove


def warehouse_rows(scene, line, inland, rng, exclusions, socles, avoid):
    frames = {"horreum_long": [], "horreum_short": []}
    length = polyline_length(line)
    along = 20.0
    while along < length - 20.0:
        key = "horreum_long" if rng.random() < 0.6 else "horreum_short"
        size = 42.0 if key == "horreum_long" else 28.0
        (x, y), (dx, dy) = polyline_point(line, along + size / 2)
        normal = Vector((-dy, dx)) * inland
        center = Vector((x, y)) + normal * (28.5 if key == "horreum_long" else 25.0)
        angle = math.atan2(dy, dx) + (math.pi if inland < 0 else 0.0)
        clear = (center - avoid).length > size / 2 + 12.0
        z = seat_on_ground(scene, key, center.x, center.y, angle, lambda px, py: not exclusions.blocked(px, py),
                           socles) if clear else None
        if z is not None:
            frames[key].append(placement(center.x, center.y, z, angle, (1.0, 1.0, rng.uniform(0.82, 1.1))))
        along += size + rng.uniform(2.0, 6.0)
    return frames


def build_port(scene, left_bank, right_bank, rng, main_streets):
    quays = []
    zones = {"left": smooth_line([p for p in left_bank if -60 < p[1] < 330]),
             "right": smooth_line([p for p in right_bank if -200 < p[1] < 460])}
    deck = QUAY + 0.12 - scene.datum
    for name, line in zones.items():
        inland = -1.0 if name == "left" else 1.0
        inner = offset_line(line, 8.0 * inland)
        outer = offset_line(line, -4.0 * inland)
        builder = MeshBuilder()
        steps = len(inner) - 1
        for index in range(steps):
            shade = 0.86 + 0.14 * ((index * 7919) % 13) / 12.0
            first = len(builder.polygons)
            builder.surface([[(x, y, deck) for x, y in inner[index:index + 2]],
                             [(x, y, deck) for x, y in outer[index:index + 2]]], arles_monuments.PLANK,
                            facing=(0, 0, 1))
            builder.tint(first, (0.95 * shade, 0.9 * shade, 0.84 * shade))
        coping = offset_line(line, -3.3 * inland)
        first = len(builder.polygons)
        builder.surface([[(x, y, deck + 0.07) for x, y in coping], [(x, y, deck + 0.07) for x, y in outer]],
                        arles_monuments.ASHLAR, facing=(0, 0, 1))
        builder.surface([[(x, y, deck + 0.07) for x, y in coping], [(x, y, deck - 0.02) for x, y in coping]],
                        arles_monuments.ASHLAR, facing=tuple(Vector((inner[1][0] - outer[1][0],
                                                                     inner[1][1] - outer[1][1], 0.0))))
        builder.tint(first, (0.62, 0.6, 0.56))
        face = [[(x, y, deck) for x, y in outer], [(x, y, WATER - scene.datum - 1.2) for x, y in outer]]
        first = len(builder.polygons)
        normal = Vector((outer[1][0] - inner[1][0], outer[1][1] - inner[1][1], 0.0))
        builder.surface(face, arles_monuments.ASHLAR, facing=tuple(normal))
        builder.tint(first, (0.48, 0.45, 0.4))
        scene.unique("port_low", builder, Matrix.Identity(4), occlusion=False)
        quays.append((name, line, inner, outer))
    jetties = []
    piles = []
    moorings = []
    for name, line, inner, outer in quays:
        length = polyline_length(outer)
        inland = -1.0 if name == "left" else 1.0
        for along in np.arange(30.0, length - 20.0, 58.0 if name == "left" else 72.0):
            (x, y), (dx, dy) = polyline_point(outer, float(along))
            out = Vector((dy, -dx)) * inland
            angle = math.atan2(-out.x, out.y)
            jetties.append(placement(x - out.x * 1.0, y - out.y * 1.0, deck, angle))
            moorings.append((x, y, dx, dy, out, name, float(along), length, outer))
        for along in np.arange(2.0, length, 6.0):
            (x, y), _ = polyline_point(outer, float(along))
            piles.append(placement(x, y, deck - 0.3, rng.uniform(0, 6.28)))
    scene.instances("port", "jetty", lambda: arles_monuments.jetty(18.0, 4.0), jetties, cast_shadow=True)
    streets = Exclusions()
    for points in ROADS.values():
        streets.polyline(points, 7.0)
    for points in main_streets:
        streets.polyline(points, 5.0)
    warehouses = {"horreum_long": [], "horreum_short": []}
    socles = {}
    for name, line, inner, outer in quays:
        rows = warehouse_rows(scene, line, -1.0 if name == "left" else 1.0, rng, streets, socles,
                              port_view(quays, deck, scene.datum)[0].to_2d())
        for key in warehouses:
            warehouses[key].extend(rows[key])
    for key, matrices in warehouses.items():
        scene.house(key, matrices)
    place_socles(scene, "port", socles)
    scene.instances("port", "quay_pile", arles_monuments.pile, piles, cast_shadow=False)
    return quays, moorings, deck


def build_necropolis(scene, exclusions, rng):
    tombs = {"tomb_enclosure": [], "tomb_mausoleum": [], "tomb_stele": [], "tomb_altar": []}
    cypresses = []
    for road, reach, start in ((ROADS["aurelia"], 420.0, 45.0), (ROADS["nemausus"], 220.0, 60.0)):
        travelled = start
        total = min(reach, polyline_length(road) - 10)
        while travelled < total:
            (x0, y0), (dx, dy) = polyline_point(road, travelled)
            for side in (-1, 1):
                if rng.random() < 0.35:
                    continue
                offset = 7.0 + rng.uniform(0, 6)
                x, y = x0 - dy * side * offset, y0 + dx * side * offset
                if exclusions.blocked(x, y):
                    continue
                angle = math.atan2(dy, dx) + (math.pi / 2 if side > 0 else -math.pi / 2)
                roll = rng.random()
                key = ("tomb_stele" if roll < 0.35 else "tomb_enclosure" if roll < 0.62 else "tomb_altar"
                       if roll < 0.85 else "tomb_mausoleum")
                half, foundation = TOMB_SIZES[key]
                heights = [scene.ground(px, py) for px, py in footprint_points(x, y, angle, half, half)]
                if max(heights) - min(heights) > foundation - 0.1:
                    continue
                tombs[key].append(placement(x, y, max(heights) - 0.08, angle))
                if rng.random() < 0.3:
                    cypresses.append((x - dy * side * 5.0, y + dx * side * 5.0))
            travelled += rng.uniform(7.0, 12.0)
    scene.instances("necropolis", "tomb_enclosure", buildings.funerary_enclosure, tombs["tomb_enclosure"])
    scene.instances("necropolis", "tomb_mausoleum", buildings.mausoleum, tombs["tomb_mausoleum"])
    scene.instances("necropolis", "tomb_stele", buildings.funerary_stele, tombs["tomb_stele"], cast_shadow=False)
    scene.instances("necropolis", "tomb_altar", buildings.tomb_altar, tombs["tomb_altar"], cast_shadow=False)
    return sum(len(value) for value in tombs.values()), cypresses


def build_vegetation(scene, exclusions, city, banks, river, cypresses, occupied, rng, grove):
    field = scene.field
    distances = np.minimum(polyline_distance(banks[0], field.grid_x, field.grid_y),
                           polyline_distance(banks[1], field.grid_x, field.grid_y))
    inside = fast_polygon(city, field.grid_x, field.grid_y)
    taken = np.zeros(river.shape, dtype=bool)
    for ox, oy in occupied:
        column = int(np.clip(round((ox + HALF) / SPACING), 0, field.samples - 1))
        row = int(np.clip(round((oy + HALF) / SPACING), 0, field.samples - 1))
        taken[max(row - 2, 0):row + 3, max(column - 2, 0):column + 3] = True

    def cell(x, y):
        column = int(np.clip(round((x + HALF) / SPACING), 0, field.samples - 1))
        row = int(np.clip(round((y + HALF) / SPACING), 0, field.samples - 1))
        return row, column

    def is_river(x, y):
        return bool(river[cell(x, y)])

    def bank_distance(x, y):
        return float(distances[cell(x, y)])

    def open_land(x, y, margin=12.0):
        index = cell(x, y)
        if river[index] or inside[index] or taken[index]:
            return False
        return not exclusions.blocked(x, y)

    def scatter(count, accept, attempts=25):
        points = []
        tries = 0
        while len(points) < count and tries < count * attempts:
            tries += 1
            x, y = rng.uniform(-HALF + 30, HALF - 30), rng.uniform(-HALF + 30, HALF - 30)
            if accept(x, y):
                points.append((x, y))
        return points

    riparian = scatter(900, lambda x, y: 6.0 < bank_distance(x, y) < 70.0 and open_land(x, y)
                       and rng.random() < 1.2 - bank_distance(x, y) / 70.0)
    marsh = scatter(500, lambda x, y: field.sample(x, y) < WATER + 1.4 and bank_distance(x, y) > 30
                    and open_land(x, y))
    reed_edges = scatter(400, lambda x, y: 0.0 < bank_distance(x, y) < 9.0 and not is_river(x, y)
                         and open_land(x, y, 6.0))
    pines = scatter(70, lambda x, y: open_land(x, y, 30.0) and bank_distance(x, y) > 90 and
                    field.sample(x, y) > WATER + 2.0)
    olives = []
    vines = []
    for bi in range(-14, 15):
        for bj in range(-24, 25):
            u0, v0 = bi * 120.0, bj * 70.0
            cx, cy = from_grid(u0 + 60.0, v0 + 35.0)
            if abs(cx) > HALF - 70 or abs(cy) > HALF - 70:
                continue
            parcel = ((bi * 73856093) ^ (bj * 19349663)) % 1000 / 1000.0
            if field.sample(cx, cy) < WATER + 1.6 or not open_land(cx, cy, 40.0) or bank_distance(cx, cy) < 80:
                continue
            if 0.9 < parcel < 0.97:
                for i in range(11):
                    for j in range(6):
                        x, y = from_grid(u0 + 6 + i * 10.5, v0 + 6 + j * 10.5)
                        if open_land(x, y, 10.0):
                            olives.append((x, y))
            elif 0.46 < parcel < 0.53 and math.hypot(cx, cy) < 1100:
                for j in range(0, 30, 2):
                    for i in range(10):
                        x, y = from_grid(u0 + 7.0 + i * 11.0, v0 + 1.4 + j * 2.3)
                        if open_land(x, y, 10.0):
                            vines.append(grounded(scene, x, y, GRID, 0.3, 5.0, -0.15, scene.ground))

    def frames(points, scale=(0.8, 1.2), sink=0.3, reach=0.8, dry=True):
        out = []
        for x, y in points:
            low = min(scene.ground(x + dx * reach, y + dy * reach) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if dry and min(scene.ground(x + dx * 3.0, y + dy * 3.0) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) < 0.3:
                continue
            out.append(placement(x, y, min(low, scene.ground(x, y)) - sink, rng.uniform(0, 2 * math.pi),
                                 rng.uniform(*scale)))
        return out

    if len(olives) > 600:
        olives = [olives[int(index)] for index in rng.choice(len(olives), 600, replace=False)]
    poplars = [point for index, point in enumerate(riparian) if index % 3 == 0]
    willows = [point for index, point in enumerate(riparian) if index % 3 == 1]
    ashes = [point for index, point in enumerate(riparian) if index % 3 == 2]
    scene.instances("vegetation", "tree_poplar", lambda: arles_details.recast(riparian_tree("poplar", 1),
                                                                              {"plaster": ("matte", None)}),
                    frames(poplars, (0.85, 1.2)))
    scene.instances("vegetation", "tree_willow", lambda: riparian_tree("willow", 2), frames(willows))
    scene.instances("vegetation", "tree_ash", lambda: riparian_tree("ash", 3), frames(ashes))
    scene.instances("vegetation", "reed_clump", lambda: arles_monuments.reeds(5), frames(marsh + reed_edges,
                                                                                         (0.8, 1.5), 0.1, 1.2, False),
                    cast_shadow=False)
    pines = pines + grove[0::2]
    olives = olives + grove[1::2]
    scene.instances("vegetation", "tree_pine", lambda: buildings.umbrella_pine(13.0, 5), frames(pines))
    scene.instances("vegetation", "tree_cypress", lambda: buildings.cypress(11.0, 4), frames(cypresses, (0.85, 1.2)))
    scene.instances("vegetation", "tree_olive", lambda: buildings.olive_tree(4.6, 3), frames(olives, (0.8, 1.15)),
                    cast_shadow=False)
    scene.instances("vegetation", "vine_row", lambda: buildings.vine_row(10.0), vines, cast_shadow=False)
    return {"poplar": len(poplars), "willow": len(willows), "ash": len(ashes), "reeds": len(marsh) + len(reed_edges),
            "pine": len(pines), "cypress": len(cypresses), "olive": len(olives), "vine_rows": len(vines)}


def riparian_tree(kind, seed):
    builder = MeshBuilder()
    rng = np.random.default_rng(seed)
    if kind == "poplar":
        buildings.trunk(builder, 9.0, 0.3, (0.3, 0.1), "plaster_grey")
        lobes = [((0.2, 0.1, 13.0), 3.6, 9.0), ((1.2, -0.6, 9.5), 2.6, 5.5), ((-1.0, 0.8, 10.5), 2.8, 6.0),
                 ((0.0, 0.0, 16.5), 2.4, 5.0)]
        material = "foliage_olive"
    elif kind == "willow":
        buildings.trunk(builder, 3.2, 0.32, (0.6, 0.2))
        lobes = [((0.6, 0.2, 5.8), 4.2, 5.4), ((-1.8, 0.6, 5.0), 3.2, 4.4), ((1.6, -1.6, 4.8), 3.0, 4.0)]
        material = "foliage_olive"
    else:
        buildings.trunk(builder, 6.0, 0.28, (0.4, 0.2))
        lobes = [((0.4, 0.2, 9.0), 4.4, 6.0), ((-2.4, 0.4, 7.6), 3.0, 4.2), ((2.0, -1.8, 7.8), 3.0, 4.0),
                 ((0.0, 0.0, 11.6), 2.8, 3.6)]
        material = "foliage_plane"
    for index, (center, radius, height) in enumerate(lobes):
        first = len(builder.polygons)
        buildings.lobe(builder, center, radius, height, material, 7, seed + index)
        shade = 0.78 + 0.22 * (center[2] / max(lobe[0][2] for lobe in lobes)) + float(rng.uniform(-0.05, 0.05))
        builder.tint(first, (shade, shade * 1.02, shade * 0.95))
    return builder


CITIZENS = [("fig_citizen", 1.4), ("fig_orator", 0.5), ("fig_pallium", 2.2), ("fig_paenula", 1.2),
            ("fig_matron", 2), ("fig_lady", 1.5), ("fig_merchant", 1.2), ("fig_child", 1), ("fig_woman_jar", 0.6),
            ("fig_worker", 0.8), ("fig_vendor", 0.5)]
COMMONERS = [("fig_worker", 3), ("fig_porter_sack", 1.5), ("fig_woman_jar", 2), ("fig_rural", 1.5),
             ("fig_merchant", 1), ("fig_child", 1.5), ("fig_lady", 1), ("fig_pallium", 0.8), ("fig_paenula", 0.8),
             ("fig_traveller", 1), ("fig_vendor", 1)]
DOCKERS = [("fig_porter_amphora", 4), ("fig_porter_sack", 3), ("fig_worker", 2), ("fig_sailor", 2),
           ("fig_merchant", 1)]


def pick(rng, weights):
    total = sum(weight for _, weight in weights)
    roll = rng.random() * total
    chosen = weights[-1][0]
    for key, weight in weights:
        roll -= weight
        if roll <= 0:
            chosen = key
            break
    variant = chosen + "_b"
    if variant in arles_life.PEOPLE and rng.random() < 0.5:
        return variant
    return chosen


def facing(x, y, tx, ty):
    return math.atan2(-(tx - x), ty - y)


def cluster(scene, rng, x, y, count, weights, z=None):
    for index in range(count):
        angle = 2 * math.pi * index / max(count, 1) + rng.uniform(-0.3, 0.3)
        radius = rng.uniform(0.6, 1.0) if count > 1 else 0.0
        px, py = x + radius * math.cos(angle), y + radius * math.sin(angle)
        turn = facing(px, py, x, y) if count > 1 else rng.uniform(0, 2 * math.pi)
        level = scene.floor(px, py) if z is None else z
        scene.add(pick(rng, weights), placement(px, py, level, turn + rng.uniform(-0.3, 0.3)))


def grounded(scene, x, y, angle, half_length, half_width, lift=0.0, height=None):
    height = height or scene.floor
    forward = Vector((-math.sin(angle), math.cos(angle)))
    side = Vector((math.cos(angle), math.sin(angle)))
    front = height(x + forward.x * half_length, y + forward.y * half_length)
    back = height(x - forward.x * half_length, y - forward.y * half_length)
    left = height(x - side.x * half_width, y - side.y * half_width)
    right = height(x + side.x * half_width, y + side.y * half_width)
    pitch = math.atan2(front - back, 2 * half_length)
    roll = math.atan2(right - left, 2 * half_width)
    z = (front + back + left + right) / 4 + lift
    return (Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle, 4, "Z") @ Matrix.Rotation(pitch, 4, "X")
            @ Matrix.Rotation(-roll, 4, "Y"))


FORUM_SPOTS = ((20.0, 6.0), (20.0, -6.0), (31.0, 1.0), (12.0, 2.6), (14.0, 2.6), (16.0, 2.6), (27.0, 8.0))


def forum_life(scene, rng, origin):
    level = origin.translation.z + 0.02
    for _ in range(22):
        for _attempt in range(40):
            x, y = rng.uniform(-1.0, 40.0), rng.uniform(-20.0, 20.0)
            if ((abs(x - 1.5) > 6.0 or abs(y) > 5.6) and abs(abs(y) - 19.0) > 2.0
                    and math.hypot(x - 40.0, y + 12.0) > 10.0 and math.hypot(x - 41.0, y - 9.0) > 7.0
                    and all(math.hypot(x - px, y - py) > 3.0 for px, py in FORUM_SPOTS)):
                break
        point = origin @ Vector((x, y, 0.0))
        cluster(scene, rng, point.x, point.y, int(rng.integers(1, 5)), CITIZENS, level)
    for index, x in enumerate((6.0, 14.0, 22.0, 30.0, 38.0)):
        for side in (-1, 1):
            if (index + side) % 2:
                continue
            frame = origin @ placement(x, side * 15.5, 0.02, -side * math.pi / 2)
            scene.add("market_stall_a" if index % 2 else "market_stall_b", frame)
            point = origin @ Vector((x, side * 13.9, 0.0))
            cluster(scene, rng, point.x, point.y, int(rng.integers(1, 3)), COMMONERS, level)
    for length, frame in arles_monuments.forum_wings():
        wing = origin @ frame
        columns = monuments.portico_columns(length - 1.0, 3.0, 6.4)
        for left, right in zip(columns[:-1], columns[1:]):
            if rng.random() > 0.22:
                continue
            middle = (left.translation + right.translation) / 2
            seat = wing @ placement(middle.x + rng.uniform(-0.4, 0.4), 0.5, 0.45)
            scene.add(pick(rng, SPECTATORS), seat)
    for local, turn in (((20.0, 6.0), 0.0), ((20.0, -6.0), math.pi), ((31.0, 1.0), math.pi / 2)):
        frame = origin @ placement(local[0], local[1], 0.02, turn)
        scene.unique("life_static", arles_details.mensa(int(local[0] + local[1])), frame)
        for side in (-0.7, 0.7):
            point = frame @ Vector((side, 1.15, 0.0))
            scene.add(pick(rng, CITIZENS), placement(point.x, point.y, level, facing(point.x, point.y, frame.translation.x,
                                                                                     frame.translation.y)))
    scene.unique("life_static", arles_details.litter(1), origin @ placement(14.0, 2.5, 0.02, -math.pi / 2 + 0.1))
    point = origin @ Vector((27.0, 8.0, 0.0))
    cluster(scene, rng, point.x, point.y, 4, [("fig_child", 1)], level)
    altar = origin @ Vector((1.5, 0.0, 0.0))
    for local in ((4.2, 0.0), (4.8, 1.8), (4.8, -1.8)):
        point = origin @ Vector((*local, 0.0))
        scene.add("fig_magistrate", placement(point.x, point.y, level, facing(point.x, point.y, altar.x, altar.y)))
    for side in (-1, 1):
        point = origin @ Vector((3.4, side * 1.5, 0.0))
        scene.add("fig_child", placement(point.x, point.y, level, facing(point.x, point.y, altar.x, altar.y)))
    for index in range(14):
        angle = math.radians(-70 + 140 * index / 13)
        radius = 6.8 + (index % 2) * 1.2
        point = origin @ Vector((1.5 + radius * math.cos(angle), radius * math.sin(angle), 0.0))
        scene.add(pick(rng, CITIZENS), placement(point.x, point.y, level, facing(point.x, point.y, altar.x, altar.y)))
    return origin @ Vector((1.5, 0.0, 2.2))


def theatre_life(scene, rng, origin, top_z, eye):
    for index in range(14):
        angle = rng.uniform(math.pi * 1.05, math.pi * 1.95)
        radius = rng.uniform(54.0, 57.0)
        point = origin @ Vector((radius * math.cos(angle), radius * math.sin(angle), 0.0))
        cluster(scene, rng, point.x, point.y, int(rng.integers(1, 4)), COMMONERS)
    variants, instances, uniques, detailed = arles_crowds.theatre_crowd(arles_crowds.eye_local(origin, eye))
    for name, matrices in instances.items():
        scene.instances("theatre", name, lambda name=name: variants[name], [origin @ m for m in matrices],
                        cast_shadow=False, occlusion=False)
    for builder in uniques:
        scene.unique("theatre", builder, origin, occlusion=False)
    for x, y, z, turn in detailed:
        point = origin @ Vector((x, y, z))
        scene.add(pick(rng, SPECTATORS), placement(point.x, point.y, point.z, turn + GRID - math.pi / 2))
    for matrix in scene.proedria:
        scene.add("fig_seated_toga", matrix)
    for x in (-6.0, -2.0, 3.0, 8.0, -10.0, 12.0):
        point = origin @ Vector((x, 3.6 + abs(x) * 0.05, 1.35))
        scene.add(pick(rng, [("fig_orator", 2), ("fig_lady", 1), ("fig_citizen", 1), ("fig_matron", 1)]),
                  placement(point.x, point.y, point.z, facing(point.x, point.y, origin.translation.x,
                                                              origin.translation.y)))
    return sum(len(value) for value in instances.values()), len(uniques), len(detailed)


def arena_life(scene, rng, levels):
    cx, cy, angle, z = arena_frame(scene, levels)
    a, b = ARENA_AXES
    for index in range(8):
        t = 2 * math.pi * (index + 0.5) / 8 + 0.2
        px, py = ellipse_point(a + 10.0, b + 10.0, t)
        wx, wy = rotate(px, py, angle)
        x, y = cx + wx, cy + wy
        scene.add("market_stall_a" if index % 2 else "market_stall_b",
                  placement(x, y, scene.floor(x, y), facing(x, y, cx, cy) + math.pi))
    for index in range(56):
        t = rng.uniform(0, 2 * math.pi) if index < 24 else scene.arena_west_t + rng.uniform(-0.9, 0.9)
        grow_by = rng.uniform(2.5, 11.0)
        px, py = ellipse_point(a + grow_by, b + grow_by, t)
        wx, wy = rotate(px, py, angle)
        cluster(scene, rng, cx + wx, cy + wy, int(rng.integers(1, 5)), COMMONERS if index % 3 else CITIZENS)
    for index in range(10):
        t = scene.arena_west_t + rng.uniform(-0.7, 0.7)
        px, py = ellipse_point(a + 1.6, b + 1.6, t)
        wx, wy = rotate(px, py, angle)
        key = ("animal_dog" if index % 5 == 0 else "fig_child" if index % 2 else
               ["fig_vendor", "fig_woman_jar_b", "fig_merchant"][index % 3])
        scene.add(key, placement(cx + wx, cy + wy, scene.floor(cx + wx, cy + wy), rng.uniform(0, 6.28)))


def port_life(scene, rng, quays, moorings, deck, boats, view):
    eye, target = view
    eye_xy = eye.to_2d()
    sight_end = eye_xy + (target.to_2d() - eye_xy).normalized() * 110.0
    props = {key: [] for key in PROPS}
    spots = []
    for name, line, inner, outer in quays:
        length = polyline_length(inner)
        inland = -1.0 if name == "left" else 1.0
        for along in np.arange(12.0, length - 10.0, 14.0):
            (x, y), (dx, dy) = polyline_point(inner, float(along))
            normal = Vector((-dy, dx)) * inland
            spot = Vector((x, y)) + normal * rng.uniform(1.5, 7.0)
            key = ["amphora_pile", "amphora_stand", "sack_pile", "barrel_group", "block_pile"][int(rng.integers(0, 5))]
            if rng.random() < 0.08:
                key = "crane"
                spot = Vector((x, y)) + normal * 2.0
            if segment_distance(spot, eye_xy, sight_end) < PROP_CLEARANCE[key] + (8.0 if key == "crane" else 1.5):
                continue
            heading = math.atan2(-dy, dx) if key != "crane" else math.atan2(normal.x, -normal.y)
            props[key].append(grounded(scene, spot.x, spot.y, heading, 1.2, 1.2))
            spots.append((spot, PROP_CLEARANCE[key]))

    def clear(point):
        return all((point - spot).length > radius + 0.6 for spot, radius in spots)

    def stand(point):
        for name, line, inner, outer in quays:
            if min((point - Vector(p)).length for p in inner) + min((point - Vector(p)).length for p in outer) < 12.6:
                return deck
        return scene.floor(point.x, point.y)

    sight = eye_xy + (target.to_2d() - eye_xy).normalized() * 45.0
    berths = [index for index, mooring in enumerate(moorings) if mooring[5] == "left" and mooring[6] + 38.0 < mooring[7]]
    front = min(berths, key=lambda index: (Vector(polyline_point(moorings[index][8], moorings[index][6] + 29.0)[0])
                                           - sight).length) if berths else -1
    for index, (x, y, dx, dy, out, name, along_m, length, outer) in enumerate(moorings):
        along = Vector((dx, dy))
        heading = math.atan2(-along.x, along.y)
        roll = rng.random()
        if (index % 3 != 0 or index == front) and along_m + 38.0 < length:
            center = Vector((x, y)) + along * 29.0 + out * 5.5
            boats["ship" if name == "left" else "barge_sacks"].append(
                placement(center.x, center.y, WATER - scene.datum - (0.9 if name == "left" else -0.05), heading))
            if name == "left":
                landing = center + along * -1.3 - out * 6.9
                if index == front:
                    for key, (o, a_) in (("amphora_stand", (1.8, 3.2)), ("sack_pile", (3.4, -3.6)),
                                         ("amphora_pile", (6.5, 4.5)), ("barrel_group", (7.0, -4.0))):
                        spot = landing - out * o + along * a_
                        props[key].append(placement(spot.x, spot.y, deck, heading + rng.uniform(-0.3, 0.3)))
                        spots.append((spot, PROP_CLEARANCE[key]))
                for k in range(3):
                    point = landing - out * (1.4 + 1.5 * k) + along * rng.uniform(-0.3, 0.3)
                    if clear(point):
                        scene.add(["fig_porter_amphora", "fig_porter_amphora_b", "fig_porter_sack"][k],
                                  placement(point.x, point.y, deck, math.atan2(out.x, -out.y)))
                scene.add("fig_merchant", placement(*(landing - out * 2.0 + along * 2.2), deck,
                                                    math.atan2(along.x, -along.y)))
            for k in range(int(rng.integers(1, 3))):
                (px, py), _ = polyline_point(outer, along_m + 29.0 + rng.uniform(-9.0, 9.0))
                point = Vector((px, py)) - out * rng.uniform(1.5, 9.0)
                if clear(point):
                    scene.add(pick(rng, DOCKERS), placement(point.x, point.y, deck,
                                                            heading + math.pi / 2 * (1 if k % 2 else -1)))
        key = ["barge_blocks", "barge_amphorae", "barge_sacks", "barge_barrels"][int(roll * 4)]
        center = Vector((x, y)) + out * 21.0 + along * rng.uniform(-6, 6)
        barge = placement(center.x, center.y, WATER - scene.datum + 0.05, heading + rng.uniform(-0.05, 0.05))
        boats[key].append(barge)
        scene.add("fig_boatman", barge @ placement(0.0, -11.8, 0.10))
        for k in range(int(rng.integers(1, 3))):
            point = Vector((x, y)) + out * rng.uniform(2.0, 16.0) + along * rng.uniform(-1.2, 1.2)
            scene.add(pick(rng, DOCKERS), placement(point.x, point.y, deck,
                                                    heading + (math.pi / 2 if k % 2 else -math.pi / 2)))
    for spot, radius in list(spots):
        if rng.random() < 0.5:
            continue
        direction = rng.uniform(0, 2 * math.pi)
        point = spot + Vector((math.cos(direction), math.sin(direction))) * (radius + rng.uniform(0.9, 1.8))
        if clear(point):
            scene.add(pick(rng, DOCKERS), placement(point.x, point.y, stand(point),
                                                    facing(point.x, point.y, spot.x, spot.y)))
    name, line, inner, outer = next(quay for quay in quays if quay[0] == "left")
    start = polyline_length(inner) * 0.55 - 15.0
    for _ in range(9):
        lane = offset_line(line, rng.uniform(-6.5, 1.5))
        (px, py), (dx, dy) = polyline_point(lane, start + rng.uniform(0.0, 60.0))
        point = Vector((px, py))
        if clear(point):
            scene.add(pick(rng, DOCKERS), placement(px, py, deck, math.atan2(-dx, dy) + rng.choice([0.0, math.pi])))
    for k, key in enumerate(("cart_amphorae", "cart_sacks", "cart_barrels", "cart_sacks")):
        (px, py), (dx, dy) = polyline_point(line, start + 40.0 + 21.0 * k)
        point = Vector((px, py)) + Vector((dy, -dx)) * rng.uniform(11.5, 13.5)
        if clear(point):
            scene.add(key, grounded(scene, point.x, point.y, math.atan2(-dx, dy) + (math.pi if k % 2 else 0.0),
                                    2.2, 0.8))
            spots.append((point, 2.4))
    for key, matrices in props.items():
        scene.instances("port", key, PROPS[key], matrices,
                        cast_shadow=key in ("crane", "amphora_stand", "amphora_pile", "barrel_group", "sack_pile"))
    return {key: len(value) for key, value in props.items()}


def river_traffic(scene, rng, left_bank, right_bank, moving):
    middle = [((lx + rx) / 2, (ly + ry) / 2) for (lx, ly), (rx, ry) in zip(left_bank, right_bank)]
    middle = smooth_line(middle, 4)
    length = polyline_length(middle)
    for index, along in enumerate((160.0, 420.0, 760.0, 1040.0)):
        if along > length - 40:
            continue
        (x, y), (dx, dy) = polyline_point(middle, along)
        offset = (-1 if index % 2 else 1) * rng.uniform(20.0, 55.0)
        px, py = x - dy * offset, y + dx * offset
        heading = math.atan2(-dx, dy) + (math.pi if index % 2 else 0.0)
        barge = placement(px, py, WATER - scene.datum + 0.05, heading)
        moving["barge_amphorae" if index % 2 else "barge_blocks"].append(barge)
        scene.add("fig_boatman", barge @ placement(0.0, -11.8, 0.10))
    for along in (520.0, 600.0):
        (x, y), (dx, dy) = polyline_point(middle, along)
        offset = rng.uniform(-60.0, 60.0)
        moving["ferry"].append(placement(x - dy * offset, y + dx * offset, WATER - scene.datum + 0.18,
                                         math.atan2(-dy, -dx)))
    for along in (300.0, 680.0, 900.0, 1150.0, 470.0, 820.0):
        if along > length - 20:
            continue
        (x, y), (dx, dy) = polyline_point(middle, along)
        offset = rng.uniform(-90.0, 90.0)
        moving["skiff"].append(placement(x - dy * offset, y + dx * offset, WATER - scene.datum + 0.18,
                                         rng.uniform(0, 6.28)))
    for along, side in ((250.0, 1), (640.0, -1), (980.0, 1)):
        if along > length - 40:
            continue
        (x, y), (dx, dy) = polyline_point(middle, along)
        offset = side * rng.uniform(25.0, 45.0)
        heading = math.atan2(-dx, dy) + (0.0 if side > 0 else math.pi)
        moving["ship_sail"].append(placement(x - dy * offset, y + dx * offset, WATER - scene.datum - 0.9, heading))
    return middle


def towing(scene, rng, halage):
    if halage is None:
        return 0
    bank, path = halage
    (x, y), (dx, dy) = polyline_point(bank, 120.0)
    outward = Vector((dy, -dx))
    barge_center = Vector((x, y)) + outward * 28.0
    heading = math.atan2(-dx, dy)
    barge = placement(barge_center.x, barge_center.y, WATER - scene.datum + 0.05, heading)
    scene.add("barge_towed", barge)
    scene.add("fig_boatman", barge @ placement(0.0, -11.8, 0.10))
    mast = barge_center + Vector((dx, dy)) * (31.0 / 2 - 31.0 / 3)
    (hx, hy), _ = polyline_point(offset_line(bank, 9.2), 160.0)
    rope = MeshBuilder()
    start = Vector((mast.x, mast.y, WATER - scene.datum + 5.0))
    end = Vector((hx, hy, scene.ground(hx, hy) + 1.3))
    arles_life.tube(rope, start, end, 0.02, 0.02, (0.45, 0.38, 0.28), 3, caps=False)
    scene.unique("life_static", rope, Matrix.Identity(4), occlusion=False)
    haulers = offset_line(bank, 9.2)
    for k in range(4):
        (px, py), _ = polyline_point(haulers, 160.0 + k * 1.6)
        scene.add("fig_hauler", placement(px, py, scene.floor(px, py), heading))
    return 1


def street_life(scene, rng, rows_dense, main_streets):
    for index, (points, along) in enumerate(((main_streets[0], 60.0), (main_streets[1], 140.0))):
        if polyline_length(points) < along + 5:
            continue
        (x, y), (dx, dy) = polyline_point(points, along)
        px, py = x - dy * 2.1, y + dx * 2.1
        scene.unique("life_static", arles_details.litter(index + 2, [(0.55, 0.16, 0.14), (0.3, 0.36, 0.5)][index]),
                     grounded(scene, px, py, math.atan2(-dx, dy), 1.5, 0.5, 0.0))
    for points in main_streets:
        length = polyline_length(points)
        for along in np.arange(10.0, length - 5.0, 9.0):
            if rng.random() < 0.7:
                continue
            (x, y), (dx, dy) = polyline_point(points, float(along))
            side = float(rng.choice([-1.0, 1.0]))
            offset = rng.uniform(1.7, 2.3)
            px, py = x - dy * side * offset, y + dx * side * offset
            roll = rng.random()
            if roll < 0.07:
                heading = math.atan2(-dx, dy) + (math.pi if rng.random() < 0.5 else 0.0)
                scene.add("pack_mule", grounded(scene, px, py, heading, 0.6, 0.3))
                scene.add("fig_rural", placement(px + dx * 1.4, py + dy * 1.4, scene.floor(px + dx * 1.4,
                                                                                            py + dy * 1.4), heading))
            elif roll < 0.12:
                scene.add("animal_dog", placement(px, py, scene.floor(px, py), rng.uniform(0, 6.28)))
            elif roll < 0.4:
                cluster(scene, rng, px, py, int(rng.integers(2, 4)), COMMONERS)
            else:
                scene.add(pick(rng, COMMONERS), placement(px, py, scene.floor(px, py),
                                                          math.atan2(-dx, dy) + (math.pi if rng.random() < 0.5 else 0)))


def road_life(scene, rng, gate_frames):
    road = ROADS["aurelia"]
    for key, along, lane in (("cart_amphorae", 60.0, -2.2), ("cart_barrels", 180.0, 2.2), ("cart_sacks", 330.0, -2.2),
                             ("pack_mule", 120.0, 2.1), ("pack_donkey", 250.0, -2.1)):
        (x, y), (dx, dy) = polyline_point(road, along)
        heading = math.atan2(-dx, dy) + (math.pi if lane > 0 else 0.0)
        px, py = x - dy * lane, y + dx * lane
        scene.add(key, grounded(scene, px, py, heading, 1.3, 0.6) if key.startswith("cart") else
                  grounded(scene, px, py, heading, 0.6, 0.3))
    road = ROADS["ernaginum"]
    for key, along, lane in (("cart_sacks", 140.0, 2.2), ("pack_mule", 260.0, -2.1)):
        (x, y), (dx, dy) = polyline_point(road, along)
        heading = math.atan2(-dx, dy) + (math.pi if lane > 0 else 0.0)
        scene.add(key, grounded(scene, x - dy * lane, y + dx * lane, heading, 1.3, 0.6))
    for name in ("aurelia", "ernaginum", "nemausus", "circus"):
        road = ROADS[name]
        length = polyline_length(road)
        for _ in range(int(length / 45)):
            (x, y), (dx, dy) = polyline_point(road, rng.uniform(15.0, length - 5.0))
            lane = rng.choice([-1.0, 1.0]) * rng.uniform(1.6, 2.4)
            px, py = x - dy * lane, y + dx * lane
            scene.add(pick(rng, [("fig_rural", 3), ("fig_traveller", 2), ("fig_porter_sack", 1),
                                 ("fig_woman_jar", 1), ("fig_worker", 1)]),
                      placement(px, py, scene.floor(px, py), math.atan2(-dx, dy) + (math.pi if lane > 0 else 0.0)))
    gate = gate_frames["auguste"]
    for local in ((-5.0, 6.0), (5.5, 4.0), (-2.0, 12.0), (3.0, -8.0), (0.0, 18.0)):
        point = gate @ Vector((local[0], local[1], 0.0))
        scene.add(pick(rng, COMMONERS), placement(point.x, point.y, scene.floor(point.x, point.y),
                                                  rng.uniform(0, 6.28)))


def countryside_life(scene, rng, exclusions, city):
    herd = (920.0, -420.0)
    for _ in range(26):
        x, y = herd[0] + rng.normal(0, 12), herd[1] + rng.normal(0, 12)
        scene.add("animal_sheep", grounded(scene, x, y, rng.uniform(0, 6.28), 0.4, 0.2))
    scene.add("fig_rural", placement(herd[0] + 16, herd[1], scene.floor(herd[0] + 16, herd[1]), 1.0))
    scene.add("animal_dog", placement(herd[0] + 14, herd[1] + 4, scene.floor(herd[0] + 14, herd[1] + 4), 2.0))


def circus_life(scene, rng, circus):
    groups = {name: [] for name in arles_crowds.CIRCUS_BUILDS}
    for world, local in scene.circus_bays:
        groups[arles_crowds.circus_variant(local)].append(world)
    for name, matrices in groups.items():
        scene.instances("circus", name, arles_crowds.CIRCUS_BUILDS[name], matrices, cast_shadow=False,
                        occlusion=False)
    track = CIRCUS_LEVEL - scene.datum + 0.03
    x, y = circus.world(-14.0, -106.0)
    scene.unique("life_static", arles_details.race(5), placement(x, y, track, circus.angle + math.pi))
    for local_x, local_y, faction, seed in ((-12.0, 195.0, "veneta", 21), (11.0, 193.5, "albata", 25)):
        x, y = circus.world(local_x, local_y)
        scene.unique("life_static", arles_details.waiting_team(faction, seed),
                     placement(x, y, track, circus.angle + math.pi + rng.uniform(-0.1, 0.1)))
    for index, (local_x, local_y) in enumerate(((-24.0, 236.0), (-9.0, 239.0), (6.0, 235.0), (21.0, 238.0),
                                                (34.0, 233.0))):
        x, y = circus.world(local_x, local_y)
        heading = circus.angle + (math.pi / 2 if index % 2 else -math.pi / 2)
        scene.unique("life_static", arles_details.led_horse(index), grounded(scene, x, y, heading, 1.0, 0.5))
    for local_x, local_y in ((-20.0, 200.0), (-4.0, 199.0), (16.0, 199.5)):
        x, y = circus.world(local_x, local_y)
        cluster(scene, rng, x, y, 3, [("fig_worker", 2), ("fig_worker_b", 2), ("fig_merchant", 1)], track)
    for _ in range(26):
        local_x = float(rng.choice([-1.0, 1.0])) * rng.uniform(52.0, 60.0)
        local_y = rng.uniform(-170.0, 200.0)
        x, y = circus.world(local_x, local_y)
        cluster(scene, rng, x, y, int(rng.integers(1, 3)), COMMONERS)
    for local_y in (-60.0, 20.0, 90.0):
        x, y = circus.world(rng.uniform(7.0, 12.0), local_y)
        sx, sy = circus.world(0.0, local_y)
        scene.add("fig_woman_jar" if local_y > 0 else "fig_worker", placement(x, y, track, facing(x, y, sx, sy)))


LIFE_BUILDS = {key: (lambda spec=spec: arles_life.person(spec)) for key, spec in arles_life.PEOPLE.items()}
LIFE_BUILDS.update({
    "animal_dog": lambda: arles_life.beast("dog"),
    "animal_sheep": lambda: arles_life.beast("sheep"),
    "pack_mule": lambda: arles_life.pack_beast("mule"),
    "pack_donkey": lambda: arles_life.pack_beast("donkey"),
    "cart_amphorae": lambda: arles_life.cart("amphorae", 1),
    "cart_barrels": lambda: arles_life.cart("barrels", 2),
    "cart_sacks": lambda: arles_life.cart("sacks", 3),
    "market_stall_a": lambda: arles_life.market_stall(0),
    "market_stall_b": lambda: arles_life.market_stall(2, (0.72, 0.36, 0.26)),
    "statue_bronze": lambda: arles_life.statue_on_base("bronze"),
    "statue_marble": lambda: arles_life.statue_on_base("marble"),
    "statue_venus": lambda: arles_life.statue("venus"),
    "statue_niche": lambda: arles_life.statue("marble"),
    "statue_toga": lambda: arles_life.statue("toga"),
    "barge_towed": lambda: arles_life.barge(cargo="blocks", seed=9),
})
BOATS = {
    "ship": lambda: arles_life.seagoing_ship(gangplank=True),
    "ship_sail": lambda: arles_life.seagoing_ship(seed=3, sail="set"),
    "barge_blocks": lambda: arles_life.barge(cargo="blocks", seed=1),
    "barge_amphorae": lambda: arles_life.barge(cargo="amphorae", seed=2),
    "barge_sacks": lambda: arles_life.barge(cargo="sacks", seed=3),
    "barge_barrels": lambda: arles_life.barge(cargo="barrels", seed=4),
    "ferry": lambda: arles_life.ferry(5),
    "skiff": lambda: arles_life.small_boat(6.5, 1.7, [(arles_life.PEOPLE["fig_boatman"], (0.0, -1.6))]),
}
PROPS = {
    "amphora_pile": lambda: arles_life.amphora_pile(3, 6, 1),
    "amphora_stand": lambda: arles_life.standing_amphorae(15, 2),
    "sack_pile": lambda: arles_life.sack_pile(3),
    "barrel_group": lambda: arles_life.barrel_group(4),
    "block_pile": lambda: arles_life.block_pile(5),
    "crane": arles_life.crane,
}


BAKED = ("fig_magistrate", "fig_citizen", "fig_orator", "fig_citizen_b", "fig_vendor", "fig_hauler", "pack_donkey",
         "cart_barrels")


def place_life(scene):
    counts = {}
    for key, matrices in scene.placements.items():
        counts[key] = len(matrices)
        if key in BAKED:
            builder = LIFE_BUILDS[key]()
            for matrix in matrices:
                scene.unique("life_static", builder, matrix, occlusion=False)
            continue
        group = "statues" if key.startswith("statue") else "life"
        figure = key.startswith("fig_")
        scene.instances(group, key, LIFE_BUILDS[key], matrices,
                        cast_shadow=not key.startswith(("animal_sheep", "fig_seated")),
                        occlusion=not figure and not key.startswith(("animal", "pack")))
    return counts


def resample(points, spacing):
    out = [Vector(points[0][:2])]
    for start, end in zip(points[:-1], points[1:]):
        a, b = Vector(start[:2]), Vector(end[:2])
        length = (b - a).length
        count = max(int(math.ceil(length / spacing)), 1)
        for k in range(1, count + 1):
            out.append(a + (b - a) * (k / count))
    return out


def add_route(scene, name, points, lift=0.0, absolute=None, spacing=2.5):
    root = scene.root("life")
    created = 0
    for index, point in enumerate(resample(points, spacing)):
        z = absolute(point) if absolute is not None else scene.floor(point.x, point.y)
        new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation((point.x, point.y, z)))
        created += 1
    scene.route_count += 1
    scene.route_points += created
    return created


def build_markers(scene, origin, theatre_origin, arena_west, circus, quays, deck, levels):
    points = {}
    points["forum"] = (origin @ Vector((41.0, 9.0, 1.7)), origin @ Vector((-10.0, -2.0, 6.0)))
    eye = theatre_origin @ Vector((-22.0, -33.0, 15.0))
    target = theatre_origin @ Vector((2.0, 9.0, 8.0))
    points["theatre"] = (eye, target)
    facade, west_t = arena_west
    cx, cy, angle, arena_z = arena_frame(scene, levels)
    a, b = ARENA_AXES
    best = None
    for step in range(-40, 41):
        t = west_t + step * 0.02
        px, py = ellipse_point(a + 28.0, b + 28.0, t)
        wx, wy = rotate(px, py, angle)
        score = abs(scene.ground(cx + wx, cy + wy) - arena_z) + abs(step) * 0.04
        if best is None or score < best[0]:
            best = (score, t, cx + wx, cy + wy)
    _, eye_t, ex, ey = best
    tx_, ty_ = rotate(*ellipse_point(a, b, eye_t - 0.3), angle)
    points["amphitheatre"] = (Vector((ex, ey, max(scene.floor(ex, ey), arena_z) + 1.7)),
                              Vector((cx + tx_, cy + ty_, arena_z + 9.0)))
    points["port-trinquetaille"] = port_view(quays, deck, scene.datum)
    eye_xy = circus.world(9.0, -160.0)
    target_xy = circus.world(-4.0, 0.0)
    points["cirque"] = (Vector((*eye_xy, CIRCUS_LEVEL - scene.datum + 4.5)),
                        Vector((*target_xy, CIRCUS_LEVEL - scene.datum + 2.0)))
    aim = Vector((-350.0, -60.0, levels["forum"] - scene.datum))
    azimuth = math.radians(225.0)
    eye_xy = aim.to_2d() + Vector((math.sin(azimuth), math.cos(azimuth))) * 820.0
    points["vue-d-ensemble"] = (Vector((eye_xy.x, eye_xy.y, levels["forum"] - scene.datum + 250.0)), aim)
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))
    return points


def port_view(quays, deck, datum):
    left = [quay for quay in quays if quay[0] == "left"][0]
    (x, y), (dx, dy) = polyline_point(left[2], polyline_length(left[2]) * 0.55)
    inland = Vector((-dy, dx)) * -1.0
    eye = Vector((x, y, deck + 7.0)) + inland.to_3d() * 16.0 - Vector((dx, dy, 0.0)) * 25.0
    target = Vector((x, y, WATER - datum)) - inland.to_3d() * 42.0 + Vector((dx, dy, 0.0)) * 60.0
    return eye, target


def site_exclusions(circus, quays, main_streets):
    exclusions = Exclusions()
    exclusions.rectangle(*from_grid(2.4, 0.0), 48.0, 37.0, GRID)
    tx, ty = SITES["theatre"]
    centre = Vector((tx, ty))
    u_axis = Vector((math.cos(GRID), math.sin(GRID)))
    exclusions.circle(tx, ty, 58.0)
    exclusions.rectangle(*(centre + u_axis * 10.0), 14.0, 58.0, GRID)
    exclusions.rectangle(*(centre + u_axis * 50.0), 34.0, 38.0, GRID)
    ax, ay = SITES["arena"]
    a, b = ARENA_AXES
    exclusions.ellipse(ax, ay, a + APRON + 4.0, b + APRON + 4.0, ARENA_BEARING)
    exclusions.circle(*SITES["gate"], 30.0)
    for gate in SECONDARY_GATES:
        exclusions.circle(*gate, 16.0)
    exclusions.rectangle(*circus.center, 72.0, 252.0, circus.angle)
    for points in ROADS.values():
        exclusions.polyline(points, 7.0)
    for points in main_streets:
        exclusions.polyline(points, 3.0)
    exclusions.polyline(WALL_TRACE, 10.0)
    for name, line, inner, outer in quays:
        exclusions.polyline(inner, 30.0)
    return exclusions


def camera_exclusions(exclusions, points):
    for key, (eye, target) in points.items():
        if key in ("vue-d-ensemble", "cirque", "theatre"):
            continue
        exclusions.corridor((eye.x, eye.y), (target.x, target.y), 10.0)
        exclusions.circle(eye.x, eye.y, 14.0)


def main_street_lines():
    decumanus = [from_grid(48.0, V_OFFSET), from_grid(122.0, V_OFFSET), from_grid(122.0, -180.0),
                 from_grid(330.0, -180.0), (392.0, -94.0)]
    cardo = [from_grid(U_OFFSET, -170.0), from_grid(U_OFFSET, -40.0), from_grid(U_OFFSET, 110.0),
             from_grid(U_OFFSET, 230.0)]
    to_arena = [from_grid(U_OFFSET + 3.0, 30.0), from_grid(215.0, 30.0)]
    to_port = [from_grid(-46.0, V_OFFSET), from_grid(-150.0, V_OFFSET), from_grid(-300.0, V_OFFSET),
               from_grid(-430.0, V_OFFSET)]
    return [decumanus, cardo, to_arena, to_port]


def trim_to(points, polygon):
    return [point for point in points if point_in_polygon(point[0], point[1], polygon)]


def build_life(scene, rng, origin, theatre_origin, top_z, levels, quays, moorings, deck, rows_dense, main_streets,
               gate_frames, circus, left_bank, right_bank, farms_points, port_view, halage, views):
    altar_smoke = forum_life(scene, rng, origin)
    crowd_counts = theatre_life(scene, rng, theatre_origin, top_z, views["theatre"][0])
    arena_life(scene, rng, levels)
    boats = {key: [] for key in BOATS}
    prop_counts = port_life(scene, rng, quays, moorings, deck, boats, port_view)
    middle = river_traffic(scene, rng, left_bank, right_bank, boats)
    for key, matrices in boats.items():
        scene.instances("boats", key, BOATS[key], matrices)
    boat_counts = {key: len(value) for key, value in boats.items()}
    towing(scene, rng, halage)
    street_life(scene, rng, rows_dense, main_streets)
    road_life(scene, rng, gate_frames)
    countryside_life(scene, rng, None, None)
    circus_life(scene, rng, circus)
    tufts = ground_detail(scene, rng, quays, circus)
    root = scene.root("life")
    smokes = [altar_smoke]
    near = sorted(rows_dense, key=lambda row: math.hypot(row[0], row[1]))[:300]
    for index in sorted(rng.choice(len(near), min(12, len(near)), replace=False)):
        x, y, z, _ = near[int(index)]
        smokes.append(Vector((x, y, z + 10.5)))
    for x, y in farms_points[:4]:
        smokes.append(Vector((x, y, scene.ground(x, y) + 7.0)))
    for name, line, inner, outer in quays:
        (x, y), _ = polyline_point(inner, polyline_length(inner) * 0.3)
        smokes.append(Vector((x, y, deck + 3.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(SITES["forum"], 45.0), (SITES["theatre"], 60.0), (SITES["arena"], 55.0), (middle[len(middle) // 2],
                                                                                          30.0),
              (middle[len(middle) // 4], 25.0), (circus.center, 40.0), ((900.0, -420.0), 25.0)]
    for index, ((x, y), height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation((x, y, scene.ground(x, y) + height)))
    for index, (key, spec) in enumerate(arles_life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda spec=spec: arles_life.person(spec), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"boats": boat_counts, "props": prop_counts, "smoke_sources": len(smokes), "bird_flocks": len(flocks),
            "walker_variants": len(arles_life.WALKERS), "figures_skipped_near_routes": scene.skipped,
            "theatre_crowd": {"instanced_wedges": crowd_counts[0], "unique_wedges": crowd_counts[1],
                              "near_detailed": crowd_counts[2]}, "tufts": tufts}


def ground_detail(scene, rng, quays, circus):
    random_state = random.Random(int(rng.integers(0, 1 << 30)))
    points = []
    for grow_by, keep in ((APRON + 2.9, 0.4), (APRON + 4.2, 0.2), (0.5, 0.25)):
        ring = arena_ring(grow_by, 260)
        points += arles_details.scatter_line(ring + ring[:1], 2.0, 0.0, random_state, 0.4, keep)
    for side in (-1.0, 1.0):
        points += arles_details.scatter_line(WALL_TRACE, 2.4, side * 1.9, random_state, 0.5, 0.3)
    for name in ("aurelia", "circus", "ernaginum"):
        road = ROADS[name][:3]
        for side in (-1.0, 1.0):
            points += arles_details.scatter_line(road, 2.2, side * 3.4, random_state, 0.6, 0.3)
    tx, ty = SITES["theatre"]
    ring = [(tx + 52.5 * math.cos(t), ty + 52.5 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 120)]
    points += arles_details.scatter_line(ring, 2.0, 0.0, random_state, 0.4, 0.35)
    outline = [circus.world(x, y) for x, y, _ in arles_monuments.circus_outline(arles_monuments.CIRCUS_DEPTH + 1.2)]
    points += arles_details.scatter_line(outline, 2.4, 0.0, random_state, 0.5, 0.3)
    for name, line, inner, outer in quays:
        inland = -1.0 if name == "left" else 1.0
        points += arles_details.scatter_line(inner, 2.0, inland * 1.2, random_state, 0.8, 0.45)
    frames = []
    for x, y in points:
        if abs(x) > HALF - 20 or abs(y) > HALF - 20:
            continue
        z = scene.ground(x, y)
        if z < 0.4:
            continue
        frames.append(placement(x, y, z, random_state.uniform(0, 6.28), random_state.uniform(0.7, 1.4)))
    scene.instances("life", "tuft", arles_details.DETAIL_BUILDS["tuft"], frames, cast_shadow=False, occlusion=False)
    return len(frames)


def farms(scene, exclusions, city, rng):
    points = []
    for _ in range(400):
        x, y = rng.uniform(-HALF + 100, HALF - 100), rng.uniform(-HALF + 100, HALF - 100)
        if point_in_polygon(x, y, city) or exclusions.blocked(x, y) or scene.field.sample(x, y) < WATER + 2.2:
            continue
        if math.hypot(x - SITES["forum"][0], y - SITES["forum"][1]) < 650:
            continue
        if all(math.hypot(x - px, y - py) > 220 for px, py in points):
            points.append((x, y))
        if len(points) >= 9:
            break
    scene.instances("countryside", "farmstead", lambda: arles_details.recast(buildings.farmstead(), PLASTERED),
                    [placement(x, y, min(relief(scene, x, y, 12.0)[0]) - 0.1, GRID + rng.integers(0, 4) * math.pi / 2)
                     for x, y in points])
    return points


def render_previews(options, views):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(views) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.12, aerosol=0.6)
    lamp = sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 7.5, (1.0, 0.72, 0.47), 0.8)
    if hasattr(lamp.data, "shadow_filter_radius"):
        lamp.data.shadow_filter_radius = 2.0
    haze_volume(stage, 45000.0, 700.0, 0.00004, SITE_HAZE, 0.3)
    configure_render(1280, 720, options["samples"], exposure=0.15, volumetric_end=40000.0)
    timings = {}
    lenses = {"vue-d-ensemble": 30.0, "forum": 26.0, "theatre": 24.0, "amphitheatre": 24.0, "port-trinquetaille": 28.0,
              "cirque": 26.0}
    for name in names:
        eye, target = views[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=lenses.get(name, 30.0))
        path = os.path.join(CACHE, "previews", f"{name}.png")
        timings[name] = round(render_still(rig, path), 1)
        print(f"PREVIEW {name} {timings[name]} s", flush=True)
    return timings


APRON = 14.0


DETAIL_BOUNDS = (-330.0, 585.0, -435.0, 480.0)


DETAIL_TEXTURE = 2048


MOBILE = ("fig_", "animal_", "pack_", "cart_", "market_stall")


ROUTE_EXEMPT = ("fig_hauler", "fig_boatman", "fig_seated")


CLEARANCE = {"fig_": 1.5, "cart_": 1.9, "pack_": 1.6, "animal_": 1.6, "market_stall": 2.4}


def arena_ring(grow, count, start=0.0):
    cx, cy = SITES["arena"]
    a, b = ARENA_AXES
    angle = math.radians(90.0 - ARENA_BEARING)
    points = []
    for index in range(count):
        t = start + 2 * math.pi * index / count
        px, py = rotate((a + grow) * math.cos(t), (b + grow) * math.sin(t), angle)
        points.append((cx + px, cy + py))
    return points


def theatre_area():
    tx, ty = SITES["theatre"]
    u_axis = Vector((math.cos(GRID), math.sin(GRID)))
    stage = Vector((tx, ty)) + u_axis * 10.0
    court = Vector((tx, ty)) + u_axis * 50.0
    stage_distance = rectangle_distance(stage.x, stage.y, 12.0, 55.0, GRID)
    court_distance = rectangle_distance(court.x, court.y, 32.0, 36.0, GRID)

    def distance(x, y):
        along = (x - tx) * math.cos(GRID) + (y - ty) * math.sin(GRID)
        disc = np.maximum(np.hypot(x - tx, y - ty) - 59.0, along)
        return np.minimum(np.minimum(disc, stage_distance(x, y)), court_distance(x, y))
    return distance


def terrain_bake(scene, features, city, banks, port_zones, grid_x, grid_y, seed):
    field = scene.field
    heights = surface_height(field, grid_x, grid_y)
    step = grid_x[0, 1] - grid_x[0, 0]
    gradient_y, gradient_x = np.gradient(heights, step)
    slope = np.hypot(gradient_x, gradient_y)
    river = rings_mask(features, ("Ecoulement naturel",), grid_x, grid_y)
    inside = fast_polygon(city, grid_x, grid_y).astype(float)
    roads = road_distance_grid(grid_x, grid_y)
    bank_distance = np.minimum(polyline_distance(banks[0][::4], grid_x, grid_y),
                               polyline_distance(banks[1][::4], grid_x, grid_y))
    shadow = sun_shadow(field, grid_x, grid_y, heights)
    port = np.min([polyline_distance(line[::3], grid_x, grid_y) for line in port_zones], axis=0)
    return terrain_colour(grid_x, grid_y, heights, slope, river, inside, roads, bank_distance, seed, shadow, port=port)


def detail_terrain(scene, features, city, banks, port_zones, tiles):
    x0, x1, y0, y1 = DETAIL_BOUNDS
    axis_x = np.linspace(x0, x1, DETAIL_TEXTURE)
    axis_y = np.linspace(y0, y1, DETAIL_TEXTURE)
    grid_x, grid_y = np.meshgrid(axis_x, axis_y)
    colour = terrain_bake(scene, features, city, banks, port_zones, grid_x, grid_y, 11)
    grain = value_noise(grid_x.shape, 420, 71, 2)
    pebbles = value_noise(grid_x.shape, 900, 73, 1)
    tufts = value_noise(grid_x.shape, 160, 79, 3)
    river = rings_mask(features, ("Ecoulement naturel",), grid_x, grid_y)
    mottle = value_noise(grid_x.shape, 70, 83, 3)
    detail = (0.86 + 0.2 * grain + 0.1 * pebbles) * (0.9 + 0.2 * mottle)
    detail = np.where(river, 1.0, detail)
    colour = colour * detail[..., None]
    green = np.clip((tufts - 0.62) * 4.0, 0.0, 1.0) * (1.0 - fast_polygon(city, grid_x, grid_y)) * (~river)
    colour = colour * (1 - 0.25 * green[..., None]) + np.array([0.42, 0.44, 0.28]) * 0.25 * green[..., None]
    image = save_pixels("terrain_detail", np.clip(colour, 0, 1), os.path.join(CACHE, "textures", "terrain_detail.jpg"),
                        quality=85)
    material = baked_material("terrain_detail", image)
    material.use_backface_culling = True
    scene.tiles["terrain_detail"] = 1.0
    field = scene.field
    c0 = int(round((x0 + HALF) / SPACING))
    c1 = int(round((x1 + HALF) / SPACING))
    r0 = int(round((y0 + HALF) / SPACING))
    r1 = int(round((y1 + HALF) / SPACING))
    builder = MeshBuilder()
    index = {}

    def vertex(c, r):
        if (c, r) not in index:
            x, y = -HALF + c * SPACING, -HALF + r * SPACING
            index[(c, r)] = builder.point((x, y, field.heights[r, c] - scene.datum), 10.0)
        return index[(c, r)]

    def uv(c, r):
        x, y = -HALF + c * SPACING, -HALF + r * SPACING
        return ((x - x0) / (x1 - x0), (y - y0) / (y1 - y0))

    for r in range(r0, r1):
        for c in range(c0, c1):
            corners = [(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)]
            builder.face([vertex(*corner) for corner in corners], "terrain_detail", smooth=True,
                         uvs=[uv(*corner) for corner in corners], raw=True)
    mesh = builder.to_mesh("terrain_detail", scene.tiles, ground_occlusion=False)
    created = new_object("terrain_detail", mesh, scene.collection, scene.root("terrain"))
    created["cast_shadow"] = True
    for tile in tiles:
        offset = tile.matrix_basis.translation
        work = bmesh.new()
        work.from_mesh(tile.data)
        doomed = []
        for face in work.faces:
            centre = face.calc_center_median()
            x, y = centre.x + offset.x, centre.y + offset.y
            if x0 < x < x1 and y0 < y < y1 and abs(face.normal.z) > 0.2:
                doomed.append(face)
        bmesh.ops.delete(work, geom=doomed, context="FACES")
        work.to_mesh(tile.data)
        work.free()
        tile.data.update()


def terrace_walls(scene, points, level, centre, seed=23):
    builder = MeshBuilder()
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        normal = Vector((mx - centre[0], my - centre[1])).normalized()
        outer = [scene.ground(mx + normal.x * d, my + normal.y * d) for d in (0.0, 2.0, 4.0, 7.0, 10.0)]
        inner = [scene.ground(mx - normal.x * d, my - normal.y * d) for d in (1.0, 3.0, 6.0)]
        if max(outer) > level + 0.8:
            top = max(outer) + 0.35
        elif min(outer) < level - 0.8:
            top = max(level, max(inner)) + 0.95
        else:
            continue
        bottom = min(outer + inner + [level]) - 0.8
        length = math.hypot(x1 - x0, y1 - y0) + 0.25
        frame = placement(mx, my, 0.0, math.atan2(y1 - y0, x1 - x0))
        builder.box((-length / 2, -0.6, bottom), (length / 2, 0.6, top), arles_monuments.ROUGH, matrix=frame,
                    bottom=False, top=False)
        builder.box((-length / 2, -0.72, top), (length / 2, 0.72, top + 0.28), buildings.ASHLAR, matrix=frame,
                    bottom=False)
    if builder.polygons:
        scene.unique("terraces", arles_monuments.weather(builder, seed, low=-1000.0), Matrix.Identity(4))
    return len(builder.polygons)


FOOTPRINTS = (("row", 16.0, 5.5, 2.6), ("domus", 16.0, 16.0, 2.6), ("house_single", 7.0, 10.5, 1.2),
              ("kitchen_garden", 14.0, 13.0, 1.2), ("horreum_long", 21.0, 7.5, 2.4), ("horreum_short", 14.0, 6.5, 2.4))


def footprint(key):
    return next((hx, hy, limit) for prefix, hx, hy, limit in FOOTPRINTS if key.startswith(prefix))


def footprint_points(x, y, angle, half_x, half_y, margin=0.0):
    points = []
    for fx in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for fy in (-1.0, -0.5, 0.0, 0.5, 1.0):
            dx, dy = rotate(fx * (half_x + margin), fy * (half_y + margin), angle)
            points.append((x + dx, y + dy))
    return points


SOCLE_PREFIXES = ("row", "domus", "horreum_long", "horreum_short")


def socle_builder(prefix):
    half_x, half_y, _ = footprint(prefix)
    builder = MeshBuilder()
    builder.box((-half_x - 0.3, -half_y - 0.3, -4.0), (half_x + 0.3, half_y + 0.3, 0.0), arles_monuments.ROUGH,
                bottom=False)
    return arles_monuments.weather(builder, 43, low=-10.0)


def seat_on_ground(scene, key, x, y, angle, accept, socles=None):
    half_x, half_y, limit = footprint(key)
    if not all(accept(px, py) for px, py in footprint_points(x, y, angle, half_x, half_y, 1.0)):
        return None
    heights = [scene.ground(px, py) for px, py in footprint_points(x, y, angle, half_x, half_y)]
    relief = max(heights) - min(heights)
    prefix = next((name for name in SOCLE_PREFIXES if key.startswith(name)), None)
    stepped = socles is not None and prefix is not None
    if relief > (4.8 if stepped else limit):
        return None
    z = max(heights) - 0.15
    if stepped and relief > 1.0:
        socles.setdefault(prefix, []).append(placement(x, y, z + 0.06, angle, (1.0, 1.0, (relief + 0.7) / 4.0)))
    return z


def place_socles(scene, group, socles):
    for prefix, matrices in socles.items():
        scene.house(f"socle_{prefix}", matrices)


TOMB_SIZES = {"tomb_enclosure": (4.0, 0.95), "tomb_mausoleum": (2.6, 0.95), "tomb_stele": (0.55, 0.55),
              "tomb_altar": (1.2, 0.75)}


SPECTATORS = [("fig_seated_toga", 1.0), ("fig_seated_tunic", 1.4), ("fig_seated_woman", 1.2)]


PROP_CLEARANCE = {"amphora_pile": 1.6, "amphora_stand": 1.3, "sack_pile": 1.5, "barrel_group": 1.6,
                  "block_pile": 2.8, "crane": 4.2}


def segment_distance(point, start, end):
    direction = end - start
    t = max(0.0, min(1.0, (point - start).dot(direction) / max(direction.length_squared, 1e-9)))
    return (point - start - direction * t).length


def towpath(right_bank):
    bank = smooth_line([p for p in right_bank if -520 < p[1] < -240])
    if len(bank) < 3:
        return None
    return bank, offset_line(bank, 7.0)


def route_specs(scene, origin, theatre_origin, levels, quays, deck, main_streets, circus, halage):
    level = origin.translation.z
    specs = []

    def forum_points(pairs):
        return [tuple((origin @ Vector((x, y, 0.0))).to_2d()) for x, y in pairs]

    specs.append(("forum-centre", forum_points([(6.0, -12.0), (36.0, -12.0), (36.0, 12.0), (6.0, 12.0)]),
                  lambda point: level + 0.02))
    specs.append(("forum-portique-nord", forum_points([(-28.0, 25.6), (37.0, 25.6)]), lambda point: level + 0.45))
    specs.append(("forum-portique-sud", forum_points([(37.0, -25.6), (-28.0, -25.6)]), lambda point: level + 0.45))
    for index, points in enumerate(main_streets):
        specs.append((f"rue-{index}", points, None))
    ring = [tuple((theatre_origin @ Vector((58.0 * math.cos(t), 58.0 * math.sin(t), 0.0))).to_2d())
            for t in np.linspace(math.pi * 1.02, math.pi * 1.98, 30)]
    specs.append(("theatre-ceinture", ring, None))
    cx, cy, angle, arena_z = arena_frame(scene, levels)
    a, b = ARENA_AXES
    for name, (t0, t1) in (("arenes-nord", (0.15, math.pi - 0.15)), ("arenes-sud", (math.pi + 0.15,
                                                                                    2 * math.pi - 0.15))):
        points = []
        for t in np.linspace(t0, t1, 40):
            px, py = ellipse_point(a + 7.0, b + 7.0, t)
            wx, wy = rotate(px, py, angle)
            points.append((cx + wx, cy + wy))
        specs.append((name, points, None))
    for name, line, inner, outer in quays:
        quay_line = offset_line(line, (-3.0 if name == "left" else 3.0))[2:-2]
        specs.append((f"quai-{name}", quay_line, lambda point: deck))
    if halage is not None:
        specs.append(("chemin-de-halage", halage[1], None))
    specs.append(("voie-aurelienne", ROADS["aurelia"][:4], None))
    specs.append(("route-ernaginum", ROADS["ernaginum"][:3], None))
    specs.append(("route-du-cirque", ROADS["circus"], None))
    specs.append(("route-de-nimes", ROADS["nemausus"][:3], None))
    specs.append(("cirque-ouest", [circus.world(-58.0, y) for y in np.linspace(-170.0, 205.0, 20)], None))
    specs.append(("cirque-est", [circus.world(58.0, y) for y in np.linspace(205.0, -170.0, 20)], None))
    return specs


def add_routes(scene, specs):
    for name, points, absolute in specs:
        add_route(scene, name, points, 0.0, absolute)


def main():
    options = arguments()
    if options.get("reuse") == "1":
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        stored = json.loads(bpy.context.scene.get("preview_points", "{}"))
        views = {key: (Vector(eye), Vector(target)) for key, (eye, target) in stored.items()}
        print("PREVIEWS", json.dumps(render_previews(options, views)), flush=True)
        return
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tiles, credits = build_library(CACHE)
    arles_monuments.arles_materials(CACHE, tiles, credits)
    frame = GeoFrame(*ORIGIN)
    features = fetch_hydro(frame, os.path.join(CACHE, "src", "bdtopo_hydro.json"))
    field, far_field, dem_urls = build_terrain(features)
    left_bank, right_bank, fine_water, fine_axis = bank_lines(features)
    city = city_polygon(left_bank)
    circus, circus_shift = place_circus(left_bank, fine_water, fine_axis)
    river = clean_terrain(field, features, city)
    port_zones = [smooth_line([p for p in left_bank if -60 < p[1] < 330]),
                  smooth_line([p for p in right_bank if -200 < p[1] < 460])]
    carve_river(field, river, left_bank, right_bank, city, port_zones)
    levels = flatten_sites(field, circus)
    datum = WATER
    scene = Scene(tiles, field, datum)
    terrain_objects(scene, far_field, features, city, (left_bank, right_bank), port_zones)
    water_cells = water_object(scene, river)
    rng = np.random.default_rng(11)
    origin, temple_frame = build_forum(scene, levels)
    theatre_origin, top_z = build_theatre(scene, levels)
    arena_west = build_arena(scene, levels)
    gate_frames, wall_counts = build_walls(scene, levels)
    circus_origin = build_circus(scene, circus)
    main_streets = [trim_to(points, city) for points in main_street_lines()]
    main_streets = [points for points in main_streets if len(points) >= 2]
    build_roads(scene, main_streets)
    quays, moorings, deck = build_port(scene, left_bank, right_bank, rng, main_streets)
    points = build_markers(scene, origin, theatre_origin, arena_west, circus, quays, deck, levels)
    exclusions = site_exclusions(circus, quays, main_streets)
    camera_exclusions(exclusions, points)
    house_counts, rows_dense = build_city(scene, exclusions, city, rng)
    trinquetaille_counts, occupied, grove = build_trinquetaille(scene, right_bank, exclusions, rng)
    farm_points = farms(scene, exclusions, city, rng)
    tomb_count, cypresses = build_necropolis(scene, exclusions, rng)
    vegetation_counts = build_vegetation(scene, exclusions, city, (left_bank, right_bank), river, cypresses,
                                         occupied + farm_points, rng, grove)
    scene.place_houses()
    halage = towpath(right_bank)
    specs = route_specs(scene, origin, theatre_origin, levels, quays, deck, main_streets, circus, halage)
    scene.avoid_routes([points for _, points, _ in specs])
    life_counts = build_life(scene, rng, origin, theatre_origin, top_z, levels, quays, moorings, deck, rows_dense,
                             main_streets, gate_frames, circus, left_bank, right_bank, farm_points,
                             points["port-trinquetaille"], halage, points)
    add_routes(scene, specs)
    placed = place_life(scene)
    scene.flush()
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    stored = sum(value.get("stored_triangles", 0) for key, value in statistics.items() if key != "total")
    statistics["total"]["stored_triangles"] = stored
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "arles.glb")
    export_seconds = export_glb(glb, roots)
    counts = {"houses": house_counts, "trinquetaille": trinquetaille_counts, "walls": wall_counts,
              "vegetation": vegetation_counts, "tombs": tomb_count, "farms": len(farm_points),
              "life": dict(placed, **life_counts), "walk_routes": scene.route_count,
              "walk_points": scene.route_points, "water_cells": water_cells,
              "static_figures": sum(len(value) for key, value in scene.placements.items() if key.startswith("fig_"))}
    report = {"datum_ngf_metres": datum, "levels_ngf_metres": {key: round(float(value), 2)
                                                               for key, value in levels.items()},
              "circus": {"center": [round(v, 1) for v in circus.center], "bearing_degrees":
                         round((-math.degrees(circus.angle)) % 360, 1), "shift_from_documented_line": circus_shift},
              "sun": [SUN_AZIMUTH, SUN_ELEVATION], "counts": counts, "statistics": statistics,
              "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
              "elevation_sources": dem_urls, "elevation_licence": ETALAB_LICENCE,
              "hydrography": "IGN BD TOPO V3 surface_hydrographique, " + ETALAB_LICENCE,
              "texture_credits": credits,
              "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                          for key, (eye, target) in points.items()}}
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in points.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    report["previews"] = render_previews(options, points)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("levels_ngf_metres", "circus", "counts", "glb_bytes",
                                                              "previews", "total_seconds")}), flush=True)


if __name__ == "__main__":
    main()

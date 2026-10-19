import math
import os
import struct
import urllib.request

import bpy
import numpy as np

from .materials import baked_material, principled_material, save_pixels
from .pont_terrain import grid_mesh
from .terrain import value_noise

TINITALY_WCS = ("http://tinitaly.pi.ingv.it/TINItaly_1_1/wcs?service=WCS&version=2.0.1&request=GetCoverage"
                "&coverageId=TINItaly_1_1__tinitaly_dem&format=image/tiff&subset=E({},{})&subset=N({},{})")
TINITALY_BOX = (1094000, 1110000, 4590000, 4606000)
TINITALY_STEP = 10.0
TINITALY_LICENCE = "CC BY 4.0, Tarquini et al. 2023, TINITALY 1.1, INGV, doi:10.13127/tinitaly/1.1"
NODATA = -1000.0
SEA_LEVEL = 0.0


def utm32(latitude, longitude):
    a = 6378137.0
    f = 1 / 298.257223563
    n = f / (2 - f)
    rectifying = a / (1 + n) * (1 + n * n / 4 + n ** 4 / 64)
    alpha = [n / 2 - 2 * n * n / 3 + 5 * n ** 3 / 16, 13 * n * n / 48 - 3 * n ** 3 / 5, 61 * n ** 3 / 240]
    phi = np.radians(latitude)
    lam = np.radians(longitude) - math.radians(9.0)
    c = 2 * math.sqrt(n) / (1 + n)
    t = np.sinh(np.arctanh(np.sin(phi)) - c * np.arctanh(c * np.sin(phi)))
    xi = np.arctan(t / np.cos(lam))
    eta = np.arctanh(np.sin(lam) / np.sqrt(1 + t * t))
    easting = 500000 + 0.9996 * rectifying * (eta + sum(alpha[j] * np.cos(2 * (j + 1) * xi) * np.sinh(2 * (j + 1) * eta)
                                                           for j in range(3)))
    northing = 0.9996 * rectifying * (xi + sum(alpha[j] * np.sin(2 * (j + 1) * xi) * np.cosh(2 * (j + 1) * eta)
                                               for j in range(3)))
    return easting, northing


def read_tiled_tiff(path):
    data = open(path, "rb").read()
    order = ">" if data[:2] == b"MM" else "<"
    offset = struct.unpack(order + "I", data[4:8])[0]
    count = struct.unpack(order + "H", data[offset:offset + 2])[0]
    tags = {}
    for index in range(count):
        entry = data[offset + 2 + 12 * index:offset + 14 + 12 * index]
        tag, kind, items = struct.unpack(order + "HHI", entry[:8])
        if kind not in (3, 4):
            continue
        size = (2 if kind == 3 else 4) * items
        raw = entry[8:8 + size] if size <= 4 else data[struct.unpack(order + "I", entry[8:12])[0]:][:size]
        tags[tag] = struct.unpack(order + ("H" if kind == 3 else "I") * items, raw)
    width, height = tags[256][0], tags[257][0]
    tile_width, tile_height = tags[322][0], tags[323][0]
    if tags[259][0] != 1 or tags[258][0] != 32:
        raise RuntimeError("expected an uncompressed float32 tiled GeoTIFF")
    result = np.zeros((height, width), np.float32)
    across = (width + tile_width - 1) // tile_width
    for index, (start, length) in enumerate(zip(tags[324], tags[325])):
        tile = np.frombuffer(data[start:start + length], dtype=np.dtype(order + "f4")).reshape(tile_height, tile_width)
        row, column = divmod(index, across)
        y0, x0 = row * tile_height, column * tile_width
        rows, columns = min(tile_height, height - y0), min(tile_width, width - x0)
        result[y0:y0 + rows, x0:x0 + columns] = tile[:rows, :columns]
    return result


def tinitaly(cache_path):
    if not os.path.exists(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        url = TINITALY_WCS.format(*TINITALY_BOX)
        request = urllib.request.Request(url, headers={"User-Agent": "roma-scene-builder/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = response.read()
        if payload[:2] not in (b"MM", b"II"):
            raise RuntimeError(f"TINITALY did not return a GeoTIFF: {payload[:200]!r}")
        with open(cache_path, "wb") as handle:
            handle.write(payload)
    heights = read_tiled_tiff(cache_path)
    return np.where(heights < NODATA, SEA_LEVEL, heights)


class Relief:
    def __init__(self, frame, cache_path):
        self.frame = frame
        self.heights = tinitaly(cache_path)

    def sample(self, xs, ys):
        latitude, longitude = self.frame.to_geo(np.asarray(xs, np.float64), np.asarray(ys, np.float64))
        easting, northing = utm32(latitude, longitude)
        west, east, south, north = TINITALY_BOX
        rows, columns = self.heights.shape
        column = np.clip((easting - west) / TINITALY_STEP - 0.5, 0, columns - 1.001)
        row = np.clip((north - northing) / TINITALY_STEP - 0.5, 0, rows - 1.001)
        c0 = column.astype(int)
        r0 = row.astype(int)
        fx = column - c0
        fy = row - r0
        h = self.heights
        top = h[r0, c0] * (1 - fx) + h[r0, c0 + 1] * fx
        bottom = h[r0 + 1, c0] * (1 - fx) + h[r0 + 1, c0 + 1] * fx
        return top * (1 - fy) + bottom * fy


def densify(points, step):
    result = [np.array(points[0], float)]
    for start, end in zip(points[:-1], points[1:]):
        start = np.array(start, float)
        end = np.array(end, float)
        pieces = max(1, int(np.linalg.norm(end - start) / step))
        result.extend(start + (end - start) * (k / pieces) for k in range(1, pieces + 1))
    return np.array(result)


def chaikin(points, passes=3):
    points = np.asarray(points, float)
    for _ in range(passes):
        quarter = 0.75 * points[:-1] + 0.25 * points[1:]
        three_quarter = 0.25 * points[:-1] + 0.75 * points[1:]
        middle = np.empty((2 * len(quarter), 2))
        middle[0::2] = quarter
        middle[1::2] = three_quarter
        points = np.vstack([points[:1], middle, points[-1:]])
    return points


class River:
    def __init__(self, course, relief, width, depth):
        self.path = densify(chaikin(course), 20.0)
        self.width = width
        self.depth = depth
        samples = np.stack([relief.sample(self.path[:, 0] + dx, self.path[:, 1] + dy)
                            for dx in (-40, 0, 40) for dy in (-40, 0, 40)])
        floor = samples.min(axis=0)
        level = np.minimum.accumulate(floor - 1.0)
        kernel = np.ones(15) / 15
        level = np.convolve(np.pad(level, 7, mode="edge"), kernel, "valid")
        self.level = np.maximum(level, SEA_LEVEL + 0.3)

    def nearest(self, xs, ys):
        best = np.full(np.shape(xs), np.inf)
        level = np.zeros(np.shape(xs))
        for index in range(len(self.path) - 1):
            x0, y0 = self.path[index]
            x1, y1 = self.path[index + 1]
            dx, dy = x1 - x0, y1 - y0
            t = np.clip(((xs - x0) * dx + (ys - y0) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
            distance = np.hypot(xs - (x0 + t * dx), ys - (y0 + t * dy))
            closer = distance < best
            best = np.where(closer, distance, best)
            level = np.where(closer, self.level[index] * (1 - t) + self.level[index + 1] * t, level)
        return best, level

    def carve(self, xs, ys, heights):
        distance, level = self.nearest(xs, ys)
        half = self.width / 2
        channel = level - 0.3 - self.depth * (1 - (np.minimum(distance, half) / half) ** 2)
        bank = level + 0.3 + np.maximum(distance - half - 12, 0) * 0.15
        return np.minimum(heights, np.where(distance < half + 12, channel, bank)), distance


    def surface(self, name):
        tangents = np.gradient(self.path, axis=0)
        tangents /= np.linalg.norm(tangents, axis=1)[:, None]
        normals = np.column_stack([-tangents[:, 1], tangents[:, 0]])
        left = self.path + normals * self.width / 2
        right = self.path - normals * self.width / 2
        count = len(self.path)
        vertices = [(*left[k], self.level[k]) for k in range(count)] + [(*right[k], self.level[k]) for k in range(count)]
        faces = [(k, k + 1, count + k + 1, count + k) for k in range(count - 1)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        return mesh


def smoothstep(edge0, edge1, value):
    t = np.clip((value - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return a * (1 - t[..., None]) + np.asarray(b) * t[..., None]


def ground_pixels(xs, heights, river_distance, seed=7):
    shape = heights.shape
    spacing = abs(xs[1] - xs[0])
    gy, gx = np.gradient(heights, spacing)
    slope = np.hypot(gx, gy)
    parcels = value_noise(shape, 22, seed, octaves=2, persistence=0.4)
    patches = value_noise(shape, 60, seed + 1, octaves=3, persistence=0.55)
    grain = value_noise(shape, 260, seed + 2, octaves=2, persistence=0.6)
    terra_rossa = np.array([0.56, 0.36, 0.24])
    stubble = np.array([0.80, 0.69, 0.45])
    pasture = np.array([0.64, 0.58, 0.38])
    meadow = np.array([0.50, 0.50, 0.31])
    riparian = np.array([0.33, 0.39, 0.21])
    scrub = np.array([0.43, 0.41, 0.29])
    gravel = np.array([0.68, 0.65, 0.57])
    colour = mix(np.broadcast_to(pasture, shape + (3,)).copy(), stubble, smoothstep(0.48, 0.56, parcels))
    colour = mix(colour, terra_rossa, smoothstep(0.55, 0.7, patches) * 0.75)
    colour = mix(colour, meadow, smoothstep(17.0, 11.0, heights) * 0.7)
    colour = mix(colour, scrub, smoothstep(0.08, 0.2, slope))
    colour = mix(colour, riparian, smoothstep(160.0, 40.0, river_distance) * 0.85)
    colour = mix(colour, gravel, smoothstep(40.0, 22.0, river_distance))
    colour *= (0.72 + 0.2 * grain)[..., None]
    return np.clip(colour, 0, 1)


def resample(values, xs, ys, texture_x, texture_y):
    column = np.clip((texture_x - xs[0]) / (xs[1] - xs[0]), 0, len(xs) - 1.001)
    row = np.clip((texture_y - ys[0]) / (ys[1] - ys[0]), 0, len(ys) - 1.001)
    c0 = column.astype(int)[None, :]
    r0 = row.astype(int)[:, None]
    fx = (column - column.astype(int))[None, :]
    fy = (row - row.astype(int))[:, None]
    top = values[r0, c0] * (1 - fx) + values[r0, c0 + 1] * fx
    bottom = values[r0 + 1, c0] * (1 - fx) + values[r0 + 1, c0 + 1] * fx
    return top * (1 - fy) + bottom * fy


def build_ground(relief, river, extent, spacing, texture_path, collection, new_object):
    x0, x1, y0, y1 = extent
    xs = np.arange(x0, x1 + spacing / 2, spacing)
    ys = np.arange(y0, y1 + spacing / 2, spacing)
    grid_x, grid_y = np.meshgrid(xs, ys)
    heights, distance = river.carve(grid_x, grid_y, relief.sample(grid_x, grid_y))
    width = 2048
    height = int(round(width * (y1 - y0) / (x1 - x0)))
    texture_x = np.linspace(x0, x1, width)
    texture_y = np.linspace(y1, y0, height)
    pixels = ground_pixels(texture_x, resample(heights, xs, ys, texture_x, texture_y),
                           resample(distance, xs, ys, texture_x, texture_y))
    image = save_pixels("cannes_ground", pixels[::-1], texture_path)
    material = baked_material("cannes_ground", image, roughness=0.97)
    uv = lambda vx, vy: np.column_stack([(vx - x0) / (x1 - x0), (vy - y0) / (y1 - y0)])
    mesh = grid_mesh("ground", xs, ys, heights, uv=uv, skirt=30.0)
    mesh.materials.append(material)
    ground = new_object("ground", mesh, collection)
    ground["cast_shadow"] = False
    return ground, heights, xs, ys


def build_far_ground(relief, extent, half, spacing, collection, new_object):
    x0, x1, y0, y1 = extent
    xs = np.arange(-half, half + spacing / 2, spacing)
    ys = np.arange(-half, half + spacing / 2, spacing)
    grid_x, grid_y = np.meshgrid(xs, ys)
    heights = relief.sample(grid_x, grid_y) - 2.0
    centre_x = (grid_x[:-1, :-1] + spacing / 2)
    centre_y = (grid_y[:-1, :-1] + spacing / 2)
    keep = ~((centre_x > x0 + spacing) & (centre_x < x1 - spacing) & (centre_y > y0 + spacing) & (centre_y < y1 - spacing))
    colours = np.broadcast_to(np.array([0.62, 0.56, 0.38]), grid_x.shape + (3,))
    mesh = grid_mesh("ground_far", xs, ys, heights, keep=keep, colours=colours)
    mesh.materials.append(principled_material("cannes_far", color=(1.0, 1.0, 1.0), roughness=0.97))
    far = new_object("ground_far", mesh, collection)
    far["cast_shadow"] = False
    return far


def build_water(river, half, collection, new_object):
    material = principled_material("water", color=(0.09, 0.17, 0.17), roughness=0.3, vertex_color=False)
    stream = new_object("river", river.surface("river"), collection)
    stream.data.materials.append(material)
    stream["cast_shadow"] = False
    sea_mesh = bpy.data.meshes.new("sea")
    sea_mesh.from_pydata([(-half, -half, SEA_LEVEL + 0.4), (half, -half, SEA_LEVEL + 0.4), (half, half, SEA_LEVEL + 0.4),
                          (-half, half, SEA_LEVEL + 0.4)], [], [(0, 1, 2, 3)])
    sea_mesh.materials.append(material)
    sea = new_object("sea", sea_mesh, collection)
    sea["cast_shadow"] = False
    return stream, sea

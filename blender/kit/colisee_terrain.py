import math
import os
import struct
import urllib.request

import numpy as np

from .terrain import GeoFrame, HeightField, polyline_distance, value_noise

TINITALY_WCS = ("https://tinitaly.pi.ingv.it/TINItaly_1_1/wcs?service=WCS&version=2.0.1&request=GetCoverage"
                "&coverageId=TINItaly_1_1__tinitaly_dem&format=image/tiff&subset=E({},{})&subset=N({},{})")
TINITALY_BOX = (783600, 795900, 4637400, 4649600)
TINITALY_STEP = 10.0
OUTER_BOX = (749600, 829600, 4603400, 4683400)
OUTER_STEP = 400.0
TINITALY_LICENCE = "CC BY 4.0, Tarquini et al. 2023, TINITALY 1.1, INGV, doi:10.13127/tinitaly/1.1"
ORIGIN = (41.890169, 12.492269)
FRAME = GeoFrame(*ORIGIN)


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


def fetch(url, cache_path):
    if not os.path.exists(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "roma-scene-builder/1.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = response.read()
        if payload[:2] not in (b"MM", b"II"):
            raise RuntimeError(f"TINITALY did not return a GeoTIFF: {payload[:200]!r}")
        with open(cache_path, "wb") as handle:
            handle.write(payload)
    return read_tiled_tiff(cache_path).astype(np.float64)


def tinitaly_outer(cache_path):
    url = TINITALY_WCS.format(*OUTER_BOX) + "&SCALEFACTOR=0.025"
    heights = fetch(url, cache_path)
    heights[heights < -1000] = 0.0
    return dem_sampler(heights, OUTER_BOX, OUTER_STEP), url


def tinitaly(cache_path):
    url = TINITALY_WCS.format(*TINITALY_BOX)
    heights = fetch(url, cache_path)
    invalid = heights < -1000
    if invalid.any():
        heights[invalid] = float(np.median(heights[~invalid]))
    return heights, url


def dem_sampler(heights, box=TINITALY_BOX, step=TINITALY_STEP):
    west, _, _, north = box

    def sample(xs, ys):
        latitude, longitude = FRAME.to_geo(np.asarray(xs, np.float64), np.asarray(ys, np.float64))
        easting, northing = utm32(latitude, longitude)
        rows, columns = heights.shape
        column = np.clip((easting - west) / step - 0.5, 0, columns - 1.001)
        row = np.clip((north - northing) / step - 0.5, 0, rows - 1.001)
        c0 = column.astype(int)
        r0 = row.astype(int)
        fx = column - c0
        fy = row - r0
        top = heights[r0, c0] * (1 - fx) + heights[r0, c0 + 1] * fx
        bottom = heights[r0 + 1, c0] * (1 - fx) + heights[r0 + 1, c0 + 1] * fx
        return top * (1 - fy) + bottom * fy
    return sample


def smooth(values, passes):
    for _ in range(passes):
        padded = np.pad(values, 1, mode="edge")
        values = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] + 4 * values) / 8
    return values


def blend_to(heights, mask_distance, level, margin):
    weight = np.clip(1.0 - mask_distance / margin, 0.0, 1.0)
    weight = weight * weight * (3 - 2 * weight)
    return heights * (1 - weight) + level * weight


def build_fields(cache_dir, edits, near_half, near_spacing, far_half, far_spacing):
    heights, url = tinitaly(os.path.join(cache_dir, "src", "tinitaly_roma.tif"))
    sample = dem_sampler(heights)

    def field(half, spacing, edited):
        samples = int(round(2 * half / spacing)) + 1
        axis = np.linspace(-half, half, samples)
        grid_x, grid_y = np.meshgrid(axis, axis)
        values = smooth(sample(grid_x, grid_y), 2)
        if edited:
            values = edits(grid_x, grid_y, values)
        return HeightField(values, half)
    return field(near_half, near_spacing, True), field(far_half, far_spacing, True), url


def ridge(grid_x, grid_y, heights, points, crest, width):
    distance = polyline_distance(points, grid_x, grid_y)
    profile = np.exp(-(distance / width) ** 2)
    lift = crest * profile
    return np.maximum(heights, heights * (1 - profile) + lift)


def densify(points, step):
    out = []
    for a, b in zip(points[:-1], points[1:]):
        count = max(int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)), 1)
        for k in range(count):
            t = k / count
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    out.append((points[-1][0], points[-1][1]))
    return out


def graded_profile(points, sample, max_grade=0.08, step=5.0, window=60.0):
    dense = densify(points, step)
    raw = np.array([float(sample(x, y)) for x, y in dense])
    lengths = np.concatenate([[0.0], np.cumsum([math.hypot(b[0] - a[0], b[1] - a[1])
                                                for a, b in zip(dense[:-1], dense[1:])])])
    half = max(int(window / step / 2), 1)
    padded = np.pad(raw, half, mode="edge")
    kernel = np.ones(2 * half + 1) / (2 * half + 1)
    levels = np.convolve(padded, kernel, mode="valid")
    levels[0] = raw[0]
    levels[-1] = raw[-1]
    for i in range(1, len(levels)):
        limit = max_grade * (lengths[i] - lengths[i - 1])
        levels[i] = min(max(levels[i], levels[i - 1] - limit), levels[i - 1] + limit)
    for i in range(len(levels) - 2, -1, -1):
        limit = max_grade * (lengths[i + 1] - lengths[i])
        levels[i] = min(max(levels[i], levels[i + 1] - limit), levels[i + 1] + limit)
    return dense, list(levels)


def road_blend(grid_x, grid_y, heights, points, levels, flat, margin):
    distance = np.full(grid_x.shape, np.inf)
    level = np.zeros(grid_x.shape)
    for (a, b), (la, lb) in zip(zip(points[:-1], points[1:]), zip(levels[:-1], levels[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        span = dx * dx + dy * dy
        if span < 1e-9:
            continue
        t = np.clip(((grid_x - a[0]) * dx + (grid_y - a[1]) * dy) / span, 0, 1)
        d = np.hypot(grid_x - (a[0] + t * dx), grid_y - (a[1] + t * dy))
        closer = d < distance
        distance = np.where(closer, d, distance)
        level = np.where(closer, la + (lb - la) * t, level)
    weight = np.clip(1.0 - (distance - flat) / margin, 0.0, 1.0)
    weight = weight * weight * (3 - 2 * weight)
    return heights * (1 - weight) + level * weight


def ground_colour(grid_x, grid_y, heights, slope, paved, seed=17, garden=None):
    shape = grid_x.shape
    noise = value_noise(shape, 12, seed)
    fine = value_noise(shape, 48, seed + 1, octaves=3)
    dry = np.dstack([0.66 + 0.10 * noise, 0.58 + 0.08 * noise, 0.40 + 0.05 * fine])
    green = np.dstack([0.36 + 0.06 * fine, 0.40 + 0.07 * noise, 0.22 + 0.03 * fine])
    city = np.dstack([0.60 + 0.05 * fine, 0.54 + 0.04 * fine, 0.46 + 0.04 * noise])
    steep = np.clip((slope - 0.12) / 0.3, 0.0, 1.0)[..., None]
    vegetation = np.clip(0.35 + 0.6 * (noise - 0.5) + 0.8 * steep[..., 0], 0.0, 1.0)
    if garden is not None:
        vegetation = vegetation * garden
        street = np.dstack([0.52 + 0.05 * fine, 0.47 + 0.04 * fine, 0.40 + 0.04 * noise])
        rubble = np.dstack([0.50 + 0.05 * noise, 0.43 + 0.04 * noise, 0.35 + 0.03 * fine])
        urban = street * (1 - steep) + rubble * steep
        city = city * garden[..., None] + urban * (1 - garden[..., None])
        paved = np.maximum(paved, 0.85 * (1 - garden))
    vegetation = vegetation[..., None]
    colour = dry * (1 - vegetation) + green * vegetation
    colour = colour * (1 - paved[..., None] * 0.85) + city * paved[..., None] * 0.85
    colour *= (0.9 + 0.16 * fine)[..., None]
    return np.clip(colour, 0, 1)

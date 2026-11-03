import heapq
import math
import os

import bpy
import numpy as np

from .cannes_terrain import chaikin, densify
from .materials import baked_material, principled_material, save_pixels
from .pompei_terrain import blur, minimum_filter, smoothstep, world_noise
from .pont_terrain import grid_mesh
from .terrain import ETALAB_LICENCE, RGE_ALTI_LAYER, fetch_lambert_grid, lambert93

CORE_HALF = 7000.0
CORE_STEP = 10.0
FAR_SOURCE_HALF = 22000.0
FAR_SOURCE_STEP = 100.0
SOURCE = {
    "name": "IGN RGE ALTI, couche ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES du service WMS de la Géoplateforme",
    "grids": ["14 km au pas de 10 m autour du Mont Auxois", "44 km au pas de 100 m pour la couronne"],
    "licence": ETALAB_LICENCE,
    "processing": ("plaine des Laumes lissée (talus de la voie ferrée, des routes et du bourg nivelés), rivières "
                   "tracées par écoulement sur le relief puis creusées, aucune image aérienne : texture calculée, "
                   "sans village, route ni MuséoParc"),
}
RIVER_AREA = 7.0e6
FLAT_RELIEF = 9.0
PLAIN_LEVEL = 262.0


def mix(colour, other, weight):
    return colour * (1 - weight[..., None]) + np.asarray(other) * weight[..., None]


def bilinear_lambert(source, xs, ys, frame):
    heights, (west, north, step), _ = source
    latitude, longitude = frame.to_geo(np.asarray(xs, np.float64), np.asarray(ys, np.float64))
    lx, ly = lambert93(latitude, longitude)
    rows, columns = heights.shape
    column = (lx - west) / step - 0.5
    row = (north - ly) / step - 0.5
    inside = (column > 1) & (column < columns - 2) & (row > 1) & (row < rows - 2)
    column = np.clip(column, 0, columns - 1.001)
    row = np.clip(row, 0, rows - 1.001)
    c0 = column.astype(int)
    r0 = row.astype(int)
    fx = column - c0
    fy = row - r0
    top = heights[r0, c0] * (1 - fx) + heights[r0, c0 + 1] * fx
    bottom = heights[r0 + 1, c0] * (1 - fx) + heights[r0 + 1, c0 + 1] * fx
    return top * (1 - fy) + bottom * fy, inside


class Relief:
    def __init__(self, frame, cache_dir):
        self.frame = frame
        self.core = fetch_lambert_grid(frame, CORE_HALF, CORE_STEP, RGE_ALTI_LAYER,
                                       os.path.join(cache_dir, "src", "rge_alti_l93_10m.bil"))
        self.far = fetch_lambert_grid(frame, FAR_SOURCE_HALF, FAR_SOURCE_STEP, RGE_ALTI_LAYER,
                                      os.path.join(cache_dir, "src", "rge_alti_l93_100m.bil"))
        self.urls = [self.core[2], self.far[2]]

    def sample(self, xs, ys):
        near, inside = bilinear_lambert(self.core, xs, ys, self.frame)
        far, _ = bilinear_lambert(self.far, xs, ys, self.frame)
        return np.where(inside, near, far)


def level_plain(heights):
    high = -minimum_filter(-heights, 2)
    low = minimum_filter(heights, 2)
    flat = smoothstep((FLAT_RELIEF - (high - low)) / 4.0) * smoothstep((PLAIN_LEVEL - heights) / 12.0)
    leveled = blur(minimum_filter(heights, 1), 4)
    return heights * (1 - flat) + leveled * flat


def flow_accumulation(heights):
    rows, columns = heights.shape
    filled = heights.copy()
    seen = np.zeros(heights.shape, dtype=bool)
    queue = []
    for r in range(rows):
        for c in (0, columns - 1):
            heapq.heappush(queue, (heights[r, c], r, c))
            seen[r, c] = True
    for c in range(1, columns - 1):
        for r in (0, rows - 1):
            heapq.heappush(queue, (heights[r, c], r, c))
            seen[r, c] = True
    order = []
    neighbours = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    while queue:
        level, r, c = heapq.heappop(queue)
        order.append((r, c))
        for dr, dc in neighbours:
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < columns and not seen[rr, cc]:
                seen[rr, cc] = True
                filled[rr, cc] = max(heights[rr, cc], level + 1e-4)
                heapq.heappush(queue, (filled[rr, cc], rr, cc))
    accumulation = np.ones(heights.shape)
    downstream = -np.ones(heights.shape + (2,), dtype=int)
    for r, c in reversed(order):
        best = None
        for dr, dc in neighbours:
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < columns:
                drop = (filled[r, c] - filled[rr, cc]) / math.hypot(dr, dc)
                if drop > 0 and (best is None or drop > best[0]):
                    best = (drop, rr, cc)
        if best:
            accumulation[best[1], best[2]] += accumulation[r, c]
            downstream[r, c] = (best[1], best[2])
    return accumulation, downstream


def trace_rivers(xs, ys, heights, spacing):
    accumulation, downstream = flow_accumulation(heights)
    river = accumulation * spacing * spacing > RIVER_AREA
    upstream = np.zeros(heights.shape, dtype=bool)
    for r, c in zip(*np.nonzero(river)):
        dr, dc = downstream[r, c]
        if dr >= 0:
            upstream[dr, dc] = True
    heads = [(r, c) for r, c in zip(*np.nonzero(river & ~upstream))]
    heads.sort(key=lambda cell: -heights[cell])
    visited = np.zeros(heights.shape, dtype=bool)
    courses = []
    for r, c in heads:
        cells = []
        while r >= 0:
            cells.append((r, c))
            if visited[r, c]:
                break
            visited[r, c] = True
            r, c = downstream[r, c]
        if len(cells) < 4:
            continue
        points = np.array([(xs[c], ys[r]) for r, c in cells], float)
        areas = np.array([accumulation[r, c] * spacing * spacing for r, c in cells])
        courses.append((points, areas))
    return courses


class River:
    def __init__(self, points, areas, height_at):
        smooth = chaikin(points, 3)
        smooth[0] = points[0]
        smooth[-1] = points[-1]
        self.path = densify(smooth, 12.0)
        distance = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(self.path, axis=0).T))])
        source = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(points, axis=0).T))])
        area = np.interp(distance / max(distance[-1], 1e-6) * source[-1], source, areas)
        self.width = 7.0 + 9.0 * np.sqrt(area / 4.0e8)
        probes = [height_at(self.path[:, 0] + dx, self.path[:, 1] + dy) for dx in (-25, 0, 25) for dy in (-25, 0, 25)]
        floor = np.min(probes, axis=0)
        level = np.minimum.accumulate(floor - 0.5)
        kernel = np.ones(9) / 9
        self.level = np.convolve(np.pad(level, 4, mode="edge"), kernel, "valid")

    def carve(self, gx, gy, heights):
        x0, y0 = self.path.min(axis=0) - 60
        x1, y1 = self.path.max(axis=0) + 60
        window = (gx > x0) & (gx < x1) & (gy > y0) & (gy < y1)
        px, py = gx[window], gy[window]
        best = np.full(px.shape, np.inf)
        level = np.zeros(px.shape)
        half = np.zeros(px.shape)
        for k in range(len(self.path) - 1):
            ax, ay = self.path[k]
            bx, by = self.path[k + 1]
            dx, dy = bx - ax, by - ay
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
            distance = np.hypot(px - (ax + t * dx), py - (ay + t * dy))
            closer = distance < best
            best = np.where(closer, distance, best)
            level = np.where(closer, self.level[k] * (1 - t) + self.level[k + 1] * t, level)
            half = np.where(closer, (self.width[k] * (1 - t) + self.width[k + 1] * t) / 2, half)
        bed = level - 0.4 - 1.4 * (1 - (np.minimum(best, half) / np.maximum(half, 1e-3)) ** 2)
        bank = level + 0.25 + np.maximum(best - half - 10.0, 0) * 0.12
        carved = heights.copy()
        target = np.where(best < half + 10.0, bed, np.where(best < half + 70.0, bank, np.inf))
        carved[window] = np.minimum(heights[window], target)
        distance = np.full(heights.shape, np.inf)
        distance[window] = best
        return carved, distance

    def ribbon(self, builder_vertices, builder_faces):
        tangents = np.gradient(self.path, axis=0)
        tangents /= np.maximum(np.linalg.norm(tangents, axis=1)[:, None], 1e-9)
        normals = np.column_stack([-tangents[:, 1], tangents[:, 0]]) * (self.width[:, None] / 2 + 1.5)
        left = self.path + normals
        right = self.path - normals
        start = len(builder_vertices)
        count = len(self.path)
        builder_vertices.extend((*left[k], self.level[k]) for k in range(count))
        builder_vertices.extend((*right[k], self.level[k]) for k in range(count))
        builder_faces.extend((start + k, start + k + 1, start + count + k + 1, start + count + k) for k in range(count - 1))


def ground_pixels(gx, gy, heights, slope, river_distance, cleared):
    shape = heights.shape
    fields = world_noise(gx, gy, 380.0, 21, octaves=3, persistence=0.55)
    copses = world_noise(gx, gy, 220.0, 22, octaves=4, persistence=0.6)
    grain = world_noise(gx, gy, 35.0, 23, octaves=3, persistence=0.6)
    stubble = np.array([0.74, 0.64, 0.40])
    pasture = np.array([0.55, 0.56, 0.32])
    dry_grass = np.array([0.66, 0.60, 0.38])
    meadow = np.array([0.42, 0.50, 0.26])
    wood = np.array([0.20, 0.27, 0.13])
    autumn = np.array([0.38, 0.34, 0.16])
    scree = np.array([0.62, 0.58, 0.48])
    riparian = np.array([0.28, 0.36, 0.17])
    colour = mix(np.broadcast_to(pasture, shape + (3,)).copy(), dry_grass, smoothstep((fields - 0.42) / 0.12))
    colour = mix(colour, stubble, smoothstep((fields - 0.6) / 0.08) * 0.85)
    colour = mix(colour, meadow, smoothstep((250.0 - heights) / 14.0) * 0.6)
    steep = smoothstep((slope - 0.12) / 0.1)
    woods = np.clip(steep * 0.85 + smoothstep((copses - 0.6) / 0.08) * 0.7, 0, 1) * (1 - cleared)
    woods *= smoothstep((river_distance - 30.0) / 40.0)
    colour = mix(colour, wood, woods)
    colour = mix(colour, autumn, woods * smoothstep((grain - 0.55) / 0.2) * 0.5)
    colour = mix(colour, scree, smoothstep((slope - 0.45) / 0.2) * 0.6)
    colour = mix(colour, riparian, smoothstep((70.0 - river_distance) / 50.0) * 0.8)
    colour *= (0.84 + 0.28 * grain)[..., None]
    return np.clip(colour, 0, 1), woods


def resample(values, xs, ys, tx, ty):
    column = np.clip((tx - xs[0]) / (xs[1] - xs[0]), 0, len(xs) - 1.001)
    row = np.clip((ty - ys[0]) / (ys[1] - ys[0]), 0, len(ys) - 1.001)
    c0 = column.astype(int)[None, :]
    r0 = row.astype(int)[:, None]
    fx = (column - column.astype(int))[None, :]
    fy = (row - row.astype(int))[:, None]
    top = values[r0, c0] * (1 - fx) + values[r0, c0 + 1] * fx
    bottom = values[r0 + 1, c0] * (1 - fx) + values[r0 + 1, c0 + 1] * fx
    return top * (1 - fy) + bottom * fy


def grid_sampler(xs, ys, heights):
    def height_at(x, y):
        column = np.clip((np.asarray(x, float) - xs[0]) / (xs[1] - xs[0]), 0, len(xs) - 1.001)
        row = np.clip((np.asarray(y, float) - ys[0]) / (ys[1] - ys[0]), 0, len(ys) - 1.001)
        c0 = column.astype(int)
        r0 = row.astype(int)
        fx = column - c0
        fy = row - r0
        top = heights[r0, c0] * (1 - fx) + heights[r0, c0 + 1] * fx
        bottom = heights[r0 + 1, c0] * (1 - fx) + heights[r0 + 1, c0 + 1] * fx
        result = top * (1 - fy) + bottom * fy
        return float(result) if np.ndim(result) == 0 else result
    return height_at


def prepare_ground(relief, extent, spacing):
    x0, x1, y0, y1 = extent
    xs = np.arange(x0, x1 + spacing / 2, spacing)
    ys = np.arange(y0, y1 + spacing / 2, spacing)
    gx, gy = np.meshgrid(xs, ys)
    heights = level_plain(relief.sample(gx, gy))
    courses = trace_rivers(xs, ys, heights, spacing)
    sampler = grid_sampler(xs, ys, heights)
    rivers = [River(points, areas, sampler) for points, areas in courses]
    distance = np.full(heights.shape, np.inf)
    for river in rivers:
        heights, reach = river.carve(gx, gy, heights)
        distance = np.minimum(distance, reach)
    return xs, ys, heights, rivers, distance


def build_ground(xs, ys, heights, river_distance, extent, texture_path, painters, collection, new_object):
    x0, x1, y0, y1 = extent
    width = 2048
    height = int(round(width * (y1 - y0) / (x1 - x0)))
    tx = np.linspace(x0, x1, width)
    ty = np.linspace(y1, y0, height)
    gx, gy = np.meshgrid(tx, ty)
    th = resample(heights, xs, ys, tx, ty)
    spacing = abs(tx[1] - tx[0])
    dy, dx = np.gradient(th, spacing)
    slope = np.hypot(dx, dy)
    distance = resample(np.minimum(river_distance, 400.0), xs, ys, tx, ty)
    cleared = np.zeros(th.shape)
    for painter in painters:
        cleared = np.maximum(cleared, painter.clearing(gx, gy, spacing))
    pixels, woods = ground_pixels(gx, gy, th, slope, distance, cleared)
    for painter in painters:
        pixels = painter.paint(pixels, gx, gy, spacing)
    image = save_pixels("alesia_ground", pixels[::-1], texture_path)
    material = baked_material("alesia_ground", image, roughness=0.97)
    uv = lambda vx, vy: np.column_stack([(vx - x0) / (x1 - x0), (vy - y0) / (y1 - y0)])
    mesh = grid_mesh("ground", xs, ys, heights, uv=uv, skirt=30.0)
    mesh.materials.append(material)
    ground = new_object("ground", mesh, collection)
    ground["cast_shadow"] = False
    return ground, (tx, ty, woods)


def build_far_ground(relief, extent, half, spacing, collection, new_object):
    x0, x1, y0, y1 = extent
    xs = np.arange(-half, half + spacing / 2, spacing)
    ys = np.arange(-half, half + spacing / 2, spacing)
    gx, gy = np.meshgrid(xs, ys)
    heights = relief.sample(gx, gy) - 1.5
    cx = gx[:-1, :-1] + spacing / 2
    cy = gy[:-1, :-1] + spacing / 2
    keep = ~((cx > x0 + spacing) & (cx < x1 - spacing) & (cy > y0 + spacing) & (cy < y1 - spacing))
    dy, dx = np.gradient(heights, spacing)
    slope = np.hypot(dx, dy)
    noise = world_noise(gx, gy, 1400.0, 31, octaves=3)
    low = np.array([0.58, 0.56, 0.33])
    wood = np.array([0.22, 0.28, 0.14])
    colours = mix(np.broadcast_to(low, gx.shape + (3,)).copy(), wood,
                  np.clip(smoothstep((slope - 0.08) / 0.08) + smoothstep((noise - 0.6) / 0.1) * 0.6, 0, 1))
    mesh = grid_mesh("ground_far", xs, ys, heights, keep=keep, colours=colours)
    mesh.materials.append(principled_material("alesia_far", color=(1.0, 1.0, 1.0), roughness=0.97))
    far = new_object("ground_far", mesh, collection)
    far["cast_shadow"] = False
    return far


def build_rivers(rivers, ditch, collection, new_object):
    vertices = list(ditch[0])
    faces = list(ditch[1])
    for river in rivers:
        river.ribbon(vertices, faces)
    mesh = bpy.data.meshes.new("river")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(principled_material("river", color=(0.10, 0.17, 0.15), roughness=0.3, vertex_color=False))
    water = new_object("river", mesh, collection)
    water["cast_shadow"] = False
    return water

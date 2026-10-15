import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .terrain import lambert93


class Field:
    def __init__(self, x0, y0, spacing, heights):
        self.x0 = x0
        self.y0 = y0
        self.spacing = spacing
        self.heights = heights
        self.rows, self.columns = heights.shape
        xs = x0 + spacing * np.arange(self.columns)
        ys = y0 + spacing * np.arange(self.rows)
        self.grid_x, self.grid_y = np.meshgrid(xs, ys)

    def sample(self, x, y):
        column = np.clip((np.asarray(x, dtype=np.float64) - self.x0) / self.spacing, 0, self.columns - 1.001)
        row = np.clip((np.asarray(y, dtype=np.float64) - self.y0) / self.spacing, 0, self.rows - 1.001)
        c0 = np.floor(column).astype(int)
        r0 = np.floor(row).astype(int)
        fx = column - c0
        fy = row - r0
        h = self.heights
        lower = h[r0, c0] * (1 - fx) + h[r0, c0 + 1] * fx
        upper = h[r0 + 1, c0] * (1 - fx) + h[r0 + 1, c0 + 1] * fx
        result = lower * (1 - fy) + upper * fy
        return float(result) if np.ndim(result) == 0 else result

    def slope(self):
        gy, gx = np.gradient(self.heights, self.spacing)
        return np.hypot(gx, gy)

    def blur(self, mask, passes):
        heights = self.heights.copy()
        for _ in range(passes):
            padded = np.pad(heights, 1, mode="edge")
            average = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]
                       + 4 * padded[1:-1, 1:-1]) / 8
            heights = np.where(mask, average, heights)
        self.heights = heights


def geo_sample(frame, xs, ys, source):
    heights, (west, north, step), _ = source
    latitude, longitude = frame.to_geo(xs, ys)
    lambert_x, lambert_y = lambert93(latitude, longitude)
    limit_r = heights.shape[0] - 1.001
    limit_c = heights.shape[1] - 1.001
    column = np.clip((lambert_x - west) / step - 0.5, 0, limit_c)
    row = np.clip((north - lambert_y) / step - 0.5, 0, limit_r)
    c0 = column.astype(int)
    r0 = row.astype(int)
    fx = column - c0
    fy = row - r0
    top = heights[r0, c0] * (1 - fx) + heights[r0, c0 + 1] * fx
    bottom = heights[r0 + 1, c0] * (1 - fx) + heights[r0 + 1, c0 + 1] * fx
    return top * (1 - fy) + bottom * fy


def distance_to_mask(mask, spacing, iterations=60):
    distance = np.where(mask, 0.0, np.inf)
    diagonal = spacing * math.sqrt(2)
    for _ in range(iterations):
        padded = np.pad(distance, 1, mode="edge")
        candidates = [padded[:-2, 1:-1] + spacing, padded[2:, 1:-1] + spacing, padded[1:-1, :-2] + spacing,
                      padded[1:-1, 2:] + spacing, padded[:-2, :-2] + diagonal, padded[2:, 2:] + diagonal,
                      padded[:-2, 2:] + diagonal, padded[2:, :-2] + diagonal]
        updated = np.minimum(distance, np.min(candidates, axis=0))
        if np.array_equal(updated, distance):
            break
        distance = updated
    return distance


def grid_mesh(name, xs, ys, heights, keep=None, uv=None, colours=None, skirt=0.0):
    rows, columns = heights.shape
    gx, gy = np.meshgrid(xs, ys)
    vertices = np.column_stack([gx.ravel(), gy.ravel(), heights.ravel()])
    index = np.arange(rows * columns).reshape(rows, columns)
    a = index[:-1, :-1]
    b = index[:-1, 1:]
    c = index[1:, 1:]
    d = index[1:, :-1]
    cells = np.ones(a.shape, dtype=bool) if keep is None else keep
    za, zb, zc, zd = (heights.ravel()[k] for k in (a, b, c, d))
    split = np.abs(za - zc) <= np.abs(zb - zd)
    first = np.where(split[..., None], np.stack([a, b, c], -1), np.stack([a, b, d], -1))
    second = np.where(split[..., None], np.stack([a, c, d], -1), np.stack([b, c, d], -1))
    triangles = np.concatenate([first[cells], second[cells]])
    if skirt > 0:
        border = np.concatenate([index[0, :], index[1:, -1], index[-1, -2::-1], index[-2:0:-1, 0]])
        lowered = vertices[border] - np.array([0.0, 0.0, skirt])
        start = len(vertices)
        vertices = np.concatenate([vertices, lowered])
        if colours is not None:
            colours = np.concatenate([colours.reshape(-1, 3), colours.reshape(-1, 3)[border]])
        count = len(border)
        following = np.roll(np.arange(count), -1)
        extra_a = np.column_stack([border[following], border, start + np.arange(count)])
        extra_b = np.column_stack([border[following], start + np.arange(count), start + following])
        triangles = np.concatenate([triangles, extra_a, extra_b])
        rows_total = len(vertices)
    else:
        rows_total = rows * columns
    used = np.unique(triangles)
    remap = np.full(rows_total, -1)
    remap[used] = np.arange(len(used))
    triangles = remap[triangles]
    vertices = vertices[used]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], triangles.tolist())
    mesh.update()
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    if uv is not None:
        coordinates = uv(vertices[:, 0], vertices[:, 1])
        layer = mesh.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", np.asarray(coordinates, dtype=np.float32)[loops].ravel())
    if colours is not None:
        rgba = np.column_stack([colours.reshape(-1, 3)[used], np.ones(len(used))])
        attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        attribute.data.foreach_set("color_srgb", rgba[loops].ravel().astype(np.float32))
        mesh.color_attributes.active_color = attribute
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()
    return mesh


class Ground:
    def __init__(self, fallback):
        self.fallback = fallback
        self.vertices = []
        self.triangles = []
        self.tree = None

    def add(self, obj):
        matrix = obj.matrix_world.copy()
        mesh = obj.data
        mesh.calc_loop_triangles()
        offset = len(self.vertices)
        self.vertices.extend(matrix @ vertex.co for vertex in mesh.vertices)
        self.triangles.extend(tuple(offset + index for index in triangle.vertices) for triangle in mesh.loop_triangles)
        self.tree = None

    def build(self):
        self.tree = BVHTree.FromPolygons(self.vertices, self.triangles, all_triangles=True)

    def height(self, x, y):
        if self.tree is None:
            self.build()
        hit = self.tree.ray_cast(Vector((x, y, 2000.0)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is None:
            return self.fallback(x, y)
        return hit[0].z

    def footprint(self, x, y, radius, samples=6):
        heights = [self.height(x, y)]
        for k in range(samples):
            angle = 2 * math.pi * k / samples
            heights.append(self.height(x + radius * math.cos(angle), y + radius * math.sin(angle)))
        return min(heights), max(heights)

    def normal(self, x, y, step=0.6):
        gx = (self.height(x + step, y) - self.height(x - step, y)) / (2 * step)
        gy = (self.height(x, y + step) - self.height(x, y - step)) / (2 * step)
        return Vector((-gx, -gy, 1.0)).normalized()

import json
import math
import os
import urllib.request

import bmesh
import bpy
import numpy as np

WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563
GEOPLATEFORME_WMS = "https://data.geopf.fr/wms-r/wms"
RGE_ALTI_LAYER = "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES"
ETALAB_LICENCE = "Licence Ouverte Etalab 2.0 (https://www.etalab.gouv.fr/licence-ouverte-open-licence/)"


class GeoFrame:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        eccentricity_squared = WGS84_F * (2 - WGS84_F)
        phi = math.radians(latitude)
        denominator = 1 - eccentricity_squared * math.sin(phi) ** 2
        meridian = WGS84_A * (1 - eccentricity_squared) / denominator ** 1.5
        normal = WGS84_A / math.sqrt(denominator)
        self.metres_per_degree_latitude = math.pi / 180 * meridian
        self.metres_per_degree_longitude = math.pi / 180 * normal * math.cos(phi)

    def to_local(self, latitude, longitude):
        return ((longitude - self.longitude) * self.metres_per_degree_longitude,
                (latitude - self.latitude) * self.metres_per_degree_latitude)

    def to_geo(self, x, y):
        return (self.latitude + y / self.metres_per_degree_latitude,
                self.longitude + x / self.metres_per_degree_longitude)


GRS80_E = 0.0818191910428158


def lambert93(latitude, longitude):
    def isometric(phi):
        sine = GRS80_E * np.sin(phi)
        return np.tan(np.pi / 4 - phi / 2) / ((1 - sine) / (1 + sine)) ** (GRS80_E / 2)

    def scale(phi):
        return np.cos(phi) / np.sqrt(1 - (GRS80_E * np.sin(phi)) ** 2)

    phi0, phi1, phi2 = math.radians(46.5), math.radians(44.0), math.radians(49.0)
    n = (math.log(scale(phi1)) - math.log(scale(phi2))) / (math.log(isometric(phi1)) - math.log(isometric(phi2)))
    radius_factor = WGS84_A * scale(phi1) / (n * isometric(phi1) ** n)
    theta = n * (np.radians(longitude) - math.radians(3.0))
    rho = radius_factor * isometric(np.radians(latitude)) ** n
    rho0 = radius_factor * isometric(phi0) ** n
    return 700000 + rho * np.sin(theta), 6600000 + rho0 - rho * np.cos(theta)


def fetch_lambert_grid(frame, half_extent, step, layer, cache_path):
    center_x, center_y = lambert93(frame.latitude, frame.longitude)
    center_x = round(float(center_x) / step) * step + step / 2
    center_y = round(float(center_y) / step) * step + step / 2
    samples = int(round(2 * half_extent / step))
    west, south = center_x - half_extent, center_y - half_extent
    east, north = center_x + half_extent, center_y + half_extent
    url = (f"{GEOPLATEFORME_WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={layer}&STYLES="
           f"&CRS=EPSG:2154&BBOX={west},{south},{east},{north}&WIDTH={samples}&HEIGHT={samples}"
           f"&FORMAT=image/x-bil;bits=32")
    if not os.path.exists(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "roma-scene-builder/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
        if len(data) != samples * samples * 4:
            raise RuntimeError(f"Unexpected elevation payload of {len(data)} bytes from {url}")
        with open(cache_path, "wb") as handle:
            handle.write(data)
        with open(cache_path + ".json", "w", encoding="utf8") as handle:
            json.dump({"url": url, "layer": layer, "crs": "EPSG:2154", "step": step, "licence": ETALAB_LICENCE},
                      handle, indent=1)
    heights = np.fromfile(cache_path, dtype="<f4").reshape(samples, samples).astype(np.float64)
    invalid = heights < -1000
    if invalid.any():
        heights[invalid] = float(np.median(heights[~invalid]))
    return heights, (west, north, step), url


def local_heights(frame, half_extent, spacing, source):
    heights, (west, north, step), url = source
    samples = int(round(2 * half_extent / spacing)) + 1
    axis = np.linspace(-half_extent, half_extent, samples)
    grid_x, grid_y = np.meshgrid(axis, axis)
    latitude, longitude = frame.to_geo(grid_x, grid_y)
    lambert_x, lambert_y = lambert93(latitude, longitude)
    limit = heights.shape[0] - 1.001
    column = np.clip((lambert_x - west) / step - 0.5, 0, limit)
    row = np.clip((north - lambert_y) / step - 0.5, 0, limit)
    column0 = column.astype(int)
    row0 = row.astype(int)
    fx = column - column0
    fy = row - row0
    top = heights[row0, column0] * (1 - fx) + heights[row0, column0 + 1] * fx
    bottom = heights[row0 + 1, column0] * (1 - fx) + heights[row0 + 1, column0 + 1] * fx
    return top * (1 - fy) + bottom * fy


class HeightField:
    def __init__(self, heights, half_extent):
        self.heights = heights
        self.half_extent = half_extent
        self.samples = heights.shape[0]
        self.spacing = 2 * half_extent / (self.samples - 1)
        axis = np.linspace(-half_extent, half_extent, self.samples)
        self.grid_x, self.grid_y = np.meshgrid(axis, axis)

    def sample(self, x, y):
        column = np.clip((np.asarray(x, dtype=np.float64) + self.half_extent) / self.spacing, 0, self.samples - 1.001)
        row = np.clip((np.asarray(y, dtype=np.float64) + self.half_extent) / self.spacing, 0, self.samples - 1.001)
        column0 = np.floor(column).astype(int)
        row0 = np.floor(row).astype(int)
        fraction_x = column - column0
        fraction_y = row - row0
        h = self.heights
        lower = h[row0, column0] * (1 - fraction_x) + h[row0, column0 + 1] * fraction_x
        upper = h[row0 + 1, column0] * (1 - fraction_x) + h[row0 + 1, column0 + 1] * fraction_x
        result = lower * (1 - fraction_y) + upper * fraction_y
        return float(result) if np.ndim(result) == 0 else result

    def lowest_under(self, points):
        return min(self.sample(x, y) for x, y in points)

    def slope(self):
        gradient_y, gradient_x = np.gradient(self.heights, self.spacing)
        return np.hypot(gradient_x, gradient_y)

    def flatten(self, signed_distance, level, margin):
        distance = signed_distance(self.grid_x, self.grid_y)
        weight = np.clip(1.0 - distance / margin, 0.0, 1.0)
        weight = weight * weight * (3 - 2 * weight)
        self.heights = self.heights * (1 - weight) + level * weight


    def infill(self, mask, iterations=1500):
        heights = self.heights.copy()
        heights[mask] = float(np.mean(heights[~mask]))
        for _ in range(iterations):
            padded = np.pad(heights, 1, mode="edge")
            average = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]) / 4
            heights[mask] = average[mask]
        self.heights = heights


def ellipse_distance(center_x, center_y, semi_major, semi_minor, rotation):
    cosine, sine = math.cos(rotation), math.sin(rotation)

    def distance(x, y):
        local_x = (x - center_x) * cosine + (y - center_y) * sine
        local_y = -(x - center_x) * sine + (y - center_y) * cosine
        radius = np.hypot(local_x / semi_minor, local_y / semi_major)
        return (radius - 1.0) * min(semi_major, semi_minor)
    return distance


def rectangle_distance(center_x, center_y, half_width, half_length, rotation):
    cosine, sine = math.cos(rotation), math.sin(rotation)

    def distance(x, y):
        local_x = (x - center_x) * cosine + (y - center_y) * sine
        local_y = -(x - center_x) * sine + (y - center_y) * cosine
        outside_x = np.abs(local_x) - half_width
        outside_y = np.abs(local_y) - half_length
        return np.maximum(outside_x, outside_y)
    return distance


def grid_mesh(name, heights, half_extent, skirt_depth=0.0, ring=None):
    samples = heights.shape[0]
    axis = np.linspace(-half_extent, half_extent, samples)
    grid_x, grid_y = np.meshgrid(axis, axis)
    vertices = np.column_stack([grid_x.ravel(), grid_y.ravel(), heights.ravel()])
    index = np.arange(samples * samples).reshape(samples, samples)
    quads = np.column_stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(),
                             index[1:, 1:].ravel(), index[1:, :-1].ravel()])
    faces = quads.tolist()
    uv_of_vertex = np.column_stack([(grid_x.ravel() + half_extent) / (2 * half_extent),
                                    (grid_y.ravel() + half_extent) / (2 * half_extent)])
    vertex_list = vertices.tolist()
    uv_list = uv_of_vertex.tolist()
    if skirt_depth > 0:
        border = (list(index[0, :]) + list(index[1:, -1]) + list(index[-1, -2::-1]) + list(index[-2:0:-1, 0]))
        skirt_start = len(vertex_list)
        for vertex_index in border:
            x, y, z = vertex_list[vertex_index]
            vertex_list.append([x, y, z - skirt_depth])
            uv_list.append(uv_list[vertex_index])
        count = len(border)
        for position in range(count):
            following = (position + 1) % count
            faces.append([border[following], border[position], skirt_start + position, skirt_start + following])
    if ring is not None:
        reach, drop = ring
        border = (list(index[0, :]) + list(index[1:, -1]) + list(index[-1, -2::-1]) + list(index[-2:0:-1, 0]))
        ring_start = len(vertex_list)
        for vertex_index in border:
            x, y, z = vertex_list[vertex_index]
            scale = reach / max(abs(x), abs(y))
            vertex_list.append([x * scale, y * scale, z - drop])
            uv_list.append([0.5, 0.03])
        count = len(border)
        for position in range(count):
            following = (position + 1) % count
            faces.append([border[following], border[position], ring_start + position, ring_start + following])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertex_list, [], faces)
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    loop_vertices = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loop_vertices)
    uv_layer.data.foreach_set("uv", np.asarray(uv_list, dtype=np.float32)[loop_vertices].ravel())
    mesh.update()
    return mesh


def remove_faces_inside(mesh, half_extent):
    work = bmesh.new()
    work.from_mesh(mesh)
    doomed = [face for face in work.faces
              if all(abs(vertex.co.x) <= half_extent + 0.5 and abs(vertex.co.y) <= half_extent + 0.5
                     for vertex in face.verts)]
    bmesh.ops.delete(work, geom=doomed, context="FACES")
    work.to_mesh(mesh)
    work.free()
    mesh.update()


def value_noise(shape, cells, seed, octaves=4, persistence=0.5):
    generator = np.random.default_rng(seed)
    height, width = shape
    total = np.zeros(shape)
    amplitude = 1.0
    norm = 0.0
    for octave in range(octaves):
        count = cells * 2 ** octave + 1
        lattice = generator.random((count + 1, count + 1))
        rows = np.linspace(0, count - 1e-6, height)
        columns = np.linspace(0, count - 1e-6, width)
        row0 = rows.astype(int)
        column0 = columns.astype(int)
        fraction_rows = (rows - row0)[:, None]
        fraction_columns = (columns - column0)[None, :]
        fraction_rows = fraction_rows * fraction_rows * (3 - 2 * fraction_rows)
        fraction_columns = fraction_columns * fraction_columns * (3 - 2 * fraction_columns)
        top = lattice[row0][:, column0] * (1 - fraction_columns) + lattice[row0][:, column0 + 1] * fraction_columns
        bottom = (lattice[row0 + 1][:, column0] * (1 - fraction_columns)
                  + lattice[row0 + 1][:, column0 + 1] * fraction_columns)
        total += amplitude * (top * (1 - fraction_rows) + bottom * fraction_rows)
        norm += amplitude
        amplitude *= persistence
    return total / norm


def polygon_mask(points, grid_x, grid_y):
    inside = np.zeros(grid_x.shape, dtype=bool)
    count = len(points)
    for index in range(count):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % count]
        crosses = (y0 > grid_y) != (y1 > grid_y)
        with np.errstate(divide="ignore", invalid="ignore"):
            intersection = x0 + (grid_y - y0) * (x1 - x0) / (y1 - y0)
        inside ^= crosses & (grid_x < intersection)
    return inside


def polyline_distance(points, grid_x, grid_y):
    distance = np.full(grid_x.shape, np.inf)
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        dx, dy = x1 - x0, y1 - y0
        length_squared = max(dx * dx + dy * dy, 1e-9)
        t = np.clip(((grid_x - x0) * dx + (grid_y - y0) * dy) / length_squared, 0, 1)
        distance = np.minimum(distance, np.hypot(grid_x - (x0 + t * dx), grid_y - (y0 + t * dy)))
    return distance


def point_in_polygon(x, y, points):
    inside = False
    count = len(points)
    for index in range(count):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % count]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside

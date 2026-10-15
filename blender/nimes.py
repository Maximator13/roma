import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector

from kit import buildings, life, monuments, urban
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, build_library, save_pixels
from kit.orders import column
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, haze_volume,
                       render_still, sun_lamp)
from kit.terrain import (ETALAB_LICENCE, RGE_ALTI_LAYER, GeoFrame, HeightField, ellipse_distance,
                         fetch_lambert_grid, grid_mesh, local_heights, point_in_polygon, polygon_mask,
                         polyline_distance, rectangle_distance, remove_faces_inside, value_noise)

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "nimes")
ORIGIN = (43.83819143, 4.35613179)
GRID = math.radians(12.0)
HALF = 1300.0
SPACING = 15.0
FAR_HALF = 5850.0
FAR_SPACING = 162.5
SUN_AZIMUTH = 291.0
SUN_ELEVATION = 12.0
BLEND = os.path.join(CACHE, "work", "nimes.blend")
PITCH = 72.0
STREET = 8.0
U_OFFSET = 36.0
V_OFFSET = 18.3
SAND_BASE = np.array([0.84, 0.72, 0.53])

SITES = {
    "maison_carree": (0.0, 0.0),
    "amphitheatre": (280.4, -366.7),
    "porte_auguste": (564.3, 138.6),
    "porte_france": (131.5, -613.0),
    "tour_magne": (-535.5, 540.2),
    "temple_diane": (-617.3, 180.6),
    "castellum": (-20.7, 456.4),
    "nymphaeum": (-548.0, 222.0),
    "basin": (-548.0, 168.0),
    "theatre": (-600.0, 252.0),
}
THERMAE_GRID = (288.0, 54.3)
AMPHITHEATRE_BEARING = 60.1
AMPHITHEATRE_AXES = (66.5, 50.5)
WALL_TRACE = [(x - 2.6, y + 1.0) for x, y in (
    (567, 138), (615, -110), (600, -320), (480, -470), (300, -515), (134, -614), (-120, -695), (-430, -705),
    (-640, -690), (-760, -605), (-1000, -475), (-1130, -450), (-1200, -325), (-1180, -100), (-1050, 60),
    (-1000, 250), (-830, 330), (-860, 440), (-700, 470), (-533, 540), (-560, 640), (-470, 760), (-380, 820),
    (-330, 960), (-250, 1040), (-90, 1120), (40, 1060), (120, 940), (230, 860), (300, 760), (330, 600),
    (420, 520), (470, 460), (520, 300))]
SECONDARY_GATES = [(-432.6, -704.0), (-1182.6, -99.0), (227.4, 861.0)]
ROADS = [
    [(564.3, 138.6), (760.0, 95.0), (1000.0, 20.0), (1300.0, -80.0)],
    [(-432.6, -704.0), (-640.0, -900.0), (-900.0, -1120.0), (-1100.0, -1300.0)],
    [(131.5, -613.0), (180.0, -820.0), (240.0, -1060.0), (300.0, -1300.0)],
    [(227.4, 861.0), (300.0, 1000.0), (380.0, 1150.0), (440.0, 1300.0)],
    [(-1182.6, -99.0), (-1300.0, -120.0)],
]
FORT_VAUBAN = [(-55.0, 425.0), (-55.0, 668.0), (182.0, 668.0), (182.0, 412.0), (60.0, 405.0)]
EMBANKMENTS = [((186.0, -564.0), (254.0, -495.0)), ((781.0, -749.0), (918.0, -603.0)),
               ((78.0, -1277.0), (303.0, -1120.0))]
MAIN_STREETS = [("v", 18.3, (36.0, 700.0)), ("u", 36.0, (-260.0, 400.0)), ("u", -36.0, (-260.0, 400.0)),
                ("u", 180.0, (-430.0, 20.0)), ("v", -53.7, (-260.0, 340.0)), ("v", 306.3, (-440.0, -30.0))]


def to_grid(x, y):
    return x * math.cos(GRID) + y * math.sin(GRID), -x * math.sin(GRID) + y * math.cos(GRID)


def from_grid(u, v):
    return u * math.cos(GRID) - v * math.sin(GRID), u * math.sin(GRID) + v * math.cos(GRID)


def rotate(x, y, angle):
    return x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 32}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def trace_frame(points, index):
    count = len(points)
    a = Vector((*points[index], 0.0))
    b = Vector((*points[(index + 1) % count], 0.0))
    return a, b


def signed_area(points):
    return sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1]
               for i in range(len(points))) / 2


def outward_normal(direction, counter_clockwise):
    normal = Vector((direction.y, -direction.x, 0.0)) if counter_clockwise else Vector((-direction.y, direction.x,
                                                                                         0.0))
    return normal.normalized()


def nearest_on_trace(point, points):
    best = None
    count = len(points)
    for index in range(count):
        a, b = trace_frame(points, index)
        segment = b - a
        t = max(0.0, min(1.0, (Vector((*point, 0.0)) - a).dot(segment) / segment.length_squared))
        candidate = a + segment * t
        distance = (candidate - Vector((*point, 0.0))).length
        if best is None or distance < best[0]:
            best = (distance, index, t, segment.normalized())
    return best


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

    def blocked(self, x, y):
        return any(shape(x, y) for shape in self.shapes)


def build_terrain():
    frame = GeoFrame(*ORIGIN)
    near = fetch_lambert_grid(frame, 1500.0, 5.0, RGE_ALTI_LAYER,
                              os.path.join(CACHE, "src", "rge_alti_l93_5m.bil"))
    far = fetch_lambert_grid(frame, 6600.0, 50.0, RGE_ALTI_LAYER,
                             os.path.join(CACHE, "src", "rge_alti_l93_50m.bil"))
    field = HeightField(local_heights(frame, HALF, SPACING, near), HALF)
    mask = polygon_mask(FORT_VAUBAN, field.grid_x, field.grid_y)
    for start, end in EMBANKMENTS:
        mask |= polyline_distance([start, end], field.grid_x, field.grid_y) < 16.0
    field.infill(mask)
    far_field = HeightField(local_heights(frame, FAR_HALF, FAR_SPACING, far), FAR_HALF)
    return field, far_field, [near[2], far[2]]


def amphitheatre_level(field):
    ax, ay = SITES["amphitheatre"]
    samples = [field.sample(ax + r * math.cos(t), ay + r * math.sin(t))
               for r in (80.0, 85.0, 90.0, 95.0) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    return float(np.median(samples))


def flatten_sites(field):
    level = field.sample(*SITES["maison_carree"])
    field.flatten(rectangle_distance(*rotate(0.0, 22.0, GRID), 42.0, 58.0, GRID), level, 25.0)
    ax, ay = SITES["amphitheatre"]
    arena_level = amphitheatre_level(field)
    a, b = AMPHITHEATRE_AXES
    field.flatten(ellipse_distance(ax, ay, a + 22, b + 22, math.radians(-AMPHITHEATRE_BEARING)), arena_level, 35.0)
    bx, by = SITES["basin"]
    field.flatten(rectangle_distance(bx - 28, by + 22, 78.0, 56.0, GRID), field.sample(bx, by), 20.0)
    for name in ("porte_auguste", "porte_france", "castellum"):
        x, y = SITES[name]
        field.flatten(lambda gx, gy, x=x, y=y: np.hypot(gx - x, gy - y) - 22.0, field.sample(x, y), 25.0)
    return level, arena_level


def street_distance(u, v):
    du = np.abs(((u - U_OFFSET + PITCH / 2) % PITCH) - PITCH / 2)
    dv = np.abs(((v - V_OFFSET + PITCH / 2) % PITCH) - PITCH / 2)
    return np.minimum(du, dv)


def sun_shadow(field, grid_x, grid_y, heights, steps=48, reach=1400.0):
    azimuth = math.radians(SUN_AZIMUTH)
    direction = (math.sin(azimuth), math.cos(azimuth))
    slope = math.tan(math.radians(SUN_ELEVATION))
    clearance = np.full(heights.shape, np.inf)
    for step in range(1, steps + 1):
        distance = reach * (step / steps) ** 1.6
        ahead = field.sample(grid_x + direction[0] * distance, grid_y + direction[1] * distance)
        clearance = np.minimum(clearance, heights + distance * slope - ahead)
    return np.clip(clearance / 6.0 + 0.5, 0.0, 1.0)


def terrain_colour(grid_x, grid_y, heights, slope, inside, roads, seed, plain_level, shadow=None, rock_level=0.74):
    u = grid_x * math.cos(GRID) + grid_y * math.sin(GRID)
    v = -grid_x * math.sin(GRID) + grid_y * math.cos(GRID)
    shape = grid_x.shape
    noise = value_noise(shape, 12, seed, 5)
    fine = value_noise(shape, 60, seed + 1, 3)
    parcel_u = np.floor(u / 118.0).astype(np.int64)
    parcel_v = np.floor(v / 59.0).astype(np.int64)
    parcel = ((parcel_u * 73856093) ^ (parcel_v * 19349663)) % 1000 / 1000.0
    crops = np.array([[0.80, 0.68, 0.40], [0.78, 0.69, 0.42], [0.74, 0.64, 0.44], [0.50, 0.50, 0.31],
                      [0.60, 0.58, 0.40], [0.68, 0.62, 0.45], [0.82, 0.71, 0.44]])
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)]
    vine = (parcel > 0.43) & (parcel < 0.57)
    rows = (np.sin(v * 2 * math.pi / 2.2) > 0.2)
    colour = np.where(vine[..., None], np.array([0.56, 0.50, 0.36]), colour)
    colour = np.where((vine & rows)[..., None], np.array([0.40, 0.44, 0.26]), colour)
    edge = (np.abs((u / 118.0) % 1.0 - 0.5) > 0.49) | (np.abs((v / 59.0) % 1.0 - 0.5) > 0.48)
    colour = np.where(edge[..., None], np.array([0.48, 0.48, 0.32]), colour)
    garrigue = np.dstack([0.33 + 0.08 * fine, 0.36 + 0.07 * fine, 0.24 + 0.03 * fine])
    rock = np.array([0.74, 0.71, 0.63])
    garrigue = np.where((fine > rock_level)[..., None], rock * (0.9 + 0.1 * noise[..., None]), garrigue)
    garrigue = np.where((fine < 0.32)[..., None], np.array([0.24, 0.29, 0.17]), garrigue)
    hill = np.clip((slope - 0.07) / 0.06, 0, 1) * 0.6 + np.clip((heights - plain_level - 18) / 20, 0, 1)
    hill = np.clip(hill + (noise - 0.5) * 0.6, 0, 1)
    colour = colour * (1 - hill[..., None]) + garrigue * hill[..., None]
    urban = np.dstack([0.70 + 0.05 * fine, 0.62 + 0.04 * fine, 0.50 + 0.03 * fine])
    city = inside.astype(float) * (1 - hill * 0.7)
    colour = colour * (1 - city[..., None]) + urban * city[..., None]
    lanes = np.clip(1.0 - (street_distance(u, v) - 3.0) / 1.5, 0, 1) * inside * np.clip(1.0 - hill * 2.0, 0, 1)
    colour = colour * (1 - lanes[..., None]) + np.array([0.80, 0.75, 0.66]) * lanes[..., None]
    road = np.clip(1.0 - (roads - 3.0) / 3.0, 0, 1)
    colour = colour * (1 - road[..., None]) + np.array([0.80, 0.74, 0.62]) * road[..., None]
    colour *= (0.94 + 0.12 * noise)[..., None]
    if shadow is not None:
        colour *= (0.74 + 0.26 * shadow)[..., None]
    return np.clip(colour, 0, 1)


def terrain_colour_at(field, xs, ys, plain_level):
    heights = field.sample(xs, ys)
    step = 3.0
    gradient_x = (field.sample(xs + step, ys) - field.sample(xs - step, ys)) / (2 * step)
    gradient_y = (field.sample(xs, ys + step) - field.sample(xs, ys - step)) / (2 * step)
    inside = polygon_mask(WALL_TRACE, xs, ys)
    roads = np.min([polyline_distance(road, xs, ys) for road in ROADS], axis=0)
    return terrain_colour(xs, ys, heights, np.hypot(gradient_x, gradient_y), inside, roads, 11, plain_level)


def terrain_objects(field, far_field, plain_level, datum, collection, root):
    resolution = 1024
    axis = np.linspace(-HALF, HALF, resolution)
    grid_x, grid_y = np.meshgrid(axis, axis)
    heights = field.sample(grid_x, grid_y)
    gradient_y, gradient_x = np.gradient(heights, axis[1] - axis[0])
    slope = np.hypot(gradient_x, gradient_y)
    inside = polygon_mask(WALL_TRACE, grid_x, grid_y)
    roads = np.min([polyline_distance(road, grid_x, grid_y) for road in ROADS], axis=0)
    shadow = sun_shadow(field, grid_x, grid_y, heights)
    colour = terrain_colour(grid_x, grid_y, heights, slope, inside, roads, 11, plain_level, shadow)
    path = os.path.join(CACHE, "textures", "terrain_colour.jpg")
    image = save_pixels("terrain_colour", colour, path, quality=88)
    material = baked_material("terrain", image)
    material.use_backface_culling = True
    carved = field.heights - datum
    kx, ky = SITES["castellum"]
    carved = np.where(np.hypot(field.grid_x - kx, field.grid_y - ky) < 9.0, carved - 2.4, carved)
    mesh = grid_mesh("terrain", carved, HALF, skirt_depth=25.0)
    mesh.materials.append(material)
    new_object("terrain", mesh, collection, root)
    far_resolution = 256
    far_axis = np.linspace(-FAR_HALF, FAR_HALF, far_resolution)
    far_x, far_y = np.meshgrid(far_axis, far_axis)
    far_heights = far_field.sample(far_x, far_y)
    far_gradient_y, far_gradient_x = np.gradient(far_heights, far_axis[1] - far_axis[0])
    far_roads = np.full(far_x.shape, 1e6)
    far_colour = terrain_colour(far_x, far_y, far_heights, np.hypot(far_gradient_x, far_gradient_y),
                                np.zeros(far_x.shape, dtype=bool), far_roads, 23, plain_level, rock_level=2.0)
    far_image = save_pixels("terrain_far_colour", far_colour, os.path.join(CACHE, "textures", "terrain_far.jpg"),
                            quality=85)
    far_material = baked_material("terrain_far", far_image)
    far_mesh = grid_mesh("terrain_far", far_field.heights - datum, FAR_HALF, ring=(40000.0, 125.0))
    remove_faces_inside(far_mesh, HALF - FAR_SPACING * 0.5)
    far_mesh.materials.append(far_material)
    far_object = new_object("terrain_far", far_mesh, collection, root)
    far_object["cast_shadow"] = False


def ground_patch(scene, name, cx, cy, radius, plain_level, spacing=3.0, lift=0.07, hole=None):
    count = int(2 * radius / spacing) + 1
    axis = np.linspace(-radius, radius, count)
    local_x, local_y = np.meshgrid(axis, axis)
    xs, ys = local_x + cx, local_y + cy
    colours = terrain_colour_at(scene.field, xs, ys, plain_level) / SAND_BASE
    colours = np.clip(colours * 0.96, 0.0, 1.0)
    heights = scene.field.sample(xs, ys) - scene.datum + lift
    index = np.arange(count * count).reshape(count, count)
    keep = np.hypot(local_x[:-1, :-1] + spacing / 2, local_y[:-1, :-1] + spacing / 2) < radius
    if hole is not None:
        keep &= ~hole(xs[:-1, :-1] + spacing / 2, ys[:-1, :-1] + spacing / 2)
    quads = np.column_stack([index[:-1, :-1][keep], index[:-1, 1:][keep], index[1:, 1:][keep], index[1:, :-1][keep]])
    vertices = np.column_stack([xs.ravel(), ys.ravel(), heights.ravel()])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], quads.tolist())
    mesh.update()
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    uv = np.column_stack([local_x.ravel() / spacing / 1.0, local_y.ravel() / spacing / 1.0])
    mesh.uv_layers.new(name="UVMap").data.foreach_set("uv", uv[loops].ravel().astype(np.float32))
    rgba = np.column_stack([colours.reshape(-1, 3), np.ones(count * count)])
    attribute = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attribute.data.foreach_set("color_srgb", rgba[loops].ravel().astype(np.float32))
    mesh.color_attributes.active_color = attribute
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.materials.append(bpy.data.materials["arena_sand"])
    created = new_object(name, mesh, scene.collection, scene.root("ground"))
    created["cast_shadow"] = False
    return created


class Scene:
    def __init__(self, tiles, field, datum):
        self.tiles = tiles
        self.field = field
        self.datum = datum
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Nimes")
        self.roots = {}
        self.pending = {}
        self.placements = {}

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return self.field.sample(x, y) - self.datum

    def unique(self, group, name, builder, matrix, occlusion=True):
        if not occlusion:
            builder.heights = [10.0] * len(builder.positions)
        self.pending.setdefault(group, []).append((builder, matrix))
        self.root(group)

    def flush(self):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(builder, matrix, keep_local=True)
            unique_object(f"{group}_static", merged, self.collection, self.root(group), self.tiles)
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True, occlusion=True, merge=False):
        if not matrices:
            return None
        if merge:
            builder = build()
            for matrix in matrices:
                self.unique(group, key, builder, matrix, occlusion)
            return None
        return self.library.place(key, build, self.collection, self.root(group), matrices, cast_shadow, occlusion)

    def add(self, key, matrix):
        self.placements.setdefault(key, []).append(matrix)


def site_matrix(scene, name, angle, local_offset=(0.0, 0.0), z=None):
    x, y = SITES[name]
    ox, oy = rotate(*local_offset, angle)
    level = scene.ground(x + ox, y + oy) if z is None else z
    return placement(x + ox, y + oy, level, angle)


def build_maison_carree(scene):
    layout = monuments.TempleLayout()
    origin = placement(0.0, 0.0, 0.0, GRID)
    frieze = "C·CAESARI·AVGVSTI·F·COS·L·CAESARI·AVGVSTI·F·COS·DESIGNATO"
    architrave = "PRINCIPIBVS·IVVENTVTIS"
    scene.unique("forum", "maison_carree_body", monuments.maison_carree_body(layout, frieze, architrave),
                 origin)
    builds = monuments.temple_columns(layout)
    for kind, frames in layout.column_frames().items():
        scene.instances("forum", f"mc_column_{kind}", builds[kind], [origin @ frame for frame in frames], merge=True)
    scene.unique("forum", "maison_carree_altar", buildings.altar(3.4, 2.4, 1.5),
                 origin @ placement(0.0, layout.front + 6.5, 0.0))
    return layout


def build_forum(scene, layout):
    origin = placement(0.0, 0.0, 0.0, GRID)
    half_width = 28.0
    south = -24.0
    north = 56.0
    depth = 7.0
    column_height = 5.6
    wings = [
        ("forum_wing_east", north - south, (half_width + 0.0, (north + south) / 2), math.pi / 2),
        ("forum_wing_west", north - south, (-half_width, (north + south) / 2), -math.pi / 2),
        ("forum_wing_south", 2 * half_width + 2 * depth + 1.6, (0.0, south), 0.0),
    ]
    column_frames = []
    for name, length, (x, y), angle in wings:
        frame = origin @ placement(x, y, 0.0, angle)
        scene.unique("forum", name, monuments.portico_wing(length, depth, column_height), frame)
        span = length - (2 * depth + 1.6 if name.endswith("south") else 0.0)
        column_frames.extend(frame @ local for local in monuments.portico_columns(span, 4.0, column_height))
    court = MeshBuilder()
    court.box((-half_width, south + 0.8, -1.0), (half_width, north + 2.0, 0.02), "paving", bottom=False)
    for x in (-half_width - depth - 0.8, half_width + 0.8):
        court.box((x, north, -1.0), (x + depth, north + 2.0, 0.45), "paving", bottom=False)
    for side in (-1, 1):
        court.box((side * 11.5, north + 1.0, 0.0), (side * (half_width + depth + 0.8), north + 2.0, 7.5),
                  "plaster", bottom=False)
    scene.unique("forum", "forum_court", court, origin)
    scene.instances("forum", "forum_column", lambda: column("corinthian", 0.62, column_height, "low"),
                    column_frames, merge=True)
    hall, hall_columns, hall_column_height = monuments.curia()
    hall_frame = origin @ placement(0.0, north + 2.0 + 8.9, 0.0, math.pi)
    scene.unique("forum", "curia", hall, hall_frame)
    scene.instances("forum", "curia_column", lambda: column("corinthian", 0.82, hall_column_height, "medium"),
                    [hall_frame @ frame for frame in hall_columns], merge=True)
    for index, y in enumerate((-12.0, 0.0, 12.0, 24.0, 36.0, 48.0)):
        for side in (-1, 1):
            key = "statue_bronze" if (index + side) % 3 else "statue_marble"
            scene.add(key, origin @ placement(side * 24.6, y, 0.02, -side * math.pi / 2))
    for x in (-18.0, -9.0, 9.0, 18.0):
        scene.add("statue_bronze", origin @ placement(x, -19.4, 0.02, math.pi))


def ellipse_point(a, b, t):
    return a * math.cos(t), b * math.sin(t)


def amphitheatre_frame(scene):
    cx, cy = SITES["amphitheatre"]
    angle = math.radians(90.0 - AMPHITHEATRE_BEARING)
    return cx, cy, angle, scene.arena_level - scene.datum


def build_amphitheatre(scene):
    cx, cy, angle, z = amphitheatre_frame(scene)
    a, b = AMPHITHEATRE_AXES
    angles, perimeter = buildings.ellipse_arc_angles(a, b, 60)
    bay_width = perimeter / 60
    frames = []
    for t in angles:
        px, py = ellipse_point(a, b, t)
        nx, ny = math.cos(t) / a, math.sin(t) / b
        rotation = math.atan2(ny, nx) - math.pi / 2
        wx, wy = rotate(px, py, angle)
        frames.append(placement(cx + wx, cy + wy, z, rotation + angle))
    axial = {0, 15, 30, 45}
    bearings = {index: math.degrees(math.atan2(frames[index].translation.x - cx, frames[index].translation.y - cy)) % 360
                for index in axial}
    north = min(axial, key=lambda index: min(abs(bearings[index] - 330.0), 360 - abs(bearings[index] - 330.0)))
    scene.instances("amphitheatre", "amphitheatre_bay", lambda: buildings.amphitheatre_bay(bay_width * 1.01),
                    [frame for index, frame in enumerate(frames) if index not in axial])
    scene.instances("amphitheatre", "amphitheatre_bay_axial",
                    lambda: buildings.amphitheatre_bay_axial(bay_width * 1.01),
                    [frames[index] for index in sorted(axial - {north})], merge=True)
    scene.unique("amphitheatre", "amphitheatre_bay_north", buildings.amphitheatre_bay_axial(bay_width * 1.01, True),
                 frames[north])
    cavea = buildings.amphitheatre_cavea(34.0, 19.0, a - 6.3, b - 6.3, 19.35)
    scene.unique("amphitheatre", "amphitheatre_cavea", cavea, placement(cx, cy, z, angle))
    scene.unique("amphitheatre", "amphitheatre_velum", urban.velum(a - 1.0, b - 1.0, 34.0, 19.0, 21.6, 19.8, angles),
                 placement(cx, cy, z, angle), occlusion=False)
    return bearings[north]


def trace_walk(points, step):
    pieces = []
    count = len(points)
    travelled = 0.0
    for index in range(count):
        a, b = trace_frame(points, index)
        segment = b - a
        length = segment.length
        n = max(int(round(length / step)), 1)
        for k in range(n):
            start = a + segment * (k / n)
            end = a + segment * ((k + 1) / n)
            pieces.append((start, end, travelled + length * (k + 0.5) / n))
        travelled += length
    return pieces, travelled


def build_walls(scene):
    ccw = signed_area(WALL_TRACE) > 0
    pieces, perimeter = trace_walk(WALL_TRACE, 10.0)
    gates = {"porte_auguste": 22.0, "porte_france": 6.0}
    holes = [(SITES[name], width) for name, width in gates.items()]
    holes += [(gate, 14.5) for gate in SECONDARY_GATES]
    holes.append((SITES["tour_magne"], 9.0))
    wall_frames = []
    for start, end, _ in pieces:
        middle = (start + end) / 2
        if any((Vector((*center, 0.0)) - middle).length < width for center, width in holes):
            continue
        direction = (end - start).normalized()
        normal = outward_normal(direction, ccw)
        rotation = math.atan2(normal.y, normal.x) - math.pi / 2
        z = min(scene.ground(start.x, start.y), scene.ground(end.x, end.y), scene.ground(middle.x, middle.y))
        wall_frames.append(placement(middle.x, middle.y, z - 0.2, rotation, ((end - start).length / 10.0 + 0.02,
                                                                             1.0, 1.0)))
    scene.instances("walls", "wall_curtain", lambda: buildings.curtain_wall(10.0, foundation=10.0), wall_frames)
    round_frames = []
    barlong_frames = []
    spacing = 72.0
    distance = 30.0
    pieces_by_length = sorted(pieces, key=lambda item: item[2])
    for start, end, along in pieces_by_length:
        if along < distance:
            continue
        distance += spacing
        middle = (start + end) / 2
        if any((Vector((*center, 0.0)) - middle).length < width + 14.0 for center, width in holes):
            continue
        direction = (end - start).normalized()
        normal = outward_normal(direction, ccw)
        rotation = math.atan2(normal.y, normal.x) - math.pi / 2
        z = scene.ground(middle.x, middle.y) - 0.3
        target = round_frames if int(along / spacing) % 3 else barlong_frames
        target.append(placement(middle.x, middle.y, z, rotation))
    scene.instances("walls", "wall_tower_round", lambda: buildings.round_tower(4.5, 13.0, 3.0, 10.0),
                    round_frames)
    scene.instances("walls", "wall_tower_barlong", lambda: buildings.barlong_tower(8.0, 6.5, 12.5, 10.0),
                    barlong_frames)
    gate_frames = {}
    for name, center in [("porte_auguste", SITES["porte_auguste"]), ("porte_france", SITES["porte_france"])] + [
            (f"gate_{index}", gate) for index, gate in enumerate(SECONDARY_GATES)]:
        _, _, _, direction = nearest_on_trace(center, WALL_TRACE)
        normal = outward_normal(direction, ccw)
        rotation = math.atan2(normal.y, normal.x) - math.pi / 2
        gate_frames[name] = placement(center[0], center[1], scene.ground(*center), rotation)
    scene.unique("gates", "porte_auguste", buildings.augustus_gate(), gate_frames["porte_auguste"])
    scene.unique("gates", "porte_de_france", buildings.porte_de_france(), gate_frames["porte_france"])
    scene.instances("gates", "gate_secondary", buildings.secondary_gate,
                    [gate_frames[f"gate_{index}"] for index in range(len(SECONDARY_GATES))])
    x, y = SITES["tour_magne"]
    scene.unique("tour_magne", "tour_magne", buildings.tour_magne(), placement(x, y, scene.ground(x, y) - 0.5,
                                                                                math.radians(22.5)))
    return gate_frames, {"round_towers": len(round_frames), "barlong_towers": len(barlong_frames),
                         "curtain_pieces": len(wall_frames)}


def road_strip(scene, points, width, step=8.0):
    lefts, rights = [], []
    kerb_left, kerb_right = [], []
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        count = max(int(length / step), 1)
        for k in range(count + (1 if (x1, y1) == points[-1] else 0)):
            x, y = x0 + dx * length * k / count, y0 + dy * length * k / count
            if abs(x) > HALF - 5 or abs(y) > HALF - 5:
                continue
            for side, target, kerb in ((1, lefts, kerb_left), (-1, rights, kerb_right)):
                px, py = x - dy * side * width / 2, y + dx * side * width / 2
                level = scene.ground(px, py)
                target.append((px, py, level + 0.15))
                qx, qy = x - dy * side * (width / 2 + 0.45), y + dx * side * (width / 2 + 0.45)
                kerb.append([(px, py, level + 0.32), (qx, qy, level + 0.32), (qx, qy, level - 0.4)])
    builder = MeshBuilder()
    builder.surface([lefts, rights], "arena_sand", facing=(0, 0, 1))
    builder.tint(0, (0.82, 0.78, 0.72))
    for kerb, facing in ((kerb_left, 1), (kerb_right, -1)):
        rows = [[point[0] for point in kerb], [point[1] for point in kerb]]
        builder.surface(rows if facing > 0 else list(reversed(rows)), "weathered_ashlar", facing=(0, 0, 1))
        sides = [[point[1] for point in kerb], [point[2] for point in kerb]]
        builder.surface(sides if facing > 0 else list(reversed(sides)), "weathered_ashlar")
    return builder


def build_roads(scene):
    for index, (road, width) in enumerate(((ROADS[0], 6.0), (ROADS[2], 5.0), (ROADS[1], 5.0))):
        scene.unique("roads", f"road_{index}", road_strip(scene, road, width), Matrix.Identity(4), occlusion=False)


def build_sanctuary(scene):
    scene.unique("fontaine", "nymphaeum", monuments.nymphaeum(), site_matrix(scene, "nymphaeum", GRID))
    basin, corners = monuments.sacred_basin()
    basin_frame = site_matrix(scene, "basin", GRID)
    scene.unique("fontaine", "sacred_basin", basin, basin_frame)
    scene.instances("fontaine", "basin_column", lambda: column("corinthian", 0.55, 5.2, "medium"),
                    [basin_frame @ frame for frame in corners], merge=True)
    scene.unique("fontaine", "basin_altar", buildings.altar(2.6, 1.8, 1.2), basin_frame @ placement(0, 0, 1.5))
    for name, offset, angle, length in (("sanctuary_portico_south", (0.0, -40.0), 0.0, 96.0),
                                        ("sanctuary_portico_east", (48.0, 5.0), math.pi / 2, 90.0)):
        frame = basin_frame @ placement(offset[0], offset[1], 0.0, angle)
        scene.unique("fontaine", name, monuments.portico_wing(length, 6.0, 5.0), frame)
        scene.instances("fontaine", f"{name}_column", lambda: column("tuscan", 0.55, 5.0, "low"),
                        [frame @ local for local in monuments.portico_columns(length, 3.6)], merge=True)
    for index, x in enumerate(range(-40, 41, 8)):
        key = "statue_bronze" if index % 3 else "statue_marble"
        scene.add(key, basin_frame @ placement(float(x), -44.2, 0.45, math.pi))
    for index, y in enumerate(range(-30, 41, 10)):
        if abs(y - 28) < 6:
            continue
        key = "statue_marble" if index % 2 else "statue_bronze"
        scene.add(key, basin_frame @ placement(52.2, float(y) + 5.0, 0.45, -math.pi / 2))
    scene.unique("fontaine", "propylaeum", monuments.propylaeum(), basin_frame @ placement(58.0, 28.0, 0.0))
    cypresses = [basin_frame @ Vector((x, y, 0.0)) for x, y in ((-40.0, -31.0), (40.0, -31.0), (-23.0, 46.0),
                                                                 (23.0, 46.0), (-31.0, 40.0), (31.0, 40.0))]
    planes = [basin_frame @ Vector((x, y, 0.0)) for x, y in ((-30.0, -22.0), (30.0, -22.0), (-36.0, 18.0),
                                                              (36.0, 22.0), (12.0, -30.0))]
    scene.unique("fontaine", "temple_de_diane", monuments.vaulted_hall(),
                 site_matrix(scene, "temple_diane", GRID - math.pi / 2))
    scene.unique("fontaine", "theatre", monuments.hillside_theatre(), site_matrix(scene, "theatre", GRID))
    tx, ty = from_grid(*THERMAE_GRID)
    scene.unique("forum", "thermae", monuments.thermae(), placement(tx, ty, scene.ground(tx, ty), GRID))
    x, y = SITES["castellum"]
    building, columns = monuments.castellum()
    frame = placement(x, y, scene.ground(x, y), GRID)
    scene.unique("castellum", "castellum", building, frame)
    scene.instances("castellum", "castellum_column", lambda: column("tuscan", 0.42, 3.6, "low"),
                    [frame @ local for local in columns], merge=True)
    channel_start = Vector(rotate(0.0, 7.2, GRID)) + Vector((x, y))
    scene.unique("castellum", "aqueduct_channel", monuments.aqueduct_channel(40.0),
                 placement(channel_start.x, channel_start.y, scene.ground(x, y) - 1.3, GRID))
    return [(point.x, point.y) for point in cypresses], [(point.x, point.y) for point in planes], basin_frame


ROW_VARIANTS = 4
TABERNAE_VARIANTS = 2
HOUSES = {f"row_{index}": (lambda index=index: urban.row_template(index + 1)) for index in range(ROW_VARIANTS)}
HOUSES.update({f"row_tabernae_{index}": (lambda index=index: urban.row_template(101 + index, tabernae=True))
               for index in range(TABERNAE_VARIANTS)})
HOUSES.update({
    "domus_a": lambda: urban.domus(11, 32.0, 30.0, 13.0, 12.0, 6.5, "plaster_white"),
    "domus_b": lambda: urban.domus(12, 28.0, 32.0, 11.0, 14.0, 6.0, "plaster_ochre"),
    "house_single_a": lambda: urban.single_house(21),
    "house_single_b": lambda: urban.single_house(22, 12.0, 8.0),
    "kitchen_garden": lambda: urban.kitchen_garden(31),
    "terrace": lambda: urban.terrace(41),
})


def main_street(axis, value):
    for street_axis, street_value, (low, high) in MAIN_STREETS:
        if street_axis == axis and abs(street_value - value) < 1.0:
            return low, high
    return None


def is_main(axis, value, along):
    span = main_street(axis, value)
    return span is not None and span[0] <= along <= span[1]


def slope_matrix(scene, u, v, along_axis, length):
    if along_axis == "u":
        a, b = from_grid(u - length / 2, v), from_grid(u + length / 2, v)
        rotation = GRID
    else:
        a, b = from_grid(u, v - length / 2), from_grid(u, v + length / 2)
        rotation = GRID + math.pi / 2
    za, zb = scene.ground(*a), scene.ground(*b)
    x, y = from_grid(u, v)
    pitch = math.atan2(zb - za, length)
    return (Matrix.Translation((x, y, (za + zb) / 2)) @ Matrix.Rotation(rotation, 4, "Z")
            @ Matrix.Rotation(-pitch, 4, "Y")), abs(zb - za) / length


def inside_city(x, y, margin=14.0):
    return point_in_polygon(x, y, WALL_TRACE) and nearest_on_trace((x, y), WALL_TRACE)[0] > margin


def build_streets(scene, exclusions, plain_level):
    corners = [to_grid(x, y) for x, y in WALL_TRACE]
    u_range = (min(u for u, _ in corners), max(u for u, _ in corners))
    v_range = (min(v for _, v in corners), max(v for _, v in corners))
    lines_u = [U_OFFSET + PITCH * k for k in range(int((u_range[0] - U_OFFSET) // PITCH) - 1,
                                                    int((u_range[1] - U_OFFSET) // PITCH) + 2)]
    lines_v = [V_OFFSET + PITCH * k for k in range(int((v_range[0] - V_OFFSET) // PITCH) - 1,
                                                    int((v_range[1] - V_OFFSET) // PITCH) + 2)]
    segments = {"street_paved": [], "street_earth": []}
    nodes = {}
    sidewalks = []

    def usable(u, v):
        x, y = from_grid(u, v)
        if not inside_city(x, y, 12.0) or exclusions.blocked(x, y):
            return False
        return scene.field.sample(x, y) < plain_level + 16.0

    for axis, lines, cross_lines in (("v", lines_v, lines_u), ("u", lines_u, lines_v)):
        for line in lines:
            for start, end in zip(cross_lines[:-1], cross_lines[1:]):
                run = []
                for k in range(4):
                    along = start + STREET / 2 + 8.0 + 16.0 * k
                    u, v = (along, line) if axis == "v" else (line, along)
                    if not usable(u, v):
                        run.append(None)
                        continue
                    matrix, grade = slope_matrix(scene, u, v, "u" if axis == "v" else "v", 16.0)
                    if grade > 0.12:
                        run.append(None)
                        continue
                    paved = is_main(axis, line, along)
                    segments["street_paved" if paved else "street_earth"].append(matrix)
                    run.append((u, v, paved))
                    if paved:
                        sidewalks.append((axis, line, along))
                for node_along, member in ((start, run[0]), (end, run[-1])):
                    if member is None:
                        continue
                    key = (round(node_along, 1), round(line, 1)) if axis == "v" else (round(line, 1),
                                                                                       round(node_along, 1))
                    nodes[key] = nodes.get(key, False) or member[2]
    node_frames = {"street_node_paved": [], "street_node_earth": []}
    fountains = []
    for (u, v), paved in nodes.items():
        matrix, _ = slope_matrix(scene, u, v, "u", 8.0)
        node_frames["street_node_paved" if paved else "street_node_earth"].append(matrix)
        if paved and (round((u - U_OFFSET) / PITCH) + round((v - V_OFFSET) / PITCH)) % 2 == 0:
            fx, fy = from_grid(u + 3.3, v + 3.3)
            fountains.append((fx, fy, GRID + math.pi))
    builds = {"street_paved": lambda: urban.street_segment(True), "street_earth": lambda: urban.street_segment(False),
              "street_node_paved": lambda: urban.street_node(True), "street_node_earth": lambda: urban.street_node(False)}
    for key, matrices in list(segments.items()) + list(node_frames.items()):
        scene.instances("streets", key, builds[key], matrices, cast_shadow=False, occlusion=False)
    fountain_frames = [placement(x, y, scene.ground(x, y) + 0.36, angle) for x, y, angle in fountains]
    scene.instances("streets", "street_fountain", urban.street_fountain, fountain_frames, occlusion=False)
    return {"segments": sum(len(m) for m in segments.values()), "nodes": len(nodes), "fountains": len(fountains)}, \
        fountain_frames, sidewalks


def block_facing_main(axis, line, low, high):
    span = main_street(axis, line)
    return span is not None and span[0] <= high and low <= span[1]


def build_city(scene, exclusions, plain_level, rng):
    cell = (PITCH - STREET) / 4
    corners = [to_grid(x, y) for x, y in WALL_TRACE]
    u_min = min(u for u, _ in corners)
    u_max = max(u for u, _ in corners)
    v_min = min(v for _, v in corners)
    v_max = max(v for _, v in corners)
    placements = {key: [] for key in HOUSES}
    trees = []
    rows_dense = []
    depth = 11.0

    def relief_at(x, y, radius):
        probe = [scene.field.sample(x + dx, y + dy) for dx in (-radius, radius) for dy in (-radius, radius)]
        return probe, max(probe) - min(probe)

    def free(points):
        return all(inside_city(x, y, 18.0) and not exclusions.blocked(x, y) for x, y in points)

    for bi in range(int((u_min - U_OFFSET) // PITCH), int((u_max - U_OFFSET) // PITCH) + 1):
        for bj in range(int((v_min - V_OFFSET) // PITCH), int((v_max - V_OFFSET) // PITCH) + 1):
            u0 = U_OFFSET + bi * PITCH + STREET / 2
            v0 = V_OFFSET + bj * PITCH + STREET / 2
            bx, by = from_grid(u0 + 32.0, v0 + 32.0)
            probe, relief = relief_at(bx, by, 30.0)
            plain = max(probe) < plain_level + 14.0 and relief < 4.5
            centrality = math.hypot(bx - 150.0, by + 60.0)
            dense = plain and rng.random() < min(0.97, max(0.45, 1.5 - centrality / 900.0))
            if dense:
                rows = [
                    (u0 + 16.0, v0 + 0.6 + depth / 2, 0.0, ("v", v0 - STREET / 2), (u0, u0 + 32.0)),
                    (u0 + 48.0, v0 + 0.6 + depth / 2, 0.0, ("v", v0 - STREET / 2), (u0 + 32.0, u0 + 64.0)),
                    (u0 + 16.0, v0 + 64.0 - 0.6 - depth / 2, math.pi, ("v", v0 + 64.0 + STREET / 2), (u0, u0 + 32.0)),
                    (u0 + 48.0, v0 + 64.0 - 0.6 - depth / 2, math.pi, ("v", v0 + 64.0 + STREET / 2),
                     (u0 + 32.0, u0 + 64.0)),
                    (u0 + 0.6 + depth / 2, v0 + 32.0, -math.pi / 2, ("u", u0 - STREET / 2), (v0 + 16.0, v0 + 48.0)),
                    (u0 + 64.0 - 0.6 - depth / 2, v0 + 32.0, math.pi / 2, ("u", u0 + 64.0 + STREET / 2),
                     (v0 + 16.0, v0 + 48.0)),
                ]
                for cu, cv, turn, (axis, line), (low, high) in rows:
                    along = Vector(rotate(16.0, 0.0, turn))
                    ends = [from_grid(cu + along.x, cv + along.y), from_grid(cu - along.x, cv - along.y),
                            from_grid(cu, cv)]
                    if not free(ends):
                        continue
                    x, y = ends[2]
                    row_probe, row_relief = relief_at(x, y, 12.0)
                    if row_relief > 5.0:
                        continue
                    z = sum(row_probe) / 4 - scene.datum - 0.15
                    if block_facing_main(axis, line, low, high):
                        key = f"row_tabernae_{rng.integers(0, TABERNAE_VARIANTS)}"
                    else:
                        key = f"row_{rng.integers(0, ROW_VARIANTS)}"
                    matrix = placement(x, y, z, GRID + turn)
                    placements[key].append(matrix)
                    rows_dense.append((x, y, z, key))
                x, y = from_grid(u0 + 32.0, v0 + 32.0)
                if free([(x, y)]):
                    z = sum(probe) / 4 - scene.datum - 0.15
                    roll = rng.random()
                    key = "domus_a" if roll < 0.5 else "domus_b" if roll < 0.9 else "kitchen_garden"
                    placements[key].append(placement(x, y, z, GRID + rng.integers(0, 4) * math.pi / 2))
                continue
            for ci in range(4):
                for cj in range(4):
                    interior = 0 < ci < 3 and 0 < cj < 3
                    if interior and not (ci == 1 and cj == 1):
                        continue
                    cu, cv = (u0 + 2 * cell, v0 + 2 * cell) if interior else (u0 + (ci + 0.5) * cell,
                                                                           v0 + (cj + 0.5) * cell)
                    x, y = from_grid(cu, cv)
                    if not free([(x, y)]):
                        continue
                    cell_probe, cell_relief = relief_at(x, y, 14.0 if interior else 7.0)
                    if cell_relief > 7.0:
                        continue
                    keep = (0.55 if interior else 0.4) if plain else (0.3 if interior else 0.16)
                    z = sum(cell_probe) / 4 - scene.datum - 0.15
                    if rng.random() > keep:
                        if not plain and cell_relief > 2.0 and rng.random() < 0.45:
                            gx = (scene.field.sample(x + 3, y) - scene.field.sample(x - 3, y)) / 6
                            gy = (scene.field.sample(x, y + 3) - scene.field.sample(x, y - 3)) / 6
                            uphill = math.atan2(gy, gx) - math.pi / 2
                            key = "terrace"
                            low = min(cell_probe) - scene.datum
                            placements[key].append(placement(x, y, low - 0.3, uphill))
                        elif rng.random() < 0.2:
                            trees.append((x + rng.uniform(-5, 5), y + rng.uniform(-5, 5)))
                        continue
                    if interior:
                        key = "kitchen_garden" if rng.random() < 0.5 else "domus_b"
                        placements[key].append(placement(x, y, z, GRID + rng.integers(0, 4) * math.pi / 2))
                        continue
                    side = "south" if cj == 0 else "north" if cj == 3 else "west" if ci == 0 else "east"
                    turn = {"south": 0.0, "east": math.pi / 2, "north": math.pi, "west": -math.pi / 2}[side]
                    fu, fv = {"south": (0, -1), "east": (1, 0), "north": (0, 1), "west": (-1, 0)}[side]
                    key = f"house_single_{'ab'[rng.integers(0, 2)]}"
                    shift = cell / 2 - 4.5 - 0.6
                    sx, sy = from_grid(cu + fu * shift, cv + fv * shift)
                    placements[key].append(placement(sx, sy, z, GRID + turn))
    for key, matrices in placements.items():
        scene.instances("city", key, HOUSES[key], matrices)
    return trees, {key: len(matrices) for key, matrices in placements.items()}, rows_dense


def scatter(scene, rng, count, accept):
    points = []
    attempts = 0
    while len(points) < count and attempts < count * 40:
        attempts += 1
        x = rng.uniform(-HALF + 20, HALF - 20)
        y = rng.uniform(-HALF + 20, HALF - 20)
        if accept(x, y):
            points.append((x, y))
    return points


def tree_frames(scene, points, rng, scale_range=(0.8, 1.2)):
    return [placement(x, y, scene.ground(x, y) - 0.2, rng.uniform(0, 2 * math.pi), rng.uniform(*scale_range))
            for x, y in points]


def road_distance(x, y):
    best = 1e9
    for road in ROADS:
        for (x0, y0), (x1, y1) in zip(road[:-1], road[1:]):
            dx, dy = x1 - x0, y1 - y0
            t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def build_landscape(scene, exclusions, plain_level, city_trees, sanctuary_trees, plane_points, rng):
    field = scene.field
    slope = field.slope()

    def slope_at(x, y):
        column_index = int(np.clip((x + HALF) / field.spacing, 0, field.samples - 1))
        row = int(np.clip((y + HALF) / field.spacing, 0, field.samples - 1))
        return float(slope[row, column_index])

    def is_hill(x, y):
        return slope_at(x, y) > 0.08 or field.sample(x, y) > plain_level + 22

    def outside(x, y):
        return not point_in_polygon(x, y, WALL_TRACE) and nearest_on_trace((x, y), WALL_TRACE)[0] > 14.0

    garrigue = scatter(scene, rng, 1500, lambda x, y: is_hill(x, y) and not exclusions.blocked(x, y) and (
        outside(x, y) or rng.random() < 0.7) and road_distance(x, y) > 8)
    oaks = scatter(scene, rng, 1100, lambda x, y: is_hill(x, y) and not exclusions.blocked(x, y) and (
        outside(x, y) or rng.random() < 0.4) and road_distance(x, y) > 10)
    olives = []
    vines = []
    for bi in range(-12, 13):
        for bj in range(-24, 25):
            u0, v0 = bi * 118.0, bj * 59.0
            cx, cy = from_grid(u0 + 59.0, v0 + 29.5)
            if abs(cx) > HALF - 60 or abs(cy) > HALF - 60:
                continue
            parcel = ((bi * 73856093) ^ (bj * 19349663)) % 1000 / 1000.0
            if not outside(cx, cy) or slope_at(cx, cy) > 0.14:
                continue
            if 0.93 < parcel < 0.975:
                for i in range(11):
                    for j in range(5):
                        x, y = from_grid(u0 + 5 + i * 10.5, v0 + 5 + j * 10.5)
                        if outside(x, y) and road_distance(x, y) > 6 and not exclusions.blocked(x, y):
                            olives.append((x, y))
            elif 0.43 < parcel < 0.57 and math.hypot(cx - 300, cy + 600) < 520:
                for j in range(26):
                    for i in range(5):
                        u, v = u0 + 12.0 + i * 22.0, v0 + 1.6 + j * 2.2
                        x, y = from_grid(u, v)
                        if outside(x, y) and road_distance(x, y) > 6 and not exclusions.blocked(x, y):
                            vines.append(placement(x, y, scene.ground(x, y) - 0.05, GRID))
    cypresses = []
    for road in ROADS[:4]:
        for (x0, y0), (x1, y1) in zip(road[:-1], road[1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            for k in range(int(length / 16)):
                t = (k + 0.5) * 16 / length
                if rng.random() < 0.4:
                    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
                    side = 1 if rng.random() < 0.5 else -1
                    x, y = x0 + (x1 - x0) * t + nx * side * 9, y0 + (y1 - y0) * t + ny * side * 9
                    if outside(x, y) and abs(x) < HALF - 10 and abs(y) < HALF - 10 and not exclusions.blocked(x, y):
                        cypresses.append((x, y))
    cypresses.extend(sanctuary_trees)
    pines = scatter(scene, rng, 60, lambda x, y: outside(x, y) and not is_hill(x, y) and road_distance(x, y) > 12)
    scene.instances("vegetation", "tree_scrub", lambda: buildings.scrub(1.8, 1),
                    tree_frames(scene, garrigue, rng, (0.7, 1.6)), cast_shadow=False)
    scene.instances("vegetation", "tree_holm_oak", lambda: buildings.holm_oak(7.5, 2), tree_frames(scene, oaks, rng))
    scene.instances("vegetation", "tree_olive", lambda: buildings.olive_tree(4.6, 3),
                    tree_frames(scene, olives + city_trees, rng, (0.8, 1.15)), cast_shadow=False)
    scene.instances("vegetation", "tree_cypress", lambda: buildings.cypress(12.0, 4),
                    tree_frames(scene, cypresses, rng, (0.8, 1.25)))
    scene.instances("vegetation", "tree_pine", lambda: buildings.umbrella_pine(13.0, 5), tree_frames(scene, pines, rng))
    scene.instances("vegetation", "tree_plane", lambda: buildings.plane_tree(15.0, 6),
                    tree_frames(scene, plane_points, rng, (0.9, 1.1)))
    scene.instances("vegetation", "vine_row", lambda: buildings.vine_row(20.0), vines, cast_shadow=False)
    tombs = {"tomb_enclosure": [], "tomb_mausoleum": [], "tomb_stele": [], "tomb_altar": []}
    for road, reach in ((ROADS[0], 420.0), (ROADS[2], 260.0)):
        (x0, y0), (x1, y1) = road[0], road[1]
        length = math.hypot(x1 - x0, y1 - y0)
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        along = 38.0
        index = 0
        while along < min(reach, length - 5):
            for side in (-1, 1):
                if rng.random() < 0.25:
                    continue
                offset = 6.5 + rng.uniform(0, 5)
                x = x0 + dx * along - dy * side * offset
                y = y0 + dy * along + dx * side * offset
                if not outside(x, y) or exclusions.blocked(x, y):
                    continue
                angle = math.atan2(dy, dx) + (math.pi / 2 if side > 0 else -math.pi / 2)
                roll = rng.random()
                key = ("tomb_stele" if roll < 0.35 else "tomb_enclosure" if roll < 0.65 else "tomb_altar"
                       if roll < 0.85 else "tomb_mausoleum")
                tombs[key].append(placement(x, y, scene.ground(x, y), angle))
                index += 1
            along += rng.uniform(6.0, 11.0)
    scene.instances("necropolis", "tomb_enclosure", buildings.funerary_enclosure, tombs["tomb_enclosure"])
    scene.instances("necropolis", "tomb_mausoleum", buildings.mausoleum, tombs["tomb_mausoleum"])
    scene.instances("necropolis", "tomb_stele", buildings.funerary_stele, tombs["tomb_stele"])
    scene.instances("necropolis", "tomb_altar", buildings.tomb_altar, tombs["tomb_altar"])
    farms = scatter(scene, rng, 14, lambda x, y: outside(x, y) and not is_hill(x, y) and 40 < road_distance(x, y)
                    < 160 and min(math.hypot(x - a, y - b) for a, b in WALL_TRACE) > 200)
    scene.instances("city", "farmstead", buildings.farmstead, [placement(x, y, scene.ground(x, y) - 0.1,
                                                                        GRID + rng.integers(0, 4) * math.pi / 2)
                                                              for x, y in farms])
    return {"scrub": len(garrigue), "holm_oak": len(oaks), "olive": len(olives) + len(city_trees),
            "cypress": len(cypresses), "pine": len(pines), "plane": len(plane_points), "vine_rows": len(vines),
            "tombs": sum(len(value) for value in tombs.values()), "farms": len(farms)}, farms


def amphitheatre_radius(bearing_degrees):
    phi = math.radians(bearing_degrees - AMPHITHEATRE_BEARING)
    a, b = AMPHITHEATRE_AXES
    return a * b / math.hypot(b * math.cos(phi), a * math.sin(phi))


def bearing_point(center, bearing_degrees, distance):
    bearing = math.radians(bearing_degrees)
    return center[0] + distance * math.sin(bearing), center[1] + distance * math.cos(bearing)


def world_point(scene, x, y, height):
    return Vector((x, y, scene.ground(x, y) + height))


def viewpoints(scene, layout, gate_frames, basin_frame, north_bearing):
    mc_target = Vector(rotate(0.0, layout.axis_front, GRID)).to_3d()
    mc_target.z = 8.5
    cx, cy = rotate(-12.0, layout.axis_front + 36.0, GRID)
    center = SITES["amphitheatre"]
    eye_bearing = north_bearing - 12.0
    cam_a = bearing_point(center, eye_bearing, amphitheatre_radius(eye_bearing) + 45.0)
    aim_bearing = north_bearing - 14.0
    facade = bearing_point(center, aim_bearing, amphitheatre_radius(aim_bearing))
    arena_z = scene.arena_level - scene.datum
    gate = gate_frames["porte_auguste"]
    gate_eye = gate @ Vector((0.0, 28.0, 0.0))
    gate_target = gate @ Vector((0.0, 0.2, 8.6))
    kx, ky = SITES["castellum"]
    castellum_level = scene.ground(kx, ky)
    castellum_eye = Vector((kx, ky, castellum_level)) + Vector((*rotate(2.0, 9.0, GRID), 13.0))
    castellum_target = Vector((kx, ky, castellum_level)) + Vector((*rotate(0.0, -0.8, GRID), -0.6))
    city = Vector((60.0, -20.0))
    eye_xy = city + Vector((math.sin(math.radians(150.0)), math.cos(math.radians(150.0)))) * 1200.0
    heading = (city - eye_xy).normalized()
    pitch = math.radians(-10.0)
    aerial_eye = Vector((eye_xy.x, eye_xy.y, scene.ground(*city) + 400.0))
    aerial_target = aerial_eye + Vector((heading.x * math.cos(pitch), heading.y * math.cos(pitch), math.sin(pitch))) * 900
    points = {
        "maison-carree": (world_point(scene, cx, cy, 1.7), mc_target),
        "amphitheatre": (Vector((cam_a[0], cam_a[1], arena_z + 2.0)), Vector((facade[0], facade[1], arena_z + 9.0))),
        "fontaine-tour-magne": (basin_frame @ Vector((6.0, -30.0, 4.0)), basin_frame @ Vector((0.0, 40.0, 9.0))),
        "porte-d-auguste": (Vector((gate_eye.x, gate_eye.y, scene.ground(gate_eye.x, gate_eye.y) + 1.7)), gate_target),
        "eau-castellum": (castellum_eye, castellum_target),
        "vue-d-ensemble": (aerial_eye, aerial_target),
    }
    return points


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))


def camera_exclusions(exclusions, points):
    for key, (eye, target) in points.items():
        if key in ("vue-d-ensemble", "eau-castellum"):
            continue
        exclusions.corridor((eye.x, eye.y), (target.x, target.y), 12.0 if key == "amphitheatre" else 9.0)
        exclusions.circle(eye.x, eye.y, 14.0)


def site_exclusions():
    exclusions = Exclusions()
    exclusions.rectangle(*rotate(0.0, 24.0, GRID), 40.0, 58.0, GRID)
    ax, ay = SITES["amphitheatre"]
    a, b = AMPHITHEATRE_AXES
    exclusions.ellipse(ax, ay, a + 22, b + 22, AMPHITHEATRE_BEARING)
    bx, by = SITES["basin"]
    exclusions.rectangle(bx - 30, by + 30, 100.0, 85.0, GRID)
    for name, radius in (("castellum", 40.0), ("porte_auguste", 34.0), ("porte_france", 30.0), ("tour_magne", 34.0)):
        exclusions.circle(*SITES[name], radius)
    for gate in SECONDARY_GATES:
        exclusions.circle(*gate, 26.0)
    exclusions.rectangle(*from_grid(*THERMAE_GRID), 36.0, 36.0, GRID)
    return exclusions


def resample(points, spacing):
    out = [Vector(points[0])]
    for start, end in zip(points[:-1], points[1:]):
        a, b = Vector(start), Vector(end)
        length = (b - a).length
        count = max(int(round(length / spacing)), 1)
        for k in range(1, count + 1):
            out.append(a + (b - a) * (k / count))
    return out


def add_route(scene, name, points, height=0.0, spacing=10.0, absolute=None):
    root = scene.root("life")
    created = []
    for index, point in enumerate(resample(points, spacing)):
        if absolute is not None:
            z = absolute(point)
        else:
            z = scene.ground(point.x, point.y) + height
        empty = new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation((point.x, point.y, z)))
        created.append(empty)
    scene.route_count += 1
    return len(created)


def grid_points(pairs):
    return [from_grid(u, v) for u, v in pairs]


def forum_points(pairs):
    return [rotate(x, y, GRID) for x, y in pairs]




def build_routes(scene, layout, gate_frames, basin_frame):
    gate = gate_frames["porte_auguste"]

    def gate_world(x, y):
        return tuple((gate @ Vector((x, y, 0.0))).to_2d())

    inner_u = to_grid(*gate_world(0.0, -18.0))[0]
    road = ROADS[0]
    start = tuple(Vector(road[1]) + (Vector(road[2]) - Vector(road[1])).normalized() * 160.0)
    for name, lane in (("voie-domitienne-nord", 2.55), ("voie-domitienne-sud", -2.55)):
        offset = 1.6 if lane > 0 else -1.6
        points = [start, road[1], gate_world(lane, 40.0), gate_world(lane, 6.0), gate_world(lane, -16.0)]
        points += grid_points([(inner_u - 12.0, V_OFFSET + offset), (300.0, V_OFFSET + offset)])
        add_route(scene, name, points, 0.15)
    add_route(scene, "decumanus-nord", grid_points([(inner_u - 14.0, V_OFFSET + 3.4), (44.0, V_OFFSET + 3.4)]), 0.36)
    add_route(scene, "decumanus-sud", grid_points([(inner_u - 14.0, V_OFFSET - 3.4), (44.0, V_OFFSET - 3.4)]), 0.36)
    add_route(scene, "forum-est", forum_points([(31.5, -26.0), (31.5, 54.0)]), absolute=lambda point: 0.45)
    add_route(scene, "forum-ouest", forum_points([(-31.5, 54.0), (-31.5, -26.0)]), absolute=lambda point: 0.45)
    add_route(scene, "forum-portique-sud", forum_points([(-30.0, -27.5), (30.0, -27.5)]), absolute=lambda point: 0.45)
    add_route(scene, "forum-centre", forum_points([(12.0, 54.0), (12.0, 26.0), (-12.0, 26.0), (-12.0, 54.0)]),
              absolute=lambda point: 0.02)
    front = layout.front
    stair = [(2.2, front + 8.0, 0.02), (2.2, front + 0.1, 0.05), (2.2, front - 4.4, 2.85), (2.2, front - 9.0, 2.85)]
    root = scene.root("life")
    for index, (x, y, z) in enumerate(stair):
        new_empty(f"walk_marches-temple_{index:02d}", scene.collection, root,
                  Matrix.Translation((*rotate(x, y, GRID), z)))
    scene.route_count += 1
    cx, cy, angle, arena_z = amphitheatre_frame(scene)
    a, b = AMPHITHEATRE_AXES
    for name, (t0, t1) in (("arenes-nord", (0.15, math.pi - 0.15)),
                           ("arenes-sud", (math.pi + 0.15, 2 * math.pi - 0.15))):
        ring = []
        for t in np.linspace(t0, t1, 30):
            px, py = ellipse_point(a + 7.0, b + 7.0, t)
            wx, wy = rotate(px, py, angle)
            ring.append((cx + wx, cy + wy))
        add_route(scene, name, ring, spacing=11.0, absolute=lambda point: arena_z + 0.07)
    north_gate = bearing_point(SITES["amphitheatre"], scene.north_bearing,
                               amphitheatre_radius(scene.north_bearing) + 4.0)
    approach_v = to_grid(*north_gate)[1]
    add_route(scene, "arenes-acces", grid_points([(183.4, V_OFFSET - 6.0), (183.4, approach_v + 30.0)])
              + [north_gate], 0.36)
    add_route(scene, "cardo-sud", grid_points([(39.4, -250.0), (39.4, -40.0)]), 0.36)
    add_route(scene, "cardo-nord", grid_points([(-39.4, 90.0), (-39.4, 300.0)]), 0.36)
    add_route(scene, "rue-des-propylees", grid_points([(-60.0, 302.9), (-420.0, 302.9)]), 0.36)
    level = basin_frame.translation.z
    portico = [tuple((basin_frame @ Vector((x, -43.5, 0.0))).to_2d()) for x in (-44.0, 44.0)]
    add_route(scene, "fontaine-portique", portico, absolute=lambda point: level + 0.45)
    walk = [tuple((basin_frame @ Vector((x, y, 0.0))).to_2d()) for x, y in ((-26.0, -16.0), (26.0, -16.0),
                                                                           (26.0, 15.5), (-26.0, 15.5))]
    add_route(scene, "fontaine-bassin", walk, absolute=lambda point: level + 0.05)
    kx, ky = SITES["castellum"]
    add_route(scene, "castellum", [(kx + x, ky + y) for x, y in rotate_all(((-12.0, -42.0), (-12.0, -10.0),
                                                                           (12.0, -10.0)))], 0.07)
    france = ROADS[2]
    direction = (Vector(france[1]) - Vector(france[0])).normalized()
    add_route(scene, "porte-de-france", [tuple(Vector(france[0]) + direction * 150.0), france[0],
                                         tuple(Vector(france[0]) - direction * 40.0)], 0.15)


def rotate_all(points):
    return [rotate(x, y, GRID) for x, y in points]


def facing(x, y, tx, ty):
    return math.atan2(-(tx - x), ty - y)


CITIZENS = [("fig_toga", 3), ("fig_toga_gesture", 2), ("fig_matron", 2), ("fig_worker", 1), ("fig_merchant", 1),
            ("fig_child", 1), ("fig_woman", 1), ("fig_porter", 1), ("fig_rural", 0.6)]
COMMONERS = [("fig_worker", 3), ("fig_porter", 2), ("fig_woman", 2), ("fig_rural", 2), ("fig_merchant", 1),
             ("fig_child", 1.5), ("fig_matron", 1), ("fig_toga", 0.6)]


def pick(rng, weights):
    total = sum(weight for _, weight in weights)
    roll = rng.random() * total
    for key, weight in weights:
        roll -= weight
        if roll <= 0:
            return key
    return weights[-1][0]


def cluster(scene, rng, frame, x, y, z, count, weights):
    for index in range(count):
        angle = 2 * math.pi * index / count + rng.uniform(-0.3, 0.3)
        radius = rng.uniform(0.55, 0.95) if count > 1 else 0.0
        px, py = x + radius * math.cos(angle), y + radius * math.sin(angle)
        turn = facing(px, py, x, y) if count > 1 else rng.uniform(0, 2 * math.pi)
        scene.add(pick(rng, weights), frame @ placement(px, py, z, turn + rng.uniform(-0.3, 0.3)))


def on_ground(scene, x, y, lift, turn):
    return placement(x, y, scene.ground(x, y) + lift, turn)


def forum_life(scene, rng, layout):
    origin = placement(0.0, 0.0, 0.0, GRID)
    front = layout.front
    altar_y = front + 6.5
    for _ in range(18):
        x, y = 0.0, 0.0
        for _attempt in range(30):
            x, y = rng.uniform(-24.0, 24.0), rng.uniform(-20.0, 52.0)
            if not (abs(x) < 9.5 and y < altar_y + 9.0) and not (abs(abs(x) - 21.0) < 2.5):
                break
        cluster(scene, rng, origin, x, y, 0.02, int(rng.integers(1, 6)), CITIZENS)
    for _ in range(14):
        step = int(rng.integers(0, 15))
        x = rng.uniform(-5.2, 5.2)
        y = front - step * 0.3 - 0.15
        turn = float(rng.choice([0.0, 0.3, -0.3, math.pi]))
        scene.add(pick(rng, CITIZENS), origin @ placement(x, y, (step + 1) * 0.19, turn))
    scene.add("fig_priest", origin @ placement(0.0, altar_y + 1.9, 0.02, math.pi))
    for x in (-1.1, 1.1):
        scene.add("fig_child", origin @ placement(x, altar_y + 2.1, 0.02, math.pi))
    scene.add("fig_worker", origin @ placement(3.0, altar_y + 0.6, 0.02, math.pi / 2))
    scene.add("animal_ox", origin @ placement(4.6, altar_y + 0.5, 0.02, math.pi / 2))
    for index in range(16):
        angle = math.radians(15 + 150 * index / 15)
        radius = 6.5 + (index % 2) * 1.2
        x, y = radius * math.cos(angle), altar_y + 1.0 + radius * math.sin(angle)
        key = pick(rng, [("fig_toga", 4), ("fig_toga_gesture", 1), ("fig_matron", 2), ("fig_child", 1)])
        scene.add(key, origin @ placement(x, y, 0.02, facing(x, y, 0.0, altar_y)))
    for side in (-1, 1):
        for y in (4.0, 16.0, 30.0, 42.0):
            key = "market_stall_a" if int(y + side) % 3 else "market_stall_b"
            scene.add(key, origin @ placement(side * 21.0, y, 0.02, -side * math.pi / 2))
            cluster(scene, rng, origin, side * 18.6, y + rng.uniform(-1, 1), 0.02, int(rng.integers(1, 3)),
                    COMMONERS)
    return origin @ Vector((0.0, altar_y, 2.0))


def street_life(scene, rng, sidewalks, fountain_frames):
    busy = [SITES["maison_carree"], SITES["porte_auguste"], SITES["amphitheatre"], from_grid(*THERMAE_GRID)]

    def crowd(axis, line, along):
        x, y = from_grid(*((along, line) if axis == "v" else (line, along)))
        near = min(math.hypot(x - bx, y - by) for bx, by in busy) < 260.0
        return int(rng.integers(1, 5)) if near else int(rng.integers(0, 2))

    entries = [entry for entry in sidewalks for _ in range(crowd(*entry))]
    for axis, line, along in entries:
        side = float(rng.choice([-1.0, 1.0]))
        position = along + rng.uniform(-6.0, 6.0)
        offset = side * rng.uniform(3.0, 3.9)
        u, v = (position, line + offset) if axis == "v" else (line + offset, position)
        x, y = from_grid(u, v)
        walk_z = scene.ground(*from_grid(*((position, line) if axis == "v" else (line, position)))) + 0.36
        heading = GRID + (0.0 if axis == "u" else -math.pi / 2) + float(rng.choice([0.0, math.pi]))
        roll = rng.random()
        if roll < 0.08:
            u2, v2 = (position, line + side * 1.2) if axis == "v" else (line + side * 1.2, position)
            mx, my = from_grid(u2, v2)
            scene.add(str(rng.choice(["pack_mule", "pack_donkey"])), placement(mx, my, walk_z - 0.24, heading))
            scene.add("fig_rural", placement(mx, my, walk_z - 0.24, heading) @ placement(0.8, 1.3, 0.0))
        elif roll < 0.13:
            scene.add("animal_dog", placement(x, y, walk_z, rng.uniform(0, 2 * math.pi)))
        elif roll < 0.35:
            cluster(scene, rng, Matrix.Identity(4), x, y, walk_z, int(rng.integers(2, 4)), COMMONERS)
        else:
            scene.add(pick(rng, COMMONERS), placement(x, y, walk_z, heading))
    for frame in fountain_frames:
        for index in range(int(rng.integers(2, 4))):
            local = [(0.0, -1.3), (-1.5, -0.2), (1.5, -0.3)][index]
            point = frame @ Vector((local[0], local[1], 0.0))
            turn = facing(point.x, point.y, frame.translation.x, frame.translation.y)
            key = ["fig_woman", "fig_child", "fig_porter"][index] if rng.random() < 0.7 else "fig_matron"
            scene.add(key, placement(point.x, point.y, frame.translation.z, turn))


def road_life(scene, rng, gate_frames):
    gate = gate_frames["porte_auguste"]
    road = ROADS[0]
    direction = (Vector(road[1]) - Vector(road[0])).normalized()
    side_vector = Vector((-direction.y, direction.x))
    inward = facing(0.0, 0.0, -direction.x, -direction.y)
    outward = inward + math.pi
    scene.add("ox_cart", gate @ placement(2.55, 10.5, 0.12, math.pi))
    scene.add("fig_rural", gate @ placement(-2.4, 7.0, 0.12, math.pi))
    for key, along, lane, heading in (("ox_cart", 150.0, -1.4, outward), ("mule_wagon", 95.0, 1.4, inward),
                                      ("pack_mule", 60.0, -1.6, outward), ("pack_donkey", 180.0, 1.5, inward),
                                      ("pack_mule", 250.0, 1.3, inward), ("pack_donkey", 40.0, 1.8, inward)):
        base = Vector(road[0]) + direction * along + side_vector * lane
        scene.add(key, on_ground(scene, base.x, base.y, 0.15, heading))
        if key.startswith("pack"):
            scene.add("fig_rural", on_ground(scene, base.x, base.y, 0.15, heading) @ placement(-0.8, 1.2, 0.0))
    for _ in range(24):
        base = Vector(road[0]) + direction * rng.uniform(25.0, 330.0) + side_vector * rng.uniform(-2.6, 2.6)
        heading = inward if rng.random() < 0.55 else outward
        key = pick(rng, [("fig_rural", 3), ("fig_porter", 2), ("fig_worker", 2), ("fig_woman", 1), ("fig_matron", 1),
                         ("fig_toga", 0.5)])
        scene.add(key, on_ground(scene, base.x, base.y, 0.15, heading))
    for _ in range(5):
        base = Vector(road[0]) + direction * rng.uniform(20.0, 200.0) + side_vector * 4.5
        scene.add("animal_dog", on_ground(scene, base.x, base.y, 0.0, rng.uniform(0, 6.28)))
    for local in ((-6.4, 4.0), (-6.4, -10.0), (6.4, 3.0), (-4.0, 14.0), (4.5, 18.0), (0.0, -22.0)):
        point = gate @ Vector((local[0], local[1], 0.0))
        scene.add(pick(rng, COMMONERS), on_ground(scene, point.x, point.y, 0.05, rng.uniform(0, 6.28)))


def amphitheatre_life(scene, rng):
    cx, cy, angle, arena_z = amphitheatre_frame(scene)
    a, b = AMPHITHEATRE_AXES
    for index in range(8):
        t = 2 * math.pi * (index + 0.5) / 8 + 0.2
        px, py = ellipse_point(a + 14.0, b + 14.0, t)
        wx, wy = rotate(px, py, angle)
        x, y = cx + wx, cy + wy
        scene.add("market_stall_a" if index % 2 else "market_stall_b",
                  placement(x, y, arena_z + 0.07, facing(x, y, cx, cy) + math.pi))
    for _ in range(42):
        t = rng.uniform(0, 2 * math.pi)
        grow = rng.uniform(4.0, 19.0)
        px, py = ellipse_point(a + grow, b + grow, t)
        wx, wy = rotate(px, py, angle)
        cluster(scene, rng, Matrix.Identity(4), cx + wx, cy + wy, arena_z + 0.07, int(rng.integers(1, 5)), COMMONERS)
    for _ in range(4):
        px, py = ellipse_point(a + 10, b + 10, rng.uniform(0, 2 * math.pi))
        wx, wy = rotate(px, py, angle)
        scene.add("animal_dog", placement(cx + wx, cy + wy, arena_z + 0.07, rng.uniform(0, 6.28)))


def sanctuary_life(scene, rng, basin_frame):
    for _ in range(16):
        if rng.random() < 0.7:
            x, y = rng.uniform(-24.0, 24.0), float(rng.choice([-16.8, 16.8]))
        else:
            x, y = float(rng.choice([-25.0, 25.0])), rng.uniform(-14.0, 14.0)
        cluster(scene, rng, basin_frame, x, y, 0.05, int(rng.integers(1, 4)), CITIZENS)
    for _ in range(6):
        cluster(scene, rng, basin_frame, rng.uniform(-40, 40), -43.0, 0.45, int(rng.integers(1, 3)), CITIZENS)
    scene.add("fig_priest", basin_frame @ placement(0.0, -2.6, 1.5, 0.0))
    kx, ky = SITES["castellum"]
    for local in ((-8.5, -9.0), (-9.5, -8.0), (9.0, -9.5)):
        x, y = rotate(*local, GRID)
        scene.add("fig_worker", on_ground(scene, kx + x, ky + y, 0.05, rng.uniform(0, 6.28)))


def countryside_life(scene, rng, farms):
    tx, ty = SITES["tour_magne"]
    herd = None
    for _ in range(300):
        x, y = tx + rng.uniform(-260, 120), ty + rng.uniform(-60, 260)
        if abs(x) < HALF - 40 and abs(y) < HALF - 40 and not point_in_polygon(x, y, WALL_TRACE) \
                and nearest_on_trace((x, y), WALL_TRACE)[0] > 40:
            herd = (x, y)
            break
    if herd is not None:
        for _ in range(18):
            x, y = herd[0] + rng.normal(0, 9), herd[1] + rng.normal(0, 9)
            scene.add("animal_goat", on_ground(scene, x, y, 0.0, rng.uniform(0, 6.28)))
        scene.add("fig_rural", on_ground(scene, herd[0] + 12, herd[1], 0.0, 1.0))
        scene.add("animal_dog", on_ground(scene, herd[0] + 10, herd[1] + 3, 0.0, 2.0))
    for x, y in farms:
        scene.add("animal_ox", on_ground(scene, x + 6, y - 6, 0.0, rng.uniform(0, 6.28)))
        scene.add(pick(rng, COMMONERS), on_ground(scene, x + 4, y - 4, 0.0, rng.uniform(0, 6.28)))


def build_life(scene, layout, gate_frames, basin_frame, fountain_frames, sidewalks, rows_dense, farms, rng):
    altar_smoke = forum_life(scene, rng, layout)
    street_life(scene, rng, sidewalks, fountain_frames)
    road_life(scene, rng, gate_frames)
    amphitheatre_life(scene, rng)
    sanctuary_life(scene, rng, basin_frame)
    countryside_life(scene, rng, farms)
    root = scene.root("life")
    smokes = [altar_smoke, basin_frame @ Vector((0.0, 0.0, 3.0))]
    tx, ty = from_grid(*THERMAE_GRID)
    smokes.append(placement(tx, ty, scene.ground(tx, ty), GRID) @ Vector((24.0, 22.0, 16.0)))
    near = sorted(rows_dense, key=lambda row: math.hypot(row[0] - 200.0, row[1] + 50.0))[:260]
    for index in sorted(rng.choice(len(near), min(10, len(near)), replace=False)):
        x, y, z, _ = near[int(index)]
        smokes.append(Vector((x, y, z + 10.5)))
    for x, y in farms[:3]:
        smokes.append(Vector((x, y + 6, scene.ground(x, y) + 6.0)))
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    flocks = [(SITES["tour_magne"], 70.0), (SITES["maison_carree"], 48.0), (SITES["amphitheatre"], 55.0),
              (SITES["basin"], 45.0), ((820.0, 40.0), 35.0)]
    for index, ((x, y), height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation((x, y, scene.ground(x, y) + height)))
    for index, (key, spec) in enumerate(life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda spec=spec: life.figure(spec), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"smoke_sources": len(smokes), "bird_flocks": len(flocks), "walker_variants": len(life.WALKERS)}


LIFE_BUILDS = {key: (lambda spec=spec: life.figure(spec)) for key, spec in life.FIGURES.items()}
LIFE_BUILDS.update({
    "animal_ox": lambda: life.animal("ox"),
    "animal_dog": lambda: life.animal("dog"),
    "animal_goat": lambda: life.animal("goat"),
    "pack_mule": lambda: life.pack_animal("mule"),
    "pack_donkey": lambda: life.pack_animal("donkey"),
    "ox_cart": life.ox_cart,
    "mule_wagon": life.mule_wagon,
    "market_stall_a": lambda: life.market_stall(0),
    "market_stall_b": lambda: life.market_stall(2, (0.72, 0.36, 0.26)),
    "statue_bronze": lambda: life.honorific_statue(True),
    "statue_marble": lambda: life.honorific_statue(False),
})


def place_life(scene):
    counts = {}
    for key, matrices in scene.placements.items():
        group = "statues" if key.startswith("statue") else "life"
        scene.instances(group, key, LIFE_BUILDS[key], matrices, cast_shadow=key.startswith(("fig_", "ox_cart",
                                                                                            "mule_wagon", "statue")),
                        occlusion=key.startswith("statue"))
        counts[key] = len(matrices)
    return counts


def preview_points(points, scene):
    gx, gy = SITES["porte_auguste"]
    inner = to_grid(gx, gy)[0]
    street_eye = from_grid(inner - 48.0, V_OFFSET - 1.4)
    street_target = from_grid(inner - 150.0, V_OFFSET + 1.0)
    return {
        "aerial": points["vue-d-ensemble"],
        "forum": points["maison-carree"],
        "amphitheatre": points["amphitheatre"],
        "porte_auguste": points["porte-d-auguste"],
        "fontaine": points["fontaine-tour-magne"],
        "castellum": points["eau-castellum"],
        "rue": (world_point(scene, *street_eye, 1.75), world_point(scene, *street_target, 2.6)),
        "temps_reel": points["maison-carree"],
    }


def render_previews(options, scene_points):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(scene_points) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.16, aerosol=0.35)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 7.0, (1.0, 0.68, 0.42), 0.8)
    haze_volume(stage, 45000.0, 600.0, 0.00007, (0.78, 0.84, 0.95), 0.3)
    configure_render(1280, 720, options["samples"], exposure=0.0, volumetric_end=40000.0)
    timings = {}
    lenses = {"aerial": 30.0, "forum": 28.0, "amphitheatre": 32.0, "porte_auguste": 24.0, "fontaine": 24.0,
              "castellum": 24.0, "rue": 28.0, "temps_reel": 28.0}
    for name in names:
        eye, target = scene_points[name]
        realtime = name == "temps_reel"
        bpy.context.scene.eevee.use_raytracing = not realtime
        bpy.context.scene.eevee.use_fast_gi = not realtime
        rig = camera(stage, f"cam_{name}", eye, target, lens=lenses.get(name, 35.0))
        path = os.path.join(CACHE, "previews", f"{name}.png")
        timings[name] = round(render_still(rig, path), 1)
        print(f"PREVIEW {name} {timings[name]} s", flush=True)
    return timings


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
    field, far_field, dem_urls = build_terrain()
    level, arena_level = flatten_sites(field)
    datum = level
    plain_level = level
    scene = Scene(tiles, field, datum)
    scene.arena_level = arena_level
    scene.route_count = 0
    terrain_objects(field, far_field, plain_level, datum, scene.collection, scene.root("terrain"))
    layout = build_maison_carree(scene)
    build_forum(scene, layout)
    scene.north_bearing = build_amphitheatre(scene)
    gate_frames, wall_counts = build_walls(scene)
    sanctuary_trees, plane_points, basin_frame = build_sanctuary(scene)
    build_roads(scene)
    points = viewpoints(scene, layout, gate_frames, basin_frame, scene.north_bearing)
    place_markers(scene, points)
    exclusions = site_exclusions()
    camera_exclusions(exclusions, points)
    street_counts, fountain_frames, sidewalks = build_streets(scene, exclusions, plain_level)
    rng = np.random.default_rng(7)
    city_trees, house_counts, rows_dense = build_city(scene, exclusions, plain_level, rng)
    counts, farms = build_landscape(scene, exclusions, plain_level, city_trees, sanctuary_trees, plane_points, rng)
    gate_out = gate_frames["porte_auguste"] @ Vector((0.0, 45.0, 0.0))
    kx, ky = SITES["castellum"]

    def castellum_hole(xs, ys):
        u = (xs - kx) * math.cos(GRID) + (ys - ky) * math.sin(GRID)
        v = -(xs - kx) * math.sin(GRID) + (ys - ky) * math.cos(GRID)
        return (np.abs(u) < 7.1) & (np.abs(v) < 7.1)

    patches = [("ground_amphitheatre", *SITES["amphitheatre"], 132.0, None),
               ("ground_castellum", kx, ky, 60.0, castellum_hole),
               ("ground_porte_auguste", gate_out.x, gate_out.y, 55.0, None)]
    for name, x, y, radius, hole in patches:
        ground_patch(scene, name, x, y, radius, plain_level, hole=hole)
    build_routes(scene, layout, gate_frames, basin_frame)
    life_counts = build_life(scene, layout, gate_frames, basin_frame, fountain_frames, sidewalks, rows_dense, farms,
                             rng)
    placed = place_life(scene)
    scene.flush()
    counts.update(wall_counts)
    counts["streets"] = street_counts
    counts["houses"] = house_counts
    counts["life"] = dict(placed, **life_counts)
    counts["walk_routes"] = scene.route_count
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    stored = sum(value.get("stored_triangles", 0) for key, value in statistics.items() if key != "total")
    statistics["total"]["stored_triangles"] = stored
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "nimes.glb")
    export_seconds = export_glb(glb, roots)
    report = {"datum_ngf_metres": round(float(datum), 2), "amphitheatre_ngf_metres": round(float(arena_level), 2),
              "sun": [SUN_AZIMUTH, SUN_ELEVATION], "counts": counts, "statistics": statistics,
              "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
              "elevation_sources": dem_urls, "elevation_licence": ETALAB_LICENCE, "texture_credits": credits,
              "terrain_infill": {"fort_vauban": FORT_VAUBAN, "embankments": EMBANKMENTS},
              "markers": {key: [list(map(lambda value: round(value, 2), eye)),
                                list(map(lambda value: round(value, 2), target))]
                          for key, (eye, target) in points.items()}}
    views = preview_points(points, scene)
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in views.items()})
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    report["previews"] = render_previews(options, views)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("datum_ngf_metres", "amphitheatre_ngf_metres", "counts",
                                                              "glb_bytes", "previews", "total_seconds")}), flush=True)


if __name__ == "__main__":
    main()

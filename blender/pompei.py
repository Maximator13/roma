import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from kit import buildings, nimes_detail, nimes_figures, nimes_scenery, pompei_life
from kit import arles_life
from kit import pompei_monuments as mon
from kit import pompei_plan as plan
from kit import pompei_terrain as pterrain
from kit import pompei_town as town
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement, unique_object
from kit.materials import baked_material, save_pixels
from kit.pompei_materials import build_library, remap
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, haze_volume,
                       render_still, sun_lamp)
from kit.terrain import grid_mesh, point_in_polygon, polygon_mask, polyline_distance, remove_faces_inside

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "pompei")
BLEND = os.path.join(CACHE, "work", "pompei.blend")
SUN_AZIMUTH = 231.0
SUN_ELEVATION = 51.0
FIELD_ORIGIN = (-16500.0, -15500.0)
FIELD_SIZE = 33000.0
FIELD_SPACING = 30.0
NEAR_HALF = 1100.0
NEAR_SPACING = 10.0
FAR_HALF = 16000.0
FAR_SPACING = 160.0
TOWN_CENTRE = (250.0, 150.0)
MAIN = dict(road=4.6, walk=2.0, kerb=0.38)
MINOR = dict(road=3.2, walk=1.3, kerb=0.32)
ROAD = dict(road=4.2, walk=0.9, kerb=0.25)
STREET_SITES = ("forum", "forum_east", "basilica", "apollo", "municipal", "venus", "forum_baths", "vettii",
                "stabian_baths", "central_baths", "theatre", "odeon", "quadriporticus", "triangular_forum",
                "palaestra", "amphitheatre")
WALKABLE = ("terrain", "streets", "forum", "venus", "vettii", "roads", "gates", "thermopolium")
VESUVIUS_AXIS = math.radians(148.0)


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 16}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def segment_distance(point, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (point - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (point - (a + ab * t)).length


def polyline_point_distance(point, points):
    return min(segment_distance(point, a, b) for a, b in zip(points[:-1], points[1:]))


class Surface:
    def __init__(self, objects):
        bpy.context.view_layer.update()
        vertices = []
        triangles = []
        offset = 0
        for item in objects:
            mesh = item.data
            co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
            mesh.vertices.foreach_get("co", co)
            mesh.calc_loop_triangles()
            tris = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get("vertices", tris)
            matrix = np.array(item.matrix_world)
            co = co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
            vertices.append(co)
            triangles.append(tris.reshape(-1, 3) + offset)
            offset += len(co)
        self.tree = BVHTree.FromPolygons(np.concatenate(vertices).tolist(), np.concatenate(triangles).tolist(),
                                         all_triangles=True)

    def height(self, x, y, hint, reach=3.0):
        hit = self.tree.ray_cast(Vector((x, y, hint + reach)), Vector((0.0, 0.0, -1.0)), reach + 8.0)
        return hint if hit[0] is None else hit[0].z


class Scene:
    def __init__(self, tiles, field):
        self.tiles = tiles
        self.field = field
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("Pompei")
        self.roots = {}
        self.pending = {}
        self.placements = {}
        self.surface = None

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def ground(self, x, y):
        return self.field.sample(x, y)

    def unique(self, group, builder, matrix=None):
        self.pending.setdefault(group, []).append((builder, matrix if matrix is not None else Matrix.Identity(4)))
        self.root(group)

    def flush(self, cast_shadow=None):
        for group, items in self.pending.items():
            merged = MeshBuilder()
            for builder, matrix in items:
                merged.merge(remap(builder), matrix, keep_local=True)
            created = unique_object(f"{group}_static.{len(self.roots[group].children):02d}", merged, self.collection,
                                    self.root(group), self.tiles)
            if cast_shadow is not None and group in cast_shadow:
                created["cast_shadow"] = cast_shadow[group]
        self.pending = {}

    def instances(self, group, key, build, matrices, cast_shadow=True):
        if not matrices:
            return None
        return self.library.place(key, lambda: remap(build()), self.collection, self.root(group), matrices,
                                  cast_shadow, False)

    def add(self, key, matrix):
        self.placements.setdefault(key, []).append(matrix)


def ash_veil(xs, ys):
    vx, vy = -5002.3, 7994.0
    dx, dy = xs - vx, ys - vy
    along = dx * math.sin(VESUVIUS_AXIS) + dy * math.cos(VESUVIUS_AXIS)
    across = -dx * math.cos(VESUVIUS_AXIS) + dy * math.sin(VESUVIUS_AXIS)
    width = 2500.0 + along * 0.25
    return smoothstep((along - 3000.0) / 3000.0) * smoothstep(1.0 - np.abs(across) / np.maximum(width, 1.0))


def mix(colour, other, weight):
    weight = np.clip(weight, 0.0, 1.0)[..., None]
    return colour * (1 - weight) + other * weight


def land_colour(xs, ys, heights, slope, masks_at):
    noise = pterrain.world_noise(xs, ys, 900.0, 3, 4)
    fine = pterrain.world_noise(xs, ys, 40.0, 4, 3)
    grain = pterrain.world_noise(xs, ys, 9.0, 5, 2)
    angle = math.radians(57.0)
    u = xs * math.cos(angle) - ys * math.sin(angle)
    v = xs * math.sin(angle) + ys * math.cos(angle)
    parcel_u = np.floor(u / 95.0).astype(np.int64)
    parcel_v = np.floor(v / 60.0).astype(np.int64)
    parcel = ((parcel_u * 73856093) ^ (parcel_v * 19349663)) % 1000 / 1000.0
    crops = np.array([[0.60, 0.53, 0.33], [0.48, 0.47, 0.27], [0.33, 0.39, 0.18], [0.54, 0.47, 0.31],
                      [0.42, 0.44, 0.26], [0.36, 0.41, 0.21], [0.30, 0.36, 0.17]])
    colour = crops[(parcel * len(crops)).astype(int) % len(crops)] * (0.88 + 0.2 * fine)[..., None]
    vine = parcel < 0.5
    rows = np.sin(u * 2 * math.pi / 2.4) > 0.0
    soil = np.array([0.50, 0.42, 0.31]) * (0.9 + 0.2 * grain)[..., None]
    leaves = np.array([0.22, 0.31, 0.12]) * (0.85 + 0.3 * grain)[..., None]
    colour = np.where(vine[..., None], np.where(rows[..., None], leaves, soil), colour)
    edge = (np.abs((u / 95.0) % 1.0 - 0.5) > 0.488) | (np.abs((v / 60.0) % 1.0 - 0.5) > 0.484)
    colour = np.where(edge[..., None], np.array([0.25, 0.31, 0.15]), colour)
    wood = np.dstack([0.17 + 0.07 * fine, 0.24 + 0.07 * fine, 0.11 + 0.04 * fine])
    scrub = np.dstack([0.36 + 0.06 * fine, 0.37 + 0.05 * fine, 0.24 + 0.04 * fine])
    rock = np.array([0.56, 0.54, 0.50]) * (0.85 + 0.25 * noise[..., None])
    hill = smoothstep((heights - 80.0) / 160.0) * (0.55 + 0.45 * noise)
    hill = np.maximum(hill, smoothstep((slope - 0.16) / 0.14))
    upland = mix(scrub, wood, smoothstep((fine - 0.35) / 0.3) * 0.8 + smoothstep((heights - 300.0) / 300.0) * 0.4)
    colour = mix(colour, upland, hill)
    colour = mix(colour, rock, smoothstep((slope - 0.8) / 0.3) * (fine > 0.4))
    volcano = masks_at["volcano"]
    radius = masks_at["volcano_radius"]
    flank_vines = 1 - smoothstep((heights - 480.0) / 140.0)
    vine_rows = np.where(rows[..., None], leaves, soil * 0.95)
    flank = mix(vine_rows, np.array([0.40, 0.42, 0.24]), (fine > 0.62).astype(float) * 0.7)
    patches = pterrain.world_noise(xs, ys, 700.0, 9, 3)
    flank = mix(flank, scrub, smoothstep((patches - 0.55) / 0.1) * 0.8)
    flank = mix(flank, wood, smoothstep((0.38 - patches) / 0.08))
    cover = mix(wood * 1.05, flank, flank_vines)
    ashen = np.dstack([0.40 + 0.06 * fine, 0.38 + 0.05 * fine, 0.35 + 0.05 * fine])
    barren = np.clip(smoothstep((heights - 960.0) / 110.0) + smoothstep((1050.0 - radius) / 300.0), 0, 1)
    cover = mix(cover, ashen, barren)
    weight = volcano * smoothstep((heights - 40.0) / 80.0)
    colour = mix(colour, cover, weight)
    sand = np.dstack([0.36 + 0.04 * grain, 0.33 + 0.04 * grain, 0.29 + 0.03 * grain])
    colour = mix(colour, sand, masks_at["beach"])
    ash = ash_veil(xs, ys) * (0.12 + 0.1 * noise)
    colour = mix(colour, np.array([0.66, 0.64, 0.60]), ash)
    colour *= (0.92 + 0.14 * noise)[..., None]
    return np.clip(colour, 0, 1)


def masks_sample(masks, field, xs, ys):
    spacing = field.spacing
    rows, columns = field.heights.shape
    c = np.clip(np.round((xs - field.x0) / spacing).astype(int), 0, columns - 1)
    r = np.clip(np.round((ys - field.y0) / spacing).astype(int), 0, rows - 1)
    return {name: value[r, c] for name, value in masks.items()}


def sun_shadow(field, xs, ys, heights, steps=40, reach=3000.0):
    azimuth = math.radians(SUN_AZIMUTH)
    direction = (math.sin(azimuth), math.cos(azimuth))
    slope = math.tan(math.radians(SUN_ELEVATION))
    clearance = np.full(heights.shape, np.inf)
    for step in range(1, steps + 1):
        distance = reach * (step / steps) ** 1.6
        ahead = field.sample(xs + direction[0] * distance, ys + direction[1] * distance)
        clearance = np.minimum(clearance, heights + distance * slope - ahead)
    return np.clip(clearance / 8.0 + 0.5, 0.0, 1.0)


def build_terrain(scene, masks, carve):
    field = scene.field
    resolution = 2048
    axis = np.linspace(-NEAR_HALF, NEAR_HALF, resolution)
    gx, gy = np.meshgrid(axis, axis)
    heights = field.sample(gx, gy)
    grad_y, grad_x = np.gradient(heights, axis[1] - axis[0])
    slope = np.hypot(grad_x, grad_y)
    at = masks_sample(masks, field, gx, gy)
    colour = land_colour(gx, gy, heights, slope, at)
    wall = [tuple(point) for point in plan.wall_trace()]
    inside = polygon_mask(wall, gx, gy)
    fine = pterrain.world_noise(gx, gy, 6.0, 5, 3)
    blotch = pterrain.world_noise(gx, gy, 35.0, 6, 3)
    town_ground = np.dstack([0.58 + 0.08 * fine, 0.55 + 0.07 * fine, 0.50 + 0.06 * fine])
    gardens = np.dstack([0.40 + 0.1 * fine, 0.42 + 0.08 * fine, 0.30 + 0.06 * fine])
    town_colour = mix(town_ground, gardens, smoothstep((0.5 - blotch) / 0.1))
    colour = np.where(inside[..., None], town_colour, colour)
    for points in plan.ROADS_OUT.values():
        distance = polyline_distance([tuple(p) for p in points], gx, gy)
        dust = smoothstep(1.0 - (distance - 2.0) / 3.0) * (~inside)
        colour = mix(colour, np.array([0.60, 0.56, 0.49]), dust)
    shadow = sun_shadow(field, gx, gy, heights)
    colour *= (0.72 + 0.28 * shadow)[..., None]
    image = save_pixels("terrain_colour", np.clip(colour, 0, 1), os.path.join(CACHE, "textures", "terrain_colour.jpg"),
                        quality=88)
    material = baked_material("terrain", image)
    material.use_backface_culling = True
    count = int(round(2 * NEAR_HALF / NEAR_SPACING)) + 1
    near_axis = np.linspace(-NEAR_HALF, NEAR_HALF, count)
    nx, ny = np.meshgrid(near_axis, near_axis)
    near = carve(nx, ny, field.sample(nx, ny))
    mesh = grid_mesh("terrain", near, NEAR_HALF, skirt_depth=30.0)
    mesh.materials.append(material)
    terrain = new_object("terrain", mesh, scene.collection, scene.root("terrain"))
    far_count = int(round(2 * FAR_HALF / FAR_SPACING)) + 1
    far_axis = np.linspace(-FAR_HALF, FAR_HALF, far_count)
    fx, fy = np.meshgrid(far_axis, far_axis)
    far_heights = field.sample(fx, fy)
    colour_axis = np.linspace(-FAR_HALF, FAR_HALF, 2048)
    cx, cy = np.meshgrid(colour_axis, colour_axis)
    ch = field.sample(cx, cy)
    cgy, cgx = np.gradient(ch, colour_axis[1] - colour_axis[0])
    far_colour = land_colour(cx, cy, ch, np.hypot(cgx, cgy), masks_sample(masks, field, cx, cy))
    far_colour *= (0.7 + 0.3 * sun_shadow(field, cx, cy, ch, 30, 6000.0))[..., None]
    far_image = save_pixels("terrain_far_colour", np.clip(far_colour, 0, 1),
                            os.path.join(CACHE, "textures", "terrain_far.jpg"), quality=86)
    far_material = baked_material("terrain_far", far_image)
    far_mesh = grid_mesh("terrain_far", far_heights, FAR_HALF, ring=(60000.0, 160.0))
    remove_faces_inside(far_mesh, NEAR_HALF - FAR_SPACING * 0.6)
    far_mesh.materials.append(far_material)
    far_object = new_object("terrain_far", far_mesh, scene.collection, scene.root("terrain"))
    far_object["cast_shadow"] = False
    water = MeshBuilder()
    reach = 70000.0
    water.polygon([(-reach, -reach, 0.0), (reach, -reach, 0.0), (reach, reach, 0.0), (-reach, reach, 0.0)], "water")
    sea = unique_object("sea", water, scene.collection, scene.root("terrain"), scene.tiles, cast_shadow=False,
                        ground_occlusion=False)
    return terrain, sea


def street_specs(scene, sites, wall):
    excluded = [sites[name] for name in STREET_SITES]
    gates = list(plan.GATES.values())

    def inside(point):
        near_gate = any((point - gate).length < 14.0 for gate in gates)
        if not near_gate and not point_in_polygon(point.x, point.y, wall):
            return False
        return not any(point_in_polygon(point.x, point.y, polygon) for polygon in excluded)

    specs = []
    for index, (points, kind) in enumerate(plan.streets()):
        spec = dict(MAIN if kind == "main" else MINOR)
        spec["points"] = [Vector(p[:2]) for p in points]
        spec["rank"] = (1000 if kind == "main" else 0) + index
        spec["kind"] = kind
        spec["inside"] = inside
        specs.append(spec)
    for name, points in plan.ROADS_OUT.items():
        spec = dict(ROAD)
        gate = points[0]
        trimmed = [Vector(points[0][:2])]
        for a, b in zip(points[:-1], points[1:]):
            trimmed.append(Vector(b[:2]))
            if (Vector(b[:2]) - gate).length > 260.0:
                break
        spec["points"] = trimmed
        spec["rank"] = 2000 + len(specs)
        spec["kind"] = "road"
        spec["inside"] = lambda point, gate=gate: (point - gate).length < 240.0 and not any(
            point_in_polygon(point.x, point.y, polygon) for polygon in excluded)
        specs.append(spec)
    for spec in specs:
        xs = [p.x for p in spec["points"]]
        ys = [p.y for p in spec["points"]]
        pad = spec["road"] / 2 + spec["walk"] + 2.0
        spec["box"] = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        spec["half"] = spec["road"] / 2 + spec["walk"]
        spec["distance"] = lambda point, points=spec["points"]: polyline_point_distance(point, points)
    return specs


def nearby(specs, point, pad=0.0):
    return [spec for spec in specs if spec["box"][0] - pad <= point.x <= spec["box"][2] + pad
            and spec["box"][1] - pad <= point.y <= spec["box"][3] + pad]


def build_streets(scene, specs):
    builder = MeshBuilder()
    stones = []
    for spec in specs:
        others = [other for other in specs if other is not spec and not (
            other["box"][2] < spec["box"][0] or other["box"][0] > spec["box"][2]
            or other["box"][3] < spec["box"][1] or other["box"][1] > spec["box"][3])]
        mesh, rows = town.street_mesh(spec, others, scene.ground)
        builder.merge(mesh)
        spec["rows"] = rows
        if spec["kind"] == "road":
            continue
        for other in others:
            if other["kind"] == "road":
                continue
            for index, (point, normal, z, road_on, walks, sink, distance) in enumerate(rows):
                gap = other["distance"](point) - (other["half"] + 1.2)
                if 0.0 <= gap < 2.0 and road_on and index % 1 == 0:
                    tangent = Vector((normal.y, -normal.x))
                    stones.append((point, tangent, z, spec))
                    break
    unique_object("streets", builder, scene.collection, scene.root("streets"), scene.tiles)
    return stones


def place_stepping_stones(scene, stones):
    seen = []
    matrices = {}
    for point, tangent, z, spec in stones:
        if any((point - other).length < 6.0 for other in seen):
            continue
        seen.append(point)
        count = 3 if spec["kind"] == "main" else 2
        key = f"stones_{count}"
        frame = (Matrix.Translation((point.x, point.y, z - max(0.0, 0.0)))
                 @ Matrix.Rotation(math.atan2(tangent.y, tangent.x), 4, "Z"))
        matrices.setdefault(key, []).append(frame)
    for key, frames in matrices.items():
        count = int(key[-1])
        spacing = 1.25 if count == 3 else 1.05
        scene.instances("streets", key, lambda count=count, spacing=spacing: town.stepping_stones(count, spacing,
                                                                                               0.36),
                        frames, cast_shadow=False)
    return len(seen)


class Occupancy:
    def __init__(self, cell=24.0):
        self.cell = cell
        self.cells = {}
        self.items = []

    def keys(self, polygon):
        xs = [p.x for p in polygon]
        ys = [p.y for p in polygon]
        for i in range(int(math.floor(min(xs) / self.cell)), int(math.floor(max(xs) / self.cell)) + 1):
            for j in range(int(math.floor(min(ys) / self.cell)), int(math.floor(max(ys) / self.cell)) + 1):
                yield (i, j)

    def overlaps(self, polygon):
        seen = set()
        for key in self.keys(polygon):
            for index in self.cells.get(key, ()):
                if index in seen:
                    continue
                seen.add(index)
                if convex_overlap(polygon, self.items[index]):
                    return True
        return False

    def add(self, polygon):
        self.items.append(polygon)
        for key in self.keys(polygon):
            self.cells.setdefault(key, []).append(len(self.items) - 1)

    def contains(self, point):
        key = (int(math.floor(point.x / self.cell)), int(math.floor(point.y / self.cell)))
        return any(point_in_polygon(point.x, point.y, self.items[index]) for index in self.cells.get(key, ()))


def convex_overlap(a, b):
    for polygon in (a, b):
        count = len(polygon)
        for index in range(count):
            p, q = polygon[index], polygon[(index + 1) % count]
            axis = Vector((q.y - p.y, p.x - q.x))
            pa = [axis.dot(point) for point in a]
            pb = [axis.dot(point) for point in b]
            if max(pa) <= min(pb) + 1e-6 or max(pb) <= min(pa) + 1e-6:
                return False
    return True


def rectangle(origin, along, inward, width, depth):
    return [origin - along * width / 2, origin + along * width / 2, origin + along * width / 2 + inward * depth,
            origin - along * width / 2 + inward * depth]


def unit_fits(polygon, specs, sites, wall_points, occupancy, own):
    centre = sum(polygon, Vector((0.0, 0.0))) / 4
    samples = polygon + [centre] + [(polygon[i] + polygon[(i + 1) % 4]) / 2 for i in range(4)]
    for point in samples:
        if not point_in_polygon(point.x, point.y, wall_points):
            return False
        if polyline_point_distance(point, wall_points + [wall_points[0]]) < 5.0:
            return False
        for polygon_site in sites:
            if point_in_polygon(point.x, point.y, polygon_site):
                return False
        for spec in nearby(specs, point, 1.0):
            limit = spec["half"] + 0.15
            if spec is own:
                limit = spec["half"] - 0.05
            if spec["distance"](point) < limit:
                return False
    for polygon_site in sites:
        for corner in polygon_site:
            if point_in_polygon(corner.x, corner.y, polygon):
                return False
    return not occupancy.overlaps(polygon)


def frontage(scene, specs, sites, eyes, rng):
    wall_points = [Vector(p[:2]) for p in plan.wall_trace()]
    site_polygons = [[Vector(p[:2]) for p in polygon] for polygon in sites.values()]
    occupancy = Occupancy()
    units = []
    order = sorted([spec for spec in specs if spec["kind"] != "road"], key=lambda spec: -spec["rank"])
    for spec in order:
        points = spec["points"]
        for a, b in zip(points[:-1], points[1:]):
            along = (b - a)
            length = along.length
            along.normalize()
            for side in (-1, 1):
                inward = Vector((-along.y, along.x)) * side
                position = 1.0
                while position < length - 4.0:
                    main = spec["kind"] == "main"
                    preferred = rng.choice([7.5, 9.0, 10.5, 12.0, 14.0, 16.0] if main else [7.0, 9.0, 11.0, 13.0, 16.0])
                    placed = False
                    width = preferred
                    for candidate in [preferred] + [value for value in (9.0, 7.0, 5.5) if value < preferred]:
                        width = min(candidate, length - position - 0.5)
                        if width < 5.0:
                            continue
                        origin = a + along * (position + width / 2) + inward * (spec["half"] + 0.05)
                        for depth in (17.0, 14.0, 11.0, 8.5, 6.5):
                            polygon = rectangle(origin, along * side, inward, width, depth)
                            if unit_fits(polygon, specs, site_polygons, wall_points, occupancy, spec):
                                occupancy.add(polygon)
                                centre_line = a + along * (position + width / 2)
                                z = scene.ground(centre_line.x, centre_line.y) + spec["kerb"]
                                near = min((origin - eye).length for eye in eyes) < 160.0
                                kind = choose_kind(rng, main, width, depth)
                                units.append(dict(origin=origin, along=along * side, inward=inward, width=width,
                                                  depth=depth, z=z, kind=kind, near=near, main=main,
                                                  seed=rng.randrange(1 << 30), street=spec))
                                placed = True
                                break
                        if placed:
                            break
                    position += width if placed else 1.5
    return units, occupancy


def choose_kind(rng, main, width, depth):
    roll = rng.random()
    if main:
        return "shop" if roll < 0.8 else "house"
    if roll < 0.18:
        return "wall"
    return "shop" if roll < 0.45 else "house"


def unit_frame(unit):
    return (Matrix.Translation((unit["origin"].x, unit["origin"].y, unit["z"]))
            @ Matrix.Rotation(plan.heading_of(unit["inward"]), 4, "Z"))


def build_units(scene, units, rng):
    regions = {}
    programmes = 0
    for index, unit in enumerate(units):
        height = rng.choice([5.2, 5.8, 6.6, 7.4, 8.2]) if unit["kind"] != "wall" else rng.uniform(3.2, 4.0)
        if unit["kind"] == "shop" and unit["main"]:
            height = rng.choice([5.6, 6.8, 7.6, 8.4])
        shutters = "mixed" if unit["near"] else "closed"
        builder = town.unit(unit["width"], unit["depth"], height, unit["kind"], unit["seed"], unit["near"], shutters)
        if unit["near"] and unit["kind"] != "wall" and rng.random() < (0.55 if unit["main"] else 0.25):
            text = town.PROGRAMMES[programmes % len(town.PROGRAMMES)]
            programmes += 1
            builder.merge(town.programme(text, unit["width"] * 0.8, unit["seed"]),
                          Matrix.Translation((rng.uniform(-0.6, 0.6), -0.03, min(height - 1.2, 3.6))))
        x, y = unit["origin"].x, unit["origin"].y
        region = ("w" if x < 120 else "e") + ("s" if y < 150 else "n")
        scene.unique(f"town_{region}", builder, unit_frame(unit))
        unit["height"] = height
    return programmes


def place_gardens(scene, occupancy, specs, sites, rng):
    wall = [Vector(p[:2]) for p in plan.wall_trace()]
    site_polygons = [[Vector(p[:2]) for p in polygon] for polygon in sites.values()]
    xs = [p.x for p in wall]
    ys = [p.y for p in wall]
    kinds = {"tree_fruit": [], "tree_cypress": [], "tree_olive": [], "tree_pine": [], "shrub": []}
    step = 7.0
    for x in np.arange(min(xs), max(xs), step):
        for y in np.arange(min(ys), max(ys), step):
            point = Vector((x + rng.uniform(-2.5, 2.5), y + rng.uniform(-2.5, 2.5)))
            if not point_in_polygon(point.x, point.y, wall) or occupancy.contains(point):
                continue
            if any(point_in_polygon(point.x, point.y, polygon) for polygon in site_polygons):
                continue
            if any(spec["distance"](point) < spec["half"] + 1.5 for spec in nearby(specs, point, 2.0)):
                continue
            if polyline_point_distance(point, wall + [wall[0]]) < 6.0:
                continue
            roll = rng.random()
            if roll > 0.55:
                continue
            key = ("tree_fruit" if roll < 0.22 else "tree_cypress" if roll < 0.29 else "tree_olive" if roll < 0.38
                   else "tree_pine" if roll < 0.41 else "shrub")
            z = scene.ground(point.x, point.y)
            kinds[key].append(placement(point.x, point.y, z - 0.2, rng.uniform(0, 2 * math.pi),
                                        rng.uniform(0.8, 1.15)))
    return kinds


TREE_BUILDS = {
    "tree_fruit": lambda: nimes_detail.holm_oak(6.0, 3),
    "tree_cypress": lambda: buildings.cypress(11.0, 4),
    "tree_olive": lambda: nimes_detail.olive_tree(5.0, 5),
    "tree_pine": lambda: nimes_scenery.umbrella_pine(13.0, 6),
    "tree_plane": lambda: nimes_detail.plane_tree(14.0, 7),
    "shrub": lambda: buildings.scrub(1.6, 8),
    "vine_row": lambda: nimes_detail.vine_row(12.0),
}


def forum_level(scene):
    return scene.ground(*plan.FORUM_ORIGIN) + 0.2


def build_forum(scene, level):
    frame = plan.frame(plan.FORUM_ORIGIN, plan.FB, level)
    builder = MeshBuilder()
    half_a, half_b = plan.FORUM_HALF
    town.tinted(builder, (0.9, 0.88, 0.83), lambda: builder.box((-half_b, -half_a, -3.0), (half_b, half_a, 0.0),
                                                                "paving", bottom=False))
    builder.merge(mon.temple_of_jupiter())
    for side in (-1, 1):
        builder.merge(mon.honorific_arch(), Matrix.Translation((side * 13.6, 66.5, 0.0)))
    lower_frames = []
    upper_frames = []
    upper_lift = mon.PORTICO_DOWN[0] + 0.6 - 0.35
    for name, centre, length, rotate in (("west", Vector((-half_b, -6.0)), 130.0, math.pi / 2),
                                         ("east", Vector((half_b, -6.0)), 130.0, -math.pi / 2),
                                         ("south", Vector((0.0, -half_a)), 2 * half_b + 2 * plan.PORTICO, math.pi)):
        local = Matrix.Translation((centre.x, centre.y, 0.0)) @ Matrix.Rotation(rotate, 4, "Z")
        if name == "east":
            for piece_centre, piece_length, top in ((-42.0, 46.0, True), (-6.0, 26.0, False), (36.0, 58.0, True)):
                piece = Matrix.Translation((0.0, piece_centre, 0.0))
                shell = mon.portico_shell(piece_length, plan.PORTICO, mon.PORTICO_DOWN[0], mon.PORTICO_UP[0],
                                          True, top)
                builder.merge(shell, local @ Matrix.Translation((piece_centre, 0.0, 0.0)))
                for x in mon.portico_columns(piece_length, 2.6):
                    world = local @ Matrix.Translation((piece_centre + x, 0.4, 0.35))
                    lower_frames.append(frame @ world)
                    if top:
                        upper_frames.append(frame @ world @ Matrix.Translation((0.0, 0.0, upper_lift)))
                if not top:
                    builder.merge(mon.scaffold(-piece_length / 2, piece_length / 2, -1.4, mon.PORTICO_DOWN[0] + 0.6,
                                               mon.PORTICO_DOWN[0] + 4.6),
                                  local @ Matrix.Translation((piece_centre, 0.0, 0.0)))
            continue
        builder.merge(mon.portico_shell(length, plan.PORTICO, mon.PORTICO_DOWN[0], mon.PORTICO_UP[0]), local)
        for x in mon.portico_columns(length, 2.6):
            world = local @ Matrix.Translation((x, 0.4, 0.35))
            lower_frames.append(frame @ world)
            upper_frames.append(frame @ world @ Matrix.Translation((0.0, 0.0, upper_lift)))
    scene.unique("forum", builder, frame)
    east = MeshBuilder()
    for y0, y1, height, colour in ((30.0, 62.0, 8.5, (0.95, 0.9, 0.82)), (12.0, 29.0, 10.0, (0.93, 0.92, 0.88)),
                                   (-6.0, 11.0, 9.0, (0.96, 0.94, 0.9)), (-52.0, -7.0, 11.5, (0.94, 0.91, 0.84))):
        east.merge(mon.hall(36.0, y1 - y0, height, colour, door=0.0, along_y=True),
                   Matrix.Translation((half_b + plan.PORTICO + 0.6 + 18.0, (y0 + y1) / 2, 0.0)))
    east.merge(mon.court_ring(20.0, 18.0, 4.0, 0.0), Matrix.Translation((half_b + plan.PORTICO + 12.0, -62.0, 0.0)))
    for x0, x1 in ((-20.0, -7.0), (-6.5, 6.5), (7.0, 20.0)):
        east.merge(mon.hall(x1 - x0, 18.0, 10.0, (0.95, 0.92, 0.86), door=3.0),
                   Matrix.Translation(((x0 + x1) / 2, -half_a - plan.PORTICO - 9.6, 0.0))
                   @ Matrix.Rotation(math.pi, 4, "Z"))
    scene.unique("forum", east, frame)
    scene.instances("forum", "col_forum_lower", lambda: mon.columns_template("tuscan", mon.PORTICO_DOWN[1],
                                                                            mon.PORTICO_DOWN[0], "low"),
                    lower_frames)
    scene.instances("forum", "col_forum_upper", lambda: mon.columns_template("ionic", mon.PORTICO_UP[1],
                                                                            mon.PORTICO_UP[0], "low"),
                    upper_frames)
    temple_frames = []
    for index, (x, y) in enumerate(mon.jupiter_columns()):
        if index == 5:
            continue
        temple_frames.append(frame @ Matrix.Translation((x, y, 3.0)))
    scene.instances("forum", "col_jupiter", lambda: mon.columns_template("corinthian", 0.95, 8.6, "medium"),
                    temple_frames)
    x, y = mon.jupiter_columns()[5]
    scene.unique("forum", mon.shoring_column(8.6), frame @ Matrix.Translation((x, y, 3.0)))
    statues = []
    for index, a in enumerate(range(-58, 32, 11)):
        statues.append(("statue_bronze" if index % 3 else "statue_marble", frame @ placement(-15.8, a, 0.0,
                                                                                            -math.pi / 2)))
    for index, a in enumerate(range(-50, 30, 16)):
        statues.append(("statue_bronze", frame @ placement(15.8, a, 0.0, math.pi / 2)))
    for x in (-7.8, 7.8):
        statues.append(("equestrian", frame @ placement(x, 35.0, 1.6, math.pi)))
    for b in (-9.0, 9.0):
        statues.append(("equestrian", frame @ placement(b, -42.0, 0.0, math.pi)))
    keyed = {}
    for key, matrix in statues:
        keyed.setdefault(key, []).append(matrix)
    scene.instances("forum", "statue_bronze", lambda: mon.standing_statue(True), keyed.get("statue_bronze", []))
    scene.instances("forum", "statue_marble", lambda: mon.standing_statue(False), keyed.get("statue_marble", []))
    scene.instances("forum", "statue_equestrian", lambda: mon.equestrian_statue(1), keyed.get("equestrian", []))
    props = MeshBuilder()
    props.merge(mon.block_pile(1, 9), Matrix.Translation((11.0, 30.0, 0.0)))
    props.merge(mon.drums(2, 4, 0.95, (0.9, 0.88, 0.82)), Matrix.Translation((-11.0, 28.0, 0.0)))
    props.merge(mon.block_pile(4, 6), Matrix.Translation((14.0, -4.0, 0.0)))
    props.merge(mon.crane(), Matrix.Translation((12.5, 47.0, 0.0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))
    scene.unique("forum", props, frame)
    return frame, len(lower_frames) + len(upper_frames) + len(temple_frames)


def build_west_monuments(scene, level):
    frame = plan.frame(plan.FORUM_ORIGIN, plan.FB, level)
    scene.unique("monuments", mon.basilica(), frame @ Matrix.Translation((-54.0, -60.0, -0.2)))
    scene.unique("monuments", mon.apollo_precinct(), frame @ Matrix.Translation((-43.0, 4.0, 0.0)))
    baths = MeshBuilder()
    baths.merge(mon.bath_block(42.0, 40.0, 3))
    centre = plan.forum_point(112.0, -27.0)
    scene.unique("monuments", baths, plan.frame(centre, plan.FB, scene.ground(*centre) + 0.2))


def venus_level(scene):
    corner = plan.forum_point(plan.VENUS[0] + 30.0, plan.VENUS[1] + 26.0)
    return scene.ground(corner.x, corner.y) + 0.1


def build_venus(scene):
    level = venus_level(scene)
    centre = plan.forum_point(*plan.VENUS)
    frame = plan.frame(centre, plan.FB, level)
    lowest = min(scene.ground(*plan.forum_point(plan.VENUS[0] + da, plan.VENUS[1] + db))
                 for da in (-30.0, 30.0) for db in (-30.0, 26.0))
    terrace = mon.venus_terrace(56.0, 60.0, max(level - lowest + 2.0, 3.0))
    scene.unique("venus", terrace, frame @ Matrix.Translation((-2.0, 0.0, 0.0)))
    scene.unique("venus_site", mon.venus_site(), frame)
    return frame, level


def build_vettii(scene):
    origin = plan.forum_point(plan.VETTII[0], 88.0 - MINOR["road"] / 2 - MINOR["walk"] - 0.05)
    z = scene.ground(origin.x, origin.y) + MINOR["kerb"]
    frame = plan.frame(origin, plan.FA, z)
    scene.unique("vettii", mon.house_vettii(), frame)
    scene.unique("vettii", mon.garden_props(), frame)
    frames = [frame @ Matrix.Translation((x, y, 0.25)) for x, y in mon.peristyle_columns()]
    scene.instances("vettii", "col_vettii", lambda: mon.columns_template("tuscan", 0.42, 4.2, "low", red_lower=True),
                    frames)
    return frame


def build_thermopolium(scene, specs):
    abbondanza = next(spec for spec in specs if spec["points"][0] == plan.ABBONDANZA[0])
    position = plan.grid_point(plan.THERMOPOLIUM_U, 0.0)
    inward = -plan.GV
    origin = position + inward * (abbondanza["half"] + 0.05)
    z = scene.ground(position.x, position.y) + abbondanza["kerb"]
    frame = Matrix.Translation((origin.x, origin.y, z)) @ Matrix.Rotation(plan.heading_of(inward), 4, "Z")
    builder = mon.thermopolium()
    builder.merge(town.programme("C IVLIVM POLYBIVM AED OVF", 6.0, 3), Matrix.Translation((2.2, -0.03, 4.0)))
    builder.merge(town.programme("M CERRINIVM VATIAM AED OVF", 4.0, 5), Matrix.Translation((-2.8, -0.03, 4.1)))
    scene.unique("thermopolium", builder, frame)
    return frame, rectangle(origin, plan.GU * -1.0, inward, 11.4, 14.4)


def build_east_monuments(scene):
    g = plan.PLEIADES
    level = scene.ground(*g["grand-theatre"])
    scene.unique("monuments", mon.theatre(), plan.frame(g["grand-theatre"], plan.GU, level - 1.5))
    odeon = g["grand-theatre"] + plan.GU * 58.0 + plan.GV * 6.0
    scene.unique("monuments", mon.hall(30.0, 34.0, 11.0, (0.95, 0.92, 0.86), door=4.0),
                 plan.frame(odeon, plan.GU, scene.ground(*odeon)))
    quadri = g["grand-theatre"] - plan.GV * 70.0 + plan.GU * 8.0
    scene.unique("monuments", mon.court_ring(66.0, 58.0, 4.2, 5.0, 4.8), plan.frame(quadri, plan.GU,
                                                                                   scene.ground(*quadri)))
    tri = g["forum-triangulaire"] - plan.GV * 10.0 - plan.GU * 12.0
    scene.unique("monuments", mon.triangular_forum(), plan.frame(tri, plan.GV, scene.ground(*tri)))
    stab = g["thermes-de-stabies"]
    scene.unique("monuments", mon.bath_block(56.0, 76.0, 9), plan.frame(stab, plan.GU, scene.ground(*stab) + 0.2))
    central = g["thermes-centraux"]
    scene.unique("monuments", mon.bath_block(56.0, 52.0, 11, open_roof=True),
                 plan.frame(central, plan.GU, scene.ground(*central) + 0.2))
    pal = g["grande-palestre"]
    pal_z = scene.ground(*pal)
    pal_frame = plan.frame(pal, plan.GU, pal_z)
    scene.unique("monuments", mon.palaestra(), pal_frame)
    planes = []
    for row in (-40.0, -32.0, 32.0, 40.0):
        for k in range(12):
            x = -62.0 + k * 11.3
            planes.append(pal_frame @ placement(x, row * 1.0, 0.0, k * 0.7, 0.9))
    amph = g["amphitheatre"]
    amph_z = scene.ground(*amph)
    scene.unique("amphitheatre", mon.amphitheatre(), plan.frame(amph, plan.GU, amph_z - 3.0))
    return planes


def build_walls(scene, wall):
    gates = list(plan.GATES.values())
    builder = MeshBuilder()
    points = [Vector(p[:2]) for p in wall]
    segments = []
    current = []
    count = len(points)
    for index in range(count):
        a, b = points[index], points[(index + 1) % count]
        steps = max(int((b - a).length / 6.0), 1)
        for k in range(steps):
            p = a.lerp(b, k / steps)
            if any((p - gate).length < 11.0 for gate in gates):
                if len(current) > 1:
                    segments.append(current)
                current = []
            else:
                current.append(p)
    if len(current) > 1:
        segments.append(current)
    for segment in segments:
        rows = []
        for index, point in enumerate(segment):
            a = segment[max(index - 1, 0)]
            b = segment[min(index + 1, len(segment) - 1)]
            tangent = (b - a).normalized()
            normal = Vector((tangent.y, -tangent.x))
            rows.append((point, normal, scene.ground(point.x, point.y)))
        for (p0, n0, z0), (p1, n1, z1) in zip(rows[:-1], rows[1:]):
            out0, out1 = p0 + n0 * 1.6, p1 + n1 * 1.6
            in0, in1 = p0 - n0 * 1.6, p1 - n1 * 1.6
            town.quad(builder, [(out0.x, out0.y, z0 - 6.0), (out1.x, out1.y, z1 - 6.0), (out1.x, out1.y, z1 + 8.0),
                                (out0.x, out0.y, z0 + 8.0)], (n0.x, n0.y, 0.0), "stone", (0.76, 0.71, 0.62))
            town.quad(builder, [(in0.x, in0.y, z0 - 2.0), (in1.x, in1.y, z1 - 2.0), (in1.x, in1.y, z1 + 8.0),
                                (in0.x, in0.y, z0 + 8.0)], (-n0.x, -n0.y, 0.0), "stone", (0.70, 0.66, 0.58))
            town.quad(builder, [(out0.x, out0.y, z0 + 8.0), (out1.x, out1.y, z1 + 8.0), (in1.x, in1.y, z1 + 8.0),
                                (in0.x, in0.y, z0 + 8.0)], (0, 0, 1), "sidewalk", (0.82, 0.78, 0.70))
            merlons = max(int((p1 - p0).length / 2.4), 1)
            for k in range(merlons):
                s0, s1 = (k + 0.2) / merlons, (k + 0.7) / merlons
                a, b = out0.lerp(out1, s0), out0.lerp(out1, s1)
                za, zb = z0 + (z1 - z0) * s0 + 8.0, z0 + (z1 - z0) * s1 + 8.0
                ia, ib = a - n0 * 0.6, b - n0 * 0.6
                tone = (0.74, 0.70, 0.62)
                town.quad(builder, [(a.x, a.y, za), (b.x, b.y, zb), (b.x, b.y, zb + 1.3), (a.x, a.y, za + 1.3)],
                          (n0.x, n0.y, 0.0), "stone", tone)
                town.quad(builder, [(ia.x, ia.y, za), (ib.x, ib.y, zb), (ib.x, ib.y, zb + 1.3),
                                    (ia.x, ia.y, za + 1.3)], (-n0.x, -n0.y, 0.0), "stone", tone)
                town.quad(builder, [(a.x, a.y, za), (ia.x, ia.y, za), (ia.x, ia.y, za + 1.3), (a.x, a.y, za + 1.3)],
                          (a.x - b.x, a.y - b.y, 0.0), "stone", tone)
                town.quad(builder, [(b.x, b.y, zb), (ib.x, ib.y, zb), (ib.x, ib.y, zb + 1.3), (b.x, b.y, zb + 1.3)],
                          (b.x - a.x, b.y - a.y, 0.0), "stone", tone)
                town.quad(builder, [(a.x, a.y, za + 1.3), (b.x, b.y, zb + 1.3), (ib.x, ib.y, zb + 1.3),
                                    (ia.x, ia.y, za + 1.3)], (0, 0, 1), "stone", (0.80, 0.76, 0.68))
    scene.unique("walls", builder)
    towers = []
    for segment in segments:
        total = 0.0
        for index in range(1, len(segment)):
            total += (segment[index] - segment[index - 1]).length
            centre = segment[index]
            if centre.y < 150.0 and centre.x < 600.0:
                continue
            if total > 85.0 and 3 < index < len(segment) - 3:
                tangent = (segment[index + 1] - segment[index - 1]).normalized()
                normal = Vector((tangent.y, -tangent.x))
                z = scene.ground(centre.x, centre.y)
                towers.append(Matrix.Translation((centre.x, centre.y, z))
                              @ Matrix.Rotation(plan.heading_of(normal), 4, "Z"))
                total = 0.0
    scene.instances("walls", "tower", lambda: town.square_tower(), towers)
    return len(towers)


def build_gates(scene, specs):
    gate_frames = {}
    for name, position in plan.GATES.items():
        road = plan.ROADS_OUT[name]
        outward = (Vector(road[1][:2]) - position).normalized()
        z = scene.ground(position.x, position.y)
        if name == "marina":
            inward = (plan.MARINA[1] - plan.MARINA[0]).normalized()
            centre = position + inward * 3.0
            frame = (Matrix.Translation((centre.x, centre.y, scene.ground(centre.x, centre.y) - 0.3))
                     @ Matrix.Rotation(plan.heading_of(inward), 4, "Z") @ Matrix.Translation((0.0, -10.5, 0.0)))
            scene.unique("gates", mon.porta_marina(), frame)
        else:
            frame = (Matrix.Translation((position.x, position.y, z - 0.2))
                     @ Matrix.Rotation(plan.heading_of(-outward), 4, "Z") @ Matrix.Translation((0.0, -7.0, 0.0)))
            passages = ((0.0, 4.2, 6.0),) if name != "ercolano" else ((-4.2, 1.6, 3.4), (0.0, 4.2, 6.0),
                                                                      (4.2, 1.6, 3.4))
            scene.unique("gates", town.gate(14.0 if name == "ercolano" else 11.0, 14.0, 9.0, passages), frame)
        gate_frames[name] = frame
    return gate_frames


def build_countryside(scene, rng):
    tombs = {"tomb_mausoleum": [], "tomb_enclosure": [], "tomb_altar": [], "tomb_stele": []}
    for name, (start, stop) in (("ercolano", (25.0, 360.0)), ("nocera", (25.0, 300.0)), ("vesuvio", (25.0, 160.0)),
                                ("stabia", (30.0, 200.0))):
        road = [Vector(p[:2]) for p in plan.ROADS_OUT[name]]
        travelled = 0.0
        for a, b in zip(road[:-1], road[1:]):
            direction = (b - a).normalized()
            length = (b - a).length
            s = 0.0
            while s < length:
                position = travelled + s
                if start < position < stop:
                    for side in (-1, 1):
                        if rng.random() < 0.55:
                            normal = Vector((-direction.y, direction.x)) * side
                            point = a + direction * s + normal * rng.uniform(6.5, 9.0)
                            key = rng.choice(list(tombs))
                            z = scene.ground(point.x, point.y)
                            tombs[key].append(Matrix.Translation((point.x, point.y, z - 0.1))
                                              @ Matrix.Rotation(plan.heading_of(-normal), 4, "Z"))
                s += rng.uniform(7.0, 11.0)
            travelled += length
    builds = {"tomb_mausoleum": buildings.mausoleum, "tomb_enclosure": buildings.funerary_enclosure,
              "tomb_altar": buildings.tomb_altar, "tomb_stele": buildings.funerary_stele}
    for key, frames in tombs.items():
        scene.instances("countryside", key, builds[key], frames)
    wall = [tuple(p) for p in plan.wall_trace()]
    roads = [[Vector(p[:2]) for p in points] for points in plan.ROADS_OUT.values()]
    vines, trees = [], {"tree_olive": [], "tree_pine": [], "tree_cypress": [], "tree_fruit": []}
    farms = []
    angle = math.radians(57.0)
    for x in np.arange(-1050.0, 1050.0, 26.0):
        for y in np.arange(-1050.0, 1050.0, 26.0):
            point = Vector((x + rng.uniform(-6, 6), y + rng.uniform(-6, 6)))
            if point_in_polygon(point.x, point.y, wall):
                continue
            if min(polyline_point_distance(point, road) for road in roads) < 9.0:
                continue
            if polyline_point_distance(point, [Vector(p) for p in wall] + [Vector(wall[0])]) < 25.0:
                continue
            z = scene.ground(point.x, point.y)
            if z < 1.5:
                continue
            distance = (point - Vector(TOWN_CENTRE)).length
            density = 1.0 if distance < 900 else 0.6
            roll = rng.random()
            parcel = (int(math.floor((point.x * 0.84 + point.y * 0.54) / 95.0)) * 7
                      + int(math.floor((-point.x * 0.54 + point.y * 0.84) / 60.0)) * 13) % 10
            if parcel < 4 and roll < 0.85 * density:
                for k in range(3):
                    p = point + Vector((-math.sin(angle), math.cos(angle))) * (k * 2.4)
                    vines.append(Matrix.Translation((p.x, p.y, scene.ground(p.x, p.y) - 0.05))
                                 @ Matrix.Rotation(math.radians(90.0 - 57.0), 4, "Z"))
            elif parcel < 7 and roll < 0.5 * density:
                trees["tree_olive"].append(placement(point.x, point.y, z - 0.2, rng.uniform(0, 6.3),
                                                     rng.uniform(0.8, 1.2)))
            elif roll < 0.08 * density:
                key = rng.choice(["tree_pine", "tree_cypress", "tree_fruit"])
                trees[key].append(placement(point.x, point.y, z - 0.2, rng.uniform(0, 6.3), rng.uniform(0.85, 1.2)))
            elif roll > 0.993 and distance < 1000:
                farms.append(placement(point.x, point.y, z - 0.2, rng.uniform(0, 6.3)))
    scene.instances("countryside", "vine_row", TREE_BUILDS["vine_row"], vines, cast_shadow=False)
    for key, frames in trees.items():
        scene.instances("countryside", f"{key}_country", TREE_BUILDS[key], frames)
    scene.instances("countryside", "farm", buildings.farmstead, farms)
    villas = []
    for point in (Vector((-520.0, 420.0)), Vector((-640.0, 560.0)), Vector((-430.0, -330.0)), Vector((960.0, -120.0))):
        z = scene.ground(point.x, point.y)
        villas.append(placement(point.x, point.y, z - 0.3, rng.uniform(0, 6.3)))
    scene.instances("countryside", "villa", lambda: mon.court_ring(40.0, 34.0, 5.0, 4.5, 6.0), villas)
    return {"tombs": sum(len(v) for v in tombs.values()), "vines": len(vines),
            "trees": sum(len(v) for v in trees.values()), "farms": len(farms), "villas": len(villas)}


def shoreline(scene, start, direction, limit=4000.0):
    point = Vector(start[:2])
    for step in range(int(limit / 10.0)):
        candidate = point + direction * 10.0 * step
        if scene.ground(candidate.x, candidate.y) < 0.0:
            return candidate
    return point + direction * limit


def build_shore(scene, rng):
    direction = Vector((-0.94, -0.34)).normalized()
    shore = shoreline(scene, plan.GATES["marina"], direction)
    boats = {"boat_small": [], "boat_ship": []}
    tangent = Vector((-direction.y, direction.x))
    for k in range(9):
        p = shore + tangent * rng.uniform(-500.0, 500.0) + direction * rng.uniform(5.0, 30.0)
        boats["boat_small"].append(Matrix.Translation((p.x, p.y, 0.05)) @ Matrix.Rotation(rng.uniform(0, 6.3), 4, "Z"))
    for k in range(4):
        p = shore + tangent * rng.uniform(-900.0, 900.0) + direction * rng.uniform(250.0, 900.0)
        boats["boat_ship"].append(Matrix.Translation((p.x, p.y, 0.0)) @ Matrix.Rotation(rng.uniform(0, 6.3), 4, "Z"))
    scene.instances("shore", "boat_small", lambda: arles_life.small_boat(6.5, 1.8), boats["boat_small"])
    scene.instances("shore", "boat_ship", lambda: arles_life.seagoing_ship(20.0, 6.0, 3, "brailed"),
                    boats["boat_ship"])
    return shore


def build_surface(scene):
    objects = []
    for name in WALKABLE:
        root = scene.roots.get(name)
        if root is None:
            continue
        for item in [root] + list(root.children_recursive):
            if item.type == "MESH" and item.name != "terrain_far" and not item.name.startswith("sea"):
                objects.append(item)
    scene.surface = Surface(objects)


def resample(points, spacing):
    out = [Vector(points[0])]
    for start, end in zip(points[:-1], points[1:]):
        a, b = Vector(start), Vector(end)
        count = max(int(math.ceil((b - a).length / spacing - 1e-6)), 1)
        for k in range(1, count + 1):
            out.append(a + (b - a) * (k / count))
    return out


def add_route(scene, name, points, hint_height):
    root = scene.root("life")
    chain = []
    for point in resample([Vector((p[0], p[1], 0.0)) for p in points], 2.6):
        z = scene.surface.height(point.x, point.y, hint_height(point))
        chain.append(Vector((point.x, point.y, z)))
    refined = [chain[0]]
    for following in chain[1:]:
        previous = refined[-1]
        middle = (previous + following) / 2
        middle.z = scene.surface.height(middle.x, middle.y, max(previous.z, following.z))
        if abs(middle.z - (previous.z + following.z) / 2) > 0.05:
            refined.append(middle)
        refined.append(following)
    for index, point in enumerate(refined):
        new_empty(f"walk_{name}_{index:02d}", scene.collection, root, Matrix.Translation(point))
    scene.route_samples.extend(point.to_2d() for point in refined)
    return len(refined)


def sidewalk_line(spec, side, start, stop):
    points = []
    half = spec["road"] / 2 + spec["walk"] * 0.5
    for point, normal, z, road_on, walks, sink, distance in spec["rows"]:
        if start <= distance <= stop:
            points.append(point + normal * side * half)
    return points


def build_routes(scene, specs, gate_frames, vettii_frame, forum_frame, level):
    scene.route_samples = []
    abbondanza = next(spec for spec in specs if spec["points"][0] == plan.ABBONDANZA[0])
    start = (plan.HOLCONIUS - plan.ABBONDANZA[0]).length + 30.0
    counts = {}
    for side, name, length in ((-1, "abbondanza-sud", 230.0), (1, "abbondanza-nord", 115.0)):
        line = sidewalk_line(abbondanza, side, start, start + length)
        counts[name] = add_route(scene, name, line, lambda p: scene.ground(p.x, p.y) + 0.6)
    road = [Vector(p[:2]) for p in plan.ROADS_OUT["marina"]]
    gate_frame = gate_frames["marina"]
    lane = [(gate_frame @ Vector((-3.6, y, 0.0))).to_2d() for y in (32.0, 21.0, 10.0, 0.0, -6.0)]
    counts["via-marina"] = add_route(scene, "via-marina", [plan.MARINA[1]] + lane
                                     + [road[1], road[1] + (road[2] - road[1]) * 0.5],
                                     lambda p: scene.ground(p.x, p.y) + 0.8)
    half_a, half_b = plan.FORUM_HALF
    forum_loop = [plan.forum_point(a, b) for a, b in ((-62.0, -half_b - 2.6), (20.0, -half_b - 2.6),
                                                      (28.0, -6.0), (24.0, 8.0), (-40.0, 8.0),
                                                      (-62.0, half_b + 2.6))]
    counts["forum"] = add_route(scene, "forum", forum_loop, lambda p: level + 0.6)
    stabiana = next(spec for spec in specs if spec["points"][0] == plan.STABIANA[0])
    line = sidewalk_line(stabiana, 1, 30.0, 200.0)
    counts["stabiana"] = add_route(scene, "stabiana", line, lambda p: scene.ground(p.x, p.y) + 0.6)
    nocera = [Vector(p[:2]) for p in plan.ROADS_OUT["nocera"]]
    counts["route-de-nocera"] = add_route(scene, "route-de-nocera", [nocera[0] + (nocera[1] - nocera[0]) * 0.15,
                                                                     nocera[1], nocera[2]],
                                          lambda p: scene.ground(p.x, p.y) + 0.6)
    vettii_street = [vettii_frame @ Vector((x, -3.4, 0.0)) for x in (-30.0, 30.0)]
    counts["vicolo-dei-vettii"] = add_route(scene, "vicolo-dei-vettii", [p.to_2d() for p in vettii_street],
                                            lambda p: scene.ground(p.x, p.y) + 0.6)
    return counts


def clear_of_routes(scene, matrices, radius):
    if not scene.route_samples:
        return matrices
    from mathutils.kdtree import KDTree
    tree = KDTree(len(scene.route_samples))
    for index, point in enumerate(scene.route_samples):
        tree.insert((point.x, point.y, 0.0), index)
    tree.balance()
    kept = []
    for matrix in matrices:
        location = matrix.translation
        _, _, distance = tree.find((location.x, location.y, 0.0))
        if distance is None or distance > radius:
            kept.append(matrix)
    return kept


def grounded(scene, matrix):
    location = matrix.translation
    z = scene.surface.height(location.x, location.y, location.z)
    return Matrix.Translation((0.0, 0.0, z - location.z)) @ matrix


def street_spot(spec, distance, side, lateral, heading_offset=0.0):
    rows = spec["rows"]
    best = min(rows, key=lambda row: abs(row[6] - distance))
    point, normal, z = best[0], best[1], best[2]
    position = point + normal * lateral * side
    tangent = Vector((normal.y, -normal.x))
    return position, z, math.atan2(-tangent.x, tangent.y) + heading_offset


def populate(scene, specs, forum_frame, level, venus_frame, vettii_frame, thermo_frame, gate_frames, rng):
    abbondanza = next(spec for spec in specs if spec["points"][0] == plan.ABBONDANZA[0])
    holconius = (plan.HOLCONIUS - plan.ABBONDANZA[0]).length
    for k in range(26):
        distance = holconius + 20.0 + k * 9.0 + rng.uniform(-3, 3)
        side = rng.choice((-1, 1))
        on_walk = rng.random() < 0.6
        lateral = abbondanza["road"] / 2 + abbondanza["walk"] * 0.5 if on_walk else rng.uniform(0.0, 1.6)
        position, z, heading = street_spot(abbondanza, distance, side, lateral, math.pi if rng.random() < 0.3 else 0.0)
        key = rng.choice(["fig_bundle", "fig_veiled", "fig_cushion", "fig_chest", "fig_child", "fig_pointing",
                          "family", "household", "dog", "fig_bundle_b", "fig_veiled_b", "fig_jar", "fig_basket",
                          "family_b"])
        scene.add(key, placement(position.x, position.y, z + (0.4 if on_walk else 0.0), heading + rng.uniform(-0.3,
                                                                                                             0.3)))
    for k, distance in enumerate((holconius + 45.0, holconius + 150.0, holconius + 260.0)):
        position, z, heading = street_spot(abbondanza, distance, -1 if k % 2 else 1, 0.4)
        scene.add("wagon" if k != 1 else "handcart", placement(position.x, position.y, z, heading + math.pi * (k == 2)))
    for k in range(10):
        distance = holconius + 30.0 + k * 22.0
        side = -1 if k % 2 else 1
        position, z, heading = street_spot(abbondanza, distance, side, abbondanza["half"] - 0.45)
        scene.add("shopkeeper", placement(position.x, position.y, z + 0.4, heading + side * math.pi / 2))
    half_a, half_b = plan.FORUM_HALF
    for k in range(9):
        a = -60.0 + k * 13.0 + rng.uniform(-2, 2)
        side = -1 if k % 2 else 1
        b = side * (half_b + plan.PORTICO * 0.5)
        scene.add(rng.choice(["shelterers", "shelterers_b", "onlookers"]),
                  forum_frame @ placement(b, a, 0.35, side * math.pi / 2 + rng.uniform(-0.3, 0.3)))
    for k in range(18):
        a = rng.uniform(-60.0, 30.0)
        b = rng.uniform(-14.0, 14.0)
        scene.add(rng.choice(["fig_bundle", "fig_veiled", "fig_pointing", "fig_cushion", "fig_chest", "household",
                              "family", "fig_shelter", "fig_veiled_b", "fig_basket"]),
                  forum_frame @ placement(b, a, 0.0, rng.uniform(-math.pi, math.pi)))
    road = [Vector(p[:2]) for p in plan.ROADS_OUT["marina"]]
    for k in range(8):
        t = 0.1 + k * 0.11
        p = road[1].lerp(road[2], t) if t < 1 else road[2]
        direction = (road[2] - road[1]).normalized()
        heading = plan.heading_of(direction)
        scene.add(rng.choice(["road_column", "road_column_b", "pack_train", "family", "handcart"]),
                  placement(p.x + rng.uniform(-1.5, 1.5), p.y + rng.uniform(-1.5, 1.5), scene.ground(p.x, p.y), heading))
    for name in ("nocera", "stabia", "sarno", "nola"):
        road = [Vector(p[:2]) for p in plan.ROADS_OUT[name]]
        for k in range(5 if name in ("nocera", "stabia") else 3):
            t = 0.25 + k * 0.17
            p = road[1].lerp(road[2], t) if t <= 1.0 else road[2]
            direction = (road[2] - road[1]).normalized()
            key = rng.choice(["road_column", "road_column_b", "wagon", "pack_train", "handcart"])
            scene.add(key, placement(p.x, p.y, scene.ground(p.x, p.y), plan.heading_of(direction)))
    for k in range(5):
        p = venus_frame @ Vector((rng.uniform(-15.0, 15.0), rng.uniform(-20.0, 20.0), 0.0))
        scene.add(rng.choice(["fig_bundle", "fig_pointing", "fig_chest"]), placement(p.x, p.y, p.z,
                                                                                    rng.uniform(0, 6.3)))
    for local in ((-1.5, 9.0), (2.5, 11.5), (-3.0, 15.0), (1.5, 24.0), (-8.0, 26.0)):
        p = vettii_frame @ Vector((local[0], local[1], 0.25))
        scene.add(rng.choice(["fig_veiled", "fig_pointing", "fig_chest", "fig_child"]),
                  placement(p.x, p.y, p.z, plan.heading_of(-plan.FB) + rng.uniform(-1.2, 1.2)))
    stabiana = next(spec for spec in specs if spec["points"][0] == plan.STABIANA[0])
    for k in range(12):
        position, z, heading = street_spot(stabiana, 40.0 + k * 22.0, rng.choice((-1, 1)), rng.uniform(0.0, 1.5))
        scene.add(rng.choice(["fig_bundle", "family", "household_b", "handcart", "pack_train", "fig_veiled"]),
                  placement(position.x, position.y, z, heading + (0.0 if k % 3 else math.pi)))
    for spec in specs:
        if spec["kind"] != "minor" or not spec.get("rows"):
            continue
        for row in spec["rows"][::28]:
            if row[3] and rng.random() < 0.25:
                position, normal, z = row[0], row[1], row[2]
                tangent = Vector((normal.y, -normal.x))
                scene.add(rng.choice(["fig_bundle", "fig_veiled", "fig_cushion", "fig_chest", "dog", "family"]),
                          placement(position.x, position.y, z, math.atan2(-tangent.x, tangent.y)
                                    + rng.choice((0.0, math.pi))))


def place_life(scene, eyes):
    counts = {}
    for key in list(scene.placements):
        scene.placements[key] = [matrix for matrix in scene.placements[key]
                                 if min((matrix.translation.to_2d() - eye).length for eye in eyes) > 7.0]
        radius = 1.6 if key in ("wagon", "handcart", "pack_train", "road_column", "road_column_b", "family",
                                "household", "household_b") else 0.7
        matrices = clear_of_routes(scene, scene.placements[key], radius)
        matrices = [grounded(scene, matrix) for matrix in matrices]
        scene.instances("life", key, pompei_life.LIFE[key], matrices, cast_shadow=key not in ("dog",))
        counts[key] = len(matrices)
    return counts


def place_effects(scene, vettii_frame, forum_frame, level):
    root = scene.root("life")
    vx, vy, vz = pterrain.vent_position(pterrain.frame_for(*plan.ORIGIN))
    new_empty("eruption_vent", scene.collection, root, Matrix.Translation((vx, vy, vz)))
    wall = [Vector(p[:2]) for p in plan.wall_trace()]
    ash_points = [plan.grid_point(u, v) for u, v in ((-200.0, 120.0), (60.0, 60.0), (300.0, 120.0), (520.0, 0.0),
                                                     (-120.0, -60.0), (200.0, -150.0), (420.0, -200.0),
                                                     (-280.0, 300.0))]
    for index, point in enumerate(ash_points):
        new_empty(f"ash_{index}", scene.collection, root,
                  Matrix.Translation((point.x, point.y, scene.ground(point.x, point.y) + 290.0)))
    smokes = [vettii_frame @ Vector((14.0, 8.0, 9.0)), plan.grid_point(150.0, 60.0).to_3d(),
              plan.grid_point(380.0, -60.0).to_3d()]
    for index, point in enumerate(smokes):
        z = point.z if point.z > 0 else scene.ground(point.x, point.y) + 9.0
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation((point.x, point.y, z)))
    flocks = [(Vector((-60.0, 40.0)), 45.0), (Vector((420.0, 160.0)), 40.0), (Vector((-420.0, -200.0)), 30.0),
              (Vector((760.0, 230.0)), 50.0)]
    for index, (point, height) in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root,
                  Matrix.Translation((point.x, point.y, scene.ground(point.x, point.y) + height)))
    for index, (key, build) in enumerate(pompei_life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda build=build: remap(build()), ground_occlusion=False)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return {"ash": len(ash_points), "smoke": len(smokes), "birds": len(flocks), "walkers": len(pompei_life.WALKERS)}


def viewpoints(scene, specs, forum_frame, level, vettii_frame, gate_frames):
    points = {}
    eye = Vector((250.0, -1750.0, 390.0))
    target = Vector((-1150.0, 2550.0, 260.0))
    points["vue-d-ensemble"] = (eye, target)
    points["le-forum"] = (forum_frame @ Vector((0.0, -64.0, 5.5)), forum_frame @ Vector((0.0, 45.0, 8.0)))
    abbondanza = next(spec for spec in specs if spec["points"][0] == plan.ABBONDANZA[0])
    eye_point = plan.grid_point(plan.THERMOPOLIUM_U - 4.0, abbondanza["road"] / 2 + abbondanza["walk"] * 0.6)
    target_point = plan.grid_point(plan.THERMOPOLIUM_U + 3.5, -6.5)
    z = scene.ground(eye_point.x, eye_point.y) + abbondanza["kerb"]
    points["la-rue"] = (Vector((eye_point.x, eye_point.y, z + 1.65)),
                        Vector((target_point.x, target_point.y, scene.ground(target_point.x, target_point.y) + 1.6)))
    points["la-maison"] = (vettii_frame @ Vector((0.0, 6.2, 0.25 + 1.6)), vettii_frame @ Vector((0.0, 24.0, 2.6)))
    gate_frame = gate_frames["marina"]
    eye_point = gate_frame @ Vector((1.4, 9.0, 0.0))
    target_point = gate_frame @ Vector((3.0, -140.0, 0.0))
    points["la-porte-marine"] = (Vector((eye_point.x, eye_point.y, scene.ground(eye_point.x, eye_point.y) + 1.7)),
                                 Vector((target_point.x, target_point.y,
                                         scene.ground(target_point.x, target_point.y) + 9.0)))
    return points


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))


def weather_all(scene):
    done = set()
    for name, root in scene.roots.items():
        if name in ("terrain", "life", "markers"):
            continue
        for item in root.children_recursive:
            if item.type != "MESH" or item.data.name in done:
                continue
            mesh = item.data
            done.add(mesh.name)
            seed = sum(ord(character) for character in mesh.name) % 97
            heights = None
            if item.parent is root:
                co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
                mesh.vertices.foreach_get("co", co)
                co = co.reshape(-1, 3)
                heights = co[:, 2] - scene.field.sample(co[:, 0], co[:, 1])
            nimes_detail.weather(mesh, heights, seed, walls=True, roofs=True,
                                 foliage=name in ("gardens", "countryside"))


def render_previews(options, points):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(points) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.35, aerosol=1.2)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 3.4, (1.0, 0.86, 0.70), 1.2)
    haze_volume(stage, 45000.0, 2500.0, 0.00009, (0.62, 0.58, 0.54), 0.25)
    configure_render(1280, 720, options["samples"], exposure=-0.4, volumetric_end=40000.0)
    timings = {}
    lenses = {"vue-d-ensemble": 30.0, "le-forum": 26.0, "la-rue": 24.0, "la-maison": 18.0, "la-porte-marine": 18.0}
    for name in names:
        eye, target = points[name]
        rig = camera(stage, f"cam_{name}", eye, target, lens=lenses.get(name, 30.0))
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
    frame = pterrain.frame_for(*plan.ORIGIN)
    dem = pterrain.load_dem(CACHE)
    wall = [tuple(p) for p in plan.wall_trace()]
    field, masks, vent = pterrain.condition(frame, dem, *FIELD_ORIGIN, FIELD_SIZE, FIELD_SPACING, wall, TOWN_CENTRE)
    del dem
    scene = Scene(tiles, field)
    rng = random.Random(79)
    sites = plan.sites()
    level = forum_level(scene)
    specs = street_specs(scene, sites, [Vector(p) for p in wall])
    forum_poly = plan.forum_rect(-plan.FORUM_HALF[0] - 6.0, plan.FORUM_HALF[0] + 6.0,
                                 -plan.FORUM_HALF[1] - plan.PORTICO - 2.0, plan.FORUM_HALF[1] + plan.PORTICO + 2.0)
    venus_poly = plan.forum_rect(plan.VENUS[0] - 32.0, plan.VENUS[0] + 32.0, plan.VENUS[1] - 32.0,
                                 plan.VENUS[1] + 28.0)
    vettii_poly = sites["vettii"]
    v_level = venus_level(scene)

    def carve(xs, ys, heights):
        result = heights.copy()
        for polygon, target in ((forum_poly, level - 0.5), (venus_poly, v_level - 0.5),
                                (vettii_poly, scene.ground(*plan.forum_point(*plan.VETTII)) - 0.3)):
            inside = polygon_mask([tuple(p) for p in polygon], xs, ys)
            result = np.where(inside, np.minimum(result, target), result)
        for spec in specs:
            distance = polyline_distance([tuple(p) for p in spec["points"]], xs, ys)
            result = np.where(distance < spec["half"] + 1.0, result - 0.45, result)
        return result

    build_terrain(scene, masks, carve)
    print("TERRAIN", round(time.perf_counter() - started, 1), flush=True)
    stones = build_streets(scene, specs)
    stone_count = place_stepping_stones(scene, stones)
    print("STREETS", round(time.perf_counter() - started, 1), flush=True)
    forum_frame, column_count = build_forum(scene, level)
    build_west_monuments(scene, level)
    venus_frame, _ = build_venus(scene)
    vettii_frame = build_vettii(scene)
    thermo_frame, thermo_rect = build_thermopolium(scene, specs)
    planes = build_east_monuments(scene)
    scene.instances("monuments", "tree_plane", TREE_BUILDS["tree_plane"], planes)
    tower_count = build_walls(scene, wall)
    gate_frames = build_gates(scene, specs)
    points = viewpoints(scene, specs, forum_frame, level, vettii_frame, gate_frames)
    eyes = [eye.to_2d() for key, (eye, _) in points.items() if key != "vue-d-ensemble"]
    sites_for_units = dict(sites)
    sites_for_units["thermopolium"] = thermo_rect
    units, occupancy = frontage(scene, specs, sites_for_units, eyes, rng)
    programmes = build_units(scene, units, rng)
    print("UNITS", len(units), round(time.perf_counter() - started, 1), flush=True)
    gardens = place_gardens(scene, occupancy, specs, sites_for_units, rng)
    for key, frames in gardens.items():
        scene.instances("gardens", key, TREE_BUILDS[key], frames, cast_shadow=key != "shrub")
    country = build_countryside(scene, rng)
    shore = build_shore(scene, rng)
    scene.flush({"venus_site": True})
    build_surface(scene)
    place_markers(scene, points)
    route_counts = build_routes(scene, specs, gate_frames, vettii_frame, forum_frame, level)
    populate(scene, specs, forum_frame, level, venus_frame, vettii_frame, thermo_frame, gate_frames, rng)
    life_counts = place_life(scene, eyes)
    effects = place_effects(scene, vettii_frame, forum_frame, level)
    weather_all(scene)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    statistics["total"]["stored_triangles"] = sum(value.get("stored_triangles", 0) for key, value in
                                                  statistics.items() if key != "total")
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "pompei.glb")
    export_seconds = export_glb(glb, roots)
    report = {
        "sun": [SUN_AZIMUTH, SUN_ELEVATION], "forum_level": round(level, 2),
        "vent": [round(value, 1) for value in pterrain.vent_position(frame)],
        "counts": {"units": len(units), "programmes": programmes, "stepping_stones": stone_count,
                   "forum_columns": column_count, "towers": tower_count, "gardens": {k: len(v) for k, v in
                                                                                      gardens.items()},
                   "countryside": country, "routes": route_counts, "life": life_counts, "effects": effects},
        "shore": [round(shore.x, 1), round(shore.y, 1)],
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "build_seconds": round(time.perf_counter() - started, 1),
        "elevation_source": pterrain.DEM_URL, "elevation_licence": pterrain.DEM_LICENCE,
        "texture_credits": credits,
        "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                    for key, (eye, target) in points.items()},
    }
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in points.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("BUILD", round(time.perf_counter() - started, 1), flush=True)
    print("PREVIEWS", json.dumps(render_previews(options, points)), flush=True)


main()

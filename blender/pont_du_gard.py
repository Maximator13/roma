import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector

from kit import pont_life
from kit.geometry import MeshBuilder, TemplateLibrary, ensure_collection, new_empty, new_object, placement
from kit.materials import baked_material, save_pixels
from kit.pont_bridge import (BASIN_INNER, BASIN_RIM, BASIN_WALL, SLAB_THICKNESS, TIER1_SPANS, Layout, Segment,
                             abutment_path, build_bridge, oriented, weathering)
from kit.pont_materials import GROUND_BASE, GROUND_TILE, build_pont_library
from kit.pont_routes import Planner, chaikin, densify, grades
from kit.pont_terrain import Field, Ground, distance_to_mask, geo_sample, grid_mesh
from kit.stage import (camera, configure_render, evening_world, export_glb, group_statistics, haze_volume,
                       render_still, sun_lamp)
from kit.terrain import ETALAB_LICENCE, RGE_ALTI_LAYER, GeoFrame, fetch_lambert_grid, polyline_distance, value_noise

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PROJECT, ".cache", "scenes", "pont-du-gard")
BLEND = os.path.join(CACHE, "work", "pont-du-gard.blend")
ORIGIN = (43.94725, 4.53529)
BASIN_GEO = (43.9484, 4.5315)
BEARING = 130.9
ARCH_S = -31.0
DATUM = 18.0
BASE_NGF = 18.2
X0, Y0, SIZE = -800.0, -550.0, 1600.0
SPACING = 2.0
COARSE = 10.0
FAR_HALF = 6000.0
FAR_SPACING = 150.0
SUN_AZIMUTH = 291.0
SUN_ELEVATION = 12.0
LOW_WATER_DROP = 0.3
PATCH = (-360.0, 190.0, -215.0, 112.0)
PATCH_SPACING = 3.0
BASIN_PATCH_SPACING = 1.25
QUARRY_CENTRE = (275.0, 688.0)
QUARRY_HALF = 92.0
QUARRY_PIT = [(205.0, 640.0), (208.0, 690.0), (233.0, 726.0), (285.0, 737.0), (331.0, 716.0), (346.0, 682.0),
              (331.0, 656.0), (290.0, 646.0), (250.0, 637.0)]
QUARRY_FRONT = [0, 1, 2, 3, 4, 5]
QUARRY_FLOOR = 23.2
DIKE = [(212.0, 630.0), (252.0, 628.0), (292.0, 637.0), (338.0, 648.0), (354.0, 664.0)]
DIKE_BREACHES = [(0.33, 0.39), (0.7, 0.76)]
TOMBS = (318.0, 688.0)
FARM = (-31.0, 505.0)
SLAB_GAP = 6.0
MAX_GRADE = 0.25
AXIS = Vector((math.sin(math.radians(BEARING)), math.cos(math.radians(BEARING))))
ACROSS = Vector((-AXIS.y, AXIS.x))
BRIDGE_ORIGIN = AXIS * ARCH_S
PATHS = {
    "rive-droite": [("b", 88.0, -125.0), ("b", 45.0, -40.0), ("b", 27.5, -11.0), ("b", 27.5, 11.0),
                    ("b", 45.0, 50.0), ("b", 62.0, 88.0)],
    "plateau-culee": [("a", 0.92, 11.0), ("a", 0.6, 11.0), ("a", 0.3, 11.0), ("a", 0.0, 13.0), ("b", -150.0, 22.0)],
    "rive-gauche": [("b", -150.0, 22.0), ("b", -68.0, 76.0), ("w", -40.0, 330.0), ("w", 40.0, 420.0),
                    ("w", 140.0, 480.0), ("w", 190.0, 560.0), ("w", 205.0, 620.0)],
    "garrigue": [("b", 150.0, -150.0), ("b", 154.0, -110.0), ("b", 179.0, -70.0), ("b", 204.0, -40.0)],
    "carriere": [("w", 225.0, 662.0), ("w", 262.0, 690.0), ("w", 295.0, 712.0), ("w", 332.0, 706.0)],
}
TRACKS = {"domaine": [(-31.0, 470.0), (40.0, 420.0)]}
GROUND_POIS = ("le-pont", "la-grande-arche", "la-carriere", "le-bassin")


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"previews": "all", "samples": 24}
    for item in values:
        key, _, value = item.partition("=")
        options[key.lstrip("-")] = value
    options["samples"] = int(options["samples"])
    return options


def to_bridge(x, y):
    dx = np.asarray(x) - BRIDGE_ORIGIN.x
    dy = np.asarray(y) - BRIDGE_ORIGIN.y
    return dx * AXIS.x + dy * AXIS.y, dx * ACROSS.x + dy * ACROSS.y


def from_bridge(u, w):
    return BRIDGE_ORIGIN.x + AXIS.x * u + ACROSS.x * w, BRIDGE_ORIGIN.y + AXIS.y * u + ACROSS.y * w


BRIDGE_MATRIX = (Matrix.Translation((BRIDGE_ORIGIN.x, BRIDGE_ORIGIN.y, 0.0))
                 @ Matrix.Rotation(math.atan2(AXIS.y, AXIS.x), 4, "Z"))


def heading(direction):
    return math.atan2(-direction[0], direction[1])


def dilate(mask):
    padded = np.pad(mask, 1)
    return mask | padded[:-2, 1:-1] | padded[2:, 1:-1] | padded[1:-1, :-2] | padded[1:-1, 2:]


def normalised_blur(values, weights, passes):
    total = values * weights
    weight = weights.astype(float)
    for _ in range(passes):
        padded = np.pad(total, 1, mode="edge")
        total = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] + 4 * total) / 8
        padded = np.pad(weight, 1, mode="edge")
        weight = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] + 4 * weight) / 8
    return total / np.maximum(weight, 1e-6)


def polygon_inside(points, xs, ys):
    inside = np.zeros(np.shape(xs), dtype=bool)
    count = len(points)
    for index in range(count):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % count]
        crosses = (y0 > ys) != (y1 > ys)
        with np.errstate(divide="ignore", invalid="ignore"):
            intersection = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)
        inside ^= crosses & (xs < intersection)
    return inside


def ranked(values):
    order = np.argsort(values, axis=None)
    ranks = np.empty(values.size)
    ranks[order] = np.arange(values.size) / max(values.size - 1, 1)
    return ranks.reshape(values.shape)


def point_distance(points, x, y):
    return float(polyline_distance(points, np.array([x]), np.array([y]))[0])


def load_terrain():
    frame = GeoFrame(*ORIGIN)
    centre_frame = GeoFrame(*frame.to_geo(X0 + SIZE / 2, Y0 + SIZE / 2))
    near = fetch_lambert_grid(centre_frame, SIZE / 2 + 60.0, 2.0, RGE_ALTI_LAYER,
                              os.path.join(CACHE, "src", "rge_alti_l93_2m.bil"))
    far = fetch_lambert_grid(centre_frame, FAR_HALF + 200.0, 50.0, RGE_ALTI_LAYER,
                             os.path.join(CACHE, "src", "rge_alti_l93_50m.bil"))
    count = int(SIZE / SPACING) + 1
    axis_x = X0 + SPACING * np.arange(count)
    axis_y = Y0 + SPACING * np.arange(count)
    gx, gy = np.meshgrid(axis_x, axis_y)
    field = Field(X0, Y0, SPACING, geo_sample(frame, gx, gy, near))
    field.blur(np.ones(field.heights.shape, dtype=bool), 3)
    far_count = int(2 * FAR_HALF / FAR_SPACING) + 1
    fx = X0 + SIZE / 2 - FAR_HALF + FAR_SPACING * np.arange(far_count)
    fy = Y0 + SIZE / 2 - FAR_HALF + FAR_SPACING * np.arange(far_count)
    fgx, fgy = np.meshgrid(fx, fy)
    far_field = Field(fx[0], fy[0], FAR_SPACING, geo_sample(frame, fgx, fgy, far))
    return field, far_field, [near[2], far[2]]


def river(field):
    h = field.heights
    candidate = (h < 19.3) & (field.slope() < 0.12)
    row = int(round((BRIDGE_ORIGIN.y - field.y0) / field.spacing))
    column = int(round((BRIDGE_ORIGIN.x - field.x0) / field.spacing))
    window = (slice(row - 50, row + 50), slice(column - 50, column + 50))
    score = h[window] + 30.0 * field.slope()[window]
    r, c = np.unravel_index(np.argmin(score), score.shape)
    mask = np.zeros(h.shape, dtype=bool)
    mask[row - 50 + r, column - 50 + c] = True
    for _ in range(4000):
        grown = dilate(mask) & candidate
        if grown.sum() == mask.sum():
            break
        mask = grown
    level = normalised_blur(np.where(mask, h, 0.0), mask, 80) - LOW_WATER_DROP
    shore = distance_to_mask(~mask, field.spacing, 40)
    bed = h - LOW_WATER_DROP - np.minimum(0.34 * shore, 3.4) - 0.05
    field.heights = np.where(mask, bed, h)
    return mask, level


def arcade_saddle(field, layout):
    u, w = to_bridge(field.grid_x, field.grid_y)
    arcade = (u > layout.tier3_start - 2.0) & (u < layout.tier2_start - 4.0)
    ceiling = layout.tops[1] + DATUM + 1.0
    cut = np.maximum(field.heights - ceiling, 0.0) * np.exp(-(w / 14.0) ** 2) * arcade
    field.heights = field.heights - cut
    return float(cut.max())


class Works:
    def __init__(self, layout, field):
        local = GeoFrame(*ORIGIN).to_local(*BASIN_GEO)
        bu, bw = to_bridge(*local)
        points, centre, toward, length = abutment_path(layout, (float(bu), float(bw)))
        self.points = points
        self.centre = centre
        self.toward = toward
        self.length = length
        self.frame = Segment(centre + toward, centre)
        levels = []
        for side in (-1, 1):
            su, sw = self.frame.to_bridge(0.0, side * 14.0)
            levels.append(float(field.sample(*from_bridge(float(su), float(sw)))))
        self.discharge = -1 if levels[0] < levels[1] else 1
        self.slab_top = layout.tops[2] + DATUM
        self.floor = layout.specus_floor + DATUM
        self.coping = self.slab_top - SLAB_THICKNESS + 0.25
        self.half = (BASIN_INNER[0] / 2 + BASIN_WALL + BASIN_RIM, BASIN_INNER[1] / 2 + BASIN_WALL + BASIN_RIM)
        stub_end = centre - toward * (self.half[0] + 15.0)
        self.line = [from_bridge(p.x, p.y) for p in list(points) + [centre]]
        self.stub = [from_bridge(p.x, p.y) for p in (centre, stub_end)]
        self.world_centre = Vector(from_bridge(centre.x, centre.y))
        su, sw = self.frame.to_bridge(0.0, self.discharge * (self.half[1] + 21.0))
        self.channel = [from_bridge(*self.frame.to_bridge(0.0, self.discharge * self.half[1])),
                        from_bridge(float(su), float(sw))]

    def basin_local(self, xs, ys):
        bu, bw = to_bridge(xs, ys)
        cos, sin = math.cos(self.frame.angle), math.sin(self.frame.angle)
        du, dw = bu - self.frame.far.x, bw - self.frame.far.y
        return du * cos + dw * sin, -du * sin + dw * cos

    def outside(self, xs, ys):
        lu, lv = self.basin_local(xs, ys)
        return np.maximum(np.abs(lu) - self.half[0], np.abs(lv) - self.half[1])

    def carve(self, xs, ys, heights):
        distance = polyline_distance(self.line, xs, ys)
        heights = np.minimum(heights, self.slab_top - 0.04 + np.clip(distance - 2.2, 0, None) * 0.35)
        heights = np.minimum(heights, self.coping - 0.03 + np.clip(self.outside(xs, ys) - 3.0, 0, None) * 0.35)
        lu, lv = self.basin_local(xs, ys)
        interior = (np.abs(lu) < BASIN_INNER[0] / 2 + 0.2) & (np.abs(lv) < BASIN_INNER[1] / 2 + 0.2)
        return np.where(interior, np.minimum(heights, self.floor - 0.3), heights)

    def blocked(self, x, y, margin):
        point = np.array([x]), np.array([y])
        if float(polyline_distance(self.line, *point)[0]) < 2.6 + margin:
            return True
        if float(polyline_distance(self.stub, *point)[0]) < 2.6 + margin:
            return True
        if float(polyline_distance(self.channel, *point)[0]) < 1.2 + margin:
            return True
        return float(self.outside(*point)[0]) < margin


def carve_quarry(field):
    loop = QUARRY_PIT + [QUARRY_PIT[0]]
    inside = polygon_inside(QUARRY_PIT, field.grid_x, field.grid_y) | (
        polyline_distance(loop, field.grid_x, field.grid_y) < 5.0)
    noise = value_noise(field.heights.shape, 60, 31, 3)
    floor = QUARRY_FLOOR + (noise - 0.5) * 0.8
    field.heights = np.where(inside, np.minimum(field.heights, floor), field.heights)
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(DIKE[:-1], DIKE[1:]))
    along = np.zeros(field.heights.shape)
    best = np.full(field.heights.shape, np.inf)
    travelled = 0.0
    for (x0, y0), (x1, y1) in zip(DIKE[:-1], DIKE[1:]):
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        t = np.clip(((field.grid_x - x0) * dx + (field.grid_y - y0) * dy) / (length * length), 0, 1)
        d = np.hypot(field.grid_x - x0 - t * dx, field.grid_y - y0 - t * dy)
        along = np.where(d < best, (travelled + t * length) / total, along)
        best = np.minimum(best, d)
        travelled += length
    front = [QUARRY_PIT[index] for index in QUARRY_FRONT]
    apron = QUARRY_FLOOR + 1.5 - 0.22 * polyline_distance(front, field.grid_x, field.grid_y)
    field.heights = np.where(inside, np.maximum(field.heights, apron), field.heights)
    breach = np.zeros(field.heights.shape, dtype=bool)
    for a, b in DIKE_BREACHES:
        breach |= (along > a) & (along < b)
    crest = QUARRY_FLOOR + 3.4 + (noise - 0.5) * 2.4
    bump = np.exp(-(best / 5.5) ** 2)
    raised = field.heights * (1 - bump) + crest * bump
    field.heights = np.where(~breach & (bump > 0.05), np.maximum(field.heights, raised), field.heights)
    field.heights = np.where(breach & (best < 7.0), np.minimum(field.heights, QUARRY_FLOOR - 0.3), field.heights)
    return inside


def dike_point(fraction):
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(DIKE[:-1], DIKE[1:]))
    target = fraction * total
    for a, b in zip(DIKE[:-1], DIKE[1:]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if target <= length:
            t = target / length
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        target -= length
    return DIKE[-1]


def classify(xs, ys, h, slope, water_level, near_water, quarry_inside, noise, fine, speck, maquis, far_weight,
             roads=None, mottle=None):
    rock_pale = np.array([0.62, 0.58, 0.5])
    rock_grey = np.array([0.5, 0.48, 0.44])
    soil = np.array([0.55, 0.47, 0.35])
    dry = np.array([0.60, 0.55, 0.41])
    garrigue = np.array([0.30, 0.34, 0.21])
    wood = np.array([0.17, 0.24, 0.11])
    canopy = np.array([0.12, 0.2, 0.08])
    gravel = np.array([0.49, 0.46, 0.40])
    shingle = np.array([0.55, 0.53, 0.48])
    olive = np.array([0.22, 0.26, 0.15])
    straw = np.array([0.62, 0.55, 0.36])
    path = np.array([0.68, 0.61, 0.48])
    colour = garrigue * (0.88 + 0.24 * fine)[..., None]
    open_ground = np.clip((noise - 0.55) * 4.0, 0, 1) * np.clip(1.2 - slope * 1.5, 0, 1) * 0.8
    colour = colour * (1 - open_ground[..., None]) + dry * open_ground[..., None]
    forest = np.clip((slope - 0.2) * 2.5, 0, 1) * np.clip((0.5 - noise) * 4.0, 0, 1) * 0.5
    colour = colour * (1 - forest[..., None]) + wood * forest[..., None]
    soil_mix = np.clip((fine - 0.64) * 4.0, 0, 1) * 0.45
    colour = colour * (1 - soil_mix[..., None]) + soil * soil_mix[..., None]
    blotch = np.clip((maquis - 0.42) * 4.0, 0, 1) * np.clip(1.6 - slope, 0, 1) * far_weight * 0.92
    crowns = 0.7 + 0.6 * speck
    colour = colour * (1 - blotch[..., None]) + canopy * crowns[..., None] * blotch[..., None]
    above = h - water_level
    if mottle is not None:
        patches = np.clip((mottle - 0.5) * 5.0, 0, 1)
        scrub = straw * (1 - patches[..., None]) + olive * patches[..., None]
        weight = np.clip((above - 3.0) / 2.0, 0, 1) * (1 - quarry_inside) * 0.8
        colour = colour * (1 - weight[..., None]) + scrub * weight[..., None]
    rock = np.clip((slope - 0.75) * 2.0, 0, 1) * np.clip(0.35 + fine, 0, 0.85)
    rock = np.maximum(rock, np.clip((slope - 0.4) * 2.5, 0, 1) * np.clip((speck - 0.58) * 6.0, 0, 1) * 0.85)
    rock_colour = rock_pale * (1 - noise[..., None] * 0.6) + rock_grey * noise[..., None] * 0.6
    colour = colour * (1 - rock[..., None]) + rock_colour * rock[..., None]
    shore = np.clip(1.0 - (above - 1.5) / 2.5, 0, 1) * near_water
    shore_colour = np.where((fine > 0.5)[..., None], shingle, gravel)
    colour = colour * (1 - shore[..., None]) + shore_colour * shore[..., None]
    wet = np.clip(1.0 - above / 0.5, 0, 1) * near_water
    colour = colour * (1 - wet[..., None] * 0.45) + np.array([0.36, 0.35, 0.3]) * wet[..., None] * 0.45
    weeds = np.clip((fine - 0.45) * 3.0, 0, 1) * 0.55
    if mottle is not None:
        weeds = 0.35 + 0.65 * np.clip((mottle - 0.35) * 2.5, 0, 1)
    meadow = np.array([0.42, 0.45, 0.28])
    quarry_colour = straw * (1 - weeds[..., None]) + meadow * weeds[..., None]
    colour = np.where(quarry_inside[..., None], quarry_colour * (0.9 + 0.2 * fine)[..., None], colour)
    if roads is not None:
        track = np.clip(1.0 - (roads - 0.6) / 1.0, 0, 1) * (0.55 + 0.35 * fine)
        colour = colour * (1 - track[..., None]) + path * track[..., None]
        farm = (np.clip(1.0 - (np.hypot(xs - FARM[0], ys - FARM[1]) - 70.0) / 30.0, 0, 1)
                * np.clip(1 - slope * 4, 0, 1))
        rows = (np.sin((xs * 0.6 + ys * 0.8) * 2 * math.pi / 2.4) > 0.3) & (farm > 0.5)
        field_colour = np.where(rows[..., None], np.array([0.42, 0.44, 0.26]), np.array([0.66, 0.55, 0.38]))
        colour = colour * (1 - farm[..., None] * 0.85) + field_colour * farm[..., None] * 0.85
    return np.clip(colour * (0.94 + 0.1 * noise)[..., None], 0, 1)


def sun_shadow(field, xs, ys, heights, steps=40, reach=900.0):
    azimuth = math.radians(SUN_AZIMUTH)
    direction = (math.sin(azimuth), math.cos(azimuth))
    slope = math.tan(math.radians(SUN_ELEVATION))
    clearance = np.full(heights.shape, np.inf)
    for step in range(1, steps + 1):
        distance = reach * (step / steps) ** 1.6
        ahead = field.sample(xs + direction[0] * distance, ys + direction[1] * distance)
        clearance = np.minimum(clearance, heights + distance * slope - ahead)
    return np.clip(clearance / 5.0 + 0.5, 0.0, 1.0)


class Scene:
    def __init__(self, tiles):
        self.tiles = tiles
        self.library = TemplateLibrary(tiles)
        self.collection = ensure_collection("PontDuGard")
        self.roots = {}
        self.placements = {}

    def root(self, name):
        if name not in self.roots:
            self.roots[name] = new_empty(name, self.collection)
        return self.roots[name]

    def add(self, key, matrix):
        self.placements.setdefault(key, []).append(matrix)


class Maps:
    def __init__(self, field, mask, level, quarry_inside):
        self.field = field
        self.mask = mask
        self.level = normalised_blur(np.where(mask, level, 0.0), mask, 60)
        self.near_water = (distance_to_mask(mask, field.spacing, 30) < 45.0).astype(float)
        self.quarry = quarry_inside.astype(float)
        self.slope = field.slope()
        shape = field.heights.shape
        speck = value_noise(shape, 260, 9, 2)
        arrays = {"level": self.level, "near_water": self.near_water, "quarry": self.quarry, "slope": self.slope,
                  "mask": mask.astype(float), "noise": ranked(value_noise(shape, 14, 5, 5)),
                  "fine": ranked(value_noise(shape, 70, 6, 3)), "speck": ranked(speck),
                  "maquis": ranked(value_noise(shape, 45, 8, 4)), "mottle": ranked(value_noise(shape, 120, 41, 3))}
        self.fields = {name: Field(X0, Y0, SPACING, array) for name, array in arrays.items()}
        self.roads = None
        self.trees = []

    def at(self, name, xs, ys):
        return self.fields[name].sample(xs, ys)

    def colour(self, xs, ys):
        distance = np.hypot(xs - BRIDGE_ORIGIN.x, ys - BRIDGE_ORIGIN.y)
        quarry = np.hypot(xs - QUARRY_CENTRE[0], ys - QUARRY_CENTRE[1])
        far_weight = 0.55 + 0.45 * np.clip((np.minimum(distance - 330.0, quarry - 170.0)) / 120.0, 0, 1)
        roads = np.min([polyline_distance(points, xs, ys) for points in self.roads], axis=0)
        colour = classify(xs, ys, self.field.sample(xs, ys), self.at("slope", xs, ys), self.at("level", xs, ys),
                          self.at("near_water", xs, ys), self.at("quarry", xs, ys) > 0.5, self.at("noise", xs, ys),
                          self.at("fine", xs, ys), self.at("speck", xs, ys), self.at("maquis", xs, ys), far_weight,
                          roads, self.at("mottle", xs, ys))
        return colour

    def canopy(self, colour, xs, ys):
        shade = np.array([0.16, 0.2, 0.11])
        for x, y, radius in self.trees:
            c0, c1 = np.searchsorted(xs, [x - radius, x + radius])
            r0, r1 = np.searchsorted(ys, [y - radius, y + radius])
            if c1 <= c0 or r1 <= r0:
                continue
            gx, gy = np.meshgrid(xs[c0:c1], ys[r0:r1])
            weight = np.clip(1.0 - np.hypot(gx - x, gy - y) / radius, 0, 1) ** 0.7 * 0.6
            window = colour[r0:r1, c0:c1]
            colour[r0:r1, c0:c1] = window * (1 - weight[..., None]) + shade * weight[..., None]
        return colour

    def water(self, x, y):
        return float(self.at("level", x, y))


def patch_cells(cxs, cys, works, routes):
    centre_x = (cxs[:-1] + cxs[1:]) / 2
    centre_y = (cys[:-1] + cys[1:]) / 2
    gx, gy = np.meshgrid(centre_x, centre_y)
    u0, u1, w0, w1 = PATCH
    pu, pw = to_bridge(gx, gy)
    bridge = (pu > u0) & (pu < u1) & (pw > w0) & (pw < w1)
    bridge |= np.min([polyline_distance(points, gx, gy) for points in routes], axis=0) < 13.0
    quarry = (np.abs(gx - QUARRY_CENTRE[0]) < QUARRY_HALF) & (np.abs(gy - QUARRY_CENTRE[1]) < QUARRY_HALF)
    basin = np.hypot(gx - works.world_centre.x, gy - works.world_centre.y) < 21.0
    return {"ground_bridge": (bridge & ~quarry & ~basin, PATCH_SPACING), "ground_quarry": (quarry, 2.5),
            "ground_basin": (basin, BASIN_PATCH_SPACING)}


def seam_heights(field, wx, wy, heights, keep):
    padded = np.pad(keep.astype(int), 1)
    touching = padded[:-1, :-1] + padded[:-1, 1:] + padded[1:, :-1] + padded[1:, 1:]
    boundary = (touching > 0) & (touching < 4)
    fx = (wx - X0) / COARSE
    fy = (wy - Y0) / COARSE
    on_x = np.isclose(fx, np.round(fx), atol=1e-4)
    on_y = np.isclose(fy, np.round(fy), atol=1e-4)
    x_lo = np.floor(fx + 1e-6) * COARSE + X0
    y_lo = np.floor(fy + 1e-6) * COARSE + Y0
    tx = (wx - x_lo) / COARSE
    ty = (wy - y_lo) / COARSE
    along_y = field.sample(wx, y_lo) * (1 - ty) + field.sample(wx, y_lo + COARSE) * ty
    along_x = field.sample(x_lo, wy) * (1 - tx) + field.sample(x_lo + COARSE, wy) * tx
    seam = np.where(on_x & on_y, field.sample(wx, wy), np.where(on_x, along_y, along_x))
    return np.where(boundary & (on_x | on_y), seam, heights)


def decimate_terrain(obj, claimed, ratio):
    count = len(obj.data.vertices)
    positions = np.empty(count * 3)
    obj.data.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    columns = np.round((positions[:, 0] - X0) / COARSE).astype(int)
    rows = np.round((positions[:, 1] - Y0) / COARSE).astype(int)
    padded = np.pad(claimed, 1, constant_values=True)
    touching = (padded[rows, columns] | padded[rows + 1, columns] | padded[rows, columns + 1]
                | padded[rows + 1, columns + 1])
    group = obj.vertex_groups.new(name="keep")
    group.add([int(index) for index in np.nonzero(touching)[0]], 1.0, "REPLACE")
    modifier = obj.modifiers.new("decimate", "DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = ratio
    modifier.use_collapse_triangulate = True
    modifier.vertex_group = "keep"
    modifier.vertex_group_factor = 1000.0
    modifier.invert_vertex_group = True
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(evaluated)
    obj.modifiers.clear()
    obj.vertex_groups.clear()
    obj.data = mesh
    return len(mesh.polygons)


def build_terrain(scene, maps, far_field, works):
    root = scene.root("terrain")
    field = maps.field
    resolution = 2048
    axis_x = np.linspace(X0, X0 + SIZE, resolution)
    axis_y = np.linspace(Y0, Y0 + SIZE, resolution)
    bx, by = np.meshgrid(axis_x, axis_y)
    colour = maps.canopy(maps.colour(bx, by), axis_x, axis_y)
    colour *= (0.85 + 0.15 * sun_shadow(field, bx, by, field.sample(bx, by)))[..., None]
    image = save_pixels("terrain_colour", colour, os.path.join(CACHE, "textures", "terrain_colour.jpg"), quality=88)
    material = baked_material("terrain", image)
    material.use_backface_culling = True
    cxs = X0 + COARSE * np.arange(int(SIZE / COARSE) + 1)
    cys = Y0 + COARSE * np.arange(int(SIZE / COARSE) + 1)
    cgx, cgy = np.meshgrid(cxs, cys)
    cells = patch_cells(cxs, cys, works, maps.roads)
    claimed = np.zeros(cells["ground_bridge"][0].shape, dtype=bool)
    for mask, _ in cells.values():
        claimed |= mask
    mesh = grid_mesh("terrain", cxs, cys, field.sample(cgx, cgy) - DATUM, keep=~claimed,
                     uv=lambda x, y: np.column_stack([(x - X0) / SIZE, (y - Y0) / SIZE]))
    mesh.materials.append(material)
    terrain = new_object("terrain", mesh, scene.collection, root)
    terrain["cast_shadow"] = False
    print("TERRAIN_DECIMATED", decimate_terrain(terrain, claimed, 0.4), flush=True)
    surfaces = [terrain]
    base = np.array(GROUND_BASE)
    for name, (mask, spacing) in cells.items():
        rows, columns = np.nonzero(mask)
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, columns.min(), columns.max() + 1
        steps = int(round(COARSE / spacing))
        xs = np.linspace(cxs[c0], cxs[c1], (c1 - c0) * steps + 1)
        ys = np.linspace(cys[r0], cys[r1], (r1 - r0) * steps + 1)
        keep = np.repeat(np.repeat(mask[r0:r1, c0:c1], steps, axis=0), steps, axis=1)
        wx, wy = np.meshgrid(xs, ys)
        heights = works.carve(wx, wy, field.sample(wx, wy))
        heights = seam_heights(field, wx, wy, heights, keep)
        lit = 0.85 + 0.15 * sun_shadow(field, wx, wy, heights)
        colours = maps.canopy(maps.colour(wx, wy), xs, ys)
        colours = np.clip(colours * lit[..., None] / base * 0.97, 0, 1)
        patch = grid_mesh(name, xs, ys, heights - DATUM, keep=keep, colours=colours,
                          uv=lambda x, y: np.column_stack([x / GROUND_TILE, y / GROUND_TILE]))
        patch.materials.append(bpy.data.materials["ground"])
        obj = new_object(name, patch, scene.collection, root)
        obj["cast_shadow"] = name == "ground_bridge"
        surfaces.append(obj)
    count = far_field.heights.shape[0]
    fxs = far_field.x0 + FAR_SPACING * np.arange(count)
    fys = far_field.y0 + FAR_SPACING * np.arange(count)
    fgx, fgy = np.meshgrid(fxs, fys)
    texels = 512
    tx, ty = np.meshgrid(np.linspace(fxs[0], fxs[-1], texels), np.linspace(fys[0], fys[-1], texels))
    fine_field = Field(fxs[0], fys[0], (fxs[-1] - fxs[0]) / (texels - 1), far_field.sample(tx, ty))
    shape = tx.shape
    far_colour = classify(tx, ty, fine_field.heights, fine_field.slope(), np.full(shape, 17.0), np.zeros(shape),
                          np.zeros(shape, dtype=bool), ranked(value_noise(shape, 12, 23, 4)),
                          ranked(value_noise(shape, 60, 24, 3)), ranked(value_noise(shape, 200, 25, 2)),
                          ranked(value_noise(shape, 70, 26, 4)), np.ones(shape))
    mist = (0.6 * (1.0 - np.exp(-np.hypot(tx - BRIDGE_ORIGIN.x, ty - BRIDGE_ORIGIN.y) / 4500.0)))[..., None]
    far_colour = far_colour * (1 - mist) + np.array([0.74, 0.78, 0.84]) * mist
    far_image = save_pixels("terrain_far", far_colour, os.path.join(CACHE, "textures", "terrain_far.jpg"), quality=85)
    far_material = baked_material("terrain_far", far_image)
    inside = (fgx > X0 + 15) & (fgx < X0 + SIZE - 15) & (fgy > Y0 + 15) & (fgy < Y0 + SIZE - 15)
    far_heights = np.where(inside, far_field.heights - 30.0, far_field.heights) - DATUM
    keep = ~(inside[:-1, :-1] & inside[1:, 1:] & inside[:-1, 1:] & inside[1:, :-1])
    far_mesh = grid_mesh("terrain_far", fxs, fys, far_heights, keep=keep,
                         uv=lambda x, y: np.column_stack([(x - fxs[0]) / (fxs[-1] - fxs[0]),
                                                          (y - fys[0]) / (fys[-1] - fys[0])]))
    far_mesh.materials.append(far_material)
    far_object = new_object("terrain_far", far_mesh, scene.collection, root)
    far_object["cast_shadow"] = False
    return surfaces


def build_water(scene, maps):
    grown = maps.mask.copy()
    for _ in range(4):
        grown = dilate(grown)
    step = 3
    sub = grown[::step, ::step]
    xs = X0 + SPACING * step * np.arange(sub.shape[1])
    ys = Y0 + SPACING * step * np.arange(sub.shape[0])
    level = maps.level[::step, ::step]
    keep = sub[:-1, :-1] | sub[1:, 1:] | sub[:-1, 1:] | sub[1:, :-1]
    depth = np.clip(level - maps.field.heights[::step, ::step], 0, 4)
    tint = np.clip(depth / 2.5, 0, 1)[..., None]
    colours = np.array([0.5, 0.56, 0.44]) * (1 - tint) + np.array([0.15, 0.25, 0.22]) * tint
    mesh = grid_mesh("river", xs, ys, level - DATUM, keep=keep, colours=colours,
                     uv=lambda x, y: np.column_stack([x / 9.0, y / 9.0]))
    mesh.materials.append(bpy.data.materials["river"])
    obj = new_object("river", mesh, scene.collection, scene.root("terrain"))
    obj["cast_shadow"] = False


def stair_cap(builder, base, outward, levels, offsets, facing, tone):
    profile = []
    for j in range(len(offsets)):
        profile.append((offsets[j], levels[j]))
        profile.append((offsets[j], levels[j + 1]))
    depth = offsets[-1] + 0.4
    profile += [(depth, levels[-1]), (depth, levels[0])]
    points = [(base.x + outward.x * o, base.y + outward.y * o, z) for o, z in profile]
    oriented(builder, points, (facing.x, facing.y, 0.0), material="quarry_face", color=tone)


def riser(builder, p0, p1, z0, top0, top1, inward, tone, along, upper, phase):
    strips = max(1, int(round((p1 - p0).length / 0.6)))
    for k in range(strips):
        a, b = k / strips, (k + 1) / strips
        q0, q1 = p0 + (p1 - p0) * a, p0 + (p1 - p0) * b
        s = along + (p1 - p0).length * (a + b) / 2
        streak = max(0.0, math.sin(s * 2.9 + phase) * math.sin(s * 1.13 + phase * 0.7))
        shade = 1.0 - 0.28 * streak * upper - 0.05 * math.sin(s * 0.7 + phase)
        oriented(builder, [(q0.x, q0.y, z0), (q1.x, q1.y, z0), (q1.x, q1.y, top0 + (top1 - top0) * b),
                           (q0.x, q0.y, top0 + (top1 - top0) * a)], inward, material="quarry_face",
                 color=tuple(c * shade for c in tone))


def quarry_faces(scene, ground, rng, frames):
    builder = MeshBuilder()
    centre = Vector(QUARRY_CENTRE)
    floor = QUARRY_FLOOR - DATUM + 0.5
    warm = (1.0, 0.94, 0.86)
    ledges = 0
    for index in range(len(QUARRY_FRONT) - 1):
        a = Vector(QUARRY_PIT[QUARRY_FRONT[index]])
        b = Vector(QUARRY_PIT[QUARRY_FRONT[index + 1]])
        length = (b - a).length
        steps = max(2, int(length / 2.4))
        direction = (b - a).normalized()
        outward = Vector((-direction.y, direction.x))
        if outward.dot((a + b) / 2 - centre) < 0:
            outward = -outward
        inward = (-outward.x, -outward.y, 0.0)
        bases = [a + direction * (length * k / steps) + outward * 1.2 for k in range(steps + 1)]
        raw = [ground.height(*(p + outward * 6.5)) + 0.15 for p in bases]
        shared = [floor]
        cursor = floor + 0.9
        while cursor < max(raw) - 0.3:
            shared.append(cursor)
            cursor += float(rng.uniform(0.7, 1.6))
        offsets = []
        depth = 0.0
        for j in range(len(shared)):
            depth += float(rng.uniform(0.2, 0.9)) if j else float(rng.uniform(0.0, 0.3))
            offsets.append(depth)
        phase = float(rng.uniform(0, 6.28))
        tone = tuple(c * (0.95 + 0.05 * (index % 3)) for c in warm)
        counts = [max(1, sum(1 for level in shared if level < min(raw[k], raw[k + 1]) - 0.3)) for k in range(steps)]
        for k in range(steps):
            p0, p1 = bases[k], bases[k + 1]
            count = counts[k]
            along = length * k / steps
            for j in range(count):
                o = outward * offsets[j]
                if j < count - 1:
                    z1 = shared[j + 1]
                    upper = 1.0 if min(raw[k], raw[k + 1]) - z1 < 2.2 else 0.35
                    riser(builder, p0 + o, p1 + o, shared[j], z1, z1, inward, tone, along, upper, phase)
                    r0, r1 = p0 + outward * offsets[j + 1], p1 + outward * offsets[j + 1]
                    q0, q1 = p0 + o, p1 + o
                    oriented(builder, [(q0.x, q0.y, z1), (q1.x, q1.y, z1), (r1.x, r1.y, z1), (r0.x, r0.y, z1)],
                             (0, 0, 1), material="quarry_face", color=tuple(c * 0.9 for c in tone))
                    if offsets[j + 1] - offsets[j] > 0.45 and rng.random() < 0.3:
                        spot = (q0 + q1 + r0 + r1) / 4
                        roll = rng.random()
                        key = "box_shrub" if roll < 0.45 else ("fig" if roll < 0.6 else "tuft")
                        size = float(rng.uniform(0.5, 0.8)) if key != "tuft" else float(rng.uniform(1.0, 1.8))
                        frames[key].append((spot.x, spot.y, float(rng.uniform(0, 6.28)), size, 0.02, 0.05))
                        ledges += 1
                else:
                    riser(builder, p0 + o, p1 + o, shared[j], raw[k], raw[k + 1], inward, tone, along, 1.0, phase)
            for end_index, base, facing, neighbour in ((k, p0, -direction, counts[k - 1] if k > 0 else None),
                                                       (k + 1, p1, direction,
                                                        counts[k + 1] if k < steps - 1 else None)):
                if neighbour is not None and neighbour <= count:
                    continue
                levels = shared[:count] + [raw[end_index]]
                stair_cap(builder, base, outward, levels, offsets[:count], facing, tuple(c * 0.62 for c in tone))
    mesh = builder.to_mesh("quarry_faces", scene.tiles, ground_occlusion=False)
    obj = new_object("quarry_faces", mesh, scene.collection, scene.root("quarry"))
    obj["cast_shadow"] = True
    return obj, ledges


def bridge_ground(ground, layout, works):
    us = np.arange(min(p.x for p in works.points) - 40.0, layout.tier3_end + 30.0, 1.0)
    ws = np.arange(min(p.y for p in works.points) - 40.0, 12.01, 1.0)
    heights = np.array([[ground.height(*from_bridge(u, w)) for u in us] for w in ws])
    local = Field(us[0], ws[0], 1.0, heights)

    def footprint(u0, u1):
        samples_u = np.linspace(u0, u1, 5)
        samples_w = np.array([-3.4, -1.6, 0.0, 1.6, 3.4])
        gu, gw = np.meshgrid(samples_u, samples_w)
        return float(np.min(local.sample(gu, gw)))
    return footprint, local.sample


def find_tier3_end(field, layout):
    t3 = layout.tops[2] + DATUM
    for u in np.arange(layout.tier2_end, layout.tier2_end + 140.0, 1.0):
        if field.sample(*from_bridge(u, 0.0)) >= t3 - 1.0:
            return float(u) + 2.0
    return layout.tier2_end + 40.0


def build_bridge_object(scene, layout, ground, rects, works):
    footprint, local_ground = bridge_ground(ground, layout, works)
    builder, arches, info = build_bridge(layout, footprint, local_ground, rects, works.centre, works.discharge,
                                         gap_at=SLAB_GAP)
    info["gap"] = info.get("gap", (SLAB_GAP - 1.25, SLAB_GAP + 1.25))
    print("BRIDGE_PARTS", builder.triangle_count(), flush=True)
    mesh = builder.to_mesh("pont_du_gard", scene.tiles, ground_occlusion=False)
    weathering(mesh, layout, local_ground)
    obj = new_object("pont_du_gard", mesh, scene.collection, scene.root("bridge"), BRIDGE_MATRIX)
    obj["cast_shadow"] = True
    return arches, info, builder.triangle_count()


def tier1_openings(layout):
    return [(centre, span / 2) for centre, span in layout.centres(0)]


def blocked_by_bridge(layout, u, w, margin):
    if not (layout.tier3_start - margin < u < layout.tier3_end + margin and abs(w) < 4.5 + margin):
        return False
    return True


class Scatter:
    def __init__(self, maps, layout, works, corridors, routes):
        self.maps = maps
        self.layout = layout
        self.works = works
        self.corridors = corridors
        self.tracks = list(routes.values())

    def route_distance(self, x, y):
        return min(point_distance(track, x, y) for track in self.tracks)

    def free(self, x, y, margin, tree=True, clearance=None):
        if not (X0 + 20 < x < X0 + SIZE - 20 and Y0 + 20 < y < Y0 + SIZE - 20):
            return False
        u, w = to_bridge(x, y)
        if blocked_by_bridge(self.layout, float(u), float(w), margin):
            return False
        if self.works.blocked(x, y, margin):
            return False
        if self.maps.at("mask", x, y) > 0.2:
            return False
        if tree and self.maps.at("quarry", x, y) > 0.2:
            return False
        if math.hypot(x - FARM[0], y - FARM[1]) < 45.0:
            return False
        limit = clearance if clearance is not None else (3.5 if tree else 2.5)
        if self.route_distance(x, y) < limit:
            return False
        point = np.array([x]), np.array([y])
        for (ax, ay), (bx, by), width in self.corridors:
            if tree and float(polyline_distance([(ax, ay), (bx, by)], *point)[0]) < width:
                return False
        return True

    def above_water(self, x, y):
        return float(self.maps.field.sample(x, y)) - self.maps.water(x, y)


TREE_RADIUS = {"holm_oak_a": 2.0, "holm_oak_b": 2.7, "holm_oak_c": 2.1, "holm_oak_d": 2.8, "pine_a": 2.6,
               "pine_b": 3.1, "willow": 2.6, "poplar": 4.0, "olive": 1.8, "fig": 1.9, "holm_oak_hero": 2.4}


def choose_vegetation(maps, layout, works, corridors, routes, rng):
    scatter = Scatter(maps, layout, works, corridors, routes)
    keys = list(pont_life.vegetation_builds())
    frames = {key: [] for key in keys}
    slope_field = maps.fields["slope"]

    def add(key, x, y, radius, sink, scale):
        frames[key].append((x, y, float(rng.uniform(0, 2 * math.pi)), scale, radius, sink))

    def near_works(x, y):
        return (math.hypot(x - BRIDGE_ORIGIN.x, y - BRIDGE_ORIGIN.y) < 270.0
                or math.hypot(x - 300.0, y - 690.0) < 120.0
                or math.hypot(x - works.world_centre.x, y - works.world_centre.y) < 90.0)

    def edge_fade(x, y):
        edge = min(x - X0, X0 + SIZE - x, y - Y0, Y0 + SIZE - y)
        return min(1.0, max(0.0, (edge - 20.0) / 100.0))

    def oak_site(x, y):
        slope = float(slope_field.sample(x, y))
        if slope > 1.15 or (slope > 0.75 and rng.random() < 0.5) or rng.random() > edge_fade(x, y):
            return False
        return scatter.above_water(x, y) >= 3.0 and scatter.free(x, y, 8.0)

    counts = {"near": 0, "far": 0}
    targets = {"near": 520, "far": 470}
    attempts = 0
    while (counts["near"] < targets["near"] or counts["far"] < targets["far"]) and attempts < 20000:
        attempts += 1
        cx, cy = float(rng.uniform(X0, X0 + SIZE)), float(rng.uniform(Y0, Y0 + SIZE))
        zone = "near" if near_works(cx, cy) else "far"
        if counts[zone] >= targets[zone] or float(maps.at("maquis", cx, cy)) < 0.45:
            continue
        if not oak_site(cx, cy):
            continue
        spread = float(rng.uniform(6.0, 15.0))
        for _ in range(int(rng.integers(4, 13))):
            x, y = cx + float(rng.normal(0, spread / 2)), cy + float(rng.normal(0, spread / 2))
            if not oak_site(x, y):
                continue
            if zone == "near":
                key = "holm_oak_a" if rng.random() < 0.6 else "holm_oak_b"
            else:
                key = "holm_oak_c" if rng.random() < 0.6 else "holm_oak_d"
            add(key, x, y, 0.35, 0.3, float(rng.uniform(0.75, 1.25)))
            counts[zone] += 1
    attempts = 0
    while len(frames["pine_a"]) + len(frames["pine_b"]) < 60 and attempts < 30000:
        attempts += 1
        x, y = float(rng.uniform(X0, X0 + SIZE)), float(rng.uniform(Y0, Y0 + SIZE))
        if float(maps.at("maquis", x, y)) > 0.55 or rng.random() > edge_fade(x, y):
            continue
        if scatter.above_water(x, y) < 6.0 or not scatter.free(x, y, 12.0):
            continue
        add("pine_a" if rng.random() < 0.5 else "pine_b", x, y, 0.4, 0.3, float(rng.uniform(0.8, 1.15)))
    eyes = [Vector(corridor[0]) for corridor in corridors]
    attempts = 0
    shrubs = ("shrub_a", "shrub_b", "box_shrub")
    while sum(len(frames[k]) for k in shrubs) < 450 and attempts < 60000:
        attempts += 1
        x, y = float(rng.uniform(X0, X0 + SIZE)), float(rng.uniform(Y0, Y0 + SIZE))
        if min((Vector((x, y)) - eye).length for eye in eyes) > 300.0 and not near_works(x, y):
            continue
        slope = float(slope_field.sample(x, y))
        if float(maps.at("maquis", x, y)) < 0.3 or scatter.above_water(x, y) < 3.0:
            continue
        if not scatter.free(x, y, 3.0, tree=False):
            continue
        key = shrubs[int(rng.integers(0, 2))] if slope < 0.6 else ("box_shrub" if rng.random() < 0.5 else "shrub_a")
        add(key, x, y, 0.5, 0.15, float(rng.uniform(0.7, 1.4)))
    attempts = 0
    while len(frames["willow"]) + len(frames["poplar"]) < 85 and attempts < 200000:
        attempts += 1
        x, y = float(rng.uniform(X0, X0 + SIZE)), float(rng.uniform(Y0, Y0 + SIZE))
        if maps.at("near_water", x, y) < 0.5:
            continue
        rise = scatter.above_water(x, y)
        if not 0.5 < rise < 6.0:
            continue
        if float(slope_field.sample(x, y)) > 0.9 or not scatter.free(x, y, 14.0):
            continue
        if min((Vector((x, y)) - eye).length for eye in eyes) < 32.0:
            continue
        add("willow" if rng.random() < 0.72 else "poplar", x, y, 0.35, 0.3, float(rng.uniform(0.75, 1.15)))
    attempts = 0
    while len(frames["boulder_a"]) + len(frames["rock_slab"]) < 130 and attempts < 30000:
        attempts += 1
        x, y = from_bridge(float(rng.uniform(-110, 130)), float(rng.uniform(-200, 110)))
        rise = scatter.above_water(x, y)
        if not 0.3 < rise < 5.0 or not scatter.free(x, y, 2.5, tree=False):
            continue
        roll = rng.random()
        if roll < 0.4:
            add("rock_slab", x, y, 0.6, 0.1, float(rng.uniform(1.4, 3.2)))
        else:
            add("boulder_a", x, y, 0.4, 0.12, float(rng.uniform(0.8, 2.4)))
    fx, fy = FARM
    for i in range(-5, 6):
        for j in range(-3, 4):
            add("vine", fx + 34.0 + i * 2.4, fy - 32.0 + j * 2.2, 0.2, 0.08, float(rng.uniform(0.85, 1.1)))
    for i in range(-3, 4):
        for j in range(-2, 3):
            x, y = fx - 36.0 + i * 8.0 + float(rng.uniform(-1, 1)), fy + 22.0 + j * 8.0 + float(rng.uniform(-1, 1))
            add("olive", x, y, 0.3, 0.25, float(rng.uniform(0.8, 1.1)))
    for dx, dy in ((14.0, 12.0), (-12.0, -16.0), (20.0, -8.0)):
        add("fig", fx + dx, fy + dy, 0.3, 0.2, 1.0)
    placed = 0
    for _ in range(3000):
        if placed >= 460:
            break
        x, y = float(rng.uniform(205, 350)), float(rng.uniform(635, 740))
        if not polygon_inside(QUARRY_PIT, np.array([x]), np.array([y]))[0]:
            continue
        if math.hypot(x - TOMBS[0], y - TOMBS[1]) < 11.0 or scatter.route_distance(x, y) < 2.5:
            continue
        roll = rng.random()
        if roll < 0.55:
            key, size = "tuft", float(rng.uniform(1.2, 2.6))
        elif roll < 0.62:
            key, size = "rubble", float(rng.uniform(0.6, 1.0))
        elif roll < 0.95:
            key, size = shrubs[int(rng.integers(0, 3))], float(rng.uniform(0.8, 1.5))
        elif roll < 0.985:
            key, size = "holm_oak_a", float(rng.uniform(0.45, 0.75))
        else:
            key, size = "fig", float(rng.uniform(0.6, 0.9))
        add(key, x, y, 0.4, 0.12, size)
        placed += 1
    maps.trees = [(x, y, TREE_RADIUS[key] * scale) for key, entries in frames.items() if key in TREE_RADIUS
                  for x, y, _, scale, _, _ in entries]
    return frames


def ground_detail(frames, maps, scatter, points, rng):
    for name in GROUND_POIS:
        eye, target = points[name]
        direction = (Vector((target.x, target.y)) - Vector((eye.x, eye.y))).normalized()
        placed = {"tuft": 0, "pebbles": 0, "rock_slab": 0}
        quota = {"tuft": 170, "pebbles": 70, "rock_slab": 18}
        for _ in range(4000):
            if all(placed[k] >= quota[k] for k in quota):
                break
            distance = float(rng.uniform(1.5, 40.0)) ** 1.0
            angle = float(rng.normal(0.0, 0.9))
            offset = Vector((direction.x * math.cos(angle) - direction.y * math.sin(angle),
                             direction.x * math.sin(angle) + direction.y * math.cos(angle))) * distance
            x, y = eye.x + offset.x, eye.y + offset.y
            if scatter.above_water(x, y) < 0.15 or float(maps.at("slope", x, y)) > 1.1:
                continue
            if scatter.route_distance(x, y) < 1.0 or not scatter.free(x, y, 0.5, tree=False, clearance=1.0):
                continue
            kind = ("tuft", "pebbles", "rock_slab")[int(rng.integers(0, 3))]
            if placed[kind] >= quota[kind]:
                continue
            placed[kind] += 1
            if kind == "tuft":
                frames["tuft"].append((x, y, float(rng.uniform(0, 6.28)), float(rng.uniform(0.7, 1.4)), 0.15, 0.03))
            elif kind == "pebbles":
                frames["pebbles"].append((x, y, float(rng.uniform(0, 6.28)), float(rng.uniform(0.8, 1.6)), 0.4, 0.02))
            else:
                frames["rock_slab"].append((x, y, float(rng.uniform(0, 6.28)), float(rng.uniform(0.6, 1.6)), 0.5,
                                            0.12))


SHADOWLESS = ("holm_oak_c", "holm_oak_d", "shrub", "box", "vine", "boulder", "tuft", "pebbles", "rock_slab", "rubble",
              "reed", "broom", "cistus", "rosemary", "kermes", "thyme")


def plant_vegetation(scene, ground, frames):
    builds = pont_life.vegetation_builds()
    counts = {}
    for key, entries in frames.items():
        if not entries:
            continue
        matrices = []
        for x, y, angle, scale, radius, sink in entries:
            low, _ = ground.footprint(x, y, radius * scale, 5)
            matrices.append(placement(x, y, low - sink * scale, angle, scale))
        scene.library.place(key, builds[key], scene.collection, scene.root("vegetation"), matrices,
                            cast_shadow=not key.startswith(SHADOWLESS), ground_occlusion=False)
        if not key.startswith(("boulder", "pebbles", "rock_slab", "rubble", "outcrop")):
            dark = 0.62 if key.startswith("tuft") else 0.5
            pont_life.vertex_shade(scene.library.meshes[key], dark)
        mesh = scene.library.meshes[key]
        counts[key] = [len(entries), sum(len(polygon.vertices) - 2 for polygon in mesh.polygons)]
    return counts


def on_ground(ground, x, y, angle, radius=0.18, lift=0.0):
    low, _ = ground.footprint(x, y, radius, 4)
    return placement(x, y, low + lift, angle)


BODY_LENGTHS = (("goat_kid", 0.45), ("goat", 0.72), ("sheep", 0.8), ("dog", 0.66), ("mule", 1.6), ("donkey", 1.3),
                ("ox_cart", 5.0), ("hand_barrow", 2.0))


def beast(scene, ground, key, x, y, angle):
    length = next(value for prefix, value in BODY_LENGTHS if key.startswith(prefix))
    reach = 0.55 * length
    fx, fy = -math.sin(angle) * reach, math.cos(angle) * reach
    front = ground.height(x + fx, y + fy)
    back = ground.height(x - fx, y - fy)
    pitch = max(-0.21, min(0.21, math.atan2(front - back, 2 * reach)))
    scene.add(key, placement(x, y, (front + back) / 2 - 0.02, angle) @ Matrix.Rotation(pitch, 4, "X"))


def shore_point(maps, u, w, step, limit=120):
    for k in range(limit):
        x, y = from_bridge(u, w + step * k)
        if float(maps.field.sample(x, y)) - maps.water(x, y) > 0.25:
            return x, y, k
    return from_bridge(u, w) + (0,)


def clear_spot(scatter, x, y, clearance, rng, reach=25.0, slope=0.5):
    for attempt in range(200):
        px = x + (float(rng.normal(0, reach / 2)) if attempt else 0.0)
        py = y + (float(rng.normal(0, reach / 2)) if attempt else 0.0)
        if scatter.route_distance(px, py) < clearance or float(scatter.maps.at("slope", px, py)) > slope:
            continue
        if scatter.above_water(px, py) < 1.0 or not scatter.free(px, py, 1.0, tree=False, clearance=clearance):
            continue
        return px, py
    return x, y


def footing_row(scatter):
    for ax, ay, dx, dy in ((188.0, 690.0, 0.0, 1.0), (240.0, 752.0, 1.0, 0.0), (362.0, 700.0, 0.0, 1.0),
                           (300.0, 760.0, 1.0, 0.0), (175.0, 655.0, 0.0, 1.0)):
        sites = [(ax + dx * 6.5 * k, ay + dy * 6.5 * k) for k in range(4)]
        if all(float(scatter.maps.at("slope", x, y)) < 0.3 and scatter.free(x, y, 3.0, tree=False, clearance=4.0)
               and not polygon_inside(QUARRY_PIT, np.array([x]), np.array([y]))[0] for x, y in sites):
            angle = math.atan2(dy, dx)
            return [(x, y, angle) for x, y in sites]
    return []


def place_life(scene, maps, ground, layout, works, info, scatter, points, rng):
    up_river = (-ACROSS.x, -ACROSS.y)
    down_river = (ACROSS.x, ACROSS.y)
    bx, by = from_bridge(-8.0, -75.0)
    water = maps.water(bx, by) - DATUM
    scene.add("boat", placement(bx, by, water - 0.16, heading(down_river) + 0.25))
    scene.add("fig_boatman", placement(bx, by, water - 0.16 + 0.12, heading(down_river) + 0.25)
              @ placement(0.0, -1.8, 0.0, 0.0))
    eye = points["le-pont"][0]
    for k in range(1, 80):
        tx, ty = eye.x + (points["le-pont"][1].x - eye.x) * k / 100, eye.y + (points["le-pont"][1].y - eye.y) * k / 100
        if maps.water(tx, ty) - float(maps.field.sample(tx, ty)) > 0.9:
            level = maps.water(tx, ty) - DATUM
            angle = heading(up_river) + 0.6
            scene.add("boat", placement(tx, ty, level - 0.16, angle))
            scene.add("fig_boatman", placement(tx, ty, level - 0.04, angle) @ placement(0.0, 1.6, 0.0, math.pi))
            break
    fx, fy, _ = shore_point(maps, 32.0, -60.0, 1.0)
    fx, fy = clear_spot(scatter, fx, fy, 3.0, rng, 8.0, 0.8)
    scene.add("fig_fisher", on_ground(ground, fx, fy, heading(up_river) - 0.5))
    scene.add("basket", on_ground(ground, fx + 0.8, fy - 0.6, 0.0))
    mx, my, _ = shore_point(maps, 24.0, -30.0, 1.0)
    water = maps.water(mx, my) - DATUM
    scene.add("boat", placement(mx - ACROSS.x * 1.5 - AXIS.x * 2.5, my - ACROSS.y * 1.5 - AXIS.y * 2.5, water - 0.16,
                                heading(up_river) + 1.2))
    hx, hy = clear_spot(scatter, *from_bridge(164.0, -125.0), 18.0, rng, 40.0, 0.45)
    for _ in range(18):
        x, y = hx + float(rng.normal(0, 8)), hy + float(rng.normal(0, 8))
        if scatter.route_distance(x, y) < 3.0:
            continue
        beast(scene, ground, "goat_dark" if rng.random() < 0.6 else "goat_light", x, y, float(rng.uniform(0, 6.28)))
    for _ in range(6):
        x, y = hx + float(rng.normal(0, 6)), hy + float(rng.normal(0, 6))
        if scatter.route_distance(x, y) < 3.0:
            continue
        beast(scene, ground, "sheep", x, y, float(rng.uniform(0, 6.28)))
    scene.add("fig_shepherd", on_ground(ground, hx + 9.0, hy + 4.0, 2.0))
    beast(scene, ground, "dog", hx + 11.0, hy + 2.0, 1.4)
    cx, cy = clear_spot(scatter, *from_bridge(190.0, -62.0), 8.0, rng, 20.0, 0.4)
    scene.add("campfire", on_ground(ground, cx, cy, 0.0, 0.5, -0.05))
    scene.add("fig_shepherd", on_ground(ground, cx + 1.4, cy + 0.6, heading((-1.4, -0.6))))
    smokes = [Vector((cx, cy, ground.height(cx, cy) + 0.4))]
    keeper = info["keeper"]
    scene.add("fig_keeper", BRIDGE_MATRIX @ Matrix.Translation(keeper) @ Matrix.Rotation(info["keeper_angle"], 4, "Z"))
    top = layout.tops[2]
    gap0, gap1 = info["gap"]
    scene.add("fig_kneeler", BRIDGE_MATRIX @ placement((gap0 + gap1) / 2, 1.1, top - SLAB_THICKNESS + 0.01, math.pi))
    for local, angle, key in (((gap0 - 3.6, 0.75), -math.pi / 2, "fig_mason"),
                              ((gap1 + 1.3, 1.15), 0.0, "basket")):
        scene.add(key, BRIDGE_MATRIX @ placement(local[0], local[1], top + 0.01, angle))
    track = TRACKS["domaine"]
    a, b = Vector(track[0]), Vector(track[1])
    direction = (b - a).normalized()
    side = Vector((-direction.y, direction.x))
    for k in range(4):
        p = a + direction * (16.0 + k * 3.6)
        beast(scene, ground, "mule_packed" if k < 3 else "mule_bare", p.x, p.y, heading(direction))
    lead = a + direction * (16.0 + 3.6 * 3 + 1.5) + side * 1.1
    scene.add("fig_muleteer", on_ground(ground, lead.x, lead.y, heading(direction)))
    drover = a + direction * 14.0 + side * 1.0
    scene.add("fig_drover", on_ground(ground, drover.x, drover.y, heading(direction)))
    cart = a + direction * 48.0
    beast(scene, ground, "ox_cart", cart.x, cart.y, heading(direction))
    fx, fy = FARM
    scene.add("farmhouse", on_ground(ground, fx, fy, 0.5, 6.0, -0.3))
    kx, ky = fx + 22.0, fy - 8.0
    scene.add("kiln", on_ground(ground, kx, ky, 0.5, 1.6, -0.2))
    scene.add("amphora_stack", on_ground(ground, kx + 4.0, ky + 3.0, 0.3, 1.0))
    smokes.append(Vector((kx, ky, ground.height(kx, ky) + 2.9)))
    smokes.append(Vector((fx + 3.0, fy, ground.height(fx, fy) + 5.6)))
    for key, dx, dy, angle in (("fig_woman", 6.0, -6.0, 2.5), ("fig_child", 7.5, -5.0, 2.0),
                               ("fig_mason", 19.0, -4.0, 4.0)):
        scene.add(key, on_ground(ground, fx + dx, fy + dy, angle))
    beast(scene, ground, "dog", fx + 4.0, fy - 9.0, 1.0)
    tombs = [("tomb_ring", 0), ("tomb_amphora", 1), ("tomb_tiles", 2)]
    tx, ty = TOMBS
    placed = 0
    for _ in range(200):
        if placed >= 13:
            break
        x, y = tx + float(rng.uniform(-9, 9)), ty + float(rng.uniform(-6, 6))
        if scatter.route_distance(x, y) < 2.5:
            continue
        key = tombs[placed % 3][0]
        scene.add(key, on_ground(ground, x, y, float(rng.uniform(-0.3, 0.3)) + 0.4, 0.3, -0.05))
        placed += 1
    for key, dx, dy, angle in (("fig_woman", -4.0, -7.0, 0.6), ("fig_child", -5.2, -7.6, 0.4)):
        x, y = clear_spot(scatter, tx + dx, ty + dy, 2.5, rng, 6.0, 0.6)
        scene.add(key, on_ground(ground, x, y, angle))
    for x, y, angle in ((236.0, 700.0, 0.4), (250.0, 718.0, 0.2), (262.0, 724.0, 0.1), (226.0, 676.0, 1.4),
                        (334.0, 708.0, 1.2), (330.0, 692.0, 0.3), (322.0, 712.0, 2.0), (318.0, 700.0, 0.9)):
        if scatter.route_distance(x, y) > 3.0:
            scene.add("quarry_block", on_ground(ground, x, y, angle, 1.0, -0.15))
    for index, (x, y, angle) in enumerate(footing_row(scatter)):
        scene.add("house_footing_a" if index % 2 == 0 else "house_footing_b",
                  on_ground(ground, x, y, angle, 2.0, 0.0))
    return smokes


def enrich_vegetation(frames, maps, scatter, points, rng):
    for key in ("reed", "broom", "cistus", "rosemary", "outcrop_a", "outcrop_b", "holm_oak_hero"):
        frames.setdefault(key, [])
    eyes = [Vector((points[name][0].x, points[name][0].y)) for name in GROUND_POIS]
    for key in ("holm_oak_a", "holm_oak_b"):
        kept = []
        for entry in frames[key]:
            if min((Vector(entry[:2]) - eye).length for eye in eyes) < 55.0:
                frames["holm_oak_hero"].append(entry)
            else:
                kept.append(entry)
        frames[key] = kept
    slope_field = maps.fields["slope"]

    def near_bridge(x, y, reach):
        return math.hypot(x - BRIDGE_ORIGIN.x, y - BRIDGE_ORIGIN.y) < reach

    def near_eye(x, y, reach):
        return min((Vector((x, y)) - eye).length for eye in eyes) < reach

    def add(key, x, y, radius, sink, scale):
        frames[key].append((x, y, float(rng.uniform(0, 2 * math.pi)), scale, radius, sink))

    quotas = {"outcrop": 90, "box": 130, "reed": 140, "flower": 190}
    for key in ("kermes", "thyme"):
        frames.setdefault(key, [])
    placed = {key: 0 for key in quotas}
    for _ in range(120000):
        if all(placed[key] >= quotas[key] for key in quotas):
            break
        x, y = float(rng.uniform(X0 + 30, X0 + SIZE - 30)), float(rng.uniform(Y0 + 30, Y0 + SIZE - 30))
        slope = float(slope_field.sample(x, y))
        rise = scatter.above_water(x, y)
        if placed["outcrop"] < quotas["outcrop"] and slope > 0.7 and rise > 2.0 and near_bridge(x, y, 520.0):
            if scatter.free(x, y, 3.0, tree=False):
                add("outcrop_a" if rng.random() < 0.6 else "outcrop_b", x, y, 0.7, 0.3, float(rng.uniform(0.7, 1.3)))
                placed["outcrop"] += 1
            continue
        if placed["box"] < quotas["box"] and slope > 0.6 and rise > 3.0 and near_bridge(x, y, 450.0):
            if scatter.free(x, y, 2.0, tree=False):
                add("box_shrub", x, y, 0.5, 0.15, float(rng.uniform(0.8, 1.5)))
                placed["box"] += 1
            continue
        if (placed["reed"] < quotas["reed"] and 0.05 < rise < 1.1 and maps.at("near_water", x, y) > 0.5
                and (near_bridge(x, y, 420.0) or near_eye(x, y, 120.0))):
            if scatter.free(x, y, 1.0, tree=False, clearance=1.5):
                cluster = int(rng.integers(1, 4))
                for _ in range(cluster):
                    px, py = x + float(rng.normal(0, 1.2)), y + float(rng.normal(0, 1.2))
                    if 0.0 < scatter.above_water(px, py) < 1.3:
                        add("reed", px, py, 0.3, 0.05, float(rng.uniform(0.75, 1.25)))
                        placed["reed"] += 1
            continue
        if (placed["flower"] < quotas["flower"] and 0.12 < slope < 0.9 and rise > 3.0
                and float(maps.at("maquis", x, y)) > 0.3 and (near_bridge(x, y, 360.0) or near_eye(x, y, 140.0))):
            if scatter.free(x, y, 2.0, tree=False):
                roll = rng.random()
                key = "broom" if roll < 0.2 else ("cistus" if roll < 0.55 else "rosemary")
                add(key, x, y, 0.4, 0.08, float(rng.uniform(0.8, 1.25)))
                placed["flower"] += 1
    for name in GROUND_POIS:
        eye, target = points[name]
        direction = (Vector((target.x, target.y)) - Vector((eye.x, eye.y))).normalized()
        count = 0
        for _ in range(600):
            if count >= 14:
                break
            distance = float(rng.uniform(5.0, 35.0))
            angle = float(rng.normal(0.0, 0.7))
            offset = Vector((direction.x * math.cos(angle) - direction.y * math.sin(angle),
                             direction.x * math.sin(angle) + direction.y * math.cos(angle))) * distance
            x, y = eye.x + offset.x, eye.y + offset.y
            if scatter.above_water(x, y) < 3.0 or not 0.25 < float(maps.at("slope", x, y)) < 0.9:
                continue
            if not scatter.free(x, y, 1.0, tree=False, clearance=1.8) or maps.at("quarry", x, y) > 0.2:
                continue
            add("cistus" if count % 2 else "rosemary", x, y, 0.4, 0.08, float(rng.uniform(0.7, 1.1)))
            count += 1
    placed = {"kermes": 0, "willow": 0, "rubble": 0}
    for _ in range(60000):
        if placed["kermes"] >= 2000:
            break
        eye = eyes[int(rng.integers(0, len(eyes)))]
        angle, distance = float(rng.uniform(0, 2 * math.pi)), float(rng.uniform(4.0, 150.0))
        x, y = eye.x + distance * math.cos(angle), eye.y + distance * math.sin(angle)
        if scatter.above_water(x, y) < 3.0 or float(slope_field.sample(x, y)) > 1.1:
            continue
        if float(maps.at("mottle", x, y)) < 0.42 or (maps.at("quarry", x, y) > 0.5 and rng.random() < 0.6):
            continue
        if not scatter.free(x, y, 0.8, tree=False, clearance=1.5):
            continue
        add("kermes" if rng.random() < 0.65 else "thyme", x, y, 0.3, 0.12, float(rng.uniform(0.6, 1.6)))
        placed["kermes"] += 1
    for _ in range(8000):
        if placed["willow"] >= 45:
            break
        eye = eyes[int(rng.integers(0, len(eyes)))]
        angle, distance = float(rng.uniform(0, 2 * math.pi)), float(rng.uniform(15.0, 120.0))
        x, y = eye.x + distance * math.cos(angle), eye.y + distance * math.sin(angle)
        if not 0.3 < scatter.above_water(x, y) < 2.5 or maps.at("near_water", x, y) < 0.5:
            continue
        if not scatter.free(x, y, 1.5):
            continue
        add("willow", x, y, 0.3, 0.2, float(rng.uniform(0.3, 0.5)))
        placed["willow"] += 1
    for _ in range(3000):
        if placed["rubble"] >= 150:
            break
        fraction = float(rng.uniform(0.02, 0.98))
        if any(a - 0.02 < fraction < b + 0.02 for a, b in DIKE_BREACHES):
            continue
        p, q = Vector(dike_point(fraction - 0.01)), Vector(dike_point(fraction + 0.01))
        side = (q - p).normalized()
        spot = (p + q) / 2 + Vector((-side.y, side.x)) * float(rng.normal(0.0, 2.6))
        if scatter.route_distance(spot.x, spot.y) < 1.5:
            continue
        if rng.random() < 0.6:
            add("rubble", spot.x, spot.y, 0.5, 0.12, float(rng.uniform(0.5, 1.0)))
        else:
            add("boulder_a", spot.x, spot.y, 0.4, 0.15, float(rng.uniform(0.4, 1.0)))
        placed["rubble"] += 1


def view_spot(points, name, distance, lateral):
    eye, target = points[name]
    forward = (Vector((target.x, target.y)) - Vector((eye.x, eye.y))).normalized()
    right = Vector((forward.y, -forward.x))
    spot = Vector((eye.x, eye.y)) + forward * distance + right * lateral
    return spot.x, spot.y


def waterside(maps, scatter, x, y, reach, rng, low=0.15, high=0.7, steep=0.4):
    best = None
    for _ in range(800):
        px, py = x + float(rng.uniform(-reach, reach)), y + float(rng.uniform(-reach, reach))
        rise = scatter.above_water(px, py)
        if not low < rise < high or float(maps.at("slope", px, py)) > steep:
            continue
        if not scatter.free(px, py, 0.8, tree=False, clearance=2.0):
            continue
        distance = math.hypot(px - x, py - y)
        if best is None or distance < best[0]:
            best = (distance, px, py)
    if best is None:
        return None
    _, px, py = best
    angles = [2 * math.pi * k / 24 for k in range(24)]
    lowest = min(angles, key=lambda a: float(maps.field.sample(px + 3.0 * math.cos(a), py + 3.0 * math.sin(a))))
    return px, py, (math.cos(lowest), math.sin(lowest))


def circle(scene, ground, x, y, keys, radius, rng):
    for index, key in enumerate(keys):
        angle = 2 * math.pi * index / len(keys) + float(rng.uniform(-0.3, 0.3))
        px, py = x + radius * math.cos(angle), y + radius * math.sin(angle)
        scene.add(key, on_ground(ground, px, py, heading((x - px, y - py)) + float(rng.uniform(-0.25, 0.25))))


def place_scenes(scene, maps, ground, layout, works, info, scatter, points, rng):
    smokes = []
    tx, ty = clear_spot(scatter, *view_spot(points, "le-pont", 24.0, 10.0), 3.0, rng, 8.0, 0.4)
    scene.add("campfire", on_ground(ground, tx, ty, 0.0, 0.5, -0.05))
    circle(scene, ground, tx, ty, ["fig_talker_a", "fig_talker_b", "fig_porter", "fig_talker_c"], 1.7, rng)
    scene.add("firewood", on_ground(ground, tx + 2.6, ty - 1.4, 0.7, 0.6))
    beast(scene, ground, "donkey", tx - 3.2, ty + 2.4, 2.2)
    smokes.append(Vector((tx, ty, ground.height(tx, ty) + 0.4)))
    drink = (waterside(maps, scatter, *view_spot(points, "le-pont", 26.0, -6.0), 14.0, rng, steep=0.2)
             or waterside(maps, scatter, *view_spot(points, "le-pont", 26.0, -6.0), 24.0, rng, steep=0.3)
             or waterside(maps, scatter, *view_spot(points, "le-pont", 26.0, -6.0), 14.0, rng))
    if drink is not None:
        dx, dy, (wx, wy) = drink
        across = Vector((-wy, wx))
        for k, key in enumerate(("mule_packed", "mule_bare", "mule_packed")):
            p = Vector((dx, dy)) + across * (k - 1) * 1.6 - Vector((wx, wy)) * (0.8 + 0.4 * (k % 2))
            beast(scene, ground, key, p.x, p.y, heading((wx, wy)) + float(rng.uniform(-0.3, 0.3)))
        lead = Vector((dx, dy)) + across * 2.8 - Vector((wx, wy)) * 1.8
        scene.add("fig_muleteer", on_ground(ground, lead.x, lead.y, heading((wx, wy)) - 0.8))
    wash = (waterside(maps, scatter, *view_spot(points, "la-grande-arche", 14.0, -6.0), 8.0, rng, steep=0.25)
            or waterside(maps, scatter, *view_spot(points, "la-grande-arche", 10.0, -4.0), 22.0, rng))
    if wash is not None:
        wx0, wy0, (wx, wy) = wash
        across = Vector((-wy, wx))
        for k in range(2):
            p = Vector((wx0, wy0)) + across * (k * 1.4 - 0.7)
            angle = heading((wx, wy)) + float(rng.uniform(-0.3, 0.3))
            scene.add("fig_washer", on_ground(ground, p.x, p.y, angle))
            stone = p + Vector((wx, wy)) * 0.75
            scene.add("wash_stone", placement(stone.x, stone.y, ground.height(stone.x, stone.y) - 0.04, angle, 0.7))
        spread = Vector((wx0, wy0)) - Vector((wx, wy)) * 3.0 + across * 1.2
        scene.add("laundry", on_ground(ground, spread.x, spread.y, heading(across), 0.8))
        girl = Vector((wx0, wy0)) - Vector((wx, wy)) * 2.4 - across * 2.0
        scene.add("fig_girl", on_ground(ground, girl.x, girl.y, heading((wx, wy)) + 0.9))
    net = (waterside(maps, scatter, *view_spot(points, "la-grande-arche", 12.0, 18.0), 8.0, rng)
           or waterside(maps, scatter, *view_spot(points, "la-grande-arche", 12.0, 18.0), 25.0, rng))
    if net is not None:
        nx, ny, (wx, wy) = net
        scene.add("fig_netter", on_ground(ground, nx, ny, heading((wx, wy))))
        rack = Vector((nx, ny)) - Vector((wx, wy)) * 1.5 + Vector((wy, -wx)) * 3.5
        scene.add("net_rack", on_ground(ground, rack.x, rack.y, heading((wy, -wx)), 1.3))
        trap = Vector((nx, ny)) - Vector((wx, wy)) * 1.5 + Vector((-wy, wx)) * 1.8
        scene.add("fish_trap", on_ground(ground, trap.x, trap.y, heading((wx, wy)) + 0.6, 0.5))
    hx, hy = clear_spot(scatter, *from_bridge(164.0, -125.0), 18.0, rng, 40.0, 0.45)
    for _ in range(7):
        x, y = hx + float(rng.normal(0, 7)), hy + float(rng.normal(0, 7))
        if scatter.route_distance(x, y) > 3.0 and scatter.above_water(x, y) > 1.0:
            beast(scene, ground, "goat_kid", x, y, float(rng.uniform(0, 6.28)))
    fx, fy = FARM
    for k in range(9):
        x, y = fx + float(rng.uniform(-9, 9)), fy - 6.0 + float(rng.uniform(-5, 4))
        if math.hypot(x - fx, y - fy) > 7.5:
            scene.add("hen" if k % 3 else "hen_white", on_ground(ground, x, y, float(rng.uniform(0, 6.28)), 0.15))
    cx, cy = clear_spot(scatter, fx + 4.0, fy - 16.0, 2.5, rng, 6.0, 0.4)
    scene.add("fig_child_hoop", on_ground(ground, cx, cy, 0.9))
    scene.add("fig_child_run", on_ground(ground, cx - 2.2, cy - 1.1, 1.1))
    sx, sy = clear_spot(scatter, fx + 13.0, fy - 12.0, 2.5, rng, 6.0, 0.4)
    scene.add("peddler_goods", on_ground(ground, sx, sy, 0.4, 0.8))
    scene.add("fig_seller", on_ground(ground, sx + 0.4, sy + 1.2, heading((-0.4, -1.2))))
    scene.add("fig_girl", on_ground(ground, sx - 1.0, sy - 1.3, heading((1.0, 1.3))))
    beast(scene, ground, "donkey", sx + 2.4, sy + 0.6, 0.3)
    scene.add("firewood", on_ground(ground, fx - 7.5, fy - 5.0, 0.1, 0.6))
    for fraction, crew in ((0.73, ("fig_digger", "fig_digger", "fig_porter")), (0.36, ("fig_digger",))):
        bx, by = dike_point(fraction)
        inward = Vector((QUARRY_CENTRE[0] - bx, QUARRY_CENTRE[1] - by)).normalized()
        along = Vector((-inward.y, inward.x))
        base = Vector((bx, by)) + inward * 3.0
        for k, key in enumerate(crew):
            p = base + along * (k - 1) * 1.9 + inward * float(rng.uniform(-0.6, 0.6))
            scene.add(key, on_ground(ground, p.x, p.y, heading(-inward) + float(rng.uniform(-0.6, 0.6))))
        for offset, depth, key, angle in ((-1.8, 2.5, "sherd_pile", 0.3), (0.2, -0.6, "hand_barrow", heading(inward)),
                                          (1.0, 1.5, "stone_basket", 0.0), (-1.0, 1.4, "stone_basket", 1.0),
                                          (1.6, 0.6, "tools", 0.6)):
            p = base + along * offset + inward * depth
            if key == "hand_barrow":
                beast(scene, ground, key, p.x, p.y, angle)
            else:
                scene.add(key, on_ground(ground, p.x, p.y, angle, 0.5))
    bx, by = dike_point(0.18)
    outward = Vector((bx - QUARRY_CENTRE[0], by - QUARRY_CENTRE[1])).normalized()
    hx, hy = clear_spot(scatter, *(Vector((bx, by)) + outward * 14.0), 4.0, rng, 10.0, 0.3)
    scene.add("hut", on_ground(ground, hx, hy, heading(-outward), 2.6, 0.0))
    scene.add("firewood", on_ground(ground, hx + 3.2, hy + 0.8, 0.4, 0.6))
    top = layout.tops[2]
    gap1 = info["gap"][1]
    for local, angle, key in (((gap1 + 0.7, 0.9), math.pi / 2, "fig_digger"),
                              ((gap1 + 2.0, -0.85), 0.3, "tools"),
                              ((gap1 + 1.0, -0.95), 0.0, "stone_basket")):
        scene.add(key, BRIDGE_MATRIX @ placement(local[0], local[1], top + 0.01, angle))
    centre = works.world_centre
    px, py = clear_spot(scatter, *view_spot(points, "le-bassin", 10.0, 6.5), 2.5, rng, 3.0, 0.5)
    scene.add("fig_porter", on_ground(ground, px, py, heading((centre.x - px, centre.y - py))))
    beast(scene, ground, "donkey", px + 1.6, py - 1.4, heading((centre.x - px, centre.y - py)) + 0.5)
    scene.add("stone_basket", on_ground(ground, px - 1.0, py + 0.9, 0.0, 0.4))
    beast(scene, ground, "dog", px - 1.8, py - 1.0, 2.4)
    gx, gy = clear_spot(scatter, *view_spot(points, "le-bassin", 16.0, -7.0), 2.5, rng, 3.0, 0.5)
    circle(scene, ground, gx, gy, ["fig_talker_c", "fig_mason"], 0.7, rng)
    gx, gy = view_spot(points, "la-carriere", 26.0, 5.0)
    grazing = 0
    for _ in range(80):
        if grazing >= 8:
            break
        x, y = gx + float(rng.normal(0, 5)), gy + float(rng.normal(0, 5))
        if maps.at("quarry", x, y) < 0.5 or scatter.route_distance(x, y) < 2.0:
            continue
        key = ("goat_dark", "goat_light", "goat_kid")[grazing % 3]
        beast(scene, ground, key, x, y, float(rng.uniform(0, 6.28)))
        grazing += 1
    mx, my = TOMBS
    gx, gy = clear_spot(scatter, mx - 6.0, my - 4.0, 2.5, rng, 4.0, 0.6)
    circle(scene, ground, gx, gy, ["fig_talker_c", "fig_seller", "fig_child"], 0.9, rng)
    return smokes


def refine(ground, points, tolerance=0.06):
    result = [points[0]]
    for q in points[1:]:
        stack = [q]
        while stack:
            target = stack[-1]
            start = result[-1]
            middle = (start + target) / 2
            error = abs(ground.height(middle.x, middle.y)
                        - (ground.height(start.x, start.y) + ground.height(target.x, target.y)) / 2)
            if error > tolerance and (target - start).length > 0.4:
                stack.append(middle)
            else:
                result.append(stack.pop())
    return result


def waypoint(kind, a, b, works):
    if kind == "b":
        return Vector(from_bridge(a, b))
    if kind == "w":
        return Vector((a, b))
    points = works.points
    index = min(int(round(a * (len(points) - 1))), len(points) - 1)
    following = points[min(index + 1, len(points) - 1)]
    previous = points[max(index - 1, 0)]
    tangent = (following - previous).normalized()
    normal = Vector((-tangent.y, tangent.x))
    if normal.y < 0:
        normal = -normal
    p = points[index] + normal * b
    return Vector(from_bridge(p.x, p.y))


def walk_mask(maps, layout, works):
    field = maps.field
    u, w = to_bridge(field.grid_x, field.grid_y)
    blocked = (np.abs(w) < 8.0) & (u > layout.tier3_start - 3.0) & (u < layout.tier3_end + 3.0)
    for centre, half in tier1_openings(layout):
        blocked &= ~((np.abs(u - centre) < half - 1.4) & (np.abs(w) < 8.0))
    near_line = np.minimum(polyline_distance(works.line, field.grid_x, field.grid_y),
                           polyline_distance(works.stub, field.grid_x, field.grid_y)) < 4.0
    channel = polyline_distance(works.channel, field.grid_x, field.grid_y) < 2.2
    basin = works.outside(field.grid_x, field.grid_y) < 2.0
    water = dilate(maps.mask)
    inside = ((field.grid_x > X0 + 25) & (field.grid_x < X0 + SIZE - 25) & (field.grid_y > Y0 + 25)
              & (field.grid_y < Y0 + SIZE - 25))
    return ~blocked & ~near_line & ~channel & ~basin & ~water & inside & (maps.slope < 0.62)


def plan_routes(maps, layout, works):
    planner = Planner(maps.field, walk_mask(maps, layout, works))
    routes = {}
    for name, spec in PATHS.items():
        waypoints = [waypoint(kind, a, b, works) for kind, a, b in spec]
        raw = planner.route(waypoints, 0.15, 0.62)
        smooth = chaikin(raw, 2)
        if all(planner.clear(p, q, 0.18) for p, q in zip(smooth[:-1], smooth[1:])):
            raw = smooth
        routes[name] = densify(raw, 2.0)
    routes["domaine"] = densify([Vector(p) for p in TRACKS["domaine"]], 2.0)
    return routes


def build_routes(scene, ground, routes):
    root = scene.root("life")
    count = 0
    worst = (0.0, "", 0.0, 0.0)
    steepest = (0.0, "")
    for name, points in routes.items():
        if name == "domaine":
            continue
        dense = refine(ground, densify(points, 2.0))
        (grade, where), heights = grades(ground, dense)
        if grade > MAX_GRADE:
            raise RuntimeError(f"walk route {name} has a grade of {grade:.2f} at {where}")
        if grade > steepest[0]:
            steepest = (round(grade, 3), name)
        for index, (p, z) in enumerate(zip(dense, heights)):
            new_empty(f"walk_{name}_{index:03d}", scene.collection, root, Matrix.Translation((p.x, p.y, z)))
        for (p, z), (q, zq) in zip(zip(dense[:-1], heights[:-1]), zip(dense[1:], heights[1:])):
            middle = (p + q) / 2
            error = abs(ground.height(middle.x, middle.y) - (z + zq) / 2)
            if error > worst[0]:
                worst = (round(error, 3), name, round(middle.x, 1), round(middle.y, 1))
        count += len(dense)
    return count, worst, steepest


def place_walkers(scene):
    root = scene.root("life")
    for index, (key, spec) in enumerate(pont_life.WALKERS.items()):
        mesh = scene.library.mesh(key, lambda spec=spec: pont_life.person(spec), ground_occlusion=False)
        pont_life.vertex_shade(mesh, 0.72, 1.05)
        created = new_object(key, mesh, scene.collection, root, placement(6000.0 + index * 3.0, 0.0, 0.0))
        created["cast_shadow"] = True
    return len(pont_life.WALKERS)


INSTANCED_LIFE = ("goat_dark", "goat_light", "sheep")


def merge_objects(objects, name, collection, parent):
    data = bpy.data.meshes.new(name)
    data.uv_layers.new(name="UVMap")
    data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    target = new_object(name, data, collection, parent)
    with bpy.context.temp_override(active_object=target, object=target, selected_objects=objects + [target],
                                   selected_editable_objects=objects + [target]):
        bpy.ops.object.join()
    colours = target.data.color_attributes
    colours.active_color = colours["Col"]
    colours.render_color_index = colours.active_color_index
    target["cast_shadow"] = True
    return target


LIFE_CELL = 400.0


def instance_life(scene):
    builds = pont_life.figure_builds()
    counts = {}
    merged = []
    for key, matrices in scene.placements.items():
        group = scene.library.place(key, builds[key], scene.collection, scene.root("life"), matrices,
                                    cast_shadow=True, ground_occlusion=False)
        if key.startswith(("mule", "goat", "sheep", "dog", "fig_", "ox")):
            pont_life.vertex_shade(scene.library.meshes[key], 0.72 if key.startswith("fig_") else 0.6, 1.05)
        counts[key] = len(matrices)
        if key not in INSTANCED_LIFE:
            for child in list(group.children):
                child.matrix_world = group.matrix_world @ child.matrix_basis
            merged.extend(group.children)
            merged.append(group)
    groups = [obj for obj in merged if obj.type == "EMPTY"]
    meshes = [obj for obj in merged if obj.type == "MESH"]
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    bpy.context.view_layer.update()
    cells = {}
    for obj in meshes:
        where = obj.matrix_world.translation
        cells.setdefault((int(where.x // LIFE_CELL), int(where.y // LIFE_CELL)), []).append(obj)
    triangles = 0
    for index, objects in enumerate(cells.values()):
        static = merge_objects(objects, f"life_static_{index}", scene.collection, scene.root("life"))
        triangles += sum(len(polygon.vertices) - 2 for polygon in static.data.polygons)
    for group in groups:
        bpy.data.objects.remove(group)
    return counts, [triangles, len(cells)]


def ground_eye(height, x, y, rise, maps=None):
    floor = height(x, y)
    if maps is not None:
        floor = max(floor, maps.water(x, y) - DATUM)
    return Vector((x, y, floor + rise))


def bank_eye(height, maps):
    best = None
    for u in np.arange(-10.0, 130.0, 4.0):
        for w in np.arange(-180.0, -118.0, 4.0):
            x, y = from_bridge(float(u), float(w))
            rise = float(maps.field.sample(x, y)) - maps.water(x, y)
            if not 2.5 < rise < 9.0 or float(maps.at("slope", x, y)) > 0.4:
                continue
            score = abs(w + 150.0) + 0.3 * abs(u - 55.0) + 3.0 * abs(rise - 4.0)
            if best is None or score < best[0]:
                best = (score, x, y)
    if best is None:
        return ground_eye(height, *from_bridge(55.0, -150.0), 1.7, maps)
    return ground_eye(height, best[1], best[2], 1.7, maps)


def arch_eye(height, maps):
    best = None
    for u in np.arange(20.0, 26.5, 0.5):
        for w in np.arange(-20.0, -15.5, 0.5):
            x, y = from_bridge(float(u), float(w))
            if float(maps.field.sample(x, y)) - maps.water(x, y) < 0.6 or float(maps.at("slope", x, y)) > 0.5:
                continue
            score = abs(u - 23.0) + abs(w + 18.0)
            if best is None or score < best[0]:
                best = (score, x, y)
    if best is not None:
        return ground_eye(height, best[1], best[2], 2.6, maps)
    for k in range(60):
        x, y = from_bridge(18.0 + k * 0.5, -36.0)
        if float(maps.field.sample(x, y)) - maps.water(x, y) > 0.6:
            return ground_eye(height, x, y, 1.6, maps)
    return ground_eye(height, *from_bridge(24.0, -36.0), 1.6, maps)


def viewpoints(height, maps, layout, works, info=None):
    t1, t2, t3 = layout.tops
    centre = Vector((*from_bridge(-10.0, 0.0), t1))
    azimuth = math.radians(235.0)
    distance = 300.0
    ax, ay = centre.x + distance * math.sin(azimuth), centre.y + distance * math.cos(azimuth)
    aerial = Vector((ax, ay, max(t3 + 45.0, height(ax, ay) + 30.0)))
    pont_eye = bank_eye(height, maps)
    pont_target = Vector((*from_bridge(-5.0, 0.0), t1 + 1.0))
    grande = arch_eye(height, maps)
    arch_target = Vector((*from_bridge(14.5, -1.5), layout.base + 7.0))
    canal_eye = BRIDGE_MATRIX @ Vector((SLAB_GAP + 4.2, -3.1, t3 + 2.9))
    canal_target = BRIDGE_MATRIX @ Vector((SLAB_GAP - 0.6, 0.3, t3 - 1.0))
    qx, qy = dike_point(0.64)
    quarry_eye = Vector((qx, qy, height(qx, qy) + 1.7))
    quarry_target = Vector((314.0, 700.0, QUARRY_FLOOR - DATUM - 0.6))
    frame = works.frame
    side = works.discharge
    ex, ey = from_bridge(*frame.to_bridge(9.5, side * 8.5))
    basin_centre = works.world_centre
    basin_eye = Vector((ex, ey, max(height(ex, ey) + 1.7, works.coping - DATUM + 2.6)))
    basin_target = Vector((basin_centre.x, basin_centre.y, works.coping - DATUM - 1.0))
    return {
        "le-pont": (pont_eye, pont_target),
        "la-grande-arche": (grande, arch_target),
        "le-canal": (canal_eye, canal_target),
        "la-carriere": (quarry_eye, quarry_target),
        "le-bassin": (basin_eye, basin_target),
        "vue-d-ensemble": (aerial, centre),
    }


def figure_view(ground):
    a, b = Vector(TRACKS["domaine"][0]), Vector(TRACKS["domaine"][1])
    direction = (b - a).normalized()
    side = Vector((-direction.y, direction.x))
    focus = a + direction * 24.0
    eye = focus - side * 8.5 + direction * 7.0
    return (Vector((eye.x, eye.y, ground.height(eye.x, eye.y) + 1.6)),
            Vector((focus.x, focus.y, ground.height(focus.x, focus.y) + 1.0)))


def crew_view(ground):
    bx, by = dike_point(0.73)
    inward = Vector((QUARRY_CENTRE[0] - bx, QUARRY_CENTRE[1] - by)).normalized()
    along = Vector((-inward.y, inward.x))
    focus = Vector((bx, by)) + inward * 3.5
    eye = focus - along * 7.0 + inward * 7.0
    return (Vector((eye.x, eye.y, ground.height(eye.x, eye.y) + 1.7)),
            Vector((focus.x, focus.y, ground.height(focus.x, focus.y) + 0.8)))


def camera_corridors(points):
    corridors = []
    for key in ("le-pont", "la-carriere", "la-grande-arche", "le-bassin"):
        eye, target = points[key]
        start = Vector((eye.x, eye.y))
        direction = (Vector((target.x, target.y)) - start).normalized()
        near = start + direction * 25.0
        corridors.append(((start.x, start.y), (near.x, near.y), 2.0))
        corridors.append(((near.x, near.y), (target.x, target.y), 9.0))
    return corridors


def place_markers(scene, points):
    root = scene.root("markers")
    for key, (eye, target) in points.items():
        new_empty(f"poi_{key}", scene.collection, root, Matrix.Translation(eye))
        new_empty(f"poi_{key}_target", scene.collection, root, Matrix.Translation(target))


def flock_height(ground, x, y, wanted):
    top = wanted
    for radius in (0.0, 20.0, 40.0, 65.0):
        for k in range(12 if radius else 1):
            angle = 2 * math.pi * k / 12
            top = max(top, ground.height(x + radius * math.cos(angle), y + radius * math.sin(angle)) + 14.0)
    return top


def place_effects(scene, ground, layout, smokes):
    root = scene.root("life")
    for index, point in enumerate(smokes):
        new_empty(f"smoke_{index}", scene.collection, root, Matrix.Translation(point))
    t1, t2, t3 = layout.tops
    flocks = []
    for (u, w), wanted in (((-20.0, -100.0), layout.base + 26.0), ((60.0, -88.0), t1 + 6.0), ((-60.0, 0.0), t3 + 8.0)):
        x, y = from_bridge(u, w)
        z = flock_height(ground, x, y, wanted) if abs(w) > 1.0 else wanted
        flocks.append(Vector((x, y, z)))
    flocks.append(Vector((250.0, 700.0, flock_height(ground, 250.0, 700.0, QUARRY_FLOOR - DATUM + 16.0))))
    for x, y in (from_bridge(-40.0, 220.0), (FARM[0] + 20.0, FARM[1] - 30.0)):
        flocks.append(Vector((x, y, flock_height(ground, x, y, 30.0))))
    for index, point in enumerate(flocks):
        new_empty(f"birds_{index}", scene.collection, root, Matrix.Translation(point))
    return [[round(v, 1) for v in point] for point in flocks]


def render_previews(options, views):
    wanted = options["previews"]
    if wanted == "none":
        return {}
    names = list(views) if wanted == "all" else wanted.split(",")
    stage = ensure_collection("Stage")
    evening_world(SUN_AZIMUTH, SUN_ELEVATION, 0.16, aerosol=0.6)
    sun_lamp(stage, SUN_AZIMUTH, SUN_ELEVATION, 7.0, (1.0, 0.6, 0.34), 0.8)
    haze_volume(stage, 30000.0, 500.0, 0.00006, (0.78, 0.84, 0.95), 0.3)
    configure_render(1280, 720, options["samples"], exposure=-0.3, volumetric_end=20000.0)
    timings = {}
    for name in names:
        eye, target = views[name]
        realtime = name == "temps_reel"
        bpy.context.scene.eevee.use_raytracing = not realtime
        bpy.context.scene.eevee.use_fast_gi = not realtime
        rig = camera(stage, f"cam_{name}", eye, target, lens=35.0 if name == "vue_d_ensemble" else 28.0)
        timings[name] = round(render_still(rig, os.path.join(CACHE, "previews", f"{name}.png")), 1)
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
    tiles, credits, rects = build_pont_library(CACHE)
    scene = Scene(tiles)
    field, far_field, dem_urls = load_terrain()
    mask, level = river(field)
    layout = Layout(BASE_NGF - DATUM)
    layout.place_top(find_tier3_end(field, layout))
    saddle = arcade_saddle(field, layout)
    works = Works(layout, field)
    field.heights = works.carve(field.grid_x, field.grid_y, field.heights)
    quarry_inside = carve_quarry(field)
    maps = Maps(field, mask, level, quarry_inside)
    routes = plan_routes(maps, layout, works)
    maps.roads = list(routes.values())
    field_height = lambda x, y: float(field.sample(x, y)) - DATUM
    rough_points = viewpoints(field_height, maps, layout, works)
    corridors = camera_corridors(rough_points)
    rng = np.random.default_rng(17)
    frames = choose_vegetation(maps, layout, works, corridors, routes, rng)
    surfaces = build_terrain(scene, maps, far_field, works)
    build_water(scene, maps)
    bpy.context.view_layer.update()
    ground = Ground(lambda x, y: float(field.sample(x, y)) - DATUM)
    for surface in surfaces:
        ground.add(surface)
    ground.build()
    faces, ledges = quarry_faces(scene, ground, rng, frames)
    ground.add(faces)
    ground.build()
    print("QUARRY_LEDGE_PLANTS", ledges, flush=True)
    arches, info, bridge_triangles = build_bridge_object(scene, layout, ground, rects, works)
    points = viewpoints(lambda x, y: ground.height(x, y), maps, layout, works, info)
    place_markers(scene, points)
    scatter = Scatter(maps, layout, works, corridors, routes)
    ground_detail(frames, maps, scatter, points, rng)
    enrich_vegetation(frames, maps, scatter, points, rng)
    vegetation = plant_vegetation(scene, ground, frames)
    smokes = place_life(scene, maps, ground, layout, works, info, scatter, points, rng)
    smokes += place_scenes(scene, maps, ground, layout, works, info, scatter, points, rng)
    route_points_count, route_error, route_grade = build_routes(scene, ground, routes)
    walkers = place_walkers(scene)
    life_counts, static_triangles = instance_life(scene)
    flocks = place_effects(scene, ground, layout, smokes)
    roots = list(scene.roots.values())
    statistics = group_statistics(roots)
    for key, value in statistics.items():
        print("GROUP", key, json.dumps(value), flush=True)
    glb = os.path.join(CACHE, "pont-du-gard.glb")
    export_seconds = export_glb(glb, roots)
    t1, t2, t3 = (top + DATUM for top in layout.tops)
    report = {
        "datum_ngf_metres": DATUM, "base_ngf_metres": BASE_NGF, "tier_tops_ngf": [t1, t2, t3],
        "bridge": {"axis_bearing": BEARING, "large_arch_along_axis": ARCH_S, "tier1_spans": list(TIER1_SPANS),
                   "tier1": [layout.tier1_start, layout.tier1_end], "tier2": [layout.tier2_start, layout.tier2_end],
                   "tier3": [layout.tier3_start, layout.tier3_end], "abutment_length": round(works.length, 1),
                   "basin_local": [round(works.world_centre.x, 1), round(works.world_centre.y, 1)],
                   "discharge_side": works.discharge, "tier2_extra_span": layout.extra_span,
                   "tier3_pier": layout.pier3, "triangles": bridge_triangles},
        "arcade_saddle_max_metres": round(saddle, 2),
        "water_level_ngf_at_bridge": round(maps.water(BRIDGE_ORIGIN.x, BRIDGE_ORIGIN.y), 2),
        "sun": [SUN_AZIMUTH, SUN_ELEVATION], "vegetation": vegetation, "life": life_counts,
        "life_static_triangles": static_triangles,
        "walk_points": route_points_count, "walk_midpoint_error_metres": route_error,
        "walk_max_grade": route_grade, "walkers": walkers, "smoke_sources": len(smokes), "bird_flocks": flocks,
        "statistics": statistics, "glb_bytes": os.path.getsize(glb), "export_seconds": round(export_seconds, 1),
        "elevation_sources": dem_urls, "elevation_licence": ETALAB_LICENCE, "texture_credits": credits,
        "markers": {key: [[round(v, 2) for v in eye], [round(v, 2) for v in target]]
                    for key, (eye, target) in points.items()},
    }
    views = {"vue_d_ensemble": points["vue-d-ensemble"], "le_pont": points["le-pont"],
             "la_grande_arche": points["la-grande-arche"], "le_canal": points["le-canal"],
             "la_carriere": points["la-carriere"], "le_bassin": points["le-bassin"],
             "temps_reel": points["le-pont"], "personnages": figure_view(ground), "berge": crew_view(ground)}
    bpy.context.scene["preview_points"] = json.dumps({key: [list(eye), list(target)]
                                                      for key, (eye, target) in views.items()})
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    report["previews"] = render_previews(options, views)
    report["total_seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(CACHE, "build_report.json"), "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=1)
    print("REPORT", json.dumps({key: report[key] for key in ("bridge", "water_level_ngf_at_bridge", "walk_points",
                                                              "walk_midpoint_error_metres", "walk_max_grade",
                                                              "life_static_triangles", "glb_bytes", "previews",
                                                              "total_seconds")}), flush=True)


if __name__ == "__main__":
    main()

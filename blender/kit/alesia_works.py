import math
import random

import numpy as np
from mathutils import Matrix, Vector

from .cannes_camps import rampart, tent, tent_rows, tinted_box
from .geometry import MATTE, MeshBuilder, placement
from .pompei_terrain import blur, world_noise

FOOT = 0.296
TOWER_SPACING = 80 * FOOT
EARTH = (0.56, 0.45, 0.31)
TURF = (0.46, 0.44, 0.28)
TIMBER = (0.42, 0.31, 0.20)
DARK_TIMBER = (0.30, 0.22, 0.15)
DITCH = (0.24, 0.19, 0.14)
LIMESTONE = (0.74, 0.70, 0.60)
DRY_STONE = (0.66, 0.62, 0.52)
DAUB = (0.64, 0.56, 0.42)
THATCH = (0.56, 0.47, 0.29)
HIDE = (0.46, 0.37, 0.27)
LEATHER_TENT = (0.62, 0.50, 0.36)

CONTREVALLATION = [(-2550, -750), (-2750, -150), (-2700, 450), (-2450, 1000), (-2000, 1300), (-1500, 1700),
                   (-950, 1800), (-400, 2100), (100, 2050), (450, 1800), (900, 1900), (1400, 1700), (1750, 1400),
                   (2250, 1300), (2700, 850), (3000, 300), (3150, -250), (2950, -800), (2500, -1250), (1900, -1400),
                   (1350, -1500), (750, -1400), (150, -1500), (-450, -1400), (-1050, -1450), (-1600, -1300),
                   (-2150, -1150)]
CIRCONVALLATION = [(-3350, -1100), (-3550, -300), (-3500, 500), (-3300, 1050), (-2850, 1400), (-2400, 1720),
                   (-1900, 2050), (-1300, 2450), (-700, 2750), (-100, 2850), (500, 2750), (1100, 2950), (1700, 2850),
                   (2350, 2600), (2950, 2200), (3450, 1600), (3800, 850), (3950, 50), (3750, -700), (3450, -1350),
                   (2950, -1950), (2250, -2350), (1450, -2600), (650, -2650), (-150, -2750), (-950, -2550),
                   (-1700, -2300), (-2450, -1950), (-2950, -1550)]

CAMPS = {
    "camp_b_flavigny": dict(centre=(900.0, -1950.0), size=(290.0, 252.0), angle=0.05, fill=0.85),
    "camp_c_bussy": dict(centre=(1900.0, 1950.0), size=(282.0, 245.0), angle=-0.35, fill=0.85),
    "camp_a_flavigny": dict(centre=(-600.0, -1850.0), size=(120.0, 100.0), angle=0.1, fill=0.8),
    "camp_du_rea_hypothese": dict(centre=(-2250.0, 1450.0), size=(330.0, 270.0), angle=0.62, fill=0.8),
    "fortin_de_l_epineuse": dict(centre=(-3120.0, -260.0), size=(70.0, 55.0), angle=-0.05, fill=0.6),
}
THIRD_DITCH = (-3100.0, -2300.0, -900.0, 700.0)
RELIEF_CAMP = dict(centre=(-4900.0, -1700.0), radii=(650.0, 420.0), angle=0.4)
OPPIDUM_CENTRE = (0.0, 120.0)
OPPIDUM_RIM = 372.0
EAST_CAMP_REACH = 230.0
TRAP_SECTORS = {
    "plaine": dict(line="contrevallation", box=(-3000.0, -2400.0, -320.0, 20.0)),
    "rea": dict(line="circonvallation", box=(-2650.0, -2050.0, 1450.0, 2000.0)),
}


def closed_chaikin(points, passes=3):
    points = np.asarray(points, float)
    for _ in range(passes):
        following = np.roll(points, -1, axis=0)
        refined = np.empty((2 * len(points), 2))
        refined[0::2] = 0.75 * points + 0.25 * following
        refined[1::2] = 0.25 * points + 0.75 * following
        points = refined
    return points


def resample_closed(points, step):
    closed = np.vstack([points, points[:1]])
    lengths = np.hypot(*np.diff(closed, axis=0).T)
    distance = np.concatenate([[0], np.cumsum(lengths)])
    count = max(8, int(distance[-1] / step))
    target = np.linspace(0, distance[-1], count, endpoint=False)
    return np.column_stack([np.interp(target, distance, closed[:, 0]), np.interp(target, distance, closed[:, 1])])


def loop_frames(path, inward):
    tangents = np.roll(path, -1, axis=0) - np.roll(path, 1, axis=0)
    tangents /= np.maximum(np.linalg.norm(tangents, axis=1)[:, None], 1e-9)
    left = np.column_stack([-tangents[:, 1], tangents[:, 0]])
    area = 0.5 * np.sum(path[:, 0] * np.roll(path[:, 1], -1) - np.roll(path[:, 0], -1) * path[:, 1])
    inside = left if area > 0 else -left
    return tangents, inside if inward else -inside


def loop_length(path):
    return float(np.hypot(*np.diff(np.vstack([path, path[:1]]), axis=0).T).sum())


class Line:
    def __init__(self, name, points, enemy_inside):
        self.name = name
        self.inward = enemy_inside
        self.path = resample_closed(closed_chaikin(points), 10.0)
        self.tangent, self.enemy = loop_frames(self.path, enemy_inside)
        self.length = loop_length(self.path)

    def offset(self, distance):
        return self.path + self.enemy * distance

    def fine(self, step=2.5):
        path = resample_closed(self.path, step)
        return path, loop_frames(path, self.inward)[1]


def strip(builder, rows, color, double=False):
    first = len(builder.polygons)
    indices = [builder.points(row) for row in rows]
    a, b, c = Vector(rows[0][0]), Vector(rows[0][1]), Vector(rows[1][0])
    flip = (b - a).cross(c - a).z < 0
    for k in range(len(rows) - 1):
        for j in range(len(rows[0]) - 1):
            quad = [indices[k][j], indices[k][j + 1], indices[k + 1][j + 1], indices[k + 1][j]]
            if flip or double:
                builder.face(list(reversed(quad)), MATTE)
            if not flip or double:
                builder.face(quad, MATTE)
    builder.tint(first, color)


AGGER = [(-5.0, -0.9), (-1.8, 2.1), (1.4, 2.1), (4.2, -0.9)]
BREASTWORK = [(1.25, 2.0), (1.25, 3.5), (1.6, 3.5), (1.6, 2.0)]


def agger(line, height_at, step=12.0):
    path, enemy = line.fine(step)
    builder = MeshBuilder()
    closed = list(range(len(path))) + [0]

    def section(profile):
        rows = []
        for k in closed:
            px, py = path[k]
            nx, ny = enemy[k]
            row = []
            for s, dz in profile:
                x, y = px + nx * s, py + ny * s
                row.append((x, y, height_at(x, y) + dz))
            rows.append(row)
        return rows

    rows = section(AGGER)
    strip(builder, [row[:2] for row in rows], EARTH)
    strip(builder, [row[1:3] for row in rows], TURF)
    strip(builder, [row[2:] for row in rows], EARTH)
    strip(builder, section(BREASTWORK), TIMBER, double=True)
    return builder


def tower():
    builder = MeshBuilder()
    for sx in (-1, 1):
        for sy in (-1, 1):
            first = len(builder.polygons)
            builder.box((sx * 1.5 - 0.14, sy * 1.5 - 0.14, 0.0), (sx * 1.5 + 0.14, sy * 1.5 + 0.14, 3.6), MATTE,
                        bottom=False, top=False)
            builder.tint(first, DARK_TIMBER)
    first = len(builder.polygons)
    builder.box((-1.75, -1.75, 3.6), (1.75, 1.75, 4.9), MATTE, bottom=True, top=True)
    builder.tint(first, TIMBER)
    return builder


def tower_matrices(line, height_at):
    path, enemy = line.fine(TOWER_SPACING)
    matrices = []
    for (px, py), (nx, ny) in zip(path, enemy):
        x, y = px + nx * 0.4, py + ny * 0.4
        heading = math.atan2(ny, nx) - math.pi / 2
        matrices.append(placement(x, y, height_at(x, y) + 2.0, heading))
    return matrices


def water_ditch(line, height_at, level):
    path, enemy = line.fine(6.0)
    heights = np.array([height_at(x, y) for x, y in path])
    wet = heights < level
    vertices = []
    faces = []
    count = len(path)
    for k in range(count):
        if not (wet[k] and wet[(k + 1) % count]):
            continue
        quad = []
        for index in (k, (k + 1) % count):
            for s in (6.3, 11.1):
                x, y = path[index] + enemy[index] * s
                quad.append((x, y, height_at(x, y) + 0.22))
        start = len(vertices)
        vertices.extend([quad[0], quad[2], quad[3], quad[1]])
        faces.append((start, start + 1, start + 2, start + 3))
    return vertices, faces


def castellum_frames(line, count=23, setback=34.0):
    lengths = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(line.path, axis=0).T))])
    result = []
    for k in range(count):
        target = (k + 0.37) * line.length / count
        index = int(np.searchsorted(lengths, target)) % len(line.path)
        centre = line.path[index] - line.enemy[index] * setback
        angle = math.atan2(line.tangent[index][1], line.tangent[index][0])
        result.append((tuple(centre), angle))
    return result


def retranchements(lines, height_at):
    builder = MeshBuilder()
    for camp in CAMPS.values():
        rampart(builder, camp["centre"], camp["size"], camp["angle"], height_at, segment=30.0,
                gate=12.0 if camp["size"][0] > 100 else 6.0)
    for centre, angle in castellum_frames(lines["contrevallation"]):
        rampart(builder, centre, (34.0, 30.0), angle, height_at, segment=11.0, gate=4.0)
    return builder


def camp_tents(height_at):
    matrices = []
    for name, camp in CAMPS.items():
        matrices += tent_rows(camp["centre"], camp["size"], camp["angle"], (16.0, 12.0), 20.0, height_at,
                              seed=len(name), jitter=0.0, fill=camp["fill"])
    return matrices


def plateau_rim(height_at, rays=200, reach=1800.0, step=8.0):
    cx, cy = OPPIDUM_CENTRE
    points = []
    for k in range(rays):
        angle = math.tau * k / rays
        dx, dy = math.cos(angle), math.sin(angle)
        distance = 40.0
        while distance < reach and height_at(cx + dx * distance, cy + dy * distance) >= OPPIDUM_RIM:
            distance += step
        points.append((cx + dx * distance, cy + dy * distance))
    return resample_closed(closed_chaikin(np.array(points), 2), 8.0)


def rim_frames(rim):
    tangent, inward = loop_frames(rim, True)
    return tangent, -inward


MURUS = [(-9.0, -0.6), (-6.5, 2.4), (-0.4, 3.8), (0.0, 3.8), (0.5, -1.2)]


def oppidum_wall(rim, height_at, gates):
    _, outward = rim_frames(rim)
    builder = MeshBuilder()
    count = len(rim)
    rows = []
    for k in range(count + 1):
        index = k % count
        px, py = rim[index]
        if any(math.hypot(px - gx, py - gy) < 9.0 for gx, gy in gates):
            if len(rows) > 1:
                strip(builder, [row[:3] for row in rows], EARTH)
                strip(builder, [row[2:] for row in rows], LIMESTONE)
            rows = []
            continue
        nx, ny = outward[index]
        row = []
        for s, dz in MURUS:
            x, y = px + nx * s, py + ny * s
            row.append((x, y, height_at(x, y) + dz))
        rows.append(row)
    if len(rows) > 1:
        strip(builder, [row[:3] for row in rows], EARTH)
        strip(builder, [row[2:] for row in rows], LIMESTONE)
    return builder


def oppidum_gates(rim):
    west = rim[np.argmin(rim[:, 0])]
    east = rim[np.argmax(rim[:, 0])]
    south = rim[np.argmin(rim[:, 1])]
    return [tuple(west), tuple(east), tuple(south)]


def point_in(points, x, y):
    inside = False
    count = len(points)
    for k in range(count):
        x0, y0 = points[k]
        x1, y1 = points[(k + 1) % count]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def hut():
    builder = MeshBuilder()
    tinted_box(builder, (-2.6, -4.0, -0.5), (2.6, 4.0, 2.0), DAUB)
    first = len(builder.polygons)
    a, b, c, d, e, f = builder.points([(-3.1, -4.4, 1.9), (3.1, -4.4, 1.9), (0.0, -3.4, 4.8),
                                       (-3.1, 4.4, 1.9), (3.1, 4.4, 1.9), (0.0, 3.4, 4.8)])
    for face in ((a, c, b), (d, e, f), (a, d, f, c), (b, c, f, e)):
        builder.face(list(face), MATTE)
    builder.tint(first, THATCH)
    return builder


def shelter():
    return tent().tint(0, HIDE)


def scatter(rng, count, accept, bounds, spacing):
    x0, x1, y0, y1 = bounds
    placed = []
    attempts = 0
    while len(placed) < count and attempts < count * 60:
        attempts += 1
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if not accept(x, y):
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < spacing * spacing for px, py in placed[-400:]):
            continue
        placed.append((x, y))
    return placed


def oppidum_huts(rim, height_at, count=320, seed=5):
    rng = random.Random(seed)
    inner = rim - rim_frames(rim)[1] * 30.0
    bounds = (inner[:, 0].min(), inner[:, 0].max(), inner[:, 1].min(), inner[:, 1].max())
    spots = scatter(rng, count, lambda x, y: point_in(inner, x, y), bounds, 16.0)
    return [placement(x, y, height_at(x, y) - 0.2, rng.uniform(0, math.pi)) for x, y in spots]


def east_camp(rim, height_at, seed=9):
    _, outward = rim_frames(rim)
    east = rim[:, 0] > rim[:, 0].max() - 380.0
    indices = np.nonzero(east)[0]
    order = indices[np.argsort(np.arctan2(rim[indices, 1] - OPPIDUM_CENTRE[1], rim[indices, 0] - OPPIDUM_CENTRE[0]))]
    curve = [tuple(rim[k] + outward[k] * EAST_CAMP_REACH) for k in order]
    builder = MeshBuilder()
    rows = []
    for x, y in curve:
        z = height_at(x, y)
        rows.append([(x, y, z - 0.5), (x, y, z + 1.8)])
    strip(builder, rows, DRY_STONE, double=True)
    rng = random.Random(seed)
    zone = np.vstack([rim[order], np.array(curve)[::-1]])
    bounds = (zone[:, 0].min(), zone[:, 0].max(), zone[:, 1].min(), zone[:, 1].max())
    spots = scatter(rng, 260, lambda x, y: point_in(zone, x, y), bounds, 9.0)
    shelters = [placement(x, y, height_at(x, y) - 0.1, rng.uniform(0, math.pi), 0.8) for x, y in spots]
    return builder, shelters, curve


def relief_camp(height_at, seed=13):
    cx, cy = RELIEF_CAMP["centre"]
    a, b = RELIEF_CAMP["radii"]
    angle = RELIEF_CAMP["angle"]
    cosine, sine = math.cos(angle), math.sin(angle)
    ring = []
    for k in range(160):
        t = math.tau * k / 160
        wobble = 1.0 + 0.05 * math.sin(3 * t + 1.0) + 0.03 * math.sin(7 * t)
        lx, ly = a * wobble * math.cos(t), b * wobble * math.sin(t)
        ring.append((cx + lx * cosine - ly * sine, cy + lx * sine + ly * cosine))
    builder = MeshBuilder()
    rows = []
    for x, y in ring + ring[:1]:
        z = height_at(x, y)
        nx, ny = x - cx, y - cy
        norm = math.hypot(nx, ny)
        nx, ny = nx / norm, ny / norm
        rows.append([(x - nx * 3.0, y - ny * 3.0, z - 0.4), (x, y, z + 1.1), (x + nx * 3.0, y + ny * 3.0, z - 0.4)])
    strip(builder, rows, EARTH)
    rng = random.Random(seed)

    def inside(x, y):
        dx, dy = x - cx, y - cy
        lx, ly = dx * cosine + dy * sine, -dx * sine + dy * cosine
        return (lx / (a - 25)) ** 2 + (ly / (b - 25)) ** 2 < 1.0

    spots = scatter(rng, 900, inside, (cx - a, cx + a, cy - a, cy + a), 11.0)
    shelters = [placement(x, y, height_at(x, y) - 0.1, rng.uniform(0, math.pi), 0.9) for x, y in spots]
    return builder, shelters, ring


def lilium():
    builder = MeshBuilder()
    first = len(builder.polygons)
    ring = [(0.42 * math.cos(math.tau * k / 6), 0.42 * math.sin(math.tau * k / 6)) for k in range(6)]
    builder.face(builder.points([(x, y, 0.03) for x, y in ring]), MATTE)
    builder.tint(first, (0.16, 0.12, 0.09))
    first = len(builder.polygons)
    tip = builder.point((0.0, 0.0, 0.25))
    base = builder.points([(0.06 * math.cos(math.tau * k / 3), 0.06 * math.sin(math.tau * k / 3), -0.2) for k in range(3)])
    for k in range(3):
        builder.face([base[k], base[(k + 1) % 3], tip], MATTE)
    builder.tint(first, (0.55, 0.42, 0.28))
    return builder


def cippus():
    builder = MeshBuilder()
    first = len(builder.polygons)
    for k, lean in enumerate((-0.35, 0.0, 0.35)):
        top = Vector((lean * 0.6, 0.15 * (k - 1), 0.85))
        base = [Vector((0.05 * math.cos(math.tau * j / 3), 0.05 * math.sin(math.tau * j / 3), -0.1)) for j in range(3)]
        indices = builder.points(base)
        apex = builder.point(top)
        for j in range(3):
            builder.face([indices[j], indices[(j + 1) % 3], apex], MATTE)
    builder.tint(first, (0.40, 0.30, 0.19))
    return builder


PATCH_LENGTH = 9.9


def trap_patch():
    builder = MeshBuilder()
    pit = lilium()
    stake = cippus()
    rng = random.Random(3)
    for row in range(5):
        for k in range(9):
            x = -PATCH_LENGTH / 2 + (k + 0.5) * PATCH_LENGTH / 9 + rng.uniform(-0.15, 0.15)
            builder.merge(stake, placement(x, 19.0 + row * 1.1, 0.0, rng.uniform(0, math.tau), rng.uniform(0.8, 1.15)))
    for row in range(8):
        for k in range(5):
            x = -PATCH_LENGTH / 2 + (k + 0.25 + 0.5 * (row % 2)) * PATCH_LENGTH / 5
            builder.merge(pit, placement(x, 25.5 + row * 0.9, 0.0, rng.uniform(0, math.tau)))
    return builder


def trap_matrices(lines, height_at):
    matrices = []
    for name, sector in TRAP_SECTORS.items():
        line = lines[sector["line"]]
        path, enemy = line.fine(PATCH_LENGTH)
        x0, x1, y0, y1 = sector["box"]
        for k, ((px, py), (nx, ny)) in enumerate(zip(path, enemy)):
            if not (x0 < px < x1 and y0 < py < y1) or (name == "rea" and k % 3 == 1):
                continue
            angle = math.atan2(ny, nx) - math.pi / 2
            matrices.append(placement(px, py, height_at(px + nx * 28.0, py + ny * 28.0) + 0.06, angle))
    return matrices


class Painter:
    def __init__(self, lines, rim, east_curve, relief_ring):
        self.lines = lines
        self.rim = rim
        self.east_curve = np.array(east_curve)
        self.relief_ring = np.array(relief_ring)

    @staticmethod
    def frame(gx, gy):
        return gx[0, 0], gx[0, -1], gy[-1, 0], gy[0, 0], gx.shape

    def stamp(self, gx, gy, xs, ys, weight=1.0, mask=None):
        x0, x1, y0, y1, (rows, columns) = self.frame(gx, gy)
        mask = np.zeros((rows, columns)) if mask is None else mask
        column = np.rint((np.asarray(xs) - x0) / (x1 - x0) * (columns - 1)).astype(int)
        row = np.rint((y1 - np.asarray(ys)) / (y1 - y0) * (rows - 1)).astype(int)
        keep = (column >= 0) & (column < columns) & (row >= 0) & (row < rows)
        mask[row[keep], column[keep]] = np.maximum(mask[row[keep], column[keep]], weight)
        return mask

    def band(self, gx, gy, path, normals, start, end, spacing):
        mask = None
        for s in np.arange(start, end + 1e-6, max(spacing * 0.6, 0.5)):
            points = path + normals * s
            mask = self.stamp(gx, gy, points[:, 0], points[:, 1], mask=mask)
        return mask

    def clearing(self, gx, gy, spacing):
        mask = np.zeros(gx.shape)
        for line in self.lines.values():
            path, enemy = line.fine(spacing * 0.7)
            mask = np.maximum(mask, self.band(gx, gy, path, enemy, -150.0, 160.0, spacing * 2.5))
        for camp in CAMPS.values():
            cx, cy = camp["centre"]
            mask = np.maximum(mask, ((gx - cx) ** 2 + (gy - cy) ** 2 < (max(camp["size"]) * 0.8) ** 2).astype(float))
        rcx, rcy = RELIEF_CAMP["centre"]
        mask = np.maximum(mask, ((gx - rcx) ** 2 + (gy - rcy) ** 2 < 800.0 ** 2).astype(float))
        mask = np.maximum(mask, ((gx - OPPIDUM_CENTRE[0]) ** 2 / 1500.0 ** 2 + (gy - OPPIDUM_CENTRE[1]) ** 2 / 800.0 ** 2
                                 < 1.0).astype(float))
        edge = world_noise(gx, gy, 90.0, 43, octaves=3)
        return np.clip(blur(mask, 10) * 1.4 - (edge - 0.5) * 0.9, 0, 1)

    def paint(self, pixels, gx, gy, spacing):
        colour = pixels.copy()
        grain = world_noise(gx, gy, 7.0, 41, octaves=2)

        def apply(mask, target, strength=1.0):
            weight = np.clip(blur(mask, 1) * 1.4, 0, 1) * strength
            return colour * (1 - weight[..., None]) + np.asarray(target) * weight[..., None]

        inside_rim = self.stamp_polygon(gx, gy, self.rim)
        colour = apply(inside_rim, (0.60, 0.55, 0.41), 0.45)
        colour = apply(self.stamp_polygon(gx, gy, self.relief_ring), (0.58, 0.52, 0.38), 0.5)
        for camp in CAMPS.values():
            corners = self.camp_corners(camp, 0.0)
            colour = apply(self.stamp_polygon(gx, gy, corners), (0.62, 0.55, 0.41), 0.55)
        for name, line in self.lines.items():
            path, enemy = line.fine(spacing * 0.6)
            colour = apply(self.band(gx, gy, path, enemy, -6.0, 5.0, spacing), EARTH, 0.85)
            colour = apply(self.band(gx, gy, path, enemy, 6.5, 10.9, spacing), DITCH, 0.95)
            colour = apply(self.band(gx, gy, path, enemy, 12.5, 16.9, spacing), DITCH, 0.95)
            traps = self.band(gx, gy, path, enemy, 18.0, 42.0, spacing) * (grain > 0.52)
            colour = apply(traps, (0.34, 0.27, 0.19), 0.7)
            if name == "contrevallation":
                colour = apply(self.band(gx, gy, path, enemy, 115.0, 121.0, spacing), DITCH, 0.9)
                x0, x1, y0, y1 = THIRD_DITCH
                plain = (path[:, 0] > x0) & (path[:, 0] < x1) & (path[:, 1] > y0) & (path[:, 1] < y1)
                colour = apply(self.band(gx, gy, path[plain], enemy[plain], 46.0, 50.4, spacing), DITCH, 0.9)
        east = self.east_curve
        tangent = np.gradient(east, axis=0)
        tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-9)
        normal = np.column_stack([tangent[:, 1], -tangent[:, 0]])
        centre = np.array(OPPIDUM_CENTRE)
        flip = np.sign(np.sum((east - centre) * normal, axis=1))[:, None]
        colour = apply(self.band(gx, gy, east, normal * flip, 2.0, 5.0, spacing), DITCH, 0.8)
        return np.clip(colour, 0, 1)

    @staticmethod
    def camp_corners(camp, margin):
        cx, cy = camp["centre"]
        hx, hy = camp["size"][0] / 2 + margin, camp["size"][1] / 2 + margin
        cosine, sine = math.cos(camp["angle"]), math.sin(camp["angle"])
        return np.array([(cx + x * cosine - y * sine, cy + x * sine + y * cosine)
                         for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))])

    @staticmethod
    def stamp_polygon(gx, gy, points):
        points = np.asarray(points, float)
        columns = np.nonzero((gx[0] >= points[:, 0].min() - 10) & (gx[0] <= points[:, 0].max() + 10))[0]
        rows = np.nonzero((gy[:, 0] >= points[:, 1].min() - 10) & (gy[:, 0] <= points[:, 1].max() + 10))[0]
        result = np.zeros(gx.shape)
        if len(columns) == 0 or len(rows) == 0:
            return result
        window = (slice(rows[0], rows[-1] + 1), slice(columns[0], columns[-1] + 1))
        wx, wy = gx[window], gy[window]
        inside = np.zeros(wx.shape, dtype=bool)
        count = len(points)
        for k in range(count):
            x0, y0 = points[k]
            x1, y1 = points[(k + 1) % count]
            if y0 == y1:
                continue
            crosses = (y0 > wy) != (y1 > wy)
            intersection = x0 + (wy - y0) * (x1 - x0) / (y1 - y0)
            inside ^= crosses & (wx < intersection)
        result[window] = inside
        return result

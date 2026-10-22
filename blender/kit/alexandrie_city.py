import math
import random

from mathutils import Vector

from .alexandrie_pharos import painted
from .geometry import MATTE, MeshBuilder
from .nimes_figures import drape, ellipsoid, tube

PLASTER = "plaster"
STONE = "limestone"
MARBLE = "marble"
PAVING = "paving"
TILES = "terracotta_tiles"
VOID = "shadow_void"
TAU = 2 * math.pi
WALLS = [(1.0, 0.98, 0.94), (1.0, 0.86, 0.62), (0.98, 0.76, 0.54), (1.0, 0.80, 0.72), (0.78, 0.86, 0.96),
         (1.0, 0.92, 0.60), (0.94, 0.70, 0.58), (1.0, 0.96, 0.86), (0.90, 0.64, 0.48), (1.0, 0.90, 0.80),
         (0.98, 0.84, 0.70), (0.84, 0.92, 0.86)]
ROOFS = [(0.97, 0.95, 0.9), (0.93, 0.88, 0.80), (0.98, 0.93, 0.84), (0.90, 0.86, 0.80)]
CLOTHS = [(0.80, 0.18, 0.12), (0.94, 0.72, 0.22), (0.22, 0.40, 0.70), (0.96, 0.93, 0.86), (0.72, 0.30, 0.48),
          (0.30, 0.58, 0.42), (0.88, 0.45, 0.16)]
WOOD = (0.44, 0.32, 0.21)
PALM_GREEN = [(0.34, 0.50, 0.20), (0.40, 0.54, 0.22), (0.30, 0.44, 0.18), (0.46, 0.56, 0.24)]
CHUNK = (64.0, 56.0)


def quad(builder, corners, normal, material, colour=None):
    first = len(builder.polygons)
    builder.oriented(corners, normal, material)
    if colour is not None:
        builder.tint(first, colour)


def lots(rng, width, depth):
    columns = rng.choice((2, 3, 3))
    rows = 2
    xs = [-width / 2]
    for k in range(1, columns):
        xs.append(-width / 2 + width * k / columns + rng.uniform(-4.0, 4.0))
    xs.append(width / 2)
    ys = [-depth / 2, rng.uniform(-5.0, 5.0), depth / 2]
    result = []
    for i in range(columns):
        for j in range(rows):
            result.append((xs[i] + 0.6, ys[j] + 0.6, xs[i + 1] - 0.6, ys[j + 1] - 0.6, i, j, columns))
    return result


def wall_box(builder, x0, y0, x1, y1, z0, z1, colour):
    painted(builder, colour, lambda: builder.box((x0, y0, z0), (x1, y1, z1), PLASTER, bottom=False, top=False))


def roof_slab(builder, x0, y0, x1, y1, z, colour, parapet=0.8, detail=True):
    painted(builder, colour, lambda: builder.oriented([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, 1),
                                                      PLASTER))
    if not detail or parapet <= 0:
        return
    t = 0.35
    edge = tuple(c * 0.97 for c in colour)
    for a, b, c, d in (((x0, y0), (x1, y0), (x1, y0 + t), (x0, y0 + t)), ((x0, y1 - t), (x1, y1 - t), (x1, y1), (x0, y1)),
                       ((x0, y0 + t), (x0 + t, y0 + t), (x0 + t, y1 - t), (x0, y1 - t)),
                       ((x1 - t, y0 + t), (x1, y0 + t), (x1, y1 - t), (x1 - t, y1 - t))):
        painted(builder, edge, lambda a=a, c=c: builder.box((a[0], a[1], z), (c[0], c[1], z + parapet), PLASTER,
                                                            bottom=False))


def windows(builder, x0, x1, y, facing, height, rng, floors, shutters=True):
    width = x1 - x0
    count = max(int(width / 4.2), 1)
    for floor in range(1, floors):
        z = floor * 3.4 + 0.8
        for k in range(count):
            x = x0 + width * (k + 0.5) / count + rng.uniform(-0.4, 0.4)
            quad(builder, [(x - 0.42, y, z), (x + 0.42, y, z), (x + 0.42, y, z + 1.1), (x - 0.42, y, z + 1.1)],
                 (0, facing, 0), VOID)
            if shutters and rng.random() < 0.45:
                tone = rng.choice([(0.30, 0.42, 0.56), (0.42, 0.30, 0.22), (0.30, 0.46, 0.32), (0.56, 0.24, 0.18)])
                for side in (-1, 1):
                    xa = x + side * 0.42
                    xb = x + side * 0.82
                    quad(builder, [(min(xa, xb), y + facing * 0.02, z), (max(xa, xb), y + facing * 0.02, z),
                                   (max(xa, xb), y + facing * 0.02, z + 1.1), (min(xa, xb), y + facing * 0.02, z + 1.1)],
                         (0, facing, 0), PLASTER, tone)


def house(builder, x0, y0, x1, y1, rng, detail, street_sides):
    width, depth = x1 - x0, y1 - y0
    floors = rng.choice((2, 2, 3, 3, 4))
    height = floors * 3.4 + 0.4
    colour = WALLS[rng.randrange(len(WALLS))]
    roof = ROOFS[rng.randrange(len(ROOFS))]
    court = detail and width > 16.0 and depth > 14.0 and rng.random() < 0.8
    if not detail:
        wall_box(builder, x0, y0, x1, y1, -1.0, height, colour)
        roof_slab(builder, x0, y0, x1, y1, height, roof, detail=False)
        if width > 16.0 and depth > 14.0:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            cw, cd = width * rng.uniform(0.1, 0.17), depth * rng.uniform(0.1, 0.17)
            cx += rng.uniform(-1.5, 1.5)
            court = (0.58, 0.60, 0.44) if rng.random() < 0.5 else (0.66, 0.62, 0.54)
            quad(builder, [(cx - cw, cy - cd, height + 0.02), (cx + cw, cy - cd, height + 0.02),
                           (cx + cw, cy + cd, height + 0.02), (cx - cw, cy + cd, height + 0.02)], (0, 0, 1), PLASTER,
                 court)
        return
    if court:
        wing = min(width, depth) * 0.3
        rects = [(x0, y0, x1, y0 + wing), (x0, y1 - wing, x1, y1), (x0, y0 + wing, x0 + wing, y1 - wing),
                 (x1 - wing, y0 + wing, x1, y1 - wing)]
        for index, (a, b, c, d) in enumerate(rects):
            wall_box(builder, a, b, c, d, -1.0, height - (0.0 if index < 2 else 3.4), colour)
            roof_slab(builder, a, b, c, d, height - (0.0 if index < 2 else 3.4), roof, 0.8, True)
        cx0, cy0, cx1, cy1 = x0 + wing, y0 + wing, x1 - wing, y1 - wing
        floor_colour = (0.46, 0.56, 0.26) if rng.random() < 0.5 else (0.92, 0.86, 0.74)
        quad(builder, [(cx0, cy0, 0.05), (cx1, cy0, 0.05), (cx1, cy1, 0.05), (cx0, cy1, 0.05)], (0, 0, 1), PLASTER,
             floor_colour)
    else:
        wall_box(builder, x0, y0, x1, y1, -1.0, height, colour)
        roof_slab(builder, x0, y0, x1, y1, height, roof, 0.8, True)
    for side, y, facing in (("south", y0, -1), ("north", y1, 1)):
        windows(builder, x0 + 1.0, x1 - 1.0, y + facing * 0.02, facing, height, rng, floors)
        if side in street_sides:
            shopfront(builder, x0, x1, y + facing * 0.03, facing, rng)
        else:
            dx = rng.uniform(x0 + 2.0, x1 - 2.0)
            quad(builder, [(dx - 0.8, y + facing * 0.03, 0.0), (dx + 0.8, y + facing * 0.03, 0.0),
                           (dx + 0.8, y + facing * 0.03, 2.6), (dx - 0.8, y + facing * 0.03, 2.6)], (0, facing, 0),
                 VOID)
    for x, facing in ((x0, -1), (x1, 1)):
        count = max(int(depth / 5.0), 1)
        for floor in range(1, floors):
            z = floor * 3.4 + 0.8
            for k in range(count):
                y = y0 + depth * (k + 0.5) / count
                quad(builder, [(x + facing * 0.02, y - 0.4, z), (x + facing * 0.02, y + 0.4, z),
                               (x + facing * 0.02, y + 0.4, z + 1.1), (x + facing * 0.02, y - 0.4, z + 1.1)],
                     (facing, 0, 0), VOID)
    rooftop(builder, x0, y0, x1, y1, height, rng, court)
    painted(builder, tuple(c * 0.86 for c in colour), lambda: builder.box((x0 - 0.05, y0 - 0.05, -0.5),
                                                                          (x1 + 0.05, y1 + 0.05, 0.9), PLASTER,
                                                                          bottom=False, top=False))


def shopfront(builder, x0, x1, y, facing, rng):
    width = x1 - x0
    count = max(int(width / 4.5), 1)
    for k in range(count):
        x = x0 + width * (k + 0.5) / count
        quad(builder, [(x - 1.3, y, 0.0), (x + 1.3, y, 0.0), (x + 1.3, y, 2.7), (x - 1.3, y, 2.7)], (0, facing, 0),
             VOID)
        if rng.random() < 0.55:
            cloth = CLOTHS[rng.randrange(len(CLOTHS))]
            out = y + facing * 2.2
            awning = [(x - 1.8, y, 3.3), (x + 1.8, y, 3.3), (x + 1.8, out, 2.7), (x - 1.8, out, 2.7)]
            quad(builder, awning, (0, facing * 0.4, 1), MATTE, cloth)
            quad(builder, list(reversed(awning)), (0, -facing * 0.4, -1), MATTE, tuple(c * 0.7 for c in cloth))
        if rng.random() < 0.4:
            tone = rng.choice([(0.72, 0.42, 0.26), (0.86, 0.70, 0.36), (0.55, 0.62, 0.30)])
            painted(builder, tone, lambda x=x: builder.box((x - 1.1, min(y, y + facing * 0.9), 0.0),
                                                           (x + 1.1, max(y, y + facing * 0.9), 0.8), MATTE,
                                                           bottom=False))


def rooftop(builder, x0, y0, x1, y1, height, rng, court):
    width, depth = x1 - x0, y1 - y0
    if rng.random() < 0.45:
        rx0 = x0 + rng.uniform(0.6, width * 0.4)
        ry0 = y0 + rng.uniform(0.6, 3.0)
        rx1 = min(rx0 + rng.uniform(3.0, 5.5), x1 - 0.6)
        ry1 = min(ry0 + rng.uniform(3.0, 4.5), y1 - 0.6)
        colour = WALLS[rng.randrange(len(WALLS))]
        wall_box(builder, rx0, ry0, rx1, ry1, height, height + 2.6, colour)
        roof_slab(builder, rx0, ry0, rx1, ry1, height + 2.6, ROOFS[0], 0.0, False)
        quad(builder, [((rx0 + rx1) / 2 - 0.5, ry0 - 0.02, height), ((rx0 + rx1) / 2 + 0.5, ry0 - 0.02, height),
                       ((rx0 + rx1) / 2 + 0.5, ry0 - 0.02, height + 2.0), ((rx0 + rx1) / 2 - 0.5, ry0 - 0.02, height + 2.0)],
             (0, -1, 0), VOID)
    if rng.random() < 0.4:
        px = x0 + rng.uniform(1.0, max(width - 6.0, 1.2))
        py = y1 - rng.uniform(1.5, 4.0) if not court else y1 - 2.0
        for dx in (0.0, 4.5):
            for dy in (0.0, -2.6):
                tube(builder, [(px + dx, py + dy, height), (px + dx, py + dy, height + 2.4)], [0.06, 0.06], WOOD, 4)
        cloth = CLOTHS[rng.randrange(len(CLOTHS))] if rng.random() < 0.6 else (0.40, 0.55, 0.22)
        quad(builder, [(px - 0.2, py - 2.8, height + 2.4), (px + 4.7, py - 2.8, height + 2.4), (px + 4.7, py + 0.2,
                                                                                               height + 2.4),
                       (px - 0.2, py + 0.2, height + 2.4)], (0, 0, 1), MATTE, cloth)
        quad(builder, [(px - 0.2, py + 0.2, height + 2.39), (px + 4.7, py + 0.2, height + 2.39),
                       (px + 4.7, py - 2.8, height + 2.39), (px - 0.2, py - 2.8, height + 2.39)], (0, 0, -1), MATTE,
             tuple(c * 0.7 for c in cloth))
    for k in range(rng.randrange(0, 2)):
        jx = rng.uniform(x0 + 1.0, x1 - 1.0)
        jy = rng.uniform(y0 + 1.0, y0 + 2.5)
        drape(builder, (0.74, 0.44, 0.28), [(0.0, height), (0.28, height + 0.1), (0.34, height + 0.5),
                                            (0.16, height + 0.85), (0.12, height + 0.95)], 6, folds=(0, 0.0, 0.0),
              squash=1.0, center=(jx, jy))


def house_chunk(seed, detail=True, width=CHUNK[0], depth=CHUNK[1], street=("south",)):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for x0, y0, x1, y1, i, j, columns in lots(rng, width, depth):
        sides = []
        if j == 0 and "south" in street:
            sides.append("south")
        if j == 1 and "north" in street:
            sides.append("north")
        house(builder, x0, y0, x1, y1, random.Random(rng.random()), detail, sides)
    return builder


def colonnade(length=24.0, height=6.4, depth=5.5, count=6, seed=0, detail=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        x = -length / 2 + length * (k + 0.5) / count
        if not detail:
            tube(builder, [(x, 0.0, 0.0), (x, 0.0, height)], [0.36, 0.3], (1.0, 0.98, 0.94), 4, MARBLE, cap=False)
            continue
        tube(builder, [(x, 0.0, 0.0), (x, 0.0, 0.5)], [0.42, 0.42], (0.98, 0.95, 0.9), 5, MARBLE)
        tube(builder, [(x, 0.0, 0.5), (x, 0.0, height - 0.6)], [0.34, 0.29], (1.0, 0.98, 0.94), 6, MARBLE)
        painted(builder, (0.98, 0.95, 0.9), lambda x=x: builder.box((x - 0.45, -0.45, height - 0.6),
                                                                    (x + 0.45, 0.45, height), MARBLE))
    painted(builder, (1.0, 0.96, 0.9), lambda: builder.box((-length / 2, -0.55, height), (length / 2, 0.55,
                                                                                          height + 0.9), MARBLE))
    painted(builder, (0.72, 0.22, 0.14), lambda: builder.box((-length / 2, -0.57, height + 0.35), (length / 2, -0.55,
                                                                                                   height + 0.6), MATTE,
                                                             bottom=False, top=False))
    roof = len(builder.polygons)
    builder.surface([[(-length / 2, -0.5, height + 0.9), (length / 2, -0.5, height + 0.9)],
                     [(-length / 2, depth, height + 2.2), (length / 2, depth, height + 2.2)]], TILES,
                    facing=(0, 0, 1))
    if not detail:
        builder.tint(roof, (0.80, 0.42, 0.28))
    wall = WALLS[rng.randrange(len(WALLS))]
    painted(builder, wall, lambda: builder.box((-length / 2, depth, -0.5), (length / 2, depth + 0.6, height + 2.4),
                                               PLASTER, bottom=False))
    painted(builder, (0.96, 0.93, 0.86), lambda: builder.box((-length / 2, -0.6, -0.4), (length / 2, depth, 0.12),
                                                             PAVING, bottom=False))
    for k in range(count - 1 if detail else 0):
        x = -length / 2 + length * (k + 1) / count
        quad(builder, [(x - 1.2, depth - 0.02, 0.12), (x + 1.2, depth - 0.02, 0.12), (x + 1.2, depth - 0.02, 2.9),
                       (x - 1.2, depth - 0.02, 2.9)], (0, -1, 0), VOID)
    if not detail:
        builder.materials = [PLASTER for _ in builder.materials]
    return builder


def street_slab(length, width, material=PAVING, colour=(1.0, 0.96, 0.9)):
    builder = MeshBuilder()
    painted(builder, colour, lambda: builder.box((-length / 2, -width / 2, -0.3), (length / 2, width / 2, 0.08),
                                                 material, bottom=False))
    painted(builder, (0.92, 0.88, 0.8), lambda: builder.box((-length / 2, -width / 2 - 0.6, -0.3),
                                                            (length / 2, -width / 2, 0.2), STONE, bottom=False))
    painted(builder, (0.92, 0.88, 0.8), lambda: builder.box((-length / 2, width / 2, -0.3),
                                                            (length / 2, width / 2 + 0.6, 0.2), STONE, bottom=False))
    return builder


def frond(builder, base, direction, length, droop, colour, width=0.55, segments=5, detail=True):
    direction = Vector(direction).normalized()
    side = Vector((-direction.y, direction.x, 0.0)).normalized()
    spine = []
    for k in range(segments + 1):
        t = k / segments
        point = base + direction * (length * t) + Vector((0.0, 0.0, length * (0.35 * t - droop * t * t)))
        spine.append(point)
    left = []
    right = []
    middle = []
    for k, point in enumerate(spine):
        t = k / segments
        half = width * math.sin(math.pi * min(t * 1.1 + 0.08, 1.0)) * (1.0 - 0.3 * t)
        middle.append(point)
        left.append(point + side * half + Vector((0.0, 0.0, -half * 0.45)))
        right.append(point - side * half + Vector((0.0, 0.0, -half * 0.45)))
    dark = tuple(c * 0.72 for c in colour)
    first = len(builder.polygons)
    builder.surface([left, middle], MATTE, smooth=True)
    builder.surface([middle, right], MATTE, smooth=True)
    builder.tint(first, colour)
    if detail:
        first = len(builder.polygons)
        builder.surface([middle, left], MATTE, smooth=True)
        builder.surface([right, middle], MATTE, smooth=True)
        builder.tint(first, dark)


def date_palm(height=13.0, seed=0, detail=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    lean = Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 0.0))
    points = []
    radii = []
    for k in range(7):
        t = k / 6
        points.append(Vector((lean.x * t * t, lean.y * t * t, height * t)))
        radii.append(0.3 - 0.08 * t + (0.08 if k == 0 else 0.0))
    bark = (0.52 + rng.uniform(-0.04, 0.04), 0.42, 0.30)
    if not detail:
        points = points[::2]
        radii = radii[::2]
    tube(builder, points, radii, bark, 7 if detail else 4, MATTE, cap=False)
    top = points[-1]
    ellipsoid(builder, top + Vector((0.0, 0.0, 0.2)), (0.42, 0.42, 0.55), (0.46, 0.40, 0.24), 6 if detail else 4,
              3 if detail else 2, MATTE)
    count = 16 if detail else 8
    colour = PALM_GREEN[rng.randrange(len(PALM_GREEN))]
    for k in range(count):
        angle = TAU * k / count + rng.uniform(-0.15, 0.15)
        tier = k % 3
        elevation = (0.65, 0.2, -0.35)[tier]
        direction = (math.cos(angle), math.sin(angle), 0.0)
        length = rng.uniform(3.6, 4.6) * (0.85 if tier == 0 else 1.0)
        tone = tuple(min(1.0, c * rng.uniform(0.88, 1.12)) for c in colour)
        frond(builder, top + Vector((0.0, 0.0, 0.35)), direction, length, 0.55 - elevation * 0.45 + 0.35, tone,
              0.6, 4 if detail else 2, detail)
    if detail and rng.random() < 0.6:
        for k in range(3):
            angle = TAU * k / 3 + rng.uniform(0, 1)
            ellipsoid(builder, top + Vector((0.55 * math.cos(angle), 0.55 * math.sin(angle), -0.5)),
                      (0.22, 0.22, 0.42), (0.86, 0.46, 0.14), 5, 3, MATTE)
    return builder


def broad_tree(height=8.0, seed=0, colour=(0.30, 0.46, 0.18), lobes=6):
    rng = random.Random(seed)
    builder = MeshBuilder()
    trunk_top = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), height * 0.42))
    tube(builder, [(0.0, 0.0, 0.0), trunk_top * 0.6, trunk_top], [0.36, 0.3, 0.22], (0.48, 0.42, 0.34), 6, MATTE)
    for k in range(lobes):
        angle = TAU * k / lobes + rng.uniform(-0.3, 0.3)
        r = height * rng.uniform(0.18, 0.3)
        centre = trunk_top + Vector((r * math.cos(angle), r * math.sin(angle), height * rng.uniform(0.12, 0.32)))
        size = height * rng.uniform(0.2, 0.3)
        tone = tuple(min(1.0, c * rng.uniform(0.85, 1.18)) for c in colour)
        ellipsoid(builder, centre, (size, size, size * 0.72), tone, 7, 4, MATTE)
    ellipsoid(builder, trunk_top + Vector((0.0, 0.0, height * 0.38)), (height * 0.26, height * 0.26, height * 0.2),
              tuple(min(1.0, c * 1.12) for c in colour), 8, 4, MATTE)
    return builder


def shrub(size=1.4, seed=0, colour=(0.30, 0.44, 0.18)):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(3):
        centre = (rng.uniform(-0.4, 0.4) * size, rng.uniform(-0.4, 0.4) * size, size * 0.35)
        tone = tuple(min(1.0, c * rng.uniform(0.85, 1.15)) for c in colour)
        ellipsoid(builder, centre, (size * 0.6, size * 0.55, size * 0.45), tone, 6, 3, MATTE)
    return builder

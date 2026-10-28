import math
import random

from mathutils import Matrix, Vector

from .buildings import arched_wall
from .geometry import MATTE, MeshBuilder, newell_normal, placement

STONE = "sandstone"
ASHLAR = "ashlar"
SLAB = "roof_slab"
TILE = "terracotta_tiles"
TURF = "ground_turf"
TIMBER = "timber"
VOID = "shadow_void"
WALL_HALF = 1.15
WALK = 4.4
PARAPET = 1.0
MERLON = 0.85
CRENEL = 2.6


def quad(builder, corners, normal, material, heights=None, color=None):
    corners = [Vector(c) for c in corners]
    if heights is None:
        heights = [None] * len(corners)
    if newell_normal(corners).dot(Vector(normal)) < 0:
        corners = list(reversed(corners))
        heights = list(reversed(heights))
    indices = [builder.point(c, h) for c, h in zip(corners, heights)]
    builder.face(indices, material, color=color)


def merlon_box(builder, center, tangent, normal, size, material):
    frame = Matrix((tangent, normal, Vector((0.0, 0.0, 1.0)))).transposed().to_4x4()
    frame.translation = Vector(center)
    builder.centered_box((0.0, 0.0, size[2] / 2), size, material, matrix=frame, bottom=False)


def wall_run(builder, stations, outward=1.0, half=WALL_HALF, footing=0.3, crenel=CRENEL, cap_start=True,
             cap_end=True, material=STONE):
    count = len(stations)
    if count < 2:
        return
    frames = []
    for index, (x, y, low, ground, walk) in enumerate(stations):
        a = Vector(stations[max(index - 1, 0)][:2])
        b = Vector(stations[min(index + 1, count - 1)][:2])
        tangent = (b - a).normalized()
        normal = Vector((-tangent.y, tangent.x)) * outward
        frames.append((Vector((x, y)), tangent, normal, low, ground, walk))

    def at(frame, offset, z):
        p, _, n, _, _, _ = frame
        return Vector((p.x + n.x * offset, p.y + n.y * offset, z))
    inner_top = half - 0.62
    for f0, f1 in zip(frames[:-1], frames[1:]):
        n = (f0[2] + f1[2]).normalized()
        n3 = Vector((n.x, n.y, 0.0))
        g0, g1 = f0[4], f1[4]
        w0, w1 = f0[5], f1[5]
        l0, l1 = f0[3], f1[3]
        top0, top1 = w0 + PARAPET, w1 + PARAPET
        quad(builder, [at(f0, half, l0), at(f1, half, l1), at(f1, half, top1), at(f0, half, top0)], n3, material,
             [l0 - g0, l1 - g1, top1 - g1, top0 - g0])
        quad(builder, [at(f0, -half, g0 + 0.32), at(f1, -half, g1 + 0.32), at(f1, -half, w1), at(f0, -half, w0)],
             -n3, material, [0.32, 0.32, w1 - g1, w0 - g0])
        quad(builder, [at(f0, -half - footing, l0), at(f1, -half - footing, l1), at(f1, -half - footing, g1 + 0.32),
                       at(f0, -half - footing, g0 + 0.32)], -n3, material, [l0 - g0, l1 - g1, 0.32, 0.32])
        quad(builder, [at(f0, -half - footing, g0 + 0.32), at(f1, -half - footing, g1 + 0.32),
                       at(f1, -half, g1 + 0.32), at(f0, -half, g0 + 0.32)], (0, 0, 1), material,
             [0.32, 0.32, 0.32, 0.32])
        quad(builder, [at(f0, -half, w0), at(f1, -half, w1), at(f1, inner_top, w1), at(f0, inner_top, w0)],
             (0, 0, 1), material, [3.0] * 4, color=(0.86, 0.84, 0.80))
        quad(builder, [at(f0, inner_top, w0), at(f1, inner_top, w1), at(f1, inner_top, top1), at(f0, inner_top, top0)],
             -n3, material, [3.0] * 4)
        quad(builder, [at(f0, inner_top, top0), at(f1, inner_top, top1), at(f1, half, top1), at(f0, half, top0)],
             (0, 0, 1), material, [3.0] * 4)
    for frame, cap, sign in ((frames[0], cap_start, -1.0), (frames[-1], cap_end, 1.0)):
        if not cap:
            continue
        t = Vector((frame[1].x, frame[1].y, 0.0)) * sign
        low, ground, walk = frame[3], frame[4], frame[5]
        quad(builder, [at(frame, -half - footing, low), at(frame, half, low), at(frame, half, walk + PARAPET),
                       at(frame, inner_top, walk + PARAPET), at(frame, inner_top, walk), at(frame, -half, walk),
                       at(frame, -half, ground + 0.32), at(frame, -half - footing, ground + 0.32)], t, material)
    travelled = 0.0
    next_merlon = crenel * 0.5
    for f0, f1 in zip(frames[:-1], frames[1:]):
        length = (f1[0] - f0[0]).length
        while next_merlon < travelled + length:
            t = (next_merlon - travelled) / max(length, 1e-6)
            p = f0[0].lerp(f1[0], t)
            walk = f0[5] + (f1[5] - f0[5]) * t
            tangent = Vector((f0[1].x, f0[1].y, 0.0))
            normal = Vector((f0[2].x, f0[2].y, 0.0))
            center = Vector((p.x, p.y, walk + PARAPET)) + normal * (half - 0.31)
            merlon_box(builder, center, tangent, normal, (crenel * 0.48, 0.62, MERLON), material)
            next_merlon += crenel
        travelled += length


def rampart_run(builder, stations, outward=1.0, width=6.5):
    count = len(stations)
    rows = []
    for index, (x, y, low, ground, walk) in enumerate(stations):
        a = Vector(stations[max(index - 1, 0)][:2])
        b = Vector(stations[min(index + 1, count - 1)][:2])
        tangent = (b - a).normalized()
        n = Vector((-tangent.y, tangent.x)) * outward
        p = Vector((x, y))
        inner = ground
        rows.append([Vector((p.x - n.x * 1.0, p.y - n.y * 1.0, walk - 1.2)),
                     Vector((p.x - n.x * 3.2, p.y - n.y * 3.2, walk - 1.5)),
                     Vector((p.x - n.x * width, p.y - n.y * width, inner - 0.4))])
    for r0, r1 in zip(rows[:-1], rows[1:]):
        for k in range(2):
            quad(builder, [r0[k], r1[k], r1[k + 1], r0[k + 1]], (0, 0, 1), TURF, [2.0, 2.0, 0.2, 0.2])


def crenellated_box(builder, x0, x1, y0, y1, z0, z1, material=STONE, merlons=True, slits=()):
    builder.box((x0, y0, z0), (x1, y1, z1), material, bottom=False)
    if merlons:
        for (ax, ay), (bx, by), normal in (((x0, y1), (x1, y1), (0, 1)), ((x1, y0), (x0, y0), (0, -1)),
                                           ((x0, y0), (x0, y1), (-1, 0)), ((x1, y1), (x1, y0), (1, 0))):
            length = math.hypot(bx - ax, by - ay)
            count = max(int(length / 2.2), 1)
            tangent = Vector(((bx - ax) / length, (by - ay) / length, 0.0))
            n = Vector((normal[0], normal[1], 0.0))
            for k in range(count):
                t = (k + 0.5) / count
                center = Vector((ax + (bx - ax) * t, ay + (by - ay) * t, z1)) - n * 0.3
                merlon_box(builder, center, tangent, n, (length / count * 0.5, 0.55, 0.8), material)
    for x, y, z, normal in slits:
        if abs(normal[0]) > 0.5:
            builder.oriented([(x, y - 0.18, z), (x, y + 0.18, z), (x, y + 0.18, z + 0.9), (x, y - 0.18, z + 0.9)],
                             normal, VOID)
        else:
            builder.oriented([(x - 0.18, y, z), (x + 0.18, y, z), (x + 0.18, y, z + 0.9), (x - 0.18, y, z + 0.9)],
                             normal, VOID)


def gate(depth_below=4.0, walk=WALK + 0.4):
    builder = MeshBuilder()
    front, back = 3.0, -3.6
    for side in (-1, 1):
        x0, x1 = sorted((side * 4.6, side * 10.0))
        crenellated_box(builder, x0, x1, back, front, -depth_below, walk + 4.4,
                        slits=[((x0 + x1) / 2, front + 0.01, walk + 1.6, (0, 1, 0)),
                               ((x0 + x1) / 2, back - 0.01, walk + 1.6, (0, -1, 0)),
                               ((x0 + x1) / 2, front + 0.01, 2.6, (0, 1, 0))])
        builder.oriented([((x0 + x1) / 2 - 0.5, back - 0.01, 0.0), ((x0 + x1) / 2 + 0.5, back - 0.01, 0.0),
                          ((x0 + x1) / 2 + 0.5, back - 0.01, 2.0), ((x0 + x1) / 2 - 0.5, back - 0.01, 2.0)],
                         (0, -1, 0), VOID)
    arched_wall(builder, -4.6, 4.6, back, front, 0.0, walk + 0.6, [(-2.3, 1.7, 2.9), (2.3, 1.7, 2.9)], ASHLAR,
                segments=8, foundation=depth_below)
    builder.box((-4.6, back, walk + 0.6), (4.6, front, walk + 0.9), STONE, bottom=False)
    for k in range(4):
        x = -4.6 + 1.15 + k * 2.3
        merlon_box(builder, (x, front - 0.3, walk + 0.9), Vector((1, 0, 0)), Vector((0, 1, 0)), (1.1, 0.55, 0.8),
                   STONE)
    builder.box((-0.6, back, -depth_below), (0.6, front, 0.05), ASHLAR, top=False, bottom=False)
    for x in (-2.3, 2.3):
        builder.box((x - 1.7, back + 0.4, -0.05), (x + 1.7, front - 0.4, 0.06), ASHLAR, bottom=False)
    return builder


def tower(width=4.8, depth=5.2, walk=WALK, outside=WALL_HALF, depth_below=4.0):
    builder = MeshBuilder()
    crenellated_box(builder, -width / 2, width / 2, outside - depth, outside, -depth_below, walk + 3.6,
                    slits=[(0.0, outside + 0.01, walk + 1.0, (0, 1, 0)), (0.0, outside - depth - 0.01, walk + 1.0,
                                                                          (0, -1, 0))])
    builder.oriented([(-0.5, outside - depth - 0.01, 0.0), (0.5, outside - depth - 0.01, 0.0),
                      (0.5, outside - depth - 0.01, 2.0), (-0.5, outside - depth - 0.01, 2.0)], (0, -1, 0), VOID)
    return builder


def hipped_roof(builder, x0, x1, y0, y1, z, rise, material, overhang=0.35):
    x0, x1, y0, y1 = x0 - overhang, x1 + overhang, y0 - overhang, y1 + overhang
    z = z - overhang * rise / max((y1 - y0) / 2, 0.1)
    span = min(x1 - x0, y1 - y0) / 2
    top = z + rise
    if x1 - x0 >= y1 - y0:
        ra = Vector((x0 + span, (y0 + y1) / 2, top))
        rb = Vector((x1 - span, (y0 + y1) / 2, top))
    else:
        ra = Vector(((x0 + x1) / 2, y0 + span, top))
        rb = Vector(((x0 + x1) / 2, y1 - span, top))
    c = [Vector((x0, y0, z)), Vector((x1, y0, z)), Vector((x1, y1, z)), Vector((x0, y1, z))]
    if x1 - x0 >= y1 - y0:
        builder.oriented([c[0], c[1], rb, ra], (0, -1, 1), material)
        builder.oriented([c[2], c[3], ra, rb], (0, 1, 1), material)
        builder.oriented([c[1], c[2], rb], (1, 0, 1), material)
        builder.oriented([c[3], c[0], ra], (-1, 0, 1), material)
    else:
        builder.oriented([c[1], c[2], rb, ra], (1, 0, 1), material)
        builder.oriented([c[3], c[0], ra, rb], (-1, 0, 1), material)
        builder.oriented([c[0], c[1], ra], (0, -1, 1), material)
        builder.oriented([c[2], c[3], rb], (0, 1, 1), material)


def gable_roof(builder, x0, x1, y0, y1, z, rise, material, wall=STONE, overhang=0.4):
    ridge = (y0 + y1) / 2
    top = z + rise
    for edge in (y0 - overhang, y1 + overhang):
        drop = rise * overhang / ((y1 - y0) / 2)
        builder.oriented([(x0 - overhang, edge, z - drop), (x1 + overhang, edge, z - drop), (x1 + overhang, ridge, top),
                          (x0 - overhang, ridge, top)], (0, edge - ridge, 1), material)
    for x, sign in ((x0, -1), (x1, 1)):
        builder.oriented([(x, y0, z), (x, y1, z), (x, ridge, top)], (sign, 0, 0), wall)


def turret(walk=WALK, depth_below=5.0):
    builder = MeshBuilder()
    outside = WALL_HALF
    builder.box((-3.0, outside - 5.9, -depth_below), (3.0, outside, walk + 3.4), STONE, bottom=False, top=False)
    hipped_roof(builder, -3.0, 3.0, outside - 5.9, outside, walk + 3.4, 1.6, SLAB)
    builder.oriented([(-0.5, outside - 5.91, 0.0), (0.5, outside - 5.91, 0.0), (0.5, outside - 5.91, 1.9),
                      (-0.5, outside - 5.91, 1.9)], (0, -1, 0), VOID)
    for x in (-1.2, 1.2):
        builder.oriented([(x - 0.25, outside + 0.01, walk + 1.4), (x + 0.25, outside + 0.01, walk + 1.4),
                          (x + 0.25, outside + 0.01, walk + 2.4), (x - 0.25, outside + 0.01, walk + 2.4)], (0, 1, 0),
                         VOID)
    builder.oriented([(-0.3, outside - 5.91, walk + 1.4), (0.3, outside - 5.91, walk + 1.4),
                      (0.3, outside - 5.91, walk + 2.4), (-0.3, outside - 5.91, walk + 2.4)], (0, -1, 0), VOID)
    for y in (outside - 4.4, outside - 1.4):
        for x, n in ((3.0, (1, 0, 0)), (-3.0, (-1, 0, 0))):
            builder.oriented([(x + 0.01 * n[0], y - 0.25, walk + 1.4), (x + 0.01 * n[0], y + 0.25, walk + 1.4),
                              (x + 0.01 * n[0], y + 0.25, walk + 2.4), (x + 0.01 * n[0], y - 0.25, walk + 2.4)], n,
                             VOID)
    return builder


def milecastle(walk=WALK, depth_below=5.0):
    builder = MeshBuilder()
    outside = WALL_HALF
    half_x = 8.75
    south = outside - 15.1
    thick = 2.5
    for x0, x1 in ((-half_x, -half_x + thick), (half_x - thick, half_x)):
        builder.box((x0, south, -depth_below), (x1, outside - 2.0, walk), STONE, bottom=False)
        builder.box((x0 if x0 < 0 else x1 - 0.6, south, walk), (x0 + 0.6 if x0 < 0 else x1, outside - 2.0,
                                                                walk + PARAPET), STONE, bottom=False)
    for x0, x1 in ((-half_x, -1.6), (1.6, half_x)):
        builder.box((x0, south, -depth_below), (x1, south + thick, walk), STONE, bottom=False)
        builder.box((x0, south, walk), (x1, south + 0.6, walk + PARAPET), STONE, bottom=False)
    arched_wall(builder, -1.6, 1.6, south, south + thick, 0.0, walk, [(0.0, 1.4, 2.6)], ASHLAR, segments=8)
    builder.box((-1.6, south, walk), (1.6, south + 0.6, walk + PARAPET), STONE, bottom=False)
    for k in range(6):
        x = -half_x + 1.2 + k * 3.0
        if abs(x) < 1.8:
            continue
        merlon_box(builder, (x, south + 0.3, walk + PARAPET), Vector((-1, 0, 0)), Vector((0, -1, 0)),
                   (1.1, 0.55, 0.8), STONE)
    for side in (-1, 1):
        for k in range(4):
            y = south + 1.5 + k * 3.3
            merlon_box(builder, (side * (half_x - 0.3), y, walk + PARAPET), Vector((0, side, 0)),
                       Vector((side, 0, 0)), (1.1, 0.55, 0.8), STONE)
    arched_wall(builder, -3.3, 3.3, outside - 3.6, outside + 0.05, -depth_below, walk + 0.4, [(0.0, 1.5, 2.8)],
                ASHLAR, segments=8, foundation=0.0)
    crenellated_box(builder, -3.3, 3.3, outside - 3.6, outside + 0.05, walk + 0.4, walk + 3.6,
                    slits=[(0.0, outside + 0.06, walk + 1.4, (0, 1, 0)), (0.0, outside - 3.61, walk + 1.4, (0, -1, 0))])
    bx0, bx1, by0, by1 = 0.6, half_x - thick - 0.2, south + thick + 0.8, outside - 3.0
    builder.box((bx0, by0, -0.5), (bx1, by1, 2.8), STONE, bottom=False, top=False)
    gable_roof(builder, bx0, bx1, by0, by1, 2.8, 1.5, SLAB)
    for y in (by0 + 1.8, by0 + 5.2):
        builder.oriented([(bx0 - 0.01, y - 0.45, 0.0), (bx0 - 0.01, y + 0.45, 0.0), (bx0 - 0.01, y + 0.45, 1.9),
                          (bx0 - 0.01, y - 0.45, 1.9)], (-1, 0, 0), VOID)
    builder.box((-half_x + thick + 0.5, south + thick + 0.5, -0.3), (-1.0, outside - 3.5, 0.05), "matte",
                bottom=False)
    builder.tint(len(builder.polygons) - 5, (0.58, 0.54, 0.44))
    return builder


def barrack(length, width=8.6, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    head = 13.0
    hw = width / 2
    body_x1 = length - head
    builder.box((0.0, -hw, -2.5), (body_x1, hw, 2.9), STONE, bottom=False, top=False)
    gable_roof(builder, 0.0, body_x1, -hw, hw, 2.9, 2.0, SLAB)
    builder.box((body_x1, -hw - 0.8, -2.5), (length, hw + 0.4, 3.6), STONE, bottom=False, top=False)
    gable_roof(builder, body_x1, length, -hw - 0.8, hw + 0.4, 3.6, 2.3, SLAB)
    rooms = max(int(body_x1 / 4.4), 2)
    for k in range(rooms):
        x = (k + 0.5) * body_x1 / rooms
        builder.oriented([(x - 0.5, hw + 0.01, 0.0), (x + 0.5, hw + 0.01, 0.0), (x + 0.5, hw + 0.01, 1.95),
                          (x - 0.5, hw + 0.01, 1.95)], (0, 1, 0), VOID)
        builder.oriented([(x + 1.1, hw + 0.01, 1.7), (x + 1.5, hw + 0.01, 1.7), (x + 1.5, hw + 0.01, 2.3),
                          (x + 1.1, hw + 0.01, 2.3)], (0, 1, 0), VOID)
    for k in range(rooms + 1):
        x = k * body_x1 / rooms
        builder.box((x - 0.1, hw + 1.9, 0.0), (x + 0.1, hw + 2.1, 2.4), TIMBER, bottom=False)
    builder.oriented([(0.0, hw, 2.85), (body_x1, hw, 2.85), (body_x1, hw + 2.3, 2.35), (0.0, hw + 2.3, 2.35)],
                     (0, 0.2, 1), SLAB)
    builder.oriented([(0.0, hw, 2.8), (body_x1, hw, 2.8), (body_x1, hw + 2.3, 2.3), (0.0, hw + 2.3, 2.3)],
                     (0, 0, -1), TIMBER)
    for x in (body_x1 + 3.0, body_x1 + 8.0):
        builder.oriented([(x - 0.5, hw + 0.41, 0.0), (x + 0.5, hw + 0.41, 0.0), (x + 0.5, hw + 0.41, 2.1),
                          (x - 0.5, hw + 0.41, 2.1)], (0, 1, 0), VOID)
        builder.oriented([(x - 0.3, -hw - 0.81, 2.0), (x + 0.3, -hw - 0.81, 2.0), (x + 0.3, -hw - 0.81, 2.8),
                          (x - 0.3, -hw - 0.81, 2.8)], (0, -1, 0), VOID)
    return builder


def granary(length=27.0, width=9.4):
    builder = MeshBuilder()
    hw = width / 2
    builder.box((0.0, -hw, -2.5), (length, hw, 6.2), STONE, bottom=False, top=False)
    gable_roof(builder, 0.0, length, -hw - 0.9, hw + 0.9, 6.2, 2.6, SLAB, overhang=0.3)
    bays = int(length / 3.0)
    for k in range(bays + 1):
        x = k * length / bays
        for side in (-1, 1):
            builder.box((x - 0.4, side * hw - (0.0 if side > 0 else 0.75), -2.5),
                        (x + 0.4, side * hw + (0.75 if side > 0 else 0.0), 5.6), STONE, bottom=False)
        if k < bays:
            for side in (-1, 1):
                xc = x + length / bays / 2
                y = side * (hw + 0.01)
                builder.oriented([(xc - 0.3, y, 0.25), (xc + 0.3, y, 0.25), (xc + 0.3, y, 0.6), (xc - 0.3, y, 0.6)],
                                 (0, side, 0), VOID)
    builder.box((length, -2.4, -2.5), (length + 2.6, 2.4, 1.1), ASHLAR, bottom=False)
    builder.oriented([(length + 0.01, -1.0, 1.1), (length + 0.01, 1.0, 1.1), (length + 0.01, 1.0, 3.3),
                      (length + 0.01, -1.0, 3.3)], (1, 0, 0), VOID)
    for y in (-2.0, 2.0):
        builder.box((length + 2.2, y - 0.2, 1.1), (length + 2.6, y + 0.2, 4.6), TIMBER, bottom=False)
    builder.oriented([(length, -2.6, 4.9), (length + 2.9, -2.6, 4.4), (length + 2.9, 2.6, 4.4), (length, 2.6, 4.9)],
                     (1, 0, 1), SLAB)
    return builder


def courtyard_ranges(builder, x0, x1, y0, y1, cx0, cx1, cy0, cy1, height, rise, roof):
    wings = [(x0, x1, y0, cy0), (x0, x1, cy1, y1), (x0, cx0, cy0, cy1), (cx1, x1, cy0, cy1)]
    for a, b, c, d in wings:
        builder.box((a, c, -2.5), (b, d, height), STONE, bottom=False, top=False)
    for a, b, c, d in wings[:2]:
        gable_roof(builder, a, b, c, d, height, rise, roof, overhang=0.3)
    for a, b, c, d in wings[2:]:
        mid = (a + b) / 2
        for edge in (a, b):
            builder.oriented([(edge, c, height), (edge, d, height), (mid, d, height + rise * (b - a) / (d - c + b - a)
                                                                     * 2), (mid, c, height + rise * (b - a) /
                                                                            (d - c + b - a) * 2)],
                             (edge - mid, 0, 1), roof)
    builder.box((cx0, cy0, -0.3), (cx1, cy1, 0.06), "matte", bottom=False)
    builder.tint(len(builder.polygons) - 5, (0.66, 0.62, 0.52))


def colonnade(builder, x0, x1, y0, y1, height, spacing=3.0):
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        length = math.hypot(bx - ax, by - ay)
        count = max(int(length / spacing), 1)
        for k in range(count + 1):
            t = k / count
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            builder.lathe([(0.24, 0.0), (0.2, 0.25), (0.17, height - 0.3), (0.26, height)], 6, ASHLAR, smooth=True,
                          matrix=placement(x, y, 0.0))


def principia():
    builder = MeshBuilder()
    x0, x1, y0, y1 = -19.0, 17.0, -13.5, 13.5
    courtyard_ranges(builder, 1.0, x1, y0, y1, 4.0, 14.0, -9.5, 9.5, 4.2, 1.8, TILE)
    builder.oriented([(x1 + 0.01, -1.6, 0.0), (x1 + 0.01, 1.6, 0.0), (x1 + 0.01, 1.6, 3.4), (x1 + 0.01, -1.6, 3.4)],
                     (1, 0, 0), VOID)
    builder.box((x1 - 6.0, -2.2, 4.2), (x1 + 0.3, 2.2, 5.6), STONE, bottom=False)
    gable_roof(builder, x1 - 6.0, x1 + 0.3, -2.4, 2.4, 5.6, 1.3, TILE)
    colonnade(builder, 4.4, 13.6, -9.1, 9.1, 3.6)
    builder.oriented([(4.0, -9.5, 3.9), (4.0, 9.5, 3.9), (5.6, 9.5, 3.4), (5.6, -9.5, 3.4)], (1, 0, 1), TILE)
    builder.box((-10.0, y0, -2.5), (1.0, y1, 8.6), STONE, bottom=False, top=False)
    gable_roof(builder, -10.0, 1.0, y0, y1, 8.6, 3.8, TILE)
    for k in range(5):
        y = y0 + (k + 0.5) * (y1 - y0) / 5
        builder.oriented([(1.01, y - 0.4, 6.4), (1.01, y + 0.4, 6.4), (1.01, y + 0.4, 7.8), (1.01, y - 0.4, 7.8)],
                         (1, 0, 0), VOID)
    builder.box((x0, y0, -2.5), (-10.0, y1, 4.6), STONE, bottom=False, top=False)
    gable_roof(builder, x0, -10.0, y0 - 0.3, y1 + 0.3, 4.6, 1.6, TILE)
    builder.box((x0 - 2.2, -3.0, -2.5), (x0, 3.0, 5.0), STONE, bottom=False, top=False)
    hipped_roof(builder, x0 - 2.2, x0, -3.0, 3.0, 5.0, 1.0, TILE, 0.2)
    return builder


def courtyard_building(width, depth, court_w, court_d, height, roof, door_side=1):
    builder = MeshBuilder()
    hx, hy = width / 2, depth / 2
    cx, cy = court_w / 2, court_d / 2
    courtyard_ranges(builder, -hx, hx, -hy, hy, -cx, cx, -cy, cy, height, 1.7, roof)
    builder.oriented([(door_side * hx + 0.01 * door_side, -1.2, 0.0), (door_side * hx + 0.01 * door_side, 1.2, 0.0),
                      (door_side * hx + 0.01 * door_side, 1.2, 2.8), (door_side * hx + 0.01 * door_side, -1.2, 2.8)],
                     (door_side, 0, 0), VOID)
    for k in range(int(width / 4.0)):
        x = -hx + (k + 0.5) * width / int(width / 4.0)
        for side in (-1, 1):
            y = side * (hy + 0.01)
            builder.oriented([(x - 0.3, y, height - 1.6), (x + 0.3, y, height - 1.6), (x + 0.3, y, height - 0.8),
                              (x - 0.3, y, height - 0.8)], (0, side, 0), VOID)
    return builder


def latrine():
    builder = MeshBuilder()
    builder.box((-6.0, -3.2, -2.0), (6.0, 3.2, 3.2), STONE, bottom=False, top=False)
    gable_roof(builder, -6.0, 6.0, -3.2, 3.2, 3.2, 1.4, SLAB)
    builder.oriented([(-0.6, 3.21, 0.0), (0.6, 3.21, 0.0), (0.6, 3.21, 2.0), (-0.6, 3.21, 2.0)], (0, 1, 0), VOID)
    builder.box((-5.0, 4.2, -0.6), (-1.8, 6.4, 0.9), ASHLAR, bottom=False)
    builder.box((-4.8, 4.4, 0.6), (-2.0, 6.2, 0.85), "water", bottom=False)
    return builder


def workshop(length=14.0, width=7.0):
    builder = MeshBuilder()
    builder.box((-length / 2, -width / 2, -2.0), (length / 2, width / 2, 3.0), STONE, bottom=False, top=False)
    gable_roof(builder, -length / 2, length / 2, -width / 2, width / 2, 3.0, 1.6, SLAB)
    builder.oriented([(-1.4, width / 2 + 0.01, 0.0), (1.4, width / 2 + 0.01, 0.0), (1.4, width / 2 + 0.01, 2.4),
                      (-1.4, width / 2 + 0.01, 2.4)], (0, 1, 0), VOID)
    return builder


def tent(color=(0.62, 0.46, 0.30)):
    builder = MeshBuilder()
    w, d, h = 1.6, 1.8, 1.9
    first = len(builder.polygons)
    for side in (-1, 1):
        builder.oriented([(-d, side * w, 0.0), (d, side * w, 0.0), (d, side * 0.2, h), (-d, side * 0.2, h)],
                         (0, side, 0.4), MATTE)
    builder.oriented([(-d, -0.2, h), (d, -0.2, h), (d, 0.2, h), (-d, 0.2, h)], (0, 0, 1), MATTE)
    for x, sign in ((-d, -1), (d, 1)):
        builder.oriented([(x, -w, 0.0), (x, w, 0.0), (x, 0.2, h), (x, -0.2, h)], (sign, 0, 0), MATTE)
    builder.tint(first, color)
    builder.oriented([(d + 0.01, -0.5, 0.0), (d + 0.01, 0.5, 0.0), (d + 0.01, 0.1, 1.5), (d + 0.01, -0.1, 1.5)],
                     (1, 0, 0), VOID)
    return builder


def stone_stack(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for layer in range(3):
        for k in range(4 - layer):
            x = -0.9 + k * 0.5 + layer * 0.25 + rng.uniform(-0.04, 0.04)
            for j in range(2):
                y = -0.25 + j * 0.5
                first = len(builder.polygons)
                builder.box((x - 0.22, y - 0.2, layer * 0.25), (x + 0.22, y + 0.2, layer * 0.25 + 0.23), MATTE)
                builder.tint(first, tuple(c * rng.uniform(0.85, 1.05) for c in (0.78, 0.71, 0.58)))
    return builder


def peat_stack(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    first = len(builder.polygons)
    for layer in range(4):
        for k in range(5 - layer):
            x = -1.0 + k * 0.42 + layer * 0.21
            builder.box((x - 0.18, -0.6, layer * 0.18), (x + 0.18, 0.6, layer * 0.18 + 0.16), MATTE)
    builder.tint(first, (0.24, 0.17, 0.11))
    return builder


def lime_kiln():
    builder = MeshBuilder()
    builder.lathe([(2.2, -1.0), (2.2, 1.6), (1.6, 2.2), (0.9, 2.3)], 10, STONE, smooth=False)
    builder.lathe([(0.9, 2.3), (0.7, 1.4), (0.0, 1.3)], 10, VOID, smooth=False)
    builder.oriented([(-0.5, 2.21, 0.0), (0.5, 2.21, 0.0), (0.5, 2.21, 1.0), (-0.5, 2.21, 1.0)], (0, 1, 0), VOID)
    return builder

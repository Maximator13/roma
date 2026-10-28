import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import Look, drape, ellipsoid, person, tube
from .orders import column

MARBLE = "marble_white"
ASHLAR = "limestone"
FRIEZE = "frieze"
GILT = "bronze_gilt"
WARM = (1.0, 0.95, 0.88)
ASHLAR_TINT = (1.0, 0.96, 0.9)
PAINT_RED = (0.70, 0.18, 0.12)
PAINT_BLUE = (0.16, 0.32, 0.64)
PAINT_GOLD = (0.88, 0.66, 0.26)
LION = (1.0, 0.95, 0.88)
PODIUM_TINT = (0.97, 0.93, 0.85)
STEPS = [(20.0, 17.0, 0.0, 0.36), (19.6, 16.6, 0.36, 0.72)]
TIERS = [(19.2, 16.2, 0.72, 5.6), (18.2, 15.2, 5.6, 11.2), (17.2, 14.2, 11.2, 15.7)]
PLATFORM = (17.2, 14.2, 15.7, 16.2)
COLUMN_X = [-15.0 + 3.0 * k for k in range(11)]
COLUMN_Y = [-12.0 + 3.0 * k for k in range(9)]
DIAMETER = 1.08
STYLOBATE = 16.45
COLUMN_HEIGHT = 9.4
CAPITAL_TOP = STYLOBATE + COLUMN_HEIGHT
PYRAMID_BASE = 27.65
PYRAMID_STEPS = 24
PYRAMID_RISE = 11.1 / PYRAMID_STEPS
PYRAMID_TOP = PYRAMID_BASE + PYRAMID_STEPS * PYRAMID_RISE
PEDESTAL_TOP = PYRAMID_TOP + 1.3
FRIEZE_Z = (14.0, 14.9)


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def ccw(hx, hy):
    return [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]


def path3(hx, hy, z):
    return [(x, y, z) for x, y in ccw(hx, hy)]


def block(builder, hx, hy, z0, z1, material, colour, bottom=False):
    painted(builder, colour, lambda: builder.prism(ccw(hx, hy), z0, z1, material, top=True, bottom=bottom))


def moulding(builder, hx, hy, z, profile, material, colour):
    painted(builder, colour, lambda: builder.sweep(path3(hx, hy, z), profile, material, closed=True))


def band(builder, hx, hy, z0, z1, material, out=0.04, tile=None):
    height = z1 - z0
    repeat = tile or height * 8.0
    corners = [Vector((x, y, 0.0)) for x, y in ccw(hx + out, hy + out)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        length = (b - a).length
        quad = [(a.x, a.y, z0), (b.x, b.y, z0), (b.x, b.y, z1), (a.x, a.y, z1)]
        start = (a.x + a.y) * 0.37 % 1.0
        uvs = [(start, 0.0), (start + length / repeat, 0.0), (start + length / repeat, 1.0), (start, 1.0)]
        builder.face(builder.points(quad), material, uvs=uvs)


def cornice(builder, hx, hy, z, scale=1.0):
    s = scale
    moulding(builder, hx, hy, z, [(-0.4, 0.0), (0.0, 0.0), (0.06 * s, 0.05 * s), (0.1 * s, 0.14 * s), (0.1 * s, 0.2 * s)],
             MARBLE, WARM)
    moulding(builder, hx, hy, z + 0.2 * s, [(0.1 * s - 0.4, 0.0), (0.1 * s, 0.0), (0.14 * s, 0.06 * s), (0.18 * s, 0.14 * s)],
             MATTE, PAINT_BLUE)
    moulding(builder, hx, hy, z + 0.34 * s, [(0.18 * s - 0.4, 0.0), (0.18 * s, 0.0), (0.44 * s, 0.02 * s),
                                             (0.5 * s, 0.06 * s), (0.5 * s, 0.24 * s)], MARBLE, WARM)
    moulding(builder, hx, hy, z + 0.58 * s, [(0.5 * s - 0.5, 0.0), (0.5 * s, 0.0), (0.5 * s, 0.04 * s),
                                             (0.47 * s, 0.06 * s)], MATTE, PAINT_RED)
    moulding(builder, hx, hy, z + 0.64 * s, [(0.47 * s - 0.5, 0.0), (0.47 * s, 0.0), (0.56 * s, 0.08 * s),
                                             (0.58 * s, 0.16 * s), (0.5 * s - 0.5, 0.16 * s)], MARBLE, WARM)


def base_moulding(builder, hx, hy, z, scale=1.0):
    s = scale
    moulding(builder, hx, hy, z, [(-0.3, 0.0), (0.24 * s, 0.0), (0.24 * s, 0.12 * s), (0.2 * s, 0.2 * s),
                                  (0.12 * s, 0.26 * s), (0.04 * s, 0.32 * s), (0.0, 0.4 * s)], MARBLE, WARM)


def podium(builder):
    for hx, hy, z0, z1 in STEPS:
        block(builder, hx, hy, z0 - 1.2, z1, MARBLE, (0.90, 0.86, 0.78))
    for index, (hx, hy, z0, z1) in enumerate(TIERS):
        block(builder, hx, hy, z0 - (1.0 if index == 0 else 0.0), z1, MARBLE, PODIUM_TINT)
        joints(builder, hx, hy, z0, z1)
        base_moulding(builder, hx, hy, z0, 1.0 if index else 1.3)
        if index < 2:
            cornice(builder, hx, hy, z1 - 0.58, 0.8)
    hx, hy, z0, z1 = TIERS[2]
    band(builder, hx, hy, FRIEZE_Z[0], FRIEZE_Z[1], FRIEZE, 0.06)
    moulding(builder, hx, hy, FRIEZE_Z[0] - 0.12, [(-0.2, 0.0), (0.1, 0.0), (0.12, 0.06), (0.1, 0.12)], MARBLE, WARM)
    cornice(builder, hx, hy, FRIEZE_Z[1], 1.0)
    phx, phy, pz0, pz1 = PLATFORM
    block(builder, phx - 0.05, phy - 0.05, pz0, pz1, MARBLE, WARM)
    block(builder, 16.0, 13.0, pz1, STYLOBATE, MARBLE, WARM)


def joints(builder, hx, hy, z0, z1, course=0.9):
    z = z0 + course
    while z < z1 - 0.3:
        band(builder, hx, hy, z - 0.025, z + 0.025, MARBLE, 0.006, 1.0)
        builder.tint(len(builder.polygons) - 4, (0.74, 0.70, 0.64))
        z += course


def column_frames():
    frames = []
    for x in COLUMN_X:
        for y in COLUMN_Y:
            if x in (COLUMN_X[0], COLUMN_X[-1]) or y in (COLUMN_Y[0], COLUMN_Y[-1]):
                frames.append(Matrix.Translation((x, y, STYLOBATE)))
    return frames


def pteron_column():
    return column("ionic", DIAMETER, COLUMN_HEIGHT, detail="high", material=MARBLE)


def entablature(builder):
    hx, hy = 15.0 - 3.0 * 0.82, 12.0 - 3.0 * 0.82
    block(builder, hx, hy, STYLOBATE, CAPITAL_TOP, ASHLAR, ASHLAR_TINT)
    band(builder, hx, hy, CAPITAL_TOP - 0.95, CAPITAL_TOP, FRIEZE, 0.03)
    moulding(builder, hx, hy, STYLOBATE, [(-0.2, 0.0), (0.12, 0.0), (0.12, 0.18), (0.04, 0.3)], MARBLE, WARM)
    z = CAPITAL_TOP
    for k, (grow, height) in enumerate(((0.0, 0.26), (0.05, 0.3), (0.1, 0.34))):
        block(builder, 15.45 + grow, 12.45 + grow, z, z + height, MARBLE, WARM, bottom=(k == 0))
        z += height
    painted(builder, PAINT_BLUE, lambda: builder.polygon(
        [(x, y, CAPITAL_TOP - 0.01) for x, y in reversed(ccw(15.0, 12.0))], MATTE))
    moulding(builder, 15.55, 12.55, z, [(-0.3, 0.0), (0.0, 0.0), (0.05, 0.04), (0.08, 0.1)], MATTE, PAINT_RED)
    z += 0.1
    block(builder, 15.6, 12.6, z, z + 0.3, MARBLE, WARM)
    for side in range(4):
        horizontal = side % 2 == 0
        half = 15.6 if horizontal else 12.6
        other = (12.6 if horizontal else 15.6) * (1 if side < 2 else -1)
        count = int(2 * half / 0.32)
        for k in range(count):
            t = -half + (k + 0.5) * 2 * half / count
            if horizontal:
                p0 = (t - 0.07, other - 0.0 if other > 0 else other - 0.16, z + 0.04)
                p1 = (t + 0.07, other + 0.16 if other > 0 else other, z + 0.26)
            else:
                p0 = (other - 0.0 if other > 0 else other - 0.16, t - 0.07, z + 0.04)
                p1 = (other + 0.16 if other > 0 else other, t + 0.07, z + 0.26)
            painted(builder, WARM, lambda p0=p0, p1=p1: builder.box(p0, p1, MARBLE, bottom=False))
    z += 0.3
    cornice(builder, 15.6, 12.6, z - 0.02, 0.9)
    return z + 0.68


def pyramid(builder, z):
    hx, hy = 15.9, 12.9
    top_x, top_y = 3.6, 2.6
    dx = (hx - top_x) / PYRAMID_STEPS
    dy = (hy - top_y) / PYRAMID_STEPS
    rng = random.Random(24)
    for k in range(PYRAMID_STEPS):
        tone = 0.86 + 0.14 * rng.random()
        colour = (WARM[0] * tone, WARM[1] * tone * 0.98, WARM[2] * tone * 0.95)
        z0 = z + k * PYRAMID_RISE
        block(builder, hx - k * dx, hy - k * dy, z0 - 0.3, z0 + PYRAMID_RISE, MARBLE, colour)
        band(builder, hx - k * dx, hy - k * dy, z0, z0 + PYRAMID_RISE * 0.18, MARBLE, 0.004, 2.0)
        builder.tint(len(builder.polygons) - 4, tuple(c * 0.8 for c in colour))
    top = z + PYRAMID_STEPS * PYRAMID_RISE
    block(builder, top_x - 0.2, top_y - 0.2, top, top + 1.3, MARBLE, WARM)
    base_moulding(builder, top_x - 0.2, top_y - 0.2, top, 0.8)
    moulding(builder, top_x - 0.2, top_y - 0.2, top + 1.0, [(-0.3, 0.0), (0.0, 0.0), (0.12, 0.12), (0.2, 0.22),
                                                           (0.2, 0.3)], MARBLE, WARM)
    return top + 1.3


def lion():
    builder = MeshBuilder()
    coat = LION
    mane = (0.90, 0.80, 0.62)
    ellipsoid(builder, (0.0, -0.1, 0.78), (0.24, 0.62, 0.27), coat, 12, 7, MARBLE)
    ellipsoid(builder, (0.0, 0.34, 0.86), (0.3, 0.34, 0.34), mane, 12, 7, MARBLE)
    ellipsoid(builder, (0.0, 0.58, 1.06), (0.3, 0.22, 0.32), mane, 12, 6, MARBLE)
    for k in range(10):
        angle = 2 * math.pi * k / 10
        ellipsoid(builder, (0.24 * math.cos(angle), 0.6 + 0.04 * math.sin(angle * 2), 1.06 + 0.24 * math.sin(angle)),
                  (0.09, 0.1, 0.09), mane, 6, 3, MARBLE)
    ellipsoid(builder, (0.0, 0.72, 1.06), (0.17, 0.17, 0.19), coat, 10, 6, MARBLE)
    ellipsoid(builder, (0.0, 0.86, 0.98), (0.1, 0.1, 0.09), coat, 8, 4, MARBLE)
    ellipsoid(builder, (0.0, 0.94, 1.0), (0.04, 0.03, 0.03), (0.30, 0.22, 0.18), 5, 3, MARBLE)
    for side in (-1, 1):
        ellipsoid(builder, (side * 0.07, 0.86, 1.12), (0.03, 0.02, 0.02), (0.36, 0.28, 0.16), 5, 3, MARBLE)
        ellipsoid(builder, (side * 0.12, 0.64, 1.25), (0.05, 0.03, 0.05), mane, 5, 3, MARBLE)
        for end, hip in ((1, 0.32), (-1, -0.5)):
            top = Vector((side * 0.15, hip, 0.74))
            knee = Vector((side * 0.16, hip + 0.06 * end, 0.38))
            paw = Vector((side * 0.16, hip + 0.04, 0.06))
            tube(builder, [top, knee, paw], [0.13 if end < 0 else 0.11, 0.08, 0.07], coat, 8, MARBLE)
            ellipsoid(builder, paw + Vector((0.0, 0.07, -0.02)), (0.08, 0.12, 0.05), coat, 6, 3, MARBLE)
    tube(builder, [(0.0, -0.68, 0.86), (0.0, -0.86, 0.6), (0.06, -0.92, 0.3), (0.1, -0.84, 0.16)],
         [0.05, 0.04, 0.035, 0.03], coat, 5, MARBLE)
    ellipsoid(builder, (0.1, -0.82, 0.14), (0.05, 0.05, 0.06), mane, 5, 3, MARBLE)
    builder.box((-0.34, -1.0, 0.0), (0.34, 1.02, 0.06), MARBLE)
    return builder


def lion_frames():
    frames = []
    edge_x, edge_y = PLATFORM[0] - 1.0, PLATFORM[1] - 1.0
    for k in range(10):
        x = -13.5 + 3.0 * k
        frames.append(placement(x, edge_y, STYLOBATE - 0.25, 0.0) @ Matrix.Translation((0.0, -0.1, 0.0)))
        frames.append(placement(x, -edge_y, STYLOBATE - 0.25, math.pi) @ Matrix.Translation((0.0, -0.1, 0.0)))
    for k in range(8):
        y = -10.5 + 3.0 * k
        frames.append(placement(edge_x, y, STYLOBATE - 0.25, -math.pi / 2) @ Matrix.Translation((0.0, -0.1, 0.0)))
        frames.append(placement(-edge_x, y, STYLOBATE - 0.25, math.pi / 2) @ Matrix.Translation((0.0, -0.1, 0.0)))
    return frames


STATUE_LOOKS = [
    dict(tunic=(0.92, 0.88, 0.80), hem=0.12, palla=(0.62, 0.22, 0.18), arms="shoulder", carry="staff", hair=0),
    dict(tunic=(0.70, 0.30, 0.22), hem=0.55, cloak=(0.30, 0.38, 0.62), belt=(0.6, 0.45, 0.26), arms="gesture",
         carry="staff", stride=0.2, hair=1),
    dict(tunic=(0.86, 0.74, 0.50), hem=0.03, palla=(0.40, 0.48, 0.66), veil=True, female=True, sleeves="long",
         arms="hip", hair=2),
    dict(tunic=(0.92, 0.90, 0.84), hem=0.55, cloak=(0.84, 0.66, 0.30), arms="forward", stride=0.25, hair=3),
]


def muted(colour, amount=0.45):
    return tuple(c * (1 - amount) + 0.95 * amount for c in colour)


def chroma(colour):
    peak = max(max(colour), 1e-4)
    return tuple(c / peak for c in colour)


def statue(index, scale):
    spec = dict(STATUE_LOOKS[index % len(STATUE_LOOKS)])
    kept = [chroma(spec[key]) for key in ("palla", "cloak") if key in spec]
    look = Look(skin=0, material=MARBLE, seed=200 + index, **spec)
    figure = person(look)
    for k, colour in enumerate(figure.polygon_colors):
        if colour is not None and any(sum(abs(a - b) for a, b in zip(chroma(colour), ref)) < 0.15 for ref in kept):
            figure.polygon_colors[k] = muted(colour, 0.4)
        else:
            figure.polygon_colors[k] = WARM
    builder = MeshBuilder()
    painted(builder, (0.92, 0.88, 0.80), lambda: builder.box((-0.36, -0.32, 0.0), (0.36, 0.32, 0.36), MARBLE))
    painted(builder, WARM, lambda: builder.box((-0.4, -0.36, 0.36), (0.4, 0.36, 0.45), MARBLE, bottom=False))
    builder.merge(figure, Matrix.Translation((0.0, 0.0, 0.45)))
    scaled = MeshBuilder()
    scaled.merge(builder, Matrix.Scale(scale, 4))
    return scaled


def statue_frames(tier, spacing, inset):
    hx, hy, _, z = TIERS[tier]
    hx -= inset
    hy -= inset
    frames = {k: [] for k in range(4)}
    rng = random.Random(40 + tier)
    sides = [((-hx, -hy), (hx, -hy), -math.pi / 2 + math.pi / 2), ((hx, -hy), (hx, hy), math.pi / 2 - math.pi / 2 - math.pi / 2),
             ((hx, hy), (-hx, hy), 0.0), ((-hx, hy), (-hx, -hy), math.pi / 2)]
    facing = [math.pi, -math.pi / 2, 0.0, math.pi / 2]
    for (a, b, _), turn in zip(sides, facing):
        a, b = Vector(a), Vector(b)
        length = (b - a).length
        count = int(length / spacing)
        for k in range(count):
            p = a.lerp(b, (k + 0.5) / count)
            frames[rng.randrange(4)].append(placement(p.x, p.y, z, turn + rng.uniform(-0.25, 0.25)))
    return frames


def horse_statue(seed=0, step=0.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    coat = (0.97, 0.93, 0.86)
    dark = (0.86, 0.80, 0.72)
    body_z = 1.32
    ellipsoid(builder, (0.0, 0.0, body_z), (0.3, 0.78, 0.36), coat, 14, 8, MARBLE)
    ellipsoid(builder, (0.0, 0.5, body_z + 0.06), (0.29, 0.36, 0.39), coat, 12, 7, MARBLE)
    ellipsoid(builder, (0.0, -0.52, body_z + 0.06), (0.31, 0.36, 0.37), coat, 12, 7, MARBLE)
    turn = rng.uniform(-0.12, 0.12)
    shoulder = Vector((0.0, 0.66, body_z + 0.22))
    poll = Vector((turn * 0.6, 1.0, body_z + 1.05))
    muzzle = Vector((turn, 1.32, body_z + 0.62))
    tube(builder, [shoulder, shoulder.lerp(poll, 0.5) + Vector((0.0, 0.05, 0.0)), poll], [0.24, 0.18, 0.12], coat, 10,
         MARBLE)
    tube(builder, [poll + Vector((0.0, -0.04, 0.02)), poll.lerp(muzzle, 0.5), muzzle], [0.12, 0.11, 0.08], coat, 9,
         MARBLE)
    ellipsoid(builder, muzzle + Vector((0.0, 0.02, -0.02)), (0.08, 0.09, 0.08), coat, 8, 4, MARBLE)
    for side in (-1, 1):
        ellipsoid(builder, poll + Vector((side * 0.06, 0.02, 0.14)), (0.03, 0.03, 0.08), coat, 5, 3, MARBLE)
        ellipsoid(builder, poll.lerp(muzzle, 0.3) + Vector((side * 0.085, 0.0, 0.03)), (0.025, 0.03, 0.025),
                  (0.42, 0.30, 0.22), 5, 3, MARBLE)
    mane = [shoulder + Vector((0.0, -0.12, 0.22)), shoulder.lerp(poll, 0.5) + Vector((0.0, -0.08, 0.16)),
            poll + Vector((0.0, -0.06, 0.1))]
    tube(builder, mane, [0.06, 0.07, 0.05], dark, 6, MARBLE, squash=0.4)
    ellipsoid(builder, poll + Vector((0.0, 0.08, 0.12)), (0.05, 0.08, 0.06), dark, 6, 3, MARBLE)
    for k, (a, b) in enumerate(((shoulder + Vector((0.0, -0.05, 0.05)), muzzle + Vector((0.0, -0.08, 0.0))),
                                (poll + Vector((0.0, 0.0, -0.02)), muzzle + Vector((0.0, -0.06, -0.05))))):
        tube(builder, [a, b], [0.022, 0.022], PAINT_RED, 4, MATTE)
    tube(builder, [Vector((0.0, 0.45, body_z + 0.35)), Vector((0.0, -0.1, body_z + 0.38))], [0.03, 0.03], PAINT_RED, 4,
         MATTE)
    ellipsoid(builder, (0.0, 0.1, body_z + 0.36), (0.32, 0.12, 0.06), PAINT_BLUE, 8, 3, MATTE)
    for side in (-1, 1):
        for end in (1, -1):
            lift = step if (end == 1 and side == 1) else 0.0
            y = end * 0.52
            top = Vector((side * 0.16, y, body_z - 0.12))
            knee = Vector((side * 0.16, y + 0.06 * end + lift * 0.3, 0.62 + lift * 0.35))
            hoof = Vector((side * 0.16, y + 0.03 + lift * 0.42, 0.06 + lift * 0.52))
            tube(builder, [top, top.lerp(knee, 0.5) + Vector((0.0, 0.0, 0.0)), knee, hoof], [0.12, 0.09, 0.06, 0.05],
                 coat, 8, MARBLE)
            ellipsoid(builder, hoof + Vector((0.0, 0.03, -0.02)), (0.065, 0.08, 0.05), dark, 6, 3, MARBLE)
    tube(builder, [(0.0, -0.84, body_z + 0.22), (0.0, -1.02, body_z - 0.2), (0.0, -1.0, body_z - 0.82)],
         [0.08, 0.1, 0.06], dark, 6, MARBLE)
    return builder


def quadriga():
    builder = MeshBuilder()
    scale = 1.45
    for k, x in enumerate((-1.08, -0.36, 0.36, 1.08)):
        horse = horse_statue(70 + k, 0.35 if k in (1, 2) else 0.0)
        builder.merge(horse, placement(x * scale, 0.9 * scale, 0.0, (0.03 if x > 0 else -0.03), scale))
    car = MeshBuilder()
    painted(car, WARM, lambda: car.box((-0.7, -0.6, 0.85), (0.7, 0.0, 0.95), MARBLE))
    front = [(math.cos(math.pi * k / 10) * 0.7, math.sin(math.pi * k / 10) * 0.35, 0.0) for k in range(11)]
    painted(car, PAINT_RED, lambda: car.sweep([(x, y, 0.95) for x, y, _ in front], [(0.0, 0.0), (0.04, 0.0),
                                                                                       (0.04, 0.85), (0.0, 0.85)],
                                              MARBLE, closed=False))
    for side in (-1, 1):
        frame = Matrix.Translation((side * 0.82, -0.3, 0.72)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        painted(car, WARM, lambda frame=frame: car.lathe([(0.6, -0.06), (0.72, -0.06), (0.72, 0.06), (0.6, 0.06), (0.6, -0.06)],
                                                           18, MARBLE, matrix=frame, smooth=False))
        painted(car, PAINT_GOLD, lambda frame=frame: car.lathe([(0.0, -0.12), (0.14, -0.12), (0.14, 0.12), (0.0, 0.12)], 10, GILT,
                                                                 matrix=frame))
        for k in range(8):
            angle = math.tau * k / 8
            tube(car, [frame @ Vector((0.12 * math.cos(angle), 0.12 * math.sin(angle), 0.0)),
                       frame @ Vector((0.62 * math.cos(angle), 0.62 * math.sin(angle), 0.0))], [0.035, 0.03], WARM, 4, MARBLE)
    tube(car, [(0.0, 0.2, 0.9), (0.0, 1.0, 1.0), (0.0, 1.6, 1.45)], [0.06, 0.06, 0.05], WARM, 6, MARBLE)
    tube(car, [(-1.5, 1.55, 1.5), (1.5, 1.55, 1.5)], [0.05, 0.05], WARM, 6, MARBLE)
    builder.merge(car, Matrix.Scale(scale, 4) @ Matrix.Translation((0.0, -0.75, 0.0)))
    return builder


def mausoleum():
    builder = MeshBuilder()
    podium(builder)
    pyramid_base = entablature(builder)
    top = pyramid(builder, pyramid_base)
    return builder, top

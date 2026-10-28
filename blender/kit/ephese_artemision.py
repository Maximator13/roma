import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import Look, coarse, drape, ellipsoid, person, tube
from .orders import fluting, gable_roof, torus_arc

MARBLE = "marble"
ASHLAR = "marble_ashlar"
POLYGONAL = "paving_polygonal"
GILT = "bronze_gilt"
TILES = "terracotta_tiles"
VOID = "shadow_void"
TAU = 2 * math.pi
STEPS = 9
STEP_H = 0.3
STEP_D = 0.55
Z0 = STEPS * STEP_H
D = 1.8
H = 17.8
FRONT_X = [-26.2, -19.0, -11.7, -4.3, 4.3, 11.7, 19.0, 26.2]
FLANK = 5.6
FLANK_COUNT = 21
HALF_Y = FLANK * (FLANK_COUNT - 1) / 2
STYLO_X = FRONT_X[-1] + 2.2
STYLO_Y = HALF_Y + 2.2
KREPIS_X = STYLO_X + STEPS * STEP_D
KREPIS_Y = STYLO_Y + STEPS * STEP_D
ZA = Z0 + H
CORNICE = ZA + 3.0
SIMA_TOP = ZA + 3.75
EAVE_HALF = STYLO_X + 1.6
RIDGE = CORNICE + EAVE_HALF * 0.27
CELLA_X = 12.6
WALL = 1.5
DOOR_Y = -28.0
BACK_Y = 30.0
ANTA_FRONT = -45.0
ANTA_BACK = 45.0
STATUE_Y = 22.0
PEDESTAL = 1.8
RED = (0.66, 0.16, 0.12)
BLUE = (0.16, 0.30, 0.62)
DEEP_BLUE = (0.10, 0.20, 0.46)
OCHRE = (0.86, 0.62, 0.26)
BEAM = (0.78, 0.58, 0.30)
RELIEF_GROUND = (0.86, 0.88, 0.92)
WHITE = (0.98, 0.96, 0.92)
EBONY = (0.24, 0.16, 0.11)
CYPRESS = (0.46, 0.30, 0.18)
AMBER = (0.86, 0.50, 0.16)


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def column_positions():
    outer = []
    inner = []
    ys = [-HALF_Y + FLANK * k for k in range(FLANK_COUNT)]
    for x in FRONT_X:
        outer.append((x, ys[0], "front"))
        outer.append((x, ys[-1], "back"))
    for y in ys[1:-1]:
        outer.append((FRONT_X[0], y, "side"))
        outer.append((FRONT_X[-1], y, "side"))
    for x in FRONT_X[1:-1]:
        inner.append((x, ys[1], "front"))
        inner.append((x, ys[-2], "back"))
    for y in ys[2:-2]:
        inner.append((FRONT_X[1], y, "side"))
        inner.append((FRONT_X[-2], y, "side"))
    porch = [(x, y, "porch") for x in (-4.3, 4.3) for y in (ANTA_FRONT, ANTA_FRONT + FLANK, ANTA_FRONT + 2 * FLANK)]
    back = [(x, y, "porch") for x in (-4.3, 4.3) for y in (ANTA_BACK, ANTA_BACK - FLANK)]
    return outer, inner, porch + back


def sculpted(position):
    x, y, kind = position
    return kind in ("front", "back") or (kind == "porch" and (y < 0.0 or abs(y - ANTA_BACK) < 0.1))


def asiatic_base(builder, d, segments=20):
    r = d / 2
    painted(builder, WHITE, lambda: builder.box((-0.7 * d, -0.7 * d, 0.0), (0.7 * d, 0.7 * d, 0.17 * d), MARBLE,
                                               bottom=False))
    profile = [(0.64 * d, 0.17 * d), (0.64 * d, 0.21 * d), (0.6 * d, 0.225 * d), (0.56 * d, 0.27 * d),
               (0.55 * d, 0.3 * d), (0.6 * d, 0.32 * d), (0.6 * d, 0.345 * d), (0.56 * d, 0.36 * d),
               (0.545 * d, 0.41 * d), (0.6 * d, 0.43 * d), (0.6 * d, 0.45 * d)]
    torus = torus_arc(0.56 * d, 0.55 * d, 0.1 * d, -90, 90, 6)
    for k, (radius, height) in enumerate(torus):
        profile.append((radius - (0.012 * d if k % 2 else 0.0), height))
    profile += [(0.52 * d, 0.66 * d), (r * 1.03, 0.68 * d), (r, 0.7 * d)]
    painted(builder, WHITE, lambda: builder.lathe(profile, segments, MARBLE, smooth=True, caps=False))
    return 0.7 * d


def fluted_shaft(builder, d, bottom, top, flutes=24, per_flute=2):
    radius = d / 2
    rings = []
    for t in (0.0, 0.12, 0.3, 0.5, 0.7, 0.88, 1.0):
        taper = 0.0 if t <= 0.3 else ((t - 0.3) / 0.7) ** 1.3
        rings.append((radius * (1 - 0.16 * taper), bottom + (top - bottom) * t))
    painted(builder, WHITE, lambda: builder.lathe(rings, flutes * per_flute, MARBLE, smooth=True,
                                                  radius_scale=fluting(flutes, 0.08), caps=False))


def spiral_points(cx, cz, y, outer, inner, turns, steps, phase=0.0, mirror=1.0):
    points = []
    for k in range(steps + 1):
        t = k / steps
        angle = phase + mirror * TAU * turns * t
        radius = outer * (inner / outer) ** t
        points.append(Vector((cx + mirror * radius * math.cos(angle), y, cz + radius * math.sin(angle))))
    return points


def volute_face(builder, cx, cz, y, facing, mirror, d, colour=WHITE):
    outer = 0.32 * d
    inner = 0.05 * d
    steps = 20
    rings = []
    for k in range(steps + 1):
        t = k / steps
        angle = math.pi / 2 + mirror * TAU * 2.2 * t
        radius = outer * (inner / outer) ** t
        rings.append([Vector((cx + mirror * radius * math.cos(angle), y, cz + radius * math.sin(angle))),
                      Vector((cx + mirror * radius * 0.6 * math.cos(angle), y + facing * 0.004,
                              cz + radius * 0.6 * math.sin(angle)))])
    rows = [[ring[0] for ring in rings], [ring[1] for ring in rings]]
    painted(builder, colour, lambda: builder.surface(rows, MARBLE, facing=(0, facing, 0)))
    disc = [Vector((cx + outer * 1.02 * math.cos(a), y - facing * 0.002, cz + outer * 1.02 * math.sin(a)))
            for a in [TAU * k / 16 for k in range(16)]]
    painted(builder, colour, lambda: builder.oriented(disc, (0, facing, 0), MARBLE))
    path = spiral_points(cx, cz, y + facing * 0.03, outer, inner * 1.4, 2.2, 20, math.pi / 2, mirror)
    profile = [(0.0, -0.03 * d), (0.025 * d, 0.0), (0.0, 0.03 * d), (-0.025 * d, 0.0)]
    painted(builder, colour, lambda: builder.sweep(path, profile, MARBLE, facade_normal=(0, facing, 0), caps=False))
    eye = [Vector((cx + 0.055 * d * math.cos(a), y + facing * 0.02, cz + 0.055 * d * math.sin(a)))
           for a in [TAU * k / 8 for k in range(8)]]
    painted(builder, (0.95, 0.75, 0.35), lambda: builder.oriented(eye, (0, facing, 0), GILT))


def ionic_capital(builder, d, bottom):
    top_r = d / 2 * 0.84
    painted(builder, WHITE, lambda: builder.lathe(torus_arc(top_r + 0.02 * d, bottom + 0.035 * d, 0.035 * d, -90, 90,
                                                            3), 24, MARBLE, smooth=True, caps=False))
    eggs = 16

    def egg(angle):
        phase = (angle * eggs / TAU) % 1.0
        return 1.0 + 0.06 * math.sin(math.pi * phase) - 0.05 * (abs(phase - 0.0) < 0.12 or phase > 0.88)
    echinus = [(top_r, bottom + 0.07 * d), (0.55 * d, bottom + 0.14 * d), (0.6 * d, bottom + 0.22 * d),
               (0.56 * d, bottom + 0.28 * d)]
    painted(builder, WHITE, lambda: builder.lathe(echinus, 32, MARBLE, smooth=True, radius_scale=egg, caps=False))
    first = len(builder.polygons) - 32 * 3
    for index in range(first, len(builder.polygons)):
        if (index - first) % 2 == 1:
            builder.polygon_colors[index] = (0.86, 0.80, 0.74)
    vz = bottom + 0.2 * d
    canalis_top = bottom + 0.42 * d
    half_w = 0.78 * d
    half_d = 0.5 * d
    painted(builder, WHITE, lambda: builder.box((-half_w, -half_d, bottom + 0.24 * d), (half_w, half_d, canalis_top),
                                               MARBLE))
    for side in (-1, 1):
        cx = side * 0.58 * d
        for facing in (-1, 1):
            volute_face(builder, cx, vz, facing * half_d, facing, side, d)
        bolster = [(0.24 * d, -half_d), (0.22 * d, -half_d * 0.6), (0.17 * d, -half_d * 0.12),
                   (0.17 * d, half_d * 0.12), (0.22 * d, half_d * 0.6), (0.24 * d, half_d)]
        frame = Matrix.Translation((cx, 0.0, vz + 0.02 * d)) @ Matrix.Rotation(math.radians(90), 4, "X")
        painted(builder, WHITE, lambda frame=frame: builder.lathe([(r, -z) for r, z in bolster], 12, MARBLE,
                                                                 smooth=True, matrix=frame, caps=False))
        belt = Matrix.Translation((cx, 0.0, vz + 0.02 * d)) @ Matrix.Rotation(math.radians(90), 4, "X")
        painted(builder, OCHRE, lambda belt=belt: builder.lathe([(0.185 * d, -0.06 * d), (0.185 * d, 0.06 * d)], 12,
                                                                GILT, smooth=True, matrix=belt, caps=False))
    painted(builder, WHITE, lambda: builder.box((-0.62 * d, -0.6 * d, canalis_top), (0.62 * d, 0.6 * d,
                                                                                    canalis_top + 0.1 * d), MARBLE))
    painted(builder, RED, lambda: builder.box((-0.64 * d, -0.62 * d, canalis_top + 0.04 * d),
                                             (0.64 * d, 0.62 * d, canalis_top + 0.07 * d), MARBLE, bottom=False,
                                             top=False))
    return canalis_top + 0.1 * d


CAPITAL = 0.52 * D


def relief_figure(seed, kind):
    rng = random.Random(seed)
    tints = [(0.97, 0.94, 0.89), (0.94, 0.91, 0.87), (0.99, 0.96, 0.91), (0.93, 0.89, 0.83), (0.96, 0.93, 0.91)]
    if kind == 0:
        look = Look(rng.choice(tints), hem=0.03, skin=0, hair=1, palla=rng.choice(tints), veil=rng.random() < 0.5,
                    female=True, sleeves="long", arms=rng.choice(["hip", "gesture", "down"]), material=MARBLE,
                    seed=seed)
    elif kind == 1:
        look = Look(rng.choice(tints), hem=0.12, skin=1, hair=0, palla=rng.choice(tints), arms="gesture",
                    material=MARBLE, seed=seed)
    else:
        look = Look((0.96, 0.92, 0.84), hem=0.62, skin=1, hair=2, cloak=rng.choice(tints), arms="staff",
                    carry="staff", material=MARBLE, seed=seed)
    return coarse(lambda: person(look), 0.6)


def sculpted_drum(builder, d, bottom, top, seed):
    radius = d / 2 * 1.04
    painted(builder, RELIEF_GROUND, lambda: builder.lathe([(radius, bottom), (radius, top)], 24, MARBLE,
                                                               smooth=True, caps=False))
    painted(builder, WHITE, lambda: builder.lathe(torus_arc(radius, bottom + 0.06, 0.06, -90, 90, 3), 24, MARBLE,
                                                  smooth=True, caps=False))
    painted(builder, WHITE, lambda: builder.lathe(torus_arc(radius, top - 0.06, 0.06, -90, 90, 3), 24, MARBLE,
                                                  smooth=True, caps=False))
    count = 8
    scale = (top - bottom - 0.1) / 1.7
    for k in range(count):
        angle = TAU * k / count + seed * 0.37
        figure = relief_figure(seed * 11 + k, (seed + k) % 3)
        reach = radius * 0.97 + 0.12
        frame = (Matrix.Translation((reach * math.cos(angle), reach * math.sin(angle), bottom + 0.05))
                 @ Matrix.Rotation(angle - math.pi / 2, 4, "Z") @ Matrix.Scale(scale, 4))
        builder.merge(figure, frame)


def ionic_mid(d=D, h=H):
    builder = MeshBuilder()
    base_top = asiatic_base(builder, d, 14)
    capital_bottom = h - CAPITAL * d / D
    fluted_shaft(builder, d, base_top, capital_bottom, 16, 2)
    top_r = d / 2 * 0.84
    painted(builder, WHITE, lambda: builder.lathe([(top_r, capital_bottom), (0.6 * d, capital_bottom + 0.2 * d),
                                                   (0.56 * d, capital_bottom + 0.28 * d)], 16, MARBLE, smooth=True,
                                                  caps=False))
    painted(builder, WHITE, lambda: builder.box((-0.78 * d, -0.5 * d, capital_bottom + 0.24 * d),
                                               (0.78 * d, 0.5 * d, capital_bottom + 0.42 * d), MARBLE))
    for side in (-1, 1):
        for facing in (-1, 1):
            cx = side * 0.58 * d
            cz = capital_bottom + 0.2 * d
            disc = [Vector((cx + 0.32 * d * math.cos(a), facing * 0.505 * d, cz + 0.32 * d * math.sin(a)))
                    for a in [TAU * k / 10 for k in range(10)]]
            painted(builder, WHITE, lambda disc=disc, facing=facing: builder.oriented(disc, (0, facing, 0), MARBLE))
            eye = [Vector((cx + 0.07 * d * math.cos(a), facing * 0.515 * d, cz + 0.07 * d * math.sin(a)))
                   for a in [TAU * k / 6 for k in range(6)]]
            painted(builder, (0.95, 0.75, 0.35), lambda eye=eye, facing=facing: builder.oriented(eye, (0, facing, 0),
                                                                                                GILT))
    painted(builder, WHITE, lambda: builder.box((-0.62 * d, -0.6 * d, capital_bottom + 0.42 * d),
                                               (0.62 * d, 0.6 * d, h), MARBLE))
    return builder


def ionic_column(d=D, h=H, caelata=False, seed=0):
    builder = MeshBuilder()
    base_top = asiatic_base(builder, d)
    capital_bottom = h - CAPITAL * d / D
    shaft_bottom = base_top
    if caelata:
        drum_top = base_top + 1.85 * d / D
        sculpted_drum(builder, d, base_top, drum_top, seed)
        shaft_bottom = drum_top
    fluted_shaft(builder, d, shaft_bottom, capital_bottom)
    ionic_capital(builder, d, capital_bottom)
    return builder


def rectangle_path(hx, hy):
    return [Vector((-hx, -hy, 0.0)), Vector((hx, -hy, 0.0)), Vector((hx, hy, 0.0)), Vector((-hx, hy, 0.0))]


ENTABLATURE = [(-0.95, 0.0), (0.72, 0.0), (0.72, 0.5), (0.8, 0.52), (0.8, 1.0), (0.88, 1.02), (0.88, 1.42),
               (1.0, 1.5), (1.02, 1.62), (1.08, 1.62), (1.08, 2.12), (1.18, 2.14), (1.62, 2.28), (1.74, 2.3),
               (1.74, 2.88), (1.88, 3.0), (1.98, 3.4), (2.02, 3.62), (1.94, 3.75), (-0.95, 3.75)]
BAND_TINTS = {7: RED, 8: OCHRE, 10: WHITE, 12: DEEP_BLUE, 15: BLUE, 16: RED, 17: OCHRE}


def entablature(builder, hx, hy, z):
    path = [p + Vector((0.0, 0.0, z)) for p in rectangle_path(hx, hy)]
    first = len(builder.polygons)
    builder.sweep(path, ENTABLATURE, MARBLE, closed=True)
    count = len(ENTABLATURE)
    for index in range(first, len(builder.polygons)):
        corner = (index - first) % count
        builder.polygon_colors[index] = BAND_TINTS.get(corner, WHITE)
    for (ax, ay), (bx, by) in (((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)),
                               ((-hx, hy), (-hx, -hy))):
        a = Vector((ax, ay))
        b = Vector((bx, by))
        direction = (b - a).normalized()
        outward = Vector((direction.y, -direction.x))
        length = (b - a).length
        count_dentils = int(length / 0.42)
        for k in range(1, count_dentils):
            p = a + direction * (k * length / count_dentils) + outward * 1.085
            corners = [Vector((p.x - direction.x * 0.08, p.y - direction.y * 0.08, z + 1.66)),
                       Vector((p.x + direction.x * 0.08, p.y + direction.y * 0.08, z + 1.66)),
                       Vector((p.x + direction.x * 0.08, p.y + direction.y * 0.08, z + 2.08)),
                       Vector((p.x - direction.x * 0.08, p.y - direction.y * 0.08, z + 2.08))]
            builder.oriented(corners, (outward.x, outward.y, 0.0), VOID)
        for k in range(int(length / 2.8)):
            p = a + direction * (1.4 + k * 2.8) + outward * 2.04
            ellipsoid(builder, (p.x, p.y, z + 3.45), (0.16, 0.16, 0.14), (0.94, 0.88, 0.70), 6, 3, MARBLE)


def pediment(builder, y, facing):
    eave = CORNICE + 0.75
    half = EAVE_HALF
    back = y - facing * 0.9
    tri = [(-half, back, eave - 0.8), (half, back, eave - 0.8), (0.0, back, RIDGE)]
    painted(builder, DEEP_BLUE, lambda: builder.oriented(tri, (0, facing, 0), MARBLE))
    for x0, x1, z0, z1 in ((-1.6, 1.6, eave + 0.6, eave + 4.0), (-9.5, -6.5, eave + 0.5, eave + 2.3),
                           (6.5, 9.5, eave + 0.5, eave + 2.3)):
        quad = [(x0, back + facing * 0.02, z0), (x1, back + facing * 0.02, z0), (x1, back + facing * 0.02, z1),
                (x0, back + facing * 0.02, z1)]
        builder.oriented(quad, (0, facing, 0), VOID)
        frame = [(x0 - 0.3, back + facing * 0.01, z0 - 0.3), (x1 + 0.3, back + facing * 0.01, z0 - 0.3),
                 (x1 + 0.3, back + facing * 0.01, z1 + 0.3), (x0 - 0.3, back + facing * 0.01, z1 + 0.3)]
        painted(builder, OCHRE, lambda frame=frame: builder.oriented(frame, (0, facing, 0), GILT))
    for side in (-1, 1):
        a = Vector((side * (half + 0.2), y, eave - 0.1))
        b = Vector((0.0, y, RIDGE + 0.2))
        direction = (b - a).normalized()
        normal = Vector((0.0, facing, 0.0))
        up = normal.cross(direction).normalized()
        if up.z < 0:
            up = -up
        for z0, z1, depth, colour in ((0.0, 0.55, 0.9, WHITE), (0.55, 0.85, 1.1, BLUE), (0.85, 1.25, 1.2, RED)):
            quad = [a + up * z0 + normal * 0.2, b + up * z0 + normal * 0.2, b + up * z1 + normal * 0.2,
                    a + up * z1 + normal * 0.2]
            painted(builder, colour, lambda quad=quad: builder.oriented(quad, (0, facing, 0.0), MARBLE))
            top = [a + up * z1 + normal * 0.2, b + up * z1 + normal * 0.2, b + up * z1 - normal * depth,
                   a + up * z1 - normal * depth]
            painted(builder, colour, lambda top=top: builder.oriented(top, (0, 0, 1), MARBLE))
    acroterion(builder, Vector((0.0, y + facing * 0.1, RIDGE + 1.1)), 2.4, facing)
    for side in (-1, 1):
        acroterion(builder, Vector((side * (half - 0.6), y + facing * 0.1, eave + 0.4)), 1.6, facing)


def acroterion(builder, base, size, facing):
    painted(builder, (0.98, 0.80, 0.40), lambda: builder.box((base.x - size * 0.3, base.y - 0.3, base.z - 0.2),
                                                             (base.x + size * 0.3, base.y + 0.3, base.z + size * 0.2),
                                                             GILT))
    for k in range(7):
        angle = math.pi * (k + 0.5) / 7
        tip = base + Vector((math.cos(angle) * size * 0.55, 0.0, size * 0.25 + math.sin(angle) * size * 0.75))
        tube(builder, [base + Vector((0.0, 0.0, size * 0.2)), tip], [0.12 * size / 2, 0.02], (0.98, 0.80, 0.40), 4,
             GILT)


def krepis(builder):
    for k in range(STEPS):
        inset = k * STEP_D
        z0 = k * STEP_H
        hx = KREPIS_X - inset
        hy = KREPIS_Y - inset
        painted(builder, (0.97 - 0.004 * k, 0.95 - 0.004 * k, 0.91), lambda hx=hx, hy=hy, z0=z0: builder.box(
            (-hx, -hy, z0 - (1.5 if k == 0 else 0.0)), (hx, hy, z0 + STEP_H), ASHLAR, bottom=False))
    painted(builder, (0.99, 0.97, 0.93), lambda: builder.box((-STYLO_X, -STYLO_Y, Z0 - 0.01),
                                                             (STYLO_X, STYLO_Y, Z0 + 0.02), MARBLE, bottom=False))


def cella(builder):
    z1 = ZA + 1.6
    for side in (-1, 1):
        x_out = side * CELLA_X
        x_in = side * (CELLA_X - WALL)
        lo, hi = sorted((x_out, x_in))
        painted(builder, WHITE, lambda lo=lo, hi=hi: builder.box((lo, ANTA_FRONT, Z0), (hi, ANTA_BACK, z1), ASHLAR,
                                                                 bottom=False))
        face = side * (CELLA_X - WALL)
        d0, d1 = sorted((face, face - side * 0.04))
        painted(builder, (0.70, 0.22, 0.16), lambda d0=d0, d1=d1: builder.box((d0, DOOR_Y + 0.1, Z0),
                                                                            (d1, BACK_Y - 0.1, Z0 + 2.2), MATTE,
                                                                            bottom=False, top=False))
        for y in (ANTA_FRONT, ANTA_BACK):
            painted(builder, WHITE, lambda y=y, lo=lo, hi=hi: builder.box((lo - 0.25, y - 0.6, Z0), (hi + 0.25, y + 0.6,
                                                                                                      Z0 + 1.0),
                                                                          MARBLE, bottom=False))
    inner = CELLA_X - WALL
    door_half = 3.2
    door_top = Z0 + 13.0
    for x0, x1 in ((-inner, -door_half), (door_half, inner)):
        painted(builder, WHITE, lambda x0=x0, x1=x1: builder.box((x0, DOOR_Y - WALL, Z0), (x1, DOOR_Y, z1), ASHLAR,
                                                                 bottom=False))
    painted(builder, WHITE, lambda: builder.box((-door_half, DOOR_Y - WALL, door_top), (door_half, DOOR_Y, z1), ASHLAR,
                                                bottom=False))
    for x in (-door_half - 0.5, door_half + 0.5):
        painted(builder, (0.99, 0.97, 0.92), lambda x=x: builder.box((x - 0.5, DOOR_Y - WALL - 0.25, Z0),
                                                                     (x + 0.5, DOOR_Y - WALL + 0.2, door_top + 1.0),
                                                                     MARBLE, bottom=False))
    painted(builder, (0.99, 0.97, 0.92), lambda: builder.box((-door_half - 1.2, DOOR_Y - WALL - 0.35, door_top),
                                                             (door_half + 1.2, DOOR_Y - WALL + 0.2, door_top + 1.4),
                                                             MARBLE, bottom=False))
    painted(builder, OCHRE, lambda: builder.box((-door_half - 1.25, DOOR_Y - WALL - 0.4, door_top + 0.5),
                                               (door_half + 1.25, DOOR_Y - WALL - 0.3, door_top + 0.8), GILT,
                                               bottom=False))
    for side in (-1, 1):
        hinge = Vector((side * door_half, DOOR_Y - 0.2, Z0))
        angle = -side * math.radians(72.0)
        leaf = Matrix.Translation(hinge + Vector((0.0, 0.2, 0.0))) @ Matrix.Rotation(angle, 4, "Z")
        l0, l1 = sorted((0.0, -side * door_half))
        painted(builder, CYPRESS, lambda leaf=leaf, l0=l0, l1=l1: builder.box((l0, 0.0, 0.0),
                                                                              (l1, 0.25, door_top - Z0), MATTE,
                                                                              matrix=leaf))
        for row in range(4):
            for column in range(2):
                cx = -side * (0.8 + column * 1.6)
                cz = 1.5 + row * 3.0
                stud = leaf @ Matrix.Translation((cx, -0.04, cz))
                ellipsoid(builder, stud.translation, (0.18, 0.06, 0.18), (0.95, 0.75, 0.36), 6, 3, GILT)
    painted(builder, WHITE, lambda: builder.box((-inner, BACK_Y, Z0), (inner, BACK_Y + WALL, z1), ASHLAR, bottom=False))
    painted(builder, (0.82, 0.78, 0.70), lambda: builder.box((-inner, DOOR_Y, Z0 - 0.01), (inner, 0.0, Z0 + 0.03),
                                                             MARBLE, bottom=False))
    painted(builder, (0.55, 0.50, 0.44), lambda: builder.box((-inner, 0.0, Z0 - 0.01), (inner, BACK_Y, Z0 + 0.03),
                                                             MARBLE, bottom=False))
    top = opening_level()
    for side in (-1, 1):
        lo, hi = sorted((side * CELLA_X, side * (CELLA_X - WALL)))
        painted(builder, WHITE, lambda lo=lo, hi=hi: builder.box((lo, DOOR_Y - WALL, z1), (hi, BACK_Y + WALL, top),
                                                                 ASHLAR, bottom=False))


def sekos_lining(builder):
    inner = CELLA_X - WALL - 0.03
    top = ZA + 1.5
    zones = [(Z0 + 2.2, Z0 + 8.5, (0.50, 0.12, 0.10)), (Z0 + 8.5, Z0 + 9.1, (0.95, 0.74, 0.34)),
             (Z0 + 9.1, top, (0.14, 0.22, 0.44))]
    for z0, z1, colour in zones:
        for side in (-1, 1):
            x = side * inner
            quad = [(x, DOOR_Y + 0.05, z0), (x, BACK_Y - 0.05, z0), (x, BACK_Y - 0.05, z1), (x, DOOR_Y + 0.05, z1)]
            painted(builder, colour, lambda quad=quad, side=side: builder.oriented(quad, (-side, 0, 0), MATTE))
        quad = [(-inner, BACK_Y - 0.03, z0), (inner, BACK_Y - 0.03, z0), (inner, BACK_Y - 0.03, z1),
                (-inner, BACK_Y - 0.03, z1)]
        painted(builder, colour, lambda quad=quad: builder.oriented(quad, (0, -1, 0), MATTE))
        for x0, x1 in ((-inner, -3.3), (3.3, inner)):
            quad = [(x0, DOOR_Y + 0.03, z0), (x1, DOOR_Y + 0.03, z0), (x1, DOOR_Y + 0.03, z1),
                    (x0, DOOR_Y + 0.03, z1)]
            painted(builder, colour, lambda quad=quad: builder.oriented(quad, (0, 1, 0), MATTE))


def ceiling(builder):
    z = ZA + 1.62
    cell = FLANK
    nx = int(round(2 * STYLO_X / cell))
    ny = int(round(2 * STYLO_Y / cell))
    for i in range(nx):
        for j in range(ny):
            x0 = -STYLO_X + i * 2 * STYLO_X / nx
            x1 = -STYLO_X + (i + 1) * 2 * STYLO_X / nx
            y0 = -STYLO_Y + j * 2 * STYLO_Y / ny
            y1 = -STYLO_Y + (j + 1) * 2 * STYLO_Y / ny
            if abs((x0 + x1) / 2) < CELLA_X - WALL and DOOR_Y < (y0 + y1) / 2 < BACK_Y:
                continue
            colour = DEEP_BLUE if (i + j) % 2 else (0.20, 0.30, 0.54)
            builder.oriented([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, -1), MATTE)
            builder.tint(len(builder.polygons) - 1, colour)
            low = z - 0.05
            band = 0.45
            for a, b, c, d in ((x0, y0, x1, y0 + band), (x0, y1 - band, x1, y1), (x0, y0 + band, x0 + band, y1 - band),
                               (x1 - band, y0 + band, x1, y1 - band)):
                builder.oriented([(a, b, low), (c, b, low), (c, d, low), (a, d, low)], (0, 0, -1), MARBLE)
                builder.tint(len(builder.polygons) - 1, BEAM)


def opening_level():
    eave = CORNICE + 0.75
    return RIDGE - (RIDGE - eave) * CELLA_X / EAVE_HALF


def roof(builder):
    eave = CORNICE + 0.75
    y0, y1 = DOOR_Y - WALL, BACK_Y + WALL
    for a, b in ((-STYLO_Y - 1.0, y0), (y1, STYLO_Y + 1.0)):
        gable_roof(builder, a, b, EAVE_HALF, eave, RIDGE, TILES, along_axis="y", imbrex=False)
        builder.tint(len(builder.polygons) - 2, (1.0, 0.92, 0.84))
    level = opening_level()
    for side in (-1, 1):
        rows = [[(side * EAVE_HALF, y0, eave), (side * CELLA_X, y0, level)],
                [(side * EAVE_HALF, y1, eave), (side * CELLA_X, y1, level)]]
        painted(builder, (1.0, 0.92, 0.84), lambda rows=rows: builder.surface(rows, TILES, facing=(0, 0, 1)))
    z1 = ZA + 1.6
    for y, facing in ((y0, 1), (y1, -1)):
        gable = [(-CELLA_X, y, z1), (CELLA_X, y, z1), (CELLA_X, y, level), (0.0, y, RIDGE), (-CELLA_X, y, level)]
        painted(builder, WHITE, lambda gable=gable, facing=facing: builder.oriented(gable, (0, facing, 0), ASHLAR))
    for k in range(int(2 * STYLO_Y / 3.0)):
        y = -STYLO_Y + 1.5 + k * 3.0
        if y0 - 1.5 < y < y1 + 1.5:
            continue
        tube(builder, [(0.0, y - 1.5, RIDGE + 0.05), (0.0, y + 1.5, RIDGE + 0.05)], [0.22, 0.22], (0.86, 0.50, 0.34),
             4, TILES)


def temple():
    builder = MeshBuilder()
    krepis(builder)
    cella(builder)
    sekos_lining(builder)
    entablature(builder, FRONT_X[-1], HALF_Y, ZA)
    ceiling(builder)
    roof(builder)
    pediment(builder, -STYLO_Y - 1.0, -1)
    pediment(builder, STYLO_Y + 1.0, 1)
    inner_hx = CELLA_X + 0.1
    painted(builder, WHITE, lambda: builder.box((-inner_hx, ANTA_FRONT - 0.9, ZA), (inner_hx, ANTA_FRONT + 0.9,
                                                                                    ZA + 1.6), MARBLE, bottom=True))
    painted(builder, WHITE, lambda: builder.box((-inner_hx, ANTA_BACK - 0.9, ZA), (inner_hx, ANTA_BACK + 0.9,
                                                                                   ZA + 1.6), MARBLE, bottom=True))
    reach = FRONT_X[-2] + 0.9
    for y in (-HALF_Y + FLANK, HALF_Y - FLANK):
        painted(builder, WHITE, lambda y=y: builder.box((-reach, y - 0.9, ZA), (reach, y + 0.9, ZA + 1.6), MARBLE))
    for x in (FRONT_X[1], FRONT_X[-2]):
        painted(builder, WHITE, lambda x=x: builder.box((x - 0.9, -HALF_Y + FLANK, ZA), (x + 0.9, HALF_Y - FLANK,
                                                                                       ZA + 1.6), MARBLE))
    for k, x in enumerate(FRONT_X):
        pedestal(builder, x, -HALF_Y, k)
    return builder


def pedestal(builder, x, y, seed):
    half = 1.4
    painted(builder, WHITE, lambda: builder.box((x - half - 0.12, y - half - 0.12, Z0),
                                               (x + half + 0.12, y + half + 0.12, Z0 + 0.25), MARBLE, bottom=False))
    painted(builder, RELIEF_GROUND, lambda: builder.box((x - half, y - half, Z0 + 0.25),
                                                       (x + half, y + half, Z0 + PEDESTAL - 0.2), MARBLE, bottom=False,
                                                       top=False))
    painted(builder, WHITE, lambda: builder.box((x - half - 0.1, y - half - 0.1, Z0 + PEDESTAL - 0.2),
                                               (x + half + 0.1, y + half + 0.1, Z0 + PEDESTAL), MARBLE, bottom=False))
    scale = (PEDESTAL - 0.5) / 1.7
    faces = [((0.0, -1.0), (-0.85, 0.0, 0.85)), ((-1.0, 0.0), (-0.5, 0.5)), ((1.0, 0.0), (-0.5, 0.5))]
    count = 0
    for (nx, ny), offsets in faces:
        turn = math.atan2(ny, nx)
        for offset in offsets:
            px = x + nx * (half + 0.05) - ny * offset
            py = y + ny * (half + 0.05) + nx * offset
            figure = relief_figure(seed * 17 + count + 300, (seed + count) % 3)
            builder.merge(figure, Matrix.Translation((px, py, Z0 + 0.27)) @ Matrix.Rotation(turn - math.pi / 2, 4, "Z")
                          @ Matrix.Scale(scale, 4))
            count += 1


def column_frames():
    outer, inner, porch = column_positions()
    frames = {"plain": [], "caelata_0": [], "caelata_1": [], "caelata_2": []}
    count = 0
    for x, y, kind in outer + inner + porch:
        matrix = Matrix.Translation((x, y, Z0))
        if kind == "front" and abs(y + HALF_Y) < 0.1:
            matrix = Matrix.Translation((x, y, Z0 + PEDESTAL)) @ Matrix.Diagonal((1.0, 1.0, (H - PEDESTAL) / H, 1.0))
        if sculpted((x, y, kind)):
            frames[f"caelata_{count % 3}"].append(matrix)
            count += 1
        else:
            frames["plain"].append(matrix)
    return frames


def artemis_statue():
    builder = MeshBuilder()
    gold = (0.98, 0.78, 0.36)
    painted(builder, WHITE, lambda: builder.box((-1.2, -1.0, 0.0), (1.2, 1.0, 1.4), MARBLE, bottom=False))
    painted(builder, RED, lambda: builder.box((-1.22, -1.02, 0.5), (1.22, 1.02, 0.9), MARBLE, bottom=False,
                                             top=False))
    painted(builder, gold, lambda: builder.box((-1.3, -1.1, 1.4), (1.3, 1.1, 1.55), GILT, bottom=False))
    z = 1.55
    squash = Matrix.Translation((0.0, 0.0, z)) @ Matrix.Diagonal((1.0, 0.72, 1.0, 1.0))
    sheath = [(0.0, 0.0), (0.3, 0.0), (0.3, 0.08), (0.27, 0.2), (0.32, 0.9), (0.38, 1.6), (0.42, 1.95)]
    painted(builder, (0.30, 0.14, 0.12), lambda: builder.lathe(sheath, 20, MATTE, smooth=True, matrix=squash,
                                                               caps=False))
    registers = [0.35, 0.68, 1.0, 1.32, 1.62]
    for k, height in enumerate(registers):
        radius = 0.3 + 0.07 * height
        colour = DEEP_BLUE if k % 2 else (0.52, 0.10, 0.10)
        painted(builder, gold, lambda height=height, radius=radius: builder.lathe(
            [(radius + 0.015, height - 0.14), (radius + 0.015, height - 0.12)], 20, GILT, smooth=True, matrix=squash,
            caps=False))
        for j in range(3):
            angle = -math.pi / 2 + (j - 1) * 0.7
            p = squash @ Vector((radius * math.cos(angle), radius * math.sin(angle), height))
            painted(builder, colour, lambda p=p: builder.box((p.x - 0.13, p.y - 0.03, p.z - 0.1),
                                                            (p.x + 0.13, p.y + 0.02, p.z + 0.1), MATTE))
            ellipsoid(builder, (p.x, p.y - 0.05, p.z), (0.07, 0.04, 0.06), gold, 6, 3, GILT)
    top = z + 1.95
    torso = Matrix.Translation((0.0, 0.0, top)) @ Matrix.Diagonal((1.0, 0.75, 1.0, 1.0))
    painted(builder, (0.36, 0.16, 0.12), lambda: builder.lathe([(0.42, 0.0), (0.4, 0.3), (0.36, 0.55), (0.18, 0.66),
                                                                (0.0, 0.68)], 20, MATTE, smooth=True, matrix=torso,
                                                               caps=False))
    for row, (height, count, radius) in enumerate(((0.1, 6, 0.37), (0.24, 7, 0.38), (0.38, 6, 0.36))):
        for k in range(count):
            angle = -math.pi / 2 + (k - (count - 1) / 2) * 0.32
            p = torso @ Vector((radius * math.cos(angle), radius * math.sin(angle), height))
            ellipsoid(builder, (p.x, p.y - 0.04, p.z), (0.07, 0.07, 0.085), AMBER if row % 2 else gold, 7, 4, GILT)
    neck = top + 0.66
    painted(builder, gold, lambda: builder.lathe(torus_arc(0.2, neck - 0.05, 0.04, -90, 90, 3), 16, GILT, smooth=True,
                                                 caps=False))
    ellipsoid(builder, (0.0, 0.0, neck + 0.08), (0.08, 0.08, 0.1), EBONY, 8, 4)
    ellipsoid(builder, (0.0, -0.02, neck + 0.3), (0.15, 0.17, 0.2), EBONY, 10, 6)
    ellipsoid(builder, (0.0, 0.03, neck + 0.36), (0.16, 0.16, 0.16), (0.12, 0.08, 0.06), 10, 5)
    polos = Matrix.Translation((0.0, 0.02, neck + 0.45))
    painted(builder, gold, lambda: builder.lathe([(0.16, 0.0), (0.2, 0.42), (0.23, 0.48), (0.0, 0.48)], 16, GILT,
                                                 smooth=False, matrix=polos))
    for k in range(5):
        angle = -math.pi / 2 + (k - 2) * 0.42
        p = polos @ Vector((0.19 * math.cos(angle), 0.19 * math.sin(angle), 0.22))
        builder.oriented([(p.x - 0.03, p.y - 0.01, p.z - 0.1), (p.x + 0.03, p.y - 0.01, p.z - 0.1),
                          (p.x + 0.03, p.y - 0.01, p.z + 0.08), (p.x - 0.03, p.y - 0.01, p.z + 0.08)],
                         (math.cos(angle), math.sin(angle), 0), VOID)
    disc = Matrix.Translation((0.0, 0.2, neck + 0.32)) @ Matrix.Rotation(math.radians(90), 4, "X")
    painted(builder, gold, lambda: builder.lathe([(0.0, 0.0), (0.62, 0.0), (0.62, 0.04), (0.0, 0.04)], 24, GILT,
                                                 smooth=False, matrix=disc))
    painted(builder, DEEP_BLUE, lambda: builder.lathe([(0.5, -0.01), (0.56, -0.01)], 24, MATTE, smooth=False,
                                                      matrix=disc, caps=False))
    for side in (-1, 1):
        shoulder = Vector((side * 0.34, -0.02, top + 0.5))
        elbow = Vector((side * 0.4, -0.1, top + 0.22))
        hand = Vector((side * 0.46, -0.5, top + 0.2))
        tube(builder, [shoulder, elbow], [0.09, 0.075], (0.36, 0.16, 0.12), 6)
        tube(builder, [elbow, hand], [0.075, 0.055], EBONY, 6)
        ellipsoid(builder, hand + Vector((0.0, -0.05, 0.0)), (0.06, 0.08, 0.05), EBONY, 6, 3)
        fillet = [hand + Vector((0.0, -0.08, 0.0)), hand + Vector((side * 0.06, -0.12, -0.6)),
                  Vector((hand.x + side * 0.1, hand.y - 0.1, z + 0.6)), Vector((hand.x + side * 0.12, hand.y - 0.05,
                                                                               z + 0.05))]
        tube(builder, fillet, [0.03, 0.035, 0.035, 0.03], (0.96, 0.92, 0.82), 4)
        for k in range(5):
            p = fillet[1].lerp(fillet[2], k / 4)
            ellipsoid(builder, (p.x, p.y - 0.02, p.z), (0.05, 0.03, 0.04), gold, 5, 3, GILT)
    return builder


def naiskos():
    builder = MeshBuilder()
    painted(builder, WHITE, lambda: builder.box((-4.6, -4.2, 0.0), (4.6, 5.0, 1.0), MARBLE, bottom=False))
    painted(builder, (0.99, 0.96, 0.9), lambda: builder.box((-4.4, -4.0, 9.9), (4.4, 4.8, 11.2), MARBLE))
    painted(builder, RED, lambda: builder.box((-4.45, -4.05, 10.5), (4.45, 4.85, 10.8), MARBLE, bottom=False,
                                             top=False))
    tri = [(-4.6, -4.2, 11.2), (4.6, -4.2, 11.2), (0.0, -4.2, 13.4)]
    painted(builder, DEEP_BLUE, lambda: builder.oriented(tri, (0, -1, 0), MARBLE))
    gable_roof(builder, -4.4, 5.0, 4.8, 11.2, 13.4, MARBLE, along_axis="y", imbrex=False)
    builder.tint(len(builder.polygons) - 2, (0.96, 0.92, 0.84))
    painted(builder, (0.40, 0.08, 0.10), lambda: builder.oriented([(-3.8, 4.4, 1.0), (3.8, 4.4, 1.0), (3.8, 4.4, 9.9),
                                                                   (-3.8, 4.4, 9.9)], (0, -1, 0), MATTE))
    return builder


def naiskos_column():
    return ionic_column(0.82, 8.9, False)


def lampstand():
    builder = MeshBuilder()
    gold = (0.95, 0.72, 0.34)
    for k in range(3):
        angle = TAU * k / 3
        tube(builder, [(0.0, 0.0, 0.3), (0.35 * math.cos(angle), 0.35 * math.sin(angle), 0.0)], [0.04, 0.03], gold, 4,
             GILT)
    tube(builder, [(0.0, 0.0, 0.2), (0.0, 0.0, 2.4)], [0.05, 0.035], gold, 6, GILT)
    painted(builder, gold, lambda: builder.lathe([(0.0, 2.4), (0.22, 2.42), (0.24, 2.52), (0.0, 2.5)], 8, GILT))
    ellipsoid(builder, (0.0, 0.0, 2.62), (0.07, 0.07, 0.14), (1.0, 0.82, 0.40), 6, 3, MATTE)
    return builder


def altar_court():
    builder = MeshBuilder()
    frames = []
    hx, hy = 18.0, 20.0
    base = 1.6
    painted(builder, WHITE, lambda: builder.box((-hx, -hy, -1.0), (hx, hy, base), ASHLAR, bottom=False))
    for k in range(6):
        y0 = hy + k * 0.4
        top = base - (k + 1) * base / 7
        painted(builder, WHITE, lambda y0=y0, top=top: builder.box((-hx + 3.0, y0, -1.0), (hx - 3.0, y0 + 0.4, top),
                                                                   MARBLE, bottom=False))
    painted(builder, (0.96, 0.93, 0.86), lambda: builder.box((-hx + 0.3, -hy + 0.3, base - 0.01),
                                                             (hx - 0.3, hy - 0.3, base + 0.03), POLYGONAL,
                                                             bottom=False))
    wall = 4.6
    for x0, y0, x1, y1 in ((-hx, -hy, hx, -hy + 1.2), (-hx, -hy, -hx + 1.2, hy - 4.0), (hx - 1.2, -hy, hx, hy - 4.0)):
        painted(builder, (0.98, 0.95, 0.9), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, base),
                                                                                         (x1, y1, base + wall),
                                                                                         ASHLAR, bottom=False))
    for x0, x1 in ((-hx, -hx + 1.2), (hx - 1.2, hx)):
        painted(builder, (0.98, 0.95, 0.9), lambda x0=x0, x1=x1: builder.box((x0, -hy, base + wall),
                                                                           (x1, hy - 4.0, base + wall + 0.5), MARBLE))
    painted(builder, (0.98, 0.95, 0.9), lambda: builder.box((-hx, -hy, base + wall), (hx, -hy + 1.2, base + wall + 0.5),
                                                            MARBLE))
    column_h = 6.4
    for k in range(9):
        x = -hx + 3.5 + k * (2 * hx - 7.0) / 8
        frames.append(Matrix.Translation((x, -hy + 0.6, base + wall + 0.5)) @ Matrix.Scale(column_h / H, 4))
    for k in range(9):
        y = -hy + 3.5 + k * (2 * hy - 9.0) / 8
        for x in (-hx + 0.6, hx - 0.6):
            frames.append(Matrix.Translation((x, y, base + wall + 0.5)) @ Matrix.Scale(column_h / H, 4))
    roof_z = base + wall + 0.5 + column_h
    for x0, y0, x1, y1 in ((-hx - 0.3, -hy - 0.3, hx + 0.3, -hy + 1.5), (-hx - 0.3, -hy - 0.3, -hx + 1.5, hy - 3.6),
                           (hx - 1.5, -hy - 0.3, hx + 0.3, hy - 3.6)):
        painted(builder, WHITE, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, roof_z), (x1, y1, roof_z + 0.9),
                                                                               MARBLE))
        painted(builder, RED, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0 - 0.02, y0 - 0.02, roof_z + 0.45),
                                                                             (x1 + 0.02, y1 + 0.02, roof_z + 0.62),
                                                                             MARBLE, bottom=False, top=False))
    for x in range(-15, 16, 5):
        ellipsoid(builder, (x, -hy - 0.15, base + wall * 0.55), (0.8, 0.3, 0.8), (0.86, 0.80, 0.70), 8, 4, MARBLE)
    altar = [(-5.5, -7.0, base, 1.2), (-4.6, -6.0, base + 1.2, 2.8), (-4.0, -5.4, base + 2.8, 3.4)]
    for x0, y0, z0, z1 in altar:
        painted(builder, WHITE, lambda x0=x0, y0=y0, z0=z0, z1=z1: builder.box((x0, y0, z0), (-x0, -y0 - 2.0,
                                                                                            base + z1),
                                                                               MARBLE, bottom=False))
    painted(builder, RED, lambda: builder.box((-4.65, -6.05, base + 1.9), (4.65, 4.05, base + 2.3), MARBLE,
                                             bottom=False, top=False))
    for k in range(6):
        y = 4.2 + k * 0.45
        painted(builder, WHITE, lambda y=y, k=k: builder.box((-3.0, y, base), (3.0, y + 0.45,
                                                                                base + 3.0 - k * 0.5), MARBLE,
                                                             bottom=False))
    ellipsoid(builder, (0.0, -1.0, base + 3.45), (1.6, 1.2, 0.25), (0.26, 0.22, 0.20), 8, 3)
    ellipsoid(builder, (0.0, -1.0, base + 3.6), (0.8, 0.6, 0.35), (0.98, 0.62, 0.22), 7, 3)
    return builder, frames, Vector((0.0, -1.0, base + 4.0)), base


def propylon(width=16.0, depth=10.0, height=8.0):
    builder = MeshBuilder()
    frames = []
    hw, hd = width / 2, depth / 2
    for x0, x1 in ((-hw - 3.0, -2.6), (2.6, hw + 3.0)):
        painted(builder, (0.96, 0.92, 0.84), lambda x0=x0, x1=x1: builder.box((x0, -hd, -1.0), (x1, hd, height + 1.6),
                                                                              ASHLAR, bottom=False))
    painted(builder, WHITE, lambda: builder.box((-2.6, -hd, height), (2.6, hd, height + 1.6), MARBLE))
    painted(builder, (0.94, 0.90, 0.82), lambda: builder.box((-hw - 3.2, -hd - 0.2, -0.1), (hw + 3.2, hd + 0.2, 0.15),
                                                             MARBLE, bottom=False))
    for x in (-1.3, 1.3):
        frames.append(Matrix.Translation((x, -hd + 0.6, 0.15)) @ Matrix.Scale((height - 0.15) / H, 4))
        frames.append(Matrix.Translation((x, hd - 0.6, 0.15)) @ Matrix.Scale((height - 0.15) / H, 4))
    for y, facing in ((-hd, -1), (hd, 1)):
        tri = [(-hw - 3.2, y, height + 1.6), (hw + 3.2, y, height + 1.6), (0.0, y, height + 4.0)]
        painted(builder, DEEP_BLUE if facing < 0 else WHITE, lambda tri=tri, facing=facing: builder.oriented(
            tri, (0, facing, 0), MARBLE))
    gable_roof(builder, -hd - 0.3, hd + 0.3, hw + 3.4, height + 1.6, height + 4.0, TILES, along_axis="y", imbrex=False)
    plaque = (0.95, 0.93, 0.88)
    for x0, x1 in ((-hw - 2.6, -3.4), (3.4, hw + 2.6)):
        painted(builder, plaque, lambda x0=x0, x1=x1: builder.box((x0, -hd - 0.12, 3.0), (x1, -hd, 5.2), MARBLE,
                                                                  bottom=False))
        for line in range(5):
            z = 4.85 - line * 0.38
            painted(builder, (0.30, 0.22, 0.20), lambda x0=x0, x1=x1, z=z: builder.oriented(
                [(x0 + 0.3, -hd - 0.13, z), (x1 - 0.3, -hd - 0.13, z), (x1 - 0.3, -hd - 0.13, z + 0.16),
                 (x0 + 0.3, -hd - 0.13, z + 0.16)], (0, -1, 0), MARBLE))
    return builder, frames


def peribolos_segment(length=40.0, height=4.2):
    builder = MeshBuilder()
    painted(builder, (0.95, 0.90, 0.80), lambda: builder.box((0.0, -0.8, -1.5), (length, 0.8, height), ASHLAR,
                                                             bottom=False))
    painted(builder, (0.98, 0.95, 0.9), lambda: builder.box((-0.1, -0.95, height), (length + 0.1, 0.95, height + 0.35),
                                                            MARBLE))
    return builder


def statue_base_row(seed=0):
    from .nimes_figures import honorific_statue
    return honorific_statue(seed % 2 == 0)


def offering_table(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    painted(builder, WHITE, lambda: builder.box((-0.8, -0.5, 0.0), (0.8, 0.5, 0.9), MARBLE, bottom=False))
    for k in range(5):
        tone = rng.choice([(0.82, 0.52, 0.30), (0.95, 0.80, 0.40), (0.62, 0.70, 0.30), (0.90, 0.30, 0.20)])
        ellipsoid(builder, (-0.6 + k * 0.3, rng.uniform(-0.2, 0.2), 0.98), (0.1, 0.1, 0.08), tone, 6, 3)
    return builder


def figurine_stall(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    cloth = [(0.80, 0.18, 0.12), (0.94, 0.72, 0.22), (0.22, 0.40, 0.70), (0.96, 0.93, 0.86)][seed % 4]
    for k in range(5):
        x0 = -2.0 + k * 0.8
        quad = [(x0, -1.4, 2.4), (x0 + 0.8, -1.4, 2.4), (x0 + 0.8, 1.2, 2.9), (x0, 1.2, 2.9)]
        tone = cloth if k % 2 == 0 else (0.98, 0.95, 0.88)
        painted(builder, tone, lambda quad=quad: builder.oriented(quad, (0, -0.3, 1), MATTE))
        painted(builder, tuple(c * 0.7 for c in tone), lambda quad=quad: builder.oriented(list(reversed(quad)),
                                                                                          (0, 0.3, -1), MATTE))
    for x in (-1.9, 1.9):
        for y, z in ((-1.3, 2.4), (1.1, 2.9)):
            tube(builder, [(x, y, 0.0), (x, y, z)], [0.05, 0.05], (0.44, 0.32, 0.21), 4)
    painted(builder, (0.58, 0.44, 0.30), lambda: builder.box((-1.8, -0.9, 0.0), (1.8, 0.1, 0.85), MATTE, bottom=False))
    for k in range(9):
        x = -1.6 + k * 0.4
        tone = rng.choice([(0.86, 0.56, 0.36), (0.80, 0.48, 0.30), (0.92, 0.70, 0.50), (0.95, 0.85, 0.6)])
        tube(builder, [(x, -0.45, 0.85), (x, -0.45, 1.08)], [0.07, 0.04], tone, 5)
        ellipsoid(builder, (x, -0.45, 1.13), (0.04, 0.04, 0.05), tone, 5, 3)
    return builder


def ox(colour=(0.95, 0.92, 0.86), garland=True):
    from .nimes_figures import beast
    builder = beast("ox")
    builder.paint(MATTE, colour)
    if garland:
        drape(builder, (0.30, 0.52, 0.20), [(0.22, 1.25), (0.3, 1.0), (0.0, 0.9)], 8, folds=(6, 0.05, 0.0),
              squash=1.0, center=(0.0, 0.85))
        tube(builder, [(-0.3, 1.0, 1.15), (0.0, 1.05, 1.0), (0.3, 1.0, 1.15)], [0.04, 0.05, 0.04], (0.82, 0.20, 0.16),
             4)
    return builder


def votive_altar(seed=0):
    builder = MeshBuilder()
    painted(builder, WHITE, lambda: builder.box((-0.9, -0.7, -0.3), (0.9, 0.7, 0.25), MARBLE, bottom=False))
    painted(builder, (0.98, 0.95, 0.9), lambda: builder.box((-0.7, -0.5, 0.25), (0.7, 0.5, 1.2), MARBLE, bottom=False))
    painted(builder, RED, lambda: builder.box((-0.72, -0.52, 0.85), (0.72, 0.52, 1.0), MARBLE, bottom=False,
                                             top=False))
    painted(builder, WHITE, lambda: builder.box((-0.8, -0.6, 1.2), (0.8, 0.6, 1.4), MARBLE))
    for x in (-0.6, 0.6):
        tube(builder, [(x, -0.6, 1.5), (x, 0.6, 1.5)], [0.12, 0.12], (0.96, 0.92, 0.86), 6, MARBLE)
    ellipsoid(builder, (0.0, 0.0, 1.45), (0.3, 0.2, 0.08), (0.86, 0.66, 0.30), 6, 3)
    return builder


def votive_stele(seed=0):
    builder = MeshBuilder()
    painted(builder, WHITE, lambda: builder.box((-0.6, -0.3, -0.3), (0.6, 0.3, 0.3), MARBLE, bottom=False))
    painted(builder, (0.97, 0.94, 0.88), lambda: builder.box((-0.45, -0.12, 0.3), (0.45, 0.12, 2.3), MARBLE,
                                                             bottom=False))
    painted(builder, DEEP_BLUE, lambda: builder.box((-0.36, -0.13, 1.4), (0.36, -0.12, 2.0), MARBLE, bottom=False,
                                                   top=False))
    for line in range(5):
        z = 0.5 + line * 0.16
        painted(builder, (0.40, 0.26, 0.22), lambda z=z: builder.oriented(
            [(-0.34, -0.125, z), (0.34, -0.125, z), (0.34, -0.125, z + 0.07), (-0.34, -0.125, z + 0.07)], (0, -1, 0),
            MARBLE))
    tri = [(-0.5, -0.13, 2.3), (0.5, -0.13, 2.3), (0.0, -0.13, 2.65)]
    painted(builder, RED, lambda: builder.oriented(tri, (0, -1, 0), MARBLE))
    tri = [(0.5, 0.13, 2.3), (-0.5, 0.13, 2.3), (0.0, 0.13, 2.65)]
    painted(builder, WHITE, lambda: builder.oriented(tri, (0, 1, 0), MARBLE))
    builder.surface([[(-0.5, -0.13, 2.3), (0.0, -0.13, 2.65), (0.5, -0.13, 2.3)],
                     [(-0.5, 0.13, 2.3), (0.0, 0.13, 2.65), (0.5, 0.13, 2.3)]], MARBLE, facing=(0, 0, 1))
    return builder

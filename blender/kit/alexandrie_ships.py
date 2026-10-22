import math
import random

from mathutils import Matrix, Vector

from .alexandrie_pharos import painted
from .arles_life import amphora_shape, hull_sections
from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import Look, coarse, ellipsoid, person, tube

PLANK = "matte"
GILT = "bronze_gilt"
PITCH = (0.14, 0.11, 0.09)
TIMBER = (0.50, 0.36, 0.24)
DECK = (0.78, 0.64, 0.46)
ROPE = (0.34, 0.28, 0.20)
LINEN = (0.94, 0.90, 0.80)
SAILS = [(0.95, 0.91, 0.80), (0.92, 0.84, 0.68), (0.90, 0.74, 0.56), (0.96, 0.93, 0.86)]
BANDS = [(0.70, 0.16, 0.10), (0.16, 0.34, 0.62), (0.86, 0.66, 0.20), (0.22, 0.46, 0.36), (0.92, 0.90, 0.84)]
TAU = 2 * math.pi


def darker(colour, factor=0.72):
    return tuple(c * factor for c in colour)


def hull(builder, length, beam, freeboard, draft, sheer_bow, sheer_stern, band, seed=0, stations=16):
    half = length / 2
    rows = []
    for index in range(stations + 1):
        s = -half + length * index / stations
        t = s / half
        fullness = max(1.0 - abs(t) ** 2.3, 0.03)
        w = beam / 2 * fullness ** 0.55
        rise = sheer_bow if t > 0 else sheer_stern
        sheer = freeboard + rise * t * t
        keel = -draft * fullness ** 0.35
        ring = []
        for k in range(7):
            angle = math.radians(-90 + 90 * k / 6)
            x = w * math.cos(angle) * (0.12 + 0.88 * k / 6) ** 0.5
            z = keel * -math.sin(angle) + sheer * (k / 6) ** 1.5 * (1 if k else 0)
            ring.append((x, s, z))
        rows.append([(-x, y, z) for x, y, z in reversed(ring)] + [(x, y, z) for x, y, z in ring[1:]])
    hull_sections(builder, rows, PLANK, PLANK, darker(DECK, 0.8), PITCH)
    first = len(builder.polygons)
    for a, b in zip(rows[:-1], rows[1:]):
        for edge, facing in ((0, -1), (-1, 1)):
            pa, pb = a[edge], b[edge]
            builder.surface([[(pa[0] * 1.005, pa[1], pa[2] - 0.55), (pa[0] * 1.005, pa[1], pa[2] - 0.05)],
                             [(pb[0] * 1.005, pb[1], pb[2] - 0.55), (pb[0] * 1.005, pb[1], pb[2] - 0.05)]], MATTE,
                            facing=(facing, 0, 0))
    builder.tint(first, band)
    first = len(builder.polygons)
    for a, b in zip(rows[:-1], rows[1:]):
        for edge, facing in ((0, -1), (-1, 1)):
            pa, pb = a[edge], b[edge]
            builder.surface([[(pa[0] * 1.004, pa[1], 0.05), (pa[0] * 1.004, pa[1], 0.35)],
                             [(pb[0] * 1.004, pb[1], 0.05), (pb[0] * 1.004, pb[1], 0.35)]], MATTE,
                            facing=(facing, 0, 0))
    builder.tint(first, (0.86, 0.84, 0.78))
    return rows


def deck(builder, length, beam, z, fraction=0.78):
    half = length / 2
    painted(builder, DECK, lambda: builder.box((-beam / 2 * 0.86, -half * fraction, z - 0.12),
                                               (beam / 2 * 0.86, half * fraction * 0.94, z), PLANK, bottom=False))


def mast(builder, y, z0, height, radius=0.24):
    tube(builder, [(0.0, y, z0), (0.0, y, z0 + height)], [radius, radius * 0.6], TIMBER, 8, PLANK)
    ellipsoid(builder, (0.0, y, z0 + height + 0.1), (radius * 0.8, radius * 0.8, radius), TIMBER, 5, 2)


def square_sail(builder, y, z_top, span, drop, belly, colour, set_sail=True, bands=0, band_colour=None):
    if set_sail:
        tube(builder, [(-span / 2 - 0.3, y + 0.25, z_top), (span / 2 + 0.3, y + 0.25, z_top)], [0.12, 0.12], TIMBER, 6,
             PLANK)
        rows = []
        for k in range(6):
            v = k / 5
            z = z_top - 0.2 - v * drop
            row = []
            for j in range(9):
                u = -1.0 + 2.0 * j / 8
                bulge = belly * (1 - u * u) * math.sin(math.pi * (0.12 + 0.88 * v)) + 0.25 * v * belly
                row.append((u * (span / 2 - 0.25 * v), y + 0.45 + bulge, z))
            rows.append(row)
        painted(builder, colour, lambda: builder.surface(rows, MATTE, smooth=True, facing=(0, 1, 0)))
        painted(builder, darker(colour, 0.8), lambda: builder.surface(rows, MATTE, smooth=True, facing=(0, -1, 0)))
        if bands and band_colour is not None:
            for k in range(bands):
                column = 1 + int(round((k + 0.5) * 7 / bands))
                column = min(column, 7)
                strip = [[rows[r][column] for r in range(6)], [rows[r][column + 1] for r in range(6)]]
                lifted = [[(p[0], p[1] + 0.03, p[2]) for p in line] for line in strip]
                painted(builder, band_colour, lambda lifted=lifted: builder.surface(lifted, MATTE, smooth=True,
                                                                                    facing=(0, 1, 0)))
        for j in (2, 4, 6):
            line = [rows[r][j] for r in range(6)]
            for a, b in zip(line[:-1], line[1:]):
                tube(builder, [Vector(a) + Vector((0, -0.04, 0)), Vector(b) + Vector((0, -0.04, 0))], [0.02, 0.02],
                     ROPE, 3, cap=False)
        return rows[-1]
    tube(builder, [(-span / 2, y + 0.25, z_top), (span / 2, y + 0.25, z_top)], [0.11, 0.11], TIMBER, 6, PLANK)
    frame = Matrix.Translation((0.0, y + 0.42, z_top - 0.35)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
    painted(builder, colour, lambda: builder.lathe(
        [(0.0, -span / 2), (0.24, -span / 2 + 0.9), (0.4, -span / 4), (0.44, 0.0), (0.4, span / 4),
         (0.24, span / 2 - 0.9), (0.0, span / 2)], 7, MATTE, smooth=True,
        matrix=frame @ Matrix.Diagonal((1.0, 0.75, 1.0, 1.0)), caps=False))
    for x in (-span * 0.36, -span * 0.12, span * 0.12, span * 0.36):
        tube(builder, [(x, y + 0.75, z_top - 0.6), (x * 0.4, y + 0.3, z_top - 6.0)], [0.015, 0.015], ROPE, 3,
             cap=False)
    return None


def stern_post(builder, half, z, scale, colour=PITCH, gilt=False):
    points = [Vector((0.0, -half + 0.4, z - 0.6)), Vector((0.0, -half - 0.8 * scale, z + 0.8 * scale)),
              Vector((0.0, -half - 0.9 * scale, z + 2.0 * scale)), Vector((0.0, -half - 0.4 * scale, z + 2.7 * scale)),
              Vector((0.0, -half + 0.3 * scale, z + 2.5 * scale))]
    radii = [0.28 * scale, 0.24 * scale, 0.2 * scale, 0.17 * scale, 0.12 * scale]
    tube(builder, points, radii, (1.0, 0.9, 0.7) if gilt else colour, 7, GILT if gilt else PLANK)
    ellipsoid(builder, points[-1] + Vector((0.0, 0.18 * scale, 0.05)), (0.17 * scale, 0.3 * scale, 0.22 * scale),
              (1.0, 0.9, 0.7) if gilt else (0.92, 0.88, 0.8), 6, 3, GILT if gilt else MATTE)


def steering_oars(builder, half, beam, z):
    for side in (-1, 1):
        tube(builder, [(side * beam * 0.42, -half + 2.6, z + 1.0), (side * beam * 0.48, -half - 1.6, -1.2)],
             [0.1, 0.08], TIMBER, 5, PLANK)
        frame = Matrix.Translation((side * beam * 0.48, -half - 1.4, -1.0)) @ Matrix.Rotation(math.radians(-20), 4, "X")
        painted(builder, TIMBER, lambda frame=frame: builder.centered_box((0.0, 0.0, 0.0), (0.1, 1.3, 1.9), PLANK,
                                                                          matrix=frame))


def eyes(builder, half, beam, z):
    for side in (-1, 1):
        ellipsoid(builder, (side * beam * 0.2, half * 0.86, z), (0.05, 0.32, 0.2), (0.95, 0.94, 0.9), 6, 3)
        ellipsoid(builder, (side * beam * 0.205, half * 0.86, z), (0.06, 0.12, 0.12), (0.08, 0.07, 0.06), 5, 2)


def crew(builder, spots, seed):
    rng = random.Random(seed)
    looks = [Look("undyed", hem=0.56, skin=2, hair=1, belt="brown", arms="swing", exomis=True, seed=seed),
             Look("woad", hem=0.56, skin=1, hair=3, belt="dark", arms="down", hat=(0.62, 0.52, 0.34), seed=seed + 1),
             Look("madder", hem=0.56, skin=2, hair=0, belt="brown", arms="carry", carry="amphora", seed=seed + 2)]
    for index, (x, y, z, heading) in enumerate(spots):
        look = looks[(index + rng.randrange(3)) % len(looks)]
        builder.merge(coarse(lambda look=look: person(look), 0.5), placement(x, y, z, heading))


def grain_carrier(seed=0, sail="set", length=40.0, beam=11.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    half = length / 2
    band = BANDS[rng.randrange(len(BANDS))]
    hull(builder, length, beam, 3.4, 2.6, 2.6, 2.0, band, seed)
    z = 3.0
    deck(builder, length, beam, z)
    painted(builder, (0.86, 0.74, 0.56), lambda: builder.box((-3.0, -half + 2.2, z), (3.0, -half + 7.5, z + 2.6), MATTE,
                                                             bottom=False))
    painted(builder, band, lambda: builder.box((-3.3, -half + 1.9, z + 2.6), (3.3, -half + 7.8, z + 2.9), MATTE))
    for x in (-1.6, 1.6):
        builder.oriented([(x - 0.4, -half + 7.52, z + 0.6), (x + 0.4, -half + 7.52, z + 0.6), (x + 0.4, -half + 7.52,
                                                                                               z + 1.9),
                          (x - 0.4, -half + 7.52, z + 1.9)], (0, 1, 0), "shadow_void")
    stern_post(builder, half, z + 1.8, 1.9, gilt=True)
    steering_oars(builder, half, beam, z)
    eyes(builder, half, beam, z - 0.6)
    tube(builder, [(0.0, half - 1.0, z), (0.0, half + 4.6, z + 6.0)], [0.2, 0.13], TIMBER, 6, PLANK)
    tube(builder, [(-2.2, half + 3.9, z + 5.2), (2.2, half + 3.9, z + 5.2)], [0.08, 0.08], TIMBER, 5, PLANK)
    main_y = 1.5
    main_height = 26.0
    mast(builder, main_y, z, main_height, 0.42)
    colour = SAILS[rng.randrange(len(SAILS))]
    yard = z + main_height - 2.0
    if sail == "set":
        square_sail(builder, main_y, yard, 22.0, 16.0, 3.2, colour, True, 2, darker(band, 0.9))
        top = [(-5.0, main_y + 0.5, yard + 0.2), (5.0, main_y + 0.5, yard + 0.2), (0.0, main_y + 0.5, yard + 3.6)]
        painted(builder, colour, lambda: builder.oriented(top, (0, 1, 0), MATTE))
        painted(builder, darker(colour), lambda: builder.oriented(list(reversed(top)), (0, -1, 0), MATTE))
        fore = [[(-2.6, half + 4.1, z + 5.0), (2.6, half + 4.1, z + 5.0)], [(-2.4, half + 3.5, z + 1.8),
                                                                             (2.4, half + 3.5, z + 1.8)]]
        painted(builder, colour, lambda: builder.surface(fore, MATTE, facing=(0, 1, 0)))
        painted(builder, darker(colour), lambda: builder.surface(fore, MATTE, facing=(0, -1, 0)))
    else:
        square_sail(builder, main_y, yard, 21.0, 0.0, 0.0, colour, False)
    for x in (-10.5, 10.5):
        tube(builder, [(0.0, main_y, z + main_height - 0.4), (x, main_y + 0.25, yard + 0.05)], [0.025, 0.025], ROPE, 3,
             cap=False)
        tube(builder, [(x, main_y + 0.25, yard), (x * 0.25, -half + 1.0, z + 1.2)], [0.025, 0.025], ROPE, 3, cap=False)
    tube(builder, [(0.0, main_y, z + main_height - 0.3), (0.0, half + 4.6, z + 6.0)], [0.035, 0.035], ROPE, 3,
         cap=False)
    tube(builder, [(0.0, main_y, z + main_height - 0.3), (0.0, -half + 0.4, z + 4.8)], [0.035, 0.035], ROPE, 3,
         cap=False)
    for side in (-1, 1):
        for dy in (-0.8, -2.2, -3.6):
            tube(builder, [(0.0, main_y, z + main_height - 0.6), (side * beam * 0.45, main_y + dy, z + 0.3)],
                 [0.025, 0.025], ROPE, 3, cap=False)
    for k in range(10):
        center = Vector((-2.4 + (k % 4) * 1.6, 6.0 + (k // 4) * 1.5, z))
        amphora_shape(builder, placement(center.x, center.y, center.z, rng.uniform(0, 6.28)),
                      (0.70, 0.42, 0.28) if k % 3 else (0.80, 0.58, 0.40), MATTE, 6)
    for k in range(8):
        ellipsoid(builder, (-2.5 + (k % 4) * 1.7, -4.0 - (k // 4) * 1.4, z + 0.3), (0.7, 0.5, 0.32),
                  (0.86, 0.78, 0.60), 6, 3)
    crew(builder, [(0.6, -half + 3.0, z + 2.9, 0.4), (-1.2, 2.5, z, 1.2), (2.0, -1.0, z, -0.5), (-2.0, 9.0, z, 2.6)],
         seed)
    return builder


def merchant(seed=0, sail="brailed", length=22.0, beam=6.6):
    rng = random.Random(seed)
    builder = MeshBuilder()
    half = length / 2
    band = BANDS[rng.randrange(len(BANDS))]
    hull(builder, length, beam, 2.2, 1.5, 1.5, 1.2, band, seed)
    z = 1.9
    deck(builder, length, beam, z)
    painted(builder, (0.82, 0.70, 0.52), lambda: builder.box((-1.7, -half + 1.4, z), (1.7, -half + 4.6, z + 1.9), MATTE,
                                                             bottom=False))
    painted(builder, darker(band, 0.9), lambda: builder.box((-1.9, -half + 1.2, z + 1.9), (1.9, -half + 4.8, z + 2.1),
                                                            MATTE))
    stern_post(builder, half, z + 1.0, 1.1)
    steering_oars(builder, half, beam, z - 0.4)
    eyes(builder, half, beam, z - 0.4)
    tube(builder, [(0.0, half - 0.6, z), (0.0, half + 2.8, z + 3.8)], [0.12, 0.08], TIMBER, 5, PLANK)
    mast_y = 1.0
    height = 14.0
    mast(builder, mast_y, z, height, 0.22)
    colour = SAILS[rng.randrange(len(SAILS))]
    yard = z + height - 1.0
    if sail == "set":
        square_sail(builder, mast_y, yard, 12.0, 9.0, 1.8, colour, True, rng.choice((0, 2)), darker(band, 0.9))
        fore = [[(-1.5, half + 2.6, z + 3.4), (1.5, half + 2.6, z + 3.4)], [(-1.4, half + 2.2, z + 1.4),
                                                                             (1.4, half + 2.2, z + 1.4)]]
        painted(builder, colour, lambda: builder.surface(fore, MATTE, facing=(0, 1, 0)))
        painted(builder, darker(colour), lambda: builder.surface(fore, MATTE, facing=(0, -1, 0)))
    else:
        square_sail(builder, mast_y, yard, 12.0, 0.0, 0.0, colour, False)
    for x in (-6.0, 6.0):
        tube(builder, [(0.0, mast_y, z + height - 0.3), (x, mast_y + 0.25, yard + 0.05)], [0.018, 0.018], ROPE, 3,
             cap=False)
    tube(builder, [(0.0, mast_y, z + height - 0.2), (0.0, half + 2.8, z + 3.8)], [0.025, 0.025], ROPE, 3, cap=False)
    tube(builder, [(0.0, mast_y, z + height - 0.2), (0.0, -half + 0.4, z + 2.6)], [0.025, 0.025], ROPE, 3, cap=False)
    for side in (-1, 1):
        for dy in (-0.6, -1.8):
            tube(builder, [(0.0, mast_y, z + height - 0.4), (side * beam * 0.45, mast_y + dy, z + 0.2)],
                 [0.02, 0.02], ROPE, 3, cap=False)
    for k in range(9):
        center = Vector((-1.4 + (k % 3) * 1.4, -4.0 + (k // 3) * 1.3, z))
        amphora_shape(builder, placement(center.x, center.y, center.z, rng.uniform(0, 6.28)),
                      (0.70, 0.42, 0.28) if k % 3 else (0.80, 0.58, 0.40), MATTE, 6)
    crew(builder, [(0.3, -half + 2.4, z + 2.1, 0.2), (-1.0, 4.0, z, 2.0)], seed)
    return builder


def galley(seed=0, length=38.0, beam=5.4, state=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    half = length / 2
    band = (0.55, 0.12, 0.30) if state else BANDS[rng.randrange(3)]
    hull(builder, length, beam, 1.7, 1.0, 1.4, 1.8, band, seed, 18)
    z = 1.5
    deck(builder, length, beam, z, 0.86)
    for side in (-1, 1):
        painted(builder, band if state else darker(band, 0.85), lambda side=side: builder.box(
            (side * beam / 2 - (0.0 if side > 0 else 0.9), -half * 0.62, z - 0.5),
            (side * beam / 2 + (0.9 if side > 0 else 0.0), half * 0.62, z + 0.25), MATTE))
    ram = [Vector((0.0, half - 0.6, 0.1)), Vector((0.0, half + 1.4, 0.0)), Vector((0.0, half + 2.6, -0.05))]
    tube(builder, ram, [0.45, 0.32, 0.05], (0.95, 0.80, 0.55), 6, GILT)
    tube(builder, [(0.0, half - 0.2, z), (0.0, half + 0.6, z + 1.8), (0.0, half + 0.2, z + 3.0)], [0.22, 0.18, 0.1],
         band, 6, PLANK)
    aplustre = [Vector((0.0, -half + 0.6, z + 0.4)), Vector((0.0, -half - 0.6, z + 1.8)), Vector((0.0, -half - 0.4, z
                                                                                                    + 3.6)),
                Vector((0.0, -half + 0.6, z + 4.6)), Vector((0.0, -half + 1.4, z + 4.2))]
    tube(builder, aplustre, [0.26, 0.22, 0.18, 0.14, 0.06], (1.0, 0.88, 0.62) if state else band, 7,
         GILT if state else PLANK)
    for k in range(4):
        tube(builder, [(0.0, -half - 0.5 + 0.1 * k, z + 3.2 - 0.3 * k), (0.0, -half + 1.4 + 0.3 * k,
                                                                        z + 4.2 - 0.2 * k)],
             [0.04, 0.03], (1.0, 0.88, 0.62) if state else TIMBER, 4, GILT if state else PLANK)
    eyes(builder, half, beam, z - 0.5)
    steering_oars(builder, half, beam, z - 0.3)
    oars = 22
    for side in (-1, 1):
        for k in range(oars):
            y = -half * 0.56 + (half * 1.12) * k / (oars - 1)
            root = Vector((side * (beam / 2 + 0.6), y, z - 0.1))
            tip = Vector((side * (beam / 2 + 6.4), y - 0.6, -0.15))
            tube(builder, [root, tip], [0.05, 0.04], TIMBER, 3, PLANK)
            blade = tip + (tip - root).normalized() * 0.5
            builder.oriented([tip + Vector((0.0, -0.13, 0.03)), tip + Vector((0.0, 0.13, 0.03)),
                              blade + Vector((0.0, 0.13, 0.03)), blade + Vector((0.0, -0.13, 0.03))],
                             (0, 0, 1), PLANK)
    mast(builder, 2.0, z, 13.0, 0.2)
    sail_colour = (0.48, 0.12, 0.30) if state else SAILS[rng.randrange(len(SAILS))]
    square_sail(builder, 2.0, z + 12.0, 12.0, 0.0, 0.0, sail_colour, False)
    if state:
        awning = [(-2.4, -half + 1.0, z + 2.6), (2.4, -half + 1.0, z + 2.6), (2.4, -half + 9.0, z + 2.6),
                  (-2.4, -half + 9.0, z + 2.6)]
        painted(builder, (0.60, 0.12, 0.26), lambda: builder.oriented(awning, (0, 0, 1), MATTE))
        painted(builder, (0.40, 0.08, 0.18), lambda: builder.oriented(list(reversed(awning)), (0, 0, -1), MATTE))
        for x in (-2.3, 2.3):
            for y in (-half + 1.2, -half + 8.8):
                tube(builder, [(x, y, z), (x, y, z + 2.6)], [0.06, 0.06], (1.0, 0.88, 0.6), 4, GILT)
        for k, y in enumerate((half - 3.0, -half + 10.5, 6.0)):
            tube(builder, [(0.0, y, z), (0.0, y, z + 6.5)], [0.05, 0.05], TIMBER, 4, PLANK)
            tube(builder, [(-0.7, y, z + 6.4), (0.7, y, z + 6.4)], [0.035, 0.035], (1.0, 0.88, 0.6), 4, GILT)
            banner = [(-0.65, y, z + 6.35), (0.65, y, z + 6.35), (0.65, y, z + 5.0), (0.0, y, z + 4.6),
                      (-0.65, y, z + 5.0)]
            painted(builder, (0.78, 0.12, 0.10), lambda banner=banner: builder.oriented(banner, (0, 1, 0), MATTE))
            painted(builder, (0.78, 0.12, 0.10), lambda banner=banner: builder.oriented(list(reversed(banner)),
                                                                                        (0, -1, 0), MATTE))
            ellipsoid(builder, (0.0, y, z + 6.8), (0.16, 0.16, 0.16), (1.0, 0.88, 0.6), 6, 3, GILT)
        crew(builder, [(1.0, -half + 3.0, z, 0.3), (-1.0, -half + 4.5, z, 3.0), (0.0, half - 4.0, z, 0.0)], seed)
    else:
        crew(builder, [(0.4, -half + 2.0, z, 0.2), (-0.6, half - 5.0, z, 3.1)], seed)
    return builder


def fishing_boat(seed=0, length=8.0, beam=2.3, sail=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    band = BANDS[rng.randrange(len(BANDS))]
    hull(builder, length, beam, 0.75, 0.45, 0.45, 0.35, band, seed, 10)
    painted(builder, DECK, lambda: builder.box((-beam / 2 * 0.7, -length * 0.36, 0.25), (beam / 2 * 0.7, length * 0.36,
                                                                                          0.3), PLANK, bottom=False))
    tube(builder, [(0.0, length * 0.12, 0.25), (0.0, length * 0.12, 5.8)], [0.07, 0.05], TIMBER, 5, PLANK)
    colour = SAILS[rng.randrange(len(SAILS))]
    if sail:
        square_sail(builder, length * 0.12, 5.4, 4.4, 3.6, 0.7, colour, True)
    else:
        square_sail(builder, length * 0.12, 5.4, 4.2, 0.0, 0.0, colour, False)
    painted(builder, (0.56, 0.48, 0.34), lambda: builder.box((-0.5, -length * 0.3, 0.3), (0.5, -length * 0.1, 0.55),
                                                             MATTE, bottom=False))
    crew(builder, [(0.2, -length * 0.32, 0.3, 0.4), (-0.3, length * 0.25, 0.3, 2.8)][:1 + seed % 2], seed)
    return builder


def lighter(seed=0, length=11.0, beam=3.6, cargo="sacks"):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hull(builder, length, beam, 1.0, 0.7, 0.4, 0.3, BANDS[rng.randrange(len(BANDS))], seed, 10)
    painted(builder, DECK, lambda: builder.box((-beam / 2 * 0.75, -length * 0.38, 0.3), (beam / 2 * 0.75,
                                                                                          length * 0.38, 0.36), PLANK,
                                               bottom=False))
    for k in range(10 if cargo == "sacks" else 8):
        x = -0.9 + (k % 3) * 0.9
        y = -length * 0.25 + (k // 3) * 1.4
        if cargo == "sacks":
            ellipsoid(builder, (x, y, 0.62), (0.45, 0.62, 0.3), (0.88, 0.80, 0.62), 6, 3)
        else:
            amphora_shape(builder, placement(x, y, 0.36, rng.uniform(0, 6.0)), (0.72, 0.44, 0.28), MATTE, 6)
    for side in (-1, 1):
        for y in (-length * 0.2, length * 0.1):
            tube(builder, [(side * beam * 0.45, y, 0.8), (side * (beam / 2 + 2.8), y - 0.3, -0.05)], [0.04, 0.035],
                 TIMBER, 3, PLANK)
    crew(builder, [(0.4, -length * 0.42, 0.36, 0.0), (-0.5, length * 0.3, 0.36, 3.0)], seed)
    return builder


def nile_barge(seed=0, length=20.0, beam=5.2, sail="set"):
    rng = random.Random(seed)
    builder = MeshBuilder()
    band = BANDS[rng.randrange(len(BANDS))]
    hull(builder, length, beam, 1.4, 0.9, 1.6, 1.4, band, seed, 12)
    z = 1.2
    deck(builder, length, beam, z, 0.82)
    painted(builder, (0.84, 0.72, 0.5), lambda: builder.box((-1.8, -length / 2 + 1.0, z), (1.8, -length / 2 + 4.6,
                                                                                          z + 1.8), MATTE,
                                                             bottom=False))
    painted(builder, (0.30, 0.50, 0.30), lambda: builder.box((-2.0, -length / 2 + 0.8, z + 1.8),
                                                             (2.0, -length / 2 + 4.8, z + 2.0), MATTE))
    mast(builder, 2.0, z, 15.0, 0.2)
    colour = SAILS[rng.randrange(len(SAILS))]
    if sail == "set":
        square_sail(builder, 2.0, z + 14.6, 7.0, 11.0, 1.4, colour, True)
    else:
        square_sail(builder, 2.0, z + 14.6, 7.0, 0.0, 0.0, colour, False)
    steering_oars(builder, length / 2, beam, z - 0.3)
    for k in range(12):
        x = -1.6 + (k % 4) * 1.05
        y = 0.0 + (k // 4) * 1.4
        ellipsoid(builder, (x, y, z + 0.3), (0.48, 0.6, 0.3), (0.90, 0.80, 0.58), 6, 3)
    crew(builder, [(0.3, -length / 2 + 0.8, z + 2.0, 0.2), (1.0, 5.0, z, 1.6)], seed)
    return builder

import math
import random

from mathutils import Matrix, Vector

from .arles_life import PITCH, PLANK, amphora_light, ellipsoid, hull_sections, painted, seagoing_ship, tube
from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import Look, coarse, person

HULL = (0.55, 0.42, 0.30)
WOOD = (0.45, 0.33, 0.22)
ROPE = (0.32, 0.27, 0.2)
SAILCLOTH = [(0.94, 0.9, 0.8), (0.9, 0.82, 0.66), (0.86, 0.6, 0.42), (0.92, 0.88, 0.78)]
STRIPES = [(0.72, 0.16, 0.12), (0.16, 0.32, 0.6), (0.86, 0.66, 0.2), (0.2, 0.44, 0.3)]


def hull_stations(length, beam, draft, freeboard, fullness_power, count=14, sheer_rise=0.6):
    half = length / 2
    stations = []
    for index in range(count + 1):
        s = -half + length * index / count
        t = s / half
        fullness = max(1.0 - abs(t) ** fullness_power, 0.05)
        w = beam / 2 * fullness ** 0.55
        sheer = freeboard + sheer_rise * t * t + (0.3 * t if t > 0 else 0.0)
        keel = -draft * fullness ** 0.35
        ring = []
        for k in range(6):
            angle = math.radians(-90 + 90 * k / 5)
            ring.append((w * math.cos(angle) * (0.15 + 0.85 * k / 5) ** 0.5, s,
                         keel * -math.sin(angle) + sheer * (k / 5) ** 1.6 * (1 if k else 0)))
        stations.append([(-x, y, z) for x, y, z in reversed(ring)] + [(x, y, z) for x, y, z in ring[1:]])
    return stations


def wales(builder, stations, colour, offset=-0.1, height=0.22):
    first = len(builder.polygons)
    for station_a, station_b in zip(stations[:-1], stations[1:]):
        a0, a1 = station_a[0], station_a[-1]
        b0, b1 = station_b[0], station_b[-1]
        builder.surface([[(a0[0] * 1.01, a0[1], a0[2] + offset - height), (a0[0] * 1.01, a0[1], a0[2] + offset)],
                         [(b0[0] * 1.01, b0[1], b0[2] + offset - height), (b0[0] * 1.01, b0[1], b0[2] + offset)]], MATTE,
                        facing=(-1, 0, 0))
        builder.surface([[(a1[0] * 1.01, a1[1], a1[2] + offset - height), (a1[0] * 1.01, a1[1], a1[2] + offset)],
                         [(b1[0] * 1.01, b1[1], b1[2] + offset - height), (b1[0] * 1.01, b1[1], b1[2] + offset)]], MATTE,
                        facing=(1, 0, 0))
    builder.tint(first, colour)


def lateen(builder, mast, mast_height, yard_length, rake, set_sail, colour, side=1.0, tack_forward=0.62):
    top = Vector((0.0, mast.y, mast.z + mast_height))
    direction = Vector((0.0, -math.cos(rake), math.sin(rake)))
    fore = top - direction * yard_length * tack_forward
    peak = top + direction * yard_length * (1.0 - tack_forward)
    tube(builder, fore, peak, 0.11, 0.06, WOOD, 6, PLANK)
    if not set_sail:
        a = fore.lerp(peak, 0.08) + Vector((0.0, 0.0, -0.18))
        b = fore.lerp(peak, 0.9) + Vector((0.0, 0.0, -0.18))
        painted(builder, colour, lambda: builder.lathe([(0.0, 0.0), (0.22, 0.06), (0.26, 0.5), (0.2, 0.9), (0.0, 1.0)], 6,
                                                       MATTE, smooth=True,
                                                       matrix=Matrix.Translation(a)
                                                       @ (b - a).to_track_quat("Z", "X").to_matrix().to_4x4()
                                                       @ Matrix.Diagonal((1.0, 1.0, (b - a).length, 1.0))))
        return
    clew = Vector((side * 0.3, mast.y - yard_length * 0.42, mast.z + 1.4))
    rows = []
    steps = 6
    for i in range(steps + 1):
        u = i / steps
        upper = fore.lerp(peak, u)
        lower = fore.lerp(clew, u)
        row = []
        for j in range(5):
            v = j / 4
            p = upper.lerp(lower, v)
            belly = 1.6 * math.sin(math.pi * u) * math.sin(math.pi * min(v * 1.1, 1.0)) * (1.0 - 0.4 * u)
            row.append(p + Vector((side * belly, 0.0, 0.0)))
        rows.append(row)
    painted(builder, colour, lambda: builder.surface(rows, MATTE, smooth=True, facing=(side, 0, 0)))
    painted(builder, tuple(c * 0.8 for c in colour), lambda: builder.surface(rows, MATTE, smooth=True,
                                                                            facing=(-side, 0, 0)))
    tube(builder, peak, clew, 0.015, 0.015, ROPE, 3, caps=False)
    tube(builder, clew, Vector((side * 1.0, mast.y - yard_length * 0.45, mast.z + 0.6)), 0.015, 0.015, ROPE, 3,
         caps=False)


def crew(builder, spots, seed):
    rng = random.Random(seed)
    looks = [Look("woad", hem=0.55, skin=2, hair=0, belt="dark", arms="down", seed=seed),
             Look("undyed", hem=0.55, skin=1, hair=1, exomis=True, belt="brown", arms="shoulder", seed=seed + 1),
             Look("madder", hem=0.55, skin=2, hair=3, belt="dark", arms="gesture", seed=seed + 2)]
    for x, y, z, turn in spots:
        builder.merge(coarse(lambda: person(rng.choice(looks)), 0.55), placement(x, y, z, turn))


def dromon(seed=0, set_sail=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    length, beam = 32.0, 4.6
    stations = hull_stations(length, beam, 1.0, 1.5, 3.2, 16, 0.5)
    hull_sections(builder, stations, PLANK, PLANK, (0.58, 0.46, 0.34), (0.22, 0.17, 0.14))
    wales(builder, stations, STRIPES[seed % len(STRIPES)], -0.05, 0.3)
    deck = 1.3
    first = len(builder.polygons)
    builder.box((-beam / 2 * 0.82, -length / 2 * 0.82, deck - 0.1), (beam / 2 * 0.82, length / 2 * 0.8, deck), PLANK,
                bottom=False)
    builder.tint(first, (0.72, 0.6, 0.46))
    oars = 24
    for side in (-1, 1):
        for k in range(oars):
            y = -length * 0.31 + length * 0.62 * k / (oars - 1)
            hole = Vector((side * beam / 2 * 0.98, y, 1.25))
            blade = Vector((side * (beam / 2 + 4.2), y - 0.6, -0.15))
            tube(builder, hole + Vector((-side * 1.2, 0.3, 0.5)), blade, 0.04, 0.035, WOOD, 4, PLANK, caps=False)
            painted(builder, WOOD, lambda blade=blade, side=side: builder.box(
                (blade.x - 0.03, blade.y - 0.12, blade.z - 0.05), (blade.x + side * 0.9, blade.y + 0.12, blade.z + 0.08),
                PLANK, bottom=False))
    stern = [Vector((0.0, -length / 2 - 0.1, 1.9)), Vector((0.0, -length / 2 - 0.9, 3.0)), Vector((0.0, -length / 2 - 0.4, 3.9))]
    for a, b in zip(stern[:-1], stern[1:]):
        tube(builder, a, b, 0.18, 0.14, PITCH, 6, PLANK)
    tube(builder, (0.0, length / 2 - 0.2, 1.4), (0.0, length / 2 + 3.2, 1.0), 0.22, 0.08, (0.3, 0.24, 0.18), 6, PLANK)
    painted(builder, (0.66, 0.36, 0.25), lambda: builder.box((-1.7, -length / 2 + 0.8, deck), (1.7, -length / 2 + 4.2, deck + 1.0),
                                                            MATTE, bottom=False))
    painted(builder, (0.62, 0.16, 0.14), lambda: builder.oriented(
        [(-1.9, -length / 2 + 0.6, deck + 2.5), (1.9, -length / 2 + 0.6, deck + 2.5), (1.9, -length / 2 + 4.4, deck + 2.5),
         (-1.9, -length / 2 + 4.4, deck + 2.5)], (0, 0, 1), MATTE))
    for x in (-1.8, 1.8):
        tube(builder, (x, -length / 2 + 0.7, deck + 1.0), (x, -length / 2 + 0.7, deck + 2.5), 0.05, 0.05, WOOD, 4, PLANK)
        tube(builder, (x, -length / 2 + 4.3, deck + 1.0), (x, -length / 2 + 4.3, deck + 2.5), 0.05, 0.05, WOOD, 4, PLANK)
    for side in (-1, 1):
        tube(builder, (side * 2.1, -length / 2 + 2.0, 3.0), (side * 2.4, -length / 2 - 1.4, -0.7), 0.08, 0.06, WOOD, 5, PLANK)
    mast = Vector((0.0, length * 0.18, deck))
    tube(builder, mast, mast + Vector((0.0, 0.0, 11.5)), 0.2, 0.12, WOOD, 7, PLANK)
    lateen(builder, mast, 11.0, 22.0, math.radians(28), set_sail, SAILCLOTH[seed % len(SAILCLOTH)], 1.0 if seed % 2 else -1.0)
    tube(builder, mast + Vector((0.0, 0.0, 11.3)), (0.0, length / 2 + 2.6, 1.6), 0.02, 0.02, ROPE, 3, caps=False)
    tube(builder, mast + Vector((0.0, 0.0, 11.3)), (0.0, -length / 2 + 1.0, 3.6), 0.02, 0.02, ROPE, 3, caps=False)
    painted(builder, (0.78, 0.12, 0.12), lambda: builder.oriented(
        [(0.0, -length / 2 - 0.4, 4.0), (0.0, -length / 2 - 0.4, 4.8), (0.0, -length / 2 - 1.8, 4.5)], (1, 0, 0), MATTE))
    painted(builder, (0.78, 0.12, 0.12), lambda: builder.oriented(
        [(0.0, -length / 2 - 0.4, 4.0), (0.0, -length / 2 - 0.4, 4.8), (0.0, -length / 2 - 1.8, 4.5)], (-1, 0, 0), MATTE))
    spots = [(rng.uniform(-1.0, 1.0), rng.uniform(-length * 0.35, length * 0.35), deck, rng.uniform(0, 6.28))
             for _ in range(5)]
    spots.append((0.4, -length / 2 + 2.2, deck + 1.0, 0.0))
    crew(builder, spots, seed * 7 + 3)
    for side in (-1, 1):
        for k in range(10):
            y = -length / 2 * 0.55 + k * length * 0.11
            ellipsoid(builder, (side * (beam / 2 - 0.55), y, deck + 0.55), (0.16, 0.18, 0.2),
                      rng.choice([(0.5, 0.36, 0.26), (0.62, 0.5, 0.36), (0.42, 0.3, 0.2)]), 5, 2)
            ellipsoid(builder, (side * (beam / 2 - 0.55), y + 0.05, deck + 0.85), (0.09, 0.1, 0.11), (0.66, 0.48, 0.36), 5, 2)
    return builder


def merchantman(seed=0, set_sail=False, length=19.0, beam=6.2):
    rng = random.Random(seed)
    builder = MeshBuilder()
    stations = hull_stations(length, beam, 1.3, 2.0, 2.3, 14, 0.9)
    hull_sections(builder, stations, PLANK, PLANK, (0.6, 0.5, 0.4), HULL if seed % 2 else PITCH)
    wales(builder, stations, STRIPES[(seed + 1) % len(STRIPES)], -0.05, 0.18)
    wales(builder, stations, (0.3, 0.22, 0.16), -0.7, 0.14)
    deck = 1.75
    first = len(builder.polygons)
    builder.box((-beam / 2 * 0.84, -length / 2 * 0.78, deck - 0.1), (beam / 2 * 0.84, length / 2 * 0.72, deck), PLANK,
                bottom=False)
    builder.tint(first, (0.74, 0.62, 0.48))
    painted(builder, (0.78, 0.62, 0.44), lambda: builder.box((-1.7, -length / 2 + 1.0, deck), (1.7, -length / 2 + 4.0, deck + 1.9),
                                                            MATTE, bottom=False))
    painted(builder, (0.68, 0.34, 0.22), lambda: builder.oriented(
        [(-1.9, -length / 2 + 0.8, deck + 1.9), (1.9, -length / 2 + 0.8, deck + 1.9), (1.9, -length / 2 + 4.3, deck + 2.3),
         (-1.9, -length / 2 + 4.3, deck + 2.3)], (0, 0, 1), MATTE))
    for side in (-1, 1):
        tube(builder, (side * 2.4, -length / 2 + 2.0, 3.5), (side * 2.7, -length / 2 - 1.0, -0.8), 0.09, 0.07, WOOD, 5, PLANK)
    tube(builder, (0.0, -length / 2 - 0.1, 3.4), (0.0, -length / 2 - 0.7, 4.8), 0.18, 0.12, PITCH, 6, PLANK)
    tube(builder, (0.0, length / 2 - 0.2, 2.9), (0.0, length / 2 + 0.9, 4.2), 0.16, 0.1, PITCH, 6, PLANK)
    mast = Vector((0.0, length * 0.14, deck))
    tube(builder, mast, mast + Vector((0.0, 0.0, 10.5)), 0.2, 0.12, WOOD, 7, PLANK)
    lateen(builder, mast, 10.0, 18.0, math.radians(30), set_sail, SAILCLOTH[(seed + 2) % len(SAILCLOTH)],
           -1.0 if seed % 2 else 1.0)
    for dy in (2.6, -3.0):
        tube(builder, mast + Vector((0.0, 0.0, 10.2)), (0.0, mast.y + dy * 2.5, deck + 0.4), 0.02, 0.02, ROPE, 3, caps=False)
    for index in range(12):
        centre = Vector((-1.6 + (index % 3) * 1.6, -3.0 + (index // 3) * 1.5, deck))
        amphora_light(builder, placement(centre.x, centre.y, centre.z, rng.uniform(0, 6.28)),
                      (0.72, 0.44, 0.3) if index % 3 else (0.82, 0.6, 0.42), True)
    crew(builder, [(0.6, -length / 2 + 2.4, deck + 1.9, 0.3), (-0.8, 2.0, deck, 1.2), (1.2, 5.0, deck, 3.0)], seed * 5 + 1)
    return builder


def grain_ship(seed=0, set_sail=False):
    return seagoing_ship(30.0, 8.6, seed, "set" if set_sail else "brailed")


def skiff(seed=0):
    builder = MeshBuilder()
    length, beam = 6.5, 1.8
    stations = hull_stations(length, beam, 0.35, 0.6, 2.0, 8, 0.25)
    hull_sections(builder, stations, PLANK, PLANK, (0.66, 0.54, 0.42), STRIPES[seed % len(STRIPES)])
    painted(builder, (0.72, 0.6, 0.46), lambda: builder.box((-0.6, -2.0, 0.05), (0.6, 2.0, 0.1), PLANK, bottom=False))
    look = Look("undyed" if seed % 2 else "woad", hem=0.55, skin=2, hair=seed % 4, exomis=seed % 2 == 0, belt="dark",
                arms="forward", hat=(0.78, 0.66, 0.4) if seed % 3 == 0 else None, seed=900 + seed)
    builder.merge(coarse(lambda: person(look), 0.6), placement(0.0, -0.8, 0.1))
    for side in (-1, 1):
        tube(builder, (side * 0.7, 0.2, 0.6), (side * 2.4, 0.6, -0.1), 0.03, 0.025, WOOD, 4, PLANK)
    if seed % 2:
        net = (0.62, 0.55, 0.42)
        ellipsoid(builder, (0.0, 1.6, 0.25), (0.45, 0.5, 0.18), net, 6, 3)
    return builder


SHIPS = {
    "ship_dromon": lambda: dromon(1, False),
    "ship_dromon_sail": lambda: dromon(2, True),
    "ship_merchant": lambda: merchantman(3, False),
    "ship_merchant_sail": lambda: merchantman(4, True),
    "ship_merchant_b": lambda: merchantman(6, False, 16.0, 5.4),
    "ship_grain": lambda: grain_ship(5, False),
    "ship_skiff": lambda: skiff(1),
    "ship_skiff_b": lambda: skiff(2),
}

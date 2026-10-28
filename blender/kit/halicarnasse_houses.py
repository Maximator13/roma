import random

from .geometry import MATTE, VOID_MATERIAL, MeshBuilder
from .halicarnasse_mausoleum import painted

STONE = "limestone"
PLASTER = "plaster"
TILES = "terracotta_tiles"
PAVING = "travertine"
VOID = VOID_MATERIAL
HOUSE_WALLS = [(0.98, 0.95, 0.89), (0.97, 0.88, 0.72), (0.95, 0.80, 0.62), (0.92, 0.70, 0.52), (0.90, 0.58, 0.42),
               (0.96, 0.92, 0.80), (0.88, 0.84, 0.76), (0.98, 0.84, 0.66)]
ROOF_TONES = [(0.80, 0.52, 0.40), (1.0, 0.80, 0.66), (1.0, 0.60, 0.40)]
CLOTHS = [(0.84, 0.20, 0.14), (0.20, 0.38, 0.70), (0.92, 0.70, 0.20), (0.30, 0.52, 0.32), (0.62, 0.22, 0.46)]


def lean_roofs(builder, x0, y0, x1, y1, inner, low, high, colour, detail=True):
    cx0, cy0, cx1, cy1 = inner
    outer = [(x0 - 0.5, y0 - 0.5), (x1 + 0.5, y0 - 0.5), (x1 + 0.5, y1 + 0.5), (x0 - 0.5, y1 + 0.5)]
    court = [(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)]
    bands = 3 if detail else 1
    for k in range(4):
        a, b = outer[k], outer[(k + 1) % 4]
        c, d = court[(k + 1) % 4], court[k]
        for j in range(bands):
            t0, t1 = j / bands, (j + 1) / bands
            ring = [(a[0] + (d[0] - a[0]) * t0, a[1] + (d[1] - a[1]) * t0, high + (low - high) * t0),
                    (b[0] + (c[0] - b[0]) * t0, b[1] + (c[1] - b[1]) * t0, high + (low - high) * t0),
                    (b[0] + (c[0] - b[0]) * t1, b[1] + (c[1] - b[1]) * t1, high + (low - high) * t1),
                    (a[0] + (d[0] - a[0]) * t1, a[1] + (d[1] - a[1]) * t1, high + (low - high) * t1)]
            shade = (0.9, 1.0, 0.94)[(j + k) % 3] if detail else 1.0
            painted(builder, tuple(c_ * shade for c_ in colour), lambda ring=ring: builder.oriented(ring, (0, 0, 1), TILES))
        if detail:
            ridge = [(a[0], a[1], high + 0.12), (b[0], b[1], high + 0.12), (b[0], b[1], high - 0.05), (a[0], a[1], high - 0.05)]
            painted(builder, tuple(c_ * 0.62 for c_ in colour), lambda ridge=ridge, k=k: builder.oriented(
                ridge, (outer[(k + 1) % 4][1] - outer[k][1], outer[k][0] - outer[(k + 1) % 4][0], 0.6), TILES))
            fascia = [(a[0], a[1], high - 0.05), (b[0], b[1], high - 0.05), (b[0], b[1], high - 0.32), (a[0], a[1], high - 0.32)]
            painted(builder, (0.42, 0.30, 0.22), lambda fascia=fascia, k=k: builder.oriented(
                fascia, (outer[(k + 1) % 4][1] - outer[k][1], outer[k][0] - outer[(k + 1) % 4][0], 0.0), MATTE))


def tower(builder, rng, hw, hd, width, height, wall, roof, detail):
    tower_w = width * rng.uniform(0.32, 0.45)
    side = rng.choice([-1, 1])
    tx0, tx1 = (hw - tower_w, hw) if side > 0 else (-hw, -hw + tower_w)
    top = height + 3.0
    back = hd * 0.2
    painted(builder, wall, lambda: builder.box((tx0, -hd, height - 0.2), (tx1, back, top), PLASTER, bottom=False))
    rise = 1.4
    mid = (tx0 + tx1) / 2
    first = len(builder.polygons)
    builder.surface([[(tx0 - 0.4, -hd - 0.4, top), (tx0 - 0.4, back + 0.4, top)],
                     [(mid, -hd - 0.4, top + rise), (mid, back + 0.4, top + rise)]], TILES, facing=(-1, 0, 1))
    builder.surface([[(mid, -hd - 0.4, top + rise), (mid, back + 0.4, top + rise)],
                     [(tx1 + 0.4, -hd - 0.4, top), (tx1 + 0.4, back + 0.4, top)]], TILES, facing=(1, 0, 1))
    builder.tint(first, roof)
    for y, n in ((-hd - 0.4, -1), (back + 0.4, 1)):
        painted(builder, wall, lambda y=y, n=n: builder.oriented([(tx0 - 0.4, y, top), (tx1 + 0.4, y, top), (mid, y, top + rise)],
                                                                 (0, n, 0), PLASTER))
    if detail:
        for k in range(2):
            x = tx0 + tower_w * (k + 1) / 3
            builder.oriented([(x - 0.35, -hd - 0.03, height + 0.8), (x + 0.35, -hd - 0.03, height + 0.8),
                              (x + 0.35, -hd - 0.03, height + 1.9), (x - 0.35, -hd - 0.03, height + 1.9)], (0, -1, 0), VOID)


def greek_house(width, depth, seed=0, storeys=1, shop=0, detail=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    wall = HOUSE_WALLS[seed % len(HOUSE_WALLS)]
    roof = ROOF_TONES[seed % len(ROOF_TONES)]
    height = 4.0
    painted(builder, wall, lambda: builder.box((-hw, -hd, -4.0), (hw, hd, height), PLASTER, bottom=False, top=False))
    if detail:
        painted(builder, (0.82, 0.76, 0.66), lambda: builder.box((-hw - 0.04, -hd - 0.04, -4.0), (hw + 0.04, hd + 0.04, 0.7),
                                                                 STONE, bottom=False, top=False))
    court_w = max(width * 0.36, 2.6)
    court_d = max(depth * 0.34, 2.4)
    cx = rng.uniform(-0.6, 0.6)
    cy = rng.uniform(0.0, 0.8)
    inner = (cx - court_w / 2, cy - court_d / 2, cx + court_w / 2, cy + court_d / 2)
    low = height - 0.35
    lean_roofs(builder, -hw, -hd, hw, hd, inner, low, height + 1.1, roof, detail)
    painted(builder, tuple(c * 0.9 for c in wall), lambda: builder.box((inner[0], inner[1], 0.0), (inner[2], inner[3], low), PLASTER,
                                                                      bottom=False, top=False))
    painted(builder, (0.80, 0.74, 0.62), lambda: builder.oriented([(inner[0], inner[1], 0.3), (inner[2], inner[1], 0.3),
                                                                   (inner[2], inner[3], 0.3), (inner[0], inner[3], 0.3)], (0, 0, 1), PAVING))
    if storeys > 1:
        tower(builder, rng, hw, hd, width, height, wall, roof, detail)
    if not detail:
        return builder
    for y, n in ((inner[1] + 0.02, 1), (inner[3] - 0.02, -1)):
        builder.oriented([(inner[0] + 0.5, y, 0.3), (inner[0] + 1.4, y, 0.3), (inner[0] + 1.4, y, 2.4), (inner[0] + 0.5, y, 2.4)],
                         (0, n, 0), VOID)
    door_x = rng.uniform(-hw + 1.6, hw - 1.6)
    builder.oriented([(door_x - 0.7, -hd - 0.03, 0.0), (door_x + 0.7, -hd - 0.03, 0.0), (door_x + 0.7, -hd - 0.03, 2.5),
                      (door_x - 0.7, -hd - 0.03, 2.5)], (0, -1, 0), VOID)
    for side in (-1, 1):
        painted(builder, (0.86, 0.80, 0.70), lambda side=side: builder.box((door_x + side * 0.7 - 0.12, -hd - 0.14, 0.0),
                                                                          (door_x + side * 0.7 + 0.12, -hd, 2.5), STONE, bottom=False))
    painted(builder, (0.55, 0.36, 0.22), lambda: builder.box((door_x - 0.6, -hd - 0.02, 0.0), (door_x - 0.05, -hd - 0.01, 2.3),
                                                             MATTE, bottom=False))
    painted(builder, (0.90, 0.86, 0.78), lambda: builder.box((door_x - 0.95, -hd - 0.12, 2.5), (door_x + 0.95, -hd, 2.75), STONE))
    for k in range(rng.randint(1, 3)):
        x = rng.uniform(-hw + 0.8, hw - 0.8)
        if abs(x - door_x) < 1.4:
            continue
        builder.oriented([(x - 0.3, -hd - 0.03, height - 1.5), (x + 0.3, -hd - 0.03, height - 1.5), (x + 0.3, -hd - 0.03, height - 0.8),
                          (x - 0.3, -hd - 0.03, height - 0.8)], (0, -1, 0), VOID)
    for k in range(shop):
        x = -hw + width * (k + 0.5) / (shop + 0.5)
        if abs(x - door_x) < 2.2:
            continue
        builder.oriented([(x - 1.2, -hd - 0.03, 0.0), (x + 1.2, -hd - 0.03, 0.0), (x + 1.2, -hd - 0.03, 2.6), (x - 1.2, -hd - 0.03, 2.6)],
                         (0, -1, 0), VOID)
        cloth = CLOTHS[rng.randrange(len(CLOTHS))]
        quad = [(x - 1.6, -hd, 3.0), (x + 1.6, -hd, 3.0), (x + 1.6, -hd - 1.8, 2.5), (x - 1.6, -hd - 1.8, 2.5)]
        painted(builder, cloth, lambda quad=quad: builder.oriented(quad, (0, -0.3, 1), MATTE))
        painted(builder, tuple(c * 0.7 for c in cloth), lambda quad=quad: builder.oriented(list(reversed(quad)), (0, 0.3, -1), MATTE))
    return builder


HOUSES = {
    "house_a": lambda: greek_house(12.0, 10.0, 0, 1, 1),
    "house_b": lambda: greek_house(14.0, 12.0, 1, 2, 0),
    "house_c": lambda: greek_house(10.0, 9.0, 2, 1, 0),
    "house_d": lambda: greek_house(16.0, 13.0, 3, 1, 2),
    "house_e": lambda: greek_house(18.0, 16.0, 4, 2, 0),
    "house_f": lambda: greek_house(11.0, 12.0, 5, 1, 1),
    "house_g": lambda: greek_house(15.0, 11.0, 6, 2, 1),
    "house_h": lambda: greek_house(9.0, 10.0, 7, 1, 0),
}
FAR_HOUSES = {
    "far_a": lambda: greek_house(13.0, 11.0, 8, 1, 0, False),
    "far_b": lambda: greek_house(10.0, 10.0, 3, 1, 0, False),
    "far_c": lambda: greek_house(15.0, 12.0, 4, 2, 0, False),
    "far_d": lambda: greek_house(11.0, 9.0, 1, 1, 0, False),
}
FOOTPRINTS = {"house_a": (12.0, 10.0), "house_b": (14.0, 12.0), "house_c": (10.0, 9.0), "house_d": (16.0, 13.0),
              "house_e": (18.0, 16.0), "house_f": (11.0, 12.0), "house_g": (15.0, 11.0), "house_h": (9.0, 10.0),
              "far_a": (13.0, 11.0), "far_b": (10.0, 10.0), "far_c": (15.0, 12.0), "far_d": (11.0, 9.0)}

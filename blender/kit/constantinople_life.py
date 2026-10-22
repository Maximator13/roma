import math
import random

from mathutils import Matrix

from .colisee_life import helmet, shield
from .geometry import MATTE, MeshBuilder, placement
from .nimes_figures import FRONT, Look, coarse, ellipsoid, person, tube

TAU = 2 * math.pi
PURPLE = (0.46, 0.10, 0.30)
CRIMSON = (0.74, 0.12, 0.12)
SCARLET = (0.86, 0.22, 0.12)
BLUE = (0.14, 0.30, 0.66)
SKY = (0.34, 0.54, 0.80)
GREEN = (0.16, 0.50, 0.26)
LEAF = (0.42, 0.62, 0.22)
SAFFRON = (0.92, 0.66, 0.16)
GOLD = (0.92, 0.72, 0.30)
WHITE = (0.95, 0.94, 0.9)
UNDYED = (0.80, 0.74, 0.62)
BROWN = (0.44, 0.32, 0.22)
BLACK = (0.14, 0.12, 0.12)
ROSE = (0.84, 0.48, 0.48)
TEAL = (0.16, 0.48, 0.5)
OCHRE = (0.78, 0.54, 0.24)
GARMENTS = [CRIMSON, BLUE, GREEN, SAFFRON, WHITE, UNDYED, ROSE, TEAL, OCHRE, SKY, PURPLE, BROWN, SCARLET, LEAF]
BRASS = (0.82, 0.62, 0.32)
WOOD = (0.45, 0.33, 0.22)


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def tablion(builder, colour, height=0.95):
    a0, a1 = FRONT + 0.25, FRONT + 0.75
    r = 0.268
    points = []
    for a, z in ((a0, height), (a1, height), (a1, height + 0.3), (a0, height + 0.3)):
        points.append((r * math.cos(a), r * 0.8 * math.sin(a), z))
    painted(builder, colour, lambda: builder.oriented(points, (math.cos(FRONT + 0.5), math.sin(FRONT + 0.5), 0.0), MATTE))


def segmenta(builder, colour):
    for side in (-1, 1):
        ellipsoid(builder, (side * 0.2, 0.06, 1.25), (0.012, 0.05, 0.05), colour, 6, 3)
    ellipsoid(builder, (0.08, 0.2, 0.42), (0.05, 0.012, 0.05), colour, 6, 3)


def candle(builder, hand=(0.17, 0.34, 1.08)):
    x, y, z = hand
    tube(builder, [(x, y, z - 0.12), (x, y, z + 0.42)], [0.022, 0.02], (0.96, 0.92, 0.8), 6)
    painted(builder, (1.0, 1.0, 1.0), lambda: builder.lathe([(0.0, z + 0.42), (0.03, z + 0.47), (0.0, z + 0.56)], 5,
                                                            "flame"))


def citizen(seed):
    rng = random.Random(seed)
    tunic = rng.choice(GARMENTS)
    cloak = rng.choice([WHITE, CRIMSON, BLUE, GREEN, OCHRE, UNDYED, TEAL])
    look = Look(tunic, hem=rng.choice([0.03, 0.12, 0.45]), skin=rng.randrange(3), hair=rng.randrange(4),
                cloak=cloak, sleeves="long", arms=rng.choice(["down", "gesture", "hip"]), stripe=GOLD if rng.random() < 0.4
                else None, belt=BROWN, seed=seed)
    builder = person(look)
    if rng.random() < 0.5:
        tablion(builder, rng.choice([PURPLE, GOLD, CRIMSON]))
    if rng.random() < 0.5:
        segmenta(builder, rng.choice([PURPLE, GOLD, BLACK]))
    return builder


def dignitary(seed):
    look = Look(WHITE, hem=0.03, skin=seed % 3, hair=seed % 4, cloak=WHITE, sleeves="long",
                arms="gesture" if seed % 2 else "down", stripe=GOLD, seed=seed)
    builder = person(look)
    tablion(builder, PURPLE)
    segmenta(builder, PURPLE)
    return builder


def woman(seed):
    rng = random.Random(seed)
    tunic = rng.choice([BLUE, CRIMSON, GREEN, SAFFRON, ROSE, TEAL, WHITE, SKY])
    veil = rng.choice([WHITE, PURPLE, BLUE, ROSE, SAFFRON, BROWN, UNDYED])
    look = Look(tunic, hem=0.03, skin=rng.randrange(3), hair=rng.randrange(4), palla=veil, veil=True, female=True,
                sleeves="long", arms=rng.choice(["down", "hip", "forward"]), stripe=GOLD if rng.random() < 0.3 else None,
                scale=0.95, seed=seed)
    return person(look)


def noblewoman(seed):
    look = Look(rng_choice(seed, [PURPLE, CRIMSON, BLUE]), hem=0.03, skin=0, hair=1, palla=GOLD, veil=True, female=True,
                sleeves="long", arms="down", stripe=GOLD, scale=0.96, seed=seed)
    builder = person(look)
    for k in range(6):
        a = FRONT - 1.0 + k * 0.4
        ellipsoid(builder, (0.15 * math.cos(a), 0.12 * math.sin(a) + 0.02, 1.43), (0.018, 0.018, 0.018), (0.9, 0.86, 0.7), 4, 2)
    return builder


def rng_choice(seed, items):
    return items[seed % len(items)]


def clergy(seed):
    look = Look(WHITE, hem=0.03, skin=seed % 3, hair=seed % 4, sleeves="long", arms="forward", stripe=GOLD if seed % 2
                else CRIMSON, seed=seed)
    builder = person(look)
    painted(builder, GOLD if seed % 2 else CRIMSON, lambda: builder.oriented(
        [(-0.15, 0.135, 1.36), (-0.1, 0.17, 0.6), (-0.04, 0.17, 0.6), (-0.09, 0.14, 1.38)], (0, 1, 0), MATTE))
    candle(builder)
    candle(builder, (-0.17, 0.34, 1.08))
    return builder


def cross_bearer(seed):
    look = Look(WHITE, hem=0.03, skin=seed % 3, hair=seed % 4, sleeves="long", arms="forward", stripe=CRIMSON, seed=seed)
    builder = person(look)
    tube(builder, [(0.0, 0.32, 0.4), (0.0, 0.32, 2.6)], [0.025, 0.022], GOLD, 5)
    painted(builder, GOLD, lambda: builder.box((-0.03, 0.29, 2.3), (0.03, 0.35, 2.85), MATTE))
    painted(builder, GOLD, lambda: builder.box((-0.2, 0.29, 2.6), (0.2, 0.35, 2.66), MATTE))
    return builder


def censer_bearer(seed):
    look = Look(WHITE, hem=0.03, skin=seed % 3, hair=seed % 4, sleeves="long", arms="gesture", stripe=GOLD, seed=seed)
    builder = person(look)
    tube(builder, [(0.31, 0.3, 1.43), (0.36, 0.34, 0.95)], [0.006, 0.006], BRASS, 3)
    ellipsoid(builder, (0.36, 0.34, 0.9), (0.07, 0.07, 0.07), BRASS, 7, 4)
    return builder


def bishop(seed):
    look = Look(WHITE, hem=0.03, skin=0, hair=2, cloak=GOLD, sleeves="long", arms="gesture", stripe=CRIMSON, seed=seed)
    builder = person(look)
    for z in (0.7, 1.0, 1.28):
        painted(builder, BLACK, lambda z=z: builder.oriented(
            [(-0.04, 0.23, z), (0.04, 0.23, z), (0.04, 0.23, z + 0.12), (-0.04, 0.23, z + 0.12)], (0, 1, 0), MATTE))
    painted(builder, WHITE, lambda: builder.oriented(
        [(-0.07, 0.205, 1.42), (0.07, 0.205, 1.42), (0.06, 0.23, 0.55), (-0.06, 0.23, 0.55)], (0, 1, 0), MATTE))
    return builder


def monk(seed):
    look = Look(BLACK if seed % 2 else BROWN, hem=0.03, skin=seed % 3, hair=2, sleeves="long", hood=BLACK if seed % 2 else BROWN,
                arms="down", seed=seed)
    return person(look)


def guard(seed):
    rng = random.Random(seed)
    look = Look(WHITE if seed % 2 else CRIMSON, hem=0.5, skin=rng.randrange(3), hair=1, belt=(0.3, 0.2, 0.12),
                cloak=CRIMSON if seed % 2 else WHITE, arms="staff", sleeves="long", seed=seed)
    builder = person(look)
    helmet(builder, "smooth", visor=False, brim=False, colour=(0.86, 0.78, 0.52))
    tube(builder, [(0.25, 0.22, 0.0), (0.25, 0.2, 2.35)], [0.02, 0.016], WOOD, 4)
    tube(builder, [(0.25, 0.2, 2.35), (0.25, 0.2, 2.58)], [0.03, 0.002], (0.7, 0.7, 0.68), 4)
    shield(builder, (-0.3, 0.12, 0.95), 0.72, 1.05, BLUE if seed % 3 else CRIMSON, 0.14)
    painted(builder, GOLD, lambda: builder.oriented(
        [(-0.62, 0.151, 0.95), (0.02, 0.151, 0.95), (0.02, 0.151, 1.0), (-0.62, 0.151, 1.0)], (0, 1, 0), MATTE))
    painted(builder, GOLD, lambda: builder.oriented(
        [(-0.325, 0.152, 0.5), (-0.275, 0.152, 0.5), (-0.275, 0.152, 1.42), (-0.325, 0.152, 1.42)], (0, 1, 0), MATTE))
    return builder


def porter(seed):
    look = Look(rng_choice(seed, [OCHRE, UNDYED, BROWN, TEAL]), hem=0.55, skin=2, hair=seed % 4, belt=BROWN,
                arms="carry", carry="amphora" if seed % 2 else None, exomis=seed % 3 == 0, seed=seed)
    builder = person(look)
    if seed % 2 == 0:
        ellipsoid(builder, (0.0, -0.18, 1.35), (0.22, 0.16, 0.28), (0.72, 0.62, 0.44), 7, 4)
    return builder


def merchant(seed):
    look = Look(rng_choice(seed, [TEAL, SAFFRON, CRIMSON, SKY]), hem=0.45, skin=seed % 3, hair=seed % 4, belt=BROWN,
                cloak=rng_choice(seed + 1, [BROWN, OCHRE, UNDYED]), arms="gesture", sleeves="long", seed=seed)
    return person(look)


def sailor(seed):
    look = Look(rng_choice(seed, [UNDYED, SKY, OCHRE]), hem=0.55, skin=2, hair=seed % 4, exomis=True, belt=BROWN,
                arms="shoulder", carry="pole" if seed % 2 else None, hat=(0.78, 0.66, 0.4) if seed % 3 == 0 else None,
                seed=seed)
    return person(look)


def child(seed):
    look = Look(rng_choice(seed, [SAFFRON, SKY, ROSE, WHITE]), hem=0.5, skin=seed % 3, hair=seed % 4, scale=0.66,
                child=True, belt=CRIMSON, arms="swing", seed=seed)
    return person(look)


WALKERS = {
    "walker_citizen": Look(BLUE, hem=0.12, skin=1, hair=0, cloak=WHITE, sleeves="long", stride=0.17, arms="swing",
                           stripe=GOLD, seed=11),
    "walker_woman": Look(CRIMSON, hem=0.03, skin=0, hair=1, palla=SAFFRON, veil=True, female=True, sleeves="long",
                         stride=0.13, arms="swing", scale=0.95, seed=13),
    "walker_porter": Look(OCHRE, hem=0.55, skin=2, hair=3, stride=0.2, arms="carry", carry="amphora", belt=BROWN,
                          seed=14),
    "walker_monk": Look(BLACK, hem=0.03, skin=1, hair=2, hood=BLACK, sleeves="long", stride=0.14, arms="swing", seed=15),
    "walker_merchant": Look(TEAL, hem=0.45, skin=1, hair=0, cloak=BROWN, belt=BROWN, sleeves="long", stride=0.18,
                            arms="swing", carry="bundle", seed=16),
    "walker_matron": Look(BLUE, hem=0.03, skin=1, hair=2, palla=WHITE, veil=True, female=True, sleeves="long", stride=0.13,
                          arms="swing", scale=0.95, seed=17),
}


def seated(seed, colour=None, near=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    garment = colour if colour is not None and rng.random() < 0.75 else rng.choice(GARMENTS)
    mantle = rng.choice([garment, WHITE, UNDYED, garment])
    skin = [(0.80, 0.60, 0.47), (0.72, 0.52, 0.39), (0.62, 0.44, 0.32)][rng.randrange(3)]
    hair = [(0.17, 0.12, 0.09), (0.30, 0.20, 0.12), (0.12, 0.10, 0.09)][rng.randrange(3)]
    female = rng.random() < 0.25
    segments = 7 if near else 5
    painted(builder, garment, lambda: builder.lathe([(0.17, 0.0), (0.19, 0.25)], segments, MATTE,
                                                    matrix=Matrix.Diagonal((1.0, 0.75, 1.0, 1.0)), caps=False))
    painted(builder, mantle, lambda: builder.lathe([(0.19, 0.25), (0.17, 0.48), (0.07, 0.66)], segments, MATTE,
                                                   matrix=Matrix.Diagonal((1.0, 0.72, 1.0, 1.0)), caps=False))
    tube(builder, [(0.0, 0.0, 0.08), (0.0, 0.42, 0.1)], [0.16, 0.14], garment, 5, squash=0.5)
    tube(builder, [(0.0, 0.42, 0.12), (0.0, 0.46, -0.4)], [0.06, 0.05], garment if female else skin, 4)
    if near:
        for side in (-1, 1):
            raised = rng.random() < 0.25
            end = (side * 0.22, 0.12, 0.92) if raised else (side * 0.12, 0.33, 0.22)
            tube(builder, [(side * 0.18, 0.0, 0.5), end], [0.05, 0.035], skin if raised else mantle, 4)
    ellipsoid(builder, (0.0, 0.015, 0.76), (0.085, 0.095, 0.11), skin, segments, 3)
    ellipsoid(builder, (0.0, -0.01, 0.8), (0.09, 0.1, 0.09), mantle if female else hair, segments, 3)
    return builder


def crowd_block(seed, colour, rows, width, depth, rise, fill=0.62, spacing=0.58):
    rng = random.Random(seed)
    pool = [seated(seed * 100 + k, colour, False) for k in range(12)]
    builder = MeshBuilder()
    for row in range(rows):
        count = int(width / spacing)
        for k in range(count):
            if rng.random() > fill:
                continue
            x = -width / 2 + (k + 0.5 + rng.uniform(-0.15, 0.15)) * spacing
            builder.merge(pool[rng.randrange(len(pool))], placement(x, -row * depth - depth * 0.55, row * rise,
                                                                     rng.uniform(-0.3, 0.3)))
    return builder


def procession(seed):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(cross_bearer(seed), placement(0.0, 0.0, 0.0))
    for k in range(5):
        for side in (-1, 1):
            builder.merge(clergy(seed + k * 2 + (side > 0)), placement(side * 0.75, -1.4 - k * 1.25 + rng.uniform(-0.1, 0.1), 0.0,
                                                                         rng.uniform(-0.08, 0.08)))
    builder.merge(censer_bearer(seed + 30), placement(-0.5, -8.2, 0.0))
    builder.merge(censer_bearer(seed + 31), placement(0.5, -8.4, 0.0))
    builder.merge(bishop(seed + 32), placement(0.0, -9.8, 0.0))
    return builder


FIGURE_DETAIL = 0.72
FIGURES = {
    "fig_citizen": lambda: coarse(lambda: citizen(21), FIGURE_DETAIL),
    "fig_citizen_b": lambda: coarse(lambda: citizen(22), FIGURE_DETAIL),
    "fig_citizen_c": lambda: coarse(lambda: citizen(23), FIGURE_DETAIL),
    "fig_dignitary": lambda: coarse(lambda: dignitary(31), FIGURE_DETAIL),
    "fig_woman": lambda: coarse(lambda: woman(41), FIGURE_DETAIL),
    "fig_woman_b": lambda: coarse(lambda: woman(42), FIGURE_DETAIL),
    "fig_noble": lambda: coarse(lambda: noblewoman(43), FIGURE_DETAIL),
    "fig_clergy": lambda: coarse(lambda: clergy(51), FIGURE_DETAIL),
    "fig_monk": lambda: coarse(lambda: monk(61), FIGURE_DETAIL),
    "fig_guard": lambda: coarse(lambda: guard(71), FIGURE_DETAIL),
    "fig_porter": lambda: coarse(lambda: porter(81), FIGURE_DETAIL),
    "fig_merchant": lambda: coarse(lambda: merchant(91), FIGURE_DETAIL),
    "fig_sailor": lambda: coarse(lambda: sailor(101), FIGURE_DETAIL),
    "fig_child": lambda: coarse(lambda: child(111), FIGURE_DETAIL),
}


def procession_group():
    return coarse(lambda: procession(500), 0.62)

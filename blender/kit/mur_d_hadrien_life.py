import math
import random

from mathutils import Matrix, Vector

from .buildings import lathe_tree, lobe
from .cannes_figures import flat_oval
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, SKIN, WOOD
from .nimes_figures import ANIMALS, Look, beast, coarse, drape, ellipsoid, legs, ox_cart, person, tube

TAU = 2 * math.pi
MAIL = (0.40, 0.41, 0.43)
IRON = (0.50, 0.51, 0.53)
BRASS = (0.78, 0.60, 0.30)
TUNIC_RED = (0.70, 0.18, 0.12)
TUNIC_UNDYED = (0.80, 0.74, 0.60)
TROUSERS = [(0.36, 0.27, 0.18), (0.30, 0.30, 0.26), (0.46, 0.36, 0.22)]
CLOAKS = [(0.30, 0.38, 0.24), (0.44, 0.32, 0.20), (0.24, 0.30, 0.42), (0.52, 0.44, 0.30), (0.60, 0.20, 0.14)]
SHIELDS = [(0.72, 0.16, 0.10), (0.20, 0.34, 0.62), (0.82, 0.62, 0.20), (0.26, 0.46, 0.26)]
DETAIL = 0.72

ANIMALS["sheep"] = dict(length=0.86, height=0.34, girth=0.46, colour=(0.46, 0.35, 0.24), neck=0.24, ears=0.07,
                        horns=0.1, lift=0.45)
ANIMALS["cow"] = dict(length=1.5, height=0.56, girth=0.66, colour=(0.24, 0.17, 0.12), neck=0.34, ears=0.09,
                      horns=0.2, lift=0.1)
ANIMALS["horse"] = dict(length=1.5, height=0.86, girth=0.56, colour=(0.40, 0.27, 0.16), neck=0.74, ears=0.13,
                        horns=0.0, lift=0.95)


def leg_polygons(spec):
    probe = MeshBuilder()
    skin = SKIN[spec.skin]
    legs(probe, spec, skin, LEATHER, spec.material)
    return len(probe.polygons)


def helmet(builder, crest=None, metal=IRON):
    drape(builder, metal, [(0.13, 1.575), (0.126, 1.64), (0.104, 1.71), (0.06, 1.756), (0.0, 1.768)], 10,
          folds=(0, 0.0, 0.0), squash=1.08, center=(0.0, -0.006))
    drape(builder, metal, [(0.13, 1.6), (0.17, 1.555), (0.18, 1.545)], 8, start=math.radians(200),
          sweep=math.radians(140), folds=(0, 0.0, 0.0), squash=1.0, center=(0.0, -0.01))
    drape(builder, BRASS, [(0.133, 1.638), (0.142, 1.63)], 10, start=math.radians(20), sweep=math.radians(140),
          folds=(0, 0.0, 0.0), squash=1.08, center=(0.0, 0.0))
    for side in (-1, 1):
        first = len(builder.polygons)
        builder.centered_box((side * 0.112, 0.03, 1.545), (0.025, 0.075, 0.1), MATTE)
        builder.tint(first, metal)
    if crest is not None:
        ellipsoid(builder, (0.0, -0.004, 1.79), (0.19, 0.03, 0.065), crest, 8, 3)


def oval_shield(builder, color, seed):
    shield = MeshBuilder()
    flat_oval(shield, (0.0, 0.0, 0.0), color, 0.62, 1.05)
    ellipsoid(shield, (0.0, 0.03, 0.0), (0.075, 0.035, 0.075), BRASS, 6, 3)
    first = len(shield.polygons)
    shield.centered_box((0.0, 0.014, 0.42), (0.36, 0.006, 0.05), MATTE)
    shield.centered_box((0.0, 0.014, -0.42), (0.36, 0.006, 0.05), MATTE)
    shield.tint(first, (0.92, 0.88, 0.74))
    builder.merge(shield, Matrix.Translation((-0.33, 0.06, 0.92)) @ Matrix.Rotation(-math.pi / 2 + 0.25, 4, "Z")
                  @ Matrix.Rotation(0.06, 4, "X"))


def spear(builder, length=2.3):
    tube(builder, [(0.255, 0.27, 0.02), (0.25, 0.2, 1.0), (0.245, 0.14, length)], [0.016, 0.016, 0.015], WOOD, 4)
    tube(builder, [(0.245, 0.14, length), (0.244, 0.138, length + 0.26)], [0.024, 0.0], IRON, 4)


def soldier(seed, cloak=None, shield=None, trousers=None, arms="staff", stride=0.0, centurion=False, mail=True,
            carry_spear=True, sword=True):
    rng = random.Random(seed)
    cloak = cloak if cloak is not None else rng.choice(CLOAKS)
    trousers = trousers if trousers is not None else rng.choice(TROUSERS)
    skin = rng.randrange(3)
    look = Look(MAIL if mail else TUNIC_RED, hem=0.6, skin=skin, hair=rng.randrange(4), cloak=cloak, belt=LEATHER,
                arms=arms, stride=stride, seed=seed)

    def build():
        built = person(look)
        count = leg_polygons(look)
        skin_colour = SKIN[skin]
        for index in range(count):
            if built.polygon_colors[index] == skin_colour:
                built.polygon_colors[index] = trousers
        drape(built, TUNIC_RED if not centurion else (0.78, 0.74, 0.62), [(0.215, 0.56), (0.212, 0.62)], 12,
              folds=(5, 0.04, seed), squash=0.74)
        helmet(built, (0.86, 0.12, 0.08) if centurion else None, BRASS if centurion else IRON)
        if sword:
            tube(built, [(-0.2 if centurion else 0.2, 0.05, 1.02), (-0.24 if centurion else 0.24, 0.12, 0.62)],
                 [0.03, 0.025], LEATHER, 4)
        if centurion:
            tube(built, [(0.27, 0.24, 0.6), (0.26, 0.18, 1.0), (0.24, 0.12, 1.25)], [0.014, 0.014, 0.012],
                 (0.40, 0.28, 0.14), 4)
            for side in (-1, 1):
                tube(built, [(side * 0.088, 0.02, 0.1), (side * 0.092, 0.03, 0.42)], [0.05, 0.055], BRASS, 5)
        else:
            if shield is not None:
                oval_shield(built, shield, seed)
            if carry_spear:
                spear(built)
        return built
    return coarse(build, DETAIL)


def worker(seed, tunic=TUNIC_UNDYED, load="stone", stride=0.0):
    rng = random.Random(seed)
    look = Look(tunic, hem=0.58, skin=rng.randrange(3), hair=rng.randrange(4), belt=LEATHER,
                arms="shoulder" if load in ("stone", "pick") else "carry", exomis=load == "pick", stride=stride,
                seed=seed, carry="pole" if load == "peat" else None)

    def build():
        built = person(look)
        trousers = rng.choice(TROUSERS)
        count = leg_polygons(look)
        skin_colour = SKIN[look.skin]
        for index in range(count):
            if built.polygon_colors[index] == skin_colour:
                built.polygon_colors[index] = trousers
        if load == "stone":
            first = len(built.polygons)
            built.centered_box((0.18, 0.02, 1.68), (0.42, 0.28, 0.22), MATTE)
            built.tint(first, (0.78, 0.71, 0.58))
        elif load == "pick":
            tube(built, [(0.24, 0.18, 1.62), (0.18, -0.15, 1.75), (0.1, -0.5, 1.82)], [0.016, 0.016, 0.015], WOOD, 4)
            tube(built, [(0.1, -0.62, 1.62), (0.1, -0.5, 1.82), (0.1, -0.42, 2.0)], [0.02, 0.025, 0.012], IRON, 4)
        elif load == "basket":
            ellipsoid(built, (0.0, -0.24, 1.2), (0.2, 0.14, 0.24), (0.58, 0.46, 0.28), 7, 4)
        return built
    return coarse(build, DETAIL)


def briton(seed, stride=0.0):
    rng = random.Random(seed)
    look = Look((0.62, 0.38, 0.22), hem=0.55, skin=0, hair=rng.choice((1, 2)), cloak=(0.36, 0.44, 0.28),
                belt=LEATHER, arms="staff", carry="staff", stride=stride, seed=seed, hair_style="long")

    def build():
        built = person(look)
        count = leg_polygons(look)
        for index in range(count):
            if built.polygon_colors[index] == SKIN[0]:
                built.polygon_colors[index] = (0.50, 0.30, 0.20)
        return built
    return coarse(build, DETAIL)


def animal(kind, seed=0):
    return beast(kind)


def flock(seed=0, count=7, kind="sheep", spread=4.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        x, y = rng.uniform(-spread, spread), rng.uniform(-spread, spread)
        built = beast(kind)
        if kind == "sheep" and rng.random() < 0.4:
            built.paint(MATTE, (0.75, 0.70, 0.60) if rng.random() < 0.5 else (0.55, 0.50, 0.45))
        builder.merge(built, placement(x, y, 0.0, rng.uniform(0, TAU)))
    return builder


def supply_cart():
    builder = ox_cart()
    escort = soldier(91, shield=SHIELDS[0], stride=0.15)
    builder.merge(escort, placement(1.3, 1.2, 0.0))
    return builder


def guard_pair(seed=0):
    builder = MeshBuilder()
    builder.merge(soldier(seed, shield=SHIELDS[seed % 4]), placement(-0.9, 0.0, 0.0, 0.1))
    builder.merge(soldier(seed + 1, shield=SHIELDS[(seed + 1) % 4], arms="down", carry_spear=False),
                  placement(0.8, 0.2, 0.0, -0.4))
    return builder


def builders_gang(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k, load in enumerate(("stone", "pick", "stone", "basket")):
        x, y = rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5)
        builder.merge(worker(seed + k, rng.choice([TUNIC_UNDYED, (0.66, 0.48, 0.30), (0.56, 0.58, 0.46)]), load),
                      placement(x, y, 0.0, rng.uniform(0, TAU)))
    return builder


def tussock(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(5):
        a = TAU * k / 5 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.05, 0.18)
        base = Vector((r * math.cos(a), r * math.sin(a), -0.05))
        tip = base + Vector((math.cos(a) * 0.25, math.sin(a) * 0.25, rng.uniform(0.5, 0.8)))
        first = len(builder.polygons)
        side = Vector((-math.sin(a), math.cos(a), 0.0)) * 0.05
        builder.face(builder.points([base - side, base + side, tip]), MATTE)
        builder.face(builder.points([tip, base + side, base - side]), MATTE)
        tone = rng.choice([(0.26, 0.36, 0.14), (0.36, 0.42, 0.18), (0.52, 0.50, 0.26)])
        builder.tint(first, tone)
    return builder


def heather_clump(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    bloom = (0.50, 0.30, 0.44) if seed % 2 else (0.44, 0.28, 0.34)
    for k in range(9):
        a = TAU * k / 9 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.0, 0.35)
        base = Vector((r * math.cos(a), r * math.sin(a), -0.04))
        tip = base + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, rng.uniform(0.25, 0.42)))
        side = Vector((-math.sin(a), math.cos(a), 0.0)) * 0.16
        first = len(builder.polygons)
        builder.face(builder.points([base - side, base + side, tip + side * 0.6, tip - side * 0.6]), MATTE)
        builder.face(builder.points([tip - side * 0.6, tip + side * 0.6, base + side, base - side]), MATTE)
        builder.tint(first, bloom if rng.random() < 0.55 else (0.34, 0.32, 0.18))
    return builder


def boulder(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    lobe(builder, (0.0, 0.0, 0.2), 0.9, 1.1, MATTE, 6, seed, flat=0.1)
    builder.tint(0, tuple(c * rng.uniform(0.85, 1.1) for c in (0.36, 0.37, 0.38)))
    return builder


def rowan(seed=0):
    builder = lathe_tree(2.4, 0.16, [(0.0, 1.8), (1.4, 2.4), (1.7, 3.6), (1.2, 4.8), (0.0, 5.3)], "foliage_shrub",
                         7, seed)
    rng = random.Random(seed)
    for k in range(5):
        a = rng.uniform(0, TAU)
        first = len(builder.polygons)
        builder.centered_box((math.cos(a) * 1.5, math.sin(a) * 1.5, rng.uniform(2.8, 4.0)), (0.18, 0.18, 0.18),
                             MATTE)
        builder.tint(first, (0.86, 0.20, 0.10))
    return builder


WALKERS = {
    "walker_auxiliaire": lambda: soldier(201, cloak=CLOAKS[0], shield=SHIELDS[0], stride=0.17),
    "walker_auxiliaire_b": lambda: soldier(202, cloak=CLOAKS[2], shield=SHIELDS[1], stride=0.17),
    "walker_centurion": lambda: soldier(203, cloak=(0.72, 0.14, 0.10), centurion=True, stride=0.16),
    "walker_ouvrier": lambda: worker(204, (0.66, 0.48, 0.30), "stone", stride=0.18),
    "walker_porteur": lambda: worker(205, (0.56, 0.58, 0.46), "basket", stride=0.18),
}

LIFE = {
    "sentry": lambda: soldier(11, shield=SHIELDS[0]),
    "sentry_b": lambda: soldier(12, shield=SHIELDS[1], cloak=CLOAKS[1]),
    "sentry_c": lambda: soldier(13, shield=SHIELDS[2], cloak=CLOAKS[3]),
    "soldier_rest": lambda: soldier(14, arms="down", carry_spear=False, cloak=CLOAKS[2]),
    "soldier_talk": lambda: soldier(15, arms="gesture", carry_spear=False, cloak=CLOAKS[4]),
    "centurion": lambda: soldier(16, cloak=(0.72, 0.14, 0.10), centurion=True, arms="gesture"),
    "guards": lambda: guard_pair(20),
    "worker_stone": lambda: worker(31, TUNIC_UNDYED, "stone"),
    "worker_pick": lambda: worker(32, (0.66, 0.48, 0.30), "pick"),
    "builders": lambda: builders_gang(40),
    "briton": lambda: briton(51),
    "sheep": lambda: flock(61, 8, "sheep", 5.0),
    "cattle": lambda: flock(62, 4, "cow", 6.0),
    "horse": lambda: beast("horse"),
    "supply_cart": supply_cart,
}

PROPS = {
    "tussock": lambda: tussock(3),
    "tussock_b": lambda: tussock(4),
    "heather": lambda: heather_clump(1),
    "heather_b": lambda: heather_clump(2),
    "boulder": lambda: boulder(5),
    "boulder_b": lambda: boulder(6),
    "rowan": lambda: rowan(7),
}

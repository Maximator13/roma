import math
import random

from mathutils import Matrix, Vector

from . import alexandrie_ships as ships
from .alexandrie_city import broad_tree, date_palm, shrub
from .alexandrie_life import CRIMSON, INDIGO, LINEN, SAFFRON, TURQUOISE, camel, camel_train, donkey_driver, figure
from .alexandrie_life import greek, lady
from .alexandrie_pharos import painted
from .colisee_life import helmet, shield
from .geometry import MATTE, MeshBuilder, placement
from .life import HAIR, LEATHER, WOOD
from .nimes_figures import POSES, Look, beast, coarse, drape, ellipsoid, pack_beast, tube

if len(HAIR) < 5:
    HAIR.append((0.56, 0.41, 0.31))
SHAVEN = 4
POSES.update({
    "giza_climb": [((0.26, 0.12, 1.42), (0.2, 0.3, 1.72)), ((-0.26, 0.1, 1.4), (-0.24, 0.32, 1.66))],
    "giza_hoe": [((0.22, 0.3, 1.0), (0.1, 0.55, 0.78)), ((-0.22, 0.3, 1.02), (-0.08, 0.52, 0.82))],
    "giza_censer": [((0.24, 0.28, 1.15), (0.18, 0.5, 1.12)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "giza_raise": [((0.27, 0.06, 1.55), (0.3, 0.12, 1.85)), ((-0.27, 0.06, 1.55), (-0.3, 0.12, 1.85))],
})
ROSE = (0.86, 0.44, 0.46)
SAFFRON_DEEP = (0.94, 0.58, 0.12)
SKY = (0.36, 0.62, 0.86)
LEAF = (0.38, 0.58, 0.26)
PURPLE = (0.52, 0.20, 0.42)
EMERALD = (0.16, 0.52, 0.36)
WHITE_LINEN = (0.99, 0.98, 0.95)
MUD = (0.50, 0.40, 0.30)
WASH = (0.97, 0.95, 0.90)
TAU = 2 * math.pi


def roman(seed, tunic=(0.94, 0.90, 0.80), mantle=INDIGO, arms="hip", stride=0.0, skin=0, hair=0, hat=None,
          scale=1.0):
    return figure(Look(tunic, hem=0.12, skin=skin, hair=hair, palla=mantle, arms=arms, stride=stride,
                       sleeves="long", hat=hat, scale=scale, seed=seed))


def paenula(seed, colour=(0.54, 0.36, 0.22), arms="down", stride=0.0):
    return figure(Look((0.90, 0.84, 0.70), hem=0.2, skin=1, hair=2, cloak=colour, hood=colour if seed % 2 else None,
                       arms=arms, stride=stride, sleeves="long", seed=seed))


def villager(seed, tunic=LINEN, arms="down", stride=0.0, carry=None, hat=None):
    return figure(Look(tunic, hem=0.52, skin=2, hair=3, belt=(0.70, 0.56, 0.36), exomis=seed % 3 == 0, arms=arms,
                       stride=stride, carry=carry, hat=hat, seed=seed))


def peasant_woman(seed, tunic=SKY, mantle=(0.20, 0.20, 0.24), arms="head", carry="jar", stride=0.0):
    return figure(lady(seed, tunic, mantle, arms, stride, carry, skin=2, hair=3))


def priest(seed, arms="down"):
    return figure(Look(WHITE_LINEN, hem=0.03, skin=1, hair=SHAVEN, sleeves="short", arms=arms,
                       belt=(0.96, 0.92, 0.80), seed=seed))


def soldier(seed, arms="staff"):
    builder = figure(Look((0.58, 0.58, 0.60), hem=0.58, skin=1, hair=0, belt=LEATHER, cloak=CRIMSON, arms=arms,
                          sleeves="long", seed=seed))
    helmet(builder, "smooth", visor=False, brim=False)
    tube(builder, [(0.25, 0.22, 0.0), (0.25, 0.2, 2.1)], [0.02, 0.016], WOOD, 4)
    tube(builder, [(0.25, 0.2, 2.1), (0.25, 0.2, 2.32)], [0.03, 0.002], (0.7, 0.7, 0.68), 4)
    shield(builder, (-0.3, 0.1, 0.95), 0.62, 1.05, (0.70, 0.16, 0.12), 0.1)
    return builder


def guide_group(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(villager(seed, LINEN, "alex_point"), placement(0.0, 1.6, 0.0, math.pi))
    tunics = [(0.94, 0.90, 0.80), (0.86, 0.88, 0.92), WHITE_LINEN]
    mantles = [INDIGO, CRIMSON, EMERALD, PURPLE, SAFFRON_DEEP]
    for k in range(4):
        angle = -0.9 + k * 0.6
        x, y = 1.6 * math.sin(angle), -0.4 + 0.5 * math.cos(angle)
        if k == 2:
            fig = figure(lady(seed + k, ROSE, TURQUOISE, "hip"))
        elif k == 3:
            fig = paenula(seed + k, (0.46, 0.30, 0.20))
        else:
            fig = roman(seed + k, rng.choice(tunics), mantles[(seed + k) % len(mantles)], rng.choice(["hip", "gesture"]),
                        skin=rng.randrange(2), hair=rng.randrange(3))
        builder.merge(fig, placement(x, y, 0.0, rng.uniform(-0.4, 0.4)))
    return builder


def visitors(seed=0, count=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    mantles = [INDIGO, CRIMSON, EMERALD, PURPLE, TURQUOISE, SAFFRON_DEEP]
    for k in range(count):
        angle = TAU * k / count + rng.uniform(-0.3, 0.3)
        x, y = 0.8 * math.cos(angle), 0.8 * math.sin(angle)
        heading = math.atan2(-x, y) + math.pi
        if rng.random() < 0.4:
            fig = figure(lady(seed + k, rng.choice([SAFFRON, ROSE, SKY, WHITE_LINEN]), rng.choice(mantles),
                              rng.choice(["hip", "gesture", "down"])))
        else:
            fig = roman(seed + k, rng.choice([(0.94, 0.90, 0.80), WHITE_LINEN, (0.86, 0.88, 0.92)]),
                        rng.choice(mantles), rng.choice(["hip", "gesture", "alex_point", "gesture"]),
                        skin=rng.randrange(2), hair=rng.randrange(3),
                        hat=(0.74, 0.60, 0.38) if rng.random() < 0.4 else None, scale=rng.uniform(0.92, 1.06))
        builder.merge(fig, placement(x, y, 0.0, heading))
    return builder


def litter(seed=0):
    builder = MeshBuilder()
    painted(builder, (0.50, 0.30, 0.18), lambda: builder.box((-0.55, -1.1, 0.95), (0.55, 1.1, 1.15), MATTE))
    for x in (-0.5, 0.5):
        for y in (-1.05, 1.05):
            tube(builder, [(x, y, 1.15), (x, y, 2.2)], [0.03, 0.03], (0.85, 0.62, 0.25), 4, "bronze_gilt")
    painted(builder, (0.70, 0.14, 0.12), lambda: builder.box((-0.62, -1.15, 2.2), (0.62, 1.15, 2.32), MATTE))
    for side in (-1, 1):
        drape(builder, (0.86, 0.24, 0.16), [(0.0, 1.3), (0.02, 1.8), (0.0, 2.2)], 4, folds=(0, 0.0, 0.0),
              squash=1.0, center=(side * 0.6, 0.0))
        painted(builder, (0.86, 0.24, 0.16), lambda side=side: builder.box((side * 0.6 - 0.02, -1.1, 1.2),
                                                                         (side * 0.6 + 0.02, 1.1, 2.2), MATTE))
        tube(builder, [(side * 0.72, -2.4, 1.05), (side * 0.72, 2.4, 1.05)], [0.045, 0.045], WOOD, 5)
    ellipsoid(builder, (0.0, 0.2, 1.35), (0.4, 0.6, 0.18), (0.94, 0.80, 0.40), 8, 3)
    for k, (x, y) in enumerate(((-0.72, -2.1), (0.72, -2.1), (-0.72, 2.1), (0.72, 2.1))):
        builder.merge(villager(seed + k, (0.86, 0.80, 0.66), "shoulder", 0.14), placement(x, y, 0.0))
    return builder


def priests_rite(seed=0):
    builder = MeshBuilder()
    builder.merge(priest(seed, "giza_censer"), placement(0.0, 0.0, 0.0))
    tube(builder, [(0.18, 0.5, 1.12), (0.18, 0.55, 0.85)], [0.01, 0.01], (0.4, 0.3, 0.2), 3)
    ellipsoid(builder, (0.18, 0.55, 0.8), (0.07, 0.07, 0.06), (0.86, 0.62, 0.26), 6, 3, "bronze_gilt")
    builder.merge(priest(seed + 1, "giza_raise"), placement(-1.2, -0.6, 0.0, 0.25))
    builder.merge(priest(seed + 2, "forward"), placement(1.2, -0.7, 0.0, -0.25))
    return builder


def guards(seed=0):
    builder = MeshBuilder()
    builder.merge(soldier(seed), placement(-0.8, 0.0, 0.0, 0.2))
    builder.merge(soldier(seed + 1), placement(0.8, 0.2, 0.0, -0.2))
    return builder


def hoeing(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(3):
        fig = villager(seed + k, rng.choice([LINEN, (0.86, 0.80, 0.66), SKY]), "giza_hoe",
                       hat=(0.80, 0.70, 0.46) if k % 2 else None)
        tube(fig, [(0.0, 0.55, 0.8), (0.0, 0.75, 0.05)], [0.02, 0.02], WOOD, 4)
        builder.merge(fig, placement(k * 1.8 - 1.8, rng.uniform(-0.6, 0.6), 0.0, rng.uniform(-0.3, 0.3)))
    return builder


def water_carriers(seed=0):
    builder = MeshBuilder()
    for k, colour in enumerate((SKY, (0.20, 0.24, 0.44), ROSE)):
        builder.merge(peasant_woman(seed + k, colour, stride=0.14 if k % 2 else 0.0), placement(k * 1.1, -k * 1.5,
                                                                                                0.0))
    builder.merge(figure(Look(SAFFRON, hem=0.5, skin=2, hair=3, scale=0.62, child=True, seed=seed + 9)),
                  placement(1.2, 0.6, 0.0, 0.5))
    return builder


def herd(seed=0, kind="goat", count=7):
    rng = random.Random(seed)
    builder = MeshBuilder()
    animal = beast(kind)
    for k in range(count):
        builder.merge(animal, placement(rng.uniform(-4, 4), rng.uniform(-3, 3), 0.0, rng.uniform(0, TAU)))
    builder.merge(villager(seed, (0.80, 0.72, 0.56), "staff", carry="staff", hat=(0.78, 0.66, 0.40)),
                  placement(5.0, 1.0, 0.0, 2.0))
    return builder


def cattle(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(3):
        builder.merge(beast("ox"), placement(k * 3.2, rng.uniform(-1.5, 1.5), 0.0, rng.uniform(0, TAU)))
    return builder


def camels_resting(seed=0):
    builder = MeshBuilder()
    builder.merge(camel(True), placement(0.0, 0.0, 0.0, 0.4))
    builder.merge(camel(False, (0.80, 0.64, 0.44)), placement(3.0, 1.0, 0.0, -0.3))
    builder.merge(villager(seed, (0.92, 0.88, 0.80), "down", hat=None), placement(1.5, -1.5, 0.0, 2.6))
    return builder


def climber(seed=0):
    return villager(seed, LINEN if seed % 2 else (0.86, 0.80, 0.66), "giza_climb", 0.12)


def shaduf(seed=0):
    builder = MeshBuilder()
    for y in (-0.7, 0.7):
        painted(builder, MUD, lambda y=y: builder.box((-0.3, y - 0.25, 0.0), (0.3, y + 0.25, 2.2), MATTE))
    tube(builder, [(0.0, -0.95, 2.2), (0.0, 0.95, 2.2)], [0.08, 0.08], WOOD, 5)
    tube(builder, [(-1.6, 0.0, 1.5), (2.8, 0.0, 3.6)], [0.07, 0.05], WOOD, 5)
    ellipsoid(builder, (-1.7, 0.0, 1.35), (0.35, 0.35, 0.32), MUD, 7, 4)
    tube(builder, [(2.8, 0.0, 3.6), (2.8, 0.0, 0.9)], [0.012, 0.012], (0.3, 0.26, 0.2), 3)
    ellipsoid(builder, (2.8, 0.0, 0.8), (0.18, 0.18, 0.14), (0.48, 0.36, 0.22), 6, 3)
    builder.merge(villager(seed, LINEN, "forward"), placement(2.2, 0.6, 0.0, 2.0))
    return builder


def saqiya(seed=0):
    builder = MeshBuilder()
    builder.lathe([(0.0, 0.0), (2.0, 0.0), (2.0, 0.6), (0.0, 0.6)], 16, MATTE)
    builder.tint(0, (0.62, 0.52, 0.40))
    tube(builder, [(0.0, 0.0, 0.6), (0.0, 0.0, 2.2)], [0.12, 0.1], WOOD, 6)
    tube(builder, [(0.0, 0.0, 1.8), (3.2, 0.0, 1.0)], [0.07, 0.06], WOOD, 5)
    for k in range(10):
        angle = TAU * k / 10
        tube(builder, [(0.0, 0.0, 1.0), (1.1 * math.cos(angle), 1.1 * math.sin(angle), 1.0)], [0.05, 0.05], WOOD,
             4)
    for k in range(14):
        angle = TAU * k / 14
        center = (2.2, 1.6 * math.cos(angle), 0.6 + 1.6 * math.sin(angle))
        ellipsoid(builder, center, (0.14, 0.14, 0.2), (0.70, 0.42, 0.28), 6, 3)
    builder.merge(beast("ox"), placement(2.8, -1.0, 0.0, 0.4))
    builder.merge(figure(Look(SAFFRON, hem=0.5, skin=2, hair=3, scale=0.66, child=True, arms="staff", seed=seed)),
                  placement(3.6, 0.6, 0.0, 2.5))
    return builder


def house(seed, kind="single"):
    rng = random.Random(seed)
    builder = MeshBuilder()
    width = rng.uniform(6.0, 9.0)
    depth = rng.uniform(6.0, 9.0)
    storeys = 2 if kind == "double" else 1
    height = 3.1 * storeys + rng.uniform(-0.2, 0.3)
    material = "plaster" if rng.random() < 0.3 else "mudbrick"
    builder.box((-width / 2, -depth / 2, -0.6), (width / 2, depth / 2, height), material)
    first = len(builder.polygons)
    builder.box((-width / 2 - 0.05, -depth / 2 - 0.05, height), (width / 2 + 0.05, depth / 2 + 0.05, height + 0.18),
                MATTE)
    builder.tint(first, (0.56, 0.46, 0.34))
    for x0, y0, x1, y1 in ((-width / 2, -depth / 2, width / 2, -depth / 2 + 0.3),
                           (-width / 2, depth / 2 - 0.3, width / 2, depth / 2),
                           (-width / 2, -depth / 2, -width / 2 + 0.3, depth / 2),
                           (width / 2 - 0.3, -depth / 2, width / 2, depth / 2)):
        builder.box((x0, y0, height + 0.18), (x1, y1, height + 0.7), material)
    door = rng.uniform(-width / 4, width / 4)
    builder.box((door - 0.5, depth / 2 - 0.05, 0.0), (door + 0.5, depth / 2 + 0.06, 2.0), "shadow_void")
    first = len(builder.polygons)
    builder.box((door - 0.6, depth / 2 + 0.02, 2.0), (door + 0.6, depth / 2 + 0.14, 2.18), MATTE)
    builder.tint(first, (0.40, 0.30, 0.20))
    for k in range(storeys):
        for x in (-width / 3, width / 3):
            builder.box((x - 0.25, depth / 2 - 0.05, 2.3 + k * 3.1), (x + 0.25, depth / 2 + 0.06, 2.75 + k * 3.1),
                        "shadow_void")
    if material == "plaster":
        first = len(builder.polygons)
        builder.box((-width / 2 - 0.02, -depth / 2 - 0.02, 0.0), (width / 2 + 0.02, depth / 2 + 0.02, 0.5), MATTE)
        builder.tint(first, rng.choice([(0.24, 0.44, 0.68), (0.72, 0.26, 0.16), (0.86, 0.66, 0.22)]))
    for k in range(rng.randrange(1, 4)):
        x = rng.uniform(-width / 2 + 1.0, width / 2 - 1.0)
        y = rng.uniform(-depth / 2 + 1.0, depth / 2 - 1.0)
        ellipsoid(builder, (x, y, height + 0.55), (rng.uniform(0.6, 1.0), rng.uniform(0.9, 1.6), 0.45),
                  (0.86, 0.74, 0.40), 7, 3)
    if rng.random() < 0.6:
        x = rng.uniform(-width / 2 + 1.5, width / 2 - 1.5)
        for post in ((-1.2, -1.0), (1.2, -1.0), (-1.2, 1.0), (1.2, 1.0)):
            tube(builder, [(x + post[0], post[1], height + 0.18), (x + post[0], post[1], height + 2.1)],
                 [0.06, 0.06], WOOD, 4)
        painted(builder, (0.52, 0.56, 0.30), lambda: builder.box((x - 1.5, -1.3, height + 2.1),
                                                                 (x + 1.5, 1.3, height + 2.3), MATTE))
    yard = rng.uniform(5.0, 8.0)
    for x0, y0, x1, y1 in ((-width / 2, depth / 2 + yard - 0.4, width / 2, depth / 2 + yard),
                           (-width / 2, depth / 2, -width / 2 + 0.4, depth / 2 + yard),
                           (width / 2 - 0.4, depth / 2, width / 2, depth / 2 + yard * 0.5)):
        builder.box((x0, y0, -0.4), (x1, y1, 1.8), "mudbrick")
    builder.lathe([(0.0, -0.2), (0.7, -0.2), (0.75, 0.4), (0.55, 0.9), (0.2, 1.15), (0.0, 1.2)], 10, "mudbrick",
                  matrix=Matrix.Translation((width / 2 - 1.4, depth / 2 + yard - 1.4, 0.0)))
    return builder


def dovecote(seed=0):
    builder = MeshBuilder()
    builder.lathe([(0.0, -0.4), (2.1, -0.4), (2.0, 2.0), (1.8, 4.0), (1.5, 5.6), (1.6, 5.8), (1.2, 6.6), (0.0, 7.0)],
                  14, "plaster")
    for k in range(18):
        angle = TAU * k / 18
        for ring in range(2):
            r = 1.62 - ring * 0.25
            ellipsoid(builder, (r * math.cos(angle), r * math.sin(angle), 5.95 + ring * 0.45), (0.14, 0.14, 0.12),
                      (0.70, 0.42, 0.28), 6, 3)
    first = len(builder.polygons)
    builder.lathe([(2.02, 3.0), (1.96, 3.3)], 14, MATTE)
    builder.tint(first, (0.30, 0.46, 0.66))
    return builder


def granaries(seed=0):
    builder = MeshBuilder()
    for k, (x, y) in enumerate(((0.0, 0.0), (2.6, 0.4), (1.2, 2.3))):
        builder.lathe([(0.0, -0.3), (1.15, -0.3), (1.2, 1.4), (0.9, 2.8), (0.4, 3.5), (0.0, 3.6)], 12, "mudbrick",
                      matrix=Matrix.Translation((x, y, 0.0)))
    return builder


def acacia(seed=0, height=6.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    top = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), height * 0.6))
    tube(builder, [(0.0, 0.0, 0.0), top * 0.5, top], [0.22, 0.18, 0.14], (0.36, 0.28, 0.22), 6)
    for k in range(5):
        angle = TAU * k / 5 + rng.uniform(-0.3, 0.3)
        tip = top + Vector((math.cos(angle) * height * 0.32, math.sin(angle) * height * 0.32, height * 0.28))
        tube(builder, [top, tip], [0.1, 0.05], (0.36, 0.28, 0.22), 4)
        ellipsoid(builder, tip, (height * 0.3, height * 0.3, height * 0.08), (0.36, 0.48, 0.20), 9, 3)
    return builder


def sycamore(seed=0):
    return broad_tree(rng_height(seed), seed, (0.22, 0.38, 0.14), 7)


def rng_height(seed):
    return 9.0 + (seed % 5) * 0.8


def palm(seed=0, height=12.0):
    return date_palm(height, seed, True)


def tamarisk(seed=0):
    return shrub(2.2, seed, (0.40, 0.48, 0.30))


def fodder_stack(seed=0):
    builder = MeshBuilder()
    rng = random.Random(seed)
    for k in range(4):
        ellipsoid(builder, (rng.uniform(-1, 1), rng.uniform(-1, 1), 0.6), (1.0, 1.4, 0.8), (0.86, 0.74, 0.40), 8, 4)
    return builder


def skiff(seed=0):
    return ships.fishing_boat(seed, 6.5, 1.8, sail=seed % 2 == 0)


def rock_cluster(seed=0, spread=2.4, count=6, material="core_stone"):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        size = rng.uniform(0.18, 0.75)
        tone = rng.uniform(0.86, 1.08)
        ellipsoid(builder, (rng.uniform(-spread, spread), rng.uniform(-spread, spread), size * 0.15),
                  (size * rng.uniform(1.0, 1.6), size, size * rng.uniform(0.45, 0.8)),
                  (tone, tone * 0.97, tone * 0.92), 7, 4, material)
    return builder


def boulder(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    size = rng.uniform(1.0, 1.8)
    ellipsoid(builder, (0.0, 0.0, size * 0.25), (size * 1.4, size, size * 0.75), (1.0, 0.96, 0.9), 9, 5,
              "sphinx_rock")
    for k in range(4):
        s = rng.uniform(0.2, 0.5)
        ellipsoid(builder, (rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2), s * 0.1), (s * 1.3, s, s * 0.6),
                  (0.95, 0.9, 0.82), 6, 3, "core_stone")
    return builder


def debris(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(5):
        w = rng.uniform(0.6, 1.4)
        d = rng.uniform(0.5, 1.0)
        h = rng.uniform(0.4, 0.9)
        frame = placement(rng.uniform(-3, 3), rng.uniform(-3, 3), -0.15, rng.uniform(0, TAU))
        builder.box((-w / 2, -d / 2, 0.0), (w / 2, d / 2, h), "casing" if k % 2 else "core_stone", matrix=frame)
    return builder


ROCKS = {
    "rocks_a": lambda: rock_cluster(1),
    "rocks_b": lambda: rock_cluster(2, 3.0, 8, "sphinx_rock"),
    "boulder": lambda: boulder(3),
    "debris": lambda: debris(4),
}

SHIPS = {
    "barge_set": lambda: ships.nile_barge(12, sail="set"),
    "barge_set_b": lambda: ships.nile_barge(14, 24.0, 6.0, sail="set"),
    "barge_furled": lambda: ships.nile_barge(13, sail="furled"),
    "merchant_set": lambda: ships.merchant(2, "set"),
    "merchant_brailed": lambda: ships.merchant(1, "brailed"),
    "galley": lambda: ships.galley(7, 30.0, 4.8),
    "fishing": lambda: ships.fishing_boat(10),
    "fishing_sail": lambda: ships.fishing_boat(11, sail=True),
    "skiff": lambda: skiff(3),
}

LIFE = {
    "guide_group": lambda: coarse(guide_group, 1.0),
    "visitors": lambda: coarse(visitors, 1.0),
    "visitors_b": lambda: coarse(lambda: visitors(23, 2), 1.0),
    "litter": lambda: coarse(litter, 0.9),
    "priests": lambda: coarse(priests_rite, 1.0),
    "guards": lambda: coarse(guards, 1.0),
    "hoeing": lambda: coarse(hoeing, 0.9),
    "water_carriers": lambda: coarse(water_carriers, 0.9),
    "goats": lambda: coarse(herd, 0.9),
    "cattle": lambda: coarse(cattle, 0.9),
    "camels": lambda: coarse(camels_resting, 0.9),
    "camel_train": lambda: coarse(camel_train, 0.9),
    "donkey_driver": lambda: coarse(donkey_driver, 0.9),
    "climber": lambda: coarse(climber, 1.0),
    "climber_b": lambda: coarse(lambda: climber(7), 1.0),
    "shaduf": lambda: coarse(shaduf, 0.9),
    "saqiya": lambda: coarse(saqiya, 0.9),
    "fig_villager": lambda: villager(41, LINEN, "down"),
    "fig_woman": lambda: peasant_woman(42),
    "fig_roman": lambda: roman(43, WHITE_LINEN, CRIMSON, "gesture"),
    "fig_soldier": lambda: soldier(44),
    "donkey": lambda: pack_beast("donkey"),
}

WALKERS = {
    "walker_roman": lambda: roman(71, (0.94, 0.90, 0.80), INDIGO, "swing", 0.17),
    "walker_lady": lambda: figure(lady(72, ROSE, (0.96, 0.92, 0.84), "swing", stride=0.14)),
    "walker_villager": lambda: villager(73, LINEN, "swing", 0.2),
    "walker_woman": lambda: peasant_woman(74, SKY, (0.20, 0.20, 0.26), "head", "jar", 0.15),
    "walker_soldier": lambda: figure(Look((0.58, 0.58, 0.60), hem=0.58, skin=1, hair=0, belt=LEATHER, cloak=CRIMSON,
                                          arms="swing", stride=0.2, sleeves="long", seed=75)),
    "walker_priest": lambda: figure(Look(WHITE_LINEN, hem=0.03, skin=1, hair=SHAVEN, arms="swing", stride=0.12,
                                         belt=(0.96, 0.92, 0.80), seed=76)),
}

HOUSES = {
    "house_a": lambda: house(1, "single"),
    "house_b": lambda: house(2, "double"),
    "house_c": lambda: house(3, "single"),
    "house_d": lambda: house(4, "double"),
    "house_e": lambda: house(5, "single"),
    "house_f": lambda: house(8, "single"),
    "house_g": lambda: house(11, "double"),
    "dovecote": lambda: dovecote(0),
    "granaries": lambda: granaries(0),
}

TREES = {
    "palm_0": lambda: palm(1, 11.0),
    "palm_1": lambda: palm(2, 13.5),
    "palm_2": lambda: palm(3, 15.5),
    "sycamore": lambda: sycamore(4),
    "acacia": lambda: acacia(5),
    "tamarisk": lambda: tamarisk(6),
}

import math
import random

from mathutils import Matrix

from . import nimes_figures
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, WOOD
from .nimes_figures import Look, ellipsoid, person, tube

TUNICS = ["undyed", "madder", "weld", "woad", "ochre", "brown", "green", "grey", "rose", "white"]
CUSHION = (0.86, 0.80, 0.66)
LINEN = (0.90, 0.87, 0.80)


def facing(x, y, tx, ty):
    return math.atan2(-(tx - x), ty - y)


def cushion(builder, colour=CUSHION):
    ellipsoid(builder, (0.0, 0.0, 1.80), (0.21, 0.17, 0.075), colour, 8, 4)
    tube(builder, [(0.0, -0.13, 1.82), (0.0, -0.105, 1.66), (0.0, -0.085, 1.52)], [0.022, 0.02, 0.018], LINEN, 4)
    tube(builder, [(-0.17, 0.0, 1.8), (-0.1, 0.02, 1.62), (-0.09, 0.0, 1.55)], [0.02, 0.018, 0.016], LINEN, 4)
    tube(builder, [(0.17, 0.0, 1.8), (0.1, 0.02, 1.62), (0.09, 0.0, 1.55)], [0.02, 0.018, 0.016], LINEN, 4)


def chest(builder, colour=(0.42, 0.30, 0.19)):
    first = len(builder.polygons)
    builder.box((0.02, -0.28, 1.5), (0.42, 0.28, 1.78), MATTE)
    builder.tint(first, colour)
    first = len(builder.polygons)
    for y in (-0.2, 0.2):
        builder.box((0.01, y - 0.025, 1.49), (0.43, y + 0.025, 1.79), MATTE)
    builder.tint(first, (0.62, 0.48, 0.24))


def sack(builder, x, y, z, size, colour=(0.66, 0.58, 0.44)):
    ellipsoid(builder, (x, y, z), (size * 0.8, size * 0.7, size), colour, 7, 4)


def fugitive(seed, kind):
    rng = random.Random(seed)
    tunic = rng.choice(TUNICS)
    skin = rng.randrange(3)
    hair = rng.randrange(4)
    female = kind in ("mother", "veiled", "basket_woman", "cushion_woman")
    if female:
        look = Look(tunic, hem=0.04, skin=skin, hair=hair, palla=rng.choice(TUNICS), veil=kind != "basket_woman",
                    female=True, sleeves="long", stride=0.13,
                    arms={"mother": "forward", "veiled": "head", "basket_woman": "head",
                          "cushion_woman": "swing"}[kind],
                    carry="basket" if kind == "basket_woman" else None, scale=0.95, seed=seed)
    elif kind == "child":
        look = Look(tunic, hem=0.5, skin=skin, hair=hair, scale=0.62, belt="brown", child=True, arms="swing",
                    stride=0.12, seed=seed)
    else:
        look = Look(tunic, hem=0.55, skin=skin, hair=hair, belt=rng.choice(["brown", "dark", LEATHER]),
                    cloak=rng.choice([None, "brown", "dark", "madder"]) if kind != "porter" else None,
                    stride=0.18,
                    arms={"bundle": "swing", "porter": "carry", "chest": "carry", "cushion": "swing",
                          "pointing": "gesture", "shelter": "head", "jar": "head", "staff": "staff"}[kind],
                    carry={"bundle": "bundle", "porter": "amphora", "jar": "jar", "staff": "staff"}.get(kind),
                    hood=rng.choice([None, "brown"]) if kind == "shelter" else None, seed=seed)
    builder = person(look)
    if kind in ("cushion", "cushion_woman"):
        cushion(builder)
    if kind == "chest":
        chest(builder)
    return builder


def group(seed, kinds, spread=0.9, heading=0.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    count = len(kinds)
    for index, kind in enumerate(kinds):
        row, column = divmod(index, 3)
        x = (column - 1) * spread * 0.75 + rng.uniform(-0.18, 0.18)
        y = -row * spread + rng.uniform(-0.2, 0.2)
        builder.merge(fugitive(seed * 13 + index, kind), placement(x, y, 0.0, heading + rng.uniform(-0.25, 0.25)))
    if count == 0:
        return builder
    return builder


def family(seed=1):
    builder = group(seed, ["bundle", "mother", "child", "chest"], 0.95)
    sack(builder, 0.55, -0.9, 0.18, 0.2)
    return builder


def household(seed=2):
    builder = group(seed, ["cushion", "veiled", "porter", "child", "basket_woman"], 1.0)
    return builder


def shelterers(seed=3, count=6):
    rng = random.Random(seed)
    builder = MeshBuilder()
    kinds = ["shelter", "pointing", "veiled", "shelter", "child", "mother", "pointing", "cushion_woman"]
    for index in range(count):
        angle = 2 * math.pi * index / count + rng.uniform(-0.3, 0.3)
        radius = rng.uniform(0.6, 1.3)
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        turn = rng.uniform(-0.6, 0.6)
        builder.merge(fugitive(seed * 31 + index, kinds[index % len(kinds)]), placement(x, y, 0.0, turn))
    return builder


def onlookers(seed=4):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index, kind in enumerate(["pointing", "shelter", "veiled", "pointing"]):
        x = (index - 1.5) * 0.85 + rng.uniform(-0.15, 0.15)
        builder.merge(fugitive(seed * 17 + index, kind), placement(x, rng.uniform(-0.3, 0.3), 0.0,
                                                                   rng.uniform(-0.4, 0.4)))
    return builder


def shopkeeper(seed=5):
    rng = random.Random(seed)
    builder = person(Look(rng.choice(TUNICS), hem=0.56, skin=rng.randrange(3), hair=rng.randrange(4),
                          apron="undyed", belt="brown", arms="forward", seed=seed))
    first = len(builder.polygons)
    builder.box((-0.4, 0.27, 0.15), (0.45, 0.31, 2.4), MATTE)
    builder.tint(first, (0.40, 0.29, 0.19))
    return builder


def plank_stack(seed=6):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for index in range(5):
        x = index * 0.2 + rng.uniform(-0.03, 0.03)
        frame = Matrix.Translation((x, 0.0, 0.0)) @ Matrix.Rotation(math.radians(-14), 4, "X")
        first = len(builder.polygons)
        builder.box((-0.09, -0.02, 0.0), (0.09, 0.02, 2.5), MATTE, matrix=frame)
        builder.tint(first, (0.40 * rng.uniform(0.85, 1.1), 0.29, 0.19))
    return builder


def wagon():
    return nimes_figures.mule_wagon()


def pack_train(seed=7):
    builder = MeshBuilder()
    builder.merge(nimes_figures.pack_beast("mule"), placement(0.0, 0.0, 0.0))
    builder.merge(nimes_figures.pack_beast("donkey"), placement(0.2, -2.3, 0.0))
    builder.merge(fugitive(seed, "staff"), placement(-0.75, 0.9, 0.0))
    tube(builder, [(-0.55, 1.0, 1.0), (-0.1, 0.9, 1.05), (0.0, 0.65, 1.2)], [0.012, 0.012, 0.012], LEATHER, 3)
    return builder


def handcart(seed=8):
    rng = random.Random(seed)
    builder = MeshBuilder()
    nimes_figures.wheel(builder, -0.55, 0.0, 0.42, 0.06, spokes=4)
    nimes_figures.wheel(builder, 0.55, 0.0, 0.42, 0.06, spokes=4)
    first = len(builder.polygons)
    builder.box((-0.5, -0.8, 0.5), (0.5, 0.7, 0.62), MATTE)
    builder.tint(first, WOOD)
    for index in range(5):
        sack(builder, rng.uniform(-0.3, 0.3), rng.uniform(-0.6, 0.5), 0.8 + (index // 3) * 0.2, 0.22,
             rng.choice([(0.66, 0.58, 0.44), (0.58, 0.32, 0.22), (0.80, 0.74, 0.60)]))
    for side in (-1, 1):
        tube(builder, [(side * 0.4, 0.7, 0.58), (side * 0.38, 1.6, 0.85)], [0.03, 0.03], WOOD, 4)
    builder.merge(fugitive(seed + 3, "bundle"), placement(0.0, 1.85, 0.0))
    return builder


def dog():
    return nimes_figures.beast("dog")


def fleeing_on_road(seed=9, count=7):
    rng = random.Random(seed)
    builder = MeshBuilder()
    kinds = ["bundle", "mother", "child", "porter", "cushion", "veiled", "chest", "basket_woman", "jar"]
    for index in range(count):
        x = rng.uniform(-1.6, 1.6)
        y = -index * 1.25 + rng.uniform(-0.3, 0.3)
        builder.merge(fugitive(seed * 7 + index, kinds[(index + seed) % len(kinds)]),
                      placement(x, y, 0.0, rng.uniform(-0.2, 0.2)))
    return builder


WALKERS = {
    "walker_bundle": lambda: fugitive(101, "bundle"),
    "walker_veiled": lambda: fugitive(102, "veiled"),
    "walker_chest": lambda: fugitive(103, "chest"),
    "walker_cushion": lambda: fugitive(104, "cushion"),
    "walker_basket": lambda: fugitive(105, "basket_woman"),
    "walker_porter": lambda: fugitive(106, "porter"),
}

LIFE = {
    "family": family,
    "household": household,
    "household_b": lambda: household(12),
    "shelterers": shelterers,
    "shelterers_b": lambda: shelterers(13, 5),
    "onlookers": onlookers,
    "shopkeeper": shopkeeper,
    "plank_stack": plank_stack,
    "wagon": wagon,
    "pack_train": pack_train,
    "handcart": handcart,
    "dog": dog,
    "road_column": fleeing_on_road,
    "road_column_b": lambda: fleeing_on_road(19, 6),
    "fig_bundle": lambda: fugitive(201, "bundle"),
    "fig_veiled": lambda: fugitive(202, "veiled"),
    "fig_cushion": lambda: fugitive(203, "cushion_woman"),
    "fig_pointing": lambda: fugitive(204, "pointing"),
    "fig_chest": lambda: fugitive(205, "chest"),
    "fig_child": lambda: fugitive(206, "child"),
    "fig_bundle_b": lambda: fugitive(211, "bundle"),
    "fig_veiled_b": lambda: fugitive(212, "veiled"),
    "fig_shelter": lambda: fugitive(213, "shelter"),
    "fig_jar": lambda: fugitive(214, "jar"),
    "fig_basket": lambda: fugitive(215, "basket_woman"),
    "family_b": lambda: family(21),
}

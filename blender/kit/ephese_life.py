import math
import random

from mathutils import Matrix

from . import alexandrie_life as alife
from .alexandrie_life import CRIMSON, INDIGO, LINEN, OLIVE, SAFFRON, TURQUOISE, figure, greek, lady
from .ephese_artemision import artemis_statue, figurine_stall, offering_table, ox
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, WOOD
from .nimes_figures import Look, beast, coarse, ellipsoid, ox_cart, person, tube

GOLD = (1.0, 0.80, 0.40)
SILVER = (0.86, 0.86, 0.88)
ROSE = (0.86, 0.46, 0.50)
SKY = (0.48, 0.66, 0.86)
MADDER = (0.78, 0.26, 0.18)
WHITE = (0.97, 0.95, 0.90)
TAU = 2 * math.pi


def toga(seed, arms="toga", stride=0.0, praetexta=None, carry=None, skin=0, hair=0):
    return Look("white", hem=0.12, skin=skin, hair=hair, toga="white", praetexta=praetexta, arms=arms, stride=stride,
                carry=carry, seed=seed)


def ephebe(seed, arms="forward", stride=0.0, cloak=WHITE):
    return Look(WHITE, hem=0.6, skin=seed % 3, hair=seed % 4, cloak=cloak, belt=(0.86, 0.70, 0.36), arms=arms,
                stride=stride, seed=seed)


def statuette(colour=GOLD, seed=0, scale=0.6):
    builder = person(Look("white", hem=0.03, palla="white", veil=seed % 2 == 0, female=seed % 2 == 0, sleeves="long",
                          arms="hip", mono=colour, material="bronze_gilt", seed=seed))
    scaled = MeshBuilder()
    scaled.merge(builder, Matrix.Scale(scale, 4))
    scaled.box((-0.12, -0.12, -0.08), (0.12, 0.12, 0.0), "bronze_gilt")
    scaled.tint(len(scaled.polygons) - 6, colour)
    return scaled


def emperor_statue(seed=0):
    builder = person(Look("white", hem=0.55, cloak="white", arms="gesture", mono=GOLD, material="bronze_gilt",
                          seed=seed))
    ellipsoid(builder, (0.0, 0.01, 1.2), (0.19, 0.15, 0.26), GOLD, 10, 6, "bronze_gilt")
    for k in range(9):
        angle = math.pi * 2 * k / 9
        tube(builder, [(0.17 * math.cos(angle), 0.13 * math.sin(angle), 0.98),
                       (0.2 * math.cos(angle), 0.16 * math.sin(angle), 0.78)], [0.04, 0.035], GOLD, 3, "bronze_gilt")
    scaled = MeshBuilder()
    scaled.merge(builder, Matrix.Scale(0.6, 4))
    return scaled


def empress_statue(seed=0):
    builder = person(Look("white", hem=0.03, palla="white", veil=True, female=True, sleeves="long", arms="gesture",
                          mono=GOLD, material="bronze_gilt", seed=seed))
    scaled = MeshBuilder()
    scaled.merge(builder, Matrix.Scale(0.6, 4))
    return scaled


def goddess_statue():
    scaled = MeshBuilder()
    scaled.merge(artemis_statue(), Matrix.Scale(0.32, 4))
    return scaled


def ferculum(seed, statue, cloth):
    builder = MeshBuilder()
    for k, (x, y) in enumerate(((-0.62, 1.15), (0.62, 1.15), (-0.62, -1.15), (0.62, -1.15))):
        builder.merge(figure(ephebe(seed + k, "shoulder", 0.1)), placement(x, y, 0.0))
    for x in (-0.62, 0.62):
        tube(builder, [(x, -1.9, 1.5), (x, 1.9, 1.5)], [0.045, 0.045], (0.52, 0.36, 0.22), 5)
    builder.box((-0.66, -0.95, 1.52), (0.66, 0.95, 1.64), "bronze_gilt")
    builder.tint(len(builder.polygons) - 6, GOLD)
    builder.box((-0.7, -1.0, 1.3), (0.7, 1.0, 1.52), MATTE, top=False)
    builder.tint(len(builder.polygons) - 5, cloth)
    builder.merge(statue, Matrix.Translation((0.0, 0.0, 1.64)))
    return builder


def bearer(seed, colour):
    builder = figure(ephebe(seed, "forward", 0.12))
    builder.merge(statuette(colour, seed), Matrix.Translation((0.0, 0.42, 0.9)))
    return builder


def procession(seed=0):
    builder = MeshBuilder()
    for k, x in enumerate((-1.2, 0.0, 1.2)):
        look = Look(LINEN, hem=0.12, skin=1, hair=2, palla=(0.62, 0.30, 0.50) if k == 1 else INDIGO,
                    arms="toga_gesture", carry="staff" if k == 1 else None, stride=0.1, seed=seed + 40 + k)
        builder.merge(figure(look), placement(x, 5.2, 0.0))
    builder.merge(ferculum(seed, goddess_statue(), (0.70, 0.14, 0.12)), placement(0.0, 1.6, 0.0))
    builder.merge(ferculum(seed + 10, emperor_statue(seed + 11), (0.42, 0.12, 0.40)), placement(0.0, -3.0, 0.0))
    builder.merge(ferculum(seed + 20, empress_statue(seed + 21), (0.16, 0.30, 0.62)), placement(0.0, -7.4, 0.0))
    for k in range(4):
        builder.merge(bearer(seed + 30 + k, SILVER if k % 2 else GOLD),
                      placement(-0.8 if k % 2 else 0.8, -10.8 - (k // 2) * 1.9, 0.0))
    builder.merge(figure(Look(WHITE, hem=0.12, skin=0, hair=2, palla=(0.92, 0.72, 0.30), arms="gesture", stride=0.12,
                              seed=seed + 50)), placement(0.0, -15.2, 0.0))
    return builder


def fasces(builder, x, y, z):
    for k in range(5):
        dx = (k % 3 - 1) * 0.03
        dy = (k // 3) * 0.03
        tube(builder, [(x + dx, y + dy - 0.2, z - 0.6), (x + dx, y + dy + 0.1, z + 0.5)], [0.016, 0.016],
             (0.62, 0.44, 0.26), 3)
    tube(builder, [(x, y - 0.06, z - 0.1), (x, y - 0.04, z + 0.1)], [0.06, 0.06], (0.72, 0.18, 0.14), 5)
    tube(builder, [(x + 0.03, y + 0.12, z + 0.45), (x + 0.16, y + 0.14, z + 0.55)], [0.012, 0.05],
         (0.74, 0.74, 0.76), 3)


def lictor(seed):
    builder = figure(Look(WHITE, hem=0.55, skin=1, hair=0, cloak=(0.70, 0.14, 0.10), belt=LEATHER, arms="shoulder",
                          stride=0.12, seed=seed))
    fasces(builder, 0.26, 0.08, 1.55)
    return builder


def proconsul(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(toga(seed, "toga_gesture", 0.1, praetexta="purple", skin=0, hair=2)), placement(0.0, 0.0,
                                                                                                         0.0))
    for k in range(12):
        builder.merge(lictor(seed + k + 1), placement(0.0, 2.0 + k * 1.3, 0.0))
    builder.merge(figure(toga(seed + 20, "toga", 0.1, skin=1, hair=0)), placement(-0.9, -1.4, 0.0))
    builder.merge(figure(toga(seed + 21, "toga", 0.1, carry="scroll", skin=1, hair=3)), placement(0.9, -1.6, 0.0))
    for x in (-1.4, 1.4):
        builder.merge(alife.soldier(seed + 30 + int(x)), placement(x, -3.0, 0.0))
    return builder


def sacrifice(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(ox((0.96, 0.94, 0.90)), placement(0.0, 0.0, 0.0, math.pi / 2))
    builder.merge(figure(Look(WHITE, hem=0.12, skin=0, hair=2, palla=(0.96, 0.92, 0.84), veil=True, arms="toga_gesture",
                              carry="patera", seed=seed)), placement(2.6, 0.6, 0.0, math.pi / 2))
    builder.merge(figure(Look(WHITE, hem=0.6, skin=1, hair=1, belt=(0.62, 0.20, 0.14), exomis=True, arms="forward",
                              seed=seed + 1)), placement(-0.6, 0.9, 0.0, -math.pi / 2))
    builder.merge(figure(Look(SAFFRON, hem=0.6, skin=2, hair=3, belt=LEATHER, arms="forward", seed=seed + 2)),
                  placement(0.4, -1.0, 0.0, 0.0))
    flute = figure(Look(ROSE, hem=0.12, skin=1, hair=0, palla=(0.92, 0.86, 0.70), arms="forward", seed=seed + 3))
    for side in (-0.06, 0.06):
        tube(flute, [(side, 0.12, 1.55), (side * 3, 0.45, 1.3)], [0.012, 0.016], (0.86, 0.72, 0.46), 3)
    builder.merge(flute, placement(3.2, -1.2, 0.0, math.pi / 2 + 0.4))
    for k in range(3):
        angle = rng.uniform(0, TAU)
        builder.merge(figure(lady(seed + 10 + k, rng.choice([SAFFRON, LINEN, ROSE, SKY]), rng.choice([INDIGO, CRIMSON,
                                                                                                    TURQUOISE]),
                                  "head" if k == 0 else "down", carry="jar" if k == 0 else None)),
                      placement(-3.0 + k * 1.1, 2.6 + math.sin(angle) * 0.3, 0.0, math.pi))
    return builder


def pilgrims(seed=0, count=4):
    rng = random.Random(seed)
    builder = MeshBuilder()
    mantles = [INDIGO, TURQUOISE, CRIMSON, OLIVE, (0.62, 0.30, 0.50), (0.92, 0.72, 0.30), SKY, ROSE]
    for k in range(count):
        x = (k % 2) * 0.9 - 0.45 + rng.uniform(-0.15, 0.15)
        y = -(k // 2) * 1.3 + rng.uniform(-0.2, 0.2)
        roll = rng.random()
        if roll < 0.4:
            look = lady(seed + k, rng.choice([SAFFRON, LINEN, ROSE, SKY, (0.86, 0.50, 0.46)]), rng.choice(mantles),
                        rng.choice(["swing", "down", "head"]), stride=0.14,
                        carry="jar" if rng.random() < 0.3 else None)
        elif roll < 0.55:
            look = toga(seed + k, "toga", 0.12, skin=rng.randrange(2), hair=rng.randrange(4))
        else:
            look = greek(seed + k, rng.choice([LINEN, (0.92, 0.88, 0.78), (0.84, 0.86, 0.90), MADDER]),
                         rng.choice(mantles), rng.choice(["swing", "gesture"]), stride=0.15, skin=rng.randrange(3),
                         hair=rng.randrange(4), carry="staff" if rng.random() < 0.3 else None)
        builder.merge(figure(look), placement(x, y, 0.0, rng.uniform(-0.2, 0.2)))
    return builder


def family(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(greek(seed, LINEN, INDIGO, "gesture", skin=1, hair=0)), placement(-0.5, 0.0, 0.0))
    builder.merge(figure(lady(seed + 1, SAFFRON, TURQUOISE, "down")), placement(0.4, 0.2, 0.0))
    builder.merge(figure(Look(MADDER, hem=0.5, skin=1, hair=1, scale=0.62, child=True, seed=seed + 2)),
                  placement(0.0, 0.9, 0.0))
    builder.merge(beast("dog"), placement(1.2, 0.8, 0.0, 0.8))
    return builder


def vendor(seed=0):
    builder = MeshBuilder()
    builder.merge(figurine_stall(seed), placement(0.0, 0.0, 0.0))
    builder.merge(figure(Look((0.80, 0.70, 0.52), hem=0.55, skin=2, hair=1, belt=LEATHER, arms="gesture",
                              apron=(0.86, 0.80, 0.66), seed=seed + 5)), placement(0.0, 0.6, 0.0, math.pi))
    builder.merge(figure(lady(seed + 6, ROSE, INDIGO, "hip")), placement(-0.8, -2.0, 0.0, 0.2))
    builder.merge(figure(greek(seed + 7, LINEN, OLIVE, "gesture")), placement(0.9, -2.1, 0.0, -0.3))
    return builder


def offering(seed=0):
    builder = MeshBuilder()
    builder.merge(offering_table(seed), placement(0.0, 0.0, 0.0))
    builder.merge(figure(lady(seed + 3, WHITE, (0.92, 0.72, 0.30), "forward")), placement(0.0, -1.2, 0.0))
    builder.merge(figure(greek(seed + 4, LINEN, CRIMSON, "down")), placement(1.0, -1.6, 0.0, 0.3))
    return builder


def ploughman(seed=0):
    builder = MeshBuilder()
    for x in (-0.6, 0.6):
        builder.merge(beast("ox"), placement(x, 0.0, 0.0))
    tube(builder, [(-0.9, 1.0, 1.1), (0.9, 1.0, 1.1)], [0.06, 0.06], WOOD, 4)
    tube(builder, [(0.0, 1.0, 1.1), (0.0, -2.6, 0.5), (0.0, -3.1, 0.0)], [0.05, 0.05, 0.04], WOOD, 4)
    builder.merge(figure(Look((0.74, 0.62, 0.44), hem=0.55, skin=2, hair=1, belt="brown", exomis=True, arms="forward",
                              hat=(0.78, 0.66, 0.40), stride=0.15, seed=seed)), placement(0.0, -3.6, 0.0))
    return builder


def shepherd(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(figure(Look((0.70, 0.58, 0.42), hem=0.5, skin=2, hair=1, cloak="brown", belt="dark", carry="staff",
                              arms="staff", hood="brown", seed=seed)), placement(0.0, 0.0, 0.0))
    for k in range(9):
        builder.merge(beast("goat"), placement(rng.uniform(-4.0, 4.0), rng.uniform(1.0, 6.0), 0.0, rng.uniform(0, TAU)))
    return builder


def fishermen(seed=0):
    return alife.fisher_pair(seed)


def seated_reader(seed=0):
    builder = MeshBuilder()
    builder.box((-0.9, -0.3, 0.0), (0.9, 0.3, 0.45), "marble")
    builder.tint(len(builder.polygons) - 6, (0.96, 0.94, 0.88))
    builder.merge(figure(toga(seed, "toga_gesture", 0.0, carry="scroll", skin=1, hair=2)), placement(-0.4, -0.6, 0.0))
    builder.merge(figure(greek(seed + 1, LINEN, INDIGO, "hip")), placement(0.6, -0.9, 0.0, 0.5))
    return builder


BASE = {
    "dock_gang": alife.dock_gang,
    "scale_table": alife.scale_table,
    "conversation": alife.conversation,
    "conversation_b": lambda: alife.conversation(31, 4),
    "conversation_c": lambda: alife.conversation(47, 2),
    "porters_line": alife.porters_line,
    "donkey_driver": alife.donkey_driver,
    "fisher_pair": alife.fisher_pair,
    "amphora_stack": lambda: alife.amphora_rank(5, 16),
    "sack_pile": lambda: alife.sack_heap(3),
    "fig_greek": lambda: figure(greek(61, LINEN, INDIGO, "hip")),
    "fig_greek_b": lambda: figure(greek(62, (0.92, 0.88, 0.78), CRIMSON, "gesture", skin=0, hair=2)),
    "fig_lady": lambda: figure(lady(63)),
    "fig_lady_b": lambda: figure(lady(64, LINEN, (0.70, 0.30, 0.50), "head", carry="jar")),
    "fig_docker": lambda: figure(alife.docker(65)),
    "fig_sack": lambda: alife.sack_carrier(66),
    "fig_child": lambda: figure(Look(SAFFRON, hem=0.5, skin=1, hair=1, scale=0.62, child=True, seed=68)),
}
LIFE = {key: (lambda build=build, key=key: coarse(build, 1.0 if key.startswith("fig_") else 0.6))
        for key, build in BASE.items()}
LIFE.update({
    "procession": lambda: coarse(lambda: procession(400), 0.75),
    "proconsul": lambda: coarse(lambda: proconsul(500), 0.7),
    "sacrifice": lambda: coarse(lambda: sacrifice(600), 0.55),
    "pilgrims": lambda: coarse(lambda: pilgrims(700, 4), 0.55),
    "pilgrims_b": lambda: coarse(lambda: pilgrims(710, 3), 0.55),
    "pilgrims_c": lambda: coarse(lambda: pilgrims(720, 5), 0.55),
    "family": lambda: coarse(lambda: family(730), 0.55),
    "vendor": lambda: coarse(lambda: vendor(740), 0.55),
    "vendor_b": lambda: coarse(lambda: vendor(741), 0.55),
    "offering": lambda: coarse(lambda: offering(750), 0.55),
    "ploughman": lambda: coarse(lambda: ploughman(760), 0.7),
    "shepherd": lambda: coarse(lambda: shepherd(770), 0.7),
    "reader": lambda: coarse(lambda: seated_reader(780), 0.55),
    "ox_cart": lambda: coarse(ox_cart, 0.55),
    "fig_toga": lambda: coarse(lambda: figure(toga(790, "toga", skin=0, hair=0)), 1.0),
    "fig_toga_b": lambda: coarse(lambda: figure(toga(791, "toga_gesture", carry="scroll", skin=1, hair=2)), 1.0),
    "fig_priestess": lambda: coarse(lambda: figure(Look(WHITE, hem=0.03, skin=0, hair=1, palla=(0.96, 0.92, 0.84),
                                                        veil=True, female=True, sleeves="long", arms="forward",
                                                        carry="patera", seed=792)), 1.0),
    "fig_ephebe": lambda: coarse(lambda: figure(ephebe(793, "hip")), 1.0),
})

WALKER_BUILDS = {
    "walker_pilgrim": lambda: figure(greek(801, LINEN, INDIGO, "swing", stride=0.17)),
    "walker_lady": lambda: figure(lady(802, ROSE, (0.96, 0.92, 0.84), "swing", stride=0.14)),
    "walker_citizen": lambda: figure(toga(803, "toga", 0.17, skin=1, hair=0)),
    "walker_porter": lambda: figure(alife.docker(804, (0.86, 0.80, 0.66), stride=0.2)),
    "walker_ephebe": lambda: figure(ephebe(805, "swing", 0.2, (0.70, 0.30, 0.50))),
    "walker_rural": lambda: figure(Look((0.74, 0.62, 0.44), hem=0.52, skin=2, hair=0, cloak="dark", belt="brown",
                                        stride=0.2, arms="swing", hat=(0.78, 0.66, 0.40), carry="bundle", seed=806)),
}


def heaped_produce(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(6):
        ellipsoid(builder, (rng.uniform(-1.0, 1.0), rng.uniform(-0.6, 0.6), 0.25), (0.4, 0.35, 0.3),
                  rng.choice([(0.86, 0.74, 0.40), (0.62, 0.70, 0.30), (0.80, 0.50, 0.24)]), 6, 3, MATTE)
    return builder


WALKERS = {key: (lambda build=build: coarse(build, 1.0)) for key, build in WALKER_BUILDS.items()}

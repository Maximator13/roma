import math
import random

from . import alexandrie_life as alife
from . import olympie_life as olife
from .geometry import MeshBuilder, placement
from .life import LEATHER
from .nimes_figures import POSES, Look, coarse, person

POSES.update({
    "rhodes_embrace": [((0.25, 0.2, 1.3), (0.06, 0.4, 1.3)), ((-0.25, 0.2, 1.3), (-0.06, 0.4, 1.28))],
    "rhodes_point": [((0.29, 0.18, 1.36), (0.36, 0.44, 1.56)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "rhodes_touch": [((0.27, 0.22, 1.22), (0.28, 0.5, 1.2)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
})

TAU = 2 * math.pi
LINEN = (0.97, 0.95, 0.90)
SAFFRON = (0.96, 0.70, 0.16)
CRIMSON = (0.80, 0.12, 0.10)
INDIGO = (0.16, 0.24, 0.62)
TURQUOISE = (0.10, 0.60, 0.66)
PURPLE = (0.36, 0.08, 0.22)
MADDER = (0.66, 0.20, 0.14)
WOAD = (0.20, 0.30, 0.55)
GREEN = (0.26, 0.56, 0.26)
ROSE = (0.94, 0.46, 0.50)
OCHRE = (0.88, 0.60, 0.26)
SKY = (0.42, 0.66, 0.92)
MANTLES = [INDIGO, CRIMSON, TURQUOISE, SAFFRON, GREEN, OCHRE, SKY, (0.96, 0.94, 0.88), ROSE, MADDER, WOAD] * 2 + [PURPLE]
TUNICS = [LINEN, (0.94, 0.90, 0.80), SAFFRON, (0.86, 0.90, 0.98), ROSE, (0.98, 0.86, 0.62)]
PAENULA = [(0.46, 0.32, 0.20), (0.56, 0.44, 0.30), (0.36, 0.30, 0.26), (0.62, 0.30, 0.20)]
PILOS = (0.70, 0.56, 0.34)


def rhodian(seed, arms="hip", stride=0.0, carry=None):
    rng = random.Random(seed)
    return Look(rng.choice(TUNICS), hem=0.1, skin=rng.randrange(3), hair=rng.randrange(4), palla=rng.choice(MANTLES),
                arms=arms, stride=stride, carry=carry, sleeves="short", seed=seed)


def woman(seed, arms="hip", stride=0.0, carry=None):
    rng = random.Random(seed)
    return Look(rng.choice([SAFFRON, ROSE, SKY, LINEN, (0.70, 0.86, 0.66)]), hem=0.03, skin=rng.randrange(2),
                hair=rng.randrange(3), palla=rng.choice(MANTLES), veil=rng.random() < 0.5, female=True,
                sleeves="long", arms=arms, stride=stride, carry=carry, scale=0.94, seed=seed)


def roman_traveller(seed, arms="down", stride=0.0, carry=None):
    rng = random.Random(seed)
    return Look((0.94, 0.90, 0.80), hem=0.42, skin=rng.randrange(2), hair=rng.randrange(3), cloak=rng.choice(PAENULA),
                belt=LEATHER, arms=arms, stride=stride, carry=carry, seed=seed)


def roman_toga(seed, arms="toga", stride=0.0):
    return Look((0.94, 0.92, 0.86), hem=0.1, skin=seed % 2, hair=1, toga=(0.97, 0.95, 0.89), arms=arms,
                stride=stride, seed=seed)


def sailor(seed, arms="hip", stride=0.0, carry=None):
    rng = random.Random(seed)
    return Look(rng.choice([(0.82, 0.60, 0.40), (0.62, 0.30, 0.22), (0.86, 0.80, 0.64), (0.40, 0.48, 0.62)]),
                hem=0.6, skin=2, hair=rng.randrange(4), belt=LEATHER, exomis=True, arms=arms, stride=stride,
                carry=carry, hat=PILOS if rng.random() < 0.5 else None, seed=seed)


def student(seed, arms="gesture", stride=0.0):
    rng = random.Random(seed)
    return Look(rng.choice(TUNICS), hem=0.15, skin=rng.randrange(3), hair=rng.randrange(3), palla=rng.choice(MANTLES),
                arms=arms, stride=stride, carry="scroll", sleeves="short", seed=seed)


def figure(look):
    return person(look)


def group(seed, members, radius=0.8):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k, look in enumerate(members):
        angle = TAU * k / len(members) + rng.uniform(-0.3, 0.3)
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        heading = math.atan2(-x, y) + math.pi
        builder.merge(figure(look), placement(x, y, 0.0, heading))
    return builder


def guide_party(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    guide = figure(Look((0.90, 0.86, 0.76), hem=0.1, skin=1, hair=2, palla=(0.50, 0.34, 0.20), arms="rhodes_point",
                        carry="staff", seed=seed))
    builder.merge(guide, placement(0.0, 1.3, 0.0, math.pi))
    visitors = [roman_traveller(seed + 1, "down"), roman_toga(seed + 2), woman(seed + 3, "hip"),
                roman_traveller(seed + 4, "hip"), rhodian(seed + 5, "down"), student(seed + 6, "down")]
    for k, look in enumerate(visitors):
        x = -2.0 + k * 0.8 + rng.uniform(-0.15, 0.15)
        y = -0.5 - 0.45 * abs(k - 2.5) + rng.uniform(-0.2, 0.2)
        builder.merge(figure(look), placement(x, y, 0.0, rng.uniform(-0.3, 0.3)))
    return builder


def thumb_embrace(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(roman_traveller(seed, "rhodes_embrace")), placement(0.0, 0.0, 0.0))
    builder.merge(figure(roman_traveller(seed + 1, "rhodes_point")), placement(1.4, -1.1, 0.0, math.radians(35)))
    builder.merge(figure(woman(seed + 2, "hip")), placement(2.4, -2.3, 0.0, math.radians(25)))
    return builder


def students(seed=0):
    return group(seed, [student(seed + k, ["gesture", "down", "hip", "rhodes_point"][k % 4]) for k in range(4)], 0.9)


def citizens(seed=0, count=3):
    rng = random.Random(seed)
    members = []
    for k in range(count):
        roll = rng.random()
        if roll < 0.2:
            members.append(roman_traveller(seed + k, rng.choice(["down", "hip", "gesture"])))
        elif roll < 0.45:
            members.append(woman(seed + k, rng.choice(["hip", "down"])))
        else:
            members.append(rhodian(seed + k, rng.choice(["hip", "gesture", "down"])))
    return group(seed, members, 0.75)


def sailors(seed=0):
    return group(seed, [sailor(seed + k, ["hip", "carry", "gesture", "down"][k % 4],
                               carry="amphora" if k % 4 == 1 else None) for k in range(3)], 0.8)


def offering(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(Look(LINEN, hem=0.06, skin=0, hair=2, palla=(0.98, 0.97, 0.94), arms="forward",
                              carry="patera", seed=seed)), placement(0.0, 0.0, 0.0))
    builder.merge(figure(woman(seed + 1, "forward", carry="basket")), placement(1.0, -0.6, 0.0, 0.3))
    builder.merge(figure(rhodian(seed + 2, "down")), placement(-1.0, -0.8, 0.0, -0.2))
    return builder


LIFE = {
    "guide_party": lambda: guide_party(301),
    "thumb_embrace": lambda: thumb_embrace(311),
    "students": lambda: students(321),
    "citizens": lambda: citizens(331, 3),
    "citizens_b": lambda: citizens(341, 2),
    "citizens_c": lambda: coarse(lambda: citizens(351, 4), 0.6),
    "sailors": lambda: sailors(361),
    "offering": lambda: offering(371),
    "fig_rhodian": lambda: figure(rhodian(381, "hip")),
    "fig_woman": lambda: figure(woman(382, "head", carry="jar")),
    "fig_roman": lambda: figure(roman_traveller(383, "gesture")),
    "fig_sailor": lambda: figure(sailor(384, "carry", carry="amphora")),
    "fig_porter": lambda: figure(sailor(385, "shoulder", carry="pole")),
    "dock_gang": alife.LIFE["dock_gang"],
    "amphora_stack": alife.LIFE["amphora_stack"],
    "sack_pile": alife.LIFE["sack_pile"],
    "scale_table": alife.LIFE["scale_table"],
    "donkey_driver": alife.LIFE["donkey_driver"],
    "spectators": lambda: olife.simple_block(391, 3, 6, 0.713, 0.44),
}

WALKERS = {
    "walker_rhodian": lambda: figure(rhodian(401, "swing", 0.17)),
    "walker_woman": lambda: figure(woman(402, "swing", 0.14)),
    "walker_roman": lambda: figure(roman_traveller(403, "swing", 0.18, carry="bundle")),
    "walker_sailor": lambda: figure(sailor(404, "swing", 0.2)),
    "walker_student": lambda: figure(Look(SAFFRON, hem=0.15, skin=1, hair=0, palla=INDIGO, arms="swing", stride=0.17,
                                          seed=405)),
    "walker_porter": lambda: figure(sailor(406, "carry", 0.2, carry="amphora")),
}

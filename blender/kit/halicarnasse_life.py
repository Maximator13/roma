import math
import random

from . import alexandrie_ships as ships
from .alexandrie_life import (CRIMSON, INDIGO, LINEN, OLIVE, SAFFRON, TURQUOISE, amphora_heap, conversation, dock_gang,
                              docker, figure, fisher_pair, greek, lady, porters_line, sack_carrier, sack_heap, soldier)
from .geometry import MeshBuilder, placement
from .nimes_figures import Look, coarse, pack_beast

TAU = 2 * math.pi
ROSE = (0.86, 0.46, 0.50)
SKY = (0.56, 0.70, 0.88)
PURPLE = (0.48, 0.16, 0.36)
WHITE = (0.96, 0.94, 0.88)
DETAIL = 0.85


def toga(seed, arms="toga_gesture", stride=0.0, carry=None):
    return Look("white", hem=0.12, skin=1, hair=seed % 3, toga="white", arms=arms, stride=stride, carry=carry, seed=seed)


def magistrate(seed):
    return Look("white", hem=0.12, skin=0, hair=2, toga="white", praetexta="purple", arms="toga_gesture", carry="scroll",
                seed=seed)


def guide_group(seed=0, count=5):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(figure(greek(seed, WHITE, OLIVE, "alex_point", skin=1, hair=2)), placement(0.0, 1.2, 0.0, math.pi))
    mantles = [INDIGO, TURQUOISE, CRIMSON, SAFFRON, ROSE, SKY, PURPLE]
    for k in range(count):
        angle = math.pi * (k + 0.5) / count + math.pi
        x, y = 1.3 * math.cos(angle) * 1.3, 1.2 + 1.3 * math.sin(angle) - 0.4
        heading = math.atan2(-(0.0 - x), (1.2 - y)) + rng.uniform(-0.3, 0.3)
        if k == 1:
            look = toga(seed + 10 + k, "toga")
        elif rng.random() < 0.4:
            look = lady(seed + k, rng.choice([SAFFRON, LINEN, ROSE, SKY]), rng.choice(mantles), rng.choice(["hip", "down"]))
        else:
            look = greek(seed + k, rng.choice([LINEN, (0.92, 0.88, 0.78), SKY]), rng.choice(mantles),
                         rng.choice(["hip", "down", "gesture"]), skin=rng.randrange(3), hair=rng.randrange(4))
        builder.merge(figure(look), placement(x, y - 1.2, 0.0, heading))
    return builder


def escort(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(magistrate(seed)), placement(0.0, 0.0, 0.0))
    builder.merge(figure(Look("white", hem=0.12, skin=1, hair=0, toga="white", arms="toga", seed=seed + 1)),
                  placement(0.9, -0.5, 0.0, 0.1))
    for k, (x, y) in enumerate(((-1.0, -1.6), (1.0, -1.6), (-1.0, -3.0), (1.0, -3.0))):
        builder.merge(soldier(seed + 2 + k), placement(x, y, 0.0))
    return builder


def market_pair(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(lady(seed, ROSE, INDIGO, "gesture")), placement(0.0, 0.0, 0.0))
    builder.merge(figure(Look((0.86, 0.66, 0.40), hem=0.5, skin=2, hair=1, apron=LINEN, arms="gesture", seed=seed + 1)),
                  placement(0.0, 1.3, 0.0, math.pi))
    return builder


FIGURES = {
    "fig_greek": lambda: coarse(lambda: figure(greek(61, LINEN, INDIGO, "hip")), DETAIL),
    "fig_greek_b": lambda: coarse(lambda: figure(greek(62, (0.92, 0.88, 0.78), CRIMSON, "gesture", skin=0, hair=2)), DETAIL),
    "fig_greek_c": lambda: coarse(lambda: figure(greek(63, SKY, SAFFRON, "down", skin=2, hair=1)), DETAIL),
    "fig_lady": lambda: coarse(lambda: figure(lady(64)), DETAIL),
    "fig_lady_b": lambda: coarse(lambda: figure(lady(65, LINEN, ROSE, "head", carry="jar")), DETAIL),
    "fig_lady_c": lambda: coarse(lambda: figure(lady(66, SKY, PURPLE, "down")), DETAIL),
    "fig_roman": lambda: coarse(lambda: figure(toga(67)), DETAIL),
    "fig_docker": lambda: coarse(lambda: figure(docker(68)), DETAIL),
    "fig_sack": lambda: coarse(lambda: sack_carrier(69), DETAIL),
    "fig_sailor": lambda: coarse(lambda: figure(Look(TURQUOISE, hem=0.6, skin=2, hair=3, belt="brown", exomis=True, arms="hip",
                                                     hat=(0.74, 0.62, 0.38), seed=70)), DETAIL),
    "fig_child": lambda: coarse(lambda: figure(Look(SAFFRON, hem=0.5, skin=1, hair=1, scale=0.62, child=True, seed=71)), DETAIL),
}

GROUPS = {
    "group_guide": lambda: coarse(lambda: guide_group(80), DETAIL),
    "group_guide_b": lambda: coarse(lambda: guide_group(90, 4), DETAIL),
    "group_escort": lambda: coarse(lambda: escort(100), DETAIL),
    "group_talk": lambda: coarse(lambda: conversation(31, 3), DETAIL),
    "group_talk_b": lambda: coarse(lambda: conversation(47, 2), DETAIL),
    "group_market": lambda: coarse(lambda: market_pair(110), DETAIL),
    "group_dock": lambda: coarse(dock_gang, DETAIL),
    "group_porters": lambda: coarse(porters_line, DETAIL),
    "group_fishers": lambda: coarse(fisher_pair, DETAIL),
    "prop_mule": lambda: coarse(lambda: pack_beast("mule"), DETAIL),
    "prop_donkey": lambda: coarse(lambda: pack_beast("donkey"), DETAIL),
    "prop_amphorae": lambda: amphora_heap(5, 3, 6),
    "prop_sacks": lambda: sack_heap(3),
}

WALKERS = {
    "walker_greek": lambda: figure(greek(171, LINEN, INDIGO, "swing", stride=0.17)),
    "walker_lady": lambda: figure(lady(172, ROSE, (0.96, 0.92, 0.84), "swing", stride=0.14)),
    "walker_docker": lambda: figure(docker(173, stride=0.2)),
    "walker_roman": lambda: figure(toga(174, "toga", stride=0.15)),
    "walker_soldier": lambda: figure(Look(CRIMSON, hem=0.55, skin=1, hair=0, belt="brown", cloak=(0.62, 0.12, 0.10),
                                          arms="swing", stride=0.2, seed=175)),
    "walker_merchant": lambda: figure(Look((0.92, 0.84, 0.62), hem=0.3, skin=1, hair=2, palla=(0.36, 0.48, 0.30),
                                           arms="swing", stride=0.16, carry="bundle", seed=176)),
}

SHIPS = {
    "ship_merchant": lambda: ships.merchant(1, "brailed"),
    "ship_merchant_set": lambda: ships.merchant(2, "set"),
    "ship_merchant_b": lambda: ships.merchant(3, "brailed", 18.0, 5.6),
    "ship_freighter": lambda: ships.grain_carrier(4, "brailed", 32.0, 9.0),
    "ship_freighter_set": lambda: ships.grain_carrier(5, "set", 30.0, 8.6),
    "ship_galley": lambda: ships.galley(6),
    "ship_fishing": lambda: ships.fishing_boat(7),
    "ship_fishing_sail": lambda: ships.fishing_boat(8, sail=True),
}

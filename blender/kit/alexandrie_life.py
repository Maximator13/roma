import math
import random

from mathutils import Matrix, Vector

from . import colisee_life
from .alexandrie_pharos import painted
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, SKIN, WOOD
from .nimes_figures import POSES, Look, coarse, drape, ellipsoid, ox_cart, pack_beast, person, tube

POSES.update({
    "alex_sack": [((0.27, 0.06, 1.42), (0.15, 0.1, 1.62)), ((-0.27, 0.06, 1.42), (-0.15, 0.1, 1.62))],
    "alex_write": [((0.22, 0.18, 1.1), (0.08, 0.32, 1.12)), ((-0.22, 0.16, 1.12), (-0.1, 0.3, 1.16))],
    "alex_point": [((0.28, 0.2, 1.34), (0.33, 0.48, 1.5)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "alex_haul": [((0.24, 0.26, 1.08), (0.12, 0.48, 1.0)), ((-0.24, 0.26, 1.08), (-0.12, 0.48, 1.0))],
})
LINEN = (0.97, 0.95, 0.90)
SAFFRON = (0.92, 0.66, 0.20)
TURQUOISE = (0.22, 0.56, 0.62)
CRIMSON = (0.72, 0.14, 0.12)
INDIGO = (0.22, 0.26, 0.52)
OLIVE = (0.52, 0.52, 0.26)
SACK = (0.88, 0.80, 0.62)
TAU = 2 * math.pi


AMPHORA_TONES = [(0.74, 0.44, 0.28), (0.82, 0.56, 0.38), (0.66, 0.38, 0.24), (0.86, 0.66, 0.48)]


def amphora(builder, matrix, colour):
    profile = [(0.0, 0.0), (0.035, 0.03), (0.06, 0.13), (0.15, 0.3), (0.185, 0.47), (0.155, 0.63), (0.075, 0.73),
               (0.055, 0.9), (0.07, 0.94), (0.0, 0.95)]
    first = len(builder.polygons)
    builder.lathe(profile, 8, MATTE, smooth=True, matrix=matrix)
    builder.tint(first, colour)
    for side in (-1, 1):
        tube(builder, [matrix @ Vector((side * 0.05, 0.0, 0.86)), matrix @ Vector((side * 0.13, 0.0, 0.83)),
                       matrix @ Vector((side * 0.12, 0.0, 0.68))], [0.018, 0.018, 0.018], colour, 4)


def figure(look):
    shoulder = look.carry == "amphora"
    if shoulder:
        look.carry = None
    builder = person(look)
    scale = Matrix.Scale(look.scale, 4)
    if look.hem > 0.25 and look.mono is None:
        skin = SKIN[look.skin]
        for side in (-1, 1):
            x = side * 0.088
            y = side * look.stride
            ellipsoid(builder, (x, y * 0.72 - 0.014, 0.3), (0.05, 0.056, 0.12), skin, 8, 4, matrix=scale)
            ellipsoid(builder, (x, y + 0.13, 0.034), (0.042, 0.05, 0.03), LEATHER, 6, 3, matrix=scale)
    if shoulder:
        tone = AMPHORA_TONES[look.seed % len(AMPHORA_TONES)]
        amphora(builder, scale @ Matrix.Translation((0.3, -0.44, 1.39)) @ Matrix.Rotation(math.radians(-70.0), 4, "X"),
                tone)
    return builder


def amphora_heap(seed=0, rows=3, count=6):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for row in range(rows):
        for k in range(count - row):
            x = -0.2 * (count - 1) + k * 0.4 + row * 0.2
            y = (-1) ** k * 0.06
            z = 0.19 + row * 0.33
            frame = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(-90 if k % 2 else 90), 4, "X")
                     @ Matrix.Translation((0.0, 0.0, -0.47)))
            amphora(builder, frame, AMPHORA_TONES[rng.randrange(len(AMPHORA_TONES))])
    return builder


def amphora_rank(seed=0, count=16):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        x = (k % 4) * 0.42 - 0.63 + rng.uniform(-0.03, 0.03)
        y = (k // 4) * 0.42 + rng.uniform(-0.03, 0.03)
        amphora(builder, placement(x, y, 0.0, rng.uniform(0, 6.28)), AMPHORA_TONES[rng.randrange(len(AMPHORA_TONES))])
    return builder


def sack_heap(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for layer, count in ((0, 6), (1, 4), (2, 2)):
        for k in range(count):
            x = (k % 3 - 1) * 0.72 + layer * 0.18
            y = (k // 3) * 0.98 + layer * 0.42
            tone = rng.uniform(0.92, 1.04)
            ellipsoid(builder, (x, y, 0.21 + layer * 0.35), (0.37, 0.52, 0.21),
                      (SACK[0] * tone, SACK[1] * tone, SACK[2] * tone), 10, 5, MATTE)
    return builder


def greek(seed, tunic=LINEN, mantle=INDIGO, arms="hip", stride=0.0, carry=None, skin=1, hair=0):
    return Look(tunic, hem=0.12, skin=skin, hair=hair, palla=mantle, arms=arms, stride=stride, carry=carry,
                sleeves="short", seed=seed)


def lady(seed, tunic=SAFFRON, mantle=TURQUOISE, arms="hip", stride=0.0, carry=None, skin=0, hair=1):
    return Look(tunic, hem=0.03, skin=skin, hair=hair, palla=mantle, veil=True, female=True, sleeves="long",
                arms=arms, stride=stride, carry=carry, scale=0.95, seed=seed)


def docker(seed, tunic=LINEN, arms="carry", carry="amphora", stride=0.0, skin=2, hair=3):
    return Look(tunic, hem=0.6, skin=skin, hair=hair, belt=LEATHER, exomis=True, arms=arms, carry=carry,
                stride=stride, seed=seed)


def sack_carrier(seed, stride=0.0):
    builder = figure(Look(LINEN, hem=0.62, skin=2, hair=1, belt=LEATHER, exomis=True, arms="alex_sack", stride=stride,
                          seed=seed))
    ellipsoid(builder, (0.0, -0.02, 1.78), (0.34, 0.24, 0.2), SACK, 8, 4, MATTE)
    return builder


def scribe(seed):
    builder = figure(Look(LINEN, hem=0.12, skin=1, hair=2, palla=(0.86, 0.80, 0.66), arms="alex_write", seed=seed))
    painted(builder, (0.62, 0.48, 0.30), lambda: builder.box((-0.16, 0.3, 1.1), (0.16, 0.36, 1.32), MATTE))
    return builder


def soldier(seed):
    builder = figure(Look(CRIMSON, hem=0.55, skin=1, hair=0, belt=LEATHER, cloak=(0.62, 0.12, 0.10), arms="staff",
                          seed=seed))
    colisee_life.helmet(builder, "smooth", visor=False, brim=False)
    tube(builder, [(0.25, 0.22, 0.0), (0.25, 0.2, 2.1)], [0.02, 0.016], WOOD, 4)
    tube(builder, [(0.25, 0.2, 2.1), (0.25, 0.2, 2.32)], [0.03, 0.002], (0.7, 0.7, 0.68), 4)
    colisee_life.shield(builder, (-0.3, 0.1, 0.95), 0.62, 1.05, CRIMSON, 0.1)
    return builder


def scale_table(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    painted(builder, (0.56, 0.42, 0.28), lambda: builder.box((-0.9, -0.4, 0.72), (0.9, 0.4, 0.8), MATTE))
    for x in (-0.8, 0.8):
        for y in (-0.3, 0.3):
            tube(builder, [(x, y, 0.0), (x, y, 0.72)], [0.04, 0.04], WOOD, 4)
    tube(builder, [(1.6, 0.0, 0.0), (1.6, 0.0, 2.1)], [0.06, 0.05], WOOD, 4)
    tube(builder, [(1.6, -0.9, 2.1), (1.6, 0.9, 2.1)], [0.04, 0.04], WOOD, 4)
    for y in (-0.85, 0.85):
        tube(builder, [(1.6, y, 2.1), (1.6, y, 1.2)], [0.012, 0.012], (0.3, 0.26, 0.2), 3)
        drape(builder, (0.78, 0.6, 0.32), [(0.0, 1.1), (0.28, 1.14), (0.3, 1.2)], 8, folds=(0, 0.0, 0.0), squash=1.0,
              center=(1.6, y), material="bronze_gilt")
    ellipsoid(builder, (1.6, 0.85, 1.32), (0.26, 0.3, 0.2), SACK, 6, 3)
    for k in range(4):
        tube(builder, [(-0.6 + k * 0.35, rng.uniform(-0.2, 0.2), 0.8), (-0.6 + k * 0.35 + 0.05, 0.0, 0.84)],
             [0.03, 0.03], (0.92, 0.88, 0.74), 4)
    builder.merge(scribe(seed + 300), placement(-0.2, -0.85, 0.0, 0.0))
    builder.merge(figure(greek(seed + 301, (0.94, 0.90, 0.80), CRIMSON, "alex_point")), placement(0.4, 1.1, 0.0,
                                                                                                    math.pi))
    builder.merge(sack_carrier(seed + 302), placement(2.4, 0.8, 0.0, -math.pi / 2))
    return builder


def dock_gang(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    builder.merge(amphora_heap(seed, 3, 6), placement(0.0, 0.0, 0.0))
    builder.merge(sack_heap(seed + 1), placement(3.2, 0.4, 0.0, 0.3))
    for k, (x, y, heading) in enumerate(((-1.6, -1.6, 0.4), (1.4, -1.9, -0.5), (4.6, -1.2, 2.6), (0.4, 2.6, 3.0))):
        if k == 2:
            builder.merge(sack_carrier(seed + k, 0.15), placement(x, y, 0.0, heading))
        else:
            tunic = rng.choice([LINEN, (0.86, 0.80, 0.66), SAFFRON, (0.80, 0.70, 0.52)])
            builder.merge(figure(docker(seed + k * 7, tunic, stride=0.12 if k % 2 else 0.0)),
                          placement(x, y, 0.0, heading))
    builder.merge(figure(greek(seed + 40, (0.92, 0.88, 0.78), (0.40, 0.30, 0.52), "alex_point")),
                  placement(-3.2, 0.4, 0.0, -1.2))
    return builder


def conversation(seed=0, count=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    mantles = [INDIGO, TURQUOISE, CRIMSON, (0.86, 0.80, 0.66), OLIVE, (0.62, 0.30, 0.50), (0.96, 0.94, 0.88)]
    for k in range(count):
        angle = TAU * k / count + rng.uniform(-0.3, 0.3)
        x, y = 0.75 * math.cos(angle), 0.75 * math.sin(angle)
        heading = math.atan2(-x, y) + math.pi
        if rng.random() < 0.35:
            look = lady(seed + k, rng.choice([SAFFRON, LINEN, (0.86, 0.50, 0.46), (0.62, 0.72, 0.84)]),
                        rng.choice(mantles), rng.choice(["hip", "down", "gesture"]))
        else:
            look = greek(seed + k, rng.choice([LINEN, (0.92, 0.88, 0.78), (0.84, 0.86, 0.90)]), rng.choice(mantles),
                         rng.choice(["hip", "gesture", "down"]), skin=rng.randrange(3), hair=rng.randrange(4))
        builder.merge(figure(look), placement(x, y, 0.0, heading))
    return builder


def porters_line(seed=0, count=4):
    builder = MeshBuilder()
    for k in range(count):
        if k % 2:
            builder.merge(sack_carrier(seed + k, 0.18), placement(0.0, k * 1.6, 0.0, 0.0))
        else:
            builder.merge(figure(docker(seed + k, stride=0.18)), placement(0.15, k * 1.6, 0.0, 0.0))
    return builder


def camel(packed=True, colour=(0.74, 0.58, 0.40)):
    builder = MeshBuilder()
    dark = tuple(c * 0.7 for c in colour)
    body_z = 1.75
    ellipsoid(builder, (0.0, 0.0, body_z), (0.42, 0.95, 0.42), colour, 10, 6)
    ellipsoid(builder, (0.0, -0.05, body_z + 0.42), (0.3, 0.42, 0.3), colour, 8, 4)
    neck = [Vector((0.0, 0.8, body_z + 0.05)), Vector((0.0, 1.25, body_z - 0.1)), Vector((0.0, 1.5, body_z + 0.4)),
            Vector((0.0, 1.55, body_z + 0.75))]
    tube(builder, neck, [0.2, 0.15, 0.12, 0.11], colour, 6)
    tube(builder, [neck[-1] + Vector((0.0, -0.05, 0.0)), neck[-1] + Vector((0.0, 0.35, -0.05))], [0.12, 0.08],
         colour, 6, start_cap=True)
    for side in (-1, 1):
        for end in (-1, 1):
            top = Vector((side * 0.22, end * 0.62, body_z - 0.25))
            knee = Vector((side * 0.22, end * 0.66, 0.85))
            foot = Vector((side * 0.22, end * 0.64, 0.05))
            tube(builder, [top, knee, foot], [0.13, 0.07, 0.06], colour, 5, cap=False)
            ellipsoid(builder, foot + Vector((0.0, 0.04, 0.0)), (0.1, 0.13, 0.05), dark, 5, 2)
        tube(builder, [neck[-1] + Vector((side * 0.06, -0.04, 0.06)), neck[-1] + Vector((side * 0.09, -0.08, 0.14))],
             [0.025, 0.005], colour, 4)
    tube(builder, [(0.0, -0.92, body_z + 0.1), (0.0, -1.02, body_z - 0.5)], [0.04, 0.03], dark, 4)
    if packed:
        for side in (-1, 1):
            ellipsoid(builder, (side * 0.5, 0.0, body_z + 0.1), (0.24, 0.42, 0.32), SACK, 7, 4)
        drape(builder, (0.70, 0.22, 0.16), [(0.46, body_z + 0.28), (0.36, body_z + 0.62), (0.0, body_z + 0.7)], 8,
              folds=(0, 0.0, 0.0), squash=1.6)
    return builder


def camel_train(seed=0):
    builder = MeshBuilder()
    for k in range(3):
        builder.merge(camel(True, (0.74 - 0.04 * k, 0.58 - 0.03 * k, 0.40)), placement(0.0, -k * 3.4, 0.0))
    builder.merge(figure(Look((0.92, 0.88, 0.80), hem=0.4, skin=2, hair=0, belt="brown", arms="forward", stride=0.18,
                              hood=(0.86, 0.82, 0.72), seed=seed)), placement(0.5, 2.2, 0.0))
    return builder


def donkey_driver(seed=0):
    builder = MeshBuilder()
    builder.merge(pack_beast("donkey"), placement(0.0, 0.0, 0.0))
    builder.merge(figure(Look((0.80, 0.70, 0.52), hem=0.56, skin=2, hair=1, belt="brown", arms="staff", carry="staff",
                              stride=0.16, hat=(0.78, 0.66, 0.40), seed=seed)), placement(0.7, 0.9, 0.0))
    return builder


def wood_carriers(seed=0):
    builder = MeshBuilder()
    for k in range(3):
        carrier = figure(docker(seed + k, (0.82, 0.74, 0.58), arms="shoulder", carry=None, stride=0.15))
        for j in range(5):
            tube(carrier, [(0.25 + 0.05 * (j % 2), -0.55, 1.62 + 0.06 * j), (0.22, 0.75, 1.68 + 0.05 * j)],
                 [0.05, 0.045], (0.46, 0.34, 0.22), 4)
        builder.merge(carrier, placement(k * 0.9, -k * 1.8, 0.0))
    builder.merge(amphora_rank(seed, 8), placement(3.0, 1.0, 0.0))
    return builder


def guards(seed=0):
    builder = MeshBuilder()
    builder.merge(soldier(seed), placement(-0.8, 0.0, 0.0, 0.2))
    builder.merge(soldier(seed + 1), placement(0.8, 0.2, 0.0, -0.2))
    return builder


def fisher_pair(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(Look((0.86, 0.80, 0.66), hem=0.62, skin=2, hair=1, belt="brown", exomis=True,
                              arms="alex_haul", hat=(0.74, 0.62, 0.38), seed=seed)), placement(0.0, 0.0, 0.0))
    builder.merge(figure(Look(TURQUOISE, hem=0.6, skin=2, hair=3, belt="brown", arms="alex_haul", seed=seed + 1)),
                  placement(1.0, -0.5, 0.0, 0.3))
    for k in range(6):
        tube(builder, [(-0.6 + k * 0.4, 0.8, 0.02), (-0.4 + k * 0.4, 1.6, 0.02)], [0.02, 0.02], (0.6, 0.55, 0.42), 3)
    ellipsoid(builder, (1.8, 0.6, 0.25), (0.35, 0.35, 0.25), (0.66, 0.52, 0.32), 7, 3)
    return builder


LIFE = {
    "dock_gang": lambda: coarse(dock_gang, 0.9),
    "scale_table": lambda: coarse(scale_table, 0.9),
    "conversation": lambda: coarse(conversation, 1.0),
    "conversation_b": lambda: coarse(lambda: conversation(31, 4), 1.0),
    "conversation_c": lambda: coarse(lambda: conversation(47, 2), 1.0),
    "porters_line": lambda: coarse(porters_line, 0.9),
    "camel_train": lambda: coarse(camel_train, 0.9),
    "donkey_driver": lambda: coarse(donkey_driver, 0.9),
    "wood_carriers": lambda: coarse(wood_carriers, 0.9),
    "guards": lambda: coarse(guards, 1.0),
    "fisher_pair": lambda: coarse(fisher_pair, 0.9),
    "ox_cart": lambda: coarse(ox_cart, 0.9),
    "amphora_stack": lambda: amphora_rank(5, 16),
    "sack_pile": lambda: sack_heap(3),
    "fig_greek": lambda: figure(greek(61, LINEN, INDIGO, "hip")),
    "fig_greek_b": lambda: figure(greek(62, (0.92, 0.88, 0.78), CRIMSON, "gesture", skin=0, hair=2)),
    "fig_lady": lambda: figure(lady(63)),
    "fig_lady_b": lambda: figure(lady(64, LINEN, (0.70, 0.30, 0.50), "head", carry="jar")),
    "fig_docker": lambda: figure(docker(65)),
    "fig_sack": lambda: sack_carrier(66),
    "fig_egyptian": lambda: figure(Look(LINEN, hem=0.5, skin=2, hair=3, belt=(0.86, 0.78, 0.50), arms="down",
                                        seed=67)),
    "fig_child": lambda: figure(Look(SAFFRON, hem=0.5, skin=1, hair=1, scale=0.62, child=True, seed=68)),
}

WALKERS = {
    "walker_greek": lambda: figure(greek(71, LINEN, INDIGO, "swing", stride=0.17)),
    "walker_lady": lambda: figure(lady(72, (0.86, 0.50, 0.46), (0.96, 0.92, 0.84), "swing", stride=0.14)),
    "walker_docker": lambda: figure(docker(73, stride=0.2)),
    "walker_egyptian": lambda: figure(Look(LINEN, hem=0.5, skin=2, hair=3, belt=(0.86, 0.78, 0.5), arms="swing",
                                           stride=0.2, seed=74)),
    "walker_soldier": lambda: figure(Look(CRIMSON, hem=0.55, skin=1, hair=0, belt=LEATHER, cloak=(0.62, 0.12, 0.10),
                                          arms="swing", stride=0.2, seed=75)),
    "walker_merchant": lambda: figure(Look((0.92, 0.84, 0.62), hem=0.3, skin=1, hair=2, palla=(0.36, 0.48, 0.30),
                                           arms="swing", stride=0.16, carry="bundle", seed=76)),
}

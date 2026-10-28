import math
import random

from mathutils import Matrix, Vector

from .buildings import trunk
from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, SKIN, WOOD
from .nimes_detail import rough_lobe
from .nimes_figures import ANIMALS, Look, beast, coarse, ellipsoid, person, tube
from .olympie_zeus import nike

ANIMALS["horse"] = dict(length=1.55, height=0.92, girth=0.6, colour=(0.45, 0.30, 0.18), neck=0.78, ears=0.14,
                        horns=0.0, lift=0.95)
TAU = 2 * math.pi
LINEN = (0.97, 0.95, 0.90)
SAFFRON = (0.95, 0.68, 0.18)
CRIMSON = (0.78, 0.13, 0.10)
INDIGO = (0.18, 0.24, 0.58)
TURQUOISE = (0.16, 0.58, 0.64)
PURPLE = (0.46, 0.10, 0.36)
GREEN = (0.32, 0.54, 0.22)
ROSE = (0.92, 0.48, 0.50)
OCHRE = (0.86, 0.62, 0.30)
SKY = (0.48, 0.66, 0.88)
MANTLES = [INDIGO, CRIMSON, TURQUOISE, SAFFRON, (0.86, 0.80, 0.66), PURPLE, GREEN, OCHRE, (0.96, 0.94, 0.88), SKY]
TUNICS = [LINEN, (0.92, 0.88, 0.78), (0.86, 0.84, 0.80), SAFFRON, (0.84, 0.86, 0.92), ROSE]
CROWD_TUNICS = [(0.86, 0.80, 0.66), (0.78, 0.52, 0.30), (0.62, 0.30, 0.22), (0.44, 0.50, 0.62), (0.92, 0.88, 0.78),
                (0.70, 0.62, 0.42), (0.52, 0.56, 0.36), (0.90, 0.70, 0.40)]
TENT_CLOTH = [((0.96, 0.94, 0.88), (0.80, 0.16, 0.12)), ((0.95, 0.70, 0.22), (0.62, 0.24, 0.10)),
              ((0.86, 0.22, 0.16), (0.96, 0.92, 0.84)), ((0.26, 0.44, 0.74), (0.96, 0.94, 0.88)),
              ((0.90, 0.86, 0.72), (0.30, 0.52, 0.26)), ((0.62, 0.42, 0.26), (0.92, 0.80, 0.52))]


def horse(colour=(0.45, 0.30, 0.18), material=MATTE):
    spec = dict(ANIMALS["horse"])
    spec["colour"] = colour
    ANIMALS["horse_tmp"] = spec
    try:
        built = beast("horse_tmp")
    finally:
        ANIMALS.pop("horse_tmp", None)
    if material != MATTE:
        built.materials = [material if name == MATTE else name for name in built.materials]
    return built


def greek(seed, tunic=LINEN, mantle=INDIGO, arms="hip", stride=0.0, skin=1, hair=0, carry=None):
    return Look(tunic, hem=0.1, skin=skin, hair=hair, palla=mantle, arms=arms, stride=stride, sleeves="short",
                carry=carry, seed=seed)


def roman(seed, arms="toga", stride=0.0, praetexta=None, skin=0, hair=1):
    return Look((0.94, 0.92, 0.86), hem=0.1, skin=skin, hair=hair, toga=(0.97, 0.95, 0.89), praetexta=praetexta,
                arms=arms, stride=stride, seed=seed)


def maiden(seed, tunic=SAFFRON, mantle=TURQUOISE, arms="hip", stride=0.0, carry=None):
    return Look(tunic, hem=0.03, skin=0, hair=1, palla=mantle, female=True, sleeves="short", arms=arms,
                stride=stride, carry=carry, scale=0.93, seed=seed)


def athlete(seed, arms="olym_run", stride=0.0, skin=1, hair=0):
    tone = SKIN[skin]
    return Look(tone, hem=0.97, skin=skin, hair=hair, arms=arms, stride=stride, sleeves="short", seed=seed,
                hem_radius=0.17)


def worker(seed, tunic=(0.80, 0.72, 0.56), arms="carry", carry=None, stride=0.0):
    return Look(tunic, hem=0.6, skin=2, hair=seed % 4, belt=LEATHER, exomis=True, arms=arms, carry=carry,
                stride=stride, seed=seed)


def judge(seed, arms="staff"):
    return Look((0.90, 0.86, 0.78), hem=0.08, skin=1, hair=2, palla=(0.50, 0.08, 0.30), arms=arms, seed=seed)


def priest(seed, arms="forward"):
    return Look(LINEN, hem=0.06, skin=0, hair=2, palla=(0.98, 0.97, 0.94), arms=arms, seed=seed,
                hat=None)


def wreath(builder, height=1.66, colour=(0.38, 0.52, 0.22)):
    for k in range(10):
        angle = TAU * k / 10
        ellipsoid(builder, (math.cos(angle) * 0.105, 0.01 + math.sin(angle) * 0.12, height), (0.035, 0.035, 0.02),
                  colour, 5, 2)


def figure(look, crowned=False):
    built = person(look)
    if crowned:
        wreath(built)
    return built


def staff(builder, x=0.27, y=0.22, height=1.9, colour=WOOD):
    tube(builder, [(x, y, 0.0), (x, y, height)], [0.018, 0.016], colour, 4)


def conversation(seed=0, count=3, roman_share=0.3, girl_share=0.2):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        angle = TAU * k / count + rng.uniform(-0.3, 0.3)
        x, y = 0.78 * math.cos(angle), 0.78 * math.sin(angle)
        heading = math.atan2(-x, y) + math.pi
        roll = rng.random()
        arms = rng.choice(["hip", "gesture", "down", "forward"])
        if roll < roman_share:
            look = roman(seed + k, "toga_gesture" if arms == "gesture" else "toga",
                         praetexta=CRIMSON if rng.random() < 0.2 else None, skin=rng.randrange(2))
        elif roll < roman_share + girl_share:
            look = maiden(seed + k, rng.choice(TUNICS), rng.choice(MANTLES), rng.choice(["hip", "down"]))
        else:
            look = greek(seed + k, rng.choice(TUNICS), rng.choice(MANTLES), arms, skin=rng.randrange(3),
                         hair=rng.randrange(4))
        builder.merge(figure(look), placement(x, y, 0.0, heading))
    return builder


def guide_group(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    guide = figure(greek(seed, (0.90, 0.86, 0.76), (0.50, 0.34, 0.20), "olym_bow", skin=1, hair=2))
    staff(guide, 0.3, 0.1, 1.85)
    builder.merge(guide, placement(0.0, 1.2, 0.0, math.pi))
    for k in range(5):
        x = -1.6 + k * 0.8 + rng.uniform(-0.15, 0.15)
        y = -0.4 - 0.5 * abs(k - 2) + rng.uniform(-0.2, 0.2)
        if k == 2:
            look = roman(seed + k, "toga")
        elif k == 4:
            look = maiden(seed + k, rng.choice(TUNICS), rng.choice(MANTLES))
        else:
            look = greek(seed + k, rng.choice(TUNICS), rng.choice(MANTLES), rng.choice(["hip", "down", "gesture"]),
                         skin=rng.randrange(3), hair=rng.randrange(4))
        builder.merge(figure(look), placement(x, y, 0.0, rng.uniform(-0.25, 0.25)))
    return builder


def governor_party(seed=0):
    builder = MeshBuilder()
    builder.merge(figure(roman(seed, "toga_gesture", praetexta=(0.62, 0.06, 0.18))), placement(0.0, 0.0, 0.0))
    for k, x in enumerate((-1.3, 1.3)):
        lictor = figure(Look(CRIMSON, hem=0.55, skin=1, hair=0, belt=LEATHER, cloak=(0.62, 0.10, 0.10),
                             arms="shoulder", seed=seed + 5 + k))
        tube(lictor, [(0.27, 0.1, 1.2), (0.25, 0.0, 1.95)], [0.05, 0.05], (0.55, 0.40, 0.26), 6)
        tube(lictor, [(0.29, 0.06, 1.9), (0.36, 0.06, 1.98)], [0.01, 0.05], (0.8, 0.8, 0.78), 3)
        builder.merge(lictor, placement(x, -1.2, 0.0))
    for k, x in enumerate((-0.8, 0.9)):
        builder.merge(figure(roman(seed + 9 + k, "toga")), placement(x, 1.3, 0.0, 0.2 * (1 if k else -1)))
    return builder


def runners(seed=0, count=4):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        built = figure(athlete(seed + k, "olym_run", stride=0.26, skin=rng.randrange(3), hair=rng.randrange(4)))
        builder.merge(built, placement(rng.uniform(-0.3, 0.3), k * 1.3 - count * 0.65, 0.0, -math.pi / 2)
                      @ Matrix.Rotation(math.radians(-8), 4, "X"))
    return builder


def race(seed=0, count=7):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        built = figure(athlete(seed + k, "olym_run", stride=0.35, skin=rng.randrange(3),
                               hair=rng.randrange(4)))
        ahead = rng.uniform(-1.8, 1.8) + (0.9 if k == count // 2 else 0.0)
        builder.merge(built, placement(ahead, (k - (count - 1) / 2) * 1.5, 0.0, -math.pi / 2)
                      @ Matrix.Rotation(math.radians(-10), 4, "X"))
    return builder


def athletes_resting(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(3):
        built = figure(athlete(seed + k, rng.choice(["hip", "down", "gesture"]), skin=rng.randrange(3),
                               hair=rng.randrange(4)))
        angle = TAU * k / 3
        builder.merge(built, placement(0.8 * math.cos(angle), 0.8 * math.sin(angle), 0.0, angle + math.pi / 2))
    trainer = figure(Look((0.62, 0.10, 0.20), hem=0.1, skin=1, hair=2, palla=(0.62, 0.10, 0.20), arms="staff",
                          seed=seed + 9))
    staff(trainer, 0.27, 0.22, 1.7, (0.85, 0.75, 0.55))
    builder.merge(trainer, placement(1.8, 0.4, 0.0, -1.9))
    return builder


def judges_row(seed=0, count=5):
    builder = MeshBuilder()
    for k in range(count):
        built = figure(judge(seed + k), crowned=True)
        staff(built, 0.27, 0.22, 1.6, (0.9, 0.86, 0.8))
        builder.merge(built, placement((k - count / 2) * 0.9, 0.0, 0.0))
    return builder


def sacrifice(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    ox = beast("ox")
    for k in range(len(ox.polygon_colors)):
        ox.polygon_colors[k] = (0.97, 0.95, 0.90)
    builder.merge(ox, placement(0.0, 0.0, 0.0, -math.pi / 2))
    for side in (-1, 1):
        ribbon = MeshBuilder()
        tube(ribbon, [(side * 0.3, 0.9, 1.3), (side * 0.32, 0.9, 0.9)], [0.03, 0.02], CRIMSON, 4)
        builder.merge(ribbon, placement(0.0, 0.0, 0.0, -math.pi / 2))
    builder.merge(figure(priest(seed), crowned=True), placement(1.8, 0.8, 0.0, math.pi / 2))
    builder.merge(figure(worker(seed + 2, LINEN, "forward")), placement(1.4, -0.7, 0.0, math.pi / 2))
    builder.merge(figure(maiden(seed + 3, LINEN, SAFFRON, "head", carry="jar")), placement(-1.8, 0.6, 0.0, -0.4))
    for k in range(3):
        builder.merge(figure(greek(seed + 4 + k, rng.choice(TUNICS), rng.choice(MANTLES), "down")),
                      placement(-2.4 - k * 0.9, -0.8 + rng.uniform(-0.3, 0.3), 0.0, math.pi / 2 + 0.3))
    return builder


def spectator_block(seed=0, rows=3, columns=6, spacing=0.62, rise=0.0, seated=False):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for row in range(rows):
        for column in range(columns):
            if rng.random() < 0.12:
                continue
            roll = rng.random()
            arms = rng.choice(["down", "hip", "olym_cheer", "gesture", "forward"])
            if roll < 0.12:
                look = roman(seed * 31 + row * 7 + column, "toga")
            elif roll < 0.2:
                look = maiden(seed * 31 + row * 7 + column, rng.choice(TUNICS), rng.choice(MANTLES))
            else:
                look = greek(seed * 31 + row * 7 + column, rng.choice(TUNICS), rng.choice(MANTLES), arms,
                             skin=rng.randrange(3), hair=rng.randrange(4))
            if rng.random() < 0.25:
                look.hat = rng.choice([(0.82, 0.70, 0.44), (0.72, 0.60, 0.36)])
            built = coarse(lambda look=look: person(look), 0.24)
            x = (column - (columns - 1) / 2) * spacing + rng.uniform(-0.12, 0.12)
            y = -row * spacing * 1.15 + rng.uniform(-0.1, 0.1)
            z = row * rise
            builder.merge(built, placement(x, y, z, rng.uniform(-0.3, 0.3), rng.uniform(0.94, 1.04)))
    return builder


def simple_person(builder, x, y, z, heading, colour, mantle, skin, scale=1.0, cheer=False, seated=False):
    squash = 0.68 if seated else 1.0
    frame = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(heading, 4, "Z")
             @ Matrix.Diagonal((scale, scale, scale * squash, 1.0)).to_4x4())
    first = len(builder.polygons)
    builder.lathe([(0.17, 0.0), (0.2, 0.9)], 4, MATTE, smooth=True, matrix=frame, caps=False)
    builder.tint(first, colour)
    first = len(builder.polygons)
    builder.lathe([(0.21, 0.9), (0.22, 1.28), (0.1, 1.46)], 4, MATTE, smooth=True, matrix=frame, caps=False)
    builder.tint(first, mantle)
    head = (Matrix.Translation((x, y, z + 1.46 * scale * squash)) @ Matrix.Rotation(heading, 4, "Z")
            @ Matrix.Scale(scale, 4))
    first = len(builder.polygons)
    builder.lathe([(0.0, 0.0), (0.095, 0.12), (0.0, 0.3)], 4, MATTE, smooth=True, matrix=head)
    builder.tint(first, skin)
    if cheer:
        for side in (-1, 1):
            tube(builder, [frame @ Vector((side * 0.2, 0.0, 1.36)), frame @ Vector((side * 0.27, 0.05, 1.72))],
                 [0.045, 0.035], skin, 3, cap=False)


def simple_block(seed=0, rows=4, columns=7, spacing=0.62, rise=0.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for row in range(rows):
        for column in range(columns):
            if rng.random() < 0.16:
                continue
            x = (column - (columns - 1) / 2) * spacing + rng.uniform(-0.2, 0.2)
            y = -row * spacing * 1.15 + rng.uniform(-0.18, 0.18)
            toga = rng.random() < 0.08
            colour = (0.95, 0.93, 0.87) if toga else rng.choice(CROWD_TUNICS)
            mantle = (0.97, 0.95, 0.89) if toga else rng.choice(MANTLES)
            seated = rng.random() < 0.45
            simple_person(builder, x, y, row * rise, rng.uniform(-0.4, 0.4), colour, mantle, SKIN[rng.randrange(3)],
                          rng.uniform(0.9, 1.06), (not seated) and rng.random() < 0.2, seated)
    return builder


def tent(seed=0, length=3.2, width=2.4, height=2.1):
    rng = random.Random(seed)
    light, dark = TENT_CLOTH[seed % len(TENT_CLOTH)]
    builder = MeshBuilder()
    hl = length / 2
    hw = width / 2
    stripes = 4
    for side in (-1, 1):
        for k in range(stripes):
            x0 = -hl + length * k / stripes
            x1 = -hl + length * (k + 1) / stripes
            colour = light if k % 2 == 0 else dark
            sag = 0.06 * rng.uniform(0.5, 1.0)
            quad = [(x0, 0.0, height), (x1, 0.0, height), (x1, side * hw, 0.05), (x0, side * hw, 0.05)]
            mid = [(x0, side * hw * 0.5, height * 0.5 - sag), (x1, side * hw * 0.5, height * 0.5 - sag)]
            builder.oriented([quad[0], quad[1], mid[1], mid[0]], (0, side, 1), MATTE)
            builder.tint(len(builder.polygons) - 1, colour)
            builder.oriented([mid[0], mid[1], quad[2], quad[3]], (0, side, 1), MATTE)
            builder.tint(len(builder.polygons) - 1, colour)
    for sign in (-1, 1):
        x = sign * hl
        builder.oriented([(x, -hw, 0.05), (x, hw, 0.05), (x, 0.0, height)], (sign, 0, 0), MATTE)
        builder.tint(len(builder.polygons) - 1, light if sign > 0 else dark)
    tube(builder, [(-hl - 0.15, 0.0, 0.0), (-hl - 0.15, 0.0, height + 0.25)], [0.04, 0.035], WOOD, 4)
    tube(builder, [(hl + 0.15, 0.0, 0.0), (hl + 0.15, 0.0, height + 0.25)], [0.04, 0.035], WOOD, 4)
    builder.oriented([(hl + 0.02, -hw * 0.45, 0.05), (hl + 0.02, hw * 0.45, 0.05), (hl + 0.02, 0.0, height * 0.75)],
                     (1, 0, 0), MATTE)
    builder.tint(len(builder.polygons) - 1, (0.12, 0.09, 0.07))
    return builder


def booth(seed=0, width=3.4, depth=2.4):
    rng = random.Random(seed)
    light, dark = TENT_CLOTH[(seed + 2) % len(TENT_CLOTH)]
    builder = MeshBuilder()
    hw = width / 2
    for x in (-hw, hw):
        for y, h in ((0.0, 2.5), (-depth, 2.0)):
            tube(builder, [(x, y, 0.0), (x, y, h)], [0.05, 0.045], WOOD, 4)
    rows = []
    for t in (0.0, 0.5, 1.0):
        row = []
        for k in range(7):
            x = -hw - 0.2 + (width + 0.4) * k / 6
            sag = 0.12 * math.sin(math.pi * t) * (0.6 + 0.4 * abs(math.sin(k)))
            row.append((x, -depth * t + 0.3 * (1 - t) - 0.2 * t, 2.55 - 0.6 * t - sag))
        rows.append(row)
    for r in range(2):
        for k in range(6):
            colour = light if k % 2 == 0 else dark
            quad = [rows[r][k], rows[r][k + 1], rows[r + 1][k + 1], rows[r + 1][k]]
            builder.oriented(quad, (0, 0, 1), MATTE)
            builder.tint(len(builder.polygons) - 1, colour)
            builder.oriented(list(reversed(quad)), (0, 0, -1), MATTE)
            builder.tint(len(builder.polygons) - 1, tuple(v * 0.8 for v in colour))
    first = len(builder.polygons)
    builder.box((-hw + 0.1, 0.0, 0.0), (hw - 0.1, 0.7, 0.9), MATTE)
    builder.tint(first, (0.56, 0.40, 0.26))
    goods = [(0.80, 0.44, 0.26), (0.92, 0.78, 0.42), (0.42, 0.56, 0.24), (0.76, 0.20, 0.16), (0.95, 0.92, 0.84)]
    for k in range(6):
        x = -hw + 0.4 + k * (width - 0.8) / 5
        ellipsoid(builder, (x, 0.35, 1.02), (0.2, 0.22, 0.12 + 0.05 * rng.random()), rng.choice(goods), 6, 3)
    for k in range(3):
        ellipsoid(builder, (-hw + 0.6 + k * 0.5, -depth * 0.6, 0.35), (0.22, 0.22, 0.35), (0.78, 0.48, 0.30), 7, 4)
    return builder


def campfire(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(8):
        angle = TAU * k / 8
        ellipsoid(builder, (math.cos(angle) * 0.55, math.sin(angle) * 0.55, 0.1), (0.16, 0.14, 0.12),
                  (0.5, 0.48, 0.44), 5, 3)
    for k in range(4):
        angle = TAU * k / 4 + 0.3
        tube(builder, [(math.cos(angle) * 0.45, math.sin(angle) * 0.45, 0.05), (0.0, 0.0, 0.35)], [0.05, 0.04],
             (0.24, 0.16, 0.10), 4)
    ellipsoid(builder, (0.0, 0.0, 0.2), (0.25, 0.25, 0.25), (1.0, 0.55, 0.12), 6, 3)
    tube(builder, [(-0.8, 0.0, 0.0), (-0.8, 0.0, 1.2), (0.8, 0.0, 1.2), (0.8, 0.0, 0.0)], [0.03] * 4, WOOD, 4)
    builder.lathe([(0.0, 0.55), (0.22, 0.6), (0.28, 0.8), (0.24, 0.95), (0.0, 0.95)], 8, MATTE)
    builder.tint(len(builder.polygons) - 8, (0.22, 0.20, 0.18))
    return builder


def tethered_horses(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    tube(builder, [(-2.6, 0.0, 1.1), (2.6, 0.0, 1.1)], [0.025, 0.025], (0.5, 0.42, 0.3), 4)
    for x in (-2.6, 2.6):
        tube(builder, [(x, 0.0, 0.0), (x, 0.0, 1.2)], [0.05, 0.05], WOOD, 4)
    colours = [(0.45, 0.30, 0.18), (0.30, 0.20, 0.13), (0.62, 0.50, 0.38), (0.86, 0.82, 0.76), (0.22, 0.17, 0.13)]
    for k in range(2):
        builder.merge(coarse(lambda: horse(rng.choice(colours)), 0.6), placement(-1.2 + k * 2.4, -1.1, 0.0,
                                                                                 rng.uniform(-0.2, 0.2)))
    return builder


def chariot(seed=0):
    builder = MeshBuilder()
    for k in range(2):
        builder.merge(horse([(0.45, 0.30, 0.18), (0.86, 0.82, 0.76)][k]), placement(-0.4 + k * 0.8, 1.6, 0.0))
    for side in (-1, 1):
        ellipsoid(builder, (side * 0.7, -0.3, 0.5), (0.04, 0.5, 0.5), (0.4, 0.28, 0.16), 10, 3)
    first = len(builder.polygons)
    builder.box((-0.6, -0.7, 0.55), (0.6, 0.1, 1.5), MATTE)
    builder.tint(first, (0.72, 0.18, 0.12))
    tube(builder, [(0.0, 0.1, 0.8), (0.0, 1.9, 1.1)], [0.05, 0.04], WOOD, 4)
    driver = figure(Look(LINEN, hem=0.15, skin=1, hair=0, belt=(0.7, 0.2, 0.1), arms="forward", seed=seed))
    builder.merge(driver, placement(0.0, -0.35, 0.55))
    return builder


def statue_base(builder, width=1.1, depth=1.1, height=1.3, material="limestone", inscribed=True):
    first = len(builder.polygons)
    builder.box((-width / 2, -depth / 2, -0.4), (width / 2, depth / 2, height), material, bottom=False)
    builder.box((-width / 2 - 0.08, -depth / 2 - 0.08, height - 0.14), (width / 2 + 0.08, depth / 2 + 0.08, height),
                material)
    builder.box((-width / 2 - 0.1, -depth / 2 - 0.1, -0.4), (width / 2 + 0.1, depth / 2 + 0.1, 0.2), material,
                bottom=False)
    builder.tint(first, (0.80, 0.76, 0.66))
    if inscribed:
        rng = random.Random(int(width * 100 + height * 10))
        for line in range(2):
            z = height * (0.66 - line * 0.1)
            x = -width * 0.36
            while x < width * 0.34:
                w = rng.uniform(0.025, 0.05)
                first = len(builder.polygons)
                f = -depth / 2 - 0.004
                builder.oriented([(x, f, z), (x + w, f, z), (x + w, f, z + 0.06), (x, f, z + 0.06)], (0, -1, 0), MATTE)
                builder.tint(first, (0.45, 0.10, 0.08))
                x += w + rng.uniform(0.02, 0.04)


def bronze_statue(kind="athlete", seed=0, base_height=1.3, scale=1.1, material="bronze"):
    builder = MeshBuilder()
    statue_base(builder, height=base_height, material="marble" if seed % 3 == 0 else "limestone")
    if kind == "athlete":
        look = athlete(seed, ["olym_raise", "hip", "gesture", "olym_spear"][seed % 4], skin=0)
    elif kind == "zeus":
        look = Look(LINEN, hem=0.1, skin=0, hair=3, palla=LINEN, arms="olym_raise", seed=seed)
    elif kind == "draped":
        look = greek(seed, LINEN, LINEN, ["hip", "down", "gesture"][seed % 3])
    else:
        look = roman(seed, "toga_gesture")
    look.mono = (1.0, 1.0, 1.0)
    look.material = material
    figure_builder = person(look)
    if kind == "zeus":
        tube(figure_builder, [(0.32, 0.12, 1.78), (0.36, 0.1, 2.05), (0.31, 0.14, 2.3)], [0.03, 0.05, 0.03],
             (1.0, 1.0, 1.0), 5, material)
    builder.merge(figure_builder, Matrix.Translation((0.0, 0.0, base_height)) @ Matrix.Scale(scale, 4))
    return builder


def equestrian(seed=0):
    builder = MeshBuilder()
    statue_base(builder, 1.4, 3.0, 1.5, "marble")
    rider = person(roman(seed, "toga_gesture"))
    mount = horse((1.0, 1.0, 1.0), "bronze")
    rider.materials = ["bronze" if name == MATTE else name for name in rider.materials]
    rider.polygon_colors = [(1.0, 1.0, 1.0)] * len(rider.polygon_colors)
    mount.polygon_colors = [(1.0, 1.0, 1.0)] * len(mount.polygon_colors)
    builder.merge(mount, Matrix.Translation((0.0, 0.0, 1.5)) @ Matrix.Scale(1.2, 4))
    builder.merge(rider, Matrix.Translation((0.0, -0.1, 1.5 + 1.05)) @ Matrix.Scale(1.15, 4))
    return builder


def nike_paionios():
    builder = MeshBuilder()
    sides = 3
    for k, (r0, r1, z0, z1) in enumerate(((1.5, 1.45, 0.0, 0.6), (1.2, 0.9, 0.6, 8.6))):
        profile = [(r0, z0), (r1, z1)]
        builder.lathe(profile, sides, "marble", smooth=False, start=math.pi / 2, caps=True)
    figure_builder = nike(1.25, "marble", (1.0, 1.0, 1.0), dress=(0.95, 0.93, 0.88))
    builder.merge(figure_builder, Matrix.Translation((0.0, 0.2, 8.6)))
    return builder


def crown(builder, centre, radii, count, lobe, colour, seed, segments=6, inner=0.78):
    rng = random.Random(seed)
    cx, cy, cz = centre
    for k in range(count):
        u = rng.uniform(-1.0, 1.0)
        angle = rng.uniform(0.0, TAU)
        ring = math.sqrt(max(0.0, 1.0 - u * u))
        reach = rng.uniform(0.3, 1.0) ** 0.6
        x = cx + math.cos(angle) * ring * radii[0] * reach
        y = cy + math.sin(angle) * ring * radii[1] * reach
        z = cz + u * radii[2] * 0.8 * reach
        size = lobe * rng.uniform(0.7, 1.15)
        first = len(builder.polygons)
        rough_lobe(builder, (x, y, z), size, size * 1.7, MATTE, segments, seed + k, 0.0, amount=0.36)
        light = 0.62 + 0.42 * (u * 0.5 + 0.5) * reach + rng.uniform(-0.06, 0.06)
        light *= inner if reach < 0.75 else 1.0
        builder.tint(first, tuple(min(1.0, c * light) for c in colour))


def plane_tree(height=17.0, seed=0, foliage=(0.30, 0.44, 0.15)):
    rng = random.Random(seed)
    builder = MeshBuilder()
    bark = (0.46, 0.43, 0.34)
    tube(builder, [(0.0, 0.0, -0.4), (0.15, 0.05, height * 0.2), (0.3, 0.1, height * 0.38)], [0.55, 0.42, 0.34], bark,
         7)
    r = height * 0.3
    for k in range(4):
        angle = TAU * k / 4 + rng.uniform(-0.3, 0.3)
        tube(builder, [(0.3, 0.1, height * 0.36), (0.3 + math.cos(angle) * r * 0.3, 0.1 + math.sin(angle) * r * 0.3,
                                                   height * 0.5),
                       (0.3 + math.cos(angle) * r * 0.5, 0.1 + math.sin(angle) * r * 0.5, height * 0.62)],
             [0.2, 0.13, 0.07], (0.40, 0.37, 0.30), 5)
    crown(builder, (0.3, 0.1, height * 0.68), (r, r, height * 0.24), 18, height * 0.12, foliage, seed + 3, 6)
    return builder


def olive_tree(height=5.5, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    bark = (0.40, 0.36, 0.30)
    for k in range(3):
        angle = TAU * k / 3 + rng.uniform(-0.4, 0.4)
        top = Vector((math.cos(angle) * 0.9, math.sin(angle) * 0.9, height * 0.48))
        tube(builder, [(0.0, 0.0, -0.3), (math.cos(angle) * 0.25, math.sin(angle) * 0.2, 0.9), top],
             [0.26, 0.17, 0.09], bark, 5)
    crown(builder, (0.0, 0.0, height * 0.66), (height * 0.36, height * 0.36, height * 0.2), 9, height * 0.17,
          (0.44, 0.50, 0.33), seed + 2, 6)
    return builder


def poplar(height=19.0, seed=0):
    builder = MeshBuilder()
    tube(builder, [(0.0, 0.0, -0.3), (0.05, 0.0, height * 0.5), (0.1, 0.0, height * 0.8)], [0.32, 0.24, 0.1],
         (0.62, 0.60, 0.54), 6)
    crown(builder, (0.05, 0.0, height * 0.6), (height * 0.13, height * 0.13, height * 0.42), 12, height * 0.075,
          (0.46, 0.56, 0.36), seed + 5, 6)
    return builder


def pine(height=14.0, seed=0, segments=7):
    rng = random.Random(seed)
    builder = MeshBuilder()
    lean = (rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2))
    first = len(builder.polygons)
    trunk(builder, height * 0.72, 0.32, lean, MATTE)
    builder.tint(first, (0.42, 0.30, 0.22))
    foliage = (0.20, 0.34, 0.14)
    for k in range(4):
        angle = TAU * k / 4 + rng.uniform(-0.5, 0.5)
        reach = height * 0.13 * rng.uniform(0.4, 1.0)
        z = height * rng.uniform(0.72, 0.86)
        first = len(builder.polygons)
        rough_lobe(builder, (lean[0] + math.cos(angle) * reach, lean[1] + math.sin(angle) * reach, z),
                   height * 0.17, height * 0.13, MATTE, 5, seed + k, 0.3, amount=0.26)
        tone = rng.uniform(0.85, 1.12)
        builder.tint(first, tuple(min(1.0, c * tone) for c in foliage))
    return builder


def far_olive(height=5.0, seed=0):
    builder = MeshBuilder()
    first = len(builder.polygons)
    builder.lathe([(0.2, -0.3), (0.14, height * 0.45)], 3, MATTE, caps=False)
    builder.tint(first, (0.42, 0.38, 0.32))
    first = len(builder.polygons)
    builder.lathe([(0.0, height * 0.32), (height * 0.42, height * 0.5), (height * 0.36, height * 0.8), (0.0, height)], 5,
                  MATTE, smooth=True, radius_scale=lambda angle: 1.0 + 0.18 * math.sin(3 * angle + seed))
    builder.tint(first, (0.44, 0.52, 0.32))
    return builder


def pine_mid(height=13.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    first = len(builder.polygons)
    builder.lathe([(0.3, -0.5), (0.2, height * 0.74)], 4, MATTE, caps=False)
    builder.tint(first, (0.42, 0.30, 0.22))
    for k in range(2):
        angle = TAU * k / 2 + rng.uniform(-0.4, 0.4)
        first = len(builder.polygons)
        rough_lobe(builder, (math.cos(angle) * height * 0.08, math.sin(angle) * height * 0.08, height * 0.8),
                   height * 0.19, height * 0.13, MATTE, 5, seed + k, 0.3, amount=0.24)
        builder.tint(first, tuple(min(1.0, c * rng.uniform(0.88, 1.1)) for c in (0.20, 0.34, 0.14)))
    return builder


def far_pine(height=13.0, seed=0):
    builder = MeshBuilder()
    first = len(builder.polygons)
    builder.lathe([(0.0, height * 0.35), (height * 0.24, height * 0.62), (height * 0.2, height * 0.85), (0.0, height)],
                  5, MATTE, smooth=True)
    builder.tint(first, (0.20, 0.32, 0.14))
    first = len(builder.polygons)
    builder.lathe([(0.25, -0.3), (0.18, height * 0.5)], 3, MATTE, caps=False)
    builder.tint(first, (0.36, 0.26, 0.18))
    return builder


def reeds(seed=0, count=4):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        x = rng.uniform(-1.2, 1.2)
        y = rng.uniform(-1.2, 1.2)
        h = rng.uniform(1.6, 2.8)
        lean = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.0))
        first = len(builder.polygons)
        builder.oriented([(x - 0.06, y, 0.0), (x + 0.06, y, 0.0), (x + lean.x, y + lean.y, h)], (0, -1, 0), MATTE)
        builder.oriented([(x, y - 0.06, 0.0), (x, y + 0.06, 0.0), (x + lean.x, y + lean.y, h)], (1, 0, 0), MATTE)
        builder.tint(first, (0.46 + rng.uniform(-0.05, 0.08), 0.52, 0.26))
    return builder


def shrub(size=1.3, seed=0, colour=(0.34, 0.42, 0.20)):
    builder = MeshBuilder()
    first = len(builder.polygons)
    rough_lobe(builder, (0.0, 0.0, size * 0.35), size, size * 0.8, MATTE, 6, seed, 0.3, amount=0.3)
    builder.tint(first, colour)
    return builder


LIFE = {
    "conversation": lambda: conversation(11, 3),
    "conversation_b": lambda: conversation(23, 4, 0.5, 0.0),
    "conversation_c": lambda: conversation(37, 2, 0.0, 0.5),
    "camp_group": lambda: coarse(lambda: conversation(43, 3, 0.1, 0.3), 0.45),
    "guide_group": lambda: guide_group(41),
    "governor": lambda: governor_party(53),
    "runners": lambda: runners(61),
    "race": lambda: race(301, 7),
    "race_b": lambda: race(311, 5),
    "athletes": lambda: athletes_resting(71),
    "judges": lambda: judges_row(81),
    "sacrifice": lambda: sacrifice(91),
    "fig_greek": lambda: figure(greek(101, LINEN, INDIGO, "hip")),
    "fig_greek_b": lambda: figure(greek(102, (0.92, 0.88, 0.78), CRIMSON, "gesture", skin=0, hair=2)),
    "fig_roman": lambda: figure(roman(103, "toga")),
    "fig_maiden": lambda: figure(maiden(104)),
    "fig_athlete": lambda: figure(athlete(105, "hip"), crowned=True),
    "fig_worker": lambda: figure(worker(106, (0.80, 0.70, 0.52), "carry", carry="amphora")),
    "camp_worker": lambda: coarse(lambda: figure(worker(107, (0.84, 0.62, 0.40), "carry", carry="amphora")), 0.5),
}

WALKERS = {
    "walker_himation": lambda: figure(greek(201, LINEN, INDIGO, "swing", stride=0.17)),
    "walker_toga": lambda: figure(roman(202, "swing", stride=0.15)),
    "walker_maiden": lambda: figure(maiden(203, SAFFRON, (0.62, 0.20, 0.42), "swing", stride=0.14)),
    "walker_athlete": lambda: figure(athlete(204, "swing", stride=0.2, skin=1, hair=1), crowned=True),
    "walker_pilgrim": lambda: figure(greek(205, (0.86, 0.80, 0.66), (0.52, 0.36, 0.22), "swing", stride=0.17,
                                           skin=2, hair=3)),
    "walker_porter": lambda: figure(worker(206, (0.84, 0.62, 0.40), "swing", stride=0.2)),
}

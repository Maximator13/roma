import math
import random

from mathutils import Matrix, Vector

from . import pantheon_architecture as arch
from . import pantheon_refine as refine
from .geometry import MATTE, MeshBuilder, placement
from .life import WOOD
from .nimes_detail import potted_plant
from .nimes_figures import (POSES, Look, amphora, basket, beast, drape, ellipsoid, market_stall, pack_beast, person,
                            tube)

POSES.update({
    "pantheon_point_up": [((0.24, 0.06, 1.66), (0.3, 0.14, 1.89)), ((-0.215, -0.01, 1.1), (-0.225, 0.04, 0.86))],
    "pantheon_orans": [((0.34, 0.1, 1.2), (0.38, 0.24, 1.43)), ((-0.34, 0.1, 1.2), (-0.38, 0.24, 1.43))],
    "pantheon_pipes": [((0.2, 0.17, 1.24), (0.08, 0.3, 1.42)), ((-0.2, 0.17, 1.22), (-0.07, 0.3, 1.36))],
    "pantheon_drum": [((0.3, 0.1, 1.28), (0.3, 0.22, 1.52)), ((-0.24, 0.16, 1.18), (-0.06, 0.34, 1.4))],
    "pantheon_cymbals": [((0.24, 0.16, 1.2), (0.12, 0.36, 1.34)), ((-0.24, 0.16, 1.2), (-0.12, 0.36, 1.34))],
    "pantheon_tray": [((0.225, 0.08, 1.1), (0.2, 0.34, 1.08)), ((-0.225, 0.08, 1.1), (-0.2, 0.34, 1.08))],
})
BRONZE_TONE = (0.78, 0.6, 0.32)
SERPENTINE = (0.66, 0.92, 0.64)
LITTER_RED = (0.46, 0.17, 0.12)
GILT = (0.86, 0.68, 0.36)
PIGEON = (0.52, 0.53, 0.56)
EAVE_Z = refine.EAVE_Z
EAVE_X = arch.PORTICO_LINE - refine.EAVE_INSET
EAVE_NORTH = refine.NORTH_LINE - refine.EAVE_INSET


def tinted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def bend(builder, pivot, reach, angle, accept):
    for index, (x, y, z) in enumerate(builder.positions):
        if z <= pivot or not accept(x):
            continue
        turn = angle * min((z - pivot) / reach, 1.0)
        dz = z - pivot
        builder.positions[index] = (x, y * math.cos(turn) - dz * math.sin(turn), pivot + y * math.sin(turn) + dz * math.cos(turn))


def tilted(spec, angle=math.radians(45.0), lean=math.radians(6.0)):
    builder = person(spec)
    bend(builder, 1.45 * spec.scale, 0.07 * spec.scale, angle, lambda x: abs(x) <= 0.15 * spec.scale)
    bend(builder, 0.9 * spec.scale, 0.2 * spec.scale, lean, lambda x: True)
    return builder


def seller(seed):
    builder = person(Look("undyed", hem=0.55, skin=2, hair=1, apron="weld", belt="brown", arms="pantheon_tray", seed=seed))
    tinted(builder, WOOD, lambda: builder.box((-0.27, 0.24, 1.05), (0.27, 0.58, 1.08), MATTE))
    for k in range(6):
        ellipsoid(builder, (-0.19 + 0.076 * k, 0.36 + 0.09 * (k % 2), 1.11), (0.055, 0.05, 0.035), (0.78, 0.56, 0.3), 6, 3)
    return builder


def disc(builder, frame, radius, thickness, colour, segments=12, material=MATTE):
    tinted(builder, colour, lambda: builder.lathe([(0.0, thickness), (radius, thickness), (radius, 0.0), (0.0, 0.0)],
                                                   segments, material, smooth=False, matrix=frame))


def musicians():
    builder = MeshBuilder()
    piper = person(Look("woad", hem=0.5, skin=1, hair=0, belt="brown", cloak="madder", arms="pantheon_pipes", seed=141))
    for side in (-1, 1):
        tube(piper, [(0.0, 0.115, 1.575), (side * 0.11, 0.46, 1.3)], [0.011, 0.017], (0.86, 0.76, 0.52), 5)
    builder.merge(piper)
    drummer = person(Look("rose", hem=0.04, skin=0, hair=1, palla="weld", female=True, sleeves="long", arms="pantheon_drum",
                          scale=0.93, seed=142))
    disc(drummer, Matrix.Translation((0.36, 0.3, 1.58)) @ Matrix.Rotation(math.radians(-35.0), 4, "Z")
         @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.2, 0.05, (0.84, 0.74, 0.56), 14)
    builder.merge(drummer, placement(0.95, -0.35, 0.0, -0.45))
    cymbalist = person(Look("weld", hem=0.5, skin=2, hair=3, belt="madder", stride=0.12, arms="pantheon_cymbals", seed=143))
    for side in (-1, 1):
        disc(cymbalist, Matrix.Translation((side * 0.08, 0.44, 1.33)) @ Matrix.Rotation(-side * math.pi / 2, 4, "Y"),
             0.085, 0.015, BRONZE_TONE, 10)
    builder.merge(cymbalist, placement(-0.95, -0.3, 0.0, 0.45))
    return builder


def hoop(builder, centre, radius, colour):
    points = [Vector(centre) + Vector((0.0, radius * math.cos(2 * math.pi * k / 14), radius * math.sin(2 * math.pi * k / 14)))
              for k in range(15)]
    tube(builder, points, [0.012] * len(points), colour, 4, cap=False)


def children_hoop():
    builder = MeshBuilder()
    runner = person(Look("white", hem=0.5, skin=1, hair=3, belt="madder", stripe="madder", child=True, scale=0.62,
                         arms="forward", stride=0.16, seed=151))
    hoop(runner, (0.14, 0.75, 0.33), 0.33, BRONZE_TONE)
    tube(runner, [(0.11, 0.2, 0.68), (0.13, 0.51, 0.56)], [0.01, 0.009], WOOD, 4)
    builder.merge(runner)
    builder.merge(person(Look("weld", hem=0.05, skin=0, hair=1, female=True, sleeves="long", child=True, scale=0.66,
                              arms="gesture", stride=0.12, seed=152)), placement(-0.6, -1.0, 0.0, 0.2))
    builder.merge(beast("dog"), placement(0.7, -0.5, 0.0, -0.3))
    return builder


def children_ball():
    builder = MeshBuilder()
    for index, (x, y, turn) in enumerate(((0.0, -1.2, 0.0), (0.0, 1.2, math.pi), (1.3, 0.1, math.pi / 2))):
        look = Look(("madder", "white", "green")[index], hem=0.5, skin=index % 3, hair=(1, 3, 0)[index], belt="brown",
                    child=True, scale=(0.62, 0.66, 0.6)[index], arms=("forward", "gesture", "down")[index],
                    stride=0.1 if index == 2 else 0.0, seed=155 + index)
        builder.merge(person(look), placement(x, y, 0.0, turn))
    ellipsoid(builder, (0.0, 0.1, 1.05), (0.08, 0.08, 0.08), (0.62, 0.32, 0.2), 8, 5)
    return builder


def bearer(seed, stride):
    return person(Look("madder", hem=0.55, skin=2, hair=3, belt="brown", arms="shoulder", stride=stride, seed=seed))


def lectica(carried=True):
    builder = MeshBuilder()
    base = 1.02 if carried else 0.4
    tinted(builder, LITTER_RED, lambda: builder.box((-0.42, -1.0, base), (0.42, 1.0, base + 0.32), MATTE))
    tinted(builder, (0.82, 0.76, 0.62), lambda: builder.box((-0.38, -0.95, base + 0.32), (0.38, 0.95, base + 0.42), MATTE))
    ellipsoid(builder, (0.0, -0.72, base + 0.52), (0.3, 0.13, 0.12), (0.62, 0.3, 0.22), 8, 4)
    for x in (-0.4, 0.4):
        for y in (-0.95, 0.95):
            tube(builder, [(x, y, base + 0.3), (x, y, base + 1.28)], [0.026, 0.026], GILT, 5)
    tinted(builder, LITTER_RED, lambda: builder.box((-0.5, -1.06, base + 1.28), (0.5, 1.06, base + 1.36), MATTE))
    drape(builder, (0.46, 0.2, 0.15), [(0.48, base + 1.36), (0.3, base + 1.45), (0.0, base + 1.48)], 4,
          start=math.pi / 4, folds=(0, 0.0, 0.0), squash=2.1)
    for side in (-1, 1):
        curtain = []
        for row, z in enumerate((base + 1.27, base + 0.35)):
            curtain.append([(side * (0.43 + 0.03 * math.sin(k * 2.3 + row)), -0.95 + 1.15 * k / 6, z) for k in range(7)])
        for facing in (-1, 1):
            tinted(builder, (0.42, 0.49, 0.58) if side > 0 else (0.74, 0.5, 0.44),
                   lambda curtain=curtain, facing=facing: builder.surface(curtain, MATTE, smooth=True,
                                                                          facing=(side * facing, 0, 0)))
    pole_z = 1.47 if carried else base + 0.16
    for x in (-0.56, 0.56):
        tube(builder, [(x, -2.25, pole_z), (x, 2.25, pole_z)], [0.04, 0.04], WOOD, 5, start_cap=True)
    if not carried:
        for x in (-0.36, 0.36):
            for y in (-0.9, 0.9):
                tinted(builder, WOOD, lambda x=x, y=y: builder.box((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, base), MATTE))
        for index, (x, y, turn) in enumerate(((1.3, 0.6, -2.0), (1.5, -0.4, 1.9), (-1.35, 1.6, -0.6))):
            builder.merge(person(Look("madder", hem=0.55, skin=2, hair=3, belt="brown", arms=("hip", "down", "gesture")[index],
                                      seed=171 + index)), placement(x, y, 0.0, turn))
        return builder
    mirror = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
    for index, (x, y) in enumerate(((0.39, 1.75), (0.39, -1.75), (-0.39, 1.75), (-0.39, -1.75))):
        frame = placement(x, y, 0.0) if x > 0 else placement(x, y, 0.0) @ mirror
        builder.merge(bearer(161 + index, 0.17 if index % 2 else -0.17), frame)
    return builder


def pigeons(seed):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for _ in range(11):
        frame = placement(rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6), 0.0, rng.uniform(0, 2 * math.pi))
        shade = rng.uniform(0.75, 1.1)
        colour = tuple(c * shade for c in PIGEON)
        ellipsoid(builder, (0.0, 0.0, 0.065), (0.055, 0.11, 0.06), colour, 6, 3, matrix=frame)
        ellipsoid(builder, (0.0, 0.1, 0.13), (0.032, 0.036, 0.032), tuple(c * 0.8 for c in colour), 5, 3, matrix=frame)
    return builder


def goods(seed):
    rng = random.Random(seed)
    builder = MeshBuilder()
    produce = [(0.45, 0.55, 0.25), (0.7, 0.3, 0.18), (0.85, 0.72, 0.4), (0.42, 0.22, 0.3), (0.62, 0.48, 0.26)]
    for k in range(3):
        amphora(builder, Matrix.Translation((-0.9 + 0.36 * k, 0.5 + 0.08 * (k % 2), 0.03)),
                (0.7 + 0.04 * k, 0.42 + 0.03 * k, 0.28))
    amphora(builder, Matrix.Translation((0.2, 0.75, 0.16)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
            @ Matrix.Translation((0.0, 0.0, -0.45)), (0.66, 0.4, 0.27))
    for k in range(3):
        ellipsoid(builder, (-0.5 + 0.45 * k, -0.25, 0.2), (0.22, 0.18, 0.22), (0.66 + 0.05 * k, 0.58, 0.44), 7, 4)
    for k in range(2):
        basket(builder, 0.9 + 0.42 * k, -0.2 + 0.4 * k, 0.0, 0.18, produce[(k + seed) % 5], seed + k)
    for _ in range(5):
        x, y = rng.uniform(-1.4, 1.6), rng.uniform(-1.1, 1.1)
        size = rng.uniform(0.06, 0.13)
        tinted(builder, (0.48 + rng.uniform(0, 0.2), 0.36, 0.22),
               lambda x=x, y=y, size=size: builder.polygon([(x + size * math.cos(a), y + size * math.sin(a), 0.012)
                                                            for a in (0.3, 1.9, 3.1, 4.6)], MATTE))
    return builder


def dark_dog():
    builder = beast("dog")
    builder.tint(0, (0.45, 0.42, 0.4))
    return builder


def antefix():
    builder = MeshBuilder()
    outline = [(-0.12, 0.0), (0.12, 0.0), (0.14, 0.12), (0.06, 0.25), (0.0, 0.32), (-0.06, 0.25), (-0.14, 0.12)]
    tinted(builder, (0.74, 0.46, 0.31), lambda: builder.oriented([(x, 0.0, z) for x, z in outline], (0, 1, 0), MATTE))
    tinted(builder, (0.6, 0.38, 0.26), lambda: builder.oriented([(x, -0.012, z) for x, z in outline], (0, -1, 0), MATTE))
    return builder


def antefix_frames(spacing=0.62):
    frames = []
    count = int((EAVE_NORTH - 30.3) / spacing)
    for side in (-1, 1):
        frames += [placement(side * EAVE_X, 30.3 + spacing * k, EAVE_Z, side * math.pi / 2) for k in range(count + 1)]
    count = int(2 * (EAVE_X - 0.4) / spacing)
    frames += [placement(-EAVE_X + 0.4 + spacing * k, EAVE_NORTH, EAVE_Z, math.pi) for k in range(count + 1)]
    return frames


def border(builder, frame, x0, x1, z0, z1, width=0.1, depth=0.1):
    for minimum, maximum in (((x0 - width, 0.0, z0 - width), (x0, depth, z1 + width)),
                             ((x1, 0.0, z0 - width), (x1 + width, depth, z1 + width)),
                             ((x0, 0.0, z1), (x1, depth, z1 + width)), ((x0, 0.0, z0 - width), (x1, depth, z0))):
        builder.box(minimum, maximum, "marble_white", matrix=frame, bottom=False)


def rotunda_trim(walls):
    beta = math.radians(22.5) - arch.ALPHA
    R = arch.R
    for index in range(8):
        centre = math.radians(22.5 + 45 * index)
        a0, a1 = centre - beta, centre + beta
        arch.arc_lathe(walls, [(R, 1.2), (R - 0.03, 1.2), (R - 0.12, 1.15), (R - 0.12, 1.1), (R - 0.07, 1.08)], a0, a1, 8,
                       "marble_white")
        arch.arc_lathe(walls, [(R - 0.07, 0.24), (R - 0.1, 0.2), (R - 0.125, 0.12), (R - 0.125, 0.0)], a0, a1, 8,
                       "marble_white")
        for side in (-1, 1):
            frame = arch.inward_frame(centre + side * (beta - 1.65 / R), R)
            border(walls, frame, -0.5, 0.5, 2.2, 6.2)
            border(walls, frame, -0.42, 0.42, 6.9, 8.7)
            centre_frame = frame @ Matrix.Translation((0.0, 0.0, 6.55)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
            disc(walls, centre_frame, 0.24, 0.06, (1.0, 1.0, 1.0), 16, "marble_white")
            disc(walls, centre_frame, 0.18, 0.07, SERPENTINE, 16, "granite_grey")
    return walls


def door_detail(builder):
    half = arch.DOOR_HALF
    for y, facing, top in ((arch.BLOCK_FRONT + 0.25, 1, arch.LINTEL_TOP), (arch.BLOCK_SLAB, -1, arch.DOOR_HEIGHT)):
        for inner, outer, depth in ((0.0, 0.3, 0.07), (0.3, 0.56, 0.035)):
            y0, y1 = sorted((y, y + facing * depth))
            for side in (-1, 1):
                x0, x1 = sorted((side * (half + inner), side * (half + outer)))
                builder.box((x0, y0, 0.0), (x1, y1, top + outer), "marble_white", bottom=False)
            builder.box((-half - outer, y0, top + inner), (half + outer, y1, top + outer), "marble_white")
    for side in (-1, 1):
        frame = placement(side * half, arch.BLOCK_SLAB, 0.0, math.radians(-80.0) if side < 0 else math.radians(260.0))
        for y0, y1 in ((-0.26, -0.22), (0.0, 0.04)):
            spots = [(0.16 + (half - 0.32) * k / 7, z) for k in range(8) for z in (0.25, 3.65, 7.25)]
            spots += [(x, 0.25 + 7.0 * k / 16) for k in range(1, 16) for x in (0.12, half - 0.12)]
            for x, z in spots:
                builder.box((x - 0.035, y0, z - 0.035), (x + 0.035, y1, z + 0.035), "bronze", matrix=frame,
                            bottom=False, top=False)
    return builder


def dressed(build, seed):
    def make():
        builder = build()
        rng = random.Random(seed)
        if "terracotta_tiles" in builder.materials:
            slot = builder.materials.index("terracotta_tiles")
            for index, material in enumerate(builder.polygon_materials):
                if material == slot:
                    shade = rng.uniform(0.84, 1.08)
                    builder.polygon_colors[index] = (shade, shade * rng.uniform(0.94, 1.02), shade * rng.uniform(0.88, 1.0))
        return builder
    return make


PROPS = {
    "prop_stall_a": lambda: market_stall(3, (0.82, 0.74, 0.58)),
    "prop_stall_b": lambda: market_stall(4, (0.86, 0.8, 0.66)),
    "prop_stall_c": lambda: market_stall(7, (0.76, 0.68, 0.5)),
    "prop_lectica": lambda: lectica(True),
    "prop_lectica_parked": lambda: lectica(False),
    "prop_musicians": musicians,
    "prop_children_hoop": children_hoop,
    "prop_children_ball": children_ball,
    "prop_dog": lambda: beast("dog"),
    "prop_dog_dark": dark_dog,
    "prop_donkey": lambda: pack_beast("donkey"),
    "prop_goods_a": lambda: goods(5),
    "prop_goods_b": lambda: goods(9),
    "prop_laurel": lambda: potted_plant(4),
}
FLAT_PROPS = {"prop_pigeons": lambda: pigeons(3), "prop_antefix": antefix}
FIGURES = {
    "fig_gazer_toga": lambda: tilted(Look("white", hem=0.12, skin=1, hair=0, toga="white", arms="toga", scale=0.95, seed=181)),
    "fig_gazer_point": lambda: tilted(Look("madder", hem=0.55, skin=2, hair=1, belt="brown", arms="pantheon_point_up", scale=0.95,
                                           seed=182)),
    "fig_gazer_girl": lambda: tilted(Look("weld", hem=0.05, skin=1, hair=1, female=True, sleeves="long", child=True,
                                          arms="pantheon_point_up", scale=0.66, seed=183)),
    "fig_gazer_woman": lambda: tilted(Look("woad", hem=0.04, skin=0, hair=1, palla="rose", female=True, sleeves="long",
                                           arms="hip", scale=0.9, seed=184)),
    "fig_orans": lambda: person(Look("white", hem=0.03, skin=1, hair=0, palla="white", veil=True, female=True,
                                     sleeves="long", arms="pantheon_orans", scale=0.9, seed=185)),
    "fig_priest": lambda: person(Look("white", hem=0.12, skin=0, hair=2, toga="white", praetexta="purple", veil=True,
                                      arms="pantheon_orans", scale=0.95, seed=186)),
    "fig_seller": lambda: seller(187),
}

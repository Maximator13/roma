import math
import random

from mathutils import Matrix, Vector

from . import alexandrie_city as acity
from . import pont_life
from .ephese_town import ephesian_block, theatre_cavea
from .geometry import MATTE, MeshBuilder
from .nimes_figures import ellipsoid, tube
from .orders import gable_roof

STONE = "limestone"
MARBLE = "marble"
ASHLAR = "marble_ashlar"
PLASTER = "plaster"
PAVING = "paving"
TILES = "terracotta_tiles"
VOID = "shadow_void"
TAU = 2 * math.pi
BRICK = (0.80, 0.46, 0.34)
WARM = (0.98, 0.93, 0.84)
OCHRES = [(1.0, 0.86, 0.62), (0.98, 0.78, 0.56), (1.0, 0.93, 0.80), (0.95, 0.70, 0.52), (1.0, 0.97, 0.92),
          (0.92, 0.66, 0.50)]


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def terrace_chunk(seed, detail, width, depth, street=("south",), plinth=8.0):
    return ephesian_block(seed, detail, width, depth, street, plinth)


def theatre():
    return theatre_cavea()


def bath_complex(width=120.0, depth=80.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    painted(builder, BRICK, lambda: builder.box((-hw, -hd, -2.0), (hw, hd, 10.0), PLASTER, bottom=False))
    gable_roof(builder, -hd, hd, hw, 10.0, 12.0, TILES, along_axis="y", imbrex=False)
    halls = [(-hw * 0.55, 0.0, hw * 0.3, hd * 0.7, 22.0), (hw * 0.1, 0.0, hw * 0.22, hd * 0.8, 26.0),
             (hw * 0.6, 0.0, hw * 0.25, hd * 0.6, 20.0)]
    for cx, cy, sx, sy, top in halls:
        painted(builder, BRICK, lambda cx=cx, cy=cy, sx=sx, sy=sy, top=top: builder.box(
            (cx - sx, cy - sy, 10.0), (cx + sx, cy + sy, top), PLASTER, bottom=False))
        vault = []
        for k in range(9):
            angle = math.pi * k / 8
            vault.append((cx - sx + sx * (1 - math.cos(angle)), top + sx * 0.35 * math.sin(angle)))
        rows = [[(x, cy - sy, z) for x, z in vault], [(x, cy + sy, z) for x, z in vault]]
        painted(builder, (0.86, 0.48, 0.34), lambda rows=rows: builder.surface(rows, TILES, facing=(0, 0, 1)))
        for y, facing in ((cy - sy, -1), (cy + sy, 1)):
            fan = [(x, y, z) for x, z in vault]
            painted(builder, BRICK, lambda fan=fan, facing=facing: builder.oriented(fan, (0, facing, 0), PLASTER))
            for k in range(3):
                x = cx - sx * 0.6 + k * sx * 0.6
                builder.oriented([(x - 1.6, y + facing * 0.03, top - 7.0), (x + 1.6, y + facing * 0.03, top - 7.0),
                                  (x + 1.6, y + facing * 0.03, top - 1.5), (x - 1.6, y + facing * 0.03, top - 1.5)],
                                 (0, facing, 0), VOID)
    for k in range(int(width / 7.0)):
        x = -hw + 3.5 + k * 7.0
        for y, facing in ((-hd, -1), (hd, 1)):
            builder.oriented([(x - 1.2, y + facing * 0.03, 4.0), (x + 1.2, y + facing * 0.03, 4.0),
                              (x + 1.2, y + facing * 0.03, 7.6), (x - 1.2, y + facing * 0.03, 7.6)], (0, facing, 0),
                             VOID)
    if rng.random() < 0.9:
        painted(builder, WARM, lambda: builder.box((-hw - 0.3, -hd - 0.3, -0.5), (hw + 0.3, hd + 0.3, 1.2), MARBLE,
                                                  bottom=False, top=False))
    return builder


def palaestra(width=90.0, depth=80.0, height=7.0):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    painted(builder, (0.94, 0.82, 0.60), lambda: builder.box((-hw, -hd, -1.0), (hw, hd, 0.25), "matte",
                                                             bottom=False))
    for x0, y0, x1, y1 in ((-hw, -hd, hw, -hd + 8.0), (-hw, hd - 8.0, hw, hd), (-hw, -hd, -hw + 8.0, hd),
                           (hw - 8.0, -hd, hw, hd)):
        painted(builder, (0.97, 0.92, 0.84), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box(
            (x0, y0, -1.0), (x1, y1, height), PLASTER, bottom=False, top=False))
        builder.surface([[(x0, y0, height), (x1, y0, height)], [(x0, y1, height), (x1, y1, height)]], TILES,
                        facing=(0, 0, 1))
    inner = []
    for k in range(int((width - 20.0) / 4.0) + 1):
        x = -hw + 10.0 + k * 4.0
        inner.append((x, -hd + 8.3))
        inner.append((x, hd - 8.3))
    for k in range(1, int((depth - 20.0) / 4.0)):
        y = -hd + 10.0 + k * 4.0
        inner.append((-hw + 8.3, y))
        inner.append((hw - 8.3, y))
    for x, y in inner:
        tube(builder, [(x, y, 0.25), (x, y, height - 0.3)], [0.34, 0.28], (1.0, 0.98, 0.94), 6, MARBLE)
    return builder


def vedius_gymnasium():
    builder = MeshBuilder()
    builder.merge(bath_complex(140.0, 70.0, 7), Matrix.Translation((0.0, 40.0, 0.0)))
    builder.merge(palaestra(100.0, 70.0), Matrix.Translation((-10.0, -32.0, 0.0)))
    painted(builder, (0.98, 0.96, 0.92), lambda: builder.box((-16.0, 4.6, 1.0), (16.0, 5.2, 3.6), MARBLE,
                                                             bottom=False))
    for line in range(4):
        z = 3.1 - line * 0.5
        painted(builder, (0.70, 0.14, 0.10), lambda z=z: builder.oriented(
            [(-14.0, 4.58, z), (14.0, 4.58, z), (14.0, 4.58, z + 0.24), (-14.0, 4.58, z + 0.24)], (0, -1, 0), MATTE))
    return builder


def stadium(length=230.0, width=34.0, height=11.0):
    builder = MeshBuilder()
    hl, hw = length / 2, width / 2
    painted(builder, (0.92, 0.80, 0.58), lambda: builder.box((-hl, -hw, -1.0), (hl, hw, 0.2), "matte", bottom=False))
    bank = 22.0
    for side in (-1, 1):
        inner = side * hw
        outer = side * (hw + bank)
        rows = []
        for k in range(12):
            t = k / 11
            y = inner + (outer - inner) * t
            rows.append([(-hl, y, 0.2 + height * t), (hl, y, 0.2 + height * t)])
        painted(builder, (0.96, 0.93, 0.86), lambda rows=rows, side=side: builder.surface(rows, MARBLE,
                                                                                           facing=(0, -side, 1)))
        y0, y1 = sorted((outer, outer + side * 1.5))
        painted(builder, OCHRES[1], lambda y0=y0, y1=y1: builder.box((-hl, y0, -6.0), (hl, y1, height + 3.0),
                                                                     STONE, bottom=False))
        for k in range(int(length / 8.0)):
            x = -hl + 4.0 + k * 8.0
            y = outer + side * 1.52
            builder.oriented([(x - 1.4, y, -1.0), (x + 1.4, y, -1.0), (x + 1.4, y, 3.5), (x - 1.4, y, 3.5)],
                             (0, side, 0), VOID)
    profile = [-math.pi / 2 + math.pi * k / 8 for k in range(9)]
    sphendone = []
    for ring in (0, 11):
        t = ring / 11
        radius = hw + bank * t
        sphendone.append([(hl + radius * math.cos(a), radius * math.sin(a), 0.2 + height * t) for a in profile])
    painted(builder, (0.96, 0.93, 0.86), lambda: builder.surface(sphendone, MARBLE, facing=(-1, 0, 1)))
    wall = [Vector((hl + (hw + bank) * math.cos(a), (hw + bank) * math.sin(a), 0.0)) for a in profile]
    painted(builder, OCHRES[1], lambda: builder.sweep(wall, [(0.0, -6.0), (1.5, -6.0), (1.5, height + 3.0),
                                                             (0.0, height + 3.0)], STONE, caps=False))
    return builder


def small_temple(width=16.0, length=26.0, seed=0):
    from .colisee_monuments import temple
    builder, frames = temple(width, length, 3.2, 10.0, 1.0, 6, "ionic", peripteral=seed % 2 == 0)
    return builder, frames.get("ionic", [])


def harbour_gate(width=24.0, height=12.0):
    builder = MeshBuilder()
    hw = width / 2
    for x in (-hw, -hw / 3, hw / 3, hw):
        painted(builder, WARM, lambda x=x: builder.box((x - 1.4, -2.0, 0.0), (x + 1.4, 2.0, height), MARBLE,
                                                      bottom=False))
    painted(builder, WARM, lambda: builder.box((-hw - 1.6, -2.2, height), (hw + 1.6, 2.2, height + 2.6), MARBLE))
    painted(builder, (0.70, 0.18, 0.12), lambda: builder.box((-hw - 1.62, -2.22, height + 1.0),
                                                             (hw + 1.62, 2.22, height + 1.4), MATTE, bottom=False,
                                                             top=False))
    return builder


def street(length, width=11.0):
    builder = MeshBuilder()
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-length / 2, -width / 2, -0.6), (length / 2, width / 2,
                                                                                               0.12), PAVING,
                                                             bottom=False))
    for side in (-1, 1):
        y0, y1 = sorted((side * width / 2, side * (width / 2 + 1.8)))
        painted(builder, (0.92, 0.88, 0.80), lambda y0=y0, y1=y1: builder.box((-length / 2, y0, -0.6),
                                                                             (length / 2, y1, 0.3), STONE,
                                                                             bottom=False))
    return builder


def cypress(height=11.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    r = height * 0.08
    tube(builder, [(0.0, 0.0, -0.4), (0.0, 0.0, 1.2)], [0.14, 0.1], (0.36, 0.28, 0.2), 4)
    crown = [(0.0, 0.6), (r * 0.8, height * 0.12), (r, height * 0.3), (r * 0.9, height * 0.5), (r * 0.66, height * 0.7),
             (r * 0.36, height * 0.88), (0.0, height)]
    phase = rng.uniform(0, 6.28)
    painted(builder, (0.17, 0.27, 0.13), lambda: builder.lathe(crown, 9, MATTE, smooth=True, radius_scale=lambda a: (
        1.0 + 0.12 * math.sin(4 * a + phase) + 0.06 * math.sin(7 * a + phase * 2))))
    return builder


def pine(height=11.0, seed=0):
    return hill_pine(height, seed)


def maquis(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(2):
        tone = rng.uniform(0.85, 1.15)
        pont_life.blob(builder, (rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 0.7), (1.3, 1.1, 0.9),
                       (0.30 * tone, 0.38 * tone, 0.19 * tone), MATTE, 5, 3, wobble=0.2, seed=seed * 5 + k)
    return builder


def hill_pine(height=10.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    top = Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), height * 0.7))
    tube(builder, [(0.0, 0.0, -0.6), top], [0.24, 0.12], (0.40, 0.30, 0.22), 4)
    for k in range(3):
        angle = TAU * k / 3 + rng.uniform(-0.4, 0.4)
        centre = top + Vector((math.cos(angle) * height * 0.14, math.sin(angle) * height * 0.14,
                               rng.uniform(-0.6, 0.6)))
        tone = rng.uniform(0.85, 1.12)
        pont_life.blob(builder, tuple(centre), (height * 0.2, height * 0.2, height * 0.1),
                       (0.22 * tone, 0.32 * tone, 0.16 * tone), MATTE, 6, 3, wobble=0.25, seed=seed * 7 + k)
    return builder


def olive(seed=0):
    return pont_life.olive(4.6, seed)


def poplar(seed=0):
    return pont_life.poplar(15.0, seed)


def plane(seed=0):
    return acity.broad_tree(15.0, seed, (0.30, 0.46, 0.18), 7)


def reed_bed(seed=0, count=5):
    rng = random.Random(seed)
    builder = MeshBuilder()
    for k in range(count):
        builder.merge(pont_life.reed(seed * 7 + k), Matrix.Translation((rng.uniform(-3.0, 3.0), rng.uniform(-3.0, 3.0),
                                                                        0.0)) @ Matrix.Scale(rng.uniform(0.9, 1.4), 4))
    return builder


def farmstead(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    wall = OCHRES[rng.randrange(len(OCHRES))]
    for x0, y0, x1, y1, h in ((-8.0, -4.0, 8.0, 4.0, 5.0), (-8.0, 4.0, -3.0, 14.0, 3.6), (4.0, 4.0, 8.0, 12.0, 3.2)):
        painted(builder, wall, lambda x0=x0, y0=y0, x1=x1, y1=y1, h=h: builder.box((x0, y0, -1.5), (x1, y1, h), PLASTER,
                                                                                   bottom=False, top=False))
        roof = MeshBuilder()
        if x1 - x0 >= y1 - y0:
            gable_roof(roof, x0 - 0.3, x1 + 0.3, (y1 - y0) / 2 + 0.4, h, h + 1.6, TILES, along_axis="x", imbrex=False)
            shift = (0.0, (y0 + y1) / 2, 0.0)
        else:
            gable_roof(roof, y0 - 0.3, y1 + 0.3, (x1 - x0) / 2 + 0.4, h, h + 1.4, TILES, along_axis="y", imbrex=False)
            shift = ((x0 + x1) / 2, 0.0, 0.0)
        roof.tint(0, (1.0, 0.86, 0.80))
        builder.merge(roof, Matrix.Translation(shift))
    painted(builder, (0.86, 0.78, 0.62), lambda: builder.box((-2.5, 4.0, -1.0), (4.0, 14.0, 1.6), STONE, bottom=False,
                                                             top=False))
    builder.oriented([(-1.0, -4.03, 0.0), (1.0, -4.03, 0.0), (1.0, -4.03, 2.4), (-1.0, -4.03, 2.4)], (0, -1, 0), VOID)
    for k in range(3):
        ellipsoid(builder, (2.0 + k * 1.2, 9.0, 0.6), (0.6, 0.6, 0.8), (0.86, 0.74, 0.40), 6, 3)
    return builder


def tomb(seed=0):
    from .alexandrie_monuments import tomb as alexandrie_tomb
    return alexandrie_tomb(seed)


def heroon(seed=0):
    builder = MeshBuilder()
    painted(builder, WARM, lambda: builder.box((-3.0, -3.0, -1.0), (3.0, 3.0, 3.0), ASHLAR, bottom=False))
    painted(builder, (0.99, 0.97, 0.92), lambda: builder.box((-3.3, -3.3, 3.0), (3.3, 3.3, 3.6), MARBLE))
    for x in (-2.4, 2.4):
        for y in (-2.4, 2.4):
            tube(builder, [(x, y, 3.6), (x, y, 7.4)], [0.28, 0.24], (1.0, 0.98, 0.94), 6, MARBLE)
    painted(builder, (0.99, 0.97, 0.92), lambda: builder.box((-3.1, -3.1, 7.4), (3.1, 3.1, 8.2), MARBLE))
    painted(builder, (0.20, 0.36, 0.62), lambda: builder.box((-3.12, -3.12, 7.7), (3.12, 3.12, 7.9), MATTE,
                                                             bottom=False, top=False))
    builder.prism([(-3.2, -3.2), (3.2, -3.2), (3.2, 3.2), (-3.2, 3.2)], 8.2, 8.6, MARBLE, bottom=False)
    painted(builder, (0.96, 0.94, 0.88), lambda: builder.lathe([(3.3, 8.6), (0.2, 11.4), (0.0, 11.5)], 4, MARBLE,
                                                               smooth=False, start=math.pi / 4))
    return builder


def wagon_shed(seed=0):
    builder = MeshBuilder()
    for x in (-4.0, 4.0):
        for y in (-3.0, 3.0):
            tube(builder, [(x, y, 0.0), (x, y, 3.0)], [0.12, 0.1], (0.44, 0.32, 0.22), 4)
    gable_roof(builder, -4.4, 4.4, 3.6, 3.0, 4.2, TILES, along_axis="x", imbrex=False)
    return builder


def fishing_hut(seed=0):
    builder = MeshBuilder()
    painted(builder, (0.70, 0.60, 0.44), lambda: builder.box((-2.5, -2.0, -0.5), (2.5, 2.0, 2.4), MATTE, bottom=False,
                                                             top=False))
    gable_roof(builder, -2.8, 2.8, 2.4, 2.4, 3.8, MATTE, along_axis="x", imbrex=False)
    builder.tint(len(builder.polygons) - 2, (0.74, 0.66, 0.44))
    return builder


def awning(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    cloth = [(0.82, 0.16, 0.10), (0.92, 0.64, 0.18), (0.80, 0.30, 0.12), (0.20, 0.38, 0.66)][seed % 4]
    for k in range(4):
        x0 = -2.4 + k * 1.2
        quad = [(x0, -1.6, 2.5), (x0 + 1.2, -1.6, 2.5), (x0 + 1.2, 1.6, 3.0), (x0, 1.6, 3.0)]
        tone = cloth if k % 2 == 0 else (0.98, 0.94, 0.86)
        painted(builder, tone, lambda quad=quad: builder.oriented(quad, (0, -0.3, 1), MATTE))
        painted(builder, tuple(c * 0.7 for c in tone), lambda quad=quad: builder.oriented(list(reversed(quad)),
                                                                                          (0, 0.3, -1), MATTE))
    for x in (-2.3, 2.3):
        for y, z in ((-1.5, 2.5), (1.5, 3.0)):
            tube(builder, [(x, y, 0.0), (x, y, z)], [0.05, 0.05], (0.44, 0.32, 0.21), 4)
    painted(builder, (0.58, 0.44, 0.30), lambda: builder.box((-2.0, -1.0, 0.0), (2.0, 0.2, 0.8), MATTE, bottom=False))
    for k in range(8):
        tone = rng.choice([(0.86, 0.60, 0.28), (0.62, 0.70, 0.30), (0.90, 0.30, 0.20), (0.95, 0.85, 0.55)])
        ellipsoid(builder, (-1.7 + k * 0.48, rng.uniform(-0.7, -0.1), 0.9), (0.2, 0.18, 0.12), tone, 6, 3)
    return builder

import math
import random

from mathutils import Matrix, Vector

from .colisee_monuments import column_frame
from .geometry import MATTE, VOID_MATERIAL, MeshBuilder, placement
from .halicarnasse_mausoleum import painted
from .nimes_figures import ellipsoid, tube
from .pantheon_city import blob, shade_crown

STONE = "limestone"
MARBLE = "marble_white"
PLASTER = "plaster"
POLISHED = "stucco_polished"
TILES = "terracotta_tiles"
PAVING = "travertine"
VOID = VOID_MATERIAL
TAU = 2 * math.pi
WARM = (1.0, 0.95, 0.88)
STONE_TONE = (0.96, 0.90, 0.80)
RED = (0.70, 0.17, 0.12)
BLUE = (0.18, 0.34, 0.66)
OCHRE = (0.90, 0.64, 0.30)
GREEN = (0.30, 0.46, 0.30)
PANELS = [(0.62, 0.40, 0.16), (0.48, 0.12, 0.08), (0.10, 0.13, 0.22), (0.56, 0.30, 0.14)]
PANEL_FRAME = (0.16, 0.12, 0.10)
WOOD = (0.42, 0.30, 0.20)
THEATRE_RADIUS = 43.0
THEATRE_ORCHESTRA = 9.0
THEATRE_ROWS = 40
THEATRE_DEPTH = 0.78
THEATRE_RISE = 0.42
THEATRE_DIAZOMA = 22
THEATRE_SWEEP = math.radians(206.0)


def row_radius(row):
    return THEATRE_ORCHESTRA + 1.4 + row * THEATRE_DEPTH + (1.4 if row >= THEATRE_DIAZOMA else 0.0)


def row_height(row):
    return 0.45 + row * THEATRE_RISE + (0.3 if row >= THEATRE_DIAZOMA else 0.0)


def theatre_top():
    return row_height(THEATRE_ROWS)


def ring_quads(builder, r0, r1, z0, z1, start, sweep, segments, material, colour):
    first = len(builder.polygons)
    for k in range(segments):
        a0 = start + sweep * k / segments
        a1 = start + sweep * (k + 1) / segments
        p = [(r0 * math.cos(a0), r0 * math.sin(a0)), (r0 * math.cos(a1), r0 * math.sin(a1)),
             (r1 * math.cos(a1), r1 * math.sin(a1)), (r1 * math.cos(a0), r1 * math.sin(a0))]
        builder.oriented([(*p[0], z0), (*p[1], z0), (*p[2], z1), (*p[3], z1)], (0, 0, 1), material)
    builder.tint(first, colour)


def riser(builder, radius, z0, z1, start, sweep, segments, material, colour):
    first = len(builder.polygons)
    for k in range(segments):
        a0 = start + sweep * k / segments
        a1 = start + sweep * (k + 1) / segments
        mid = (a0 + a1) / 2
        builder.oriented([(radius * math.cos(a0), radius * math.sin(a0), z0), (radius * math.cos(a1), radius * math.sin(a1), z0),
                          (radius * math.cos(a1), radius * math.sin(a1), z1), (radius * math.cos(a0), radius * math.sin(a0), z1)],
                         (-math.cos(mid), -math.sin(mid), 0.0), material)
    builder.tint(first, colour)


def greek_theatre(seed=5):
    rng = random.Random(seed)
    builder = MeshBuilder()
    frames = []
    start = -math.pi / 2 - THEATRE_SWEEP / 2
    segments = 44
    ring_quads(builder, 0.0, THEATRE_ORCHESTRA, 0.0, 0.0, 0.0, TAU, 36, PAVING, (0.94, 0.82, 0.64))
    ring_quads(builder, THEATRE_ORCHESTRA, THEATRE_ORCHESTRA + 1.4, 0.02, 0.02, 0.0, TAU, 36, PAVING, (0.86, 0.82, 0.74))
    previous_radius = THEATRE_ORCHESTRA + 1.4
    previous_z = 0.02
    for row in range(THEATRE_ROWS):
        r = row_radius(row)
        z = row_height(row)
        if row == THEATRE_DIAZOMA:
            ring_quads(builder, previous_radius, r, previous_z, previous_z, start, THEATRE_SWEEP, segments, PAVING,
                       (0.9, 0.86, 0.78))
            riser(builder, r, previous_z, z, start, THEATRE_SWEEP, segments, STONE, (0.92, 0.86, 0.76))
        else:
            riser(builder, previous_radius if row else r - THEATRE_DEPTH, previous_z, z, start, THEATRE_SWEEP, segments,
                  STONE, (0.90 + 0.04 * (row % 2), 0.85, 0.75))
        tone = 1.0 - 0.05 * rng.random()
        ring_quads(builder, previous_radius if row else r - THEATRE_DEPTH, r + THEATRE_DEPTH, z, z, start,
                   THEATRE_SWEEP, segments, MARBLE, (0.98 * tone, 0.94 * tone, 0.86 * tone))
        previous_radius = r + THEATRE_DEPTH
        previous_z = z
    top = theatre_top()
    ring_quads(builder, previous_radius, THEATRE_RADIUS + 1.0, top, top, start, THEATRE_SWEEP, segments, PAVING,
               (0.86, 0.82, 0.72))
    riser(builder, THEATRE_RADIUS + 1.0, top, top + 1.2, start, THEATRE_SWEEP, segments, STONE, STONE_TONE)
    ring_quads(builder, THEATRE_RADIUS + 1.0, THEATRE_RADIUS + 1.8, top + 1.2, top + 1.2, start, THEATRE_SWEEP, segments,
               STONE, STONE_TONE)
    stairs_lower = 9
    stairs_upper = 17
    for count, rows in ((stairs_lower, range(0, THEATRE_DIAZOMA)), (stairs_upper, range(THEATRE_DIAZOMA, THEATRE_ROWS))):
        for k in range(count + 1):
            angle = start + THEATRE_SWEEP * k / count
            c, s = math.cos(angle), math.sin(angle)
            frame = Matrix(((c, -s, 0.0, 0.0), (s, c, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
            for row in rows:
                r = row_radius(row)
                z = row_height(row)
                if row == THEATRE_DIAZOMA or row == 0:
                    continue
                painted(builder, (0.84, 0.78, 0.68), lambda r=r, z=z, frame=frame: builder.box(
                    (r - THEATRE_DEPTH / 2, -0.45, z - THEATRE_RISE - 0.02), (r + 0.02, 0.45, z - THEATRE_RISE / 2), STONE,
                    frame, bottom=False))
    for side in (-1, 1):
        angle = start if side < 0 else start + THEATRE_SWEEP
        c, s = math.cos(angle), math.sin(angle)
        outward = Vector((c, s, 0.0))
        tangent = Vector((-s, c, 0.0)) * (-side)
        inner = outward * (THEATRE_ORCHESTRA + 1.2)
        outer = outward * (THEATRE_RADIUS + 1.8)
        a, b = inner, outer
        quad_top = [a + tangent * 0.0, b + tangent * 0.0, b + tangent * 1.6, a + tangent * 1.6]
        first = len(builder.polygons)
        builder.prism([(p.x, p.y) for p in quad_top], -6.0, 0.0, STONE, top=False, bottom=False)
        ramp = [a, b, b + tangent * 1.6, a + tangent * 1.6]
        heights = [0.6, top + 1.3, top + 1.3, 0.6]
        builder.oriented([(p.x, p.y, h) for p, h in zip(ramp, heights)], (0, 0, 1), STONE)
        for p0, p1, h0, h1 in ((a, b, 0.6, top + 1.3), (a + tangent * 1.6, b + tangent * 1.6, 0.6, top + 1.3)):
            builder.oriented([(p0.x, p0.y, -6.0), (p1.x, p1.y, -6.0), (p1.x, p1.y, h1), (p0.x, p0.y, h0)],
                             tangent if p0 is not a else -tangent, STONE)
        builder.tint(first, (0.92, 0.85, 0.72))
    skene_y0 = THEATRE_ORCHESTRA + 1.0
    length = 26.25
    hl = length / 2
    proscenium = 3.1
    painted(builder, (0.94, 0.88, 0.78), lambda: builder.box((-hl, skene_y0, -1.0), (hl, skene_y0 + 3.0, proscenium),
                                                             STONE, bottom=False))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-hl - 0.2, skene_y0 - 0.25, proscenium),
                                                             (hl + 0.2, skene_y0 + 3.0, proscenium + 0.45), MARBLE))
    painted(builder, RED, lambda: builder.box((-hl - 0.22, skene_y0 - 0.27, proscenium + 0.12),
                                              (hl + 0.22, skene_y0 - 0.2, proscenium + 0.3), MATTE, bottom=False, top=False))
    for k in range(14):
        x = -hl + 0.6 + (length - 1.2) * k / 13
        frames.append(column_frame(x, skene_y0 - 0.12, 0.0, 0.46, proscenium))
        if k < 13:
            x0, x1 = x + 0.35, x + (length - 1.2) / 13 - 0.35
            colour = PANELS[(k + seed) % len(PANELS)]
            first = len(builder.polygons)
            builder.oriented([(x0, skene_y0 - 0.02, 0.35), (x1, skene_y0 - 0.02, 0.35), (x1, skene_y0 - 0.02, proscenium - 0.25),
                              (x0, skene_y0 - 0.02, proscenium - 0.25)], (0, -1, 0), MATTE)
            builder.tint(first, PANEL_FRAME)
            first = len(builder.polygons)
            builder.oriented([(x0 + 0.12, skene_y0 - 0.03, 0.47), (x1 - 0.12, skene_y0 - 0.03, 0.47),
                              (x1 - 0.12, skene_y0 - 0.03, proscenium - 0.37), (x0 + 0.12, skene_y0 - 0.03, proscenium - 0.37)],
                             (0, -1, 0), MATTE)
            builder.tint(first, colour)
            mx, mz = (x0 + x1) / 2, (0.47 + proscenium - 0.37) / 2
            blob = [(mx + 0.32 * math.sin(a) * (0.7 + 0.3 * math.cos(3 * a)), skene_y0 - 0.04, mz + 0.85 * math.cos(a))
                    for a in [math.tau * j / 9 for j in range(9)]]
            first = len(builder.polygons)
            builder.oriented(blob, (0, -1, 0), MATTE)
            builder.tint(first, tuple(min(1.0, c * 1.5 + 0.18) for c in colour))
    back = skene_y0 + 3.0
    depth = 8.0
    height = 10.6
    painted(builder, (0.95, 0.87, 0.74), lambda: builder.box((-hl - 3.0, back, -1.5), (hl + 3.0, back + depth, height),
                                                             STONE, bottom=False))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-hl - 3.2, back - 0.2, height - 0.6),
                                                             (hl + 3.2, back + depth + 0.2, height), MARBLE))
    for k, x in enumerate((-8.4, -2.8, 2.8, 8.4)):
        builder.oriented([(x - 1.5, back - 0.03, proscenium + 0.5), (x + 1.5, back - 0.03, proscenium + 0.5),
                          (x + 1.5, back - 0.03, proscenium + 4.4), (x - 1.5, back - 0.03, proscenium + 4.4)], (0, -1, 0), VOID)
        frames.append(column_frame(x - 1.75, back - 0.3, proscenium + 0.45, 0.42, 4.6))
        frames.append(column_frame(x + 1.75, back - 0.3, proscenium + 0.45, 0.42, 4.6))
    for x in (-6.0, 0.0, 6.0):
        builder.oriented([(x - 0.9, back - 0.03, -0.2), (x + 0.9, back - 0.03, -0.2), (x + 0.9, back - 0.03, 2.6),
                          (x - 0.9, back - 0.03, 2.6)], (0, -1, 0), VOID)
    for x0, x1 in ((-hl - 3.0, -hl), (hl, hl + 3.0)):
        builder.oriented([(x0 + 0.6, back - 0.03, 0.0), (x1 - 0.6, back - 0.03, 0.0), (x1 - 0.6, back - 0.03, 3.2),
                          (x0 + 0.6, back - 0.03, 3.2)], (0, -1, 0), VOID)
    rise = depth * 0.14
    first = len(builder.polygons)
    builder.surface([[(-hl - 3.4, back - 0.4, height), (hl + 3.4, back - 0.4, height)],
                     [(-hl - 3.4, back + depth / 2, height + rise), (hl + 3.4, back + depth / 2, height + rise)]], TILES,
                    facing=(0, -1, 1))
    builder.surface([[(-hl - 3.4, back + depth / 2, height + rise), (hl + 3.4, back + depth / 2, height + rise)],
                     [(-hl - 3.4, back + depth + 0.4, height), (hl + 3.4, back + depth + 0.4, height)]], TILES,
                    facing=(0, 1, 1))
    builder.tint(first, (0.96, 0.62, 0.44))
    for x in (-hl - 3.2, hl + 3.2):
        n = -1 if x < 0 else 1
        painted(builder, (0.95, 0.87, 0.74), lambda x=x, n=n: builder.oriented(
            [(x, back - 0.2, height), (x, back + depth + 0.2, height), (x, back + depth / 2, height + rise)], (n, 0, 0), STONE))
    for side in (-1, 1):
        gx = side * (hl + 6.5)
        painted(builder, (0.96, 0.90, 0.80), lambda gx=gx: builder.box((gx - 0.5, skene_y0 - 1.0, 0.0), (gx + 0.5, skene_y0, 4.2),
                                                                      MARBLE))
        painted(builder, (0.96, 0.90, 0.80), lambda gx=gx: builder.box((gx - 3.0, skene_y0 - 1.0, 4.2), (gx + 3.0, skene_y0, 5.0),
                                                                      MARBLE))
        frames.append(column_frame(gx - 2.4, skene_y0 - 0.5, 0.0, 0.4, 4.2))
        frames.append(column_frame(gx + 2.4, skene_y0 - 0.5, 0.0, 0.4, 4.2))
    return builder, frames


def temple_terrace(builder, hx, hy, z, colour=STONE_TONE):
    painted(builder, colour, lambda: builder.box((-hx, -hy, z - 14.0), (hx, hy, z), STONE, bottom=False))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-hx - 0.2, -hy - 0.2, z - 0.35), (hx + 0.2, hy + 0.2, z + 0.02),
                                                             PAVING))


def statue(builder, base, height, colour, gilt_colour=(0.92, 0.72, 0.30)):
    x, y, z = base
    painted(builder, (0.98, 0.94, 0.88), lambda: builder.box((x - 0.6, y - 0.6, z), (x + 0.6, y + 0.6, z + 1.6), MARBLE))
    tube(builder, [(x, y, z + 1.6), (x, y, z + 1.6 + height * 0.45), (x, y, z + 1.6 + height * 0.85)],
         [height * 0.12, height * 0.1, height * 0.07], colour, 8)
    ellipsoid(builder, (x, y, z + 1.6 + height * 0.93), (height * 0.07, height * 0.07, height * 0.08), gilt_colour, 8, 5)


def palace(seed=3):
    rng = random.Random(seed)
    builder = MeshBuilder()
    frames = []
    hx, hy = 34.0, 24.0
    wing = 9.0
    height = 9.5
    painted(builder, (0.92, 0.84, 0.70), lambda: builder.box((-hx - 4.0, -hy - 4.0, -12.0), (hx + 4.0, hy + 4.0, 0.0), STONE,
                                                             bottom=False))
    painted(builder, (0.96, 0.92, 0.84), lambda: builder.box((-hx - 4.2, -hy - 4.2, -0.3), (hx + 4.2, hy + 4.2, 0.05), PAVING,
                                                             bottom=False))
    wall = (1.0, 0.86, 0.72)
    rects = [(-hx, -hy, hx, -hy + wing), (-hx, hy - wing, hx, hy), (-hx, -hy + wing, -hx + wing, hy - wing),
             (hx - wing, -hy + wing, hx, hy - wing)]
    for x0, y0, x1, y1 in rects:
        painted(builder, wall, lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box((x0, y0, 0.0), (x1, y1, height), POLISHED,
                                                                              bottom=False, top=False))
        painted(builder, (0.98, 0.95, 0.90), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box(
            (x0 - 0.25, y0 - 0.25, height - 0.7), (x1 + 0.25, y1 + 0.25, height), MARBLE, bottom=True))
        painted(builder, (0.80, 0.30, 0.20), lambda x0=x0, y0=y0, x1=x1, y1=y1: builder.box(
            (x0 - 0.04, y0 - 0.04, 0.0), (x1 + 0.04, y1 + 0.04, 1.4), POLISHED, bottom=False, top=False))
        along_x = (x1 - x0) > (y1 - y0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        half_short = ((y1 - y0) if along_x else (x1 - x0)) / 2 + 0.6
        rise = half_short * 0.4
        first = len(builder.polygons)
        if along_x:
            builder.surface([[(x0 - 0.6, cy - half_short, height), (x1 + 0.6, cy - half_short, height)],
                             [(x0 - 0.6, cy, height + rise), (x1 + 0.6, cy, height + rise)]], TILES, facing=(0, -1, 1))
            builder.surface([[(x0 - 0.6, cy, height + rise), (x1 + 0.6, cy, height + rise)],
                             [(x0 - 0.6, cy + half_short, height), (x1 + 0.6, cy + half_short, height)]], TILES,
                            facing=(0, 1, 1))
        else:
            builder.surface([[(cx - half_short, y0 - 0.6, height), (cx - half_short, y1 + 0.6, height)],
                             [(cx, y0 - 0.6, height + rise), (cx, y1 + 0.6, height + rise)]], TILES, facing=(-1, 0, 1))
            builder.surface([[(cx, y0 - 0.6, height + rise), (cx, y1 + 0.6, height + rise)],
                             [(cx + half_short, y0 - 0.6, height), (cx + half_short, y1 + 0.6, height)]], TILES,
                            facing=(1, 0, 1))
        builder.tint(first, (0.98, 0.60, 0.42))
    for side in (-1, 1):
        for k in range(12):
            x = -hx + 3.0 + k * (2 * hx - 6.0) / 11
            y = side * (hy + 0.03)
            for z0 in (1.8, 5.8):
                builder.oriented([(x - 0.6, y, z0), (x + 0.6, y, z0), (x + 0.6, y, z0 + 2.0), (x - 0.6, y, z0 + 2.0)],
                                 (0, side, 0), VOID)
    for side in (-1, 1):
        for k in range(8):
            y = -hy + 3.0 + k * (2 * hy - 6.0) / 7
            x = side * (hx + 0.03)
            for z0 in (1.8, 5.8):
                builder.oriented([(x, y - 0.6, z0), (x, y + 0.6, z0), (x, y + 0.6, z0 + 2.0), (x, y - 0.6, z0 + 2.0)],
                                 (side, 0, 0), VOID)
    ix, iy = hx - wing, hy - wing
    painted(builder, (0.30, 0.48, 0.22), lambda: builder.box((-ix + 3.5, -iy + 3.5, 0.0), (ix - 3.5, iy - 3.5, 0.25), MATTE,
                                                             bottom=False))
    for k in range(10):
        x = -ix + 2.0 + k * (2 * ix - 4.0) / 9
        for y in (-iy + 2.0, iy - 2.0):
            frames.append(column_frame(x, y, 0.05, 0.55, 5.2))
    for k in range(1, 4):
        y = -iy + 2.0 + k * (2 * iy - 4.0) / 4
        for x in (-ix + 2.0, ix - 2.0):
            frames.append(column_frame(x, y, 0.05, 0.55, 5.2))
    first = len(builder.polygons)
    for x0, y0, x1, y1 in ((-ix, -iy, ix, -iy + 3.0), (-ix, iy - 3.0, ix, iy), (-ix, -iy + 3.0, -ix + 3.0, iy - 3.0),
                           (ix - 3.0, -iy + 3.0, ix, iy - 3.0)):
        builder.box((x0, y0, 5.25), (x1, y1, 5.9), MARBLE)
    builder.tint(first, (0.98, 0.95, 0.88))
    painted(builder, (0.30, 0.52, 0.66), lambda: builder.box((-4.0, -2.4, 0.0), (4.0, 2.4, 0.45), MARBLE, bottom=False))
    painted(builder, (0.20, 0.42, 0.56), lambda: builder.box((-3.7, -2.1, 0.45), (3.7, 2.1, 0.46), "pool", bottom=False))
    for k in range(8):
        tx = rng.uniform(-ix + 5.0, ix - 5.0)
        ty = rng.choice([-1, 1]) * rng.uniform(4.0, iy - 4.5)
        builder.merge(oleander(1.6 + rng.random(), seed + k), placement(tx, ty, 0.25))
    gate_x = 0.0
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((gate_x - 6.0, hy - 0.5, 0.0), (gate_x + 6.0, hy + 3.5, 1.0), MARBLE,
                                                             bottom=False))
    for x in (-4.5, -1.5, 1.5, 4.5):
        frames.append(column_frame(gate_x + x, hy + 2.6, 1.0, 0.7, 7.0))
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((gate_x - 6.0, hy + 1.6, 8.0), (gate_x + 6.0, hy + 3.6, 9.2), MARBLE))
    painted(builder, BLUE, lambda: builder.box((gate_x - 6.02, hy + 3.58, 8.3), (gate_x + 6.02, hy + 3.62, 8.9), MATTE,
                                               bottom=False, top=False))
    return builder, frames


def oleander(size=2.0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    first = len(builder.polygons)
    for k in range(5):
        centre = Vector((rng.uniform(-0.45, 0.45) * size, rng.uniform(-0.45, 0.45) * size, size * rng.uniform(0.35, 0.6)))
        ellipsoid(builder, centre, (size * 0.45, size * 0.42, size * 0.42), (0.22, 0.38, 0.18), 7, 4, MATTE)
    shade_crown(builder, first, (0.12, 0.24, 0.10), (0.34, 0.50, 0.24))
    blossom = rng.choice([(0.96, 0.42, 0.58), (0.98, 0.62, 0.70), (0.94, 0.94, 0.90), (0.90, 0.30, 0.42)])
    for k in range(14):
        angle = rng.uniform(0, TAU)
        tilt = rng.uniform(0.2, 1.3)
        p = Vector((math.cos(angle) * math.cos(tilt), math.sin(angle) * math.cos(tilt), math.sin(tilt)))
        centre = Vector((0.0, 0.0, size * 0.48)) + Vector((p.x * size * 0.62, p.y * size * 0.62, p.z * size * 0.45))
        ellipsoid(builder, centre, (0.16, 0.16, 0.12), blossom, 4, 2, MATTE)
    return builder


def olive(seed=0, height=5.5, detail=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    lean = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0.0))
    trunk_top = Vector((lean.x, lean.y, height * 0.38))
    tube(builder, [(0.0, 0.0, -0.4), (lean.x * 0.4 + 0.1, lean.y * 0.4, height * 0.18), trunk_top],
         [0.26, 0.2, 0.16], (0.36, 0.30, 0.24), 6)
    for k in range(3):
        angle = TAU * k / 3 + rng.uniform(-0.4, 0.4)
        end = trunk_top + Vector((math.cos(angle) * height * 0.22, math.sin(angle) * height * 0.22, height * 0.22))
        tube(builder, [trunk_top, end], [0.12, 0.07], (0.38, 0.32, 0.26), 5)
    first = len(builder.polygons)
    blob(builder, trunk_top + Vector((0.0, 0.0, height * 0.32)), height * 0.4, height * 0.36, seed, 9 if detail else 6, 0.2)
    for k in range(4 if detail else 2):
        angle = TAU * k / 4 + rng.uniform(-0.5, 0.5)
        offset = Vector((math.cos(angle), math.sin(angle), 0.0)) * height * 0.3
        blob(builder, trunk_top + offset + Vector((0.0, 0.0, height * rng.uniform(0.18, 0.4))), height * 0.24, height * 0.24,
             seed + k + 7, 7 if detail else 5, 0.2)
    shade_crown(builder, first, (0.22, 0.28, 0.17), (0.56, 0.62, 0.42))
    return builder


def maquis(seed=0, size=1.6, detail=True):
    rng = random.Random(seed)
    builder = MeshBuilder()
    first = len(builder.polygons)
    for k in range(4 if detail else 3):
        centre = (rng.uniform(-0.6, 0.6) * size, rng.uniform(-0.6, 0.6) * size, size * rng.uniform(0.2, 0.4))
        ellipsoid(builder, centre, (size * 0.6, size * 0.55, size * 0.42), (0.30, 0.36, 0.20), 6 if detail else 5, 3 if detail else 2,
                  MATTE)
    shade_crown(builder, first, (0.16, 0.22, 0.11), (0.44, 0.48, 0.26))
    return builder


def fountain_house(seed=7):
    builder = MeshBuilder()
    frames = []
    width, depth, height = 14.0, 7.0, 6.2
    hw = width / 2
    painted(builder, (0.94, 0.88, 0.78), lambda: builder.box((-hw - 1.0, -2.0, -8.0), (hw + 1.0, depth + 1.0, 0.0), STONE,
                                                             bottom=False))
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((-hw, 0.0, 0.0), (hw, depth, height), MARBLE, bottom=False))
    for k in range(4):
        x = -hw + 2.2 + k * (width - 4.4) / 3
        builder.oriented([(x - 1.1, -0.02, 0.6), (x + 1.1, -0.02, 0.6), (x + 1.1, -0.02, 3.8), (x - 1.1, -0.02, 3.8)],
                         (0, -1, 0), VOID)
    for k in range(5):
        x = -hw + 0.6 + k * (width - 1.2) / 4
        frames.append(column_frame(x, -1.0, 0.0, 0.55, 5.0))
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.box((-hw - 0.3, -1.6, 5.0), (hw + 0.3, 0.2, 5.8), MARBLE))
    painted(builder, RED, lambda: builder.box((-hw - 0.32, -1.62, 5.25), (hw + 0.32, -1.58, 5.55), MATTE, bottom=False,
                                              top=False))
    painted(builder, (0.98, 0.95, 0.88), lambda: builder.oriented([(-hw - 0.3, -1.6, 5.8), (hw + 0.3, -1.6, 5.8),
                                                                   (0.0, -1.6, 7.6)], (0, -1, 0), MARBLE))
    painted(builder, BLUE, lambda: builder.oriented([(-hw + 0.6, -1.62, 5.95), (hw - 0.6, -1.62, 5.95), (0.0, -1.62, 7.3)],
                                                    (0, -1, 0), MATTE))
    first = len(builder.polygons)
    builder.surface([[(-hw - 0.6, -1.7, 5.8), (hw + 0.6, -1.7, 5.8)], [(-hw - 0.6, depth / 2, 7.6), (hw + 0.6, depth / 2, 7.6)]],
                    TILES, facing=(0, -1, 1))
    builder.surface([[(-hw - 0.6, depth / 2, 7.6), (hw + 0.6, depth / 2, 7.6)], [(-hw - 0.6, depth + 0.4, height), (hw + 0.6, depth + 0.4, height)]],
                    TILES, facing=(0, 1, 1))
    builder.tint(first, (0.98, 0.62, 0.44))
    painted(builder, (0.96, 0.92, 0.84), lambda: builder.box((-hw + 0.5, -4.6, 0.0), (hw - 0.5, -1.6, 0.8), MARBLE, bottom=False))
    painted(builder, (0.10, 0.36, 0.44), lambda: builder.box((-hw + 0.8, -4.3, 0.8), (hw - 0.8, -1.9, 0.81), "pool", bottom=False))
    painted(builder, (0.98, 0.95, 0.90), lambda: builder.box((hw - 3.4, -0.06, 1.2), (hw - 0.5, 0.0, 3.4), MARBLE))
    for k in range(9):
        z = 1.45 + k * 0.22
        painted(builder, (0.30, 0.26, 0.24), lambda z=z: builder.box((hw - 3.2, -0.08, z), (hw - 0.7, -0.06, z + 0.06), MATTE,
                                                                    bottom=False, top=False))
    return builder, frames


def stele(height=2.4, width=0.9):
    builder = MeshBuilder()
    painted(builder, (0.92, 0.88, 0.80), lambda: builder.box((-0.75, -0.5, 0.0), (0.75, 0.5, 0.5), STONE, bottom=False))
    painted(builder, (0.99, 0.97, 0.93), lambda: builder.box((-width / 2, -0.14, 0.5), (width / 2, 0.14, 0.5 + height), MARBLE,
                                                             bottom=False))
    first = len(builder.polygons)
    builder.oriented([(-width / 2 - 0.05, -0.16, 0.5 + height), (width / 2 + 0.05, -0.16, 0.5 + height),
                      (0.0, -0.16, 0.5 + height + 0.35)], (0, -1, 0), MARBLE)
    builder.oriented([(-width / 2 - 0.05, 0.16, 0.5 + height), (width / 2 + 0.05, 0.16, 0.5 + height),
                      (0.0, 0.16, 0.5 + height + 0.35)], (0, 1, 0), MARBLE)
    builder.tint(first, (0.99, 0.97, 0.93))
    for k in range(14):
        z = 0.75 + k * (height - 0.5) / 14
        span = width * (0.38 if k % 5 else 0.3)
        painted(builder, (0.34, 0.28, 0.26), lambda z=z, span=span: builder.box((-span, -0.16, z), (span, -0.15, z + 0.045), MATTE,
                                                                               bottom=False, top=False))
    return builder


def wall_run(length, height=8.0, thickness=3.2, foot=-14.0):
    builder = MeshBuilder()
    painted(builder, (0.92, 0.84, 0.70), lambda: builder.box((0.0, -thickness / 2, foot), (length, thickness / 2, height), STONE,
                                                             bottom=False))
    count = max(int(length / 2.6), 1)
    for k in range(count):
        x = length * (k + 0.5) / count
        painted(builder, (0.92, 0.84, 0.70), lambda x=x: builder.box((x - 0.6, thickness / 2 - 0.6, height), (x + 0.6, thickness / 2, height + 1.2),
                                                                    STONE, bottom=False))
    return builder


def wall_tower(size=8.0, height=12.0, foot=-14.0):
    builder = MeshBuilder()
    h = size / 2
    painted(builder, (0.94, 0.86, 0.72), lambda: builder.box((-h, -h, foot), (h, h, height), STONE, bottom=False))
    painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-h - 0.3, -h - 0.3, height), (h + 0.3, h + 0.3, height + 0.5), STONE))
    first = len(builder.polygons)
    rise = 2.2
    corners = [(-h - 0.5, -h - 0.5), (h + 0.5, -h - 0.5), (h + 0.5, h + 0.5), (-h - 0.5, h + 0.5)]
    apex = builder.point((0.0, 0.0, height + 0.5 + rise))
    ring = builder.points([(x, y, height + 0.5) for x, y in corners])
    for k in range(4):
        builder.face([ring[k], ring[(k + 1) % 4], apex], TILES)
    builder.tint(first, (0.96, 0.60, 0.42))
    for k in range(4):
        angle = TAU * k / 4
        n = Vector((math.cos(angle), math.sin(angle), 0.0))
        side = Vector((-n.y, n.x, 0.0))
        c = n * (h + 0.02)
        builder.oriented([c - side * 0.4 + Vector((0, 0, height - 3.0)), c + side * 0.4 + Vector((0, 0, height - 3.0)),
                          c + side * 0.4 + Vector((0, 0, height - 1.6)), c - side * 0.4 + Vector((0, 0, height - 1.6))], n, VOID)
    return builder


def city_gate(width=7.0, depth=12.0, height=11.0):
    builder = MeshBuilder()
    for side in (-1, 1):
        builder.merge(wall_tower(10.0, height + 3.0), Matrix.Translation((side * (width / 2 + 5.0), 0.0, 0.0)))
    painted(builder, (0.94, 0.86, 0.72), lambda: builder.box((-width / 2, -depth / 2, 5.6), (width / 2, depth / 2, height), STONE))
    for y in (-depth / 2 - 0.02, depth / 2 + 0.02):
        n = -1 if y < 0 else 1
        builder.oriented([(-2.6, y, 0.0), (2.6, y, 0.0), (2.6, y, 5.6), (-2.6, y, 5.6)], (0, n, 0), VOID)
    return builder


def terrace_wall(length, height, foot=-10.0, thickness=1.6, cap=True):
    builder = MeshBuilder()
    painted(builder, (0.90, 0.83, 0.70), lambda: builder.box((0.0, -thickness / 2, foot), (length, thickness / 2, height), STONE,
                                                             bottom=False))
    if cap:
        painted(builder, (0.98, 0.94, 0.86), lambda: builder.box((-0.2, -thickness / 2 - 0.15, height),
                                                                 (length + 0.2, thickness / 2 + 0.15, height + 0.3), MARBLE))
    return builder


def propylon(width=14.0, depth=8.0, column_height=6.4):
    builder = MeshBuilder()
    frames = []
    hw, hd = width / 2, depth / 2
    for k in range(3):
        painted(builder, (0.96, 0.92, 0.84), lambda k=k: builder.box((-hw - 0.6 + k * 0.2, -hd - 1.2 + k * 0.4, -1.0 + k * 0.0),
                                                                    (hw + 0.6 - k * 0.2, hd + 1.2 - k * 0.4, 0.2 + k * 0.2), MARBLE,
                                                                    bottom=False))
    base = 0.6
    for y in (-hd + 0.4, hd - 0.4):
        for k in range(4):
            x = -hw + 1.0 + k * (width - 2.0) / 3
            frames.append(column_frame(x, y, base, 0.8, column_height))
    top = base + column_height
    painted(builder, WARM, lambda: builder.box((-hw - 0.3, -hd - 0.3, top), (hw + 0.3, hd + 0.3, top + 1.4), MARBLE))
    painted(builder, BLUE, lambda: builder.box((-hw - 0.32, -hd - 0.32, top + 0.6), (hw + 0.32, hd + 0.32, top + 1.0), MATTE,
                                               bottom=False, top=False))
    painted(builder, RED, lambda: builder.box((-hw - 0.34, -hd - 0.34, top + 1.2), (hw + 0.34, hd + 0.34, top + 1.32), MATTE,
                                              bottom=False, top=False))
    rise = 2.2
    first = len(builder.polygons)
    builder.surface([[(-hw - 0.5, -hd - 0.5, top + 1.4), (-hw - 0.5, hd + 0.5, top + 1.4)],
                     [(0.0, -hd - 0.5, top + 1.4 + rise), (0.0, hd + 0.5, top + 1.4 + rise)]], TILES, facing=(-1, 0, 1))
    builder.surface([[(0.0, -hd - 0.5, top + 1.4 + rise), (0.0, hd + 0.5, top + 1.4 + rise)],
                     [(hw + 0.5, -hd - 0.5, top + 1.4), (hw + 0.5, hd + 0.5, top + 1.4)]], TILES, facing=(1, 0, 1))
    builder.tint(first, (0.98, 0.62, 0.44))
    for y in (-hd - 0.3, hd + 0.3):
        n = -1 if y < 0 else 1
        painted(builder, WARM, lambda y=y, n=n: builder.oriented([(-hw - 0.3, y, top + 1.4), (hw + 0.3, y, top + 1.4),
                                                                  (0.0, y, top + 1.4 + rise)], (0, n, 0), MARBLE))
        painted(builder, BLUE, lambda y=y, n=n: builder.oriented([(-hw + 0.6, y + n * 0.02, top + 1.6), (hw - 0.6, y + n * 0.02, top + 1.6),
                                                                  (0.0, y + n * 0.02, top + 1.4 + rise - 0.3)], (0, n, 0), MATTE))
    return builder, frames


def quay(length, width=12.0, top=1.4, foot=-5.0):
    builder = MeshBuilder()
    painted(builder, (0.90, 0.84, 0.72), lambda: builder.box((0.0, -width, foot), (length, 0.0, top - 0.2), STONE, bottom=False,
                                                             top=False))
    painted(builder, (0.96, 0.92, 0.84), lambda: builder.box((-0.2, -width, top - 0.3), (length + 0.2, 0.25, top), PAVING,
                                                             bottom=False))
    for k in range(int(length / 9.0)):
        x = 4.5 + k * 9.0
        painted(builder, (0.70, 0.66, 0.58), lambda x=x: builder.box((x - 0.25, -0.6, top), (x + 0.25, -0.1, top + 0.55), STONE,
                                                                    bottom=False))
    return builder


def awning(width=5.0, depth=3.6, colours=((0.86, 0.20, 0.14), (0.96, 0.84, 0.50))):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    for k in range(6):
        x0 = -hw + width * k / 6
        x1 = -hw + width * (k + 1) / 6
        colour = colours[k % 2]
        quad = [(x0, -hd, 2.5), (x1, -hd, 2.5), (x1, hd, 3.0), (x0, hd, 3.0)]
        painted(builder, colour, lambda quad=quad: builder.oriented(quad, (0, -0.3, 1), MATTE))
        painted(builder, tuple(c * 0.75 for c in colour), lambda quad=quad: builder.oriented(list(reversed(quad)), (0, 0.3, -1), MATTE))
    for x in (-hw + 0.1, hw - 0.1):
        for y, z in ((-hd + 0.1, 2.5), (hd - 0.1, 3.0)):
            tube(builder, [(x, y, 0.0), (x, y, z)], [0.05, 0.05], WOOD, 4)
    painted(builder, (0.62, 0.48, 0.32), lambda: builder.box((-hw + 0.4, -0.5, 0.0), (hw - 0.4, 0.5, 0.85), MATTE, bottom=False))
    produce = [(0.86, 0.5, 0.16), (0.42, 0.62, 0.2), (0.7, 0.2, 0.18), (0.9, 0.82, 0.5), (0.5, 0.3, 0.5)]
    for k in range(5):
        x = -hw + 0.9 + k * (width - 1.8) / 4
        ellipsoid(builder, (x, 0.0, 0.92), (0.34, 0.3, 0.12), produce[k % 5], 6, 3, MATTE)
    return builder

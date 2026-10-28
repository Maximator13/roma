import math

from .ephese_artemision import ASHLAR, DEEP_BLUE, GILT, MARBLE, OCHRE, RED, TILES, VOID, WHITE, painted
from .geometry import MeshBuilder
from .nimes_figures import tube

PAVING = "paving"
BAYS = [(-6.65, 1.75, 4.6), (0.0, 2.5, 6.5), (6.65, 1.75, 4.6)]
HALF_WIDTH = 10.8
DEPTH = 6.0
TOP = 10.4
ATTIC = 12.4
TOWER = 9.0
TOWER_TOP = 16.0


def arch(cx, w, s, steps=12):
    return [(cx + w * math.cos(math.pi * (1 - k / steps)), s + w * math.sin(math.pi * (1 - k / steps)))
            for k in range(steps + 1)]


def gate_front(builder):
    edges = [-HALF_WIDTH]
    for cx, w, s in BAYS:
        edges += [cx - w, cx + w]
    edges.append(HALF_WIDTH)
    for x0, x1 in zip(edges[0::2], edges[1::2]):
        painted(builder, (0.97, 0.95, 0.90), lambda x0=x0, x1=x1: builder.box((x0, -DEPTH, -5.0), (x1, DEPTH, TOP),
                                                                             MARBLE, bottom=False, top=False))
    for cx, w, s in BAYS:
        curve = arch(cx, w, s)
        for y, facing in ((-DEPTH, -1), (DEPTH, 1)):
            outline = [(x, y, z) for x, z in curve] + [(cx + w, y, TOP), (cx - w, y, TOP)]
            painted(builder, (0.97, 0.95, 0.90), lambda outline=outline, facing=facing: builder.oriented(
                outline, (0, facing, 0), MARBLE))
            ring = [(x, y + facing * 0.02, z) for x, z in arch(cx, w + 0.45, s)]
            inner = [(x, y + facing * 0.02, z) for x, z in arch(cx, w, s)]
            painted(builder, WHITE, lambda ring=ring, inner=inner, facing=facing: builder.surface(
                [inner, ring], MARBLE, facing=(0, facing, 0)))
        rows = [[(x, -DEPTH, z) for x, z in curve], [(x, DEPTH, z) for x, z in curve]]
        painted(builder, (0.84, 0.82, 0.78), lambda rows=rows: builder.surface(rows, MARBLE, facing=(0, 0, -1)))
        painted(builder, (0.98, 0.95, 0.88), lambda cx=cx, w=w: builder.box((cx - w, -DEPTH - 3.0, -0.6),
                                                                           (cx + w, DEPTH + 3.0, 0.1), PAVING,
                                                                           bottom=False))
    for y, facing in ((-DEPTH, -1), (DEPTH, 1)):
        for x in (-9.6, -3.7, 3.7, 9.6):
            yy = y + facing * 0.35
            tube(builder, [(x, yy, 0.0), (x, yy, 0.6)], [0.62, 0.6], WHITE, 10, MARBLE)
            tube(builder, [(x, yy, 0.6), (x, yy, TOP - 1.2)], [0.42, 0.36], WHITE, 10, MARBLE)
            painted(builder, WHITE, lambda x=x, yy=yy: builder.box((x - 0.55, yy - 0.5, TOP - 1.2),
                                                                  (x + 0.55, yy + 0.5, TOP - 0.8), MARBLE))
        y0, y1 = sorted((y, y + facing * 0.9))
        painted(builder, WHITE, lambda y0=y0, y1=y1: builder.box((-HALF_WIDTH, y0, TOP - 0.8), (HALF_WIDTH, y1, TOP),
                                                                MARBLE, bottom=True))
        b0, b1 = sorted((y + facing * 0.9, y + facing * 0.92))
        painted(builder, RED, lambda b0=b0, b1=b1: builder.box((-HALF_WIDTH, b0, TOP - 0.55), (HALF_WIDTH, b1,
                                                                                               TOP - 0.3),
                                                              MARBLE, bottom=False, top=False))
    painted(builder, (0.98, 0.96, 0.92), lambda: builder.box((-HALF_WIDTH, -DEPTH, TOP), (HALF_WIDTH, DEPTH, ATTIC),
                                                             MARBLE, bottom=False))
    painted(builder, WHITE, lambda: builder.box((-HALF_WIDTH - 0.4, -DEPTH - 0.4, ATTIC),
                                               (HALF_WIDTH + 0.4, DEPTH + 0.4, ATTIC + 0.5), MARBLE))
    painted(builder, DEEP_BLUE, lambda: builder.box((-HALF_WIDTH - 0.42, -DEPTH - 0.42, ATTIC + 0.15),
                                                   (HALF_WIDTH + 0.42, DEPTH + 0.42, ATTIC + 0.3), MARBLE,
                                                   bottom=False, top=False))
    for y, facing in ((-DEPTH, -1), (DEPTH, 1)):
        for line, z in enumerate((TOP + 1.25, TOP + 0.55)):
            span = 7.5 - line * 1.5
            quad = [(-span, y + facing * 0.03, z), (span, y + facing * 0.03, z), (span, y + facing * 0.03, z + 0.4),
                    (-span, y + facing * 0.03, z + 0.4)]
            painted(builder, (0.98, 0.80, 0.40), lambda quad=quad, facing=facing: builder.oriented(
                quad, (0, facing, 0), GILT))


def tower(builder, side):
    x0, x1 = sorted((side * HALF_WIDTH, side * (HALF_WIDTH + TOWER)))
    painted(builder, (0.95, 0.90, 0.80), lambda: builder.box((x0, -DEPTH - 0.5, -8.0), (x1, DEPTH + 0.5, TOWER_TOP),
                                                             ASHLAR, bottom=False, top=False))
    painted(builder, WHITE, lambda: builder.box((x0 - 0.3, -DEPTH - 0.8, TOWER_TOP - 0.6),
                                               (x1 + 0.3, DEPTH + 0.8, TOWER_TOP), MARBLE, top=False))
    cx = (x0 + x1) / 2
    apex = (cx, 0.0, TOWER_TOP + 4.2)
    corners = [(x0 - 0.6, -DEPTH - 1.1, TOWER_TOP), (x1 + 0.6, -DEPTH - 1.1, TOWER_TOP),
               (x1 + 0.6, DEPTH + 1.1, TOWER_TOP), (x0 - 0.6, DEPTH + 1.1, TOWER_TOP)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        mid = ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2, 1.2)
        painted(builder, (0.86, 0.46, 0.32), lambda a=a, b=b, mid=mid: builder.oriented([a, b, apex], mid, TILES))
    for y, facing in ((-DEPTH - 0.5, -1), (DEPTH + 0.5, 1)):
        for k in range(2):
            wx = x0 + 2.4 + k * 4.2
            builder.oriented([(wx - 0.6, y + facing * 0.02, 10.6), (wx + 0.6, y + facing * 0.02, 10.6),
                              (wx + 0.6, y + facing * 0.02, 13.0), (wx - 0.6, y + facing * 0.02, 13.0)],
                             (0, facing, 0), VOID)
            painted(builder, OCHRE, lambda wx=wx, y=y, facing=facing: builder.oriented(
                [(wx - 0.8, y + facing * 0.01, 10.4), (wx + 0.8, y + facing * 0.01, 10.4),
                 (wx + 0.8, y + facing * 0.01, 10.6), (wx - 0.8, y + facing * 0.01, 10.6)], (0, facing, 0), MARBLE))


def magnesian_gate():
    builder = MeshBuilder()
    gate_front(builder)
    for side in (-1, 1):
        tower(builder, side)
    return builder

import math

from .colisee_monuments import UNIT
from .geometry import MeshBuilder
from .halicarnasse_mausoleum import painted

STONE = "limestone"
TONE = (0.92, 0.86, 0.74)


def fluted_outline(radius, flutes, depth, width, back):
    outline = [(-width, back), (-width, 0.0)]
    steps = flutes * 2
    for k in range(steps + 1):
        angle = math.pi + math.pi * k / steps
        r = radius if k % 2 == 0 else radius - depth
        outline.append((r * math.cos(angle), r * math.sin(angle)))
    outline += [(width, 0.0), (width, back)]
    return outline


def doric_half():
    builder = MeshBuilder()
    painted(builder, TONE, lambda: builder.box((-0.75, -0.62, 0.0), (0.75, 1.15, 0.22), STONE, bottom=False))
    shaft = fluted_outline(0.5, 10, 0.05, 0.65, 1.1)
    painted(builder, TONE, lambda: builder.prism(shaft, 0.22, UNIT * 0.87, STONE, top=False, bottom=False))
    echinus = [(x * 1.14, y * 1.14 if y < 0 else y) for x, y in fluted_outline(0.5, 8, 0.0, 0.65, 1.1)]
    painted(builder, TONE, lambda: builder.prism(echinus, UNIT * 0.87, UNIT * 0.93, STONE, top=False, bottom=False))
    painted(builder, (0.95, 0.90, 0.80), lambda: builder.box((-0.8, -0.66, UNIT * 0.93), (0.8, 1.15, UNIT), STONE, bottom=False))
    return builder

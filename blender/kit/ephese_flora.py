import math
import random

from mathutils import Vector

from .geometry import MATTE, MeshBuilder
from .pont_life import blob, tube

BARK = (0.42, 0.34, 0.26)
OLIVE_BARK = (0.46, 0.42, 0.36)


def branches(builder, rng, base, top, count, reach, lift, radius, colour):
    tips = []
    tube(builder, base, top, radius, radius * 0.7, colour, MATTE, 6, caps=False)
    for k in range(count):
        angle = 2 * math.pi * k / count + rng.uniform(-0.5, 0.5)
        tip = Vector(top) + Vector((math.cos(angle) * reach * rng.uniform(0.7, 1.1),
                                    math.sin(angle) * reach * rng.uniform(0.7, 1.1), lift * rng.uniform(0.7, 1.2)))
        tube(builder, top, tip, radius * 0.6, radius * 0.3, colour, MATTE, 5, caps=False)
        tips.append(tip)
    return tips


def clusters(builder, rng, tips, size, colour, flat, seed, centre=None):
    for k, tip in enumerate(tips + ([centre] if centre is not None else [])):
        tone = rng.uniform(0.82, 1.15)
        shade = tuple(min(c * tone, 1.0) for c in colour)
        scale = size * rng.uniform(0.8, 1.15)
        blob(builder, tuple(Vector(tip) + Vector((0.0, 0.0, scale * flat * 0.4))), (scale, scale, scale * flat),
             shade, MATTE, 9, 5, wobble=0.22, seed=seed * 13 + k)


def close_olive(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    lean = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0.0))
    top = Vector((0.0, 0.0, 1.5)) + lean
    tube(builder, (0.0, 0.0, -0.3), (lean.x * 0.4, lean.y * 0.4, 0.8), 0.32, 0.26, OLIVE_BARK, MATTE, 7, caps=False)
    tips = branches(builder, rng, (lean.x * 0.4, lean.y * 0.4, 0.8), tuple(top), 4, 1.5, 1.2, 0.22, OLIVE_BARK)
    clusters(builder, rng, tips, 1.25, (0.44, 0.49, 0.33), 0.62, seed, centre=top + Vector((0.0, 0.0, 1.6)))
    return builder


def close_pine(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    bend = Vector((rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), 0.0))
    middle = Vector((0.0, 0.0, 4.5)) + bend * 0.4
    top = Vector((0.0, 0.0, 8.4)) + bend
    tube(builder, (0.0, 0.0, -0.3), tuple(middle), 0.3, 0.24, BARK, MATTE, 6, caps=False)
    tips = branches(builder, rng, tuple(middle), tuple(top), 4, 2.6, 0.9, 0.2, BARK)
    clusters(builder, rng, tips, 2.2, (0.20, 0.32, 0.15), 0.42, seed, centre=top + Vector((0.0, 0.0, 1.1)))
    return builder


def close_plane(seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    top = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 5.5))
    tube(builder, (0.0, 0.0, -0.3), tuple(top * 0.5), 0.42, 0.36, (0.58, 0.54, 0.44), MATTE, 7, caps=False)
    tips = branches(builder, rng, tuple(top * 0.5), tuple(top), 5, 3.2, 3.0, 0.3, (0.58, 0.54, 0.44))
    clusters(builder, rng, tips, 2.7, (0.30, 0.46, 0.18), 0.75, seed, centre=top + Vector((0.0, 0.0, 4.4)))
    return builder

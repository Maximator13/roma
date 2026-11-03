from mathutils import Vector

from .cannes_figures import (BRONZE, HORSE_BAY, HORSE_DUN, IRON, LEATHER, MAIL, SHIELD_CENTER, SHIELD_HAND, SKIN,
                             WOOD, WOOL_RED, arms, blade, body, box, cavalry, flat_oval, head, horse, legs, montefortino,
                             quad_both, rider, scutum, shaft)
from .geometry import MATTE, MeshBuilder
from .nimes_figures import ellipsoid, tube

SCARLET = (0.66, 0.09, 0.07)
CHECK = (0.42, 0.34, 0.22)
GAUL_TUNIC = (0.52, 0.44, 0.30)
GAUL_SHIELD = (0.38, 0.40, 0.27)
FAIR_HAIR = (0.60, 0.44, 0.22)
GERMAN_TUNIC = (0.55, 0.50, 0.38)
SAGUM = (0.44, 0.24, 0.16)
DRESS = (0.58, 0.50, 0.38)
SHAWL = (0.36, 0.30, 0.24)
HORSE_GREY = (0.66, 0.62, 0.56)
ROMAN_SHIELD = (0.54, 0.28, 0.18)


def legionnaire():
    builder = MeshBuilder()
    legs(builder, SKIN)
    body(builder, WOOL_RED, MAIL, skirt_length=0.34)
    arms(builder, WOOL_RED, SKIN, (0.27, 0.3, 1.02), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN)
    montefortino(builder, (0.0, 0.0, 1.62), plumes=False)
    tube(builder, [(0.0, -0.01, 1.76), (0.0, -0.01, 1.81)], [0.02, 0.012], BRONZE, 4)
    scutum(builder, SHIELD_CENTER, ROMAN_SHIELD)
    box(builder, (0.24, 0.0, 0.86), (0.05, 0.08, 0.5), LEATHER)
    shaft(builder, (0.27, 0.2, 0.25), (0.27, 0.42, 1.55), 0.022, WOOD)
    shaft(builder, (0.27, 0.42, 1.55), (0.27, 0.52, 2.2), 0.009, IRON, 0.05)
    return builder


def german():
    builder = MeshBuilder()
    seat = horse(builder, 0.92, HORSE_BAY)
    shoulder = rider(builder, seat, GERMAN_TUNIC, GERMAN_TUNIC, SKIN, None, (0.0, 0.0),
                     lambda b, z: flat_oval(b, (-0.28, 0.32, z - 0.3), (0.45, 0.38, 0.25), 0.5, 0.85))
    shaft(builder, (0.27, -0.5, shoulder - 0.4), (0.27, 1.7, shoulder + 0.1), 0.017, WOOD, 0.22)
    return builder


def caesar():
    builder = MeshBuilder()
    seat = horse(builder, 1.0, HORSE_GREY, cloth=SCARLET)
    shoulder = rider(builder, seat, WOOL_RED, BRONZE, SKIN, None, (0.1, 0.25), lambda b, z: None)
    top = shoulder + 0.02
    for side in (-1, 1):
        quad_both(builder, [Vector((side * 0.02, -0.12, top)), Vector((side * 0.24, -0.1, top)),
                            Vector((side * 0.42, -0.42, seat - 0.35)), Vector((side * 0.02, -0.5, seat - 0.4))], SCARLET)
    quad_both(builder, [Vector((-0.24, -0.1, top)), Vector((0.24, -0.1, top)), Vector((0.2, 0.05, top + 0.05)),
                        Vector((-0.2, 0.05, top + 0.05))], SCARLET)
    return builder


def gaul_warrior():
    builder = MeshBuilder()
    legs(builder, SKIN, trousers=CHECK)
    body(builder, GAUL_TUNIC, GAUL_TUNIC, skirt_length=0.3)
    arms(builder, GAUL_TUNIC, SKIN, (0.27, 0.25, 1.1), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN, hair=FAIR_HAIR)
    tube(builder, [(-0.05, 0.1, 1.57), (0.0, 0.11, 1.56), (0.05, 0.1, 1.57)], [0.012, 0.015, 0.012], FAIR_HAIR, 3)
    flat_oval(builder, SHIELD_CENTER, GAUL_SHIELD, 0.58, 1.1)
    shaft(builder, (0.27, 0.1, 0.3), (0.27, 0.45, 2.3), 0.018, WOOD, 0.3)
    return builder


def gaul_noble():
    builder = MeshBuilder()
    legs(builder, SKIN, trousers=CHECK)
    body(builder, SAGUM, MAIL, skirt_length=0.32)
    arms(builder, MAIL, SKIN, (0.27, 0.32, 1.12), SHIELD_HAND)
    head(builder, (0.0, 0.0, 1.62), SKIN, hair=FAIR_HAIR)
    ellipsoid(builder, (0.0, -0.005, 1.67), (0.11, 0.12, 0.09), IRON, 7, 3)
    tube(builder, [(0.0, -0.18, 1.45), (0.0, -0.24, 0.9)], [0.18, 0.22], SAGUM, 6, cap=False, squash=0.4)
    flat_oval(builder, SHIELD_CENTER, (0.48, 0.36, 0.22), 0.58, 1.1)
    blade(builder, (0.27, 0.32, 1.12), 0.75, 0.03)
    return builder


def gaul_rider():
    builder = MeshBuilder()
    seat = horse(builder, 0.95, HORSE_DUN, cloth=SAGUM)
    shoulder = rider(builder, seat, CHECK, MAIL, SKIN, None, (0.0, 0.0),
                     lambda b, z: flat_oval(b, (-0.28, 0.32, z - 0.3), GAUL_SHIELD, 0.5, 0.9))
    ellipsoid(builder, (0.0, 0.025, seat + 0.73), (0.11, 0.12, 0.09), IRON, 7, 3)
    shaft(builder, (0.27, -0.5, shoulder - 0.4), (0.27, 1.8, shoulder + 0.1), 0.017, WOOD, 0.24)
    return builder


def archer():
    builder = MeshBuilder()
    legs(builder, SKIN, trousers=CHECK)
    body(builder, GERMAN_TUNIC, GERMAN_TUNIC, skirt_length=0.28)
    arms(builder, GERMAN_TUNIC, SKIN, (0.18, 0.15, 1.38), (-0.12, 0.55, 1.4))
    head(builder, (0.0, 0.0, 1.62), SKIN, hair=(0.32, 0.22, 0.12))
    tube(builder, [(-0.12, 0.52, 0.85), (-0.12, 0.62, 1.4), (-0.12, 0.52, 1.95)], [0.014, 0.016, 0.014], WOOD, 3)
    tube(builder, [(0.15, -0.16, 0.95), (0.18, -0.2, 1.45)], [0.06, 0.06], LEATHER, 5)
    return builder


def civilian():
    builder = MeshBuilder()
    tube(builder, [(0.0, 0.0, 0.02), (0.0, 0.0, 0.6), (0.0, 0.0, 1.0)], [0.27, 0.22, 0.18], DRESS, 7, squash=0.8)
    tube(builder, [(0.0, 0.0, 0.98), (0.0, 0.0, 1.2), (0.0, 0.01, 1.42)], [0.16, 0.17, 0.18], SHAWL, 7, squash=0.65)
    tube(builder, [(0.0, 0.0, 1.42), (0.0, 0.0, 1.5)], [0.05, 0.05], SKIN, 5, cap=False)
    arms(builder, SHAWL, SKIN, (0.12, 0.25, 1.05), (-0.12, 0.25, 1.05))
    head(builder, (0.0, 0.0, 1.58), SKIN, hair=(0.36, 0.24, 0.14))
    return builder


def army_block():
    builder = MeshBuilder()
    box(builder, (0.0, 0.0, 0.85), (28.0, 18.0, 1.7), (0.40, 0.33, 0.24))
    box(builder, (0.0, 8.4, 0.95), (28.4, 1.8, 1.9), (0.55, 0.46, 0.30))
    for k in range(9):
        x = -12.6 + k * 3.15
        box(builder, (x, 0.0, 2.9), (0.3, 16.0, 2.5), (0.36, 0.30, 0.24))
    return builder


def slab(builder, center, size, color):
    first = len(builder.polygons)
    builder.centered_box(center, size, MATTE, bottom=False)
    builder.tint(first, color)


def far_foot(lower, upper, shield=None, height=1.0):
    builder = MeshBuilder()
    slab(builder, (0.0, 0.0, 0.47 * height), (0.34, 0.24, 0.94 * height), lower)
    slab(builder, (0.0, 0.0, 0.94 * height + 0.42), (0.4, 0.26, 0.84), upper)
    if shield is not None:
        slab(builder, (-0.15, 0.25, 0.98), (0.58, 0.07, 1.05), shield)
    return builder


def far_rider(horse_color, rider_color, scale=1.0):
    s = scale
    builder = MeshBuilder()
    slab(builder, (0.0, 0.0, 1.12 * s), (0.5 * s, 1.7 * s, 0.62 * s), horse_color)
    slab(builder, (0.0, 0.0, 0.42 * s), (0.4 * s, 1.2 * s, 0.84 * s), horse_color)
    slab(builder, (0.0, 0.05, 1.43 * s + 0.6), (0.42, 0.32, 1.0), rider_color)
    return builder


TROOPS = {
    "legionnaire": (legionnaire, lambda: far_foot(WOOL_RED, MAIL, ROMAN_SHIELD)),
    "cavalier": (lambda: cavalry("cavalier"), lambda: far_rider(HORSE_DUN, MAIL)),
    "germain": (german, lambda: far_rider(HORSE_BAY, GERMAN_TUNIC, 0.92)),
    "cesar": (caesar, lambda: far_rider(HORSE_GREY, SCARLET)),
    "gaulois": (gaul_warrior, lambda: far_foot(CHECK, GAUL_TUNIC, GAUL_SHIELD)),
    "noble": (gaul_noble, lambda: far_foot(CHECK, MAIL, (0.48, 0.36, 0.22))),
    "cavalier-gaulois": (gaul_rider, lambda: far_rider(HORSE_DUN, CHECK, 0.95)),
    "archer": (archer, lambda: far_foot(CHECK, GERMAN_TUNIC)),
    "civil": (civilian, lambda: far_foot(DRESS, SHAWL)),
    "armee": (army_block, army_block),
}

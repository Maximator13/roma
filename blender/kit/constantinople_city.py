import random

from mathutils import Matrix

from .constantinople_sophia import WARM_WHITE, arch_outline, box, colonnade, facing_quad, tinted
from .geometry import MeshBuilder

PLASTERS = {
    "ochre": (0.86, 0.58, 0.30), "rose": (0.86, 0.50, 0.44), "cream": (0.94, 0.84, 0.62), "white": (0.93, 0.90, 0.83),
    "blue": (0.56, 0.70, 0.86), "red": (0.78, 0.36, 0.24), "yellow": (0.94, 0.75, 0.34), "sage": (0.64, 0.75, 0.54),
}
WOOD = (0.46, 0.31, 0.2)
SHUTTER = [(0.2, 0.36, 0.5), (0.3, 0.44, 0.26), (0.5, 0.24, 0.16), (0.36, 0.26, 0.18)]


def opening(builder, x, z, width, height, y, facing, arched=True, colour=(0.12, 0.1, 0.09)):
    outline = arch_outline(width, height, 4) if arched else [(-width / 2, 0.0), (width / 2, 0.0), (width / 2, height),
                                                             (-width / 2, height)]
    points = [(x + px, y, z + pz) for px, pz in outline]
    facing_quad(builder, points, (0, facing, 0), "matte", colour=colour)


def hip_roof(builder, hw, hd, z, rise, overhang=0.45):
    a, b = hw + overhang, hd + overhang
    ridge = max(a - b, 0.0)
    top = z + min(a, b) * rise
    corners = [(-a, -b, z - 0.1), (a, -b, z - 0.1), (a, b, z - 0.1), (-a, b, z - 0.1)]
    r0, r1 = (-ridge, 0.0, top), (ridge, 0.0, top)
    facing_quad(builder, [corners[0], corners[1], r1, r0], (0, -1, 1), "terracotta_tiles")
    facing_quad(builder, [corners[2], corners[3], r0, r1], (0, 1, 1), "terracotta_tiles")
    facing_quad(builder, [corners[1], corners[2], r1], (1, 0, 1), "terracotta_tiles")
    facing_quad(builder, [corners[3], corners[0], r0], (-1, 0, 1), "terracotta_tiles")


def gable_roof(builder, hw, hd, z, rise, wall, colour, overhang=0.45):
    a, b = hw + overhang, hd + overhang
    top = z + hd * rise
    for side in (1, -1):
        facing_quad(builder, [(-a, side * b, z - 0.1), (a, side * b, z - 0.1), (a, 0.0, top), (-a, 0.0, top)], (0, side, 1),
                    "terracotta_tiles")
        facing_quad(builder, [(side * hw, -hd, z), (side * hw, hd, z), (side * hw, 0.0, top)], (side, 0, 0), wall,
                    colour=colour)


def balcony(builder, x0, x1, z, depth=1.2, front=-1):
    y0 = front * 0.0
    y1 = front * depth
    tinted(builder, WOOD, lambda: builder.box((x0, min(y0, y1), z - 0.15), (x1, max(y0, y1), z), "matte"))
    tinted(builder, (0.52, 0.38, 0.26), lambda: builder.box((x0, min(y1, y1 - front * 0.06), z), (x1, max(y1, y1 - front * 0.06),
                                                                                                 z + 1.0), "matte",
                                                            bottom=False))
    for x in (x0 + 0.2, (x0 + x1) / 2, x1 - 0.2):
        tinted(builder, WOOD, lambda x=x: builder.box((x - 0.07, min(0.0, y1 * 0.8), z - 1.0), (x + 0.07, max(0.0, y1 * 0.8), z - 0.15),
                                                      "matte"))
    facing_quad(builder, [(x0 - 0.1, y1 * 1.05, z + 2.4), (x1 + 0.1, y1 * 1.05, z + 2.4), (x1 + 0.1, 0.0, z + 2.8),
                          (x0 - 0.1, 0.0, z + 2.8)], (0, front, 1), "terracotta_tiles")


def townhouse(width, depth, floors, plaster, roof="hip", balcony_floor=None, shops=0, seed=0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    colour = PLASTERS[plaster]
    hw, hd = width / 2, depth / 2
    storey = 3.3
    height = floors * storey
    box(builder, (-hw, -hd, -4.0), (hw, hd, height), "plaster", colour)
    box(builder, (-hw - 0.05, -hd - 0.05, -4.0), (hw + 0.05, hd + 0.05, 0.5), "plaster",
        tuple(c * 0.78 for c in colour))
    if roof == "hip":
        hip_roof(builder, hw, hd, height, 0.42)
    else:
        gable_roof(builder, hw, hd, height, 0.45, "plaster", colour)
    front = -hd - 0.03
    if shops:
        for k in range(shops):
            x = -hw + width * (k + 0.5) / shops
            opening(builder, x, 0.0, min(2.4, width / shops - 0.8), 2.7, front, -1, arched=True)
            tinted(builder, rng.choice([(0.8, 0.3, 0.2), (0.2, 0.4, 0.6), (0.86, 0.7, 0.3), (0.3, 0.5, 0.3)]),
                   lambda x=x: builder.box((x - 1.1, -hd - 1.2, 2.6), (x + 1.1, -hd, 2.7), "matte"))
    else:
        opening(builder, rng.uniform(-hw * 0.4, hw * 0.4), 0.0, 1.3, 2.4, front, -1, arched=True)
    shutter = rng.choice(SHUTTER)
    for floor in range(1, floors):
        count = max(int(width / 3.2), 1)
        for k in range(count):
            x = -hw + width * (k + 0.5) / count
            z = floor * storey + 0.9
            opening(builder, x, z, 0.8, 1.5, front, -1)
            facing_quad(builder, [(x - 0.75, front - 0.02, z), (x - 0.42, front - 0.02, z), (x - 0.42, front - 0.02, z + 1.2),
                                  (x - 0.75, front - 0.02, z + 1.2)], (0, -1, 0), "matte", colour=shutter)
            opening(builder, x, z, 0.8, 1.5, hd + 0.03, 1)
    for side in (1, -1):
        for floor in range(1, floors):
            facing_quad(builder, [(side * (hw + 0.03), -0.4, floor * storey + 0.9), (side * (hw + 0.03), 0.4, floor * storey + 0.9),
                                  (side * (hw + 0.03), 0.4, floor * storey + 2.2), (side * (hw + 0.03), -0.4, floor * storey + 2.2)],
                        (side, 0, 0), "matte", colour=(0.12, 0.1, 0.09))
    if balcony_floor is not None and balcony_floor < floors:
        balcony(builder, -hw + 0.6, hw - 0.6, balcony_floor * storey, 1.2, -1)
    return builder


def court_house(width, depth, plaster, seed=0):
    builder = MeshBuilder()
    colour = PLASTERS[plaster]
    hw, hd = width / 2, depth / 2
    wing = 5.0
    height = 6.6
    for (x0, y0), (x1, y1) in (((-hw, -hd), (hw, -hd + wing)), ((-hw, hd - wing), (hw, hd)),
                               ((-hw, -hd + wing), (-hw + wing, hd - wing)), ((hw - wing, -hd + wing), (hw, hd - wing))):
        box(builder, (x0, y0, -4.0), (x1, y1, height), "plaster", colour)
    for (x0, y0), (x1, y1), axis in (((-hw - 0.4, -hd - 0.4), (hw + 0.4, -hd + wing), "y"),
                                     ((-hw - 0.4, hd - wing), (hw + 0.4, hd + 0.4), "y"),
                                     ((-hw - 0.4, -hd + wing), (-hw + wing, hd - wing), "x"),
                                     ((hw - wing, -hd + wing), (hw + 0.4, hd - wing), "x")):
        if axis == "y":
            mid = (y0 + y1) / 2
            for edge in (y0, y1):
                facing_quad(builder, [(x0, edge, height), (x1, edge, height), (x1, mid, height + 1.6), (x0, mid, height + 1.6)],
                            (0, edge - mid, 1), "terracotta_tiles")
        else:
            mid = (x0 + x1) / 2
            for edge in (x0, x1):
                facing_quad(builder, [(edge, y0, height), (edge, y1, height), (mid, y1, height + 1.6), (mid, y0, height + 1.6)],
                            (edge - mid, 0, 1), "terracotta_tiles")
    cw, cd = hw - wing, hd - wing
    facing_quad(builder, [(-cw, -cd, 0.05), (cw, -cd, 0.05), (cw, cd, 0.05), (-cw, cd, 0.05)], (0, 0, 1), "matte",
                colour=(0.36, 0.56, 0.2))
    tinted(builder, (0.24, 0.42, 0.14), lambda: builder.lathe([(0.0, 0.0), (1.4, 0.8), (1.6, 2.2), (1.0, 3.2), (0.0, 3.6)], 7,
                                                             "matte", smooth=True))
    opening(builder, 0.0, 0.0, 1.5, 2.6, -hd - 0.03, -1)
    for k in range(4):
        x = -hw + width * (k + 0.5) / 4
        opening(builder, x, 3.9, 0.7, 1.3, -hd - 0.03, -1)
        opening(builder, x, 3.9, 0.7, 1.3, hd + 0.03, 1)
    return builder


def portico_bay(plaster, seed=0, length=4.2, depth=6.5, upper=2, back=9.0):
    rng = random.Random(seed)
    builder = MeshBuilder()
    colour = PLASTERS[plaster]
    height = 6.2
    box(builder, (0.0, 0.0, -1.5), (length, depth, 0.25), "travertine", (0.86, 0.8, 0.72))
    colonnade(builder, (0.0, 0.6), (length * 2, 0.6), 1, height - 0.6, 0.5, 0.25, WARM_WHITE, style="impost")
    box(builder, (0.0, 0.2, height - 0.35), (length, 1.0, height), "marble_white", WARM_WHITE, bottom=True)
    facing_quad(builder, [(-0.25, -0.3, height), (length + 0.25, -0.3, height), (length + 0.25, depth, height + 1.5),
                          (-0.25, depth, height + 1.5)],
                (0, -0.4, 1), "terracotta_tiles")
    facing_quad(builder, [(0.0, -0.3, height - 0.05), (length, -0.3, height - 0.05), (length, depth, height + 1.45),
                          (0.0, depth, height + 1.45)], (0, 0.4, -1), "plaster", colour=(0.84, 0.78, 0.68))
    top = height + 1.6 + upper * 3.3
    tinted(builder, colour, lambda: builder.box((0.0, depth, -4.0), (length, depth + back, top), "plaster", top=False))
    tinted(builder, tuple(c * 0.72 for c in colour), lambda: builder.box((-0.02, depth - 0.04, -1.5),
                                                                       (length + 0.02, depth + 0.02, 0.9), "plaster",
                                                                       top=False, bottom=False))
    opening(builder, length / 2, 0.25, 2.6, 2.8, depth - 0.06, -1, arched=True, colour=(0.18, 0.13, 0.1))
    awning = rng.choice([(0.8, 0.18, 0.12), (0.12, 0.34, 0.68), (0.94, 0.7, 0.18), (0.18, 0.5, 0.26), (0.62, 0.16, 0.36)])
    rows = [[(0.3, depth - 0.07, 3.3), (length - 0.3, depth - 0.07, 3.3)], [(0.3, depth - 1.3, 2.6), (length - 0.3, depth - 1.3, 2.6)]]
    for side in (1, -1):
        facing_quad(builder, [rows[0][0], rows[0][1], rows[1][1], rows[1][0]], (0, -1, side), "matte",
                    colour=awning if side > 0 else tuple(c * 0.75 for c in awning))
    tinted(builder, (0.5, 0.36, 0.24), lambda: builder.box((0.5, depth - 1.0, 0.25), (length - 0.5, depth - 0.4, 1.15), "matte"))
    goods = rng.choice([[(0.75, 0.42, 0.26), (0.62, 0.2, 0.14)], [(0.86, 0.72, 0.3), (0.46, 0.6, 0.22)],
                        [(0.3, 0.3, 0.62), (0.7, 0.18, 0.3)], [(0.92, 0.88, 0.78), (0.55, 0.4, 0.25)]])
    for k in range(5):
        x = 0.9 + k * (length - 1.8) / 4
        tinted(builder, goods[k % 2], lambda x=x: builder.lathe([(0.0, 1.15), (0.16, 1.2), (0.18, 1.38), (0.0, 1.45)], 6,
                                                                "matte", smooth=True,
                                                                matrix=Matrix.Translation((x, depth - 0.7, 0.0))))
    shutter = rng.choice(SHUTTER)
    for floor in range(upper):
        z = height + 1.9 + floor * 3.3
        opening(builder, length / 2, z, 0.9, 1.6, depth - 0.03, -1)
        facing_quad(builder, [(length / 2 - 0.95, depth - 0.05, z), (length / 2 - 0.5, depth - 0.05, z),
                              (length / 2 - 0.5, depth - 0.05, z + 1.3), (length / 2 - 0.95, depth - 0.05, z + 1.3)],
                    (0, -1, 0), "matte", colour=shutter)
        opening(builder, length / 2, z, 0.9, 1.6, depth + back + 0.03, 1)
    ridge = depth + back / 2
    rise = back / 2 * 0.42
    for y_eave, sign in ((depth - 0.5, -1), (depth + back + 0.5, 1)):
        facing_quad(builder, [(-0.02, y_eave, top - 0.1), (length + 0.02, y_eave, top - 0.1), (length + 0.02, ridge, top + rise),
                              (-0.02, ridge, top + rise)], (0, sign, 1), "terracotta_tiles")
        y_wall = depth if sign < 0 else depth + back
        facing_quad(builder, [(0.0, y_eave, top - 0.12), (length, y_eave, top - 0.12), (length, y_wall, top - 0.12),
                              (0.0, y_wall, top - 0.12)], (0, 0, -1), "plaster", colour=tuple(c * 0.8 for c in colour))
    for x, sign in ((0.0, -1), (length, 1)):
        facing_quad(builder, [(x, depth, top), (x, depth + back, top), (x, ridge, top + rise)], (sign, 0, 0), "plaster",
                    colour=colour)
    return builder


HOUSES = {
    "house_a": lambda: townhouse(10.0, 8.0, 2, "ochre", "gable", None, 1, 1),
    "house_b": lambda: townhouse(12.0, 9.0, 3, "cream", "hip", 2, 0, 2),
    "house_c": lambda: townhouse(8.0, 7.0, 2, "rose", "gable", 1, 0, 3),
    "house_d": lambda: townhouse(14.0, 10.0, 3, "white", "hip", None, 2, 4),
    "house_e": lambda: court_house(20.0, 18.0, "blue", 5),
    "house_f": lambda: townhouse(9.0, 12.0, 2, "red", "gable", None, 2, 6),
    "house_g": lambda: townhouse(16.0, 12.0, 4, "yellow", "hip", 2, 3, 7),
    "house_h": lambda: court_house(18.0, 16.0, "cream", 8),
    "house_i": lambda: townhouse(11.0, 9.0, 3, "sage", "hip", 1, 1, 9),
}
FOOTPRINTS = {"house_a": (10.0, 8.0), "house_b": (12.0, 9.0), "house_c": (8.0, 7.0), "house_d": (14.0, 10.0),
              "house_e": (20.0, 18.0), "house_f": (9.0, 12.0), "house_g": (16.0, 12.0), "house_h": (18.0, 16.0),
              "house_i": (11.0, 9.0)}


def far_block(width, depth, height, plaster):
    builder = MeshBuilder()
    colour = PLASTERS[plaster]
    box(builder, (-width / 2, -depth / 2, -3.0), (width / 2, depth / 2, height), "plaster", colour)
    hip_roof(builder, width / 2, depth / 2, height, 0.4, 0.3)
    return builder


FAR_HOUSES = {
    "far_a": lambda: far_block(12.0, 9.0, 6.0, "cream"),
    "far_b": lambda: far_block(9.0, 8.0, 5.0, "ochre"),
    "far_c": lambda: far_block(14.0, 10.0, 7.0, "white"),
    "far_d": lambda: far_block(10.0, 10.0, 5.5, "rose"),
}


FAR_FOOTPRINTS = {"far_a": (12.0, 9.0), "far_b": (9.0, 8.0), "far_c": (14.0, 10.0), "far_d": (10.0, 10.0)}

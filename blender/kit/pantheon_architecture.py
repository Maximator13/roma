import math

from mathutils import Matrix, Vector

from .buildings import arched_wall
from .geometry import MeshBuilder, placement, rotation_toward
from .orders import (CAPITAL_HEIGHT, SHAFT_TOP_RATIO, attic_base, corinthian_capital, corinthian_entablature_profile,
                     facing_text_matrix, gable_roof, inscription, pilaster, raking_cornice_profile, shaft, tile_roof)

R = 21.65
WALL = 6.2
RO = R + WALL
SPRING = R
OCULUS = 4.46
OCULUS_HEIGHT = 2 * R
HALF_OPENING = 4.45
ALPHA = math.asin(HALF_OPENING / R)
CHORD = R * math.cos(ALPHA)
ORDER_TOP = 10.7
ENTABLATURE_TOP = 13.0
ATTIC_TOP = 20.9
PIAZZA = -1.4
BLOCK_FRONT = 31.5
BLOCK_SLAB = 30.3
BLOCK_HALF = 17.5
BLOCK_TOP = 23.2
DOOR_HALF = 2.45
DOOR_HEIGHT = 7.53
LINTEL_TOP = 8.25
PORCH_HALF = 16.9
PORCH_EDGE = 45.3
STEP_RISE = 0.2
STEP_TREAD = 0.3
PORCH_D = 1.48
PORCH_COLUMN = 15.05
PORCH_SPACING = 4.45
FRONT_X = [PORCH_SPACING * (index - 3.5) for index in range(8)]
INNER_X = [FRONT_X[0], FRONT_X[2], FRONT_X[5], FRONT_X[7]]
ROWS = (43.6, 38.9, 34.2)
ENTABLATURE_HEIGHT = 2.5 * PORCH_D
CORNICE_TOP = PORCH_COLUMN + ENTABLATURE_HEIGHT
SLOPE = math.radians(23.0)
INNER_D = 1.05
NICHE_COLUMN_X = 1.65
PLAZA_HALF = 30.0
PLAZA_SOUTH = 10.0
PLAZA_NORTH = 163.5
PORTICO_FLOOR = PIAZZA + 5 * STEP_RISE
PORTICO_EDGE = PLAZA_HALF + 4 * STEP_TREAD
PORTICO_BACK = 38.0
PORTICO_COLUMN = 8.5
PORTICO_D = 0.9
PORTICO_SPACING = 3.6
PORTICO_LINE = PLAZA_HALF + 2.25
INSCRIPTION = "M·AGRIPPA·L·F·COS·TERTIVM·FECIT"
BAY_TOP = 11.84
APSE_EXTENSION = 1.4
APSE_COLUMN_X = HALF_OPENING - 0.6
COLUMN_RADIUS = R - 0.5
ENTRANCE_CUT = ALPHA
APSE_CUT = math.asin((HALF_OPENING - 1.25) / R)
PILASTER_DEPTH = 0.45


def polar(radius, angle, z=0.0):
    return Vector((radius * math.sin(angle), radius * math.cos(angle), z))


def inward_frame(angle, radius, z=0.0):
    point = polar(radius, angle, z)
    return placement(point.x, point.y, z, math.pi - angle)


def arc_lathe(builder, profile, a0, a1, segments, material, smooth=True):
    builder.lathe(profile, segments, material, smooth=smooth, start=math.pi / 2 - a1, sweep=a1 - a0, caps=False)


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def beam(builder, start, end, width, depth, material):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    frame = rotation_toward(direction)
    frame.translation = start
    builder.box((-width / 2, 0.0, -depth / 2), (width / 2, direction.length, depth / 2), material, matrix=frame)


def roman_column(diameter, height, shaft_material, trim_material="marble_white", flutes=0, detail="high", segments=24):
    builder = MeshBuilder()
    attic_base(builder, diameter, segments, trim_material)
    capital_bottom = height - CAPITAL_HEIGHT["corinthian"] * diameter
    shaft(builder, diameter, 0.5 * diameter, capital_bottom, SHAFT_TOP_RATIO["corinthian"],
          flutes * 3 if flutes else segments, shaft_material, flutes)
    corinthian_capital(builder, diameter, capital_bottom, trim_material, detail)
    return builder


def quad(builder, corners, hint, material, colour=None):
    first = len(builder.polygons)
    builder.oriented([Vector(corner) for corner in corners], Vector(hint), material)
    if colour is not None:
        builder.tint(first, colour)


def vertical_strip(builder, points, z0, z1, target, material, colour=None):
    for start, end in zip(points[:-1], points[1:]):
        middle = (start + end) / 2
        hint = Vector((target.x - middle.x, target.y - middle.y, 0.0))
        quad(builder, [(start.x, start.y, z0), (end.x, end.y, z0), (end.x, end.y, z1), (start.x, start.y, z1)], hint,
             material, colour)


def levels(z0, z1, step=1.25):
    count = max(int(math.ceil((z1 - z0) / step)), 1)
    return [z0 + (z1 - z0) * k / count for k in range(count + 1)]


def banded_strip(builder, points, z0, z1, target, material, colour=None):
    heights = levels(z0, z1)
    for low, high in zip(heights[:-1], heights[1:]):
        vertical_strip(builder, points, low, high, target, material, colour)


def bay_point(normal, tangent, t, s, z):
    return tangent * t + normal * s + Vector((0.0, 0.0, z))


def barrel(builder, normal, tangent, end, steps=14, pieces=4):
    for k in range(steps):
        corners = []
        for psi in (math.pi * k / steps, math.pi * (k + 1) / steps):
            t = HALF_OPENING * math.cos(psi)
            corners.append((t, ENTABLATURE_TOP + HALF_OPENING * math.sin(psi), math.sqrt(R * R - t * t)))
        for piece in range(pieces):
            a = [bay_point(normal, tangent, t, start + (end - start) * piece / pieces, z) for t, z, start in corners]
            b = [bay_point(normal, tangent, t, start + (end - start) * (piece + 1) / pieces, z) for t, z, start in corners]
            middle = (a[0] + a[1] + b[0] + b[1]) / 4
            axis_point = normal * normal.dot(middle) + Vector((0.0, 0.0, ENTABLATURE_TOP))
            quad(builder, [a[0], a[1], b[1], b[0]], axis_point - middle, "stucco", (0.88, 0.87, 0.85))


def semidome(builder, normal, tangent, base, rows=6, columns=14):
    centre = normal * base + Vector((0.0, 0.0, ENTABLATURE_TOP))
    for row in range(rows):
        e0, e1 = math.pi / 2 * row / rows, math.pi / 2 * (row + 1) / rows
        for column in range(columns):
            p0 = math.pi * column / columns - math.pi / 2
            p1 = math.pi * (column + 1) / columns - math.pi / 2
            points = [centre + HALF_OPENING * (math.cos(e) * (tangent * math.sin(p) + normal * math.cos(p))
                                               + Vector((0.0, 0.0, math.sin(e))))
                      for p, e in ((p0, e0), (p1, e0), (p1, e1), (p0, e1))]
            quad(builder, points, centre - sum(points, Vector()) / 4, "stucco", (0.86, 0.85, 0.83))


def opening(walls, floor, index, columns, statues):
    angle = math.radians(45 * index)
    normal = Vector((math.sin(angle), math.cos(angle), 0.0))
    tangent = Vector((math.cos(angle), -math.sin(angle), 0.0))
    centre = normal * CHORD
    left = centre - tangent * HALF_OPENING
    right = centre + tangent * HALF_OPENING
    arc = [polar(R, angle - ALPHA + 2 * ALPHA * step / 8) for step in range(9)]
    extension = 0.0
    if index == 0:
        reach = BLOCK_FRONT - CHORD
        outline = [left, left + normal * (BLOCK_SLAB - CHORD), right + normal * (BLOCK_SLAB - CHORD), right]
        floor_outline = [left + normal * reach, right + normal * reach]
        depth = BLOCK_SLAB - CHORD
    elif index % 2:
        depth = 3.6
        outline = [left, left + normal * depth, right + normal * depth, right]
        floor_outline = outline[1:3]
    else:
        extension = APSE_EXTENSION if index == 4 else 0.0
        depth = extension + HALF_OPENING
        curve = [centre + normal * extension + tangent * HALF_OPENING * math.sin(psi) + normal * HALF_OPENING * math.cos(psi)
                 for psi in (math.radians(-90 + 180 * step / 14) for step in range(1, 14))]
        outline = [left] + ([left + normal * extension] if extension else []) + curve + (
            [right + normal * extension] if extension else []) + [right]
        floor_outline = outline[1:-1]
    target = centre + normal * (depth * 0.5)
    wall_material = "marble_white" if index == 0 else "pavonazzetto"
    strips = [outline[:2], outline[2:]] if index == 0 else [outline]
    top = ENTABLATURE_TOP if index in (0, 4) else ORDER_TOP + 0.02
    for strip in strips:
        vertical_strip(walls, strip, 0.0, 1.08, target, "giallo", (0.86, 0.86, 0.86))
        banded_strip(walls, strip, 1.08, top, target, wall_material, (0.84, 0.84, 0.84))
    if index == 0:
        barrel(walls, normal, tangent, BLOCK_SLAB)
    elif index == 4:
        barrel(walls, normal, tangent, CHORD + extension, pieces=1)
        semidome(walls, normal, tangent, CHORD + extension)
    else:
        quad(walls, [(point.x, point.y, ORDER_TOP + 0.02) for point in outline], (0, 0, -1), "stucco",
             (0.7, 0.69, 0.67))
    floor.oriented(arc + list(reversed(floor_outline)), (0, 0, 1), "floor_sectile")
    if index == 0:
        return
    kind = "pavonazzetto" if index == 4 else "giallo"
    offset = APSE_COLUMN_X if index == 4 else NICHE_COLUMN_X
    for side in (-1, 1):
        point = polar(COLUMN_RADIUS, angle + side * math.asin(offset / R))
        columns[kind].append(placement(point.x, point.y, 0.0, -angle))
    spot = centre + normal * (depth * (0.62 if index % 2 else 0.58))
    frame = placement(spot.x, spot.y, 0.0, math.pi - angle)
    walls.box((-0.85, -0.85, 0.0), (0.85, 0.85, 1.5), "marble_white", matrix=frame)
    walls.box((-0.95, -0.95, 1.5), (0.95, 0.95, 1.62), "marble_white", matrix=frame)
    statues.append(placement(spot.x, spot.y, 1.62, math.pi - angle))


def pier(walls, centre):
    beta = math.radians(22.5) - ALPHA
    a0, a1 = centre - beta, centre + beta
    arc_lathe(walls, [(R, 1.08), (R - 0.07, 1.08), (R - 0.07, 0.0)], a0, a1, 6, "giallo")
    arc_lathe(walls, [(R, z) for z in reversed(levels(1.08, ORDER_TOP))], a0, a1, 6, "pavonazzetto")
    for side in (-1, 1):
        edge = centre + side * (beta - 0.55 / R)
        walls.merge(fluted_pilaster(1.0, ORDER_TOP, PILASTER_DEPTH, "giallo"), inward_frame(edge, R))
    for side in (-1, 1):
        spot = centre + side * (beta - 1.65 / R)
        frame = inward_frame(spot, R)
        walls.box((-0.42, 0.0, 6.9), (0.42, 0.05, 8.7), "porphyry", matrix=frame)
        walls.box((-0.5, 0.0, 2.2), (0.5, 0.04, 6.2), "giallo", matrix=frame)


def fluted_pilaster(width, height, depth, material, trim="marble_white", flutes=7):
    builder = MeshBuilder()
    w = width
    builder.box((-0.62 * w, 0.0, 0.0), (0.62 * w, depth + 0.12 * w, 0.18 * w), trim, bottom=False)
    builder.box((-0.56 * w, 0.0, 0.18 * w), (0.56 * w, depth + 0.07 * w, 0.32 * w), trim, bottom=False)
    capital_bottom = height - CAPITAL_HEIGHT["corinthian"] * w
    builder.box((-0.5 * w, 0.0, 0.32 * w), (0.5 * w, depth, capital_bottom), material, bottom=False, top=False)
    for k in range(1, flutes):
        x = -0.5 * w + w * k / flutes
        builder.box((x - 0.018 * w, depth - 0.01, 0.42 * w), (x + 0.018 * w, depth + 0.025 * w, capital_bottom - 0.12 * w),
                    material, bottom=False, top=False)
    capital = MeshBuilder()
    corinthian_capital(capital, 0.95 * w, 0.0, trim, "medium", arc=(0.0, math.pi))
    builder.merge(capital, placement(0.0, max(depth - 0.4 * w, 0.0), capital_bottom))
    return builder


def aedicula(segmental, column_material):
    builder = MeshBuilder()
    builder.box((-2.1, 0.0, 0.0), (2.1, 1.25, 1.55), "marble_white", bottom=False)
    builder.box((-1.6, 1.25, 0.35), (1.6, 1.29, 1.25), "porphyry", bottom=False)
    builder.box((-2.2, 0.0, 1.55), (2.2, 1.36, 1.7), "marble_white")
    painted(builder, (0.8, 0.8, 0.8), lambda: builder.box((-1.15, 0.0, 1.7), (1.15, 0.1, 6.2), "pavonazzetto",
                                                         bottom=False))
    for x in (-1.5, 1.5):
        builder.merge(roman_column(0.46, 4.5, column_material, "marble_white", 0, "medium", 12),
                      placement(x, 0.85, 1.7))
    builder.box((-2.1, 0.0, 6.2), (2.1, 1.3, 6.9), "marble_white")
    builder.box((-2.25, 0.0, 6.9), (2.25, 1.45, 7.12), "marble_white")
    if segmental:
        arc = [(-2.25 * math.cos(math.pi * step / 10), 7.12 + 0.75 * math.sin(math.pi * step / 10)) for step in range(11)]
        builder.oriented([Vector((x, 1.45, z)) for x, z in arc], (0, 1, 0), "marble_white")
        for (x0, z0), (x1, z1) in zip(arc[:-1], arc[1:]):
            quad(builder, [(x0, 0.0, z0), (x1, 0.0, z1), (x1, 1.45, z1), (x0, 1.45, z0)],
                 ((x0 + x1) / 2, 0.0, (z0 + z1) / 2 - 6.4), "marble_white")
    else:
        apex = 7.12 + 2.25 * math.tan(SLOPE)
        builder.oriented([Vector((-2.25, 1.45, 7.12)), Vector((2.25, 1.45, 7.12)), Vector((0.0, 1.45, apex))], (0, 1, 0),
                         "marble_white")
        for side in (-1, 1):
            quad(builder, [(side * 2.25, 0.0, 7.12), (0.0, 0.0, apex), (0.0, 1.45, apex), (side * 2.25, 1.45, 7.12)],
                 (side * math.sin(SLOPE), 0.0, math.cos(SLOPE)), "marble_white")
    return builder


def spans(first, second):
    return [(first, math.pi - second), (math.pi + second, 2 * math.pi - first)]


def span_lathe(walls, profile, cuts, material):
    for a0, a1 in spans(*cuts):
        arc_lathe(walls, profile, a0, a1, max(int(round(128 * (a1 - a0) / (2 * math.pi))), 8), material)


def entablature_ring(walls):
    cornice = [(R, ENTABLATURE_TOP), (R - 1.8, ENTABLATURE_TOP), (R - 1.8, 12.92), (R - 1.67, 12.8), (R - 1.6, 12.62),
               (R - 1.6, 12.5), (R - 1.25, 12.46), (R - 1.19, 12.38), (R - 1.19, 12.22), (R - 1.07, 12.16),
               (R - 1.0, 12.1)]
    frieze = [(R - 1.0, 12.1), (R - 0.95, 12.08), (R - 0.95, 11.47)]
    architrave = [(R - 0.95, 11.47), (R - 1.05, 11.42), (R - 1.05, 11.36), (R - 1.02, 11.32), (R - 1.02, 11.06),
                  (R - 1.0, 11.04), (R - 1.0, ORDER_TOP), (R, ORDER_TOP)]
    cuts = (ENTRANCE_CUT, APSE_CUT)
    span_lathe(walls, cornice, cuts, "marble_white")
    span_lathe(walls, frieze, cuts, "porphyry")
    span_lathe(walls, architrave, cuts, "marble_white")
    outline = cornice + frieze[1:] + architrave[1:]
    for cut, side in ((ENTRANCE_CUT, -1), (math.pi - APSE_CUT, 1), (math.pi + APSE_CUT, -1),
                      (2 * math.pi - ENTRANCE_CUT, 1)):
        hint = Vector((math.cos(cut), -math.sin(cut), 0.0)) * side
        walls.oriented([polar(r, cut, z) for r, z in outline], hint, "marble_white")


def bay_attic(walls, angle, steps=16):
    normal = Vector((math.sin(angle), math.cos(angle), 0.0))
    tangent = Vector((math.cos(angle), -math.sin(angle), 0.0))
    for k in range(steps):
        a = angle - ALPHA + 2 * ALPHA * k / steps
        b = angle - ALPHA + 2 * ALPHA * (k + 1) / steps
        lows = [ENTABLATURE_TOP + math.sqrt(max(HALF_OPENING ** 2 - (R * math.sin(value - angle)) ** 2, 0.0))
                for value in (a, b)]
        for fraction in ((0.0, 0.5), (0.5, 1.0)):
            za = [lows[0] + (ATTIC_TOP - lows[0]) * f for f in fraction]
            zb = [lows[1] + (ATTIC_TOP - lows[1]) * f for f in fraction]
            quad(walls, [polar(R, a, za[0]), polar(R, b, zb[0]), polar(R, b, zb[1]), polar(R, a, za[1])],
                 -polar(1.0, (a + b) / 2), "marble_white")
    band = []
    for k in range(17):
        psi = math.pi * k / 16
        ring = []
        for rho in (HALF_OPENING, HALF_OPENING + 0.55):
            t = rho * math.cos(psi)
            ring.append(bay_point(normal, tangent, t, math.sqrt((R - 0.06) ** 2 - t * t),
                                  ENTABLATURE_TOP + rho * math.sin(psi)))
        band.append(ring)
    for (a0, a1), (b0, b1) in zip(band[:-1], band[1:]):
        quad(walls, [a0, b0, b1, a1], -normal, "marble_white", (0.95, 0.94, 0.92))


def attic(walls):
    cuts = (ALPHA, ALPHA)
    span_lathe(walls, [(R, z) for z in reversed(levels(13.45, ATTIC_TOP))], cuts, "marble_white")
    span_lathe(walls, [(R, 13.45), (R - 0.16, 13.45), (R - 0.16, ENTABLATURE_TOP)], cuts, "marble_white")
    arc_lathe(walls, [(R, SPRING), (R - 0.8, SPRING), (R - 0.8, 21.5), (R - 0.55, 21.32), (R - 0.3, 21.12),
                      (R - 0.12, 20.98), (R, ATTIC_TOP)], 0.0, 2 * math.pi, 128, "marble_white")
    bay_attic(walls, 0.0)
    bay_attic(walls, math.pi)
    for index in range(16):
        angle = math.radians(22.5 * index)
        frame = inward_frame(angle, R)
        if index not in (0, 8):
            walls.box((-1.35, 0.0, 15.0), (1.35, 0.16, 18.9), "marble_white", matrix=frame)
            painted(walls, (0.5, 0.62, 0.5), lambda: walls.box((-1.02, 0.0, 15.3), (1.02, 0.2, 18.6), "granite_grey",
                                                               matrix=frame))
            walls.box((-1.6, 0.0, 18.9), (1.6, 0.3, 19.15), "marble_white", matrix=frame)
        middle = angle + math.radians(11.25)
        if min(abs(math.remainder(middle - bay, 2 * math.pi)) for bay in (0.0, math.pi)) < math.radians(15.0):
            continue
        for side in (-1, 1):
            walls.merge(pilaster(0.62, 7.0, 0.1, "giallo"), inward_frame(middle + side * math.radians(3.0), R, 13.45))
        walls.box((-0.55, 0.0, 15.2), (0.55, 0.06, 19.0), "porphyry", matrix=inward_frame(middle, R))


def sphere_point(theta, phi, radius):
    return Vector((radius * math.cos(phi) * math.sin(theta), radius * math.cos(phi) * math.cos(theta),
                   SPRING + radius * math.sin(phi)))


def coffer_rows(count=28, rib=0.11, rows=5, start=3.0):
    step = 2 * math.pi / count
    rings = []
    phi = math.radians(start)
    for _ in range(rows):
        bottom = phi + step * rib * math.cos(phi)
        height = step * (1 - rib) * math.cos(bottom)
        for _ in range(4):
            height = step * (1 - rib) * math.cos(bottom + height / 2)
        rings.append((bottom, bottom + height))
        phi = bottom + height
    return rings, phi + step * rib * math.cos(phi)


def coffer(builder, t0, t1, p0, p1, steps=4, depth=0.17):
    centre = Vector((0.0, 0.0, SPRING))
    width = t1 - t0
    height = p1 - p0
    rects = [(t0 + 0.075 * k * width, t1 - 0.075 * k * width, p0 + 0.1 * k * height, p1 - 0.055 * k * height)
             for k in range(steps + 1)]

    def corners(rect, radius):
        return [sphere_point(rect[0], rect[2], radius), sphere_point(rect[1], rect[2], radius),
                sphere_point(rect[1], rect[3], radius), sphere_point(rect[0], rect[3], radius)]
    middle = sphere_point((t0 + t1) / 2, (p0 + p1) / 2, R)
    for k in range(steps):
        r0 = R + depth * k
        r1 = R + depth * (k + 1)
        outer0 = corners(rects[k], r0)
        outer1 = corners(rects[k], r1)
        inner1 = corners(rects[k + 1], r1)
        for edge in range(4):
            i, j = edge, (edge + 1) % 4
            edge_middle = (outer0[i] + outer0[j]) / 2
            quad(builder, [outer0[i], outer0[j], outer1[j], outer1[i]], middle - edge_middle, "stucco",
                 (0.9 - 0.07 * k,) * 3)
            ledge = [outer1[i], outer1[j], inner1[j], inner1[i]]
            quad(builder, ledge, centre - (outer1[i] + inner1[j]) / 2, "stucco", (0.93 - 0.07 * k,) * 3)
    panel = corners(rects[steps], R + depth * steps)
    quad(builder, panel, centre - sum(panel, Vector()) / 4, "stucco", (0.66, 0.65, 0.63))


def dome(builder, columns=28, rib=0.11):
    step = 2 * math.pi / columns
    width = step * (1 - rib)
    rings, coffer_top = coffer_rows(columns, rib)
    oculus_phi = math.acos(OCULUS / R)
    thetas = []
    for column in range(columns):
        thetas += [column * step - width / 2, column * step + width / 2]
    thetas.append(thetas[0] + 2 * math.pi)
    phis = [0.0]
    coffer_rows_index = set()
    for bottom, top in rings:
        phis.append(bottom)
        coffer_rows_index.add(len(phis) - 1)
        phis.append(top)
    phis.append(coffer_top)
    for extra in range(1, 5):
        phis.append(coffer_top + (oculus_phi - coffer_top) * extra / 4)
    centre = Vector((0.0, 0.0, SPRING))
    for row in range(len(phis) - 1):
        for cell in range(len(thetas) - 1):
            if row in coffer_rows_index and cell % 2 == 0:
                coffer(builder, thetas[cell], thetas[cell + 1], phis[row], phis[row + 1])
                continue
            points = [sphere_point(thetas[cell], phis[row], R), sphere_point(thetas[cell + 1], phis[row], R),
                      sphere_point(thetas[cell + 1], phis[row + 1], R), sphere_point(thetas[cell], phis[row + 1], R)]
            quad(builder, points, centre - sum(points, Vector()) / 4, "stucco", (0.94, 0.93, 0.91))
    oculus_z = SPRING + R * math.sin(oculus_phi)
    lip = math.sqrt(R * R - (OCULUS + 0.6) ** 2) + SPRING
    builder.lathe([(OCULUS, 44.35), (OCULUS, lip), (OCULUS + 0.6, lip)], 48, "bronze", smooth=True, caps=False)
    return {"rings": [(math.degrees(a), math.degrees(b)) for a, b in rings], "oculus_z": oculus_z}


def interior():
    walls = MeshBuilder()
    floor = MeshBuilder()
    columns = {"giallo": [], "pavonazzetto": []}
    statues = []
    rings = [[polar(R * ring / 16, 2 * math.pi * step / 128) for step in range(128)] for ring in range(1, 17)]
    floor.surface(rings, "floor_sectile", closed=True, facing=(0, 0, 1))
    floor.oriented(rings[0], (0, 0, 1), "floor_sectile")
    for index in range(8):
        opening(walls, floor, index, columns, statues)
        pier(walls, math.radians(22.5 + 45 * index))
    entablature_ring(walls)
    attic(walls)
    dome_info = dome(walls)
    aediculae = {"aedicula_triangular": [], "aedicula_segmental": []}
    small_statues = []
    for index in range(8):
        angle = math.radians(22.5 + 45 * index)
        key = "aedicula_segmental" if index % 2 else "aedicula_triangular"
        aediculae[key].append(inward_frame(angle, R + 0.08))
        small_statues.append(inward_frame(angle, R + 0.08) @ placement(0.0, 0.5, 1.7))
    return walls, floor, columns, statues, aediculae, small_statues, dome_info


def exterior_dome(builder):
    front = math.radians(39.0)
    arc_lathe(builder, [(RO, PIAZZA), (RO, BLOCK_TOP)], front, 2 * math.pi - front, 80, "brick")
    arc_lathe(builder, [(RO, BLOCK_TOP), (RO, 28.2)], 0.0, 2 * math.pi, 96, "brick")
    arc_lathe(builder, [(RO + 0.45, PIAZZA), (RO + 0.45, PIAZZA + 0.8), (RO + 0.2, PIAZZA + 1.0), (RO, PIAZZA + 1.1)],
              front, 2 * math.pi - front, 80, "marble_white")
    for level in (12.6, 21.6):
        arc_lathe(builder, [(RO, level - 0.3), (RO + 0.25, level - 0.2), (RO + 0.25, level), (RO + 0.65, level + 0.18),
                            (RO + 0.65, level + 0.4), (RO, level + 0.4)], front, 2 * math.pi - front, 80, "marble_white")
    top = [(RO, 28.2), (RO + 0.3, 28.35), (RO + 0.3, 28.55), (RO + 0.95, 28.75), (RO + 0.95, 28.95), (RO - 0.25, 28.95)]
    arc_lathe(builder, top, 0.0, 2 * math.pi, 96, "marble_white")
    radius = RO - 0.25
    height = 28.95
    steps = []
    for _ in range(6):
        steps += [(radius, height), (radius, height + 0.8)]
        height += 0.8
        radius -= 0.45
        steps.append((radius, height))
    arc_lathe(builder, steps, 0.0, 2 * math.pi, 96, "bronze_tiles", smooth=False)
    rim_radius = OCULUS + 1.2
    rim_height = 44.0
    centre = ((radius * radius + height * height) - (rim_radius * rim_radius + rim_height * rim_height)) / (
        2 * (height - rim_height))
    sphere = math.hypot(radius, height - centre)
    start = math.atan2(height - centre, radius)
    end = math.atan2(rim_height - centre, rim_radius)
    cap = [(sphere * math.cos(start + (end - start) * k / 24), centre + sphere * math.sin(start + (end - start) * k / 24))
           for k in range(25)]
    arc_lathe(builder, cap, 0.0, 2 * math.pi, 96, "bronze_tiles")
    arc_lathe(builder, [(rim_radius, rim_height), (rim_radius, 44.35), (OCULUS, 44.35)], 0.0, 2 * math.pi, 48, "bronze")


def door_leaf(builder, hinge_x, side):
    frame = placement(hinge_x, BLOCK_SLAB, 0.0, math.radians(-80.0) if side < 0 else math.radians(260.0))
    builder.box((0.0, -0.22, 0.0), (DOOR_HALF, 0.0, DOOR_HEIGHT), "bronze", matrix=frame)
    for z0, z1 in ((0.5, 3.4), (3.9, 7.0)):
        builder.box((0.3, -0.27, z0), (DOOR_HALF - 0.3, -0.22, z1), "bronze", matrix=frame, bottom=False, top=False)
        builder.box((0.3, 0.0, z0), (DOOR_HALF - 0.3, 0.05, z1), "bronze", matrix=frame, bottom=False, top=False)


def span_box(builder, x0, x1, y0, y1, z0, z1, material):
    builder.box((min(x0, x1), y0, z0), (max(x0, x1), y1, z1), material)


def door(builder):
    for side in (-1, 1):
        span_box(builder, side * DOOR_HALF, side * HALF_OPENING, BLOCK_SLAB, BLOCK_FRONT, 0.0, BAY_TOP, "marble_white")
        span_box(builder, side * DOOR_HALF, side * (DOOR_HALF + 0.85), BLOCK_FRONT, BLOCK_FRONT + 0.25, 0.0,
                 LINTEL_TOP + 0.8, "marble_white")
        door_leaf(builder, side * DOOR_HALF, side)
    builder.box((-DOOR_HALF, BLOCK_SLAB, DOOR_HEIGHT), (DOOR_HALF, BLOCK_FRONT, LINTEL_TOP), "marble_white")
    builder.box((-HALF_OPENING, BLOCK_SLAB, BAY_TOP), (HALF_OPENING, BLOCK_FRONT, BLOCK_TOP), "marble_white")
    builder.box((-DOOR_HALF - 0.85, BLOCK_FRONT, LINTEL_TOP), (DOOR_HALF + 0.85, BLOCK_FRONT + 0.25, LINTEL_TOP + 0.8),
                "marble_white")
    builder.box((-DOOR_HALF - 1.3, BLOCK_FRONT, BAY_TOP), (DOOR_HALF + 1.3, BLOCK_FRONT + 0.6, BAY_TOP + 0.45),
                "marble_white")
    y = (BLOCK_SLAB + BLOCK_FRONT) / 2
    middle = (LINTEL_TOP + BAY_TOP) / 2
    for z0, z1 in ((LINTEL_TOP, LINTEL_TOP + 0.12), (BAY_TOP - 0.12, BAY_TOP), (middle - 0.05, middle + 0.05)):
        builder.box((-DOOR_HALF, y - 0.06, z0), (DOOR_HALF, y + 0.06, z1), "bronze")
    bars = 14
    for index in range(bars + 1):
        x = -DOOR_HALF + 2 * DOOR_HALF * index / bars
        builder.box((x - 0.035, y - 0.035, LINTEL_TOP), (x + 0.035, y + 0.035, BAY_TOP), "bronze", bottom=False,
                    top=False)


def niche_recess(builder, x):
    radius = 2.0
    curve = [Vector((x + radius * math.cos(math.pi * step / 12), BLOCK_SLAB - radius * math.sin(math.pi * step / 12), 0.0))
             for step in range(13)]
    target = Vector((x, BLOCK_SLAB - 0.5, 0.0))
    vertical_strip(builder, curve, 0.9, 7.5, target, "marble_white", (0.78, 0.78, 0.78))
    builder.oriented([Vector((point.x, point.y, 0.9)) for point in curve], (0, 0, 1), "marble_white")
    first = len(builder.polygons)
    builder.lathe([(radius, 0.0), (radius * math.cos(math.pi / 8), radius * math.sin(math.pi / 8)),
                   (radius * math.cos(math.pi / 4), radius * math.sin(math.pi / 4)),
                   (radius * math.cos(3 * math.pi / 8), radius * math.sin(3 * math.pi / 8)), (0.0, radius)][::-1],
                  12, "marble_white", smooth=True, matrix=placement(x, BLOCK_SLAB, 7.5), start=math.pi, sweep=math.pi,
                  caps=False)
    builder.tint(first, (0.72, 0.72, 0.72))


def oak_wreath(leaves=26, radius=1.05):
    builder = MeshBuilder()
    leaf = [(0.0, -0.5), (0.55, -0.32), (0.75, 0.0), (0.55, 0.32), (0.0, 0.5)]
    for k in range(leaves):
        angle = 2 * math.pi * k / leaves
        for row, (offset, tilt) in enumerate(((-0.09, 0.5), (0.09, -0.5))):
            spot = radius + offset
            frame = (Matrix.Translation((spot * math.cos(angle + row * 0.12), spot * math.sin(angle + row * 0.12), 0.0))
                     @ Matrix.Rotation(angle + row * 0.12 + math.pi / 2 + tilt, 4, "Z")
                     @ Matrix.Rotation(math.pi / 2, 4, "Y")
                     @ Matrix.Diagonal((0.09, 0.15, 0.36, 1.0)))
            builder.lathe(leaf, 6, "bronze_gilt", smooth=True, matrix=frame)
    return builder


def eagle():
    half = [(0.0, 0.78), (0.1, 0.76), (0.15, 0.62), (0.24, 0.46), (0.52, 0.62), (0.86, 0.8), (1.2, 0.88), (1.1, 0.66),
            (1.17, 0.54), (1.0, 0.42), (1.06, 0.27), (0.86, 0.16), (0.88, 0.02), (0.6, -0.02), (0.34, -0.1),
            (0.24, -0.36), (0.3, -0.76), (0.1, -0.68), (0.0, -0.8)]
    outline = half[:-1] + [(-x, y) for x, y in reversed(half[1:])]
    outline = list(reversed(outline))
    builder = MeshBuilder()
    builder.prism(outline, 0.0, 0.16, "bronze_gilt")
    return builder


def frieze_point():
    return Vector((0.0, ROWS[0] + 0.43 * PORCH_D, PORCH_COLUMN + 1.115 * PORCH_D))


def porch():
    builder = MeshBuilder()
    floor = MeshBuilder()
    floor.box((-BLOCK_HALF, BLOCK_FRONT, PIAZZA), (BLOCK_HALF, PORCH_EDGE, 0.0), "marble_paving", bottom=False)
    for step in range(1, 7):
        floor.box((-PORCH_HALF, PORCH_EDGE, PIAZZA - 0.2), (PORCH_HALF, PORCH_EDGE + STEP_TREAD * (7 - step),
                                                             PIAZZA + STEP_RISE * step), "marble_white", bottom=False)
    for side in (-1, 1):
        x0, x1 = sorted((side * HALF_OPENING, side * BLOCK_HALF))
        arched_wall(builder, x0, x1, BLOCK_SLAB, BLOCK_FRONT, 0.0, BLOCK_TOP, [(side * 11.125, 2.0, 7.5)],
                    "marble_white", segments=12, sill=0.9)
        niche_recess(builder, side * 11.125)
        quad(builder, [(side * BLOCK_HALF, 21.0, PIAZZA), (side * BLOCK_HALF, BLOCK_FRONT, PIAZZA),
                       (side * BLOCK_HALF, BLOCK_FRONT, BLOCK_TOP), (side * BLOCK_HALF, 21.0, BLOCK_TOP)],
             (side, 0, 0), "brick")
        for x in (side * 6.675, side * 15.575):
            builder.merge(pilaster(1.5, PORCH_COLUMN, 0.4, "marble_white"), placement(x, BLOCK_FRONT, 0.0))
        builder.box((side * 6.675 - 0.6, BLOCK_FRONT, PORCH_COLUMN), (side * 6.675 + 0.6, ROWS[0], PORCH_COLUMN + 1.6),
                    "marble_white")
    door(builder)
    path = [(FRONT_X[7], BLOCK_FRONT, PORCH_COLUMN), (FRONT_X[7], ROWS[0], PORCH_COLUMN),
            (FRONT_X[0], ROWS[0], PORCH_COLUMN), (FRONT_X[0], BLOCK_FRONT, PORCH_COLUMN)]
    builder.sweep(path, corinthian_entablature_profile(PORCH_D), "marble_white")
    half = abs(FRONT_X[0]) + 1.45 * PORCH_D
    tympanum_y = ROWS[0] + 0.4 * PORCH_D
    tympanum_half = half
    apex = CORNICE_TOP + tympanum_half * math.tan(SLOPE)
    builder.oriented([Vector((-tympanum_half, tympanum_y, CORNICE_TOP)), Vector((tympanum_half, tympanum_y, CORNICE_TOP)),
                      Vector((0.0, tympanum_y, apex))], (0, 1, 0), "marble_white")
    raking_apex = CORNICE_TOP + half * math.tan(SLOPE)
    builder.sweep([(-half, ROWS[0], CORNICE_TOP), (0.0, ROWS[0], raking_apex), (half, ROWS[0], CORNICE_TOP)],
                  raking_cornice_profile(PORCH_D), "marble_white", facade_normal=(0, 1, 0))
    wreath_z = CORNICE_TOP + 2.8
    builder.merge(oak_wreath(), placement(0.0, tympanum_y + 0.2, wreath_z) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    builder.merge(eagle(), placement(0.0, tympanum_y + 0.36, wreath_z) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    for side in (-1, 1):
        beam(builder, (side * 0.4, tympanum_y + 0.2, wreath_z - 1.0), (side * 1.7, tympanum_y + 0.2, wreath_z - 1.8), 0.2,
             0.05, "bronze_gilt")
    ridge = CORNICE_TOP + (PORCH_HALF + 0.7) * math.tan(SLOPE) - 0.35
    gable_roof(builder, BLOCK_FRONT, tympanum_y, PORCH_HALF + 0.7, CORNICE_TOP, ridge, "bronze_tiles", along_axis="y",
               imbrex=True, pitch=0.62)
    for side in (-1, 1):
        quad(builder, [(side * (PORCH_HALF + 0.7), BLOCK_FRONT, CORNICE_TOP - 0.12),
                       (side * (PORCH_HALF + 0.7), tympanum_y, CORNICE_TOP - 0.12),
                       (0.0, tympanum_y, ridge - 0.25), (0.0, BLOCK_FRONT, ridge - 0.25)], (0, 0, -1), "bronze",
             (0.7, 0.7, 0.7))
    trusses = MeshBuilder()
    rise = math.tan(SLOPE)
    for y in (ROWS[2], ROWS[1], ROWS[0] - 0.4, (BLOCK_FRONT + ROWS[2]) / 2):
        beam(trusses, (-PORCH_HALF, y, CORNICE_TOP - 0.45), (PORCH_HALF, y, CORNICE_TOP - 0.45), 0.4, 0.55, "bronze")
        top = ridge - 0.45
        for side in (-1, 1):
            beam(trusses, (side * PORCH_HALF, y, CORNICE_TOP - 0.3), (0.0, y, top), 0.38, 0.45, "bronze")
            beam(trusses, (side * 6.675, y, PORCH_COLUMN + 1.6), (side * 6.675, y, CORNICE_TOP - 0.7), 0.4, 0.4, "bronze")
            beam(trusses, (side * 6.675, y, CORNICE_TOP - 0.45), (0.0, y, top - 2.2), 0.28, 0.28, "bronze")
            beam(trusses, (side * 6.675, y, CORNICE_TOP - 0.45),
                 (side * 6.675, y, CORNICE_TOP + (PORCH_HALF - 6.675) * rise - 0.4), 0.26, 0.26, "bronze")
        beam(trusses, (0.0, y, CORNICE_TOP - 0.45), (0.0, y, top), 0.34, 0.34, "bronze")
    for x in (-13.0, -9.0, -4.5, 0.0, 4.5, 9.0, 13.0):
        z = CORNICE_TOP + (PORCH_HALF - abs(x)) * rise - 0.5
        beam(trusses, (x, BLOCK_FRONT, z), (x, tympanum_y - 0.3, z), 0.24, 0.3, "bronze")
    builder.merge(trusses)
    upper = MeshBuilder()
    cornice = [(-0.3, 0.0), (0.0, 0.0), (0.0, 0.3), (0.3, 0.42), (0.55, 0.62), (0.7, 0.66), (0.7, 0.8), (-0.3, 0.8)]
    upper.sweep([(BLOCK_HALF, 21.0, BLOCK_TOP - 0.8), (BLOCK_HALF, BLOCK_FRONT, BLOCK_TOP - 0.8),
                 (-BLOCK_HALF, BLOCK_FRONT, BLOCK_TOP - 0.8), (-BLOCK_HALF, 21.0, BLOCK_TOP - 0.8)], cornice,
                "marble_white")
    upper_apex = BLOCK_TOP + BLOCK_HALF * math.tan(SLOPE)
    upper.oriented([Vector((-BLOCK_HALF, BLOCK_FRONT + 0.02, BLOCK_TOP)), Vector((BLOCK_HALF, BLOCK_FRONT + 0.02, BLOCK_TOP)),
                    Vector((0.0, BLOCK_FRONT + 0.02, upper_apex))], (0, 1, 0), "marble_white")
    upper.sweep([(-BLOCK_HALF - 0.6, BLOCK_FRONT, BLOCK_TOP), (0.0, BLOCK_FRONT, upper_apex + 0.25),
                 (BLOCK_HALF + 0.6, BLOCK_FRONT, BLOCK_TOP)], raking_cornice_profile(1.1), "marble_white",
                facade_normal=(0, 1, 0))
    gable_roof(upper, 19.0, BLOCK_FRONT, BLOCK_HALF + 0.5, BLOCK_TOP, upper_apex - 0.2, "bronze_tiles", along_axis="y",
               imbrex=True, pitch=0.7)
    builder.merge(upper)
    columns = {"porch_grey": [placement(x, ROWS[0], 0.0) for x in FRONT_X],
               "porch_rose": [placement(x, y, 0.0) for y in ROWS[1:] for x in INNER_X]}
    return builder, floor, columns, [placement(side * 11.125, BLOCK_SLAB - 0.4, 0.9, 0.0) for side in (-1, 1)]


def inscription_builder():
    probe, width = inscription(INSCRIPTION, 0.7, "bronze_letters", 0.05)
    letter = min(0.86, 0.7 * 27.0 / max(width, 1e-3))
    letters, width = inscription(INSCRIPTION, letter, "bronze_letters", 0.05)
    origin = frieze_point() + Vector((0.0, 0.03, 0.0))
    placed = MeshBuilder()
    placed.merge(letters, facing_text_matrix(origin, (0, 1, 0)))
    return placed, {"letter_height": round(letter, 3), "width": round(width, 2)}


def segmented_wall(builder, a0, a1, b0, b1, along, piece=6.0):
    count = max(int(round((b1 - b0) / piece)), 1)
    for k in range(count):
        c0, c1 = b0 + (b1 - b0) * k / count, b0 + (b1 - b0) * (k + 1) / count
        if along == "y":
            builder.box((a0, c0, PIAZZA - 1.0), (a1, c1, 11.6), "plaster_cream", bottom=False)
        else:
            builder.box((c0, a0, PIAZZA - 1.0), (c1, a1, 11.6), "plaster_cream", bottom=False)


def plaza_floor(floor, cell=2.0):
    x_count = int(round((2 * PLAZA_HALF + 0.2) / cell))
    y_count = int(round((PLAZA_NORTH + 0.1 - PLAZA_SOUTH) / cell))
    for i in range(x_count):
        x0 = -PLAZA_HALF - 0.1 + (2 * PLAZA_HALF + 0.2) * i / x_count
        x1 = -PLAZA_HALF - 0.1 + (2 * PLAZA_HALF + 0.2) * (i + 1) / x_count
        for j in range(y_count):
            y0 = PLAZA_SOUTH + (PLAZA_NORTH + 0.1 - PLAZA_SOUTH) * j / y_count
            y1 = PLAZA_SOUTH + (PLAZA_NORTH + 0.1 - PLAZA_SOUTH) * (j + 1) / y_count
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            path = max(0.0, 1.0 - abs(cx) / 3.0) * (1.0 if cy > PORCH_EDGE else 0.0)
            foot = max(0.0, 1.0 - max(cy - (PORCH_EDGE + 1.8), 0.0) / 3.0) * (1.0 if abs(cx) < PORCH_HALF + 1.0 else 0.0)
            shade = 1.0 - 0.1 * max(path, foot)
            first = len(floor.polygons)
            floor.oriented([Vector((x0, y0, PIAZZA)), Vector((x1, y0, PIAZZA)), Vector((x1, y1, PIAZZA)),
                            Vector((x0, y1, PIAZZA))], (0, 0, 1), "travertine")
            floor.tint(first, (shade, shade * 0.99, shade * 0.97))


def portico_side(builder, floor, side):
    for step in range(1, 5):
        x0, x1 = sorted((side * (PLAZA_HALF + STEP_TREAD * (step - 1)), side * PORTICO_EDGE))
        floor.box((x0, 30.0, PIAZZA - 0.2), (x1, PLAZA_NORTH, PIAZZA + STEP_RISE * step), "giallo", bottom=False)
    x0, x1 = sorted((side * PORTICO_EDGE, side * PORTICO_BACK))
    floor.box((x0, 30.0, PIAZZA - 0.2), (x1, PLAZA_NORTH + 8.0, PORTICO_FLOOR), "giallo", bottom=False)
    wall_x0, wall_x1 = sorted((side * PORTICO_BACK, side * (PORTICO_BACK + 0.6)))
    segmented_wall(builder, wall_x0, wall_x1, 30.0, PLAZA_NORTH + 8.6, "y")
    for y in range(36, 160, 9):
        quad(builder, [(side * (PORTICO_BACK - 0.02), y - 1.2, PORTICO_FLOOR), (side * (PORTICO_BACK - 0.02), y + 1.2, PORTICO_FLOOR),
                       (side * (PORTICO_BACK - 0.02), y + 1.2, PORTICO_FLOOR + 3.6),
                       (side * (PORTICO_BACK - 0.02), y - 1.2, PORTICO_FLOOR + 3.6)], (-side, 0, 0), "shadow_void")
    beam_top = PORTICO_FLOOR + PORTICO_COLUMN + 0.9
    x0, x1 = sorted((side * (PORTICO_LINE - 0.55), side * (PORTICO_LINE + 0.55)))
    builder.box((x0, 30.0, PORTICO_FLOOR + PORTICO_COLUMN), (x1, PLAZA_NORTH + 2.8, beam_top), "marble_white")
    tile_roof(builder, (side * (PORTICO_BACK + 0.6), 30.0, 11.8), (side * (PORTICO_BACK + 0.6), PLAZA_NORTH + 8.6, 11.8),
              (-side * (PORTICO_BACK + 0.6 - PORTICO_LINE + 0.8), 0.0, beam_top + 0.1 - 11.8), "terracotta_tiles",
              imbrex=False)
    quad(builder, [(side * (PORTICO_LINE + 0.5), 30.0, beam_top - 0.05), (side * PORTICO_BACK, 30.0, 11.4),
                   (side * PORTICO_BACK, PLAZA_NORTH + 8.0, 11.4), (side * (PORTICO_LINE + 0.5), PLAZA_NORTH + 8.0, beam_top - 0.05)],
         (0, 0, -1), "plaster", (0.75, 0.68, 0.6))
    return [placement(side * PORTICO_LINE, 32.0 + PORTICO_SPACING * index, PORTICO_FLOOR)
            for index in range(int((PLAZA_NORTH - 33.0) / PORTICO_SPACING) + 1)]


def piazza():
    builder = MeshBuilder()
    floor = MeshBuilder()
    plaza_floor(floor)
    frames = portico_side(builder, floor, -1) + portico_side(builder, floor, 1)
    for step in range(1, 5):
        floor.box((-PORTICO_EDGE, PLAZA_NORTH + STEP_TREAD * (step - 1), PIAZZA - 0.2),
                  (PORTICO_EDGE, PLAZA_NORTH + 1.2, PIAZZA + STEP_RISE * step), "giallo", bottom=False)
    floor.box((-PORTICO_BACK, PLAZA_NORTH + 1.2, PIAZZA - 0.2), (PORTICO_BACK, PLAZA_NORTH + 8.0, PORTICO_FLOOR), "giallo",
              bottom=False)
    north_line = PLAZA_NORTH + 2.25
    back = PLAZA_NORTH + 8.0
    segmented_wall(builder, back, back + 0.6, -PORTICO_BACK - 0.6, PORTICO_BACK + 0.6, "x")
    for x in range(-27, 28, 9):
        quad(builder, [(x - 1.2, back - 0.02, PORTICO_FLOOR), (x + 1.2, back - 0.02, PORTICO_FLOOR),
                       (x + 1.2, back - 0.02, PORTICO_FLOOR + 3.6), (x - 1.2, back - 0.02, PORTICO_FLOOR + 3.6)], (0, -1, 0),
             "shadow_void")
    beam_top = PORTICO_FLOOR + PORTICO_COLUMN + 0.9
    builder.box((-PORTICO_LINE - 0.55, north_line - 0.55, PORTICO_FLOOR + PORTICO_COLUMN),
                (PORTICO_LINE + 0.55, north_line + 0.55, beam_top), "marble_white")
    tile_roof(builder, (-PORTICO_BACK - 0.6, back + 0.6, 11.8), (PORTICO_BACK + 0.6, back + 0.6, 11.8),
              (0.0, -(back + 0.6 - north_line + 0.8), beam_top + 0.1 - 11.8), "terracotta_tiles", imbrex=False)
    quad(builder, [(-PORTICO_BACK, north_line + 0.5, beam_top - 0.05), (PORTICO_BACK, north_line + 0.5, beam_top - 0.05),
                   (PORTICO_BACK, back, 11.4), (-PORTICO_BACK, back, 11.4)], (0, 0, -1), "plaster", (0.75, 0.68, 0.6))
    count = int(round(2 * PORTICO_LINE / PORTICO_SPACING))
    frames += [placement(-PORTICO_LINE + 2 * PORTICO_LINE * index / count, north_line, PORTICO_FLOOR)
               for index in range(count + 1)]
    for side in (-1, 1):
        x0, x1 = sorted((side * 26.0, side * (PORTICO_BACK + 0.6)))
        hall = MeshBuilder()
        hall.box((x0, -16.0, PIAZZA - 1.0), (x1, 16.0, 10.0), "brick", bottom=False)
        gable_roof(hall, x0, x1, 16.4, 10.0, 13.0, "terracotta_tiles", along_axis="x", imbrex=False)
        builder.merge(hall, placement(0.0, 6.0, 0.0))
    return builder, floor, frames

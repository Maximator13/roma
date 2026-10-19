import math
import random

from mathutils import Matrix, Vector

from .geometry import MeshBuilder, placement
from .orders import (ENGAGED_HALF, STONE, column, facing_text_matrix, gable_ends, gable_roof, inscription, pilaster,
                     simple_entablature_profile, tile_roof)

WEATHERED = "weathered_ashlar"
ASHLAR = "lens_ashlar"
TILES = "terracotta_tiles"
VOID = "shadow_void"


def arched_wall(builder, x0, x1, y_back, y_front, z0, z_top, openings, material, segments=10, sill=None,
                foundation=0.0):
    left = x0
    for center, half, impost in sorted(openings):
        if center - half > left + 1e-4:
            builder.box((left, y_back, z0 - foundation), (center - half, y_front, z_top), material, bottom=False)
        arch = [(center + half * math.cos(math.pi * (1 - i / segments)),
                 impost + half * math.sin(math.pi * (1 - i / segments))) for i in range(segments + 1)]
        for (xa, za), (xb, zb) in zip(arch[:-1], arch[1:]):
            builder.oriented([(xa, y_front, za), (xb, y_front, zb), (xb, y_front, z_top), (xa, y_front, z_top)],
                             (0, 1, 0), material)
            builder.oriented([(xa, y_back, za), (xb, y_back, zb), (xb, y_back, z_top), (xa, y_back, z_top)],
                             (0, -1, 0), material)
            middle_x = (xa + xb) / 2
            middle_z = (za + zb) / 2
            builder.oriented([(xa, y_front, za), (xb, y_front, zb), (xb, y_back, zb), (xa, y_back, za)],
                             (center - middle_x, 0, impost - middle_z), material)
        builder.oriented([(center - half, y_back, z_top), (center + half, y_back, z_top),
                          (center + half, y_front, z_top), (center - half, y_front, z_top)], (0, 0, 1), material)
        if sill is not None:
            builder.box((center - half, y_back + 0.15, z0), (center + half, y_front - 0.15, sill), material,
                        bottom=False)
        left = center + half
    if x1 > left + 1e-4:
        builder.box((left, y_back, z0 - foundation), (x1, y_front, z_top), material, bottom=False)
    return builder


def straight_moulding(builder, x0, x1, height, profile, material, y=0.0):
    builder.sweep([(x1, y, height), (x0, y, height)], profile, material, caps=True)
    return builder


def amphitheatre_bay(width):
    builder = MeshBuilder()
    half = width / 2
    opening = (width - 2.2) / 2
    arched_wall(builder, -half, half, -1.2, 0.0, 0.0, 7.5, [(0.0, opening, 4.9)], ASHLAR, segments=7,
                foundation=2.5)
    builder.merge(pilaster(1.1, 7.2, 0.22, ASHLAR), placement(-half, 0.0, 0.3))
    builder.box((-half, -1.2, 7.5), (half, -0.4, 8.4), ASHLAR, bottom=False)
    straight_moulding(builder, -half, half, 7.5, simple_entablature_profile(0.9, 0.38), ASHLAR)
    arched_wall(builder, -half, half, -1.2, 0.0, 8.4, 15.4, [(0.0, opening, 12.3)], ASHLAR, segments=7,
                sill=9.3)
    builder.merge(column("tuscan", 0.82, 6.0, detail="low", material=ASHLAR, arc=ENGAGED_HALF),
                  placement(-half, 0.05, 9.4))
    builder.box((-half, -1.2, 15.4), (half, -0.4, 16.4), ASHLAR, bottom=False)
    straight_moulding(builder, -half, half, 15.4, simple_entablature_profile(1.0, 0.42), ASHLAR)
    builder.box((-half, -1.0, 16.4), (half, 0.0, 20.4), ASHLAR, bottom=False)
    straight_moulding(builder, -half, half, 20.4, simple_entablature_profile(0.6, 0.32), ASHLAR)
    for x in (-width / 4, width / 4):
        builder.box((x - 0.22, 0.0, 19.35), (x + 0.22, 0.6, 19.95), ASHLAR)
        builder.box((x - 0.18, 0.0, 16.55), (x + 0.18, 0.42, 16.85), ASHLAR)
        builder.lathe([(0.14, 16.85), (0.11, 25.2)], 5, "dark_wood", smooth=True, matrix=placement(x, 0.34, 0.0))
    vault = [(-3.2 + 2.0 * math.cos(math.pi * i / 8), 5.2 + 2.0 * math.sin(math.pi * i / 8)) for i in range(9)]
    builder.surface([[(x, y, z) for y, z in vault] for x in (-half, half)], WEATHERED)
    builder.box((-half, -5.2, -0.2), (half, -1.2, 0.0), "paving", bottom=False)
    builder.box((-half, -5.2, 8.2), (half, -1.2, 8.4), WEATHERED, bottom=False)
    builder.box((-half, -5.2, 15.9), (half, -1.2, 16.4), WEATHERED)
    arched_wall(builder, -half, half, -6.4, -5.2, 0.0, 8.2, [(0.0, 1.3, 2.7)], WEATHERED, segments=4)
    arched_wall(builder, -half, half, -6.4, -5.2, 8.2, 16.4, [(0.0, 1.2, 10.6)], WEATHERED, segments=4)
    builder.box((-1.4, -7.0, 0.0), (1.4, -6.3, 4.1), VOID, bottom=False)
    builder.box((-1.3, -7.0, 8.2), (1.3, -6.3, 11.9), VOID, bottom=False)
    builder.box((-half, -6.4, 19.3), (half, -1.0, 19.6), "paving", bottom=False)
    builder.box((-half, -6.4, 16.4), (half, -5.2, 19.3), WEATHERED, bottom=False, top=False)
    return builder


def amphitheatre_bay_axial(width, bulls=False):
    builder = amphitheatre_bay(width)
    half = width / 2 - 0.35
    base = 8.0
    apex = base + half * 0.32
    front = 0.95
    builder.oriented([(-half, front, base), (half, front, base), (0.0, front, apex)], (0, 1, 0), ASHLAR)
    builder.oriented([(-half, front, base), (0.0, front, apex), (0.0, -0.2, apex), (-half, -0.2, base)], (-0.3, 0, 1),
                     ASHLAR)
    builder.oriented([(half, front, base), (half, -0.2, base), (0.0, -0.2, apex), (0.0, front, apex)], (0.3, 0, 1),
                     ASHLAR)
    builder.box((-half, -0.2, base - 0.35), (half, front, base), ASHLAR)
    if bulls:
        for side in (-1, 1):
            x = side * (half - 0.2)
            builder.box((x - 0.28, 0.0, 10.0), (x + 0.28, 0.5, 10.6), ASHLAR)
            builder.box((x - 0.2, 0.5, 9.8), (x + 0.2, 1.05, 10.4), ASHLAR)
            for horn in (-1, 1):
                builder.box((x + horn * 0.2, 0.55, 10.4), (x + horn * 0.45, 0.7, 10.55), ASHLAR)
    return builder


def ellipse_point(semi_x, semi_y, angle):
    return Vector((semi_x * math.cos(angle), semi_y * math.sin(angle), 0.0))


def ellipse_arc_angles(semi_x, semi_y, count):
    samples = 4096
    points = [ellipse_point(semi_x, semi_y, 2 * math.pi * i / samples) for i in range(samples + 1)]
    lengths = [0.0]
    for a, b in zip(points[:-1], points[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1]
    angles = []
    cursor = 0
    for item in range(count):
        target = total * item / count
        while lengths[cursor + 1] < target:
            cursor += 1
        fraction = (target - lengths[cursor]) / max(lengths[cursor + 1] - lengths[cursor], 1e-9)
        angles.append(2 * math.pi * (cursor + fraction) / samples)
    return angles, total


def amphitheatre_cavea(arena_x, arena_y, outer_x, outer_y, top, rows=34, samples=80):
    builder = MeshBuilder()
    profile = [(0.0, 0.0), (0.0, 3.2), (0.035, 3.2), (0.035, 3.7), (0.06, 3.7)]
    step_depth = (1.0 - 0.06) / rows
    step_rise = (top - 3.7) / rows
    for row in range(rows):
        s = 0.06 + step_depth * row
        height = 3.7 + step_rise * row
        profile.append((s, height + step_rise))
        profile.append((s + step_depth, height + step_rise))
    angles = [2 * math.pi * i / samples for i in range(samples)]
    radial_rows = []
    for s, height in profile:
        ring = []
        for angle in angles:
            inner = ellipse_point(arena_x, arena_y, angle)
            outer = ellipse_point(outer_x, outer_y, angle)
            point = inner + (outer - inner) * s
            point.z = height
            ring.append(point)
        radial_rows.append(ring)
    builder.surface(list(reversed(radial_rows)), WEATHERED, closed=True)
    arena = [ellipse_point(arena_x, arena_y, angle) + Vector((0, 0, 0.05)) for angle in angles]
    builder.polygon(arena, "arena_sand")
    parapet = [[ellipse_point(arena_x - 0.05, arena_y - 0.05, a) + Vector((0, 0, z)) for a in angles]
               for z in (3.2, 4.1)]
    builder.surface(parapet, "plaster_ochre", closed=True)
    return builder


def curtain_wall(length, thickness=2.0, walk=7.6, foundation=8.0, material=WEATHERED):
    builder = MeshBuilder()
    h = length / 2
    t = thickness / 2
    builder.box((-h, -t, -foundation), (h, t, walk), material, bottom=False)
    builder.box((-h, t - 0.55, walk), (h, t, walk + 0.75), material, bottom=False)
    merlons = max(int(round(length / 2.6)), 1)
    step = length / merlons
    for index in range(merlons):
        center = -h + step * (index + 0.5)
        builder.box((center - 0.7, t - 0.55, walk + 0.75), (center + 0.7, t, walk + 1.65), material, bottom=False)
    return builder


def tower_windows(builder, center, radius, height, angles_degrees):
    for angle_degrees in angles_degrees:
        angle = math.radians(angle_degrees)
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        frame = Matrix.Rotation(angle - math.pi / 2, 4, "Z")
        frame.translation = Vector(center) + direction * (radius - 0.08)
        builder.centered_box((0.0, 0.0, height), (0.65, 0.3, 1.3), VOID, matrix=frame)


def round_tower(radius=4.5, height=13.0, offset=3.5, foundation=8.0, material=WEATHERED, segments=10, start=0.0):
    builder = MeshBuilder()
    center = (0.0, offset, 0.0)
    move = placement(0.0, offset, 0.0)
    builder.box((-radius * 0.7, -1.0, -foundation), (radius * 0.7, offset, height - 1.0), material, bottom=False)
    builder.lathe([(radius, -foundation), (radius, height - 0.7)], segments, material, smooth=segments > 8,
                  matrix=move, start=start, caps=False)
    builder.lathe([(radius, height - 0.7), (radius + 0.25, height - 0.5), (radius + 0.25, height - 0.1),
                   (radius + 0.45, height)], segments, ASHLAR, smooth=False, matrix=move, start=start, caps=False)
    builder.lathe([(radius + 0.45, height), (radius + 0.6, height - 0.15), (0.0, height + radius * 0.6)],
                  segments, TILES, smooth=False, matrix=move, start=start)
    tower_windows(builder, center, radius, height - 3.0, (30, 90, 150))
    tower_windows(builder, center, radius, height - 7.5, (60, 120))
    return builder


def barlong_tower(width=8.0, projection=6.5, height=12.5, foundation=8.0, material=WEATHERED):
    builder = MeshBuilder()
    half = width / 2
    builder.box((-half, -1.0, -foundation), (half, projection, height - 0.6), material, bottom=False)
    builder.box((-half - 0.25, -1.25, height - 0.6), (half + 0.25, projection + 0.25, height), ASHLAR, bottom=False)
    apex_low = Vector((0.0, (projection - 1.0) / 2, height + 2.6))
    corners = [Vector((-half - 0.5, -1.5, height)), Vector((half + 0.5, -1.5, height)),
               Vector((half + 0.5, projection + 0.5, height)), Vector((-half - 0.5, projection + 0.5, height))]
    ridge_a = apex_low + Vector((-half * 0.35, 0, 0))
    ridge_b = apex_low + Vector((half * 0.35, 0, 0))
    builder.oriented([corners[0], corners[1], ridge_b, ridge_a], (0, -1, 1), TILES)
    builder.oriented([corners[2], corners[3], ridge_a, ridge_b], (0, 1, 1), TILES)
    builder.oriented([corners[1], corners[2], ridge_b], (1, 0, 1), TILES)
    builder.oriented([corners[3], corners[0], ridge_a], (-1, 0, 1), TILES)
    for x in (-half * 0.5, half * 0.5):
        builder.centered_box((x, projection + 0.02, height - 3.2), (0.6, 0.1, 1.3), VOID)
    builder.centered_box((0.0, projection + 0.02, height - 7.5), (0.6, 0.1, 1.3), VOID)
    return builder


def secondary_gate(material=WEATHERED):
    builder = MeshBuilder()
    arched_wall(builder, -6.0, 6.0, -4.0, 1.0, 0.0, 10.0, [(0.0, 2.2, 4.6)], material, foundation=6.0)
    straight_moulding(builder, -6.0, 6.0, 10.0, simple_entablature_profile(0.8, 0.35), ASHLAR, y=1.0)
    builder.box((-6.0, -4.0, 10.0), (6.0, 0.6, 11.4), material)
    for side in (-1, 1):
        builder.merge(round_tower(4.2, 14.0, 2.5, 6.0, material), placement(side * 9.5, 0.0, 0.0))
    builder.box((-2.3, -4.2, 0.0), (2.3, -3.8, 4.4), VOID, bottom=False)
    return builder


def porte_de_france(material=WEATHERED):
    builder = MeshBuilder()
    arched_wall(builder, -5.0, 5.0, -2.5, 0.8, 0.0, 9.0, [(0.0, 2.0, 4.4)], ASHLAR, foundation=6.0)
    straight_moulding(builder, -5.0, 5.0, 8.4, simple_entablature_profile(0.6, 0.3), ASHLAR, y=0.8)
    builder.box((-5.0, -2.5, 9.0), (5.0, 0.6, 13.0), ASHLAR, bottom=False)
    for x in (-3.6, -1.2, 1.2, 3.6):
        builder.merge(pilaster(0.55, 3.4, 0.12, ASHLAR), placement(x, 0.6, 9.0))
    straight_moulding(builder, -5.0, 5.0, 12.4, simple_entablature_profile(0.6, 0.3), ASHLAR, y=0.6)
    return builder


def augustus_gate():
    builder = MeshBuilder()
    openings = [(-6.4, 0.95, 3.0), (-2.55, 1.95, 4.8), (2.55, 1.95, 4.8), (6.4, 0.95, 3.0)]
    arched_wall(builder, -10.0, 10.0, -2.6, 0.0, 0.0, 8.0, openings, ASHLAR, segments=12, foundation=3.0)
    for x in (-8.8, -4.975, 0.0, 4.975, 8.8):
        builder.merge(pilaster(0.62 if abs(x) < 1 else 0.55, 7.4, 0.16, ASHLAR), placement(x, 0.0, 0.25))
    builder.box((-10.0, -2.6, 8.0), (10.0, -0.4, 9.9), ASHLAR, bottom=False)
    builder.box((-10.0, -0.4, 8.0), (10.0, 0.18, 9.2), ASHLAR, bottom=False)
    straight_moulding(builder, -10.0, 10.0, 9.2, simple_entablature_profile(0.7, 0.45), ASHLAR, y=0.18)
    builder.box((-10.0, -2.6, 9.9), (10.0, -0.1, 11.6), ASHLAR, bottom=False)
    straight_moulding(builder, -10.0, 10.0, 11.6, simple_entablature_profile(0.35, 0.25), ASHLAR, y=-0.1)
    for side in (-1, 1):
        tower = MeshBuilder()
        tower.lathe([(5.0, -3.0), (5.0, 15.3)], 20, ASHLAR, smooth=True, start=0.0, sweep=math.pi, caps=False,
                    matrix=placement(0.0, -1.0, 0.0))
        tower.box((-5.0, -12.0, -3.0), (5.0, -1.0, 15.3), ASHLAR, bottom=False)
        tower.lathe([(5.0, 15.3), (5.3, 15.6), (5.3, 16.1)], 20, ASHLAR, start=0.0, sweep=math.pi, caps=False,
                    matrix=placement(0.0, -1.0, 0.0))
        tower.box((-5.3, -12.0, 15.3), (5.3, -1.0, 16.1), ASHLAR, bottom=False)
        tower.lathe([(5.5, 16.1), (0.0, 19.4)], 20, TILES, start=0.0, sweep=math.pi, caps=False,
                    matrix=placement(0.0, -1.0, 0.0))
        tower.oriented([(-5.5, -1.0, 16.1), (5.5, -1.0, 16.1), (0.0, -1.0, 19.4)], (0, -1, 0), TILES)
        gable_roof(tower, -12.3, -1.0, 5.5, 16.1, 19.4, TILES, along_axis="y", imbrex=False)
        tower.oriented([(-5.0, -12.0, 16.1), (5.0, -12.0, 16.1), (0.0, -12.0, 19.1)], (0, -1, 0), ASHLAR)
        tower_windows(tower, (0.0, -1.0, 0.0), 5.0, 12.5, (45, 90, 135))
        builder.merge(tower, placement(side * 15.0, 0.0, 0.0))
    for side in (-1, 1):
        x_low, x_high = sorted((side * 10.0, side * 11.0))
        builder.box((x_low, -14.0, -2.0), (x_high, -2.6, 9.0), WEATHERED, bottom=False)
    inner = [(-6.4, 0.9, 2.8), (-2.55, 1.9, 4.6), (2.55, 1.9, 4.6), (6.4, 0.9, 2.8)]
    arched_wall(builder, -10.0, 10.0, -16.0, -14.0, 0.0, 9.0, inner, WEATHERED, foundation=3.0)
    builder.box((-10.0, -16.0, 9.0), (10.0, -14.0, 9.6), ASHLAR)
    builder.box((-10.0, -14.0, -0.15), (10.0, 0.0, 0.0), "paving", bottom=False)
    first, width_first = inscription("IMP·CAESAR·DIVI·F·AVGVSTVS·COS·XI·TRIB·POTEST·VIII", 0.3)
    second, width_second = inscription("PORTAS·MVROS·COL·DAT", 0.3)
    builder.merge(first, facing_text_matrix((0.0, 0.2, 8.82), (0, 1, 0)) @ Matrix.Scale(min(1.0, 18.0 / width_first), 4))
    builder.merge(second, facing_text_matrix((0.0, 0.2, 8.38), (0, 1, 0)) @ Matrix.Scale(min(1.0, 18.0 / width_second), 4))
    return builder


def tour_magne():
    builder = MeshBuilder()
    octagon = 8
    start = math.pi / 8
    builder.lathe([(10.4, -6.0), (10.4, 0.0), (9.9, 9.0)], octagon, WEATHERED, smooth=False, start=start, caps=False)
    builder.lathe([(9.9, 9.0), (10.2, 9.3), (10.2, 9.7), (8.6, 9.7)], octagon, ASHLAR, smooth=False, start=start,
                  caps=False)
    builder.lathe([(8.6, 9.7), (8.2, 18.0)], octagon, WEATHERED, smooth=False, start=start, caps=False)
    builder.lathe([(8.2, 18.0), (8.45, 18.3), (8.45, 18.7), (7.3, 18.7)], octagon, ASHLAR, smooth=False,
                  start=start, caps=False)
    builder.lathe([(7.3, 18.7), (7.3, 27.0)], octagon, ASHLAR, smooth=False, start=start, caps=False)
    builder.lathe([(7.3, 27.0), (7.75, 27.3), (7.75, 28.0), (6.3, 28.0)], octagon, ASHLAR, smooth=False,
                  start=start, caps=False)
    builder.lathe([(6.3, 28.0), (6.3, 35.0)], octagon, ASHLAR, smooth=False, start=start, caps=False)
    builder.lathe([(6.3, 35.0), (6.75, 35.3), (6.75, 36.0), (5.9, 36.0), (5.9, 36.6), (0.0, 36.6)], octagon, ASHLAR,
                  smooth=False, start=start, caps=False)
    pilaster_mesh = pilaster(0.85, 8.3, 0.18, ASHLAR)
    tuscan = column("tuscan", 0.75, 7.0, detail="low", material=ASHLAR)
    for corner in range(octagon):
        angle = start + 2 * math.pi * corner / octagon + math.pi / 8
        apothem_middle = 7.3 * math.cos(math.pi / octagon)
        for along in (-1.4, 1.4):
            frame = Matrix.Rotation(angle - math.pi / 2, 4, "Z")
            frame.translation = (math.cos(angle) * apothem_middle - math.sin(angle) * along,
                                 math.sin(angle) * apothem_middle + math.cos(angle) * along, 18.7)
            builder.merge(pilaster_mesh, frame)
        corner_angle = start + 2 * math.pi * corner / octagon
        builder.merge(tuscan, placement(math.cos(corner_angle) * 6.3, math.sin(corner_angle) * 6.3, 28.0))
        window_frame = Matrix.Rotation(angle - math.pi / 2, 4, "Z")
        window_frame.translation = (math.cos(angle) * (6.3 * math.cos(math.pi / octagon) - 0.1),
                                    math.sin(angle) * (6.3 * math.cos(math.pi / octagon) - 0.1), 31.5)
        builder.centered_box((0.0, 0.0, 0.0), (1.2, 0.4, 2.4), VOID, matrix=window_frame)
    return builder


def courtyard_house(width, depth, court_width, court_depth, height, wall_material, roof_pitch=0.35,
                    court_material="garden_green", door_side=-1, foundation=3.0):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    cw, cd = court_width / 2, court_depth / 2
    wings = [((-hw, -hd), (hw, -cd)), ((-hw, cd), (hw, hd)), ((-hw, -cd), (-cw, cd)), ((cw, -cd), (hw, cd))]
    for (x0, y0), (x1, y1) in wings:
        builder.box((x0, y0, -foundation), (x1, y1, height), wall_material, bottom=False, top=False)
    builder.box((-cw, -cd, -0.2), (cw, cd, 0.05), court_material, bottom=False)
    rise = roof_pitch
    roof_wings = [((-hw - 0.3, -hd - 0.3), (hw + 0.3, -cd), "y", -1), ((-hw - 0.3, cd), (hw + 0.3, hd + 0.3), "y", 1),
                  ((-hw - 0.3, -cd), (-cw, cd), "x", -1), ((cw, -cd), (hw + 0.3, cd), "x", 1)]
    for (x0, y0), (x1, y1), axis, side in roof_wings:
        if axis == "y":
            ridge_y = (y0 + y1) / 2
            span = (y1 - y0) / 2
            top = height + span * rise
            for edge_y in (y0, y1):
                corners = [(x0, edge_y, height), (x1, edge_y, height), (x1, ridge_y, top), (x0, ridge_y, top)]
                builder.oriented(corners, (0, edge_y - ridge_y, 1), TILES)
            for x in (x0, x1):
                builder.oriented([(x, y0, height), (x, y1, height), (x, ridge_y, top)], (x, 0, 0), wall_material)
        else:
            ridge_x = (x0 + x1) / 2
            span = (x1 - x0) / 2
            top = height + span * rise
            for edge_x in (x0, x1):
                corners = [(edge_x, y0, height), (edge_x, y1, height), (ridge_x, y1, top), (ridge_x, y0, top)]
                builder.oriented(corners, (edge_x - ridge_x, 0, 1), TILES)
    door_y = door_side * (hd + 0.02)
    builder.oriented([(-0.9, door_y, 0.0), (0.9, door_y, 0.0), (0.9, door_y, 2.8), (-0.9, door_y, 2.8)],
                     (0, door_side, 0), VOID)
    for x in (-hw * 0.6, hw * 0.6):
        builder.oriented([(x - 0.35, door_y, height - 1.6), (x + 0.35, door_y, height - 1.6),
                          (x + 0.35, door_y, height - 0.8), (x - 0.35, door_y, height - 0.8)], (0, door_side, 0), VOID)
    return builder


def block_house(width, depth, height, wall_material, roof_pitch=0.4, shops=0, foundation=3.0, windows=2):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    builder.box((-hw, -hd, -foundation), (hw, hd, height), wall_material, bottom=False, top=False)
    top = height + hd * roof_pitch
    for side in (-1, 1):
        corners = [(-hw - 0.4, side * (hd + 0.4), height - 0.16), (hw + 0.4, side * (hd + 0.4), height - 0.16),
                   (hw + 0.4, 0.0, top), (-hw - 0.4, 0.0, top)]
        builder.oriented(corners, (0, side, 1), TILES)
    gable_ends(builder, -hw, hw, hd, height, top, wall_material, along_axis="x")
    front = -hd - 0.02
    if shops:
        spacing = width / shops
        for index in range(shops):
            x = -hw + spacing * (index + 0.5)
            builder.oriented([(x - spacing * 0.32, front, 0.0), (x + spacing * 0.32, front, 0.0),
                              (x + spacing * 0.32, front, 2.6), (x - spacing * 0.32, front, 2.6)], (0, -1, 0), VOID)
    else:
        builder.oriented([(-0.8, front, 0.0), (0.8, front, 0.0), (0.8, front, 2.5), (-0.8, front, 2.5)], (0, -1, 0), VOID)
    floors = max(int(height / 3.2), 1)
    for floor in range(1, floors):
        for index in range(windows):
            x = -hw + width * (index + 0.5) / windows
            z = floor * 3.2 + 0.8
            builder.oriented([(x - 0.4, front, z), (x + 0.4, front, z), (x + 0.4, front, z + 1.1),
                              (x - 0.4, front, z + 1.1)], (0, -1, 0), VOID)
    return builder


def farmstead():
    builder = MeshBuilder()
    builder.merge(block_house(16.0, 8.0, 4.0, "plaster_white", windows=2), placement(0.0, 6.0, 0.0))
    builder.merge(block_house(8.0, 12.0, 3.6, "plaster_ochre", windows=1), placement(-12.0, -2.0, 0.0, math.pi / 2))
    for (x0, y0), (x1, y1) in (((-8.0, -10.0), (12.0, -9.4)), ((11.4, -10.0), (12.0, 2.0))):
        builder.box((x0, y0, -1.5), (x1, y1, 1.8), "plaster_white", bottom=False)
    builder.box((-8.0, -9.4, -0.2), (11.4, 2.0, 0.03), "matte", bottom=False)
    builder.tint(len(builder.polygons) - 5, (0.66, 0.57, 0.44))
    return builder


def lathe_tree(trunk_height, trunk_radius, crown, crown_material, segments=7, seed=0):
    builder = MeshBuilder()
    generator = random.Random(seed)
    phases = [generator.uniform(0, 6.28) for _ in range(3)]

    def wobble(angle):
        return 1.0 + 0.12 * math.sin(3 * angle + phases[0]) + 0.07 * math.sin(5 * angle + phases[1])
    if trunk_height > 0:
        builder.lathe([(trunk_radius, -0.5), (trunk_radius * 0.8, trunk_height + 0.3)], 3, "bark", smooth=True,
                      caps=False)
    builder.lathe(crown, segments, crown_material, smooth=True, radius_scale=wobble)
    return builder


def lobe(builder, center, radius, height, material, segments=6, seed=0, flat=0.0):
    generator = random.Random(seed)
    phase = generator.uniform(0, 6.28)
    x, y, z = center
    profile = [(0.0, -height * (0.55 - flat)), (radius * 0.85, -height * 0.3), (radius, height * 0.08),
               (radius * 0.7, height * 0.38), (0.0, height * 0.5)]
    builder.lathe(profile, segments, material, smooth=True, matrix=placement(x, y, z),
                  radius_scale=lambda angle: 1.0 + 0.14 * math.sin(3 * angle + phase))


def trunk(builder, top, radius, lean=(0.0, 0.0), material="bark", at=(0.0, 0.0, 0.0)):
    shear = Matrix(((1, 0, lean[0] / max(top, 0.1), at[0]), (0, 1, lean[1] / max(top, 0.1), at[1]), (0, 0, 1, at[2]),
                    (0, 0, 0, 1)))
    builder.lathe([(radius * 1.15, -0.5), (radius * 0.75, top)], 4, material, smooth=True,
                  caps=False, matrix=shear)


def cypress(height=11.0, seed=0):
    builder = MeshBuilder()
    r = height * 0.085
    trunk(builder, 0.9, 0.12)
    crown = [(0.0, 0.5), (r * 0.7, height * 0.1), (r, height * 0.22), (r * 0.93, height * 0.4),
             (r * 0.74, height * 0.6), (r * 0.46, height * 0.79), (r * 0.18, height * 0.93), (0.0, height)]
    generator = random.Random(seed)
    phase = generator.uniform(0, 6.28)
    builder.lathe(crown, 10, "foliage_cypress", smooth=True,
                  radius_scale=lambda angle: 1.0 + 0.08 * math.sin(4 * angle + phase))
    return builder


def umbrella_pine(height=13.0, seed=0):
    builder = MeshBuilder()
    base = height * 0.66
    trunk(builder, base + 0.6, 0.26, (0.8, 0.3))
    lobe(builder, (0.8, 0.3, base + 1.2), height * 0.36, 2.6, "foliage_dark", 8, seed, 0.3)
    lobe(builder, (-1.6, -0.6, base + 0.6), height * 0.2, 1.8, "foliage_dark", 6, seed + 1, 0.3)
    return builder


def holm_oak(height=8.0, seed=0):
    builder = MeshBuilder()
    trunk(builder, height * 0.38, 0.2, (0.3, 0.0))
    r = height * 0.32
    lobe(builder, (0.4, 0.2, height * 0.62), r, height * 0.55, "foliage_dark", 6, seed)
    lobe(builder, (-r * 0.75, -r * 0.2, height * 0.5), r * 0.72, height * 0.42, "foliage_dark", 5, seed + 1)
    return builder


def olive_tree(height=4.5, seed=0):
    builder = MeshBuilder()
    trunk(builder, 1.5, 0.17, (0.35, 0.1))
    r = height * 0.33
    lobe(builder, (0.6, 0.3, height * 0.66), r, height * 0.5, "foliage_olive", 6, seed, 0.1)
    lobe(builder, (-0.6, -0.4, height * 0.55), r * 0.8, height * 0.4, "foliage_olive", 5, seed + 3, 0.1)
    return builder


def plane_tree(height=16.0, seed=0):
    builder = MeshBuilder()
    trunk(builder, height * 0.45, 0.4, (0.4, 0.2), "plaster_grey")
    r = height * 0.3
    lobe(builder, (0.4, 0.2, height * 0.68), r, height * 0.5, "foliage_plane", 8, seed)
    lobe(builder, (-r * 0.75, 0.3, height * 0.56), r * 0.7, height * 0.4, "foliage_plane", 7, seed + 1)
    lobe(builder, (r * 0.6, -r * 0.6, height * 0.55), r * 0.7, height * 0.38, "foliage_plane", 7, seed + 2)
    return builder


def scrub(size=1.6, seed=0):
    crown = [(0.0, -0.3), (size * 0.55, size * 0.2), (size * 0.3, size * 0.6), (0.0, size * 0.75)]
    return lathe_tree(0.0, 0.0, crown, "garrigue", 5, seed)


def garden_shrub(builder, x, y, size, seed=0, material="foliage_shrub"):
    lobe(builder, (x, y, size * 0.45), size * 0.55, size * 0.9, material, 5, seed)


def vine_row(length=10.0):
    builder = MeshBuilder()
    half = length / 2
    for x in (-half + 0.2, half - 0.2):
        builder.box((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, 1.2), "dark_wood", bottom=False, top=False)
    builder.prism([(-half, -0.3), (half, -0.3), (half, 0.3), (-half, 0.3)], 0.55, 1.25, "foliage_vine", bottom=False)
    return builder


def mausoleum():
    builder = MeshBuilder()
    builder.box((-2.4, -2.4, -1.0), (2.4, 2.4, 1.2), ASHLAR, bottom=False)
    builder.box((-2.6, -2.6, 1.2), (2.6, 2.6, 1.5), ASHLAR, bottom=False)
    builder.box((-1.9, -1.9, 1.5), (1.9, 1.9, 5.0), ASHLAR, bottom=False)
    for x, y in ((-1.9, -1.9), (1.9, -1.9), (1.9, 1.9), (-1.9, 1.9)):
        builder.centered_box((x, y, 3.25), (0.4, 0.4, 3.5), ASHLAR, bottom=False)
    builder.box((-2.2, -2.2, 5.0), (2.2, 2.2, 5.4), ASHLAR, bottom=False)
    builder.lathe([(3.0, 5.4), (0.0, 7.8)], 4, ASHLAR, smooth=False, start=math.pi / 4)
    builder.centered_box((0.0, -1.95, 3.0), (1.0, 0.1, 1.6), VOID)
    return builder


def funerary_enclosure():
    builder = MeshBuilder()
    for (x0, y0), (x1, y1) in (((-4.0, -4.0), (4.0, -3.5)), ((-4.0, 3.5), (4.0, 4.0)),
                               ((-4.0, -3.5), (-3.5, 3.5)), ((3.5, -3.5), (4.0, 3.5))):
        builder.box((x0, y0, -1.0), (x1, y1, 1.3), ASHLAR, bottom=False)
    for x in (-2.0, 0.0, 2.0):
        builder.box((x - 0.35, 2.2, -0.5), (x + 0.35, 2.45, 1.6), ASHLAR, bottom=False)
    builder.box((-0.9, -1.0, -0.5), (0.9, 1.0, 0.9), ASHLAR, bottom=False)
    return builder


def funerary_stele():
    builder = MeshBuilder()
    builder.box((-0.55, -0.35, -0.6), (0.55, 0.35, 0.3), ASHLAR, bottom=False)
    builder.box((-0.4, -0.12, 0.3), (0.4, 0.12, 1.75), ASHLAR, bottom=False, top=False)
    builder.oriented([(-0.45, -0.12, 1.75), (0.45, -0.12, 1.75), (0.0, -0.12, 2.1)], (0, -1, 0), ASHLAR)
    builder.oriented([(-0.45, 0.12, 1.75), (0.45, 0.12, 1.75), (0.0, 0.12, 2.1)], (0, 1, 0), ASHLAR)
    builder.oriented([(-0.45, -0.12, 1.75), (0.0, -0.12, 2.1), (0.0, 0.12, 2.1), (-0.45, 0.12, 1.75)], (-1, 0, 1), ASHLAR)
    builder.oriented([(0.45, -0.12, 1.75), (0.45, 0.12, 1.75), (0.0, 0.12, 2.1), (0.0, -0.12, 2.1)], (1, 0, 1), ASHLAR)
    builder.centered_box((0.0, -0.125, 1.15), (0.5, 0.02, 0.6), VOID)
    return builder


def tomb_altar():
    builder = MeshBuilder()
    builder.box((-1.2, -1.2, -0.8), (1.2, 1.2, 0.4), ASHLAR, bottom=False)
    builder.box((-0.85, -0.85, 0.4), (0.85, 0.85, 2.4), ASHLAR, bottom=False, top=False)
    builder.box((-1.0, -1.0, 2.4), (1.0, 1.0, 2.75), ASHLAR, bottom=False)
    for side in (-1, 1):
        builder.lathe([(0.0, -0.9), (0.2, -0.9), (0.2, 0.9), (0.0, 0.9)], 6, ASHLAR,
                      matrix=Matrix.Translation((side * 0.75, 0.0, 2.95)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    builder.centered_box((0.0, -0.86, 1.4), (1.1, 0.04, 0.8), VOID)
    return builder


def altar(width=3.2, depth=2.2, height=1.4):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    builder.box((-hw - 0.25, -hd - 0.25, -0.5), (hw + 0.25, hd + 0.25, 0.3), ASHLAR, bottom=False)
    builder.box((-hw, -hd, 0.3), (hw, hd, height), "lens_smooth", bottom=False)
    builder.box((-hw - 0.15, -hd - 0.15, height), (hw + 0.15, hd + 0.15, height + 0.25), "lens_smooth", bottom=False)
    for side in (-1, 1):
        builder.lathe([(0.0, -hd), (0.22, -hd), (0.18, 0.0), (0.22, hd), (0.0, hd)], 8, "lens_smooth",
                      matrix=Matrix.Translation((side * (hw - 0.2), 0.0, height + 0.42)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    return builder

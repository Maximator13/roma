import math
import os

import bpy
from mathutils import Matrix, Vector

from .geometry import MeshBuilder, UP

STONE = "lens_smooth"
FLUTED = "lens_fluted"
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "node_modules",
                         "@fontsource", "cinzel", "files", "cinzel-latin-600-normal.woff")
SHAFT_TOP_RATIO = {"tuscan": 0.78, "ionic": 0.84, "corinthian": 0.85}
CAPITAL_HEIGHT = {"tuscan": 0.5, "ionic": 0.42, "corinthian": 1.15}


def torus_arc(center_radius, center_height, radius, start_degrees, end_degrees, steps):
    return [(center_radius + radius * math.cos(math.radians(start_degrees + (end_degrees - start_degrees) * i / steps)),
             center_height + radius * math.sin(math.radians(start_degrees + (end_degrees - start_degrees) * i / steps)))
            for i in range(steps + 1)]


FULL_ARC = (0.0, 2 * math.pi)


def arc_segments(segments, arc):
    return max(int(round(segments * arc[1] / (2 * math.pi))), 2)


def within_arc(angle, arc, margin=0.0):
    if arc[1] >= 2 * math.pi - 1e-6:
        return True
    return (angle - arc[0] + margin) % (2 * math.pi) <= arc[1] + 2 * margin


def attic_base(builder, diameter, segments, material, arc=FULL_ARC):
    d = diameter
    builder.box((-0.7 * d, -0.7 * d, 0.0), (0.7 * d, 0.7 * d, 0.16 * d), material, bottom=False)
    profile = (torus_arc(0.6 * d, 0.25 * d, 0.09 * d, -90, 90, 4)
               + [(0.55 * d, 0.36 * d), (0.545 * d, 0.39 * d), (0.57 * d, 0.405 * d)]
               + torus_arc(0.55 * d, 0.45 * d, 0.05 * d, -90, 90, 3)
               + [(0.51 * d, 0.5 * d)])
    builder.lathe(profile, arc_segments(segments, arc), material, smooth=True, caps=False, start=arc[0],
                  sweep=arc[1])


def tuscan_base(builder, diameter, segments, material, arc=FULL_ARC):
    d = diameter
    builder.box((-0.62 * d, -0.62 * d, 0.0), (0.62 * d, 0.62 * d, 0.25 * d), material, bottom=False)
    builder.lathe(torus_arc(0.52 * d, 0.37 * d, 0.12 * d, -90, 90, 4) + [(0.5 * d, 0.5 * d)],
                  arc_segments(segments, arc), material, smooth=True, caps=False, start=arc[0], sweep=arc[1])


def fluting(flutes, depth):
    period = 2 * math.pi / flutes

    def scale(angle):
        phase = (angle % period) / period
        if phase < 0.18:
            return 1.0
        return 1.0 - depth * math.sin(math.pi * (phase - 0.18) / 0.82)
    return scale


def shaft(builder, diameter, bottom, top, top_ratio, segments, material, flutes=0, arc=FULL_ARC):
    radius = diameter / 2
    rings = []
    for t in (0.0, 0.15, 0.33, 0.5, 0.67, 0.84, 1.0):
        taper = 0.0 if t <= 0.33 else ((t - 0.33) / 0.67) ** 1.3
        rings.append((radius * (1 - (1 - top_ratio) * taper), bottom + (top - bottom) * t))
    radius_scale = fluting(flutes, 0.09) if flutes else None
    builder.lathe(rings, arc_segments(segments, arc), material, smooth=True, radius_scale=radius_scale, caps=False,
                  start=arc[0], sweep=arc[1])


def concave_abacus_outline(corner_radius, sag, steps=4):
    outline = []
    for side in range(4):
        start_angle = math.radians(45 + 90 * side)
        end_angle = math.radians(135 + 90 * side)
        start = Vector((corner_radius * math.cos(start_angle), corner_radius * math.sin(start_angle)))
        end = Vector((corner_radius * math.cos(end_angle), corner_radius * math.sin(end_angle)))
        middle = (start + end) / 2
        control = middle - middle.normalized() * sag * 2
        for step in range(steps):
            t = step / steps
            point = start * (1 - t) ** 2 + control * 2 * (1 - t) * t + end * t * t
            outline.append((point.x, point.y))
    return outline


def acanthus_leaf(builder, angle, bottom, height, base_radius, flare, width, diameter, material):
    radial = Vector((math.cos(angle), math.sin(angle), 0.0))
    lateral = Vector((-math.sin(angle), math.cos(angle), 0.0))
    rows = []
    for t, width_factor, outward, lift in ((0.0, 1.0, 0.0, 0.0), (0.4, 1.1, 0.03, 0.4), (0.72, 0.9, 0.09, 0.72),
                                           (0.9, 0.55, 0.16, 0.9), (1.0, 0.15, 0.22, 0.93)):
        radius = base_radius + flare * t + outward * diameter
        row = []
        for across in (-1.0, -0.5, 0.0, 0.5, 1.0):
            rib = (0.015 * diameter) * (1 - abs(across)) if t < 0.95 else 0.0
            point = radial * (radius + rib) + lateral * (across * width_factor * width / 2)
            point.z = bottom + height * lift
            row.append(point)
        rows.append(row)
    builder.surface(rows, material, smooth=True, facing=radial)


def corinthian_capital(builder, diameter, bottom, material, detail, arc=FULL_ARC):
    d = diameter
    h = CAPITAL_HEIGHT["corinthian"] * d
    top_radius = d / 2 * SHAFT_TOP_RATIO["corinthian"]
    segments = arc_segments(24 if detail == "high" else 12, arc)
    builder.lathe(torus_arc(top_radius, bottom + 0.03 * d, 0.035 * d, -90, 90, 3 if detail == "high" else 2),
                  segments, material, smooth=True, caps=False, start=arc[0], sweep=arc[1])
    bell = [(top_radius * 0.97, bottom + 0.06 * d), (top_radius, bottom + 0.3 * h), (0.47 * d, bottom + 0.72 * h),
            (0.53 * d, bottom + 0.86 * h), (0.55 * d, bottom + 0.88 * h)]
    builder.lathe(bell, segments, material, smooth=True, caps=False, start=arc[0], sweep=arc[1])
    abacus_bottom = bottom + 0.88 * h
    outline = concave_abacus_outline(0.74 * d, 0.07 * d, 4 if detail == "high" else 2)
    builder.prism(outline, abacus_bottom, bottom + h, material)
    leaf_width = 2 * math.pi * top_radius * 1.12 / 8
    if detail == "high":
        for index in range(8):
            if within_arc(math.radians(22.5 + 45 * index), arc, 0.2):
                acanthus_leaf(builder, math.radians(22.5 + 45 * index), bottom + 0.05 * d, 0.4 * h, top_radius,
                              0.02 * d, leaf_width, d, material)
            if within_arc(math.radians(45 * index), arc, 0.2):
                acanthus_leaf(builder, math.radians(45 * index), bottom + 0.08 * d, 0.66 * h, top_radius * 0.98,
                              0.05 * d, leaf_width * 1.05, d, material)
        for index in range(4):
            angle = math.radians(45 + 90 * index)
            if not within_arc(angle, arc, 0.3):
                continue
            radial = Vector((math.cos(angle), math.sin(angle), 0.0))
            tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
            center = radial * 0.62 * d + Vector((0, 0, bottom + 0.8 * h))
            frame = Matrix((tangent.cross(radial), radial, tangent)).transposed().to_4x4()
            frame.translation = center
            builder.lathe([(0.0, -0.05 * d), (0.085 * d, -0.05 * d), (0.085 * d, 0.05 * d), (0.0, 0.05 * d)],
                          8, material, smooth=True, matrix=frame)
            stem = [radial * 0.47 * d + Vector((0, 0, bottom + 0.55 * h)),
                    radial * 0.53 * d + Vector((0, 0, bottom + 0.7 * h)),
                    radial * 0.6 * d + Vector((0, 0, bottom + 0.78 * h))]
            builder.sweep(stem, [(-0.03 * d, -0.02 * d), (0.03 * d, -0.02 * d), (0.03 * d, 0.02 * d),
                                 (-0.03 * d, 0.02 * d)], material, facade_normal=tangent)
            face_angle = math.radians(90 * index)
            face_point = Vector((math.cos(face_angle), math.sin(face_angle), 0.0)) * 0.50 * d
            builder.centered_box((face_point.x, face_point.y, abacus_bottom + 0.06 * h),
                                 (0.12 * d, 0.12 * d, 0.13 * d), material)
    else:
        for index in range(8):
            angle = math.radians(45 * index)
            if not within_arc(angle, arc, 0.2):
                continue
            radial = Vector((math.cos(angle), math.sin(angle), 0.0))
            lateral = Vector((-math.sin(angle), math.cos(angle), 0.0))
            rows = []
            for lift, outward, width_factor in ((0.05, 0.0, 1.0), (0.45, 0.04, 1.05), (0.75, 0.13, 0.4)):
                center = radial * (top_radius + outward * d)
                rows.append([center - lateral * leaf_width * width_factor / 2 + Vector((0, 0, bottom + lift * h)),
                             center + lateral * leaf_width * width_factor / 2 + Vector((0, 0, bottom + lift * h))])
            builder.surface(rows, material, smooth=True, facing=radial)


def ionic_capital(builder, diameter, bottom, material):
    d = diameter
    top_radius = d / 2 * SHAFT_TOP_RATIO["ionic"]
    builder.lathe([(top_radius, bottom), (0.55 * d, bottom + 0.12 * d), (0.56 * d, bottom + 0.18 * d),
                   (0.5 * d, bottom + 0.22 * d)], 16, material, smooth=True, caps=False)
    builder.box((-0.62 * d, -0.4 * d, bottom + 0.18 * d), (0.62 * d, 0.4 * d, bottom + 0.34 * d), material)
    for side in (-1, 1):
        frame = Matrix.Rotation(math.radians(90), 4, "X")
        frame.translation = (side * 0.6 * d, 0.0, bottom + 0.2 * d)
        builder.lathe([(0.0, -0.4 * d), (0.17 * d, -0.4 * d), (0.15 * d, -0.2 * d), (0.13 * d, 0.0),
                       (0.15 * d, 0.2 * d), (0.17 * d, 0.4 * d), (0.0, 0.4 * d)], 12, material, smooth=True,
                      matrix=frame)
    builder.box((-0.58 * d, -0.58 * d, bottom + 0.34 * d), (0.58 * d, 0.58 * d, bottom + 0.42 * d), material)


def tuscan_capital(builder, diameter, bottom, material, segments=16, arc=FULL_ARC):
    d = diameter
    top_radius = d / 2 * SHAFT_TOP_RATIO["tuscan"]
    profile = (torus_arc(top_radius, bottom + 0.04 * d, 0.04 * d, -90, 90, 2)
               + [(top_radius, bottom + 0.12 * d), (top_radius + 0.02 * d, bottom + 0.14 * d),
                  (0.52 * d, bottom + 0.25 * d), (0.58 * d, bottom + 0.33 * d)])
    builder.lathe(profile, arc_segments(segments, arc), material, smooth=True, caps=False, start=arc[0],
                  sweep=arc[1])
    builder.box((-0.6 * d, -0.6 * d, bottom + 0.33 * d), (0.6 * d, 0.6 * d, bottom + 0.5 * d), material)


ENGAGED_HALF = (math.pi / 2 - (math.pi + 0.3) / 2, math.pi + 0.3)


def engaged_corner(facing_angle):
    return (facing_angle - 0.75 * math.pi, 1.5 * math.pi)


def column(order, diameter, height, detail="high", material=STONE, arc=FULL_ARC):
    builder = MeshBuilder()
    segments = {"high": 24, "medium": 16, "low": 10}[detail]
    if order == "tuscan":
        tuscan_base(builder, diameter, segments, material, arc)
    else:
        attic_base(builder, diameter, segments, material, arc)
    capital_bottom = height - CAPITAL_HEIGHT[order] * diameter
    flutes = 24 if (order != "tuscan" and detail == "high") else 0
    shaft_segments = flutes * 3 if flutes else segments
    shaft_material = FLUTED if (order != "tuscan" and detail == "medium" and material == STONE) else material
    shaft(builder, diameter, 0.5 * diameter, capital_bottom, SHAFT_TOP_RATIO[order], shaft_segments, shaft_material,
          flutes, arc)
    if order == "corinthian":
        corinthian_capital(builder, diameter, capital_bottom, material, detail, arc)
    elif order == "ionic":
        ionic_capital(builder, diameter, capital_bottom, material)
    else:
        tuscan_capital(builder, diameter, capital_bottom, material, max(segments, 8), arc)
    return builder


def pilaster(width, height, depth, material=STONE):
    builder = MeshBuilder()
    w = width
    builder.box((-0.62 * w, 0.0, 0.0), (0.62 * w, depth + 0.12 * w, 0.18 * w), material, bottom=False)
    builder.box((-0.56 * w, 0.0, 0.18 * w), (0.56 * w, depth + 0.07 * w, 0.32 * w), material, bottom=False)
    builder.box((-0.5 * w, 0.0, 0.32 * w), (0.5 * w, depth, height - 0.45 * w), material, bottom=False, top=False)
    builder.box((-0.56 * w, 0.0, height - 0.45 * w), (0.56 * w, depth + 0.06 * w, height - 0.2 * w), material,
                bottom=False)
    builder.box((-0.64 * w, 0.0, height - 0.2 * w), (0.64 * w, depth + 0.14 * w, height), material)
    return builder


def corinthian_entablature_profile(diameter):
    d = diameter
    points = [(-0.45, 0.0), (0.40, 0.0), (0.40, 0.22), (0.42, 0.24), (0.42, 0.44), (0.45, 0.46), (0.45, 0.64),
              (0.50, 0.69), (0.51, 0.75), (0.43, 0.75), (0.43, 1.48), (0.47, 1.50), (0.49, 1.56), (0.49, 1.60),
              (0.50, 1.60), (0.50, 1.76), (0.53, 1.78), (0.58, 1.84), (0.60, 1.84), (0.60, 2.06), (1.22, 2.06),
              (1.22, 2.26), (1.27, 2.28), (1.32, 2.36), (1.40, 2.44), (1.45, 2.50), (-0.45, 2.50)]
    return [(out * d, up * d) for out, up in points]


def raking_cornice_profile(diameter):
    d = diameter
    points = [(-0.45, 0.0), (0.47, 0.0), (0.49, 0.06), (0.49, 0.10), (0.50, 0.10), (0.50, 0.26), (0.53, 0.28),
              (0.58, 0.34), (0.60, 0.34), (0.60, 0.56), (1.22, 0.56), (1.22, 0.76), (1.27, 0.78), (1.32, 0.86),
              (1.40, 0.94), (1.45, 1.0), (-0.45, 1.0)]
    return [(out * d, up * d) for out, up in points]


def simple_entablature_profile(height, projection):
    h = height
    p = projection
    return [(-0.5, 0.0), (0.0, 0.0), (0.0, 0.42 * h), (0.04 * p, 0.45 * h), (0.04 * p, 0.6 * h),
            (0.25 * p, 0.66 * h), (0.6 * p, 0.72 * h), (p, 0.78 * h), (p, 0.92 * h), (p * 1.05, h), (-0.5, h)]


def dentil(diameter, material=STONE):
    d = diameter
    return MeshBuilder().box((-0.055 * d, 0.48 * d, 1.61 * d), (0.055 * d, 0.62 * d, 1.76 * d), material, bottom=True)


def modillion(diameter, material=STONE):
    d = diameter
    builder = MeshBuilder()
    builder.box((-0.11 * d, 0.58 * d, 1.95 * d), (0.11 * d, 1.16 * d, 2.065 * d), material)
    builder.box((-0.1 * d, 0.58 * d, 1.86 * d), (0.1 * d, 0.84 * d, 1.95 * d), material)
    builder.box((-0.09 * d, 0.98 * d, 1.9 * d), (0.09 * d, 1.12 * d, 1.95 * d), material)
    return builder


def instance_frame(origin, outward, upward):
    outward = Vector(outward).normalized()
    upward = Vector(upward).normalized()
    along = outward.cross(upward).normalized()
    frame = Matrix((along, outward, upward)).transposed().to_4x4()
    frame.translation = origin
    return frame


def frames_along(path, spacing, closed, margin, facade_normal=None, base_height=0.0):
    frames = []
    count = len(path)
    segment_count = count if closed else count - 1
    outward_of = []
    for index in range(segment_count):
        tangent = (Vector(path[(index + 1) % count]) - Vector(path[index])).normalized()
        if facade_normal is None:
            outward_of.append((Vector((tangent.y, -tangent.x, 0.0)), UP.copy()))
        else:
            outward_of.append((Vector(facade_normal), tangent.cross(Vector(facade_normal)).normalized()))
    shared_corners = margin <= 1e-6
    for index in range(segment_count):
        start = Vector(path[index])
        end = Vector(path[(index + 1) % count])
        direction = end - start
        length = direction.length
        tangent = direction / length
        outward, upward = outward_of[index]
        usable = length - 2 * margin
        if usable <= 0:
            continue
        count_items = max(int(usable / spacing), 1)
        step = usable / count_items
        first_item = 1 if shared_corners else 0
        last_item = count_items - 1 if shared_corners else count_items
        for item in range(first_item, last_item + 1):
            point = start + tangent * (margin + step * item) + upward * base_height
            frames.append(instance_frame(point, outward, upward))
    if shared_corners:
        for index in range(count):
            previous = index - 1 if index > 0 else (segment_count - 1 if closed else None)
            following = index if index < segment_count else None
            normals = [outward_of[item] for item in (previous, following) if item is not None]
            outward = sum((normal for normal, _ in normals), Vector((0.0, 0.0, 0.0))).normalized()
            upward = normals[0][1]
            frames.append(instance_frame(Vector(path[index]) + upward * base_height, outward, upward))
    return frames


def tile_roof(builder, ridge_start, ridge_end, eave_offset, material, pitch=0.5, imbrex=True):
    ridge_start = Vector(ridge_start)
    ridge_end = Vector(ridge_end)
    eave_offset = Vector(eave_offset)
    along = ridge_end - ridge_start
    length = along.length
    direction = along / length
    normal = direction.cross(eave_offset).normalized()
    if normal.z < 0:
        normal = -normal
    channels = max(int(round(length / pitch)), 1)
    actual_pitch = length / channels
    if not imbrex:
        corners = [ridge_start, ridge_end, ridge_end + eave_offset, ridge_start + eave_offset]
        if (corners[1] - corners[0]).cross(corners[3] - corners[0]).dot(normal) < 0:
            corners.reverse()
        builder.polygon(corners, material)
        return builder
    shape = [(0.0, 0.0), (0.6, 0.0), (0.63, 0.1), (0.7, 0.2), (0.8, 0.24), (0.9, 0.2), (0.97, 0.1)]
    cross_section = []
    for channel in range(channels):
        for s, h in shape:
            cross_section.append((channel + s, h))
    cross_section.append((channels, 0.0))
    rows = []
    for offset in (Vector((0, 0, 0)), eave_offset):
        rows.append([ridge_start + direction * s * actual_pitch + normal * h * actual_pitch * 0.55 + offset
                     for s, h in cross_section])
    test = (rows[0][1] - rows[0][0]).cross(rows[1][0] - rows[0][0])
    if test.dot(normal) < 0:
        rows.reverse()
    builder.surface(rows, material, smooth=False)
    eave_row = [ridge_start + eave_offset + direction * s * actual_pitch + normal * h * actual_pitch * 0.55
                for s, h in cross_section]
    outward = eave_offset.normalized()
    for channel in range(channels):
        arch = eave_row[channel * len(shape) + 1: channel * len(shape) + len(shape)] + [eave_row[(channel + 1) * len(shape)]]
        if (arch[1] - arch[0]).cross(arch[-1] - arch[0]).dot(outward) < 0:
            arch.reverse()
        builder.polygon(arch, material)
    return builder


def ridge_cap(builder, start, end, radius, material, segments=6):
    start = Vector(start)
    end = Vector(end)
    direction = (end - start).normalized()
    frame = Matrix((direction.cross(UP).normalized(), UP.copy(), direction)).transposed()
    frame = frame.to_4x4()
    frame.translation = start
    length = (end - start).length
    profile = [(radius * math.cos(math.pi * i / segments), radius * math.sin(math.pi * i / segments))
               for i in range(segments + 1)]
    rows = [[frame @ Vector((x, y, 0.0)) for x, y in profile], [frame @ Vector((x, y, length)) for x, y in profile]]
    builder.surface(rows, material)
    return builder


def gable_roof(builder, length_start, length_end, half_width, eave_height, ridge_height, material,
               along_axis="y", imbrex=True, pitch=0.5):
    def point(along, across, height):
        return (across, along, height) if along_axis == "y" else (along, across, height)
    for side in (-1, 1):
        ridge_a = point(length_start, 0.0, ridge_height)
        ridge_b = point(length_end, 0.0, ridge_height)
        eave = Vector(point(0.0, side * half_width, eave_height)) - Vector(point(0.0, 0.0, ridge_height))
        tile_roof(builder, ridge_a, ridge_b, eave, material, pitch, imbrex)
    if imbrex:
        ridge_cap(builder, point(length_start, 0.0, ridge_height + 0.05), point(length_end, 0.0, ridge_height + 0.05),
                  0.16, material)
    return builder


def gable_ends(builder, length_start, length_end, half_width, eave_height, ridge_height, material, along_axis="y"):
    for along, facing in ((length_start, -1), (length_end, 1)):
        if along_axis == "y":
            triangle = [(-half_width, along, eave_height), (half_width, along, eave_height), (0.0, along, ridge_height)]
        else:
            triangle = [(along, half_width, eave_height), (along, -half_width, eave_height), (along, 0.0, ridge_height)]
        if facing < 0:
            triangle.reverse()
        builder.polygon(triangle, material)
    return builder


def podium(builder, half_width, back, front, height, stair_depth, cheek, material="lens_ashlar",
           moulding_material=STONE, steps=15):
    outline = [(-half_width, back), (half_width, back), (half_width, front), (half_width - cheek, front),
               (half_width - cheek, front - stair_depth), (-half_width + cheek, front - stair_depth),
               (-half_width + cheek, front), (-half_width, front)]
    builder.prism(outline, 0.0, height, material, bottom=False)
    path = [(-half_width + cheek, front, 0.0), (-half_width, front, 0.0), (-half_width, back, 0.0),
            (half_width, back, 0.0), (half_width, front, 0.0), (half_width - cheek, front, 0.0)]
    base_profile = [(-0.3, 0.0), (0.35, 0.0), (0.35, 0.25), (0.28, 0.3), (0.22, 0.42), (0.12, 0.5), (0.05, 0.6),
                    (0.0, 0.65), (-0.3, 0.65)]
    crown_profile = [(-0.3, height - 0.75), (0.0, height - 0.75), (0.08, height - 0.65), (0.15, height - 0.5),
                     (0.2, height - 0.42), (0.2, height - 0.3), (0.32, height - 0.22), (0.4, height - 0.1),
                     (0.4, height), (-0.3, height)]
    builder.sweep(path, base_profile, moulding_material)
    builder.sweep(path, crown_profile, moulding_material)
    rise = height / steps
    tread = stair_depth / steps
    for step in range(steps):
        builder.box((-half_width + cheek + 0.01, front - stair_depth, step * rise),
                    (half_width - cheek - 0.01, front - step * tread, (step + 1) * rise), material, bottom=False)
    return builder


def roman_font():
    return bpy.data.fonts.load(FONT_PATH, check_existing=True)


def text_mesh(text, size):
    curve = bpy.data.curves.new("text_probe", type="FONT")
    curve.font = roman_font()
    curve.body = text
    curve.size = size
    holder = bpy.data.objects.new("text_probe", curve)
    bpy.context.scene.collection.objects.link(holder)
    return curve, holder


def cap_height_ratio():
    curve, holder = text_mesh("H", 1.0)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(holder.evaluated_get(depsgraph))
    heights = [vertex.co.y for vertex in mesh.vertices]
    ratio = max(heights) - min(heights)
    bpy.data.objects.remove(holder)
    bpy.data.curves.remove(curve)
    bpy.data.meshes.remove(mesh)
    return ratio


def inscription(text, letter_height, material="bronze_gilt", depth=0.035):
    curve = bpy.data.curves.new("inscription_text", type="FONT")
    curve.font = roman_font()
    curve.body = text
    curve.size = letter_height / cap_height_ratio()
    curve.extrude = depth / 2
    curve.resolution_u = 2
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    holder = bpy.data.objects.new("inscription_text", curve)
    bpy.context.scene.collection.objects.link(holder)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(holder.evaluated_get(depsgraph))
    builder = MeshBuilder()
    offset = len(builder.positions)
    for vertex in mesh.vertices:
        builder.point(vertex.co)
    for polygon in mesh.polygons:
        builder.face([offset + index for index in polygon.vertices], material)
    width = max((vertex.co.x for vertex in mesh.vertices), default=0.0) - min((vertex.co.x for vertex in mesh.vertices),
                                                                            default=0.0)
    bpy.data.objects.remove(holder)
    bpy.data.curves.remove(curve)
    bpy.data.meshes.remove(mesh)
    return builder, width


def facing_text_matrix(origin, outward):
    outward = Vector(outward).normalized()
    reading = UP.cross(outward).normalized()
    frame = Matrix((reading, UP.copy(), outward)).transposed().to_4x4()
    frame.translation = origin
    return frame

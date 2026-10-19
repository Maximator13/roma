import math

from mathutils import Matrix, Vector

from .buildings import ASHLAR, TILES, VOID, WEATHERED, arched_wall, straight_moulding
from .geometry import MATTE as MATTE_LEAD, MeshBuilder, placement
from .orders import (ENGAGED_HALF, STONE, column, corinthian_entablature_profile, dentil, engaged_corner,
                     facing_text_matrix, frames_along, gable_roof, inscription, modillion, podium,
                     pilaster, raking_cornice_profile, simple_entablature_profile)


class TempleLayout:
    def __init__(self, spacing=2.4, front_columns=6, flank_columns=11, diameter=0.9, column_height=9.0,
                 podium_height=2.85, steps=15, tread=0.3, cheek=1.0, side_margin=0.77, end_margin=1.2,
                 pronaos_bays=3, pediment_degrees=15.0):
        self.spacing = spacing
        self.front_columns = front_columns
        self.flank_columns = flank_columns
        self.diameter = diameter
        self.column_height = column_height
        self.podium_height = podium_height
        self.steps = steps
        self.cheek = cheek
        self.stair_depth = steps * tread
        self.axis_half_width = spacing * (front_columns - 1) / 2
        self.half_width = self.axis_half_width + side_margin
        podium_length = spacing * (flank_columns - 1) + 2 * end_margin
        total = podium_length + self.stair_depth
        self.back = -total / 2
        self.front = total / 2
        self.axis_back = self.back + end_margin
        self.axis_front = self.back + podium_length - end_margin
        self.cella_front = self.axis_front - pronaos_bays * spacing
        self.entablature = podium_height + column_height
        self.cornice_top = self.entablature + 2.5 * diameter
        self.raking_half = self.axis_half_width + 1.45 * diameter
        self.rise = self.raking_half * math.tan(math.radians(pediment_degrees))
        self.apex = self.cornice_top + self.rise + 1.0 * diameter

    def rectangle(self, z):
        w = self.axis_half_width
        return [(-w, self.axis_back, z), (w, self.axis_back, z), (w, self.axis_front, z), (-w, self.axis_front, z)]

    def column_frames(self):
        w = self.axis_half_width
        s = self.spacing
        z = self.podium_height
        free = [placement(-w + s * i, self.axis_front, z) for i in range(self.front_columns)]
        engaged = []
        corners = []
        for k in range(1, self.flank_columns):
            y = self.axis_front - s * k
            is_free = y > self.cella_front + 1e-6
            for side in (-1, 1):
                if k == self.flank_columns - 1:
                    corners.append(placement(side * w, y, z, math.radians(135 if side < 0 else 225)))
                elif is_free:
                    free.append(placement(side * w, y, z))
                else:
                    engaged.append(placement(side * w, y, z, math.radians(90 if side < 0 else -90)))
        for i in range(1, self.front_columns - 1):
            engaged.append(placement(-w + s * i, self.axis_back, z, math.pi))
        return {"free": free, "engaged": engaged, "corner": corners}


def temple_columns(layout):
    d = layout.diameter
    h = layout.column_height
    return {
        "free": lambda: column("corinthian", d, h, "high"),
        "engaged": lambda: column("corinthian", d, h, "medium", arc=ENGAGED_HALF),
        "corner": lambda: column("corinthian", d, h, "medium", arc=engaged_corner(math.pi / 2)),
    }


def cella(builder, layout, door_width=3.27, door_height=6.87, wall=0.85):
    w = layout.axis_half_width
    z0 = layout.podium_height
    z1 = layout.entablature
    t = wall / 2
    yb, yc = layout.axis_back, layout.cella_front
    builder.box((-w - t, yb - t, z0), (-w + t, yc + t, z1), ASHLAR, bottom=False, top=False)
    builder.box((w - t, yb - t, z0), (w + t, yc + t, z1), ASHLAR, bottom=False, top=False)
    builder.box((-w + t, yb - t, z0), (w - t, yb + t, z1), ASHLAR, bottom=False, top=False)
    half_door = door_width / 2
    builder.box((-w + t, yc - t, z0), (-half_door - 0.45, yc + t, z1), ASHLAR, bottom=False, top=False)
    builder.box((half_door + 0.45, yc - t, z0), (w - t, yc + t, z1), ASHLAR, bottom=False, top=False)
    builder.box((-half_door - 0.45, yc - t, z0 + door_height + 0.45), (half_door + 0.45, yc + t, z1), ASHLAR,
                bottom=False, top=False)
    for side in (-1, 1):
        builder.box((side * half_door, yc + t - 0.05, z0), (side * (half_door + 0.45), yc + t + 0.12,
                                                            z0 + door_height + 0.45), STONE, bottom=False)
    builder.box((-half_door - 0.45, yc + t - 0.05, z0 + door_height), (half_door + 0.45, yc + t + 0.16,
                                                                       z0 + door_height + 0.6), STONE)
    builder.box((-half_door, yc - 0.1, z0), (half_door, yc + 0.05, z0 + door_height), "dark_wood", bottom=False)
    for x in (-half_door * 0.5, half_door * 0.5):
        builder.box((x - 0.04, yc + 0.05, z0 + 0.4), (x + 0.04, yc + 0.09, z0 + door_height - 0.4), "bronze_gilt")
    ceiling = layout.entablature + 0.7 * layout.diameter
    builder.box((-w + 0.3, layout.axis_back + 0.3, ceiling), (w - 0.3, layout.axis_front - 0.3, ceiling + 0.2),
                STONE, top=False)
    return builder


def pediment(builder, layout, facing):
    d = layout.diameter
    y = layout.axis_front if facing > 0 else layout.axis_back
    z = layout.cornice_top - 0.02
    half = layout.raking_half
    left = (-half * facing, y, z)
    right = (half * facing, y, z)
    builder.sweep([left, (0.0, y, z + layout.rise), right], raking_cornice_profile(d), STONE,
                  facade_normal=(0, facing, 0))
    face_y = y + facing * 0.39 * d
    inner = half - 1.1 * d
    builder.oriented([(-inner, face_y, z), (inner, face_y, z), (0.0, face_y, z + layout.rise * inner / half)],
                     (0, facing, 0), STONE)
    return builder


def rinceau_frieze(builder, layout):
    d = layout.diameter
    w = layout.axis_half_width + 0.43 * d + 0.006
    y0 = layout.axis_back - 0.43 * d - 0.006
    y1 = layout.axis_front + 0.43 * d + 0.006
    z0 = layout.entablature + 0.76 * d
    z1 = layout.entablature + 1.47 * d
    repeat = (z1 - z0) * 8.0
    faces = [
        [(w, y0, z0), (w, y1, z0), (w, y1, z1), (w, y0, z1)],
        [(-w, y1, z0), (-w, y0, z0), (-w, y0, z1), (-w, y1, z1)],
        [(-w, y0, z0), (w, y0, z0), (w, y0, z1), (-w, y0, z1)],
    ]
    for corners in faces:
        length = (Vector(corners[1]) - Vector(corners[0])).length
        uvs = [(0.0, 0.0), (length / repeat, 0.0), (length / repeat, 1.0), (0.0, 1.0)]
        builder.polygon(corners, "frieze_rinceau", uvs=uvs)


def raking_ornament(builder, layout, facing):
    d = layout.diameter
    y = layout.axis_front if facing > 0 else layout.axis_back
    z = layout.cornice_top - 0.02
    half = layout.raking_half
    path = [(-half * facing, y, z), (0.0, y, z + layout.rise), (half * facing, y, z)]
    for spacing, piece in ((0.66, modillion(d)), (0.2, dentil(d))):
        for frame in frames_along(path, spacing, False, 0.55, facade_normal=(0, facing, 0), base_height=-1.5 * d):
            builder.merge(piece, frame)


def lion_heads(builder, layout, spacing=0.66):
    d = layout.diameter
    z = layout.entablature + 2.36 * d
    count = int((layout.axis_front - layout.axis_back) / spacing)
    for side in (-1, 1):
        x = side * (layout.axis_half_width + 1.45 * d + 0.03)
        for index in range(count + 1):
            y = layout.axis_back + index * spacing
            builder.lathe([(0.0, -0.1), (0.07, -0.08), (0.095, 0.0), (0.07, 0.08), (0.0, 0.1)], 6, STONE,
                          matrix=Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))


def maison_carree_body(layout, frieze_text, architrave_text):
    builder = MeshBuilder()
    d = layout.diameter
    podium(builder, layout.half_width, layout.back, layout.front, layout.podium_height, layout.stair_depth,
           layout.cheek, steps=layout.steps)
    cella(builder, layout)
    builder.sweep(layout.rectangle(layout.entablature), corinthian_entablature_profile(d), STONE, closed=True)
    for frame in frames_along(layout.rectangle(layout.entablature), 0.2, True, 0.0):
        builder.merge(dentil(d), frame)
    for frame in frames_along(layout.rectangle(layout.entablature), 0.66, True, 0.0):
        builder.merge(modillion(d), frame)
    pediment(builder, layout, 1)
    pediment(builder, layout, -1)
    raking_ornament(builder, layout, 1)
    raking_ornament(builder, layout, -1)
    rinceau_frieze(builder, layout)
    lion_heads(builder, layout)
    roof_low = layout.cornice_top + 0.8 * d
    gable_roof(builder, layout.axis_back - 0.9, layout.axis_front + 0.9, layout.raking_half + 0.1, roof_low,
               roof_low + layout.rise + 0.1 * math.tan(math.radians(15)), "roof_tiles", along_axis="y", pitch=0.55)
    frieze_face = layout.axis_front + 0.43 * d + 0.02
    available = 2 * layout.axis_half_width
    for text, height, z, face in ((frieze_text, 0.3, layout.entablature + 1.11 * d, frieze_face),
                                  (architrave_text, 0.22, layout.entablature + 0.33 * d,
                                   layout.axis_front + 0.42 * d + 0.02)):
        letters, width = inscription(text, height)
        scale = min(1.0, available * 0.92 / max(width, 1e-3))
        builder.merge(letters, facing_text_matrix((0.0, face, z), (0, 1, 0)) @ Matrix.Scale(scale, 4))
    return builder


def portico_wing(length, depth=7.0, column_height=5.6, wall_material="plaster", floor="paving"):
    builder = MeshBuilder()
    hl = length / 2
    stylobate = 0.45
    top = stylobate + column_height
    beam = 0.95
    back_top = top + beam + 2.4
    builder.box((-hl, -depth - 0.8, -1.5), (hl, 0.75, stylobate), floor, bottom=False)
    builder.box((-hl, -0.38, top), (hl, 0.38, top + beam * 0.72), STONE, bottom=True)
    straight_moulding(builder, -hl, hl, top + beam * 0.72, simple_entablature_profile(beam * 0.28, 0.32), STONE,
                      y=0.38)
    builder.box((-hl, -depth - 0.8, stylobate), (hl, -depth, back_top), wall_material, bottom=False)
    builder.box((-hl, -depth, top + beam - 0.12), (hl, 0.38, top + beam), "dark_wood", top=False)
    builder.oriented([(-hl - 0.2, 0.9, top + beam), (hl + 0.2, 0.9, top + beam),
                      (hl + 0.2, -depth - 0.9, back_top + 0.1), (-hl - 0.2, -depth - 0.9, back_top + 0.1)],
                     (0, 1, 1), TILES)
    for x in (-hl, hl):
        builder.oriented([(x, 0.38, top + beam), (x, -depth, top + beam), (x, -depth, back_top)],
                         (x, 0, 0), wall_material)
    return builder


def portico_columns(length, spacing, column_height=5.6):
    count = max(int(round(length / spacing)), 1)
    step = length / count
    return [placement(-length / 2 + step * (index + 0.5), 0.0, 0.45) for index in range(count)]


def curia(width=22.0, depth=17.0, height=12.0):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    base = 1.2
    builder.box((-hw - 0.4, -hd - 0.4, -1.5), (hw + 0.4, hd + 0.4, base), ASHLAR, bottom=False)
    steps = 6
    for step in range(steps):
        builder.box((-hw + 2.0, hd + 0.4, base * step / steps - 0.3),
                    (hw - 2.0, hd + 0.4 + 3.0 * (1 - step / steps), base * (step + 1) / steps), ASHLAR,
                    bottom=False)
    builder.box((-hw, -hd, base), (hw, hd - 4.0, height), "plaster_white", bottom=False, top=False)
    builder.box((-1.6, hd - 4.05, base), (1.6, hd - 3.9, base + 5.2), VOID, bottom=False)
    straight_moulding(builder, -hw, hw, height, simple_entablature_profile(0.9, 0.4), STONE, y=hd)
    builder.box((-hw, hd - 4.0, height - 0.9), (hw, hd, height), STONE)
    rise = hw * math.tan(math.radians(15))
    gable_roof(builder, -hd - 0.5, hd + 0.4, hw + 0.4, height + 0.75, height + 0.75 + rise, TILES, along_axis="y",
               imbrex=False)
    for y in (-hd - 0.5, hd + 0.4):
        builder.oriented([(-hw, y, height + 0.7), (hw, y, height + 0.7), (0.0, y, height + 0.7 + rise)],
                         (0, 1 if y > 0 else -1, 0), STONE)
    columns = [placement(x, hd - 0.6, base) for x in (-7.5, -2.5, 2.5, 7.5)]
    return builder, columns, height - 0.9 - base


def castellum(radius=2.95, depth=1.4, size=13.0, column_height=3.6):
    builder = MeshBuilder()
    half = size / 2
    builder.box((-half - 0.5, -half - 0.5, -2.6), (half + 0.5, half + 0.5, 0.3), ASHLAR, bottom=False, top=False)
    inner_ring = []
    outer_ring = []
    for step in range(32):
        theta = 2 * math.pi * step / 32
        cosine, sine = math.cos(theta), math.sin(theta)
        inner_ring.append((cosine * (radius + 0.5), sine * (radius + 0.5), 0.3))
        scale = (half + 0.5) / max(abs(cosine), abs(sine))
        outer_ring.append((cosine * scale, sine * scale, 0.3))
    builder.surface([outer_ring, inner_ring], ASHLAR, closed=True, facing=(0, 0, 1))
    builder.lathe([(radius + 0.5, 0.3), (radius + 0.5, 0.75), (radius, 0.75), (radius, -depth), (0.0, -depth)],
                  32, "lens_smooth", smooth=False)
    builder.lathe([(radius, -0.74), (0.0, -0.74)], 32, "water", smooth=False, caps=False)
    builder.box((-half, half - 0.7, 0.3), (half, half, 5.0), "plaster_ochre", bottom=False)
    first = len(builder.polygons)
    builder.box((-half + 0.7, half - 0.75, 1.0), (half - 0.7, half - 0.7, 4.2), MATTE_LEAD)
    builder.tint(first, (0.32, 0.50, 0.52))
    first = len(builder.polygons)
    for k in range(6):
        x = -half + 1.2 + k * (size - 2.4) / 6
        builder.box((x, half - 0.76, 2.1 + 0.12 * (k % 2)), (x + (size - 2.4) / 6 - 0.15, half - 0.75, 2.42 + 0.12 * (k % 2)),
                    MATTE_LEAD, bottom=False, top=False)
    builder.tint(first, (0.62, 0.76, 0.74))
    builder.box((-1.1, half - 0.8, 0.3), (1.1, half + 0.2, 1.6), VOID)
    roof_low = 0.3 + column_height
    for side in range(4):
        frame = Matrix.Rotation(side * math.pi / 2, 4, "Z")
        builder.box((-half, -half, roof_low), (half, -half + 2.4, roof_low + 0.45), STONE, matrix=frame)
        corners = [Vector((-half - 0.3, -half - 0.3, roof_low + 0.45)), Vector((half + 0.3, -half - 0.3,
                                                                               roof_low + 0.45)),
                   Vector((half - 2.6, -half + 2.6, roof_low + 1.6)), Vector((-half + 2.6, -half + 2.6,
                                                                             roof_low + 1.6))]
        builder.oriented([frame @ corner for corner in corners], frame @ Vector((0, -1, 2)), TILES)
    for pair in range(5):
        center = math.radians(198 + 36 * pair)
        for offset in (-0.11, 0.11):
            angle = center + offset
            direction = Vector((math.cos(angle), math.sin(angle), 0.0))
            frame = Matrix.Translation(direction * (radius - 0.22) + Vector((0.0, 0.0, -0.45)))
            frame = frame @ Matrix.Rotation(angle, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
            first = len(builder.polygons)
            builder.lathe([(0.13, 0.3), (0.13, -0.3), (0.2, -0.3), (0.2, 0.3)], 8, MATTE_LEAD, matrix=frame,
                          caps=False)
            builder.tint(first, (0.44, 0.45, 0.47))
            builder.lathe([(0.0, 0.0), (0.13, 0.0)], 8, VOID, matrix=frame, caps=False)
    for x, y in ((-1.2, -0.6), (0.0, -1.4), (1.2, -0.6)):
        builder.lathe([(0.18, -depth + 0.01), (0.0, -depth + 0.01)], 6, VOID, matrix=Matrix.Translation((x, y, 0.0)),
                      caps=False)
    builder.oriented([(-0.6, radius - 0.01, -0.9), (0.6, radius - 0.01, -0.9), (0.6, radius - 0.01, 0.3),
                      (-0.6, radius - 0.01, 0.3)], (0, -1, 0), VOID)
    builder.polygon([(-0.5, radius - 0.25, -0.73), (0.5, radius - 0.25, -0.73), (0.5, radius + 0.3, 0.32),
                     (-0.5, radius + 0.3, 0.32)], "water")
    columns = []
    for angle in (0.0, math.pi / 2, -math.pi / 2):
        for along in (-4.4, -1.5, 1.5, 4.4):
            offset = Vector((along, -half + 0.5, 0.3))
            point = Matrix.Rotation(angle, 4, "Z") @ offset
            columns.append(placement(point.x, point.y, point.z))
    for along in (-half + 0.5, half - 0.5):
        columns.append(placement(along, -half + 0.5, 0.3))
    return builder, columns


def aqueduct_channel(length, width=1.6, height=1.9):
    builder = MeshBuilder()
    builder.box((-width / 2, 0.0, -2.0), (width / 2, length, height), ASHLAR, bottom=False)
    builder.box((-width / 2 - 0.15, 0.0, height), (width / 2 + 0.15, length, height + 0.3), ASHLAR, bottom=False)
    return builder


def nymphaeum(radius=16.0):
    builder = MeshBuilder()
    builder.lathe([(radius + 1.2, -0.5), (radius + 1.2, 1.4), (radius, 1.4), (radius, -1.2)], 24, ASHLAR,
                  smooth=False, start=0.0, sweep=math.pi, caps=False)
    builder.lathe([(radius, 0.35), (0.0, 0.35)], 24, "water", smooth=False, start=0.0, sweep=math.pi,
                  caps=False)
    builder.box((-radius - 1.2, -0.6, -1.2), (radius + 1.2, 0.0, 0.9), STONE, bottom=False)
    shaft = column("ionic", 0.6, 5.2, "low")
    for index in range(17):
        angle = math.pi * index / 16
        center = Vector((math.cos(angle), math.sin(angle), 0.0)) * (radius + 0.6)
        builder.merge(shaft, placement(center.x, center.y, 1.4))
    builder.lathe([(radius + 1.0, 6.6), (radius + 1.0, 7.4), (radius + 1.25, 7.6), (radius + 1.25, 7.9),
                   (radius - 0.2, 7.9), (radius - 0.2, 6.6)], 24, STONE, smooth=False, start=0.0,
                  sweep=math.pi, caps=False)
    for x in (-radius - 0.6, radius + 0.6):
        builder.centered_box((x, 0.3, 4.65), (1.0, 0.6, 6.5), STONE)
    return builder


def sacred_basin(width=44.0, depth=26.0, island=13.0):
    builder = MeshBuilder()
    hw, hd = width / 2, depth / 2
    for (x0, y0), (x1, y1) in (((-hw - 6, -hd - 6), (hw + 6, -hd - 0.6)), ((-hw - 6, hd + 0.6), (hw + 6, hd + 6)),
                               ((-hw - 6, -hd - 0.6), (-hw - 0.6, hd + 0.6)), ((hw + 0.6, -hd - 0.6),
                                                                           (hw + 6, hd + 0.6))):
        builder.box((x0, y0, -1.5), (x1, y1, 0.05), "paving", bottom=False)
    for (x0, y0), (x1, y1) in (((-hw - 0.6, -hd - 0.6), (hw + 0.6, -hd)), ((-hw - 0.6, hd), (hw + 0.6, hd + 0.6)),
                               ((-hw - 0.6, -hd), (-hw, hd)), ((hw, -hd), (hw + 0.6, hd))):
        builder.box((x0, y0, -1.6), (x1, y1, 1.0), STONE, bottom=False)
    builder.box((-hw, -hd, 0.0), (hw, hd, 0.3), "water", bottom=False)
    hi = island / 2
    builder.box((-hi, -hi, -1.6), (hi, hi, 1.2), ASHLAR, bottom=False)
    builder.box((-hi - 0.2, -hi - 0.2, 1.2), (hi + 0.2, hi + 0.2, 1.5), STONE, bottom=False)
    builder.box((-1.6, hi, 0.0), (1.6, hd, 1.2), ASHLAR, bottom=False)
    corners = [placement(x, y, 1.5) for x in (-hi + 0.8, hi - 0.8) for y in (-hi + 0.8, hi - 0.8)]
    return builder, corners


def vaulted_hall(width=9.6, length=14.5, height=9.0):
    builder = MeshBuilder()
    hw = width / 2
    openings = [(-2.9, 1.0, 3.6), (0.0, 1.5, 4.6), (2.9, 1.0, 3.6)]
    arched_wall(builder, -hw, hw, -0.9, 0.0, 0.0, height, openings, ASHLAR, foundation=2.0)
    builder.box((-hw, -length, -2.0), (-hw + 0.9, -0.9, height), ASHLAR, bottom=False)
    builder.box((hw - 0.9, -length, -2.0), (hw, -0.9, height), ASHLAR, bottom=False)
    builder.box((-hw, -length, -2.0), (hw, -length + 0.9, height), ASHLAR, bottom=False)
    for opening_x in (-2.9, 0.0, 2.9):
        builder.box((opening_x - 1.0, -2.0, 0.0), (opening_x + 1.0, -1.9, 3.0), VOID, bottom=False)
    for x in (-4.45, -1.72, 1.72, 4.45):
        builder.merge(pilaster(0.42, height - 0.4, 0.12, STONE), placement(x, 0.0, 0.0))
    straight_moulding(builder, -hw, hw, height, simple_entablature_profile(0.7, 0.35), STONE)
    rise = hw * 0.32
    gable_roof(builder, -length - 0.3, 0.6, hw + 0.4, height + 0.55, height + 0.55 + rise, TILES, along_axis="y",
               imbrex=False)
    builder.oriented([(-hw, 0.6, height + 0.5), (hw, 0.6, height + 0.5), (0.0, 0.6, height + 0.5 + rise)],
                     (0, 1, 0), STONE)
    builder.oriented([(-hw, -length - 0.3, height + 0.5), (hw, -length - 0.3, height + 0.5),
                      (0.0, -length - 0.3, height + 0.5 + rise)], (0, -1, 0), STONE)
    return builder


def hillside_theatre(radius=24.0, rows=14, orchestra=7.0):
    builder = MeshBuilder()
    rise = 0.42
    tread = (radius - orchestra) / rows
    profile = [(orchestra, -0.2)]
    for row in range(rows):
        profile.append((orchestra + tread * row, rise * (row + 1)))
        profile.append((orchestra + tread * (row + 1), rise * (row + 1)))
    profile.append((radius + 1.0, rise * rows + 1.5))
    profile.append((radius + 1.0, -6.0))
    builder.lathe(list(reversed(profile)), 24, WEATHERED, smooth=False, start=0.0, sweep=math.pi, caps=False)
    builder.lathe([(orchestra, 0.0), (0.0, 0.0)], 12, "paving", smooth=False, start=0.0, sweep=math.pi,
                  caps=False)
    builder.box((-orchestra - 6, -5.0, -3.0), (orchestra + 6, 0.0, 1.2), ASHLAR, bottom=False)
    return builder


def bath_hall(builder, x0, x1, y0, y1, height, wall_material):
    builder.box((x0, y0, -1.5), (x1, y1, height), wall_material, bottom=False, top=False)
    rise = (y1 - y0) / 2 * 0.3
    gable_roof(builder, x0 - 0.4, x1 + 0.4, (y1 - y0) / 2 + 0.4, height, height + rise, TILES, along_axis="x",
               imbrex=False)
    for x in (x0 - 0.4, x1 + 0.4):
        builder.oriented([(x, y0 - 0.4, height), (x, y1 + 0.4, height), (x, (y0 + y1) / 2, height + rise)],
                         (1 if x > x0 else -1, 0, 0), wall_material)
    span = x1 - x0
    count = max(int(span / 4.5), 1)
    for index in range(count):
        x = x0 + span * (index + 0.5) / count
        builder.centered_box((x, y0 - 0.02, height * 0.62), (1.6, 0.1, height * 0.36), VOID)
        builder.centered_box((x, y1 + 0.02, height * 0.62), (1.6, 0.1, height * 0.36), VOID)


def thermae():
    builder = MeshBuilder()
    builder.box((-32.0, -30.0, -1.5), (32.0, 30.0, 0.1), "paving", bottom=False)
    builder.box((-30.0, -28.0, 0.1), (30.0, -2.0, 0.15), "arena_sand", bottom=False)
    for (x0, y0), (x1, y1) in (((-32.0, -30.0), (32.0, -29.2)), ((-32.0, -29.2), (-31.2, 0.0)),
                               ((31.2, -29.2), (32.0, 0.0))):
        builder.box((x0, y0, 0.0), (x1, y1, 5.5), "plaster", bottom=False)
    builder.box((-6.0, -18.0, 0.1), (6.0, -10.0, 0.2), "water", bottom=False)
    bath_hall(builder, -30.0, -12.0, 2.0, 22.0, 12.0, "plaster_white")
    bath_hall(builder, -12.0, 4.0, 4.0, 20.0, 10.5, "plaster_white")
    bath_hall(builder, 4.0, 26.0, 1.0, 25.0, 15.0, "plaster_white")
    builder.lathe([(6.0, -1.5), (6.0, 12.0)], 10, "plaster_white", smooth=True, start=0.0, sweep=math.pi,
                  caps=False, matrix=placement(15.0, 25.0, 0.0))
    builder.lathe([(6.4, 12.0), (0.0, 14.8)], 10, TILES, smooth=False, start=0.0, sweep=math.pi, caps=False,
                  matrix=placement(15.0, 25.0, 0.0))
    builder.box((-30.0, -2.0, 0.0), (26.0, 2.0, 6.0), "plaster", bottom=False)
    builder.oriented([(-30.5, -2.6, 6.0), (26.5, -2.6, 6.0), (26.5, 2.0, 7.6), (-30.5, 2.0, 7.6)], (0, -1, 1),
                     TILES)
    return builder


def propylaeum(width=12.0, depth=6.0, column_height=7.0):
    builder = MeshBuilder()
    hw = width / 2
    builder.box((-hw - 0.6, -depth / 2 - 0.6, -1.5), (hw + 0.6, depth / 2 + 0.6, 0.6), ASHLAR, bottom=False)
    shaft = column("corinthian", 0.75, column_height, "low")
    for y in (-depth / 2 + 0.5, depth / 2 - 0.5):
        for x in (-hw + 0.6, -hw / 3, hw / 3, hw - 0.6):
            builder.merge(shaft, placement(x, y, 0.6))
    top = 0.6 + column_height
    builder.box((-hw - 0.2, -depth / 2 - 0.2, top), (hw + 0.2, depth / 2 + 0.2, top + 1.1), STONE)
    rise = (depth / 2 + 0.4) * 0.3
    gable_roof(builder, -hw - 0.4, hw + 0.4, depth / 2 + 0.4, top + 1.1, top + 1.1 + rise, TILES, along_axis="x",
               imbrex=False)
    for x, facing in ((-hw - 0.4, -1), (hw + 0.4, 1)):
        builder.oriented([(x, -depth / 2 - 0.2, top + 1.1), (x, depth / 2 + 0.2, top + 1.1), (x, 0.0, top + 1.1 + rise)],
                         (facing, 0, 0), STONE)
    return builder

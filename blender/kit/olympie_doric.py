import math

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder
from .orders import ionic_capital, shaft, tile_roof, ridge_cap, attic_base

STUCCO = (0.98, 0.96, 0.91)
TRIGLYPH = (0.08, 0.13, 0.36)
REGULA = (0.10, 0.20, 0.52)
TAENIA = (0.78, 0.13, 0.08)
TYMPANUM = (0.16, 0.34, 0.72)
SIMA_RED = (0.82, 0.16, 0.09)
SIMA_BLUE = (0.12, 0.28, 0.62)
GOLD = (1.0, 1.0, 1.0)


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)
    return builder


def box(builder, x0, y0, z0, x1, y1, z1, material, colour=None, bottom=False):
    first = len(builder.polygons)
    builder.box((min(x0, x1), min(y0, y1), min(z0, z1)), (max(x0, x1), max(y0, y1), max(z0, z1)), material,
                bottom=bottom)
    if colour is not None:
        builder.tint(first, colour)


def doric_column(diameter, height, material="plaster", flutes=20, detail="high", colour=None, top_ratio=0.78,
                 capital=0.42):
    builder = MeshBuilder()
    d = diameter
    capital_bottom = height - capital * d
    segments = flutes * 3 if detail == "high" else (flutes * 2 if detail == "medium" else 10)
    shaft(builder, d, -0.2, capital_bottom - 0.06 * d, top_ratio, segments, material,
          flutes if detail != "low" else 0)
    top = d / 2 * top_ratio
    if detail == "low":
        builder.lathe([(top, capital_bottom - 0.06 * d), (top, capital_bottom), (0.6 * d, capital_bottom + 0.25 * d)],
                      10, material, smooth=True, caps=False)
        a = 0.6 * d
        builder.box((-a, -a, capital_bottom + 0.25 * d), (a, a, height), material)
        if colour is not None:
            builder.tint(0, colour)
        return builder
    neck = [(top, capital_bottom - 0.06 * d), (top * 0.985, capital_bottom - 0.05 * d), (top * 0.985,
                                                                                         capital_bottom - 0.035 * d),
            (top, capital_bottom - 0.03 * d), (top, capital_bottom)]
    ring_segments = 24 if detail == "high" else 14
    painted(builder, TAENIA, lambda: builder.lathe(neck, ring_segments, material, smooth=True, caps=False))
    h = capital * d
    echinus = [(top, capital_bottom), (top * 1.03, capital_bottom + 0.05 * h), (top * 1.03, capital_bottom + 0.09 * h),
               (top * 1.06, capital_bottom + 0.12 * h), (top * 1.06, capital_bottom + 0.16 * h),
               (0.5 * d, capital_bottom + 0.3 * h), (0.58 * d, capital_bottom + 0.45 * h),
               (0.6 * d, capital_bottom + 0.55 * h)]
    builder.lathe(echinus, ring_segments, material, smooth=True, caps=False)
    painted(builder, REGULA, lambda: builder.lathe([(top * 1.031, capital_bottom + 0.06 * h),
                                                     (top * 1.031, capital_bottom + 0.08 * h)], ring_segments, material,
                                                    smooth=True, caps=False))
    a = 0.6 * d
    builder.box((-a, -a, capital_bottom + 0.55 * h), (a, a, height), material)
    if colour is not None:
        builder.tint(0, colour)
    return builder


def ionic_column(diameter, height, material="marble", detail="high"):
    builder = MeshBuilder()
    d = diameter
    segments = 48 if detail == "high" else 14
    attic_base(builder, d, 16 if detail == "high" else 10, material)
    capital_bottom = height - 0.42 * d
    shaft(builder, d, 0.5 * d, capital_bottom, 0.84, segments, material, 24 if detail == "high" else 0)
    ionic_capital(builder, d, capital_bottom, material)
    return builder


def simple_ionic(diameter, height, material="plaster"):
    builder = MeshBuilder()
    d = diameter
    builder.lathe([(0.66 * d, 0.0), (0.66 * d, 0.14 * d), (0.56 * d, 0.3 * d), (0.5 * d, 0.36 * d)], 10, material,
                  smooth=True, caps=False)
    builder.lathe([(0.5 * d, 0.36 * d), (0.42 * d, height - 0.4 * d)], 10, material, smooth=True, caps=False)
    builder.lathe([(0.42 * d, height - 0.4 * d), (0.5 * d, height - 0.26 * d), (0.5 * d, height - 0.2 * d)], 10,
                  material, smooth=True, caps=False)
    builder.box((-0.68 * d, -0.42 * d, height - 0.3 * d), (0.68 * d, 0.42 * d, height - 0.12 * d), material)
    for side in (-1, 1):
        frame = Matrix.Translation((side * 0.62 * d, 0.0, height - 0.3 * d)) @ Matrix.Rotation(math.pi / 2, 4, "X")
        builder.lathe([(0.0, -0.42 * d), (0.2 * d, -0.42 * d), (0.2 * d, 0.42 * d), (0.0, 0.42 * d)], 8, material,
                      smooth=True, matrix=frame)
    builder.box((-0.6 * d, -0.6 * d, height - 0.12 * d), (0.6 * d, 0.6 * d, height), material)
    return builder


def rectangle_ring(builder, x_out, y_out, x_in, y_in, z0, z1, material, colour=None):
    first = len(builder.polygons)
    builder.box((-x_out, -y_out, z0), (x_out, -y_in, z1), material, bottom=False)
    builder.box((-x_out, y_in, z0), (x_out, y_out, z1), material, bottom=False)
    builder.box((-x_out, -y_in, z0), (-x_in, y_in, z1), material, bottom=False)
    builder.box((x_in, -y_in, z0), (x_out, y_in, z1), material, bottom=False)
    if colour is not None:
        builder.tint(first, colour)


def side_frames(half_x, half_y):
    return [(Vector((half_x, 0.0)), Vector((1.0, 0.0)), Vector((0.0, 1.0)), half_y),
            (Vector((-half_x, 0.0)), Vector((-1.0, 0.0)), Vector((0.0, -1.0)), half_y),
            (Vector((0.0, half_y)), Vector((0.0, 1.0)), Vector((-1.0, 0.0)), half_x),
            (Vector((0.0, -half_y)), Vector((0.0, -1.0)), Vector((1.0, 0.0)), half_x)]


def slab_on_face(builder, centre, outward, tangent, along0, along1, out0, out1, z0, z1, material, colour=None):
    corners = []
    for a in (along0, along1):
        for o in (out0, out1):
            corners.append(centre + tangent * a + outward * o)
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    box(builder, min(xs), min(ys), z0, max(xs), max(ys), z1, material, colour)


class Peripteral:
    def __init__(self, length, width, front, flank, diameter, column_height, architrave, frieze, geison, steps,
                 step_height, roof_rise, front_spacing=None, flank_spacing=None, cella=None, material="plaster",
                 roof="terracotta_tiles", tile_pitch=0.6, stone="limestone", colourful=True):
        self.length = length
        self.width = width
        self.front = front
        self.flank = flank
        self.d = diameter
        self.column_height = column_height
        self.architrave = architrave
        self.frieze = frieze
        self.geison = geison
        self.steps = steps
        self.step_height = step_height
        self.roof_rise = roof_rise
        self.material = material
        self.roof = roof
        self.tile_pitch = tile_pitch
        self.stone = stone
        self.colourful = colourful
        margin = self.d * 0.62 + 0.04
        self.axis_x = self.axes(length / 2 - margin, flank, flank_spacing)
        self.axis_y = self.axes(width / 2 - margin, front, front_spacing)
        self.half_x = self.axis_x[-1]
        self.half_y = self.axis_y[-1]
        self.cella = cella
        self.arch_top = column_height + architrave
        self.frieze_top = self.arch_top + frieze
        self.geison_top = self.frieze_top + geison

    @staticmethod
    def axes(half, count, spacing):
        if spacing is None:
            return [-half + 2 * half * k / (count - 1) for k in range(count)]
        inner = spacing * (count - 3)
        corner = (2 * half - inner) / 2
        positions = [-half]
        for k in range(count - 2):
            positions.append(-half + corner + spacing * k)
        positions.append(half)
        return positions

    def column_positions(self):
        positions = []
        for y in self.axis_y:
            positions.append((self.axis_x[0], y))
            positions.append((self.axis_x[-1], y))
        for x in self.axis_x[1:-1]:
            positions.append((x, self.axis_y[0]))
            positions.append((x, self.axis_y[-1]))
        return positions

    def krepis(self, builder, foundation=1.6):
        top = 0.0
        stone = self.stone
        for step in range(self.steps):
            grow = (step + 1) * self.step_height * 1.05
            z1 = top - step * self.step_height
            z0 = z1 - self.step_height
            builder.box((-self.length / 2 - grow + self.step_height * 1.05, -self.width / 2 - grow + self.step_height * 1.05, z0),
                        (self.length / 2 + grow - self.step_height * 1.05, self.width / 2 + grow - self.step_height * 1.05, z1),
                        stone, bottom=False)
        depth = self.steps * self.step_height
        grow = self.steps * self.step_height * 1.05 + 0.3
        builder.box((-self.length / 2 - grow, -self.width / 2 - grow, -depth - foundation),
                    (self.length / 2 + grow, self.width / 2 + grow, -depth), stone, bottom=False)

    def entablature(self, builder, shields=None):
        d = self.d
        m = self.material
        out = 0.42 * d
        x_out = self.half_x + out
        y_out = self.half_y + out
        x_in = self.half_x - out
        y_in = self.half_y - out
        rectangle_ring(builder, x_out, y_out, x_in, y_in, self.column_height, self.arch_top, m, STUCCO)
        taenia_h = self.architrave * 0.09
        rectangle_ring(builder, x_out + 0.05, y_out + 0.05, x_in, y_in, self.arch_top - taenia_h, self.arch_top, m,
                       TAENIA if self.colourful else STUCCO)
        rectangle_ring(builder, x_out - 0.02, y_out - 0.02, x_in, y_in, self.arch_top, self.frieze_top, m, STUCCO)
        tri_w = d * 0.47
        for centre, outward, tangent, half in side_frames(x_out - 0.02, y_out - 0.02):
            positions = self.axis_y if abs(outward.x) > 0.5 else self.axis_x
            slots = []
            for a, b in zip(positions[:-1], positions[1:]):
                slots.extend([a, (a + b) / 2])
            slots.append(positions[-1])
            slots[0] = -half + tri_w / 2
            slots[-1] = half - tri_w / 2
            for index, s in enumerate(slots):
                world_along = s if tangent.x + tangent.y > 0 else -s
                along = world_along
                for bar in (-1, 0, 1):
                    c0 = along + bar * tri_w / 3 - tri_w / 7
                    c1 = along + bar * tri_w / 3 + tri_w / 7
                    slab_on_face(builder, centre, outward, tangent, c0, c1, -0.05, 0.07, self.arch_top,
                                 self.frieze_top - 0.04, m, TRIGLYPH if self.colourful else STUCCO)
                slab_on_face(builder, centre, outward, tangent, along - tri_w / 2, along + tri_w / 2, -0.05, 0.04,
                             self.frieze_top - 0.12, self.frieze_top, m, TRIGLYPH if self.colourful else STUCCO)
                slab_on_face(builder, centre, outward, tangent, along - tri_w / 2, along + tri_w / 2, 0.0, 0.1,
                             self.arch_top - taenia_h - 0.12, self.arch_top - taenia_h, m,
                             REGULA if self.colourful else STUCCO)
                if shields and index < len(slots) - 1:
                    key = (round(outward.x), round(outward.y))
                    wanted = shields.get(key, ())
                    if index in wanted:
                        nxt = slots[index + 1] if tangent.x + tangent.y > 0 else -slots[index + 1]
                        middle = (along + nxt) / 2
                        point = centre + tangent * middle + outward * 0.09
                        z = (self.arch_top + self.frieze_top) / 2
                        radius = min(self.frieze, abs(nxt - along) - tri_w) * 0.42
                        frame = Matrix.Translation((point.x, point.y, z)) @ Matrix(
                            (Vector((tangent.x, tangent.y, 0.0)), Vector((0.0, 0.0, 1.0)),
                             Vector((outward.x, outward.y, 0.0)))).transposed().to_4x4()
                        builder.lathe([(0.0, 0.16), (radius * 0.25, 0.15), (radius * 0.3, 0.12), (radius * 0.92, 0.04),
                                       (radius, 0.0), (radius, -0.04)], 18, "bronze_gilt", smooth=True, caps=True,
                                      matrix=frame)
        g0 = self.frieze_top
        g1 = self.geison_top
        over = 0.62 * self.geison / 0.645 + 0.1
        rectangle_ring(builder, x_out + over, y_out + over, x_in, y_in, g0, g1, m, STUCCO)
        rectangle_ring(builder, x_out + over + 0.03, y_out + over + 0.03, x_out + over - 0.3, y_out + over - 0.3,
                       g1 - self.geison * 0.32, g1, m, SIMA_BLUE if self.colourful else STUCCO)
        mutule = (SIMA_BLUE if self.colourful else STUCCO)
        for centre, outward, tangent, half in side_frames(x_out, y_out):
            count = int(2 * half / (tri_w * 1.25))
            for k in range(count):
                along = -half + (k + 0.5) * 2 * half / count
                slab_on_face(builder, centre, outward, tangent, along - tri_w * 0.4, along + tri_w * 0.4, 0.05,
                             over - 0.05, g0 - 0.07, g0, m, mutule)
        return x_out + over, y_out + over

    def pediments(self, builder, eave_x, eave_y, east_colour=TYMPANUM):
        m = self.material
        top = self.geison_top
        rise = self.roof_rise
        for sign in (-1, 1):
            x_face = sign * (self.half_x + 0.42 * self.d - 0.06)
            tympanum = [(x_face, -self.half_y - 0.42 * self.d, top), (x_face, self.half_y + 0.42 * self.d, top),
                        (x_face, 0.0, top + rise * (self.half_y + 0.42 * self.d) / eave_y)]
            builder.oriented(tympanum, (sign, 0.0, 0.0), m)
            builder.tint(len(builder.polygons) - 1, east_colour if self.colourful else STUCCO)
            back = [(sign * (self.half_x - 1.0), y, z) for _, y, z in tympanum]
            builder.oriented(back, (-sign, 0.0, 0.0), m)
            builder.tint(len(builder.polygons) - 1, STUCCO)
            x_out = sign * eave_x
            x_in = sign * (self.half_x + 0.42 * self.d - 0.1)
            for side in (-1, 1):
                start = Vector((0.0, side * eave_y, top - 0.02))
                end = Vector((0.0, 0.0, top + rise))
                for lift, colour in ((self.geison * 0.65, STUCCO), (self.geison * 0.32, SIMA_RED)):
                    a = Vector((x_in, start.y, start.z))
                    b = Vector((x_in, end.y, end.z))
                    c = Vector((x_out, end.y, end.z))
                    e = Vector((x_out, start.y, start.z))
                    first = len(builder.polygons)
                    up = Vector((0.0, 0.0, lift))
                    builder.oriented([a, b, c, e], (0, 0, -1), m)
                    builder.oriented([a + up, e + up, c + up, b + up], (0, 0, 1), m)
                    builder.oriented([e, c, c + up, e + up], (sign, 0, 0), m)
                    builder.tint(first, colour if self.colourful else STUCCO)
                    top_shift = up
                    start = start + top_shift
                    end = end + top_shift
        return top + rise

    def roof_cover(self, builder, eave_x, eave_y):
        top = self.geison_top
        rise = self.roof_rise
        for side in (-1, 1):
            tile_roof(builder, Vector((-eave_x, 0.0, top + rise + 0.05)),
                      Vector((eave_x, 0.0, top + rise + 0.05)),
                      Vector((0.0, side * eave_y, -rise)), self.roof, self.tile_pitch, True)
        ridge_cap(builder, (-eave_x, 0.0, top + rise + 0.1), (eave_x, 0.0, top + rise + 0.1), 0.22, self.roof)
        count = int(2 * eave_x / self.tile_pitch)
        for side in (-1, 1):
            for k in range(count + 1):
                x = -eave_x + 2 * eave_x * k / count
                y = side * (eave_y + 0.02)
                tri = [(x - self.tile_pitch * 0.28, y, top - 0.02), (x + self.tile_pitch * 0.28, y, top - 0.02),
                       (x, y, top + self.tile_pitch * 0.55)]
                builder.oriented(tri, (0.0, side, 0.0), self.roof)


def in_antis_front(builder, x_face, half_y, wall, height, sign, material, colour=STUCCO):
    first = len(builder.polygons)
    for side in (-1, 1):
        y0 = side * half_y
        y1 = side * (half_y - wall)
        builder.box((min(x_face, x_face - sign * 0.0), min(y0, y1), 0.0), (max(x_face, x_face), max(y0, y1), height),
                    material, bottom=False)
    builder.tint(first, colour)


def cella_box(builder, x0, x1, half_y, wall, height, material, colour=STUCCO, door=None, base_colour=None,
              closed_ends=(True, True)):
    first = len(builder.polygons)
    for side in (-1, 1):
        y_outer = side * half_y
        y_inner = side * (half_y - wall)
        builder.box((x0, min(y_outer, y_inner), 0.0), (x1, max(y_outer, y_inner), height), material, bottom=False)
    for index, x in enumerate((x0, x1)):
        if not closed_ends[index]:
            continue
        inner = x + wall if index == 0 else x - wall
        lo, hi = min(x, inner), max(x, inner)
        if door is None or door.get(index) is None:
            builder.box((lo, -half_y + wall, 0.0), (hi, half_y - wall, height), material, bottom=False)
            continue
        width, door_h = door[index]
        builder.box((lo, -half_y + wall, 0.0), (hi, -width / 2, height), material, bottom=False)
        builder.box((lo, width / 2, 0.0), (hi, half_y - wall, height), material, bottom=False)
        builder.box((lo, -width / 2, door_h), (hi, width / 2, height), material, bottom=False)
    builder.tint(first, colour)
    if base_colour is not None:
        for side in (-1, 1):
            for face in (half_y + 0.02, half_y - wall - 0.02):
                y = side * face
                painted(builder, base_colour, lambda y=y: builder.box((x0, min(y, y + 0.001), 0.0),
                                                                      (x1, max(y, y + 0.001), 1.1), material,
                                                                      bottom=False))


def in_antis_building(width, depth, column_height, diameter, wall_material="plaster", stone="limestone",
                      roof="terracotta_tiles", steps=2, step_height=0.32, colourful=True, pediment_colour=TYMPANUM,
                      tile_pitch=0.5, wall_colour=STUCCO, sima=SIMA_RED, acroterion=None, columns=2):
    builder = MeshBuilder()
    d = diameter
    half_y = width / 2
    front = depth / 2
    back = -depth / 2
    for step in range(steps):
        grow = (steps - step) * step_height
        builder.box((back - grow, -half_y - grow, -(step + 1) * step_height), (front + grow, half_y + grow,
                                                                               -step * step_height), stone,
                    bottom=False)
    builder.box((back - steps * step_height - 0.3, -half_y - steps * step_height - 0.3, -steps * step_height - 1.2),
                (front + steps * step_height + 0.3, half_y + steps * step_height + 0.3, -steps * step_height), stone,
                bottom=False)
    wall = max(0.55, d * 0.7)
    porch = min(depth * 0.3, 3.2)
    cella_box(builder, back + 0.3, front - porch, half_y - 0.3, wall, column_height, wall_material, wall_colour,
              door={1: (min(2.0, width * 0.3), column_height * 0.62)})
    for side in (-1, 1):
        painted(builder, wall_colour, lambda side=side: builder.box(
            (front - porch, min(side * (half_y - 0.3), side * (half_y - 0.3 - wall)), 0.0),
            (front - 0.2, max(side * (half_y - 0.3), side * (half_y - 0.3 - wall)), column_height), wall_material,
            bottom=False))
    arch_h = d * 0.85
    frieze_h = d * 0.85
    geison_h = d * 0.35
    top = column_height + arch_h
    painted(builder, STUCCO, lambda: builder.box((back + 0.1, -half_y - 0.05, column_height),
                                                 (front + 0.05, half_y + 0.05, top), wall_material))
    painted(builder, TAENIA if colourful else STUCCO, lambda: builder.box(
        (back + 0.08, -half_y - 0.08, top - 0.08), (front + 0.08, half_y + 0.08, top), wall_material))
    painted(builder, STUCCO, lambda: builder.box((back + 0.1, -half_y - 0.05, top), (front + 0.03, half_y + 0.03,
                                                                                       top + frieze_h), wall_material))
    tri_w = d * 0.5
    span = (2 * (half_y - 0.3)) / max(columns + 1, 1)
    slots = int(round(2 * half_y / (tri_w * 2.6)))
    for k in range(slots + 1):
        y = -half_y + 0.03 + tri_w / 2 + (2 * half_y - tri_w - 0.06) * k / max(slots, 1)
        for bar in (-1, 0, 1):
            painted(builder, TRIGLYPH if colourful else STUCCO, lambda y=y, bar=bar: builder.box(
                (front + 0.03, y + bar * tri_w / 3 - tri_w / 7, top), (front + 0.1, y + bar * tri_w / 3 + tri_w / 7,
                                                                       top + frieze_h - 0.04), wall_material))
    ft = top + frieze_h
    painted(builder, STUCCO, lambda: builder.box((back - 0.3, -half_y - 0.35, ft), (front + 0.4, half_y + 0.35,
                                                                                    ft + geison_h), wall_material))
    rise = width * 0.13
    for x_face, sign in ((front + 0.03, 1), (back + 0.1, -1)):
        tri = [(x_face, -half_y, ft + geison_h), (x_face, half_y, ft + geison_h), (x_face, 0.0, ft + geison_h + rise)]
        builder.oriented(tri, (sign, 0, 0), wall_material)
        builder.tint(len(builder.polygons) - 1, pediment_colour if colourful else STUCCO)
    for side in (-1, 1):
        tile_roof(builder, Vector((back - 0.45, 0.0, ft + geison_h + rise + 0.06)),
                  Vector((front + 0.55, 0.0, ft + geison_h + rise + 0.06)),
                  Vector((0.0, side * (half_y + 0.4), -rise - 0.06)), roof, tile_pitch, True)
        first = len(builder.polygons)
        for x0, x1 in ((front + 0.4, front + 0.6),):
            a = Vector((x0, side * (half_y + 0.4), ft + geison_h))
            b = Vector((x0, 0.0, ft + geison_h + rise + 0.1))
            builder.box((x0, min(0.0, side * (half_y + 0.42)), ft + geison_h - 0.02),
                        (x1, max(0.0, side * (half_y + 0.42)), ft + geison_h + 0.04), wall_material)
        builder.tint(first, sima if colourful else STUCCO)
        for x_face in (front + 0.5,):
            rake = [(x_face, side * (half_y + 0.45), ft + geison_h - 0.02),
                    (x_face, 0.0, ft + geison_h + rise + 0.18), (x_face, 0.0, ft + geison_h + rise - 0.2),
                    (x_face, side * (half_y + 0.45), ft + geison_h - 0.4)]
            builder.oriented(rake, (1, 0, 0), wall_material)
            builder.tint(len(builder.polygons) - 1, sima if colourful else STUCCO)
    ridge_cap(builder, (back - 0.45, 0.0, ft + geison_h + rise + 0.12), (front + 0.55, 0.0, ft + geison_h + rise + 0.12),
              0.14, roof)
    if acroterion is not None:
        apex = Vector((front + 0.5, 0.0, ft + geison_h + rise + 0.1))
        frame = Matrix.Translation(apex) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        first = len(builder.polygons)
        builder.lathe([(0.0, -0.06), (width * 0.08, -0.06), (width * 0.08, 0.06), (0.0, 0.06)], 16, wall_material,
                      matrix=Matrix.Translation(apex + Vector((0.0, 0.0, width * 0.08)))
                      @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        builder.tint(first, acroterion)
    positions = []
    for k in range(columns):
        y = -half_y + 0.3 + wall + (2 * (half_y - 0.3 - wall)) * (k + 1) / (columns + 1)
        positions.append((front - 0.45, y))
    return builder, positions, top + frieze_h + geison_h + rise

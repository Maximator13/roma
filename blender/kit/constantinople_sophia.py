import math

from mathutils import Matrix, Vector

from .geometry import MeshBuilder, newell_normal
from .orders import column

TAU = 2 * math.pi
HONEY = (0.98, 0.80, 0.60)
WARM_WHITE = (0.92, 0.88, 0.80)
VERDE = (0.36, 0.62, 0.46)
DOME_R = 15.5
DOME_Z = 40.1
SPRING = 24.6
PEND_R = DOME_R * math.sqrt(2)
GALLERY_Z = 12.0
ROOF_Z = 24.0
HALF_W = 36.5
WEST = -34.0
EAST = 31.0
NARTHEX = -40.0
EXONARTHEX = -45.0
ATRIUM_WEST = -95.0
ATRIUM_HALF = 31.0
APSE_R = 6.8
AMBO_U = 6.5


def tinted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def facing_quad(builder, points, hint, material, smooth=False, colour=None):
    points = [Vector(p) for p in points]
    if newell_normal(points).dot(Vector(hint)) < 0:
        points.reverse()
    builder.polygon(points, material, smooth, color=colour)


def grid_surface(builder, rows, material, hint, smooth=True, colour=None):
    for r in range(len(rows) - 1):
        for c in range(len(rows[r]) - 1):
            quad = [rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]]
            centre = sum((Vector(p) for p in quad), Vector()) / 4
            facing_quad(builder, quad, hint(centre), material, smooth, colour)


def box(builder, minimum, maximum, material, colour=None, bottom=False):
    tinted(builder, colour or (1.0, 1.0, 1.0), lambda: builder.box(minimum, maximum, material, bottom=bottom))


def arch_outline(width, height, segments=6):
    radius = width / 2
    spring = height - radius
    points = [(-radius, 0.0), (radius, 0.0)]
    for k in range(segments + 1):
        a = math.pi * k / segments
        points.append((radius * math.cos(a), spring + radius * math.sin(a)))
    return points


def window(builder, origin, right, outward, width, height, thickness, lit=True, inset=0.06):
    origin = Vector(origin)
    right = Vector(right).normalized()
    outward = Vector(outward).normalized()
    up = Vector((0.0, 0.0, 1.0))
    outline = arch_outline(width, height)
    front = [origin + right * x + up * z + outward * inset for x, z in outline]
    facing_quad(builder, front, outward, "glass_dark")
    if lit:
        back = [origin + right * x + up * z - outward * (thickness + inset) for x, z in outline]
        facing_quad(builder, back, -outward, "glass_lit")


def sphere_point(centre, radius, azimuth, elevation):
    return Vector((centre[0] + radius * math.cos(elevation) * math.cos(azimuth),
                   centre[1] + radius * math.cos(elevation) * math.sin(azimuth),
                   centre[2] + radius * math.sin(elevation)))


def shell(builder, centre, radius, start, sweep, el0, el1, segments, rings, material, inward, colour=None):
    centre = Vector(centre)
    rows = []
    for i in range(rings + 1):
        el = el0 + (el1 - el0) * i / rings
        rows.append([sphere_point(centre, radius, start + sweep * k / segments, el) for k in range(segments + 1)])
    sign = -1.0 if inward else 1.0
    grid_surface(builder, rows, material, lambda p: (p - centre) * sign, True, colour)


def window_band(builder, centre, radius, thickness, z0, height, start, sweep, count, pier_share, buttress,
                lintel=0.7, inner="gold_mosaic", outer="plaster", colour=HONEY):
    centre = Vector(centre)
    step = sweep / count
    pier = step * pier_share
    top = z0 + height + lintel
    for k in range(count + (0 if abs(sweep - TAU) < 1e-6 else 1)):
        a = start + k * step
        a0, a1 = a - pier / 2, a + pier / 2
        if abs(sweep - TAU) > 1e-6:
            a0 = max(a0, start)
            a1 = min(a1, start + sweep)
        corners = []
        for ang in (a0, a1):
            for r in (radius, radius + thickness):
                corners.append(Vector((centre.x + r * math.cos(ang), centre.y + r * math.sin(ang))))
        outline = [corners[0], corners[2], corners[3], corners[1]]
        pts = [Vector((p.x, p.y, 0.0)) for p in outline]
        mid = sum(pts, Vector()) / 4
        for i in range(4):
            p, q = pts[i], pts[(i + 1) % 4]
            quad = [Vector((p.x, p.y, z0)), Vector((q.x, q.y, z0)), Vector((q.x, q.y, top)), Vector((p.x, p.y, top))]
            facing_quad(builder, quad, ((p + q) / 2 - mid), outer, colour=colour)
        if buttress > 0:
            am = (a0 + a1) / 2
            radial = Vector((math.cos(am), math.sin(am), 0.0))
            side = Vector((-math.sin(am), math.cos(am), 0.0))
            base = centre.to_2d().to_3d() + radial * (radius + thickness)
            half = (radius + thickness) * (a1 - a0) / 2 * 0.8
            b0 = base - side * half
            b1 = base + side * half
            c0 = b0 + radial * buttress
            c1 = b1 + radial * buttress
            lo, hi = z0, top + 0.4
            for p, q in ((b0, c0), (c0, c1), (c1, b1)):
                facing_quad(builder, [Vector((p.x, p.y, lo)), Vector((q.x, q.y, lo)), Vector((q.x, q.y, hi)), Vector((p.x, p.y, hi))],
                            ((p + q) / 2 - base) if (p, q) != (c0, c1) else radial, outer, colour=colour)
            facing_quad(builder, [Vector((b0.x, b0.y, hi)), Vector((c0.x, c0.y, hi - 0.6)), Vector((c1.x, c1.y, hi - 0.6)),
                                  Vector((b1.x, b1.y, hi))], Vector((0, 0, 1)) + radial * 0.5, "lead")
        if k < count:
            b0 = a1
            b1 = a + step - pier / 2
            spring = z0 + height
            n = 6
            inner_rows = []
            for j in range(n + 1):
                t = j / n
                ang = b0 + (b1 - b0) * t
                rise = math.sqrt(max(0.0, 1.0 - (2 * t - 1) ** 2))
                zb = spring - (height * 0.28) * (1.0 - rise)
                inner_rows.append((ang, zb))
            for (ang, zb), (ang2, zb2) in zip(inner_rows[:-1], inner_rows[1:]):
                for r, hint_sign, material, tint in ((radius, -1.0, inner, (1.0, 1.0, 1.0)),
                                                    (radius + thickness, 1.0, outer, colour)):
                    p = Vector((centre.x + r * math.cos(ang), centre.y + r * math.sin(ang), 0.0))
                    q = Vector((centre.x + r * math.cos(ang2), centre.y + r * math.sin(ang2), 0.0))
                    quad = [Vector((p.x, p.y, zb)), Vector((q.x, q.y, zb2)), Vector((q.x, q.y, top)),
                            Vector((p.x, p.y, top))]
                    radial = Vector((math.cos((ang + ang2) / 2), math.sin((ang + ang2) / 2), 0.0))
                    facing_quad(builder, quad, radial * hint_sign, material, colour=tint)
                pi = Vector((centre.x + radius * math.cos(ang), centre.y + radius * math.sin(ang), zb))
                qi = Vector((centre.x + radius * math.cos(ang2), centre.y + radius * math.sin(ang2), zb2))
                po = Vector((centre.x + (radius + thickness) * math.cos(ang), centre.y + (radius + thickness) * math.sin(ang), zb))
                qo = Vector((centre.x + (radius + thickness) * math.cos(ang2), centre.y + (radius + thickness) * math.sin(ang2), zb2))
                facing_quad(builder, [pi, qi, qo, po], Vector((0, 0, -1)), outer, colour=colour)
            sill_z = z0
            p = Vector((centre.x + radius * math.cos(b0), centre.y + radius * math.sin(b0), sill_z))
            q = Vector((centre.x + radius * math.cos(b1), centre.y + radius * math.sin(b1), sill_z))
            po = Vector((centre.x + (radius + thickness) * math.cos(b0), centre.y + (radius + thickness) * math.sin(b0), sill_z))
            qo = Vector((centre.x + (radius + thickness) * math.cos(b1), centre.y + (radius + thickness) * math.sin(b1), sill_z))
            facing_quad(builder, [p, q, qo, po], Vector((0, 0, 1)), "marble_white")
    return top


def revolve_band(builder, centre, radius, z0, z1, start, sweep, segments, material, outward=True, colour=None):
    centre = Vector(centre)
    rows = []
    for z in (z0, z1):
        rows.append([Vector((centre.x + radius * math.cos(start + sweep * k / segments),
                             centre.y + radius * math.sin(start + sweep * k / segments), z))
                     for k in range(segments + 1)])
    sign = 1.0 if outward else -1.0
    grid_surface(builder, rows, material, lambda p: Vector((p.x - centre.x, p.y - centre.y, 0.0)) * sign, False, colour)


def annulus(builder, centre, r0, r1, z, start, sweep, segments, material, up=True, colour=None):
    centre = Vector(centre)
    rows = []
    for r in (r0, r1):
        rows.append([Vector((centre.x + r * math.cos(start + sweep * k / segments),
                             centre.y + r * math.sin(start + sweep * k / segments), z)) for k in range(segments + 1)])
    grid_surface(builder, rows, material, lambda p: Vector((0, 0, 1 if up else -1)), False, colour)


def cross(builder, base, height, material="bronze_gilt"):
    x, y, z = base
    w = height * 0.09
    builder.box((x - w, y - w, z), (x + w, y + w, z + height), material, bottom=False)
    builder.box((x - w, y - height * 0.32, z + height * 0.6), (x + w, y + height * 0.32, z + height * 0.6 + 2 * w),
                material)


def impost_column(diameter, height, material="marble_white", capital=WARM_WHITE):
    builder = MeshBuilder()
    r = diameter / 2
    cap = min(diameter * 0.85, 0.9)
    shaft_top = height - cap
    builder.lathe([(r * 1.3, 0.0), (r * 1.3, 0.18), (r * 1.12, 0.26), (r * 1.02, 0.34), (r, shaft_top - 0.12),
                   (r * 1.08, shaft_top - 0.06), (r * 1.08, shaft_top)], 10, material, smooth=True)
    tinted(builder, capital, lambda: builder.lathe([(r * 1.45, shaft_top), (r * 2.0, height - 0.12), (r * 2.05, height),
                                                    (0.0, height)], 4, "marble_white", smooth=False,
                                                   matrix=Matrix.Rotation(math.pi / 4, 4, "Z")))
    return builder


def colonnade(builder, start, end, count, height, diameter, z, colour=VERDE, material="marble_white", style="ionic"):
    start, end = Vector(start), Vector(end)
    if style == "impost":
        template = impost_column(diameter, height, material)
    else:
        template = column("ionic", diameter, height, "low", material)
    for k in range(count):
        t = (k + 0.5) / count
        p = start.lerp(end, t)
        first = len(builder.polygons)
        builder.merge(template, Matrix.Translation((p.x, p.y, z)))
        builder.tint(first, colour)


def slab_strips(builder, inside, u0, u1, v0, v1, z0, z1, cell, top_material, bottom_material, top_colour=None,
                bottom_colour=None, sides=True):
    nu = int(round((u1 - u0) / cell))
    nv = int(round((v1 - v0) / cell))
    mask = [[inside(u0 + (i + 0.5) * cell, v0 + (j + 0.5) * cell) for i in range(nu)] for j in range(nv)]
    for j in range(nv):
        i = 0
        while i < nu:
            if not mask[j][i]:
                i += 1
                continue
            start = i
            while i < nu and mask[j][i]:
                i += 1
            a, b = u0 + start * cell, u0 + i * cell
            c, d = v0 + j * cell, v0 + (j + 1) * cell
            facing_quad(builder, [(a, c, z1), (b, c, z1), (b, d, z1), (a, d, z1)], (0, 0, 1), top_material,
                        colour=top_colour)
            facing_quad(builder, [(a, c, z0), (b, c, z0), (b, d, z0), (a, d, z0)], (0, 0, -1), bottom_material,
                        colour=bottom_colour)
            if sides:
                if j == 0 or not all(mask[j - 1][start:i]):
                    facing_quad(builder, [(a, c, z0), (b, c, z0), (b, c, z1), (a, c, z1)], (0, -1, 0), bottom_material,
                                colour=bottom_colour)
                if j == nv - 1 or not all(mask[j + 1][start:i]):
                    facing_quad(builder, [(a, d, z0), (b, d, z0), (b, d, z1), (a, d, z1)], (0, 1, 0), bottom_material,
                                colour=bottom_colour)
                facing_quad(builder, [(a, c, z0), (a, d, z0), (a, d, z1), (a, c, z1)], (-1, 0, 0), bottom_material,
                            colour=bottom_colour)
                facing_quad(builder, [(b, c, z0), (b, d, z0), (b, d, z1), (b, c, z1)], (1, 0, 0), bottom_material,
                            colour=bottom_colour)


def nave_open(u, v, margin=0.0):
    if abs(u) <= DOME_R + margin and abs(v) <= DOME_R + margin:
        return True
    for centre in (DOME_R, -DOME_R):
        if (u - centre) * (1 if centre > 0 else -1) >= -margin and math.hypot(u - centre, v) <= DOME_R + margin:
            return True
    if u > EAST - 2.0 and abs(v) < APSE_R + margin and u < EAST + APSE_R + margin:
        return True
    return False


def pier_at(u, v):
    return DOME_R - 0.01 <= abs(u) <= 22.5 and DOME_R + 1.5 <= abs(v) <= HALF_W


def pendentives(builder):
    for quadrant in range(4):
        base = quadrant * math.pi / 2 + math.pi / 4
        rows = []
        steps = 10
        for i in range(steps + 1):
            phi = base - math.pi / 4 + (math.pi / 2) * i / steps
            limit = DOME_R / max(abs(math.cos(phi)), abs(math.sin(phi)))
            row = []
            for j in range(7):
                r = DOME_R + (limit - DOME_R) * j / 6
                z = SPRING + math.sqrt(max(PEND_R ** 2 - r * r, 0.0))
                row.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
            rows.append(row)
        grid_surface(builder, rows, "gold_mosaic", lambda p: Vector((-p.x, -p.y, -(p.z - SPRING))), True)
    for side in range(4):
        angle = side * math.pi / 2
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        tangent = Vector((-direction.y, direction.x, 0.0))
        rows = []
        for depth in (DOME_R, DOME_R + 1.6):
            row = []
            for k in range(17):
                s = -DOME_R + 2 * DOME_R * k / 16
                z = SPRING + math.sqrt(max(DOME_R ** 2 - s * s, 0.0))
                row.append(direction * depth + tangent * s + Vector((0, 0, z)))
            rows.append(row)
        grid_surface(builder, rows, "gold_mosaic", lambda p: Vector((0, 0, -1)), True)


def great_arch_faces(builder, side):
    direction = Vector((0.0, side, 0.0))
    tangent = Vector((1.0, 0.0, 0.0))
    outer = 17.6
    rows = []
    for radius in (DOME_R, outer):
        row = []
        for k in range(17):
            a = math.pi * k / 16
            row.append(direction * (DOME_R + 1.6) + tangent * (radius * math.cos(a))
                       + Vector((0, 0, SPRING + radius * math.sin(a))))
        rows.append(row)
    grid_surface(builder, rows, "plaster", lambda p: direction, False, HONEY)
    rows = []
    for depth in (DOME_R + 1.6, DOME_R - 1.0):
        row = []
        for k in range(17):
            a = math.pi * k / 16
            row.append(direction * depth + tangent * (outer * math.cos(a)) + Vector((0, 0, SPRING + outer * math.sin(a))))
        rows.append(row)
    grid_surface(builder, rows, "lead", lambda p: Vector((p.x, 0.0, p.z - SPRING)), True)


def tympanum(builder, side):
    v_in = side * DOME_R
    v_out = side * (DOME_R + 1.6)
    bottom = 20.0
    outline = [(-DOME_R, bottom), (DOME_R, bottom)]
    for k in range(17):
        a = math.pi * k / 16
        outline.append((DOME_R * math.cos(a), SPRING + DOME_R * math.sin(a)))
    for v, hint, material, colour in ((v_in, -side, "plaster", WARM_WHITE), (v_out, side, "plaster", HONEY)):
        facing_quad(builder, [(x, v, z) for x, z in outline], (0, hint, 0), material, colour=colour)
    for row_z, xs, w, h in ((25.6, (-9.6, -3.2, 3.2, 9.6), 2.2, 4.4), (31.4, (-6.6, -2.2, 2.2, 6.6), 1.9, 4.0)):
        for x in xs:
            window(builder, (x, v_out, row_z), (side, 0, 0), (0, side, 0), w, h, 1.6)
    for x in (-12.0, -7.2, -2.4, 2.4, 7.2, 12.0):
        window(builder, (x, v_out, 21.0), (side, 0, 0), (0, side, 0), 1.3, 2.6, 1.6)


def dome(builder):
    top = window_band(builder, (0.0, 0.0, DOME_Z), DOME_R, 1.0, DOME_Z, 3.2, 0.0, TAU, 40, 0.32, 1.1, lintel=0.9)
    el_in = math.asin((top - DOME_Z) / DOME_R)
    shell(builder, (0.0, 0.0, DOME_Z), DOME_R, 0.0, TAU, el_in, math.pi / 2, 80, 12, "gold_mosaic", True)
    r_out = DOME_R + 1.0
    el_out = math.asin((top - DOME_Z) / r_out)
    shell(builder, (0.0, 0.0, DOME_Z), r_out, 0.0, TAU, el_out, math.pi / 2, 80, 10, "lead", False)
    for k in range(40):
        a = TAU * k / 40 + TAU / 80
        rows = []
        for depth in (DOME_R - 0.32, DOME_R):
            row = []
            for i in range(10):
                el = el_in + (math.pi / 2 - 0.05 - el_in) * i / 9
                width = 0.28 * math.cos(el) + 0.04
                centre = sphere_point((0, 0, DOME_Z), depth, a, el)
                tangent = Vector((-math.sin(a), math.cos(a), 0.0))
                row.append((centre, tangent * width))
            rows.append(row)
        inner_rows = [[c - t for c, t in rows[0]], [c + t for c, t in rows[0]]]
        grid_surface(builder, [list(x) for x in zip(*inner_rows)], "gold_mosaic",
                     lambda p: -(p - Vector((0, 0, DOME_Z))), True, (0.86, 0.74, 0.55))
    annulus(builder, (0, 0, 0), DOME_R - 0.4, r_out + 0.5, top, 0.0, TAU, 80, "marble_white", True, WARM_WHITE)
    revolve_band(builder, (0, 0, 0), r_out + 0.5, top - 0.35, top, 0.0, TAU, 80, "marble_white", True, WARM_WHITE)
    medallion = sphere_point((0, 0, DOME_Z), DOME_R - 0.05, 0.0, math.pi / 2)
    facing_quad(builder, [medallion + Vector((2.2 * math.cos(a), 2.2 * math.sin(a), -0.12)) for a in [TAU * k / 16 for k in range(16)]],
                (0, 0, -1), "matte", colour=(0.08, 0.13, 0.4))
    for w, h in ((0.28, 1.6), (1.1, 0.28)):
        facing_quad(builder, [medallion + Vector((x, y, -0.16)) for x, y in ((-w, -h), (w, -h), (w, h), (-w, h))], (0, 0, -1),
                    "gold_mosaic")
    crown = DOME_Z + r_out
    tinted(builder, (1.0, 1.0, 1.0), lambda: builder.lathe([(0.0, crown - 0.2), (0.7, crown), (0.45, crown + 0.6),
                                                            (0.0, crown + 0.8)], 10, "bronze_gilt"))
    cross(builder, (0.0, 0.0, crown + 0.7), 3.4)
    skirt = [(r_out + 0.2, DOME_Z + 0.8), (22.5, 33.0)]
    rows = []
    for r, z in skirt:
        rows.append([Vector((r * math.cos(TAU * k / 64), r * math.sin(TAU * k / 64), z)) for k in range(65)])
    grid_surface(builder, rows, "lead", lambda p: Vector((p.x, p.y, 4.0 * (p.length - 0.0) / max(p.length, 1))),
                 True)


def semidome(builder, sign):
    centre = Vector((sign * DOME_R, 0.0, SPRING))
    start = -math.pi / 2 if sign > 0 else math.pi / 2
    top = window_band(builder, centre, DOME_R, 1.0, SPRING, 2.6, start, math.pi, 5, 0.42, 0.0, lintel=0.7)
    el_in = math.asin((top - SPRING) / DOME_R)
    shell(builder, centre, DOME_R, start, math.pi, el_in, math.pi / 2, 30, 10, "gold_mosaic", True)
    r_out = DOME_R + 1.0
    el_out = math.asin((top - SPRING) / r_out)
    shell(builder, centre, r_out, start, math.pi, el_out, math.pi / 2, 30, 8, "lead", False)
    annulus(builder, (centre.x, centre.y, 0.0), DOME_R - 0.3, r_out + 0.4, top, start, math.pi, 30, "marble_white",
            True, WARM_WHITE)


def exedra_columns(builder, sign):
    centre = Vector((sign * DOME_R, 0.0))
    template = impost_column(0.95, 9.0, "porphyry")
    upper = impost_column(0.7, 6.5, "marble_white")
    for degrees in (-72, -52, -32, 32, 52, 72):
        a = math.radians(degrees) + (0 if sign > 0 else math.pi)
        p = centre + Vector((math.cos(a), math.sin(a))) * (DOME_R - 0.8)
        for template_used, z, colour in ((template, 0.0, (1.0, 1.0, 1.0)), (upper, GALLERY_Z + 0.8, VERDE)):
            first = len(builder.polygons)
            builder.merge(template_used, Matrix.Translation((p.x, p.y, z)))
            builder.tint(first, colour)


def block_walls(builder):
    t = 2.0
    for v0, v1 in ((HALF_W - t, HALF_W), (-HALF_W, -HALF_W + t)):
        box(builder, (WEST, v0, -2.0), (EAST, v1, ROOF_Z + 0.6), "plaster", HONEY)
    for u0, u1 in ((EAST - t, EAST),):
        for v0, v1 in ((APSE_R, HALF_W), (-HALF_W, -APSE_R)):
            box(builder, (u0, v0, -2.0), (u1, v1, ROOF_Z + 0.6), "plaster", HONEY)
    for v0, v1 in ((4.0, HALF_W), (-HALF_W, -4.0)):
        box(builder, (WEST, v0, -2.0), (WEST + t, v1, ROOF_Z + 0.6), "plaster", HONEY)
    box(builder, (WEST, -4.0, 9.0), (WEST + t, 4.0, ROOF_Z + 0.6), "plaster", HONEY)
    for sign_u in (1, -1):
        for sign_v in (1, -1):
            u0, u1 = sorted((sign_u * DOME_R, sign_u * 22.5))
            v0, v1 = sorted((sign_v * (DOME_R + 1.6), sign_v * HALF_W))
            box(builder, (u0, v0, -2.0), (u1, v1, 37.5), "plaster", HONEY)
            facing_quad(builder, [(u0, v0, 37.5), (u1, v0, 37.5), (u1, v1, 38.6), (u0, v1, 38.6)][::1],
                        (0, 0, 1), "lead")
    for side in (1, -1):
        v = side * HALF_W
        for u in [x * 4.6 for x in range(-7, 7)]:
            if WEST + 2 < u < EAST - 2 and not (DOME_R - 1 < abs(u) < 23.5):
                window(builder, (u, v, 3.0), (side, 0, 0), (0, side, 0), 1.8, 4.6, 2.0)
                window(builder, (u, v, 15.0), (side, 0, 0), (0, side, 0), 2.0, 5.6, 2.0)
    for v in (-28.0, -21.0, 21.0, 28.0, -12.0, 12.0):
        window(builder, (EAST, v, 3.5), (0, -1, 0), (1, 0, 0), 1.8, 4.4, 2.0)
        window(builder, (EAST, v, 15.0), (0, -1, 0), (1, 0, 0), 2.0, 5.4, 2.0)


def roofs_and_floors(builder):
    def inside(u, v):
        return WEST + 2.0 < u < EAST - 2.0 and abs(v) < HALF_W - 2.0
    floor_inside = lambda u, v: WEST + 2.0 < u < EAST and abs(v) < HALF_W - 2.0
    slab_strips(builder, floor_inside, WEST, EAST, -HALF_W, HALF_W, -0.4, 0.0, 1.0, "marble_paving", "marble_paving",
                top_colour=(0.9, 0.86, 0.8), sides=False)
    for u in (-22.0, -8.5, 8.5, 22.0):
        facing_quad(builder, [(u - 0.45, -DOME_R - 1.0, 0.02), (u + 0.45, -DOME_R - 1.0, 0.02), (u + 0.45, DOME_R + 1.0, 0.02),
                              (u - 0.45, DOME_R + 1.0, 0.02)], (0, 0, 1), "marble_white", colour=(0.24, 0.5, 0.36))
    gallery = lambda u, v: inside(u, v) and not nave_open(u, v, 0.4) and not pier_at(u, v) and abs(v) > DOME_R + 1.4 or (
        inside(u, v) and not nave_open(u, v, 1.6) and not pier_at(u, v))
    slab_strips(builder, gallery, WEST, EAST, -HALF_W, HALF_W, GALLERY_Z, GALLERY_Z + 0.8, 1.0, "marble_paving",
                "plaster", bottom_colour=WARM_WHITE)
    roof = lambda u, v: (WEST - 0.5 < u < EAST + 0.5 and abs(v) < HALF_W + 0.5 and not nave_open(u, v, 0.6)
                         and not pier_at(u, v))
    slab_strips(builder, roof, WEST - 0.5, EAST + 0.5, -HALF_W - 0.5, HALF_W + 0.5, ROOF_Z, ROOF_Z + 0.6, 1.0, "lead",
                "plaster", bottom_colour=WARM_WHITE)


def arcade(builder, v, half, supports, spring, top, rise_max, colour, steps=10):
    for a, b in zip(supports[:-1], supports[1:]):
        mid = (a + b) / 2
        span = (b - a) / 2
        rise = min(span, rise_max)
        points = [(mid - span * math.cos(math.pi * k / steps), spring + rise * math.sin(math.pi * k / steps))
                  for k in range(steps + 1)]
        for (u0, z0), (u1, z1) in zip(points[:-1], points[1:]):
            for side in (1, -1):
                y = v + side * half
                facing_quad(builder, [(u0, y, z0), (u1, y, z1), (u1, y, top), (u0, y, top)], (0, side, 0), "plaster",
                            colour=colour)
            facing_quad(builder, [(u0, v - half, z0), (u1, v - half, z1), (u1, v + half, z1), (u0, v + half, z0)],
                        (mid - (u0 + u1) / 2, 0, spring - (z0 + z1) / 2), "plaster", colour=colour)


def aisle_colonnades(builder):
    for side in (1, -1):
        v = side * (DOME_R + 0.8)
        colonnade(builder, (-DOME_R, v), (DOME_R, v), 4, 9.0, 1.1, 0.0, style="impost")
        supports = [-DOME_R] + [-DOME_R + 2 * DOME_R * (k + 0.5) / 4 for k in range(4)] + [DOME_R]
        arcade(builder, v, 0.8, supports, 9.0, GALLERY_Z + 0.8, 3.4, WARM_WHITE)
        colonnade(builder, (-DOME_R, v), (DOME_R, v), 6, 6.8, 0.75, GALLERY_Z + 0.8, VERDE, style="impost")
        box(builder, (-DOME_R, v - 0.8, 19.6), (DOME_R, v + 0.8, 20.0), "marble_white", WARM_WHITE, bottom=True)


def apse(builder):
    centre = Vector((EAST, 0.0))
    sides = 5
    outer = APSE_R + 1.6
    points = []
    for k in range(sides + 1):
        a = -math.pi / 2 + math.pi * k / sides
        points.append(centre + Vector((math.cos(a), math.sin(a))) * outer / math.cos(math.pi / (2 * sides)))
    for p, q in zip(points[:-1], points[1:]):
        normal = Vector(((p + q) / 2 - centre)).to_3d()
        facing_quad(builder, [(p.x, p.y, -2.0), (q.x, q.y, -2.0), (q.x, q.y, 20.6), (p.x, p.y, 20.6)], normal,
                    "plaster", colour=HONEY)
        mid = (p + q) / 2
        right = (q - p).normalized().to_3d()
        window(builder, (mid.x, mid.y, 11.0), right, normal, 1.6, 5.2, 1.6)
    revolve_band(builder, (EAST, 0, 0), APSE_R, 0.0, 20.6, -math.pi / 2, math.pi, 16, "pavonazzetto", False,
                 (0.98, 0.95, 0.92))
    annulus(builder, (EAST, 0, 0), APSE_R, outer + 0.2, 20.6, -math.pi / 2, math.pi, 16, "marble_white", True)
    shell(builder, (EAST, 0.0, 20.6), APSE_R, -math.pi / 2, math.pi, 0.0, math.pi / 2, 16, 6, "gold_mosaic", True)
    shell(builder, (EAST, 0.0, 20.6), outer - 0.4, -math.pi / 2, math.pi, 0.0, math.pi / 2, 12, 5, "lead", False)
    for k in range(5):
        a = -math.pi / 2 + math.pi * (k + 0.5) / 5
        p = centre + Vector((math.cos(a), math.sin(a))) * APSE_R
        tinted(builder, (1.0, 1.0, 1.0), lambda p=p: builder.box((p.x - 0.4, p.y - 0.4, 0.0), (p.x + 0.4, p.y + 0.4, 0.6 + 0.0),
                                                                 "marble_white", bottom=False))
    for step in range(5):
        r = APSE_R - 0.6 - step * 0.55
        rows = []
        for z in (0.45 * step, 0.45 * (step + 1)):
            rows.append([Vector((EAST + r * math.cos(-math.pi / 2 + math.pi * k / 12), r * math.sin(-math.pi / 2 + math.pi * k / 12), z))
                         for k in range(13)])
        grid_surface(builder, rows, "marble_white", lambda p: Vector((EAST - p.x, -p.y, 0.0)), False)
        annulus(builder, (EAST, 0, 0), r - 0.55, r, 0.45 * (step + 1), -math.pi / 2, math.pi, 12, "marble_white", True)


def lining(builder):
    for sign_u in (1, -1):
        for sign_v in (1, -1):
            u0, u1 = sorted((sign_u * DOME_R, sign_u * 22.5))
            v = sign_v * (DOME_R + 1.6) - sign_v * 0.03
            for z0, z1, mat, colour in ((0.0, 0.5, "granite_grey", (0.4, 0.42, 0.44)), (0.5, 11.0, "pavonazzetto", None),
                                        (11.0, 12.0, "giallo", None), (12.8, 19.6, "pavonazzetto", (0.92, 0.95, 1.0))):
                facing_quad(builder, [(u0, v, z0), (u1, v, z0), (u1, v, z1), (u0, v, z1)], (0, -sign_v, 0), mat,
                            colour=colour)
            u = sign_u * DOME_R - sign_u * 0.03
            v0, v1 = sorted((sign_v * (DOME_R + 1.6), sign_v * HALF_W))
            for z0, z1, mat in ((0.0, 11.0, "giallo"), (12.8, 19.6, "pavonazzetto")):
                facing_quad(builder, [(u, v0, z0), (u, v1, z0), (u, v1, z1), (u, v0, z1)], (-sign_u, 0, 0), mat)
            u = sign_u * 22.5 + sign_u * 0.03
            for z0, z1, mat in ((0.0, 11.0, "pavonazzetto"),):
                facing_quad(builder, [(u, v0, z0), (u, v1, z0), (u, v1, z1), (u, v0, z1)], (sign_u, 0, 0), mat)


def furnishings(builder):
    chancel_u = DOME_R + 2.0
    for v in (-7.5, 7.5):
        box(builder, (chancel_u, v - 0.12, 0.0), (EAST - 2.0, v + 0.12, 1.1), "silver")
    box(builder, (chancel_u - 0.12, -7.5, 0.0), (chancel_u + 0.12, 7.5, 1.1), "silver")
    for k in range(12):
        v = -7.0 + 14.0 * k / 11
        tinted(builder, (1.0, 1.0, 1.0), lambda v=v: builder.lathe([(0.16, 0.0), (0.14, 4.2), (0.22, 4.4), (0.0, 4.45)],
                                                                    8, "silver", matrix=Matrix.Translation((chancel_u, v, 0.0))))
    box(builder, (chancel_u - 0.2, -7.2, 4.4), (chancel_u + 0.2, 7.2, 4.8), "silver")
    for k in range(6):
        v = -6.0 + 12.0 * k / 5
        disc = Matrix.Translation((chancel_u - 0.14, v, 2.6)) @ Matrix.Rotation(math.pi / 2, 4, "Y") @ Matrix.Diagonal((0.55, 0.42, 1.0, 1.0))
        tinted(builder, (1.0, 1.0, 1.0), lambda disc=disc: builder.lathe([(0.0, 0.0), (1.0, 0.0), (1.0, 0.04)], 12,
                                                                        "silver", matrix=disc))
    centre = Vector((EAST - 6.0, 0.0))
    for du, dv in ((-2.2, -2.2), (2.2, -2.2), (2.2, 2.2), (-2.2, 2.2)):
        tinted(builder, (1.0, 1.0, 1.0), lambda du=du, dv=dv: builder.lathe(
            [(0.22, 0.0), (0.18, 5.6), (0.28, 5.8), (0.0, 5.85)], 8, "silver",
            matrix=Matrix.Translation((centre.x + du, centre.y + dv, 0.0))))
    box(builder, (centre.x - 2.6, centre.y - 2.6, 5.8), (centre.x + 2.6, centre.y + 2.6, 6.6), "silver", bottom=True)
    tinted(builder, (1.0, 1.0, 1.0), lambda: builder.lathe([(3.6, 6.6), (0.3, 9.6), (0.0, 9.8)], 8, "silver",
                                                          matrix=Matrix.Translation((centre.x, centre.y, 0.0))
                                                          @ Matrix.Rotation(math.pi / 8, 4, "Z")))
    cross(builder, (centre.x, centre.y, 9.7), 1.3)
    box(builder, (centre.x - 1.4, centre.y - 0.8, 0.0), (centre.x + 1.4, centre.y + 0.8, 1.1), "bronze_gilt")
    ambo = Matrix.Diagonal((1.5, 1.0, 1.0, 1.0))
    tinted(builder, (1.0, 1.0, 1.0), lambda: builder.lathe([(1.6, 0.0), (1.6, 1.9), (1.85, 2.05), (1.85, 2.7), (0.0, 2.7)],
                                                          16, "marble_white", matrix=Matrix.Translation((AMBO_U, 0.0, 0.0)) @ ambo))
    for k in range(8):
        a = TAU * k / 8
        p = Vector((AMBO_U + 2.75 * math.cos(a), 1.85 * math.sin(a)))
        tinted(builder, VERDE, lambda p=p: builder.lathe([(0.18, 0.0), (0.15, 2.4)], 8, "marble_white",
                                                          matrix=Matrix.Translation((p.x, p.y, 0.0)), caps=False))
    for direction in (-1, 1):
        for k in range(8):
            u0 = AMBO_U + direction * (2.3 + k * 0.28)
            u1 = u0 + direction * 0.28
            z = 2.7 - (k + 1) * 0.3
            box(builder, (min(u0, u1), -0.6, 0.0), (max(u0, u1), 0.6, z), "marble_white", WARM_WHITE)
    solea_start = AMBO_U + 2.3 + 8 * 0.28
    for side in (1, -1):
        quad = [(solea_start, side * 1.1, 0.0), (chancel_u, side * 1.1, 0.0), (chancel_u, side * 1.1, 1.0),
                (solea_start, side * 1.1, 1.0)]
        facing_quad(builder, quad, (0, side, 0), "marble_white")
        facing_quad(builder, quad, (0, -side, 0), "marble_white")
    ring_z = 5.6
    ring_r = 11.0
    revolve_band(builder, (0, 0, 0), ring_r, ring_z - 0.12, ring_z + 0.12, 0.0, TAU, 48, "bronze_gilt", True)
    revolve_band(builder, (0, 0, 0), ring_r, ring_z - 0.12, ring_z + 0.12, 0.0, TAU, 48, "bronze_gilt", False)
    for k in range(48):
        a = TAU * k / 48
        x, y = ring_r * math.cos(a), ring_r * math.sin(a)
        tinted(builder, (1.0, 1.0, 1.0), lambda x=x, y=y: builder.lathe(
            [(0.0, ring_z + 0.1), (0.09, ring_z + 0.2), (0.05, ring_z + 0.38), (0.0, ring_z + 0.42)], 4, "flame",
            matrix=Matrix.Translation((x, y, 0.0))))
    for k in range(8):
        a = TAU * k / 8
        start = Vector((ring_r * math.cos(a), ring_r * math.sin(a), ring_z))
        end = Vector((DOME_R * 0.92 * math.cos(a), DOME_R * 0.92 * math.sin(a), DOME_Z + 1.0))
        axis = (end - start).normalized()
        side = axis.cross(Vector((0, 0, 1))).normalized() * 0.03
        facing_quad(builder, [start - side, start + side, end + side, end - side], axis.cross(side), "bronze")
        facing_quad(builder, [start - side, start + side, end + side, end - side], -axis.cross(side), "bronze")


def narthexes(builder):
    box(builder, (NARTHEX, -HALF_W, -2.0), (WEST, -HALF_W + 1.8, 21.6), "plaster", HONEY)
    box(builder, (NARTHEX, HALF_W - 1.8, -2.0), (WEST, HALF_W, 21.6), "plaster", HONEY)
    box(builder, (NARTHEX, -HALF_W, -2.0), (NARTHEX + 1.6, HALF_W, 21.6), "plaster", HONEY)
    facing_quad(builder, [(NARTHEX - 0.3, -HALF_W - 0.3, 21.6), (WEST, -HALF_W - 0.3, 21.6), (WEST, HALF_W + 0.3, 21.6),
                          (NARTHEX - 0.3, HALF_W + 0.3, 21.6)], (0, 0, 1), "lead")
    box(builder, (NARTHEX + 1.6, -HALF_W + 1.8, 10.0), (WEST, HALF_W - 1.8, 10.8), "marble_paving", WARM_WHITE, bottom=True)
    for v in [k * 5.0 for k in range(-6, 7)]:
        window(builder, (NARTHEX, v, 13.0), (0, -1, 0), (-1, 0, 0), 2.2, 5.6, 1.6)
    box(builder, (EXONARTHEX, -HALF_W, -2.0), (NARTHEX, -HALF_W + 1.4, 11.6), "plaster", HONEY)
    box(builder, (EXONARTHEX, HALF_W - 1.4, -2.0), (NARTHEX, HALF_W, 11.6), "plaster", HONEY)
    for v0, v1 in ((-HALF_W, -2.5), (2.5, HALF_W)):
        box(builder, (EXONARTHEX, v0, -2.0), (EXONARTHEX + 1.4, v1, 11.6), "plaster", HONEY)
    box(builder, (EXONARTHEX, -2.5, 6.8), (EXONARTHEX + 1.4, 2.5, 11.6), "plaster", HONEY)
    rows = [[(EXONARTHEX - 0.6, -HALF_W - 0.4, 11.4), (EXONARTHEX - 0.6, HALF_W + 0.4, 11.4)],
            [(NARTHEX, -HALF_W - 0.4, 13.2), (NARTHEX, HALF_W + 0.4, 13.2)]]
    grid_surface(builder, rows, "lead", lambda p: Vector((-0.6, 0, 1)), False)
    for v in (-25.0, -17.5, -10.0, 10.0, 17.5, 25.0):
        tinted(builder, (0.55, 0.36, 0.2), lambda v=v: builder.box((EXONARTHEX - 0.1, v - 1.1, 0.0),
                                                                    (EXONARTHEX + 0.02, v + 1.1, 4.8), "bronze", bottom=False))
        window(builder, (EXONARTHEX, v, 6.5), (0, -1, 0), (-1, 0, 0), 1.8, 3.6, 1.4, lit=False)
    tinted(builder, (0.6, 0.4, 0.22), lambda: builder.box((EXONARTHEX - 0.1, -2.0, 0.0), (EXONARTHEX + 0.02, 2.0, 6.4),
                                                          "bronze_gilt", bottom=False))
    for v in (-6.0, 0.0, 6.0):
        tinted(builder, (0.6, 0.4, 0.22), lambda v=v: builder.box((NARTHEX - 0.05, v - 1.4, 0.0), (NARTHEX + 0.02, v + 1.4, 6.0),
                                                                  "bronze", bottom=False))
    tinted(builder, (0.6, 0.42, 0.24), lambda: builder.box((WEST - 0.05, -2.2, 0.0), (WEST + 0.02, 2.2, 8.4),
                                                          "bronze_gilt", bottom=False))
    floor = lambda u, v: abs(v) < HALF_W - 1.0
    slab_strips(builder, floor, EXONARTHEX, WEST, -HALF_W, HALF_W, -0.4, 0.0, 1.0, "marble_paving", "marble_paving",
                sides=False)
    for v in (-31.0, -21.25, -13.75, -6.0, 6.0, 13.75, 21.25, 31.0):
        box(builder, (EXONARTHEX - 0.45, v - 0.55, -0.5), (EXONARTHEX, v + 0.55, 11.2), "plaster", HONEY)
    for v in [k * 5.0 + 2.5 for k in range(-7, 7)]:
        box(builder, (NARTHEX - 0.4, v - 0.45, 11.6), (NARTHEX, v + 0.45, 21.2), "plaster", HONEY)
    for u0, z in ((EXONARTHEX, 11.0), (NARTHEX, 21.0)):
        box(builder, (u0 - 0.7, -HALF_W - 0.3, z), (u0, HALF_W + 0.3, z + 0.6), "marble_white", WARM_WHITE, bottom=True)
    for side in (1, -1):
        v0, v1 = sorted((side * (HALF_W + 0.5), side * (HALF_W - 0.1)))
        box(builder, (WEST - 0.3, v0, ROOF_Z - 0.4), (EAST + 0.3, v1, ROOF_Z + 0.2), "marble_white", WARM_WHITE, bottom=True)
        for u in (-29.5, -9.0, 9.0, 27.5):
            v0, v1 = sorted((side * HALF_W, side * (HALF_W + 0.5)))
            box(builder, (u - 0.6, v0, -0.5), (u + 0.6, v1, ROOF_Z - 0.4), "plaster", HONEY)


def atrium(builder):
    u0, u1 = ATRIUM_WEST, EXONARTHEX
    half = ATRIUM_HALF
    depth = 6.5
    height = 7.2
    for side in (1, -1):
        v_back = side * half
        box(builder, (u0, min(v_back, v_back - side * 1.2), -2.0), (u1, max(v_back, v_back - side * 1.2), height + 0.4),
            "plaster", HONEY)
        colonnade(builder, (u0 + depth, side * (half - depth)), (u1, side * (half - depth)), 9, 5.6, 0.62, 0.3,
                  WARM_WHITE)
        box(builder, (u0 + depth, side * (half - depth) - 0.45, 5.9), (u1, side * (half - depth) + 0.45, 6.6),
            "marble_white", WARM_WHITE, bottom=True)
        rows = [[(u0, side * (half - depth - 0.9), 6.6), (u1, side * (half - depth - 0.9), 6.6)],
                [(u0, side * half, height + 1.6), (u1, side * half, height + 1.6)]]
        grid_surface(builder, rows, "terracotta_tiles", lambda p: Vector((0, -side * 0.4, 1)), False)
        rows = [[(u0, side * (half - depth - 0.9), 6.55), (u1, side * (half - depth - 0.9), 6.55)],
                [(u0, side * half, height + 1.55), (u1, side * half, height + 1.55)]]
        grid_surface(builder, rows, "plaster", lambda p: Vector((0, side * 0.4, -1)), False, WARM_WHITE)
    box(builder, (u0, -half, -2.0), (u0 + 1.2, -4.0, height + 0.4), "plaster", HONEY)
    box(builder, (u0, 4.0, -2.0), (u0 + 1.2, half, height + 0.4), "plaster", HONEY)
    colonnade(builder, (u0 + depth, -half + depth), (u0 + depth, half - depth), 8, 5.6, 0.62, 0.3, WARM_WHITE)
    box(builder, (u0 + depth - 0.45, -half + depth, 5.9), (u0 + depth + 0.45, half - depth, 6.6), "marble_white",
        WARM_WHITE, bottom=True)
    rows = [[(u0 + depth + 0.9, -half, 6.6), (u0 + depth + 0.9, half, 6.6)], [(u0, -half, height + 1.6), (u0, half, height + 1.6)]]
    grid_surface(builder, rows, "terracotta_tiles", lambda p: Vector((0.4, 0, 1)), False)
    box(builder, (u0 - 3.0, -6.0, -2.0), (u0 + 1.2, 6.0, 11.0), "plaster", HONEY)
    facing_quad(builder, [(u0 - 3.0, -6.4, 11.0), (u0 + 1.4, -6.4, 11.0), (u0 + 1.4, 0, 13.0), (u0 - 3.0, 0, 13.0)],
                (0, -1, 1), "terracotta_tiles")
    facing_quad(builder, [(u0 - 3.0, 6.4, 11.0), (u0 + 1.4, 6.4, 11.0), (u0 + 1.4, 0, 13.0), (u0 - 3.0, 0, 13.0)],
                (0, 1, 1), "terracotta_tiles")
    tinted(builder, (0.55, 0.36, 0.2), lambda: builder.box((u0 - 3.05, -2.0, 0.0), (u0 - 2.95, 2.0, 6.0), "bronze",
                                                          bottom=False))
    court = lambda u, v: True
    slab_strips(builder, court, u0 + 1.2, u1, -half + 1.2, half - 1.2, -0.5, 0.0, 1.0, "marble_paving", "marble_paving",
                top_colour=(0.84, 0.8, 0.72), sides=False)
    centre = Vector(((u0 + depth + u1) / 2, 0.0))
    octagon = Matrix.Translation((centre.x, centre.y, 0.0)) @ Matrix.Rotation(math.pi / 8, 4, "Z")
    tinted(builder, (0.95, 0.92, 0.88), lambda: builder.lathe([(4.6, 0.0), (4.6, 0.9), (4.2, 0.9), (4.2, 0.35)], 8,
                                                             "marble_white", matrix=octagon))
    facing_quad(builder, [octagon @ Vector((4.25 * math.cos(TAU * k / 8), 4.25 * math.sin(TAU * k / 8), 0.6))
                          for k in range(8)], (0, 0, 1), "pool")
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        p = centre + Vector((math.cos(a), math.sin(a))) * 3.0
        tinted(builder, VERDE, lambda p=p: builder.lathe([(0.22, 0.6), (0.2, 5.2), (0.3, 5.4)], 8, "marble_white",
                                                          matrix=Matrix.Translation((p.x, p.y, 0.0))))
    tinted(builder, (1.0, 1.0, 1.0), lambda: builder.lathe([(3.3, 5.4), (3.3, 6.0), (0.4, 8.4), (0.0, 8.6)], 8, "lead",
                                                          matrix=Matrix.Translation((centre.x, centre.y, 0.0))))
    cross(builder, (centre.x, centre.y, 8.5), 1.2)
    tinted(builder, (1.0, 1.0, 1.0), lambda: builder.lathe([(0.6, 0.6), (0.5, 1.8), (0.9, 2.0), (0.0, 2.2)], 8,
                                                          "marble_white", matrix=Matrix.Translation((centre.x, centre.y, 0.0))))
    return centre


def interior_ring_walls(builder):
    for sign in (1, -1):
        centre = Vector((sign * DOME_R, 0.0))
        start = -math.pi / 2 if sign > 0 else math.pi / 2
        for z0, z1, mat in ((9.0, GALLERY_Z + 0.8, "plaster"), (19.6, SPRING, "plaster")):
            rows = []
            for z in (z0, z1):
                rows.append([Vector((centre.x + (DOME_R - 0.6) * math.cos(start + math.pi * k / 24),
                                     centre.y + (DOME_R - 0.6) * math.sin(start + math.pi * k / 24), z)) for k in range(25)])
            grid_surface(builder, rows, mat, lambda p, c=centre: Vector((c.x - p.x, c.y - p.y, 0.0)), False, WARM_WHITE)


def hagia_sophia():
    builder = MeshBuilder()
    block_walls(builder)
    roofs_and_floors(builder)
    for side in (1, -1):
        tympanum(builder, side)
        great_arch_faces(builder, side)
    pendentives(builder)
    dome(builder)
    for sign in (1, -1):
        semidome(builder, sign)
        exedra_columns(builder, sign)
    interior_ring_walls(builder)
    aisle_colonnades(builder)
    apse(builder)
    lining(builder)
    furnishings(builder)
    narthexes(builder)
    fountain = atrium(builder)
    return builder, fountain


def baptistery(r=6.5):
    builder = MeshBuilder()
    sides = 8
    for k in range(sides):
        a0, a1 = TAU * k / sides, TAU * (k + 1) / sides
        p = Vector((r * math.cos(a0), r * math.sin(a0)))
        q = Vector((r * math.cos(a1), r * math.sin(a1)))
        normal = ((p + q) / 2).to_3d()
        facing_quad(builder, [(p.x, p.y, -2.0), (q.x, q.y, -2.0), (q.x, q.y, 11.0), (p.x, p.y, 11.0)], normal, "plaster",
                    colour=HONEY)
        mid = (p + q) / 2
        window(builder, (mid.x, mid.y, 6.0), (q - p).normalized().to_3d(), normal, 1.4, 3.4, 1.0, lit=False)
    annulus(builder, (0, 0, 0), 0.0, r + 0.3, 11.0, 0.0, TAU, 16, "lead", True)
    revolve_band(builder, (0, 0, 0), r * 0.69, 11.0, 13.4, 0.0, TAU, 16, "plaster", True, HONEY)
    shell(builder, (0.0, 0.0, 13.4), r * 0.72, 0.0, TAU, 0.0, math.pi / 2, 16, 5, "lead", False)
    cross(builder, (0.0, 0.0, 13.3 + r * 0.72), 1.5)
    return builder


def hagia_irene():
    builder = MeshBuilder()
    length, half = 44.0, 16.0
    for v0, v1 in ((half - 1.4, half), (-half, -half + 1.4)):
        box(builder, (-length / 2, v0, -2.0), (length / 2, v1, 14.0), "banded")
    box(builder, (-length / 2, -half, -2.0), (-length / 2 + 1.4, half, 14.0), "banded")
    box(builder, (length / 2 - 1.4, -half, -2.0), (length / 2, half, 14.0), "banded")
    rows = [[(-length / 2 - 0.5, -half - 0.6, 13.8), (length / 2 + 0.5, -half - 0.6, 13.8)],
            [(-length / 2 - 0.5, 0.0, 18.0), (length / 2 + 0.5, 0.0, 18.0)],
            [(-length / 2 - 0.5, half + 0.6, 13.8), (length / 2 + 0.5, half + 0.6, 13.8)]]
    grid_surface(builder, rows, "terracotta_tiles", lambda p: Vector((0, p.y * 0.3, 1)), False)
    for x in (-length / 2, length / 2):
        sign = 1 if x > 0 else -1
        facing_quad(builder, [(x, -half - 0.6, 13.8), (x, half + 0.6, 13.8), (x, 0.0, 18.0)], (sign, 0, 0), "banded")
    base, rise, radius = 18.4, 5.0, 8.3
    revolve_band(builder, (4.0, 0, 0), radius, 13.8, base, 0.0, TAU, 24, "banded", True)
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        p = Vector((4.0 + (radius + 0.02) * math.cos(a), (radius + 0.02) * math.sin(a), 16.9))
        window(builder, p, (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0), 0.7, 1.3, 1.0, lit=False)
    curvature = (radius ** 2 + rise ** 2) / (2 * rise)
    shell(builder, (4.0, 0.0, base + rise - curvature), curvature, 0.0, TAU, math.asin((curvature - rise) / curvature),
          math.pi / 2, 24, 5, "lead", False)
    cross(builder, (4.0, 0.0, base + rise - 0.1), 1.6)
    revolve_band(builder, (length / 2, 0, 0), 6.0, -2.0, 11.0, -math.pi / 2, math.pi, 10, "banded", True)
    shell(builder, (length / 2, 0.0, 11.0), 6.0, -math.pi / 2, math.pi, 0.0, math.pi / 2, 10, 4, "terracotta_tiles", False)
    for side in (1, -1):
        for x in [-16.0 + 5.0 * k for k in range(7)]:
            window(builder, (x, side * half, 8.0), (side, 0, 0), (0, side, 0), 1.6, 3.6, 1.4, lit=False)
    box(builder, (-length / 2 - 7.0, -half, -2.0), (-length / 2, half, 9.0), "banded")
    facing_quad(builder, [(-length / 2 - 7.5, -half - 0.4, 9.0), (-length / 2, -half - 0.4, 9.0),
                          (-length / 2, half + 0.4, 9.0), (-length / 2 - 7.5, half + 0.4, 9.0)], (0, 0, 1),
                "terracotta_tiles")
    tinted(builder, (0.55, 0.36, 0.2), lambda: builder.box((-length / 2 - 7.06, -1.8, 0.0), (-length / 2 - 6.95, 1.8, 4.5),
                                                          "bronze", bottom=False))
    a0 = -length / 2 - 7.0
    for side in (1, -1):
        box(builder, (a0 - 30.0, side * half - (0.6 if side > 0 else 0.0), -2.0),
            (a0, side * half + (0.0 if side > 0 else 0.6), 5.2), "banded")
        rows = [[(a0 - 30.0, side * (half - 5.0), 4.8), (a0, side * (half - 5.0), 4.8)],
                [(a0 - 30.0, side * half, 6.4), (a0, side * half, 6.4)]]
        grid_surface(builder, rows, "terracotta_tiles", lambda p, s=side: Vector((0, -s * 0.4, 1)), False)
        colonnade(builder, (a0 - 30.0, side * (half - 5.0)), (a0, side * (half - 5.0)), 7, 4.2, 0.5, 0.3, WARM_WHITE)
    box(builder, (a0 - 31.0, -half, -2.0), (a0 - 30.0, -3.0, 5.2), "banded")
    box(builder, (a0 - 31.0, 3.0, -2.0), (a0 - 30.0, half, 5.2), "banded")
    return builder


def light_beams(relative_azimuth, elevation):
    builder = MeshBuilder()
    delta = math.radians(relative_azimuth)
    e = math.radians(elevation)
    direction = Vector((-math.cos(delta) * math.cos(e), math.sin(delta) * math.cos(e), -math.sin(e)))
    sources = []
    for k in range(5):
        a = -math.pi / 2 + math.pi * (k + 0.5) / 5
        sources.append((Vector((DOME_R + DOME_R * math.cos(a), DOME_R * math.sin(a), SPRING + 1.4)), 1.4, 2.4))
    for k in range(5):
        a = -math.pi / 2 + math.pi * (k + 0.5) / 5
        sources.append((Vector((EAST + APSE_R * math.cos(a), APSE_R * math.sin(a), 13.6)), 1.4, 4.6))
    side = direction.cross(Vector((0.0, 0.0, 1.0))).normalized()
    up = side.cross(direction).normalized()
    for origin, width, height in sources:
        length = min(origin.z / math.sin(e), (origin.x - WEST - 4.0) / max(-direction.x, 1e-3))
        end = origin + direction * length
        spread = 1.0 + length / 60.0
        corners = []
        for p, scale in ((origin, 1.0), (end, spread)):
            corners.append([p + side * sx * width / 2 * scale + up * sz * height / 2 * scale
                            for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        for i in range(4):
            j = (i + 1) % 4
            builder.polygon([corners[0][i], corners[0][j], corners[1][j], corners[1][i]], "light_beam")
    return builder

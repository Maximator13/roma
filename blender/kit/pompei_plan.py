import math

from mathutils import Matrix, Vector

ORIGIN = (40.74941, 14.485429)
FORUM_BEARING = -15.0
GRID_BEARING = 57.0
FORUM_ORIGIN = Vector((-64.2, 9.4))
HOLCONIUS = Vector((240.0, 41.0))
FORUM_HALF = (71.0, 19.0)
PORTICO = 5.6

GATES = {
    "marina": Vector((-189.7, -93.0)),
    "ercolano": Vector((-353.4, 262.2)),
    "vesuvio": Vector((-112.2, 440.8)),
    "nola": Vector((450.4, 477.3)),
    "sarno": Vector((758.1, 378.0)),
    "nocera": Vector((674.6, 12.3)),
    "stabia": Vector((381.7, -120.1)),
}
PLEIADES = {
    "temple-de-jupiter": Vector((-77.7, 59.6)),
    "sanctuaire-de-venus": Vector((-144.2, -109.5)),
    "porte-marine": GATES["marina"],
    "thermopolium": Vector((408.9, 150.6)),
    "maison-des-vettii": Vector((-72.2, 298.6)),
    "basilique": Vector((-77.7, -75.6)),
    "temple-d-apollon": Vector((-85.3, -22.2)),
    "macellum": Vector((-26.4, 74.7)),
    "thermes-de-stabies": Vector((177.3, 66.6)),
    "thermes-centraux": Vector((106.6, 234.9)),
    "grand-theatre": Vector((251.4, -66.9)),
    "forum-triangulaire": Vector((191.9, -64.2)),
    "grande-palestre": Vector((714.3, 147.5)),
    "amphitheatre": Vector((822.0, 206.9)),
}


def axis(bearing):
    angle = math.radians(bearing)
    return Vector((math.sin(angle), math.cos(angle)))


FA = axis(FORUM_BEARING)
FB = Vector((FA.y, -FA.x))
GU = axis(GRID_BEARING)
GV = Vector((-GU.y, GU.x))


def forum_point(a, b):
    return FORUM_ORIGIN + FA * a + FB * b


def grid_point(u, v):
    return HOLCONIUS + GU * u + GV * v


def to_forum(point):
    d = Vector(point[:2]) - FORUM_ORIGIN
    return d.dot(FA), d.dot(FB)


def to_grid(point):
    d = Vector(point[:2]) - HOLCONIUS
    return d.dot(GU), d.dot(GV)


def heading_of(direction):
    return math.atan2(-direction[0], direction[1])


def frame(point, along, z=0.0):
    return Matrix.Translation((point[0], point[1], z)) @ Matrix.Rotation(math.atan2(along[1], along[0]), 4, "Z")


def wall_trace():
    west = [GATES["marina"], Vector((-236.0, -28.0)), Vector((-290.0, 70.0)), Vector((-335.0, 175.0)),
            GATES["ercolano"], Vector((-318.0, 340.0)), Vector((-230.0, 405.0)), GATES["vesuvio"],
            Vector((40.0, 462.0)), Vector((250.0, 482.0)), GATES["nola"], Vector((600.0, 452.0)),
            Vector((700.0, 418.0)), GATES["sarno"]]
    east = [grid_point(u, v) for u, v in ((646.0, -45.0), (652.0, -150.0), (640.0, -240.0), (612.0, -275.0),
                                          (500.0, -270.0))]
    south = [GATES["nocera"], grid_point(250.0, -262.0), grid_point(140.0, -245.0), GATES["stabia"],
             Vector((300.0, -168.0)), Vector((215.0, -165.0)), Vector((160.0, -128.0)), Vector((70.0, -128.0)),
             Vector((-20.0, -138.0)), Vector((-110.0, -150.0)), Vector((-180.0, -140.0)), Vector((-205.0, -115.0))]
    return west + east + south


STABIANA = [GATES["stabia"], GATES["vesuvio"]]
FORTUNA_JUNCTION = Vector((72.4, 231.8))
ABBONDANZA = [forum_point(-58.0, FORUM_HALF[1] + PORTICO + 1.0), HOLCONIUS, PLEIADES["thermopolium"],
              GATES["sarno"]]
NOLA = [GATES["nola"], FORTUNA_JUNCTION, Vector((-137.0, 95.6)), Vector((-212.5, 99.0))]
CONSOLARE = [GATES["ercolano"], Vector((-212.5, 99.0))]
MARINA = [GATES["marina"], forum_point(-32.0, -FORUM_HALF[1] - PORTICO - 1.0)]


def east_lines():
    lines = []
    for v, low, high in ((125.0, -40.0, 660.0), (-95.0, -40.0, 660.0), (-190.0, -40.0, 380.0),
                         (345.0, -80.0, 660.0)):
        lines.append(([grid_point(low, v), grid_point(high, v)], "minor"))
    for u in (75.0, 120.0, 165.0, 210.0, 255.0, 300.0, 395.0, 440.0, 485.0, 530.0, 575.0):
        lines.append(([grid_point(u, -300.0), grid_point(u, 520.0)], "minor"))
    lines.append(([GATES["nocera"], grid_point(349.0, 520.0)], "main"))
    return lines


def west_lines():
    lines = []
    for b, low, high in ((0.0, FORUM_HALF[0] + 4.0, 470.0), (-44.0, 60.0, 470.0), (44.0, 60.0, 470.0),
                         (88.0, 60.0, 470.0), (-88.0, 60.0, 470.0), (132.0, 60.0, 470.0)):
        lines.append(([forum_point(low, b), forum_point(high, b)], "minor"))
    for a, low, high in ((205.0, -170.0, 220.0), (320.0, -170.0, 220.0), (395.0, -170.0, 220.0),
                         (30.0, FORUM_HALF[1] + PORTICO, 230.0), (-8.0, 62.0, 230.0),
                         (-95.0, -60.0, 60.0)):
        lines.append(([forum_point(a, low), forum_point(a, high)], "minor"))
    for b, low, high in ((95.0, -110.0, 130.0), (140.0, -110.0, 130.0), (180.0, -110.0, 130.0),
                         (60.0, -110.0, -64.0), (-50.0, -150.0, -82.0)):
        lines.append(([forum_point(low, b), forum_point(high, b)], "minor"))
    return lines


def streets():
    lines = [(ABBONDANZA, "main"), (STABIANA, "main"), (NOLA, "main"), (CONSOLARE, "main"), (MARINA, "main")]
    return lines + east_lines() + west_lines()


ROADS_OUT = {
    "marina": [GATES["marina"], Vector((-260.0, -125.0)), Vector((-420.0, -190.0)), Vector((-640.0, -260.0)),
               Vector((-900.0, -330.0)), Vector((-1150.0, -390.0))],
    "ercolano": [GATES["ercolano"], Vector((-430.0, 330.0)), Vector((-560.0, 460.0)), Vector((-780.0, 650.0)),
                 Vector((-1100.0, 930.0)), Vector((-1500.0, 1300.0))],
    "vesuvio": [GATES["vesuvio"], Vector((-160.0, 560.0)), Vector((-260.0, 800.0)), Vector((-420.0, 1150.0))],
    "nola": [GATES["nola"], Vector((520.0, 600.0)), Vector((640.0, 820.0)), Vector((820.0, 1150.0))],
    "sarno": [GATES["sarno"], Vector((880.0, 450.0)), Vector((1100.0, 560.0)), Vector((1500.0, 760.0))],
    "nocera": [GATES["nocera"], Vector((760.0, -60.0)), Vector((900.0, -150.0)), Vector((1150.0, -300.0)),
               Vector((1600.0, -560.0))],
    "stabia": [GATES["stabia"], Vector((420.0, -230.0)), Vector((470.0, -420.0)), Vector((520.0, -700.0)),
               Vector((560.0, -1100.0)), Vector((600.0, -1700.0))],
}


def forum_rect(a0, a1, b0, b1):
    return [forum_point(a0, b0), forum_point(a1, b0), forum_point(a1, b1), forum_point(a0, b1)]


def grid_rect(u0, u1, v0, v1):
    return [grid_point(u0, v0), grid_point(u1, v0), grid_point(u1, v1), grid_point(u0, v1)]


def rect_around(centre, along, half_long, half_short):
    along = Vector(along).normalized()
    across = Vector((-along.y, along.x))
    centre = Vector(centre[:2])
    return [centre - along * half_long - across * half_short, centre + along * half_long - across * half_short,
            centre + along * half_long + across * half_short, centre - along * half_long + across * half_short]


def ellipse_polygon(centre, along, half_long, half_short, steps=28):
    along = Vector(along).normalized()
    across = Vector((-along.y, along.x))
    return [Vector(centre[:2]) + along * half_long * math.cos(2 * math.pi * k / steps)
            + across * half_short * math.sin(2 * math.pi * k / steps) for k in range(steps)]


VETTII = (281.0, 66.0)
VETTII_SIZE = (44.0, 34.0)
VENUS = (-94.0, -110.0)
THERMOPOLIUM_U = 200.0


def sites():
    va, vb = VETTII
    venus_a, venus_b = VENUS
    return {
        "forum": forum_rect(-FORUM_HALF[0] - 4.0, FORUM_HALF[0] + 4.0, -FORUM_HALF[1] - PORTICO - 0.6,
                            FORUM_HALF[1] + PORTICO + 0.6),
        "forum_east": forum_rect(-62.0, 62.0, FORUM_HALF[1] + PORTICO + 0.6, 62.0),
        "basilica": forum_rect(-74.0, -46.0, -82.0, -26.0),
        "apollo": forum_rect(-24.0, 32.0, -60.0, -26.0),
        "municipal": forum_rect(-98.0, -75.0, -26.0, 26.0),
        "venus": forum_rect(venus_a - 30.0, venus_a + 30.0, venus_b - 30.0, venus_b + 26.0),
        "forum_baths": forum_rect(92.0, 132.0, -48.0, -6.0),
        "vettii": forum_rect(va - VETTII_SIZE[0] / 2, va + VETTII_SIZE[0] / 2, vb - VETTII_SIZE[1] / 2,
                             vb + VETTII_SIZE[1] / 2),
        "stabian_baths": rect_around(PLEIADES["thermes-de-stabies"], GV, 40.0, 30.0),
        "central_baths": rect_around(PLEIADES["thermes-centraux"], GV, 30.0, 28.0),
        "theatre": ellipse_polygon(PLEIADES["grand-theatre"], GU, 36.0, 36.0),
        "odeon": rect_around(PLEIADES["grand-theatre"] + GU * 34.0 + GV * 48.0, GU, 13.0, 15.0),
        "quadriporticus": rect_around(PLEIADES["grand-theatre"] - GV * 70.0 + GU * 8.0, GU, 34.0, 30.0),
        "triangular_forum": rect_around(PLEIADES["forum-triangulaire"] - GV * 10.0 - GU * 12.0, GV, 48.0, 22.0),
        "palaestra": rect_around(PLEIADES["grande-palestre"], GU, 70.5, 53.5),
        "amphitheatre": ellipse_polygon(PLEIADES["amphitheatre"], GV, 68.0, 53.0),
        "marina_gate": rect_around(GATES["marina"], (MARINA[1] - MARINA[0]).normalized(), 24.0, 14.0),
    }

import math

from mathutils import Vector

from .terrain import GeoFrame, point_in_polygon

ORIGIN = (31.2014, 29.9098)
FRAME = GeoFrame(*ORIGIN)
PHAROS_GEO = (31.214039, 29.885368)
GRID_BEARING = math.radians(68.0)
D = Vector((math.sin(GRID_BEARING), math.cos(GRID_BEARING)))
N = Vector((-D.y, D.x))
C0 = Vector((-600.0, -360.0))
BLOCK_T = 300.0
BLOCK_N = 280.0
CITY_T = (-3000.0, 2700.0)
CITY_N = (-1450.0, 1400.0)
ROYAL_T = (150.0, 2100.0)
ROYAL_N = 230.0
QUAY_TOP = 1.6
HEPTASTADION_TOP = 2.4
HEPTASTADION_WIDTH = 22.0


def local(latitude, longitude):
    x, y = FRAME.to_local(latitude, longitude)
    return Vector((x, y))


PHAROS = local(*PHAROS_GEO)
HEPTASTADION = (Vector((-2010.0, -150.0)), Vector((-2420.0, 1090.0)))
HEPTASTADION_BRIDGES = (0.36, 0.7)


def grid_point(t, n):
    return C0 + D * t + N * n


def grid_coords(point):
    offset = Vector((point[0], point[1])) - C0
    return offset.dot(D), offset.dot(N)


def lake_n(t):
    return -1600.0 - 70.0 * math.sin(t / 900.0 + 0.6) - 0.00012 * max(t - 2600.0, 0.0) ** 2


MAINLAND_SEA = [
    (-40000.0, -15500.0), (-26000.0, -10100.0), (-14000.0, -5200.0), (-11000.0, -4100.0), (-8600.0, -3200.0), (-7000.0, -2600.0), (-5800.0, -2120.0),
    (-4800.0, -1700.0), (-3900.0, -1300.0), (-3350.0, -1040.0), (-2900.0, -760.0), (-2540.0, -470.0),
    (-2260.0, -250.0), (-2090.0, -160.0), (-1930.0, -105.0), (-1720.0, -45.0), (-1480.0, 0.0), (-1340.0, 30.0),
    (-1300.0, 95.0), (-1255.0, 140.0), (-1190.0, 135.0), (-1150.0, 70.0), (-1010.0, 62.0), (-860.0, 66.0),
    (-700.0, 78.0), (-560.0, 105.0), (-430.0, 160.0), (-320.0, 240.0), (-240.0, 360.0), (-190.0, 500.0),
    (-150.0, 620.0), (-120.0, 720.0), (-95.0, 860.0), (-65.0, 1000.0), (-30.0, 1110.0), (25.0, 1180.0),
    (95.0, 1150.0), (160.0, 1030.0), (205.0, 890.0), (260.0, 790.0), (420.0, 740.0), (800.0, 790.0),
    (1300.0, 940.0), (2000.0, 1190.0), (2800.0, 1490.0), (3800.0, 1860.0), (5000.0, 2310.0), (7000.0, 3020.0),
    (10000.0, 4060.0), (14000.0, 5500.0), (26000.0, 9800.0),
    (40000.0, 14800.0),
]

PHAROS_ISLAND = [
    (-5000.0, -420.0), (-4650.0, -250.0), (-4200.0, 30.0), (-3700.0, 380.0), (-3200.0, 720.0), (-2850.0, 960.0),
    (-2600.0, 1150.0), (-2480.0, 1265.0), (-2430.0, 1330.0), (-2390.0, 1300.0), (-2365.0, 1210.0),
    (-2385.0, 1120.0), (-2460.0, 1075.0), (-2700.0, 905.0), (-2820.0, 820.0), (-3200.0, 480.0), (-3700.0, 120.0),
    (-4200.0, -200.0), (-4600.0, -440.0), (-4850.0, -520.0),
]

ANTIRHODOS = [
    (-1150.0, 225.0), (-1085.0, 215.0), (-1020.0, 285.0), (-955.0, 370.0), (-905.0, 440.0), (-925.0, 482.0),
    (-975.0, 462.0), (-1040.0, 395.0), (-1110.0, 320.0), (-1165.0, 265.0),
]

REEFS = [
    [(20.0, 1215.0), (-160.0, 1260.0), (-420.0, 1300.0), (-700.0, 1335.0), (-980.0, 1360.0), (-1180.0, 1372.0)],
    [(-2480.0, 1470.0), (-2620.0, 1400.0), (-2860.0, 1180.0), (-3150.0, 960.0), (-3500.0, 700.0),
     (-3900.0, 420.0), (-4400.0, 90.0)],
    [(-5050.0, -520.0), (-5250.0, -720.0), (-5420.0, -980.0)],
    [(160.0, 1150.0), (300.0, 1120.0), (480.0, 1060.0)],
]


def pharos_islet(radius=92.0):
    return [(PHAROS.x + radius * math.cos(math.radians(22.5 + 45 * k)),
             PHAROS.y + radius * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]


def lake_shore():
    points = []
    for k in range(0, 161):
        t = -40000.0 + k * 500.0
        p = grid_point(t, lake_n(t))
        points.append((p.x, p.y))
    return points


def mainland():
    shore = lake_shore()
    return MAINLAND_SEA + list(reversed(shore))


def far_shore():
    points = []
    for k in range(0, 161):
        t = -40000.0 + k * 500.0
        n = lake_n(t) - 5200.0 - 1400.0 * math.sin(t / 3900.0 + 1.1) - 500.0 * math.sin(t / 1300.0)
        p = grid_point(t, n)
        points.append((p.x, p.y))
    return points + [(points[-1][0] + 20000.0, points[-1][1] - 60000.0), (points[0][0] - 20000.0, points[0][1] - 60000.0)]


KIBOTOS = dict(t=-1900.0, n=520.0, width=230.0, depth=200.0)
CANAL_T = -1880.0
CANAL_WIDTH = 24.0


def kibotos_polygon():
    k = KIBOTOS
    corners = [(-k["width"] / 2, -k["depth"] / 2), (k["width"] / 2, -k["depth"] / 2), (k["width"] / 2, 400.0),
               (-k["width"] / 2, 400.0)]
    return [tuple(grid_point(k["t"] + a, k["n"] + b)) for a, b in corners]


def canal_polygon():
    k = KIBOTOS
    half = CANAL_WIDTH / 2
    top = k["n"] - k["depth"] / 2 + 5.0
    bottom = lake_n(CANAL_T) - 60.0
    return [tuple(grid_point(CANAL_T + a, b)) for a, b in ((-half, bottom), (half, bottom), (half, top), (-half, top))]


QUAY_RANGE = (11, 36)


def lake_port_line():
    site = SITES["lake_port"]
    points = []
    for k in range(13):
        t = site["t"] + site["width"] / 2 - site["width"] * k / 12
        p = grid_point(t, lake_n(t))
        points.append((p.x, p.y))
    return points


def quay_lines():
    lines = [MAINLAND_SEA[QUAY_RANGE[0]:QUAY_RANGE[1]], ANTIRHODOS + ANTIRHODOS[:1], lake_port_line()]
    for polygon in water_cuts():
        lines.append(list(polygon) + [polygon[0]])
    return lines


def land_polygons():
    return [mainland(), far_shore(), PHAROS_ISLAND, ANTIRHODOS, pharos_islet()]


def water_cuts():
    return [kibotos_polygon(), canal_polygon()]


def is_land(x, y):
    if any(point_in_polygon(x, y, polygon) for polygon in water_cuts()):
        return False
    return any(point_in_polygon(x, y, polygon) for polygon in land_polygons())


SITES = {
    "caesareum": dict(t=-10.0, n=325.0, width=150.0, depth=120.0),
    "theatre": dict(t=330.0, n=320.0, width=110.0, depth=90.0),
    "poseidion": dict(t=-455.0, n=625.0, width=60.0, depth=60.0),
    "neoria": dict(t=-1080.0, n=660.0, width=210.0, depth=110.0),
    "gymnasium": dict(t=450.0, n=-140.0, width=280.0, depth=250.0),
    "paneion": dict(t=-108.0, n=-393.0, width=150.0, depth=150.0),
    "serapeum": dict(t=-1270.0, n=-1250.0, width=230.0, depth=190.0),
    "lake_port": dict(t=-600.0, n=-1500.0, width=500.0, depth=90.0),
}


def in_site(x, y, pad=0.0):
    t, n = grid_coords((x, y))
    for name, s in SITES.items():
        if abs(t - s["t"]) <= s["width"] / 2 + pad and abs(n - s["n"]) <= s["depth"] / 2 + pad:
            return name
    return None


def in_royal(t, n):
    return ROYAL_T[0] <= t <= ROYAL_T[1] and n >= ROYAL_N


def city_wall():
    t0, t1 = CITY_T
    points = []
    for k in range(0, 24):
        t = t0 + (t1 - t0) * k / 23
        points.append(grid_point(t, lake_n(t) + 140.0))
    east = [grid_point(t1, lake_n(t1) + 140.0 + (CITY_N[1] - lake_n(t1) - 140.0) * k / 8) for k in range(1, 9)]
    west = [grid_point(t0, CITY_N[1] - (CITY_N[1] - lake_n(t0) - 140.0) * k / 8) for k in range(0, 8)]
    return west + points + east

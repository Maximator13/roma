import math

import numpy as np
from mathutils import Vector

ORIGIN_OSGB = (378978.0, 568800.0)
ORIGIN_GEO = (55.0131, -2.3311)
EA_BOX = (-3000.0, -1800.0, 2000.0, 2200.0)
CORE = (-1150.0, -560.0, 2000.0, 1000.0, 4.0, (2048, 1024))
CORE_WEST = (-1150.0, -560.0, 1000.0, 1000.0, 4.0, (2048, 2048))
CORE_EAST = (-150.0, -560.0, 1000.0, 1000.0, 4.0, (2048, 2048))
NEAR = (-3000.0, -1800.0, 5000.0, 4000.0, 12.0, (2048, 1638))
MID = (-12000.0, -12000.0, 24000.0, 24000.0, 100.0, (2048, 2048))
FAR = (-45000.0, -45000.0, 90000.0, 90000.0, 600.0, (1024, 1024))

FORT = dict(cx=0.5, cy=-1.0, angle=math.radians(12.3), half_u=91.5, half_v=52.0, radius=9.0)
STREET_U = 20.0

WALL_GUIDE = [
    (-3000, -1054), (-2845, -1051), (-2713, -1000), (-2563, -929), (-2384, -894), (-2306, -885), (-2026, -833),
    (-1844, -800), (-1797, -786), (-1690, -568), (-1564, -394), (-1502, -359), (-1435, -326), (-1354, -286),
    (-1245, -262), (-1131, -237), (-1059, -238), (-916, -182), (-854, -140), (-738, -120), (-639, -95),
    (-511, -75), (-401, -53), (-346, -19), (-270, 1), (-195, 19),
]
WALL_EAST = [
    (150, 92), (205, 145), (225, 230), (260, 310), (330, 370), (420, 400), (500, 440), (577, 467), (700, 540),
    (800, 600), (880, 720), (930, 850), (950, 1000), (965, 1150), (1017, 1250), (1198, 1315), (1520, 1400),
    (1872, 1485), (2016, 1500), (2300, 1640),
]
VALLUM = [
    (-3000, -1670), (-2500, -1545), (-1990, -1410), (-1890, -1300), (-1810, -1190), (-1600, -1060), (-1400, -950),
    (-1150, -800), (-915, -660), (-500, -420), (0, -170), (430, 50), (700, 190), (900, 270), (1060, 360),
    (1250, 500), (1490, 720), (1800, 1010), (2000, 1200), (2200, 1390),
]
MILECASTLE_37 = (-419.0, -85.0)
TURRET_37A = (-928.0, -190.0)
TURRET_37B = (-1398.0, -330.0)
ROMAN_MILE = 1480.0
LAKES = {
    "crag_lough": dict(seed=(-2280.0, -800.0), box=(-2700.0, -980.0, -1850.0, -620.0), north=True),
    "greenlee_lough": dict(seed=(-1850.0, 900.0), box=(-2600.0, 450.0, -1150.0, 1400.0), north=True),
    "broomlee_lough": dict(seed=(130.0, 960.0), box=(-350.0, 650.0, 620.0, 1260.0), north=True),
    "grindon_lough": dict(seed=(1470.0, -1100.0), box=(950.0, -1400.0, 2000.0, -800.0)),
}


def fort_point(u, v):
    f = FORT
    c, s = math.cos(f["angle"]), math.sin(f["angle"])
    return Vector((f["cx"] + u * c - v * s, f["cy"] + u * s + v * c))


def fort_local(x, y):
    f = FORT
    c, s = math.cos(f["angle"]), math.sin(f["angle"])
    dx = np.asarray(x, dtype=np.float64) - f["cx"]
    dy = np.asarray(y, dtype=np.float64) - f["cy"]
    return dx * c + dy * s, -dx * s + dy * c


def fort_ring(inset=0.0, step=1.5):
    f = FORT
    hu, hv, r = f["half_u"] - inset, f["half_v"] - inset, max(f["radius"] - inset, 1.0)
    points = []
    corners = [(hu - r, hv - r, 0.0), (-hu + r, hv - r, 90.0), (-hu + r, -hv + r, 180.0), (hu - r, -hv + r, 270.0)]
    for cu, cv, start in corners:
        for k in range(7):
            a = math.radians(start + 15.0 * k)
            points.append(tuple(fort_point(cu + r * math.cos(a), cv + r * math.sin(a))))
    return points


def resample_line(points, spacing):
    result = [tuple(points[0])]
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        length = math.hypot(bx - ax, by - ay)
        steps = max(int(math.ceil(length / spacing)), 1)
        for k in range(1, steps + 1):
            t = k / steps
            result.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return result


def chaikin(points, rounds=2):
    for _ in range(rounds):
        refined = [points[0]]
        for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
            refined.append((0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by))
            refined.append((0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by))
        refined.append(points[-1])
        points = refined
    return points


def polyline_distance(points, xs, ys):
    xs = np.asarray(xs, dtype=np.float64)
    ys = np.asarray(ys, dtype=np.float64)
    best = np.full(xs.shape, np.inf)
    station = np.zeros(xs.shape)
    side = np.zeros(xs.shape)
    total = 0.0
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / (length * length), 0.0, 1.0)
        px, py = ax + t * dx, ay + t * dy
        distance = np.hypot(xs - px, ys - py)
        closer = distance < best
        best = np.where(closer, distance, best)
        station = np.where(closer, total + t * length, station)
        cross = dx * (ys - ay) - dy * (xs - ax)
        side = np.where(closer, np.sign(cross), side)
        total += length
    return best, station, side


def stations(points):
    result = [0.0]
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        result.append(result[-1] + math.hypot(bx - ax, by - ay))
    return result


def along(points, s):
    total = stations(points)
    s = min(max(s, 0.0), total[-1])
    for index in range(len(points) - 1):
        if total[index + 1] >= s:
            a = Vector(points[index])
            b = Vector(points[index + 1])
            length = max(total[index + 1] - total[index], 1e-9)
            direction = (b - a).normalized()
            return a + direction * (s - total[index]), direction
    a = Vector(points[-2])
    b = Vector(points[-1])
    return b, (b - a).normalized()


def nearest_station(points, x, y):
    _, station, _ = polyline_distance(points, np.array([x]), np.array([y]))
    return float(station[0])


VALLUM_SMOOTH = chaikin([tuple(map(float, p)) for p in VALLUM], 3)

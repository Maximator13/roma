import math

import numpy as np

KHUFU = dict(key="khufu", x=328.0, y=343.0, half_x=115.15, half_y=115.15, height=146.6, top=3.2, casing="casing")
KHAFRE = dict(key="khafre", x=0.0, y=0.0, half_x=107.65, half_y=107.65, height=143.5, top=0.0, casing="casing",
              granite=1.4)
MENKAURE = dict(key="menkaure", x=-241.0, y=-399.0, half_x=51.1, half_y=52.3, height=65.0, top=0.0,
                casing="casing", granite=15.5)
QUEENS_EAST = [
    dict(key="g1a", x=533.0, y=300.0, half_x=24.75, half_y=24.75, height=30.25, state="ruined", seed=1),
    dict(key="g1b", x=538.0, y=245.0, half_x=24.75, half_y=24.75, height=30.0, state="ruined", seed=2),
    dict(key="g1c", x=541.0, y=192.0, half_x=23.12, half_y=23.12, height=29.6, state="ruined", seed=3),
]
QUEENS_SOUTH = [
    dict(key="g3a", x=-186.0, y=-519.0, half_x=22.0, half_y=22.0, height=28.4, state="cased", seed=4, granite=4.0),
    dict(key="g3b", x=-236.0, y=-519.0, half_x=15.5, half_y=15.5, height=21.0, state="stepped", seed=5),
    dict(key="g3c", x=-281.0, y=-519.0, half_x=15.5, half_y=15.5, height=21.0, state="stepped", seed=6),
]
GREAT = [KHUFU, KHAFRE, MENKAURE]
ALL_PYRAMIDS = GREAT + QUEENS_EAST + QUEENS_SOUTH
SPHINX = dict(x=656.0, y=-89.0, floor=20.0, rim=27.6)
PIT = dict(x0=SPHINX["x"] - 47.0, x1=SPHINX["x"] + 54.0, y0=SPHINX["y"] - 25.0, y1=SPHINX["y"] + 25.0)
TERRACE = dict(x0=SPHINX["x"] + 54.0, x1=SPHINX["x"] + 128.0, y0=SPHINX["y"] - 46.0, y1=SPHINX["y"] + 46.0,
               top=SPHINX["rim"] - 0.1)
STAIR = dict(width=12.6, lower=13, upper=30, rise=0.176, tread=0.4, landing=6.0)
KHUFU_TEMPLE = dict(x0=443.5, x1=495.0, y0=316.0, y1=370.0)
KHAFRE_TEMPLE = dict(x0=110.0, x1=166.0, y0=-28.0, y1=28.0)
MENKAURE_TEMPLE = dict(x0=-188.0, x1=-142.0, y0=-424.0, y1=-374.0)
MENKAURE_VALLEY = dict(x0=420.0, x1=462.0, y0=-492.0, y1=-446.0)
KHAFRE_VALLEY = dict(x0=690.0, x1=736.0, y0=-178.0, y1=-134.0)
CAUSEWAYS = {
    "khafre": [(166.0, -10.0), (690.0, -142.0)],
    "khufu": [(495.0, 356.0), (820.0, 400.0), (1120.0, 446.0)],
    "menkaure": [(-142.0, -399.0), (150.0, -430.0), (420.0, -468.0)],
}
KHENTKAWES = dict(x=378.0, y=-377.0, half=22.5, height=17.5)
CROW_WALL = dict(x0=640.0, x1=842.0, y=-548.0, thickness=10.0, height=9.0, gate=(735.0, 7.0))
ISIS = dict(x=574.0, y=192.0)
WEST_FIELD = dict(x0=-150.0, x1=188.0, y0=246.0, y1=566.0)
EAST_FIELD = dict(x0=598.0, x1=792.0, y0=140.0, y1=330.0)
VILLAGE = dict(x=1120.0, y=-110.0, radius=210.0)
EDGE = [(14000.0, -60000.0), (6000.0, -12000.0), (1500.0, -3000.0), (960.0, -900.0), (900.0, -560.0),
        (800.0, -300.0), (775.0, -100.0), (765.0, 300.0), (640.0, 600.0), (420.0, 800.0), (40.0, 1100.0),
        (-600.0, 1500.0), (-2000.0, 3000.0), (-4500.0, 12000.0), (-6000.0, 60000.0)]
NILE = [(5600.0, -60000.0), (6400.0, -20000.0), (7300.0, -12000.0), (7700.0, -6000.0), (7150.0, -2400.0),
        (7350.0, 600.0), (7900.0, 3400.0), (8300.0, 7000.0), (8100.0, 12000.0), (9000.0, 30000.0),
        (12000.0, 60000.0)]
NILE_HALF = 330.0
ISLAND = dict(x=7420.0, y=-900.0, a=130.0, b=780.0, angle=0.05)
CANALS = [
    [(1450.0, -3200.0), (1400.0, -1500.0), (1460.0, -600.0), (1420.0, 200.0), (1300.0, 900.0), (1150.0, 1600.0),
     (900.0, 2600.0)],
    [(1430.0, -820.0), (2300.0, -900.0), (3600.0, -760.0), (5200.0, -880.0), (6900.0, -820.0)],
    [(1350.0, 700.0), (2600.0, 900.0), (4200.0, 760.0), (6000.0, 900.0), (7100.0, 1000.0)],
]
CANAL_HALF = [7.0, 5.5, 5.0]
BASINS = [(860.0, 1060.0, 520.0, 640.0), (1080.0, 1300.0, 560.0, 700.0), (900.0, 1080.0, 700.0, 820.0),
          (1180.0, 1350.0, 210.0, 350.0), (1500.0, 1660.0, -520.0, -360.0), (1500.0, 1650.0, 240.0, 420.0)]
TRACKS = [
    [(1000.0, -60.0), (880.0, -40.0), (780.0, -80.0), (712.0, -89.0)],
    [(990.0, -150.0), (860.0, -250.0), (730.0, -320.0), (560.0, -330.0), (380.0, -300.0), (300.0, -200.0)],
    [(1080.0, 40.0), (980.0, 180.0), (860.0, 300.0), (760.0, 360.0), (640.0, 380.0), (520.0, 385.0)],
    [(520.0, 385.0), (450.0, 480.0), (330.0, 488.0), (200.0, 470.0), (190.0, 300.0), (150.0, 140.0)],
    [(150.0, 140.0), (20.0, 135.0), (-150.0, 120.0), (-250.0, -40.0), (-250.0, -300.0)],
]
ABUSIR = [(7020.0, -9120.0, 39.0, 50.0), (7130.0, -9300.0, 33.0, 40.0), (6900.0, -9420.0, 37.0, 45.0)]
SAQQARA = dict(x=8320.0, y=-11650.0, base_x=60.0, base_y=54.0, height=62.0, steps=6)
HAMLETS = [dict(x=1600.0, y=-200.0, radius=75.0), dict(x=980.0, y=1150.0, radius=70.0)]
LEVELS = {"flood": 17.6, "canal": 16.9, "basin": 17.3, "nile": 16.2, "water": 17.95}


def stair_height(x):
    st = STAIR
    x0 = PIT["x1"]
    floor = SPHINX["floor"] + 0.12
    lower = x0 + st["lower"] * st["tread"]
    middle = floor + st["lower"] * st["rise"]
    upper = lower + st["landing"]
    end = upper + st["upper"] * st["tread"]
    return np.interp(x, [x0, lower, upper, end], [floor, middle, middle, TERRACE["top"]])


def stair_fill(x, y):
    half = STAIR["width"] / 2 + 1.6
    dy = np.maximum(np.abs(np.asarray(y) - SPHINX["y"]) - half, 0.0)
    return np.minimum(TERRACE["top"] - 0.22, stair_height(x) + 1.0 + dy * 0.55)


STAIR_END = PIT["x1"] + STAIR["tread"] * (STAIR["lower"] + STAIR["upper"]) + STAIR["landing"]
FILL_REACH = STAIR["width"] / 2 + 21.0


def edge_x(y):
    ys = np.array([p[1] for p in EDGE])
    xs = np.array([p[0] for p in EDGE])
    order = np.argsort(ys)
    return np.interp(y, ys[order], xs[order])


def polyline_distance(points, gx, gy):
    distance = np.full(np.shape(gx), np.inf)
    station = np.zeros(np.shape(gx))
    run = 0.0
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        t = np.clip(((gx - x0) * dx + (gy - y0) * dy) / max(length * length, 1e-9), 0.0, 1.0)
        d = np.hypot(gx - (x0 + t * dx), gy - (y0 + t * dy))
        closer = d < distance
        distance = np.where(closer, d, distance)
        station = np.where(closer, run + t * length, station)
        run += length
    return distance, station


def box_distance(gx, gy, x0, x1, y0, y1):
    dx = np.maximum(np.maximum(x0 - gx, gx - x1), 0.0)
    dy = np.maximum(np.maximum(y0 - gy, gy - y1), 0.0)
    inside = (gx >= x0) & (gx <= x1) & (gy >= y0) & (gy <= y1)
    return np.where(inside, -np.minimum(np.minimum(gx - x0, x1 - gx), np.minimum(gy - y0, y1 - gy)),
                    np.hypot(dx, dy))


def resample_line(points, spacing):
    result = []
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        steps = max(int(math.ceil(length / spacing)), 1)
        for k in range(steps):
            t = k / steps
            result.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    result.append(points[-1])
    return result

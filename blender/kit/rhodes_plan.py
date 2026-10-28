import math

import numpy as np
from mathutils import Vector

from .constantinople_terrain import smoothstep
from .rhodes_terrain import box_weight, flatten
from .terrain import point_in_polygon, polyline_distance

QUAY_TOP = 1.6
BLOCK_X = 100.0
BLOCK_Y = 50.0
GRID_X0 = 50.0
GRID_Y0 = 0.0
STREET = 6.0
AVENUE = 15.0
AVENUE_Y = -450.0
AVENUE_X = 250.0
SOUTH_WALL_Y = -1750.0

SANCTUARY = dict(centre=(-1166.0, -616.0), half=(60.0, 76.0), level=74.0)
TEMPLE = Vector((-1160.0, -652.0))
TEMPLE_SIZE = (31.0, 15.6)
COLOSSUS = Vector((-1190.0, -586.0))
COLOSSUS_FALL = math.radians(8.0)
ATHENA = dict(centre=(-1146.0, -372.0), half=(38.0, 27.0), level=76.5)
STADIUM_AXIS_X = -1025.0
STADIUM_Y = (-805.0, -605.0)
STADIUM_HALF = 15.0
STADIUM_LEVEL = 52.0
STADIUM_ROWS = 14
STADIUM_ROW = (0.82, 0.44)
ODEON = dict(centre=(-1062.0, -532.0), radius=14.0, orchestra=5.0, level=58.6)
AGORA = dict(centre=(700.0, -470.0), half=(80.0, 55.0))
GYMNASIUM = dict(centre=(-300.0, -900.0), half=(70.0, 55.0))

MANDRAKI = [(150.0, 900.0), (150.0, 760.0), (170.0, 640.0), (168.0, 540.0), (196.0, 410.0), (232.0, 300.0),
            (266.0, 222.0), (300.0, 172.0), (348.0, 142.0), (388.0, 132.0), (388.0, 380.0), (388.0, 600.0),
            (420.0, 900.0)]
INNER_PORT = [(538.0, 160.0), (532.0, 20.0), (526.0, -120.0), (532.0, -252.0), (600.0, -262.0), (668.0, -256.0),
              (700.0, -196.0), (734.0, -60.0), (748.0, 60.0), (748.0, 160.0)]
GREAT_PORT = [(874.0, 260.0), (874.0, 172.0), (877.0, -57.0), (889.0, -303.0), (906.0, -444.0), (950.0, -530.0),
              (1056.0, -560.0), (1109.0, -546.0), (1140.0, -470.0), (1168.0, -373.0), (1186.0, -303.0),
              (1200.0, -206.0), (1249.0, -168.0), (1284.0, -130.0), (1366.0, -122.0), (1366.0, 260.0)]
HARBOURS = {"mandraki": MANDRAKI, "inner": INNER_PORT, "great": GREAT_PORT}

MOLES = {
    "mandraki_est": dict(points=[(402.0, 70.0), (402.0, 380.0), (398.0, 598.0)], width=24.0),
    "mandraki_nord": dict(points=[(150.0, 770.0), (232.0, 790.0), (300.0, 802.0)], width=18.0),
    "grand_port_est": dict(points=[(1388.0, -150.0), (1388.0, 60.0), (1384.0, 214.0)], width=26.0),
    "port_interieur": dict(points=[(810.0, 160.0), (812.0, 238.0)], width=60.0),
}
MOLE_CUTS = [
    [(380.0, 30.0), (560.0, 30.0), (560.0, 100.0), (416.0, 100.0), (414.0, 612.0), (384.0, 612.0)],
    [(130.0, 758.0), (312.0, 784.0), (312.0, 818.0), (130.0, 790.0)],
    [(1360.0, -150.0), (1403.0, -150.0), (1400.0, 228.0), (1360.0, 228.0)],
]
SEA_FILLS = [[(1430.0, -2300.0), (1800.0, -2300.0), (1800.0, -820.0), (1430.0, -820.0)]]

SITES = {
    "sanctuary": dict(centre=SANCTUARY["centre"], half=(SANCTUARY["half"][0] + 6.0, SANCTUARY["half"][1] + 6.0)),
    "athena": dict(centre=ATHENA["centre"], half=(ATHENA["half"][0] + 6.0, ATHENA["half"][1] + 6.0)),
    "stadium": dict(centre=(STADIUM_AXIS_X, -700.0), half=(30.0, 125.0)),
    "odeon": dict(centre=ODEON["centre"], half=(30.0, 30.0)),
    "agora": AGORA,
    "gymnasium": GYMNASIUM,
}


def is_harbour_water(x, y):
    return any(point_in_polygon(x, y, polygon) for polygon in HARBOURS.values())


def in_site(x, y, pad=0.0):
    for name, site in SITES.items():
        cx, cy = site["centre"]
        hx, hy = site["half"]
        if abs(x - cx) < hx + pad and abs(y - cy) < hy + pad:
            return name
    return None


def street_lines_x():
    return [GRID_X0 + k * BLOCK_X for k in range(-25, 25)]


def street_lines_y():
    return [GRID_Y0 + k * BLOCK_Y for k in range(-45, 30)]


def street_width_x(x):
    return AVENUE if abs(x - AVENUE_X) < 1.0 else STREET


def street_width_y(y):
    return AVENUE if abs(y - AVENUE_Y) < 1.0 else STREET


def west_wall_x(y):
    return np.interp(y, [-1800.0, -1400.0, -1000.0, -600.0, -300.0, 0.0, 300.0, 600.0],
                     [-1560.0, -1640.0, -1500.0, -1370.0, -1180.0, -880.0, -560.0, -300.0])


def acropolis_zone(x, y):
    return (x < -930.0) & (y > -1000.0) & (y < -280.0)


def city_mask(gx, gy):
    return (gx > west_wall_x(gy)) & (gy > SOUTH_WALL_Y)


def built_mask(gx, gy):
    return city_mask(gx, gy) & ~acropolis_zone(gx, gy)


def street_mask(gx, gy):
    near_x = np.abs(((gx - GRID_X0 + BLOCK_X / 2) % BLOCK_X) - BLOCK_X / 2)
    near_y = np.abs(((gy - GRID_Y0 + BLOCK_Y / 2) % BLOCK_Y) - BLOCK_Y / 2)
    streets = (near_x < STREET / 2 + 0.5) | (near_y < STREET / 2 + 0.5)
    avenues = (np.abs(gx - AVENUE_X) < AVENUE / 2 + 0.5) | (np.abs(gy - AVENUE_Y) < AVENUE / 2 + 0.5)
    return (streets | avenues) & built_mask(gx, gy)


def paved_mask(gx, gy):
    weight = np.zeros(np.shape(gx))
    for site, margin in ((SANCTUARY, 0.5), (ATHENA, 0.5), (AGORA, 0.5), (GYMNASIUM, 0.5)):
        cx, cy = site["centre"]
        hx, hy = site["half"]
        weight = np.maximum(weight, box_weight(gx, gy, cx, cy, hx - 4.0, hy - 4.0, 1.0) * 0.85)
    return weight


def stadium_distance(gx, gy):
    y0, y1 = STADIUM_Y
    along = np.abs(gx - STADIUM_AXIS_X) - STADIUM_HALF
    round_end = np.hypot(gx - STADIUM_AXIS_X, gy - y1) - STADIUM_HALF
    return np.where(gy > y1, round_end, along)


def track_mask(gx, gy):
    y0, y1 = STADIUM_Y
    inside = (stadium_distance(gx, gy) < 0.0) & (gy > y0 - 2.0)
    return inside.astype(np.float64) * 0.9


def harbour_weight(gx, gy):
    distance = np.full(np.shape(gx), np.inf)
    for polygon in HARBOURS.values():
        distance = np.minimum(distance, polyline_distance(list(polygon) + [polygon[0]], gx, gy))
    return smoothstep(1.0 - (distance - 40.0) / 20.0)


def shape_ground(gx, gy, ground):
    return ground


def stadium_shape(gx, gy, heights):
    y0, y1 = STADIUM_Y
    distance = stadium_distance(gx, gy)
    depth, rise = STADIUM_ROW
    seats = STADIUM_LEVEL + np.clip(distance, 0.0, STADIUM_ROWS * depth) * rise / depth
    seats = np.where(distance < 0.0, STADIUM_LEVEL, seats)
    length_weight = smoothstep(1.0 - (y0 - gy) / 12.0) * smoothstep(1.0 - (gy - (y1 + 40.0)) / 10.0)
    weight = smoothstep(1.0 - (distance - STADIUM_ROWS * depth) / 10.0) * length_weight
    return flatten(heights, weight, seats)


def odeon_shape(gx, gy, heights):
    cx, cy = ODEON["centre"]
    radius = np.hypot(gx - cx, gy - cy)
    facing = (gx - cx) < 4.0
    cavea = ODEON["level"] + np.clip(radius - ODEON["orchestra"], 0.0, ODEON["radius"] - ODEON["orchestra"]) * 0.58
    target = np.where(facing, cavea, ODEON["level"])
    weight = smoothstep(1.0 - (radius - ODEON["radius"]) / 8.0)
    return flatten(heights, weight, target)


def shape_after(gx, gy, heights):
    heights = stadium_shape(gx, gy, heights)
    heights = odeon_shape(gx, gy, heights)
    for site in (SANCTUARY, ATHENA):
        cx, cy = site["centre"]
        hx, hy = site["half"]
        heights = flatten(heights, box_weight(gx, gy, cx, cy, hx, hy, 3.0), site["level"])
    for site in (AGORA, GYMNASIUM):
        cx, cy = site["centre"]
        hx, hy = site["half"]
        inside = box_weight(gx, gy, cx, cy, hx, hy, 0.01) > 0.5
        level = float(np.mean(heights[inside])) if inside.any() else 0.0
        heights = flatten(heights, box_weight(gx, gy, cx, cy, hx, hy, 12.0), level)
    return heights


def site_level(name):
    return {"sanctuary": SANCTUARY["level"], "athena": ATHENA["level"]}[name]

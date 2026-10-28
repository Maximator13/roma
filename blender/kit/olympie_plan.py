import math

from mathutils import Vector

from .terrain import GeoFrame

ORIGIN = (37.6378, 21.6300)
FRAME = GeoFrame(*ORIGIN)
ALTIS_LEVEL = 33.0
TERRACE_LEVEL = 36.4
ARENA_LEVEL = 33.2
ALPHEIOS_LEVEL = 23.0

ZEUS = Vector((0.0, 0.0))
HERAION = Vector((-40.0, 118.0))
PHILIPPEION = Vector((-82.0, 96.0))
PRYTANEION = Vector((-88.0, 132.0))
PELOPION = Vector((-22.0, 58.0))
GREAT_ALTAR = Vector((8.0, 88.0))
METROON = Vector((40.0, 114.0))
NYMPHAEUM = Vector((2.0, 152.0))
TREASURY_X = (22.0, 124.0)
TREASURY_FRONT = 141.0
ZANES = [(62.0 + 4.3 * k, 128.5) for k in range(14)]
CRYPT_WEST = 136.0
CRYPT_EAST = 168.0
STADIUM_AXIS_Y = 146.0
ARENA = (168.0, 380.5, STADIUM_AXIS_Y - 16.0, STADIUM_AXIS_Y + 16.0)
ECHO_STOA = (128.0, 10.0, 106.0)
NIKE_PAIONIOS = Vector((44.0, -12.0))
OLIVE_CROWN = Vector((-44.0, 6.0))
ALTIS_WALL = [(-104.0, -52.0), (126.0, -52.0), (126.0, 10.0)]
ALTIS_WALL_WEST = [(-104.0, -52.0), (-104.0, 128.0)]
BOULEUTERION = Vector((-2.0, -86.0))
SOUTH_STOA = (-48.0, 48.0, -122.0)
LEONIDAION = Vector((-96.0, -104.0))
WORKSHOP = Vector((-136.0, -14.0))
PALAESTRA = Vector((-146.0, 60.0))
GYMNASIUM_X = (-180.0, -112.0)
GYMNASIUM_Y = (104.0, 310.0)
KLADEOS_BATHS = Vector((-170.0, -18.0))
NERO_HOUSE = Vector((186.0, 26.0))
KRONOS = Vector((96.0, 290.0))

KLADEOS = [(-232.0, 900.0), (-214.0, 640.0), (-200.0, 420.0), (-206.0, 240.0), (-198.0, 80.0), (-204.0, -60.0),
           (-226.0, -200.0), (-262.0, -330.0), (-300.0, -420.0)]
KLADEOS_LEVELS = [44.0, 39.0, 35.0, 31.6, 29.4, 28.0, 26.2, 24.6, 23.0]
ALPHEIOS = [(-6000.0, -2400.0), (-4200.0, -1700.0), (-2600.0, -1100.0), (-1500.0, -640.0), (-700.0, -470.0),
            (0.0, -440.0), (700.0, -430.0), (1500.0, -200.0), (2600.0, 150.0), (4000.0, 500.0), (5500.0, 950.0),
            (7000.0, 1300.0)]


def meander(points, step=60.0, amplitude=55.0, wavelength=1300.0):
    result = []
    total = sum((Vector(b) - Vector(a)).length for a, b in zip(points[:-1], points[1:]))
    count = int(total / step)
    for index in range(count + 1):
        s = min(index * step, total)
        remaining = s
        for a, b in zip(points[:-1], points[1:]):
            a = Vector(a)
            b = Vector(b)
            length = (b - a).length
            if remaining <= length or b == Vector(points[-1]):
                position = a + (b - a) * min(remaining / length, 1.0)
                direction = (b - a).normalized()
                break
            remaining -= length
        side = Vector((-direction.y, direction.x))
        damp = min(1.0, max(0.0, (abs(position.x) - 500.0) / 900.0))
        offset = amplitude * (0.35 + 0.65 * damp) * (math.sin(2 * math.pi * s / wavelength)
                                                     + 0.4 * math.sin(2 * math.pi * s / (wavelength * 0.37) + 1.3))
        result.append(((position + side * offset).x, (position + side * offset).y))
    return result


ALPHEIOS = meander(ALPHEIOS)


def local(latitude, longitude):
    x, y = FRAME.to_local(latitude, longitude)
    return Vector((x, y))


def heading(direction):
    return math.atan2(direction[1], direction[0]) - math.pi / 2


def polyline_length(points):
    return sum((Vector(b) - Vector(a)).length for a, b in zip(points[:-1], points[1:]))


def along(points, distance):
    remaining = distance
    for a, b in zip(points[:-1], points[1:]):
        a = Vector(a)
        b = Vector(b)
        length = (b - a).length
        if remaining <= length:
            return a + (b - a) * (remaining / max(length, 1e-9)), (b - a).normalized()
        remaining -= length
    a = Vector(points[-2])
    b = Vector(points[-1])
    return b, (b - a).normalized()

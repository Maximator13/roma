import math
import random

from mathutils import Matrix, Vector

from .geometry import MATTE, MeshBuilder, placement
from .life import LEATHER, SKIN, WOOD
from .nimes_figures import POSES, Look, coarse, drape, ellipsoid, person, tube

POSES.update({
    "colisee_fight": [((0.31, 0.16, 1.2), (0.29, 0.42, 1.27)), ((-0.29, 0.18, 1.14), (-0.17, 0.36, 1.12))],
    "colisee_lunge": [((0.3, 0.26, 1.32), (0.27, 0.56, 1.46)), ((-0.3, 0.14, 1.12), (-0.2, 0.34, 1.05))],
    "colisee_trident": [((0.3, 0.14, 1.12), (0.22, 0.38, 1.18)), ((-0.3, 0.12, 1.12), (-0.18, 0.4, 1.2))],
    "colisee_horn": [((0.27, 0.2, 1.36), (0.12, 0.3, 1.56)), ((-0.26, 0.16, 1.2), (-0.1, 0.3, 1.36))],
    "colisee_rope": [((0.27, 0.12, 1.62), (0.14, 0.2, 1.86)), ((-0.27, 0.12, 1.5), (-0.14, 0.2, 1.7))],
    "colisee_rake": [((0.26, 0.16, 1.1), (0.16, 0.36, 1.0)), ((-0.26, 0.16, 1.2), (-0.12, 0.38, 1.25))],
})
BRASS = (0.78, 0.6, 0.32)
STEEL = (0.62, 0.62, 0.6)
LINEN = (0.92, 0.9, 0.84)
SCUTUM = (0.62, 0.2, 0.14)
PURPLE = (0.42, 0.12, 0.2)
TAU = 2 * math.pi


def painted(builder, colour, action):
    first = len(builder.polygons)
    action()
    builder.tint(first, colour)


def bare(seed, skin, hair, arms, stride=0.22, scale=1.0):
    tone = SKIN[skin]
    builder = person(Look(tone, hem=0.86, skin=skin, hair=hair, arms=arms, stride=stride, scale=1.0, seed=seed))
    drape(builder, LINEN, [(0.218, 0.8), (0.207, 0.92), (0.198, 1.02)], 12, folds=(5, 0.05, seed), squash=0.74)
    drape(builder, BRASS, [(0.206, 0.98), (0.21, 1.06), (0.2, 1.13)], 12, folds=(0, 0.0, 0.0), squash=0.72)
    return builder


def manica(builder, side):
    shoulder = Vector((side * 0.182, 0.0, 1.38))
    pose = POSES["colisee_fight"][0 if side > 0 else 1]
    elbow, wrist = Vector(pose[0]), Vector(pose[1])
    for k in range(4):
        a = shoulder.lerp(elbow, k / 4) if k < 2 else elbow.lerp(wrist, (k - 2) / 2)
        b = shoulder.lerp(elbow, (k + 1) / 4) if k < 2 else elbow.lerp(wrist, (k - 1) / 2)
        tube(builder, [a, b], [0.075, 0.07], LINEN if k % 2 else (0.82, 0.78, 0.7), 6)


def greave(builder, side, stride, high=False):
    x = side * 0.087
    y = side * stride
    tube(builder, [(x, y * 0.9, 0.12), (x * 1.03, y * 0.6, 0.5 if not high else 0.62)], [0.06, 0.068], BRASS, 6,
         start_cap=True)
    if high:
        tube(builder, [(x * 1.05, y * 0.5, 0.62), (x * 1.1, y * 0.3, 0.84)], [0.072, 0.08], LINEN, 6)


def helmet(builder, crest, visor=True, brim=True, colour=BRASS):
    ellipsoid(builder, (0.0, 0.0, 1.635), (0.128, 0.142, 0.16), colour, 10, 6)
    if brim:
        drape(builder, colour, [(0.13, 1.55), (0.205, 1.53), (0.2, 1.5)], 12, folds=(0, 0.0, 0.0), squash=1.0)
    if visor:
        painted(builder, (0.18, 0.16, 0.14), lambda: builder.oriented(
            [(-0.07, 0.137, 1.55), (0.07, 0.137, 1.55), (0.07, 0.125, 1.68), (-0.07, 0.125, 1.68)], (0, 1, 0), MATTE))
    if crest == "fish":
        path = [Vector((0.0, -0.16, 1.66)), Vector((0.0, -0.08, 1.83)), Vector((0.0, 0.06, 1.86)),
                Vector((0.0, 0.14, 1.76))]
        tube(builder, path, [0.02, 0.05, 0.05, 0.02], colour, 4, squash=0.35)
    elif crest == "griffin":
        path = [Vector((0.0, -0.14, 1.72)), Vector((0.0, -0.04, 1.85)), Vector((0.0, 0.08, 1.9)),
                Vector((0.0, 0.16, 1.84))]
        tube(builder, path, [0.02, 0.04, 0.04, 0.015], colour, 4, squash=0.4)
        for side in (-1, 1):
            tube(builder, [(side * 0.11, 0.0, 1.72), (side * 0.14, -0.02, 1.98)], [0.02, 0.006], (0.86, 0.82, 0.74), 4)
    elif crest == "smooth":
        tube(builder, [(0.0, -0.15, 1.62), (0.0, -0.02, 1.81), (0.0, 0.13, 1.7)], [0.012, 0.03, 0.012], colour, 4,
             squash=0.3)


def shield(builder, centre, width, height, colour, curve=0.12):
    cx, cy, cz = centre
    rows = []
    for k in range(4):
        z = cz - height / 2 + height * k / 3
        row = []
        for j in range(5):
            u = -1 + 2 * j / 4
            row.append((cx + u * width / 2, cy - curve * u * u, z))
        rows.append(row)
    painted(builder, colour, lambda: builder.surface(rows, MATTE, facing=(0, 1, 0)))
    back = [[(x, y - 0.03, z) for x, y, z in row] for row in rows]
    painted(builder, tuple(c * 0.6 for c in colour), lambda: builder.surface(back, MATTE, facing=(0, -1, 0)))
    ellipsoid(builder, (cx, cy + 0.03, cz), (0.08, 0.04, 0.08), BRASS, 6, 3)


def blade(builder, wrist, length, curved=False):
    wrist = Vector(wrist)
    tube(builder, [wrist + Vector((0.0, -0.03, 0.0)), wrist + Vector((0.0, 0.06, 0.0))], [0.025, 0.025], BRASS, 4)
    if curved:
        points = [wrist + Vector((0.0, 0.06, 0.0)), wrist + Vector((0.0, 0.25, 0.04)), wrist + Vector((0.0, 0.4, -0.05)),
                  wrist + Vector((0.0, length, -0.14))]
    else:
        points = [wrist + Vector((0.0, 0.06, 0.0)), wrist + Vector((0.0, length, 0.02))]
    tube(builder, points, [0.03] * (len(points) - 1) + [0.004], STEEL, 4, squash=0.25)


def murmillo(seed=1):
    builder = bare(seed, 1, 1, "colisee_fight")
    manica(builder, 1)
    greave(builder, -1, 0.22)
    helmet(builder, "fish")
    shield(builder, (-0.14, 0.46, 1.0), 0.62, 1.02, SCUTUM, 0.14)
    blade(builder, POSES["colisee_fight"][0][1], 0.5)
    return builder


def thraex(seed=2):
    builder = bare(seed, 0, 0, "colisee_lunge", stride=0.26)
    manica(builder, 1)
    greave(builder, -1, 0.26, True)
    greave(builder, 1, 0.26, True)
    helmet(builder, "griffin")
    shield(builder, (-0.14, 0.42, 1.0), 0.48, 0.56, (0.74, 0.56, 0.3), 0.06)
    blade(builder, POSES["colisee_lunge"][0][1], 0.42, True)
    return builder


def retiarius(seed=3):
    builder = bare(seed, 2, 3, "colisee_trident", stride=0.24)
    manica(builder, -1)
    tube(builder, [(-0.2, -0.02, 1.36), (-0.27, 0.0, 1.52), (-0.32, 0.02, 1.62)], [0.08, 0.06, 0.03], BRASS, 5,
         squash=0.3)
    tube(builder, [(0.32, -0.6, 1.0), (0.05, 0.2, 1.2), (-0.25, 1.15, 1.4)], [0.022, 0.022, 0.02], WOOD, 4,
         start_cap=True)
    for offset in (-0.07, 0.0, 0.07):
        tube(builder, [(-0.25 + offset, 1.15, 1.4), (-0.27 + offset * 1.2, 1.4, 1.48)], [0.012, 0.003], STEEL, 3)
    rows = []
    for r, z in enumerate((1.18, 0.78, 0.36)):
        spread = 0.05 + 0.2 * r
        rows.append([(-0.19 + (-1 + 2 * c / 5) * spread, 0.42 + 0.05 * r + 0.05 * math.sin(c * 1.7 + r), z)
                     for c in range(6)])
    for facing in ((0, 1, 0), (0, -1, 0)):
        painted(builder, (0.6, 0.55, 0.42), lambda facing=facing: builder.surface(rows, MATTE, facing=facing))
    return builder


def secutor(seed=4):
    builder = bare(seed, 1, 0, "colisee_fight")
    manica(builder, 1)
    greave(builder, -1, 0.22)
    helmet(builder, "smooth", visor=False, brim=False, colour=(0.7, 0.66, 0.58))
    for side in (-1, 1):
        painted(builder, (0.12, 0.1, 0.09), lambda side=side: builder.box((side * 0.045 - 0.015, 0.135, 1.63),
                                                                          (side * 0.045 + 0.015, 0.145, 1.66), MATTE))
    shield(builder, (-0.14, 0.46, 1.0), 0.62, 1.02, (0.32, 0.36, 0.5), 0.14)
    blade(builder, POSES["colisee_fight"][0][1], 0.5)
    return builder


def referee(seed=5):
    return person(Look("white", hem=0.5, skin=1, hair=2, stripe="purple", belt="dark", carry="staff", arms="staff",
                       seed=seed))


def cornicen(seed=6):
    builder = person(Look("ochre", hem=0.5, skin=1, hair=1, belt=LEATHER, arms="colisee_horn", seed=seed))
    centre = Vector((0.0, -0.05, 1.3))
    points = [centre + Vector((0.55 * math.cos(a), 0.0, 0.55 * math.sin(a))) for a in
              [math.radians(v) for v in range(100, 400, 30)]]
    tube(builder, points, [0.02 + 0.008 * k for k in range(len(points))], BRASS, 5)
    tube(builder, [(0.0, 0.2, 1.6), points[0]], [0.015, 0.02], BRASS, 4)
    tube(builder, [(0.0, -0.05, 1.3), (0.0, -0.05, 1.85)], [0.015, 0.015], WOOD, 4)
    return builder


def organ():
    builder = MeshBuilder()
    painted(builder, (0.5, 0.36, 0.22), lambda: builder.lathe([(0.45, 0.0), (0.45, 0.9), (0.55, 1.0), (0.55, 1.1)],
                                                              10, MATTE))
    painted(builder, (0.45, 0.32, 0.2), lambda: builder.box((-0.6, -0.3, 1.1), (0.6, 0.3, 1.4), MATTE))
    for k in range(12):
        x = -0.5 + k / 11.0
        tube(builder, [(x, -0.05, 1.4), (x, -0.05, 1.6 + 0.9 * (1 - abs(k - 5.5) / 6))], [0.035, 0.035], BRASS, 5)
    builder.merge(person(Look("woad", hem=0.5, skin=0, hair=0, arms="forward", seed=31)), placement(0.0, 0.85, 0.0,
                                                                                                    math.pi))
    return builder


def attendant(seed=7):
    builder = person(Look("undyed", hem=0.55, skin=2, hair=1, belt=LEATHER, arms="colisee_rake", stride=0.1,
                          seed=seed))
    tube(builder, [(0.25, -0.5, 1.3), (0.0, 0.5, 0.95), (-0.15, 1.15, 0.05)], [0.02, 0.02, 0.02], WOOD, 4,
         start_cap=True)
    painted(builder, WOOD, lambda: builder.box((-0.45, 1.12, 0.0), (0.15, 1.2, 0.08), MATTE))
    return builder


def sailor(seed=8):
    return coarse(lambda: person(Look("woad", hem=0.56, skin=2, hair=1, belt=LEATHER, arms="colisee_rope", stride=0.12,
                                      hat=(0.5, 0.42, 0.32), seed=seed)), 0.5)


def praetorian(seed=9):
    builder = person(Look("madder", hem=0.55, skin=1, hair=0, belt=LEATHER, cloak="madder", arms="staff",
                          seed=seed))
    drape(builder, BRASS, [(0.2, 1.0), (0.215, 1.2), (0.21, 1.35), (0.15, 1.44)], 12, folds=(0, 0.0, 0.0),
          squash=0.68)
    helmet(builder, "smooth", visor=False, brim=False)
    tube(builder, [(0.25, 0.22, 0.0), (0.25, 0.2, 2.2)], [0.02, 0.016], WOOD, 4)
    tube(builder, [(0.25, 0.2, 2.2), (0.25, 0.2, 2.42)], [0.03, 0.002], STEEL, 4)
    shield(builder, (-0.3, 0.1, 0.95), 0.55, 0.95, (0.62, 0.2, 0.14), 0.1)
    return builder


def guard(seed=13):
    builder = person(Look("white", hem=0.5, skin=seed % 3, hair=1, belt=LEATHER, arms="down", seed=seed))
    tube(builder, [(0.2, -0.02, 1.38), (0.0, 0.17, 1.2), (-0.2, 0.04, 1.0)], [0.012, 0.012, 0.012], LEATHER, 4)
    tube(builder, [(-0.21, 0.02, 1.0), (-0.24, 0.08, 0.56)], [0.03, 0.022], (0.36, 0.26, 0.18), 5, start_cap=True)
    return builder


def emperor(seed=10):
    builder = person(Look(PURPLE, hem=0.12, skin=0, hair=2, toga=PURPLE, arms="toga_gesture", seed=seed))
    drape(builder, (0.3, 0.42, 0.18), [(0.13, 1.68), (0.135, 1.72)], 10, folds=(9, 0.12, 0.0), squash=0.95)
    return builder


def senator(seed=11, gesture=False):
    return person(Look("white", hem=0.12, skin=seed % 3, hair=seed % 4, toga="white", praetexta="purple" if seed % 3
                       else None, stripe="purple", arms="toga_gesture" if gesture else "toga", seed=seed))


def lictor(seed=12):
    builder = person(Look("white", hem=0.12, skin=1, hair=1, toga="white", arms="shoulder", seed=seed))
    painted(builder, (0.5, 0.32, 0.18), lambda: builder.lathe([(0.06, 0.0), (0.06, 0.9), (0.0, 0.92)], 6, MATTE,
                                                              matrix=Matrix.Translation((0.24, 0.14, 1.0))
                                                              @ Matrix.Rotation(0.5, 4, "X")))
    return builder


def lion():
    builder = MeshBuilder()
    coat = (0.72, 0.56, 0.32)
    mane = (0.4, 0.27, 0.14)
    ellipsoid(builder, (0.0, 0.0, 0.72), (0.26, 0.75, 0.3), coat, 10, 6)
    ellipsoid(builder, (0.0, 0.6, 0.9), (0.34, 0.3, 0.36), mane, 8, 5)
    ellipsoid(builder, (0.0, 0.85, 0.88), (0.16, 0.22, 0.16), coat, 8, 4)
    for side in (-1, 1):
        for end in (-1, 1):
            tube(builder, [(side * 0.15, end * 0.52, 0.66), (side * 0.15, end * 0.55, 0.3), (side * 0.15, end * 0.58, 0.02)],
                 [0.09, 0.07, 0.07], coat, 5)
    tube(builder, [(0.0, -0.72, 0.8), (0.0, -1.1, 0.5), (0.0, -1.25, 0.25)], [0.03, 0.025, 0.04], coat, 4)
    return builder


def cage():
    builder = MeshBuilder()
    for x in (-0.9, 0.9):
        for y in (-1.3, 1.3):
            tube(builder, [(x, y, 0.0), (x, y, 2.0)], [0.06, 0.06], WOOD, 4)
    for z in (0.05, 1.95):
        painted(builder, WOOD, lambda z=z: builder.box((-0.95, -1.35, z - 0.05), (0.95, 1.35, z + 0.05), MATTE))
    for k in range(7):
        x = -0.9 + 1.8 * k / 6
        tube(builder, [(x, 1.3, 0.05), (x, 1.3, 1.95)], [0.025, 0.025], (0.36, 0.26, 0.18), 3)
    return builder


def gladiator_pair(left, right, gap=1.7):
    builder = MeshBuilder()
    builder.merge(left, placement(0.0, -gap / 2, 0.0, 0.0))
    builder.merge(right, placement(0.15, gap / 2, 0.0, math.pi))
    return builder


FIGURE_BUILDS = {
    "fig_murmillo": murmillo,
    "fig_thraex": thraex,
    "fig_retiarius": retiarius,
    "fig_secutor": secutor,
    "fig_referee": referee,
    "fig_cornicen": cornicen,
    "prop_organ": organ,
    "fig_attendant": attendant,
    "fig_sailor": sailor,
    "fig_praetorian": praetorian,
    "fig_guard": guard,
    "fig_emperor": emperor,
    "fig_senator": lambda: senator(11),
    "fig_senator_gesture": lambda: senator(14, True),
    "fig_lictor": lictor,
    "prop_lion": lion,
    "prop_cage": cage,
}

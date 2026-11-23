"""City density pass: a river, new districts, street trees and layered roads.

    blender -b blender/sets/city_v008.blend --python tools/blender/build_city_density.py -- <out.blend>

  * the Skyhaven River winds west-east south of downtown (y about -1540): stone embankments,
    tree-lined promenades with lamps and benches, riverside lawns; bridges where the Skyway and
    two extended downtown streets (x = 100 and x = -500) cross, a white arch on the Skyway bridge
  * Riverside district south of the river: a street grid of mixed blocks (podium towers, mid-rise
    apartments, rows of smaller buildings, a pocket park), varied heights and facades, rooftop
    plant and gardens, street trees, parked cars
  * Eastgate office park between Heights Avenue and the hospital: glass offices of different
    heights round a plaza, a loop road, parking, trees
  * street trees along every downtown street
  * the River Expressway: an elevated road on piers along the north bank (14 m up) with barriers,
    traffic and ramps down at both ends
  * episode cameras: CT_cam_ep_city_aerial, CT_cam_ep_river, CT_cam_ep_downtown_street,
    CT_cam_ep_riverside
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(909)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {"asphalt": "#55575c", "bank": "#b9ad98", "bank_top": "#e2dccf", "lawn2": "#86c35a", "deck": "#cfcbc3",
             "pier": "#d9d5cc", "roof_g": "#6aa84f", "roof_m": "#9aa0a7", "arch": "#f6f6f3"}.items():
    M[k] = toon("CT_" + k, v)
M.setdefault("pave", M.get("paving"))
WATER_KEY = "water_pool" if "water_pool" in M else "water"
WATER = M[WATER_KEY]

old = bpy.data.collections.get("CT_CityDensity")
if old:
    for o in list(old.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
CD = bpy.data.collections.new("CT_CityDensity")
bpy.data.collections["City"].children.link(CD)
use(CD)

TREES = [bpy.data.objects[n] for n in ("CT.tree_a_t", "CT.tree_a_t", "CT.tree_b_t") if bpy.data.objects.get(n)]
PALM = bpy.data.objects.get("CT.palm_t")
CARS = [bpy.data.objects[n] for n in ("CT.car_t%d" % i for i in range(6)) if bpy.data.objects.get(n)]
TREE_ITEMS, CAR_ITEMS = [], []


def tree(x, y, s=None, kind=None):
    TREE_ITEMS.append((kind or random.choice(TREES), (x, y, 0.0), random.uniform(0, 6.28), s or random.uniform(0.8, 1.2)))


# ================================================================ the river
def river_y(x):
    return -1540.0 + 55.0 * math.sin(x / 380.0) + 25.0 * math.sin(x / 170.0 + 1.0)


RX = [x for x in range(-2700, 3001, 25)]
RC = [(x, river_y(x)) for x in RX]


def offset_pts(off):
    out = []
    for i, (x, y) in enumerate(RC):
        a = Vector(RC[max(0, i - 1)])
        b = Vector(RC[min(len(RC) - 1, i + 1)])
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        out.append(Vector((x, y)) + n * off)
    return out


strip("CT.river_water", RC, 80, WATER, 0.015)
for side in (1, -1):
    strip("CT.river_lawn_%d" % side, [tuple(p) for p in offset_pts(side * 66)], 36, M["lawn2"], 0.008)
    strip("CT.river_prom_%d" % side, [tuple(p) for p in offset_pts(side * 46)], 8, M["pave"], 0.02)
bk = P("CT.river_banks")
for side in (1, -1):
    pts = offset_pts(side * 41)
    for a, b in zip(pts, pts[1:]):
        bk.beam((a.x, a.y, 0.35), (b.x, b.y, 0.35), 2.2, 0.9, "bank")
        bk.beam((a.x, a.y, 0.85), (b.x, b.y, 0.85), 2.4, 0.15, "bank_top")
bk.done(outline=0.02)

# roads that cross the river (extensions of downtown streets) and the bridges
CROSS = []
for xs in (100.0, -500.0):
    strip("CT.street_ext_%d" % int(xs), [(xs, -1350.0), (xs, -2030.0)], 18, M["r_street"], 0.022)
    CROSS.append((Vector((xs, river_y(xs))), Vector((0, 1)), 18.0, False))
A, B = Vector((1360.0, -1400.0)), Vector((1800.0, -2000.0))
best = min(((abs((A.lerp(B, t)).y - river_y(A.lerp(B, t).x)), t) for t in [k / 400 for k in range(401)]))
CROSS.append((A.lerp(B, best[1]), (B - A).normalized(), 28.0, True))
br = P("CT.bridges")
for c, d, w, arch in CROSS:
    n = Vector((-d.y, d.x))
    span = 110.0
    for side in (1, -1):
        e = c + n * side * (w / 2 + 0.6)
        a3, b3 = e - d * span / 2, e + d * span / 2
        br.beam((a3.x, a3.y, 0.55), (b3.x, b3.y, 0.55), 1.0, 1.0, "pier")          # girder
        br.beam((a3.x, a3.y, 1.55), (b3.x, b3.y, 1.55), 0.35, 0.12, "arch")         # handrail
        for k in range(23):
            p = a3.lerp(b3, k / 22)
            br.box(p.x - 0.08, p.x + 0.08, p.y - 0.08, p.y + 0.08, 1.0, 1.55, "arch")
        if arch:
            prev = None
            for k in range(17):
                t = k / 16
                p = a3.lerp(b3, t)
                q = Vector((p.x, p.y, 1.5 + 22.0 * math.sin(t * math.pi)))
                if prev is not None:
                    br.beam(prev, q, 1.2, 1.2, "arch")
                    if 0 < k < 16 and k % 2 == 0:
                        br.beam((p.x, p.y, 1.5), q, 0.15, 0.15, "arch")
                prev = q
    for k in (-1, 1):
        p = c + d * k * 22
        br.box(p.x - 3, p.x + 3, p.y - 3, p.y + 3, -0.5, 0.05, "pier")
br.done(outline=0.03)
# promenade life: trees, lamps and benches on both banks (not on the bridges)
lb = P("CT.prom_furniture")
for side in (1, -1):
    pts = offset_pts(side * 52)
    for i, p in enumerate(pts):
        if any((p - c).length < 30 for c, d, w, a in CROSS):
            continue
        if i % 1 == 0:
            tree(p.x, p.y, random.uniform(0.85, 1.15))
        if i % 2 == 0:
            q = offset_pts(side * 42.6)[i]
            lb.box(q.x - 0.1, q.x + 0.1, q.y - 0.1, q.y + 0.1, 0.0, 4.2, "frame")
            lb.box(q.x - 0.35, q.x + 0.35, q.y - 0.35, q.y + 0.35, 4.2, 4.45, "white_c")
        if i % 3 == 1:
            q = offset_pts(side * 49.5)[i]
            lb.box(q.x - 0.9, q.x + 0.9, q.y - 0.25, q.y + 0.25, 0.4, 0.5, "bench")
            lb.box(q.x - 0.9, q.x + 0.9, q.y - 0.3, q.y - 0.2, 0.0, 0.4, "frame")
lb.done(outline=0.01)


# ================================================================ building kit
FACS = ["f_glass_blue", "f_glass_teal", "f_glass_dark", "f_office", "f_stone", "f_brick", "f_apart", "f_apart2", "f_shop"]


def building(p, x0, x1, y0, y1, h, fac, roof_bits=True):
    p.box(x0, x1, y0, y1, 0.0, h, fac)
    p.box(x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5, h, h + 1.0, "white_c")
    if roof_bits and (x1 - x0) > 14 and (y1 - y0) > 14:
        r = random.random()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if r < 0.35:                                       # roof garden
            p.box(x0 + 2, x1 - 2, y0 + 2, y1 - 2, h + 1.0, h + 1.4, "roof_g")
        elif r < 0.7:                                      # plant room and AC units
            p.box(cx - 5, cx + 5, cy - 4, cy + 4, h + 1.0, h + 5.0, "roof_m")
            for k in range(3):
                p.box(x0 + 3 + k * 4, x0 + 6 + k * 4, y1 - 6, y1 - 3, h + 1.0, h + 2.4, "uld" if "uld" in M else "roof_m")
        else:                                              # water tank
            p.cyl((cx + 3, cy, h + 3.5), 2.5, 5.0, "roof_m", segs=12)


def fill_block(p, x0, x1, y0, y1, centre_h, kind=None):
    w, d = x1 - x0, y1 - y0
    kind = kind or random.choice(("podium", "podium", "midrise", "midrise", "row", "row", "tower2"))
    if kind == "park":
        p.box(x0, x1, y0, y1, 0.0, 0.08, "lawn2")
        p.blob(((x0 + x1) / 2, (y0 + y1) / 2, 0.05), (w * 0.2, d * 0.15, 0.06), "water" if "water" in M else "pool", subdiv=2)
        for k in range(14):
            tree(random.uniform(x0 + 5, x1 - 5), random.uniform(y0 + 5, y1 - 5))
        return
    if kind == "podium":
        building(p, x0, x1, y0, y1, random.uniform(9, 14), "f_shop", roof_bits=False)
        tw, td = w * random.uniform(0.35, 0.55), d * random.uniform(0.35, 0.55)
        cx, cy = x0 + w * random.uniform(0.3, 0.7), y0 + d * random.uniform(0.3, 0.7)
        building(p, cx - tw / 2, cx + tw / 2, cy - td / 2, cy + td / 2, centre_h * random.uniform(0.8, 1.3),
                 random.choice(FACS[:5]))
    elif kind == "tower2":
        for sx in (-1, 1):
            cx = (x0 + x1) / 2 + sx * w * 0.24
            building(p, cx - w * 0.2, cx + w * 0.2, y0 + d * 0.2, y1 - d * 0.2, centre_h * random.uniform(0.6, 1.2),
                     random.choice(FACS[:5]))
    elif kind == "midrise":
        for sx in (-1, 1):
            cx = (x0 + x1) / 2 + sx * w * 0.25
            building(p, cx - w * 0.22, cx + w * 0.22, y0 + 4, y1 - 4, random.uniform(15, 32), random.choice(FACS[3:8]))
        for k in range(4):
            tree((x0 + x1) / 2 + random.uniform(-3, 3), y0 + 8 + k * (d - 16) / 3, 0.8)
    else:                                                  # row of smaller buildings
        n = random.choice((4, 5))
        for k in range(n):
            a = x0 + k * w / n
            building(p, a + 1, a + w / n - 1, y0 + 4, y0 + d * 0.45, random.uniform(9, 20), random.choice(FACS[3:]))
            building(p, a + 1, a + w / n - 1, y1 - d * 0.45, y1 - 4, random.uniform(9, 20), random.choice(FACS[3:]))


def street_trees_x(y, x0, x1, skip_x, step=16):
    x = x0
    while x < x1:
        if all(abs(x - s) > 14 for s in skip_x):
            tree(x, y + 12.5, 0.75)
            tree(x, y - 12.5, 0.75)
        x += step


def street_trees_y(x, y0, y1, skip_y, step=16):
    y = y0
    while y < y1:
        if all(abs(y - s) > 14 for s in skip_y):
            tree(x + 12.5, y, 0.75)
            tree(x - 12.5, y, 0.75)
        y += step


# ================================================================ Riverside district (south of the river)
RXS = [-900.0 + 150 * i for i in range(15)]                # -900 .. 1200
RYS = [-1730.0, -1870.0, -2010.0]
for i, x in enumerate(RXS):
    strip("CT.rs_ns%d" % i, [(x, RYS[0] + 9), (x, RYS[-1] - 9)], 16, M["r_street"], 0.02)
for j, y in enumerate(RYS):
    strip("CT.rs_ew%d" % j, [(RXS[0] - 9, y), (RXS[-1] + 9, y)], 16, M["r_street"], 0.021)
pad = P("CT.rs_pavement")
pad.box(RXS[0] - 12, RXS[-1] + 12, RYS[-1] - 12, RYS[0] + 12, -0.05, 0.012, "pave")
pad.done(outline=0.0)
rs = P("CT.riverside_blocks")
for i in range(len(RXS) - 1):
    for j in range(len(RYS) - 1):
        x0, x1 = RXS[i] + 13, RXS[i + 1] - 13
        y1, y0 = RYS[j] - 13, RYS[j + 1] + 13
        centre = 30 + 70 * max(0.0, 1.0 - abs((x0 + x1) / 2 - 150) / 900) ** 1.2
        kind = "park" if (i, j) in ((6, 0), (11, 1)) else None
        fill_block(rs, x0, x1, y0, y1, centre, kind)
rs.done(outline=0.12)
for y in RYS:
    street_trees_x(y, RXS[0], RXS[-1], RXS)
for x in RXS:
    street_trees_y(x, RYS[-1], RYS[0], RYS)
for k in range(140):                                       # parked cars along Riverside streets
    if random.random() < 0.5:
        y = random.choice(RYS) + random.choice((-6.0, 6.0))
        x = random.uniform(RXS[0], RXS[-1])
        if all(abs(x - s) > 12 for s in RXS):
            CAR_ITEMS.append((random.choice(CARS), (x, y, 0.03), math.radians(90 if y > 0 else 90), 1.0))
    else:
        x = random.choice(RXS) + random.choice((-6.0, 6.0))
        y = random.uniform(RYS[-1], RYS[0])
        if all(abs(y - s) > 12 for s in RYS):
            CAR_ITEMS.append((random.choice(CARS), (x, y, 0.03), 0.0, 1.0))

# ================================================================ Eastgate office park
eg = P("CT.eastgate")
eg.box(930, 1290, -560, -150, -0.05, 0.012, "pave")
eg.box(1060, 1160, -400, -300, 0.012, 0.03, "lawn2")
eg.cyl((1110, -350, 0.3), 8.0, 0.6, "white_c", segs=32)
eg.cyl((1110, -350, 0.55), 7.0, 0.2, WATER_KEY, segs=32)
for (x0, x1, y0, y1, h, fac) in ((945, 1010, -230, -165, 42, "f_glass_blue"), (1030, 1095, -230, -165, 28, "f_glass_teal"),
                                 (1200, 1275, -250, -165, 55, "f_glass_dark"), (945, 1030, -545, -470, 22, "f_office"),
                                 (1180, 1275, -545, -460, 36, "f_glass_blue"), (945, 1000, -430, -300, 18, "f_stone")):
    building(eg, x0, x1, y0, y1, h, fac)
eg.done(outline=0.12)
strip("CT.eastgate_loop", [(940, -280), (1290, -280)], 10, M["r_street"], 0.02)
strip("CT.eastgate_parking", [(1180, -420), (1280, -420)], 30, M["r_parking"], 0.025)
for k in range(30):
    CAR_ITEMS.append((random.choice(CARS), (random.uniform(1185, 1275), random.uniform(-432, -408), 0.03),
                      random.choice((0.0, math.pi)), 1.0))
for k in range(20):
    tree(random.uniform(1065, 1155), random.choice((-305.0, -395.0)) + random.uniform(-3, 3), 0.8)

# ================================================================ downtown street trees
DX = [-500, -350, -200, -50, 100, 250, 400, 550, 700, 850]
DY = [-600, -750, -900, -1050, -1200, -1350]
for y in DY:
    street_trees_x(y, DX[0], DX[-1], DX)
for x in DX:
    street_trees_y(x, DY[-1], DY[0], DY)

# ================================================================ River Expressway (elevated)
EY, EZ, EW = -1395.0, 14.0, 24.0
EX0, EX1 = -1380.0, 1250.0
strip("CT.expressway_deck_road", [(EX0, EY), (EX1, EY)], EW, M["r_highway"], EZ + 0.6)
ex = P("CT.expressway")
ex.box(EX0, EX1, EY - EW / 2 - 0.5, EY + EW / 2 + 0.5, EZ - 1.2, EZ + 0.58, "deck")
for sy in (-1, 1):
    ex.box(EX0, EX1, EY + sy * (EW / 2 + 0.5) - 0.4, EY + sy * (EW / 2 + 0.5) + 0.4, EZ + 0.58, EZ + 1.6, "pier")
x = EX0 + 20
while x < EX1 - 10:
    ex.box(x - 1.6, x + 1.6, EY - 2.5, EY + 2.5, 0.0, EZ - 1.2, "pier")          # pier
    ex.box(x - 2.2, x + 2.2, EY - EW / 2, EY + EW / 2, EZ - 2.2, EZ - 1.2, "pier")  # cap beam
    x += 45
for (xa, xb, za, zb) in ((EX1, EX1 + 200, EZ, 0.6), (EX0 - 200, EX0, 0.6, EZ)):   # ramps down at both ends
    steps = 10
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        xa0, xa1 = xa + (xb - xa) * t0, xa + (xb - xa) * t1
        z0, z1 = za + (zb - za) * t0, za + (zb - za) * t1
        ex.beam((xa0, EY, z0 + 0.3), (xa1, EY, z1 + 0.3), EW, 0.6, "asphalt")
        if min(z0, z1) > 2:
            ex.box((xa0 + xa1) / 2 - 1.4, (xa0 + xa1) / 2 + 1.4, EY - 2.2, EY + 2.2, 0.0, min(z0, z1) - 0.3, "pier")
ex.done(outline=0.05)
strip("CT.expressway_link_e", [(EX1 + 200, EY), (1346, EY), (1350, -1385)], 14, M["r_street"], 0.022)
strip("CT.expressway_link_w", [(EX0 - 200, EY), (-1455, EY), (-1455, -1180)], 14, M["r_street"], 0.022)
for k in range(60):                                        # traffic on the expressway
    x = random.uniform(EX0 + 10, EX1 - 10)
    lane = random.choice((-7.5, -3.0, 3.0, 7.5))
    rot = math.radians(90) if lane < 0 else math.radians(-90)
    CAR_ITEMS.append((random.choice(CARS), (x, EY + lane, EZ + 0.62), rot, 1.0))

# ================================================================ merge the many copies, cameras
scatter("CT.density_trees", CD, TREE_ITEMS, outline=0.05)
if CAR_ITEMS:
    scatter("CT.density_cars", CD, CAR_ITEMS, outline=0.02)


def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.5, 16000
    co = bpy.data.objects.new(name, cd)
    CD.objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


cam("CT_cam_ep_city_aerial", (1350.0, -2450.0, 420.0), (120.0, -1150.0, 0.0), 30)
cam("CT_cam_ep_river", (276.0, river_y(276.0) - 47.0, 3.2), (190.0, -1250.0, 62.0), 22)
cam("CT_cam_ep_downtown_street", (107.0, -1185.0, 2.0), (107.0, -640.0, 32.0), 24)
cam("CT_cam_ep_riverside", (300.0, -2032.0, 2.2), (300.0, -1740.0, 30.0), 24)

consolidate(CD, ("CT_cam", "CT.density_trees", "CT.density_cars"))

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

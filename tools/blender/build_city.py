"""Skyhaven, the city around the family's mansion (cartoon toon style).

    blender -b --factory-startup --python tools/blender/build_city.py -- <out.blend> <mansion.blend>

Real-metre layout under CT.root (scaled 0.62 like the mansion), mansion at the origin
facing -Y (south). X = east, Y = north.

  Skyhaven Heights (rich, north)   the mansion behind a gated wall on Heights Avenue,
                                   neighbour villas with pools, Heights Academy
                                   (international school), Skyhaven Galleria (mall),
                                   country club and golf course, lake with a marina
  Downtown (south)                 street grid of towers, Skyhaven Tower, a central park
  Civic (east of downtown)         Skyhaven General Hospital with helipad, fire station,
                                   police station
  Maple Park (west, middle class)  streets of family houses (the second family's home is
                                   CT.family2_home), Maple Park Primary school, supermarket,
                                   park and playground, apartment blocks, petrol station
  Skyway (highway)                 from the Heights down past the hospital to the airport
  Skyhaven International (SE)      two 3 km runways, taxiways, terminal with jet bridges and
                                   parked jets, control tower, hangars, car park
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
MANSION = argv[1] if len(argv) > 1 else None
random.seed(2026)

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
S = bpy.context.scene
S.name = "Skyhaven"

ROOT = bpy.data.collections.new("City")
S.collection.children.link(ROOT)
C = {}
for n in ("CT_Ground", "CT_Roads", "CT_Heights", "CT_Downtown", "CT_Civic", "CT_MaplePark", "CT_Airport",
          "CT_Nature", "CT_Traffic", "CT_Cams"):
    c = bpy.data.collections.new(n)
    ROOT.children.link(c)
    C[n] = c
RIG = bpy.data.objects.new("CT.root", None)
ROOT.objects.link(RIG)
RIG.scale = (K.SCALE,) * 3
K.PARENT[0] = RIG

# ---------------------------------------------------------------- materials
for k, v in {
    "grass": "#79b44c", "grass2": "#8cc45a", "fairway": "#9fd06a", "sand2": "#ecd9a0", "water": "#5aa7d6",
    "water_lt": "#a6d6f0", "pave": "#d7d2c8", "concrete2": "#c8c4bc", "apron": "#bdbab3", "asphalt": "#55575c",
    "curb": "#e6e2da", "roof_red": "#b9573f", "roof_grey": "#6b6f78", "roof_brown": "#7e5a43", "roof_flat": "#9a9ca3",
    "wall_a": "#f1e3c6", "wall_b": "#cfe0e8", "wall_c": "#f4d3c4", "wall_d": "#e8edd8", "wall_e": "#fbf6ec",
    "wall_f": "#f2e08c", "door_blue": "#3f6fa8", "door_red": "#b8453a", "door_green": "#4f7d55",
    "win": "#4a6274", "white_c": "#f6f4ef", "red_cross": "#d6403a", "fire_red": "#c8362e", "police": "#2f4a7a",
    "yellow": "#f2c14e", "teal": "#2f9a9a", "plane": "#f5f6f7", "plane_belly": "#c9ced3", "tyre_c": "#2a2a2e",
    "metal": "#b8bec4", "tower_cab": "#5f8fb0", "sign_green": "#2f7a4a", "sign_text": "#ffffff", "pool": "#6fc6e8",
    "bark": "#7a5234", "leaf_a": "#5e9a3f", "leaf_b": "#7db454", "pine": "#3f7a4a", "mountain": "#8fa6b8",
    "mountain2": "#a9bccb", "snow": "#f4f7fa", "track": "#c9674b", "court": "#4f8fb8", "car_r": "#d24a3c",
    "car_b": "#3f6fa8", "car_w": "#f2f2f0", "car_k": "#2e2e33", "car_y": "#f2c14e", "car_s": "#b8bec4",
    "glass_c": "#33414d", "brick": "#b5654a", "slide": "#e2574c", "bench": "#8a5a3a", "fountain": "#bfe3f2",
    "helipad": "#4a4d52"}.items():
    M[k] = toon("CT_" + k, v)
FAC = {
    "glass_blue": facade("CT_f_glass_blue", "#dfe7ec", "#5f87a8", 3.0, 0.86, 3.8, 0.12, 0.92),
    "glass_teal": facade("CT_f_glass_teal", "#e4ece9", "#3f8f92", 2.6, 0.84, 3.8, 0.1, 0.94),
    "glass_dark": facade("CT_f_glass_dark", "#c9ced3", "#34495c", 3.4, 0.8, 4.0, 0.1, 0.92),
    "office": facade("CT_f_office", "#f1ede4", "#4f6b80", 3.2, 0.6, 3.6, 0.28, 0.82),
    "stone": facade("CT_f_stone", "#d8c7a8", "#3f4f5c", 3.0, 0.5, 3.8, 0.3, 0.8),
    "brick": facade("CT_f_brick", "#b5654a", "#3f4f5c", 3.0, 0.5, 3.2, 0.32, 0.8),
    "apart": facade("CT_f_apart", "#f0d9b5", "#4a6274", 3.6, 0.45, 3.0, 0.3, 0.78),
    "apart2": facade("CT_f_apart2", "#cfe0e8", "#4a6274", 3.6, 0.45, 3.0, 0.3, 0.78),
    "hospital": facade("CT_f_hospital", "#f7f7f4", "#4f9aa8", 3.0, 0.6, 3.8, 0.25, 0.85),
    "school": facade("CT_f_school", "#d77a55", "#f4efe2", 3.4, 0.55, 3.6, 0.3, 0.8),
    "school2": facade("CT_f_school2", "#f1ede4", "#3f6fa8", 3.4, 0.55, 3.6, 0.3, 0.82),
    "terminal": facade("CT_f_terminal", "#e8eef2", "#6aa3c8", 4.0, 0.9, 6.0, 0.05, 0.95),
    "shop": facade("CT_f_shop", "#f4efe2", "#5f87a8", 4.0, 0.8, 5.0, 0.08, 0.7),
    "hangar": facade("CT_f_hangar", "#cfd4d8", "#9aa3aa", 1.2, 0.08, 50.0, 0.0, 1.0),
}
M["pave"] = M["paving"]
for k, m in FAC.items():
    M["f_" + k] = m
ROAD = {
    "avenue": striped("CT_r_avenue", "#55575c", "#f4f1e6", [("b", 0.48, 0.52, 0), ("b", 0.03, 0.05, 0), ("b", 0.95, 0.97, 0)]),
    "street": striped("CT_r_street", "#5b5d62", "#f4f1e6", [("b", 0.47, 0.53, 6.0)]),
    "highway": striped("CT_r_highway", "#4f5156", "#f4f1e6", [("b", 0.02, 0.035, 0), ("b", 0.965, 0.98, 0),
                                                               ("b", 0.245, 0.255, 9.0), ("b", 0.745, 0.755, 9.0),
                                                               ("b", 0.47, 0.53, 0)]),
    "runway": striped("CT_r_runway", "#4b4d52", "#f8f8f5", [("b", 0.49, 0.51, 30.0), ("b", 0.015, 0.03, 0), ("b", 0.97, 0.985, 0)]),
    "taxi": striped("CT_r_taxi", "#66686d", "#f2c14e", [("b", 0.485, 0.515, 0)]),
    "parking": striped("CT_r_parking", "#6a6c71", "#f4f1e6", [("b", 0.0, 0.4, 2.8, 0.05), ("b", 0.6, 1.0, 2.8, 0.05)]),
}
for k, m in ROAD.items():
    M["r_" + k] = m

use(C["CT_Ground"])


# ---------------------------------------------------------------- small helpers
def bx(p, c, size, k, z0=0.0):
    """Box by centre (x, y) and size (w, d, h) standing on z0."""
    p.box(c[0] - size[0] / 2, c[0] + size[0] / 2, c[1] - size[1] / 2, c[1] + size[1] / 2, z0, z0 + size[2], k)


BATCH = {}


def dup(src, name, loc, rot=0.0, scale=1.0, coll=None, merge=True):
    """Place a copy of a template. merge=True (default) batches copies into one mesh per
    template and collection (EEVEE draws thousands of outlined objects badly); merge=False
    makes a linked duplicate object (for props that get animated or named)."""
    coll = coll or TARGET[0]
    if merge:
        mw = (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rot), 4, 'Z')
              @ Matrix.Diagonal((scale, scale, scale, 1)))
        BATCH.setdefault((src.name, coll.name), []).append(mw)
        return None
    ob = bpy.data.objects.new(name, src.data)
    coll.objects.link(ob)
    ob.parent = RIG
    for m in src.modifiers:
        n = ob.modifiers.new(m.name, m.type)
        if m.type == 'SOLIDIFY':
            n.thickness, n.offset, n.use_flip_normals, n.material_offset, n.use_rim =                 m.thickness, m.offset, m.use_flip_normals, m.material_offset, m.use_rim
    ob.location = loc
    ob.rotation_euler.z = math.radians(rot)
    ob.scale = (scale,) * 3
    return ob


def flush_batches():
    for (sname, cname), mats in BATCH.items():
        src = bpy.data.objects[sname]
        bm = bmesh.new()
        for mw in mats:
            tmp = bmesh.new()
            tmp.from_mesh(src.data)
            bmesh.ops.transform(tmp, matrix=mw, verts=tmp.verts)
            me = bpy.data.meshes.new("_b")
            tmp.to_mesh(me)
            tmp.free()
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        name = sname[:-2] + "_all." + cname[3:] if sname.endswith("_t") else sname + "_all"
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for m in src.data.materials:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        bpy.data.collections[cname].objects.link(ob)
        ob.parent = RIG
        for m in src.modifiers:
            n = ob.modifiers.new(m.name, m.type)
            if m.type == 'SOLIDIFY':
                n.thickness, n.offset, n.use_flip_normals, n.material_offset, n.use_rim =                     m.thickness, m.offset, m.use_flip_normals, m.material_offset, m.use_rim


def template(p, name, outline=0.02):
    """Build a piece at the origin and hide it (used only through dup)."""
    ob = p.done(outline=outline)
    ob.hide_render = ob.hide_viewport = True
    return ob


# ---------------------------------------------------------------- ground and nature
g = P("CT.ground")
g.box(-9000, 9000, -9000, 9000, -0.4, -0.06, "grass")
g.done(outline=0)
use(C["CT_Nature"])
# lake with marina (south of Heights Avenue, west of the boulevard)
lk = P("CT.lake")
lk.blob((-400, -265, -0.05), (270, 150, 0.05), "water", subdiv=3)
lk.blob((-400, -265, -0.09), (290, 168, 0.07), "sand2", subdiv=3)
lk.done(outline=0)
mar = P("CT.marina")
mar.box(-520, -280, -128, -118, 0.0, 0.6, "bench")
for x in (-500, -440, -380, -320):
    mar.box(x - 1.5, x + 1.5, -150, -128, 0.0, 0.6, "bench")
mar.done(outline=0.05)
yacht = P("CT.yacht_t")
yacht.box(-2.5, 2.5, -9, 9, 0.0, 2.2, "white_c", taper=(0.75, 0.9))
yacht.blob((0, -9, 1.6), (2.3, 3.5, 1.2), "white_c")
yacht.box(-1.8, 1.8, -4, 4, 2.2, 4.2, "white_c")
yacht.box(-1.85, 1.85, -3.9, 3.9, 3.0, 3.6, "glass_c")
yacht.box(-2.5, 2.5, -9, 9, 0.0, 0.5, "door_blue")
Y_T = template(yacht, "CT.yacht_t")
for i, x in enumerate((-470, -410, -350, -290, -230)):
    dup(Y_T, "CT.yacht%d" % i, (x + random.uniform(-6, 6), -168 - random.uniform(0, 30), 0.0), random.uniform(-15, 15))
# golf course + country club (south of the avenue, east of the boulevard)
gf = P("CT.golf")
gf.box(220, 900, -430, -110, -0.06, 0.01, "grass2")
for c, r in (((330, -200), (60, 28)), ((520, -300), (80, 30)), ((740, -180), (70, 26)), ((800, -360), (60, 30)),
             ((420, -380), (55, 22))):
    gf.blob((c[0], c[1], 0.0), (r[0], r[1], 0.03), "fairway", subdiv=2)
for c in ((360, -230), (560, -280), (700, -200), (780, -380)):
    gf.blob((c[0], c[1], 0.0), (9, 6, 0.06), "sand2", subdiv=2)
for c in ((310, -195), (545, -305), (760, -175), (815, -365)):
    gf.cyl((c[0], c[1], 3.5), 0.12, 7.0, "white_c", segs=6)
    gf.box(c[0], c[0] + 2.2, c[1] - 0.05, c[1] + 0.05, 5.6, 7.0, "red_cross")
gf.blob((600, -390, 0.0), (40, 18, 0.06), "water", subdiv=2)
gf.done(outline=0)
club = P("CT.country_club")
bx(club, (560, -150), (70, 26, 7), "white_c")
bx(club, (560, -150), (78, 32, 0.8), "white_c", 7.0)
club.box(527, 593, -164, -163, 1.0, 5.6, "win")
bx(club, (520, -125), (24, 12, 1.2), "pool", -1.0)
for i in range(3):
    bx(club, (640 + i * 22, -135), (18, 34, 0.1), "court")
club.done(outline=0.12)
# distant mountains on the horizon
mt = P("CT.mountains")
for k in range(36):
    a = k / 36 * math.tau + random.uniform(-0.04, 0.04)
    r = random.uniform(6500, 8200)
    h = random.uniform(600, 1500)
    c = (math.cos(a) * r + 1200, math.sin(a) * r - 1500, 0)
    mt.cyl((c[0], c[1], h / 2), random.uniform(900, 1600), h, random.choice(("mountain", "mountain2")), segs=7, r2=0.0)
    if h > 1200:
        mt.cyl((c[0], c[1], h * 0.86), 260, h * 0.28, "snow", segs=7, r2=0.0)
mt.done(outline=0)

# trees (templates + duplicates)
t1 = P("CT.tree_a_t")
t1.cyl((0, 0, 1.6), 0.28, 3.2, "bark", r2=0.18)
for (x, y, z, r, k) in ((0, 0, 4.6, 2.2, "leaf_a"), (1.1, 0.3, 3.9, 1.6, "leaf_b"), (-1.0, -0.4, 4.0, 1.5, "leaf_b"),
                        (0.2, 0.9, 5.4, 1.4, "leaf_a")):
    t1.blob((x, y, z), (r, r, r * 0.85), k, subdiv=1)
TREE_A = template(t1, "CT.tree_a_t", outline=0.06)
t2 = P("CT.tree_b_t")
t2.cyl((0, 0, 1.0), 0.22, 2.0, "bark")
t2.cyl((0, 0, 3.4), 2.0, 3.6, "pine", r2=0.0, segs=8)
t2.cyl((0, 0, 5.2), 1.5, 3.0, "pine", r2=0.0, segs=8)
TREE_B = template(t2, "CT.tree_b_t", outline=0.06)
t3 = P("CT.palm_t")
for i in range(6):
    t3.cyl((0.12 * i, 0, 0.9 + i * 1.6), 0.25 - i * 0.02, 1.7, "bark", segs=8)
for k in range(7):
    a = k / 7 * math.tau
    t3.beam((0.7, 0, 9.6), (0.7 + math.cos(a) * 3.2, math.sin(a) * 3.2, 8.4), 1.0, 0.15, "leaf_a")
PALM = template(t3, "CT.palm_t", outline=0.04)
TREES = []


def tree_at(x, y, kind=None, s=None):
    src = kind or random.choice((TREE_A, TREE_A, TREE_B))
    dup(src, "CT.tree", (x, y, 0), random.uniform(0, 360), s or random.uniform(0.8, 1.3), C["CT_Nature"])


# ================================================================ ROADS
use(C["CT_Roads"])
AV_Y = -66
road_heights = strip("CT.heights_avenue", [(-1250, AV_Y), (1300, AV_Y)], 16, M["r_avenue"], 0.02)
BOUL = [(100, AV_Y), (100, -600)]
strip("CT.main_boulevard", BOUL, 18, M["r_avenue"], 0.025)
SKYWAY = [(1300, AV_Y), (1360, -200), (1360, -1400), (1800, -2000), (2400, -2430), (2700, -2560), (3950, -2560)]
strip("CT.skyway", SKYWAY, 28, M["r_highway"], 0.03)
# downtown grid
DX = [-500, -350, -200, -50, 100, 250, 400, 550, 700, 850]
DY = [-600, -750, -900, -1050, -1200, -1350]
for i, x in enumerate(DX):
    strip("CT.dt_ns%d" % i, [(x, DY[0] - 10), (x, DY[-1] + 10)], 18, M["r_street"], 0.02)
for j, y in enumerate(DY):
    x1 = 1360 if y in (-750, -1050) else DX[-1] + 10
    strip("CT.dt_ew%d" % j, [(DX[0] - 10, y), (x1, y)], 18, M["r_street"], 0.022)
# Maple Park streets
MP_Y = [-560, -680, -800, -920, -1040]
MP_X = [-1450, -1060, -680]
for j, y in enumerate(MP_Y):
    strip("CT.mp_ew%d" % j, [(-1455, y), (-675, y)], 10, M["r_street"], 0.02)
for i, x in enumerate(MP_X):
    strip("CT.mp_ns%d" % i, [(x, -500), (x, -1180)], 10, M["r_street"], 0.021)
strip("CT.mp_link_dt", [(-680, -750), (-500, -750)], 12, M["r_street"], 0.021)
strip("CT.mp_link_north", [(-680, -500), (-680, AV_Y)], 12, M["r_street"], 0.021)
strip("CT.mp_link_west", [(-1455, -500), (-1455, -440), (-1250, AV_Y)], 12, M["r_street"], 0.021)
# airport roads
strip("CT.terminal_frontage", [(2700, -2575), (3950, -2575)], 22, M["r_avenue"], 0.035)
strip("CT.carpark", [(3020, -2470), (3600, -2470)], 90, M["r_parking"], 0.03)

# ================================================================ SKYHAVEN HEIGHTS
use(C["CT_Heights"])
# mansion gate and boundary wall
gw = P("CT.mansion_wall")
for x0, x1 in ((-62, 6.0), (14.0, 62)):
    gw.box(x0, x1, -58.6, -58.0, 0.0, 2.2, "white_c")
    gw.box(x0, x1, -58.8, -57.8, 2.2, 2.45, "white_c")
for x in (-62, 62):
    gw.box(x - 0.3, x + 0.3, -58.6, 62, 0.0, 2.2, "white_c")
for x in (5.2, 14.8):
    gw.box(x - 0.8, x + 0.8, -59.0, -57.6, 0.0, 3.2, "stone2")
    gw.box(x - 0.9, x + 0.9, -59.1, -57.5, 3.2, 3.45, "white_c")
for k in range(16):
    x = 6.2 + k * 0.5
    gw.box(x - 0.04, x + 0.04, -58.35, -58.25, 0.1, 2.3, "frame")
gw.box(6.0, 14.0, -58.4, -58.2, 2.2, 2.35, "frame")
gw.box(6.0, 14.0, -58.4, -58.2, 1.0, 1.1, "frame")
gw.done(outline=0.03)
label("CT.mansion_number", "7", (5.2, -59.15, 2.6), 0, 0.6, M["frame"], 0.05)


def villa(name, x, y, rot, variant):
    v = P(name)
    w = 22 + variant * 3
    v.box(-w / 2, w / 2, -6, 8, 0, 3.4, "white_c")
    v.box(-w / 2 + 1, w / 2 - 1, -6.1, -5.9, 0.6, 2.9, "glass_c")
    v.box(-w / 2 - 1.5, w / 2 + 1.5, -8, 9, 3.4, 4.0, "white_c")
    off = (-4, 3, -2)[variant % 3]
    v.box(off - 7, off + 7, -4, 7, 4.0, 7.2, ("wall_e", "wood", "beige")[variant % 3])
    v.box(off - 6.5, off + 6.5, -4.1, -3.9, 4.6, 6.7, "glass_c")
    v.box(off - 8.5, off + 8.5, -6, 8.5, 7.2, 7.8, "white_c")
    v.box(-w / 2 + 2, -w / 2 + 14, -22, -12, -0.6, 0.05, "pool")
    v.box(-w / 2 + 1, -w / 2 + 15, -23, -11, -0.05, 0.02, "pave")
    v.box(w / 2 - 6, w / 2 - 1, -40, -8, 0.0, 0.04, "pave")
    for xx in (-w / 2 - 8, w / 2 + 8):
        v.box(xx - 0.3, xx + 0.3, -40, 20, 0.0, 1.6, "white_c")
    v.box(-w / 2 - 8, w / 2 - 6.5, -40.3, -39.7, 0.0, 1.6, "white_c")
    v.box(w / 2 - 0.5, w / 2 + 8, -40.3, -39.7, 0.0, 1.6, "white_c")
    return v.done((x, y, 0), rot, outline=0.06)


for i, x in enumerate((-1120, -780, -620, -460, -300, -150, 150, 300, 460, 620, 780)):
    if -1150 < x < -950:
        continue
    villa("CT.villa%d" % i, x, -18, 0, i)
    tree_at(x - 18, -36, PALM)
    tree_at(x + 18, -36, PALM)
    tree_at(x + random.uniform(-15, 15), 15, None)
for x in range(-1200, 1300, 36):
    if not (-70 < x < 70):
        tree_at(x + random.uniform(-3, 3), AV_Y - 13, PALM, 0.9)
        if not (-760 < x < 920):
            tree_at(x + 18, AV_Y + 13, PALM, 0.9)

# Skyhaven Galleria (upscale mall, west end of the avenue)
gal = P("CT.galleria")
bx(gal, (-1050, 40), (190, 90, 16), "f_shop")
bx(gal, (-1050, 40), (198, 96, 1.2), "white_c", 16)
gal.blob((-1050, 40, 16), (40, 30, 14), "fountain", subdiv=2)
bx(gal, (-1050, -8), (60, 8, 0.8), "white_c", 6)
for x in (-1078, -1022):
    bx(gal, (x, -10), (1.2, 1.2, 6), "white_c")
gal.done(outline=0.12)
strip("CT.galleria_parking", [(-1140, -30), (-960, -30)], 22, M["r_parking"], 0.03)
label("CT.galleria_sign", "SKYHAVEN GALLERIA", (-1050, -12.4, 8.8), 0, 3.2, M["frame"], 0.3)
# Heights Academy (international school, east end)
ac = P("CT.heights_academy")
bx(ac, (1050, 70), (160, 24, 14), "f_school2")
bx(ac, (985, 115), (30, 70, 14), "f_school2")
bx(ac, (1115, 115), (30, 70, 14), "f_school2")
bx(ac, (1050, 70), (168, 28, 1.0), "white_c", 14)
bx(ac, (1050, 55), (30, 8, 18), "white_c")
bx(ac, (1050, 270), (150, 100, 0.06), "grass2")
ac.box(975, 1125, 228, 312, 0.06, 0.08, "track")
ac.box(985, 1115, 236, 304, 0.08, 0.1, "grass2")
bx(ac, (1050, 165), (40, 18, 0.1), "court")
ac.done(outline=0.1)
label("CT.academy_sign", "HEIGHTS ACADEMY", (1050, 50.6, 15.0), 0, 2.6, M["door_blue"], 0.3)

# ================================================================ DOWNTOWN
use(C["CT_Downtown"])
dtp = P("CT.downtown_pavement")
dtp.box(DX[0] - 20, DX[-1] + 20, DY[-1] - 20, DY[0] + 20, -0.06, 0.012, "pave")
dtp.done(outline=0)
STY = ("glass_blue", "glass_teal", "glass_dark", "office", "stone", "glass_blue", "office")
for i in range(len(DX) - 1):
    for j in range(len(DY) - 1):
        x0, x1 = DX[i] + 12, DX[i + 1] - 12
        y1, y0 = DY[j] - 12, DY[j + 1] + 12
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        name = "CT.block_%d_%d" % (i, j)
        if (i, j) == (4, 2):                       # central park
            pk = P("CT.central_park")
            pk.box(x0, x1, y0, y1, 0.0, 0.08, "grass2")
            pk.cyl((cx, cy, 0.3), 14, 0.6, "white_c", segs=32)
            pk.cyl((cx, cy, 0.55), 12, 0.2, "fountain", segs=32)
            pk.cyl((cx, cy, 2.0), 1.2, 4.0, "white_c", segs=16)
            for a in range(4):
                pk.beam((cx, cy, 0.1), (cx + math.cos(a * math.pi / 2) * (x1 - x0) / 2,
                                         cy + math.sin(a * math.pi / 2) * (y1 - y0) / 2, 0.1), 5, 0.06, "pave")
            pk.done(outline=0.05)
            for k in range(22):
                tree_at(random.uniform(x0 + 6, x1 - 6), random.uniform(y0 + 6, y1 - 6))
            continue
        if (i, j) == (5, 2):                       # Skyhaven Tower
            t = P("CT.skyhaven_tower")
            for k, (w, h0, h1) in enumerate(((70, 0, 120), (56, 120, 220), (42, 220, 300), (26, 300, 330))):
                t.box(cx - w / 2, cx + w / 2, cy - w / 2, cy + w / 2, h0, h1, "f_glass_teal")
                t.box(cx - w / 2 - 1, cx + w / 2 + 1, cy - w / 2 - 1, cy + w / 2 + 1, h1 - 1, h1, "white_c")
            t.cyl((cx, cy, 360), 1.2, 60, "metal", segs=8)
            t.blob((cx, cy, 391), (2.2, 2.2, 2.2), "red_cross")
            t.done(outline=0.25)
            label("CT.tower_sign", "SKYHAVEN", (cx, cy - 36, 108), 0, 9, M["white_c"], 0.6)
            continue
        b = P(name)
        n = random.choice((1, 2, 2, 3, 4))
        heights = 40 + 160 * (1.0 - min(1.0, (abs(cx - 250) + abs(cy + 975)) / 900)) ** 1.5
        if n == 1:
            parts = [(cx, cy, x1 - x0 - 10, y1 - y0 - 10)]
        elif n == 2:
            parts = [(cx - (x1 - x0) / 4, cy, (x1 - x0) / 2 - 8, y1 - y0 - 10),
                     (cx + (x1 - x0) / 4, cy, (x1 - x0) / 2 - 8, y1 - y0 - 10)]
        else:
            parts = [(cx + sx * (x1 - x0) / 4, cy + sy * (y1 - y0) / 4, (x1 - x0) / 2 - 8, (y1 - y0) / 2 - 8)
                     for sx in (-1, 1) for sy in (-1, 1)][:n]
        for (px, py, w, d) in parts:
            h = max(18, heights * random.uniform(0.45, 1.15))
            st = random.choice(STY)
            if h > 90 and random.random() < 0.6:
                b.box(px - w / 2, px + w / 2, py - d / 2, py + d / 2, 0, h * 0.62, "f_" + st)
                b.box(px - w / 2.7, px + w / 2.7, py - d / 2.7, py + d / 2.7, h * 0.62, h, "f_" + st)
                b.box(px - w / 2.7 - 0.6, px + w / 2.7 + 0.6, py - d / 2.7 - 0.6, py + d / 2.7 + 0.6, h, h + 2.5, "white_c")
            else:
                b.box(px - w / 2, px + w / 2, py - d / 2, py + d / 2, 0, h, "f_" + st)
                b.box(px - w / 2 - 0.6, px + w / 2 + 0.6, py - d / 2 - 0.6, py + d / 2 + 0.6, h, h + 1.8, "white_c")
                if random.random() < 0.5:
                    b.box(px - 4, px + 4, py - 4, py + 4, h + 1.8, h + 6, "roof_flat")
        b.done(outline=0.15)
for x in DX:
    for y in range(DY[-1], DY[0], 30):
        if random.random() < 0.5:
            tree_at(x + 13, y + 15, TREE_A, 0.7)

# ================================================================ CIVIC: hospital, fire, police
use(C["CT_Civic"])
h = P("CT.hospital")
bx(h, (1110, -760), (150, 40, 26), "f_hospital")
bx(h, (1045, -705), (40, 70, 34), "f_hospital")
bx(h, (1175, -705), (40, 70, 34), "f_hospital")
bx(h, (1110, -700), (60, 40, 46), "f_hospital")
bx(h, (1110, -700), (62, 42, 1.0), "white_c", 46)
h.cyl((1110, -700, 47.2), 15, 0.4, "helipad", segs=40)
h.cyl((1110, -700, 47.45), 13.5, 0.1, "white_c", segs=40)
h.cyl((1110, -700, 47.5), 12.8, 0.1, "helipad", segs=40)
bx(h, (1110, -790), (40, 14, 0.8), "red_cross", 5.0)
for x in (1092, 1128):
    bx(h, (x, -796), (1.0, 1.0, 5.0), "white_c")
h.box(1102, 1118, -781.2, -780.6, 30, 40, "red_cross")
h.box(1105, 1115, -781.2, -780.6, 26.0, 44.0, "red_cross")
h.done(outline=0.15)
label("CT.hospital_H", "H", (1110, -700, 47.62), 0, 14, M["white_c"], 0.05, upright=False)
label("CT.hospital_sign", "SKYHAVEN GENERAL HOSPITAL", (1110, -780.8, 22.5), 0, 3.6, M["red_cross"], 0.3)
strip("CT.hospital_parking", [(1010, -830), (1210, -830)], 40, M["r_parking"], 0.03)
fs = P("CT.fire_station")
bx(fs, (1040, -1010), (70, 26, 11), "f_brick")
for k in range(3):
    fs.box(1012 + k * 20, 1028 + k * 20, -1023.2, -1022.8, 0.0, 7.0, "fire_red")
bx(fs, (1075, -1000), (10, 10, 20), "f_brick")
fs.done(outline=0.1)
label("CT.fire_sign", "FIRE STATION 1", (1040, -1023.6, 9.0), 0, 2.2, M["white_c"], 0.2)
pol = P("CT.police")
bx(pol, (1150, -1120), (80, 30, 14), "f_office")
pol.box(1130, 1170, -1135.3, -1134.9, 0.0, 4.5, "police")
pol.done(outline=0.1)
label("CT.police_sign", "POLICE", (1150, -1135.6, 10.5), 0, 3.0, M["police"], 0.25)

# ================================================================ MAPLE PARK (middle class)
use(C["CT_MaplePark"])
HOUSES = []
H_STY = [("wall_a", "roof_red", "door_blue"), ("wall_b", "roof_grey", "door_red"), ("wall_c", "roof_brown", "door_green"),
         ("wall_d", "roof_red", "door_blue"), ("wall_e", "roof_grey", "door_green"), ("wall_b", "roof_brown", "door_red")]


def house_piece(name, wall, roof, door, garage):
    p = P(name)
    w, d, hh = 9.0, 8.0, 3.0
    p.box(-w / 2, w / 2, -d / 2, d / 2, 0, hh * 2, wall)
    # gable roof (ridge along X)
    t = bmesh.new()
    vs = [t.verts.new(v) for v in ((-w / 2 - 0.5, -d / 2 - 0.6, hh * 2), (w / 2 + 0.5, -d / 2 - 0.6, hh * 2),
                                   (w / 2 + 0.5, d / 2 + 0.6, hh * 2), (-w / 2 - 0.5, d / 2 + 0.6, hh * 2),
                                   (-w / 2 - 0.5, 0, hh * 2 + 3.2), (w / 2 + 0.5, 0, hh * 2 + 3.2))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)):
        t.faces.new([vs[i] for i in f])
    p._merge(t, roof, False)
    p.box(-0.6, 0.6, -d / 2 - 0.05, -d / 2, 0, 2.2, door)
    for x in (-3.0, 2.8):
        p.box(x - 0.8, x + 0.8, -d / 2 - 0.05, -d / 2, 0.9, 2.2, "win")
        p.box(x - 0.8, x + 0.8, -d / 2 - 0.05, -d / 2, 3.9, 5.1, "win")
    p.box(-0.8, 0.8, -d / 2 - 0.05, -d / 2, 3.9, 5.1, "win")
    p.box(-1.2, 1.2, -d / 2 - 1.4, -d / 2, 2.5, 2.7, "white_c")             # porch roof
    if garage:
        p.box(w / 2, w / 2 + 4.5, -d / 2, d / 2 - 1, 0, 3.0, wall)
        p.box(w / 2 + 0.4, w / 2 + 4.1, -d / 2 - 0.05, -d / 2, 0, 2.5, "white_c")
        p.box(w / 2 - 0.2, w / 2 + 4.7, -d / 2 - 0.2, d / 2 - 0.8, 3.0, 3.3, roof)
        p.box(w / 2 + 0.3, w / 2 + 4.2, -14, -d / 2, 0.0, 0.05, "pave")
    p.box(-0.7, 0.7, -14, -d / 2, 0.0, 0.05, "pave")                         # front path
    for xx in (-8.5, 8.5):                                                   # low hedge fence line
        p.box(xx - 0.25, xx + 0.25, -11, 4, 0.0, 0.6, "leaf_a")
    return template(p, name, outline=0.05)


H_T = [house_piece("CT.house_t%d" % i, *H_STY[i], garage=(i % 2 == 0)) for i in range(6)]
F2 = house_piece("CT.house_family2_t", "wall_f", "roof_grey", "door_blue", True)
F2_POS = (-996, -800 + 22, 0)
n = 0
for y in MP_Y:
    for side in (1, -1):
        if y == MP_Y[-1] and side == -1:
            continue
        x = -1428.0
        while x < -700:
            if abs(x - (-1060)) < 18:
                x += 24
                continue
            pos = (x, y + side * 22, 0)
            rot = 0 if side == 1 else 180
            if abs(pos[0] - F2_POS[0]) < 2 and abs(pos[1] - F2_POS[1]) < 2:
                dup(F2, "CT.family2_home", pos, rot, merge=False)
                tree_at(x - 6, y + side * 34, TREE_A, 1.1)
            else:
                HOUSES.append(dup(random.choice(H_T), "CT.house", pos, rot))
                if random.random() < 0.55:
                    tree_at(x + random.uniform(-5, 5), y + side * random.uniform(30, 36), None, random.uniform(0.7, 1.0))
            n += 1
            x += 24
# make sure the family-2 home exists even if the grid moves
if not bpy.data.objects.get("CT.family2_home"):
    dup(F2, "CT.family2_home", F2_POS, 0, merge=False)
label("CT.family2_mailbox", "12", (F2_POS[0] + 2.5, F2_POS[1] - 13.5, 1.4), 0, 0.5, M["door_blue"], 0.04)
# Maple Park Primary
sc = P("CT.maple_primary")
bx(sc, (-1545, -720), (110, 20, 10), "f_school")
bx(sc, (-1590, -770), (20, 80, 10), "f_school")
bx(sc, (-1545, -720), (114, 24, 0.8), "white_c", 10)
bx(sc, (-1545, -705), (24, 6, 12), "white_c")
bx(sc, (-1540, -900), (130, 90, 0.06), "grass2")
sc.box(-1600, -1480, -940, -860, 0.06, 0.08, "track")
sc.box(-1592, -1488, -932, -868, 0.08, 0.1, "grass2")
bx(sc, (-1500, -800), (40, 30, 0.08), "court")
for k in range(4):                                                           # playground
    sc.cyl((-1600 + k * 8, -820, 1.2), 0.15, 2.4, "slide", segs=6)
sc.box(-1606, -1574, -823, -817, 2.4, 2.6, "slide")
sc.done(outline=0.1)
label("CT.maple_primary_sign", "MAPLE PARK PRIMARY", (-1545, -702.8, 10.8), 0, 2.4, M["door_blue"], 0.25)
bus = P("CT.school_bus_t")
bus.box(-1.3, 1.3, -6, 6, 0.5, 3.2, "yellow")
bus.box(-1.32, 1.32, -5.5, 4.5, 2.0, 2.8, "glass_c")
bus.box(-1.3, 1.3, -6, -4.6, 0.5, 2.0, "yellow")
for sy in (-4, 4):
    for sx in (-1.2, 1.2):
        bus.cyl((sx, sy, 0.5), 0.5, 0.3, "tyre_c", axis='X', segs=12)
BUS = template(bus, "CT.school_bus_t", outline=0.03)
for i, x in enumerate((-1520, -1505)):
    dup(BUS, "CT.school_bus%d" % i, (x, -695, 0), 90, merge=False)
dup(BUS, "CT.academy_bus", (1020, 40, 0), 90, coll=C["CT_Heights"], merge=False)
# supermarket and petrol station
sm = P("CT.supermarket")
bx(sm, (-1545, -580), (100, 50, 9), "f_shop")
bx(sm, (-1545, -580), (104, 54, 1.0), "door_green", 9)
bx(sm, (-1545, -606), (40, 3, 1.6), "door_green", 6.5)
sm.done(outline=0.1)
strip("CT.supermarket_parking", [(-1600, -625), (-1490, -625)], 28, M["r_parking"], 0.03)
label("CT.supermarket_sign", "FRESH MART", (-1545, -607.8, 8.0), 0, 2.4, M["white_c"], 0.2)
ps = P("CT.petrol_station")
bx(ps, (-640, -470), (30, 18, 0.6), "white_c", 5.0)
for x in (-650, -630):
    bx(ps, (x, -470), (1.0, 1.0, 5.0), "door_red")
    bx(ps, (x, -465), (1.6, 0.8, 1.6), "car_s")
bx(ps, (-640, -440), (20, 12, 4), "f_shop")
bx(ps, (-610, -470), (1.0, 1.0, 9), "door_red")
bx(ps, (-610, -470), (5, 0.6, 3), "door_red", 9)
ps.box(-655, -625, -480, -460, 0.0, 0.03, "pave")
ps.done(outline=0.06)
# park, playground, apartments
pk = P("CT.maple_park")
pk.box(-1440, -1080, -1170, -1060, 0.0, 0.07, "grass2")
pk.blob((-1260, -1115, 0.05), (40, 22, 0.05), "water", subdiv=2)
for k in range(3):
    x = -1380 + k * 12
    pk.box(x - 4, x + 4, -1090, -1088, 2.4, 2.6, "bench")
    for sx in (-4, 4):
        pk.beam((x + sx, -1093, 0), (x + sx, -1089, 2.6), 0.2, 0.2, "bench")
        pk.beam((x + sx, -1085, 0), (x + sx, -1089, 2.6), 0.2, 0.2, "bench")
pk.box(-1352, -1344, -1100, -1080, 0.0, 0.12, "sand2")
pk.beam((-1340, -1100, 3), (-1330, -1100, 0.2), 1.0, 0.15, "slide")
pk.box(-1342, -1338, -1101, -1099, 0, 3.0, "door_blue")
pk.done(outline=0.04)
for k in range(30):
    tree_at(random.uniform(-1430, -1090), random.uniform(-1165, -1065))
for i, x in enumerate((-1010, -920, -830, -740)):
    hgt = random.choice((18, 21, 24))
    a = P("CT.apartments%d" % i)
    bx(a, (x, -1120), (60, 22, hgt), "f_apart" if i % 2 == 0 else "f_apart2")
    bx(a, (x, -1120), (62, 24, 0.8), "white_c", hgt)
    for k in range(int(hgt // 3) - 1):
        a.box(x - 26, x + 26, -1131.6, -1131.0, 3 * (k + 1) - 0.1, 3 * (k + 1) + 0.15, "white_c")
    a.done(outline=0.08)

# ================================================================ AIRPORT
use(C["CT_Airport"])
apt = P("CT.airport_ground")
apt.box(1950, 5100, -3560, -2600, -0.06, 0.005, "grass2")
apt.box(2740, 3860, -2885, -2700, 0.0, 0.03, "apron")
for x in (2900, 3300, 3700):
    apt.box(x - 12, x + 12, -2960, -2885, 0.0, 0.03, "apron")
apt.done(outline=0)
strip("CT.runway_1", [(2000, -3050), (5000, -3050)], 60, M["r_runway"], 0.04)
strip("CT.runway_2", [(2000, -3400), (5000, -3400)], 60, M["r_runway"], 0.04)
strip("CT.taxiway_a", [(2000, -2950), (5000, -2950)], 23, M["r_taxi"], 0.035)
strip("CT.taxiway_b", [(2000, -3250), (5000, -3250)], 23, M["r_taxi"], 0.035)
for i, x in enumerate((2030, 3500, 4970)):
    strip("CT.taxi_link_%d" % i, [(x, -2950), (x, -3400)], 23, M["r_taxi"], 0.036)
# runway threshold bars and numbers
th = P("CT.runway_marks")
for ry in (-3050, -3400):
    for x0 in (2010, 4950):
        for k in range(8):
            y = ry - 24 + k * 6.6
            th.box(x0, x0 + 40, y, y + 3, 0.045, 0.06, "white_c")
th.done(outline=0)
label("CT.rwy_09L", "09L", (2080, -3050, 0.07), 90, 16, M["white_c"], 0.02, upright=False)
label("CT.rwy_09R", "09R", (2080, -3400, 0.07), 90, 16, M["white_c"], 0.02, upright=False)
# terminal
tm = P("CT.terminal")
tm.box(2800, 3800, -2700, -2610, 0, 22, "f_terminal")
tm.blob((3300, -2655, 21), (520, 47, 9), "white_c", subdiv=3)
tm.box(2780, 3820, -2602, -2590, 9.0, 9.8, "white_c")                    # departures canopy
for x in range(2800, 3801, 50):
    tm.box(x - 0.6, x + 0.6, -2596, -2594, 0, 9.0, "white_c")
tm.done(outline=0.2)
label("CT.terminal_sign", "SKYHAVEN INTERNATIONAL", (3300, -2611.5, 15.5), 0, 7.5, M["door_blue"], 0.5)
# control tower
ct = P("CT.control_tower")
ct.cyl((3960, -2650, 30), 5, 60, "white_c", segs=20)
ct.cyl((3960, -2650, 61), 9, 2, "white_c", segs=20)
ct.cyl((3960, -2650, 65), 9.5, 6, "tower_cab", r2=11, segs=16)
ct.cyl((3960, -2650, 69), 11.5, 1.6, "white_c", segs=16)
ct.cyl((3960, -2650, 74), 0.4, 8, "metal", segs=6)
ct.done(outline=0.12)
# hangars
for i, x in enumerate((4250, 4420, 4590)):
    hg = P("CT.hangar%d" % i)
    hg.cyl((x, -2690, 0), 60, 140, "f_hangar", axis='Y', segs=24)
    hg.box(x - 45, x + 45, -2761, -2760, 0, 24, "metal")
    hg.done(outline=0.15)
# multi-storey car park
cp = P("CT.carpark_building")
for k in range(4):
    cp.box(3050, 3550, -2520, -2420, k * 4.0, k * 4.0 + 0.6, "concrete2")
    for x in range(3050, 3551, 50):
        cp.box(x - 0.6, x + 0.6, -2520, -2419, k * 4.0, k * 4.0 + 4.0, "concrete2")
cp.done(outline=0.08)


# airliner (template): nose toward -Y, about 45 m long, Skyhaven Air livery
def airliner(name, tail="teal"):
    a = P(name)
    a.cyl((0, 0, 4.5), 2.9, 36, "plane", axis='Y', segs=20)
    a.blob((0, -18, 4.5), (2.9, 5.0, 2.9), "plane")
    a.cyl((0, 22.5, 5.1), 2.9, 9, "plane", axis='Y', segs=20, r2=0.7)
    a.box(-2.92, 2.92, -14, 16, 5.2, 5.6, "glass_c")                       # window line
    a.box(-2.95, 2.95, -17, 18, 3.4, 3.9, tail)                            # cheat line
    a.box(-1.6, 1.6, -21.8, -20.6, 5.0, 6.0, "glass_c")                   # cockpit
    for sx in (-1, 1):
        a.beam((sx * 2.0, -2, 3.2), (sx * 18.5, 7.5, 4.4), 5.5, 0.55, "plane")  # wing
        a.beam((sx * 1.0, 23, 5.6), (sx * 7.0, 26, 6.0), 2.6, 0.35, "plane")    # tailplane
        a.cyl((sx * 7.5, -2.5, 2.2), 1.3, 5.0, "plane_belly", axis='Y', segs=16)
        a.cyl((sx * 7.5, -5.0, 2.2), 1.05, 0.3, "glass_c", axis='Y', segs=16)
        a.cyl((sx * 2.0, 3.0, 0.9), 0.55, 0.5, "tyre_c", axis='X', segs=12)
        a.beam((sx * 2.0, 3.0, 1.3), (sx * 2.0, 3.0, 3.0), 0.25, 0.25, "metal")
    a.cyl((0, -15, 0.9), 0.5, 0.4, "tyre_c", axis='X', segs=12)
    a.beam((0, -15, 1.2), (0, -15, 2.5), 0.2, 0.2, "metal")
    a.beam((0, 19, 6.5), (0, 26.5, 14.0), 5.5, 0.45, tail)                  # fin
    a.box(-2.9, 2.9, -16, 16, 1.6, 3.4, "plane_belly", taper=(0.7, 1.0))
    return template(a, name, outline=0.06)


JET = airliner("CT.jet_t", "teal")
JET2 = airliner("CT.jet2_t", "door_red")
for i, x in enumerate(range(2900, 3701, 160)):
    dup(random.choice((JET, JET, JET2)), "CT.jet_gate%d" % i, (x, -2775, 0), 180, merge=False)
    jb = P("CT.jet_bridge%d" % i)
    jb.beam((x - 14, -2700, 5.0), (x - 4.5, -2748, 5.0), 3.0, 3.0, "metal")
    jb.box(x - 15, x - 13, -2722, -2720, 0, 4.0, "metal")
    jb.done(outline=0.05)
dup(JET, "CT.jet_taxi", (2600, -2950, 0), 90, merge=False)
take = dup(JET2, "CT.jet_takeoff", (4300, -3050, 9), 90, merge=False)
take.rotation_euler.x = math.radians(-8)
land = dup(JET, "CT.jet_landing", (1500, -3400, 110), -90, merge=False)
land.rotation_euler.x = math.radians(-3)
# apron service vehicles
sv = P("CT.service_t")
sv.box(-1.2, 1.2, -2.5, 2.5, 0.4, 2.2, "yellow")
sv.cyl((0, -1.5, 0.4), 0.4, 2.6, "tyre_c", axis='X', segs=10)
sv.cyl((0, 1.5, 0.4), 0.4, 2.6, "tyre_c", axis='X', segs=10)
SV = template(sv, "CT.service_t", outline=0.03)
for i in range(10):
    dup(SV, "CT.service%d" % i, (random.uniform(2780, 3820), random.uniform(-2840, -2720), 0), random.uniform(0, 360))

# airport sign gantry over the Skyway
use(C["CT_Roads"])
sg = P("CT.airport_gantry")
for x in (1345, 1375):
    sg.box(x - 0.4, x + 0.4, -1000.4, -999.6, 0, 9, "metal")
sg.box(1344, 1376, -1000.5, -999.5, 7.5, 8.2, "metal")
sg.box(1350, 1370, -1000.7, -1000.3, 5.0, 9.0, "sign_green")
sg.done(outline=0.04)
label("CT.airport_sign", "AIRPORT  >>", (1360, -999.0, 7.0), 180, 1.6, M["sign_text"], 0.05)

# ================================================================ TRAFFIC
use(C["CT_Traffic"])
CARS = []
for k, col in enumerate(("car_r", "car_b", "car_w", "car_k", "car_y", "car_s")):
    c = P("CT.car_t%d" % k)
    c.box(-0.95, 0.95, -2.3, 2.3, 0.35, 1.05, col)
    c.box(-0.85, 0.85, -1.0, 1.1, 1.05, 1.55, "glass_c", taper=(0.9, 0.75))
    c.box(-0.75, 0.75, -0.7, 0.9, 1.53, 1.6, col)
    for sy in (-1.45, 1.45):
        c.cyl((0, sy, 0.35), 0.34, 2.0, "tyre_c", axis='X', segs=10)
    CARS.append(template(c, "CT.car_t%d" % k, outline=0.02))


def traffic(pts, width, n, lanes=2, allowed=None):
    """Parked-looking traffic; `allowed` lanes keep Ace's driving lane clear (see build_airport_drive)."""
    segs = [(Vector(a), Vector(b)) for a, b in zip(pts, pts[1:])]
    total = sum((b - a).length for a, b in segs)
    for i in range(n):
        s = random.uniform(0, total)
        for a, b in segs:
            L = (b - a).length
            if s <= L:
                d = (b - a).normalized()
                lane = random.choice(allowed or list(range(lanes)))
                side = 1 if lane < lanes / 2 else -1
                off = (width / 2) * (0.25 + 0.5 * (lane % (lanes // 2 or 1)) / max(1, lanes // 2)) * side
                p = a + d * s + Vector((-d.y, d.x)) * -off
                # car local front is -Y; heading rotates -Y onto the travel direction
                heading = math.degrees(math.atan2(-d.x * side, d.y * side)) + 180
                dup(random.choice(CARS), "CT.car", (p.x, p.y, 0.03), heading)
                break
            s -= L


traffic(SKYWAY, 28, 120, 4, allowed=[0, 2, 3])
traffic([(-1250, AV_Y), (1300, AV_Y)], 16, 60, allowed=[1])
traffic(BOUL, 18, 25)
for x in DX:
    traffic([(x, DY[0]), (x, DY[-1])], 18, 6)
for y in DY:
    traffic([(DX[0], y), (DX[-1], y)], 18, 8)
for y in MP_Y:
    traffic([(-1450, y), (-680, y)], 10, 5)
traffic([(2700, -2575), (3950, -2575)], 22, 30, 4, allowed=[0, 2, 3])
# parked cars
for k in range(140):
    dup(random.choice(CARS), "CT.car_parked", (random.uniform(3060, 3590), random.uniform(-2505, -2435), 0.03),
        random.choice((0, 180)))
for k in range(30):
    dup(random.choice(CARS), "CT.car_parked", (random.uniform(-1595, -1495), random.uniform(-635, -615), 0.03),
        random.choice((0, 180)))
for k in range(28):
    dup(random.choice(CARS), "CT.car_parked", (random.uniform(1015, 1205), random.uniform(-845, -815), 0.03),
        random.choice((0, 180)))
# ambulance and fire engine
amb = P("CT.ambulance")
amb.box(1100, 1102.2, -800, -794, 0.4, 3.0, "white_c")
amb.box(1100, 1102.2, -800, -799.5, 1.4, 1.9, "red_cross")
amb.box(1100.6, 1101.6, -797.5, -797, 3.0, 3.25, "door_blue")
amb.done(outline=0.03)
fe = P("CT.fire_engine")
fe.box(1010, 1012.5, -1036, -1026, 0.4, 3.2, "fire_red")
fe.box(1010.2, 1012.3, -1036.2, -1033, 1.8, 2.8, "glass_c")
fe.box(1010.5, 1012, -1032, -1026, 3.2, 3.5, "metal")
fe.done(outline=0.03)

flush_batches()
SKIP = ("CT.jet_", "CT.school_bus", "CT.academy_bus", "CT.family2_home", "CT.mansion")
for cn in ("CT_Ground", "CT_Roads", "CT_Heights", "CT_Downtown", "CT_Civic", "CT_MaplePark", "CT_Airport",
           "CT_Nature", "CT_Traffic"):
    K.PARENT[0] = RIG
    consolidate(C[cn], SKIP)

# ================================================================ link the mansion
use(C["CT_Heights"])
if MANSION and os.path.exists(MANSION):
    with bpy.data.libraries.load(MANSION, link=True) as (src, dst):
        dst.collections = ["Mansion"]
    mc = dst.collections[0]
    inst = bpy.data.objects.new("CT.mansion", None)
    inst.instance_type = 'COLLECTION'
    inst.instance_collection = mc
    C["CT_Heights"].objects.link(inst)

# ================================================================ light, world, cameras
use(C["CT_Cams"])
w = bpy.data.worlds.new("CT_world")
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs[0].default_value = lin("#c6dbea") + [1]
bg.inputs[1].default_value = 0.9
S.world = w
sun = bpy.data.lights.new("CT_sun", 'SUN')
sun.energy = 3.6
sun.color = lin("#fff1dc")
sun.angle = math.radians(2)
so = bpy.data.objects.new("CT_sun", sun)
C["CT_Cams"].objects.link(so)
so.rotation_euler = (-Vector((0.55, 0.62, -0.56)).normalized()).to_track_quat('Z', 'Y').to_euler()


def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 1.0
    cd.clip_end = 16000
    co = bpy.data.objects.new(name, cd)
    C["CT_Cams"].objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


S.camera = cam("CT_cam_overview", (-2600, 1400, 2300), (900, -1500, 0), 26)
cam("CT_cam_heights", (-60, -78, 6), (300, -50, 6), 24)
cam("CT_cam_mansion_city", (-70, 85, 34), (25, -260, -10), 24)
cam("CT_cam_skyway", (1352, -1250, 4.5), (1400, -1700, 2), 30)
cam("CT_cam_airport", (2500, -2420, 160), (3400, -2900, 0), 30)
cam("CT_cam_terminal", (3000, -2560, 8), (3500, -2650, 14), 26)
cam("CT_cam_downtown", (95, -660, 6), (300, -1000, 110), 22)
cam("CT_cam_hospital", (1240, -900, 14), (1110, -735, 20), 26)
cam("CT_cam_maple_street", (-1240, -667, 3.0), (-1000, -695, 3), 26)
cam("CT_cam_family2", (-978, -800, 3.0), (-996, -776, 4.0), 28)
cam("CT_cam_schools", (-1420, -650, 40), (-1560, -800, 0), 28)
cam("CT_cam_galleria", (-1010, -95, 5), (-1060, 0, 10), 26)

S.render.engine = 'BLENDER_EEVEE'
S.eevee.taa_render_samples = 16
S.view_settings.view_transform = 'Standard'
S.render.resolution_x, S.render.resolution_y = 1920, 1080
S.render.fps = 24

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    if MANSION:
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_mainfile()

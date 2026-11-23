"""Furnished rooms inside the family's mansion.

    blender -b blender/sets/mansion_v001.blend --python tools/blender/build_mansion_interior.py -- <out.blend>

Adds a top-level collection "Mansion_Interior" laid out on the same plan as the
exterior (same real-metre coordinates under MN.root, scaled to the characters):

  ground floor  living room (left wing), kitchen + dining (middle),
                entrance hall with floating stair and stone feature wall (right)
  first floor   main bedroom (wood wing), Max's nursery (opens onto the terrace),
                landing behind the lattice screen with a spiral stair
  top floor     Ace's drone workshop (opens onto the big cantilevered terrace)

The interior is a set: walls, floors and ceilings with real door and window
openings, but no exterior skin. Two view layers: "Exterior" (house, grounds,
car) and "Interior" (rooms and their lights). Interior cameras are MNI_cam_*.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(11)
S = bpy.context.scene
RIG = bpy.data.objects["MN.root"]
K.PARENT[0] = RIG

old = bpy.data.collections.get("Mansion_Interior")
if old:
    for o in list(old.all_objects):
        if o is not RIG:
            bpy.data.objects.remove(o)
    for c in list(old.children_recursive):
        bpy.data.collections.remove(c)
    bpy.data.collections.remove(old)
IROOT = bpy.data.collections.new("Mansion_Interior")
S.collection.children.link(IROOT)
IROOT.objects.link(RIG)                    # the scale root lives in both collections
IC = {}
for n in ("MNI_Ground", "MNI_First", "MNI_Top", "MNI_Lights", "MNI_Cams"):
    c = bpy.data.collections.new(n)
    IROOT.children.link(c)
    IC[n] = c

# ---------------------------------------------------------------- materials
for k, v in {
    "wall": "#f3ede3", "ceiling": "#f8f5ef", "skirting": "#e2d9ca", "oak": "#c99d6e", "oak_dk": "#a87d52",
    "tile": "#e6dfd2", "tile_ln": "#cfc6b6", "marble": "#efebe4", "marble_ln": "#d9d2c6", "carpet": "#e9e3f0",
    "concrete": "#b4afa7", "sage": "#a9bf9f", "dusty": "#9fb4c8", "skyblue": "#bcd8ec", "cloud": "#fbfbfb",
    "terracotta": "#c96f53", "navy": "#3d4a63", "mustard": "#e0a43c", "cream": "#f4ecdc", "linen": "#e9e1d2",
    "sofa": "#7d8f86", "cushion": "#e7c59a", "steel": "#cfd4d8", "black": "#2e2e33", "screen": "#29313b",
    "book1": "#c8463a", "book2": "#3d6f8f", "book3": "#e0a43c", "book4": "#6a8f4f", "book5": "#8a5a8f",
    "duvet": "#f6f3ee", "throw": "#c96f53", "pillow": "#dfe7ee", "crib": "#fbf8f3", "blanket": "#a7c7e7",
    "toy_r": "#e2574c", "toy_y": "#f2c14e", "toy_b": "#4f8fd1", "toy_g": "#6fbf73", "teddy": "#b9824f",
    "paper": "#f7f1df", "blueprint": "#3f6fa8", "bp_line": "#dce9f7", "rubber": "#3a3a3e", "fruit": "#f08a3a",
    "apple": "#c8463a", "leafy": "#6aa84f", "frame_gold": "#c9a45c", "art1": "#e3a87a", "art2": "#7fa3b8",
    "art3": "#d9c07a", "mirror": "#cfe0ea"}.items():
    soft = k in ("wall", "ceiling", "skyblue", "carpet", "concrete", "marble", "tile")
    M[k] = toon("MNI_" + k, v, (0.86, 0.94, 1.0) if soft else (0.62, 0.84, 1.0))


def emit(name, hexcol, strength=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = lin(hexcol) + [1]
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
    m.diffuse_color = lin(hexcol) + [1]
    return m


M["day"] = emit("MNI_day", "#dff0fa")
M["glow"] = emit("MNI_glow", "#fff1c9", 1.2)
M["tv_on"] = emit("MNI_tv", "#5d86a8", 0.9)
M["mon"] = emit("MNI_monitor", "#7fb3d9", 1.0)


# ---------------------------------------------------------------- builders (P comes from mansion_kit)
def wall_x(name, x0, x1, y, z0, z1, holes=(), k="wall", t=0.2):
    """Wall along X centred on y; holes = (a, b, zb, zt)."""
    p = P(name)
    c = x0
    for a, b, zb, zt in sorted(holes):
        if a > c:
            p.box(c, a, y - t / 2, y + t / 2, z0, z1, k)
        if zb > z0:
            p.box(a, b, y - t / 2, y + t / 2, z0, zb, k)
        if zt < z1:
            p.box(a, b, y - t / 2, y + t / 2, zt, z1, k)
        c = b
    if c < x1:
        p.box(c, x1, y - t / 2, y + t / 2, z0, z1, k)
    return p.done(outline=0.01)


def wall_y(name, y0, y1, x, z0, z1, holes=(), k="wall", t=0.2):
    p = P(name)
    c = y0
    for a, b, zb, zt in sorted(holes):
        if a > c:
            p.box(x - t / 2, x + t / 2, c, a, z0, z1, k)
        if zb > z0:
            p.box(x - t / 2, x + t / 2, a, b, z0, zb, k)
        if zt < z1:
            p.box(x - t / 2, x + t / 2, a, b, zt, z1, k)
        c = b
    if c < y1:
        p.box(x - t / 2, x + t / 2, c, y1, z0, z1, k)
    return p.done(outline=0.01)


def pane_x(name, a, b, zb, zt, y, cols=3, rows=1, frame="black"):
    """Bright daylight pane with a slim frame in a hole of a wall along X."""
    p = P(name)
    p.box(a, b, y - 0.02, y + 0.02, zb, zt, "day")
    f = 0.06
    for x0, x1, z0, z1 in ((a, b, zt - f, zt), (a, b, zb, zb + f), (a, a + f, zb, zt), (b - f, b, zb, zt)):
        p.box(x0, x1, y - 0.07, y + 0.07, z0, z1, frame)
    for k in range(1, cols):
        x = a + (b - a) * k / cols
        p.box(x - 0.03, x + 0.03, y - 0.05, y + 0.05, zb, zt, frame)
    for k in range(1, rows):
        z = zb + (zt - zb) * k / rows
        p.box(a, b, y - 0.05, y + 0.05, z - 0.03, z + 0.03, frame)
    return p.done(outline=0.006)


def floor(name, x0, x1, y0, y1, z, k, line=None, step=0.22, axis='X'):
    p = P(name)
    z += 0.012                      # sit just above the structural slab
    p.box(x0, x1, y0, y1, z - 0.04, z, k)
    if line:
        if axis == 'X':     # planks running along X: joints every `step` in Y
            y = y0 + step
            while y < y1 - 0.01:
                p.box(x0, x1, y - 0.006, y + 0.006, z, z + 0.002, line)
                y += step
        else:               # square tiles
            y = y0 + step
            while y < y1 - 0.01:
                p.box(x0, x1, y - 0.008, y + 0.008, z, z + 0.002, line)
                y += step
            x = x0 + step
            while x < x1 - 0.01:
                p.box(x - 0.008, x + 0.008, y0, y1, z, z + 0.002, line)
                x += step
    return p.done(outline=0)


def slab(name, x0, x1, y0, y1, z0, z1, holes=(), k="ceiling"):
    """Floor/ceiling slab with rectangular holes (x0, x1, y0, y1), cut in X strips."""
    p = P(name)
    xs = sorted({x0, x1} | {h[0] for h in holes} | {h[1] for h in holes})
    for a, b in zip(xs, xs[1:]):
        if b <= x0 or a >= x1:
            continue
        cut = sorted((h[2], h[3]) for h in holes if h[0] <= a and h[1] >= b)
        c = y0
        for ya, yb in cut:
            if ya > c:
                p.box(a, b, c, ya, z0, z1, k)
            c = max(c, yb)
        if c < y1:
            p.box(a, b, c, y1, z0, z1, k)
    return p.done(outline=0.01)


def area_light(name, loc, size, energy, color="#fff3e2"):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = size
    ld.energy = energy
    ld.color = lin(color)
    lo = bpy.data.objects.new(name, ld)
    IC["MNI_Lights"].objects.link(lo)
    lo.parent = RIG
    lo.location = loc
    return lo


def point_light(name, loc, energy, color="#ffd9a0", radius=0.1):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = lin(color)
    ld.shadow_soft_size = radius
    lo = bpy.data.objects.new(name, ld)
    IC["MNI_Lights"].objects.link(lo)
    lo.parent = RIG
    lo.location = loc
    return lo


# ---------------------------------------------------------------- furniture
def sofa(name, w=2.4, loc=(0, 0, 0), rot=0.0, col="sofa"):
    p = P(name)
    d = 0.95
    p.box(-w / 2, w / 2, -d / 2, d / 2, 0.08, 0.42, col)
    p.box(-w / 2, w / 2, d / 2 - 0.22, d / 2, 0.42, 0.85, col)
    for sx in (-1, 1):
        p.box(sx * w / 2 - (0.2 if sx > 0 else 0), sx * w / 2 + (0.0 if sx > 0 else 0.2), -d / 2, d / 2, 0.42, 0.65, col)
    n = 3 if w > 2 else 2
    cw = (w - 0.4) / n
    for i in range(n):
        x = -w / 2 + 0.2 + cw * i
        p.box(x + 0.02, x + cw - 0.02, -d / 2 + 0.02, d / 2 - 0.24, 0.42, 0.55, col)
    for sx in (-0.6, 0.55):
        p.blob((sx * w / 2, d / 2 - 0.3, 0.68), (0.22, 0.09, 0.2), "cushion")
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box(sx * w / 2 * 0.92 - 0.03, sx * w / 2 * 0.92 + 0.03, sy * d / 2 * 0.85 - 0.03, sy * d / 2 * 0.85 + 0.03, 0, 0.08, "black")
    return p.done(loc, rot)


def armchair(name, loc, rot, col="mustard"):
    p = P(name)
    p.box(-0.45, 0.45, -0.42, 0.42, 0.12, 0.45, col)
    p.box(-0.45, 0.45, 0.22, 0.42, 0.45, 0.92, col, taper=(1.0, 1.0))
    p.box(-0.45, -0.3, -0.42, 0.42, 0.45, 0.66, col)
    p.box(0.3, 0.45, -0.42, 0.42, 0.45, 0.66, col)
    p.box(-0.3, 0.3, -0.4, 0.22, 0.45, 0.55, col)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box(sx * 0.38 - 0.025, sx * 0.38 + 0.025, sy * 0.35 - 0.025, sy * 0.35 + 0.025, 0, 0.12, "oak_dk")
    return p.done(loc, rot)


def table(name, w, d, h, loc, rot=0.0, top="oak", legs="oak_dk", round_=False):
    p = P(name)
    if round_:
        p.cyl((0, 0, h - 0.02), w / 2, 0.04, top, segs=32)
        p.cyl((0, 0, (h - 0.04) / 2), 0.06, h - 0.04, legs)
        p.cyl((0, 0, 0.02), w / 4, 0.04, legs)
    else:
        p.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.045, h, top)
        for sx in (-1, 1):
            for sy in (-1, 1):
                p.box(sx * (w / 2 - 0.08) - 0.03, sx * (w / 2 - 0.08) + 0.03, sy * (d / 2 - 0.08) - 0.03,
                      sy * (d / 2 - 0.08) + 0.03, 0, h - 0.045, legs)
    return p.done(loc, rot)


def chair(name, loc, rot, col="oak", seat="cream"):
    p = P(name)
    p.box(-0.22, 0.22, -0.22, 0.22, 0.43, 0.48, seat)
    p.box(-0.22, 0.22, 0.18, 0.22, 0.48, 0.95, col)
    p.box(-0.18, 0.18, 0.17, 0.19, 0.6, 0.88, seat)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box(sx * 0.19 - 0.02, sx * 0.19 + 0.02, sy * 0.19 - 0.02, sy * 0.19 + 0.02, 0, 0.43, col)
    return p.done(loc, rot)


def stool(name, loc, rot=0.0):
    p = P(name)
    p.cyl((0, 0, 0.72), 0.2, 0.06, "terracotta", segs=24)
    p.cyl((0, 0, 0.36), 0.03, 0.72, "black")
    p.cyl((0, 0, 0.3), 0.15, 0.02, "black", segs=20)
    p.cyl((0, 0, 0.01), 0.18, 0.02, "black", segs=20)
    return p.done(loc, rot)


def high_chair(name, loc, rot):
    p = P(name)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.beam((sx * 0.25, sy * 0.25, 0), (sx * 0.17, sy * 0.15, 0.7), 0.04, 0.04, "crib")
    p.box(-0.2, 0.2, -0.18, 0.2, 0.7, 0.76, "crib")
    p.box(-0.2, 0.2, 0.16, 0.2, 0.76, 1.15, "crib")
    p.box(-0.2, -0.17, -0.18, 0.2, 0.76, 0.9, "crib")
    p.box(0.17, 0.2, -0.18, 0.2, 0.76, 0.9, "crib")
    p.box(-0.24, 0.24, -0.42, -0.16, 0.88, 0.91, "blanket")
    p.box(-0.15, 0.15, -0.1, 0.15, 0.76, 0.8, "blanket")
    return p.done(loc, rot)


def lamp_floor(name, loc):
    p = P(name)
    p.cyl((0, 0, 0.02), 0.18, 0.04, "black")
    p.cyl((0, 0, 0.8), 0.018, 1.56, "black")
    p.cyl((0, 0, 1.62), 0.24, 0.3, "glow", r2=0.16)
    return p.done(loc)


def lamp_table(name, loc):
    p = P(name)
    p.cyl((0, 0, 0.12), 0.08, 0.24, "terracotta", r2=0.05)
    p.cyl((0, 0, 0.36), 0.15, 0.2, "glow", r2=0.1)
    return p.done(loc)


def pendant(name, loc, drop, r=0.2, col="black"):
    p = P(name)
    p.cyl((0, 0, -drop / 2), 0.008, drop, "black", segs=6)
    p.cyl((0, 0, -drop - 0.1), r, 0.2, col, r2=0.04, segs=24)
    p.cyl((0, 0, -drop - 0.19), r * 0.6, 0.02, "glow", segs=16)
    return p.done(loc, outline=0.008)


def bookshelf(name, w, h, loc, rot=0.0):
    p = P(name)
    d = 0.35
    p.box(-w / 2, w / 2, -d / 2, d / 2, 0, 0.05, "oak")
    p.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.04, h, "oak")
    p.box(-w / 2, -w / 2 + 0.04, -d / 2, d / 2, 0, h, "oak")
    p.box(w / 2 - 0.04, w / 2, -d / 2, d / 2, 0, h, "oak")
    p.box(-w / 2, w / 2, d / 2 - 0.02, d / 2, 0, h, "oak_dk")
    n = 4
    for i in range(1, n + 1):
        z = h * i / (n + 1)
        p.box(-w / 2, w / 2, -d / 2, d / 2, z - 0.02, z + 0.02, "oak")
    for i in range(n + 1):
        z0 = h * i / (n + 1) + 0.02 + (0.05 if i == 0 else 0)
        x = -w / 2 + 0.06
        while x < w / 2 - 0.25:
            bw = random.uniform(0.03, 0.06)
            bh = random.uniform(0.18, 0.28)
            if random.random() < 0.12:
                p.blob((x + 0.08, 0, z0 + 0.08), (0.07, 0.07, 0.08), random.choice(("terracotta", "leafy", "cream")))
                x += 0.2
                continue
            p.box(x, x + bw, -d / 2 + 0.05, d / 2 - 0.05, z0, z0 + bh, random.choice(("book1", "book2", "book3", "book4", "book5", "cream")))
            x += bw + 0.005
            if random.random() < 0.08:
                x += 0.15
    return p.done(loc, rot)


def art(name, w, h, loc, rot, cols=("art1", "art2", "art3"), frame="frame_gold"):
    """Framed abstract picture hanging on a wall (local -Y faces the room)."""
    p = P(name)
    p.box(-w / 2, w / 2, -0.03, 0, -h / 2, h / 2, frame)
    p.box(-w / 2 + 0.05, w / 2 - 0.05, -0.04, -0.03, -h / 2 + 0.05, h / 2 - 0.05, "cream")
    p.blob((-w * 0.15, -0.045, -h * 0.05), (w * 0.22, 0.006, h * 0.25), cols[0], subdiv=2)
    p.blob((w * 0.18, -0.05, h * 0.12), (w * 0.15, 0.006, h * 0.18), cols[1], subdiv=2)
    p.box(-w * 0.35, w * 0.3, -0.05, -0.044, -h * 0.32, -h * 0.28, cols[2])
    return p.done(loc, rot, outline=0.006)


def plant(name, loc, s=1.0, pot="cream"):
    p = P(name)
    p.cyl((0, 0, 0.22 * s), 0.2 * s, 0.44 * s, pot, r2=0.16 * s)
    for k in range(8):
        a = k / 8 * math.tau + random.uniform(-0.2, 0.2)
        rr = random.uniform(0.1, 0.22) * s
        p.blob((math.cos(a) * rr, math.sin(a) * rr, (0.55 + random.uniform(0, 0.45)) * s),
               (0.14 * s, 0.14 * s, 0.22 * s), random.choice(("plant", "plant2")))
    return p.done(loc, outline=0.008)


def rug(name, w, d, loc, col, border="cream", rot=0.0, round_=False):
    p = P(name)
    if round_:
        p.cyl((0, 0, 0.008), w / 2, 0.016, border, segs=40)
        p.cyl((0, 0, 0.012), w / 2 - 0.12, 0.016, col, segs=40)
    else:
        p.box(-w / 2, w / 2, -d / 2, d / 2, 0, 0.016, border)
        p.box(-w / 2 + 0.12, w / 2 - 0.12, -d / 2 + 0.12, d / 2 - 0.12, 0, 0.02, col)
    return p.done(loc, rot, outline=0.004)


def curtain(name, w, h, loc, rot=0.0, col="linen"):
    p = P(name)
    n = 6
    for i in range(n):
        x = -w / 2 + w * (i + 0.5) / n
        p.cyl((x, 0, h / 2), w / n * 0.6, h, col, segs=10)
    p.cyl((0, 0, h + 0.05), 0.02, w + 0.3, "black", axis='X', segs=8)
    return p.done(loc, rot, outline=0.006)


def drone(name, loc, rot=0.0, s=1.0, col="terracotta"):
    p = P(name)
    p.box(-0.12 * s, 0.12 * s, -0.16 * s, 0.16 * s, 0.0, 0.07 * s, col)
    p.blob((0, -0.02 * s, 0.08 * s), (0.09 * s, 0.11 * s, 0.05 * s), "navy")
    p.cyl((0, -0.17 * s, 0.035 * s), 0.025 * s, 0.03 * s, "black", axis='Y', segs=12)
    for sx in (-1, 1):
        for sy in (-1, 1):
            e = (sx * 0.32 * s, sy * 0.32 * s, 0.05 * s)
            p.beam((0, 0, 0.04 * s), e, 0.035 * s, 0.025 * s, "navy")
            p.cyl((e[0], e[1], e[2] + 0.02 * s), 0.03 * s, 0.05 * s, "black", segs=12)
            p.cyl((e[0], e[1], e[2] + 0.05 * s), 0.17 * s, 0.008 * s, "steel", segs=24)
            p.box(e[0] - 0.16 * s, e[0] + 0.16 * s, e[1] - 0.012 * s, e[1] + 0.012 * s, e[2] + 0.055 * s, e[2] + 0.062 * s, "black")
    p.box(-0.1 * s, -0.08 * s, -0.08 * s, 0.08 * s, -0.12 * s, 0, "black")
    p.box(0.08 * s, 0.1 * s, -0.08 * s, 0.08 * s, -0.12 * s, 0, "black")
    p.box(-0.14 * s, 0.14 * s, -0.09 * s, -0.07 * s, -0.13 * s, -0.11 * s, "black")
    p.box(-0.14 * s, 0.14 * s, 0.07 * s, 0.09 * s, -0.13 * s, -0.11 * s, "black")
    return p.done(loc, rot, outline=0.004)


# ================================================================ GROUND FLOOR
use(IC["MNI_Ground"])
G0, G1 = 0.15, 2.95
# floors
floor("MNI.living_floor", -10.0, -3.0, 0.8, 10.0, G0, "oak", "oak_dk", 0.22)
floor("MNI.kitchen_floor", -3.0, 2.0, 0.0, 10.0, G0, "tile", "tile_ln", 0.6, axis='T')
floor("MNI.hall_floor", 2.0, 6.75, 0.25, 10.0, G0, "marble", "marble_ln", 0.9, axis='T')
# outer walls (inside face of the exterior skin)
wall_x("MNI.living_front", -10.0, -3.0, 0.9, G0, G1,
       [(-9.45, -8.2, 0.75, 2.4), (-7.6, -5.85, 0.75, 2.4), (-5.3, -3.55, 0.75, 2.4)])
pane_x("MNI.living_win_a", -9.45, -8.2, 0.75, 2.4, 0.9, cols=1)
pane_x("MNI.living_win_b", -7.6, -5.85, 0.75, 2.4, 0.9)
pane_x("MNI.living_win_c", -5.3, -3.55, 0.75, 2.4, 0.9)
wall_y("MNI.living_left", 0.8, 10.0, -9.9, G0, G1)
wall_x("MNI.back_gf", -10.0, 6.75, 9.9, G0, G1, [(-8.4, -5.6, G0, 2.45)])
pane_x("MNI.patio_doors", -8.4, -5.6, G0, 2.45, 9.9, cols=2)
wall_x("MNI.kitchen_front", -3.0, 2.0, 0.1, G0, G1, [(0.1, 1.3, 1.3, 2.3)])
pane_x("MNI.kitchen_win", 0.1, 1.3, 1.3, 2.3, 0.1, cols=2)
wall_x("MNI.hall_front", 2.0, 6.75, 0.35, G0, G1,
       [(2.6, 3.0, 0.7, 2.6), (3.25, 3.65, 0.7, 2.6), (3.9, 4.3, 0.7, 2.6), (5.35, 6.55, G0, 2.55)])
for i, x in enumerate((2.6, 3.25, 3.9)):
    pane_x("MNI.hall_slot%d" % i, x, x + 0.4, 0.7, 2.6, 0.35, cols=1, frame="oak_dk")
# front door from inside (closed), with a handle
d = P("MNI.front_door")
d.box(5.35, 6.55, 0.33, 0.37, G0, 2.55, "door")
for k in range(7):
    d.box(5.42 + k * 0.155, 5.44 + k * 0.155, 0.37, 0.385, 0.3, 2.45, "wood_dk")
d.box(5.45, 5.49, 0.38, 0.46, 0.9, 1.6, "steel")
d.done(outline=0.008)
# partitions
wall_y("MNI.living_kitchen", 0.0, 9.9, -3.0, G0, G1, [(5.2, 8.8, G0, 2.45)])
wall_y("MNI.kitchen_hall", 0.1, 9.9, 2.0, G0, G1, [(1.4, 2.6, G0, 2.35)])
wall_y("MNI.hall_right", 0.25, 9.9, 6.8, G0, G1)
# ceiling of the ground floor = first-floor slab, with the stair void
slab("MNI.slab_gf", -10.0, 7.2, 0.0, 10.0, G1, 3.35, holes=[(5.1, 6.6, 4.2, 9.5)])
# skirting in the living room
sk = P("MNI.living_skirting")
sk.box(-9.8, -3.1, 1.0, 1.04, G0, G0 + 0.1, "skirting")
sk.box(-9.8, -9.76, 1.0, 9.8, G0, G0 + 0.1, "skirting")
sk.done(outline=0)

# --- living room ---
rug("MNI.living_rug", 4.2, 3.2, (-6.4, 3.6, G0), "terracotta")
sofa("MNI.sofa", 2.6, (-4.0, 3.6, G0), -90)
armchair("MNI.armchair", (-6.3, 6.1, G0), 15)
table("MNI.coffee_table", 1.2, 0.7, 0.4, (-6.3, 3.6, G0), 90)
ct = P("MNI.coffee_props")
ct.cyl((-6.2, 3.3, G0 + 0.44), 0.12, 0.04, "cream")
for k, (x, y) in enumerate(((-6.25, 3.28), (-6.13, 3.34), (-6.2, 3.38))):
    ct.blob((x, y, G0 + 0.5), (0.04, 0.04, 0.04), ("fruit", "apple", "fruit")[k])
ct.box(-6.5, -6.2, 3.85, 4.05, G0 + 0.4, G0 + 0.44, "book2")
ct.box(-6.48, -6.22, 3.87, 4.03, G0 + 0.44, G0 + 0.47, "book3")
ct.done(outline=0.005)
tv = P("MNI.tv_unit")
tv.box(-9.8, -9.35, 2.4, 4.8, G0, G0 + 0.5, "oak")
tv.box(-9.36, -9.34, 2.5, 3.55, G0 + 0.05, G0 + 0.45, "oak_dk")
tv.box(-9.36, -9.34, 3.65, 4.7, G0 + 0.05, G0 + 0.45, "oak_dk")
tv.box(-9.75, -9.7, 2.85, 4.35, G0 + 0.85, G0 + 1.7, "black")
tv.box(-9.7, -9.69, 2.9, 4.3, G0 + 0.9, G0 + 1.65, "tv_on")
tv.done(outline=0.008)
plant("MNI.living_plant_a", (-9.4, 1.5, G0), 1.3, "terracotta")
plant("MNI.living_plant_b", (-3.6, 9.2, G0), 1.1)
plant("MNI.living_plant_c", (-9.3, 5.6, G0), 0.9)
lamp_floor("MNI.living_lamp", (-4.0, 1.75, G0))
bookshelf("MNI.living_books", 1.8, 2.1, (-4.3, 9.6, G0), 180)
art("MNI.living_art", 1.6, 1.0, (-3.12, 3.6, 1.75), 90)
art("MNI.living_art2", 0.7, 0.9, (-9.78, 7.4, 1.6), -90, cols=("art2", "terracotta", "navy"))
curtain("MNI.living_curtain_l", 0.5, 2.5, (-9.6, 1.2, G0), 0)
curtain("MNI.living_curtain_r", 0.5, 2.5, (-3.3, 1.2, G0), 0)
pendant("MNI.living_pendant", (-6.3, 3.6, G1), 0.8, 0.3, "cream")

# --- kitchen + dining ---
kc = P("MNI.kitchen_counter")
kc.box(-2.0, 1.95, 0.2, 0.85, G0, G0 + 0.85, "cream")                 # base cabinets
kc.box(-2.05, 2.0, 0.18, 0.88, G0 + 0.85, G0 + 0.92, "marble")       # worktop
x = -2.0
while x < 1.9:
    kc.box(x + 0.02, x + 0.53, 0.86, 0.87, G0 + 0.1, G0 + 0.8, "linen")
    kc.box(x + 0.22, x + 0.33, 0.87, 0.9, G0 + 0.7, G0 + 0.73, "steel")
    x += 0.55
kc.box(-2.0, 0.1, 0.18, 0.21, G0 + 0.92, G0 + 1.5, "terracotta")      # tiled splashback
for z in (G0 + 1.07, G0 + 1.22, G0 + 1.37):
    kc.box(-2.0, 0.1, 0.21, 0.215, z - 0.006, z + 0.006, "cream")
kc.box(-2.0, -0.1, 0.2, 0.55, G0 + 1.6, G0 + 2.35, "sage")            # upper cabinets
for xx in (-1.6, -1.0, -0.45):
    kc.box(xx - 0.05, xx + 0.05, 0.55, 0.57, G0 + 1.65, G0 + 1.68, "steel")
kc.box(0.3, 1.1, 0.3, 0.75, G0 + 0.86, G0 + 0.93, "steel")            # sink
kc.cyl((0.7, 0.28, G0 + 1.1), 0.02, 0.36, "steel", segs=10)
kc.beam((0.7, 0.28, G0 + 1.27), (0.7, 0.45, G0 + 1.22), 0.03, 0.03, "steel")
kc.box(-1.4, -0.6, 0.3, 0.8, G0 + 0.92, G0 + 0.94, "black")           # hob
for cx, cy in ((-1.2, 0.45), (-0.8, 0.45), (-1.2, 0.68), (-0.8, 0.68)):
    kc.cyl((cx, cy, G0 + 0.945), 0.08, 0.004, "terracotta", segs=20)
kc.cyl((-1.2, 0.47, G0 + 1.0), 0.13, 0.12, "navy", segs=20)          # pot
kc.box(-1.45, -0.55, 0.2, 0.6, G0 + 1.6, G0 + 1.65, "steel")          # extractor
kc.box(-1.15, -0.85, 0.2, 0.45, G0 + 1.65, G0 + 2.35, "steel")
kc.done(outline=0.008)
fr = P("MNI.fridge")
fr.box(-2.9, -2.05, 0.2, 0.95, G0, G0 + 2.1, "steel")
fr.box(-2.9, -2.05, 0.94, 0.96, G0 + 1.3, G0 + 1.32, "black")
fr.box(-2.2, -2.16, 0.96, 1.02, G0 + 1.4, G0 + 1.9, "black")
fr.box(-2.2, -2.16, 0.96, 1.02, G0 + 0.6, G0 + 1.2, "black")
fr.box(-2.7, -2.45, 0.96, 0.97, G0 + 1.5, G0 + 1.8, "paper")          # Max's drawing on the fridge
fr.blob((-2.58, 0.975, G0 + 1.68), (0.05, 0.004, 0.04), "toy_y")
fr.done(outline=0.008)
isl = P("MNI.island")
isl.box(-1.6, 0.6, 2.6, 3.4, G0, G0 + 0.88, "navy")
isl.box(-1.7, 0.7, 2.5, 3.75, G0 + 0.88, G0 + 0.94, "marble")
isl.cyl((-0.8, 3.0, G0 + 0.97), 0.18, 0.06, "cream", r2=0.12)
for k in range(5):
    isl.blob((-0.8 + random.uniform(-0.08, 0.08), 3.0 + random.uniform(-0.08, 0.08), G0 + 1.03),
             (0.045, 0.045, 0.045), random.choice(("fruit", "apple", "toy_y")))
isl.box(0.0, 0.35, 2.75, 3.05, G0 + 0.94, G0 + 0.97, "oak")           # chopping board
isl.done(outline=0.008)
for i, x in enumerate((-1.2, -0.5, 0.2)):
    stool("MNI.stool%d" % i, (x, 4.05, G0))
for i, x in enumerate((-1.2, 0.2)):
    pendant("MNI.island_pendant%d" % i, (x - 0.1, 3.1, G1), 0.9, 0.18, "terracotta")
table("MNI.dining_table", 2.2, 1.0, 0.76, (-0.5, 7.2, G0))
for i, x in enumerate((-1.3, -0.5, 0.3)):
    chair("MNI.dchair_f%d" % i, (x, 6.45, G0), 180, "oak", "terracotta")
    chair("MNI.dchair_b%d" % i, (x, 7.95, G0), 0, "oak", "terracotta")
chair("MNI.dchair_end", (-1.95, 7.2, G0), -90, "oak", "terracotta")
high_chair("MNI.high_chair", (1.05, 7.2, G0), 90)
dt = P("MNI.dining_props")
dt.cyl((-0.5, 7.2, G0 + 0.8), 0.14, 0.08, "cream", r2=0.1)
dt.blob((-0.5, 7.2, G0 + 0.92), (0.12, 0.12, 0.1), "leafy")
for x in (-1.3, -0.5, 0.3):
    for y in (6.85, 7.55):
        dt.cyl((x, y, G0 + 0.775), 0.13, 0.01, "cream", segs=24)
dt.done(outline=0.005)
pendant("MNI.dining_pendant", (-0.5, 7.2, G1), 0.75, 0.32, "cream")
plant("MNI.kitchen_plant", (1.6, 9.4, G0), 1.2, "terracotta")
art("MNI.kitchen_clock", 0.45, 0.45, (1.88, 5.0, 2.1), -90, cols=("cream", "navy", "black"), frame="black")

# --- entrance hall ---
fw = P("MNI.feature_wall")
fw.box(6.6, 6.75, 0.35, 9.9, G0, G1, "stone2")
fw.done(outline=0.006)
stone_face("MNI.feature_wall_stone", 0.4, 9.85, G0, G1, 6.6, side=True)
st = P("MNI.stair")
RISE = (3.35 - G0) / 18
for k in range(18):
    y1 = 9.3 - 0.28 * k
    y0 = y1 - 0.3
    z = G0 + RISE * (k + 1)
    st.box(5.1, 6.6, y0, y1, z - 0.09, z, "oak")
    st.box(5.08, 5.11, y0 + 0.02, y1 - 0.02, z, z + 0.9, "rail")       # glass baluster panel
st.beam((5.095, 9.3, G0 + 1.05), (5.095, 4.26, 3.35 + 0.9), 0.05, 0.05, "black")
st.done(outline=0.008)
rug("MNI.hall_rug", 2.2, 2.2, (3.7, 3.0, G0), "navy", "cream", round_=True)
con = P("MNI.console")
con.box(2.1, 2.5, 5.6, 7.2, G0 + 0.78, G0 + 0.83, "oak")
for y in (5.7, 7.1):
    con.box(2.15, 2.45, y - 0.03, y + 0.03, G0, G0 + 0.78, "black")
con.cyl((2.3, 6.0, G0 + 1.0), 0.08, 0.34, "terracotta", r2=0.05)
con.blob((2.3, 6.0, G0 + 1.28), (0.12, 0.12, 0.16), "leafy")
con.box(2.15, 2.4, 6.6, 6.95, G0 + 0.83, G0 + 0.9, "book2")
con.cyl((2.12, 6.4, G0 + 1.75), 0.55, 0.03, "frame_gold", axis='X', segs=40)
con.cyl((2.13, 6.4, G0 + 1.75), 0.5, 0.03, "mirror", axis='X', segs=40)
con.done(outline=0.008)
bench = P("MNI.bench")
bench.box(2.1, 2.55, 8.0, 9.4, G0 + 0.4, G0 + 0.47, "oak")
bench.box(2.1, 2.55, 8.05, 8.12, G0, G0 + 0.4, "oak_dk")
bench.box(2.1, 2.55, 9.28, 9.35, G0, G0 + 0.4, "oak_dk")
bench.blob((2.3, 8.4, G0 + 0.57), (0.16, 0.18, 0.1), "cushion")
for k, y in enumerate((8.3, 8.8, 9.25)):
    bench.cyl((2.12, y, 1.9), 0.02, 0.1, "steel", axis='X', segs=8)
bench.blob((2.18, 8.8, 1.55), (0.08, 0.16, 0.38), "terracotta")      # Tori's coat
bench.done(outline=0.008)
plant("MNI.hall_plant_a", (4.8, 0.9, G0), 1.3, "cream")
plant("MNI.hall_plant_b", (2.5, 0.9, G0), 0.9, "terracotta")
art("MNI.hall_art", 1.2, 0.8, (2.12, 4.0, 1.7), -90, cols=("art2", "art1", "navy"))
# chandelier hanging in the stair void (three floors high)
ch = P("MNI.chandelier")
ch.cyl((5.85, 6.9, 7.0), 0.01, 4.8, "black", segs=6)
for k in range(14):
    a = k * 2.4
    r = 0.15 + 0.035 * k
    z = 4.9 - k * 0.12
    ch.cyl((5.85 + math.cos(a) * r, 6.9 + math.sin(a) * r, z + 0.3), 0.004, 0.6, "black", segs=4)
    ch.blob((5.85 + math.cos(a) * r, 6.9 + math.sin(a) * r, z), (0.07, 0.07, 0.07), "glow", subdiv=2)
ch.done(outline=0.004)

# ================================================================ FIRST FLOOR
use(IC["MNI_First"])
F0, F1 = 3.35, 6.4
floor("MNI.bed_floor", -9.0, -3.5, 1.0, 8.2, F0, "oak", "oak_dk", 0.22)
floor("MNI.nursery_floor", -3.5, 3.8, 2.0, 8.2, F0, "carpet")
floor("MNI.corridor_floor", -9.0, 3.8, 8.2, 9.5, F0, "oak", "oak_dk", 0.22)
floor("MNI.landing_floor_a", 3.8, 6.6, 1.4, 4.2, F0, "marble", "marble_ln", 0.9, axis='T')
floor("MNI.landing_floor_b", 3.8, 5.1, 4.2, 9.5, F0, "marble", "marble_ln", 0.9, axis='T')
# walls
wall_x("MNI.bed_front", -9.0, -3.5, 1.1, F0, F1, [(-7.35, -4.65, 4.0, 5.95)])
pane_x("MNI.bed_win", -7.35, -4.65, 4.0, 5.95, 1.1, cols=4, frame="cream")
wall_y("MNI.bed_left", 1.0, 9.5, -8.9, F0, F1)
wall_y("MNI.bed_nursery", 1.0, 8.2, -3.5, F0, F1)
wall_x("MNI.corridor_inner", -9.0, 3.85, 8.2, F0, F1, [(-5.0, -4.0, F0, 5.55), (1.5, 2.4, F0, 5.55)])
wall_x("MNI.back_ff", -9.0, 6.6, 9.45, F0, F1)
wall_x("MNI.nursery_front", -3.5, 3.85, 2.1, F0, F1, [(-2.8, 2.6, F0, 5.7)])
pane_x("MNI.nursery_doors", -2.8, 2.6, F0, 5.7, 2.1, cols=4)
wall_y("MNI.nursery_landing", 1.4, 9.5, 3.85, F0, F1, [(8.25, 9.35, F0, 5.6)])
# landing tower (double height behind the lattice)
wall_y("MNI.landing_right", 1.4, 9.5, 6.55, F0, 9.4)
wall_x("MNI.landing_back", 3.8, 6.6, 9.45, F0, 9.4)
wall_x("MNI.landing_front", 3.8, 6.6, 1.45, F0, 9.4, [(3.95, 6.45, 3.5, 9.25)])
lat = bpy.data.objects.get("MN.lattice_screen")
if lat:                                    # the real lattice, seen from inside
    lc = bpy.data.objects.new("MNI.lattice_view", lat.data)
    IC["MNI_First"].objects.link(lc)
    lc.parent = RIG
    for m in lat.modifiers:
        if m.type == 'SOLIDIFY':
            so = lc.modifiers.new(m.name, 'SOLIDIFY')
            so.thickness, so.offset, so.use_flip_normals, so.material_offset = m.thickness, m.offset, True, m.material_offset
rl = P("MNI.void_rail")
rl.box(5.08, 5.12, 4.2, 9.4, F0, F0 + 0.95, "rail")
rl.box(5.06, 5.14, 4.2, 9.4, F0 + 0.95, F0 + 0.99, "black")
rl.done(outline=0.006)
# spiral stair to the workshop
sp = P("MNI.spiral")
CX, CY, RS = 5.8, 2.3, 0.78
sp.cyl((CX, CY, (F0 + 7.9) / 2), 0.07, 7.9 - F0, "black", segs=16)
NS = 18
for k in range(NS):
    a = math.radians(-90 + 19 * k)
    z = F0 + (7.0 - F0) * (k + 1) / NS
    xf = Matrix.Translation((CX, CY, 0)) @ Matrix.Rotation(a, 4, 'Z')
    sp.box(0.05, RS, -0.13, 0.13, z - 0.05, z, "oak", taper=None, xf=xf)
    sp.box(RS - 0.02, RS, -0.01, 0.01, z, z + 0.9, "black", xf=xf)
    if k:
        a0 = math.radians(-90 + 19 * (k - 1))
        z0 = F0 + (7.0 - F0) * k / NS
        sp.beam((CX + math.cos(a0) * RS, CY + math.sin(a0) * RS, z0 + 0.9),
                (CX + math.cos(a) * RS, CY + math.sin(a) * RS, z + 0.9), 0.04, 0.04, "black")
sp.done(outline=0.006)
slab("MNI.top_platform", 3.8, 6.6, 3.1, 4.4, 6.85, 7.0)
glass_rail("MNI.top_platform_rail", 4.6, 6.55, 4.36, 4.4, 7.0)
slab("MNI.landing_ceiling", 3.8, 6.6, 1.4, 9.5, 9.4, 9.6)
plant("MNI.landing_plant", (4.3, 1.8, F0), 1.4, "terracotta")
art("MNI.landing_art", 1.0, 1.4, (6.43, 3.0, 4.9), 90, cols=("art1", "art3", "terracotta"))
# ceiling of the first floor = top-floor slab
slab("MNI.slab_ff", -9.0, 3.85, 1.0, 9.5, F1, 7.0)

# --- main bedroom ---
rug("MNI.bed_rug", 3.2, 2.6, (-6.25, 6.4, F0), "dusty", "cream")
bed = P("MNI.bed")
bed.box(-1.05, 1.05, -1.15, 1.0, 0.0, 0.32, "oak")                  # frame
bed.box(-1.0, 1.0, -1.1, 0.95, 0.32, 0.55, "duvet")                 # mattress
bed.box(-1.06, 1.06, -1.16, 0.45, 0.5, 0.64, "duvet")               # duvet
bed.box(-1.07, 1.07, -0.75, -0.35, 0.52, 0.67, "throw")             # throw
bed.box(-1.15, 1.15, 0.95, 1.12, 0.0, 1.35, "dusty")                # headboard
for i in range(5):
    x = -1.1 + 0.44 * i
    bed.box(x + 0.02, x + 0.42, 0.93, 0.96, 0.4, 1.3, "navy")
for sx in (-0.48, 0.48):
    bed.blob((sx, 0.72, 0.68), (0.38, 0.14, 0.13), "pillow")
    bed.blob((sx * 0.85, 0.5, 0.67), (0.26, 0.1, 0.12), "cushion")
bed.done((-6.25, 7.05, F0), 0)
for i, x in enumerate((-7.75, -4.75)):
    ns = P("MNI.nightstand%d" % i)
    ns.box(-0.28, 0.28, -0.22, 0.22, 0.0, 0.55, "oak")
    ns.box(-0.26, 0.26, -0.225, -0.22, 0.3, 0.5, "oak_dk")
    ns.done((x, 7.8, F0))
    lamp_table("MNI.bed_lamp%d" % i, (x, 7.85, F0 + 0.55))
wd = P("MNI.wardrobe")
wd.box(-0.32, 0.32, -1.6, 1.6, 0.0, 2.45, "oak")
for y in (-0.8, 0.0, 0.8):
    wd.box(0.32, 0.335, y - 0.008, y + 0.008, 0.05, 2.4, "oak_dk")
for y in (-0.08, 0.08, -0.88, 0.88):
    wd.box(0.335, 0.36, y - 0.012, y + 0.012, 0.9, 1.5, "frame_gold")
wd.done((-8.45, 4.4, F0))
van = P("MNI.vanity")
van.box(-0.3, 0.0, -0.65, 0.65, 0.72, 0.77, "cream")
for y in (-0.6, 0.6):
    van.box(-0.28, -0.02, y - 0.03, y + 0.03, 0.0, 0.72, "frame_gold")
van.cyl((-0.02, 0.0, 1.35), 0.42, 0.02, "frame_gold", axis='X', segs=40)
van.cyl((-0.035, 0.0, 1.35), 0.38, 0.02, "mirror", axis='X', segs=40)
van.blob((-0.15, -0.35, 0.82), (0.04, 0.04, 0.05), "terracotta")
van.cyl((-0.15, 0.3, 0.83), 0.05, 0.12, "cream", r2=0.03)
van.blob((-0.15, 0.3, 0.95), (0.08, 0.08, 0.08), "toy_r")
van.done((-3.62, 3.6, F0))
stool("MNI.vanity_stool", (-4.2, 3.6, F0 - 0.25))
armchair("MNI.bed_armchair", (-8.1, 2.1, F0), 210, "sage")
plant("MNI.bed_plant", (-3.95, 1.55, F0), 1.1)
curtain("MNI.bed_curtain_l", 0.5, 2.9, (-7.75, 1.35, F0))
curtain("MNI.bed_curtain_r", 0.5, 2.9, (-4.25, 1.35, F0))
art("MNI.bed_art", 1.8, 0.6, (-6.25, 8.07, 5.55), 0, cols=("art3", "dusty", "terracotta"))
pendant("MNI.bed_pendant", (-6.25, 5.0, F1), 0.6, 0.35, "cream")

# --- Max's nursery ---
cl = P("MNI.nursery_clouds")                       # sky-blue accent wall with clouds
cl.box(-3.4, 3.75, 8.08, 8.1, F0, F1, "skyblue")
for cx, cz, s in ((-2.6, 5.6, 1.0), (-0.2, 5.9, 0.8), (1.9, 5.4, 1.1), (0.9, 4.6, 0.6), (-1.5, 4.4, 0.55)):
    for dx, dz, r in ((-0.25, 0, 0.22), (0.0, 0.08, 0.3), (0.28, 0.0, 0.22)):
        cl.blob((cx + dx * s, 8.07, cz + dz * s), (r * s, 0.015, r * 0.75 * s), "cloud", subdiv=2)
cl.done(outline=0.004)
rug("MNI.nursery_rug", 2.6, 2.6, (0.2, 5.0, F0), "toy_y", "cream", round_=True)
cr = P("MNI.crib")
W2, D2 = 0.75, 0.42
cr.box(-W2, W2, -D2, D2, 0.28, 0.34, "crib")
cr.box(-W2 + 0.03, W2 - 0.03, -D2 + 0.03, D2 - 0.03, 0.34, 0.46, "duvet")
cr.box(-W2 + 0.04, W2 * 0.3, -D2 + 0.04, D2 - 0.04, 0.46, 0.5, "blanket")
for sx in (-1, 1):
    for sy in (-1, 1):
        cr.box(sx * W2 - 0.04, sx * W2 + 0.04, sy * D2 - 0.04, sy * D2 + 0.04, 0, 1.0, "crib")
for sy in (-1, 1):
    cr.box(-W2, W2, sy * D2 - 0.03, sy * D2 + 0.03, 0.92, 0.98, "crib")
    for k in range(13):
        x = -W2 + 0.11 * (k + 1)
        cr.box(x - 0.015, x + 0.015, sy * D2 - 0.015, sy * D2 + 0.015, 0.34, 0.93, "crib")
for sx in (-1, 1):
    cr.box(sx * W2 - 0.03, sx * W2 + 0.03, -D2, D2, 0.92, 0.98, "crib")
    for k in range(6):
        y = -D2 + 0.12 * (k + 1)
        cr.box(sx * W2 - 0.015, sx * W2 + 0.015, y - 0.015, y + 0.015, 0.34, 0.93, "crib")
cr.blob((0.45, 0.0, 0.56), (0.13, 0.11, 0.12), "teddy")             # teddy in the crib
cr.blob((0.45, 0.0, 0.73), (0.09, 0.08, 0.08), "teddy")
cr.done((-0.6, 7.5, F0))
mob = P("MNI.mobile")                              # little aeroplanes over the crib
mob.cyl((-0.6, 7.5, 5.6), 0.006, 1.6, "black", segs=4)
mob.box(-1.0, -0.2, 7.49, 7.51, 4.82, 4.84, "oak")
mob.box(-0.61, -0.59, 7.1, 7.9, 4.84, 4.86, "oak")
for k, (x, y) in enumerate(((-1.0, 7.5), (-0.2, 7.5), (-0.6, 7.1), (-0.6, 7.9))):
    c = ("toy_r", "toy_y", "toy_b", "toy_g")[k]
    mob.cyl((x, y, 4.7), 0.003, 0.24, "black", segs=4)
    mob.box(x - 0.025, x + 0.025, y - 0.1, y + 0.1, 4.54, 4.58, c)
    mob.box(x - 0.12, x + 0.12, y - 0.02, y + 0.02, 4.57, 4.59, c)
    mob.box(x - 0.05, x + 0.05, y + 0.07, y + 0.09, 4.58, 4.62, c)
mob.done(outline=0.003)
chg = P("MNI.changing_table")
chg.box(-0.55, 0.55, -0.3, 0.3, 0.0, 0.9, "crib")
chg.box(-0.52, 0.52, -0.31, -0.3, 0.08, 0.42, "blanket")
chg.box(-0.52, 0.52, -0.31, -0.3, 0.46, 0.82, "skyblue")
chg.box(-0.5, 0.5, -0.27, 0.27, 0.9, 0.97, "pillow")
chg.box(-0.55, -0.5, -0.3, 0.3, 0.9, 1.05, "crib")
chg.box(0.5, 0.55, -0.3, 0.3, 0.9, 1.05, "crib")
chg.box(0.5, 0.55, -0.3, 0.3, 0.9, 1.05, "crib")
chg.cyl((0.35, 0.0, 1.04), 0.05, 0.14, "toy_b", segs=12)
chg.done((1.9, 7.85, F0))
rk = P("MNI.rocking_chair")
for sx in (-1, 1):
    for k in range(6):
        a0, a1 = -0.5 + k / 6, -0.5 + (k + 1) / 6
        rk.beam((sx * 0.28, a0 * 0.9, 0.06 + 0.12 * a0 * a0), (sx * 0.28, a1 * 0.9, 0.06 + 0.12 * a1 * a1), 0.04, 0.035, "oak")
    rk.box(sx * 0.28 - 0.025, sx * 0.28 + 0.025, -0.25, -0.2, 0.06, 0.45, "oak")
    rk.box(sx * 0.28 - 0.025, sx * 0.28 + 0.025, 0.2, 0.25, 0.06, 1.0, "oak")
    rk.box(sx * 0.28 - 0.03, sx * 0.28 + 0.03, -0.28, 0.22, 0.62, 0.66, "oak")
rk.box(-0.28, 0.28, -0.25, 0.25, 0.43, 0.48, "oak")
rk.box(-0.26, 0.26, -0.22, 0.2, 0.48, 0.55, "sage")
rk.box(-0.26, 0.26, 0.18, 0.24, 0.55, 0.98, "sage")
rk.box(-0.28, 0.28, 0.2, 0.26, 0.98, 1.03, "oak")
rk.done((2.7, 4.3, F0), -35)
tb = P("MNI.toys")
tb.box(-3.35, -2.75, 4.7, 5.6, 0.0 + F0, F0 + 0.5, "toy_b")                       # toy box
tb.box(-3.37, -2.73, 4.68, 5.62, F0 + 0.5, F0 + 0.56, "toy_y")
for k, (x, y, c) in enumerate(((0.9, 4.6, "toy_r"), (1.05, 4.45, "toy_b"), (0.98, 4.55, "toy_g"), (-0.4, 4.2, "toy_y"))):
    z = F0 + (0.12 if k == 2 else 0.0)
    tb.box(x - 0.06, x + 0.06, y - 0.06, y + 0.06, z, z + 0.12, c)
tb.blob((-0.9, 5.6, F0 + 0.14), (0.14, 0.14, 0.14), "toy_r")                      # ball
tb.box(-0.2, 0.3, 5.75, 5.85, F0 + 0.03, F0 + 0.13, "toy_b")                      # toy plane
tb.box(0.0, 0.1, 5.5, 6.1, F0 + 0.1, F0 + 0.13, "toy_b")
tb.box(-0.25, -0.17, 5.75, 5.85, F0 + 0.1, F0 + 0.25, "toy_y")
for x in (-0.05, 0.25):
    tb.cyl((x, 5.68, F0 + 0.03), 0.03, 0.02, "black", axis='X', segs=10)
tb.blob((2.95, 6.8, F0 + 0.18), (0.16, 0.13, 0.18), "teddy")                      # big teddy
tb.blob((2.95, 6.8, F0 + 0.43), (0.12, 0.11, 0.11), "teddy")
for sx in (-1, 1):
    tb.blob((2.95 + sx * 0.08, 6.8, F0 + 0.53), (0.04, 0.03, 0.04), "teddy")
    tb.blob((2.95 + sx * 0.15, 6.75, F0 + 0.22), (0.05, 0.05, 0.08), "teddy")
tb.blob((2.95, 6.7, F0 + 0.41), (0.05, 0.02, 0.04), "cream")
tb.done(outline=0.006)
shelf = P("MNI.nursery_shelves")
for z in (4.6, 5.2):
    shelf.box(3.45, 3.75, 3.2, 4.6, z, z + 0.04, "crib")
    for k, c in enumerate(("toy_r", "toy_y", "toy_b", "toy_g")):
        y = 3.4 + k * 0.33
        if (k + int(z * 10)) % 2:
            shelf.box(3.5, 3.7, y - 0.08, y + 0.08, z + 0.04, z + 0.2, c)
        else:
            shelf.blob((3.6, y, z + 0.12), (0.08, 0.08, 0.08), c)
shelf.done(outline=0.005)
plant("MNI.nursery_plant", (-3.1, 2.5, F0), 1.0, "toy_y")
art("MNI.nursery_art", 0.6, 0.6, (-3.38, 6.6, 4.8), 90, cols=("toy_y", "toy_b", "toy_r"), frame="crib")
pendant("MNI.nursery_pendant", (0.2, 5.0, F1), 0.5, 0.3, "skyblue")

# --- corridor ---
art("MNI.corridor_art1", 0.8, 0.6, (-6.5, 9.33, 4.9), 0)
art("MNI.corridor_art2", 0.8, 0.6, (-1.0, 9.33, 4.9), 0, cols=("art2", "art3", "terracotta"))
plant("MNI.corridor_plant", (3.4, 9.0, F0), 0.9)

# ================================================================ TOP FLOOR: Ace's workshop
use(IC["MNI_Top"])
T0, T1 = 7.0, 9.4
floor("MNI.workshop_floor", -7.5, 3.85, 0.6, 7.0, T0, "concrete", "tile_ln", 1.2, axis='T')
wall_x("MNI.workshop_front", -7.5, 3.85, 0.7, T0, T1, [(-6.2, -1.6, 7.4, 9.0), (-0.8, 2.8, T0, 9.0)])
pane_x("MNI.workshop_win", -6.2, -1.6, 7.4, 9.0, 0.7, cols=4)
pane_x("MNI.workshop_doors", -0.8, 2.8, T0, 9.0, 0.7, cols=3)
wall_y("MNI.workshop_left", 0.6, 7.0, -7.4, T0, T1)
wall_x("MNI.workshop_back", -7.5, 3.85, 6.9, T0, T1)
wall_y("MNI.workshop_right", 0.6, 7.0, 3.85, T0, T1, [(3.3, 4.2, T0, 9.1)])
slab("MNI.workshop_ceiling", -7.5, 3.85, 0.6, 7.0, T1, 9.6)
wb = P("MNI.workbench")
wb.box(-6.9, -3.0, 6.0, 6.8, T0 + 0.9, T0 + 0.96, "oak")
for x in (-6.8, -5.0, -3.1):
    wb.box(x - 0.04, x + 0.04, 6.05, 6.75, T0, T0 + 0.9, "black")
wb.box(-6.85, -3.05, 6.1, 6.75, T0 + 0.25, T0 + 0.29, "black")
wb.box(-6.9, -3.0, 6.78, 6.85, T0 + 1.1, T0 + 2.2, "cream")              # pegboard
for k in range(9):
    x = -6.7 + k * 0.42
    c = ("navy", "terracotta", "black", "steel")[k % 4]
    wb.box(x - 0.02, x + 0.02, 6.74, 6.78, T0 + 1.35, T0 + 1.75, c)
    wb.box(x - 0.08, x + 0.08, 6.74, 6.78, T0 + 1.7, T0 + 1.78, c)
for k in range(6):
    x = -6.6 + k * 0.6
    wb.cyl((x, 6.6, T0 + 0.99), 0.05, 0.06, random.choice(("terracotta", "navy", "steel")), segs=12)
wb.box(-4.6, -3.6, 6.2, 6.6, T0 + 0.96, T0 + 1.0, "blueprint")
wb.box(-5.3, -4.9, 6.5, 6.7, T0 + 0.96, T0 + 1.2, "black")                 # little toolbox
wb.done(outline=0.008)
drone("MNI.drone_bench", (-5.7, 6.35, T0 + 1.08), 20, 0.9, "terracotta")
stand = P("MNI.drone_stand")
stand.cyl((0, 0, 0.02), 0.3, 0.04, "black")
stand.cyl((0, 0, 0.5), 0.03, 1.0, "steel", segs=10)
stand.cyl((0, 0, 1.02), 0.12, 0.04, "black")
stand.done((-3.6, 3.4, T0))
drone("MNI.drone_big", (-3.6, 3.4, T0 + 1.18), -25, 1.8, "navy")
dk = P("MNI.desk")
dk.box(0.2, 2.9, 6.1, 6.8, T0 + 0.74, T0 + 0.78, "oak")
for x in (0.3, 2.8):
    dk.box(x - 0.04, x + 0.04, 6.15, 6.75, T0, T0 + 0.74, "black")
for x, rz in ((1.0, 10), (2.1, -10)):
    dk.box(x - 0.42, x + 0.42, 6.48, 6.52, T0 + 0.95, T0 + 1.45, "black")
    dk.box(x - 0.39, x + 0.39, 6.47, 6.48, T0 + 0.98, T0 + 1.42, "mon")
    dk.box(x - 0.03, x + 0.03, 6.52, 6.56, T0 + 0.78, T0 + 0.96, "black")
dk.box(1.2, 1.9, 6.15, 6.35, T0 + 0.78, T0 + 0.8, "black")
dk.blob((2.2, 6.25, T0 + 0.84), (0.05, 0.05, 0.06), "terracotta")         # mug
dk.done(outline=0.008)
oc = P("MNI.office_chair")
oc.cyl((0, 0, 0.03), 0.3, 0.04, "black", segs=5)
oc.cyl((0, 0, 0.25), 0.03, 0.42, "steel", segs=8)
oc.box(-0.25, 0.25, -0.24, 0.24, 0.45, 0.55, "navy")
oc.box(-0.24, 0.24, 0.2, 0.27, 0.55, 1.1, "navy")
oc.done((1.55, 5.5, T0), 175)
dr = P("MNI.drafting_table")
dr.box(-0.6, 0.6, -0.4, 0.4, -0.02, 0.02, "oak", xf=Matrix.Translation((0, 0, 0.95)) @ Matrix.Rotation(math.radians(25), 4, 'X'))
dr.box(-0.52, 0.52, -0.33, 0.33, 0.02, 0.03, "blueprint", xf=Matrix.Translation((0, 0, 0.95)) @ Matrix.Rotation(math.radians(25), 4, 'X'))
for k in range(5):
    dr.box(-0.4 + k * 0.18, -0.38 + k * 0.18, -0.25, 0.25, 0.03, 0.035, "bp_line",
           xf=Matrix.Translation((0, 0, 0.95)) @ Matrix.Rotation(math.radians(25), 4, 'X'))
dr.box(-0.4, 0.4, -0.02, 0.0, 0.03, 0.035, "bp_line", xf=Matrix.Translation((0, 0, 0.95)) @ Matrix.Rotation(math.radians(25), 4, 'X'))
for sx in (-1, 1):
    dr.beam((sx * 0.5, -0.3, 0), (sx * 0.5, 0.0, 0.9), 0.05, 0.05, "black")
    dr.beam((sx * 0.5, 0.3, 0), (sx * 0.5, 0.0, 0.9), 0.05, 0.05, "black")
dr.done((-0.6, 3.2, T0), 0)
stool("MNI.drafting_stool", (-0.6, 2.4, T0 - 0.1))
sh = P("MNI.workshop_shelves")
for z in (0.4, 1.0, 1.6, 2.2):
    sh.box(-7.3, -6.9, 1.5, 4.5, z - 0.02, z + 0.02, "black")
    y = 1.6
    while y < 4.3:
        bw = random.uniform(0.25, 0.5)
        sh.box(-7.25, -6.95, y, y + bw, z + 0.02, z + random.uniform(0.18, 0.4),
               random.choice(("cream", "linen", "terracotta", "navy", "oak")))
        y += bw + 0.05
for y in (1.5, 4.5):
    sh.box(-7.3, -6.9, y - 0.03, y + 0.03, T0 - T0, 2.4, "black")
sh.done((0, 0, T0), outline=0.008)
art("MNI.workshop_poster", 1.2, 0.85, (-7.28, 5.4, 8.4), 90, cols=("bp_line", "terracotta", "bp_line"), frame="blueprint")
plant("MNI.workshop_plant", (3.4, 1.2, T0), 1.2, "concrete")
for i, x in enumerate((-5.0, -1.5, 1.6)):
    pendant("MNI.workshop_pendant%d" % i, (x, 4.0, T1), 0.6, 0.28, "black")

# ================================================================ lights
for name, loc, size, e in (
        ("MNI_L_living", (-6.5, 5.3, 2.85), (6.0, 8.0), 900), ("MNI_L_kitchen", (-0.5, 5.0, 2.85), (4.5, 9.0), 700),
        ("MNI_L_hall", (4.4, 5.0, 2.85), (4.0, 9.0), 600), ("MNI_L_tower", (5.2, 5.4, 9.3), (2.6, 7.5), 700),
        ("MNI_L_bed", (-6.25, 4.6, 6.3), (5.0, 6.6), 700), ("MNI_L_nursery", (0.2, 5.1, 6.3), (6.8, 5.6), 800),
        ("MNI_L_corridor", (-2.6, 8.85, 6.3), (12.0, 1.0), 200), ("MNI_L_workshop", (-1.8, 3.8, 9.3), (10.5, 5.8), 1000)):
    area_light(name, loc, size, e)
point_light("MNI_P_living_lamp", (-4.0, 1.75, 1.6), 60)
point_light("MNI_P_chandelier", (5.85, 6.9, 4.4), 150)
point_light("MNI_P_bedlamps", (-6.25, 7.6, 4.3), 60)
point_light("MNI_P_window_kitchen", (0.7, 0.6, 1.9), 80, "#dff0fa")
point_light("MNI_P_window_nursery", (0.0, 2.6, 4.6), 120, "#dff0fa")

# ================================================================ cameras
use(IC["MNI_Cams"])


def icam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    co = bpy.data.objects.new(name, cd)
    IC["MNI_Cams"].objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


icam("MNI_cam_living", (-3.4, 8.9, 1.75), (-7.6, 2.4, 1.0), 20)
icam("MNI_cam_kitchen", (1.6, 9.5, 1.85), (-1.0, 2.0, 0.9), 20)
icam("MNI_cam_hall", (2.4, 1.0, 1.7), (5.8, 7.5, 2.2), 18)
icam("MNI_cam_bedroom", (-3.9, 1.6, 5.1), (-7.2, 7.2, 3.8), 20)
icam("MNI_cam_nursery", (3.3, 2.6, 5.0), (-1.2, 7.6, 3.9), 20)
icam("MNI_cam_workshop", (3.3, 1.2, 8.8), (-4.5, 5.6, 7.6), 20)
icam("MNI_cam_landing", (4.3, 9.1, 4.6), (5.8, 2.0, 5.6), 18)

# ================================================================ view layers
vl_ext = S.view_layers[0]
vl_ext.name = "Exterior"
vl_int = S.view_layers.get("Interior") or S.view_layers.new("Interior")


def set_excl(vl, name, ex):
    def walk(lc):
        for c in lc.children:
            if c.name == name:
                c.exclude = ex
            walk(c)
    walk(vl.layer_collection)


set_excl(vl_ext, "Mansion_Interior", True)
set_excl(vl_int, "Mansion_Interior", False)
set_excl(vl_int, "Mansion", True)
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

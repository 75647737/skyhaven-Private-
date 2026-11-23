"""Airport patch 1: the entrance gateway on the Skyway (modern, landscaped, alive).

    blender -b blender/sets/city_v002.blend --python tools/blender/build_airport_gateway.py -- <out.blend>

Built in a local frame that follows the Skyway (x = along the road towards the airport,
y = left of the road, z = up), placed where the road enters the airport grounds:
  * the gateway: two tapered white pylons with teal glass fins, a swept "wing" beam over the
    road carrying SKYHAVEN INTERNATIONAL AIRPORT on both faces, three flags each side
  * cascading waterfalls on both sides: three stone tiers with water sheets that flow
    (animated shader) into pools with dancing fountain jets
  * flower beds in waves of colour along both verges, round flower medallions, hedges,
    lawn mounds, an avenue of palms, modern lamp posts with banners
  * a WELCOME monument, an aircraft sculpture on a plinth, birds circling over the water
Animation is driven by the frame number (drivers), so any shot is "live" without keys.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(8)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {"gw_white": "#f7f6f2", "gw_teal": "#2aa6a6", "gw_glass": "#7fc3d6", "stone_a": "#b9a68c",
             "stone_b": "#9c8a73", "stone_c": "#d6c7ad", "coping": "#ece6da", "fl_red": "#e2453c",
             "fl_pink": "#f07aa8", "fl_yellow": "#f6c936", "fl_purple": "#8a5cc7", "fl_white": "#fbf8f2",
             "fl_orange": "#f28a2e", "hedge": "#3f7d3a", "mound": "#86c35a", "pole": "#3b3f46",
             "banner": "#2aa6a6", "banner2": "#f6c936", "flag_r": "#d6403a", "flag_b": "#2f6fb0",
             "bird": "#33363b", "silver": "#d5dade", "pool_edge": "#e9e3d6"}.items():
    M[k] = toon("CT_" + k, v)


def driven_value(nt, expr):
    v = nt.nodes.new('ShaderNodeValue')
    fc = v.outputs[0].driver_add("default_value")
    fc.driver.expression = expr
    return v.outputs[0]


def water(name, base, light, coord, speed, period, duty=0.22):
    """Toon water whose light streaks move: coord 'Z' falls downward, 'XY' ripples outward."""
    def fn(nt):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sx.inputs[0])
        t = driven_value(nt, "frame/24")
        if coord == 'Z':
            # vertical light streaks (by x) broken into dashes that slide down (z + time)
            xw = nmath(nt, 'ADD', sx.outputs[0], sx.outputs[1])
            wob = nmath(nt, 'MULTIPLY', nmath(nt, 'SINE', nmath(nt, 'MULTIPLY', xw, 2.3)), 0.12)
            streak = nmath(nt, 'LESS_THAN', nmath(nt, 'FRACT', nmath(nt, 'ADD', nmath(nt, 'DIVIDE', xw, 0.85), wob)), 0.16)
            off = nmath(nt, 'MULTIPLY', nmath(nt, 'FRACT', nmath(nt, 'MULTIPLY', xw, 0.37)), 3.0)
            zz = nmath(nt, 'ADD', nmath(nt, 'ADD', sx.outputs[2], nmath(nt, 'MULTIPLY', t, speed)), off)
            seg = nmath(nt, 'LESS_THAN', nmath(nt, 'FRACT', nmath(nt, 'DIVIDE', zz, 2.4)), 0.62)
            return mix(nt, nmath(nt, 'MULTIPLY', streak, seg), rgb(nt, base), rgb(nt, light))
        else:
            r = nmath(nt, 'ADD', nmath(nt, 'MULTIPLY', sx.outputs[0], sx.outputs[0]),
                      nmath(nt, 'MULTIPLY', sx.outputs[1], sx.outputs[1]))
            c = nmath(nt, 'SUBTRACT', nmath(nt, 'SQRT', r), nmath(nt, 'MULTIPLY', t, speed))
        s = nmath(nt, 'LESS_THAN', nmath(nt, 'FRACT', nmath(nt, 'DIVIDE', c, period)), duty)
        return mix(nt, s, rgb(nt, base), rgb(nt, light))
    m = toon_shader(name, fn, ks=(0.8, 0.92, 1.0))
    m.diffuse_color = lin(base) + [1]
    return m


M["fall"] = water("CT_water_fall", "#5fb3e0", "#e8f6ff", 'Z', 2.2, 0.9, 0.3)
M["pool"] = water("CT_water_pool", "#4fa6d8", "#bfe6fa", 'XY', 0.8, 1.6, 0.18)

for name in ("CT_AirportGateway",):
    old = bpy.data.collections.get(name)
    if old:
        for o in list(old.all_objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(old)
GW = bpy.data.collections.new("CT_AirportGateway")
bpy.data.collections["City"].children.link(GW)
use(GW)

# ---------------------------------------------------------------- local frame on the Skyway
A, B = Vector((1800.0, -2000.0)), Vector((2400.0, -2430.0))
D = (B - A).normalized()
G = A.lerp(B, 0.62)                                    # gateway centre on the road
HEAD = math.degrees(math.atan2(D.y, D.x))              # local +X = travel direction
LEFT = Vector((-D.y, D.x))


def W(lx, ly, z=0.0):
    p = G + D * lx + LEFT * ly
    return Vector((p.x, p.y, z))


def facing(lx_dir, ly_dir):
    """rot_z for a label whose readable face points along local (lx_dir, ly_dir)."""
    f = D * lx_dir + LEFT * ly_dir
    return math.degrees(math.atan2(f.x, -f.y))


ROAD = 14.0                                            # half width of the Skyway

# ================================================================ THE GATEWAY
g = P("CT.gateway")
for sy in (1, -1):
    y = sy * (ROAD + 7)
    g.box(-3.5, 3.5, y - 3.0, y + 3.0, 0.0, 30.0, "gw_white", taper=(0.55, 0.7))
    g.box(-0.6, 0.6, y - 3.4, y + 3.4, 2.0, 27.0, "gw_glass", taper=(0.8, 0.75))
    g.box(-4.5, 4.5, y - 4.0, y + 4.0, 0.0, 0.8, "coping")
# swept wing beam over the road (two beams that cross like a gull wing)
for sy in (1, -1):
    g.beam((0, sy * (ROAD + 7), 26.0), (2.0, 0.0, 21.0), 3.2, 1.6, "gw_white")
    g.beam((0, sy * (ROAD + 7), 24.4), (2.0, 0.0, 19.6), 3.0, 0.35, "gw_teal")
g.box(-1.8, 1.8, -12.0, 12.0, 18.2, 21.0, "gw_white")             # sign band
g.box(-1.85, 1.85, -11.6, 11.6, 18.4, 18.8, "gw_teal")
g.done(G.to_3d(), HEAD, outline=0.12)
for face, lx in ((-1, -1.9), (1, 1.9)):
    p = W(lx, 0.0, 19.6)
    label("CT.gateway_sign_%s" % ("in" if face < 0 else "out"), "SKYHAVEN INTERNATIONAL AIRPORT",
          p, facing(face, 0), 0.95, M["gw_teal"] if face < 0 else M["gw_white"], 0.12)
    label("CT.gateway_sign2_%s" % ("in" if face < 0 else "out"), "WELCOME  -  KARIBU",
          W(lx, 0.0, 18.95 - 0.55), facing(face, 0), 0.5, M["gw_white"] if face < 0 else M["gw_teal"], 0.06)

# flags (they sway)
FLAG_COLS = ["flag_r", "gw_teal", "flag_b", "fl_yellow", "gw_white", "flag_r"]
k = 0
for sy in (1, -1):
    for j in range(3):
        lx, ly = -52 - j * 7, sy * (ROAD + 13)
        pole = P("CT.flagpole_%d" % k)
        pole.cyl((0, 0, 7.5), 0.12, 15.0, "silver", segs=8)
        pole.blob((0, 0, 15.1), (0.25, 0.25, 0.25), "silver")
        pole.done(W(lx, ly), HEAD, outline=0.02)
        fl = P("CT.flag_%d" % k)
        fl.box(0.0, 4.2, -0.04, 0.04, 12.0, 14.6, FLAG_COLS[k])
        fob = fl.done(W(lx, ly, 0.0), HEAD + 180, outline=0.02)
        fc = fob.driver_add("rotation_euler", 2)
        fc.driver.expression = "%.4f + 0.22*sin(frame*0.13 + %.2f)" % (math.radians(HEAD + 160), k * 1.3)
        k += 1

# ================================================================ WATERFALLS
for sy in (1, -1):
    tiers = [(10.5, 70.0, 54.0), (7.0, 54.0, 44.0), (3.8, 44.0, 34.0)]   # (top z, outer y, inner y)
    wf = P("CT.waterfall_%s" % ("L" if sy > 0 else "R"))
    x0, x1 = -38.0, 38.0
    for ztop, yo, yi in tiers:
        a, b = sorted((sy * yo, sy * yi))
        wf.box(x0, x1, a, b, 0.0, ztop, "stone_b")
        wf.box(x0 - 0.3, x1 + 0.3, a - 0.2 if sy < 0 else a, b + 0.2 if sy > 0 else b, ztop, ztop + 0.35, "coping")
        # stone courses on the face that looks at the road
        face = sy * yi
        z = 0.0
        row = 0
        while z < ztop - 0.1:
            h = min(0.55, ztop - z)
            x = x0 + (0.6 if row % 2 else 0.0)
            while x < x1 - 0.1:
                w = min(random.uniform(1.6, 3.2), x1 - x)
                wf.box(x + 0.06, x + w - 0.06, face - 0.12 if sy > 0 else face, face if sy > 0 else face + 0.12,
                       z + 0.05, z + h - 0.05, random.choice(("stone_a", "stone_a", "stone_c", "stone_b")))
                x += w
            z += h
            row += 1
        # water sheets spilling over the lip (in the middle 60 %), slightly in front of the face
        fy = face - 0.35 * sy
        wf.box(-24.0, 24.0, min(fy, fy - 0.12 * sy), max(fy, fy - 0.12 * sy), 0.3, ztop + 0.36, "fall")
        wf.box(-24.0, 24.0, min(face, face + 6.0 * sy), max(face, face + 6.0 * sy), ztop + 0.34, ztop + 0.44, "pool")
        for q in range(40):                                    # foam where the sheet lands
            fx = -23.5 + q * 1.2 + random.uniform(-0.3, 0.3)
            fz = (tiers[tiers.index((ztop, yo, yi)) + 1][0] + 0.4) if (ztop, yo, yi) != tiers[-1] else 0.75
            wf.blob((fx, fy - 0.6 * sy, fz), (0.75, 0.55, 0.42), "fl_white", subdiv=1)
        for q in range(26):                                    # plants along the tier edge
            px = x0 + 1.0 + q * 2.9
            if -25 < px < 25:
                continue
            wf.blob((px, face + 0.9 * sy, ztop + 0.9), (0.9, 0.7, 0.7), random.choice(("hedge", "fl_pink", "fl_yellow")), subdiv=1)
    # pool at the bottom
    a, b = sorted((sy * 34.0, sy * 24.0))
    wf.box(x0 - 2, x1 + 2, a - (0.8 if sy < 0 else 0), b + (0.8 if sy > 0 else 0), 0.0, 0.7, "pool_edge")
    wf.box(x0 - 1.2, x1 + 1.2, a, b, 0.0, 0.62, "pool")
    wf.done(G.to_3d(), HEAD, outline=0.06)
    # dancing fountain jets in the pool
    for j in range(7):
        lx = -30 + j * 10
        ly = sy * 29.0
        jt = P("CT.fountain_%s%d" % ("L" if sy > 0 else "R", j))
        jt.cyl((0, 0, 1.6), 0.28, 2.0, "fall", segs=10, r2=0.12)
        jt.blob((0, 0, 2.7), (0.6, 0.6, 0.45), "fl_white", subdiv=1)
        job = jt.done(W(lx, ly, 0.6), HEAD, outline=0.0)
        f = job.driver_add("scale", 2)
        f.driver.expression = "1.0 + 0.45*sin(frame*0.35 + %.2f)" % (j * 0.9 + (0 if sy > 0 else 2))

# ================================================================ FLOWERS, HEDGES, LAWNS
FL = ["fl_red", "fl_pink", "fl_yellow", "fl_purple", "fl_white", "fl_orange"]
M["leafy_g"] = toon("CT_leafy_g", "#4f9a3c")


KIND_OF = {"fl_red": ("hibiscus", "tulip"), "fl_pink": ("cosmos",), "fl_yellow": ("tulip_y", "marigold"),
           "fl_purple": ("violet",), "fl_white": ("daisy",), "fl_orange": ("marigold",)}
FLOWER_T = {k: flower_template(k) for k in FLOWER_KINDS}
FLOWERS = []          # (template, root-space location, rotation, scale) -> one merged mesh at the end


def flower_bush(p, x, y, z, col, s=1.0, origin=None, head=None):
    """Green foliage mound (in piece p) with 4-6 real flowers of one kind standing out of it."""
    p.blob((x, y, z + 0.12 * s), (0.8 * s, 0.8 * s, 0.25 * s), "leafy_g", subdiv=1)
    o = origin if origin is not None else G
    hd = math.radians(head if head is not None else HEAD)
    ca, sa = math.cos(hd), math.sin(hd)
    for q in range(random.randint(4, 6)):
        fx, fy = x + random.uniform(-0.55, 0.55) * s, y + random.uniform(-0.55, 0.55) * s
        wx, wy = o.x + ca * fx - sa * fy, o.y + sa * fx + ca * fy
        FLOWERS.append((FLOWER_T[random.choice(KIND_OF[col])], (wx, wy, z), random.uniform(0, 6.28),
                        s * random.uniform(0.8, 1.15)))


fb = P("CT.gateway_flowers")
for sy in (1, -1):
    for lx in range(-220, 221, 3):
        if -40 < lx < 40:
            continue
        for j in range(3):                                       # three rows of flowers in waves
            ly = sy * (ROAD + 2.2 + j * 1.5)
            band = int((lx / 18.0 + j * 0.7 + (0 if sy > 0 else 3)) % len(FL))
            for q in range(2):
                fx = lx + q * 1.5 + random.uniform(-0.3, 0.3)
                flower_bush(fb, fx, ly + random.uniform(-0.3, 0.3), 0.0, FL[band])
        fb.box(lx - 1.5, lx + 1.5, sy * (ROAD + 1.0) - 0.3, sy * (ROAD + 1.0) + 0.3, 0.0, 0.8, "hedge")
        fb.box(lx - 1.5, lx + 1.5, sy * (ROAD + 7.2) - 0.35, sy * (ROAD + 7.2) + 0.35, 0.0, 1.0, "hedge")
    # round flower medallions on the lawns beside the waterfalls
    for cx in (-70.0, 70.0):
        cy = sy * 46.0
        fb.cyl((cx, cy, 0.12), 13.0, 0.24, "hedge", segs=40)
        for ring, col in enumerate(("fl_white", "fl_red", "fl_yellow", "fl_pink", "fl_purple")):
            r = 11.5 - ring * 2.3
            n = max(6, int(2 * math.pi * r / 1.2))
            for q in range(n):
                a = q / n * math.tau
                flower_bush(fb, cx + math.cos(a) * r, cy + math.sin(a) * r, 0.2, col, 0.9)
        fb.cyl((cx, cy, 1.0), 0.8, 2.0, "gw_white", segs=16)
        fb.blob((cx, cy, 2.4), (1.2, 1.2, 0.8), "fl_red", subdiv=1)
fb.done(G.to_3d(), HEAD, outline=0.015)
lawn = P("CT.gateway_lawns")
for sy in (1, -1):
    lawn.box(-260, 260, min(sy * (ROAD + 0.5), sy * 95), max(sy * (ROAD + 0.5), sy * 95), -0.05, 0.03, "mound")
    for cx, cy, r in ((-140, 55, 22), (130, 60, 26), (-200, 70, 18), (200, 48, 16)):
        lawn.blob((cx, sy * cy, 0.0), (r, r * 0.7, 2.4), "mound", subdiv=2)
lawn.done(G.to_3d(), HEAD, outline=0.0)

# palms and lamp posts along both verges
PALM = bpy.data.objects.get("CT.palm_t")
lp = P("CT.gateway_lamps")
for sy in (1, -1):
    for lx in range(-240, 241, 24):
        if -44 < lx < 44:
            continue
        ly = sy * (ROAD + 10.5)
        if PALM:
            o = bpy.data.objects.new("CT.gw_palm", PALM.data)
            GW.objects.link(o)
            o.parent = RIG
            o.location = W(lx, ly)
            o.rotation_euler.z = random.uniform(0, 6.28)
            o.scale = (random.uniform(0.95, 1.2),) * 3
            for m in PALM.modifiers:
                n = o.modifiers.new(m.name, m.type)
                n.thickness, n.offset, n.use_flip_normals, n.material_offset = m.thickness, m.offset, True, m.material_offset
        lx2 = lx + 12
        if -44 < lx2 < 44:
            continue
        ly2 = sy * (ROAD + 4.6)
        lp.box(lx2 - 0.15, lx2 + 0.15, ly2 - 0.15, ly2 + 0.15, 0.0, 9.0, "pole")
        lp.beam((lx2, ly2, 9.0), (lx2, ly2 - sy * 3.0, 9.6), 0.25, 0.2, "pole")
        lp.box(lx2 - 0.4, lx2 + 0.4, ly2 - sy * 3.0 - 0.6, ly2 - sy * 3.0 + 0.6, 9.3, 9.6, "glow" if "glow" in M else "fl_white")
        lp.box(lx2 - 0.05, lx2 + 0.05, ly2 - 0.02 - 0.9, ly2 + 0.02 - 0.9, 5.0, 8.0, "banner")
        lp.box(lx2 - 0.05, lx2 + 0.05, ly2 + 0.9 - 0.02, ly2 + 0.9 + 0.02, 5.0, 8.0, "banner2")
        lp.box(lx2 - 0.05, lx2 + 0.05, ly2 - 0.9, ly2 + 0.9, 7.95, 8.05, "pole")
lp.done(G.to_3d(), HEAD, outline=0.02)

# WELCOME monument before the gateway, aircraft sculpture on a plinth
mon = P("CT.welcome_monument")
mon.box(-2.0, 2.0, -12.0, 12.0, 0.0, 4.2, "stone_c")
mon.box(-2.2, 2.2, -12.3, 12.3, 4.2, 4.5, "coping")
mon.box(-2.6, 2.6, -13.0, 13.0, 0.0, 0.4, "coping")
for q in range(24):
    flower_bush(mon, -3.4, -11.5 + q, 0.0, FL[q % len(FL)], 0.9, origin=W(-120.0, -(ROAD + 26.0)), head=HEAD - 25)
MON_LX, MON_LY = -120.0, -(ROAD + 26.0)
mon.done(W(MON_LX, MON_LY), HEAD - 25, outline=0.04)
label("CT.welcome_text", "WELCOME TO SKYHAVEN INTERNATIONAL", W(MON_LX - 2.05, MON_LY, 2.6),
      HEAD - 25 + 90, 0.95, M["gw_teal"], 0.06)
ped = P("CT.sculpture_plinth")
ped.cyl((0, 0, 1.0), 6.0, 2.0, "coping", segs=32)
ped.beam((0, 0, 2.0), (2.0, 0, 13.0), 0.9, 0.9, "silver")
ped.done(W(150, 46), HEAD, outline=0.05)
JET = bpy.data.objects.get("CT.jet_t")
if JET:
    sc = bpy.data.objects.new("CT.sculpture_jet", JET.data)
    GW.objects.link(sc)
    sc.parent = RIG
    sc.location = W(152, 46, 13.5)
    sc.rotation_euler = (math.radians(-22), math.radians(8), math.radians(HEAD + 90))
    sc.scale = (0.45,) * 3
    for m in JET.modifiers:
        n = sc.modifiers.new(m.name, m.type)
        n.thickness, n.offset, n.use_flip_normals, n.material_offset = m.thickness, m.offset, True, m.material_offset

# birds circling over the waterfalls
for b in range(7):
    bd = P("CT.bird_%d" % b)
    bd.beam((0, 0, 0), (-0.9, 0.7, 0.35), 0.18, 0.06, "bird")
    bd.beam((0, 0, 0), (0.9, 0.7, 0.35), 0.18, 0.06, "bird")
    bd.blob((0, 0.1, 0), (0.16, 0.35, 0.14), "bird", subdiv=1)
    bob = bd.done(outline=0.0)
    sy = 1 if b % 2 == 0 else -1
    c = W(random.uniform(-20, 20), sy * 52)
    r = random.uniform(14, 30)
    ph = b * 0.9
    sp = random.uniform(0.012, 0.022)
    h = random.uniform(18, 32)
    for ax, expr in ((0, "%.2f + %.2f*cos(frame*%.4f + %.2f)" % (c.x, r, sp, ph)),
                     (1, "%.2f + %.2f*sin(frame*%.4f + %.2f)" % (c.y, r, sp, ph)),
                     (2, "%.2f + 1.5*sin(frame*0.05 + %.2f)" % (h, ph))):
        f = bob.driver_add("location", ax)
        f.driver.expression = expr
    f = bob.driver_add("rotation_euler", 2)
    f.driver.expression = "frame*%.4f + %.2f" % (sp, ph)
    bob.scale = (2.2,) * 3

scatter("CT.gateway_flower_heads", GW, FLOWERS, outline=0.004)

# merge the static pieces (keeps EEVEE happy), animated ones stay separate
consolidate(GW, ("CT.flag_", "CT.fountain_", "CT.bird_", "CT.sculpture_jet"))


# ================================================================ cameras
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 1.0, 16000
    co = bpy.data.objects.new(name, cd)
    bpy.data.collections["CT_Cams"].objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


cam("CT_cam_gateway", W(-170, -10.5, 3.2), W(0, 0, 14), 30)
cam("CT_cam_gateway_waterfall", W(-30, 9, 2.6), W(6, 46, 3.6), 24)
cam("CT_cam_gateway_aerial", W(-210, -150, 85), W(10, 0, 4), 30)
cam("CT_cam_gateway_flowers", W(-75, -16.5, 1.6), W(-40, -18, 1.0), 26)

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

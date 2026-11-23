"""Inside the terminal (Departures): commercial wing + the Skytrade Aviation private wing.

    blender -b blender/sets/city_v004.blend --python tools/blender/build_terminal_interior.py -- <out.blend>

The terminal is x 2800..3800, y -2700 (airside) .. -2610 (kerb side), real metres under CT.root.
  Commercial wing (x 2805..3488): check-in islands with desks, screens and baggage belts, departure
      boards, INFORMATION desk, security lanes (scanners and arches), airside shops, a cafe,
      gate seating and tall windows to the apron.
  Skytrade Aviation private wing (x 3492..3795), own entrance from the kerb (sign reads
      SKYTRADE AVIATION): reception with a navy feature wall, the Skytrade Aviation lounge
      (sofas, armchairs, bar, a model jet), glass-walled offices, a meeting room, an operations
      room with a flight board, and the door to the private apron.
Navy / cream / white with a thin red pinstripe (the Skytrade livery from the blueprint).
Interior collection "CT_TerminalInterior"; view layer "Terminal" shows it with the exterior
terminal hidden (the default view layer hides the interior). Cameras CT_cam_t_*.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(21)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {
    "t_floor": "#e9e4da", "t_floor_ln": "#d3ccbf", "t_wall": "#f4f1ea", "t_ceiling": "#fbfaf6", "t_column": "#e6e1d7",
    "st_navy": "#1f2f57", "st_navy2": "#2c3f6e", "st_cream": "#efe6d2", "st_red": "#c8302c", "st_wood": "#b07c4f",
    "st_marble": "#f3f0ea", "st_marble_ln": "#ddd6ca", "st_leather": "#8a5a3a", "st_glass": "#cfe6ee",
    "desk_w": "#f6f4ef", "desk_g": "#8f949b", "belt": "#2e3035", "screen": "#1b2533", "seat_b": "#3b5f8f",
    "seat_g": "#5f6670", "shop_a": "#d9572b", "shop_b": "#2f8f8a", "shop_c": "#f2c14e", "cafe": "#6b4a32",
    "rug_n": "#33456f", "plant_g": "#4f8a3c", "plant_g2": "#6aa84f", "pot_w": "#f1ece3", "steel2": "#c9ced3",
    "skin_a": "#f0c6a0", "skin_b": "#c68a5e", "skin_c": "#8d5a3b", "uniform_st": "#1f2f57", "shirt_w": "#fbfaf6",
    "trouser_d": "#33363b", "case_r": "#c8463a", "case_b": "#3f6fa8", "hair_d": "#2a1a12", "hair_b": "#a3743f"}.items():
    M[k] = toon("CT_" + k, v)


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


M["day"] = emit("CT_t_day", "#dff0fa")
M["glow"] = emit("CT_t_glow", "#fff1c9", 1.3)
M["scr_blue"] = emit("CT_t_scr_blue", "#3d6ea8", 0.9)
M["scr_text"] = emit("CT_t_scr_text", "#ffd45a", 1.2)
M["scr_white"] = emit("CT_t_scr_white", "#eef4fa", 1.1)
M["skylight"] = emit("CT_t_skylight", "#e8f4fc", 1.0)
gm = bpy.data.materials.get("CT_t_clear_glass") or bpy.data.materials.new("CT_t_clear_glass")
gm.use_nodes = True
_nt = gm.node_tree
_nt.nodes.clear()
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent')
_em = _nt.nodes.new('ShaderNodeEmission')
_em.inputs[0].default_value = lin("#cfe6ee") + [1]
_mx = _nt.nodes.new('ShaderNodeMixShader')
_mx.inputs[0].default_value = 0.15
_nt.links.new(_tr.outputs[0], _mx.inputs[1])
_nt.links.new(_em.outputs[0], _mx.inputs[2])
_nt.links.new(_mx.outputs[0], _nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
if hasattr(gm, "surface_render_method"):
    gm.surface_render_method = 'BLENDED'
M["clear_glass"] = gm

old = bpy.data.collections.get("CT_TerminalInterior")
if old:
    for o in list(old.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
TI = bpy.data.collections.new("CT_TerminalInterior")
bpy.data.collections["City"].children.link(TI)
use(TI)

X0, X1, YF, YA = 2803.0, 3797.0, -2611.5, -2698.5         # inner faces
F0, CEIL = 0.15, 10.0
WING = 3490.0                                             # partition between the wings

# ================================================================ shell
sh = P("CT.t_shell")
sh.box(X0, X1, YA, YF, F0 - 0.1, F0, "t_floor")
y = YA + 3.0
while y < YF:                                             # floor tile joints
    sh.box(X0, WING, y - 0.02, y + 0.02, F0, F0 + 0.004, "t_floor_ln")
    y += 3.0
x = X0 + 3.0
while x < WING:
    sh.box(x - 0.02, x + 0.02, YA, YF, F0, F0 + 0.004, "t_floor_ln")
    x += 3.0
sh.box(WING, X1, YA, YF, F0, F0 + 0.01, "st_marble")       # Skytrade wing: marble
x = WING + 2.0
while x < X1:
    sh.box(x - 0.015, x + 0.015, YA, YF, F0 + 0.01, F0 + 0.014, "st_marble_ln")
    x += 2.0
sh.box(X0, X1, YA, YF, CEIL, CEIL + 0.3, "t_ceiling")      # ceiling
for x in range(2840, 3480, 60):                           # skylight strips (commercial)
    sh.box(x, x + 6, YA + 6, YF - 6, CEIL - 0.02, CEIL, "skylight")
sh.box(X0 - 0.3, X0, YA, YF, F0, CEIL, "t_wall")           # end walls
sh.box(X1, X1 + 0.3, YA, YF, F0, CEIL, "t_wall")
# front (kerb) wall: glass from 0.4 to 7, three entrances (3000, 3300 commercial; 3600 Skytrade)
sh.box(X0, X1, YF, YF + 0.3, 7.0, CEIL, "t_wall")
sh.box(X0, X1, YF, YF + 0.3, F0, 0.4, "t_wall")
sh.box(X0, X1, YF + 0.05, YF + 0.15, 0.4, 7.0, "day")
for x in range(int(X0) + 6, int(X1), 6):                   # mullions
    sh.box(x - 0.08, x + 0.08, YF - 0.05, YF + 0.05, 0.4, 7.0, "frame")
sh.box(X0, X1, YF - 0.05, YF + 0.05, 3.6, 3.75, "frame")
# airside wall: tall windows to the apron
sh.box(X0, X1, YA - 0.3, YA, 8.5, CEIL, "t_wall")
sh.box(X0, X1, YA - 0.3, YA, F0, 0.5, "t_wall")
sh.box(X0, X1, YA - 0.15, YA - 0.05, 0.5, 8.5, "day")
for x in range(int(X0) + 5, int(X1), 5):
    sh.box(x - 0.1, x + 0.1, YA - 0.02, YA + 0.06, 0.5, 8.5, "frame")
# columns
for x in range(2830, 3480, 30):
    for yy in (-2628.0, -2682.0):
        sh.cyl((x, yy, (F0 + CEIL) / 2), 0.45, CEIL - F0, "t_column", segs=16)
# partition between the wings (a door, kept closed)
sh.box(WING - 0.15, WING + 0.15, YA, YF, F0, CEIL, "t_wall")
sh.done(outline=0.02)

# ================================================================ COMMERCIAL WING
# --- check-in islands: desks facing the entrance, a belt behind, a backlit panel with screens
ISL = [(2870, 2975), (3025, 3130), (3170, 3275), (3325, 3430)]
ck = P("CT.t_checkin")
for (a, b) in ISL:
    yb = -2640.0
    ck.box(a, b, yb - 1.4, yb + 1.4, F0, F0 + 0.5, "belt")                # baggage belt
    ck.box(a, b, yb - 1.2, yb + 1.2, F0 + 0.5, F0 + 0.55, "steel2")
    ck.box(a, b, yb - 3.2, yb - 1.6, F0, F0 + 3.6, "st_cream")            # back panel
    ck.box(a, b, yb + 1.6, yb + 1.9, F0 + 0.0, F0 + 1.1, "desk_w")       # desk run (front)
    n = int((b - a) / 3.5)
    for k in range(n):
        x = a + 1.75 + k * 3.5
        ck.box(x - 1.3, x + 1.3, yb + 1.9, yb + 2.9, F0, F0 + 1.05, "desk_w")
        ck.box(x - 1.35, x + 1.35, yb + 1.85, yb + 2.95, F0 + 1.05, F0 + 1.12, "desk_g")
        ck.box(x - 0.3, x + 0.3, yb + 2.0, yb + 2.1, F0 + 1.12, F0 + 1.55, "screen")
        ck.box(x - 0.6, x + 0.6, yb + 1.0, yb + 1.9, F0, F0 + 0.35, "steel2")   # scale
        ck.box(x - 0.5, x + 0.5, yb - 1.55, yb - 1.5, F0 + 2.4, F0 + 3.3, "scr_blue")
    ck.box(a + 2, b - 2, yb + 1.92, yb + 1.95, F0 + 0.55, F0 + 0.75, "seat_b")       # blue band
for (a, b) in ISL:                                        # queue posts
    for k in range(int((b - a) / 4)):
        x = a + 2 + k * 4
        for yy in (-2632.0, -2629.0):
            ck.cyl((x, yy, F0 + 0.5), 0.05, 1.0, "steel2", segs=8)
        ck.box(x, x + 4, -2632.03, -2631.97, F0 + 0.92, F0 + 0.96, "seat_b")
ck.done(outline=0.012)
for i, (a, b) in enumerate(ISL):
    label("CT.t_isl_%d" % i, "CHECK-IN  %s" % "ABCD"[i], ((a + b) / 2, -2643.25, F0 + 3.1), 180, 1.0, M["st_navy"], 0.05)
# departure boards hanging from the ceiling, facing the entrance
db = P("CT.t_boards")
for x in (2930, 3150, 3370):
    db.box(x - 6, x + 6, -2622.2, -2621.8, 6.0, 8.6, "screen")
    db.box(x - 0.1, x + 0.1, -2622.05, -2621.95, 8.6, CEIL, "frame")
    for r in range(6):
        z = 8.2 - r * 0.38
        db.box(x - 5.6, x - 1.0, -2621.82, -2621.78, z - 0.1, z + 0.1, "scr_text")
        db.box(x - 0.6, x + 2.2, -2621.82, -2621.78, z - 0.1, z + 0.1, "scr_white")
        db.box(x + 2.6, x + 5.6, -2621.82, -2621.78, z - 0.1, z + 0.1, "scr_text" if r % 3 else "scr_blue")
db.done(outline=0.01)
for x in (2930, 3150, 3370):
    label("CT.t_board_title_%d" % x, "DEPARTURES", (x, -2621.75, 8.85), 180, 0.55, M["scr_white"], 0.02)
# information desk (round) between the entrances
inf = P("CT.t_info")
inf.cyl((3150, -2626, F0 + 0.55), 2.6, 1.1, "desk_w", segs=40)
inf.cyl((3150, -2626, F0 + 1.12), 2.7, 0.06, "desk_g", segs=40)
inf.cyl((3150, -2626, F0 + 0.6), 2.05, 1.2, "t_floor", segs=40)
inf.box(3149, 3151, -2626.1, -2625.9, F0 + 1.15, 3.4, "steel2")
inf.box(3147.5, 3152.5, -2626.15, -2625.85, 3.4, 4.2, "st_navy")
inf.done(outline=0.012)
label("CT.t_info_sign", "INFORMATION", (3150, -2625.8, 3.8), 180, 0.42, M["scr_white"], 0.02)
# security: a wall with lanes, scanners and walk-through arches
sec = P("CT.t_security")
sec.box(X0, WING - 0.2, -2656.3, -2655.7, F0, 3.2, "st_cream")
sec.box(X0, WING - 0.2, -2656.3, -2655.7, 3.2, 3.6, "st_navy")
for k in range(8):
    x = 3000 + k * 40 / 1.0 * 0.6
    sec.box(x - 2.6, x + 2.6, -2656.4, -2655.6, F0, 3.2, "t_ceiling")          # opening (light)
    sec.box(x - 2.4, x - 0.6, -2659.0, -2653.0, F0, F0 + 0.9, "seat_g")        # x-ray belt
    sec.box(x - 2.2, x - 0.8, -2657.2, -2654.8, F0 + 0.9, F0 + 2.0, "desk_g")  # scanner tunnel
    sec.box(x + 0.4, x + 0.6, -2656.2, -2655.8, F0, F0 + 2.4, "steel2")        # arch
    sec.box(x + 1.7, x + 1.9, -2656.2, -2655.8, F0, F0 + 2.4, "steel2")
    sec.box(x + 0.4, x + 1.9, -2656.2, -2655.8, F0 + 2.3, F0 + 2.5, "steel2")
sec.done(outline=0.012)
label("CT.t_sec_sign", "SECURITY  -  ALL GATES", (3110, -2655.6, 3.4), 180, 0.38, M["scr_white"], 0.02)
# airside: shops along the security wall, a cafe, seating rows facing the windows
sp = P("CT.t_airside")
for x, col in ((2870, "shop_a"), (2930, "shop_b")):
    sp.box(x - 25, x + 25, -2667.0, -2657.0, F0, 0.2, "t_floor")
    sp.box(x - 25, x + 25, -2667.2, -2666.8, F0, 3.4, "day")
    sp.box(x - 25, x + 25, -2667.3, -2666.7, 3.4, 4.0, col)
    for k in range(5):
        xx = x - 20 + k * 10
        sp.box(xx - 2, xx + 2, -2662.0, -2660.0, F0, 1.8, col)
cf = 3420
sp.box(cf - 30, cf + 30, -2667.3, -2666.7, 3.4, 4.0, "cafe")
sp.box(cf - 12, cf + 12, -2664.0, -2662.0, F0, 1.1, "cafe")
sp.box(cf - 12.2, cf + 12.2, -2664.1, -2661.9, 1.1 + F0, 1.18 + F0, "st_cream")
for k in range(6):
    x = cf - 20 + k * 8
    sp.cyl((x, -2675.0, F0 + 0.37), 0.5, 0.05, "st_wood", segs=16)
    sp.cyl((x, -2675.0, F0 + 0.19), 0.05, 0.37, "frame", segs=6)
    for a in (0, math.pi):
        sp.box(x + math.cos(a) * 0.9 - 0.25, x + math.cos(a) * 0.9 + 0.25, -2675.25, -2674.75, F0, F0 + 0.45, "cafe")
# gate seating: rows of linked seats facing the windows
for xs in (2990, 3100, 3210, 3320):
    for row in range(4):
        yy = -2680.0 - row * 3.0
        sp.box(xs - 20, xs + 20, yy - 0.3, yy + 0.3, F0, F0 + 0.38, "frame")
        for k in range(20):
            x = xs - 19 + k * 2.0
            sp.box(x - 0.85, x + 0.85, yy - 0.3, yy + 0.35, F0 + 0.42, F0 + 0.5, "seat_b")
            sp.box(x - 0.85, x + 0.85, yy + 0.3, yy + 0.45, F0 + 0.5, F0 + 1.05, "seat_b")
for x, g in ((2960, "A1  A2"), (3240, "A3  A4"), (3460, "A5  A6")):
    sp.box(x - 3, x + 3, -2693.2, -2692.8, 5.0, 6.2, "screen")
sp.done(outline=0.012)
for x, g in ((2960, "GATES A1 - A2"), (3240, "GATES A3 - A4"), (3460, "GATES A5 - A6")):
    label("CT.t_gate_" + g[-2:], g, (x, -2692.75, 5.6), 180, 0.45, M["scr_text"], 0.02)
for x, nm in ((2870, "DUTY FREE"), (2930, "BOOKS & GIFTS"), (3420, "SKYHAVEN CAFE")):
    label("CT.t_shop_%d" % x, nm, (x, -2667.35, 3.7), 0, 0.42, M["shirt_w"], 0.03)

# ================================================================ SKYTRADE AVIATION PRIVATE WING
# a suite of believable size (x 3540..3660) inside the wing; the rest is back-of-house
SA, SB, SC = 3540.0, 3660.0, 5.0                          # suite x range, suite ceiling height
sw = P("CT.st_suite_shell")
for x in (SA, SB):
    sw.box(x - 0.15, x + 0.15, YA, YF, F0, CEIL, "t_wall")
sw.box(SA, SB, YA, YF, SC, SC + 0.25, "st_wood")          # warm timber ceiling
for k in range(12):
    x = SA + 5 + k * 10
    sw.box(x - 0.15, x + 0.15, YA, YF, SC - 0.25, SC, "st_cream")
# reception room x 3570..3630, y up to -2636; feature wall with openings to the lounge at both ends
sw.box(3569.85, 3570.15, -2636.0, YF, F0, SC, "t_wall")
sw.box(3629.85, 3630.15, -2636.0, YF, F0, SC, "t_wall")
sw.box(3577.0, 3623.0, -2636.4, -2636.0, F0, SC, "st_navy")
sw.box(3577.0, 3623.0, -2636.0, -2635.94, 2.2, 2.27, "st_red")
sw.box(3577.0, 3623.0, -2636.0, -2635.95, F0, 0.35, "st_wood")
sw.box(SA, 3570.0, -2636.4, -2636.0, F0, SC, "t_wall")
sw.box(3630.0, SB, -2636.4, -2636.0, F0, SC, "t_wall")
# offices block x 3540..3598 behind glass fronts facing the lounge
sw.box(3597.85, 3598.15, YA, -2636.4, SC - 0.6, SC, "t_wall")
sw.done(outline=0.015)

skr = P("CT.st_reception")
for k in range(24):                                       # curved reception desk
    a0 = math.radians(200 + k * 140 / 24)
    a1 = math.radians(200 + (k + 1) * 140 / 24)
    c = Vector((3600, -2622.0))
    pa = [c + Vector((math.cos(a0), math.sin(a0))) * r for r in (5.0, 5.9)]
    pb = [c + Vector((math.cos(a1), math.sin(a1))) * r for r in (5.0, 5.9)]
    xs = [q.x for q in pa + pb]; ys = [q.y for q in pa + pb]
    skr.box(min(xs), max(xs), min(ys), max(ys), F0, F0 + 1.05, "st_navy")
    skr.box(min(xs) - 0.05, max(xs) + 0.05, min(ys) - 0.05, max(ys) + 0.05, F0 + 1.05, F0 + 1.13, "desk_w")
    skr.box(min(xs), max(xs), min(ys) - 0.02, max(ys) + 0.02, F0 + 0.62, F0 + 0.66, "st_red")
for x in (3597, 3603):
    skr.box(x - 0.5, x + 0.5, -2628.2, -2627.6, F0 + 1.13, F0 + 1.5, "screen")
skr.box(3594, 3606, -2614.0, -2611.6, F0, F0 + 0.02, "rug_n")
for x in (3574, 3626):                                    # waiting chairs either side
    for k in range(3):
        y = -2616 - k * 4
        skr.box(x - 1.0, x + 1.0, y - 1.0, y + 1.0, F0, F0 + 0.45, "st_leather")
        skr.box(x - 1.0 if x < 3600 else x + 0.7, x - 0.7 if x < 3600 else x + 1.0, y - 1.0, y + 1.0, F0 + 0.45, F0 + 1.05, "st_leather")
for x, y in ((3573, -2633), (3627, -2633)):
    skr.cyl((x, y, F0 + 0.45), 0.6, 0.9, "pot_w", segs=16, r2=0.45)
    for k in range(7):
        a = k / 7 * math.tau
        skr.blob((x + math.cos(a) * 0.4, y + math.sin(a) * 0.4, F0 + 1.3 + random.uniform(0, 0.8)), (0.45, 0.45, 0.6),
                 random.choice(("plant_g", "plant_g2")), subdiv=1)
for x in range(3580, 3621, 8):                            # pendant lights
    skr.cyl((x, -2626, SC - 0.6), 0.01, 1.2, "frame", segs=4)
    skr.cyl((x, -2626, SC - 1.3), 0.35, 0.3, "st_navy", r2=0.06, segs=16)
    skr.cyl((x, -2626, SC - 1.44), 0.22, 0.02, "glow", segs=12)
skr.done(outline=0.015)
label("CT.st_wall_logo", "SKYTRADE AVIATION", (3600, -2635.88, 3.55), 180, 1.25, M["shirt_w"], 0.06)
label("CT.st_wall_tag", "PRIVATE  JET  CHARTER", (3600, -2635.88, 2.75), 180, 0.42, M["st_cream"], 0.04)


def sofa(p, x, y, rot, w=3.2, col="st_cream", cush="st_navy2"):
    ca, sa = math.cos(rot), math.sin(rot)
    def tr(lx, ly):
        return x + ca * lx - sa * ly, y + sa * lx + ca * ly
    def bx(lx0, lx1, ly0, ly1, z0, z1, m):
        pts = [tr(a, b) for a in (lx0, lx1) for b in (ly0, ly1)]
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        p.box(min(xs), max(xs), min(ys), max(ys), z0, z1, m)
    bx(-w / 2, w / 2, -0.5, 0.5, F0 + 0.1, F0 + 0.45, col)
    bx(-w / 2, w / 2, 0.3, 0.5, F0 + 0.45, F0 + 0.95, col)
    bx(-w / 2, -w / 2 + 0.22, -0.5, 0.5, F0 + 0.45, F0 + 0.7, col)
    bx(w / 2 - 0.22, w / 2, -0.5, 0.5, F0 + 0.45, F0 + 0.7, col)
    for k in range(3):
        cx = -w / 2 + 0.25 + (w - 0.5) * (k + 0.5) / 3
        bx(cx - 0.42, cx + 0.42, -0.45, 0.28, F0 + 0.45, F0 + 0.58, col)
    bx(-w / 2 + 0.4, -w / 2 + 0.9, 0.12, 0.3, F0 + 0.55, F0 + 0.95, cush)
    bx(w / 2 - 0.9, w / 2 - 0.4, 0.12, 0.3, F0 + 0.55, F0 + 0.95, cush)


def armchair(p, x, y, rot, col="st_leather"):
    sofa(p, x, y, rot, w=1.1, col=col, cush=col)


# --- the Skytrade Aviation lounge (x 3600..3660, y -2640..-2698)
lg = P("CT.st_lounge")
lg.box(3604, 3652, -2694, -2644, F0 + 0.01, F0 + 0.03, "rug_n")
lg.box(3605, 3651, -2693, -2645, F0 + 0.03, F0 + 0.035, "st_cream")
lg.box(3606, 3650, -2692, -2646, F0 + 0.035, F0 + 0.04, "rug_n")
for gx in (3611, 3627, 3643):
    for gy in (-2652, -2667, -2682):
        sofa(lg, gx, gy + 2.4, math.pi)                   # faces the windows (-Y)
        armchair(lg, gx - 2.8, gy, -math.pi / 2)
        armchair(lg, gx + 2.8, gy, math.pi / 2)
        lg.box(gx - 1.0, gx + 1.0, gy - 0.6, gy + 0.6, F0, F0 + 0.42, "st_wood")
        lg.box(gx - 1.05, gx + 1.05, gy - 0.65, gy + 0.65, F0 + 0.42, F0 + 0.46, "st_glass")
        lg.box(gx - 0.3, gx + 0.1, gy - 0.2, gy + 0.1, F0 + 0.46, F0 + 0.5, "st_red")
        lg.cyl((gx + 0.5, gy + 0.2, F0 + 0.55), 0.06, 0.18, "shirt_w", segs=10)
        lg.cyl((gx, gy, SC - 1.0), 0.6, 0.25, "st_navy", r2=0.1, segs=16)            # pendant over each group
        lg.cyl((gx, gy, SC - 0.45), 0.01, 0.9, "frame", segs=4)
        lg.cyl((gx, gy, SC - 1.13), 0.4, 0.02, "glow", segs=12)
# bar along the east wall of the suite
lg.box(3655, 3659.6, -2690, -2648, F0, F0 + 1.1, "st_navy")
lg.box(3654.8, 3659.6, -2690.2, -2647.8, F0 + 1.1, F0 + 1.18, "st_marble")
lg.box(3654.75, 3655.0, -2690, -2648, F0 + 0.55, F0 + 0.6, "st_red")
lg.box(3659.4, 3659.8, -2690, -2648, F0 + 1.6, F0 + 3.2, "st_wood")
for k in range(7):
    y = -2687 + k * 6.0
    lg.cyl((3653.5, y, F0 + 0.42), 0.32, 0.06, "st_leather", segs=16)
    lg.cyl((3653.5, y, F0 + 0.21), 0.05, 0.42, "frame", segs=6)
    for j in range(6):
        lg.cyl((3659.2, y + (j - 2.5) * 0.35, F0 + 1.82), 0.08, 0.38, random.choice(("st_glass", "plant_g", "case_r")), segs=8)
# a model of Skye (light jet) on a plinth by the lounge entrance
mj = Vector((3627, -2641.5, F0 + 1.75))
lg.cyl((mj.x, mj.y, F0 + 0.6), 0.9, 1.2, "desk_w", segs=24)
lg.cyl((mj.x, mj.y, F0 + 1.25), 0.95, 0.06, "st_navy", segs=24)
lg.cyl(tuple(mj), 0.18, 2.4, "shirt_w", axis='X', segs=16)
lg.blob((mj.x - 1.25, mj.y, mj.z), (0.3, 0.18, 0.18), "shirt_w")
lg.beam((mj.x - 0.2, mj.y, mj.z - 0.05), (mj.x + 0.4, mj.y - 1.3, mj.z), 0.45, 0.04, "shirt_w")
lg.beam((mj.x - 0.2, mj.y, mj.z - 0.05), (mj.x + 0.4, mj.y + 1.3, mj.z), 0.45, 0.04, "shirt_w")
lg.beam((mj.x + 1.0, mj.y, mj.z + 0.1), (mj.x + 1.3, mj.y, mj.z + 0.7), 0.35, 0.04, "st_navy")
lg.box(mj.x - 1.2, mj.x + 1.2, mj.y - 0.19, mj.y + 0.19, mj.z - 0.02, mj.z + 0.02, "st_red")
# framed photos of the fleet on the lounge's north wall (facing the windows)
for x in (3612, 3646):
    lg.box(x - 4.5, x + 4.5, -2636.6, -2636.4, 1.5, 4.3, "frame")
    lg.box(x - 4.2, x + 4.2, -2636.75, -2636.6, 1.75, 4.05, "st_glass")
    lg.box(x - 2.8, x + 2.8, -2636.8, -2636.75, 2.75, 3.15, "shirt_w")
    lg.box(x - 0.4, x + 0.4, -2636.8, -2636.75, 2.2, 3.7, "shirt_w")
    lg.box(x - 2.8, x + 2.8, -2636.82, -2636.8, 2.82, 2.88, "st_red")
for x, y in ((3603, -2696), (3656, -2696), (3603, -2645)):
    lg.cyl((x, y, F0 + 0.45), 0.6, 0.9, "pot_w", segs=16, r2=0.45)
    for k in range(7):
        a = k / 7 * math.tau
        lg.blob((x + math.cos(a) * 0.4, y + math.sin(a) * 0.4, F0 + 1.3 + random.uniform(0, 0.8)), (0.45, 0.45, 0.6),
                random.choice(("plant_g", "plant_g2")), subdiv=1)
lg.done(outline=0.012)
label("CT.st_lounge_sign", "SKYTRADE AVIATION LOUNGE", (3629, -2636.85, 4.55), 0, 0.5, M["st_navy"], 0.04)

# --- offices (x 3540..3598): glass fronts facing the lounge, desks, an operations room
of = P("CT.st_offices")
GL = []                                                   # see-through glass goes in its own object (no outline)
ROOMS = [(-2637.0, -2652.0, "OPERATIONS"), (-2652.5, -2667.5, "FLIGHT PLANNING"), (-2668.0, -2683.0, "MEETING ROOM"),
         (-2683.5, -2698.0, "CREW ROOM")]
for (ya, yb, nm) in ROOMS:
    GL.append((3597.8, 3598.2, yb, ya, F0, SC - 0.6))
    of.box(3597.7, 3598.3, yb, ya, 1.4, 1.46, "st_red")
    of.box(SA, 3598, yb - 0.1, yb + 0.1, F0, SC, "t_wall")
    cy = (ya + yb) / 2
    if nm == "MEETING ROOM":
        of.box(3555, 3590, cy - 2.2, cy + 2.2, F0 + 0.72, F0 + 0.78, "st_wood")
        of.box(3568, 3578, cy - 1.0, cy + 1.0, F0, F0 + 0.72, "frame")
        for k in range(6):
            x = 3558 + k * 6.0
            for s_ in (-1, 1):
                of.box(x - 0.3, x + 0.3, cy + s_ * 3.0 - 0.3, cy + s_ * 3.0 + 0.3, F0, F0 + 0.48, "seat_g")
                of.box(x - 0.3, x + 0.3, cy + s_ * 3.3 - 0.06, cy + s_ * 3.3 + 0.06, F0 + 0.48, F0 + 1.1, "seat_g")
        of.box(SA + 0.2, SA + 0.4, cy - 4, cy + 4, 1.0, 3.0, "screen")
        continue
    for k in range(3 if nm != "CREW ROOM" else 1):
        x = 3552 + k * 15
        of.box(x - 3, x + 3, cy - 1.0, cy + 1.0, F0 + 0.72, F0 + 0.78, "desk_w")
        of.box(x - 2.9, x - 2.7, cy - 0.9, cy + 0.9, F0, F0 + 0.72, "frame")
        of.box(x + 2.7, x + 2.9, cy - 0.9, cy + 0.9, F0, F0 + 0.72, "frame")
        for d in (-0.8, 0.8):
            of.box(x + d - 0.55, x + d + 0.55, cy + 0.55, cy + 0.65, F0 + 0.95, F0 + 1.55, "screen")
        of.box(x - 0.4, x + 0.4, cy - 2.0, cy - 1.3, F0, F0 + 0.5, "st_navy")
        of.box(x - 0.4, x + 0.4, cy - 2.05, cy - 1.95, F0 + 0.5, F0 + 1.2, "st_navy")
    if nm == "OPERATIONS":
        of.box(SA + 0.2, SA + 0.4, cy - 6, cy + 6, 1.0, 3.6, "screen")
        for r in range(6):
            of.box(SA + 0.45, SA + 0.5, cy - 5.6, cy - 0.5, 3.3 - r * 0.38, 3.45 - r * 0.38, "scr_text")
        of.box(SA + 0.45, SA + 0.5, cy + 0.5, cy + 5.6, 1.3, 3.3, "scr_blue")
    if nm == "CREW ROOM":
        sofa(of, 3585, cy, -math.pi / 2, w=4.0, col="st_navy2", cush="st_red")
of.box(3624, 3636, -2698.7, -2698.3, F0, 3.6, "st_navy")                 # door to the private apron
GL.append((3624.5, 3635.5, -2698.75, -2698.7, F0 + 0.2, 3.4))
of.done(outline=0.01)
gl = P("CT.st_glass_clear")
for g in GL:
    gl.box(*g, "clear_glass")
gl.done(outline=0.0)
for (ya, yb, nm) in ROOMS:
    label("CT.st_room_" + nm.split()[0].lower(), nm, (3598.35, (ya + yb) / 2, 3.2), 90, 0.32, M["st_navy"], 0.02)
label("CT.st_airside_door", "PRIVATE APRON", (3630, -2698.2, 3.95), 180, 0.42, M["st_navy"], 0.02)

# ================================================================ PEOPLE (a few, so it feels used)
def person(name, loc, rot, shirt, trousers, skin, hair, case=None):
    b = P(name)
    b.box(-0.21, 0.21, -0.13, 0.13, 0.86, 1.38, shirt, taper=(0.85, 0.9))
    for sx in (-1, 1):
        b.box(sx * 0.1 - 0.075, sx * 0.1 + 0.075, -0.08, 0.08, 0.0, 0.86, trousers)
        b.box(sx * 0.1 - 0.08, sx * 0.1 + 0.08, -0.18, 0.08, 0.0, 0.08, "frame")
        b.box(sx * 0.27 - 0.055, sx * 0.27 + 0.055, -0.06, 0.06, 0.8, 1.36, shirt)
        b.blob((sx * 0.27, 0, 0.76), (0.06, 0.06, 0.07), skin)
    b.cyl((0, 0, 1.42), 0.07, 0.1, skin, segs=8)
    b.blob((0, 0, 1.66), (0.2, 0.19, 0.23), skin)
    b.blob((0, 0.03, 1.79), (0.2, 0.19, 0.12), hair)
    for sx in (-1, 1):
        b.blob((sx * 0.075, -0.17, 1.7), (0.045, 0.02, 0.055), "shirt_w", subdiv=1)
        b.blob((sx * 0.075, -0.19, 1.69), (0.022, 0.01, 0.028), "frame", subdiv=1)
    if case:
        b.box(0.32, 0.52, -0.22, 0.22, 0.05, 0.62, case)
        b.box(0.4, 0.44, -0.04, 0.04, 0.62, 0.9, "frame")
    return b.done(loc, rot, outline=0.012)


ppl = [("CT.t_p_reception1", (3597, -2628.6, F0), 180, "uniform_st", "uniform_st", "skin_a", "hair_b", None),
       ("CT.t_p_reception2", (3603, -2628.6, F0), 180, "uniform_st", "uniform_st", "skin_c", "hair_d", None),
       ("CT.t_p_guest1", (3600, -2618.5, F0), 0, "st_cream", "trouser_d", "skin_b", "hair_d", "case_b"),
       ("CT.t_p_checkin1", (2905, -2636.8, F0), 180, "seat_b", "trouser_d", "skin_a", "hair_d", None),
       ("CT.t_p_checkin2", (3058, -2636.8, F0), 180, "seat_b", "trouser_d", "skin_c", "hair_d", None),
       ("CT.t_p_trav1", (2905, -2632.5, F0), 0, "shop_a", "trouser_d", "skin_b", "hair_d", "case_r"),
       ("CT.t_p_trav2", (2915, -2630.0, F0), 0, "shop_b", "trouser_d", "skin_a", "hair_b", "case_b"),
       ("CT.t_p_trav3", (3150, -2620.0, F0), 0, "shop_c", "trouser_d", "skin_c", "hair_d", "case_r"),
       ("CT.t_p_lounge1", (3627, -2669.0, F0), 0, "st_navy2", "trouser_d", "skin_a", "hair_b", None),
       ("CT.t_p_office1", (3552, -2646.5, F0), 0, "shirt_w", "trouser_d", "skin_c", "hair_d", None)]
for nm, loc, rot, sh_, tr_, sk, hr, cs in ppl:
    person(nm, loc, rot, sh_, tr_, sk, hr, cs)

# ================================================================ the Skytrade entrance outside
dep = bpy.data.objects.get("CT.departures_3600")
if dep:
    dep.data.body = "SKYTRADE AVIATION"
    dep.data.size = 0.72
use(TI)
pin = P("CT.st_entrance_stripe")
pin.box(3593.6, 3606.4, -2594.55, -2594.5, 7.05, 7.12, "st_red")
pin.done(outline=0.0)
pin_o = bpy.data.objects["CT.st_entrance_stripe"]
TI.objects.unlink(pin_o)
bpy.data.collections["CT_AirportDetail"].objects.link(pin_o)

# ================================================================ lights, cameras, view layers
def area(name, loc, size, energy, col="#fff3e2"):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = size
    ld.energy = energy
    ld.color = lin(col)
    lo = bpy.data.objects.new(name, ld)
    TI.objects.link(lo)
    lo.parent = RIG
    lo.location = loc
    return lo


for x in range(2840, 3480, 80):
    area("CT_tl_hall_%d" % x, (x + 40, -2655, CEIL - 0.3), (80, 80), 60000)
area("CT_tl_sky_rec", (3600, -2624, SC - 0.3), (58, 22), 9000, "#fff0d8")
area("CT_tl_sky_lounge", (3629, -2668, SC - 0.3), (58, 56), 16000, "#ffe9cc")
area("CT_tl_sky_off", (3569, -2668, SC - 0.4), (56, 60), 12000)


def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.3, 4000
    co = bpy.data.objects.new(name, cd)
    TI.objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


cam("CT_cam_t_checkin", (3000, -2614, 2.2), (2950, -2645, 2.0), 20)
cam("CT_cam_t_hall", (2820, -2616, 7.5), (3200, -2660, 1.0), 18)
cam("CT_cam_t_airside", (3060, -2671, 1.8), (3200, -2697, 3.5), 22)
cam("CT_cam_st_reception", (3600, -2612.6, 1.75), (3600, -2636, 2.4), 20)
cam("CT_cam_st_lounge", (3609.0, -2640.5, 2.6), (3650, -2690, 0.6), 20)
cam("CT_cam_st_offices", (3606, -2648, 1.8), (3580, -2668, 1.4), 20)
ec = cam("CT_cam_st_entrance", (3612.0, -2566.0, 2.0), (3600.0, -2600.0, 5.0), 26)
TI.objects.unlink(ec)
bpy.data.collections["CT_AirportDetail"].objects.link(ec)

vl_main = S.view_layers[0]
vl_t = S.view_layers.get("Terminal") or S.view_layers.new("Terminal")


def set_excl(vl, name, ex):
    def walk(lc):
        for c in lc.children:
            if c.name == name:
                c.exclude = ex
            walk(c)
    walk(vl.layer_collection)


set_excl(vl_main, "CT_TerminalInterior", True)
for n in ("CT_Airport", "CT_AirportDetail", "CT_Traffic", "CT_Drive", "CT_AirportGateway"):
    set_excl(vl_t, n, True)

consolidate(TI, ("CT.t_p_", "CT_cam", "CT_tl", "CT.st_glass_clear"))

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

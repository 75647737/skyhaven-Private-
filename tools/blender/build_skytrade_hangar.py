"""Skytrade Aviation hangar, private apron and the fleet (blueprint: Skye, Atlas, Hummingbird, Ranger).

    blender -b blender/sets/city_v005.blend --python tools/blender/build_skytrade_hangar.py -- <out.blend>

East of the commercial hangars (real metres under CT.root):
  hangar     x 4760..4850, y -2700..-2640, doors open to the south (apron); navy fascia with a red
             pinstripe, SKYTRADE AVIATION on the apron and road faces, white epoxy floor with
             yellow guide lines, a two-storey glass office annex on the east side
  inside     Atlas (long-range jet) and Skye (light jet)
  apron      Ranger (turboprop) and a second Skye; helipad with Hummingbird (helicopter);
             taxiway link to taxiway A; service road from the terminal, staff car park, a navy SUV
Fleet livery: white with navy belly and tail, a thin red pinstripe, SKYTRADE on the tail,
no registrations. Aircraft face -Y (nose out through the hangar door).
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(31)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {"ac_white": "#f7f8f9", "ac_navy": "#1f2f57", "ac_red": "#c8302c", "ac_glass": "#26323f",
             "ac_grey": "#b9bec4", "ac_tyre": "#2a2a2e", "h_floor": "#eceae5", "h_line": "#f2c14e",
             "h_wall": "#eef0f2", "h_door": "#b8bec6", "h_steel": "#8f959c", "apron2": "#c4c1ba"}.items():
    M[k] = toon("CT_" + k, v)
OLD = bpy.data.collections.get("CT_Skytrade")
if OLD:
    for o in list(OLD.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(OLD)
SK = bpy.data.collections.new("CT_Skytrade")
bpy.data.collections["City"].children.link(SK)
use(SK)


# ================================================================ FLEET (templates in local metres, nose -Y)
def livery_body(p, L, R, z, nose_len, tail_len, tail_up=0.6):
    """Fuselage: cylinder + nose + tapered tail, navy belly band, red pinstripe, windows."""
    y0 = -L / 2 + nose_len
    y1 = L / 2 - tail_len
    p.cyl((0, (y0 + y1) / 2, z), R, y1 - y0, "ac_white", axis='Y', segs=20)
    p.blob((0, y0, z), (R, nose_len, R * 0.95), "ac_white")
    p.cyl((0, y1 + tail_len / 2, z + tail_up / 2), R, tail_len, "ac_white", axis='Y', segs=20, r2=R * 0.35)
    p.box(-R * 1.01, R * 1.01, y0 - nose_len * 0.4, y1 + tail_len * 0.5, z - R * 0.98, z - R * 0.35, "ac_navy")
    p.box(-R * 1.02, R * 1.02, y0 - nose_len * 0.3, y1 + tail_len * 0.3, z - R * 0.3, z - R * 0.24, "ac_red")
    p.box(-R * 0.75, R * 0.75, y0 - nose_len * 0.62, y0 - nose_len * 0.3, z + R * 0.2, z + R * 0.62, "ac_glass")
    n = int((y1 - y0) / 1.0)
    for k in range(1, n):
        y = y0 + k * (y1 - y0) / n
        for sx in (-1, 1):
            p.box(sx * R * 1.0 - 0.02, sx * R * 1.0 + 0.02, y - 0.17, y + 0.17, z + R * 0.08, z + R * 0.42, "ac_glass")
    return y0, y1


def wing(p, root, tip, chord_root, chord_tip, thick, mat="ac_white", winglet=0.0):
    """Swept wing from root (x, y, z) to tip, chord measured along Y."""
    steps = 6
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        a = Vector(root).lerp(Vector(tip), t0)
        b = Vector(root).lerp(Vector(tip), t1)
        c = chord_root + (chord_tip - chord_root) * (t0 + t1) / 2
        p.beam(a, b, c, thick, mat)
    if winglet:
        tv = Vector(tip)
        p.beam(tv, tv + Vector((0, winglet * 0.5, winglet)), chord_tip * 0.8, thick, "ac_navy")


def gear(p, x, y, z_axle, h):
    p.cyl((x, y, z_axle), h * 0.28, h * 0.22, "ac_tyre", axis='X', segs=12)
    p.beam((x, y, z_axle), (x, y, z_axle + h), h * 0.12, h * 0.12, "ac_grey")


def jet(name, L, R, span, sweep, eng_r, fin_h):
    """Business jet: rear engines, T-tail, winglets (Skye: L~16, Atlas: L~30)."""
    p = P(name)
    z = R + 1.0 * (L / 16)
    y0, y1 = livery_body(p, L, R, z, L * 0.14, L * 0.22, tail_up=R * 0.6)
    wy = -L * 0.02
    for sx in (-1, 1):
        wing(p, (sx * R * 0.6, wy, z - R * 0.55), (sx * span / 2, wy + sweep, z - R * 0.3), L * 0.16, L * 0.06,
             L * 0.012, winglet=L * 0.07)
        ey = y1 - L * 0.05
        p.cyl((sx * (R + eng_r * 1.1), ey, z + R * 0.35), eng_r, L * 0.17, "ac_white", axis='Y', segs=16)
        p.cyl((sx * (R + eng_r * 1.1), ey - L * 0.085, z + R * 0.35), eng_r * 0.78, 0.05, "ac_glass", axis='Y', segs=16)
        p.box(sx * (R + eng_r * 1.1) - eng_r * 1.01, sx * (R + eng_r * 1.1) + eng_r * 1.01, ey - L * 0.06, ey + L * 0.06,
              z + R * 0.35 - 0.05 * L / 16, z + R * 0.35 + 0.05 * L / 16, "ac_red")
        p.beam((sx * R * 0.7, ey, z + R * 0.35), (sx * (R + eng_r * 0.3), ey, z + R * 0.35), L * 0.06, L * 0.012, "ac_white")
    fy = L / 2 - L * 0.08
    p.beam((0, fy - L * 0.06, z + R * 0.6), (0, fy + L * 0.04, z + R * 0.6 + fin_h), L * 0.11, L * 0.012, "ac_navy")
    for sx in (-1, 1):                                    # T-tail stabiliser
        p.beam((0, fy + L * 0.03, z + R * 0.6 + fin_h), (sx * span * 0.18, fy + L * 0.07, z + R * 0.6 + fin_h),
               L * 0.07, L * 0.01, "ac_white")
    gear(p, 0, y0 + L * 0.06, (z - R) * 0.28, z - R)
    for sx in (-1, 1):
        gear(p, sx * R * 1.1, wy + L * 0.05, (z - R) * 0.28, z - R)
    ob = p.done(outline=0.03)
    return ob, (R * 1.04, -L * 0.08, z + R * 0.62), L * 0.035


def turboprop(name):
    """Ranger: straight wing, two engines with four-blade propellers, T-tail (~14 m)."""
    p = P(name)
    L, R, z = 14.0, 0.95, 1.9
    y0, y1 = livery_body(p, L, R, z, 1.8, 3.4, tail_up=0.5)
    for sx in (-1, 1):
        wing(p, (sx * R * 0.6, -0.6, z + 0.2), (sx * 8.5, -0.2, z + 0.45), 2.2, 1.2, 0.18)
        ex = sx * 3.0
        p.cyl((ex, -1.4, z + 0.1), 0.42, 3.2, "ac_white", axis='Y', segs=14, r2=0.3)
        p.box(ex - 0.43, ex + 0.43, -2.6, -0.2, z - 0.05, z + 0.02, "ac_navy")
        p.blob((ex, -3.15, z + 0.1), (0.2, 0.3, 0.2), "ac_red")
        for b in range(4):                                # propeller blades
            a = b / 4 * math.tau + 0.4
            p.beam((ex, -3.25, z + 0.1), (ex + math.cos(a) * 1.3, -3.25, z + 0.1 + math.sin(a) * 1.3), 0.18, 0.05, "ac_glass")
    p.beam((0, L / 2 - 2.2, z + 0.6), (0, L / 2 - 0.6, z + 3.2), 1.6, 0.16, "ac_navy")
    for sx in (-1, 1):
        p.beam((0, L / 2 - 0.9, z + 3.15), (sx * 2.6, L / 2 - 0.5, z + 3.2), 1.1, 0.12, "ac_white")
    gear(p, 0, y0 + 0.8, 0.3, z - R)
    for sx in (-1, 1):
        gear(p, sx * 3.0, -0.4, 0.35, z - 0.2)
    ob = p.done(outline=0.025)
    return ob, (R * 1.04, 1.0, z + R * 0.62), 0.42


def helicopter(name):
    """Hummingbird: rounded cabin, tail boom, main and tail rotors, skids (~12 m)."""
    p = P(name)
    z = 1.5
    p.blob((0, 0, z), (1.25, 2.3, 1.2), "ac_white")
    p.box(-1.27, 1.27, -2.0, 1.6, z - 1.15, z - 0.45, "ac_navy")
    p.box(-1.28, 1.28, -1.8, 1.4, z - 0.42, z - 0.36, "ac_red")
    p.blob((0, -1.4, z + 0.25), (1.0, 1.0, 0.75), "ac_glass")
    for sx in (-1, 1):
        p.box(sx * 1.24 - 0.02, sx * 1.24 + 0.02, -0.4, 0.9, z - 0.1, z + 0.55, "ac_glass")
    p.cyl((0, 4.2, z + 0.35), 0.38, 5.4, "ac_white", axis='Y', segs=14, r2=0.16)
    p.beam((0, 6.6, z + 0.35), (0, 7.3, z + 1.8), 0.8, 0.12, "ac_navy")
    p.cyl((0.18, 7.1, z + 1.3), 0.8, 0.04, "ac_glass", axis='X', segs=18)
    p.cyl((0, 0.1, z + 1.35), 0.12, 0.6, "ac_grey", segs=10)
    p.cyl((0, 0.1, z + 1.7), 0.3, 0.2, "ac_navy", segs=12)
    for b in range(4):
        a = b / 4 * math.tau + 0.3
        p.beam((0, 0.1, z + 1.75), (math.cos(a) * 5.6, 0.1 + math.sin(a) * 5.6, z + 1.68), 0.32, 0.05, "ac_glass")
    for sx in (-1, 1):
        p.cyl((sx * 1.05, 0.0, 0.12), 0.07, 4.4, "ac_grey", axis='Y', segs=8)
        for yy in (-1.0, 1.0):
            p.beam((sx * 1.05, yy, 0.12), (sx * 0.8, yy, z - 0.9), 0.08, 0.08, "ac_grey")
    ob = p.done(outline=0.02)
    return ob, (0.42, 4.4, z + 0.62), 0.32


def side_label(ob, name, at, size):
    """SKYTRADE along both sides of the fuselage, above the windows (reads nose-to-tail... left to right)."""
    x, y, z = at
    for sx, rot in ((1, 90), (-1, -90)):
        lb = label(name + ("_R" if sx > 0 else "_L"), "SKYTRADE", (0, 0, 0), rot, size, M["ac_navy"], 0.01)
        lb.parent = ob
        lb.location = (sx * x, y, z)
        lb.rotation_euler = (math.radians(90), 0, math.radians(rot))


def place(builder, name, loc, rot, *args):
    res = builder(name, *args)
    ob, fin, fs = res
    ob.location = loc
    ob.rotation_euler.z = math.radians(rot)
    side_label(ob, name + "_name", fin, fs)
    return ob


# ================================================================ HANGAR
HX0, HX1, HY0, HY1, HH = 4760.0, 4850.0, -2700.0, -2640.0, 18.0
hg = P("CT.sky_hangar")
hg.box(HX0, HX1, HY0, HY1, -0.04, 0.05, "h_floor")
for x in range(int(HX0) + 15, int(HX1), 15):              # yellow guide lines
    hg.box(x - 0.1, x + 0.1, HY0, HY1 - 4, 0.05, 0.06, "h_line")
hg.box(HX0, HX1, HY0 + 2, HY0 + 2.2, 0.05, 0.06, "h_line")
hg.box(HX0 - 0.5, HX0, HY0, HY1, 0.0, HH, "h_wall")      # side and back walls
hg.box(HX1, HX1 + 0.5, HY0, HY1, 0.0, HH, "h_wall")
hg.box(HX0, HX1, HY1, HY1 + 0.5, 0.0, HH, "h_wall")
hg.box(HX0 - 1, HX1 + 1, HY0 - 1, HY1 + 1, HH, HH + 1.2, "h_wall")      # roof
for x in range(int(HX0) + 10, int(HX1), 10):               # roof trusses
    hg.box(x - 0.3, x + 0.3, HY0, HY1, HH - 1.6, HH, "h_steel")
hg.box(HX0 - 1, HX1 + 1, HY0 - 1.2, HY0 - 0.6, HH - 3.2, HH + 1.2, "ac_navy")      # fascia over the door
hg.box(HX0 - 1, HX1 + 1, HY0 - 1.25, HY0 - 1.2, HH - 2.6, HH - 2.45, "ac_red")
hg.box(HX0 - 1, HX1 + 1, HY1 + 0.5, HY1 + 1.1, HH - 3.2, HH + 1.2, "ac_navy")      # fascia on the road side
hg.box(HX0 - 1, HX1 + 1, HY1 + 1.1, HY1 + 1.15, HH - 2.6, HH - 2.45, "ac_red")
for k in range(4):                                         # door panels stacked open at both sides
    for side, x0 in ((-1, HX0 + 0.6 + k * 0.6), (1, HX1 - 0.6 - k * 0.6)):
        hg.box(x0 - 0.25, x0 + 0.25, HY0 - 0.3 - k * 0.35, HY0 + 0.3 - k * 0.35, 0.0, HH - 3.2, "h_door")
for x in range(int(HX0) + 8, int(HX1), 12):                # hanging lights
    for y in (-2690, -2672, -2654):
        hg.cyl((x, y, HH - 2.4), 0.8, 0.5, "h_steel", r2=0.2, segs=12)
        hg.cyl((x, y, HH - 2.67), 0.55, 0.04, "lamp" if "lamp" in M else "ac_white", segs=12)
# tool carts, stairs and a tug inside
for x, y in ((4772, -2650), (4838, -2650)):
    hg.box(x - 1.2, x + 1.2, y - 0.6, y + 0.6, 0.0, 1.1, "ac_red")
    hg.box(x - 1.25, x + 1.25, y - 0.65, y + 0.65, 1.1, 1.15, "h_steel")
for k in range(6):                                         # boarding stairs at Atlas' door
    hg.box(4784.5 + k * 0.45, 4785.0 + k * 0.45, -2684.0, -2682.6, 0.0, 0.3 + k * 0.32, "h_steel")
hg.done(outline=0.04)
# office annex: two floors of glass with navy frames
ax = P("CT.sky_annex")
ax.box(HX1 + 0.5, HX1 + 30, HY0, HY1, 0.0, 10.0, "h_wall")
ax.box(HX1 + 0.5, HX1 + 30, HY0 - 0.15, HY0 + 0.05, 0.6, 4.4, "ac_glass")
ax.box(HX1 + 0.5, HX1 + 30, HY0 - 0.15, HY0 + 0.05, 5.6, 9.4, "ac_glass")
ax.box(HX1, HX1 + 30.5, HY0 - 0.4, HY0, 4.4, 5.6, "ac_navy")
ax.box(HX1, HX1 + 30.5, HY0 - 0.45, HY0 - 0.4, 4.9, 5.0, "ac_red")
ax.box(HX1, HX1 + 30.5, HY0 - 0.8, HY1 + 0.5, 10.0, 10.6, "ac_navy")
for x in range(int(HX1) + 4, int(HX1) + 30, 4):
    ax.box(x - 0.08, x + 0.08, HY0 - 0.2, HY0, 0.6, 9.4, "ac_navy")
ax.box(HX1 + 12, HX1 + 18, HY0 - 0.25, HY0 - 0.15, 0.0, 3.0, "ac_navy")             # entrance door
ax.done(outline=0.03)
label("CT.sky_hangar_sign_apron", "SKYTRADE AVIATION", ((HX0 + HX1) / 2, HY0 - 1.3, HH - 0.9), 0, 3.4, M["ac_white"], 0.15)
label("CT.sky_hangar_sign_road", "SKYTRADE AVIATION", ((HX0 + HX1) / 2, HY1 + 1.2, HH - 0.9), 180, 3.4, M["ac_white"], 0.15)
label("CT.sky_annex_sign", "OPERATIONS  -  CREW", (HX1 + 15, HY0 - 0.5, 5.05), 0, 0.6, M["ac_white"], 0.03)

# ================================================================ APRON, HELIPAD, ROADS
ap = P("CT.sky_apron")
ap.box(4700, 4960, -2885, -2700, -0.02, 0.025, "apron2")
for x in (4780, 4840, 4920):                               # parking stands
    ap.box(x - 0.2, x + 0.2, -2860, -2705, 0.025, 0.035, "h_line")
ap.box(4870, 4893, -2950, -2885, -0.02, 0.025, "apron2")   # link to taxiway A
ap.box(4881.3, 4881.7, -2950, -2885, 0.025, 0.035, "h_line")
ap.cyl((4925, -2745, 0.04), 12.0, 0.04, "helipad", segs=48)
ap.cyl((4925, -2745, 0.065), 11.0, 0.02, "ac_white", segs=48)
ap.cyl((4925, -2745, 0.075), 10.4, 0.02, "helipad", segs=48)
ap.done(outline=0.0)
label("CT.sky_helipad_H", "H", (4925, -2752.5, 0.09), 0, 9, M["ac_white"], 0.02, upright=False)
strip("CT.sky_service_road", [(3950, -2575), (4700, -2575), (4870, -2600), (4870, -2630)], 12, M["r_street"], 0.03)
strip("CT.sky_staff_parking", [(4880, -2615), (4940, -2615)], 22, M["r_parking"], 0.03)
suv = P("CT.sky_suv")
suv.box(-1.0, 1.0, -2.4, 2.4, 0.4, 1.2, "ac_navy")
suv.box(-0.92, 0.92, -1.2, 1.9, 1.2, 1.85, "ac_glass", taper=(0.95, 0.85))
suv.box(-0.85, 0.85, -0.9, 1.7, 1.83, 1.92, "ac_navy")
suv.box(-1.02, 1.02, -2.2, 2.2, 0.75, 0.8, "ac_red")
for sx, sy in ((-1, -1.5), (1, -1.5), (-1, 1.5), (1, 1.5)):
    suv.cyl((sx * 0.9, sy, 0.4), 0.4, 0.3, "ac_tyre", axis='X', segs=12)
suv.done((4895, -2612, 0.03), 90, outline=0.02)

# ================================================================ THE FLEET
place(jet, "CT.sky_atlas", (4792, -2672, 0.05), 0, 30.0, 1.45, 28.0, 4.0, 1.0, 5.5)
place(jet, "CT.sky_skye_in", (4834, -2668, 0.05), 0, 16.0, 0.95, 15.0, 2.0, 0.6, 3.0)
place(jet, "CT.sky_skye_out", (4840, -2790, 0.0), -20, 16.0, 0.95, 15.0, 2.0, 0.6, 3.0)
place(turboprop, "CT.sky_ranger", (4780, -2790, 0.0), 20)
place(helicopter, "CT.sky_hummingbird", (4925, -2745, 0.08), -30)

# lights for the hangar interior
ld = bpy.data.lights.new("CT_sky_hangar_light", 'AREA')
ld.shape = 'RECTANGLE'
ld.size, ld.size_y = 85, 55
ld.energy = 60000
ld.color = lin("#fff6e8")
lo = bpy.data.objects.new("CT_sky_hangar_light", ld)
SK.objects.link(lo)
lo.parent = RIG
lo.location = ((HX0 + HX1) / 2, (HY0 + HY1) / 2, HH - 3.0)


def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.5, 16000
    co = bpy.data.objects.new(name, cd)
    SK.objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


cam("CT_cam_sky_hangar", (4705, -2800, 7), (4805, -2685, 9), 24)
cam("CT_cam_sky_hangar_in", (4768, -2698, 3.2), (4810, -2660, 4.0), 20)
cam("CT_cam_sky_apron", (4995, -2840, 9), (4860, -2745, 3), 26)
cam("CT_cam_sky_heli", (4950, -2772, 3.0), (4925, -2745, 2.5), 28)
cam("CT_cam_sky_aerial", (4600, -2960, 130), (4840, -2710, 0), 30)

consolidate(SK, ("CT.sky_atlas", "CT.sky_skye", "CT.sky_ranger", "CT.sky_hummingbird", "CT.sky_suv"))

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

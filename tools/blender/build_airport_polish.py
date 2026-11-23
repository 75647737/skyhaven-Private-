"""Airport polish for episode framing: facade detail, tower detail, a busy apron.

    blender -b blender/sets/city_v007.blend --python tools/blender/build_airport_polish.py -- <out.blend>

  * terminal: white vertical fins every 8 m on the kerb and airside glass, floor spandrel bands,
    a roof-edge fascia, glass sheen strips
  * tower: shaft bands, three glass strips, a balcony ring under the cab, an entrance canopy
  * apron: taxi-lane centreline with lead-offs to every stand, hatched no-parking zones, red
    equipment restraint lines, hold-short bars at taxiway A, a two-lane service road with dashes
    and crossings; GSE parking with container rows, dollies, tugs, belt loaders, stairs,
    fuel trucks; ground crew in hi-vis vests; cones at every stand
  * activity (looping keys): a baggage train and a follow-me car drive the service road, a
    marshaller waves his wands at stand A4
  * episode cameras: CT_cam_ep_airport_hero, CT_cam_ep_apron, CT_cam_ep_tower, CT_cam_ep_skytrade
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(808)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
FPS = 24
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {"fin": "#f6f6f3", "spandrel": "#dfe4e8", "sheen": "#a9cde4", "hatch": "#f2c14e",
             "restraint": "#d6403a", "uld": "#c9ced3", "uld_dk": "#8f959c", "hivis": "#f7d117",
             "hivis_o": "#f28a2e", "crew_tr": "#2b3a55", "skin1": "#f0c6a0", "skin2": "#c68a5e",
             "skin3": "#8d5a3b", "followme": "#f7d117", "check": "#2e2e33", "wand": "#ff5a1e"}.items():
    M[k] = toon("CT_" + k, v)

old = bpy.data.collections.get("CT_AirportPolish")
if old:
    for o in list(old.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
AP = bpy.data.collections.new("CT_AirportPolish")
bpy.data.collections["City"].children.link(AP)
use(AP)

# ================================================================ replace the three big arched hangars
for o in list(bpy.data.collections["CT_Airport"].objects):
    if o.type != 'MESH' or o.library:
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    kill = [v for v in bm.verts if 4180 < v.co.x < 4660 and -2775 < v.co.y < -2605 and v.co.z > 0.2]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        bm.to_mesh(o.data)
        o.data.update()
    bm.free()
mh = P("CT.mro_hangars")
for cx in (4300.0, 4500.0):
    x0, x1, y0, y1, h = cx - 75, cx + 75, -2740.0, -2640.0, 16.0
    mh.box(x0, x1, y0, y1, 0.0, h, "fin")
    mh.box(x0, x1, y0 - 0.3, y0, 0.0, h - 3.0, "uld")                     # closed doors
    for k in range(1, 6):
        mh.box(x0 + k * 25 - 0.15, x0 + k * 25 + 0.15, y0 - 0.4, y0 - 0.3, 0.0, h - 3.0, "uld_dk")
    mh.box(x0 - 0.5, x1 + 0.5, y0 - 0.8, y0, h - 3.0, h + 0.4, "tw_navy")
    mh.box(x0 - 0.5, x1 + 0.5, y0 - 0.85, y0 - 0.8, h - 2.2, h - 2.05, "restraint")
    for k in range(8):                                                        # roof lights / vents
        mh.box(x0 + 10 + k * 18, x0 + 14 + k * 18, y0 + 20, y1 - 20, h, h + 0.8, "uld")
mh.done(outline=0.06)
# cargo / maintenance apron in front of the new hangars (fills the gap to the Skytrade apron)
ca = P("CT.cargo_apron")
ca.box(4180, 4700, -2885, -2741, -0.02, 0.026, "apron")
for x in (4260, 4400, 4540):
    ca.box(x - 0.2, x + 0.2, -2880, -2745, 0.026, 0.036, "hatch")
    ca.box(x - 20, x + 20, -2760.2, -2759.8, 0.026, 0.036, "restraint")
ca.box(4180, 4700, -2875.2, -2874.8, 0.026, 0.036, "hatch")
ca.box(4400, 4423, -2950, -2885, -0.02, 0.026, "apron")
ca.done(outline=0.0)
JET = bpy.data.objects.get("CT.jet_t")
for i, (x, rot) in enumerate(((4260, 180), (4540, 165))):
    if JET:
        cj = bpy.data.objects.new("CT.cargo_jet%d" % i, JET.data)
        AP.objects.link(cj)
        cj.parent = RIG
        cj.location = (x, -2805, 0.0)
        cj.rotation_euler.z = math.radians(rot)
        for m in JET.modifiers:
            n = cj.modifiers.new(m.name, m.type)
            n.thickness, n.offset, n.use_flip_normals, n.material_offset = m.thickness, m.offset, True, m.material_offset
CARGO_X = (4260, 4400, 4540)
label("CT.mro_sign_a", "SKYHAVEN AIRCRAFT MAINTENANCE", (4300.0, -2740.9, 14.4), 0, 1.8, M["fin"], 0.08)
label("CT.mro_sign_b", "CARGO  &  MAINTENANCE", (4500.0, -2740.9, 14.4), 0, 1.8, M["fin"], 0.08)

# ================================================================ terminal facade
TX0, TX1, TYF, TYA, TH = 2800.0, 3800.0, -2610.0, -2700.0, 22.0
ENTR = (3000.0, 3300.0, 3600.0)
fa = P("CT.terminal_facade")
x = TX0
while x <= TX1 + 0.1:
    for face, s in ((TYF, 1), (TYA, -1)):
        if face == TYF and any(abs(x - e) < 7 for e in ENTR):
            fa.box(x - 0.25, x + 0.25, face, face + s * 1.4, 4.8, TH, "fin")
        else:
            fa.box(x - 0.25, x + 0.25, min(face, face + s * 1.4), max(face, face + s * 1.4), 0.3, TH, "fin")
    x += 8.0
for z in (7.2, 14.4):
    for face, s in ((TYF, 1), (TYA, -1)):
        fa.box(TX0, TX1, min(face, face + s * 0.5), max(face, face + s * 0.5), z - 0.35, z + 0.35, "spandrel")
for face, s in ((TYF, 1), (TYA, -1)):
    fa.box(TX0 - 4, TX1 + 4, min(face, face + s * 3.0), max(face, face + s * 3.0), TH, TH + 1.6, "fin")    # roof fascia
    fa.box(TX0 - 4, TX1 + 4, min(face, face + s * 3.05), max(face, face + s * 3.05), TH + 0.5, TH + 0.62, "ac_navy")
for k in range(40):                                        # diagonal sheen strips on the glass
    x = TX0 + 10 + k * 25 + random.uniform(-4, 4)
    for face, s in ((TYF, 1), (TYA, -1)):
        fa.beam((x, face + s * 0.05, 2.0), (x + 4.0, face + s * 0.05, 12.0), 0.9, 0.04, "sheen")
fa.done(outline=0.03)

# ================================================================ tower detail
TWX, TWY = 3960.0, -2650.0
td = P("CT.tower_detail")
for z in range(16, 64, 8):                                 # shaft bands (radius follows the taper)
    r = 4.6 - (4.6 - 3.4) * (z - 9.6) / 55.0 + 0.12
    td.cyl((TWX, TWY, z), r, 0.45, "tw_navy" if z % 16 == 0 else "fin", segs=24)
for a in (90, 210, 330):                                   # three glass strips
    ra = math.radians(a)
    td.beam((TWX + math.cos(ra) * 4.55, TWY + math.sin(ra) * 4.55, 11.0),
            (TWX + math.cos(ra) * 3.45, TWY + math.sin(ra) * 3.45, 62.0), 0.9, 0.2, "tw_glass")
td.cyl((TWX, TWY, 66.9), 9.6, 0.35, "tw_navy", segs=32)    # balcony ring under the cab
for k in range(32):
    a = k / 32 * math.tau
    td.cyl((TWX + math.cos(a) * 9.45, TWY + math.sin(a) * 9.45, 67.6), 0.05, 1.1, "tw_steel", segs=4)
td.cyl((TWX, TWY, 68.15), 9.5, 0.08, "tw_steel", segs=32)
td.box(TWX - 6, TWX + 6, TWY - 13.5, TWY - 9.2, 3.6, 4.0, "tw_navy")     # entrance canopy
for x in (TWX - 5.6, TWX + 5.6):
    td.box(x - 0.15, x + 0.15, TWY - 13.3, TWY - 13.0, 0.0, 3.6, "tw_steel")
td.done(outline=0.05)

# ================================================================ apron markings
mk = P("CT.apron_markings2")
Z = 0.036
mk.box(2760, 3840, -2866.2, -2865.8, Z, Z + 0.01, "hatch")               # taxi-lane centreline
STANDS = [2900 + 160 * i for i in range(6)]
for x in STANDS:                                           # curved lead-off to each stand
    pts = [Vector((x - 45 + 45 * math.sin(t * math.pi / 2), -2866 + 45 * (1 - math.cos(t * math.pi / 2)), Z))
           for t in [k / 10 for k in range(11)]]
    for a, b in zip(pts, pts[1:]):
        mk.beam(a, b, 0.4, 0.01, "hatch")
    for sx in (-1, 1):                                     # red equipment restraint lines
        mk.box(x + sx * 24.2, x + sx * 24.6, -2840, -2712, Z, Z + 0.01, "restraint")
    mk.box(x - 24.6, x + 24.6, -2840.4, -2840.0, Z, Z + 0.01, "restraint")
for x in STANDS[:-1]:                                      # hatched no-parking zone between stands
    cx = x + 80
    for k in range(-6, 7):
        mk.beam((cx + k * 2.2 - 3, -2840, Z), (cx + k * 2.2 + 3, -2828, Z), 0.5, 0.01, "hatch")
    mk.box(cx - 16, cx + 16, -2840.2, -2839.9, Z, Z + 0.01, "hatch")
    mk.box(cx - 16, cx + 16, -2828.1, -2827.8, Z, Z + 0.01, "hatch")
for x in (2900, 3300, 3700, 4881.5):                       # hold-short bars at taxiway A
    for k in range(4):
        y = -2930 + k * 0.9
        mk.box(x - 11.5, x + 11.5, y - 0.15, y + 0.15, 0.04, 0.05, "hatch")
y = -2708.5                                                # service road centre dashes + crossings
x = 2760
while x < 3840:
    mk.box(x, x + 3, y - 0.12, y + 0.12, Z, Z + 0.01, "white_c")
    x += 7
for x in STANDS:
    for k in range(6):
        xx = x - 30 + k * 1.2
        mk.box(xx, xx + 0.6, -2712, -2705, Z, Z + 0.012, "white_c")
mk.done(outline=0.0)


# ================================================================ ground equipment (batched)
def tmpl(name):
    return bpy.data.objects.get(name)


ITEMS = []
TUG, CART, FUEL, BELT, CAT, CONE = (tmpl("CT.tug_t"), tmpl("CT.cart_t"), tmpl("CT.fuel_truck_t"),
                                   tmpl("CT.belt_loader_t"), tmpl("CT.catering_t"), tmpl("CT.cone_t"))
uld = P("CT.uld_t")
uld.box(-0.8, 0.8, -0.78, 0.78, 0.35, 1.95, "uld", taper=(0.9, 1.0))
uld.box(-0.82, 0.82, -0.8, 0.8, 0.0, 0.35, "uld_dk")
uld.box(-0.81, 0.81, -0.79, -0.77, 0.5, 1.8, "uld_dk")
ULD = uld.done(outline=0.015)
ULD.hide_render = ULD.hide_viewport = True
stairs = P("CT.stairs_t")
stairs.box(-1.2, 1.2, -3.5, 2.0, 0.4, 1.0, "white_c")
for k in range(9):
    stairs.box(-0.7, 0.7, -3.2 + k * 0.55, -2.65 + k * 0.55, 1.0 + k * 0.38, 1.12 + k * 0.38, "uld_dk")
stairs.beam((-0.75, -3.2, 1.9), (-0.75, 1.7, 4.8), 0.06, 0.06, "uld_dk")
stairs.beam((0.75, -3.2, 1.9), (0.75, 1.7, 4.8), 0.06, 0.06, "uld_dk")
for sy in (-2.6, 1.4):
    stairs.cyl((0, sy, 0.4), 0.4, 2.4, "tyre_c", axis='X', segs=10)
STAIRS = stairs.done(outline=0.015)
STAIRS.hide_render = STAIRS.hide_viewport = True
for zone in range(5):                                      # GSE parking between stands (behind the hatch)
    x0 = STANDS[zone] + 58
    for k in range(4):
        ITEMS.append((ULD, (x0 + k * 1.9, -2720.0, 0.03), 0.0, 1.0))
        ITEMS.append((ULD, (x0 + k * 1.9, -2722.0, 0.03), 0.0, 1.0))
    ITEMS.append((CART, (x0 + 10, -2721.0, 0.03), math.radians(90), 1.0))
    ITEMS.append((CART, (x0 + 13, -2721.0, 0.03), math.radians(90), 1.0))
    ITEMS.append((TUG, (x0 + 16.5, -2721.0, 0.03), math.radians(90), 1.0))
    ITEMS.append((STAIRS if zone % 2 else BELT, (x0 + 22, -2723.0, 0.03), math.radians(90), 1.0))
for i, x in enumerate(STANDS):                             # cones and chocks at every stand
    for dx, dy in ((0, -2751.5), (19, -2770), (-19, -2770), (0, -2799), (6, -2752), (-6, -2752)):
        ITEMS.append((CONE, (x + dx, dy, 0.03), 0.0, 1.0))
    if i in (1, 4):
        ITEMS.append((FUEL, (x - 11, -2785, 0.03), 0.0, 1.0))
    if i in (2, 5):
        ITEMS.append((STAIRS, (x + 4, -2758, 0.03), math.radians(-15), 1.0))
ITEMS += [(TUG, (2830, -2860, 0.03), math.radians(30), 1.0), (TUG, (3790, -2860, 0.03), math.radians(-40), 1.0)]
for k in range(8):                                         # Skytrade apron too
    ITEMS.append((CONE, (4780 + random.uniform(-25, 25), -2760 + random.uniform(-30, 20), 0.03), 0.0, 1.0))
ITEMS += [(FUEL, (4808, -2768, 0.03), math.radians(80), 1.0), (STAIRS, (4846, -2780, 0.03), math.radians(-20), 1.0),
          (TUG, (4865, -2812, 0.03), math.radians(160), 1.0)]
for x in CARGO_X:                                          # containers, dollies and tugs on the cargo apron
    for r in range(3):
        for k in range(6):
            ITEMS.append((ULD, (x + 30 + k * 1.9, -2752 - r * 2.2, 0.03), 0.0, 1.0))
    ITEMS += [(TUG, (x + 18, -2770, 0.03), math.radians(60), 1.0), (CART, (x + 22, -2768, 0.03), math.radians(60), 1.0),
              (BELT, (x - 8, -2790, 0.03), math.radians(10), 1.0), (FUEL, (x + 14, -2830, 0.03), math.radians(-20), 1.0)]
    for k in range(5):
        ITEMS.append((CONE, (x + random.uniform(-20, 20), random.uniform(-2840, -2770), 0.03), 0.0, 1.0))
ITEMS += [(ULD, (4670 + k * 1.9, -2865, 0.03), 0.0, 1.0) for k in range(5)]
ITEMS += [(TUG, (4690, -2858, 0.03), math.radians(100), 1.0), (CART, (4683, -2858.5, 0.03), math.radians(100), 1.0)]
# foreground dressing for the two ground-level episode cameras
ITEMS += [(ULD, (3418 + k * 1.9, -2753.0, 0.03), 0.0, 1.0) for k in range(4)]
ITEMS += [(CART, (3428.5, -2757.5, 0.03), math.radians(20), 1.0), (TUG, (3432.0, -2761.5, 0.03), math.radians(30), 1.0),
          (CONE, (3440.0, -2756.0, 0.03), 0.0, 1.0), (CONE, (3437.0, -2752.5, 0.03), 0.0, 1.0)]
ITEMS += [(TUG, (4826.0, -2822.0, 0.03), math.radians(-30), 1.0), (CART, (4796.0, -2820.0, 0.03), math.radians(80), 1.0),
          (CART, (4793.0, -2817.0, 0.03), math.radians(80), 1.0), (CONE, (4805.0, -2826.0, 0.03), 0.0, 1.0),
          (CONE, (4818.0, -2827.0, 0.03), 0.0, 1.0)]
scatter("CT.apron_gse", AP, ITEMS, outline=0.02)


# ================================================================ ground crew (hi-vis)
def crew_piece(name, vest, skin, pose=0):
    p = P(name)
    p.box(-0.2, 0.2, -0.12, 0.12, 0.86, 1.38, vest, taper=(0.85, 0.9))
    p.box(-0.21, 0.21, -0.125, 0.125, 1.05, 1.12, "white_c")
    for sx in (-1, 1):
        p.box(sx * 0.1 - 0.075, sx * 0.1 + 0.075, -0.08, 0.08, 0.0, 0.86, "crew_tr")
        p.box(sx * 0.1 - 0.08, sx * 0.1 + 0.08, -0.18, 0.08, 0.0, 0.08, "frame")
        if pose == 1 and sx > 0:                           # pointing / signalling arm
            p.beam((0.26, 0, 1.34), (0.62, -0.25, 1.62), 0.11, 0.11, vest)
        else:
            p.box(sx * 0.27 - 0.055, sx * 0.27 + 0.055, -0.06, 0.06, 0.8, 1.36, vest)
    p.cyl((0, 0, 1.42), 0.07, 0.1, skin, segs=8)
    p.blob((0, 0, 1.66), (0.2, 0.19, 0.23), skin)
    p.blob((0, 0.02, 1.8), (0.2, 0.19, 0.1), "white_c")       # helmet / cap
    for sx in (-1, 1):
        p.blob((sx * 0.075, -0.17, 1.7), (0.045, 0.02, 0.055), "white_c", subdiv=1)
        p.blob((sx * 0.075, -0.19, 1.69), (0.022, 0.01, 0.028), "frame", subdiv=1)
    p.box(-0.21, 0.21, -0.126, 0.126, 1.25, 1.3, "white_c")
    o = p.done(outline=0.012)
    o.hide_render = o.hide_viewport = True
    return o


CREW = [crew_piece("CT.crew_t%d" % i, v, s, pose) for i, (v, s, pose) in
        enumerate((("hivis", "skin1", 0), ("hivis_o", "skin2", 0), ("hivis", "skin3", 1), ("hivis_o", "skin1", 1)))]
people = []
for i, x in enumerate(STANDS):
    for k in range(3):
        people.append((random.choice(CREW), (x + random.uniform(-14, 14), random.uniform(-2795, -2755), 0.03),
                       random.uniform(0, 6.28), 1.0))
for k in range(6):
    people.append((random.choice(CREW), (4790 + random.uniform(-30, 40), random.uniform(-2800, -2705), 0.03),
                   random.uniform(0, 6.28), 1.0))
people += [(CREW[0], (3427.0, -2750.0, 0.03), math.radians(200), 1.0), (CREW[2], (3436.0, -2758.0, 0.03), math.radians(140), 1.0),
           (CREW[1], (4817.0, -2818.0, 0.03), math.radians(170), 1.0), (CREW[3], (4800.0, -2812.0, 0.03), math.radians(200), 1.0)]
for x in CARGO_X:
    for k in range(4):
        people.append((random.choice(CREW), (x + random.uniform(-15, 40), random.uniform(-2840, -2750), 0.03),
                       random.uniform(0, 6.28), 1.0))
people += [(CREW[1], (4676, -2861, 0.03), math.radians(120), 1.0), (CREW[2], (4700, -2864, 0.03), math.radians(80), 1.0)]
scatter("CT.apron_crew", AP, people, outline=0.012)


# ================================================================ moving things (looping)
def fcurves_of(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for lay in getattr(action, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def loop_along(ob, pts, period, start=1):
    """Drive along a closed polyline at constant speed, facing the way it goes (nose -Y)."""
    pts = [Vector(p) for p in pts] + [Vector(pts[0])]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + (b - a).length)
    ob.rotation_mode = 'XYZ'
    last_h = None
    for i, (p, c) in enumerate(zip(pts, cum)):
        f = start + period * c / cum[-1]
        d = (pts[min(i + 1, len(pts) - 1)] - p) if i < len(pts) - 1 else (p - pts[i - 1])
        h = math.atan2(d.x, -d.y)
        if last_h is not None:
            while h - last_h > math.pi:
                h -= math.tau
            while h - last_h < -math.pi:
                h += math.tau
        last_h = h
        ob.location = (p.x, p.y, 0.03)
        ob.rotation_euler = (0, 0, h)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    for fcu in fcurves_of(ob.animation_data.action):
        for kp in fcu.keyframe_points:
            kp.interpolation = 'LINEAR'
        fcu.modifiers.new('CYCLES')


train = P("CT.baggage_train")
train.box(-0.9, 0.9, -1.5, 1.5, 0.3, 1.0, "yellow")
train.box(-0.8, 0.8, 0.2, 1.4, 1.0, 1.9, "glass_c")
train.box(-0.85, 0.85, 0.15, 1.45, 1.9, 2.0, "yellow")
for k in range(4):
    y0 = 2.6 + k * 3.0
    train.box(-0.8, 0.8, y0, y0 + 2.4, 0.35, 0.5, "uld_dk")
    train.box(-0.75, 0.75, y0 + 0.1, y0 + 2.3, 0.5, 1.55, random.choice(("lug1", "lug2", "lug4", "uld")))
    train.box(-0.05, 0.05, y0 - 0.6, y0, 0.4, 0.45, "uld_dk")
for y in [-1.0, 1.0] + [2.9 + k * 3.0 for k in range(4)] + [4.7 + k * 3.0 for k in range(4)]:
    train.cyl((0, y, 0.3), 0.3, 1.9, "tyre_c", axis='X', segs=10)
TRAIN = train.done(outline=0.015)
loop_along(TRAIN, [(2780, -2710.3), (3820, -2710.3), (3830, -2706.7), (2770, -2706.7)], 120 * FPS)
fm = P("CT.follow_me")
fm.box(-0.95, 0.95, -2.3, 2.3, 0.35, 1.05, "followme")
fm.box(-0.85, 0.85, -1.0, 1.1, 1.05, 1.55, "glass_c", taper=(0.9, 0.75))
fm.box(-0.75, 0.75, -0.7, 0.9, 1.53, 1.6, "followme")
for k in range(6):
    fm.box(-0.97 if k % 2 else -0.97, 0.97, -2.0 + k * 0.7, -1.65 + k * 0.7, 0.6, 0.8, "check" if k % 2 == 0 else "followme")
fm.box(-0.5, 0.5, -0.3, 0.3, 1.6, 1.95, "check")
fm.box(-0.52, 0.52, -0.32, 0.32, 1.95, 2.05, "followme")
for sy in (-1.45, 1.45):
    fm.cyl((0, sy, 0.35), 0.34, 2.0, "tyre_c", axis='X', segs=10)
FM = fm.done(outline=0.02)
loop_along(FM, [(3500, -2866), (3900, -2866), (4300, -2930), (4880, -2930), (4880, -2860), (4300, -2900), (3900, -2880)],
           90 * FPS, start=200)
# marshaller at stand A4 waving the wands
mar = crew_piece("CT.marshaller", "hivis_o", "skin2")
mar.hide_render = mar.hide_viewport = False
mar.location = (3380.0, -2735.0, 0.03)
mar.rotation_euler.z = math.radians(180)
for side, sx in (("L", 1), ("R", -1)):
    w = P("CT.marshaller_wand_" + side)
    w.box(-0.05, 0.05, -0.05, 0.05, -0.62, 0.0, "hivis_o")
    w.cyl((0, 0, -0.85), 0.04, 0.5, "wand", segs=8)
    wo = w.done(outline=0.008)
    wo.parent = mar
    wo.location = (sx * 0.29, 0.0, 1.34)
    f = wo.driver_add("rotation_euler", 1)
    f.driver.expression = "%.2f*(2.2 + 0.5*sin(frame*0.18))" % sx


# ================================================================ episode cameras
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.5, 16000
    cd.sensor_width = 36
    co = bpy.data.objects.new(name, cd)
    AP.objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


cam("CT_cam_ep_airport_hero", (4728.0, -2872.0, 9.0), (3800.0, -2655.0, 28.0), 32)
cam("CT_cam_ep_apron", (3448.0, -2768.0, 2.6), (3362.0, -2700.0, 13.0), 24)
cam("CT_cam_ep_tower", (3770.0, -2738.0, 6.0), (3935.0, -2652.0, 32.0), 22)
cam("CT_cam_ep_skytrade", (4811.0, -2838.0, 2.2), (4806.0, -2700.0, 12.0), 22)

consolidate(AP, ("CT.baggage_train", "CT.follow_me", "CT.marshaller", "CT_cam", "CT.apron_gse", "CT.apron_crew", "CT.cargo_jet",
                 "CT.uld_t", "CT.stairs_t", "CT.crew_t"))

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

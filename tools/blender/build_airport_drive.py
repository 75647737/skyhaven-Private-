"""Airport detail and Ace's drive from the mansion to the terminal.

    blender -b blender/sets/city_v001.blend --python tools/blender/build_airport_drive.py -- <out.blend>

Adds to the city (real metres under CT.root):
  CT_AirportDetail  departures kerb with sidewalk, bollards, palms, three glass entrances with
                    DEPARTURES signs under the canopy, zebra crossings to the car park, taxi rank,
                    airport shuttle; apron stand markings (yellow lead-in lines, stop bars, gate
                    numbers A1-A6), proper jet bridges (rotunda, tunnel, cab, wheel leg), ground
                    vehicles at each gate (baggage trains, fuel trucks, belt loaders, catering
                    truck, pushback tug, cones); airport road signs on the Skyway
  CT_Drive          Ace's white car (same as the one in the carport), the route curve
                    CT.route_mansion_airport and a timed drive: carport -> driveway -> gate ->
                    Heights Avenue -> Skyway -> terminal frontage -> stops at the Departures door;
                    chase camera CT_cam_drive (child of the car) and CT_cam_dropoff at the kerb.
Scene frame range is set to the whole drive; markers name each leg.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(77)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
M.setdefault("pave", M.get("paving"))
for k, v in {"navy_sign": "#22325a", "orange": "#e8772e", "cone": "#f05a28", "lug1": "#c8463a", "lug2": "#3f6fa8",
             "lug3": "#2e2e33", "lug4": "#6a8f4f", "shuttle": "#2f6fb0"}.items():
    M[k] = toon("CT_" + k, v)

for name in ("CT_AirportDetail", "CT_Drive"):
    old = bpy.data.collections.get(name)
    if old:
        for o in list(old.all_objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(old)
AD = bpy.data.collections.new("CT_AirportDetail")
DR = bpy.data.collections.new("CT_Drive")
for c in (AD, DR):
    bpy.data.collections["City"].children.link(c)
for i in range(10):                                   # old thin jet bridges
    o = bpy.data.objects.get("CT.jet_bridge%d" % i)
    if o:
        bpy.data.objects.remove(o)
use(AD)

# ---------------------------------------------------------------- batching (merged copies)
BATCH = {}


def place(src, loc, rot=0.0, scale=1.0, coll=None):
    mw = (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rot), 4, 'Z')
          @ Matrix.Diagonal((scale, scale, scale, 1)))
    BATCH.setdefault((src.name, (coll or AD).name), []).append(mw)


def flush(tag):
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
        name = "%s_%s" % (sname[:-2] if sname.endswith("_t") else sname, tag)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for m in src.data.materials:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        bpy.data.collections[cname].objects.link(ob)
        ob.parent = RIG
        for m in src.modifiers:
            if m.type == 'SOLIDIFY':
                n = ob.modifiers.new(m.name, 'SOLIDIFY')
                n.thickness, n.offset, n.use_flip_normals, n.material_offset, n.use_rim = \
                    m.thickness, m.offset, m.use_flip_normals, m.material_offset, m.use_rim
    BATCH.clear()


def template(p, outline=0.02):
    ob = p.done(outline=outline)
    ob.hide_render = ob.hide_viewport = True
    return ob


# ================================================================ DEPARTURES KERB
TY = -2610.0                                           # terminal front face
kb = P("CT.departures_kerb")
kb.box(2790, 3810, -2609.5, -2587, 0.0, 0.15, "pave")
kb.box(2790, 3810, -2587.3, -2586.9, 0.0, 0.16, "white_c")
# entrances: glass doors, frames, DEPARTURES boards hanging from the canopy
for x in (3000, 3300, 3600):
    kb.box(x - 6, x + 6, TY, TY + 0.6, 0.15, 4.6, "frame")                    # entrance on the kerb side
    kb.box(x - 5.6, x + 5.6, TY + 0.5, TY + 0.7, 0.15, 4.3, "tower_cab")
    for k in range(-2, 3):
        kb.box(x + k * 2.2 - 0.06, x + k * 2.2 + 0.06, TY + 0.5, TY + 0.75, 0.15, 4.3, "frame")
    kb.box(x - 6.5, x + 6.5, -2595.4, -2594.6, 6.9, 8.6, "navy_sign")
    kb.box(x - 0.15, x + 0.15, -2595.1, -2594.9, 8.6, 9.0, "metal")
    for dx in (-5.2, 5.2):
        kb.box(x + dx - 0.6, x + dx + 0.6, -2589.6, -2589.0, 0.15, 1.0, "white_c")   # planter
# bollards along the kerb
for k in range(0, 340):
    x = 2795 + k * 3.0
    kb.cyl((x, -2588.0, 0.6), 0.12, 0.9, "metal", segs=8)
kb.done(outline=0.03)
for x in (3000, 3300, 3600):
    label("CT.departures_%d" % x, "DEPARTURES", (x, -2594.5, 7.75), 180, 1.0, M["sign_text"], 0.05)
label("CT.dropoff_paint", "DROP-OFF", (3300, -2581.5, 0.04), 0, 2.2, M["white_c"], 0.01, upright=False)
PALM = bpy.data.objects.get("CT.palm_t")
for x in range(2830, 3800, 60):
    if all(abs(x - d) > 12 for d in (3000, 3300, 3600)):
        place(PALM, (x, -2605, 0.15), random.uniform(0, 360), 0.8)
# zebra crossings from the car park
zb = P("CT.zebra_crossings")
for xc in (3150, 3450):
    y = -2585.5
    while y < -2564.5:
        zb.box(xc - 3, xc + 3, y, y + 0.55, 0.04, 0.05, "white_c")
        y += 1.1
zb.done(outline=0)
# taxi rank and shuttle
taxi = P("CT.taxi_t")
taxi.box(-0.95, 0.95, -2.3, 2.3, 0.35, 1.05, "yellow")
taxi.box(-0.85, 0.85, -1.0, 1.1, 1.05, 1.55, "glass_c", taper=(0.9, 0.75))
taxi.box(-0.75, 0.75, -0.7, 0.9, 1.53, 1.6, "yellow")
taxi.box(-0.35, 0.35, -0.15, 0.15, 1.6, 1.85, "white_c")
taxi.box(-0.97, 0.97, -0.4, 0.4, 0.7, 0.8, "car_k")
for sy in (-1.45, 1.45):
    taxi.cyl((0, sy, 0.35), 0.34, 2.0, "tyre_c", axis='X', segs=10)
TAXI = template(taxi)
for k in range(7):
    place(TAXI, (3680 + k * 6.2, -2582.5, 0.04), 90)
sh = P("CT.airport_shuttle")
sh.box(2880, 2892, -2584.3, -2581.5, 0.5, 3.4, "shuttle")
sh.box(2880.5, 2891.5, -2584.35, -2581.45, 1.9, 2.9, "glass_c")
sh.box(2880, 2892, -2584.3, -2581.5, 3.4, 3.6, "white_c")
for x in (2882.5, 2889.5):
    sh.cyl((x, -2582.9, 0.5), 0.5, 2.9, "tyre_c", axis='Y', segs=12)
sh.done(outline=0.03)
label("CT.shuttle_sign", "AIRPORT SHUTTLE", (2886, -2581.4, 3.0), 180, 0.5, M["white_c"], 0.02)

# ================================================================ APRON: markings and gates
use(AD)
mk = P("CT.apron_markings")
GATES = []
for i in range(6):
    o = bpy.data.objects.get("CT.jet_gate%d" % i)
    if o:
        GATES.append((i, o.location.x / RIG.scale.x if o.parent is None else o.location.x))
for i, x in GATES:
    mk.box(x - 0.25, x + 0.25, -2950, -2752, 0.035, 0.045, "yellow")          # lead-in line
    mk.box(x - 3, x + 3, -2750.5, -2750, 0.035, 0.045, "yellow")              # stop bar
    mk.box(x - 22, x - 21.6, -2860, -2705, 0.035, 0.045, "red_cross")         # stand boundary
    mk.box(x + 21.6, x + 22, -2860, -2705, 0.035, 0.045, "red_cross")
mk.box(2760, 3840, -2712.4, -2712.0, 0.035, 0.045, "white_c")                 # service road
mk.box(2760, 3840, -2705.4, -2705.0, 0.035, 0.045, "white_c")
mk.done(outline=0)
for i, x in GATES:
    label("CT.gate_A%d" % (i + 1), "A%d" % (i + 1), (x, -2875, 0.05), 0, 9, M["yellow"], 0.01, upright=False)
    label("CT.gate_sign_A%d" % (i + 1), "A%d" % (i + 1), (x - 14, -2700.6, 13.5), 0, 3, M["yellow"], 0.1)
    # jet bridge: rotunda by the terminal, tunnel, cab at the front door, wheel leg
    jb = P("CT.jet_bridge_A%d" % (i + 1))
    rx, ry = x - 14, -2714
    jb.cyl((rx, ry, 3.0), 2.2, 6.0, "white_c", segs=16)
    jb.cyl((rx, ry, 0.2), 1.0, 0.4, "metal", segs=12)
    jb.box(rx - 1.8, rx + 1.8, -2711, TY - 0.2, 3.6, 6.6, "white_c")           # link to the terminal
    door = Vector((x - 3.3, -2752.0, 5.2))
    a = Vector((rx, ry, 5.2))
    jb.beam(a, door + Vector((-1.6, 1.5, 0)), 2.8, 2.8, "white_c")
    jb.box(door.x - 2.4, door.x + 0.2, door.y - 0.2, door.y + 2.6, 3.8, 6.6, "white_c")
    jb.box(door.x - 2.42, door.x + 0.22, door.y + 0.5, door.y + 2.4, 4.8, 5.8, "glass_c")
    leg = a.lerp(door, 0.62)
    jb.box(leg.x - 0.25, leg.x + 0.25, leg.y - 0.25, leg.y + 0.25, 0.6, 3.8, "metal")
    jb.box(leg.x - 1.4, leg.x + 1.4, leg.y - 0.5, leg.y + 0.5, 0.2, 0.7, "metal")
    for dx in (-1.1, 1.1):
        jb.cyl((leg.x + dx, leg.y, 0.45), 0.45, 0.4, "tyre_c", axis='X', segs=10)
    jb.done(outline=0.05)

# ground vehicles (templates)
tug = P("CT.tug_t")
tug.box(-0.9, 0.9, -1.5, 1.5, 0.3, 1.0, "yellow")
tug.box(-0.8, 0.8, 0.2, 1.4, 1.0, 1.9, "glass_c")
tug.box(-0.85, 0.85, 0.15, 1.45, 1.9, 2.0, "yellow")
for sy in (-1.0, 1.0):
    tug.cyl((0, sy, 0.3), 0.3, 1.9, "tyre_c", axis='X', segs=10)
TUG = template(tug)
cart = P("CT.cart_t")
cart.box(-0.8, 0.8, -1.2, 1.2, 0.35, 0.5, "metal")
cart.box(-0.82, 0.82, -1.22, 1.22, 0.5, 1.8, "white_c")
cart.box(-0.75, 0.75, -1.1, 1.1, 0.5, 1.7, "glass_c")
for k, col in enumerate(("lug1", "lug2", "lug3", "lug4")):
    cart.box(-0.6 + (k % 2) * 0.62, -0.05 + (k % 2) * 0.62, -0.95 + (k // 2) * 1.0, -0.2 + (k // 2) * 1.0, 0.5, 1.05, col)
for sy in (-0.8, 0.8):
    cart.cyl((0, sy, 0.25), 0.25, 1.7, "tyre_c", axis='X', segs=8)
CART = template(cart)
fuel = P("CT.fuel_truck_t")
fuel.box(-1.2, 1.2, -5.0, -2.6, 0.5, 2.8, "white_c")
fuel.box(-1.15, 1.15, -4.9, -3.6, 1.7, 2.6, "glass_c")
fuel.cyl((0, 0.6, 1.9), 1.25, 6.4, "white_c", axis='Y', segs=16)
fuel.box(-1.27, 1.27, -2.4, 3.8, 1.5, 1.8, "red_cross")
for sy in (-4.0, 1.0, 3.0):
    fuel.cyl((0, sy, 0.5), 0.5, 2.4, "tyre_c", axis='X', segs=10)
FUEL = template(fuel)
belt = P("CT.belt_loader_t")
belt.box(-1.0, 1.0, -2.5, 2.5, 0.3, 1.0, "yellow")
belt.beam((0, -3.5, 1.0), (0, 3.8, 3.6), 1.0, 0.25, "car_k")
belt.box(-0.7, 0.7, -2.3, -1.0, 1.0, 1.9, "glass_c")
for sy in (-1.8, 1.8):
    belt.cyl((0, sy, 0.3), 0.3, 2.0, "tyre_c", axis='X', segs=10)
BELT = template(belt)
cat = P("CT.catering_t")
cat.box(-1.2, 1.2, -4.5, -2.4, 0.5, 2.6, "white_c")
cat.box(-1.15, 1.15, -4.4, -3.4, 1.6, 2.4, "glass_c")
cat.box(-1.3, 1.3, -2.2, 3.8, 3.4, 6.0, "white_c")
cat.box(-1.32, 1.32, -2.2, 3.8, 4.3, 4.7, "teal")
for k in range(4):
    z = 1.0 + k * 0.6
    cat.beam((-1.0, -2.0, z), (-1.0, 3.6, z + 0.6), 0.1, 0.1, "metal")
    cat.beam((1.0, -2.0, z), (1.0, 3.6, z + 0.6), 0.1, 0.1, "metal")
for sy in (-3.6, 2.8):
    cat.cyl((0, sy, 0.5), 0.5, 2.4, "tyre_c", axis='X', segs=10)
CAT = template(cat)
cone = P("CT.cone_t")
cone.cyl((0, 0, 0.35), 0.2, 0.7, "cone", r2=0.03, segs=10)
cone.box(-0.25, 0.25, -0.25, 0.25, 0.0, 0.05, "cone")
CONE = template(cone, outline=0.01)
for n, (i, x) in enumerate(GATES):
    # plane centre at (x, -2775), nose +Y towards the terminal
    for k in range(3):
        place(CART if k else TUG, (x + 9.5, -2768 - k * 3.2, 0.03), 0)
    place(BELT, (x + 4.5, -2762, 0.03), 35)
    if n % 2 == 0:
        place(FUEL, (x - 11, -2778, 0.03), 0)
    if n == 3:
        place(CAT, (x - 4.0, -2760, 0.03), -30)
    for dx, dy in ((0, -2751), (18.5, -2768), (-18.5, -2768), (0, -2798)):
        place(CONE, (x + dx, dy, 0.03), 0)
place(TUG, (GATES[1][1], -2800, 0.03), 180)                                  # pushback tug

# ================================================================ SIGNS ON THE ROUTE
use(AD)


def road_sign(name, x, y, rot, lines, w=14, h=5.0, z=4.0):
    p = P(name)
    p.box(-w / 2, w / 2, -0.25, 0.25, z, z + h, "sign_green")
    for dx in (-w / 2 + 1.2, w / 2 - 1.2):
        p.box(dx - 0.25, dx + 0.25, -0.2, 0.2, 0, z, "metal")
    p.done((x, y, 0), rot, outline=0.04)
    for k, t in enumerate(lines):
        lb = label(name + "_t%d" % k, t, (0, -0.3, z + h - 1.3 - k * 1.6), 0, 1.15, M["sign_text"], 0.05)
        lb.parent = bpy.data.objects[name]


road_sign("CT.sign_heights_airport", 1250, -82, 0, ["SKYWAY  >", "AIRPORT  18 km"], w=12)
road_sign("CT.sign_airport_2km", 1342, -1700, 180, ["SKYHAVEN INTERNATIONAL", "2 km"], w=16)
road_sign("CT.sign_departures", 2560, -2470, 210, ["DEPARTURES  >", "ARRIVALS  >", "PARKING  P"], w=13, h=6.0)

flush("detail")
consolidate(AD, ("CT.sign_",))

# ================================================================ ACE'S DRIVE
use(DR)
# the same white car as the one in the mansion carport (mansion: centre (9.8, 2.4), nose -Y)
car = P("CT.ace_car")
W, L = 1.95, 4.75
car.box(-W / 2, W / 2, -L / 2, L / 2, 0.42, 1.08, "car_w")
car.box(-0.86, 0.86, -0.75, 1.55, 1.05, 1.6, "glass_c", taper=(0.9, 0.78))
car.box(-0.74, 0.74, -0.4, 1.25, 1.58, 1.66, "car_w")
for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    x, y = sx * (W / 2 - 0.12), sy * 1.52
    car.cyl((x, y, 0.38), 0.37, 0.28, "tyre_c", axis='X')
    car.cyl((x + sx * 0.12, y, 0.38), 0.21, 0.06, "metal", axis='X')
car.box(-0.85, -0.45, -L / 2 - 0.02, -L / 2 + 0.05, 0.82, 0.94, "lamp" if "lamp" in M else "white_c")
car.box(0.45, 0.85, -L / 2 - 0.02, -L / 2 + 0.05, 0.82, 0.94, "lamp" if "lamp" in M else "white_c")
car.box(-0.35, 0.35, -L / 2 - 0.02, -L / 2 + 0.05, 0.6, 0.8, "frame")
car.box(-0.85, -0.45, L / 2 - 0.05, L / 2 + 0.02, 0.82, 0.94, "red_cross")
car.box(0.45, 0.85, L / 2 - 0.05, L / 2 + 0.02, 0.82, 0.94, "red_cross")
car.box(-W / 2 - 0.02, W / 2 + 0.02, -L / 2 - 0.04, L / 2 + 0.04, 0.42, 0.5, "frame")
CAR = car.done(outline=0.02)
bv = CAR.modifiers.new("Bevel", 'BEVEL')
bv.width, bv.segments, bv.limit_method = 0.06, 2, 'ANGLE'
CAR.modifiers.move(len(CAR.modifiers) - 1, 0)


def offset_line(pts, off):
    """Offset a polyline to the right of its direction by `off` metres (right-hand traffic)."""
    pts = [Vector(p) for p in pts]
    out = []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1] - p).normalized(); n = Vector((d.y, -d.x))
        elif i == len(pts) - 1:
            d = (p - pts[i - 1]).normalized(); n = Vector((d.y, -d.x))
        else:
            d0, d1 = (p - pts[i - 1]).normalized(), (pts[i + 1] - p).normalized()
            n0, n1 = Vector((d0.y, -d0.x)), Vector((d1.y, -d1.x))
            n = (n0 + n1).normalized()
            n = n / max(0.3, n.dot(n0))
        out.append(p + n * off)
    return out


def smooth_corners(pts, r):
    """Replace each inner corner by a short arc (quadratic) so the car turns smoothly."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        rr = min(r, (b - a).length * 0.45, (c - b).length * 0.45)
        p0 = b + (a - b).normalized() * rr
        p2 = b + (c - b).normalized() * rr
        for k in range(7):
            t = k / 6
            out.append(p0 * (1 - t) ** 2 + b * 2 * t * (1 - t) + p2 * t * t)
    out.append(pts[-1])
    return out


SKY = [(1300, -66), (1360, -200), (1360, -1400), (1800, -2000), (2400, -2430), (2700, -2560)]
sky_lane = offset_line(SKY, 10.5)          # outer southbound lane (kept clear of traffic)
LEGS = [  # (points, speed m/s, marker name)
    ([(9.8, 2.4), (9.8, -20.0), (10.0, -52.0)], 3.5, "driveway"),
    ([(10.0, -52.0), (10.6, -62.0), (16.0, -70.0)], 4.0, "gate"),
    ([(16.0, -70.0), (1270.0, -70.0)], 16.0, "heights_avenue"),
    ([(1270.0, -70.0)] + [tuple(p) for p in sky_lane[1:-1]] + [(2690.0, -2572.0)], 30.0, "skyway"),
    ([(2690.0, -2572.0), (2760.0, -2583.2), (3240.0, -2583.2)], 11.0, "frontage"),
    ([(3240.0, -2583.2), (3300.0, -2583.2)], 4.0, "dropoff"),
]
route = []
seg_speed = []
for pts, v, nm in LEGS:
    pts = [Vector(p) for p in pts]
    if route and (route[-1] - pts[0]).length < 0.01:
        pts = pts[1:]
    route += pts
route = smooth_corners(route, 14.0)
cd = bpy.data.curves.new("CT.route_mansion_airport", 'CURVE')
cd.dimensions = '3D'
sp = cd.splines.new('POLY')
sp.points.add(len(route) - 1)
for pt, p in zip(sp.points, route):
    pt.co = (p.x, p.y, 0.05, 1)
cd.use_path = True
cd.path_duration = 10000
ROUTE = bpy.data.objects.new("CT.route_mansion_airport", cd)
DR.objects.link(ROUTE)
ROUTE.parent = RIG
ROUTE.hide_render = True

# timing: walk the legs in order, accumulate distance and time
FPS = 24
dist_total = sum((b - a).length for a, b in zip(route, route[1:]))
keys = [(1, 0.0)]
markers = []
t = 0.0
d_acc = 0.0
ri = 0
for pts, v, nm in LEGS:
    end = Vector(pts[-1])
    markers.append((nm, 1 + int(t * FPS)))
    # advance along route until we reach the vertex closest to the leg end
    while ri < len(route) - 1:
        seg = (route[ri + 1] - route[ri]).length
        d_acc += seg
        t += seg / v
        ri += 1
        if (route[ri] - end).length < 0.5 or (ri < len(route) - 1 and (route[ri] - end).length < 16 and
                                                (route[ri + 1] - end).length > (route[ri] - end).length):
            break
    keys.append((1 + t * FPS, d_acc / dist_total))
# ease: a short start from rest and a stop at the kerb
end_frame = int(keys[-1][0]) + 1
cd.animation_data_create()
for f, frac in keys:
    cd.eval_time = frac * cd.path_duration
    cd.keyframe_insert("eval_time", frame=f)
fc = cd.animation_data.action.fcurves[0] if hasattr(cd.animation_data.action, "fcurves") and cd.animation_data.action.fcurves else None
if fc is None:
    for lay in cd.animation_data.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for f in cb.fcurves:
                    fc = f
for kp in fc.keyframe_points:
    kp.interpolation = 'LINEAR'
fc.keyframe_points[0].interpolation = 'SINE'
fc.keyframe_points[-2].interpolation = 'SINE'
HOLD = 5 * FPS
S.frame_start, S.frame_end = 1, end_frame + HOLD
S.render.fps = FPS

CAR.parent = None
CAR.scale = (K.SCALE,) * 3
CAR.location = (0, 0, 0)
fp = CAR.constraints.new('FOLLOW_PATH')
fp.target = ROUTE
fp.use_curve_follow = True
fp.forward_axis = 'TRACK_NEGATIVE_Y'
fp.up_axis = 'UP_Z'

for nm, f in markers + [("arrive_departures", end_frame)]:
    mk_ = S.timeline_markers.get(nm) or S.timeline_markers.new(nm, frame=f)
    mk_.frame = f


def cam(name, lens):
    cdat = bpy.data.cameras.new(name)
    cdat.lens = lens
    cdat.clip_start, cdat.clip_end = 1.0, 16000
    co = bpy.data.objects.new(name, cdat)
    DR.objects.link(co)
    return co


chase = cam("CT_cam_drive", 26)
chase.parent = CAR                                        # car local metres: behind = +Y
chase.location = (0.0, 11.0, 3.6)
chase.rotation_euler = (math.radians(80), 0, math.radians(180))
drop = cam("CT_cam_dropoff", 28)
drop.parent = RIG
drop.location = (3322, -2568, 2.2)
drop.rotation_euler = (Vector((3292, -2590, 2.4)) - Vector((3322, -2568, 2.2))).to_track_quat('-Z', 'Y').to_euler()
gatecam = cam("CT_cam_gate_exit", 24)
gatecam.parent = RIG
gatecam.location = (30, -80, 3.0)
gatecam.rotation_euler = (Vector((10, -55, 2.0)) - Vector((30, -80, 3.0))).to_track_quat('-Z', 'Y').to_euler()
S["drive_end_frame"] = end_frame

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    open(OUT + ".frames.txt", "w").write(repr(markers + [("arrive", end_frame), ("total_m", round(dist_total))]))

"""Ace drives to the airport obeying the rules of the road (Kenya: keep LEFT).

    blender -b blender/sets/city_v003.blend --python tools/blender/build_drive_rules.py -- <out.blend> <ace.blend>

Replaces the simple drive of city v002 (collection CT_Drive) with:
  * the mansion gate: a security booth with a uniformed watchman (he salutes), an intercom /
    remote post with a blinking light; the gate leaves swing open when the car arrives and close
    behind it
  * Ace's car with open sides, seats, a see-through windscreen, steering wheel, indicators and
    brake lights; Ace sits in the right-hand driver's seat with his hands on the wheel
  * a driving simulation with acceleration, braking and stops:
      stop at the closed gate (Ace waves to the watchman) -> gate opens -> give way at the
      avenue (looks right, then left) -> LEFT indicator, turn onto Heights Avenue ->
      traffic lights at the Main Boulevard junction (red: stops at the line; green: goes) ->
      RIGHT indicator onto the Skyway -> zebra crossing at the terminal (waits for people
      crossing) -> pulls in at Departures
  * traffic lights with timed red / amber / green phases, pedestrians that walk across
Every timing is printed to <out.blend>.frames.txt and set as timeline markers.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
ACE = argv[1] if len(argv) > 1 else None
random.seed(5)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
SC = K.SCALE
K.PARENT[0] = RIG
FPS = 24
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {"uniform": "#2c3e66", "uniform_lt": "#5b7bb5", "skin": "#8a5a3c", "skin2": "#c48a5f",
             "cap": "#1f2b47", "badge": "#f2c14e", "shoe": "#1c1c20", "booth": "#f4f1ea", "seat": "#3a3f48",
             "dash": "#2e2e33", "shirt_p": "#e2574c", "shirt_q": "#4f9a8a", "trouser": "#3b3f46",
             "suitcase": "#c96f53", "eye_w": "#ffffff", "eye_k": "#1a1a1a"}.items():
    M[k] = toon("CT_" + k, v)


def emit_mat(name, hexcol, expr):
    """Emission material whose strength is driven by an expression of `frame`."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = lin(hexcol) + [1]
    nt.links.new(e.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
    fc = e.inputs[1].driver_add("default_value")
    fc.driver.expression = expr
    m.diffuse_color = lin(hexcol) + [1]
    return m


old = bpy.data.collections.get("CT_Drive")
if old:
    for o in list(old.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
for c in list(bpy.data.collections):
    if c.name.startswith("AceCartoon") and c.library is None:
        for o in list(c.all_objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)
DR = bpy.data.collections.new("CT_Drive")
bpy.data.collections["City"].children.link(DR)
use(DR)


# ================================================================ ROUTE (keep left)
def offset_line(pts, off):
    """Offset to the LEFT of travel by `off` (keep left)."""
    pts = [Vector(p) for p in pts]
    out = []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1] - p).normalized(); n = Vector((-d.y, d.x))
        elif i == len(pts) - 1:
            d = (p - pts[i - 1]).normalized(); n = Vector((-d.y, d.x))
        else:
            d0, d1 = (p - pts[i - 1]).normalized(), (pts[i + 1] - p).normalized()
            n0, n1 = Vector((-d0.y, d0.x)), Vector((-d1.y, d1.x))
            n = (n0 + n1).normalized()
            n = n / max(0.3, n.dot(n0))
        out.append(p + n * off)
    return out


def smooth_corners(pts, r):
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        rr = min(r, (b - a).length * 0.45, (c - b).length * 0.45)
        p0 = b + (a - b).normalized() * rr
        p2 = b + (c - b).normalized() * rr
        for k in range(9):
            t = k / 8
            out.append(p0 * (1 - t) ** 2 + b * 2 * t * (1 - t) + p2 * t * t)
    out.append(pts[-1])
    return out


SKY = [(1300, -66), (1360, -200), (1360, -1400), (1800, -2000), (2400, -2430), (2700, -2560)]
sky_lane = offset_line(SKY, 10.5)                       # outer southbound lane, east side
AV_LANE = -62.0                                          # Heights Avenue eastbound lane (north side)
FR_LANE = -2583.2                                        # terminal frontage, kerb lane (one-way east)
RAW = ([(9.8, 2.4), (9.8, -20.0), (10.0, -45.0), (10.0, -56.0), (11.5, -61.0), (17.0, AV_LANE),
        (1270.0, AV_LANE)] + [tuple(p) for p in sky_lane[1:-1]] +
       [(2690.0, -2572.0), (2760.0, FR_LANE), (3300.0, FR_LANE)])
route = smooth_corners(RAW, 12.0)
cum = [0.0]
for a, b in zip(route, route[1:]):
    cum.append(cum[-1] + (b - a).length)
TOTAL = cum[-1]


def s_at(pt):
    """Arc length of the route point nearest to pt."""
    pt = Vector(pt)
    best = (1e18, 0.0)
    for i, (a, b) in enumerate(zip(route, route[1:])):
        ab = b - a
        t = max(0.0, min(1.0, (pt - a).dot(ab) / max(1e-9, ab.length_squared)))
        d = (a + ab * t - pt).length
        if d < best[0]:
            best = (d, cum[i] + ab.length * t)
    return best[1]


def pos_at(s):
    for i in range(len(route) - 1):
        if cum[i + 1] >= s:
            t = (s - cum[i]) / max(1e-9, cum[i + 1] - cum[i])
            return route[i].lerp(route[i + 1], t)
    return route[-1]


# speed limits (m/s) by arc length, and the stops
LIMITS = [(0.0, 3.0), (s_at((10.0, -45.0)), 2.5), (s_at((17.0, AV_LANE)), 13.0), (s_at((1180.0, AV_LANE)), 8.0),
          (s_at(sky_lane[1]) + 40, 25.0), (s_at((2690.0, -2572.0)) - 120, 12.0), (s_at((2760.0, FR_LANE)), 8.0),
          (s_at((3200.0, FR_LANE)), 4.0)]
STOPS = [  # (arc length, dwell seconds, name)
    (s_at((10.0, -52.5)), 4.0, "gate"),
    (s_at((10.0, -56.6)), 4.5, "give_way"),
    (s_at((86.5, AV_LANE)), 6.0, "red_light"),
    (s_at((3144.0, FR_LANE)), 5.0, "zebra"),
    (TOTAL - 0.01, 6.0, "departures"),
]
STOPS.sort()


def limit_at(s):
    v = LIMITS[0][1]
    for s0, vv in LIMITS:
        if s >= s0:
            v = vv
    return v


ACC, DEC = 2.0, 2.8
frames_s, speeds = [], []
s, v, f = 0.0, 0.0, 1
events = {}
si = 0
hold = int(1.5 * FPS)                                    # a moment before setting off
for _ in range(hold):
    frames_s.append(s); speeds.append(0.0)
while si < len(STOPS) or s < TOTAL - 0.02:
    nxt = STOPS[si] if si < len(STOPS) else (TOTAL, 0, "end")
    ds = nxt[0] - s
    v_allow = math.sqrt(max(0.0, 2 * DEC * max(0.0, ds - 0.05)))
    for s0, vv in LIMITS:                                # slow down before lower limits ahead
        if s0 > s:
            v_allow = min(v_allow, math.sqrt(vv * vv + 2 * DEC * (s0 - s)))
    vt = min(limit_at(s), v_allow)
    v = min(vt, v + ACC / FPS) if v < vt else max(vt, v - DEC / FPS)
    s = min(nxt[0], s + v / FPS)
    frames_s.append(s); speeds.append(v)
    if nxt[0] - s < 0.06 and si < len(STOPS):
        s = nxt[0]
        arrive = len(frames_s) + 1
        for _ in range(int(nxt[1] * FPS)):
            frames_s.append(s); speeds.append(0.0)
        events[nxt[2]] = (arrive, len(frames_s) + 1)
        v = 0.0
        si += 1
    if len(frames_s) > 40000:
        break
END = len(frames_s)


def frame_at_s(sq):
    for i, sv in enumerate(frames_s):
        if sv >= sq:
            return i + 1
    return END


# ================================================================ THE CAR (cabin open so Ace shows)
car = P("CT.ace_car")
Wd, L = 1.95, 4.75
car.box(-Wd / 2, Wd / 2, -L / 2, L / 2, 0.42, 1.08, "car_w")              # body
car.box(-Wd / 2 + 0.06, Wd / 2 - 0.06, -L / 2 + 0.3, L / 2 - 0.3, 0.5, 0.55, "seat")   # floor
for x0 in (-0.86, 0.68):                                                 # pillars
    for y0, y1, z1 in ((-0.95, -0.8, 1.98), (0.25, 0.37, 1.98), (1.5, 1.68, 1.98)):
        car.box(x0, x0 + 0.18, y0, y1, 1.08, z1, "car_w")
car.box(-0.92, 0.92, -0.95, 1.7, 1.98, 2.06, "car_w")                   # roof
car.box(-0.86, 0.86, 1.55, 1.68, 1.08, 1.98, "glass_c")                  # rear window (solid)
car.box(-Wd / 2, Wd / 2, -L / 2, -1.1, 1.08, 1.12, "car_w")              # bonnet line
car.box(-0.9, 0.9, -1.25, -1.05, 1.0, 1.16, "dash")                      # dashboard (low, so his hands show)
for x in (-0.42, 0.42):                                                  # front seats
    car.box(x - 0.26, x + 0.26, -0.35, 0.15, 0.55, 0.78, "seat")
    car.box(x - 0.26, x + 0.26, 0.1, 0.24, 0.78, 1.55, "seat", taper=(0.9, 1.0))
    car.box(x - 0.14, x + 0.14, 0.12, 0.22, 1.55, 1.75, "seat")
car.box(-0.85, 0.85, 0.75, 1.3, 0.55, 0.8, "seat")                       # rear bench
car.box(-0.85, 0.85, 1.2, 1.4, 0.8, 1.45, "seat")
car.cyl((-0.42, -0.98, 1.22), 0.04, 0.4, "dash", axis='Y', segs=8)       # steering column
tw = Matrix.Translation((-0.42, -0.8, 1.32)) @ Matrix.Rotation(math.radians(62), 4, 'X')
ring = bmesh.new()
bmesh.ops.create_cone(ring, cap_ends=False, segments=20, radius1=0.2, radius2=0.2, depth=0.04)
for vtx in ring.verts:
    vtx.co = tw @ vtx.co
car._merge(ring, "dash", True)
for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    x, y = sx * (Wd / 2 - 0.12), sy * 1.52
    car.cyl((x, y, 0.38), 0.37, 0.28, "tyre_c", axis='X')
    car.cyl((x + sx * 0.12, y, 0.38), 0.21, 0.06, "metal", axis='X')
car.box(-0.35, 0.35, -L / 2 - 0.02, -L / 2 + 0.05, 0.6, 0.8, "frame")
car.box(-Wd / 2 - 0.02, Wd / 2 + 0.02, -L / 2 - 0.04, L / 2 + 0.04, 0.42, 0.5, "frame")
car.box(-0.85, -0.45, -L / 2 - 0.02, -L / 2 + 0.05, 0.82, 0.94, "white_c")   # headlights
car.box(0.45, 0.85, -L / 2 - 0.02, -L / 2 + 0.05, 0.82, 0.94, "white_c")
CAR = car.done(outline=0.02)
CAR.parent = None
CAR.scale = (SC,) * 3
# windscreen: see-through tinted glass
gm = bpy.data.materials.get("CT_windscreen") or bpy.data.materials.new("CT_windscreen")
gm.use_nodes = True
nt = gm.node_tree
nt.nodes.clear()
tr = nt.nodes.new('ShaderNodeBsdfTransparent')
em = nt.nodes.new('ShaderNodeEmission')
em.inputs[0].default_value = lin("#bfe0ee") + [1]
mx = nt.nodes.new('ShaderNodeMixShader')
mx.inputs[0].default_value = 0.18
nt.links.new(tr.outputs[0], mx.inputs[1])
nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
if hasattr(gm, "surface_render_method"):
    gm.surface_render_method = 'BLENDED'
ws = bmesh.new()
for a, b, c, d in [((-0.86, -0.95, 1.98), (0.86, -0.95, 1.98), (0.86, -1.1, 1.1), (-0.86, -1.1, 1.1))]:
    vs = [ws.verts.new(p) for p in (a, b, c, d)]
    ws.faces.new(vs)
wme = bpy.data.meshes.new("CT.ace_car_windscreen")
ws.to_mesh(wme)
ws.free()
wme.materials.append(gm)
WS = bpy.data.objects.new("CT.ace_car_windscreen", wme)
DR.objects.link(WS)
WS.parent = CAR


# indicators and brake lights (emission driven by frame / baked keys)
def windows_expr(wins, period=14):
    if not wins:
        return "0.05"
    cond = " or ".join("(%d<=frame<=%d)" % w for w in wins)
    return "(4.0 if (frame %% %d) < %d else 0.15) if (%s) else 0.15" % (period, period // 2, cond)


IND = {"L": [], "R": []}
brake = emit_mat("CT_brake_lights", "#ff3b30", "0.6")
lamp_mats = {}
for side in ("L", "R"):
    lamp_mats[side] = None                              # filled after the timings are known
ind_objs = {}
for side, sx in (("L", 1), ("R", -1)):                  # car's left = +X (car faces -Y)
    p = P("CT.ace_car_ind_" + side)
    p.box(sx * 0.98 - 0.06, sx * 0.98 + 0.06, -L / 2 - 0.03, -L / 2 + 0.1, 0.78, 0.9, "white_c")
    p.box(sx * 0.98 - 0.06, sx * 0.98 + 0.06, L / 2 - 0.1, L / 2 + 0.03, 0.78, 0.9, "white_c")
    o = p.done(outline=0.0)
    o.parent = CAR
    ind_objs[side] = o
bl = P("CT.ace_car_brakes")
for sx in (-1, 1):
    bl.box(sx * 0.65 - 0.2, sx * 0.65 + 0.2, L / 2 - 0.05, L / 2 + 0.03, 0.82, 0.96, "white_c")
blo = bl.done(outline=0.0)
blo.parent = CAR
blo.data.materials[0] = brake

# route curve + follow path
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
cd.animation_data_create()
act = bpy.data.actions.new("CT_route_time")
cd.animation_data.action = act
fc = act.fcurve_ensure_for_datablock(cd, "eval_time")
keys = [(i + 1, frames_s[i] / TOTAL * cd.path_duration) for i in range(0, END, 2)] + [(END, cd.path_duration)]
fc.keyframe_points.add(len(keys))
fc.keyframe_points.foreach_set("co", [c for kv in keys for c in kv])
for kp in fc.keyframe_points:
    kp.interpolation = 'LINEAR'
fc.update()
cfp = CAR.constraints.new('FOLLOW_PATH')
cfp.target = ROUTE
cfp.use_curve_follow = True
cfp.forward_axis = 'TRACK_NEGATIVE_Y'
cfp.up_axis = 'UP_Z'
S.frame_start, S.frame_end = 1, END + 48

# brake lights: bright while slowing or stopped
bact = bpy.data.actions.new("CT_brake_time")
bnode = [n for n in brake.node_tree.nodes if n.type == 'EMISSION'][0]
bnode.inputs[1].driver_remove("default_value")
brake.node_tree.animation_data_create()
brake.node_tree.animation_data.action = bact
bfc = bact.fcurve_ensure_for_datablock(brake.node_tree, 'nodes["%s"].inputs[1].default_value' % bnode.name)
prev = None
for i in range(1, END):
    on = 3.5 if (speeds[i] < speeds[i - 1] - 0.005 or speeds[i] < 0.05) else 0.5
    if on != prev:
        kp = bfc.keyframe_points.insert(i + 1, on)
        kp.interpolation = 'CONSTANT'
        prev = on

# indicator windows from the route
ev = events
fz_gw = ev["give_way"]
IND["L"].append((fz_gw[0] - 30, frame_at_s(s_at((40.0, AV_LANE)))))                    # left out of the gate
IND["R"].append((frame_at_s(s_at((1200.0, AV_LANE))), frame_at_s(s_at(sky_lane[1]) + 30)))  # right onto the Skyway
IND["L"].append((frame_at_s(s_at((2690.0, -2572.0)) - 90), frame_at_s(s_at((2760.0, FR_LANE)))))  # left to the terminal
IND["L"].append((frame_at_s(s_at((3250.0, FR_LANE))), END))                            # pulling in at the kerb
for side in ("L", "R"):
    mat = emit_mat("CT_indicator_" + side, "#ffa21a", windows_expr(IND[side]))
    ind_objs[side].data.materials[0] = mat

# ================================================================ ACE AT THE WHEEL
ACE_RIG = None
if ACE and os.path.exists(ACE):
    try:
        with bpy.data.libraries.load(ACE, link=True) as (src, dst):
            dst.collections = ["AceCartoon"]
        lc = dst.collections[0]
        inst = bpy.data.objects.new("ACE_instance", None)
        inst.instance_type = 'COLLECTION'
        inst.instance_collection = lc
        S.collection.objects.link(inst)
        bpy.context.view_layer.objects.active = inst
        inst.select_set(True)
        with bpy.context.temp_override(active_object=inst, object=inst, selected_objects=[inst],
                                       selected_editable_objects=[inst]):
            bpy.ops.object.make_override_library()
        ACE_RIG = [o for o in S.objects if o.type == 'ARMATURE' and o.library is None
                   and o.name.startswith("AC.rig")][0]
    except Exception as e:
        open((OUT or "drive") + ".ace_error.txt", "w").write(repr(e))
if ACE_RIG:
    rig = ACE_RIG
    if rig.animation_data:
        rig.animation_data.action = None
    hip_z = rig.data.bones["hips"].head_local.z * rig.scale.z if "hips" in rig.data.bones else 0.45
    rig.parent = CAR
    rig.matrix_parent_inverse = Matrix.Identity(4)
    rig.scale = tuple(v / SC for v in rig.scale)
    rig.location = (-0.42, -0.08, 0.86 - hip_z / SC)
    rig.rotation_euler = (0, 0, 0)
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'

    def key(bone, idx, f, val):
        b = pb[bone]
        b.rotation_euler[idx] = val
        b.keyframe_insert("rotation_euler", index=idx, frame=f)

    for s_ in ("L", "R"):
        sg = 1 if s_ == "R" else -1
        if "leg." + s_ in pb:
            key("leg." + s_, 0, 1, -1.45)
        if "foot." + s_ in pb:
            key("foot." + s_, 0, 1, 0.45)
        key("upper_arm." + s_, 0, 1, -1.05)
        key("upper_arm." + s_, 2, 1, sg * 0.12)
        key("forearm." + s_, 0, 1, -0.55)
        key("forearm." + s_, 2, 1, sg * -0.25)
        for fn in ("index", "middle", "ring", "pinky"):
            nm = "finger_%s.%s" % (fn, s_)
            if nm in pb:
                key(nm, 0, 1, -1.1)
    # head: looks at the watchman at the gate, right then left at the give-way, up at the lights,
    # right (south kerb) at the zebra, forward otherwise.  Y+ = turn to his left.
    look = [(1, 0.0)]
    g0, g1 = ev["gate"]
    look += [(g0 + 6, 0.0), (g0 + 18, 0.75), (g1 - 12, 0.75), (g1 + 6, 0.0)]
    w0, w1 = ev["give_way"]
    look += [(w0 + 4, 0.0), (w0 + 16, -0.85), (w0 + 46, -0.85), (w0 + 62, 0.8), (w0 + 92, 0.8), (w1 - 4, 0.0)]
    z0, z1 = ev["zebra"]
    look += [(z0 - 30, 0.0), (z0 - 10, -0.45), (z1 - 24, -0.2), (z1 + 6, 0.0)]
    look.sort()
    for fr, val in look:
        key("head", 1, fr, val)
    r0, r1 = ev["red_light"]
    for fr, val in ((r0 - 8, 0.0), (r0 + 10, -0.18), (r1 - 30, -0.18), (r1 - 10, 0.0)):
        key("head", 0, fr, val)
    # a friendly wave to the watchman with the left hand (the gate side)
    for fr, ux, fx, uz in ((g0 + 10, -1.05, -0.55, -0.12), (g0 + 22, -1.6, -1.3, -0.55),
                           (g1 - 20, -1.6, -1.3, -0.55), (g1 - 4, -1.05, -0.55, -0.12)):
        key("upper_arm.L", 0, fr, ux)
        key("upper_arm.L", 2, fr, uz)
        key("forearm.L", 0, fr, fx)
    for k in range(6):
        fr = g0 + 24 + k * 6
        if fr < g1 - 20:
            key("forearm.L", 2, fr, 0.25 if k % 2 else -0.25)
    key("forearm.L", 2, g1 - 18, -0.25)
    if "blink" in rig.keys():
        for fr in range(40, END, 97):
            for df, val in ((0, 0.0), (2, 1.0), (5, 0.0)):
                rig["blink"] = val
                rig.keyframe_insert('["blink"]', frame=fr + df)


# ================================================================ PEOPLE (watchman, pedestrians)
def person(name, loc, rot, cols, cap=False, suitcase=False, coll=None):
    """Simple cartoon person (big head like the family). Returns body, arms {L,R}, legs {L,R}."""
    shirt, trousers, skin = cols
    b = P(name)
    b.box(-0.21, 0.21, -0.13, 0.13, 0.86, 1.38, shirt, taper=(0.85, 0.9))
    b.box(-0.22, 0.22, -0.14, 0.14, 0.86, 0.94, "shoe")
    b.cyl((0, 0, 1.42), 0.07, 0.1, skin, segs=8)
    b.blob((0, 0, 1.66), (0.2, 0.19, 0.23), skin, subdiv=2)
    for sx in (-1, 1):
        b.blob((sx * 0.075, -0.17, 1.7), (0.045, 0.02, 0.055), "eye_w", subdiv=1)
        b.blob((sx * 0.075, -0.19, 1.69), (0.022, 0.01, 0.028), "eye_k", subdiv=1)
        b.blob((sx * 0.2, 0.0, 1.66), (0.035, 0.03, 0.05), skin, subdiv=1)
    b.blob((0, -0.2, 1.63), (0.03, 0.03, 0.03), skin, subdiv=1)
    b.box(-0.05, 0.05, -0.185, -0.175, 1.565, 1.575, "eye_k")
    if cap:
        b.cyl((0, 0.01, 1.84), 0.205, 0.11, "cap", segs=16)
        b.box(-0.14, 0.14, -0.33, -0.12, 1.79, 1.81, "cap")
        b.box(-0.04, 0.04, -0.205, -0.19, 1.83, 1.88, "badge")
        b.box(0.08, 0.16, -0.135, -0.125, 1.25, 1.31, "badge")
    else:
        b.blob((0, 0.03, 1.8), (0.19, 0.18, 0.11), "eye_k", subdiv=2)
    body = b.done(loc, rot, outline=0.012)
    (coll or DR).objects.unlink(body) if coll else None
    if coll:
        coll.objects.link(body)
    parts = {}
    for side, sx in (("L", 1), ("R", -1)):
        a = P("%s_arm_%s" % (name, side))
        a.box(-0.055, 0.055, -0.06, 0.06, -0.56, 0.0, shirt)
        a.blob((0, 0, -0.6), (0.06, 0.06, 0.07), skin, subdiv=1)
        ao = a.done(outline=0.01)
        ao.parent = body
        ao.location = (sx * 0.27, 0.0, 1.34)
        ao.rotation_mode = 'XYZ'
        lg = P("%s_leg_%s" % (name, side))
        lg.box(-0.075, 0.075, -0.08, 0.08, -0.8, 0.0, trousers)
        lg.box(-0.08, 0.08, -0.18, 0.08, -0.86, -0.78, "shoe")
        lo = lg.done(outline=0.01)
        lo.parent = body
        lo.location = (sx * 0.1, 0.0, 0.86)
        lo.rotation_mode = 'XYZ'
        parts[side] = (ao, lo)
    if suitcase:
        sc_ = P(name + "_case")
        sc_.box(-0.1, 0.1, -0.2, 0.2, -1.05, -0.62, "suitcase")
        sc_.box(-0.02, 0.02, -0.05, 0.05, -0.62, -0.58, "frame")
        co = sc_.done(outline=0.01)
        co.parent = parts["R"][0]
    return body, parts


def walk_drivers(parts, phase, rate=0.42):
    for side, sg in (("L", 1), ("R", -1)):
        ao, lo = parts[side]
        f = lo.driver_add("rotation_euler", 0)
        f.driver.expression = "%.2f*sin(frame*%.3f + %.2f)" % (0.45 * sg, rate, phase)
        f = ao.driver_add("rotation_euler", 0)
        f.driver.expression = "%.2f*sin(frame*%.3f + %.2f)" % (-0.4 * sg, rate, phase)


def keyloc(ob, pts, interp='LINEAR'):
    for fr, p in pts:
        ob.location = p
        ob.keyframe_insert("location", frame=fr)
    if ob.animation_data and ob.animation_data.action:
        for fcu in _fcurves(ob.animation_data.action):
            for kp in fcu.keyframe_points:
                kp.interpolation = interp


def _fcurves(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for lay in getattr(action, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


# --- the gate: booth, watchman, intercom post, gate leaves swinging open
booth = P("CT.security_booth")
booth.box(16.2, 19.8, -56.6, -52.6, 0.0, 2.6, "booth")
booth.box(16.15, 19.85, -56.65, -56.55, 1.1, 2.2, "glass_c")
booth.box(16.1, 16.2, -56.4, -52.8, 1.1, 2.2, "glass_c")
booth.box(15.7, 20.3, -57.3, -52.2, 2.6, 2.85, "white_c")
booth.box(19.8, 19.9, -55.6, -54.2, 0.0, 2.1, "door_blue")
booth.done(outline=0.03)
label("CT.security_sign", "SECURITY", (18.0, -57.35, 2.72), 0, 0.32, M["door_blue"], 0.03)
ic = P("CT.intercom_post")
ic.box(2.9, 3.4, -60.4, -59.9, 0.0, 1.45, "frame")
ic.box(2.85, 3.45, -60.45, -60.35, 1.0, 1.35, "metal")
ic.done(outline=0.02)
led = P("CT.intercom_led")
led.box(3.05, 3.25, -60.48, -60.44, 1.28, 1.33, "white_c")
lo_ = led.done(outline=0.0)
lo_.data.materials[0] = emit_mat("CT_intercom_led", "#3bd16f", "3.0 if (frame % 30) < 15 else 0.3")
g0, g1 = ev["gate"]
open_start, open_end = g0 - 30, g0 + 36                    # remote: starts opening as he pulls up
close_start = frame_at_s(s_at((10.0, -62.0))) + 60
for side, sgn_ in (("L", 1), ("R", -1)):
    leaf = bpy.data.objects.get("CT.mansion_gate_" + side)
    if leaf:
        leaf.rotation_mode = 'XYZ'
        for fr, ang in ((1, 0.0), (open_start, 0.0), (open_end, sgn_ * 1.6), (close_start, sgn_ * 1.6),
                        (close_start + 70, 0.0)):
            leaf.rotation_euler[2] = ang
            leaf.keyframe_insert("rotation_euler", index=2, frame=fr)
# watchman beside the booth, facing the drive; salutes as the car stops, steps back when it goes
guard, gparts = person("CT.watchman", (15.2, -55.0, 0.0), -60, ("uniform_lt", "uniform", "skin"), cap=True)
ra = gparts["R"][0]
for fr, (x, z) in ((1, (0.0, 0.0)), (g0 - 10, (0.0, 0.0)), (g0 + 8, (-2.6, -0.35)), (g1 - 6, (-2.6, -0.35)),
                   (g1 + 10, (0.0, 0.0))):
    ra.rotation_euler[0], ra.rotation_euler[2] = x, z
    ra.keyframe_insert("rotation_euler", index=0, frame=fr)
    ra.keyframe_insert("rotation_euler", index=2, frame=fr)
la = gparts["L"][0]
for fr, z in ((1, 0.0), (open_start - 8, 0.0), (open_start, -0.9), (open_start + 30, -0.9), (open_start + 40, 0.0)):
    la.rotation_euler[0] = -1.2 if z else 0.0                  # points the remote at the gate
    la.keyframe_insert("rotation_euler", index=0, frame=fr)

# ================================================================ TRAFFIC LIGHTS (Heights Ave x Main Boulevard)
r0, r1 = ev["red_light"]
T_amber, T_red, T_ra, T_green = r0 - 96, r0 - 60, r1 - 24, r1
A_expr = {  # avenue phase (Ace's direction)
    "red": "4.0 if (%d <= frame < %d) else 0.12" % (T_red, T_green),
    "amber": "4.0 if (%d <= frame < %d or %d <= frame < %d) else 0.12" % (T_amber, T_red, T_ra, T_green),
    "green": "4.0 if (frame < %d or frame >= %d) else 0.12" % (T_amber, T_green)}
B_expr = {  # boulevard phase (opposite)
    "red": "0.12 if (%d <= frame < %d) else 4.0" % (T_red + 24, T_ra - 30),
    "amber": "4.0 if (%d <= frame < %d) else 0.12" % (T_ra - 30, T_ra),
    "green": "4.0 if (%d <= frame < %d) else 0.12" % (T_red + 24, T_ra - 30)}
LCOL = {"red": "#ff3b30", "amber": "#ffb020", "green": "#2ee86a"}
for ph, ex in (("A", A_expr), ("B", B_expr)):
    for c in ("red", "amber", "green"):
        M["tl_%s_%s" % (ph, c)] = emit_mat("CT_tl_%s_%s" % (ph, c), LCOL[c], ex[c])
tl = P("CT.traffic_lights")
SIG = [((88.0, -55.0), (-1, 0), "A"), ((112.0, -77.0), (1, 0), "A"), ((90.5, -77.0), (0, -1), "B"),
       ((109.5, -55.0), (0, 1), "B")]
for (x, y), (fx, fy), ph in SIG:
    tl.box(x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.0, 4.6, "pole")
    cx, cy = x + fx * 0.25, y + fy * 0.25
    tl.box(cx - 0.22, cx + 0.22, cy - 0.22, cy + 0.22, 3.3, 4.6, "frame")
    for k, c in enumerate(("red", "amber", "green")):
        z = 4.35 - k * 0.42
        tl.cyl((cx + fx * 0.22, cy + fy * 0.22, z), 0.14, 0.06, "tl_%s_%s" % (ph, c),
               axis='X' if fx else 'Y', segs=12)
tl.box(87.5, 87.9, -66.0, -58.0, 0.02, 0.05, "white_c")                    # stop line (eastbound)
tl.box(112.1, 112.5, -74.0, -66.0, 0.02, 0.05, "white_c")
tl.box(91.0, 100.0, -77.6, -77.2, 0.02, 0.05, "white_c")
tl.done(outline=0.015)

# ================================================================ PEDESTRIANS AT THE ZEBRA (frontage x=3150)
z0, z1 = ev["zebra"]
walkers = [("CT.ped_a", ("shirt_p", "trouser", "skin2"), 3148.6, -2591.0, -2559.0, z0 - 130, True),
           ("CT.ped_b", ("shirt_q", "trouser", "skin"), 3150.8, -2592.0, -2558.0, z0 - 105, False),
           ("CT.ped_c", ("uniform_lt", "trouser", "skin2"), 3149.6, -2557.0, -2591.0, z0 - 60, True)]
for nm, cols, x, ya, yb, t0, case in walkers:
    head = 180 if yb > ya else 0
    body, parts = person(nm, (x, ya, 0.0), head, cols, suitcase=case)
    t1 = t0 + int(abs(yb - ya) / 1.3 * FPS)
    keyloc(body, [(1, (x, ya, 0.0)), (t0, (x, ya, 0.0)), (t1, (x, yb, 0.0))])
    walk_drivers(parts, random.uniform(0, 3))

# ================================================================ CAMERAS + MARKERS
def cam(name, loc, target, lens, parent=None):
    cdat = bpy.data.cameras.new(name)
    cdat.lens = lens
    cdat.clip_start, cdat.clip_end = 0.5, 16000
    co = bpy.data.objects.new(name, cdat)
    DR.objects.link(co)
    co.parent = parent or RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


chase = cam("CT_cam_drive", (0, 11.0, 3.6), (0, 0, 1.2), 26, CAR)
cam("CT_cam_driver", (-0.2, -3.6, 1.55), (-0.42, 0.0, 1.45), 24, CAR)
cam("CT_cam_gate_out", (24.0, -77.0, 2.2), (11.0, -56.0, 1.6), 24)
cam("CT_cam_gate_in", (4.5, -40.0, 2.0), (12.0, -57.0, 1.3), 26)
cam("CT_cam_junction", (120.0, -96.0, 5.0), (90.0, -63.0, 2.0), 26)
cam("CT_cam_zebra", (3178.0, -2597.0, 2.6), (3146.0, -2578.0, 1.3), 26)
cam("CT_cam_dropoff", (3322.0, -2568.0, 2.2), (3292.0, -2590.0, 2.4), 28)

for mk in list(S.timeline_markers):
    S.timeline_markers.remove(mk)
for nm, (a, b) in ev.items():
    S.timeline_markers.new(nm + "_stop", frame=a)
    S.timeline_markers.new(nm + "_go", frame=b)
S["drive_end_frame"] = END

consolidate(DR, ("CT.ace_car", "CT.watchman", "CT.ped_", "CT.intercom_led", "CT.traffic_lights"))

if OUT:
    info = dict(events=ev, end=END, total_m=round(TOTAL), indicators=IND, gate=(open_start, open_end, close_start),
                lights=(T_amber, T_red, T_ra, T_green), ace=bool(ACE_RIG))
    open(OUT + ".frames.txt", "w").write(repr(info))
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

"""Airport patch: a modern control tower, runway lighting and aircraft that land and take off.

    blender -b blender/sets/city_v006.blend --python tools/blender/build_tower_runways.py -- <out.blend>

  * the old simple tower (at x 3960, y -2650) is cut out of the merged airport mesh and replaced by a
    modern tower: two-storey base, slim tapering shaft with a glass strip, a flared glass cab with
    navy mullions, a roof with antennas and a blinking red beacon (~75 m)
  * runway 09L/27R (y -3050) and 09R/27L (y -3400): white edge lights every 60 m, green threshold
    lights, red end lights, a 900 m approach light line in the grass to the west of each runway,
    PAPI lights (two red, two white) beside the touchdown zone, an orange windsock that sways
  * movement (keys with a Cycles modifier, so they repeat every 30 s through any shot):
      CT.jet_landing    approaches from the west, flares, touches down on 09R and rolls out
      CT.jet_takeoff    rolls down 09L, rotates and climbs away to the east
Cameras CT_cam_tower, CT_cam_tower_cab, CT_cam_rwy_landing, CT_cam_rwy_takeoff.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
FPS = 24
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m
for k, v in {"tw_concrete": "#e9e6e0", "tw_glass": "#4a7896", "tw_navy": "#1f2f57", "tw_steel": "#9aa0a7",
             "sock": "#f07a1e", "sock_w": "#fbfbfb"}.items():
    M[k] = toon("CT_" + k, v)


def emit(name, hexcol, strength=2.0, expr=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = lin(hexcol) + [1]
    e.inputs[1].default_value = strength
    if expr:
        fc = e.inputs[1].driver_add("default_value")
        fc.driver.expression = expr
    nt.links.new(e.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
    m.diffuse_color = lin(hexcol) + [1]
    return m


M["l_white"] = emit("CT_l_white", "#fff8e0", 3.0)
M["l_green"] = emit("CT_l_green", "#38e07a", 3.0)
M["l_red"] = emit("CT_l_red", "#ff3b30", 3.0)
M["l_beacon"] = emit("CT_l_beacon", "#ff2a20", 1.0, "6.0 if (frame % 36) < 6 else 0.2")
M["l_approach"] = emit("CT_l_approach", "#fff2c8", 1.0, "5.0 if ((frame // 2) % 15) == 0 else 1.2")

old = bpy.data.collections.get("CT_TowerRunways")
if old:
    for o in list(old.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
TR = bpy.data.collections.new("CT_TowerRunways")
bpy.data.collections["City"].children.link(TR)
use(TR)

# ================================================================ remove the old simple tower
TX, TY = 3960.0, -2650.0
for o in list(bpy.data.collections["CT_Airport"].objects):
    if o.type != 'MESH' or o.library:
        continue
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    kill = [v for v in bm.verts
            if (v.co.x - TX) ** 2 + (v.co.y - TY) ** 2 < 12.5 ** 2 and v.co.z > 0.2]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        bm.to_mesh(me)
        me.update()
    bm.free()

# ================================================================ the modern tower
tw = P("CT.tower")
tw.box(TX - 14, TX + 14, TY - 9, TY + 9, 0.0, 9.0, "tw_concrete")            # base building
tw.box(TX - 14.1, TX + 14.1, TY - 9.1, TY - 8.9, 1.0, 3.8, "tw_glass")
tw.box(TX - 14.1, TX + 14.1, TY - 9.1, TY - 8.9, 5.2, 8.0, "tw_glass")
tw.box(TX - 14.5, TX + 14.5, TY - 9.5, TY + 9.5, 9.0, 9.6, "tw_navy")
tw.box(TX - 14.6, TX + 14.6, TY - 9.6, TY - 9.5, 9.2, 9.3, "ac_red" if "ac_red" in M else "red_cross")
tw.cyl((TX, TY, 9.6 + 27.5), 4.6, 55.0, "tw_concrete", segs=24, r2=3.4)    # tapering shaft
tw.box(TX - 0.9, TX + 0.9, TY - 4.7, TY - 3.9, 11.0, 63.0, "tw_glass")      # glass strip (lift)
tw.cyl((TX, TY, 66.0), 6.0, 2.2, "tw_concrete", segs=24, r2=7.0)            # cab floor, flaring out
tw.cyl((TX, TY, 70.0), 7.2, 6.0, "tw_glass", segs=16, r2=9.0)               # glass cab, wider at the top
for k in range(16):                                                         # mullions
    a = k / 16 * math.tau
    tw.beam((TX + math.cos(a) * 7.25, TY + math.sin(a) * 7.25, 67.0),
            (TX + math.cos(a) * 9.05, TY + math.sin(a) * 9.05, 73.0), 0.28, 0.28, "tw_navy")
tw.cyl((TX, TY, 73.6), 9.8, 1.3, "tw_navy", segs=24)                        # roof
tw.cyl((TX, TY, 74.6), 6.0, 0.8, "tw_concrete", segs=24)
for k in range(3):                                                          # antennas
    a = k / 3 * math.tau
    tw.cyl((TX + math.cos(a) * 3.0, TY + math.sin(a) * 3.0, 78.0), 0.12, 6.0, "tw_steel", segs=6)
tw.blob((TX + 2.0, TY, 75.8), (1.3, 1.3, 1.1), "sock_w")                    # radar dome
tw.done(outline=0.12)
bc = P("CT.tower_beacon")
bc.blob((TX, TY, 81.4), (0.6, 0.6, 0.6), "l_beacon", subdiv=1)
bc.done(outline=0.0)
label("CT.tower_sign", "SKYHAVEN TOWER", (TX, TY - 9.65, 7.0), 0, 1.6, M["tw_navy"], 0.08)

# ================================================================ runway lighting
RWY = [(-3050.0, "L"), (-3400.0, "R")]
X0, X1, HALF = 2000.0, 5000.0, 30.0
lt = P("CT.runway_lights")
for ry, tag in RWY:
    x = X0 + 30
    while x < X1 - 20:                                    # edge lights
        for sy in (-1, 1):
            lt.cyl((x, ry + sy * (HALF + 1.5), 0.25), 0.25, 0.5, "l_white", segs=8)
        x += 60
    for k in range(-7, 8):                                # thresholds (green) and ends (red)
        y = ry + k * 4.0
        lt.box(X0 - 1.0, X0 + 0.0, y - 0.35, y + 0.35, 0.0, 0.4, "l_green")
        lt.box(X1, X1 + 1.0, y - 0.35, y + 0.35, 0.0, 0.4, "l_red")
    for k in range(1, 31):                                # approach line to the west
        x = X0 - k * 30
        lt.box(x - 0.4, x + 0.4, ry - 0.4, ry + 0.4, 0.0, 1.2, "tw_steel")
        lt.box(x - 0.6, x + 0.6, ry - 0.6, ry + 0.6, 1.2, 1.6, "l_approach")
        if k % 10 == 0:
            for j in range(-5, 6):
                lt.box(x - 0.4, x + 0.4, ry + j * 2.5 - 0.4, ry + j * 2.5 + 0.4, 1.2, 1.6, "l_approach")
    for j, col in enumerate(("l_red", "l_red", "l_white", "l_white")):   # PAPI on the left of touchdown
        lt.box(X0 + 290, X0 + 292, ry + HALF + 12 + j * 3.0, ry + HALF + 13.5 + j * 3.0, 0.0, 1.1, "tw_steel")
        lt.box(X0 + 289.6, X0 + 290.0, ry + HALF + 12.2 + j * 3.0, ry + HALF + 13.3 + j * 3.0, 0.5, 1.0, col)
lt.done(outline=0.0)
# windsock beside runway 09L
ws_pole = P("CT.windsock_pole")
ws_pole.cyl((2500, -3010, 4.0), 0.12, 8.0, "tw_steel", segs=8)
ws_pole.done(outline=0.03)
ws = P("CT.windsock")
for k in range(5):
    r0, r1 = 0.6 - k * 0.08, 0.6 - (k + 1) * 0.08
    ws.cyl((0, k * 0.8 + 0.4, 0), r0, 0.8, "sock" if k % 2 == 0 else "sock_w", axis='Y', segs=12, r2=r1)
wso = ws.done(outline=0.02)
wso.location = (2500, -3010, 7.6)
fc = wso.driver_add("rotation_euler", 2)
fc.driver.expression = "0.35*sin(frame*0.05) + 0.12*sin(frame*0.23)"
fc = wso.driver_add("rotation_euler", 0)
fc.driver.expression = "-0.25 + 0.08*sin(frame*0.31)"


# ================================================================ aircraft movements (looping)
def fcurves_of(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for lay in getattr(action, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def animate(ob, keys, period):
    """keys: (frame, (x, y, z), pitch_radians). Heading +X (rot z 90). Cycles every `period` frames."""
    ob.animation_data_clear()
    ob.rotation_mode = 'XYZ'
    for f, loc, pitch in keys:
        ob.location = loc
        ob.rotation_euler = (pitch, 0.0, math.radians(90))
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    for fcu in fcurves_of(ob.animation_data.action):
        for kp in fcu.keyframe_points:
            kp.interpolation = 'BEZIER'
        fcu.modifiers.new('CYCLES')


P_LEN = 30 * FPS
land = bpy.data.objects.get("CT.jet_landing")
if land:
    ry = -3400.0
    animate(land, [(1, (800.0, ry, 260.0), math.radians(-2)),
                   (int(10 * FPS), (1900.0, ry, 60.0), math.radians(-3)),
                   (int(13 * FPS), (2240.0, ry, 6.0), math.radians(-7)),      # flare
                   (int(14 * FPS), (2380.0, ry, 0.0), math.radians(-2)),      # touchdown
                   (int(22 * FPS), (3500.0, ry, 0.0), 0.0),                   # roll-out, slowing
                   (int(29 * FPS), (3900.0, ry, 0.0), 0.0),
                   (P_LEN, (800.0, ry, 260.0), math.radians(-2))], P_LEN)
    for fcu in fcurves_of(land.animation_data.action):                        # jump back unseen
        fcu.keyframe_points[-1].interpolation = 'CONSTANT'
        fcu.keyframe_points[-2].interpolation = 'CONSTANT'
take = bpy.data.objects.get("CT.jet_takeoff")
if take:
    ry = -3050.0
    animate(take, [(1, (2100.0, ry, 0.0), 0.0),
                   (int(4 * FPS), (2140.0, ry, 0.0), 0.0),                     # lined up, power up
                   (int(14 * FPS), (3150.0, ry, 0.0), 0.0),
                   (int(16 * FPS), (3500.0, ry, 2.0), math.radians(-10)),     # rotate, lift off
                   (int(26 * FPS), (5600.0, ry, 260.0), math.radians(-12)),
                   (P_LEN, (6400.0, ry, 420.0), math.radians(-10))], P_LEN)
    for fcu in fcurves_of(take.animation_data.action):
        fcu.keyframe_points[-1].interpolation = 'CONSTANT'


# ================================================================ cameras
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.5, 16000
    co = bpy.data.objects.new(name, cd)
    TR.objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


cam("CT_cam_tower", (3905, -2735, 4.0), (3960, -2650, 40.0), 24)
cam("CT_cam_tower_cab", (TX - 3.0, TY - 11.5, 72.0), (3200, -3200, 0.0), 24)
cam("CT_cam_rwy_landing", (2520, -3460, 3.0), (2300, -3400, 8.0), 26)
cam("CT_cam_rwy_takeoff", (3600, -2990, 3.0), (3300, -3050, 5.0), 24)

consolidate(TR, ("CT.windsock", "CT.tower_beacon", "CT_cam"))

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

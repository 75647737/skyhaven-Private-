"""Build the family's mansion (exterior) in the cartoon toon style.

    blender -b --factory-startup --python tools/blender/build_mansion.py -- <out.blend>

A modern tropical villa: stacked white slabs with a deep cantilevered terrace,
a warm wood-clad wing, stacked-stone walls, a tall white lattice screen, a wood
pergola with hanging vines over the carport, glass railings with planters, a
lawn, paving, trees and Ace's car under the carport.

Units are metres at the same scale as the existing sets (doors about 2.1 m,
characters about 1.07 m tall). The front of the house faces -Y (towards the
street and the default cameras), X runs along the front, Z is up.
Everything lives in collections MN_House, MN_Grounds, MN_Car and MN_Cams under
"Mansion", so shots can link the "Mansion" collection.
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(7)

# ---------------------------------------------------------------- scene reset
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
S = bpy.context.scene
S.name = "Mansion"



import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

ROOT = bpy.data.collections.new("Mansion")
S.collection.children.link(ROOT)
COLLS = {}
for n in ("MN_House", "MN_Grounds", "MN_Car", "MN_Cams"):
    c = bpy.data.collections.new(n)
    ROOT.children.link(c)
    COLLS[n] = c
RIG = bpy.data.objects.new("MN.root", None)
ROOT.objects.link(RIG)
RIG.scale = (K.SCALE,) * 3
K.PARENT[0] = RIG
use(COLLS["MN_House"])

# ================================================================ the house
use(COLLS["MN_House"])
# plinth and front step
box("MN.plinth", -11.8, 12.4, -0.9, 10.4, 0.0, 0.15, M["white2"], bevel=0.02)

# --- ground floor -----------------------------------------------------------
# left wing (white frame with deep window bays)
box("MN.gf_left_body", -10.0, -3.0, 0.8, 10.0, 0.15, 3.0, M["sand"])
boxes("MN.gf_left_frame", [
    (-10.0, -9.6, -0.35, 0.8, 0.15, 3.0, 0), (-3.4, -3.0, -0.35, 0.8, 0.15, 3.0, 0),
    (-8.05, -7.8, -0.25, 0.8, 0.15, 2.6, 0), (-5.7, -5.45, -0.25, 0.8, 0.15, 2.6, 0),
    (-10.0, -3.0, -0.35, 0.8, 2.55, 3.0, 0)], [M["white"]], outline=0.025)
window("MN.gf_win_a", -9.45, -8.2, 0.75, 2.4, 0.8, cols=1)
window("MN.gf_win_b", -7.6, -5.85, 0.75, 2.4, 0.8, cols=3)
window("MN.gf_win_c", -5.3, -3.55, 0.75, 2.4, 0.8, cols=3)
planter("MN.gf_planter_l", -9.6, -3.4, -0.3, 0.45, 0.15, h=0.55, size=0.28)
# grey and beige blocks
box("MN.gf_grey", -3.0, -1.0, -0.45, 10.0, 0.15, 2.95, M["grey"])
box("MN.gf_beige", -1.0, 2.0, 0.0, 10.0, 0.15, 3.0, M["beige"])
window("MN.gf_win_d", 0.1, 1.3, 1.3, 2.3, 0.0, cols=2)
# stone wing with tall slot windows and the front door
box("MN.gf_stone_body", 2.0, 7.2, 0.25, 10.0, 0.15, 3.0, M["stone1"])
stone_face("MN.gf_stone_face", 2.0, 7.2, 0.15, 2.95, 0.25)
for i, x in enumerate((2.6, 3.25, 3.9)):
    window("MN.gf_slot%d" % i, x, x + 0.4, 0.7, 2.6, 0.2, cols=1, mats=[M["glass"], M["wood_dk"], M["glass_lt"]])
door = boxes("MN.front_door", [
    (5.35, 6.55, 0.17, 0.2, 0.15, 2.55, 0),
    (5.2, 6.7, 0.1, 0.2, 2.55, 2.68, 1), (5.2, 5.35, 0.1, 0.2, 0.15, 2.55, 1), (6.55, 6.7, 0.1, 0.2, 0.15, 2.55, 1)]
    + [(5.42 + k * 0.155, 5.42 + k * 0.155 + 0.02, 0.15, 0.17, 0.3, 2.45, 1) for k in range(7)]
    + [(6.35, 6.39, 0.08, 0.17, 0.9, 1.6, 2)], [M["door"], M["wood_dk"], M["chrome"]], outline=0.01)
pot_plant("MN.door_pot_l", 4.85, -0.35, 0.15, r=0.25, h=0.55, leaf=0.5)
pot_plant("MN.door_pot_r", 7.0, -0.35, 0.15, r=0.2, h=0.45, leaf=0.42)
pot_plant("MN.door_pot_r2", 4.4, -0.45, 0.15, r=0.18, h=0.35, leaf=0.36)

# ground-floor roof = first-floor terrace slab (deep white fascia)
box("MN.gf_slab", -10.2, 7.2, -0.6, 10.2, 2.95, 3.35, M["white"], outline=0.03)
# carport roof and columns
box("MN.carport_slab", 7.2, 12.4, -1.0, 9.0, 2.95, 3.3, M["white"], outline=0.03)
boxes("MN.carport_cols", [(11.8, 12.25, -0.9, -0.45, 0.15, 2.95, 0), (11.8, 12.25, 5.6, 6.05, 0.15, 2.95, 0)],
      [M["white"]], outline=0.025)
box("MN.carport_back", 7.2, 12.4, 8.8, 9.0, 0.15, 2.95, M["sand"])
planter("MN.carport_planter", 12.4, 14.6, -1.3, -0.3, 0.0, h=0.6, size=0.3)

# --- first floor ------------------------------------------------------------
# left wing clad in warm wood with a big white-framed window
box("MN.ff_wood", -9.0, -3.5, 1.0, 9.5, 3.35, 6.4, M["wood"])
grooves("MN.ff_wood_lines", -9.0, -3.5, 3.35, 6.4, 1.0)
grooves("MN.ff_wood_lines_side", 1.0, 9.5, 3.35, 6.4, -9.0, side=True)
boxes("MN.ff_win_surround", [(-7.6, -4.4, 0.65, 1.0, 5.95, 6.2, 0), (-7.6, -4.4, 0.65, 1.0, 3.75, 4.0, 0),
                             (-7.6, -7.35, 0.65, 1.0, 4.0, 5.95, 0), (-4.65, -4.4, 0.65, 1.0, 4.0, 5.95, 0)],
      [M["white"]], outline=0.02)
window("MN.ff_win_big", -7.35, -4.65, 4.0, 5.95, 1.0, cols=4)
# middle: recessed beige living space with sliding glass doors onto the terrace
box("MN.ff_mid", -3.5, 3.8, 2.0, 9.5, 3.35, 6.4, M["sand"])
window("MN.ff_slider", -2.8, 2.6, 3.4, 5.7, 2.0, cols=4)
# behind the lattice: darker volume so the holes read
box("MN.ff_screen_back", 3.8, 6.6, 1.4, 9.5, 3.35, 9.4, M["shadow"], outline=0.0)
# tall white lattice screen (jaali)
lat = []
X0, X1, Z0, Z1 = 3.8, 6.6, 3.35, 9.4
nx, nz = 8, 20
bar = 0.11
for k in range(nx + 1):
    x = X0 + (X1 - X0) * k / nx
    lat.append((x - bar / 2, x + bar / 2, 0.55, 0.85, Z0, Z1, 0))
for k in range(nz + 1):
    z = Z0 + (Z1 - Z0) * k / nz
    lat.append((X0 - bar / 2, X1 + bar / 2, 0.55, 0.85, z - bar / 2, z + bar / 2, 0))
lat += [(X0 - 0.2, X0, 0.5, 0.9, Z0, Z1 + 0.05, 0), (X1, X1 + 0.05, 0.5, 0.9, Z0, Z1 + 0.05, 0)]
boxes("MN.lattice_screen", lat, [M["white"]], outline=0.01)
# tall beige fin beside the screen
box("MN.fin_tall", 6.6, 7.2, 0.35, 9.5, 3.35, 9.85, M["beige"])
# first-floor stepped parapets and terrace railing
steps_l = [(-7.4 + 0.25 * k, -7.15 + 0.25 * k, -0.6, 0.6, 3.35, 3.35 + 0.95 - 0.22 * k, 0) for k in range(4)]
steps_r = [(3.0 + 0.25 * k, 3.25 + 0.25 * k, -0.6, 0.6, 3.35, 3.35 + 0.29 + 0.22 * k, 0) for k in range(4)]
boxes("MN.parapet_steps", steps_l + steps_r, [M["white"]], outline=0.02)
glass_rail("MN.ff_rail", -6.4, 3.0, -0.52, -0.48, 3.35)
planter("MN.ff_planter", -6.4, 3.0, -0.45, 0.05, 3.35, h=0.32, size=0.22)
# carport terrace: railing, wooden pergola, curtain of vines
glass_rail("MN.cp_rail", 7.2, 12.3, -0.95, -0.91, 3.3)
glass_rail("MN.cp_rail_side", 12.28, 12.32, -0.95, 8.8, 3.3)
perg = [(11.85, 12.15, -0.85, -0.55, 3.3, 6.25, 0), (11.85, 12.15, 6.3, 6.6, 3.3, 6.25, 0),
        (7.2, 12.3, -0.9, -0.55, 6.0, 6.3, 0), (7.2, 12.3, 6.3, 6.65, 6.0, 6.3, 0),
        (11.85, 12.2, -0.9, 6.65, 6.0, 6.3, 0)]
x = 7.45
while x < 11.8:
    perg.append((x, x + 0.09, -1.05, 6.8, 6.3, 6.46, 0))
    x += 0.38
boxes("MN.pergola", perg, [M["wood"]], outline=0.012)
use(COLLS["MN_House"])
vines("MN.pergola_vines", 7.3, 12.2, -0.95, 6.02, 0.5, 2.2, 46)
pot_plant("MN.cp_pot", 11.4, 0.2, 3.3, r=0.24, h=0.5, leaf=0.5)

# --- second level: big cantilevered terrace and upper rooms -----------------
box("MN.cantilever", -9.0, 3.8, -2.3, 6.5, 6.4, 7.0, M["white"], outline=0.035)
box("MN.cantilever_soffit", -8.8, 3.6, -2.1, 0.9, 6.38, 6.4, M["white2"], outline=0)
box("MN.upper", -7.5, 3.8, 0.6, 7.0, 7.0, 9.4, M["beige"])
window("MN.upper_win", -6.2, -1.6, 7.4, 9.0, 0.6, cols=4)
window("MN.upper_win2", -0.8, 2.8, 7.0, 9.0, 0.6, cols=3)
glass_rail("MN.can_rail", -5.4, 3.7, -2.24, -2.2, 7.0)
stone_face("MN.can_stonewall", -8.9, -5.4, 7.0, 7.6, -2.0)
box("MN.can_stonewall_core", -8.9, -5.4, -2.0, -1.5, 7.0, 7.6, M["stone2"], outline=0.0)
shrubs("MN.can_stone_plants", -8.8, -5.5, -1.95, -1.55, 7.55, 0.24)
vines("MN.can_vines", -8.9, -7.0, -2.32, 6.95, 0.6, 1.7, 14)
glass_rail("MN.can_rail_side", -9.0, -8.96, -2.3, 0.5, 7.0)
# roof slab, slatted pergola roof over the lattice side, top tier
box("MN.roof", -9.0, 3.8, -1.2, 7.6, 9.4, 9.85, M["white"], outline=0.035)
sl = [(3.8, 7.2, -1.2, -0.9, 9.5, 9.85, 0), (6.9, 7.2, -1.2, 7.6, 9.5, 9.85, 0)]
x = 3.95
while x < 6.9:
    sl.append((x, x + 0.1, -1.2, 7.6, 9.55, 9.8, 0))
    x += 0.32
boxes("MN.roof_slats", sl, [M["white"]], outline=0.01)
box("MN.top_tier", -5.5, 1.5, 1.6, 6.6, 9.85, 10.65, M["white2"], outline=0.03)
box("MN.top_tier_cap", -5.7, 1.7, 1.4, 6.8, 10.65, 10.85, M["white"], outline=0.03)

# --- left tower: stone with white louvres and a green wall ------------------
box("MN.tower", -11.4, -10.0, 1.0, 4.2, 0.15, 7.4, M["stone2"])
stone_face("MN.tower_face", -11.4, -10.0, 0.15, 7.4, 1.0)
box("MN.tower_cap", -11.6, -9.8, 0.8, 4.4, 7.4, 7.6, M["white"], outline=0.025)
fins = [(-12.0, -10.0, 0.2, 2.8, 4.3 + 0.36 * k, 4.42 + 0.36 * k, 0) for k in range(8)]
fins.append((-12.05, -11.9, 0.2, 2.8, 4.3, 7.3, 0))
boxes("MN.tower_fins", fins, [M["white"]], outline=0.012)
vines("MN.tower_vines", -11.35, -10.1, 0.96, 6.8, 1.0, 3.6, 12)

# ================================================================ grounds
use(COLLS["MN_Grounds"])
box("MN.lawn", -60, 60, -60, 60, -0.05, 0.0, M["lawn"], outline=0)
box("MN.apron", -12.2, 14.8, -7.0, -0.9, 0.0, 0.03, M["paving"], outline=0)
box("MN.carport_floor", 7.2, 12.4, -0.9, 8.8, 0.15, 0.16, M["paving"], outline=0)
box("MN.driveway", 7.4, 12.2, -60, -7.0, 0.0, 0.025, M["drive"], outline=0)
box("MN.path", 4.9, 6.9, -16, -7.0, 0.0, 0.03, M["paving"], outline=0)
# paving joints
j = []
for k in range(1, 9):
    y = -0.9 - k * 0.76
    j.append((-12.2, 14.8, y - 0.015, y + 0.015, 0.03, 0.034, 0))
x = -12.2
while x < 14.8:
    j.append((x - 0.015, x + 0.015, -7.0, -0.9, 0.03, 0.034, 0))
    x += 1.5
boxes("MN.apron_joints", j, [M["drive"]], outline=0)
shrubs("MN.hedge_front_l", -13.0, -3.0, -8.2, -7.3, 0.0, 0.4)
shrubs("MN.hedge_front_r", 14.2, 20.0, -8.2, -7.3, 0.0, 0.4)
shrubs("MN.hedge_side_l", -13.6, -12.6, -6.5, 9.0, 0.0, 0.45)
tree("MN.tree_l1", -17.0, 3.0, 1.15, 3.6)
tree("MN.tree_l2", -15.5, 13.0, 1.0, 3.2)
tree("MN.tree_r1", 17.5, -5.0, 1.3, 4.2)
tree("MN.tree_r2", 18.5, 8.0, 1.1, 3.6)
tree("MN.tree_b1", -2.0, 17.5, 1.2, 3.4)
tree("MN.tree_b2", 8.0, 16.0, 1.1, 3.0)
for i, (x, y) in enumerate(((-11.0, -1.6), (-1.6, -1.3), (13.6, -2.2))):
    pot_plant("MN.yard_pot%d" % i, x, y, 0.0, r=0.3, h=0.6, leaf=0.6)

# ================================================================ Ace's car
use(COLLS["MN_Car"])
CX, CY = 9.8, 2.4


def car():
    W, L = 1.95, 4.75
    box("MN.car_body", CX - W / 2, CX + W / 2, CY - L / 2, CY + L / 2, 0.42, 1.08, M["car"], outline=0.02, bevel=0.14)
    box("MN.car_cabin", CX - 0.86, CX + 0.86, CY - 0.75, CY + 1.55, 1.05, 1.6, M["car_glass"], outline=0.02,
        bevel=0.08, taper=(0.9, 0.78))
    box("MN.car_roof", CX - 0.74, CX + 0.74, CY - 0.4, CY + 1.25, 1.58, 1.66, M["car"], outline=0.015, bevel=0.03)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x = CX + sx * (W / 2 - 0.12)
        y = CY + sy * 1.52
        cyl("MN.car_tyre%d" % i, (x, y, 0.38), 0.37, 0.28, M["tyre"], axis='X', outline=0.012)
        cyl("MN.car_hub%d" % i, (x + sx * 0.12, y, 0.38), 0.21, 0.06, M["chrome"], axis='X', outline=0.006)
    boxes("MN.car_details", [
        (CX - 0.85, CX - 0.45, CY - L / 2 - 0.02, CY - L / 2 + 0.05, 0.82, 0.94, 0),
        (CX + 0.45, CX + 0.85, CY - L / 2 - 0.02, CY - L / 2 + 0.05, 0.82, 0.94, 0),
        (CX - 0.35, CX + 0.35, CY - L / 2 - 0.02, CY - L / 2 + 0.05, 0.6, 0.8, 1),
        (CX - 0.85, CX - 0.45, CY + L / 2 - 0.05, CY + L / 2 + 0.02, 0.82, 0.94, 2),
        (CX + 0.45, CX + 0.85, CY + L / 2 - 0.05, CY + L / 2 + 0.02, 0.82, 0.94, 2),
        (CX - W / 2 - 0.02, CX + W / 2 + 0.02, CY - L / 2 - 0.04, CY + L / 2 + 0.04, 0.42, 0.5, 1)],
        [M["lamp"], M["frame"], M["tail"]], outline=0.006)


car()

# ================================================================ light, world, cameras
use(COLLS["MN_Cams"])
w = bpy.data.worlds.new("MN_world")
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs[0].default_value = lin("#c6dbea") + [1]
bg.inputs[1].default_value = 0.9
S.world = w

sun = bpy.data.lights.new("MN_sun", 'SUN')
sun.energy = 3.6
sun.color = lin("#fff1dc")
sun.angle = math.radians(2)
so = bpy.data.objects.new("MN_sun", sun)
COLLS["MN_Cams"].objects.link(so)
so.parent = RIG
d = Vector((0.55, 0.62, -0.56)).normalized()
so.rotation_euler = (-d).to_track_quat('Z', 'Y').to_euler()
so.location = (0, 0, 20)




def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 400
    co = bpy.data.objects.new(name, cd)
    COLLS["MN_Cams"].objects.link(co)
    co.parent = RIG
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


S.camera = cam("MN_cam_3q", (-19.0, -23.0, 2.6), (0.5, 2.0, 4.6), 26)
cam("MN_cam_front", (0.5, -36.0, 4.5), (0.5, 2.0, 4.8), 32)
cam("MN_cam_aerial", (-28.0, -36.0, 26.0), (1.0, 2.0, 2.5), 30)
cam("MN_cam_entry", (11.0, -9.5, 1.1), (5.5, 0.3, 1.8), 24)

S.render.engine = 'BLENDER_EEVEE'
S.eevee.taa_render_samples = 16
S.view_settings.view_transform = 'Standard'
S.render.resolution_x, S.render.resolution_y = 1920, 1080
S.render.fps = 24

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

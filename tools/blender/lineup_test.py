"""Character lineup test: are the cast readable by silhouette and face alone?

    blender -b --factory-startup --python tools/blender/lineup_test.py -- <repo_root> <out_dir>

Appends the five cartoon masters into an empty scene, side by side at their true relative size,
and renders (orthographic, so nothing is distorted by perspective):
  lineup_colour.png          front, full colour, names under each figure
  lineup_silhouette.png      front, solid black on white (no colour, no lines)
  lineup_silhouette_3q.png   three-quarter view, solid black
  lineup_silhouette_side.png profile, solid black
  faces_front.png            heads only, aligned at the same eye height, front
  faces_3q.png               heads only, three-quarter
Nothing is saved.
"""
import bpy, os, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
CH = os.path.join(ROOT, "blender", "characters")
CAST = [("Ace", "ace_cartoon_v004.blend", "AceCartoon"),
        ("Tori", "tori_cartoon_v004.blend", "ToriCartoon"),
        ("Max", "max_cartoon_v002.blend", "MaxCartoon"),
        ("Daniel", "daniel_cartoon_v001.blend", "DanielCartoon"),
        ("Emma", "emma_cartoon_v001.blend", "EmmaCartoon")]
GAP = 0.78
S = bpy.context.scene
for o in list(bpy.data.objects):          # factory scene: cube, camera, light
    bpy.data.objects.remove(o)


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


figs = []
for i, (name, fn, cname) in enumerate(CAST):
    with bpy.data.libraries.load(os.path.join(CH, fn), link=False) as (src, dst):
        dst.collections = [cname]
    col = dst.collections[0]
    S.collection.children.link(col)
    rig = [o for o in col.all_objects if o.type == 'ARMATURE' and o.parent is None][0]
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    figs.append(dict(name=name, rig=rig, col=col, x0=rig.location.x, z0=rig.location.z))

bpy.context.view_layer.update()
# the masters carry preview helpers (backdrop cards, floors): keep only the figure itself
hidden = []
for f in figs:
    for o in f["col"].all_objects:
        if o is not None and o.type in ('MESH', 'CURVE') and max(o.dimensions) > 1.4:
            o.hide_render = True
            hidden.append(o.name)
print("HIDDEN", hidden)
# true heights, then spacing: each figure's slot sized by its height so small Max is not lost
for f in figs:
    pts = []
    for o in f["col"].all_objects:
        if o.type == 'MESH' and not o.hide_render:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    f["top"] = max(p.z for p in pts)
    f["w"] = max(p.x for p in pts) - min(p.x for p in pts)
    f["cx"] = (max(p.x for p in pts) + min(p.x for p in pts)) / 2
    pb = f["rig"].pose.bones["head"]
    mw = f["rig"].matrix_world
    f["head_c"] = (mw @ pb.head + mw @ pb.tail) / 2
PITCH = max(f["w"] for f in figs) + 0.22
for i, f in enumerate(figs):
    f["slot"] = i * PITCH
    f["rig"].location.x += f["slot"] - f["cx"]
x = (len(figs) - 1) * PITCH
TOTAL = x
tallest = max(f["top"] for f in figs)
mid_x = (figs[0]["slot"] + figs[-1]["slot"]) / 2

# names
lab_mat = bpy.data.materials.new("lineup_label")
lab_mat.use_nodes = True
nt = lab_mat.node_tree
nt.nodes.clear()
e = nt.nodes.new('ShaderNodeEmission')
e.inputs[0].default_value = lin("#2b2f36") + [1]
nt.links.new(e.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
labels = []
for f in figs:
    cu = bpy.data.curves.new("lab_" + f["name"], 'FONT')
    cu.body = f["name"] + "\n%.2f m" % f["top"]
    cu.align_x = 'CENTER'
    cu.size = 0.085
    ob = bpy.data.objects.new("lab_" + f["name"], cu)
    S.collection.objects.link(ob)
    ob.location = (f["slot"], -0.3, -0.12)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(lab_mat)
    labels.append(ob)
# height guides every 0.25 m
gm = bpy.data.materials.new("lineup_guide")
gm.use_nodes = True
g = gm.node_tree
g.nodes.clear()
ge = g.nodes.new('ShaderNodeEmission')
ge.inputs[0].default_value = lin("#c9ced6") + [1]
g.links.new(ge.outputs[0], g.nodes.new('ShaderNodeOutputMaterial').inputs[0])
guides = []
for k in range(0, 6):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(mid_x, 0.45, k * 0.25))
    p = bpy.context.object
    p.scale = (TOTAL + 0.6, 0.004, 1)
    p.rotation_euler = (math.radians(90), 0, 0)
    p.data.materials.append(gm)
    guides.append(p)

# light + world
sd = bpy.data.lights.new("sun", 'SUN')
sd.energy = 3.2
so = bpy.data.objects.new("sun", sd)
S.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-30))
w = bpy.data.worlds.new("lineup")
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.0
S.world = w
S.view_settings.view_transform = 'Standard'
S.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [i.identifier for i in S.render.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
S.eevee.taa_render_samples = 32
S.render.film_transparent = False

cd = bpy.data.cameras.new("cam")
cd.type = 'ORTHO'
cam = bpy.data.objects.new("cam", cd)
S.collection.objects.link(cam)
S.camera = cam

black = bpy.data.materials.new("sil")
black.use_nodes = True
b = black.node_tree
b.nodes.clear()
be = b.nodes.new('ShaderNodeEmission')
be.inputs[0].default_value = (0, 0, 0, 1)
b.links.new(be.outputs[0], b.nodes.new('ShaderNodeOutputMaterial').inputs[0])
VL = bpy.context.view_layer


def outlines(on):
    for f in figs:
        for o in f["col"].all_objects:
            for m in o.modifiers:
                if m.type == 'SOLIDIFY' and m.use_flip_normals:
                    m.show_render = on


def turn(deg):
    for f in figs:
        f["rig"].rotation_euler.z = math.radians(deg)


def shot(fname, tgt, ortho, res, sil=False, ang=0.0):
    a = math.radians(ang)
    cam.location = Vector(tgt) + Vector((0, -10, 0))
    cam.rotation_euler = (math.radians(90), 0, 0)
    cd.ortho_scale = ortho
    S.render.resolution_x, S.render.resolution_y = res
    S.render.resolution_percentage = 100
    VL.material_override = black if sil else None
    outlines(not sil)
    for o in labels + guides:
        o.hide_render = sil
    S.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)


span = figs[-1]["slot"] - figs[0]["slot"] + 1.0
full_c = (mid_x, 0, tallest / 2 - 0.05)
shot("lineup_colour.png", full_c, max(span, (tallest + 0.4) * 16 / 9), (1920, 1080))
shot("lineup_silhouette.png", full_c, max(span, (tallest + 0.4) * 16 / 9), (1920, 1080), sil=True)
turn(-35)
shot("lineup_silhouette_3q.png", full_c, max(span, (tallest + 0.4) * 16 / 9), (1920, 1080), sil=True)
turn(-90)
shot("lineup_silhouette_side.png", full_c, max(span, (tallest + 0.4) * 16 / 9), (1920, 1080), sil=True)

# faces: heads side by side at the same height, framed tight
turn(0)
bpy.context.view_layer.update()
HZ = max(f["head_c"].z for f in figs)
FP = 0.42
for i, f in enumerate(figs):
    f["rig"].location.z += HZ - f["head_c"].z
    f["rig"].location.x += i * FP - f["slot"]
for o in labels + guides:
    o.hide_render = True
labels.clear(); guides.clear()
fc = (2 * FP, 0, HZ + 0.01)
shot("faces_front.png", fc, 5 * FP, (1920, 640))
turn(-35)
shot("faces_3q.png", fc, 5 * FP, (1920, 640))
turn(-90)
shot("faces_side.png", fc, 5 * FP, (1920, 640))
print("LINEUP_DONE")

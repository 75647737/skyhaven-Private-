"""Daniel Carter (cartoon), dad of the Carters, the middle-class neighbours (blueprint, later seasons).

    blender -b blender/characters/ace_cartoon_v004.blend --python tools/blender/build_daniel.py -- <out.blend>

Built from cartoon Ace v004 so he shares the rig, real fingers, seated eyes, mouth set and
face sliders (lip-sync and expressions work the same way). Original look, clearly not Ace:
  * about 40, a little taller (rig x1.05), a friendly dad belly, broader jaw
  * deep brown skin #8d5a3b, short curly black hair #1e1410 and a neat short beard
  * mustard polo shirt #e0a43c with short sleeves (forearms bare), collar and two buttons
  * dark blue jeans #34465e, white trainers with grey soles, a wristwatch on the left wrist
Prefix "DC", collection "DanielCartoon", rig "DC.rig".
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(40)

PAL = dict(skin="#8d5a3b", polo="#e0a43c", jeans="#34465e", hair="#1e1410", shoe="#f2f2f0",
           sole="#b9bec4", lace="#d9dde1", watch="#2e2e33", watch_face="#d5dade", collar="#e9b54e",
           button="#fbf6ec", lips="#6e3f2a")


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def set_colour(m, hexcol):
    """Repaint a toon material (Color Ramp or plain) to a new base colour, keeping its shading steps."""
    c = lin(hexcol)
    done = False
    for n in m.node_tree.nodes if m.node_tree else []:
        if n.type == 'VALTORGB':
            els = n.color_ramp.elements
            ks = [0.62, 0.84, 1.0] + [1.0] * max(0, len(els) - 3)
            if len(els) == 2:
                ks = [0.7, 1.0]
            for e, k in zip(els, ks):
                e.color = [v * k for v in c] + [1]
            done = True
    m.diffuse_color = c + [1]
    return done


# ------------------------------------------------------------------ rename Ace -> Daniel
for o in bpy.data.objects:
    if o.name.startswith("AC."):
        o.name = "DC." + o.name[3:]
for m in bpy.data.materials:
    if m.name.startswith("AC_"):
        m.name = "DC_" + m.name[3:]
for a in bpy.data.actions:
    if a.name.startswith("AC_"):
        a.name = "DC_" + a.name[3:]
for c in bpy.data.collections:
    if c.name == "AceCartoon":
        c.name = "DanielCartoon"
for ar in bpy.data.armatures:
    if ar.name.startswith("AC"):
        ar.name = "DC" + ar.name[2:]
RIG = bpy.data.objects["DC.rig"]
COLL = bpy.data.collections["DanielCartoon"]
if RIG.animation_data:
    RIG.animation_data.action = None
for pb in RIG.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)
RIG.data.pose_position = 'REST'
bpy.context.view_layer.update()
MAT = {m.name[3:]: m for m in bpy.data.materials if m.name.startswith("DC_")}

# ------------------------------------------------------------------ colours
set_colour(MAT["skin"], PAL["skin"])
set_colour(MAT["sweater"], PAL["polo"])
set_colour(MAT["trousers"], PAL["jeans"])
set_colour(MAT["hair"], PAL["hair"])
for k, col in (("shoe_upper", PAL["shoe"]), ("shoe_sole", PAL["sole"]), ("shoe_lace", PAL["lace"])):
    if k in MAT:
        set_colour(MAT[k], col)
if "nose" in MAT:
    set_colour(MAT["nose"], "#7a4c31")
MAT["sweater"].name = "DC_polo"
MAT["trousers"].name = "DC_jeans"


def new_mat(name, hexcol):
    m = MAT["skin"].copy()
    m.name = "DC_" + name
    set_colour(m, hexcol)
    MAT[name] = m
    return m


OUTL = bpy.data.materials.get("DC_outline")

# ------------------------------------------------------------------ taller, belly, broader jaw
RIG.scale = (1.05, 1.05, 1.05)
sw = bpy.data.objects["DC.sweater"]
for v in sw.data.vertices:                        # 8-vertex box (bevel + subsurf): belly forward, wider hem
    if v.co.z < 0.42:
        v.co.x *= 1.12
        if v.co.y < 0:
            v.co.y -= 0.045
        else:
            v.co.y += 0.01
    else:
        v.co.x *= 1.04
hp = bpy.data.objects["DC.hips"]
for v in hp.data.vertices:
    v.co.x *= 1.1
    if v.co.y < 0:
        v.co.y -= 0.02
hd = bpy.data.objects["DC.head"]
for v in hd.data.vertices:                        # broader, squarer jaw below the eyes
    t = max(0.0, min(1.0, (0.76 - v.co.z) / 0.11))
    v.co.x *= 1.0 + 0.09 * t * t
    if v.co.z < 0.68:
        v.co.z -= 0.006 * t

# ------------------------------------------------------------------ short sleeves: forearms bare
for side in ("L", "R"):
    arm = bpy.data.objects["DC.arm." + side]
    me = arm.data
    if MAT["skin"].name not in [m.name for m in me.materials]:
        me.materials.append(MAT["skin"])
    ski = [m.name for m in me.materials].index(MAT["skin"].name)
    # outline slot for the new material: put outline at the end and re-point the solidify offset
    n_main = len([m for m in me.materials if m and not m.name.endswith("outline")])
    for p in me.polygons:
        zc = sum(me.vertices[i].co.z for i in p.vertices) / len(p.vertices)
        if zc < 0.505:
            p.material_index = ski
    mats = [m for m in me.materials]
    mains = [m for m in mats if not m.name.endswith("outline")]
    remap = {i: mains.index(m) for i, m in enumerate(mats) if m in mains}
    idx = [remap.get(p.material_index, 0) for p in me.polygons]
    me.materials.clear()
    for m in mains:
        me.materials.append(m)
    for _ in mains:
        me.materials.append(OUTL)
    for p, i in zip(me.polygons, idx):
        p.material_index = i
    for mod in arm.modifiers:
        if mod.type == 'SOLIDIFY':
            mod.material_offset = len(mains)
    cuff = bpy.data.objects.get("DC.cuff." + side)
    if cuff:
        bpy.data.objects.remove(cuff)


# ------------------------------------------------------------------ new parts (bone-parented)
def part(name, bone, bm, mats, outline=-0.004, sub=1):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    COLL.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    if sub:
        s = ob.modifiers.new("Smooth", 'SUBSURF')
        s.levels = s.render_levels = sub
    if outline and OUTL:
        for _ in mats:
            me.materials.append(OUTL)
        so = ob.modifiers.new("Outline", 'SOLIDIFY')
        so.thickness, so.offset, so.use_flip_normals = outline, 1, True
        so.material_offset, so.use_rim = len(mats), False
    ob.parent = RIG
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = RIG.matrix_world.copy()
    return ob


def blob_into(bm, c, r, mi=0, subdiv=1):
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1)
    me = bpy.data.meshes.new("_t")
    for v in tmp.verts:
        v.co = Vector((c[0] + v.co.x * r[0], c[1] + v.co.y * r[1], c[2] + v.co.z * r[2]))
    tmp.to_mesh(me)
    tmp.free()
    off = len(bm.faces)
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for f in bm.faces[off:]:
        f.material_index = mi
    bpy.data.meshes.remove(me)


def box_into(bm, c, s, mi=0):
    tmp = bmesh.new()
    bmesh.ops.create_cube(tmp, size=1)
    me = bpy.data.meshes.new("_t")
    for v in tmp.verts:
        v.co = Vector((c[0] + v.co.x * s[0], c[1] + v.co.y * s[1], c[2] + v.co.z * s[2]))
    tmp.to_mesh(me)
    tmp.free()
    off = len(bm.faces)
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for f in bm.faces[off:]:
        f.material_index = mi
    bpy.data.meshes.remove(me)


# head ellipsoid (from Ace's head bounds) used to place hair and beard on the skin
HC = Vector((0.0, 0.0, 0.825))
HR = Vector((0.15 * 1.02, 0.143, 0.19))


def on_head(theta, phi, lift=0.0):
    """theta: around (0 = front -Y, + = his left), phi: elevation (-pi/2..pi/2)."""
    x = math.sin(theta) * math.cos(phi)
    y = -math.cos(theta) * math.cos(phi)
    z = math.sin(phi)
    n = Vector((x / HR.x, y / HR.y, z / HR.z)).normalized()
    p = Vector((HC.x + HR.x * x, HC.y + HR.y * y, HC.z + HR.z * z))
    return p + n * lift, n


# short curly hair: small curls over the top and back, a clean hairline above the forehead
old_hair = bpy.data.objects.get("DC.hair")
if old_hair:
    bpy.data.objects.remove(old_hair)
bm = bmesh.new()
for i in range(520):
    th = random.uniform(-math.pi, math.pi)
    ph = random.uniform(0.05, 1.5)
    front = abs(th) < 1.25
    if front and ph < 0.62:                       # forehead: hairline higher at the front
        continue
    if abs(abs(th) - math.pi / 2) < 0.32 and ph < 0.32:   # keep the ears clear
        continue
    p, n = on_head(th, ph, 0.012)
    r = random.uniform(0.022, 0.032)
    blob_into(bm, p, (r, r, r * 0.85), 0)
part("DC.hair", "head", bm, [MAT["hair"]], outline=-0.003, sub=0)

# neat short beard along the jaw, chin and up to the sideburns (mouth area left clear)
bm = bmesh.new()
for i in range(420):
    th = random.uniform(-1.75, 1.75)
    ph = random.uniform(-0.95, -0.2)
    p, n = on_head(th, ph, 0.004)
    if p.z > 0.715 and abs(th) < 1.1:
        continue
    if abs(p.x) < 0.06 and 0.645 < p.z < 0.715:  # the mouth
        continue
    if p.y > 0.02:
        continue
    r = random.uniform(0.012, 0.017)
    blob_into(bm, p, (r, r, r * 0.8), 0)
for i in range(60):                               # sideburns
    side = random.choice((-1, 1))
    th = side * random.uniform(1.25, 1.5)
    ph = random.uniform(-0.25, 0.45)
    p, n = on_head(th, ph, 0.004)
    blob_into(bm, p, (0.013, 0.013, 0.011), 0)
for i in range(40):                               # moustache, small and close to the lip
    th = random.uniform(-0.3, 0.3)
    p, n = on_head(th, -0.52, 0.006)
    p.z = 0.712 + random.uniform(-0.002, 0.003)
    blob_into(bm, p, (0.011, 0.009, 0.007), 0)
part("DC.beard", "head", bm, [MAT["hair"]], outline=-0.002, sub=0)

# polo collar, placket and buttons on the chest bone
new_mat("collar", PAL["collar"])
new_mat("button", PAL["button"])
bm = bmesh.new()
for sx in (-1, 1):
    box_into(bm, (sx * 0.045, -0.085, 0.6), (0.07, 0.05, 0.018), 0)
    box_into(bm, (sx * 0.06, -0.02, 0.612), (0.04, 0.12, 0.016), 0)
box_into(bm, (0.0, 0.05, 0.612), (0.12, 0.03, 0.02), 0)
box_into(bm, (0.0, -0.124, 0.555), (0.03, 0.006, 0.07), 0)
blob_into(bm, (0.0, -0.13, 0.575), (0.006, 0.004, 0.006), 1)
blob_into(bm, (0.0, -0.13, 0.545), (0.006, 0.004, 0.006), 1)
part("DC.collar", "chest", bm, [MAT["collar"], MAT["button"]], outline=-0.002, sub=1)
# sleeve hems (a slightly darker band where the sleeve ends)
new_mat("hem", "#c98f2d")
for side, sx in (("L", 1), ("R", -1)):
    bm = bmesh.new()
    tmp = bmesh.new()
    bmesh.ops.create_cone(tmp, cap_ends=False, segments=16, radius1=0.036, radius2=0.036, depth=0.012)
    me = bpy.data.meshes.new("_t")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    arm_ob = bpy.data.objects["DC.arm." + side]
    zs = [v.co for v in arm_ob.data.vertices if abs(v.co.z - 0.505) < 0.01]
    cx = sum(v.x for v in zs) / max(1, len(zs)) if zs else sx * 0.2
    cy = sum(v.y for v in zs) / max(1, len(zs)) if zs else 0.0
    rr = max(((v.x - cx) ** 2 + (v.y - cy) ** 2) ** 0.5 for v in zs) if zs else 0.036
    for v in bm.verts:
        v.co = Vector((cx + v.co.x / 0.036 * (rr + 0.004), cy + v.co.y / 0.036 * (rr + 0.004), 0.505 + v.co.z))
    part("DC.hem." + side, "upper_arm." + side, bm, [MAT["hem"]], outline=-0.002, sub=0)
# wristwatch (left wrist)
new_mat("watch", PAL["watch"])
new_mat("watch_face", PAL["watch_face"])
fa = RIG.data.bones["forearm.L"]
wrist = fa.tail_local
bm = bmesh.new()
tmp = bmesh.new()
bmesh.ops.create_cone(tmp, cap_ends=False, segments=14, radius1=0.026, radius2=0.026, depth=0.012)
me = bpy.data.meshes.new("_t")
tmp.to_mesh(me)
tmp.free()
bm.from_mesh(me)
bpy.data.meshes.remove(me)
for v in bm.verts:
    v.co = Vector((wrist.x + v.co.x, wrist.y + v.co.y, wrist.z + 0.018 + v.co.z))
blob_into(bm, (wrist.x + 0.026, wrist.y - 0.004, wrist.z + 0.018), (0.006, 0.013, 0.013), 1)
part("DC.watch", "forearm.L", bm, [MAT["watch"], MAT["watch_face"]], outline=-0.002, sub=0)

RIG.data.pose_position = 'POSE'
for o in COLL.all_objects:
    o.hide_render = False
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

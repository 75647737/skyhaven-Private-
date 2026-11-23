"""Daniel Carter (cartoon), dad of the Carters, the middle-class neighbours (blueprint, later seasons).

    blender -b blender/characters/ace_cartoon_v004.blend --python tools/blender/build_daniel.py -- <out.blend>

Built from cartoon Ace v004 so he shares the rig, real fingers, seated eyes, mouth set and
face sliders (lip-sync and expressions work the same way). Original look, clearly not Ace:
  * about 40, a little taller (rig x1.05), a friendly dad belly, broader jaw
  * fair European skin #f2cbb0, short neat dark-blond hair #a3743f with a side-swept quiff, blue eyes, clean-shaven
  * mustard polo shirt #e0a43c with short sleeves (forearms bare), collar and two buttons
  * dark blue jeans #34465e, white trainers with grey soles, a wristwatch on the left wrist
Prefix "DC", collection "DanielCartoon", rig "DC.rig".
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(40)

PAL = dict(skin="#f2cbb0", polo="#e0a43c", jeans="#34465e", hair="#a3743f", shoe="#f2f2f0", iris="#3f74a8",
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
    set_colour(MAT["nose"], "#e7a98c")
if "iris" in MAT:
    set_colour(MAT["iris"], PAL["iris"])
MAT["sweater"].name = "DC_polo"
MAT["trousers"].name = "DC_jeans"


def new_mat(name, hexcol):
    m = MAT["skin"].copy()
    m.name = "DC_" + name
    set_colour(m, hexcol)
    MAT[name] = m
    return m


OUTL = bpy.data.materials.get("DC_outline")
# Ace's sweater knit lines (curve objects) don't belong on a polo
for o in list(bpy.data.objects):
    mats = getattr(o.data, "materials", None) if o.data else None
    if mats and any(m and m.name == "DC_knit" for m in mats):
        bpy.data.objects.remove(o)
if bpy.data.objects.get("DC.hem"):                 # the sweater's ribbed hem (a curve) - not on a polo
    bpy.data.objects.remove(bpy.data.objects["DC.hem"])

# ------------------------------------------------------------------ taller, belly, broader jaw
sw = bpy.data.objects["DC.sweater"]
for v in sw.data.vertices:                        # slimmer upper body that narrows to a waist, small tummy
    v.co.y *= 0.9
    if v.co.z < 0.42:
        v.co.x *= 0.86
        if v.co.y < 0:
            v.co.y -= 0.012
    else:
        v.co.x *= 0.9
hp = bpy.data.objects["DC.hips"]
for v in hp.data.vertices:
    v.co.x *= 0.92
    v.co.y *= 0.92
SHOULDER_IN = 0.194 * 0.1                         # arms move in with the narrower shoulders
# smaller, neater ears, a little closer to the head
for side, sx in (("L", 1), ("R", -1)):
    ear = bpy.data.objects.get("DC.ear." + side)
    if ear:
        piv = Vector((sx * 0.135, 0.01, 0.795))
        for v in ear.data.vertices:
            r = v.co - piv
            v.co = piv + Vector((r.x * 0.62, r.y * 0.78, r.z * 0.8))
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


# short, neat dark-blond hair: a smooth cap with a soft side-swept quiff at the front
old_hair = bpy.data.objects.get("DC.hair")
if old_hair:
    bpy.data.objects.remove(old_hair)
bm = bmesh.new()
for i in range(170):
    th = random.uniform(-math.pi, math.pi)
    ph = random.uniform(0.12, 1.5)
    front = abs(th) < 1.2
    if front and ph < 0.66:
        continue
    if abs(abs(th) - math.pi / 2) < 0.34 and ph < 0.38:   # keep the ears clear
        continue
    p, n = on_head(th, ph, 0.006)
    r = random.uniform(0.045, 0.058)
    blob_into(bm, p - n * 0.02, (r, r, r * 0.7), 0, 2)
for k in range(9):                                # quiff, swept to his right
    th = -0.75 + k * 0.17
    p, n = on_head(th, 0.72 + 0.05 * math.sin(k * 0.7), 0.02 + 0.012 * math.sin(k / 8 * math.pi))
    blob_into(bm, p, (0.05, 0.04, 0.032), 0, 2)
for side in (-1, 1):                              # short sideburns
    p, n = on_head(side * 1.36, 0.28, 0.0)
    blob_into(bm, p, (0.014, 0.022, 0.05), 0, 1)
part("DC.hair", "head", bm, [MAT["hair"]], outline=-0.003, sub=1)

# polo collar, placket and buttons on the chest bone
new_mat("collar", PAL["collar"])
new_mat("button", PAL["button"])
bm = bmesh.new()
for sx in (-1, 1):                                # pointed collar flaps lying on the chest
    tmp = bmesh.new()
    pts = [(sx * 0.012, -0.112, 0.622), (sx * 0.07, -0.1, 0.63), (sx * 0.062, -0.132, 0.585), (sx * 0.02, -0.136, 0.572)]
    vs = [tmp.verts.new(Vector(p_)) for p_ in pts]
    vs2 = [tmp.verts.new(Vector(p_) + Vector((0, 0.012, 0))) for p_ in pts]
    tmp.faces.new(vs); tmp.faces.new(list(reversed(vs2)))
    for i in range(4):
        tmp.faces.new((vs[i], vs[(i + 1) % 4], vs2[(i + 1) % 4], vs2[i]))
    me_ = bpy.data.meshes.new("_t"); tmp.to_mesh(me_); tmp.free()
    bm.from_mesh(me_); bpy.data.meshes.remove(me_)
    box_into(bm, (sx * 0.075, -0.03, 0.622), (0.05, 0.14, 0.02), 0)    # collar band round the neck
box_into(bm, (0.0, 0.05, 0.622), (0.15, 0.03, 0.022), 0)
box_into(bm, (0.0, -0.131, 0.548), (0.032, 0.008, 0.06), 0)            # placket
blob_into(bm, (0.0, -0.137, 0.565), (0.007, 0.004, 0.007), 1)
blob_into(bm, (0.0, -0.137, 0.535), (0.007, 0.004, 0.007), 1)
part("DC.collar", "chest", bm, [MAT["collar"], MAT["button"]], outline=-0.002, sub=1)
# wristwatch (left wrist)
new_mat("watch", PAL["watch"])
new_mat("watch_face", PAL["watch_face"])
fa = RIG.data.bones["forearm.L"]
wrist = fa.tail_local
bm = bmesh.new()
tmp = bmesh.new()
bmesh.ops.create_cone(tmp, cap_ends=False, segments=14, radius1=0.031, radius2=0.031, depth=0.014)
me = bpy.data.meshes.new("_t")
tmp.to_mesh(me)
tmp.free()
bm.from_mesh(me)
bpy.data.meshes.remove(me)
for v in bm.verts:
    v.co = Vector((wrist.x + v.co.x, wrist.y + v.co.y, wrist.z + 0.006 + v.co.z))
blob_into(bm, (wrist.x + 0.031, wrist.y - 0.004, wrist.z + 0.006), (0.007, 0.016, 0.016), 1)
part("DC.watch", "forearm.L", bm, [MAT["watch"], MAT["watch_face"]], outline=-0.002, sub=0)

# ------------------------------------------------------------------ proportions: legs, arms, hands, fingers
LEG_OFF = 0.032          # longer legs (raises everything above the hips)
ARM_K = 0.18             # upper arm and forearm 18 % longer
HAND_K = 1.2             # bigger hands
FING_LEN, FING_FAT = 1.32, 1.1
bpy.context.view_layer.objects.active = RIG
RIG.select_set(True)
RIG.data.pose_position = 'REST'
bpy.ops.object.mode_set(mode='EDIT')
eb = RIG.data.edit_bones
for b in eb:
    b.use_connect = False
OLD = {b.name: (b.head.copy(), b.tail.copy()) for b in eb}
NEW = {}
for b in eb:
    h, tl = OLD[b.name]
    if b.name in ("root",) or b.name.startswith("foot."):
        NEW[b.name] = (h.copy(), tl.copy())
    elif b.name.startswith("leg."):
        NEW[b.name] = (h + Vector((0, 0, LEG_OFF)), tl.copy())
    else:
        NEW[b.name] = (h + Vector((0, 0, LEG_OFF)), tl + Vector((0, 0, LEG_OFF)))
ARMOFF = {}
ARM_BONES = ("upper_arm", "forearm", "hand", "thumb", "finger_index", "finger_middle", "finger_ring", "finger_pinky")
for s in ("L", "R"):
    sx = 1 if s == "L" else -1
    for bn in ARM_BONES:                               # whole arm chain in with the shoulders
        nm = "%s.%s" % (bn, s)
        if nm in NEW:
            h2, t2 = NEW[nm]
            NEW[nm] = (h2 - Vector((sx * SHOULDER_IN, 0, 0)), t2 - Vector((sx * SHOULDER_IN, 0, 0)))
for s in ("L", "R"):
    uh, ut = OLD["upper_arm." + s]
    fh, ft = OLD["forearm." + s]
    off1 = (ut - uh) * ARM_K
    off2 = (ft - fh) * ARM_K
    ARMOFF[s] = (off1, off2, uh.z, ut.z, ft.z)
    u_new = NEW["upper_arm." + s]
    NEW["upper_arm." + s] = (u_new[0], u_new[1] + off1)
    f_new = NEW["forearm." + s]
    NEW["forearm." + s] = (f_new[0] + off1, f_new[1] + off1 + off2)
    hh, ht = OLD["hand." + s]
    nh = NEW["hand." + s][0] + off1 + off2
    NEW["hand." + s] = (nh, nh + (ht - hh) * HAND_K)
    for fn in ("thumb", "finger_index", "finger_middle", "finger_ring", "finger_pinky"):
        nm = "%s.%s" % (fn, s)
        if nm in OLD:
            oh, ot = OLD[nm]
            h2 = nh + (oh - hh) * HAND_K
            NEW[nm] = (h2, h2 + (ot - oh) * FING_LEN)
for b in eb:
    b.head, b.tail = NEW[b.name]
bpy.ops.object.mode_set(mode='OBJECT')
DT = {n: NEW[n][1] - OLD[n][1] for n in NEW}          # bone tail moves = how bone children move

# meshes that must change shape as well as follow their bone
for o in list(COLL.all_objects):
    if not o or o.type != 'MESH' or o.parent != RIG:
        continue
    bn = o.parent_bone if o.parent_type == 'BONE' else ""
    me = o.data
    if bn.startswith("leg."):                          # stretch the trouser legs up to the new hips
        z0 = OLD[bn][1].z
        L0 = OLD[bn][0].z - z0
        k = (L0 + LEG_OFF) / L0
        for v in me.vertices:
            v.co.z = z0 + (v.co.z - z0) * k
    elif bn.startswith("hand."):
        oh = OLD[bn][0]; nh = NEW[bn][0]
        for v in me.vertices:
            v.co = nh + (v.co - oh) * HAND_K - DT[bn]
    elif bn.split(".")[0] in ("thumb", "finger_index", "finger_middle", "finger_ring", "finger_pinky"):
        oh, ot = OLD[bn]; nh = NEW[bn][0]
        d = (ot - oh).normalized()
        for v in me.vertices:
            r = v.co - oh
            along = d * r.dot(d)
            v.co = nh + along * FING_LEN + (r - along) * FING_FAT - DT[bn]
    elif o.name.startswith("DC.arm."):                 # skinned sleeve+forearm: raise and stretch
        s = o.name[-1]
        off1, off2, zs, ze, zw = ARMOFF[s]
        for v in me.vertices:
            z = v.co.z
            if z >= zs:
                add = Vector((0, 0, 0))
            elif z >= ze:
                add = off1 * ((zs - z) / max(1e-6, zs - ze))
            elif z >= zw:
                add = off1 + off2 * ((ze - z) / max(1e-6, ze - zw))
            else:
                add = off1 + off2
            sx = 1 if s == "L" else -1
            v.co = v.co + add + Vector((-sx * SHOULDER_IN, 0, LEG_OFF))
    me.update()

RIG.scale = (1.03, 1.03, 1.03)
RIG.data.pose_position = 'POSE'
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

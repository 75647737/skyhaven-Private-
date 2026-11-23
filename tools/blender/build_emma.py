"""Emma Carter (cartoon), mum of the Carters, the middle-class neighbours (blueprint, later seasons).

    blender -b blender/characters/tori_cartoon_v004.blend --python tools/blender/build_emma.py -- <out.blend>

Built from cartoon Tori v004 so she shares the rig, real fingers, seated eyes, lashes, mouth set and
face sliders. Original look, clearly not Tori:
  * a white European woman: fair skin #f4d2b8, auburn hair #9c4a2a in a soft top bun, green eyes, cream headband
  * teal knee-length dress #2f8f8a (Tori's wrap shape) with a cream belt, cap sleeves
  * gold hoop earrings and a gold-and-pearl bead necklace
  * coral flat shoes (no heels)
Prefix "EC", collection "EmmaCartoon", rig "EC.rig".
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
random.seed(38)

PAL = dict(skin="#f4d2b8", hair="#9c4a2a", dress="#2f8f8a", belt="#efe3c8", shoe="#e07a5f", sole="#b85a42",
           band="#efe3c8", gold="#e0b04a", blush="#e8a08e", nose="#eaa98f", iris="#4f8a5a",
           beads=("#e0b04a", "#f6efe2", "#e0b04a", "#f6efe2"))


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def set_colour(m, hexcol):
    c = lin(hexcol)
    for n in m.node_tree.nodes if m.node_tree else []:
        if n.type == 'VALTORGB':
            els = n.color_ramp.elements
            ks = [0.62, 0.84, 1.0] + [1.0] * max(0, len(els) - 3)
            if len(els) == 2:
                ks = [0.7, 1.0]
            for e, k in zip(els, ks):
                e.color = [v * k for v in c] + [1]
    m.diffuse_color = c + [1]


# ------------------------------------------------------------------ rename Tori -> Emma
for o in bpy.data.objects:
    if o.name.startswith("TC."):
        o.name = "EC." + o.name[3:]
for m in bpy.data.materials:
    for pre in ("AC_", "TC_"):
        if m.name.startswith(pre):
            m.name = "EC_" + m.name[3:]
for a in bpy.data.actions:
    for pre in ("AC_", "TC_"):
        if a.name.startswith(pre):
            a.name = "EC_" + a.name[3:]
for c in bpy.data.collections:
    if c.name == "ToriCartoon":
        c.name = "EmmaCartoon"
for ar in bpy.data.armatures:
    if ar.name.startswith("TC") or ar.name.startswith("AC"):
        ar.name = "EC" + ar.name[2:]
RIG = bpy.data.objects["EC.rig"]
COLL = bpy.data.collections["EmmaCartoon"]
if RIG.animation_data:
    RIG.animation_data.action = None
for pb in RIG.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)
RIG.data.pose_position = 'REST'
bpy.context.view_layer.update()
MAT = {m.name[3:]: m for m in bpy.data.materials if m.name.startswith("EC_")}
OUTL = MAT.get("outline")

# ------------------------------------------------------------------ colours
set_colour(MAT["skin"], PAL["skin"])
set_colour(MAT["hair"], PAL["hair"])
set_colour(MAT["dress"], PAL["dress"])
if "belt" in MAT:
    set_colour(MAT["belt"], PAL["belt"])
for k, col in (("shoe_upper", PAL["shoe"]), ("shoe_sole", PAL["sole"])):
    if k in MAT:
        set_colour(MAT[k], col)
if "blush" in MAT:
    set_colour(MAT["blush"], PAL["blush"])
if "nose" in MAT:
    set_colour(MAT["nose"], PAL["nose"])
if "iris" in MAT:
    set_colour(MAT["iris"], PAL["iris"])

# ------------------------------------------------------------------ a longer midi dress, less flare
dr = bpy.data.objects.get("EC.dress")
if dr:
    for v in dr.data.vertices:
        if v.co.z < 0.42:
            t_ = (0.42 - v.co.z)
            v.co.z = 0.42 - t_ * 1.45
            k_ = 1.0 - 0.18 * min(1.0, t_ / 0.2)
            v.co.x *= k_
            v.co.y *= k_

# ------------------------------------------------------------------ hair: no long hair or fringe
for nm in ("EC.hair_long", "EC.fringe", "EC.heel.L", "EC.heel.R"):
    o = bpy.data.objects.get(nm)
    if o:
        bpy.data.objects.remove(o)


def part(name, bone, bm, mats, outline=-0.004, sub=1):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    # geometry is written in world units (the rig is scaled 0.95); store it in rig space
    bmesh.ops.transform(bm, matrix=RIG.matrix_world.inverted(), verts=bm.verts)
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


def merge_tmp(bm, tmp, mi):
    me = bpy.data.meshes.new("_t")
    tmp.to_mesh(me)
    tmp.free()
    off = len(bm.faces)
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for f in bm.faces[off:]:
        f.material_index = mi
    bpy.data.meshes.remove(me)


def blob_into(bm, c, r, mi=0, subdiv=1):
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1)
    for v in tmp.verts:
        v.co = Vector((c[0] + v.co.x * r[0], c[1] + v.co.y * r[1], c[2] + v.co.z * r[2]))
    merge_tmp(bm, tmp, mi)


def new_mat(name, hexcol):
    m = MAT["skin"].copy()
    m.name = "EC_" + name
    set_colour(m, hexcol)
    MAT[name] = m
    return m


# head ellipsoid (Tori's head bounds)
HC = Vector((0.0, 0.0, 0.784))
HR = Vector((0.143, 0.136, 0.18))


def head_r_at(z):
    k = max(0.0, 1.0 - ((z - HC.z) / HR.z) ** 2)
    return HR.x * math.sqrt(k), HR.y * math.sqrt(k)


# --- auburn hair: smooth, pulled back into a soft top bun, a few loose strands by the ears
bm = bmesh.new()
for i in range(160):
    th = random.uniform(-math.pi, math.pi)
    ph = random.uniform(0.15, 1.45)
    if abs(th) < 1.2 and ph < 0.6:                  # forehead clear
        continue
    if abs(abs(th) - math.pi / 2) < 0.3 and ph < 0.38:
        continue
    x = math.sin(th) * math.cos(ph)
    y = -math.cos(th) * math.cos(ph)
    z = math.sin(ph)
    p = Vector((HC.x + HR.x * x, HC.y + HR.y * y, HC.z + HR.z * z))
    r = random.uniform(0.045, 0.055)
    blob_into(bm, p, (r, r, r * 0.6), 0, 2)
PC = Vector((0.0, 0.035, 0.985))                  # the bun
blob_into(bm, PC, (0.085, 0.08, 0.07), 0, 2)
for k in range(10):
    a_ = k / 10 * math.tau
    blob_into(bm, PC + Vector((math.cos(a_) * 0.05, math.sin(a_) * 0.05, 0.01 * math.sin(3 * a_))),
              (0.045, 0.04, 0.04), 0, 2)
for side in (-1, 1):                              # a soft loose wisp in front of each ear
    blob_into(bm, (side * 0.133, -0.05, 0.775), (0.011, 0.016, 0.055), 0, 2)
part("EC.puff", "head", bm, [MAT["hair"]], outline=-0.003, sub=1)

# --- coral headband just behind the hairline (lower at the front, higher at the back)
new_mat("band", PAL["band"])
bm = bmesh.new()
N = 48
loops = []
for k in range(N):
    a = k / N * math.tau
    zc = 0.93 - 0.03 * (-math.sin(a))              # sin(a) < 0 at the front (-Y)
    rx, ry = head_r_at(zc)
    ring = []
    for dz, grow in ((-0.013, 0.008), (0.013, 0.008), (0.013, 0.0), (-0.013, 0.0)):
        rx2, ry2 = head_r_at(zc + dz)
        ring.append(bm.verts.new(((rx2 + grow) * math.cos(a), (ry2 + grow) * math.sin(a), zc + dz)))
    loops.append(ring)
for k in range(N):
    a_, b_ = loops[k], loops[(k + 1) % N]
    for j in range(4):
        bm.faces.new((a_[j], a_[(j + 1) % 4], b_[(j + 1) % 4], b_[j]))
part("EC.headband", "head", bm, [MAT["band"]], outline=-0.002, sub=1)

# --- gold hoop earrings
new_mat("gold", PAL["gold"])
for side, sx in (("L", 1), ("R", -1)):
    bm = bmesh.new()
    tmp = bmesh.new()
    bmesh.ops.create_cone(tmp, cap_ends=False, segments=20, radius1=0.022, radius2=0.022, depth=0.004)
    bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    bmesh.ops.translate(tmp, vec=Vector((sx * 0.152, 0.005, 0.695)), verts=tmp.verts)
    merge_tmp(bm, tmp, 0)
    part("EC.earring." + side, "head", bm, [MAT["gold"]], outline=-0.0012, sub=1)

# --- beaded necklace round the base of the neck (on the chest bone)
bead_mats = []
for i, col in enumerate(PAL["beads"]):
    bead_mats.append(new_mat("bead%d" % i, col))
bm = bmesh.new()
nb = 27
for k in range(nb):
    a = (k - (nb - 1) / 2) / (nb - 1) * math.radians(220)      # 0 = front
    x = 0.074 * math.sin(a)
    y = -0.098 * math.cos(a) - 0.006
    z = 0.575 - 0.045 * max(0.0, math.cos(a)) ** 2
    blob_into(bm, (x, y - 0.012 * max(0.0, math.cos(a)), z), (0.009, 0.009, 0.009), k % len(bead_mats))
part("EC.necklace", "chest", bm, bead_mats, outline=-0.001, sub=0)

RIG.data.pose_position = 'POSE'
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)

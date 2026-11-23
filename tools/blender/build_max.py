"""Build baby Max Sterling (cartoon, ~1 year) from cartoon Ace.

    blender -b blender/characters/ace_cartoon_v002.blend \
        --python tools/blender/add_fingers.py ...  (not needed, this script calls it)
    blender -b blender/characters/ace_cartoon_v002.blend --python tools/blender/build_max.py -- <out.blend> [preview_dir]

Keeps Ace's head, face parts, mouth set, face sliders and rig, and rebuilds a baby
body: round babygrow (#a7c7e7) with footies, chubby sleeves, short chubby
fingers, messy dark tufts (#3b2416), blush, and a small aeroplane patch.
Everything is bone-parented (rigid), like the other cartoon characters.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else None
PREVIEW = argv[1] if len(argv) > 1 else None
HERE = os.path.dirname(os.path.abspath(__file__))

RIG_SCALE = 0.72     # whole baby; head stays Ace-sized in rig units, so it reads big
DZ = -0.155          # head and face move down by this (rig units)

PAL = dict(skin="#dba67c", grow="#a7c7e7", hair="#3b2416", trim="#f6f1e6",
           patch="#3d4a63", blush="#e8968a")
ACE_SKIN, ACE_SWEATER, ACE_HAIR = "#c68a5e", "#5b7a99", "#2a1a12"


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def recolor(src, name, new_hex, ref_hex):
    m = src.copy()
    m.name = name
    new, ref = lin(new_hex), lin(ref_hex)
    k = [n / max(r, 1e-4) for n, r in zip(new, ref)]
    for n in m.node_tree.nodes:
        if n.type == 'VALTORGB':
            for e in n.color_ramp.elements:
                e.color = [min(1.0, e.color[i] * k[i]) for i in range(3)] + [1]
    m.diffuse_color = new + [1]
    return m


# ------------------------------------------------------------------ rename
def rename_all():
    for o in bpy.data.objects:
        if o.name.startswith("AC."):
            o.name = "MX." + o.name[3:]
        elif o.name.startswith("AC_"):
            o.name = "MX_" + o.name[3:]
    for m in bpy.data.materials:
        if m.name.startswith("AC_"):
            m.name = "MX_" + m.name[3:]
    for a in bpy.data.actions:
        if a.name.startswith("AC_"):
            a.name = "MX_" + a.name[3:]
    for c in bpy.data.collections:
        if c.name == "AceCartoon":
            c.name = "MaxCartoon"
    bpy.data.objects["MX.rig"].data.name = "MX.rig"


RIG = None
COLL = None
OUTLINE = None


def link(ob):
    COLL.objects.link(ob)
    return ob


def finish(ob, mat, bone, outline=-0.006, sub=2, smooth=True):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    if outline:
        ob.data.materials.append(OUTLINE)
    if ob.type == 'MESH':
        for p in ob.data.polygons:
            p.use_smooth = smooth
            p.material_index = 0
        if sub:
            s = ob.modifiers.new("Smooth", 'SUBSURF')
            s.levels = 1
            s.render_levels = sub
    if outline:
        so = ob.modifiers.new("Outline", 'SOLIDIFY')
        so.thickness = outline
        so.offset = 1
        so.use_flip_normals = True
        so.material_offset = 1
        so.use_rim = False
    ob.parent = RIG
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = RIG.matrix_world.copy()   # mesh data is in rig space
    return ob


def new_mesh(name):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new(name)
    return link(bpy.data.objects.new(name, me))


def ellipsoid(name, center, size, segs=(24, 14), shape=None):
    ob = new_mesh(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=1)
    for v in bm.verts:
        co = v.co.copy()
        if shape:
            co = shape(co)
        v.co = Vector((center[0] + co.x * size[0], center[1] + co.y * size[1], center[2] + co.z * size[2]))
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def capsule(name, p0, p1, r0, r1=None):
    r1 = r0 if r1 is None else r1
    p0, p1 = Vector(p0), Vector(p1)
    ob = new_mesh(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=1)
    L = (p1 - p0).length
    for v in bm.verts:
        t = 1.0 if v.co.z > 0 else 0.0
        r = r0 + (r1 - r0) * t
        v.co = Vector((v.co.x * r, v.co.y * r, v.co.z * r + t * L))
    rot = Vector((0, 0, 1)).rotation_difference((p1 - p0).normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(p0) @ rot, verts=bm.verts)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def cone(name, base, direction, r, length):
    ob = new_mesh(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=0.0, depth=length)
    for v in bm.verts:
        v.co.z += length / 2
    rot = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(base)) @ rot, verts=bm.verts)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def lathe(name, p0, p1, radii, segs=20, rings=None):
    """Round tube from p0 to p1 with a radius profile (list, evenly spaced), capped by half-spheres."""
    p0, p1 = Vector(p0), Vector(p1)
    ax = p1 - p0
    L = ax.length
    ob = new_mesh(name)
    bm = bmesh.new()
    n = len(radii)
    rings = rings or max(8, n * 3)
    def rad(t):
        x = t * (n - 1)
        i = min(int(x), n - 2)
        u = x - i
        u = u * u * (3 - 2 * u)
        return radii[i] * (1 - u) + radii[i + 1] * u
    rows = []
    cap = 5
    for j in range(cap, 0, -1):                       # bottom cap (at p0)
        a = math.pi / 2 * j / cap
        rows.append((-radii[0] * math.sin(a), radii[0] * math.cos(a)))
    for j in range(rings + 1):
        t = j / rings
        rows.append((t * L, rad(t)))
    for j in range(1, cap + 1):                       # top cap (at p1)
        a = math.pi / 2 * j / cap
        rows.append((L + radii[-1] * math.sin(a), radii[-1] * math.cos(a)))
    verts = []
    for z, r in rows:
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        verts.append(ring)
    for a_, b_ in zip(verts, verts[1:]):
        for k in range(segs):
            bm.faces.new((a_[k], a_[(k + 1) % segs], b_[(k + 1) % segs], b_[k]))
    bm.faces.new(list(reversed(verts[0])))
    bm.faces.new(verts[-1])
    rot = Vector((0, 0, 1)).rotation_difference(ax.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(p0) @ rot, verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def remap(ob, fn):
    """Apply fn(rig_space_point) -> point to every vertex / curve point of ob."""
    mw = ob.matrix_world
    inv = mw.inverted()
    rw = RIG.matrix_world
    rinv = rw.inverted()
    f = lambda c: inv @ (rw @ fn(rinv @ (mw @ c)))
    if ob.type == 'MESH':
        for v in ob.data.vertices:
            v.co = f(v.co)
        ob.data.update()
    elif ob.type == 'CURVE':
        for sp in ob.data.splines:
            for pt in sp.bezier_points:
                pt.co, pt.handle_left, pt.handle_right = f(pt.co), f(pt.handle_left), f(pt.handle_right)


def scale_about(c, k):
    c = Vector(c)
    kk = k if hasattr(k, "__len__") else (k, k, k)
    return lambda p: Vector((c.x + (p.x - c.x) * kk[0], c.y + (p.y - c.y) * kk[1], c.z + (p.z - c.z) * kk[2]))


def centroid(objs):
    pts = []
    for o in objs:
        if o.type == 'MESH':
            pts += [RIG.matrix_world.inverted() @ (o.matrix_world @ v.co) for v in o.data.vertices]
    return sum(pts, Vector()) / max(1, len(pts))


def surface_point(obj, origin, direction):
    """Ray cast in rig space onto obj's base mesh (obj in rest pose)."""
    mw = obj.matrix_world
    inv = mw.inverted()
    o = inv @ (RIG.matrix_world @ Vector(origin))
    d = (inv.to_3x3() @ (RIG.matrix_world.to_3x3() @ Vector(direction))).normalized()
    hit, loc, nor, _ = obj.ray_cast(o, d)
    if not hit:
        return None, None
    w = RIG.matrix_world.inverted() @ (mw @ loc)
    n = (RIG.matrix_world.inverted().to_3x3() @ (mw.to_3x3() @ nor)).normalized()
    return w, n


# ------------------------------------------------------------------ build
def build():
    global RIG, COLL, OUTLINE
    rename_all()
    RIG = bpy.data.objects["MX.rig"]
    COLL = bpy.data.collections["MaxCartoon"]
    OUTLINE = bpy.data.materials["MX_outline"]
    if RIG.animation_data:
        RIG.animation_data.action = None
    for pb in RIG.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    RIG.data.pose_position = 'REST'

    # materials
    M = {}
    M["skin"] = bpy.data.materials["MX_skin"]
    src_skin = M["skin"].copy()
    M["skin"] = recolor(src_skin, "MX_skin_baby", PAL["skin"], ACE_SKIN)
    M["nose"] = recolor(bpy.data.materials["MX_nose"], "MX_nose_baby", PAL["skin"], ACE_SKIN)
    M["grow"] = recolor(bpy.data.materials["MX_sweater"], "MX_babygrow", PAL["grow"], ACE_SWEATER)
    M["hair"] = recolor(bpy.data.materials["MX_hair"], "MX_hair_baby", PAL["hair"], ACE_HAIR)
    M["trim"] = recolor(bpy.data.materials["MX_sweater"], "MX_trim", PAL["trim"], ACE_SWEATER)
    M["patch"] = recolor(bpy.data.materials["MX_sweater"], "MX_patch", PAL["patch"], ACE_SWEATER)
    M["blush"] = recolor(bpy.data.materials["MX_skin"], "MX_blush", PAL["blush"], ACE_SKIN)
    bpy.data.materials.remove(src_skin)
    for o in bpy.data.objects:
        if o.type not in ('MESH', 'CURVE'):
            continue
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            if m.name == "MX_skin":
                o.data.materials[i] = M["skin"]
            elif m.name == "MX_nose":
                o.data.materials[i] = M["nose"]
            elif m.name == "MX_hair":
                o.data.materials[i] = M["hair"]

    # remove adult body parts
    for n in ["arm.L", "arm.R", "cable.L", "cable.R", "collar", "cuff.L", "cuff.R", "hem",
              "hips", "leg.L", "leg.R", "shoe.L", "shoe.R", "sweater", "fringe"]:
        o = bpy.data.objects.get("MX." + n)
        if o:
            bpy.data.objects.remove(o)

    # ---------------- bones
    bpy.context.view_layer.objects.active = RIG
    RIG.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = RIG.data.edit_bones
    head_tree = [b for b in eb if b.name == "head" or (b.parent and any(p.name == "head" for p in b.parent_recursive + [b.parent]))]
    for b in head_tree:
        b.head.z += DZ
        b.tail.z += DZ
    def setb(name, h, t):
        b = eb[name]
        b.head, b.tail = Vector(h), Vector(t)
    setb("hips", (0, 0, 0.20), (0, 0, 0.27))
    setb("chest", (0, 0, 0.27), (0, 0, 0.44))
    for s, sx in (("L", 1), ("R", -1)):
        setb("upper_arm." + s, (0.138 * sx, 0, 0.405), (0.192 * sx, 0.004, 0.338))
        setb("forearm." + s, (0.192 * sx, 0.004, 0.338), (0.224 * sx, -0.010, 0.272))
        setb("hand." + s, (0.224 * sx, -0.010, 0.272), (0.246 * sx, -0.018, 0.196))
        setb("leg." + s, (0.072 * sx, 0, 0.185), (0.094 * sx, -0.004, 0.058))
        setb("foot." + s, (0.094 * sx, -0.004, 0.058), (0.104 * sx, -0.092, 0.030))
    # keep bone rolls consistent with Ace (arms rolled the same way)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    # ---------------- body
    def belly(co):
        # baby build: narrow sloping shoulders, round tummy pushed forward,
        # no real waist, wide nappy bum at the bottom and back
        z = co.z
        prof = [(-1.0, 0.70), (-0.75, 1.02), (-0.45, 1.06), (-0.05, 1.0), (0.35, 0.93), (0.7, 0.78), (1.0, 0.45)]
        for (z0, w0), (z1, w1) in zip(prof, prof[1:]):
            if z0 <= z <= z1:
                u = (z - z0) / (z1 - z0)
                u = u * u * (3 - 2 * u)
                w = w0 + (w1 - w0) * u
                break
        y = co.y
        if y < 0:          # tummy
            y *= 1.0 + 0.10 * math.exp(-((z + 0.05) / 0.45) ** 2)
        else:              # nappy bum
            y *= 0.90 + 0.16 * math.exp(-((z + 0.55) / 0.3) ** 2)
        return Vector((co.x * w, y * w, z))
    torso = ellipsoid("MX.babygrow", (0, -0.004, 0.300), (0.160, 0.140, 0.190), segs=(32, 20), shape=belly)
    finish(torso, M["grow"], "chest")
    # round collar
    col = new_mesh("MX.collar")
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=24, radius=0.058)
    bmesh.ops.translate(bm, vec=Vector((0, -0.004, 0.468)), verts=bm.verts)
    bm.to_mesh(col.data)
    bm.free()
    cu = bpy.data.curves.new("MX.collar", 'CURVE')
    bpy.data.objects.remove(col)
    cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(3)
    for i, a in enumerate([0, 90, 180, 270]):
        r = math.radians(a)
        p = sp.bezier_points[i]
        p.co = (0.062 * math.cos(r), -0.004 + 0.058 * math.sin(r), 0.466)
        p.handle_left_type = p.handle_right_type = 'AUTO'
    sp.use_cyclic_u = True
    cu.bevel_depth = 0.011
    cu.bevel_resolution = 3
    colo = link(bpy.data.objects.new("MX.collar", cu))
    finish(colo, M["trim"], "chest", outline=0)

    # shoulders, chubby tapered sleeves with white cuffs, chubby legs, footies
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        ub = RIG.data.bones["upper_arm." + s_]
        fb = RIG.data.bones["forearm." + s_]
        finish(ellipsoid("MX.shoulder." + s_, ub.head_local + Vector((-0.006 * sx, 0, -0.004)), (0.054, 0.052, 0.050)), M["grow"], "upper_arm." + s_)
        finish(lathe("MX.sleeve_upper." + s_, ub.head_local, ub.tail_local, [0.047, 0.049, 0.044, 0.041]), M["grow"], "upper_arm." + s_)
        cuff_at = fb.head_local.lerp(fb.tail_local, 0.80)
        finish(lathe("MX.sleeve_fore." + s_, fb.head_local, cuff_at, [0.042, 0.043, 0.040, 0.038]), M["grow"], "forearm." + s_)
        finish(lathe("MX.cuff." + s_, cuff_at, fb.tail_local, [0.038, 0.037]), M["trim"], "forearm." + s_, outline=-0.004)
        lb = RIG.data.bones["leg." + s_]
        fo = RIG.data.bones["foot." + s_]
        # thigh roll, little knee crease, round calf
        finish(lathe("MX.leg." + s_, lb.head_local, lb.tail_local + Vector((0, 0, 0.008)),
                     [0.070, 0.074, 0.071, 0.061, 0.064, 0.058, 0.054]), M["grow"], "leg." + s_)
        c = fo.head_local
        foot = ellipsoid("MX.footie." + s_, (c.x + 0.006 * sx, c.y - 0.036, 0.034), (0.056, 0.080, 0.038),
                         shape=lambda co: Vector((co.x * (1.12 if co.y < 0 else 0.95), co.y, co.z * (1.15 if co.z > 0 else 0.8))))
        # toes turned a little out, like a baby's stance
        remap(foot, lambda p, c=c, sx=sx: (Matrix.Translation(c) @ Matrix.Rotation(math.radians(10 * sx), 4, 'Z') @ Matrix.Translation(-c)) @ p)
        finish(foot, M["grow"], "foot." + s_)
        sole = ellipsoid("MX.sole." + s_, (c.x + 0.006 * sx, c.y - 0.040, 0.004), (0.046, 0.068, 0.006), segs=(16, 8))
        remap(sole, lambda p, c=c, sx=sx: (Matrix.Translation(c) @ Matrix.Rotation(math.radians(10 * sx), 4, 'Z') @ Matrix.Translation(-c)) @ p)
        finish(sole, M["trim"], "foot." + s_, outline=0)

    # ---------------- baby face
    head = bpy.data.objects["MX.head"]
    hb = RIG.data.bones["head"]
    hz0 = hb.head_local.z                 # chin level is about hz0 + 0.04
    eye_z = hz0 + 0.215
    def cheeks(p):
        # chubby cheeks and a softer jaw: widen and round out below the eyes
        t = max(0.0, min(1.0, (eye_z - p.z) / 0.16))
        bump = math.sin(math.pi * min(1.0, t * 1.15)) if t > 0 else 0.0
        side = min(1.0, abs(p.x) / 0.09)
        k = 1.0 + 0.085 * bump * side
        y = p.y * (1.0 + 0.05 * bump * side) if p.y < 0 else p.y
        return Vector((p.x * k, y, p.z + 0.006 * bump))
    remap(head, cheeks)
    # bigger baby eyes
    for s_ in "LR":
        parts = [bpy.data.objects.get("MX.%s.%s" % (n, s_)) for n in ("eye", "iris", "pupil", "shine")]
        parts = [o for o in parts if o]
        c = centroid(parts[:1])
        for o in parts:
            remap(o, scale_about(c, 1.14))
    # softer, lighter, shorter brows a little higher
    M["brow"] = recolor(bpy.data.materials["MX_hair"], "MX_brow_baby", "#7a5a40", ACE_HAIR)
    for s_ in "LR":
        br = bpy.data.objects.get("MX.brow." + s_)
        if br and br.type == 'CURVE':
            br.data.bevel_depth *= 0.5
            br.data.materials[0] = M["brow"]
            pts = [RIG.matrix_world.inverted() @ (br.matrix_world @ p.co) for p in br.data.splines[0].bezier_points]
            c = sum(pts, Vector()) / len(pts)
            remap(br, lambda p, c=c: scale_about(c, (0.78, 1.0, 0.6))(p) + Vector((0, 0, 0.008)))
    # button nose, smaller mouth, smaller ears
    nose = bpy.data.objects["MX.nose"]
    remap(nose, scale_about(centroid([nose]), 0.62))
    mb = RIG.data.bones["mouth"].head_local
    for o in bpy.data.objects:
        if o.name.startswith("MX.mouth."):
            remap(o, scale_about(mb, (0.8, 0.9, 0.8)))
    for s_ in "LR":
        ear = bpy.data.objects.get("MX.ear." + s_)
        if ear:
            remap(ear, scale_about(centroid([ear]), 0.85))
    top = hb.head_local + Vector((0, 0, 0.40))
    # messy tufts: flame-shaped flicks rooted in the hair, cast onto the skull
    tufts = [((0.000, -0.070), (0.10, -0.80, 0.60), 0.046, 0.115),
             ((-0.045, -0.050), (-0.55, -0.60, 0.60), 0.040, 0.100),
             ((0.050, -0.045), (0.60, -0.55, 0.60), 0.040, 0.105),
             ((0.020, -0.010), (0.25, -0.30, 0.95), 0.044, 0.110),
             ((-0.030, 0.010), (-0.35, -0.10, 0.95), 0.040, 0.095),
             ((0.000, 0.050), (0.05, 0.45, 0.90), 0.042, 0.090),
             ((-0.080, 0.030), (-0.85, 0.10, 0.55), 0.034, 0.080),
             ((0.085, 0.025), (0.85, 0.15, 0.55), 0.034, 0.082),
             ((0.030, -0.100), (0.35, -0.95, 0.10), 0.030, 0.075)]
    for i, ((x, y), d, r, L) in enumerate(tufts):
        p, n = surface_point(head, (x, y, top.z + 0.3), (0, 0, -1))
        if p is None:
            continue
        # root sits inside the hair shell, which is ~2 cm above the skull
        finish(cone("MX.tuft%d" % i, p + n * 0.012, d, r, L), M["hair"], "head", outline=-0.004, sub=1)
    # blush on the cheeks
    for s, sx in (("L", 1), ("R", -1)):
        p, n = surface_point(head, (0.095 * sx, -0.5, hb.head_local.z + 0.105), (0, 1, 0))
        if p is None:
            continue
        b = ellipsoid("MX.blush." + s, p + n * 0.001, (0.028, 0.006, 0.019), segs=(16, 8))
        # turn the flat side to the surface normal
        bm = bmesh.new()
        bm.from_mesh(b.data)
        rot = Vector((0, -1, 0)).rotation_difference(n).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation(p) @ rot @ Matrix.Translation(-p), verts=bm.verts)
        bm.to_mesh(b.data)
        bm.free()
        finish(b, M["blush"], "head", outline=0, sub=1)

    # ---------------- star patch on the chest
    p, n = surface_point(torso, (0, -0.6, 0.365), (0, 1, 0))
    if p is not None:
        ob = new_mesh("MX.patch_star")
        bm = bmesh.new()
        R1, R2, T = 0.030, 0.013, 0.004
        top, bot = [], []
        for k in range(10):
            a = math.pi / 2 + k * math.pi / 5
            r = R1 if k % 2 == 0 else R2
            x, z = r * math.cos(a), r * math.sin(a)
            top.append(bm.verts.new((x, -T, z)))
            bot.append(bm.verts.new((x, 0.0, z)))
        bm.faces.new(top)
        bm.faces.new(list(reversed(bot)))
        for k in range(10):
            bm.faces.new((top[k], bot[k], bot[(k + 1) % 10], top[(k + 1) % 10]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        rot = Vector((0, -1, 0)).rotation_difference(n).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation(p + n * 0.002) @ rot, verts=bm.verts)
        bm.to_mesh(ob.data)
        bm.free()
        sw = ob.modifiers.new("OnTummy", 'SHRINKWRAP')
        sw.target = torso
        sw.wrap_method = 'NEAREST_SURFACEPOINT'
        sw.wrap_mode = 'OUTSIDE_SURFACE'
        sw.offset = 0.003
        finish(ob, M["patch"], "chest", outline=0, sub=0, smooth=False)

    # ---------------- babygrow snaps down the front
    for i, z in enumerate((0.225, 0.180, 0.135)):
        p, n = surface_point(torso, (0, -0.6, z), (0, 1, 0))
        if p is None:
            continue
        snap = ellipsoid("MX.snap%d" % i, p + n * 0.001, (0.010, 0.0045, 0.010), segs=(16, 8))
        finish(snap, M["trim"], "chest", outline=-0.002, sub=1)

    # ---------------- fingers: short and chubby
    g = {"__name__": "__main__", "PREFIX": "MX", "HAND_SCALE": 1.25, "FINGER_LEN": 0.55,
         "FINGER_FAT": 1.0, "PALM_START": 0.004}
    src = os.path.join(HERE, "add_fingers.py")
    exec(compile(open(src).read(), src, 'exec'), g)
    for o in bpy.data.objects:
        if o.name.startswith(("MX.finger_", "MX.hand.", "MX.thumb.")):
            for i, m in enumerate(o.data.materials):
                if m and m.name == "MX_skin":
                    o.data.materials[i] = M["skin"]

    # ---------------- seat the (bigger) eyes and brows into the face
    g2 = {"__name__": "__main__", "PREFIX": "MX"}
    src2 = os.path.join(HERE, "fix_eyes.py")
    exec(compile(open(src2).read(), src2, 'exec'), g2)

    # ---------------- rig scale, camera, lights
    RIG.scale = (RIG_SCALE,) * 3
    # softer, more open baby expression by default (scenes can still key these)
    RIG["brows"] = 0.25
    RIG["brow_tilt"] = 0.2
    RIG.data.pose_position = 'POSE'
    cam = bpy.data.objects.get("MX_cam")
    if cam:
        tgt = Vector((0, 0, 0.31))
        cam.location = (0.42, -1.55, 0.42)
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = 55
    for n in ("MX_key", "MX_fill"):
        L = bpy.data.objects.get(n)
        if L:
            L.location = Vector(L.location) * 0.7
    if bpy.data.materials.get("MX_skin") and bpy.data.materials["MX_skin"].users == 0:
        bpy.data.materials.remove(bpy.data.materials["MX_skin"])
    if bpy.data.actions.get("MX_wave_talk"):
        RIG.animation_data_create()
        RIG.animation_data.action = bpy.data.actions["MX_wave_talk"]
        bpy.data.actions["MX_wave_talk"].use_fake_user = True
        RIG.animation_data.action = None
    bpy.context.scene.frame_set(1)


def previews(d):
    os.makedirs(d, exist_ok=True)
    S = bpy.context.scene
    S.render.resolution_x, S.render.resolution_y = 600, 700
    S.render.resolution_percentage = 100
    S.eevee.taa_render_samples = 16
    cam = S.camera
    tgt = Vector((0, 0, 0.31))
    for name, ang in (("front", 0), ("threeq", 35), ("side", 90)):
        a = math.radians(ang)
        cam.location = tgt + Vector((1.6 * math.sin(a), -1.6 * math.cos(a), 0.12))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        S.render.filepath = os.path.join(d, "max_%s.png" % name)
        bpy.ops.render.render(write_still=True)
    cam.location = (0.42, -1.55, 0.42)
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()


build()
if PREVIEW:
    previews(PREVIEW)
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_MAX_DONE")

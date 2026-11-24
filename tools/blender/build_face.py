"""Face that reads in front, three-quarter and side view, for any of the cartoon cast.

    blender -b <char.blend> --python tools/blender/build_face.py -- <PREFIX> <out.blend>

PREFIX: AC (Ace), TC (Tori), MX (Max), DC (Daniel), EC (Emma).  The same approach as Ace v005
(`build_ace_face.py`, which this generalises), with a style per character (STYLES below):

  head     re-sampled from the character's own head at high resolution (same skull and hairline),
           then given a continuous profile: forehead, brow, a nose sculpted into the head, philtrum,
           upper and lower lip with the mouth line between them, chin and jaw
  nose     bridge, bulb, wings, nostrils that show from the front and a crease round each wing
  ears     outer rim, inner Y fold, a lighter bowl, tragus and lobe; outlined so the folds draw
  attached eyes, irises, pupils, highlights, brows, blush and every mouth piece shrinkwrapped onto a
           camera-invisible twin of the head, so they stay on the face as the head turns, blinks and
           the jaw moves; mouth lines, nostrils and nose creases are projected along the face's
           forward axis so thin lines stay clean
  mouth    head shape keys driven by the `mouth` slider (jaw open, lips round, lips pressed, lower lip
           tucked, smile, frown)

Every head is mapped onto Ace's head proportions ("A space": centre (0, 0, 0.825), half size
0.15 x 0.143 x 0.19), sculpted there with the character's style, and mapped back, so one set of
numbers places the features on heads of every size (Max is a baby at rig scale 0.72).
"""
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
PFX, OUT = argv[0], argv[1]
P = PFX + "."

# ------------------------------------------------------------------ styles (A space, metres)
#  bridge: (amount at root, amount added by the tip, power, width at root, width at tip, root z, length)
#  bulb:   (z, amount, width, height)          wings: (x, z, amount, size)       under: underside tuck
#  lips:   (philtrum, upper, line depth, lower, groove)                          chin: (amount, width)
#  jaw:    how far the lower face comes forward of the old egg (1 = Ace)
#  crease: (wing centre x, z, radius)          nostril: (x, z, width, height)    ear: size
STYLES = {
    "AC": dict(bridge=(0.003, 0.016, 1.5, 0.0110, 0.0185, 0.799, 0.060), bulb=(0.7240, 0.0390, 0.0215, 0.0195),
               wings=(0.0200, 0.7155, 0.0215, 0.0103), under=0.66, lips=(0.0055, 0.0100, 0.0050, 0.0095, 0.0045),
               chin=(0.0090, 0.0270), jaw=1.0, brow=0.0030, cheek=(0.0045, 0.022),
               crease=(0.0200, 0.7155, 0.0123), nostril=(0.0105, 0.7080, 0.0052, 0.0029), ear=1.30),
    # Tori: small, soft, slightly upturned nose; full lips; a gentle chin
    "TC": dict(bridge=(0.002, 0.010, 1.6, 0.0085, 0.0130, 0.796, 0.058), bulb=(0.7285, 0.0270, 0.0150, 0.0140),
               wings=(0.0140, 0.7205, 0.0125, 0.0078), under=0.52, lips=(0.0050, 0.0110, 0.0055, 0.0115, 0.0045),
               chin=(0.0060, 0.0240), jaw=0.88, brow=0.0012, cheek=(0.0050, 0.024),
               crease=(0.0140, 0.7205, 0.0088), nostril=(0.0078, 0.7135, 0.0040, 0.0022), ear=1.12),
    # Emma: straighter, longer nose with a small rounded tip; full lips; neat chin
    "EC": dict(bridge=(0.003, 0.019, 1.2, 0.0085, 0.0135, 0.799, 0.064), bulb=(0.7250, 0.0320, 0.0140, 0.0140),
               wings=(0.0148, 0.7170, 0.0125, 0.0078), under=0.60, lips=(0.0050, 0.0095, 0.0055, 0.0110, 0.0045),
               chin=(0.0075, 0.0240), jaw=0.92, brow=0.0015, cheek=(0.0045, 0.022),
               crease=(0.0148, 0.7170, 0.0090), nostril=(0.0082, 0.7105, 0.0040, 0.0022), ear=1.15),
    # Daniel: long straight nose, narrower bulb, strong chin and jaw; still neat ears
    "DC": dict(bridge=(0.005, 0.024, 1.1, 0.0095, 0.0150, 0.801, 0.068), bulb=(0.7215, 0.0360, 0.0165, 0.0150),
               wings=(0.0165, 0.7140, 0.0150, 0.0085), under=0.64, lips=(0.0050, 0.0080, 0.0045, 0.0085, 0.0045),
               chin=(0.0130, 0.0340), jaw=1.12, brow=0.0045, cheek=(0.0035, 0.022),
               crease=(0.0165, 0.7140, 0.0102), nostril=(0.0092, 0.7075, 0.0045, 0.0024), ear=1.08),
    # Max: a baby button nose, chubby cheeks, small lips, a soft chin that sits back
    "MX": dict(bridge=(0.000, 0.006, 2.0, 0.0080, 0.0110, 0.790, 0.058), bulb=(0.7300, 0.0200, 0.0150, 0.0130),
               wings=(0.0115, 0.7230, 0.0085, 0.0070), under=0.70, lips=(0.0035, 0.0065, 0.0040, 0.0075, 0.0035),
               chin=(0.0040, 0.0260), jaw=0.62, brow=0.0, cheek=(0.0095, 0.030),
               crease=(0.0115, 0.7230, 0.0070), nostril=(0.0065, 0.7175, 0.0032, 0.0018), ear=1.20),
}
ST = STYLES[PFX]

rig = bpy.data.objects[P + "rig"]
if rig.animation_data:
    rig.animation_data.action = None
rig.data.pose_position = 'REST'
bpy.context.view_layer.update()
head = bpy.data.objects[P + "head"]


def g(u, s):
    return math.exp(-0.5 * (u / s) ** 2)


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def Wm(o):
    """World matrix from the parent chain: hidden objects (the mouth shapes switched off by drivers)
    are not evaluated, so their stored matrix_world can be stale."""
    if o.parent and o.parent_type == 'BONE':
        pb = rig.pose.bones[o.parent_bone]
        Pm = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    else:
        Pm = o.parent.matrix_world if o.parent else Matrix()
    return Pm @ o.matrix_parent_inverse @ o.matrix_basis, Pm


def set_world(o, W):
    _, Pm = Wm(o)
    o.matrix_basis = (Pm @ o.matrix_parent_inverse).inverted() @ W


# ------------------------------------------------------------------ sample the old head, map to A space
sol = [m for m in head.modifiers if m.type == 'SOLIDIFY']
for m in sol:
    m.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
ev = head.evaluated_get(dg)
me0 = ev.to_mesh()
mw = head.matrix_world.copy()
wpts = [mw @ v.co for v in me0.vertices]
wpolys = [p.vertices[:] for p in me0.polygons]
ev.to_mesh_clear()
for m in sol:
    m.show_viewport = True
lo = Vector([min(p[i] for p in wpts) for i in range(3)])
hi = Vector([max(p[i] for p in wpts) for i in range(3)])
CC = (lo + hi) / 2
HC = (hi - lo) / 2
CA = Vector((0.0, 0.0, 0.825))
HA = Vector((0.15, 0.143, 0.19))
SC = Vector((HA.x / HC.x, HA.y / HC.y, HA.z / HC.z))
K = HC.z / HA.z                                   # world metres per A-space metre (for offsets)


def toA(p):
    d = p - CC
    return CA + Vector((d.x * SC.x, d.y * SC.y, d.z * SC.z))


def fromA(q):
    d = q - CA
    return CC + Vector((d.x / SC.x, d.y / SC.y, d.z / SC.z))


def vecW(d):
    return Vector((d.x / SC.x, d.y / SC.y, d.z / SC.z))


bvh = BVHTree.FromPolygons([toA(p) for p in wpts], wpolys)


def front_y(z, x=0.0):
    hit = bvh.ray_cast(Vector((x, 0.0, z)), Vector((0, -1, 0)))
    return hit[0].y if hit[0] else None


PROF = [(0.790, None), (0.750, -0.1435), (0.720, -0.1400), (0.700, -0.1345), (0.680, -0.1280),
        (0.660, -0.1205), (0.645, -0.1120), (0.637, -0.1000), (0.630, -0.0800)]


def prof(z):
    if z >= PROF[0][0]:
        return None
    for (z0, y0), (z1, y1) in zip(PROF, PROF[1:]):
        if z1 <= z <= z0:
            y0 = front_y(z0) if y0 is None else y0
            return y0 + (y1 - y0) * (z0 - z) / (z0 - z1)
    return PROF[-1][1]


b0, b1, bp, bw0, bw1, bz, bl = ST["bridge"]
NOSE = []
for k in range(14):
    t = k / 13
    NOSE.append((0.0, bz - bl * t, b0 + b1 * t ** bp, bw0 + (bw1 - bw0) * t, 0.0090))
bz_, ba, bsx, bsz = ST["bulb"]
wx, wz, wa, ws = ST["wings"]
NOSE += [(0.0, bz_, ba, bsx, bsz), (wx, wz, wa, ws, ws * 0.92), (-wx, wz, wa, ws, ws * 0.92)]
ph_, up_, line_, low_, grv_ = ST["lips"]
ch_a, ch_w = ST["chin"]
ck_a, ck_s = ST["cheek"]
RELIEF = [
    (0.045, 0.868, ST["brow"], 0.030, 0.010), (-0.045, 0.868, ST["brow"], 0.030, 0.010),
    (0.0, 0.7040, ph_, 0.0120, 0.0060),
    (0.0, 0.6990, up_, 0.0280, 0.0050),
    (0.0, 0.6880, -line_, 0.0340, 0.0026),
    (0.0, 0.6765, low_, 0.0250, 0.0058),
    (0.0, 0.6655, -grv_, 0.0260, 0.0048),
    (0.0, 0.6500, ch_a, ch_w, 0.0110),
    (0.068, 0.722, ck_a, ck_s, ck_s), (-0.068, 0.722, ck_a, ck_s, ck_s),
    (0.062, 0.808, -0.0030, 0.026, 0.024), (-0.062, 0.808, -0.0030, 0.026, 0.024),
]
UNDER = ST["under"]
JAW = ST["jaw"]


def shape_point(p):
    q = p.copy()
    if q.y < 0:
        yt = prof(q.z)
        if yt is not None:
            y0 = front_y(q.z)
            if y0 is not None and y0 < -1e-4:
                ratio = min(1.0, max(0.0, q.y / y0))
                q.y += (yt - y0) * JAW * ratio ** 1.6 * (1.0 - smooth(0.750, 0.790, q.z))
        front = min(1.0, max(0.0, (-q.y - 0.06) / 0.05))
        d = 0.0
        for (x, z, a, sx, sz) in RELIEF:
            d += a * g(q.x - x, sx) * g(q.z - z, sz)
        nose = 0.0
        for (x, z, a, sx, sz) in NOSE:
            nose = max(nose, a * g(q.x - x, sx) * g(q.z - z, sz if q.z >= z else sz * UNDER))
        q.y -= (d + nose) * front
    return q


# ------------------------------------------------------------------ new high-resolution head
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=176, v_segments=128, radius=1.0)
for v in bm.verts:
    d = v.co.normalized()
    hit = bvh.ray_cast(CA, d)
    v.co = hit[0] if hit[0] else CA + Vector((d.x * HA.x, d.y * HA.y, d.z * HA.z))
for v in bm.verts:
    v.co = shape_point(v.co)
shapedA = [v.co.copy() for v in bm.verts]
inv = mw.inverted()
for v in bm.verts:
    v.co = inv @ fromA(v.co)
for f in bm.faces:
    f.smooth = True
newme = bpy.data.meshes.new(P + "head_face")
bm.to_mesh(newme)
bm.free()
for s in head.data.materials:
    newme.materials.append(s)
head.data = newme
for m in head.modifiers:
    if m.type == 'SUBSURF':
        m.levels = m.render_levels = 1

# ------------------------------------------------------------------ mouth shape keys
R3 = mw.to_3x3().inverted()
head.shape_key_add(name="Basis")


def add_key(name, fn):
    kb = head.shape_key_add(name=name, from_mix=False)
    for i, p in enumerate(shapedA):
        d = fn(p)
        if d is not None and d.length > 1e-7:
            kb.data[i].co = kb.data[i].co + R3 @ vecW(d)
    return kb


def frontw(p):
    return min(1.0, max(0.0, (-p.y - 0.04) / 0.05))


def k_jaw(p):
    return Vector((0, 0.003, -0.0095)) * (1 - smooth(0.664, 0.690, p.z)) * frontw(p) * g(p.x, 0.075)


def k_round(p):
    return Vector((-p.x * 0.30, -0.0075, 0)) * g(p.x, 0.030) * g(p.z - 0.688, 0.015) * frontw(p)


def k_press(p):
    return Vector((0, 0.0028, (0.688 - p.z) * 0.35)) * g(p.x, 0.034) * g(p.z - 0.688, 0.011) * frontw(p)


def k_tuck(p):
    return Vector((0, 0.0045, 0.0035)) * g(p.x, 0.024) * g(p.z - 0.677, 0.007) * frontw(p)


def k_smile(p):
    w = sum(g(p.x - s * 0.058, 0.022) * g(p.z - 0.712, 0.020) for s in (-1, 1)) * frontw(p)
    c = sum(g(p.x - s * 0.040, 0.010) * g(p.z - 0.690, 0.008) for s in (-1, 1)) * frontw(p)
    return Vector((0, -0.003, 0.0055)) * w + Vector((0, 0.001, 0.003)) * c


def k_frown(p):
    c = sum(g(p.x - s * 0.040, 0.011) * g(p.z - 0.688, 0.010) for s in (-1, 1)) * frontw(p)
    return Vector((0, 0.0005, -0.004)) * c


KEYS = {"jaw_open": (k_jaw, "1.0*(abs(m-2)<0.5) + 0.45*(abs(m-3)<0.5) + 0.8*(abs(m-4)<0.5) + 0.25*(abs(m-5)<0.5) + 0.1*(abs(m-7)<0.5)"),
        "lips_round": (k_round, "0.65*(abs(m-4)<0.5) + 1.0*(abs(m-5)<0.5)"),
        "lips_press": (k_press, "1.0*(abs(m-6)<0.5)"),
        "lip_tuck": (k_tuck, "1.0*(abs(m-7)<0.5)"),
        "smile": (k_smile, "1.0*(m<0.5) + 0.35*(abs(m-3)<0.5)"),
        "frown": (k_frown, "1.0*(abs(m-8)<0.5)")}
for name, (fn, expr) in KEYS.items():
    kb = add_key(name, fn)
    dr = kb.driver_add("value").driver
    dr.type = 'SCRIPTED'
    var = dr.variables.new()
    var.name = "m"
    var.targets[0].id = rig
    var.targets[0].data_path = '["mouth"]'
    dr.expression = expr

# ------------------------------------------------------------------ camera-invisible twin the features stick to
surf = bpy.data.objects.new(P + "head_surface", newme)
for c in head.users_collection:
    c.objects.link(surf)
surf.parent, surf.parent_type, surf.parent_bone = head.parent, head.parent_type, head.parent_bone
surf.matrix_parent_inverse = head.matrix_parent_inverse.copy()
surf.matrix_basis = head.matrix_basis.copy()
sm = surf.modifiers.new("Smooth", 'SUBSURF')
sm.levels = sm.render_levels = 1
for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
    if hasattr(surf, attr):
        setattr(surf, attr, False)
surf.display_type = 'WIRE'
surf.hide_select = True


def stick(ob, offset, project=False):
    sw = ob.modifiers.new("OnFace", 'SHRINKWRAP')
    sw.target = surf
    sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'ABOVE_SURFACE'
    sw.offset = offset * K
    if project:
        R = Wm(ob)[0].to_3x3().normalized()
        ax = [k for k in range(3) if abs(R.col[k].y) > 0.95]
        if ax:
            sw.wrap_method = 'PROJECT'
            sw.use_project_x, sw.use_project_y, sw.use_project_z = (ax[0] == 0, ax[0] == 1, ax[0] == 2)
            sw.use_negative_direction = sw.use_positive_direction = True
            sw.cull_face = 'OFF'
        else:
            print("STICK: no local axis along Y for", ob.name, "- nearest point used")
    i = len(ob.modifiers) - 1
    to = 0
    for j, m in enumerate(ob.modifiers):
        if m.type == 'SUBSURF':
            to = j + 1
    if i != to:
        ob.modifiers.move(i, to)


def front_half(ob):
    m3 = Wm(ob)[0].to_3x3()
    bmh = bmesh.new()
    bmh.from_mesh(ob.data)
    bmh.normal_update()
    bmesh.ops.delete(bmh, geom=[f for f in bmh.faces if (m3 @ f.normal).y > 0.05], context='FACES')
    bmh.to_mesh(ob.data)
    bmh.free()


for side in ("L", "R"):
    for part in ("eye.", "iris.", "pupil.", "shine."):
        ob = bpy.data.objects[P + part + side]
        if ob.data.users > 1:
            ob.data = ob.data.copy()
        front_half(ob)

# mouth pieces: bring each just in front of the new surface, then lay it on (open shapes a touch smaller)
new_bvh = BVHTree.FromPolygons([mw @ v.co for v in newme.vertices], [p.vertices[:] for p in newme.polygons])
groups = {}                      # pieces of one mouth shape (line, inside, teeth, tongue) move as one
for o in bpy.data.objects:
    if o.name.startswith(P + "mouth.") and o.type in ('MESH', 'CURVE'):
        W, _ = Wm(o)
        if o.type == 'MESH':
            ps = [W @ v.co for v in o.data.vertices]
        else:
            ps = [W @ bp.co for sp in o.data.splines for bp in sp.bezier_points]
            ps += [W @ Vector(pt.co[:3]) for sp in o.data.splines for pt in sp.points]
        if ps:
            groups.setdefault(o.name[len(P) + 6:len(P) + 8], []).append((o, W, ps))
for tag, items in groups.items():
    allp = [q for (_, _, ps) in items for q in ps]
    cz = sum(q.z for q in allp) / len(allp)
    cx = sum(q.x for q in allp) / len(allp)
    hit = new_bvh.ray_cast(Vector((cx, CC.y, cz)), Vector((0, -1, 0)))
    if not hit[0]:
        continue
    T = Matrix.Translation((0, (hit[0].y - 0.004 * K) - min(q.y for q in allp), 0))
    if tag in ("2_", "3_", "4_"):                 # open shapes: a touch smaller and higher
        big = tag == "2_"
        c = Vector((cx, 0.0, cz))
        T = (Matrix.Translation(c + Vector((0, 0, (0.006 if big else 0.003) * K)))
             @ Matrix.Diagonal((0.88 if big else 0.92, 1.0, 0.72 if big else 0.82, 1.0)) @ Matrix.Translation(-c) @ T)
    if tag in ("4_", "5_"):                       # round shapes: the opening sits centred in the ring
        ring = [it for it in items if it[0].type == 'CURVE']
        if ring:
            rp = ring[0][2]
            rc = Vector((sum(q.x for q in rp) / len(rp), 0, sum(q.z for q in rp) / len(rp)))
            for k_, (o, W, ps) in enumerate(items):
                if o.type == 'MESH':
                    pc = Vector((sum(q.x for q in ps) / len(ps), 0, sum(q.z for q in ps) / len(ps)))
                    items[k_] = (o, Matrix.Translation(rc - pc) @ W, ps)
    for (o, W, _) in items:
        set_world(o, T @ W)
bpy.context.view_layer.update()

SKIN = head.data.materials[0]
OUTL = head.data.materials[1]


def darker(src, name, k):
    m = bpy.data.materials.get(name) or src.copy()
    m.name = name
    for n in m.node_tree.nodes:
        if n.type == 'VALTORGB':
            for e in n.color_ramp.elements:
                c = e.color
                e.color = (c[0] * k[0], c[1] * k[1], c[2] * k[2], c[3])
        if n.type in ('EMISSION', 'BSDF_DIFFUSE') and not n.inputs[0].is_linked:
            c = n.inputs[0].default_value
            n.inputs[0].default_value = (c[0] * k[0], c[1] * k[1], c[2] * k[2], c[3])
    return m


SKIN_D = darker(SKIN, PFX + "_skin_fold", (0.62, 0.50, 0.46))
NOSTRIL = darker(SKIN, PFX + "_nostril", (0.34, 0.23, 0.21))
BOWL = darker(SKIN, PFX + "_ear_bowl", (0.86, 0.80, 0.77))

# eye rims (layers on the face sit 1.2-1.4 mm apart, enough depth precision for wide-range
# episode cameras; at 0.7 mm they z-fought)
for side in ("L", "R"):
    eo = bpy.data.objects[P + "eye." + side]
    for m in eo.modifiers:
        if m.type == 'SOLIDIFY':
            m.show_render = m.show_viewport = False
    rme = eo.data.copy()
    rme.name = P + "eye_rim." + side
    cen = sum((v.co for v in rme.vertices), Vector()) / len(rme.vertices)
    for v in rme.vertices:
        v.co = cen + (v.co - cen) * 1.11
    # a ring, not a disc: the rim never lies under the white, so no camera can show it through
    ext = [max(abs(v.co[i] - cen[i]) for v in rme.vertices) or 1.0 for i in range(3)]
    big = sorted(range(3), key=lambda i: -ext[i])[:2]
    bmr = bmesh.new()
    bmr.from_mesh(rme)
    inner = [f for f in bmr.faces
             if sum(((f.calc_center_median()[i] - cen[i]) / ext[i]) ** 2 for i in big) ** 0.5 < 0.84]
    bmesh.ops.delete(bmr, geom=inner, context='FACES')
    bmr.to_mesh(rme)
    bmr.free()
    rme.materials.clear()
    rme.materials.append(OUTL)
    rim = bpy.data.objects.new(P + "eye_rim." + side, rme)
    for c in eo.users_collection:
        c.objects.link(rim)
    rim.parent, rim.parent_type, rim.parent_bone = eo.parent, eo.parent_type, eo.parent_bone
    rim.matrix_parent_inverse = eo.matrix_parent_inverse.copy()
    rim.matrix_basis = eo.matrix_basis.copy()
    ss = rim.modifiers.new("Smooth", 'SUBSURF')
    ss.levels = ss.render_levels = 1
    stick(rim, 0.0002)

for side in ("L", "R"):
    stick(bpy.data.objects[P + "eye." + side], 0.0016)
    stick(bpy.data.objects[P + "iris." + side], 0.0030)
    stick(bpy.data.objects[P + "pupil." + side], 0.0042)
    stick(bpy.data.objects[P + "shine." + side], 0.0054)
    stick(bpy.data.objects[P + "brow." + side], 0.0030)
    bl_ = bpy.data.objects.get(P + "blush." + side)
    if bl_:
        stick(bl_, 0.0008)
for o in list(bpy.data.objects):
    if o.name.startswith(P + "mouth."):
        off = 0.0010 if o.name.endswith("_in") else 0.0020 if ("teeth" in o.name) else 0.0016 if "tongue" in o.name else 0.0024
        stick(o, off, project=True)
nose_old = bpy.data.objects[P + "nose"]
nose_old.hide_render = nose_old.hide_viewport = True


# ------------------------------------------------------------------ ears (built in A space)
def ellipsoid(bm, c, U, V, N, r, mat, seg=14, rings=10):
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=seg, v_segments=rings, radius=1.0)
    M = Matrix(((U.x * r[0], V.x * r[1], N.x * r[2]), (U.y * r[0], V.y * r[1], N.y * r[2]), (U.z * r[0], V.z * r[1], N.z * r[2])))
    vm = {v: bm.verts.new(c + M @ v.co) for v in t.verts}
    for f in t.faces:
        nf = bm.faces.new([vm[v] for v in f.verts])
        nf.material_index = mat
        nf.smooth = True
    t.free()


def tube(bm, pts, rads, N, mat, ring=10):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = (N - t * N.dot(t)).normalized()
        b = t.cross(a)
        rings.append([bm.verts.new(p + (a * math.cos(k / ring * math.tau) + b * math.sin(k / ring * math.tau)) * rads[i])
                      for k in range(ring)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(ring):
            f = bm.faces.new((r0[k], r0[(k + 1) % ring], r1[(k + 1) % ring], r1[k]))
            f.material_index = mat
            f.smooth = True
    for rr, p, flip in ((rings[0], pts[0], True), (rings[-1], pts[-1], False)):
        cv = bm.verts.new(p)
        for k in range(ring):
            vs = (rr[k], rr[(k + 1) % ring], cv)
            f = bm.faces.new(vs[::-1] if flip else vs)
            f.material_index = mat
            f.smooth = True


def build_ear(side):
    s = 1 if side == "L" else -1
    ob = bpy.data.objects[P + "ear." + side]
    pts = [ob.matrix_world @ Vector(cn) for cn in ob.bound_box]
    oc = toA(sum(pts, Vector()) / 8)
    c = Vector((abs(oc.x) - 0.006, oc.y + 0.004, oc.z - 0.001))
    N = Vector((1.0, -0.42, 0.05)).normalized()
    V = Vector((0.0, 0.22, 1.0))
    V = (V - N * V.dot(N)).normalized()
    U = V.cross(N).normalized()
    bm = bmesh.new()

    def at(u, v, w):
        return c + U * u + V * v + N * w
    ru, rv = 0.0235, 0.0400
    ellipsoid(bm, at(0.002, 0.0, 0.004), U, V, N, (ru, rv, 0.0085), 0, seg=20, rings=14)
    ellipsoid(bm, at(0.004, -0.030, 0.006), U, V, N, (0.0115, 0.0125, 0.0065), 0)
    hel, rad = [], []
    for i in range(26):
        t = i / 25
        ph = math.radians(128 - 205 * t)
        hel.append(at(ru * 0.93 * math.cos(ph) + 0.002, rv * 0.94 * math.sin(ph), 0.0118))
        rad.append(0.0030 + 0.0020 * math.sin(math.pi * min(1, t * 1.25)))
    tube(bm, hel, rad, N, 0)
    anti, arad = [], []
    for i in range(16):
        t = i / 15
        ph = math.radians(82 - 140 * t)
        anti.append(at(0.0115 * math.cos(ph) + 0.004, 0.022 * math.sin(ph) + 0.001, 0.0122))
        arad.append(0.0026 + 0.0010 * math.sin(math.pi * t))
    tube(bm, anti, arad, N, 0)
    br = [anti[0].lerp(at(-0.010, 0.026, 0.0118), t / 5) for t in range(6)]
    tube(bm, br, [0.0022 - 0.0006 * t / 5 for t in range(6)], N, 0)
    ellipsoid(bm, at(-0.0035, -0.004, 0.0122), U, V, N, (0.0095, 0.0135, 0.0012), 2)
    ellipsoid(bm, at(-0.0175, -0.008, 0.0080), U, V, N, (0.0045, 0.0055, 0.0038), 0)
    for v in bm.verts:
        v.co = c + (v.co - c) * ST["ear"]
    if s < 0:
        for v in bm.verts:
            v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    im = ob.matrix_world.inverted()
    for v in bm.verts:
        v.co = im @ fromA(v.co)
    me = bpy.data.meshes.new(P + "ear_face." + side)
    bm.to_mesh(me)
    bm.free()
    for m in (SKIN, OUTL, BOWL, OUTL):
        me.materials.append(m)
    ob.data = me
    for m in ob.modifiers:
        if m.type == 'SOLIDIFY':
            m.thickness = -0.0024 * K
            m.material_offset = 1
        if m.type == 'SUBSURF':
            m.levels = m.render_levels = 1


build_ear("L")
build_ear("R")


def head_child(name, me):
    ob = bpy.data.objects.new(name, me)
    for c in head.users_collection:
        c.objects.link(ob)
    ob.parent, ob.parent_type, ob.parent_bone = rig, 'BONE', "head"
    bpy.context.view_layer.update()
    ob.matrix_world = Matrix()
    return ob


# nostrils
nx, nz, nw, nh = ST["nostril"]
bm = bmesh.new()
for s in (-1, 1):
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=12, v_segments=8, radius=1.0)
    vm = {v: bm.verts.new(fromA(Vector((s * nx + v.co.x * nw, -0.22 + v.co.y * 0.002, nz + v.co.z * nh)))) for v in t.verts}
    for f in t.faces:
        bm.faces.new([vm[v] for v in f.verts]).smooth = True
    t.free()
nme = bpy.data.meshes.new(P + "nostrils")
bm.to_mesh(nme)
bm.free()
nme.materials.append(NOSTRIL)
stick(head_child(P + "nostrils", nme), 0.0006, project=True)

# nose creases round each wing
cx_, cz_, cr = ST["crease"]
bm = bmesh.new()
for sd in (-1, 1):
    n = 15
    arc = [fromA(Vector((sd * (cx_ + cr * math.cos(math.radians(100 - 185 * i / (n - 1)))), -0.22,
                         cz_ + cr * 0.92 * math.sin(math.radians(100 - 185 * i / (n - 1)))))) for i in range(n)]
    rads = [(0.0005 + 0.0009 * math.sin(math.pi * i / (n - 1)) ** 0.7) * K * (0.8 + 0.2 * cr / 0.0123) for i in range(n)]
    tube(bm, arc, rads, Vector((0, -1, 0)), 0, ring=8)
fme = bpy.data.meshes.new(P + "nose_fold")
bm.to_mesh(fme)
bm.free()
fme.materials.append(SKIN_D)
stick(head_child(P + "nose_fold", fme), 0.0007, project=True)

# ------------------------------------------------------------------ per-character fixes seen in profile
if PFX == "EC":
    # the loose wisp in front of each ear was a flat oval blob inside EC.puff, which stood out like a
    # disc in three-quarter and side view: remove those two islands, draw each wisp as a thin curl
    puff = bpy.data.objects[P + "puff"]
    pm = puff.matrix_world
    bmp = bmesh.new()
    bmp.from_mesh(puff.data)
    bmp.verts.ensure_lookup_table()
    kill = set()
    for sd in (-1, 1):
        cw = rig.matrix_world @ Vector((sd * 0.133, -0.05, 0.775))
        v0 = min(bmp.verts, key=lambda v: (pm @ v.co - cw).length)
        isl, todo = {v0}, [v0]
        while todo:
            v = todo.pop()
            for e in v.link_edges:
                o_ = e.other_vert(v)
                if o_ not in isl:
                    isl.add(o_)
                    todo.append(o_)
        if len(isl) < 1500:
            kill |= isl
    bmesh.ops.delete(bmp, geom=list(kill), context='VERTS')
    bmp.to_mesh(puff.data)
    bmp.free()
    bm = bmesh.new()
    for sd in (-1, 1):
        n = 14
        pts = []
        for i in range(n):
            t = i / (n - 1)
            pts.append(rig.matrix_world @ Vector((sd * (0.128 + 0.010 * math.sin(math.pi * t) - 0.004 * t),
                                                  -0.040 - 0.016 * math.sin(math.pi * t * 0.8),
                                                  0.805 - 0.090 * t + 0.010 * math.sin(math.pi * t * 2))))
        tube(bm, pts, [(0.0055 - 0.0045 * t ** 1.3) * K / 0.95 for t in [i / (n - 1) for i in range(n)]],
             Vector((sd, 0, 0)), 0, ring=8)
    wme = bpy.data.meshes.new(P + "wisps")
    bm.to_mesh(wme)
    bm.free()
    wme.materials.append(puff.data.materials[0])
    wme.materials.append(OUTL)
    wo = head_child(P + "wisps", wme)
    ws_ = wo.modifiers.new("Smooth", 'SUBSURF')
    ws_.levels = ws_.render_levels = 1
    wl = wo.modifiers.new("Outline", 'SOLIDIFY')
    wl.thickness, wl.offset, wl.use_flip_normals, wl.material_offset = -0.0018, 1.0, True, 1

    for sd, side in ((1, "L"), (-1, "R")):        # hoops hang clear of the jaw from the new lobes
        er = bpy.data.objects.get(P + "earring." + side)
        if er:
            W, _ = Wm(er)
            set_world(er, Matrix.Translation((sd * 0.008 * K, -0.004 * K, 0)) @ W)

if PFX == "DC":
    # the polo collar flaps stood off the chest and floated in front of the neck in profile: lay the
    # collar onto the shirt
    col = bpy.data.objects[P + "collar"]
    cands = [o for o in rig.children_recursive if o.type == 'MESH' and o.parent_bone == "chest" and o is not col
             and not o.hide_render]
    shirt = max(cands, key=lambda o: o.dimensions.x * o.dimensions.y * o.dimensions.z)
    print("DC collar target:", shirt.name)
    sw = col.modifiers.new("OnShirt", 'SHRINKWRAP')
    sw.target = shirt
    sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'OUTSIDE_SURFACE'
    sw.offset = 0.0025
    col.modifiers.move(len(col.modifiers) - 1, 0)

rig.data.pose_position = 'POSE'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False)
print("FACE_DONE", PFX)

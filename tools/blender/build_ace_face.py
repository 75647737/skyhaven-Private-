"""Ace's face rebuilt so it reads in front, three-quarter and true side view (cartoon Ace v005).

    blender -b blender/characters/ace_cartoon_v004.blend --python tools/blender/build_ace_face.py -- <out.blend>

  head     re-sampled from v004's head at high resolution (same skull, same hairline), then given a
           real profile: forehead, soft brow ridge, a nose sculpted into the head (bridge from between
           the eyes to a rounded tip, nostril wings, a turned-under base), philtrum, upper and lower lip
           with the mouth line between them, a chin and a jaw that comes forward of the egg shape
  ears     outer rim (helix) running from above the tragus round to the lobe, an inner Y-shaped fold
           (antihelix), a darker bowl (concha), a tragus and a fleshy lobe; outlined, so the folds draw
  nostrils two small dark openings under the tip (seen from three-quarter and below)
  attached eyes, irises, pupils, highlights, brows and every mouth piece are shrinkwrapped onto the
           face surface (a hidden twin of the head), so they lie on the curve of the face and stay on it
           as the head turns, blinks and the jaw moves
  mouth    the face itself is part of the mouth rig: head shape keys driven by the same `mouth` slider
           (0 smile, 1 rest, 2 A, 3 E, 4 O, 5 U/W, 6 M/B/P, 7 F/V, 8 frown): jaw open, lips round/
           forward, lips pressed, lower lip tucked, cheeks up for the smile, corners down for the frown
The old separate nose blob is hidden (kept in the file).
"""
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
P = "AC."
rig = bpy.data.objects[P + "rig"]
if rig.animation_data:
    rig.animation_data.action = None
rig.data.pose_position = 'REST'
bpy.context.view_layer.update()
head = bpy.data.objects[P + "head"]
C = Vector((0.0, 0.0, 0.825))           # head centre (world, rest pose, rig at origin)


def g(u, s):
    return math.exp(-0.5 * (u / s) ** 2)


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ sample the old head
sol = [m for m in head.modifiers if m.type == 'SOLIDIFY']
for m in sol:
    m.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
ev = head.evaluated_get(dg)
me0 = ev.to_mesh()
mw = head.matrix_world.copy()
bvh = BVHTree.FromPolygons([mw @ v.co for v in me0.vertices], [p.vertices[:] for p in me0.polygons])
ev.to_mesh_clear()
for m in sol:
    m.show_viewport = True


def front_y(z, x=0.0):
    hit = bvh.ray_cast(Vector((x, 0.0, z)), Vector((0, -1, 0)))
    return hit[0].y if hit[0] else None


# target front profile of the lower face at x = 0 (before nose and lips are added)
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


# nose: a ridge of gaussians from the root between the eyes down to the tip, plus tip ball and wings
NOSE = []
for k in range(14):
    t = k / 13
    NOSE.append((0.0, 0.797 - 0.068 * t, 0.003 + 0.025 * t ** 1.25, 0.0085 + 0.005 * t, 0.0085))
NOSE += [(0.0, 0.7265, 0.0335, 0.0145, 0.0105),            # tip
         (0.0165, 0.7165, 0.0135, 0.0075, 0.0075),           # wings
         (-0.0165, 0.7165, 0.0135, 0.0075, 0.0075)]
RELIEF = [  # (x, z, amount forward, sigma x, sigma z)  summed
    (0.045, 0.868, 0.0030, 0.030, 0.010), (-0.045, 0.868, 0.0030, 0.030, 0.010),   # brow ridge
    (0.0, 0.7035, 0.0040, 0.0120, 0.0060),                                         # philtrum
    (0.0, 0.6985, 0.0050, 0.0270, 0.0045),                                         # upper lip
    (0.0, 0.6880, -0.0030, 0.0330, 0.0025),                                        # mouth line
    (0.0, 0.6770, 0.0055, 0.0230, 0.0055),                                         # lower lip
    (0.0, 0.6660, -0.0030, 0.0250, 0.0050),                                        # groove under the lip
    (0.0, 0.6500, 0.0075, 0.0260, 0.0110),                                         # chin
    (0.068, 0.722, 0.0045, 0.022, 0.022), (-0.068, 0.722, 0.0045, 0.022, 0.022),   # cheeks
    (0.062, 0.808, -0.0030, 0.026, 0.024), (-0.062, 0.808, -0.0030, 0.026, 0.024),  # soft eye sockets
]


def shape_point(p):
    q = p.copy()
    if q.y < 0:
        yt = prof(q.z)
        if yt is not None:
            y0 = front_y(q.z)
            if y0 is not None and y0 < -1e-4:
                ratio = min(1.0, max(0.0, q.y / y0))
                q.y += (yt - y0) * ratio ** 1.6 * (1.0 - smooth(0.750, 0.790, q.z))
        front = min(1.0, max(0.0, (-q.y - 0.06) / 0.05))
        d = 0.0
        for (x, z, a, sx, sz) in RELIEF:
            d += a * g(q.x - x, sx) * g(q.z - z, sz)
        nose = 0.0
        for (x, z, a, sx, sz) in NOSE:
            nose = max(nose, a * g(q.x - x, sx) * g(q.z - z, sz))
        q.y -= (d + nose) * front
    return q


# ------------------------------------------------------------------ new high-resolution head
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=176, v_segments=128, radius=1.0)
ellip = Vector((0.15, 0.143, 0.19))
for v in bm.verts:
    d = v.co.normalized()
    hit = bvh.ray_cast(C, d)
    p = hit[0] if hit[0] else C + Vector((d.x * ellip.x, d.y * ellip.y, d.z * ellip.z))
    v.co = p
base_world = [v.co.copy() for v in bm.verts]
for v in bm.verts:
    v.co = shape_point(v.co)
shaped_world = [v.co.copy() for v in bm.verts]
inv = mw.inverted()
for v in bm.verts:
    v.co = inv @ v.co
for f in bm.faces:
    f.smooth = True
newme = bpy.data.meshes.new(P + "head_v005")
bm.to_mesh(newme)
bm.free()
for s in head.data.materials:
    newme.materials.append(s)
old_head_me = head.data
head.data = newme
for m in head.modifiers:
    if m.type == 'SUBSURF':
        m.levels = m.render_levels = 1

# ------------------------------------------------------------------ mouth shape keys (deltas in world, stored local)
R3 = mw.to_3x3().inverted()
head.shape_key_add(name="Basis")


def add_key(name, fn):
    kb = head.shape_key_add(name=name, from_mix=False)
    for i, p in enumerate(shaped_world):
        d = fn(p)
        if d is not None and d.length > 1e-7:
            kb.data[i].co = kb.data[i].co + R3 @ d
    return kb


def frontw(p):
    return min(1.0, max(0.0, (-p.y - 0.04) / 0.05))


def k_jaw(p):
    w = (1 - smooth(0.664, 0.690, p.z)) * frontw(p) * g(p.x, 0.075)
    return Vector((0, 0.003, -0.0095)) * w


def k_round(p):
    w = g(p.x, 0.030) * g(p.z - 0.688, 0.015) * frontw(p)
    return Vector((-p.x * 0.30, -0.0075, 0)) * w


def k_press(p):
    w = g(p.x, 0.034) * g(p.z - 0.688, 0.011) * frontw(p)
    return Vector((0, 0.0028, (0.688 - p.z) * 0.35)) * w


def k_tuck(p):
    w = g(p.x, 0.024) * g(p.z - 0.677, 0.007) * frontw(p)
    return Vector((0, 0.0045, 0.0035)) * w


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
    fc = kb.driver_add("value")
    dr = fc.driver
    dr.type = 'SCRIPTED'
    var = dr.variables.new()
    var.name = "m"
    var.targets[0].id = rig
    var.targets[0].data_path = '["mouth"]'
    dr.expression = expr

# ------------------------------------------------------------------ hidden twin of the head: the surface features stick to
surf = bpy.data.objects.new(P + "head_surface", newme)
for c in head.users_collection:
    c.objects.link(surf)
surf.parent = head.parent
surf.parent_type = head.parent_type
surf.parent_bone = head.parent_bone
surf.matrix_parent_inverse = head.matrix_parent_inverse.copy()
surf.matrix_basis = head.matrix_basis.copy()
sm = surf.modifiers.new("Smooth", 'SUBSURF')
sm.levels = sm.render_levels = 1
for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
    if hasattr(surf, attr):
        setattr(surf, attr, False)
surf.display_type = 'WIRE'
surf.hide_select = True


def stick(ob, offset):
    sw = ob.modifiers.new("OnFace", 'SHRINKWRAP')
    sw.target = surf
    sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'ABOVE_SURFACE'
    sw.offset = offset
    i = len(ob.modifiers) - 1
    to = 0
    for j, m in enumerate(ob.modifiers):
        if m.type == 'SUBSURF':
            to = j + 1
    if i != to:
        ob.modifiers.move(i, to)


# the eye parts are closed, flattened shells: keep only their front half, so that once they are laid
# onto the face the layers stack cleanly (white, iris, pupil, highlight) and the outline rims the white
def front_half(ob):
    m3 = ob.matrix_world.to_3x3()
    bmh = bmesh.new()
    bmh.from_mesh(ob.data)
    bmh.normal_update()
    kill = [f for f in bmh.faces if (m3 @ f.normal).y > 0.05]
    bmesh.ops.delete(bmh, geom=kill, context='FACES')
    bmh.to_mesh(ob.data)
    bmh.free()


for side in ("L", "R"):
    for part in ("eye.", "iris.", "pupil.", "shine."):
        ob = bpy.data.objects[P + part + side]
        if ob.data.users > 1:
            ob.data = ob.data.copy()
        front_half(ob)

# the mouth pieces sat on the old, receding lower face: bring each one just in front of the new
# surface first, so the shrinkwrap lays it where it was drawn (and not down on the jaw)
new_bvh = BVHTree.FromPolygons([mw @ v.co for v in newme.vertices], [p.vertices[:] for p in newme.polygons])
for o in bpy.data.objects:
    if o.name.startswith(P + "mouth.") and o.type in ('MESH', 'CURVE'):
        if o.type == 'MESH':
            ps = [o.matrix_world @ v.co for v in o.data.vertices]
        else:
            ps = [o.matrix_world @ Vector(pt.co[:3]) for sp in o.data.splines for pt in (list(sp.bezier_points) or list(sp.points))]
            ps = [o.matrix_world @ (bp.co) for sp in o.data.splines for bp in sp.bezier_points] or ps
        if not ps:
            continue
        cz = sum(q.z for q in ps) / len(ps)
        cx = sum(q.x for q in ps) / len(ps)
        hit = new_bvh.ray_cast(Vector((cx, 0.0, cz)), Vector((0, -1, 0)))
        if not hit[0]:
            continue
        dy = (hit[0].y - 0.004) - min(q.y for q in ps)
        o.matrix_world = Matrix.Translation((0, dy, 0)) @ o.matrix_world
        if o.name[len(P) + 6:len(P) + 8] in ("2_", "3_", "4_"):       # open shapes: a touch smaller and higher
            c = Vector((cx, 0.0, cz))
            big = o.name[len(P) + 6:len(P) + 8] == "2_"
            o.matrix_world = (Matrix.Translation(c + Vector((0, 0, 0.006 if big else 0.003)))
                              @ Matrix.Diagonal((0.88 if big else 0.92, 1.0, 0.72 if big else 0.82, 1.0))
                              @ Matrix.Translation(-c) @ o.matrix_world)

# a crisp dark rim behind each eye white (the white is now a single sheet, its inverted-hull outline
# would sit inside the head); it rides the same eye bone, so it closes with the blink
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
    rme.materials.clear()
    rme.materials.append(bpy.data.materials[P[:-1] + "_outline"])
    rim = bpy.data.objects.new(P + "eye_rim." + side, rme)
    for c in eo.users_collection:
        c.objects.link(rim)
    rim.parent, rim.parent_type, rim.parent_bone = eo.parent, eo.parent_type, eo.parent_bone
    rim.matrix_parent_inverse = eo.matrix_parent_inverse.copy()
    rim.matrix_basis = eo.matrix_basis.copy()
    ss = rim.modifiers.new("Smooth", 'SUBSURF')
    ss.levels = ss.render_levels = 1
    stick(rim, 0.0005)

for side in ("L", "R"):
    stick(bpy.data.objects[P + "eye." + side], 0.0012)
    stick(bpy.data.objects[P + "iris." + side], 0.0022)
    stick(bpy.data.objects[P + "pupil." + side], 0.0030)
    stick(bpy.data.objects[P + "shine." + side], 0.0038)
    stick(bpy.data.objects[P + "brow." + side], 0.0030)
for o in bpy.data.objects:
    if o.name.startswith(P + "mouth."):
        off = 0.0010 if o.name.endswith("_in") else 0.0020 if ("teeth" in o.name) else 0.0016 if "tongue" in o.name else 0.0024
        stick(o, off)
nose_old = bpy.data.objects[P + "nose"]
nose_old.hide_render = nose_old.hide_viewport = True


# ------------------------------------------------------------------ materials
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


SKIN = bpy.data.materials[P[:-1] + "_skin"]
OUTL = bpy.data.materials[P[:-1] + "_outline"]
SKIN_D = darker(SKIN, P[:-1] + "_skin_fold", (0.55, 0.44, 0.40))
NOSTRIL = darker(SKIN, P[:-1] + "_nostril", (0.32, 0.22, 0.2))


# ------------------------------------------------------------------ ears
def ellipsoid(bm, c, U, V, N, r, mat, seg=14, rings=10):
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=seg, v_segments=rings, radius=1.0)
    M = Matrix(((U.x * r[0], V.x * r[1], N.x * r[2]), (U.y * r[0], V.y * r[1], N.y * r[2]), (U.z * r[0], V.z * r[1], N.z * r[2])))
    vm = {}
    for v in t.verts:
        vm[v] = bm.verts.new(c + M @ v.co)
    for f in t.faces:
        nf = bm.faces.new([vm[v] for v in f.verts])
        nf.material_index = mat
        nf.smooth = True
    t.free()


def tube(bm, pts, rads, N, mat, ring=10):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = N - t * N.dot(t)
        a.normalize()
        b = t.cross(a)
        rr = []
        for k in range(ring):
            ang = k / ring * math.tau
            rr.append(bm.verts.new(p + (a * math.cos(ang) + b * math.sin(ang)) * rads[i]))
        rings.append(rr)
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
    N = Vector((1.0, -0.42, 0.05)).normalized()          # splayed forward so the ear reads from the front
    V = Vector((0.0, 0.22, 1.0))
    V = (V - N * V.dot(N)).normalized()
    U = V.cross(N).normalized()           # towards the back of the head
    c = Vector((0.149, 0.014, 0.794))
    bm = bmesh.new()

    def at(u, v, w):
        return c + U * u + V * v + N * w
    ru, rv = 0.0235, 0.0400
    ellipsoid(bm, at(0.002, 0.0, 0.004), U, V, N, (ru, rv, 0.0085), 0, seg=20, rings=14)      # ear body
    ellipsoid(bm, at(0.004, -0.030, 0.006), U, V, N, (0.0115, 0.0125, 0.0065), 0)            # lobe
    hel = []
    rad = []
    n = 26
    for i in range(n):
        t = i / (n - 1)
        ph = math.radians(128 - 205 * t)
        hel.append(at(ru * 0.93 * math.cos(ph) + 0.002, rv * 0.94 * math.sin(ph), 0.0118))
        rad.append(0.0030 + 0.0020 * math.sin(math.pi * min(1, t * 1.25)))
    tube(bm, hel, rad, N, 0)                                                                    # helix rim
    anti = []
    arad = []
    for i in range(16):
        t = i / 15
        ph = math.radians(82 - 140 * t)
        anti.append(at(0.0115 * math.cos(ph) + 0.004, 0.022 * math.sin(ph) + 0.001, 0.0122))
        arad.append(0.0026 + 0.0010 * math.sin(math.pi * t))
    tube(bm, anti, arad, N, 0)                                                                  # antihelix
    top = anti[0]
    br = [top.lerp(at(-0.010, 0.026, 0.0118), t / 5) for t in range(6)]
    tube(bm, br, [0.0022 - 0.0006 * t / 5 for t in range(6)], N, 0)                             # upper fork
    ellipsoid(bm, at(-0.0035, -0.004, 0.0122), U, V, N, (0.0095, 0.0135, 0.0012), 2)          # concha bowl
    ellipsoid(bm, at(-0.0185, -0.008, 0.0105), U, V, N, (0.0045, 0.0055, 0.0040), 0)          # tragus
    if s < 0:
        for v in bm.verts:
            v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    ob = bpy.data.objects[P + "ear." + side]
    im = ob.matrix_world.inverted()
    for v in bm.verts:
        v.co = im @ v.co
    me = bpy.data.meshes.new(P + "ear_v005." + side)
    bm.to_mesh(me)
    bm.free()
    for m in (SKIN, OUTL, SKIN_D, OUTL):
        me.materials.append(m)
    ob.data = me
    for m in ob.modifiers:
        if m.type == 'SOLIDIFY':
            m.thickness = -0.0024
            m.material_offset = 1
        if m.type == 'SUBSURF':
            m.levels = m.render_levels = 1


build_ear("L")
build_ear("R")

# ------------------------------------------------------------------ nostrils
bm = bmesh.new()
for s in (-1, 1):
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=12, v_segments=8, radius=1.0)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.0042, v.co.y * 0.0030, v.co.z * 0.0022))
    vm = {v: bm.verts.new(v.co + Vector((s * 0.0080, -0.150, 0.7105))) for v in t.verts}
    for f in t.faces:
        bm.faces.new([vm[v] for v in f.verts]).smooth = True
    t.free()
nme = bpy.data.meshes.new(P + "nostrils")
bm.to_mesh(nme)
bm.free()
nme.materials.append(NOSTRIL)
nos = bpy.data.objects.new(P + "nostrils", nme)
for c in head.users_collection:
    c.objects.link(nos)
nos.parent = rig
nos.parent_type = 'BONE'
nos.parent_bone = "head"
bpy.context.view_layer.update()
nos.matrix_world = Matrix()
st = nos.modifiers.new("OnFace", 'SHRINKWRAP')
st.target = surf
st.wrap_method = 'NEAREST_SURFACEPOINT'
st.wrap_mode = 'ABOVE_SURFACE'
st.offset = 0.0006

# nose fold: a soft line under the tip from one nostril wing to the other, so the nose reads from the front
bm = bmesh.new()
arc = []
for i in range(13):
    t = i / 12 * 2 - 1
    arc.append(Vector((t * 0.0215, -0.16, 0.7155 - 0.0055 * (1 - t * t) + 0.004 * t ** 4)))
tube(bm, arc, [0.0012 + 0.0010 * (1 - abs(i / 6 - 1)) for i in range(13)], Vector((0, -1, 0)), 0, ring=8)
fme = bpy.data.meshes.new(P + "nose_fold")
bm.to_mesh(fme)
bm.free()
fme.materials.append(SKIN_D)
fold = bpy.data.objects.new(P + "nose_fold", fme)
for c in head.users_collection:
    c.objects.link(fold)
fold.parent, fold.parent_type, fold.parent_bone = rig, 'BONE', "head"
bpy.context.view_layer.update()
fold.matrix_world = Matrix()
sf = fold.modifiers.new("OnFace", 'SHRINKWRAP')
sf.target = surf
sf.wrap_method = 'NEAREST_SURFACEPOINT'
sf.wrap_mode = 'ABOVE_SURFACE'
sf.offset = 0.0007

rig.data.pose_position = 'POSE'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False)
print("ACE_FACE_DONE")

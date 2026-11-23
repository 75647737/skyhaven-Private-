"""Replace the blob shoes of cartoon Ace / Tori with shaped shoes.

    blender -b <master.blend> --python tools/blender/build_shoes.py -- <PREFIX> <out.blend>

Ace ("AC"): brown leather lace-ups — lofted upper (heel counter, instep, rounded
toe box), darker sole with a little toe spring, three cream laces.
Tori ("TC"): nude low pumps — thin sole on a gentle wedge, small block heel,
low-cut upper so the top of the foot shows, little terracotta bow.
Everything is bone-parented to foot.L/R, like the rest of the cartoon rig.
"""
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREFIX = argv[0] if argv else globals().get("PREFIX", "AC")
OUT = argv[1] if len(argv) > 1 else None
RIG = bpy.data.objects[PREFIX + ".rig"]


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def toon_from(src, name, hexcol):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = src.copy()
    m.name = name
    c = lin(hexcol)
    for n in m.node_tree.nodes:
        if n.type == 'VALTORGB':
            el = n.color_ramp.elements
            ks = [0.55, 0.8, 1.0] + [1.0] * (len(el) - 3)
            for e, k in zip(el, ks):
                e.color = [v * k for v in c] + [1]
    m.diffuse_color = c + [1]
    return m


SPEC = {
    "AC": dict(cx=0.074, y_heel=0.072, y_toe=-0.134, sole=0.015, spring=0.009,
               w=[(0.0, 0.040), (0.35, 0.046), (0.70, 0.058), (0.88, 0.050), (1.0, 0.012)],
               h=[(0.0, 0.058), (0.30, 0.066), (0.55, 0.060), (0.78, 0.040), (0.93, 0.030), (1.0, 0.010)],
               base=lambda t: 0.0,
               colors=dict(upper="#3a2418", sole="#1c120c", lace="#efe6d2"),
               laces=(0.56, 0.64, 0.72), heel_block=None, bow=None),
    "TC": dict(cx=0.0705, y_heel=0.040, y_toe=-0.112, sole=0.006, spring=0.004,
               w=[(0.0, 0.026), (0.40, 0.032), (0.72, 0.038), (0.90, 0.030), (1.0, 0.008)],
               h=[(0.0, 0.030), (0.45, 0.024), (0.62, 0.030), (0.82, 0.026), (0.95, 0.016), (1.0, 0.006)],
               base=lambda t: 0.012 + 0.014 * (1 - min(1.0, t / 0.6)) ** 1.5,
               colors=dict(upper="#d8bf94", sole="#a8875c", lace="#c96f53"),
               laces=(), heel_block=(0.0, 0.24, 0.046), bow=0.66),
}


def interp(pts, t):
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return pts[-1][1]


def loft(name, sp, sx, z_lo, z_hi_fn, w_fn, segs=14, n=28, flat_bottom=True):
    """Shoe-like solid: sections across the foot from heel (t=0) to toe (t=1)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        t = i / n
        y = sp["y_heel"] + (sp["y_toe"] - sp["y_heel"]) * t
        w = w_fn(t)
        z0 = z_lo(t)
        h = max(0.002, z_hi_fn(t) - z0)
        ring = []
        for j in range(segs + 1):                  # arc over the top, side to side
            a = math.pi * j / segs
            ca, sa = math.cos(a), math.sin(a)
            x = w * (abs(ca) ** 0.8) * (1 if ca >= 0 else -1)
            z = z0 + h * (sa ** 0.6)
            ring.append(bm.verts.new((sp["cx"] * sx + x, y, z)))
        # flat bottom back across
        for j in range(1, 4):
            x = -w + 2 * w * j / 4
            ring.append(bm.verts.new((sp["cx"] * sx + x, y, z0)))
        rings.append(ring)
    m = len(rings[0])
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(m):
            bm.faces.new((a_[k], a_[(k + 1) % m], b_[(k + 1) % m], b_[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return me


def obj(name, me, mats, bone, outline=-0.004, sub=2):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    ob = bpy.data.objects.new(name, me)
    COLL.objects.link(ob)
    for mt in mats:
        me.materials.append(mt)
    for p in me.polygons:
        p.use_smooth = True
        p.material_index = 0
    if sub:
        s = ob.modifiers.new("Smooth", 'SUBSURF')
        s.levels, s.render_levels = 1, sub
    if outline and len(mats) > 1:
        so = ob.modifiers.new("Outline", 'SOLIDIFY')
        so.thickness, so.offset, so.use_flip_normals, so.material_offset, so.use_rim = outline, 1, True, 1, False
    ob.parent = RIG
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = RIG.matrix_world.copy()
    return ob


def ellipsoid_me(name, c, size, segs=(16, 8)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=1)
    for v in bm.verts:
        v.co = Vector((c[0] + v.co.x * size[0], c[1] + v.co.y * size[1], c[2] + v.co.z * size[2]))
    bm.to_mesh(me)
    bm.free()
    return me


def run():
    global COLL
    sp = SPEC[PREFIX]
    old_shoe = bpy.data.objects[PREFIX + ".shoe.L"]
    COLL = old_shoe.users_collection[0]
    shoe_mat, outline = old_shoe.data.materials[0], old_shoe.data.materials[1]
    M = {k: toon_from(shoe_mat, "%s_shoe_%s" % (PREFIX, k), v) for k, v in sp["colors"].items()}
    act = RIG.animation_data.action if RIG.animation_data else None
    if RIG.animation_data:
        RIG.animation_data.action = None
    pp = RIG.data.pose_position
    RIG.data.pose_position = 'REST'
    for n in ("shoe", "heel"):
        for s in "LR":
            o = bpy.data.objects.get("%s.%s.%s" % (PREFIX, n, s))
            if o:
                bpy.data.objects.remove(o)
    w_fn = lambda t: interp(sp["w"], t)
    spring = lambda t: sp["spring"] * max(0.0, (t - 0.72) / 0.28) ** 2
    for s, sx in (("L", 1), ("R", -1)):
        base = lambda t: sp["base"](t) + spring(t)
        # sole
        me = loft("%s.sole.%s" % (PREFIX, s), sp, sx, base, lambda t: base(t) + sp["sole"],
                  lambda t: w_fn(t) + 0.004, segs=8)
        obj("%s.sole.%s" % (PREFIX, s), me, [M["sole"], outline], "foot." + s, outline=-0.003, sub=1)
        # upper
        top = lambda t: base(t) + sp["sole"] + interp(sp["h"], t)
        me = loft("%s.shoe.%s" % (PREFIX, s), sp, sx, lambda t: base(t) + sp["sole"] * 0.6, top, w_fn)
        obj("%s.shoe.%s" % (PREFIX, s), me, [M["upper"], outline], "foot." + s)
        # laces (Ace)
        for i, t in enumerate(sp["laces"]):
            y = sp["y_heel"] + (sp["y_toe"] - sp["y_heel"]) * t
            z = top(t) + 0.002
            me = ellipsoid_me("%s.lace%d.%s" % (PREFIX, i, s), (sp["cx"] * sx, y, z), (w_fn(t) * 0.55, 0.0035, 0.0028))
            obj("%s.lace%d.%s" % (PREFIX, i, s), me, [M["lace"], outline], "foot." + s, outline=-0.0015, sub=1)
        # block heel (Tori)
        if sp["heel_block"]:
            t0, t1, hw = sp["heel_block"]
            y0 = sp["y_heel"] + (sp["y_toe"] - sp["y_heel"]) * t0 - 0.002
            y1 = sp["y_heel"] + (sp["y_toe"] - sp["y_heel"]) * t1
            zt = base(0.0)
            me = bpy.data.meshes.new("%s.heelblock.%s" % (PREFIX, s))
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                taper = 0.85 if v.co.z < 0 else 1.0
                v.co = Vector((sp["cx"] * sx + v.co.x * hw * taper, (y0 + y1) / 2 + v.co.y * (y0 - y1) * taper, zt / 2 + v.co.z * zt))
            bm.to_mesh(me)
            bm.free()
            ob = obj("%s.heel.%s" % (PREFIX, s), me, [M["sole"], outline], "foot." + s, outline=-0.003, sub=0)
            bv = ob.modifiers.new("Bevel", 'BEVEL')
            bv.width, bv.segments = 0.003, 2
            ob.modifiers.move(len(ob.modifiers) - 1, 0)
        # little bow on the toe (Tori)
        if sp["bow"]:
            t = sp["bow"]
            y = sp["y_heel"] + (sp["y_toe"] - sp["y_heel"]) * t
            z = top(t) + 0.003
            for k, dx in enumerate((-0.007, 0.007)):
                me = ellipsoid_me("%s.bow%d.%s" % (PREFIX, k, s), (sp["cx"] * sx + dx, y, z), (0.0075, 0.004, 0.005))
                obj("%s.bow%d.%s" % (PREFIX, k, s), me, [M["lace"], outline], "foot." + s, outline=-0.0012, sub=1)
            me = ellipsoid_me("%s.bowknot.%s" % (PREFIX, s), (sp["cx"] * sx, y, z + 0.001), (0.003, 0.004, 0.0035))
            obj("%s.bowknot.%s" % (PREFIX, s), me, [M["lace"], outline], "foot." + s, outline=-0.0012, sub=1)
    RIG.data.pose_position = pp
    if act:
        RIG.animation_data.action = act


run()
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    open(OUT + ".log", "w").write("ok")

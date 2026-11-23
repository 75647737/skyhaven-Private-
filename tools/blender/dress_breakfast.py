"""Dress the kitchen for the breakfast scene (breakfast_v001.blend).

Run inside Blender with the scene open (it rebuilds its own objects each time):
  * hob on the counter with a frying pan and an egg; kettle moved along;
  * the round table is replaced by a family table with a cloth that hangs low
    (it hides the seated characters' legs), two chairs facing the camera;
  * breakfast for two on a budget: one egg split over two plates, toast, mugs,
    Max's sippy cup, the napkin with Ace's drone sketch;
  * a bill held to the fridge with a magnet (blueprint: tight budget);
  * hand props: Tori's spatula, Ace's napkin and pencil (bone-parented) plus
    "resting" copies (spatula on the counter, napkin on the table) so the
    animation can hand them over by switching visibility.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

S = bpy.context.scene
COLL_NAME = "Breakfast"


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


BASE = bpy.data.materials["RM_wall"]
OUT = bpy.data.materials["RM_outline"]


def toon(name, hexcol):
    m = bpy.data.materials.get(name)
    if m is None:
        m = BASE.copy()
        m.name = name
    c = lin(hexcol)
    cr = [n for n in m.node_tree.nodes if n.type == 'VALTORGB'][0]
    for e, k in zip(cr.color_ramp.elements, (0.6, 0.82, 1.0)):
        e.color = [v * k for v in c] + [1]
    m.diffuse_color = c + [1]
    return m


M = {k: toon("BF_" + k, v) for k, v in {
    "hob": "#2b2b30", "ring": "#d9572b", "pan": "#3a3a42", "egg": "#fbf7ee", "yolk": "#f5b21f",
    "plate": "#fbfaf6", "toast": "#d79b55", "crust": "#a8672f", "mug_a": "#c96f53", "mug_b": "#3d4a63",
    "sippy": "#a7c7e7", "lid": "#f6f1e6", "cloth": "#f4efe4", "check": "#cfdcc4", "table": "#a86f45",
    "chair": "#c96f53", "paper": "#f7f1df", "ink": "#3a3a3a", "red": "#c8463a", "magnet": "#e0a43c",
    "wood": "#c08a55", "steel": "#c9ced3", "pencil": "#f2c14e", "napkin": "#fffdf6"}.items()}

coll = bpy.data.collections.get(COLL_NAME) or bpy.data.collections.new(COLL_NAME)
if coll.name not in S.collection.children:
    S.collection.children.link(coll)
for o in list(coll.objects):
    bpy.data.objects.remove(o)


def finish(ob, mat, outline=0.005, smooth=True, sub=0, bevel=0.0):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    if ob.type == 'MESH':
        for p in ob.data.polygons:
            p.use_smooth = smooth
    if bevel:
        b = ob.modifiers.new("Bevel", 'BEVEL')
        b.width, b.segments, b.limit_method = bevel, 2, 'NONE'
    if sub:
        s = ob.modifiers.new("Smooth", 'SUBSURF')
        s.levels = s.render_levels = sub
    if outline:
        ob.data.materials.append(OUT)
        so = ob.modifiers.new("Outline", 'SOLIDIFY')
        so.thickness, so.offset, so.use_flip_normals, so.material_offset, so.use_rim = outline, 1, True, 1, False
    return ob


def mesh(name, build):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build(bm)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def box(name, c, size, mat, outline=0.005, bevel=0.0, rot=None):
    def b(bm):
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if rot:
            bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return finish(mesh(name, b), mat, outline, smooth=bool(bevel), bevel=bevel)


def cyl(name, c, r, depth, mat, outline=0.004, segs=32, r2=None, rot=None, cap=True):
    def b(bm):
        bmesh.ops.create_cone(bm, cap_ends=cap, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
        if rot:
            bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return finish(mesh(name, b), mat, outline)


def blob(name, c, size, mat, outline=0.003, segs=(20, 10), squash=None):
    def b(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=1)
        for v in bm.verts:
            co = v.co.copy()
            if squash:
                co = squash(co)
            v.co = Vector((c[0] + co.x * size[0], c[1] + co.y * size[1], c[2] + co.z * size[2]))
    return finish(mesh(name, b), mat, outline)


def egg_half(name, c, r, rot=0.0):
    """Fried egg white (wobbly flat blob) + yolk."""
    def wob(co):
        a = math.atan2(co.y, co.x)
        k = 1 + 0.12 * math.sin(3 * a + rot) + 0.06 * math.sin(5 * a + 1.3 + rot)
        return Vector((co.x * k, co.y * k, co.z))
    blob(name + "_white", c, (r, r * 0.85, 0.006), M["egg"], outline=0.002, squash=wob)
    blob(name + "_yolk", (c[0] + r * 0.15, c[1], c[2] + 0.006), (r * 0.42, r * 0.42, 0.012), M["yolk"], outline=0.002)


# ------------------------------------------------------------------ hide the old round table
for o in bpy.data.objects:
    if o.name.startswith(("KT.table", "KT.chair", "KT.bowl", "KT.fruit", "KT.lamp_cord", "KT.lamp_shade")):
        o.hide_render = True
        o.hide_set(True)
k = bpy.data.objects.get("KT.kettle")
if k:
    k.location.x = 4.95 - 3.5 + k.location.x if False else k.location.x
for n in ("KT.kettle", "KT.kettle_lid"):
    o = bpy.data.objects.get(n)
    if o:
        o.location.x = 1.45      # shift from x 3.5 to about 4.95 (mesh was built at x 3.5)

# ------------------------------------------------------------------ hob, pan, egg
HX, HY, TOPZ = 3.95, 1.22, 0.630
box("BF.hob", (HX, HY, TOPZ + 0.006), (0.40, 0.34, 0.012), M["hob"], outline=0.004, bevel=0.004)
for i, (dx, dy, r) in enumerate([(-0.095, -0.05, 0.065), (0.10, 0.06, 0.055)]):
    def ring(bm, dx=dx, dy=dy, r=r):
        bmesh.ops.create_circle(bm, cap_ends=False, segments=32, radius=r)
        bmesh.ops.translate(bm, vec=Vector((HX + dx, HY + dy, TOPZ + 0.0125)), verts=bm.verts)
    ob = mesh("BF.hob_ring%d" % i, ring)
    sk = ob.modifiers.new("Wire", 'SKIN')
    for v in ob.data.skin_vertices[0].data:
        v.radius = (0.004, 0.004)
    finish(ob, M["ring"], outline=0)
PX, PY = HX - 0.095, HY - 0.05
cyl("BF.pan", (PX, PY, TOPZ + 0.030), 0.095, 0.03, M["pan"], r2=0.105, segs=40)
cyl("BF.pan_inside", (PX, PY, TOPZ + 0.031), 0.088, 0.03, M["hob"], outline=0, segs=40)
cyl("BF.pan_handle", (PX - 0.17, PY - 0.06, TOPZ + 0.04), 0.012, 0.16, M["pan"], segs=12,
    rot=Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(-20), 4, 'X') if False else
    Matrix.Rotation(math.radians(-19), 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'Y'))
egg_half("BF.pan_egg", (PX, PY, TOPZ + 0.048), 0.05)

# ------------------------------------------------------------------ family table + cloth + chairs
TX, TY, TZ = 5.0, 0.12, 0.40
TW, TD = 1.02, 0.56
box("BF.table_top", (TX, TY, TZ - 0.02), (TW, TD, 0.04), M["table"], bevel=0.008)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("BF.table_leg%d%d" % (sx, sy), (TX + sx * (TW / 2 - 0.05), TY + sy * (TD / 2 - 0.05), (TZ - 0.04) / 2),
            (0.04, 0.04, TZ - 0.04), M["table"], outline=0.003)
# cloth: top sheet plus a skirt on the camera side and the ends
box("BF.cloth_top", (TX, TY, TZ + 0.002), (TW * 0.94, TD + 0.04, 0.006), M["cloth"], outline=0.004, bevel=0.002)
DROP = 0.24
box("BF.cloth_front", (TX, TY - TD / 2 - 0.021, TZ - DROP / 2), (TW * 0.94, 0.008, DROP), M["cloth"], outline=0.004)
for sx in (-1, 1):
    box("BF.cloth_end%d" % sx, (TX + sx * (TW * 0.47 + 0.004), TY, TZ - DROP / 2 + 0.03), (0.008, TD + 0.04, DROP - 0.06),
        M["cloth"], outline=0.004)
for i in range(7):                                    # simple check pattern stripes on the front drop
    x = TX - TW * 0.42 + i * TW * 0.14
    box("BF.cloth_stripe%d" % i, (x, TY - TD / 2 - 0.026, TZ - DROP / 2), (0.03, 0.004, DROP), M["check"], outline=0)
box("BF.cloth_band", (TX, TY - TD / 2 - 0.027, TZ - DROP + 0.05), (TW * 0.94, 0.004, 0.03), M["check"], outline=0)

CHAIRS = {"tori": (4.72, 0.62), "ace": (5.30, 0.62)}
SEAT = 0.20
for name, (cx, cy) in CHAIRS.items():
    box("BF.chair_seat_" + name, (cx, cy, SEAT - 0.015), (0.30, 0.28, 0.03), M["chair"], bevel=0.006)
    box("BF.chair_back_" + name, (cx, cy + 0.15, SEAT + 0.20), (0.30, 0.03, 0.34), M["chair"], bevel=0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("BF.chair_leg_%s%d%d" % (name, sx, sy), (cx + sx * 0.12, cy + sy * 0.11, (SEAT - 0.03) / 2),
                (0.025, 0.025, SEAT - 0.03), M["table"], outline=0.002)

# ------------------------------------------------------------------ breakfast for two (+ Max)
PLATES = {"tori": (4.74, 0.02), "ace": (5.28, 0.02)}
for name, (x, y) in PLATES.items():
    cyl("BF.plate_" + name, (x, y, TZ + 0.012), 0.085, 0.012, M["plate"], r2=0.07, segs=40)
    egg_half("BF.egg_" + name, (x - 0.02, y + 0.005, TZ + 0.022), 0.034, rot=1.0 if name == "ace" else 2.5)
    box("BF.toast_" + name, (x + 0.035, y - 0.01, TZ + 0.026), (0.06, 0.062, 0.012), M["toast"], outline=0.002, bevel=0.004,
        rot=Matrix.Rotation(math.radians(18), 4, 'Z'))
cyl("BF.mug_tori", (4.52, 0.13, TZ + 0.045), 0.032, 0.08, M["mug_a"], segs=28)
cyl("BF.mug_ace", (5.50, 0.13, TZ + 0.045), 0.032, 0.08, M["mug_b"], segs=28)
for n, x in (("tori", 4.52 - 0.036), ("ace", 5.50 + 0.036)):
    def handle(bm, x=x):
        bmesh.ops.create_circle(bm, cap_ends=False, segments=16, radius=0.022)
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector((x, 0.13, TZ + 0.045)), verts=bm.verts)
    ob = mesh("BF.mug_handle_" + n, handle)
    ob.modifiers.new("Wire", 'SKIN')
    for v in ob.data.skin_vertices[0].data:
        v.radius = (0.005, 0.005)
    finish(ob, M["mug_a" if n == "tori" else "mug_b"], outline=0)
cyl("BF.sippy", (4.98, -0.02, TZ + 0.04), 0.022, 0.07, M["sippy"], segs=24)
cyl("BF.sippy_lid", (4.98, -0.02, TZ + 0.083), 0.024, 0.018, M["lid"], r2=0.012, segs=24)
# napkin with the drone sketch, lying on the table in front of Ace's plate (shown when he sits)
NAP = (5.12, -0.12)


def napkin(name, center, rot_m, parent=None):
    def b(bm):
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.045)
        bmesh.ops.transform(bm, matrix=rot_m, verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    ob = finish(mesh(name, b), M["napkin"], outline=0.002, smooth=False)
    # drone sketch: body, 4 arms, 4 rotors
    sk = []
    lines = [((0, 0), (0.016, 0.016)), ((0, 0), (-0.016, 0.016)), ((0, 0), (0.016, -0.016)), ((0, 0), (-0.016, -0.016))]
    for i, (a, bpt) in enumerate(lines):
        mid = ((a[0] + bpt[0]) / 2, (a[1] + bpt[1]) / 2)
        ang = math.atan2(bpt[1] - a[1], bpt[0] - a[0])
        def ln(bm, mid=mid, ang=ang):
            bmesh.ops.create_cube(bm, size=1)
            for v in bm.verts:
                v.co = Vector((v.co.x * 0.024, v.co.y * 0.0022, v.co.z * 0.0008))
            bmesh.ops.transform(bm, matrix=rot_m @ Matrix.Translation((mid[0], mid[1], 0.0012)) @ Matrix.Rotation(ang, 4, 'Z'), verts=bm.verts)
            bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
        sk.append(finish(mesh("%s_line%d" % (name, i), ln), M["ink"], outline=0, smooth=False))
        def rotor(bm, p=bpt):
            bmesh.ops.create_circle(bm, cap_ends=False, segments=16, radius=0.008)
            bmesh.ops.transform(bm, matrix=rot_m @ Matrix.Translation((p[0], p[1], 0.0012)), verts=bm.verts)
            bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
        r = mesh("%s_rotor%d" % (name, i), rotor)
        r.modifiers.new("Wire", 'SKIN')
        for v in r.data.skin_vertices[0].data:
            v.radius = (0.0011, 0.0011)
        sk.append(finish(r, M["ink"], outline=0))
    def bodyc(bm):
        bmesh.ops.create_circle(bm, cap_ends=True, segments=12, radius=0.005)
        bmesh.ops.transform(bm, matrix=rot_m @ Matrix.Translation((0, 0, 0.0014)), verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    sk.append(finish(mesh(name + "_body", bodyc), M["ink"], outline=0))
    for o in sk:
        o.parent = ob
        o.matrix_parent_inverse = ob.matrix_world.inverted()
    return ob


napkin("BF.napkin_table", (NAP[0], NAP[1], TZ + 0.006), Matrix.Rotation(math.radians(-15), 4, 'Z'))

# ------------------------------------------------------------------ bill on the fridge
FX, FY, FZ = 5.79 + 0.0, 0.995, 1.15
box("BF.bill", (6.0, FY - 0.004, FZ), (0.13, 0.004, 0.17), M["paper"], outline=0.002)
box("BF.bill_head", (6.0, FY - 0.008, FZ + 0.06), (0.10, 0.003, 0.018), M["red"], outline=0)
for i in range(4):
    box("BF.bill_line%d" % i, (6.0 - 0.01 * (i % 2), FY - 0.008, FZ + 0.025 - i * 0.025), (0.09 - 0.02 * (i % 2), 0.003, 0.005), M["ink"], outline=0)
box("BF.bill_total", (6.03, FY - 0.008, FZ - 0.07), (0.05, 0.003, 0.008), M["red"], outline=0)
blob("BF.magnet", (6.0, FY - 0.012, FZ + 0.082), (0.016, 0.008, 0.016), M["magnet"])

# ------------------------------------------------------------------ resting spatula on the counter (shown after she puts it down)
def spatula(name):
    def b(bm):
        # handle along +Y from -0.06 to +0.05, blade +0.05..+0.11 (origin = grip)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.007, radius2=0.006, depth=0.11)
        bmesh.ops.transform(bm, matrix=Matrix.Translation((0, -0.005, 0)) @ Matrix.Rotation(math.radians(-90), 4, 'X'), verts=bm.verts)
    h = finish(mesh(name, b), M["wood"], outline=0.002)
    def bl(bm):
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.045, v.co.y * 0.06, v.co.z * 0.003))
        bmesh.ops.translate(bm, vec=Vector((0, 0.08, 0)), verts=bm.verts)
    blade = finish(mesh(name + "_blade", bl), M["steel"], outline=0.0015, smooth=False, bevel=0.002)
    blade.parent = h
    return h


sp_rest = spatula("BF.spatula_rest")
sp_rest.location = (HX + 0.22, HY - 0.08, TOPZ + 0.012)
sp_rest.rotation_euler = (0, 0, math.radians(200))


# ------------------------------------------------------------------ hand props (bone-parented to the overridden rigs)
def rig(name):
    return [o for o in S.objects if o.name == name and o.library is None][0]


def attach(ob, rig_obj, bone, loc, rot):
    ob.parent = rig_obj
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    ob.matrix_parent_inverse = Matrix()
    ob.location = loc            # relative to the bone tail, bone axes
    ob.rotation_euler = rot
    ob.scale = (1 / rig_obj.scale.x,) * 3 if False else (1, 1, 1)


tori, ace = rig("TC.rig"), rig("AC.rig")
sp = spatula("BF.spatula_hand")
attach(sp, tori, "hand.L", (0.0, -0.035, 0.0), (0, 0, 0))
nap = napkin("BF.napkin_hand", (0, 0, 0), Matrix())
attach(nap, ace, "hand.L", (0.0, -0.03, -0.012), (0, 0, 0))
def pencil_b(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.004, radius2=0.004, depth=0.07)
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(-90), 4, 'X'), verts=bm.verts)
pen = finish(mesh("BF.pencil_hand", pencil_b), M["pencil"], outline=0.0015)
attach(pen, ace, "hand.R", (0.0, -0.02, 0.0), (0, 0, 0))

print("dressed", len(coll.objects))

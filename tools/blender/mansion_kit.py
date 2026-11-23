"""Shared toon-architecture kit for the Skyhaven mansion scripts.

Used by build_mansion.py (exterior) and build_mansion_interior.py (rooms).
Geometry is written in real metres; the scripts parent everything to MN.root,
which scales the house to the cartoon characters (see SCALE).
"""
import bpy, bmesh, math, random
import math as math_mod
from mathutils import Vector, Matrix

SCALE = 0.62          # real metres -> cartoon set units (Ace is 1.07 = a 1.73 m adult)
TARGET = [None]       # collection new objects go into
PARENT = [None]       # object new objects are parented to (MN.root)


def use(coll):
    TARGET[0] = coll

def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def _toon_value(nt, ks):
    """Three-step toon light value WITHOUT a Color Ramp node: EEVEE packs every Color Ramp
    in the scene into one table of 128 rows, and a city with the mansion linked has far more
    materials than that (the extra ones rendered black). Steps at 0.16 and 0.7 like before."""
    d = nt.nodes.new('ShaderNodeBsdfDiffuse')
    s2r = nt.nodes.new('ShaderNodeShaderToRGB')
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(d.outputs[0], s2r.inputs[0])
    nt.links.new(s2r.outputs[0], bw.inputs[0])
    v = bw.outputs[0]
    s1 = nt.nodes.new('ShaderNodeMath'); s1.operation = 'GREATER_THAN'
    nt.links.new(v, s1.inputs[0]); s1.inputs[1].default_value = 0.16
    s2 = nt.nodes.new('ShaderNodeMath'); s2.operation = 'GREATER_THAN'
    nt.links.new(v, s2.inputs[0]); s2.inputs[1].default_value = 0.7
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY_ADD'
    nt.links.new(s1.outputs[0], m1.inputs[0]); m1.inputs[1].default_value = ks[1] - ks[0]; m1.inputs[2].default_value = ks[0]
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY_ADD'
    nt.links.new(s2.outputs[0], m2.inputs[0]); m2.inputs[1].default_value = ks[2] - ks[1]
    nt.links.new(m1.outputs[0], m2.inputs[2])
    return m2.outputs[0]


def _toon_finish(nt, value, color):
    mixn = nt.nodes.new('ShaderNodeMix')
    mixn.data_type = 'RGBA'
    mixn.blend_type = 'MULTIPLY'
    mixn.inputs[0].default_value = 1.0
    ins = [s for s in mixn.inputs if s.type == 'RGBA']
    nt.links.new(value, ins[0])
    if isinstance(color, (list, tuple)):
        ins[1].default_value = color
    else:
        nt.links.new(color, ins[1])
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new([s for s in mixn.outputs if s.type == 'RGBA'][0], em.inputs[0])
    nt.links.new(em.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])


def toon(name, hexcol, ks=(0.62, 0.84, 1.0)):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    c = lin(hexcol)
    _toon_finish(nt, _toon_value(nt, ks), c + [1])
    m.diffuse_color = c + [1]
    return m


OUTL = bpy.data.materials.get("MN_outline") or bpy.data.materials.new("MN_outline")
OUTL.use_nodes = True
_nt = OUTL.node_tree
_nt.nodes.clear()
_em = _nt.nodes.new('ShaderNodeEmission')
_em.inputs[0].default_value = lin("#2a221d") + [1]
_nt.links.new(_em.outputs[0], _nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
OUTL.use_backface_culling = True
OUTL.diffuse_color = lin("#2a221d") + [1]

M = {k: toon("MN_" + k, v) for k, v in {
    "white": "#f4f1ea", "white2": "#e6e1d7", "beige": "#dcc6a6", "sand": "#e9dcc6", "grey": "#8f9195",
    "wood": "#a0613a", "wood_dk": "#6f3f24", "stone1": "#b9a68c", "stone2": "#9c8a73", "stone3": "#d0c1a8",
    "glass": "#4a5e6e", "glass_lt": "#7f97a8", "frame": "#3b3b40", "shadow": "#6b6058",
    "rail": "#dcedf2", "plant": "#4f8a3c", "plant2": "#6aa84f", "vine": "#5d8f37", "lawn": "#74b04a",
    "paving": "#d9d2c5", "drive": "#b9b3a8", "trunk": "#7a5234", "leaf1": "#5e9a3f", "leaf2": "#7db454",
    "pot": "#f1ece3", "soil": "#5a4333", "door": "#8a4f2b",
    "car": "#f2f2f0", "car_glass": "#2f3a45", "tyre": "#26262a", "chrome": "#c9ced3", "lamp": "#fff6d8",
    "tail": "#c8463a"}.items()}


# ---------------------------------------------------------------- helpers
def new_obj(name, bm, mats, outline=0.025, smooth=False, bevel=0.0, sub=0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    TARGET[0].objects.link(ob)
    if PARENT[0]:
        ob.parent = PARENT[0]
    for mt in mats:
        me.materials.append(mt)
    if smooth is not None:          # None keeps the per-face flags set in the bmesh
        for p in me.polygons:
            p.use_smooth = smooth
    if bevel:
        b = ob.modifiers.new("Bevel", 'BEVEL')
        b.width, b.segments, b.limit_method = bevel, 2, 'ANGLE'
        b.harden_normals = False
    if sub:
        s = ob.modifiers.new("Smooth", 'SUBSURF')
        s.levels = s.render_levels = sub
    if outline:
        for _ in mats:
            me.materials.append(OUTL)
        so = ob.modifiers.new("Outline", 'SOLIDIFY')
        so.thickness, so.offset, so.use_flip_normals = outline, 1, True
        so.material_offset, so.use_rim = len(mats), False
    return ob


def add_box(bm, x0, x1, y0, y1, z0, z1, mi=0, taper=None):
    vs = []
    for z in (z0, z1):
        for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            if taper and z == z1:
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                x, y = cx + (x - cx) * taper[0], cy + (y - cy) * taper[1]
            vs.append(bm.verts.new((x, y, z)))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for q in f:
        bm.faces.new([vs[i] for i in q]).material_index = mi


def box(name, x0, x1, y0, y1, z0, z1, mat, outline=0.025, bevel=0.0, taper=None):
    bm = bmesh.new()
    add_box(bm, x0, x1, y0, y1, z0, z1, 0, taper)
    return new_obj(name, bm, [mat], outline, bevel=bevel)


def boxes(name, items, mats, outline=0.02, bevel=0.0):
    """items: (x0, x1, y0, y1, z0, z1, material index)."""
    bm = bmesh.new()
    for it in items:
        add_box(bm, *it)
    return new_obj(name, bm, mats, outline, bevel=bevel)


def blobs(name, items, mats, outline=0.02, subdiv=2):
    """items: (cx, cy, cz, rx, ry, rz, material index) ellipsoids, one mesh."""
    bm = bmesh.new()
    for cx, cy, cz, rx, ry, rz, mi in items:
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1)
        me = bpy.data.meshes.new("_tmp")
        for v in tmp.verts:
            n = 1 + random.uniform(-0.07, 0.07)
            v.co = Vector((cx + v.co.x * rx * n, cy + v.co.y * ry * n, cz + v.co.z * rz * n))
        tmp.to_mesh(me)
        tmp.free()
        off = len(bm.faces)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[off:]:
            f.material_index = mi
        bpy.data.meshes.remove(me)
    return new_obj(name, bm, mats, outline, smooth=True)


def cyl(name, c, r, depth, mat, outline=0.02, segs=24, axis='Z', r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return new_obj(name, bm, [mat], outline, smooth=True)


def window(name, x0, x1, z0, z1, y, cols=2, rows=1, frame=0.07, depth=0.12, mats=None):
    """Glass pane recessed behind a slim dark frame; the wall face is at y (front = -Y)."""
    mats = mats or [M["glass"], M["frame"], M["glass_lt"]]
    it = [(x0, x1, y - 0.01, y + 0.02, z0, z1, 0)]
    # little diagonal sheen strips
    w = x1 - x0
    for k in range(cols):
        cx = x0 + w * (k + 0.3) / cols
        it.append((cx, cx + w * 0.08 / cols, y - 0.012, y - 0.008, z0 + (z1 - z0) * 0.35, z1 - (z1 - z0) * 0.1, 2))
    f = frame
    it += [(x0 - f, x1 + f, y - depth, y, z1, z1 + f, 1), (x0 - f, x1 + f, y - depth, y, z0 - f, z0, 1),
           (x0 - f, x0, y - depth, y, z0, z1, 1), (x1, x1 + f, y - depth, y, z0, z1, 1)]
    for k in range(1, cols):
        x = x0 + w * k / cols
        it.append((x - f / 2, x + f / 2, y - depth * 0.6, y, z0, z1, 1))
    for k in range(1, rows):
        z = z0 + (z1 - z0) * k / rows
        it.append((x0, x1, y - depth * 0.6, y, z - f / 2, z + f / 2, 1))
    return boxes(name, it, mats, outline=0.012)


def stone_face(name, x0, x1, z0, z1, y, depth=0.05, side=False):
    """Stacked stone: random-length courses standing proud of a wall at y (or at x if side)."""
    it = []
    z = z0
    while z < z1 - 0.02:
        h = min(random.uniform(0.14, 0.26), z1 - z)
        x = x0
        while x < x1 - 0.02:
            w = min(random.uniform(0.35, 1.1), x1 - x)
            mi = random.choice((0, 0, 1, 2))
            if side:
                it.append((y - depth, y, x + 0.012, x + w - 0.012, z + 0.012, z + h - 0.012, mi))
            else:
                it.append((x + 0.012, x + w - 0.012, y - depth, y, z + 0.012, z + h - 0.012, mi))
            x += w
        z += h
    return boxes(name, it, [M["stone1"], M["stone2"], M["stone3"]], outline=0.006)


def grooves(name, x0, x1, z0, z1, y, step=0.24, mat="wood_dk", side=False):
    it = []
    z = z0 + step
    while z < z1 - 0.05:
        if side:
            it.append((y - 0.012, y, x0, x1, z, z + 0.03, 0))
        else:
            it.append((x0, x1, y - 0.012, y, z, z + 0.03, 0))
        z += step
    return boxes(name, it, [M[mat]], outline=0)


def vines(name, x0, x1, y, z_top, lmin, lmax, n, axis='X'):
    it = []
    for k in range(n):
        t = x0 + (x1 - x0) * (k + random.uniform(0.1, 0.9)) / n
        L = random.uniform(lmin, lmax)
        w = random.uniform(0.04, 0.08)
        mi = random.choice((0, 1))
        if axis == 'X':
            it.append((t, t + w, y - 0.03, y + 0.03, z_top - L, z_top, mi))
        else:
            it.append((y - 0.03, y + 0.03, t, t + w, z_top - L, z_top, mi))
    bm_items = it
    ob = boxes(name, bm_items, [M["vine"], M["plant"]], outline=0.004)
    # leaf tufts along the strands
    tufts = []
    for (a0, a1, b0, b1, c0, c1, mi) in it:
        z = c1 - random.uniform(0.0, 0.3)
        while z > c0 + 0.1:
            tufts.append(((a0 + a1) / 2 + random.uniform(-0.05, 0.05), (b0 + b1) / 2 - 0.04, z,
                          random.uniform(0.06, 0.11), 0.05, random.uniform(0.06, 0.1), random.choice((0, 1))))
            z -= random.uniform(0.18, 0.35)
    blobs(name + "_leaves", tufts, [M["leaf1"], M["leaf2"]], outline=0.004, subdiv=1)
    return ob


def shrubs(name, x0, x1, y0, y1, z, size=0.32, density=1.0):
    it = []
    x = x0 + size * 0.6
    while x < x1 - size * 0.4:
        for yy in ((y0 + y1) / 2,) if (y1 - y0) < size * 2.2 else (y0 + size * 0.7, y1 - size * 0.7):
            r = size * random.uniform(0.8, 1.15)
            it.append((x + random.uniform(-0.05, 0.05), yy, z + r * 0.55, r, r * 0.9, r * 0.75, random.choice((0, 1))))
        x += size * random.uniform(1.0, 1.35) / density
    return blobs(name, it, [M["plant"], M["plant2"]], outline=0.012)


def planter(name, x0, x1, y0, y1, z0, h=0.45, mat="white", plants=True, size=0.3):
    box(name, x0, x1, y0, y1, z0, z0 + h, M[mat], outline=0.02)
    box(name + "_soil", x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z0 + h - 0.06, z0 + h + 0.005, M["soil"], outline=0)
    if plants:
        shrubs(name + "_plants", x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z0 + h - 0.05, size)


def glass_rail(name, x0, x1, y0, y1, z0, h=0.95):
    it = [(x0, x1, y0, y1, z0, z0 + h, 0), (x0, x1, y0 - 0.02, y1 + 0.02, z0 + h, z0 + h + 0.04, 1)]
    ob = boxes(name, it, [M["rail"], M["frame"]], outline=0.006)
    return ob


def pot_plant(name, x, y, z, r=0.22, h=0.45, leaf=0.42):
    cyl(name + "_pot", (x, y, z + h / 2), r, h, M["pot"], r2=r * 0.8, outline=0.012)
    it = []
    for k in range(7):
        a = k / 7 * math.tau + random.uniform(-0.2, 0.2)
        rr = leaf * random.uniform(0.25, 0.5)
        it.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z + h + leaf * random.uniform(0.35, 0.8),
                   leaf * 0.32, leaf * 0.32, leaf * 0.45, random.choice((0, 1))))
    it.append((x, y, z + h + leaf * 0.9, leaf * 0.35, leaf * 0.35, leaf * 0.5, 1))
    blobs(name + "_leaves", it, [M["plant"], M["plant2"]], outline=0.008)


def tree(name, x, y, s=1.0, trunk_h=3.2):
    cyl(name + "_trunk", (x, y, trunk_h / 2), 0.22 * s, trunk_h, M["trunk"], r2=0.15 * s, outline=0.02)
    it = []
    for k in range(9):
        a = random.uniform(0, math.tau)
        d = random.uniform(0.4, 1.6) * s
        r = random.uniform(1.0, 1.6) * s
        it.append((x + math.cos(a) * d, y + math.sin(a) * d, trunk_h + random.uniform(0.3, 1.8) * s,
                   r, r, r * 0.85, random.choice((0, 1))))
    blobs(name + "_crown", it, [M["leaf1"], M["leaf2"]], outline=0.03)




# ---------------------------------------------------------------- pieces (multi-material objects)
class P:
    """One furniture object made of boxes, cylinders, blobs and beams in local
    coordinates (origin on the floor at the footprint centre, front = -Y)."""

    def __init__(s, name):
        s.name, s.bm, s.mats = name, bmesh.new(), []

    def mi(s, k):
        m = M[k]
        if m not in s.mats:
            s.mats.append(m)
        return s.mats.index(m)

    def _merge(s, tmp, k, smooth, xf=None):
        if xf is not None:
            bmesh.ops.transform(tmp, matrix=xf, verts=tmp.verts)
        me = bpy.data.meshes.new("_t")
        tmp.to_mesh(me)
        tmp.free()
        off = len(s.bm.faces)
        s.bm.from_mesh(me)
        s.bm.faces.ensure_lookup_table()
        i = s.mi(k)
        for f in s.bm.faces[off:]:
            f.material_index = i
            f.smooth = smooth
        bpy.data.meshes.remove(me)

    def box(s, x0, x1, y0, y1, z0, z1, k, taper=None, xf=None):
        t = bmesh.new()
        add_box(t, x0, x1, y0, y1, z0, z1, 0, taper)
        s._merge(t, k, False, xf)

    def cyl(s, c, r, h, k, axis='Z', segs=20, r2=None, xf=None):
        t = bmesh.new()
        bmesh.ops.create_cone(t, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
        if axis == 'X':
            bmesh.ops.rotate(t, verts=t.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
        elif axis == 'Y':
            bmesh.ops.rotate(t, verts=t.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
        bmesh.ops.translate(t, vec=Vector(c), verts=t.verts)
        s._merge(t, k, True, xf)

    def blob(s, c, r, k, subdiv=2):
        t = bmesh.new()
        bmesh.ops.create_icosphere(t, subdivisions=subdiv, radius=1)
        for v in t.verts:
            v.co = Vector((c[0] + v.co.x * r[0], c[1] + v.co.y * r[1], c[2] + v.co.z * r[2]))
        s._merge(t, k, True)

    def beam(s, p0, p1, w, h, k):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        t = bmesh.new()
        bmesh.ops.create_cube(t, size=1)
        xf = (Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat('X', 'Z').to_matrix().to_4x4()
              @ Matrix.Diagonal((d.length, w, h, 1)))
        s._merge(t, k, False, xf)

    def done(s, loc=(0, 0, 0), rot=0.0, outline=0.012):
        ob = new_obj(s.name, s.bm, s.mats, outline, smooth=None)
        ob.location = loc
        ob.rotation_euler.z = math.radians(rot)
        return ob




# ---------------------------------------------------------------- node helpers for patterned toon materials
def _sock(nt, v):
    if isinstance(v, (int, float)):
        n = nt.nodes.new('ShaderNodeValue')
        n.outputs[0].default_value = v
        return n.outputs[0]
    return v


def nmath(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    nt.links.new(_sock(nt, a), n.inputs[0])
    if b is not None:
        nt.links.new(_sock(nt, b), n.inputs[1])
    return n.outputs[0]


def rgb(nt, hexcol):
    n = nt.nodes.new('ShaderNodeRGB')
    n.outputs[0].default_value = lin(hexcol) + [1]
    return n.outputs[0]


def mix(nt, fac, a, b, blend='MIX'):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    ins = [s for s in n.inputs if s.type == 'RGBA']
    nt.links.new(_sock(nt, fac), n.inputs[0])
    nt.links.new(a, ins[0])
    nt.links.new(b, ins[1])
    return [s for s in n.outputs if s.type == 'RGBA'][0]


def toon_shader(name, color_fn, ks=(0.62, 0.84, 1.0)):
    """Toon material whose base colour comes from color_fn(node_tree) -> colour socket."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    _toon_finish(nt, _toon_value(nt, ks), color_fn(nt))
    return m


def facade(name, wall, glass, bay=3.2, win=0.62, floor_h=3.6, sill=0.3, head=0.85, frame=None):
    """Window grid in object space on every vertical face; roofs stay wall-coloured."""
    def fn(nt):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sx.inputs[0])
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        sn = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Normal'], sn.inputs[0])
        u = nmath(nt, 'FRACT', nmath(nt, 'DIVIDE', nmath(nt, 'ADD', sx.outputs[0], sx.outputs[1]), bay))
        h_ok = nmath(nt, 'LESS_THAN', u, win)
        v = nmath(nt, 'FRACT', nmath(nt, 'DIVIDE', sx.outputs[2], floor_h))
        v_ok = nmath(nt, 'MULTIPLY', nmath(nt, 'GREATER_THAN', v, sill), nmath(nt, 'LESS_THAN', v, head))
        side = nmath(nt, 'LESS_THAN', nmath(nt, 'ABSOLUTE', sn.outputs[2]), 0.5)
        mask = nmath(nt, 'MULTIPLY', nmath(nt, 'MULTIPLY', h_ok, v_ok), side)
        return mix(nt, mask, rgb(nt, wall), rgb(nt, glass))
    m = toon_shader(name, fn)
    m.diffuse_color = lin(wall) + [1]
    return m


def striped(name, base, line, rules):
    """UV-patterned surface (roads, runways, parking). u = metres along, v = 0..1 across.
    rules: list of (kind, a, b, c): ('band', v0, v1, dash) band across v (dash = period in m, 0 = solid)."""
    def fn(nt):
        uvn = nt.nodes.new('ShaderNodeUVMap')
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(uvn.outputs[0], sx.inputs[0])
        u, v = sx.outputs[0], sx.outputs[1]
        total = None
        for rule in rules:
            kind, v0, v1, dash = rule[:4]
            duty = rule[4] if len(rule) > 4 else 0.5
            inb = nmath(nt, 'MULTIPLY', nmath(nt, 'GREATER_THAN', v, v0), nmath(nt, 'LESS_THAN', v, v1))
            if dash:
                d = nmath(nt, 'LESS_THAN', nmath(nt, 'FRACT', nmath(nt, 'DIVIDE', u, dash)), duty)
                inb = nmath(nt, 'MULTIPLY', inb, d)
            total = inb if total is None else nmath(nt, 'MAXIMUM', total, inb)
        return mix(nt, total, rgb(nt, base), rgb(nt, line))
    m = toon_shader(name, fn)
    m.diffuse_color = lin(base) + [1]
    return m


def strip(name, pts, width, mat, z=0.0, outline=0.0):
    """Flat ribbon along a polyline (roads, runways) with UV u = metres along, v = 0..1 across."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    pts = [Vector((p[0], p[1], z)) for p in pts]
    L, R, U = [], [], []
    acc = 0.0
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1] - p).normalized()
            n = Vector((-d.y, d.x, 0))
        elif i == len(pts) - 1:
            d = (p - pts[i - 1]).normalized()
            n = Vector((-d.y, d.x, 0))
        else:
            d0 = (p - pts[i - 1]).normalized()
            d1 = (pts[i + 1] - p).normalized()
            n0, n1 = Vector((-d0.y, d0.x, 0)), Vector((-d1.y, d1.x, 0))
            n = (n0 + n1).normalized()
            n = n / max(0.3, n.dot(n0))
        if i:
            acc += (p - pts[i - 1]).length
        L.append(bm.verts.new(p + n * width / 2))
        R.append(bm.verts.new(p - n * width / 2))
        U.append(acc)
    for i in range(len(pts) - 1):
        f = bm.faces.new((R[i], R[i + 1], L[i + 1], L[i]))
        for lp, (uu, vv) in zip(f.loops, ((U[i], 0), (U[i + 1], 0), (U[i + 1], 1), (U[i], 1))):
            lp[uv].uv = (uu, vv)
    return new_obj(name, bm, [mat], outline, smooth=False)


def label(name, text, loc, rot_z=0.0, size=4.0, mat=None, depth=0.3, upright=True):
    """Extruded text sign (local text faces -Y when upright)."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = depth
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu)
    TARGET[0].objects.link(ob)
    if PARENT[0]:
        ob.parent = PARENT[0]
    if mat:
        cu.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = (math_mod.radians(90) if upright else 0, 0, math_mod.radians(rot_z))
    return ob


# ---------------------------------------------------------------- consolidation
def consolidate(coll, skip_prefixes=(), name=None):
    """Merge the static mesh objects of a collection into one object per outline thickness.

    EEVEE (Blender 5.3) silently stops drawing some surfaces when a scene has a few hundred
    separately outlined objects (the inverted-hull shell then shows through as black), so big
    sets keep their static pieces merged. Objects that are hidden, animated, constrained,
    parented-to, named in skip_prefixes, or carry modifiers other than the outline stay as
    they are. Transforms are applied into the merged mesh (parented to PARENT[0])."""
    groups = {}
    for o in list(coll.objects):
        if (o.type != 'MESH' or o.hide_render or o.children or o.animation_data or o.constraints
                or any(o.name.startswith(p) for p in skip_prefixes)):
            continue
        if any(m.type != 'SOLIDIFY' for m in o.modifiers):
            continue
        so = [m for m in o.modifiers if m.type == 'SOLIDIFY']
        th = round(so[0].thickness, 4) if so else 0.0
        groups.setdefault(th, []).append(o)
    made = []
    for th, objs in groups.items():
        if len(objs) < 2:
            continue
        bm = bmesh.new()
        mats = []
        for o in objs:
            me = o.data
            tmp = bmesh.new()
            tmp.from_mesh(me)
            for f in tmp.faces:
                m = me.materials[f.material_index] if f.material_index < len(me.materials) else None
                if m is None or m == OUTL:
                    m = me.materials[0] if me.materials else None
                if m not in mats:
                    mats.append(m)
                f.material_index = mats.index(m)
            bmesh.ops.transform(tmp, matrix=o.matrix_basis, verts=tmp.verts)   # matrix_local may be stale before a depsgraph update
            tm = bpy.data.meshes.new("_c")
            tmp.to_mesh(tm)
            tmp.free()
            bm.from_mesh(tm)
            bpy.data.meshes.remove(tm)
        nm = "%s.merged_%s" % (name or coll.name, str(th).replace(".", "_"))
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        if PARENT[0]:
            ob.parent = PARENT[0]
        if th:
            for _ in mats:
                me.materials.append(OUTL)
            so = ob.modifiers.new("Outline", 'SOLIDIFY')
            so.thickness, so.offset, so.use_flip_normals = th, 1, True
            so.material_offset, so.use_rim = len(mats), False
        for o in objs:
            d = o.data
            bpy.data.objects.remove(o)
            if d.users == 0:
                bpy.data.meshes.remove(d)
        made.append(ob)
    return made

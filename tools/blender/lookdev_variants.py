"""Render-time look development: time of day and weather variants of a city camera.

    blender -b blender/sets/city_v009.blend --python tools/blender/lookdev_variants.py -- \
        <variant> <camera> <out.png> [width height frame]

variant: night | morning | rain | snow | highland   (highland = morning light, snow only on the peaks)

Nothing is saved: the script edits materials, world, lights and adds weather geometry, then renders.
  every variant  window grids broken up per window (tints, drawn blinds; lit windows at night),
                 shadow / light tints in every toon material, a gradient sky, real atmospheric
                 haze (world volume) for depth
  night          deep blue moonlight, warm lit windows, apron floodlight masts with pools of light,
                 glowing runway and taxiway lights, wet reflection streaks under the lights
  morning        low sun from the east, long shadows, warm light, light haze
  rain           dark wet pavement, puddles, rain streaks only near the camera, light reflections,
                 grey sky and heavier haze
  snow           snow on roofs, verges, trees and peaks, slushy service roads, cleared runways and
                 taxiways, muted sky, falling snow near the camera
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mansion_kit as K
importlib.reload(K)
from mansion_kit import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VAR = argv[0] if argv else "morning"
CAM = argv[1] if len(argv) > 1 else "CT_cam_ep_airport_hero"
OUTP = argv[2] if len(argv) > 2 else "//lookdev.png"
W, H = (int(argv[3]), int(argv[4])) if len(argv) > 4 else (1920, 1080)
FRAME = int(argv[5]) if len(argv) > 5 else 300
random.seed(42)
S = bpy.context.scene
RIG = bpy.data.objects["CT.root"]
K.PARENT[0] = RIG
LV = bpy.data.collections.new("CT_Lookdev")
bpy.data.collections["City"].children.link(LV)
use(LV)
for m in bpy.data.materials:
    if m.name.startswith("CT_"):
        M[m.name[3:]] = m

P_ = {  # per variant: shadow tint, light tint, sky horizon, sky zenith, haze colour, haze per metre, sun
    "night":    dict(sh=(0.22, 0.27, 0.48), li=(0.44, 0.5, 0.76), hz="#2a3a63", ze="#060a18", fog="#1f2b4a", dens=0.00022,
                     sun=(0.5, "#a9bde6", -0.55, 0.62, -0.56)),
    "morning":  dict(sh=(0.80, 0.84, 1.0), li=(1.12, 0.99, 0.84), hz="#f8d2a8", ze="#7fa8d6", fog="#f3d8bc", dens=0.00013,
                     sun=(4.0, "#ffd6a6", -0.94, 0.12, -0.32)),
    "rain":     dict(sh=(0.62, 0.66, 0.74), li=(0.78, 0.82, 0.88), hz="#9aa3ad", ze="#5d6670", fog="#9ba4ae", dens=0.0006,
                     sun=(1.4, "#c9d3de", 0.3, 0.5, -0.81)),
    "snow":     dict(sh=(0.82, 0.87, 0.98), li=(1.0, 1.0, 1.03), hz="#dfe4ea", ze="#aeb8c4", fog="#e4e9ef", dens=0.0005,
                     sun=(1.8, "#eef3fa", 0.4, 0.5, -0.77)),
    "highland": dict(sh=(0.80, 0.84, 1.0), li=(1.1, 1.0, 0.88), hz="#f3dcc0", ze="#86b0da", fog="#ece2d6", dens=0.00012,
                     sun=(3.8, "#ffe0b8", -0.9, 0.2, -0.38)),
}[VAR]
WET = VAR in ("rain", "night")
SNOW = VAR == "snow"
GROUND = ("asphalt", "apron", "apron2", "paving", "pave", "drive", "concrete2", "helipad", "h_floor")
GRASS = ("grass", "grass2", "lawn2", "fairway", "mound", "lawn")
ROADS_PREFIX = ("CT_r_",)


def lin3(h):
    return lin(h)


# ================================================================ facades with per-window variety
FAC = {"glass_blue": ("#dfe7ec", "#5f87a8", 3.0, 0.86, 3.8, 0.12, 0.92), "glass_teal": ("#e4ece9", "#3f8f92", 2.6, 0.84, 3.8, 0.1, 0.94),
       "glass_dark": ("#c9ced3", "#34495c", 3.4, 0.8, 4.0, 0.1, 0.92), "office": ("#f1ede4", "#4f6b80", 3.2, 0.6, 3.6, 0.28, 0.82),
       "stone": ("#d8c7a8", "#3f4f5c", 3.0, 0.5, 3.8, 0.3, 0.8), "brick": ("#b5654a", "#3f4f5c", 3.0, 0.5, 3.2, 0.32, 0.8),
       "apart": ("#f0d9b5", "#4a6274", 3.6, 0.45, 3.0, 0.3, 0.78), "apart2": ("#cfe0e8", "#4a6274", 3.6, 0.45, 3.0, 0.3, 0.78),
       "hospital": ("#f7f7f4", "#4f9aa8", 3.0, 0.6, 3.8, 0.25, 0.85), "school": ("#d77a55", "#f4efe2", 3.4, 0.55, 3.6, 0.3, 0.8),
       "school2": ("#f1ede4", "#3f6fa8", 3.4, 0.55, 3.6, 0.3, 0.82), "terminal": ("#e8eef2", "#6aa3c8", 4.0, 0.9, 6.0, 0.05, 0.95),
       "shop": ("#f4efe2", "#5f87a8", 4.0, 0.8, 5.0, 0.08, 0.7), "hangar": ("#cfd4d8", "#9aa3aa", 1.2, 0.08, 50.0, 0.0, 1.0)}


def facade_variety(name, wall, glass, bay, win, floor_h, sill, head):
    hold = {}

    def fn(nt):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sx.inputs[0])
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        sn = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Normal'], sn.inputs[0])
        ur = nmath(nt, 'DIVIDE', nmath(nt, 'ADD', sx.outputs[0], sx.outputs[1]), bay)
        vr = nmath(nt, 'DIVIDE', sx.outputs[2], floor_h)
        h_ok = nmath(nt, 'LESS_THAN', nmath(nt, 'FRACT', ur), win)
        v = nmath(nt, 'FRACT', vr)
        v_ok = nmath(nt, 'MULTIPLY', nmath(nt, 'GREATER_THAN', v, sill), nmath(nt, 'LESS_THAN', v, head))
        side = nmath(nt, 'LESS_THAN', nmath(nt, 'ABSOLUTE', sn.outputs[2]), 0.5)
        mask = nmath(nt, 'MULTIPLY', nmath(nt, 'MULTIPLY', h_ok, v_ok), side)
        cxyz = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(nmath(nt, 'FLOOR', ur), cxyz.inputs[0])
        nt.links.new(nmath(nt, 'FLOOR', vr), cxyz.inputs[1])
        cxyz.inputs[2].default_value = (sum(map(ord, name)) % 97) * 0.37
        wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
        wn.noise_dimensions = '3D'
        nt.links.new(cxyz.outputs[0], wn.inputs['Vector'])
        r = wn.outputs['Value']
        g = rgb(nt, glass)
        gd = mix(nt, 0.45, g, rgb(nt, "#1a2430"))
        gl = mix(nt, 0.5, g, rgb(nt, "#d7e8f2"))
        blind = rgb(nt, "#e9e1cf")
        col = mix(nt, nmath(nt, 'MULTIPLY', nmath(nt, 'GREATER_THAN', r, 0.12), nmath(nt, 'LESS_THAN', r, 0.32)), g, gd)
        col = mix(nt, nmath(nt, 'GREATER_THAN', r, 0.86), col, gl)
        col = mix(nt, nmath(nt, 'LESS_THAN', r, 0.12), col, blind)
        out = mix(nt, mask, rgb(nt, wall), col)
        if SNOW:
            up = nmath(nt, 'GREATER_THAN', sn.outputs[2], 0.5)
            out = mix(nt, up, out, rgb(nt, "#f4f7fb"))
        hold["lit"] = nmath(nt, 'MULTIPLY', mask, nmath(nt, 'GREATER_THAN', r, 0.42))
        hold["nt"] = nt
        return out
    m = toon_shader(name, fn)
    if VAR == "night":                                     # warm lit windows on top of the toon colour
        nt = hold["nt"]
        em0 = [n for n in nt.nodes if n.type == 'EMISSION'][0]
        outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
        e2 = nt.nodes.new('ShaderNodeEmission')
        e2.inputs[0].default_value = lin("#ffcf86") + [1]
        nt.links.new(nmath(nt, 'MULTIPLY', hold["lit"], 2.4), e2.inputs[1])
        add = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(em0.outputs[0], add.inputs[0])
        nt.links.new(e2.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], outn.inputs[0])
    return m


for k, args in FAC.items():
    facade_variety("CT_f_" + k, *args)


# ================================================================ shadow / light tint (and wet / snow) on every toon material
def is_toon(m):
    if not m or not m.use_nodes or not m.node_tree or m.library:
        return None
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.blend_type == 'MULTIPLY' and n.data_type == 'RGBA':
            outs = [s for s in n.outputs if s.type == 'RGBA'][0]
            if any(l.to_node.type == 'EMISSION' for l in outs.links):
                return n
    return None


def patch(m):
    mx = is_toon(m)
    if mx is None:
        return
    nt = m.node_tree
    ins = [s for s in mx.inputs if s.type == 'RGBA']
    val_in, col_in = ins[0], ins[1]
    out = [s for s in mx.outputs if s.type == 'RGBA'][0]
    em = [l.to_node for l in out.links if l.to_node.type == 'EMISSION'][0]
    key = m.name[3:] if m.name.startswith("CT_") else m.name
    # base colour adjustments
    base = col_in.links[0].from_socket if col_in.is_linked else rgb(nt, "#000000")
    if not col_in.is_linked:
        c = col_in.default_value
        b = nt.nodes.new('ShaderNodeRGB')
        b.outputs[0].default_value = (c[0], c[1], c[2], 1)
        base = b.outputs[0]
    is_ground = key in GROUND or m.name.startswith(ROADS_PREFIX)
    if WET and is_ground:
        base = mix(nt, 1.0, base, rgb(nt, "#8c96a6"), 'MULTIPLY')
    if SNOW:
        if key in GRASS:
            base = rgb(nt, "#eef3f8")
        elif key in ("mountain", "mountain2", "snow"):
            base = mix(nt, 0.85, base, rgb(nt, "#f4f7fb"))
        elif m.name.startswith(ROADS_PREFIX) and ("runway" in key or "taxi" in key or "highway" in key):
            pass                                                    # cleared
        elif is_ground:
            base = mix(nt, 0.35, base, rgb(nt, "#a7adb5"))         # slush
        else:
            geo = nt.nodes.new('ShaderNodeNewGeometry')
            sn = nt.nodes.new('ShaderNodeSeparateXYZ')
            nt.links.new(geo.outputs['Normal'], sn.inputs[0])
            base = mix(nt, nmath(nt, 'GREATER_THAN', sn.outputs[2], 0.6), base, rgb(nt, "#f2f6fa"))
    if VAR == "highland" and key in ("mountain", "mountain2", "snow"):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sp = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sp.inputs[0])
        base = mix(nt, nmath(nt, 'GREATER_THAN', sp.outputs[2], 900.0), base, rgb(nt, "#f4f7fb"))
    nt.links.new(base, col_in)
    # tint by the toon light step: shadow tint .. light tint
    v = val_in.links[0].from_socket
    f = nmath(nt, 'DIVIDE', nmath(nt, 'SUBTRACT', v, 0.62), 0.38, clamp=True)
    sh = nt.nodes.new('ShaderNodeRGB'); sh.outputs[0].default_value = tuple(P_["sh"]) + (1,)
    li = nt.nodes.new('ShaderNodeRGB'); li.outputs[0].default_value = tuple(P_["li"]) + (1,)
    tint = mix(nt, f, sh.outputs[0], li.outputs[0])
    if WET and is_ground:
        tint = mix(nt, 1.0, tint, rgb(nt, "#b8bcc4"), 'MULTIPLY')
    final = mix(nt, 1.0, out, tint, 'MULTIPLY')
    cdn = nt.nodes.new('ShaderNodeCameraData')
    keep = nmath(nt, 'EXPONENT', nmath(nt, 'MULTIPLY', cdn.outputs['View Z Depth'], -P_["dens"] / 0.62))
    final = mix(nt, keep, rgb(nt, P_["fog"]), final)
    nt.links.new(final, em.inputs[0])


for m in list(bpy.data.materials):
    patch(m)
# outlines a touch softer and cooler at night
if VAR == "night" and bpy.data.materials.get("MN_outline"):
    for n in bpy.data.materials["MN_outline"].node_tree.nodes:
        if n.type == 'EMISSION':
            n.inputs[0].default_value = lin("#05070d") + [1]

# ================================================================ world: gradient sky + haze
w = bpy.data.worlds.new("CT_world_" + VAR)
w.use_nodes = True
nt = w.node_tree
nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeTexCoord')
sz = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Generated'], sz.inputs[0])
fac = nmath(nt, 'MULTIPLY', nmath(nt, 'MAXIMUM', sz.outputs[2], 0.0), 2.2, clamp=True)
sky = mix(nt, fac, rgb(nt, P_["hz"]), rgb(nt, P_["ze"]))
bg = nt.nodes.new('ShaderNodeBackground')
nt.links.new(sky, bg.inputs[0])
bg.inputs[1].default_value = 1.0
wo = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(bg.outputs[0], wo.inputs['Surface'])
S.world = w

# ================================================================ sun
sun = bpy.data.objects.get("CT_sun")
en, col, dx, dy, dz = P_["sun"]
sun.data.energy = en
sun.data.color = lin(col)
sun.rotation_euler = (-Vector((dx, dy, dz)).normalized()).to_track_quat('Z', 'Y').to_euler()
mi = bpy.data.objects.get("CT.mansion")
if mi:
    mi.hide_render = True                                  # its own sun would light the scene


# ================================================================ camera frustum helpers (root space)
cam = bpy.data.objects[CAM]
S.camera = cam
S.frame_set(FRAME)
bpy.context.view_layer.update()
to_root = RIG.matrix_world.inverted()
cw = cam.matrix_world
fov = cam.data.angle


def frustum_point(dmin, dmax, ground=False):
    d = random.uniform(dmin, dmax)
    x = random.uniform(-1, 1) * math.tan(fov / 2) * d
    y = random.uniform(-0.56, 0.56) * math.tan(fov / 2) * d
    p = to_root @ (cw @ Vector((x, y, -d)))
    if ground:
        p.z = 0.045
    return p


def glow_mat(name, hexcol, strength, alpha=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = lin(hexcol) + [1]
    e.inputs[1].default_value = strength
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    if alpha is None:
        nt.links.new(e.outputs[0], o.inputs[0])
    else:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mx = nt.nodes.new('ShaderNodeMixShader')
        mx.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(e.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], o.inputs[0])
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = 'BLENDED'
    return m


M["lk_glow"] = glow_mat("CT_lk_glow", "#ffd9a0", 6.0)
M["lk_refl"] = glow_mat("CT_lk_refl", "#ffc878", 0.7, alpha=0.22)
M["lk_refl_cool"] = glow_mat("CT_lk_refl_cool", "#cfe2f2", 0.6, alpha=0.25)
M["lk_rain"] = glow_mat("CT_lk_rain", "#dfe8f0", 0.9, alpha=0.35)
M["lk_snow"] = glow_mat("CT_lk_snow", "#ffffff", 1.4)
M["lk_puddle"] = toon("CT_lk_puddle", "#4c5a6b", ks=(0.9, 0.95, 1.0))
M["lk_mast"] = toon("CT_lk_mast", "#8f959c")

# ================================================================ apron floodlight masts (night, rain)
MASTS = []
for d, side in ((70, -0.62), (130, -0.5), (210, -0.42), (320, -0.36), (170, 0.05), (280, 0.12)):
    q = to_root @ (cw @ Vector((side * math.tan(fov / 2) * d, 0, -d)))
    MASTS.append((q.x, q.y))
if VAR in ("night", "rain"):
    mp = P("CT.lk_masts")
    for (x, y) in MASTS:
        mp.box(x - 0.4, x + 0.4, y - 0.4, y + 0.4, 0.0, 26.0, "lk_mast")
        mp.box(x - 3.0, x + 3.0, y - 0.6, y + 0.6, 26.0, 26.6, "lk_mast")
        for k in range(4):
            mp.box(x - 2.8 + k * 1.5, x - 1.6 + k * 1.5, y - 0.2, y + 0.9, 25.4, 26.0, "lk_glow")
    mp.done(outline=0.03)
    for i, (x, y) in enumerate(MASTS):
        ld = bpy.data.lights.new("CT_lk_flood%d" % i, 'SPOT')
        ld.energy = 160000 if VAR == "night" else 40000
        ld.color = lin("#ffd6a0")
        ld.spot_size = math.radians(125)
        ld.spot_blend = 0.6
        lo = bpy.data.objects.new("CT_lk_flood%d" % i, ld)
        LV.objects.link(lo)
        lo.parent = RIG
        lo.location = (x, y + 2.0, 25.5)
        lo.rotation_euler = (0, 0, 0)
    # wet reflection streaks under the bright things, stretched towards the camera
    cpos = to_root @ cw.translation
    rf = P("CT.lk_reflections")
    srcs = [(x, y) for (x, y) in MASTS] + [(x, -2703.0) for x in range(2810, 3800, 25)]
    for (x, y) in srcs:
        d = Vector((cpos.x - x, cpos.y - y)).normalized()
        L = 28.0 if (x, y) in MASTS else 9.0
        a = Vector((x, y, 0.05)) + d.to_3d() * 2.5
        b = a + d.to_3d() * L
        rf.beam(a, b, 0.9 if (x, y) in MASTS else 0.6, 0.01, "lk_refl" if VAR == "night" else "lk_refl_cool")
    rf.done(outline=0.0)

# ================================================================ rain: puddles + streaks near the camera
if VAR == "rain":
    pd = P("CT.lk_puddles")
    for k in range(55):
        p = frustum_point(8, 220, ground=True)
        r = random.uniform(0.8, 3.0)
        pd.blob((p.x, p.y, 0.04), (r, r * random.uniform(0.4, 0.8), 0.01), "lk_puddle", subdiv=2)
        pd.blob((p.x + r * 0.2, p.y + r * 0.1, 0.05), (r * 0.5, r * 0.18, 0.006), "lk_refl_cool", subdiv=1)
    pd.done(outline=0.0)
    rn = P("CT.lk_rain")
    wind = Vector((0.15, 0.05, -1.0)).normalized()
    for k in range(1100):
        p = frustum_point(4, 45)
        Lr = random.uniform(0.35, 0.8)
        rn.beam(p, p + wind * Lr, 0.006, 0.006, "lk_rain")
    rn.done(outline=0.0)

# ================================================================ snow: falling flakes near the camera
if VAR == "snow":
    sn = P("CT.lk_snowfall")
    for k in range(2400):
        p = frustum_point(4, 60)
        r = random.uniform(0.012, 0.03)
        sn.blob(p, (r, r, r), "lk_snow", subdiv=1)
    sn.done(outline=0.0)

# ================================================================ render
S.render.resolution_x, S.render.resolution_y, S.render.resolution_percentage = W, H, 100
layer = S.view_layers[0].name
for vl in S.view_layers:
    vl.use = (vl.name == layer)
S.render.filepath = OUTP
bpy.ops.render.render(write_still=True, layer=layer)

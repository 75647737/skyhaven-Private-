"""Build Ace Sterling as a realistic human avatar with MPFB2 (all assets CC0).

Run:  blender -b --python build_ace.py -- <out.blend>
Change body size, eyes, hair or clothes by editing ACE below and re-running.
"""
import bpy, sys, json, os
from bl_ext.user_default.mpfb.services import HumanService, FaceService

OUT = sys.argv[sys.argv.index("--") + 1]

ACE = {
    "name": "Ace",
    "phenotype": {               # MakeHuman macros, 0..1
        "gender": 1.0,           # male
        "age": 0.54,             # ~30 years (0.5 = 25, 1.0 = 90)
        "height": 0.665,          # tuned to ~1.80 m
        "muscle": 0.62,          # broad build
        "weight": 0.58,
        "proportions": 0.6,
        "firmness": 0.5, "cupsize": 0.5,
        "race": {"african": 0.62, "caucasian": 0.26, "asian": 0.12},  # warm brown
    },
    "skin_mhmat": "young_african_male/young_african_male.mhmat",
    "skin_material_type": "ENHANCED_SSS",
    "eyes": "high-poly/high-poly.mhclo",
    "eyes_material_type": "MAKESKIN",
    "eyebrows": "eyebrow001/eyebrow001.mhclo",
    "eyelashes": "eyelashes01/eyelashes01.mhclo",
    "teeth": "teeth_base/teeth_base.mhclo",
    "tongue": "tongue01/tongue01.mhclo",
    "hair": "short04/short04.mhclo",
    "clothes": [
        "toigo_fisherman_sweater/toigo_fisherman_sweater.mhclo",
        "toigo_wool_pants/toigo_wool_pants.mhclo",
        "shoes02/shoes02.mhclo",
    ],
    "rig": "default",
    "targets": [                     # face tweaks on top of the macros
        {"target": "l-eye-scale-incr", "value": 0.35},   # bigger, friendlier eyes
        {"target": "r-eye-scale-incr", "value": 0.35},
    ],
    "expressions": [], "makeup": [], "proxy": "",
    "color_adjustments": {}, "skin_material_settings": {}, "eyes_material_settings": {},
}

# Optional quick overrides for tests, e.g. ACE_OVERRIDE='{"hair": "short04/short04.mhclo"}'
ACE.update(json.loads(os.environ.get("ACE_OVERRIDE", "{}")))

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)

settings = HumanService.get_default_deserialization_settings()
settings["subdiv_levels"] = 1
basemesh = HumanService.deserialize_from_dict(ACE, settings)

# Face controls: 52 ARKit-style faceunits (blinks, brows, smiles...) + Microsoft visemes for lip-sync
FaceService.load_targets(basemesh, load_microsoft_visemes=True, load_meta_visemes=False, load_arkit_faceunits=True)

# ---------------------------------------------------------------- look: blueprint palette
import numpy as np

PALETTE = {                      # blueprint section 3 (sRGB hex)
    "skin": "b29567",          # calibrated so the RENDERED skin lands on ~#b28362 (blueprint #c68a5e read orange on realistic skin)
    "hair": "2a1a12",
    "toigo_fisherman_sweater": "5b7a99", "toigo_wool_pants": "8f7f62", "shoes02": "3a2418",
}
SKIN_ROUGHNESS, SKIN_CLEARCOAT, SKIN_SSS = 0.55, 0.03, 0.06  # less waxy / less orange than MPFB defaults (0.45 / 0.10 / 0.2)


def hex_lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def image_stats(img):
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    px = px[(px[:, 3] > 0.5) & (px[:, :3].sum(1) > 0.03)]      # ignore empty/transparent UV space
    rgb = px[:, :3].mean(0)
    lum = float((px[:, :3] @ np.array([0.2126, 0.7152, 0.0722])).mean())
    return rgb, lum


def recolor_texture(obj, hex_color):
    """Clothes/hair: keep the texture's light-and-dark detail, replace its colour."""
    m = obj.material_slots[0].material
    nt = m.node_tree
    tex = nt.nodes["diffuseTexture"]
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = bsdf.inputs["Base Color"].links[0].from_socket
    _, lum = image_stats(tex.image)
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    gain = nt.nodes.new("ShaderNodeMath"); gain.operation = "MULTIPLY"; gain.inputs[1].default_value = 1.0 / max(lum, 1e-3)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(src, bw.inputs[0]); nt.links.new(bw.outputs[0], gain.inputs[0])
    nt.links.new(gain.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (*hex_lin(hex_color), 1)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])


def recolor_skin(body, hex_color):
    """Skin: per-channel gain so the texture's average matches the target tone (keeps pores/variation)."""
    m = body.material_slots[0].material
    grp_node = next(n for n in m.node_tree.nodes if n.type == "GROUP")
    g = grp_node.node_tree
    bsdf = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED")
    src = bsdf.inputs["Base Color"].links[0].from_socket
    rgb, _ = image_stats(g.nodes["DiffuseTexture"].image)
    target = hex_lin(hex_color)
    mix = g.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt_link = g.links
    nt_link.new(src, mix.inputs[6])
    mix.inputs[7].default_value = (*[t / max(c, 1e-3) for t, c in zip(target, rgb)], 1)
    nt_link.new(mix.outputs[2], bsdf.inputs["Base Color"])
    grp_node.inputs["Roughness"].default_value = SKIN_ROUGHNESS
    grp_node.inputs["Clearcoat"].default_value = SKIN_CLEARCOAT
    grp_node.inputs["SSS strength"].default_value = SKIN_SSS


def tune_eyes(eyes):
    """Iris hue nudged from reddish toward warm brown, slightly darker."""
    nt = eyes.material_slots[0].material.node_tree
    tex = nt.nodes["diffuseTexture"]
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Hue"].default_value = 0.53; hs.inputs["Saturation"].default_value = 1.4; hs.inputs["Value"].default_value = 0.6
    for l in list(tex.outputs["Color"].links):
        nt.links.new(hs.outputs["Color"], l.to_socket)
    nt.links.new(tex.outputs["Color"], hs.inputs["Color"])


objs = {o.name.split(".", 1)[1]: o for o in bpy.data.objects if o.type == "MESH" and "." in o.name}
recolor_skin(objs["body"], PALETTE["skin"])
hair_obj = next(o for k, o in objs.items() if k == os.path.basename(ACE["hair"]).split(".")[0])
recolor_texture(hair_obj, PALETTE["hair"])
tune_eyes(objs["high-poly"])
for part in ("toigo_fisherman_sweater", "toigo_wool_pants", "shoes02"):
    recolor_texture(objs[part], PALETTE[part])

# Sweater sits a few millimetres further out so the trouser waistband never pokes through the hem
sw = objs["toigo_fisherman_sweater"]
disp = sw.modifiers.new("HemClearance", "DISPLACE"); disp.strength = 0.006; disp.mid_level = 0.0

# Report
dg = bpy.context.evaluated_depsgraph_get()
ev = basemesh.evaluated_get(dg)
zs = [(ev.matrix_world @ v.co).z for v in ev.data.vertices]
keys = [k.name for k in basemesh.data.shape_keys.key_blocks] if basemesh.data.shape_keys else []
print("ACE height_m", round(max(zs) - min(zs), 3))
print("ACE objects", sorted(o.name for o in bpy.data.objects))
print("ACE shape_keys", len(keys), [k for k in keys if any(s in k.lower() for s in ("blink", "brow", "smile", "viseme", "aa", "oh"))][:20])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ACE saved", OUT)

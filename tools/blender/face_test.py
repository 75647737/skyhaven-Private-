"""Ace face test: 5 s of life (breathing, blinks, eye darts, brows, smile, "Still planning.").

blender ace_v005.blend --python face_test.py -- <out_prefix> [frames e.g. 20,60 | all] [res_pct]
"""
import bpy, sys, math, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, FRAMES = argv[0], argv[1]
PCT = int(argv[2]) if len(argv) > 2 else 50
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = bpy.data.objects["Ace.body"]
keys = body.data.shape_keys.key_blocks

# ---- eyebrows + eyelashes follow the face surface (so they move with blinks / brow raises)
for name in ("Ace.eyebrow001", "Ace.eyelashes01"):
    o = bpy.data.objects[name]
    sd = o.modifiers.new("FollowFace", "SURFACE_DEFORM"); sd.target = body
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_move_to_index(modifier=sd.name, index=0)
        bpy.ops.object.surfacedeform_bind(modifier=sd.name)
    if "Armature" in o.modifiers:
        o.modifiers["Armature"].show_viewport = o.modifiers["Armature"].show_render = False

# ---- relaxed arms: rotate upper arms down (pick axis/sign by testing which brings the elbow inward)
def lower_arm(side, deg=48):
    pb = rig.pose.bones[f"upperarm01.{side}"]
    best = None
    for axis in (0, 2):
        for sign in (1, -1):
            pb.rotation_euler = (0, 0, 0); pb.rotation_euler[axis] = sign * math.radians(deg)
            bpy.context.view_layer.update()
            t = rig.matrix_world @ pb.tail
            score = abs(t.x) + abs(t.y - (rig.matrix_world @ pb.head).y)
            if best is None or score < best[0]:
                best = (score, axis, sign)
    pb.rotation_euler = (0, 0, 0); pb.rotation_euler[best[1]] = best[2] * math.radians(deg)
    pb.keyframe_insert("rotation_euler", frame=1)
lower_arm("L"); lower_arm("R")

# ---- helpers
def key(name, frames_vals):
    k = keys[name]
    for f, v in frames_vals:
        k.value = v; k.keyframe_insert("value", frame=f)

def blink(f):
    for n in ("eyeBlinkLeft", "eyeBlinkRight"):
        key(n, [(f - 2, 0), (f, 1), (f + 1, 1), (f + 4, 0)])

def bone_wave(bone, axis, amp_deg, period, phase=0.0, start=1, end=121, step=4):
    pb = rig.pose.bones[bone]
    for f in range(start, end + 1, step):
        pb.rotation_euler[axis] = math.radians(amp_deg) * math.sin(2 * math.pi * (f / period) + phase)
        pb.keyframe_insert("rotation_euler", index=axis, frame=f)

sc.frame_start, sc.frame_end, sc.render.fps = 1, 120, 24

# breathing (chest rises), gentle head sway, small weight shift
bone_wave("spine03", 0, 1.2, 80)
bone_wave("spine05", 0, -0.8, 80, 0.4)
bone_wave("head", 1, 2.5, 110, 0.0)
bone_wave("head", 0, 1.5, 70, 1.0)
bone_wave("neck01", 2, 1.2, 95, 0.5)

# blinks every ~2 s
for f in (20, 66, 112):
    blink(f)

# eye darts (look slightly left, back, right)
for side in ("L", "R"):
    pb = rig.pose.bones[f"eye.{side}"]
    for f, z in ((1, 0), (34, 0), (37, 6), (48, 6), (51, 0), (90, 0), (93, -4), (104, -4), (107, 0)):
        pb.rotation_euler[2] = math.radians(z); pb.keyframe_insert("rotation_euler", index=2, frame=f)

# brows lift with the idea, then a warm smile
for n, v in (("browInnerUp", 0.7), ("browOuterUpLeft", 0.5), ("browOuterUpRight", 0.5)):
    key(n, [(26, 0), (32, v), (44, v), (52, 0.1)])
for n in ("mouthSmileLeft", "mouthSmileRight"):
    key(n, [(44, 0), (52, 0.65), (72, 0.6), (78, 0.15), (110, 0.15), (118, 0.55)])
for n in ("cheekSquintLeft", "cheekSquintRight"):
    key(n, [(44, 0), (52, 0.35), (72, 0.3), (78, 0), (110, 0), (118, 0.3)])

# "Still planning." (frames 80-108), visemes with jaw
line = [("s_z_15", 80), ("d_t_n_19", 83), ("y_iy_ih_ix_06", 85), ("l_14", 88), ("p_b_m_21", 91),
        ("l_14", 93), ("ey_eh_uh_04", 95), ("d_t_n_19", 98), ("y_iy_ih_ix_06", 100), ("k_g_ng_20", 103), ("sil_00", 107)]
for (vis, f), nxt in zip(line, line[1:] + [("sil_00", 112)]):
    if vis == "sil_00":
        continue
    key(vis, [(f - 2, 0), (f, 0.9), (nxt[1] - 1, 0.6), (nxt[1] + 1, 0)])
key("jawOpen", [(78, 0), (85, 0.12), (88, 0.05), (91, 0.0), (95, 0.18), (100, 0.1), (104, 0.06), (108, 0)])

# ---- light, camera, render
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.20, 0.17, 0.15, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
head_pos = rig.matrix_world @ rig.pose.bones["head"].head
def light(n, off, e, size, col):
    L = bpy.data.objects.new(n, bpy.data.lights.new(n, "AREA")); L.data.energy = e; L.data.size = size; L.data.color = col
    L.location = head_pos + mathutils.Vector(off); L.rotation_euler = (head_pos - L.location).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(L)
light("Key", (-1.0, -1.4, 0.6), 220, 1.2, (1.0, 0.93, 0.84))      # warm morning key
light("Fill", (1.3, -1.0, 0.1), 70, 1.5, (0.85, 0.9, 1.0))
light("Rim", (0.6, 1.2, 0.5), 140, 0.8, (1.0, 0.95, 0.9))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
target = head_pos + mathutils.Vector((0, -0.02, 0.03))
a = math.radians(22)
cam.location = target + mathutils.Vector((math.sin(a) * 1.4, -math.cos(a) * 1.4, 0.02))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 60
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 1.37; cam.data.dof.aperture_fstop = 2.8
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 32
sc.view_settings.view_transform = "AgX"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, PCT
sc.render.image_settings.file_format = "PNG"
if FRAMES == "all":
    sc.render.filepath = OUT + "_"
    sc.render.use_overwrite = False
    bpy.ops.render.render(animation=True)
else:
    for f in map(int, FRAMES.split(",")):
        sc.frame_set(f); sc.render.filepath = f"{OUT}_{f:04d}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.quit_blender()

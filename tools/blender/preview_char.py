"""Preview renders of a cartoon character master file (background mode).

    blender -b <file.blend> --python tools/blender/preview_char.py -- <PREFIX> <out_dir> [tag]

Writes <tag>_front/threeq/side/face_side/face_front/hand.png using a temporary camera.
"""
import bpy, os, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
PREFIX, OUT = argv[0], argv[1]
TAG = argv[2] if len(argv) > 2 else PREFIX.lower()
os.makedirs(OUT, exist_ok=True)
S = bpy.context.scene
rig = bpy.data.objects[PREFIX + ".rig"]
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0)
S.frame_set(1)
bpy.context.view_layer.update()
mw = rig.matrix_world
head = mw @ rig.pose.bones["head"].head
top = mw @ rig.pose.bones["head"].tail
hand = mw @ rig.pose.bones["hand.L"].tail
H = top.z
mid = Vector((0, 0, H * 0.5))
face = Vector((0, head.y, (head.z + top.z) / 2 - 0.02 * rig.scale.z))
cd = bpy.data.cameras.new("_pcam")
cam = bpy.data.objects.new("_pcam", cd)
S.collection.objects.link(cam)
S.camera = cam
S.render.resolution_percentage = 100
S.eevee.taa_render_samples = 16


def shot(name, tgt, ang, dist, lens=50, res=(600, 700), dz=0.0):
    a = math.radians(ang)
    cd.lens = lens
    cam.location = tgt + Vector((dist * math.sin(a), -dist * math.cos(a), dz))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    S.render.resolution_x, S.render.resolution_y = res
    S.render.filepath = os.path.join(OUT, "%s_%s.png" % (TAG, name))
    bpy.ops.render.render(write_still=True)


d = H * 2.4
shot("front", mid, 0, d, dz=H * 0.1)
shot("threeq", mid, 35, d, dz=H * 0.1)
shot("side", mid, 90, d, dz=H * 0.1)
fh = (top.z - head.z)
shot("face_front", face, 0, fh * 2.6, res=(600, 600))
shot("face_side", face, 90, fh * 2.6, res=(600, 600))
shot("hand", hand + Vector((0, 0, 0.02)), 40, fh * 1.3, res=(500, 500))
feet = Vector((0, -0.03 * rig.scale.z, 0.04 * rig.scale.z))
shot("feet", feet, 30, fh * 1.5, res=(600, 450), dz=fh * 0.4)
shot("feet_side", feet, 90, fh * 1.3, res=(600, 450), dz=fh * 0.15)
print("PREVIEW_DONE")

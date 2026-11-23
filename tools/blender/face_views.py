"""Face review sheets for a cartoon character file (background mode).

    blender -b <char.blend> --python tools/blender/face_views.py -- <PREFIX> <out_dir> [tag]

  <tag>_turn.png     head in front, three-quarter and true side view, side by side (neutral smile)
  <tag>_mouth.png    the nine mouth shapes (0 smile, 1 rest, 2 A, 3 E, 4 O, 5 U/W, 6 M/B/P, 7 F/V,
                     8 frown), each in front (top row) and side view (bottom row)
  <tag>_expr.png     expressions in front and three-quarter: happy, talking, surprised, cross,
                     worried, blink
"""
import bpy, os, sys, math
import numpy as np
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
    pb.rotation_quaternion = (1, 0, 0, 0)
S.frame_set(1)
bpy.context.view_layer.update()
mw = rig.matrix_world
hb = rig.pose.bones["head"]
top = (mw @ hb.tail).z
bot = (mw @ hb.head).z
H = top - bot
tgt = Vector((0, 0, bot + H * 0.5))
cd = bpy.data.cameras.new("_fcam")
cd.lens = 85
cam = bpy.data.objects.new("_fcam", cd)
S.collection.objects.link(cam)
S.camera = cam
S.eevee.taa_render_samples = 24
S.render.resolution_percentage = 100
S.render.film_transparent = False
TMP = os.path.join(OUT, "_tiles")
os.makedirs(TMP, exist_ok=True)
DEFAULT = {k: rig[k] for k in ("mouth", "blink", "blink_L", "blink_R", "look_x", "look_y", "brows", "brow_tilt") if k in rig.keys()}


def setp(**kw):
    for k, v in DEFAULT.items():
        rig[k] = v
    for k, v in kw.items():
        rig[k] = v
    rig.update_tag()
    S.frame_set(1)
    bpy.context.view_layer.update()


def tile(name, ang, res=(640, 720), dist=None):
    a = math.radians(ang)
    d = dist or H * 4.6
    cam.location = tgt + Vector((d * math.sin(a), -d * math.cos(a), H * 0.05))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    S.render.resolution_x, S.render.resolution_y = res
    p = os.path.join(TMP, name + ".png")
    S.render.filepath = p
    bpy.ops.render.render(write_still=True)
    return p


def stitch(rows, path):
    imgs = []
    for row in rows:
        arrs = []
        for p in row:
            im = bpy.data.images.load(p)
            w, h = im.size
            a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
            arrs.append(a)
            bpy.data.images.remove(im)
        imgs.append(np.concatenate(arrs, axis=1))
    W = max(r.shape[1] for r in imgs)
    imgs = [np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0)), constant_values=1.0) for r in imgs]
    full = np.concatenate(imgs[::-1], axis=0)       # blender images are stored bottom row first
    h, w = full.shape[:2]
    out = bpy.data.images.new("sheet", w, h, alpha=True)
    out.pixels = full.ravel()
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()


setp(mouth=0)
stitch([[tile("t_front", 0), tile("t_3q", 35), tile("t_side", 90)]], os.path.join(OUT, TAG + "_turn.png"))

top_row, side_row = [], []
for m in range(9):
    setp(mouth=m)
    top_row.append(tile("m%d_f" % m, 0, res=(360, 400)))
    side_row.append(tile("m%d_s" % m, 90, res=(360, 400)))
stitch([top_row, side_row], os.path.join(OUT, TAG + "_mouth.png"))

EXPR = [("happy", dict(mouth=0, brows=0.4)), ("talk", dict(mouth=3, brows=0.2)),
        ("surprised", dict(mouth=4, brows=1.0)), ("cross", dict(mouth=8, brows=-0.6, brow_tilt=-1.0)),
        ("worried", dict(mouth=1, brow_tilt=1.0)), ("blink", dict(mouth=0, blink=1.0))]
fr, tq = [], []
for name, kw in EXPR:
    setp(**kw)
    fr.append(tile("e_%s_f" % name, 0, res=(400, 440)))
    tq.append(tile("e_%s_q" % name, 35, res=(400, 440)))
stitch([fr, tq], os.path.join(OUT, TAG + "_expr.png"))
print("FACE_VIEWS_DONE")

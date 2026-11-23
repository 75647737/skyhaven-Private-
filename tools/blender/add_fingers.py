"""Give a cartoon character (cartoon Ace / cartoon Tori rig) real fingers.

Run inside Blender with the character's master file open, e.g.
    PREFIX = "AC"  (objects AC.hand.L ...)   or  "TC" for Tori
It replaces the mitt on each hand with a rounded palm, four fingers and a thumb.
Each finger gets its own bone (finger_<name>.<side>, child of hand.<side>) and a
rigid, bone-parented mesh, like the rest of the cartoon rig, so a finger is
posed by rotating its bone.  Curl = rotate the finger bone on its local X axis
(NEGATIVE curls toward the palm, e.g. -0.4 relaxed, -1.4 fist); spread = local Z.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

PREFIX = globals().get("PREFIX", "AC")
RIG = bpy.data.objects[PREFIX + ".rig"]
SKIN = None

# finger layout in HAND space: x = palm normal (out of the back of the hand),
# y = down the hand (bone direction), z = across the hand (front of body = -z)
# name, z offset across the hand, length, radius
FINGERS = [("index", -0.0225, 0.036, 0.0100),
           ("middle", -0.0075, 0.040, 0.0104),
           ("ring", 0.0075, 0.037, 0.0100),
           ("pinky", 0.0215, 0.030, 0.0090)]
PALM_Y0, PALM_LEN = 0.022, 0.044    # palm starts just below the cuff
PALM_W, PALM_T = 0.062, 0.036       # width across, thickness
OUTLINE_FINGER = -0.0032
OUTLINE_PALM = -0.0045

# optional overrides (set before exec): HAND_SCALE scales the whole hand,
# FINGER_LEN / FINGER_FAT scale finger length / thickness (baby: short + chubby),
# PALM_START moves where the palm begins below the wrist.
HS = globals().get("HAND_SCALE", 1.0)
FL = globals().get("FINGER_LEN", 1.0)
FF = globals().get("FINGER_FAT", 1.0)
FINGERS = [(n, z * HS * FF ** 0.5, L * HS * FL, r * HS * FF) for n, z, L, r in FINGERS]
PALM_Y0 = globals().get("PALM_START", PALM_Y0)
PALM_LEN, PALM_W, PALM_T = PALM_LEN * HS, PALM_W * HS * FF ** 0.5, PALM_T * HS
THUMB_LEN, THUMB_R = 0.034 * HS * FL ** 0.5, 0.0108 * HS * FF
OUTLINE_FINGER *= HS
OUTLINE_PALM *= HS


def hand_frame(side):
    """Matrix from hand space to armature space, with a unit hand-bone frame."""
    b = RIG.data.bones["hand." + side]
    m = b.matrix_local.copy()
    return m


def capsule(bm, radius, length, mat):
    """Capsule along +Y from 0 to length, transformed by mat."""
    ret = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=radius)
    vs = ret["verts"]
    for v in vs:
        # stretch: upper half (y>0) moves to the tip
        if v.co.y > 0:
            v.co.y += length - 2 * radius
        v.co.y += radius
        # slightly flatter across the palm normal
        v.co.x *= 0.88
    bmesh.ops.transform(bm, matrix=mat, verts=vs)
    return vs


def add_outline(ob, thick, mats):
    ob.data.materials.clear()
    for m in mats:
        ob.data.materials.append(m)
    sub = ob.modifiers.new("Smooth", 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    so = ob.modifiers.new("Outline", 'SOLIDIFY')
    so.thickness = thick
    so.offset = 1
    so.use_flip_normals = True
    so.material_offset = 1
    so.use_rim = False
    for p in ob.data.polygons:
        p.use_smooth = True
        p.material_index = 0


def parent_to_bone(ob, bone):
    ob.parent = RIG
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = RIG.matrix_world.copy()   # mesh data is in armature space


def mesh_object(name, coll):
    old = bpy.data.objects.get(name)
    if old:
        me_old = old.data
        bpy.data.objects.remove(old)
        if me_old.users == 0:
            bpy.data.meshes.remove(me_old)
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def run():
    hand_obj = bpy.data.objects[PREFIX + ".hand.L"]
    coll = hand_obj.users_collection[0]
    mats = [hand_obj.data.materials[0], hand_obj.data.materials[1]]

    # ---------------- bones (edit mode)
    bpy.context.view_layer.objects.active = RIG
    for o in bpy.context.selected_objects:
        o.select_set(False)
    RIG.select_set(True)
    pose_pos = RIG.data.pose_position
    RIG.data.pose_position = 'REST'
    bpy.ops.object.mode_set(mode='EDIT')
    eb = RIG.data.edit_bones
    for side in "LR":
        hb = eb["hand." + side]
        M = hb.matrix.copy()          # armature space, unit axes
        ax = M.to_3x3()
        X, Y, Z = ax.col[0], ax.col[1], ax.col[2]
        origin = hb.head.copy()
        sgn = 1 if side == "L" else -1   # Z points to the back for both sides, X flips with side
        for name, zo, L, r in FINGERS:
            bn = "finger_%s.%s" % (name, side)
            b = eb.get(bn) or eb.new(bn)
            base = origin + Y * (PALM_Y0 + PALM_LEN - 0.006 * HS) + Z * zo
            # fingers fan out a little
            d = (Y + Z * zo * 2.2).normalized()
            b.head = base
            b.tail = base + d * L
            b.parent = hb
            b.use_connect = False
            b.align_roll(X * sgn)   # bone Z -> palm normal; curl axis = bone X
            b.use_deform = False
        tb = eb["thumb." + side]
        tbase = origin + Y * (PALM_Y0 + 0.012 * HS) + Z * (-PALM_W * 0.45) + X * (-sgn * 0.004)
        tdir = (Y * 0.75 + Z * -0.55 + X * (-sgn * 0.25)).normalized()
        tb.head = tbase
        tb.tail = tbase + tdir * THUMB_LEN
        tb.align_roll(X * sgn)
    bpy.ops.object.mode_set(mode='OBJECT')
    # new pose bones default to quaternions; the rest of the rig uses Euler XYZ
    for side in "LR":
        for name, *_ in FINGERS:
            RIG.pose.bones["finger_%s.%s" % (name, side)].rotation_mode = 'XYZ'

    # ---------------- meshes
    for side in "LR":
        hb = RIG.data.bones["hand." + side]
        M = hb.matrix_local
        X, Y, Z = (M.to_3x3().col[i] for i in range(3))
        sgn = 1 if side == "L" else -1

        # palm: rounded box in hand space
        palm = bpy.data.objects[PREFIX + ".hand." + side]
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            hx, hy, hz = v.co.x * PALM_T, (v.co.y + 0.5) * PALM_LEN + PALM_Y0, v.co.z * PALM_W
            # taper the wrist end
            if v.co.y < 0:
                hz *= 0.8
                hx *= 0.85
            v.co = hb.head_local + X * hx + Y * hy + Z * hz
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
        me = palm.data
        me.clear_geometry() if hasattr(me, "clear_geometry") else None
        bm.to_mesh(me)
        bm.free()
        palm.modifiers.clear()
        add_outline(palm, OUTLINE_PALM, mats)
        palm.matrix_parent_inverse = Matrix()
        parent_to_bone(palm, "hand." + side)

        # fingers
        for name, zo, L, r in FINGERS:
            bn = "finger_%s.%s" % (name, side)
            b = RIG.data.bones[bn]
            ob = mesh_object("%s.finger_%s.%s" % (PREFIX, name, side), coll)
            bm = bmesh.new()
            capsule(bm, r, b.length, b.matrix_local @ Matrix.Rotation(0, 4, 'X'))
            bm.to_mesh(ob.data)
            bm.free()
            add_outline(ob, OUTLINE_FINGER, mats)
            parent_to_bone(ob, bn)

        # thumb
        tb = RIG.data.bones["thumb." + side]
        th = bpy.data.objects[PREFIX + ".thumb." + side]
        bm = bmesh.new()
        capsule(bm, THUMB_R, tb.length, tb.matrix_local)
        th.data.clear_geometry() if hasattr(th.data, "clear_geometry") else None
        bm.to_mesh(th.data)
        bm.free()
        th.modifiers.clear()
        add_outline(th, OUTLINE_FINGER, mats)
        th.matrix_parent_inverse = Matrix()
        parent_to_bone(th, "thumb." + side)
        th.hide_render = False
        th.hide_viewport = False
        th.hide_set(False)

    RIG.data.pose_position = pose_pos
    bpy.context.view_layer.update()


run()

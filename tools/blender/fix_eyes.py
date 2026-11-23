"""Seat a cartoon character's eyes (and brows/lashes) into the face.

The eyes were flat discs standing in front of the face, so in profile they
stuck out like coins.  For every point of the eye parts that lies in front of
the skin, this pulls it back toward the skin along the face's forward axis,
keeping K of its height above the skin.  Front views barely change; profiles
show the eye sitting in the head.

Run inside Blender with the master file open:  PREFIX = "AC" / "TC" / "MX".
"""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PREFIX = globals().get("PREFIX", "AC")
K_EYE = globals().get("K_EYE", 0.28)       # eye white / iris / pupil / shine
K_BROW = globals().get("K_BROW", 0.35)     # brows, lashes

RIG = bpy.data.objects[PREFIX + ".rig"]
HEAD = bpy.data.objects[PREFIX + ".head"]


def run():
    act = RIG.animation_data.action if RIG.animation_data else None
    if RIG.animation_data:
        RIG.animation_data.action = None
    pose_pos = RIG.data.pose_position
    RIG.data.pose_position = 'REST'
    # skin surface without the outline shell
    hidden = []
    for m in HEAD.modifiers:
        if m.type == 'SOLIDIFY' and m.show_viewport:
            m.show_viewport = False
            hidden.append(m)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(HEAD, dg)
    hm = HEAD.matrix_world
    hinv = hm.inverted()
    fwd = (RIG.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()   # face looks along -Y

    def skin_y(pw):
        """World point on the skin straight behind/in front of pw along the face axis."""
        # shoot from in front of the face back toward it, so the first hit is the face
        o = hinv @ (pw + fwd * 0.5)
        d = (hinv.to_3x3() @ -fwd).normalized()
        loc, nor, idx, dist = bvh.ray_cast(o, d)
        return None if loc is None else hm @ loc

    def squash(pw, k):
        s = skin_y(pw)
        if s is None:
            return pw
        h = (pw - s).dot(fwd)        # how far the point stands out in front of the skin
        if h <= 0:
            return pw
        return pw - fwd * (h * (1 - k))   # pull it back toward the skin

    keys_eye = (".eye.", ".iris.", ".pupil.", ".shine.")
    keys_brow = (".brow.", ".lash")
    done = []
    for ob in bpy.data.objects:
        if not ob.name.startswith(PREFIX + "."):
            continue
        k = None
        if any(t in ob.name for t in keys_eye):
            k = K_EYE
        elif any(t in ob.name for t in keys_brow):
            k = K_BROW
        if k is None:
            continue
        mw = ob.matrix_world
        inv = mw.inverted()
        if ob.type == 'MESH':
            for v in ob.data.vertices:
                v.co = inv @ squash(mw @ v.co, k)
            ob.data.update()
        elif ob.type == 'CURVE':
            for sp in ob.data.splines:
                for p in sp.bezier_points:
                    for attr in ("co", "handle_left", "handle_right"):
                        setattr(p, attr, inv @ squash(mw @ getattr(p, attr), k))
                for p in sp.points:
                    w = p.co[3]
                    c = inv @ squash(mw @ Vector(p.co[:3]), k)
                    p.co = (c.x, c.y, c.z, w)
        done.append(ob.name)

    for m in hidden:
        m.show_viewport = True
    RIG.data.pose_position = pose_pos
    if act:
        RIG.animation_data.action = act
    print("FIX_EYES", PREFIX, len(done), done)
    return done


run()

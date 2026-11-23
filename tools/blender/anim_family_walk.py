"""Family greeting + walk between rooms (greeting_room_v003.blend).

Ace comes in through the living-room door; Tori, carrying baby Max on her hip,
turns to him; they wave and talk (Max waves and laughs); then they walk into
the kitchen and wave at the camera.

Run inside Blender with the scene open. Rebuilds GR_ace_walk, GR_tori_walk,
GR_max_carry (one key per frame) and the camera. Edit CHOREO and run again.

Walk model (rigid cartoon legs, no knees):
  * steps are tied to distance travelled, so the standing foot stays planted;
  * the body vaults over the standing leg (inverted pendulum): it is highest
    when the legs pass and lowest at heel strike, as in a human walk;
  * the swinging leg shortens a little (bone scale) so the foot clears the floor;
  * heel strike (toes up) -> flat foot -> push-off (heel up);
  * pelvis twists toward the swinging leg and drops on the swing side, the chest
    counter-twists, arms swing against the legs with more elbow on the forward
    swing, the head stays level.

Rig notes (cartoon rigs, Euler XYZ):
  leg.*        rot X  - = forward;  foot.* rot X  - = toes up
  upper_arm.*  rot X  - = forward;  rot Z raises sideways (+ for .R, - for .L)
  forearm.*    rot X  - = bend forward; rot Z bends outward (+ .R, - .L)
  finger_*     rot X  - = curl;  character faces -Y; heading = atan2(dx, -dy)
"""
import bpy, math, random
from mathutils import Matrix, Vector, Euler

END = 470

CHOREO = {
    "AC.rig": dict(
        stride=0.21, step_frames=8.8,
        paths=[[(14, -2.75, 0.55), (60, -1.6, 0.48), (124, -0.5, 0.05)],
               [(206, -0.5, 0.05), (290, 1.55, -0.12), (338, 2.81, -0.12), (400, 4.10, -0.08)]],
        face=[(0, 90), (128, 24), (200, 24), (406, 0)],
        waves=[(130, 170, "R"), (414, 456, "L")],
        talk=[(132, 154), (418, 434)],
        look=[(0, 0.0), (126, 0.5), (200, 0.5), (206, 0.0)],
        blinks=[44, 108, 172, 250, 330, 404, 446],
        carry=None,
    ),
    "TC.rig": dict(
        stride=0.17, step_frames=10.5,
        paths=[[(196, 0.5, 0.0), (280, 1.75, 0.30), (340, 2.81, 0.32), (392, 3.45, 0.14)]],
        face=[(0, 0), (18, -55), (128, -24), (190, -24), (396, 0)],
        waves=[(138, 178, "L"), (416, 458, "L")],
        talk=[(156, 178), (436, 452)],
        look=[(0, 0.0), (18, -0.6), (128, -0.5), (192, 0.0)],
        blinks=[12, 80, 160, 232, 318, 384, 450],
        carry="R",          # Max on her right hip
    ),
}
MAX = dict(
    rig="MX.rig", parent="TC.rig", scale=0.61,
    # hip seat in Tori's hips-bone space: x = her right (-), y = up the bone, z = forward
    seat=Vector((-0.19, 0.12, 0.035)), yaw=-14,
    waves=[(142, 186, "R"), (420, 462, "R")],
    laugh=[(144, 164), (424, 440)],
    blinks=[30, 98, 190, 270, 352, 430],
)
CAM_X = [(1, -0.6), (96, -0.6), (132, 0.0), (206, 0.0), (400, 3.75), (END, 3.75)]
CAM_Y = [(1, -3.4), (404, -3.4), (END, -3.05)]


# ---------------------------------------------------------------- helpers
def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def interp_keys(keys, f):
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * smooth((f - f0) / (f1 - f0))
    return keys[-1][1]


def path_pos(path, f):
    """Constant speed along the polyline, eased over the first/last frames."""
    f0, f1 = path[0][0], path[-1][0]
    pts = [(p[1], p[2]) for p in path]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total, T = sum(seg), f1 - f0
    e = min(12.0, T / 3)
    vmax = total / (T - e)
    t = max(0.0, min(T, f - f0))
    if t < e:
        s = vmax * t * t / (2 * e)
    elif t > T - e:
        r = T - t
        s = total - vmax * r * r / (2 * e)
    else:
        s = vmax * (e / 2) + vmax * (t - e)
    for i, L in enumerate(seg):
        a, b = pts[i], pts[i + 1]
        if s <= L or i == len(seg) - 1:
            u = 0 if L == 0 else min(1, s / L)
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        s -= L
    return pts[-1]


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def blink_value(blinks, f):
    bl = 0.0
    for b in blinks:
        if b <= f < b + 2:
            bl = max(bl, (f - b + 1) / 2)
        elif b + 2 <= f <= b + 3:
            bl = 1.0
        elif b + 3 < f <= b + 7:
            bl = max(bl, 1 - (f - b - 3) / 4)
    return bl


def mouth_keys(seed, spans, shapes=(2, 3, 4, 5, 1, 6, 7, 2, 3, 4), rest=0):
    rnd = random.Random(seed)
    keys = [(0, rest)]
    for t0, t1 in spans:
        f = t0
        while f < t1:
            keys.append((f, rnd.choice(shapes)))
            f += rnd.choice([3, 3, 4, 5])
        keys.append((t1, rest))
    return keys


def wave_weight(waves, f, side=None):
    w = 0.0
    for (w0, w1, s) in waves:
        if side and s != side:
            continue
        w = max(w, smooth((f - w0) / 7.0) * smooth((w1 - f) / 7.0))
    return w


def new_action(rig, name):
    ad = rig.animation_data or rig.animation_data_create()
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad.action = act
    return act


def write(act, rig, chans, const=()):
    for (path, idx), kv in chans.items():
        fc = act.fcurve_ensure_for_datablock(rig, path, index=idx)
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(kv))
        fc.keyframe_points.foreach_set("co", [c for fv in kv for c in fv])
        interp = 'CONSTANT' if path in const else 'LINEAR'
        for kp in fc.keyframe_points:
            kp.interpolation = interp
        fc.update()


PB = 'pose.bones["%s"].%s'


def put_arm(put, f, side, A):
    put(PB % ("upper_arm." + side, "rotation_euler"), 0, f, A["ux"])
    put(PB % ("upper_arm." + side, "rotation_euler"), 2, f, A["uz"])
    put(PB % ("forearm." + side, "rotation_euler"), 0, f, A["fx"])
    put(PB % ("forearm." + side, "rotation_euler"), 2, f, A["fz"])
    put(PB % ("hand." + side, "rotation_euler"), 2, f, A["hz"])


def put_fingers(rig, put, f, side, curl_base, open_w, a=0.0, phase=0.0, fist=0.0):
    if "finger_index." + side not in rig.pose.bones:
        return
    for i, name in enumerate(("index", "middle", "ring", "pinky")):
        relax = curl_base - 0.08 * i - 0.05 * a * math.sin(phase + i * 0.6)
        relax = relax * (1 - fist) + (-1.3) * fist
        curl = relax * (1 - open_w) + 0.12 * open_w
        spread = open_w * (0.28, 0.09, -0.09, -0.28)[i] * (1 if side == "L" else -1)
        put(PB % ("finger_%s.%s" % (name, side), "rotation_euler"), 0, f, curl)
        put(PB % ("finger_%s.%s" % (name, side), "rotation_euler"), 2, f, spread)
    put(PB % ("thumb." + side, "rotation_euler"), 0, f, -0.15 * (1 - open_w))


def wave_arm(A, f, waves, side):
    sg = 1 if side == "R" else -1
    w = wave_weight(waves, f, side)
    if w <= 0:
        return A, 0.0
    w0 = min(w0 for (w0, _, s) in waves if s == side and w0 <= f + 7) if any(s == side and w0 <= f + 7 for (w0, _, s) in waves) else f
    wig = math.sin(2 * math.pi * (f - w0) / 9.0)
    target = dict(ux=-0.35, uz=sg * 1.6, fx=-0.1, fz=sg * (0.3 + 0.3 * wig), hz=sg * 0.3 * wig)
    return {k: A[k] * (1 - w) + target[k] * w for k in A}, w


# ---------------------------------------------------------------- walkers
def bake_walker(rig_name, C):
    rig = bpy.data.objects[rig_name]
    act = new_action(rig, "GR_" + ("ace" if rig_name.startswith("AC") else "tori") + "_walk")
    chans = {}
    put = lambda path, idx, f, v: chans.setdefault((path, idx), []).append((f, v))

    sc = rig.scale.z
    Lf = rig.data.bones["leg.L"].head_local.z * sc        # hip pivot to floor (world)
    stride = C["stride"]
    a_max = math.asin(min(0.9, 0.5 * stride / Lf))
    nominal = stride / C["step_frames"]
    paths = C["paths"]
    start_xy = (paths[0][0][1], paths[0][0][2])
    prev = start_xy
    dist = 0.0
    heading = math.radians(C["face"][0][1])
    amp = 0.0
    for f in range(0, END + 1):
        pos = None
        for p in paths:
            if p[0][0] <= f <= p[-1][0]:
                pos = path_pos(p, f)
        if pos is None:
            done = [p for p in paths if p[-1][0] < f]
            pos = (done[-1][-1][1], done[-1][-1][2]) if done else start_xy
        x, y = pos
        speed = math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
        dist += speed
        amp += (min(1.0, speed / (nominal * 0.75)) - amp) * 0.3
        a = amp

        # heading (look ahead while walking)
        target = None
        for p in paths:
            if p[0][0] <= f + 4 and f - 2 <= p[-1][0]:
                ax, ay = path_pos(p, f + 4)
                bx, by = path_pos(p, f - 1)
                if math.hypot(ax - bx, ay - by) > 1e-4:
                    target = math.atan2(ax - bx, -(ay - by))
        if target is None:
            target = math.radians(interp_keys(C["face"], f))
        heading += wrap(target - heading) * 0.2

        # ---- gait
        u = dist / stride
        k = int(math.floor(u))
        ph = u - k                                  # 0 = heel strike of the stance leg
        stance = "L" if k % 2 == 0 else "R"
        swing = "R" if stance == "L" else "L"
        st = math.asin(max(-0.95, min(0.95, (ph - 0.5) * stride / Lf)))   # + = foot behind hip
        e = ph * ph * (3 - 2 * ph)
        sw = a_max * (1 - 2 * e)                   # back (+) -> front (-)
        leg = {stance: st * a, swing: sw * a}
        lift = {stance: 0.0, swing: 0.11 * a * math.sin(math.pi * ph)}
        # feet: flat on the floor, heel strike toes-up, push-off heel-up
        roll_st = -0.28 * smooth(1 - ph / 0.18) + 0.22 * smooth((ph - 0.7) / 0.3)
        roll_sw = -0.18 * math.sin(math.pi * ph)
        foot = {stance: -leg[stance] + roll_st * a, swing: -leg[swing] + roll_sw * a}

        # body height: vault over the standing leg (+ tiny settle after heel strike)
        bob = (Lf * math.cos(st) - Lf) * a - 0.004 * a * math.exp(-((ph - 0.08) / 0.08) ** 2)
        put("location", 0, f, x)
        put("location", 1, f, y)
        put("location", 2, f, bob)
        put("rotation_euler", 2, f, heading)

        sgn_st = 1 if stance == "L" else -1
        breathe = math.sin(2 * math.pi * f / 72.0)
        for s in "LR":
            put(PB % ("leg." + s, "rotation_euler"), 0, f, leg[s])
            put(PB % ("leg." + s, "scale"), 1, f, 1.0 - lift[s])
            put(PB % ("foot." + s, "rotation_euler"), 0, f, foot[s])
        # pelvis: twist toward the swinging leg, drop on the swing side
        twist = 0.11 * a * math.cos(math.pi * ph) * sgn_st
        drop = 0.035 * a * math.sin(math.pi * ph) * sgn_st
        put(PB % ("hips", "rotation_euler"), 1, f, twist)
        put(PB % ("hips", "rotation_euler"), 2, f, drop)
        put(PB % ("chest", "rotation_euler"), 0, f, 0.06 * a + 0.02 * breathe)
        put(PB % ("chest", "rotation_euler"), 1, f, -1.5 * twist)
        put(PB % ("chest", "rotation_euler"), 2, f, -0.8 * drop)

        # arms against the legs
        arm = {}
        for s in "LR":
            swing_a = -0.85 * leg[s]                       # leg forward -> same-side arm back
            out = 0.13 if s == "R" else -0.13
            arm[s] = dict(ux=swing_a, uz=out + (0.04 if s == "R" else -0.04) * breathe,
                          fx=-0.18 - 0.2 * a - 0.45 * max(0.0, -swing_a), fz=0.0, hz=0.0)
        # carrying arm holds Max
        if C.get("carry"):
            s = C["carry"]
            sg = 1 if s == "R" else -1
            arm[s] = dict(ux=-0.42, uz=sg * 0.32, fx=-1.45, fz=sg * -0.15, hz=sg * -0.2)
        talk_tilt = 0.0
        open_w = {}
        for s in "LR":
            if C.get("carry") == s:
                open_w[s] = 0.0
                continue
            arm[s], w = wave_arm(arm[s], f, C["waves"], s)
            open_w[s] = w
            talk_tilt += 0.06 * w * (1 if s == "R" else -1)
        for s in "LR":
            put_arm(put, f, s, arm[s])
            put_fingers(rig, put, f, s, -0.35 if C.get("carry") != s else -0.75, open_w[s], a, dist / stride * math.pi)

        # head: level gaze while walking, nods while talking
        nod = 0.0
        for (t0, t1) in C["talk"]:
            if t0 <= f <= t1:
                nod = 0.05 * math.sin(2 * math.pi * (f - t0) / 14.0)
        put(PB % ("head", "rotation_euler"), 0, f, nod - 0.05 * a - 0.5 * (0.06 * a))
        put(PB % ("head", "rotation_euler"), 1, f, -0.5 * (-1.5 * twist + twist))
        put(PB % ("head", "rotation_euler"), 2, f, -talk_tilt)

        put('["look_x"]', 0, f, interp_keys(C["look"], f))
        put('["blink"]', 0, f, blink_value(C["blinks"], f))
        put('["brows"]', 0, f, 0.5 * max(wave_weight(C["waves"], f, "L"), wave_weight(C["waves"], f, "R")))

    write(act, rig, chans)
    fc = act.fcurve_ensure_for_datablock(rig, '["mouth"]')
    fc.keyframe_points.clear()
    for fr, v in mouth_keys(sum(map(ord, rig_name)), C["talk"]):
        fc.keyframe_points.insert(fr, v).interpolation = 'CONSTANT'


# ---------------------------------------------------------------- Max on the hip
def bake_max():
    S = bpy.context.scene
    mx = bpy.data.objects.get(MAX["rig"])
    if mx is None:
        return
    mom = bpy.data.objects[MAX["parent"]]
    mx.scale = (MAX["scale"],) * 3
    act = new_action(mx, "GR_max_carry")
    chans = {}
    put = lambda path, idx, f, v: chans.setdefault((path, idx), []).append((f, v))
    hip_h = mx.data.bones["hips"].head_local.z * MAX["scale"]
    # rig axes expressed in bone axes (bone Y is up, bone Z is forward = -rig Y)
    bone_to_rig = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    yaw = Matrix.Rotation(math.radians(MAX["yaw"]), 4, 'Z')
    prev_rot = None
    for f in range(0, END + 1):
        S.frame_set(f)
        hb = mom.matrix_world @ mom.pose.bones["hips"].matrix
        seat = hb @ (MAX["seat"] / 1.0)
        # orientation: mom's hips frame converted to an upright rig frame, then yaw out
        R = hb.to_3x3().normalized().to_4x4() @ bone_to_rig @ yaw
        loc = Vector(seat) - R.to_3x3() @ Vector((0, 0, hip_h))
        eul = R.to_euler('XYZ', prev_rot) if prev_rot else R.to_euler('XYZ')
        prev_rot = eul
        for i in range(3):
            put("location", i, f, loc[i])
            put("rotation_euler", i, f, eul[i])

        # pose: sitting astride her hip, little legs dangling forward, one arm round mum
        jig = math.sin(2 * math.pi * f / 11.0)
        put(PB % ("hips", "rotation_euler"), 0, f, 0.04)
        put(PB % ("chest", "rotation_euler"), 0, f, 0.05 + 0.02 * math.sin(2 * math.pi * f / 60))
        for s, sx in (("L", 1), ("R", -1)):
            put(PB % ("leg." + s, "rotation_euler"), 0, f, -0.75 + 0.10 * math.sin(2 * math.pi * f / 40 + (0 if s == "L" else 1.7)))
            put(PB % ("leg." + s, "rotation_euler"), 2, f, 0.45 * sx * -1)
            put(PB % ("foot." + s, "rotation_euler"), 0, f, 0.5)
        hug = dict(ux=-0.95, uz=0.35, fx=-1.0, fz=0.25, hz=0.0)          # left arm round mum (L: + z = inward)
        rest = dict(ux=-0.25, uz=0.25, fx=-0.45, fz=0.0, hz=0.0)          # right arm free
        A_r, w = wave_arm(rest, f, MAX["waves"], "R")
        # excited baby wave: faster wiggle and a little bounce
        if w > 0:
            A_r["fz"] += 0.25 * w * jig
        put_arm(put, f, "L", hug)
        put_arm(put, f, "R", A_r)
        mx_rig = mx
        put_fingers(mx_rig, put, f, "L", -0.7, 0.0)
        put_fingers(mx_rig, put, f, "R", -0.45, w)
        # head: looks at dad during the greeting, around the room while carried
        look = interp_keys([(0, -0.2), (110, -0.2), (130, 0.6), (190, 0.6), (210, 0.0), (300, -0.4), (360, 0.3), (410, 0.0)], f)
        put(PB % ("head", "rotation_euler"), 1, f, 0.25 * look)
        put(PB % ("head", "rotation_euler"), 2, f, 0.05 * math.sin(2 * math.pi * f / 50))
        put('["look_x"]', 0, f, look)
        put('["blink"]', 0, f, blink_value(MAX["blinks"], f))
        laugh_w = max([smooth((f - a) / 4) * smooth((b - f) / 4) for a, b in MAX["laugh"]] + [0])
        put('["brows"]', 0, f, 0.25 + 0.55 * max(laugh_w, w))
        put('["brow_tilt"]', 0, f, 0.2)
    write(act, mx, chans)
    fc = act.fcurve_ensure_for_datablock(mx, '["mouth"]')
    fc.keyframe_points.clear()
    for fr, v in mouth_keys(7, MAX["laugh"], shapes=(2, 2, 4, 2, 3, 0), rest=0):
        fc.keyframe_points.insert(fr, v).interpolation = 'CONSTANT'


def camera():
    cam = bpy.data.objects["GR_cam"]
    cam.animation_data_clear()
    for keys, idx in ((CAM_X, 0), (CAM_Y, 1)):
        for f, v in keys:
            cam.location[idx] = v
            cam.keyframe_insert("location", index=idx, frame=f)


def run():
    S = bpy.context.scene
    S.frame_start, S.frame_end = 1, END
    for name, C in CHOREO.items():
        bake_walker(name, C)
    bake_max()
    camera()
    S.frame_set(1)


run()

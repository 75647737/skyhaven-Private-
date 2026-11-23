"""Greeting + walk between rooms for cartoon Ace and Tori (greeting_room_v002.blend).

Run inside Blender with the scene open. It rebuilds the actions
GR_ace_greet_walk and GR_tori_greet_walk (one key per frame) and the camera move.
Edit the CHOREO block below and run again to change the acting.

Rig notes (AC.rig / TC.rig, cartoon rig, Euler XYZ):
  leg.*        rot X  - = swing forward, + = back
  upper_arm.*  rot X  - = forward;  rot Z raises the arm sideways (+ for .R, - for .L)
  forearm.*    rot X  - = bend forward; rot Z bends outward (+ for .R, - for .L)
  character faces -Y at heading 0; heading = atan2(dx, -dy)
"""
import bpy, math, random

FPS = 24
END = 340

# ---------------------------------------------------------------- choreography
# paths: list of (frame, x, y). The character walks between points at constant
# speed with eased start/stop; between paths it stands.
# face:  list of (frame, heading_deg) used while standing.
# waves: (start, end, side)   talk: (start, end)   blinks: [frames]
CHOREO = {
    "AC.rig": dict(
        stride=0.21, swing=0.48, arm=0.38,
        paths=[[(14, -2.75, 0.55), (46, -1.55, 0.48), (80, -0.5, 0.05)],
               [(146, -0.5, 0.05), (190, 1.6, -0.12), (222, 2.81, -0.12), (262, 4.45, -0.08)]],
        face=[(0, 90), (82, 22), (140, 22), (266, 0)],
        waves=[(84, 122, "R"), (280, 322, "L")],
        talk=[(88, 108), (284, 300)],
        look=[(0, 0.0), (82, 0.5), (140, 0.5), (146, 0.0)],
        blinks=[40, 116, 200, 304],
    ),
    "TC.rig": dict(
        stride=0.17, swing=0.36, arm=0.30,
        paths=[[(138, 0.5, 0.0), (180, 1.75, 0.32), (218, 2.81, 0.34), (256, 3.75, 0.12)]],
        face=[(0, 0), (16, -55), (84, -22), (132, -22), (260, 0)],
        waves=[(92, 130, "L"), (278, 324, "R")],
        talk=[(110, 130), (300, 318)],
        look=[(0, 0.0), (16, -0.6), (84, -0.5), (134, 0.0)],
        blinks=[10, 70, 156, 244, 318],
    ),
}
CAM_X = [(1, -0.6), (60, -0.6), (92, 0.0), (148, 0.0), (276, 4.1), (END, 4.1)]
CAM_Y = [(1, -3.4), (276, -3.4), (END, -3.0)]


# ---------------------------------------------------------------- helpers
def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def interp_keys(keys, f, ease=True):
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            u = (f - f0) / (f1 - f0)
            return v0 + (v1 - v0) * (smooth(u) if ease else u)
    return keys[-1][1]


def path_pos(path, f):
    """Constant speed along the polyline, eased over the first/last 10 frames."""
    f0, f1 = path[0][0], path[-1][0]
    pts = [(p[1], p[2]) for p in path]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    T = f1 - f0
    e = min(10.0, T / 3)
    # trapezoid speed profile -> distance at time t
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


def mouth_seq(seed, f0, f1):
    rnd = random.Random(seed)
    keys, f = [], f0
    shapes = [2, 3, 4, 5, 1, 6, 7, 2, 3, 4]
    while f < f1:
        keys.append((f, rnd.choice(shapes)))
        f += rnd.choice([3, 3, 4, 5])
    keys.append((f1, 0))
    return keys


def bake(rig_name, C):
    rig = bpy.data.objects[rig_name]
    side_sign = {"R": 1, "L": -1}
    ad = rig.animation_data or rig.animation_data_create()
    act_name = "GR_" + ("ace" if rig_name.startswith("AC") else "tori") + "_greet_walk"
    old = bpy.data.actions.get(act_name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(act_name)
    act.use_fake_user = True
    ad.action = act

    chans = {}

    def put(path, idx, f, v):
        chans.setdefault((path, idx), []).append((f, v))

    # walk state per frame
    paths = C["paths"]
    start_xy = (paths[0][0][1], paths[0][0][2])
    x, y = start_xy
    phase, heading = 0.0, math.radians(C["face"][0][1])
    prev = (x, y)
    nominal = C["stride"] * 2 / 16.0  # metres per frame at a 16-frame cycle
    amp_s = 0.0
    for f in range(0, END + 1):
        # position
        pos = None
        for p in paths:
            if p[0][0] <= f <= p[-1][0]:
                pos = path_pos(p, f)
        if pos is None:
            done = [p for p in paths if p[-1][0] < f]
            pos = (done[-1][-1][1], done[-1][-1][2]) if done else start_xy
        x, y = pos
        dx, dy = x - prev[0], y - prev[1]
        speed = math.hypot(dx, dy)
        prev = (x, y)
        amp_t = min(1.0, speed / nominal)
        amp_s += (amp_t - amp_s) * 0.35
        phase += speed / C["stride"] * math.pi

        # heading: look a few frames ahead while walking
        walking = None
        for p in paths:
            if p[0][0] <= f + 4 and f - 2 <= p[-1][0]:
                walking = p
        if walking is not None:
            ax, ay = path_pos(walking, f + 4)
            bx, by = path_pos(walking, f - 1)
            if math.hypot(ax - bx, ay - by) > 1e-4:
                target = math.atan2(ax - bx, -(ay - by))
            else:
                target = math.radians(interp_keys(C["face"], f))
        else:
            target = math.radians(interp_keys(C["face"], f))
        heading += wrap(target - heading) * 0.22

        s, c = math.sin(phase), math.cos(phase)
        a = amp_s
        bob = 0.014 * a * (c * c) - 0.006 * a
        put("location", 0, f, x)
        put("location", 1, f, y)
        put("location", 2, f, bob)
        put("rotation_euler", 2, f, heading)

        breathe = math.sin(2 * math.pi * f / 72.0)
        pb = 'pose.bones["%s"].rotation_euler'
        # legs + feet
        put(pb % "leg.L", 0, f, -C["swing"] * a * s)
        put(pb % "leg.R", 0, f, C["swing"] * a * s)
        put(pb % "foot.L", 0, f, 0.6 * C["swing"] * a * s * (1 if s > 0 else 0.4))
        put(pb % "foot.R", 0, f, -0.6 * C["swing"] * a * s * (1 if s < 0 else 0.4))
        # torso
        put(pb % "hips", 1, f, 0.10 * a * s)
        put(pb % "hips", 2, f, 0.03 * a * c)
        put(pb % "chest", 0, f, 0.07 * a + 0.02 * breathe)
        put(pb % "chest", 1, f, -0.16 * a * s)

        # arms: walk swing, then wave on top
        arm = {
            "L": dict(ux=C["arm"] * a * s, uz=-0.12 - 0.05 * breathe, fx=-0.15 - 0.25 * a, fz=0.0, hz=0.0),
            "R": dict(ux=-C["arm"] * a * s, uz=0.12 + 0.05 * breathe, fx=-0.15 - 0.25 * a, fz=0.0, hz=0.0),
        }
        talk_tilt = 0.0
        for (w0, w1, side) in C["waves"]:
            w = smooth((f - w0) / 7.0) * smooth((w1 - f) / 7.0)
            if w <= 0:
                continue
            sg = side_sign[side]
            wig = math.sin(2 * math.pi * (f - w0) / 9.0)
            # Short arms + big head: a raised hand ends up by the cheek, so keep the
            # upper arm level and out to the side, slightly forward, and wave the
            # forearm between ~10 and ~45 degrees above level.
            target = dict(ux=-0.35, uz=sg * 1.6, fx=-0.1, fz=sg * (0.3 + 0.3 * wig), hz=sg * 0.3 * wig)
            for k in arm[side]:
                arm[side][k] = arm[side][k] * (1 - w) + target[k] * w
            talk_tilt += 0.06 * w * sg
        # fingers (v002 rigs): relaxed curl, opening flat and spread while waving
        open_w = {"L": 0.0, "R": 0.0}
        for (w0, w1, side) in C["waves"]:
            open_w[side] = max(open_w[side], smooth((f - w0 + 3) / 6.0) * smooth((w1 - f + 3) / 6.0))
        for side in "LR":
            if "finger_index." + side not in rig.pose.bones:
                continue
            w = open_w[side]
            for i, name in enumerate(("index", "middle", "ring", "pinky")):
                relax = -0.35 - 0.08 * i - 0.06 * a * math.sin(phase + i * 0.6)
                curl = relax * (1 - w) + 0.12 * w
                spread = w * (0.28, 0.09, -0.09, -0.28)[i] * (1 if side == "L" else -1)
                put(pb % ("finger_%s.%s" % (name, side)), 0, f, curl)
                put(pb % ("finger_%s.%s" % (name, side)), 2, f, spread)
            put(pb % ("thumb." + side), 0, f, -0.15 * (1 - w))

        for side in "LR":
            A = arm[side]
            put(pb % ("upper_arm." + side), 0, f, A["ux"])
            put(pb % ("upper_arm." + side), 2, f, A["uz"])
            put(pb % ("forearm." + side), 0, f, A["fx"])
            put(pb % ("forearm." + side), 2, f, A["fz"])
            put(pb % ("hand." + side), 2, f, A["hz"])

        # head: small nods while talking, gentle tilt with the wave
        nod = 0.0
        for (t0, t1) in C["talk"]:
            if t0 <= f <= t1:
                nod = 0.05 * math.sin(2 * math.pi * (f - t0) / 14.0)
        put(pb % "head", 0, f, nod - 0.03 * a)
        put(pb % "head", 2, f, -talk_tilt)

        # face sliders
        put('["look_x"]', 0, f, interp_keys(C["look"], f))
        bl = 0.0
        for b in C["blinks"]:
            if b <= f < b + 2:
                bl = (f - b + 1) / 2
            elif b + 2 <= f <= b + 3:
                bl = 1.0
            elif b + 3 < f <= b + 7:
                bl = 1 - (f - b - 3) / 4
        put('["blink"]', 0, f, bl)
        put('["brows"]', 0, f, 0.5 * sum(smooth((f - w0) / 6) * smooth((w1 - f) / 6) for w0, w1, _ in C["waves"]))

    # write dense curves
    for (path, idx), kv in chans.items():
        fc = act.fcurve_ensure_for_datablock(rig, path, index=idx)
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(kv))
        flat = [c for fv in kv for c in fv]
        fc.keyframe_points.foreach_set("co", flat)
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

    # mouth: constant keys
    fc = act.fcurve_ensure_for_datablock(rig, '["mouth"]')
    keys = [(0, 0)]
    for i, (t0, t1) in enumerate(C["talk"]):
        keys += mouth_seq(sum(map(ord, rig_name)) + i, t0, t1)
    fc.keyframe_points.clear()
    for f, v in keys:
        kp = fc.keyframe_points.insert(f, v)
        kp.interpolation = 'CONSTANT'
    return act


def camera():
    cam = bpy.data.objects["GR_cam"]
    cam.animation_data_clear()
    for keys, idx in ((CAM_X, 0), (CAM_Y, 1)):
        for f, v in keys:
            cam.location[idx] = v
            cam.keyframe_insert("location", index=idx, frame=f)
    for fc in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'


def run():
    S = bpy.context.scene
    S.frame_start, S.frame_end = 1, END
    for name, C in CHOREO.items():
        bake(name, C)
    camera()
    S.frame_set(1)


run()

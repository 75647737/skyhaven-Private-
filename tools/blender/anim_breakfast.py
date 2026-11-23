"""Breakfast scene (Episode 1, scene 2 sketch) — breakfast_v001.blend.

Shot 1 (kitchen, stove): Tori cooks one egg with Max on her left hip, talks to
  him, Max giggles; she puts the spatula down, goes to the doorway and calls Ace.
Shot 2 (living room): Ace sketches his drone on a napkin, answers, walks off.
Shot 3 (kitchen, table): Tori sits with Max on her lap; Ace comes in, greets
  Max, sits; "Still dreaming?" / "Still planning." / "Eat, before it gets cold."

Voices: episodes/breakfast-test/voices/<id>.mp3 + .json (ElevenLabs timing),
made by tools/audio/elevenlabs_tts.py. Lip-sync is keyed from that timing on
each rig's `mouth` slider; faces (brows, tilt, looks, blinks, head) are keyed
from the EXPR blocks below. Run inside Blender with the scene open; re-run
after editing. Uses the walk model of anim_family_walk.py.
"""
import bpy, json, math, os, random
from mathutils import Matrix, Vector

FPS = 24
END = 792
VOICE_DIR = bpy.path.abspath("//../../../episodes/breakfast-test/voices")

LINES = {  # id: start frame
    "L01": 30, "L02": 118, "L03": 222, "L04": 272,
    "L05": 490, "L06": 533, "L07": 628, "L08": 662, "L09": 706,
}
CUTS = [(1, "BF_cam_stove"), (240, "BF_cam_living"), (400, "BF_cam_table")]
SPEAKER = {"Ace": "AC.rig", "Tori": "TC.rig", "Max": "MX.rig"}

# ---------------------------------------------------------------- choreography
TORI = dict(
    rig="TC.rig", stride=0.17, step_frames=10.5,
    # a path with one point is an instant move (done off camera, during a cut)
    paths=[[(0, 3.84, 0.90)],
           [(168, 3.84, 0.90), (214, 3.32, 0.40)],
           [(399, 4.72, 0.66)]],
    face=[(0, 180), (50, 180), (72, -40), (122, -40), (142, 180), (164, 180), (216, -72), (300, -72), (399, 0), (END, 0)],
    sit=[(0, 0), (398, 0), (399, 1), (END, 1)],
    gestures=[(0, 54, "cook", "R"), (54, 126, "hold_spatula", "R"), (126, 152, "cook", "R"),
              (150, 166, "put_down", "R"), (214, 266, "call", "R"),
              (0, 398, "carry_hip", "L"), (399, END, "carry_lap", "L"),
              (410, 700, "table", "R"), (700, 760, "mug", "R"), (760, END, "table", "R")],
    expr={"brows": [(0, 0.1), (40, 0.25), (95, 0.45), (115, 0.3), (220, 0.7), (262, 0.2), (480, 0.35),
                    (626, 0.5), (650, 0.35), (700, 0.25), (745, 0.15)],
          "brow_tilt": [(0, 0.0), (30, 0.15), (115, 0.0), (700, 0.25), (750, 0.15)],
          "look_x": [(0, 0.0), (60, 0.2), (85, 0.7), (112, 0.7), (130, 0.0), (214, 0.0), (264, 0.0),
                     (400, -0.5), (470, 0.5), (540, 0.4), (600, 0.6), (626, 0.7), (656, 0.6), (700, 0.2), (730, 0.0)],
          "look_y": [(0, -0.4), (85, 0.0), (160, 0.0), (400, 0.0), (700, -0.3), (730, 0.0)],
          "head_yaw": [(0, 0.0), (60, 0.1), (85, 0.4), (112, 0.4), (130, 0.05), (214, 0.0), (400, -0.15), (470, 0.25),
                       (540, 0.15), (620, 0.3), (656, 0.3), (700, 0.1), (745, 0.0)],
          "head_tilt": [(0, 0.0), (90, -0.12), (112, -0.08), (130, 0.0), (626, -0.14), (656, -0.06), (706, 0.1), (740, 0.0)],
          "head_pitch": [(0, 0.12), (80, 0.04), (130, 0.08), (160, 0.0), (214, -0.05), (264, 0.0), (700, 0.05), (745, 0.0)],
          "smile": [(0, 1)]},
    extra_blinks=[100, 266, 452, 655],
)
ACE = dict(
    rig="AC.rig", stride=0.21, step_frames=8.8,
    paths=[[(0, 0.78, 0.52)],
           [(345, 0.78, 0.52), (398, 2.05, 0.28)],
           [(399, 3.05, 0.40), (440, 4.20, 0.90), (488, 5.14, 0.98)],
           [(578, 5.14, 0.98), (590, 5.30, 0.98), (606, 5.30, 0.68)]],
    face=[(0, 18), (300, 18), (330, 18), (488, 0), (540, -20), (574, -20), (606, 0), (END, 0)],
    sit=[(0, 0), (606, 0), (620, 1), (END, 1)],
    gestures=[(0, 344, "sketch", "LR"), (345, 612, "hold_napkin", "L"), (500, 528, "wave_small", "R"),
              (622, END, "table", "LR")],
    expr={"brows": [(0, -0.15), (262, -0.1), (270, 0.5), (300, 0.2), (312, -0.2), (335, 0.3), (400, 0.2),
                    (488, 0.6), (530, 0.5), (575, 0.2), (628, 0.35), (662, 0.45), (690, 0.4), (720, 0.2)],
          "brow_tilt": [(0, -0.15), (262, 0.0), (700, 0.1)],
          "look_x": [(0, 0.0), (262, 0.0), (268, 0.8), (300, 0.7), (312, 0.0), (400, 0.3), (488, -0.6),
                     (575, 0.0), (626, -0.7), (700, -0.3), (740, 0.0)],
          "look_y": [(0, -0.8), (262, -0.8), (268, 0.1), (300, 0.0), (312, -0.8), (336, 0.0), (488, -0.4),
                     (575, 0.0), (700, -0.2), (740, 0.0)],
          "head_yaw": [(0, 0.0), (262, 0.0), (270, 0.45), (305, 0.4), (316, 0.0), (488, -0.35), (575, 0.0),
                       (626, -0.3), (700, -0.2), (740, 0.0)],
          "head_tilt": [(0, 0.05), (262, 0.05), (490, 0.15), (530, 0.1), (575, 0.0), (662, 0.08), (695, 0.0)],
          "head_pitch": [(0, 0.22), (262, 0.22), (270, 0.0), (312, 0.18), (336, 0.0), (488, 0.15), (575, 0.0)],
          "smile": [(0, 0), (336, 1), (400, 1)]},
    extra_blinks=[250, 340, 486, 640],
    wink=(694, 704, "R"),
)
MAX = dict(
    rig="MX.rig", parent="TC.rig", scale=0.61,
    expr={"brows": [(0, 0.3), (118, 0.7), (165, 0.4), (533, 0.8), (575, 0.4), (720, 0.8), (770, 0.4)],
          "look_x": [(0, 0.2), (40, -0.3), (90, 0.5), (118, 0.6), (165, 0.0), (222, -0.6), (264, 0.0),
                     (400, -0.6), (470, 0.6), (575, 0.3), (628, 0.6), (662, 0.7), (706, -0.4), (740, 0.0)],
          "look_y": [(0, -0.3), (90, 0.3), (165, 0.0), (480, 0.5), (575, 0.0)],
          "head_yaw": [(0, 0.1), (40, -0.2), (90, 0.15), (165, 0.0), (222, -0.35), (264, 0.0),
                       (400, -0.4), (470, 0.45), (575, 0.2), (628, 0.3), (662, 0.35), (706, -0.2), (740, 0.0)],
          "head_pitch": [(0, 0.1), (90, -0.15), (165, 0.0), (480, -0.25), (575, 0.0)],
          "smile": [(0, 1)]},
    gestures=[(118, 165, "giggle"), (533, 578, "reach_up"), (718, 768, "clap")],
    extra_blinks=[60, 200, 330, 460, 600, 690],
)
CAMS = {
    "BF_cam_stove": dict(lens=28, keys=[(1, (2.93, -0.20, 0.80), (3.95, 0.86, 0.52)),
                                        (160, (2.95, -0.10, 0.78), (3.85, 0.80, 0.52)),
                                        (239, (2.90, -0.85, 0.74), (3.38, 0.45, 0.50))]),
    "BF_cam_living": dict(lens=33, keys=[(240, (0.45, -1.25, 0.68), (0.80, 0.52, 0.55)),
                                         (399, (0.55, -1.10, 0.66), (0.95, 0.50, 0.52))]),
    "BF_cam_table": dict(lens=36, keys=[(400, (5.0, -1.85, 0.66), (5.0, 0.45, 0.42)),
                                        (640, (5.0, -1.85, 0.66), (5.0, 0.45, 0.42)),
                                        (END, (5.0, -1.55, 0.64), (5.0, 0.48, 0.44))]),
}


# ---------------------------------------------------------------- helpers
def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def keyval(keys, f, ease=True):
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            u = (f - f0) / max(1e-6, (f1 - f0))
            return v0 + (v1 - v0) * (smooth(u) if ease else u)
    return keys[-1][1]


def path_pos(path, f):
    if len(path) == 1:
        return path[0][1], path[0][2]
    f0, f1 = path[0][0], path[-1][0]
    pts = [(p[1], p[2]) for p in path]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total, T = sum(seg), f1 - f0
    e = min(10.0, T / 3)
    vmax = total / (T - e)
    t = max(0.0, min(T, f - f0))
    s = vmax * t * t / (2 * e) if t < e else (total - vmax * (T - t) ** 2 / (2 * e) if t > T - e else vmax * (e / 2) + vmax * (t - e))
    for i, L in enumerate(seg):
        if s <= L or i == len(seg) - 1:
            u = 0 if L == 0 else min(1, s / L)
            a, b = pts[i], pts[i + 1]
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        s -= L
    return pts[-1]


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def override(name):
    return [o for o in bpy.context.scene.objects if o.name == name and o.library is None][0]


def new_action(rig, name):
    ad = rig.animation_data or rig.animation_data_create()
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad.action = act
    return act


def write(act, rig, chans):
    for (path, idx), kv in chans.items():
        fc = act.fcurve_ensure_for_datablock(rig, path, index=idx)
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(kv))
        fc.keyframe_points.foreach_set("co", [c for fv in kv for c in fv])
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()


def write_const(act, rig, path, keys):
    fc = act.fcurve_ensure_for_datablock(rig, path)
    fc.keyframe_points.clear()
    for f, v in keys:
        fc.keyframe_points.insert(f, v).interpolation = 'CONSTANT'


PB = 'pose.bones["%s"].%s'


# ---------------------------------------------------------------- lip-sync
VOWEL = {"a": 2, "i": 2, "e": 3, "o": 4, "u": 5, "w": 5, "y": 3}
CONS = {"m": 6, "b": 6, "p": 6, "f": 7, "v": 7}


def load_line(lid):
    p = os.path.join(VOICE_DIR, lid + ".json")
    return json.load(open(p, encoding="utf-8"))


def mouth_keys_for(lid, start, rest):
    d = load_line(lid)
    keys, last = [], None
    chars, st, en = d["chars"], d["starts"], d["ends"]
    for i, ch in enumerate(chars):
        c = ch.lower()
        f = start + int(round(st[i] * FPS))
        if c in VOWEL:
            v = VOWEL[c]
        elif c in CONS:
            v = CONS[c]
        elif c.isalpha():
            v = 3 if c in "sztdnckgjxlr" else 1
        else:
            gap = (st[i + 1] if i + 1 < len(st) else en[i]) - st[i]
            v = 1 if gap > 0.10 else None
        if v is None or v == last:
            continue
        if keys and f - keys[-1][0] < 2:        # hold every shape at least 2 frames
            if v in (6, 7):                     # but always show lip closures
                keys[-1] = (keys[-1][0], v)
                last = v
            continue
        keys.append((f, v))
        last = v
    end = start + int(math.ceil(d["duration"] * FPS))
    keys.append((end + 1, rest))
    return keys, end


def talk_spans(who):
    out = []
    for lid, s in LINES.items():
        d = load_line(lid)
        if d["who"] == who:
            out.append((s, s + int(math.ceil(d["duration"] * FPS))))
    return out


def auto_blinks(seed, extra):
    rnd = random.Random(seed)
    b, f = list(extra), 20 + rnd.randint(0, 30)
    while f < END:
        if all(abs(f - e) > 25 for e in extra):
            b.append(f)
        f += rnd.randint(55, 105)
    return sorted(b)


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


def face_and_mouth(put, act, rig, who, C, f_range, talk):
    blinks = auto_blinks(sum(map(ord, who)), C.get("extra_blinks", []))
    E = C["expr"]
    for f in f_range:
        talking = any(a <= f <= b for a, b in talk)
        env = 0.0
        for a, b in talk:
            if a <= f <= b:
                env = 0.5 + 0.5 * math.sin(2 * math.pi * (f - a) / 11.0)
        put('["brows"]', 0, f, keyval(E["brows"], f) + 0.12 * env * (1 if talking else 0))
        if "brow_tilt" in E:
            put('["brow_tilt"]', 0, f, keyval(E["brow_tilt"], f))
        put('["look_x"]', 0, f, keyval(E["look_x"], f))
        if "look_y" in E:
            put('["look_y"]', 0, f, keyval(E["look_y"], f))
        put('["blink"]', 0, f, blink_value(blinks, f))
        if C.get("wink"):
            w0, w1, side = C["wink"]
            wv = smooth((f - w0) / 2) * smooth((w1 - f) / 3)
            put('["blink_%s"]' % side, 0, f, wv)
    # mouth from the voice timing
    rest_keys = [(0, 0 if keyval(E["smile"], 0) >= 0.5 else 1)]
    for lid, s in sorted(LINES.items(), key=lambda kv: kv[1]):
        d = load_line(lid)
        if d["who"] != who:
            continue
        rest = 0 if keyval(E["smile"], s + 40) >= 0.5 else 1
        k, end = mouth_keys_for(lid, s, rest)
        rest_keys += k
    rest_keys.sort()
    write_const(act, rig, '["mouth"]', rest_keys)


def head_motion(put, f, E, talk, extra_pitch=0.0, extra_yaw=0.0):
    nod = 0.0
    for a, b in talk:
        if a <= f <= b:
            nod = 0.045 * math.sin(2 * math.pi * (f - a) / 13.0) * smooth((f - a) / 4) * smooth((b - f) / 4)
    put(PB % ("head", "rotation_euler"), 0, f, keyval(E.get("head_pitch", [(0, 0)]), f) + nod + extra_pitch)
    put(PB % ("head", "rotation_euler"), 1, f, keyval(E.get("head_yaw", [(0, 0)]), f) + extra_yaw)
    put(PB % ("head", "rotation_euler"), 2, f, keyval(E.get("head_tilt", [(0, 0)]), f))


# ---------------------------------------------------------------- arm poses
def arm(ux=0.0, uz=0.0, fx=-0.2, fz=0.0, hx=0.0, hz=0.0, curl=-0.35, spread=0.0, thumb=-0.15):
    return dict(ux=ux, uz=uz, fx=fx, fz=fz, hx=hx, hz=hz, curl=curl, spread=spread, thumb=thumb)


def sgn(side):
    return 1 if side == "R" else -1      # outward Z sign for upper arm / forearm


def gesture_pose(kind, side, f, f0):
    s = sgn(side)
    t = f - f0
    if kind == "carry_hip":      # forearm along her side under Max, upper arm a little out
        return arm(ux=-0.10, uz=s * 0.42, fx=-1.55, fz=s * -0.05, hz=s * -0.2, curl=-0.9)
    if kind == "carry_lap":      # arm round Max's tummy
        return arm(ux=-0.55, uz=s * -0.05, fx=-1.35, fz=s * -0.75, hz=s * -0.3, curl=-0.7)
    if kind == "cook":           # spatula over the pan, little flips
        flip = math.sin(2 * math.pi * t / 22.0)
        return arm(ux=-1.55 + 0.08 * flip, uz=s * 0.10, fx=-0.55 + 0.25 * max(0, flip), fz=s * -0.15, hx=0.25 * flip,
                   curl=-1.25, thumb=-0.6)
    if kind == "hold_spatula":   # spatula held low while she talks to Max
        return arm(ux=-0.45, uz=s * 0.18, fx=-0.95, fz=s * -0.1, hx=-0.2, curl=-1.25, thumb=-0.6)
    if kind == "put_down":       # reach right and down to the counter
        return arm(ux=-1.25, uz=s * 0.45, fx=-0.4, fz=0.0, curl=-0.6)
    if kind == "call":           # hand cupped beside the mouth
        return arm(ux=-1.05, uz=s * -0.15, fx=-2.15, fz=s * -0.55, hz=s * 0.3, curl=-0.55, spread=0.0, thumb=-0.4)
    if kind == "sketch":         # L holds the napkin at the chest, R draws with the pencil
        if side == "L":
            return arm(ux=-0.80, uz=s * -0.30, fx=-1.45, fz=s * -0.35, hz=s * -0.3, curl=-0.5, thumb=-0.5)
        stroke = math.sin(2 * math.pi * t / 14.0)
        lift = 1.0 if (t // 30) % 3 == 2 else 0.0      # pause every third beat
        return arm(ux=-0.85 + 0.05 * stroke * (1 - lift), uz=s * -0.42, fx=-1.55 + 0.08 * stroke * (1 - lift),
                   fz=s * -0.30, hz=s * 0.15 * stroke, curl=-1.1, thumb=-0.6)
    if kind == "hold_napkin":
        return arm(ux=-0.45, uz=s * -0.15, fx=-1.0, fz=s * -0.2, curl=-0.5, thumb=-0.5)
    if kind == "wave_small":
        wig = math.sin(2 * math.pi * t / 8.0)
        return arm(ux=-0.9, uz=s * 0.55, fx=-0.9, fz=s * (0.2 + 0.25 * wig), hz=s * 0.2 * wig, curl=0.1,
                   spread=0.25, thumb=0.0)
    if kind == "table":          # forearms resting on the table edge
        return arm(ux=-0.75, uz=s * 0.12, fx=-0.75, fz=s * -0.35, hz=s * -0.2, curl=-0.45)
    if kind == "mug":            # hand round the mug
        return arm(ux=-0.70, uz=s * 0.35, fx=-0.80, fz=s * -0.15, hz=0.0, curl=-1.0, thumb=-0.6)
    return None


def walk_arm(side, leg_x, a, breathe):
    swing = -0.85 * leg_x
    out = 0.13 if side == "R" else -0.13
    return arm(ux=swing, uz=out + (0.04 if side == "R" else -0.04) * breathe,
               fx=-0.18 - 0.2 * a - 0.45 * max(0.0, -swing), curl=-0.35 - 0.05 * a)


def blend(a, b, w):
    return {k: a[k] * (1 - w) + b[k] * w for k in a}


def put_arm(put, rig, f, side, A):
    put(PB % ("upper_arm." + side, "rotation_euler"), 0, f, A["ux"])
    put(PB % ("upper_arm." + side, "rotation_euler"), 2, f, A["uz"])
    put(PB % ("forearm." + side, "rotation_euler"), 0, f, A["fx"])
    put(PB % ("forearm." + side, "rotation_euler"), 2, f, A["fz"])
    put(PB % ("hand." + side, "rotation_euler"), 0, f, A["hx"])
    put(PB % ("hand." + side, "rotation_euler"), 2, f, A["hz"])
    if "finger_index." + side in rig.pose.bones:
        for i, n in enumerate(("index", "middle", "ring", "pinky")):
            put(PB % ("finger_%s.%s" % (n, side), "rotation_euler"), 0, f, A["curl"] - 0.06 * i * (A["curl"] < -0.2))
            put(PB % ("finger_%s.%s" % (n, side), "rotation_euler"), 2, f,
                A["spread"] * (0.28, 0.09, -0.09, -0.28)[i] / 0.28 * (1 if side == "L" else -1))
        put(PB % ("thumb." + side, "rotation_euler"), 0, f, A["thumb"])


# ---------------------------------------------------------------- walkers (Ace, Tori)
def bake_person(C, who):
    rig = override(C["rig"])
    act = new_action(rig, "BF_%s" % who.lower())
    chans = {}
    put = lambda path, idx, f, v: chans.setdefault((path, idx), []).append((f, v))
    sc = rig.scale.z
    Lf = rig.data.bones["leg.L"].head_local.z * sc
    stride = C["stride"]
    a_max = math.asin(min(0.9, 0.5 * stride / Lf))
    nominal = stride / C["step_frames"]
    talk = talk_spans(who)
    paths = C["paths"]
    prev, dist, amp = None, 0.0, 0.0
    heading = math.radians(C["face"][0][1])
    for f in range(0, END + 1):
        # position: the last path that has started
        cur = [p for p in paths if p[0][0] <= f][-1]
        x, y = path_pos(cur, f) if f <= cur[-1][0] else (cur[-1][1], cur[-1][2])
        jump = prev is None or math.hypot(x - prev[0], y - prev[1]) > 0.15
        speed = 0.0 if jump else math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
        dist += speed
        amp = 0.0 if jump else amp + (min(1.0, speed / (nominal * 0.75)) - amp) * 0.3
        a = amp
        # heading
        target = None
        if len(cur) > 1 and cur[0][0] <= f <= cur[-1][0] + 2:
            ax, ay = path_pos(cur, min(f + 4, cur[-1][0]))
            bx, by = path_pos(cur, max(f - 1, cur[0][0]))
            if math.hypot(ax - bx, ay - by) > 1e-3:
                target = math.atan2(ax - bx, -(ay - by))
        if target is None:
            target = math.radians(keyval(C["face"], f))
        heading = target if jump else heading + wrap(target - heading) * 0.2
        sit = keyval(C["sit"], f)

        # gait
        u = dist / stride
        k = int(math.floor(u))
        ph = u - k
        stance = "L" if k % 2 == 0 else "R"
        swing = "R" if stance == "L" else "L"
        st = math.asin(max(-0.95, min(0.95, (ph - 0.5) * stride / Lf)))
        e = ph * ph * (3 - 2 * ph)
        leg = {stance: st * a, swing: a_max * (1 - 2 * e) * a}
        lift = {stance: 0.0, swing: 0.11 * a * math.sin(math.pi * ph)}
        roll_st = -0.28 * smooth(1 - ph / 0.18) + 0.22 * smooth((ph - 0.7) / 0.3)
        foot = {stance: -leg[stance] + roll_st * a, swing: -leg[swing] - 0.18 * math.sin(math.pi * ph) * a}
        bob = (Lf * math.cos(st) - Lf) * a - 0.004 * a * math.exp(-((ph - 0.08) / 0.08) ** 2)
        drop = (Lf - 0.24) * sit
        put("location", 0, f, x)
        put("location", 1, f, y)
        put("location", 2, f, bob - drop)
        put("rotation_euler", 2, f, heading)
        sg_st = 1 if stance == "L" else -1
        breathe = math.sin(2 * math.pi * f / 72.0)
        for s in "LR":
            put(PB % ("leg." + s, "rotation_euler"), 0, f, leg[s] * (1 - sit) - 1.50 * sit)
            put(PB % ("leg." + s, "rotation_euler"), 2, f, 0.10 * sit * (1 if s == "L" else -1) * -1)
            put(PB % ("leg." + s, "scale"), 1, f, 1.0 - lift[s] * (1 - sit))
            put(PB % ("foot." + s, "rotation_euler"), 0, f, foot[s] * (1 - sit) + 0.45 * sit)
        twist = 0.11 * a * math.cos(math.pi * ph) * sg_st
        tilt = 0.035 * a * math.sin(math.pi * ph) * sg_st
        put(PB % ("hips", "rotation_euler"), 1, f, twist)
        put(PB % ("hips", "rotation_euler"), 2, f, tilt)
        put(PB % ("chest", "rotation_euler"), 0, f, 0.06 * a + 0.02 * breathe + 0.06 * sit)
        put(PB % ("chest", "rotation_euler"), 1, f, -1.5 * twist)
        put(PB % ("chest", "rotation_euler"), 2, f, -0.8 * tilt)

        # arms: walk swing, then gestures on top
        A = {s: walk_arm(s, leg[s], a, breathe) for s in "LR"}
        for (g0, g1, kind, sides) in C["gestures"]:
            w = smooth((f - g0 + 6) / 6.0) * smooth((g1 - f + 6) / 6.0) if g0 > 0 else smooth((g1 - f + 6) / 6.0)
            if w <= 0:
                continue
            for s in sides:
                P = gesture_pose(kind, s, f, g0)
                if P:
                    A[s] = blend(A[s], P, w)
        for s in "LR":
            put_arm(put, rig, f, s, A[s])
        head_motion(put, f, C["expr"], talk, extra_pitch=-0.03 * a)
    write(act, rig, chans)
    chans.clear()
    face_and_mouth(put, act, rig, who, C, range(0, END + 1), talk)
    write(act, rig, chans)
    return rig


# ---------------------------------------------------------------- Max
def bake_max():
    S = bpy.context.scene
    mx = override(MAX["rig"])
    mom = override(MAX["parent"])
    mx.scale = (MAX["scale"],) * 3
    act = new_action(mx, "BF_max")
    chans = {}
    put = lambda path, idx, f, v: chans.setdefault((path, idx), []).append((f, v))
    hip_h = mx.data.bones["hips"].head_local.z * MAX["scale"]
    talk = talk_spans("Max")
    prev_rot = None
    for f in range(0, END + 1):
        S.frame_set(f)
        mw = mom.matrix_world
        heading = mom.matrix_world.to_euler('XYZ').z
        lap = keyval(TORI["sit"], f) > 0.5
        if not lap:
            # bottom on her left forearm, back against her left side, facing out to the front-left
            fa = mom.pose.bones["forearm.L"]
            p0, p1 = mw @ fa.head, mw @ fa.tail
            seat = p0.lerp(p1, 0.45) + Vector((0, 0, 0.028))
            side_in = (mw.to_3x3() @ Vector((-1, 0, 0))).normalized() * 0.012   # snug toward her
            seat += side_in
            yaw = heading + math.radians(70)
        else:
            hb = mw @ mom.pose.bones["hips"].matrix
            seat = hb @ Vector((0.075, 0.075, 0.115))       # on her left thigh (bone: x left, y up, z fwd)
            yaw = heading + math.radians(8)
        R = Matrix.Rotation(yaw, 4, 'Z')
        loc = seat - Vector((0, 0, hip_h))
        eul = R.to_euler('XYZ', prev_rot) if prev_rot else R.to_euler('XYZ')
        prev_rot = eul
        for i in range(3):
            put("location", i, f, loc[i])
        put("rotation_euler", 2, f, eul.z)
        put("rotation_euler", 0, f, 0.0)
        put("rotation_euler", 1, f, 0.0)

        jig = math.sin(2 * math.pi * f / 11.0)
        put(PB % ("hips", "rotation_euler"), 0, f, 0.0 if not lap else -0.05)
        put(PB % ("chest", "rotation_euler"), 0, f, 0.03 + 0.02 * math.sin(2 * math.pi * f / 60))
        for s, sx in (("L", 1), ("R", -1)):
            if not lap:   # straddling: legs forward and apart, little kicks
                lx = -0.95 + 0.12 * math.sin(2 * math.pi * f / 40 + (0 if s == "L" else 1.7))
                lz = 0.45 * -sx
            else:         # sitting on the lap: legs out in front
                lx = -1.40 + 0.10 * math.sin(2 * math.pi * f / 36 + (0 if s == "L" else 2.1))
                lz = 0.18 * -sx
            put(PB % ("leg." + s, "rotation_euler"), 0, f, lx)
            put(PB % ("leg." + s, "rotation_euler"), 2, f, lz)
            put(PB % ("foot." + s, "rotation_euler"), 0, f, 0.45)
        # arms
        if not lap:
            A = {"R": arm(ux=-0.55, uz=0.15, fx=-0.9, fz=-0.35, curl=-0.8),     # hand on mum's arm
                 "L": arm(ux=-0.30, uz=-0.25, fx=-0.55, curl=-0.5)}
        else:
            A = {"R": arm(ux=-0.70, uz=0.10, fx=-0.80, fz=-0.30, curl=-0.6),
                 "L": arm(ux=-0.70, uz=-0.10, fx=-0.80, fz=0.30, curl=-0.6)}
        for (g0, g1, kind) in MAX["gestures"]:
            w = smooth((f - g0 + 5) / 5.0) * smooth((g1 - f + 5) / 5.0)
            if w <= 0:
                continue
            t = f - g0
            for s in "LR":
                sg = sgn(s)
                if kind == "giggle":       # happy arm flaps
                    flap = math.sin(2 * math.pi * t / 7.0 + (0 if s == "L" else 1.0))
                    P = arm(ux=-0.9 + 0.25 * flap, uz=sg * (0.45 + 0.2 * flap), fx=-0.7, fz=sg * 0.2, curl=-0.2, spread=0.2, thumb=0.0)
                elif kind == "reach_up":   # both arms up to dad
                    open_ = math.sin(2 * math.pi * t / 9.0)
                    P = arm(ux=-2.2, uz=sg * 0.25, fx=-0.25, fz=sg * 0.1 * open_, curl=0.05 * open_, spread=0.3, thumb=0.0)
                elif kind == "clap":
                    c = 0.5 + 0.5 * math.sin(2 * math.pi * t / 8.0)
                    P = arm(ux=-1.05, uz=sg * -0.45, fx=-0.75, fz=sg * -(0.25 + 0.35 * c), hz=sg * -0.4, curl=0.05, spread=0.1, thumb=0.0)
                A[s] = blend(A[s], P, w)
        for s in "LR":
            put_arm(put, mx, f, s, A[s])
        bounce = 0.0
        for (g0, g1, kind) in MAX["gestures"]:
            if g0 <= f <= g1 and kind in ("giggle", "clap"):
                bounce = 0.05 * jig
        head_motion(put, f, MAX["expr"], talk, extra_pitch=-bounce)
    write(act, mx, chans)
    chans.clear()
    face_and_mouth(put, act, mx, "Max", MAX, range(0, END + 1), talk)
    write(act, mx, chans)
    # mouth open with joy while clapping (on top of the voice keys)
    fc = act.fcurve_ensure_for_datablock(mx, '["mouth"]')
    for f, v in ((718, 2), (740, 0), (744, 2), (766, 0)):
        fc.keyframe_points.insert(f, v).interpolation = 'CONSTANT'


# ---------------------------------------------------------------- props, cameras, sound
def set_vis(ob, frames):
    """frames: list of (frame, visible). Keys the object and its children."""
    for o in [ob] + list(ob.children):
        o.animation_data_clear()
        for f, vis in frames:
            o.hide_render = not vis
            o.hide_viewport = not vis
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)
        for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def props():
    O = bpy.data.objects
    tori, ace = override("TC.rig"), override("AC.rig")
    sp = O["BF.spatula_hand"]
    sp.parent_bone = "hand.R"
    sp.location = (0.0, -0.035, 0.0)
    sp.rotation_euler = (math.radians(-10), 0, 0)
    set_vis(sp, [(0, True), (160, False)])
    set_vis(O["BF.spatula_rest"], [(0, False), (160, True)])
    set_vis(O["BF.napkin_hand"], [(0, True), (612, False)])
    set_vis(O["BF.pencil_hand"], [(0, True), (612, False)])
    set_vis(O["BF.napkin_table"], [(0, False), (612, True)])
    # egg: in the pan until she plates it off camera (shot 3 shows the plates)
    for n in ("BF.pan_egg_white", "BF.pan_egg_yolk"):
        set_vis(O[n], [(0, True), (399, False)])


def cameras():
    S = bpy.context.scene
    for name, c in CAMS.items():
        cam = bpy.data.objects.get(name)
        if cam is None:
            cd = bpy.data.cameras.new(name)
            cam = bpy.data.objects.new(name, cd)
            S.collection.objects.link(cam)
        cam.data.lens = c["lens"]
        cam.animation_data_clear()
        for f, loc, tgt in c["keys"]:
            cam.location = loc
            cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_euler", frame=f)
    for m in list(S.timeline_markers):
        S.timeline_markers.remove(m)
    for f, name in CUTS:
        mk = S.timeline_markers.new(name, frame=f)
        mk.camera = bpy.data.objects[name]
    S.camera = bpy.data.objects[CUTS[0][1]]


def sound():
    S = bpy.context.scene
    ed = S.sequence_editor or S.sequence_editor_create()
    strips = ed.strips if hasattr(ed, "strips") else ed.sequences
    for st in list(strips):
        strips.remove(st)
    chan = {"Tori": 1, "Ace": 2, "Max": 3}
    for lid, s in LINES.items():
        d = load_line(lid)
        path = os.path.join(VOICE_DIR, lid + ".mp3")
        snd = strips.new_sound(lid + "_" + d["who"], path, chan[d["who"]], s)
        snd.volume = 1.0 if d["who"] != "Max" else 0.85
    S.render.use_sequencer = False


def run():
    S = bpy.context.scene
    S.frame_start, S.frame_end = 1, END
    S.render.fps = FPS
    # retire the greeting scene's actions on these rigs
    bake_person(TORI, "Tori")
    bake_person(ACE, "Ace")
    bake_max()
    props()
    cameras()
    sound()
    S.frame_set(1)


run()

"""Episode 1 sound: ElevenLabs voice lines + synthesised SFX, no music.
1) fits each line into the timeline (start = planned start, pushed later if the previous line in the
   same scene is still speaking; bubble end = voice end + 0.3 s) and rewrites timeline.js
2) mixes voices (Leo's call lines get a phone band-pass) and SFX into episode1_audio.wav"""
import json, re, subprocess, sys, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'audio'))
from beat_cinematic import SR, t_, lp, hp, reverb, add, boom, tom, tick, bell, env
rng = np.random.default_rng(3)
src = open(os.path.join(HERE, 'timeline.js')).read()
TL = json.loads(src[src.index('{'):src.rindex('}') + 1])

def load(p):
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', p, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    nz = np.where(np.abs(x) > 0.01)[0]                       # trim leading/trailing silence
    return x[max(0, nz[0] - 400):nz[-1] + 2400] if len(nz) else x

scene_of = lambda t: next(s['id'] for s in TL['scenes'] if s['t0'] <= t < s['t1'])
voices, prev_end, prev_scene = [], -1, None
for i, l in enumerate(TL['lines']):
    x = load(os.path.join(HERE, 'voices', f'L{i}.mp3'))
    if i == 10: x = x[:int(2.4 * SR)] * np.r_[np.ones(int(2.0 * SR)), np.linspace(1, 0, int(2.4 * SR) - int(2.0 * SR))][:len(x[:int(2.4 * SR)])]
    sc = scene_of(l[0]); start = l[0]
    if sc == prev_scene and start < prev_end + 0.25: start = prev_end + 0.25
    end = start + len(x) / SR
    l[0], l[1] = round(start, 2), round(end + 0.3, 2)
    voices.append((start, x, l[2])); prev_end, prev_scene = end, sc
    print(f'L{i:02d} {l[2]:7s} {start:7.2f}-{end:7.2f}  {l[3]}')

N = int(TL['duration'] * SR); vox = np.zeros(N); fx = np.zeros(N)
for start, x, who in voices:
    if who == 'phone': x = np.tanh(hp(lp(x, 3400), 380) * 2.2) * 0.75   # phone line
    add(vox, x, start)

# ---- SFX (all synthesised)
def noise(d): return rng.normal(0, 1, int(d * SR))
def whoosh(d=1.2):
    t = t_(d); n = noise(d); out = np.zeros_like(n); seg = int(.04 * SR)
    for k in range(0, len(n), seg):
        fc = 300 + 3000 * np.sin(np.pi * k / len(n)); out[k:k + seg] = lp(n[k:k + seg * 2], fc)[:len(out[k:k + seg])]
    return out * np.sin(np.pi * t / d) ** 2 * .5
def pop(): t = t_(.15); return np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 40) * .6
def flip(): return hp(noise(.25), 2000) * env(int(.25 * SR), .01, .06) * .5
def thud(): return tom(55, .8) * 1.1
def fall(): t = t_(1.5); return np.sin(2 * np.pi * np.cumsum(900 - 500 * t / 1.5) / SR) * .25 + whoosh(1.5) * .6
def drip(): t = t_(.18); return np.sin(2 * np.pi * np.cumsum(700 + 1600 * t / .18) / SR) * np.exp(-t * 30) * .35
def paperjet(): return whoosh(.9) * 1.2
def buzz():
    t = t_(4.5); on = ((t % 1.0) < .55).astype(float); return np.sign(np.sin(2 * np.pi * 150 * t)) * on * .12 * (1 - t / 9)
def toastpop():
    t = t_(.9); clk = hp(noise(.03), 3000) * .9; spr = np.sin(2 * np.pi * (220 + 140 * np.sin(2 * np.pi * 9 * t)) * t) * np.exp(-t * 5) * .35
    o = spr.copy(); o[:len(clk)] += clk; return o
def ding(): return bell(1318.5, 1.6) * .3
def dial():
    t = t_(2.2); return (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * ((t % 1.1) < .7) * .06
def bus(): return lp(noise(8.5), 180) * .5 * np.minimum(1, t_(8.5) / .5) * np.minimum(1, (8.5 - t_(8.5)) / .5)
def jet():
    d = 13.5; t = t_(d); return (lp(noise(d), 900) * .35 + hp(lp(noise(d), 5000), 2500) * .08) * np.minimum(1, t / 2)
def sting():   # one hit into the end card (shutter) + a bell that rings low under it
    t = t_(6); o = bell(587.33, 6)[:len(t)] * .25; b = boom(3.0); o[:len(b)] += b * .9; return o
SFX = dict(whoosh=whoosh, pop=pop, flip=flip, fall=fall, thud=thud, drip=drip, paperjet=paperjet, buzz=buzz, toastpop=toastpop,
           ding=ding, dial=dial, bus=bus, jet=jet)
for at, name in TL['sfx']: add(fx, SFX[name](), at)
add(fx, sting(), TL['shutter'])
room = reverb(vox, .5, .08, 9)
mix = room * 1.0 + reverb(fx, 1.2, .2, 4) * .55
end = int((TL['duration'] - .8) * SR); mix[end:] *= np.linspace(1, 0, N - end)
mix /= np.abs(mix).max() / .95
st = np.stack([mix, mix], 1)
out = os.path.join(HERE, 'episode1_audio.wav')
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'alimiter=limit=0.7:level=false', out],
               input=(st * 32767).astype(np.int16).tobytes(), check=True)
open(os.path.join(HERE, 'timeline.js'), 'w').write('window.TL = ' + json.dumps(TL, ensure_ascii=False, indent=1) + ';\n')
print('wrote', out)

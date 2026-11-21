"""Skytrade's own cinematic beat, synthesised from scratch (no samples, no licences).
Built on a cut grid so every hit lands on a video cut:  python3 audio/beat_cinematic.py out.wav [bar_seconds] [bars] [end_bars]
Layers: sub booms on cuts, taiko-style toms, a low string ostinato (D minor), a pad, a ticking clock,
a riser into the end card, a big final hit and a 3-note sonic logo (D-A-D)."""
import sys, numpy as np, subprocess
SR = 48000
rng = np.random.default_rng(7)

def t_(d): return np.arange(int(d * SR)) / SR
def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d); return e
def lp(x, fc):   # FFT low-pass with a soft roll-off
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))
def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (fc / np.maximum(f, 1)) ** 4); return np.fft.irfft(X, len(x))
def reverb(x, secs=2.2, wet=0.35, seed=1):
    r = np.random.default_rng(seed); n = int(secs * SR); ir = r.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 6.9 / secs)
    ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n; y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return x * (1 - wet) + y * wet * 1.2
def saw(f, t): return 2 * ((f * t) % 1) - 1
def add(buf, sig, at):
    i = int(at * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]

def boom(d=3.0):   # sub drop + distorted body + noise crack
    t = t_(d); f = 38 + 70 * np.exp(-t * 9); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.tanh(2.2 * np.sin(ph)) * np.exp(-t * 1.4)
    crack = hp(rng.normal(0, 1, len(t)), 1800) * np.exp(-t * 40) * 0.5
    return body + crack
def tom(f0=90, d=0.9):
    t = t_(d); f = f0 * (1 + 0.8 * np.exp(-t * 30)); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 6) + lp(rng.normal(0, 1, len(t)), 900) * np.exp(-t * 25) * 0.35
def tick(d=0.05):
    t = t_(d); return lp(hp(rng.normal(0, 1, len(t)), 5000), 11000) * np.exp(-t * 140)
def note(f, d, bright=1800):   # staccato low strings: detuned saws, filtered
    t = t_(d); s = sum(saw(f * k, t) for k in (1, 1.004, 0.996)) / 3
    return lp(s, bright) * env(len(t), 0.008, d * 0.45)
def pad(freqs, d):
    t = t_(d); s = sum(saw(f * k, t) for f in freqs for k in (1, 1.003, 0.997)) / (3 * len(freqs))
    a = np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.8); return lp(s, 900) * a
def riser(d):
    t = t_(d); n = rng.normal(0, 1, len(t)); out = np.zeros_like(t); seg = int(0.05 * SR)
    for k in range(0, len(t), seg):   # sweep the band up
        fc = 300 * (25 ** (k / len(t))); out[k:k + seg] = lp(n[k:k + seg * 2], fc)[:len(out[k:k + seg])]
    f = 110 * 4 ** (t / d); tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    return (out * 0.6 + tone) * (t / d) ** 2
def bell(f, d=2.5):
    t = t_(d); s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3) + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)
    return s * env(len(t), 0.003, 0.9)

def build(bar=2.3, bars=7, end_bars=2):
    beat = bar / 4; total = bar * (bars + end_bars) + 1.5
    N = int(total * SR); drums, strings, padb, fx, logo = (np.zeros(N) for _ in range(5))
    D, F, C, Bb, A = 73.42, 87.31, 65.41, 58.27, 55.0
    prog = [(D, [D, F * 1, A * 2]), (Bb, [Bb, D, F]), (F, [F, A * 2, C * 2]), (C, [C, 82.41, 98.0])]
    end = bar * bars
    for b in range(bars):
        t0 = b * bar
        add(drums, boom() * (1.0 if b % 2 == 0 else 0.75), t0)                      # boom on every cut
        for k, (pos, f0, g) in enumerate([(1.5, 95, .45), (2, 80, .6), (3, 95, .35), (3.5, 110, .4)]):
            if b == 0 and pos < 2: continue
            add(drums, tom(f0) * g, t0 + pos * beat)
        for s in range(16):                                                          # clock ticks on 16ths
            add(fx, tick() * (0.16 if s % 4 == 0 else 0.06), t0 + s * beat / 4)
        root, chord = prog[b % 4]
        for s in range(8):                                                           # string ostinato on 8ths
            f = root * (2 if s % 4 == 2 else 1) * (1.5 if s == 7 else 1)
            add(strings, note(f * 2, beat / 2 * 0.95, 1400 + 300 * (b / bars)) * (0.9 if s % 2 == 0 else 0.6), t0 + s * beat / 2)
        add(padb, pad(chord, bar + 0.6), t0)
    add(fx, riser(bar * 0.98) * 0.8, end - bar)                                     # build into the end card
    add(drums, boom(4.5) * 1.3, end)                                                 # the big final hit
    add(drums, tom(60, 1.6) * 1.0, end)
    add(padb, pad([D, A * 2, D * 2], bar * end_bars + 1.2) * 1.2, end)
    for k, f in enumerate([293.66, 440.0, 587.33]):                                  # sonic logo D-A-D
        add(logo, bell(f) * 0.5, end + 0.9 + k * beat * 0.75)
    mix = (reverb(drums, 1.6, 0.25, 1) * 0.9 + reverb(strings, 1.8, 0.3, 2) * 0.55 + reverb(padb, 3.0, 0.5, 3) * 0.5
           + reverb(fx, 1.2, 0.2, 4) * 0.5 + reverb(logo, 3.5, 0.55, 5) * 0.7)
    mix = np.tanh(mix * 1.1) ; mix /= np.abs(mix).max() / 0.89
    fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade) ** 2
    st = np.stack([mix, np.roll(mix, int(0.011 * SR)) * 0.96], 1)                   # a little stereo width
    return st

if __name__ == '__main__':
    out = sys.argv[1]; bar = float(sys.argv[2]) if len(sys.argv) > 2 else 2.3
    bars = int(sys.argv[3]) if len(sys.argv) > 3 else 7; eb = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    st = build(bar, bars, eb); pcm = (st * 32767).astype(np.int16).tobytes()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', out], input=pcm, check=True)
    print('wrote', out, round(len(st) / SR, 1), 's')

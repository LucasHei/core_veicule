"""Compose un beat phonk original de 30 s calé sur promo.html (120 BPM)
et l'ajoute à exo_ac_tiktok.mp4.

Repères de la vidéo (s) : coupes 3.5 / 7 / 19.5 / 25.5, tampons BAN 8.5 / 10.7 / 12.9 / 15.1 / 17.3.
"""
import pathlib
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
DUR = 30.0
BPM = 120
BEAT = 60 / BPM
STEP = BEAT / 4  # double-croche
HERE = pathlib.Path(__file__).parent
rng = np.random.default_rng(7)

mix = np.zeros(int(SR * DUR) + SR)


def t_(d):
    return np.arange(int(SR * d)) / SR


def add(sig, at, gain=1.0):
    i = int(at * SR)
    end = min(len(mix), i + len(sig))
    mix[i:end] += sig[: end - i] * gain


def filt(sig, kind, f):
    return sosfilt(butter(4, f, kind, fs=SR, output="sos"), sig)


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


# ---------- instruments ----------
def kick():
    t = t_(0.45)
    f = 45 + 110 * np.exp(-t * 28)
    return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7))


def clap():
    d = 0.25
    n = filt(noise(d), "bandpass", [900, 4500])
    env = np.zeros(int(SR * d))
    for k, o in enumerate((0, 0.012, 0.024)):
        s = int(o * SR)
        env[s:] += np.exp(-np.arange(len(env) - s) / SR * (60 if k < 2 else 16))
    return n * env * 0.9


def hat(open_=False):
    d = 0.18 if open_ else 0.05
    return filt(noise(d), "highpass", 7000) * np.exp(-t_(d) * (18 if open_ else 90)) * 0.35


def cowbell(f):
    t = t_(0.32)
    s = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    s = filt(s, "bandpass", [f * 0.8, f * 4])
    return s * np.exp(-t * 11) * 0.22


def bass808(f, d):
    t = t_(d)
    f_t = f * (1 + 0.6 * np.exp(-t * 40))
    env = np.minimum(1, t * 200) * np.exp(-t * 1.2)
    env[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f_t) / SR)) * env * 0.55


def impact():
    t = t_(1.6)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    crack = filt(noise(1.6), "lowpass", 3000) * np.exp(-t * 9) * 0.5
    return np.tanh(1.8 * (boom + crack)) * 0.9


def riser(d):
    t = t_(d)
    n = noise(d)
    out = np.zeros_like(n)
    chunks = 40
    for k in range(chunks):
        a, b = k * len(n) // chunks, (k + 1) * len(n) // chunks
        out[a:b] = filt(n, "bandpass", [200 + 8 * k ** 1.6, 400 + 25 * k ** 1.6])[a:b]
    return out * (t / d) ** 2 * 0.5


def stamp():
    t = t_(0.3)
    thump = np.sin(2 * np.pi * np.cumsum(60 + 200 * np.exp(-t * 50)) / SR) * np.exp(-t * 14)
    snap = filt(noise(0.3), "bandpass", [1500, 6000]) * np.exp(-t * 45)
    return np.tanh(2 * (thump + snap)) * 0.6


def glitch(d):
    t = t_(d)
    s = np.sign(np.sin(2 * np.pi * 180 * t)) * (rng.uniform(size=len(t)) > 0.5)
    return filt(s, "bandpass", [300, 3000]) * 0.15


# ---------- arrangement ----------
A1, F1, G1, E1, C2 = 55.0, 43.65, 49.0, 41.2, 65.4
BASS_BARS = [A1, A1, F1, G1]                        # une note par mesure
MELO = [440, 0, 523, 440, 0, 659, 587, 0, 523, 0, 440, 392, 0, 440, 0, 0]  # 16 doubles-croches


def bar_time(bar):
    return bar * 4 * BEAT


# Intro 0–3.5 : drone + riser + glitch, kicks espacés
intro_drone = np.sin(2 * np.pi * A1 * t_(3.5)) * np.linspace(0, 0.35, int(3.5 * SR))
add(intro_drone, 0)
add(riser(3.4), 0.1)
add(glitch(0.25), 1.1)
add(glitch(0.2), 2.3)
for b in (0, 2, 4, 5, 6):
    add(kick(), b * BEAT, 0.6)

# Coupes : impacts
for c in (3.5, 7.0, 19.5, 25.5):
    add(impact(), c, 0.9)

# Logo 3.5–7 : cowbell seul, pas de batterie
for i in range(int((7.0 - 3.5) / STEP)):
    f = MELO[i % 16]
    if f:
        add(cowbell(f), 3.5 + i * STEP, 0.8)
add(riser(1.2), 5.8, 0.6)

# Drop 7–25.5 : beat complet
start, end = 7.0, 25.5
n_steps = int(round((end - start) / STEP))
for i in range(n_steps):
    t = start + i * STEP
    s16 = i % 16
    bar = i // 16
    if s16 in (0, 6, 10) or (bar % 2 and s16 == 14):
        add(kick(), t)
    if s16 in (4, 12):
        add(clap(), t)
    add(hat(open_=(s16 % 8 == 6)), t, 1.0 if s16 % 2 == 0 else 0.6)
    if MELO[s16]:
        add(cowbell(MELO[s16] * (2 if bar % 4 == 3 and s16 > 8 else 1)), t)
    if s16 == 0:
        note = BASS_BARS[bar % 4]
        add(bass808(note, 4 * BEAT - 0.02), t)

# Respiration avant le panel (18.5–19.5) : on coupe les kicks via un trou dans le mix
gap_a, gap_b = int(18.75 * SR), int(19.5 * SR)
mix[gap_a:gap_b] *= np.linspace(1, 0.25, gap_b - gap_a)
add(riser(0.75), 18.75, 0.7)

# Tampons BAN
for s in (8.5, 10.7, 12.9, 15.1, 17.3):
    add(stamp(), s, 0.9)

# Outro 25.5–30 : 808 tenu + cowbell, puis fin nette
add(bass808(A1, 3.5), 25.5)
for i in range(32):
    f = MELO[i % 16]
    if f:
        add(cowbell(f), 25.5 + i * STEP, 0.7)
add(bass808(F1, 2.0), 27.5)
for b in range(int(4.5 / BEAT)):
    add(hat(), 25.5 + b * BEAT + BEAT / 2, 0.7)
add(kick(), 29.5, 1.0)
add(clap(), 29.5, 0.8)

# ---------- master ----------
out = mix[: int(SR * DUR)]
out = out / np.max(np.abs(out)) * 1.4
out = np.tanh(out) * 0.92
fade = int(0.25 * SR)
out[-fade:] *= np.linspace(1, 0, fade)
wav = HERE / "exo_ac_beat.wav"
wavfile.write(wav, SR, (out * 32767).astype(np.int16))

video = HERE / "exo_ac_tiktok.mp4"
final = HERE / "exo_ac_tiktok_son.mp4"
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav),
    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", str(final),
], check=True)
print(final)

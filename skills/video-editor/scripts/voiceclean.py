#!/usr/bin/env python3
"""Clean a voice recording: drop retakes/labels, shorten pauses > 0.5 s, level it.

Usage: voiceclean.py <audio> <words.json> <out.wav> [--remove "s-e" ...] [--remove-words "i-j" ...]
                     [--thresh -38] [--lufs -16]
  --remove        seconds range to drop (source time); suffix "!" (e.g. "239.95-245.55!") to cut exactly,
                  without snapping — use when the snap slides into a neighbouring word
  --remove-words  word-index range [i, j) from words.json to drop — from word i's start to word j's start
Every cut point is snapped to the quietest 50 ms within ±0.35 s, so no word gets clipped.
Writes <out.wav> (48 kHz mono), <out>.keep.json ([[s,e],...] source seconds) for remapping captions,
and prints how much was removed.
"""
import argparse, array, json, math, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("audio"); ap.add_argument("words"); ap.add_argument("out")
ap.add_argument("--remove", action="append", default=[])
ap.add_argument("--remove-words", action="append", default=[])
ap.add_argument("--thresh", type=float, default=-38.0, help="dBFS below which a 50 ms window counts as silence")
ap.add_argument("--maxgap", type=float, default=0.5); ap.add_argument("--pad", type=float, default=0.12)
ap.add_argument("--lufs", type=float, default=-16.0)
a = ap.parse_args()

SR, HOP = 8000, 400                                   # 50 ms windows for the envelope
raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", a.audio, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True).stdout
pcm = array.array("h"); pcm.frombytes(raw[: len(raw) // 2 * 2])
env = []
for i in range(0, len(pcm) - HOP, HOP):
    r = math.sqrt(sum(x * x for x in pcm[i:i + HOP]) / HOP) + 1e-9
    env.append(20 * math.log10(r / 32768))
dur = len(env) * HOP / SR
words = json.load(open(a.words))

def snap(t, reach=0.35):
    i0, i1 = max(0, int((t - reach) * 20)), min(len(env) - 1, int((t + reach) * 20))
    best = min(range(i0, i1 + 1), key=lambda i: (env[i], abs(i / 20 - t)))
    return best / 20 + 0.025

# 1. speech regions from the envelope, joining gaps <= maxgap
speech, cur = [], None
for i, d in enumerate(env):
    t = i / 20
    if d > a.thresh:
        cur = [t, t + 0.05] if cur is None else [cur[0], t + 0.05]
    elif cur is not None and t - cur[1] > a.maxgap:
        speech.append(cur); cur = None
if cur: speech.append(cur)
keep = [[max(0, s - a.pad), min(dur, e + a.pad)] for s, e in speech if e - s >= 0.1]

# 2. removals
rem = []
for r in a.remove:
    exact = r.endswith("!")                      # "s-e!" = cut exactly here, no snapping
    s, e = map(float, r.rstrip("!").split("-"))
    rem.append((s, e) if exact else (snap(s), snap(e)))
for r in a.remove_words:
    i, j = map(int, r.split("-"))
    s = words[i]["start"]; e = words[j]["start"] if j < len(words) else dur
    rem.append((snap(s), snap(e)))

def subtract(ranges, cut):
    out = []
    for s, e in ranges:
        cs, ce = cut
        if ce <= s or cs >= e: out.append([s, e]); continue
        if cs > s: out.append([s, cs])
        if ce < e: out.append([ce, e])
    return out
for c in sorted(rem):
    keep = subtract(keep, c)
keep = [[round(s, 3), round(e, 3)] for s, e in keep if e - s > 0.15]

# 3. render: join with tiny fades, light clean-up, level
parts, labels = [], []
for k, (s, e) in enumerate(keep):
    d = e - s
    parts.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(d - 0.015, 0):.3f}:d=0.015[p{k}];")
    labels.append(f"[p{k}]")
fc = "".join(parts) + "".join(labels) + f"concat=n={len(keep)}:v=0:a=1,highpass=f=80,afftdn=nf=-45,loudnorm=I={a.lufs}:TP=-1.5:LRA=11,aresample=48000[o]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.audio, "-filter_complex", fc, "-map", "[o]",
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", a.out], check=True)
json.dump(keep, open(a.out.rsplit(".", 1)[0] + ".keep.json", "w"))
kept = sum(e - s for s, e in keep)
print(f"{a.out}: {dur:.1f}s -> {kept:.1f}s  (removed {len(rem)} retake/label ranges, {dur - kept:.1f}s total incl. pauses)")

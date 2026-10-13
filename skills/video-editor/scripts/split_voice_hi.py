#!/usr/bin/env python3
"""Hindi: split the cleaned voice per frame at the pause before each frame's first phrase, and write
audio_meta.json with per-word timings distributed across each phrase by character length
(Whisper's Hindi word timings are unreliable; phrase timings from pauses are solid)."""
import json, os, subprocess, sys

VOICE, CAPS, ENDPAD = sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
ph = json.load(open(CAPS))["phrases"]
total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VOICE],
                             capture_output=True, text=True).stdout)
frames = sorted({p["frame"] for p in ph})
first = {f: min(p["start"] for p in ph if p["frame"] == f) for f in frames}
last = {f: max(p["end"] for p in ph if p["frame"] == f) for f in frames}
cuts = [0.0] + [round((last[f - 1] + first[f]) / 2, 3) for f in frames[1:]] + [total]
os.makedirs("assets/voice", exist_ok=True)
voices = []
for i, f in enumerate(frames):
    s, e = cuts[i], cuts[i + 1]
    path = f"assets/voice/{f:02d}.wav"
    af = ["-af", f"apad=pad_dur={ENDPAD}"] if f == frames[-1] else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-ss", str(s), "-to", str(e), *af, "-ac", "1", "-ar", "48000",
                    "-c:a", "pcm_s16le", path], check=True)
    words, k = [], 0
    for p in [p for p in ph if p["frame"] == f]:
        toks = p["text"].split()
        weights = [max(len(t), 2) for t in toks]
        span, t0 = p["end"] - p["start"], p["start"]
        for tok, wgt in zip(toks, weights):
            d = span * wgt / sum(weights)
            words.append({"id": f"w{f}_{k}", "text": tok, "start": round(t0 - s, 3), "end": round(t0 + d - s, 3)})
            t0 += d; k += 1
    dur = round(e - s + (ENDPAD if f == frames[-1] else 0), 3)
    voices.append({"frame": f, "path": path, "duration_s": dur, "words": words})
    print(f"frame {f:2d}: {s:6.2f}-{e:6.2f} ({dur:5.2f}s) {' '.join(w['text'] for w in words)[:60]}")
json.dump({"bgm": None, "bgm_pending": False, "voices": voices, "sfx": []}, open("audio_meta.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total + ENDPAD, 3))

"""Split a cleaned Hindi voiceover at natural pauses (>= 0.2 s under -38 dB), cap phrases at 7 s
(splitting at the quietest point), transcribe each with whisper medium (Hindi), and write
<voice>.phrases.json next to the audio. Usage: hi_phrases.py <cleaned-voice.wav>
Phrase timings are reliable; Whisper's Hindi spelling is not — write corrected caption text yourself."""
import array, json, math, os, subprocess, sys

MODEL = os.path.expanduser("~/.cache/whisper-cpp/ggml-medium.bin")
src = os.path.abspath(sys.argv[1])
W = os.path.dirname(src)
name = os.path.splitext(os.path.basename(src))[0]
raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", src, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
a = array.array('h'); a.frombytes(raw[:len(raw) // 2 * 2]); H = 400          # 50 ms windows
env = [20 * math.log10(math.sqrt(sum(x * x for x in a[i:i + H]) / H) / 32768 + 1e-9) for i in range(0, len(a) - H, H)]
dur = len(env) / 20
# speech runs
runs, cur, quiet = [], None, 0
for i, d in enumerate(env):
    if d > -38:
        if cur is None: cur = [i, i]
        cur[1] = i; quiet = 0
    elif cur is not None:
        quiet += 1
        if quiet >= 4:                                   # >= 0.2 s of quiet ends a phrase
            runs.append(cur); cur = None
if cur: runs.append(cur)
phr = [[r[0] / 20, (r[1] + 1) / 20] for r in runs if (r[1] - r[0]) >= 6]
out = []
for s, e in phr:                                         # cap length
    while e - s > 7:
        lo, hi = int((s + 2.5) * 20), int((s + 7) * 20)
        k = min(range(lo, hi), key=lambda j: env[j]); out.append([s, k / 20]); s = k / 20
    out.append([s, e])
res = []
tmp = os.path.join(W, f".{name}._ph.wav")
for s, e in out:
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{max(0, s - 0.08):.3f}", "-to", f"{min(dur, e + 0.08):.3f}", "-i", src,
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", tmp], check=True)
    r = subprocess.run(["whisper-cli", "-ng", "-m", MODEL, "-f", tmp, "-l", "hi", "-nt", "-np", "-mc", "0", "-ac", "512",
                        "-bs", "1", "-bo", "1"], capture_output=True, text=True, errors="replace")
    t = " ".join(r.stdout.split())
    res.append({"start": round(s, 2), "end": round(e, 2), "heard": t})
    print(f"[{s:6.2f}-{e:6.2f}] {t}", flush=True)
json.dump(res, open(os.path.join(W, name + ".phrases.json"), "w"), ensure_ascii=False, indent=1)
os.remove(tmp)

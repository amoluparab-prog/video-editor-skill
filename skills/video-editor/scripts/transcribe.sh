#!/usr/bin/env bash
# Word-level transcript with whisper.cpp.
# Usage: transcribe.sh <video> <workdir>   (MODEL=small.en|medium|base.en ..., WLANG=hi for Hindi)
# Writes <workdir>/audio16k.wav, words.json [{"w","start","end"}], transcript.txt
set -euo pipefail
src="$1"; work="$2"; model="${MODEL:-small.en}"
mdir="$HOME/.cache/whisper-cpp"; mfile="$mdir/ggml-$model.bin"
mkdir -p "$mdir" "$work"
if [ ! -s "$mfile" ]; then
  echo "Downloading whisper model $model ..." >&2
  curl -fL --retry 3 -o "$mfile.part" "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-$model.bin"
  mv "$mfile.part" "$mfile"
fi
ffmpeg -hide_banner -loglevel error -y -i "$src" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$work/audio16k.wav"
# Metal on Intel Macs returns empty/garbage transcripts (seen 2026-10-12) — use CPU there.
gpu=""; [ "$(uname -m)" = "x86_64" ] && gpu="-ng"
lang=en; case "$model" in *.en) ;; *) lang="${WLANG:-auto}";; esac   # WLANG=hi for Hindi (needs a multilingual model, e.g. MODEL=medium)
whisper-cli $gpu -m "$mfile" -f "$work/audio16k.wav" -l "$lang" -ml 1 -sow -oj -of "$work/whisper" >/dev/null 2>&1
python3 - "$work" <<'PY'
import json, sys, os
work = sys.argv[1]
d = json.load(open(os.path.join(work, "whisper.json")))
words = []
for s in d.get("transcription", []):
    t = s["text"].strip()
    if not t or t.startswith("["):
        continue
    words.append({"w": t, "start": s["offsets"]["from"] / 1000, "end": s["offsets"]["to"] / 1000})
json.dump(words, open(os.path.join(work, "words.json"), "w"), indent=0)
with open(os.path.join(work, "transcript.txt"), "w") as f:
    line, last = [], None
    for x in words:
        if last is not None and x["start"] - last > 0.5:
            f.write(f'[{line[0]["start"]:7.2f}] ' + " ".join(y["w"] for y in line) + "\n"); line = []
        line.append(x); last = x["end"]
    if line:
        f.write(f'[{line[0]["start"]:7.2f}] ' + " ".join(y["w"] for y in line) + "\n")
print(f"{len(words)} words -> {work}/words.json, transcript.txt")
PY

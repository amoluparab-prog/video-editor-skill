#!/usr/bin/env python3
"""Keep only the given time ranges of a video and join them, frame-accurately.

Usage: cut.py <source> <keep.json> <out.mp4> [--vf FILTERS] [--af FILTERS] [--crf 16]
keep.json: [[start, end], ...] seconds, in source time. --vf/--af are applied after the join
(e.g. --vf "scale=...,subtitles=caps.ass" — caption timings must then be in *output* time).
"""
import argparse, json, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("keep"); ap.add_argument("out")
ap.add_argument("--vf", default=""); ap.add_argument("--af", default="")
ap.add_argument("--crf", default="16")
a = ap.parse_args()

keep = json.load(open(a.keep))
parts, labels = [], []
for i, (s, e) in enumerate(keep):
    parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.01,afade=t=out:st={max(e - s - 0.01, 0)}:d=0.01[a{i}];")
    labels.append(f"[v{i}][a{i}]")
fc = "".join(parts) + "".join(labels) + f"concat=n={len(keep)}:v=1:a=1[vc][ac]"
fc += f";[vc]{a.vf or 'null'}[vo];[ac]{a.af or 'anull'}[ao]"

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.src,
       "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
       "-c:v", "libx264", "-preset", "slow", "-crf", a.crf, "-pix_fmt", "yuv420p", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", a.out]
subprocess.run(cmd, check=True)
print("wrote", a.out, "kept", round(sum(e - s for s, e in keep), 2), "s")

#!/usr/bin/env python3
"""Brand-styled word-highlight captions as a transparent overlay — no libass needed.

Homebrew's core ffmpeg (9.x) ships without libass/freetype, so `subtitles=`/`drawtext`
don't exist. Instead this draws each caption state as a PNG with ImageMagick (`magick`)
and writes an ffmpeg concat list. Every PNG is forced to PNG32: an all-transparent frame otherwise
saves as gray+alpha, and ffmpeg drops its alpha mid-stream (the video goes black between lines).

Usage:
  captions.py <words.json> <outdir> --w 1080 --h 1920 [--keep keep.json] [--offset 0] [--max-words 3]
Then:
  ffmpeg -f concat -safe 0 -i <outdir>/captions.txt -vf "fps=30,format=rgba" -c:v qtrle caps.mov
  ffmpeg -i video.mp4 -i caps.mov -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -preset slow -crf 16 -c:a copy out.mp4
(Overlaying the concat list directly only shows the first caption — always render caps.mov first.)

Reads primary/accent/font_file from ../brand.md. With --keep, source-time words are remapped
to the cut's output time (words outside kept ranges are dropped). Each line shows 2–4 words,
white on a primary-colored box; the spoken word turns accent.
"""
import argparse, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("words"); ap.add_argument("outdir")
ap.add_argument("--w", type=int, default=1080); ap.add_argument("--h", type=int, default=1920)
ap.add_argument("--offset", type=float, default=0.0)
ap.add_argument("--keep")
ap.add_argument("--max-words", type=int, default=3)
a = ap.parse_args()

skill = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
brand = {}
for line in open(os.path.join(skill, "brand.md")):
    m = re.match(r"^(primary|accent|font|font_file):\s*(.+?)\s*$", line)
    if m:
        brand[m[1]] = m[2].split("(")[0].strip()
if "PENDING" in (brand.get("primary"), brand.get("accent"), brand.get("font_file")):
    raise SystemExit("brand.md has no colors/font yet — ask the user once and fill it in.")
font = os.path.join(skill, brand["font_file"])
if not os.path.exists(font):
    raise SystemExit(f"brand font file missing: {font}")

words = json.load(open(a.words))
if a.keep:
    ranges, out, acc = json.load(open(a.keep)), [], 0.0
    for s, e in ranges:
        for x in words:
            if x["start"] >= s - 0.05 and x["end"] <= e + 0.05:
                out.append({"w": x["w"], "start": acc + max(x["start"] - s, 0), "end": acc + min(x["end"], e) - s})
        acc += e - s
    words = out
for x in words:
    x["start"] += a.offset; x["end"] += a.offset

# group into lines: break on max words, sentence punctuation, or a gap > 0.4s
lines, cur = [], []
for x in words:
    if cur and (len(cur) >= a.max_words or x["start"] - cur[-1]["end"] > 0.4 or re.search(r"[.!?,]$", cur[-1]["w"])):
        lines.append(cur); cur = []
    cur.append(x)
if cur:
    lines.append(cur)

vertical = a.h > a.w
fs = round(a.h * (0.042 if vertical else 0.06))
bottom = round(a.h * (0.24 if vertical else 0.09))   # keep clear of platform UI
pad_x, pad_y, gap = round(fs * 0.45), round(fs * 0.28), round(fs * 0.32)
os.makedirs(a.outdir, exist_ok=True)

blank = os.path.join(a.outdir, "blank.png")
subprocess.run(["magick", "-size", f"{a.w}x{a.h}", "xc:none", "PNG32:" + blank], check=True)

def render(path, ln, hi):
    cmd = ["magick", "-background", brand["primary"], "-font", font, "-pointsize", str(fs)]
    for j, y in enumerate(ln):
        if j:
            cmd += ["(", "-size", f"{gap}x1", "xc:" + brand["primary"], ")"]
        word = y["w"].upper().strip(".,!?;:")
        cmd += ["(", "+size", "-fill", brand["accent"] if j == hi else "white", "label:" + word.replace("%", "%%").replace("\\", ""), ")"]
    cmd += ["-gravity", "center", "+append", "+repage",
            "-bordercolor", brand["primary"], "-border", f"{pad_x}x{pad_y}",
            "-resize", f"{int(a.w * 0.9)}x>",
            "-background", "none", "-gravity", "south", "-extent", f"{a.w}x{a.h - bottom}",
            "-gravity", "north", "-extent", f"{a.w}x{a.h}", "PNG32:" + path]
    subprocess.run(cmd, check=True)

entries, t, n = [], 0.0, 0
for ln in lines:
    end = ln[-1]["end"] + 0.15
    if ln[0]["start"] > t:
        entries.append((blank, ln[0]["start"] - t))
    for i, x in enumerate(ln):
        s = max(x["start"], t)
        e = ln[i + 1]["start"] if i + 1 < len(ln) else end
        if e <= s:
            continue
        n += 1; p = os.path.join(a.outdir, f"c{n:04d}.png")
        render(p, ln, i)
        entries.append((p, e - s)); t = e
entries.append((blank, 1.0))
with open(os.path.join(a.outdir, "captions.txt"), "w") as f:
    f.write("ffconcat version 1.0\n")
    for p, d in entries:
        f.write(f"file '{os.path.abspath(p)}'\nduration {d:.3f}\n")
    f.write(f"file '{os.path.abspath(blank)}'\n")   # concat demuxer needs the last file repeated
print(f"{len(lines)} caption lines, {n} frames -> {a.outdir}/captions.txt")

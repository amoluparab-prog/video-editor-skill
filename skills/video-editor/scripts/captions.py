#!/usr/bin/env python3
"""Brand-styled word-highlight captions (.ass) from words.json.

Usage: captions.py <words.json> <out.ass> --w 1080 --h 1920 [--offset 0] [--keep keep.json]
Reads primary/accent/font from ../brand.md. With --keep, source-time words are remapped
to the cut's output time (words outside kept ranges are dropped).
Each line shows 2–4 words in white on a primary-colored box; the spoken word turns accent.
"""
import argparse, json, os, re

ap = argparse.ArgumentParser()
ap.add_argument("words"); ap.add_argument("out")
ap.add_argument("--w", type=int, default=1080); ap.add_argument("--h", type=int, default=1920)
ap.add_argument("--offset", type=float, default=0.0)
ap.add_argument("--keep")
ap.add_argument("--max-words", type=int, default=3)
a = ap.parse_args()

brand = {}
for line in open(os.path.join(os.path.dirname(__file__), "..", "brand.md")):
    m = re.match(r"^(primary|accent|font|font_file):\s*(.+?)\s*$", line)
    if m:
        brand[m[1]] = m[2].split("(")[0].strip()
if "PENDING" in (brand.get("primary"), brand.get("accent"), brand.get("font")):
    raise SystemExit("brand.md has no colors/font yet — ask the user once and fill it in.")

def ass_color(hexstr, alpha="00"):
    h = hexstr.lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()

def ts(t):
    t = max(t, 0); cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

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

fs = round(a.h * (0.045 if a.h > a.w else 0.06))
margin_v = round(a.h * (0.26 if a.h > a.w else 0.10))
white, prim, acc_c = "&H00FFFFFF", ass_color(brand["primary"]), ass_color(brand["accent"])
hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {a.w}
PlayResY: {a.h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{brand['font']},{fs},{white},{white},{prim},{prim},-1,0,0,0,100,100,1,0,3,{round(fs*0.28)},0,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
for ln in lines:
    end = ln[-1]["end"] + 0.15
    for i, x in enumerate(ln):
        s = x["start"]; e = ln[i + 1]["start"] if i + 1 < len(ln) else end
        txt = " ".join(("{\\c" + acc_c + "}" + y["w"].upper() + "{\\c" + white + "}") if j == i else y["w"].upper()
                       for j, y in enumerate(ln))
        pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if i == 0 else ""
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{pop}{txt}")
open(a.out, "w").write(hdr + "\n".join(ev) + "\n")
print(f"{len(lines)} caption lines -> {a.out}")

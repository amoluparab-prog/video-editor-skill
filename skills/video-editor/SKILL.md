---
name: video-editor
description: Your personal video editor. Use whenever the user wants a video edited, cut, trimmed, cleaned up, captioned, reframed, split, branded, leveled, brightened or exported — talking-head clips, Reels, TikToks, Shorts, YouTube videos, a phone recording, a .MOV/.MP4 they point at, "edit this", "cut my retakes", "make this a reel", "add captions", "split this into videos", "it's too dark", "my voice is too quiet". Also use when they ask to update their brand colors/font for video. This skill owns the edit itself (copy, transcribe, cut retakes and pauses, split, level, grade, export); it hands off to the HyperFrames skills only for designed graphics or cinematic captions.
---

# Video editor

The user records themselves and wants finished, post-ready videos without opening an editor. You are the editor; **they are the director** — they make the creative calls, you make them happen and tell them the truth about the footage.

## Before every edit: ask three questions

Ask these together, in one message, before touching anything (skip one only if they already answered it in this request):

1. **Where is it going?** Instagram Reels, TikTok, YouTube Shorts, YouTube (wide), LinkedIn, somewhere else.
2. **What should the viewer do at the end?** Follow, comment, click a link, buy, nothing — this decides the last line you keep and any end card.
3. **Captions and graphics, or a clean cut?**

If the brand slot in [brand.md](brand.md) is empty, ask for their two brand colors and font in that same message (once ever — see "Brand").

## The original is sacred

- Never modify, move or re-save the original file. Copy it into a work folder first and do everything there.
- Work folder: `~/VideoWork/<original-name>-<YYYYMMDD-HHMM>/`. It must **not** be inside iCloud Drive (`~/Library/Mobile Documents`), `~/Library/CloudStorage`, or Dropbox — sync clients time out on multi-GB video and can evict files mid-render. `~/VideoWork` is plain local disk.
- Save each finished video **next to the original** with a new name: `<original-name> - <platform> edit.mp4` (e.g. `interview - reel edit.mp4`). Never overwrite an existing file; add ` v2`, ` v3`.
- If the original itself sits in iCloud and is a placeholder (not downloaded), tell the user rather than forcing a download that may stall.

## Transcribe every word with timestamps

Run `bash ~/.claude/skills/video-editor/scripts/transcribe.sh <video> <workdir>` — whisper.cpp, offline, word-level. It writes `words.json` (`[{"w","start","end"}]`, seconds) and `transcript.txt`. Read the transcript before cutting; if it reads like gibberish, rerun with `MODEL=medium` (slower, better on accents) before trusting it.

## Cutting: retakes and pauses

Use the word timings to decide what to keep, then render with `python3 ~/.claude/skills/video-editor/scripts/cut.py <workdir>/source.* <keep.json> <out.mp4>` where `keep.json` is `[[start,end], ...]` in seconds.

- **Retakes — keep only the best take.** Signs: the speaker says "let's redo that", "again", "sorry", "one more time", "wait", "cut that"; or the same opening words of a sentence appear twice within ~20 s; or a sentence trails off and restarts. Keep the **last complete, fluent** take unless an earlier one is clearly better (fewer stumbles); drop the false starts *and* the "let's redo that" itself.
- **Pauses** — remove every silence over 0.5 s between kept words, but leave ~0.12 s of air on each side of a cut so words aren't clipped and it doesn't sound robotic. Cross-check with `ffmpeg -af silencedetect=n=-35dB:d=0.5` when breaths or room noise fool the word timings.
- Tell the user what you cut in plain words ("removed 3 restarts and 41 s of pauses — 2:10 → 1:29"), and list any retake call you weren't sure about with its timestamp so they can overrule you.

## One recording, several videos

If the transcript shows separate topics (a new intro like "okay, next one", a long gap, a clap/reset, a change of subject), propose the split points with one-line summaries, then export each as its own file next to the original: `<original-name> - part 1 <short-topic>.mp4`, etc. Each part gets the full treatment above.

## Brand: make it look like them

Read [brand.md](brand.md) first — it holds the saved colors, font and voice notes. Source priority:
1. A branding skill or brand files the user points to.
2. `brand.md` in this skill.
3. Ask once for two colors + font, then **write them into `brand.md`** so it is never asked again.

If a folder named **B-roll kit** exists (search `~`, `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Movies`, `~/Pictures`), use its logo, photos and graphics for intros, end cards and cutaways; note its path in `brand.md` once found.

Captions in brand style: `python3 ~/.claude/skills/video-editor/scripts/captions.py <words.json> <capdir> --w W --h H [--keep keep.json]` draws 2–4-word lines (white on the primary color, spoken word in the accent) as transparent PNGs with ImageMagick and writes `<capdir>/captions.txt`; overlay it with `ffmpeg -i cut.mp4 -f concat -safe 0 -i <capdir>/captions.txt -filter_complex "[1:v]format=rgba[c];[0:v][c]overlay=0:0:eof_action=pass" ...`. It deliberately avoids ffmpeg's `subtitles`/`drawtext` filters: Homebrew's ffmpeg 9 is built without libass/freetype, so those filters don't exist (found 2026-10-12). The brand font file ships inside this skill (`fonts/`). For designed graphics, lower-thirds, cinematic or "behind-the-subject" captions, use the HyperFrames skills instead: `/talking-head-recut` (graphic overlays) or `/embedded-captions` (cinematic captions) — run the cut/level/grade here first, then hand them the finished cut.

## Formats and quality

| Destination | Canvas | Notes |
|---|---|---|
| Reels, TikTok, Shorts | 1080×1920 (9:16) | reframe on the face; keep captions above the bottom ~20% (platform UI) and out of the right-edge button column |
| YouTube | 1920×1080, or 3840×2160 if the source is 4K | never upscale |

Always export at the highest sensible quality: H.264 `-crf 16 -preset slow -pix_fmt yuv420p -profile:v high`, keep source frame rate, AAC 320k 48 kHz, `-movflags +faststart`. Use H.265/ProRes only if asked. Phone HDR (HLG/Dolby Vision .MOV) must be tone-mapped to SDR, or it looks washed out on Instagram — check `color_transfer` with ffprobe.

## Audio: level each voice separately

Target about −14 LUFS integrated, true peak −1 dB. If the video mixes an AI/TTS voice with the user's real voice, **don't normalize the whole track at once** — the AI voice is usually louder and denser, so the real voice ends up sounding quiet. Find each voice's segments (word timings plus the user's confirmation of which parts are AI), run `loudnorm` per segment to the same target, then join. Light cleanup is fine (`highpass=f=80`, gentle `afftdn`) — never so much that they sound underwater.

## Dark or grainy footage: fix it, then tell the truth

Measure brightness with `signalstats` (YAVG on 0–255; a well-lit face is ~90–140). If it's dark, lift it with `eq`/`curves` and denoise with `hqdn3d` (or `nlmeans` for heavy grain), then compare before/after stills. Then say plainly:
- "Fixed, looks good" — or
- "Better, but still soft/noisy — fine for a story, not for your main feed" — or
- "**I'd reshoot this.** Brightening this much turns the grain into mush; face a window or add a light." Say this when YAVG is under ~45 or the denoise visibly smears the face. Don't oversell a rescue.

## Done means

- The finished file(s) exist next to the original, play end to end (check with ffprobe: duration, resolution, audio stream present), and you looked at a few frames yourself (captions readable, not cut off, face in frame).
- You told the user: the exact path of each file, what you changed, anything you weren't sure about, and an honest quality note.
- You end with: **"Watch it once before you post — you're the director."**

If blocked (missing tool, file won't decode, footage unusable), stop and say exactly what's wrong and what the user can do; don't ship a half-edit as finished.

## Setup facts (verified 2026-10-12 on macOS; re-check with `command -v`)

- Tools: `ffmpeg`/`ffprobe` (brew), `whisper-cli` (brew `whisper.cpp` — renamed from `whisper-cpp`), `magick` (brew `imagemagick`, for captions), Node.js 22+ (needed by HyperFrames, `npx hyperframes ...`). Re-check with `command -v`. Homebrew may build these from source on Intel Macs (slow — run installs in the background). If `ffmpeg` fails with "Library not loaded … libx265", a brew upgrade broke it: `brew reinstall ffmpeg`.
- Whisper models live in `~/.cache/whisper-cpp/` (`ggml-small.en.bin` default; `transcribe.sh` downloads a missing one from huggingface.co/ggerganov/whisper.cpp).
- HyperFrames skills are installed in `~/.claude/skills/` (hyperframes, embedded-captions, talking-head-recut, media-use, …) via `npx skills add heygen-com/hyperframes -g`. Update with `npx skills update -g`.

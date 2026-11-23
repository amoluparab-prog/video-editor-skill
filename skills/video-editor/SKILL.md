---
name: video-editor
description: Your personal video editor. Use whenever the user wants a video edited, cut, trimmed, cleaned up, captioned, reframed, split, branded, leveled, brightened or exported — talking-head clips, Reels, TikToks, Shorts, YouTube videos, a phone recording, a .MOV/.MP4 they point at, "edit this", "cut my retakes", "make this a reel", "add captions", "split this into videos", "it's too dark", "my voice is too quiet", "make a Hindi version". Also use when they ask to update their brand colors/font for video. This skill owns the edit itself (copy, transcribe, cut retakes and pauses, split, level, grade, export); it hands off to the HeyGen HyperFrames skills for designed graphics, animated explainers and cinematic captions.
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
- Work folder: `~/VideoWork/<original-name>-<YYYYMMDD-HHMM>/`. It must **not** be inside iCloud Drive (`~/Library/Mobile Documents`), `~/Library/CloudStorage`, or Dropbox — sync clients time out on multi-GB video and can evict files mid-render.
- Save each finished video **next to the original** with a new name: `<original-name> - <platform> edit.mp4`. Never overwrite an existing file; add ` v2`, ` v3`.
- If the original sits in iCloud as an un-downloaded placeholder, say so rather than forcing a download that may stall.

## Transcribe every word with timestamps

`bash ~/.claude/skills/video-editor/scripts/transcribe.sh <video> <workdir>` — whisper.cpp, offline, word-level → `words.json` (`[{"w","start","end"}]`, seconds) and `transcript.txt`. Read the transcript before cutting; if it reads like gibberish, rerun with `MODEL=medium`. Fix proper nouns Whisper mishears (e.g. "cloud code" → Claude Code) before using words for captions.

## Cutting: retakes and pauses

Decide what to keep from the word timings, then `python3 ~/.claude/skills/video-editor/scripts/cut.py <source> <keep.json> <out.mp4>` (`keep.json` = `[[start,end], ...]`).

- **Retakes — keep only the best take.** Signs: "let's redo that", "again", "sorry", "one more time", "wait", "cut that"; the same opening words twice within ~20 s; a sentence that trails off and restarts. Keep the **last complete, fluent** take unless an earlier one is clearly better; drop the false starts *and* the "let's redo that". Watch for the phrase being part of the script itself (a prompt that says "let me try that again") — don't cut scripted lines.
- **Pauses** — remove every silence over 0.5 s between kept words, leaving ~0.12 s of air at each cut.
- Tell the user what you cut in plain words ("removed 3 restarts and 41 s of pauses — 2:10 → 1:29") and list any call you weren't sure about with its timestamp.

## Voiceovers recorded on a phone

- Ask for **iPhone Voice Memos, Lossless, Mono**, one memo per section, AirDropped to Downloads. People read section labels aloud ("Video B… intro", "Outro") — cut those too.
- `scripts/voiceclean.py <audio> <words.json> <out.wav> --remove-words i-j … --remove s-e …` shortens pauses > 0.5 s from the loudness envelope (word timings lie about pauses), snaps cuts to the quietest point nearby (suffix `!` on a range — `"239.92-245.55!"` — to cut exactly when the snap slides into a neighbouring word), drops < 0.15 s scraps, and levels to −16 LUFS.
- **Always re-transcribe the cleaned file and read it end to end.** It catches retakes the first transcript glossed over and lines cut by bad timestamps. Whisper's word times bunch up in the last seconds of a file — re-transcribe the tail on its own before cutting near the end.
- iPhone memos end with one corrupt ALAC frame; the decode warning is harmless.

## Hindi (and other non-English) audio

- Use `MODEL=medium WLANG=hi`. Hindi word timings are unreliable and short windows make Whisper loop. Instead: `scripts/hi_phrases.py <cleaned-voice.wav>` splits at natural pauses and transcribes each phrase alone → `<voice>.phrases.json` (reliable phrase times, unreliable spelling).
- Write the **correct** caption text per phrase yourself into a `captions.json` (`{"phrases":[{"frame","start","end","text"}]}`); Whisper's Hindi spelling is poor and it garbles English words inside Hindi. Verify suspected retakes by transcribing short pieces — the medium model also *invents* repeats.
- **Devanagari on screen:** font `fonts/NotoSansDevanagari-var.ttf` (Google Noto, OFL) after the Latin brand font in the stack; `letter-spacing: 0` (tracking breaks matras); line-height ≥ 1.3; never split a Devanagari word into per-letter animated spans; keep technical terms in Latin.

## One recording, several videos

If the transcript shows separate topics (a new intro, a long gap, a clap/reset), propose split points with one-line summaries, then export each as its own file next to the original.

## Brand: make it look like them

Read [brand.md](brand.md) first. Source priority: a branding skill or brand files they point to → `brand.md` → ask once for two colors + font and **write them into `brand.md`** (and their social handle, for end cards). If a folder named **B-roll kit** exists (search `~`, `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Movies`, `~/Pictures`), use its logo, photos and graphics; note its path in `brand.md`. Put the brand font file in `fonts/`.

Simple brand captions: `scripts/captions.py <words.json> <capdir> --w W --h H [--keep keep.json]` draws 2–4-word lines (white on the primary color, spoken word in the accent) as transparent PNGs with ImageMagick. Render them to a video first, then overlay:

```
ffmpeg -f concat -safe 0 -i <capdir>/captions.txt -vf "fps=30,format=rgba" -c:v qtrle caps.mov
ffmpeg -i cut.mp4 -i caps.mov -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass,format=yuv420p[v]" -map "[v]" -map 0:a ...
```

This avoids ffmpeg's `subtitles`/`drawtext`, which Homebrew's ffmpeg 9 doesn't build.

## Designed, animated videos (HeyGen HyperFrames) over the user's own voice

When they want "nice visuals, not dull cards", build with HyperFrames (`/hyperframes` → `/faceless-explainer`): brief → storyboard (approve) → sketch sheet (approve) → one worker per frame → assemble → `lint`/`check` → Studio preview → render on approval. What made it work:

- **Their voice instead of TTS:** split the cleaned wav per storyboard frame at the gap before each frame's first word and write `audio_meta.json` yourself (`{bgm:null, voices:[{frame, path:"assets/voice/NN.wav", duration_s, words:[{id,text,start,end} frame-relative]}], sfx:[]}`), then `audio.mjs sync-durations`. Pad the last frame's wav with silence for the end card. For Hindi, `scripts/split_voice_hi.py <voice.wav> <captions.json>` does this from phrase captions.
- **Cue tables:** give each frame a `cues` line (word@seconds from frame start) so workers land reveals on spoken words.
- **Worker rules:** asset paths root-relative (`assets/...`; `../` fails lint), one pinned GSAP version, ids starting with a letter.
- **frame.md brand remix** can mis-map colors onto a preset; check the result and fix by hand.
- **Captions:** the generated `captions.html` holds the last caption until the end — clamp the last group to its last word + 0.3 s so the end card is clean. For Devanagari, add the Noto font-face and set letter-spacing 0.
- **Persistent elements** (a progress rail across many frames): build ONE overlay composition on its own track above the frames rather than trusting every worker to draw it identically.
- **Translated versions:** copy the project, re-split the new voice, re-sync durations, and adapt each frame with one worker (copy table + glossary + new cues). Reset frame durations to the voice length before `transitions.mjs inject`.
- Images: `npx hyperframes media-use resolve --type image --intent "<scene>" --project .` (HeyGen library).

## Music and dance videos

- **No lyric captions** — lyrics are someone else's copyrighted words. Use a hook title and a CTA end card instead.
- **Ask who the stars are**; crowd footage needs to know whom to follow.
- **Cut on the beat:** estimate tempo from an onset envelope, fit a beat grid at each cut, join where the gap is a whole number of bars, 12 ms audio fades, one `concat` encode.
- **Smart 9:16 crop from wide footage:** mark subjects' centres per second, run a speed-limited follow, drive `crop` per frame with `sendcmd` (`<t> crop@c0 x <px>;`) — a long inline piecewise x-expression fails to configure.

## Formats and quality

| Destination | Canvas | Notes |
|---|---|---|
| Reels, TikTok, Shorts | 1080×1920 (9:16) | keep captions above the bottom ~20% and out of the right-edge button column |
| YouTube | 1920×1080, or 3840×2160 if the source is 4K | never upscale |

**Joining clips:** never stream-copy (`-f concat … -c copy`) segments rendered separately from a looped image or with `-shortest` — video runs slightly longer than audio, the drift adds up, and players stutter then drop the sound. Join in one encode with the `concat` filter and check audio/video durations match.

Export: H.264 `-crf 16 -preset slow -pix_fmt yuv420p -profile:v high`, source frame rate, AAC 320k 48 kHz, `-movflags +faststart`. Tone-map phone HDR to SDR (check `color_transfer`).

## Audio: level each voice separately

Target ≈ −14 LUFS, true peak −1 dB. If an AI/TTS voice and the user's real voice share a video, `loudnorm` each voice's segments separately, then join — otherwise the real voice ends up quiet.

## Dark or grainy footage: fix it, then tell the truth

Measure with `signalstats` (YAVG 0–255; a well-lit face ≈ 90–140). Lift with `eq`/`curves`, denoise with `hqdn3d`/`nlmeans`, compare stills, then say plainly: fixed / better but not for the main feed / **reshoot** (YAVG under ~45 or the denoise smears the face).

## Done means

- Finished file(s) exist next to the original, play end to end (ffprobe: duration, resolution, audio present), and you looked at frames yourself.
- You told the user the exact path, what changed, anything uncertain, and an honest quality note.
- You end with: **"Watch it once before you post — you're the director."**

If blocked (missing tool, file won't decode, footage unusable), say exactly what's wrong and what they can do; don't ship a half-edit.

## Setup facts (verified 2026-10-12 on macOS; re-check with `command -v`)

- Tools: `ffmpeg`/`ffprobe`, `whisper-cli` (whisper.cpp; if Homebrew can't build it, build from https://github.com/ggml-org/whisper.cpp with cmake), `magick` (ImageMagick), Node.js 22+ for HyperFrames (`npx hyperframes …`). On Intel Macs `transcribe.sh` runs Whisper CPU-only (Metal returned empty transcripts).
- Whisper models live in `~/.cache/whisper-cpp/` (`transcribe.sh` downloads a missing one).
- HyperFrames skills: `npx skills add heygen-com/hyperframes -g`; update with `npx skills update -g`.
- In zsh, a variable holding several filenames is not word-split — build file lists in Python or arrays.

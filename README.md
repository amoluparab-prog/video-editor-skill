# video-editor — a skill that turns Claude into your video editor

I record short videos for Reels, TikTok and YouTube. The recording is the easy part. The editing — cutting retakes, killing dead air, adding captions in my colors, exporting the right size — is what eats the evening. So I taught Claude to do it, and saved what it learned as a skill so it does it the same way every time.

You're the director. It asks three questions before every edit, never touches your original file, finds your retakes from a word-level transcript, trims pauses over half a second, splits one long recording into separate videos, uses your brand colors and font, balances an AI voice against your real one, tells you honestly when footage needs a reshoot, and reminds you to watch it once before you post.

## Two ways to get it

**1. Take the skill directly.** Copy `skills/video-editor` into `~/.claude/skills/`, then install the free tools it uses:

```bash
brew install ffmpeg whisper-cpp node
npx skills add heygen-com/hyperframes -g
```

The first time you ask for an edit, it asks for your two brand colors and font and remembers them.

**2. Let your AI build it from the prompt.** Paste [PROMPT.md](PROMPT.md) (or [PROMPT.hi.md](PROMPT.hi.md) in Hindi) into Claude Code, or read it aloud to your AI. It checks your machine, installs what's missing, adds HeyGen's HyperFrames skills, writes the same skill, and proves it with a seven-second captioned test clip.

## What's inside

```
skills/video-editor/
  SKILL.md            the rules and how to apply them
  brand.md            your colors, font, voice notes (filled in on first use)
  fonts/              drop your brand font file here
  scripts/
    transcribe.sh     whisper.cpp, word-level timestamps, offline
    cut.py            keep a list of time ranges and join them, frame-accurate
    captions.py       word-highlight captions in your brand style (.ass)
```

## Built on

- [FFmpeg](https://ffmpeg.org) for every cut, grade and export
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) for transcription, on your machine
- [HeyGen HyperFrames](https://github.com/heygen-com/hyperframes) for designed graphics and cinematic captions

## License

MIT

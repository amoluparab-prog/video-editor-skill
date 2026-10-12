# The "be my video editor" prompt

Paste this into Claude Code (or read it aloud to your AI). It sets up the free tools, installs HeyGen's HyperFrames skills, and writes a permanent `video-editor` skill so your AI edits your videos the same way every time.

---

I'd like you to take on the job of my video editor, and to write down everything you learn as a reusable skill so you never have to be taught twice. Hear me out fully before you start.

**Part 1 — Get the machine ready.**
See whether FFmpeg, Whisper and Node.js are on this computer. They're all free. Install whatever is missing, tell me in a line or two what each step does, and pause to check with me before anything that asks for my password.

**Part 2 — Add HeyGen's HyperFrames skills.**
They live at github.com/heygen-com/hyperframes and install with `npx skills add heygen-com/hyperframes`. Afterwards, confirm you can actually see them. If they ended up in `.agent/skills` or `.agents/skills`, link them into `.claude/skills` so you can use them.

**Part 3 — Write a skill named `video-editor` in `.claude/skills`, with these house rules:**

1. **Check in first.** Before any edit, ask me three things: which platform it's for (Reels, TikTok, YouTube…), what I want viewers to do when it ends, and whether I want captions and graphics or a plain clean cut.
2. **My original stays untouched.** Do the work on a copy in a local folder that isn't synced by iCloud or Dropbox, since huge video files stall there. Put each finished video beside the original under a new name.
3. **Transcribe with timestamps.** Use Whisper to get every word and when it was spoken. Use that to find my do-overs: if I restart a line or say something like "let me try that again," keep just the strongest take. Trim out any silence longer than half a second.
4. **One recording, many videos.** If a single file holds more than one video, cut it into separate files.
5. **Stay on brand.** If I already have a brand skill or brand files, take my colors, fonts and tone from them. If not, ask me once for my two brand colors and my font, and store them in the skill so you never ask again. If there's a folder called "B-roll kit," use the logo, photos and graphics in it.
6. **Right shape, best quality.** Vertical 9:16 for Reels and TikTok, widescreen for YouTube, and always export at the highest quality.
7. **Balance the voices.** If an AI voice and my real voice share a video, set each one's loudness on its own so I'm never drowned out.
8. **Be straight about bad footage.** If a clip is dark or grainy, improve it, tell me honestly how it turned out, and say if I'd be better off reshooting.
9. **Hand it back properly.** When you're done, tell me exactly where the file is and remind me to watch it once before posting. I make the final call.

**Part 4 — Prove it works.**
Make a short test clip, around seven seconds, with captions in my brand style.

**To wrap up,** tell me in three short sentences what you can now do with my videos, and suggest one edit I could ask you for first.

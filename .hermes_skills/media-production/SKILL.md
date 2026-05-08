---
name: media-production
description: "Media content production and consumption — Spotify playback control, YouTube transcript extraction, GIF search (Tenor API), audio spectrogram analysis (songsee), open-source music generation (HeartMuLa), and remote 3D rendering (Blender headless via SSH)."
category: media
---

# Media Production — Spotify, YouTube, GIFs, Audio Analysis, Music Generation, 3D Rendering

## Quick Reference

| Tool | Purpose | Category |
|------|---------|----------|
| `spotify` (Hermes tools) | Playback control, playlists, search | Audio playback |
| `youtube-content` + script | Transcript extraction → summary/thread/blog | Video content |
| `gif-search` (Tenor API) | GIF search and download | Visual content |
| `songsee` | Spectrogram / audio feature visualization | Audio analysis |
| `heartmula` | Open-source music generation from lyrics + tags | Audio generation |
| Blender headless via SSH | Remote GPU rendering (Pi → MX25Rig PC) | 3D rendering |

---

## Section 1: Spotify Playback Control

**Tools**: `spotify_playback`, `spotify_devices`, `spotify_queue`, `spotify_search`, `spotify_playlists`, `spotify_albums`, `spotify_library`

### Prereq
Spotify account. Playback mutation requires **Premium**. Search/playlist/read ops work on Free.

### Core Patterns

**Play by search (one call, then play):**
```
spotify_search({"query": "miles davis kind of blue", "types": ["album"], "limit": 1})
→ play URI: spotify:album:1weenld61qoidwYuZ1GESA
spotify_playback({"action": "play", "context_uri": "spotify:album:..."})
```

**What's playing? (single call, no preflight):**
```
spotify_playback({"action": "get_currently_playing"})
```
204/empty = nothing playing. Don't retry.

**Pause / Skip / Volume — direct action, no inspection:**
```
spotify_playback({"action": "pause"})
spotify_playback({"action": "next"})
spotify_playback({"action": "set_volume", "volume_percent": 50})
```

**Add to playlist:**
```
spotify_playlists({"action": "list"})  # find playlist ID
spotify_playback({"action": "get_currently_playing"})  # get track URI
spotify_playlists({"action": "add_items", "playlist_id": "...", "uris": ["spotify:track:..."]})
```

### Failure Modes
- **403 No active device** → Spotify not open anywhere. User opens Spotify first.
- **403 Premium required** → Free user tried playback mutation.
- **204 on get_currently_playing** → Nothing playing, not an error.
- **429** → Rate limit. Wait + retry once.
- **401** → Run `hermes auth spotify`.

### Rules
- Don't `get_state` before every action — just act.
- Don't describe search results unless asked — play the top result.
- User playlists → `spotify_playlists list`, NOT `spotify_search`.
- Use full URIs from search results directly.

---

## Section 2: YouTube Transcript Extraction

**Tool**: `fetch_transcript.py` script + LLM reformattting

### Setup
```bash
pip install youtube-transcript-api
```

### Fetch
```bash
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only --timestamps
```

Accepts: standard URLs, youtu.be shorts, embeds, live links, or raw 11-char video ID.

### Output Formats (LLM transformation)
After fetching, transform based on request:
- **Summary** — 5-10 sentence overview (default)
- **Chapters** — timestamped topic list
- **Thread** — numbered posts, each under 280 chars
- **Blog post** — full article with sections
- **Quotes** — notable quotes with timestamps

### Workflow
1. Fetch with `--text-only --timestamps`
2. Validate — non-empty and correct language
3. Chunk if >50K chars (~40K with 2K overlap, summarize each, merge)
4. Transform to requested format
5. Verify output before presenting

### Errors
- **Transcript disabled** → tell user; suggest checking subtitles on video page
- **Private/unavailable** → relay error, verify URL
- **No language match** → retry without `--language`
- **Empty output** → video likely has no captions

---

## Section 3: GIF Search (Tenor API)

**Tool**: curl + jq directly against Tenor API

### Setup
```bash
# Add to ~/.hermes/.env
TENOR_API_KEY=...
```
Free key at https://developers.google.com/tenor/guides/quickstart

### Search and Download
```bash
# Top result URL
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=$TENOR_API_KEY" \
  | jq -r '.results[].media_formats.gif.url'

# Download
URL=$(curl -s "...search?q=celebration&limit=1..." | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

### Formats Available
`gif` (full), `tinygif` (preview), `mp4`, `tinymp4`, `webm`, `nanogif`

### Notes
- URL-encode spaces as `+`
- `tinygif` for chat/display; `gif` for download
- Direct URLs work in markdown: `![alt](url)`

---

## Section 4: Audio Spectrogram Analysis (songsee)

**Tool**: `songsee` (Go CLI) — spectrograms and multi-panel audio feature grids

### Install
```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

### Visualizations
`spectrogram`, `mel`, `chroma`, `hpss`, `selfsim`, `loudness`, `tempogram`, `mfcc`, `flux`

### Common Uses
```bash
songsee track.mp3 -o spectrogram.png
songsee track.mp3 --viz spectrogram,mel,chroma,mfcc -o grid.png
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg
```

Useful for comparing audio outputs, debugging synthesis, documenting pipelines. Output can be inspected with `vision_analyze`.

---

## Section 5: Open-Source Music Generation (HeartMuLa)

**Tool**: HeartMuLa / heartlib — generates full songs from lyrics + tags. Apache-2.0, comparable to Suno.

### Hardware
- **Min**: 8GB VRAM with `--lazy_load true` (~6.2GB peak)
- **Rec**: 16GB+ VRAM
- **CPU**: possible but extremely slow (30-60 min vs ~4 min on GPU)
- **RTF** ≈ 1.0 — 4-min song ≈ 4 min generation

### Install + Setup
```bash
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
uv venv --python 3.10 .venv && . .venv/bin/activate
uv pip install -e .
uv pip install --upgrade datasets transformers  # fix dependency conflicts
```

**Required patches** (Feb 2026 dependency conflicts):
1. `src/heartlib/heartmula/modeling_heartmula.py` — add `Llama3ScaledRoPE.rope_init()` after `reset_caches`
2. `src/heartlib/pipelines/music_generation.py` — add `ignore_mismatched_sizes=True` to all `HeartCodec.from_pretrained()` calls

**Download models**:
```bash
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

### Usage
```bash
python ./examples/run_music_generation.py \
  --model_path=./ckpt --version="3B" \
  --lyrics=./assets/lyrics.txt \
  --tags=./assets/tags.txt \
  --save_path=./assets/output.mp3 \
  --lazy_load true
```

**Tags** (comma-separated, no spaces): `piano,happy,wedding,synthesizer`

**Lyrics** with structural tags:
```
[Intro]
[Verse]
Your lyrics here...
[Chorus]
Chorus lyrics...
[Bridge]
[Outro]
```

### Key Parameters
`--max_audio_length_ms` (default 240000 = 4min), `--cfg_scale` (1.5), `--temperature` (1.0), `--topk` (50)

### Pitfalls
- **DO NOT use bf16 for HeartCodec** — use fp32 (default)
- Tags may be ignored — lyrics dominate; experiment with ordering
- Triton unavailable on macOS — Linux/CUDA only for GPU acceleration

---

## Section 6: Blender Headless Remote Rendering (Pi → MX25Rig)

**Context**: Raspberry Pi (10.0.0.14) drives Blender headless on MX25Rig PC (10.0.0.91) via SSH + SCP. PC has AMD 7900 XT for Cycles/Eevee. Blender 5.1.0 via Flatpak.

### Pipeline
```bash
# 1. Write script locally (Pi) with write_file tool
# 2. SCP to PC, render, SCP result back
scp /tmp/render_scene.py Evan@10.0.0.91:/home/Evan/render_scene.py
ssh Evan@10.0.0.91 "flatpak run org.blender.Blender --background --python /home/Evan/render_scene.py"
scp Evan@10.0.0.91:/home/Evan/output.png /tmp/output.png
```

### ALWAYS Use Unique Output Filenames
`room_v6.png` not `test_render.png` — old files mask missing new renders.

### ALWAYS Kill Stale Processes First
```bash
ssh Evan@10.0.0.91 "killall -9 -f blender 2>/dev/null; sleep 2"
```

### ALWAYS Run Foreground
Background renders (`&`) fail silently — file never appears, old process holds the path. Use `timeout` or capture stdout directly.

### Blender 5 Critical Bugs / API Changes
| Issue | Fix |
|-------|-----|
| UV sphere grey in Cycles | Use `primitive_ico_sphere_add` — UV spheres have per-loop UV data that overrides Principled BSDF |
| `radius2` on cylinder | Removed in Blender 5 — use `primitive_cylinder_add(radius=size, depth=size*2)` |
| `primitive_uv_sphere_add` | Removed — use `primitive_ico_sphere_add(radius=...)` |
| `wm.append()` sets `active_object = None` | Use `bpy.context.scene.objects[-1]` after append |
| Material `default_value` tuple assignment | Set element-by-element: `val[0]=r; val[1]=g; val[2]=b; val[3]=1` |
| `use_nodes = False` deprecated | Always use node-based materials |
| Bloom removed in Blender 5.1.0 | Do NOT use `bpy.context.scene.eevee.use_bloom` — AttributeError |
| Emissive materials in Eevee | Use Cycles, or Principled BSDF with emission strength 15-20+ in dark scene |

### Material Color (element-by-element)
```python
bsdf.inputs["Base Color"].default_value[0] = r  # R
bsdf.inputs["Base Color"].default_value[1] = g  # G
bsdf.inputs["Base Color"].default_value[2] = b  # B
bsdf.inputs["Base Color"].default_value[3] = 1.0  # A
```

### Lighting Recipes
**Bright room (recommended)**: World BG (0.85-0.90, 0.82-0.88, 0.78-0.85, 1.0) strength 1.0 + ceiling area light energy 200-250.
**Dark moody** → Eevee fails (grey everywhere). Use Cycles only.

### Camera FOV
Blender 5 default FOV ~40° horizontal at 16:9. At y=-5, visible width ≈ 3.64 units. Keep x-spread within ±2.

### SSH Heredoc Warning
**QUOTES GET STRIPPED** from terminal heredocs — subscript notation (`bsdf.inputs["Base Color"]`) loses quotes via SSH. Write scripts with `write_file` tool, then `scp`. Never `cat > file << 'EOF'` for Python scripts.

### Verify Render
```bash
# Check new file exists and is recent
ssh Evan@10.0.0.91 "stat /home/Evan/room_v6.png"
# Average pixel color (shouldn't be grey ~59 everywhere)
convert /tmp/output.png -resize 1x1! txt:-
```

---

## Cross-Tool Patterns

| Need | Tool |
|------|------|
| Play music | `spotify` |
| Analyze audio features | `songsee` |
| Generate original music | `heartmula` |
| Find reaction GIF | `gif-search` |
| Extract video content | `youtube-content` |
| 3D renders | Blender headless |
| Combined audio+visual output | Render to image, attach to Spotify playlist share |

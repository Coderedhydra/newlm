## AI 2D Animator (Gemini-powered)

This framework:
- Generates a concise story outline and scene motion plan using Gemini
- Animates provided character PNGs (no AI character generation) with smooth easing
- Composites over pluggable backgrounds (gradient or directory of images)
- Exports PNG frames and optional MP4

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env`:

```
GOOGLE_API_KEY=YOUR_KEY
```

### Create sample assets

```bash
python -m ai2d_animator sample_assets --assets-dir ./assets
```

### Run (online with Gemini)

```bash
python -m ai2d_animator run \
  --prompt "Two friends explore a neon city" \
  --assets-dir ./assets \
  --width 1280 --height 720 --fps 24 \
  --scenes 3 --seconds-per-scene 3 \
  --output-dir ./frames \
  --output-video ./demo.mp4
```

Using YAML config:

```yaml
# config.yaml
prompt: Two friends explore a neon city
assets_dir: ./assets
width: 1280
height: 720
fps: 24
scenes: 3
seconds_per_scene: 3.0
background_provider: gradient
output_dir: ./frames
output_video: ./demo.mp4
offline: false
```

```bash
python -m ai2d_animator run --config ./config.yaml --prefer-config
```

### Run offline (no Gemini)

```bash
python -m ai2d_animator run --prompt "Demo" --assets-dir ./assets --offline
```

### Use image directory backgrounds

```bash
python -m ai2d_animator run \
  --prompt "Forest adventure" \
  --assets-dir ./assets \
  --background image_dir \
  --background-image-dir ./bg_images \
  --output-video demo.mp4
```

Notes:
- Coordinates are normalized (0..1), origin top-left.
- Easing per segment follows the next keyframe's easing.
- Output frames go to `--output-dir`.

### Flask Web UI

Run the web app:

```bash
python3 -m ai2d_animator.web.app
```

Open `http://localhost:7860`:
- Upload character PNGs and background images
- Enter story prompt and settings
- Click Generate Video to start a background job
- Watch live status and download the MP4 when done

# newlmdfgsdf

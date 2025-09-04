from __future__ import annotations

import math
import os
from typing import Dict, List, Tuple, Callable, Optional

import numpy as np
from PIL import Image, ImageOps
from tqdm import tqdm

from .easing import EASING_FUNCTIONS
from .types import Story, Scene, MotionTrack, CharacterAsset, RenderConfig, Keyframe
from .backgrounds import PROVIDERS


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _load_character_images(assets: List[CharacterAsset]) -> Dict[str, Image.Image]:
    images: Dict[str, Image.Image] = {}
    for asset in assets:
        img = Image.open(asset.image_path).convert("RGBA")
        images[asset.name] = img
    return images


def _interpolate_keyframes(keyframes: List[Keyframe], t: float) -> Tuple[float, float, float, float, float]:
    if not keyframes:
        return (0.5, 0.5, 1.0, 0.0, 1.0)
    if t <= keyframes[0].time:
        k = keyframes[0]
        return (k.x, k.y, k.scale, k.rotation_deg, k.opacity)
    if t >= keyframes[-1].time:
        k = keyframes[-1]
        return (k.x, k.y, k.scale, k.rotation_deg, k.opacity)

    # find segment
    for i in range(1, len(keyframes)):
        k0 = keyframes[i - 1]
        k1 = keyframes[i]
        if k0.time <= t <= k1.time:
            segment_t = (t - k0.time) / max(1e-6, (k1.time - k0.time))
            easing = EASING_FUNCTIONS.get(k1.easing, EASING_FUNCTIONS["linear"])  # ease toward k1
            tt = easing(segment_t)
            x = k0.x + (k1.x - k0.x) * tt
            y = k0.y + (k1.y - k0.y) * tt
            scale = k0.scale + (k1.scale - k0.scale) * tt
            rot = k0.rotation_deg + (k1.rotation_deg - k0.rotation_deg) * tt
            op = k0.opacity + (k1.opacity - k0.opacity) * tt
            return (x, y, scale, rot, op)
    k = keyframes[-1]
    return (k.x, k.y, k.scale, k.rotation_deg, k.opacity)


def _composite_character(
    canvas: Image.Image,
    sprite: Image.Image,
    x: float,
    y: float,
    scale: float,
    rotation_deg: float,
    opacity: float,
) -> Image.Image:
    width, height = canvas.size
    # transform sprite
    target_w = int(sprite.width * scale)
    target_h = int(sprite.height * scale)
    target_w = max(1, target_w)
    target_h = max(1, target_h)
    sp = sprite.resize((target_w, target_h), Image.LANCZOS)
    if abs(rotation_deg) > 0.001:
        sp = sp.rotate(rotation_deg, expand=True, resample=Image.BICUBIC)
    if opacity < 1.0:
        alpha = sp.getchannel("A")
        alpha = Image.eval(alpha, lambda a: int(a * opacity))
        sp.putalpha(alpha)

    # position center at normalized x,y
    px = int(x * width - sp.width / 2)
    py = int(y * height - sp.height / 2)

    # composite
    canvas.alpha_composite(sp, (px, py))
    return canvas


def render_story(
    story: Story,
    character_assets: List[CharacterAsset],
    config: RenderConfig,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[str]:
    _ensure_dir(config.output_dir)
    sprites = _load_character_images(character_assets)
    provider_cls = PROVIDERS.get(config.background_provider, None)
    if provider_cls is None:
        raise ValueError(f"Unknown background provider: {config.background_provider}")
    provider = provider_cls()

    frame_paths: List[str] = []
    frame_index = 0
    for s_idx, scene in enumerate(story.scenes):
        num_frames = int(math.ceil(scene.duration_seconds * config.fps))
        for f in tqdm(range(num_frames), desc=f"Scene {s_idx+1}/{len(story.scenes)}"):
            t = (f / max(1, num_frames - 1)) * scene.duration_seconds
            bg = provider.get_frame(s_idx, t, config.width, config.height, scene).convert("RGBA")
            canvas = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
            canvas.alpha_composite(bg)

            for track in scene.tracks:
                sprite = sprites.get(track.character)
                if sprite is None:
                    continue
                x, y, sc, rot, op = _interpolate_keyframes(sorted(track.keyframes, key=lambda k: k.time), t)
                canvas = _composite_character(canvas, sprite, x, y, sc, rot, op)

            # Save frame
            frame_path = os.path.join(config.output_dir, f"frame_{frame_index:06d}.png")
            canvas.save(frame_path)
            frame_paths.append(frame_path)
            frame_index += 1
            if on_progress is not None:
                on_progress(frame_index, -1)

    return frame_paths


def write_video_from_frames(frame_paths: List[str], output_video: str, fps: int) -> None:
    try:
        import imageio.v3 as iio
        import imageio_ffmpeg  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("imageio and imageio-ffmpeg are required for video export") from exc
    imgs = [iio.imread(fp) for fp in frame_paths]
    iio.imwrite(output_video, imgs, fps=fps)


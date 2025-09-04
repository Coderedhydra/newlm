from __future__ import annotations

from typing import Tuple

from PIL import Image

from .base import BackgroundProvider
from ..types import Scene


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_rgb(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(_lerp(c1[0], c2[0], t)),
        int(_lerp(c1[1], c2[1], t)),
        int(_lerp(c1[2], c2[2], t)),
    )


class GradientBackgroundProvider(BackgroundProvider):
    def get_frame(self, scene_index: int, t: float, width: int, height: int, scene: Scene) -> Image.Image:
        # Pick colors deterministically per scene
        base_colors = [
            (30, 30, 60),
            (20, 60, 90),
            (60, 20, 80),
            (10, 90, 80),
        ]
        c1 = base_colors[scene_index % len(base_colors)]
        c2 = base_colors[(scene_index + 1) % len(base_colors)]
        # Slight animate angle via t
        alpha = 0.5 + 0.5 * (t % 1.0)
        mixed_top = _lerp_rgb(c1, c2, alpha)
        mixed_bottom = _lerp_rgb(c2, c1, alpha)

        img = Image.new("RGB", (width, height))
        pixels = img.load()
        for y in range(height):
            row_color = _lerp_rgb(mixed_top, mixed_bottom, y / max(1, height - 1))
            for x in range(width):
                pixels[x, y] = row_color
        return img


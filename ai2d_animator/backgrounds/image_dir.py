from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image

from .base import BackgroundProvider
from ..types import Scene
from ..utils import resize_cover


class ImageDirectoryBackgroundProvider(BackgroundProvider):
    def __init__(self, directory: str | None = None) -> None:
        self.directory = directory or "./backgrounds"
        p = Path(self.directory)
        p.mkdir(parents=True, exist_ok=True)
        self.images: List[Path] = [
            fp for fp in sorted(p.iterdir()) if fp.suffix.lower() in {".png", ".jpg", ".jpeg"}
        ]

    def get_frame(self, scene_index: int, t: float, width: int, height: int, scene: Scene) -> Image.Image:
        if not self.images:
            # fallback blank
            return Image.new("RGB", (width, height), (32, 32, 32))
        # choose image by scene index (wrap around)
        idx = scene_index % len(self.images)
        img = Image.open(self.images[idx]).convert("RGB")
        return resize_cover(img, width, height)


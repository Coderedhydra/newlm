from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image

from ..types import Scene


class BackgroundProvider(ABC):
    @abstractmethod
    def get_frame(
        self,
        scene_index: int,
        t: float,
        width: int,
        height: int,
        scene: Scene,
    ) -> Image.Image:  # pragma: no cover - interface
        raise NotImplementedError


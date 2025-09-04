from __future__ import annotations

from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    prompt: Optional[str] = None
    assets_dir: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    scenes: Optional[int] = None
    seconds_per_scene: Optional[float] = None
    background_provider: Optional[str] = None
    background_image_dir: Optional[str] = None
    output_dir: Optional[str] = None
    output_video: Optional[str] = None
    offline: Optional[bool] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    fallback_model_name: Optional[str] = None


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return AppConfig(**data)


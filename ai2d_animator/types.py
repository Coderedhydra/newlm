from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Keyframe(BaseModel):
    time: float = Field(..., description="Seconds from start of scene")
    x: float = Field(..., description="Normalized X position in [0,1]")
    y: float = Field(..., description="Normalized Y position in [0,1]")
    scale: float = Field(1.0, description="Uniform scale, 1.0 is original size")
    rotation_deg: float = Field(0.0, description="Rotation in degrees")
    opacity: float = Field(1.0, description="Opacity in [0,1]")
    easing: str = Field("linear", description="Easing function name")

    @field_validator("x", "y")
    @classmethod
    def _clamp01(cls, value: float) -> float:
        return max(0.0, min(1.0, value))

    @field_validator("opacity")
    @classmethod
    def _clamp_opacity(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class MotionTrack(BaseModel):
    character: str
    keyframes: List[Keyframe]


class Scene(BaseModel):
    title: str
    description: str
    duration_seconds: float = Field(..., gt=0)
    background_prompt: Optional[str] = None
    background_image_path: Optional[str] = None
    tracks: List[MotionTrack] = Field(default_factory=list)


class Story(BaseModel):
    title: str
    synopsis: str
    characters: List[str]
    scenes: List[Scene]

    def total_duration(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)


class CharacterAsset(BaseModel):
    name: str
    image_path: str


class RenderConfig(BaseModel):
    width: int = 1280
    height: int = 720
    fps: int = 24
    output_dir: str = "./frames"
    output_video: Optional[str] = None
    background_provider: str = "gradient"


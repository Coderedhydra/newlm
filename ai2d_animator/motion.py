from __future__ import annotations

import json
from typing import List, Optional

from .gemini_client import GeminiClient
from .types import Story, MotionTrack, Keyframe, Scene


SYSTEM_INSTRUCTION = (
    "You are an animation motion planner. You must return strictly valid JSON with numeric values, not text.")


def _build_motion_prompt(story: Story, fps: int) -> str:
    skeleton = {
        "scenes": [
            {
                "tracks": [
                    {
                        "character": "string",
                        "keyframes": [
                            {
                                "time": 0.0,
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1.0,
                                "rotation_deg": 0.0,
                                "opacity": 1.0,
                                "easing": "linear",
                            }
                        ],
                    }
                ]
            }
        ]
    }
    # Provide concise scene briefs to the model
    briefs = []
    for idx, scene in enumerate(story.scenes):
        briefs.append(
            {
                "scene_index": idx,
                "duration_seconds": scene.duration_seconds,
                "description": scene.description,
            }
        )
    return (
        "Plan motion keyframes for each scene of a 2D animation.\n"
        "Rules:\n"
        "- Use only the characters provided.\n"
        "- Coordinates x,y are normalized in [0,1], (0,0) top-left, (1,1) bottom-right.\n"
        "- Include at least 3-5 keyframes per character per scene for smooth motion.\n"
        "- Spread keyframes across the entire scene duration.\n"
        "- Use easing {linear, easeInQuad, easeOutQuad, easeInOutQuad, easeInCubic, easeOutCubic, easeInOutCubic}.\n"
        f"- Target FPS is {fps}, but return times in seconds.\n"
        "- Avoid sudden jumps; keep motion subtle and readable.\n"
        "- Keep opacity between 0 and 1.\n"
        "Return JSON matching this skeleton (values filled in):\n"
        + json.dumps(skeleton, indent=2)
        + "\nHere are the scene briefs:"\
        + json.dumps(briefs, indent=2)
        + "\nCharacters: " + ", ".join(story.characters)
    )


def generate_motion_plan(
    gemini: GeminiClient,
    story: Story,
    fps: int = 24,
    offline: bool = False,
) -> Story:
    if offline:
        # Simple ping-pong motion stub for each character
        updated_scenes: List[Scene] = []
        for scene in story.scenes:
            tracks: List[MotionTrack] = []
            for name in story.characters:
                duration = scene.duration_seconds
                keyframes = [
                    Keyframe(time=0.0, x=0.2, y=0.5, scale=1.0, rotation_deg=0.0, opacity=1.0, easing="easeInOutQuad"),
                    Keyframe(time=duration * 0.5, x=0.8, y=0.5, scale=1.0, rotation_deg=0.0, opacity=1.0, easing="easeInOutQuad"),
                    Keyframe(time=duration, x=0.2, y=0.5, scale=1.0, rotation_deg=0.0, opacity=1.0, easing="easeInOutQuad"),
                ]
                tracks.append(MotionTrack(character=name, keyframes=keyframes))
            updated_scenes.append(Scene(**{**scene.model_dump(), "tracks": tracks}))
        story.scenes = updated_scenes
        return story

    prompt = _build_motion_prompt(story, fps)
    data = gemini.generate_json(prompt, system_instruction=SYSTEM_INSTRUCTION)
    # Merge tracks into story scenes
    for idx, scene in enumerate(story.scenes):
        try:
            tracks_json = data["scenes"][idx]["tracks"]
        except Exception:
            tracks_json = []
        tracks: List[MotionTrack] = []
        for t in tracks_json:
            if t.get("character") not in story.characters:
                continue
            try:
                kfs = [Keyframe(**k) for k in t.get("keyframes", [])]
            except Exception:
                kfs = []
            if not kfs:
                # Add trivial hold if missing
                kfs = [Keyframe(time=0.0, x=0.5, y=0.5)]
            tracks.append(MotionTrack(character=t.get("character", "unknown"), keyframes=kfs))
        scene.tracks = tracks
    return story


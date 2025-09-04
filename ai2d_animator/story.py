from __future__ import annotations

import json
from typing import List, Optional

from .gemini_client import GeminiClient
from .types import Story, Scene


SYSTEM_INSTRUCTION = (
    "You are a story and motion planner for 2D animations. You must return compact JSON that strictly follows the requested schema."
)


def _build_story_prompt(user_prompt: str, character_names: List[str], num_scenes: int, seconds_per_scene: float) -> str:
    schema = {
        "title": "string",
        "synopsis": "string",
        "characters": ["string"],
        "scenes": [
            {
                "title": "string",
                "description": "string",
                "duration_seconds": seconds_per_scene,
                "background_prompt": "string",
                "background_image_path": None,
                "tracks": [],
            }
        ],
    }
    return (
        "Create a short story outline suitable for a 2D animation.\n"
        f"User prompt: {user_prompt}\n"
        f"Characters (fixed assets, do not invent new ones): {', '.join(character_names)}\n"
        f"Number of scenes: {num_scenes}. Each scene duration: {seconds_per_scene:.2f} seconds.\n"
        "Important constraints:\n"
        "- Only use the provided characters list.\n"
        "- Keep text concise.\n"
        "- Provide a creative 'background_prompt' for each scene that an external image generator can use.\n"
        "- Do not include motion tracks; those are generated later.\n"
        "Return JSON matching this skeleton (values filled in):\n"
        + json.dumps(schema, indent=2)
    )


def generate_story(
    gemini: GeminiClient,
    user_prompt: str,
    character_names: List[str],
    num_scenes: int = 3,
    seconds_per_scene: float = 3.0,
    offline_stub: Optional[Story] = None,
) -> Story:
    if offline_stub is not None:
        return offline_stub

    prompt = _build_story_prompt(user_prompt, character_names, num_scenes, seconds_per_scene)
    data = gemini.generate_json(prompt, system_instruction=SYSTEM_INSTRUCTION)
    # Ensure scenes count and durations
    scenes_data = data.get("scenes", [])[:num_scenes]
    for scene in scenes_data:
        scene["duration_seconds"] = float(seconds_per_scene)
        scene["tracks"] = []
        scene.setdefault("background_prompt", "")
        scene["background_image_path"] = None
    story = Story(
        title=data.get("title", "AI 2D Animation"),
        synopsis=data.get("synopsis", ""),
        characters=character_names,
        scenes=[Scene(**s) for s in scenes_data],
    )
    return story


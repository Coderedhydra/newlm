from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from dotenv import load_dotenv

from .gemini_client import GeminiClient
from .story import generate_story
from .motion import generate_motion_plan
from .renderer import render_story, write_video_from_frames
from .types import CharacterAsset, RenderConfig, Story, Scene
from .backgrounds import PROVIDERS
from .config import load_config, AppConfig


app = typer.Typer(add_completion=False, no_args_is_help=True)


def _load_assets(directory: str) -> List[CharacterAsset]:
    p = Path(directory)
    if not p.exists():
        raise FileNotFoundError(f"Assets directory not found: {directory}")
    assets: List[CharacterAsset] = []
    for file in sorted(p.iterdir()):
        if file.suffix.lower() in {".png"}:
            name = file.stem
            assets.append(CharacterAsset(name=name, image_path=str(file)))
    if not assets:
        raise RuntimeError("No PNG character assets found in the provided directory.")
    return assets


@app.command()
def sample_assets(
    assets_dir: str = typer.Option("./assets", help="Directory to write sample character PNGs"),
):
    """Create two simple placeholder character PNGs (alice.png, bob.png)."""
    from PIL import Image, ImageDraw

    p = Path(assets_dir)
    p.mkdir(parents=True, exist_ok=True)

    def make_circle(color: tuple[int, int, int], name: str) -> None:
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((32, 32, 480, 480), fill=color + (255,))
        img.save(p / f"{name}.png")

    make_circle((255, 80, 80), "alice")
    make_circle((80, 160, 255), "bob")
    print(f"[bold green]Wrote sample assets[/bold green] to {assets_dir}")

@app.command()
def run(
    prompt: Optional[str] = typer.Option(None, help="High-level story prompt"),
    assets_dir: str = typer.Option("./assets", help="Directory with character PNGs named by character"),
    width: int = typer.Option(1280, help="Output width"),
    height: int = typer.Option(720, help="Output height"),
    fps: int = typer.Option(24, help="Frames per second"),
    scenes: int = typer.Option(3, help="Number of scenes"),
    seconds_per_scene: float = typer.Option(3.0, help="Duration per scene in seconds"),
    output_dir: str = typer.Option("./frames", help="Directory to write PNG frames"),
    output_video: Optional[str] = typer.Option(None, help="Optional mp4 path to write video using imageio-ffmpeg"),
    background: str = typer.Option("gradient", help="Background provider: " + ", ".join(PROVIDERS.keys())),
    background_image_dir: Optional[str] = typer.Option(None, help="Required if background=image_dir: directory with background images"),
    offline: bool = typer.Option(False, help="Run without calling Gemini (stub motions)"),
    api_key: Optional[str] = typer.Option(None, help="Google API key; otherwise uses GOOGLE_API_KEY env var"),
    config: Optional[str] = typer.Option(None, help="Path to YAML config"),
    prefer_config: bool = typer.Option(False, help="If true, config overrides CLI when set"),
):
    """Generate story, motion plan, and render frames."""
    load_dotenv()

    # Load config if provided
    cfg: Optional[AppConfig] = load_config(config) if config else None

    def choose(val, cfg_val):
        if prefer_config and cfg_val is not None:
            return cfg_val
        return val if val is not None else cfg_val

    prompt = choose(prompt, cfg.prompt if cfg else None)
    if not prompt:
        raise typer.BadParameter("prompt is required (via --prompt or --config)")
    assets_dir = choose(assets_dir, cfg.assets_dir if cfg else None) or assets_dir
    width = int(choose(width, cfg.width if cfg else None))
    height = int(choose(height, cfg.height if cfg else None))
    fps = int(choose(fps, cfg.fps if cfg else None))
    scenes = int(choose(scenes, cfg.scenes if cfg else None))
    seconds_per_scene = float(choose(seconds_per_scene, cfg.seconds_per_scene if cfg else None))
    output_dir = choose(output_dir, cfg.output_dir if cfg else None) or output_dir
    output_video = choose(output_video, cfg.output_video if cfg else None)
    background = choose(background, cfg.background_provider if cfg else None) or background
    background_image_dir = choose(background_image_dir, cfg.background_image_dir if cfg else None)
    offline = bool(choose(offline, cfg.offline if cfg else None))
    api_key = choose(api_key, cfg.api_key if cfg else None)

    assets = _load_assets(assets_dir)
    character_names = [a.name for a in assets]
    print(f"[bold green]Characters:[/bold green] {', '.join(character_names)}")

    if offline:
        gemini = None
    else:
        gemini = GeminiClient(api_key=api_key)

    if offline:
        offline_scenes = [
            Scene(
                title=f"Scene {i+1}",
                description="Characters move left-right.",
                duration_seconds=seconds_per_scene,
                background_prompt="soft gradient",
                tracks=[],
            )
            for i in range(scenes)
        ]
        story = Story(title="Offline Demo", synopsis=prompt, characters=character_names, scenes=offline_scenes)
    else:
        story = generate_story(
            gemini,
            user_prompt=prompt,
            character_names=character_names,
            num_scenes=scenes,
            seconds_per_scene=seconds_per_scene,
        )

    story = generate_motion_plan(
        gemini if gemini is not None else None,  # type: ignore
        story,
        fps=fps,
        offline=offline,
    )

    config = RenderConfig(
        width=width,
        height=height,
        fps=fps,
        output_dir=output_dir,
        output_video=output_video,
        background_provider=background,
    )
    # Inject background provider configuration when needed
    if background == "image_dir" and background_image_dir:
        # Monkey-patch provider init to pass directory
        from .backgrounds.image_dir import ImageDirectoryBackgroundProvider

        def provider_factory():
            return ImageDirectoryBackgroundProvider(directory=background_image_dir)

        # Override temporarily
        from . import backgrounds as _bg

        _bg.PROVIDERS["image_dir"] = lambda: provider_factory()  # type: ignore

    frame_paths = render_story(story, assets, config)

    if output_video:
        try:
            write_video_from_frames(frame_paths, output_video, fps=fps)
            print(f"[bold green]Wrote video:[/bold green] {output_video}")
        except Exception:
            print("[yellow]Video export failed; frames still written.[/yellow]")

    print(f"[bold green]Done.[/bold green] Wrote {len(frame_paths)} frames to {output_dir}")


if __name__ == "__main__":
    app()


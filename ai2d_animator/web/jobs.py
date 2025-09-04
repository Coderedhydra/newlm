from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..gemini_client import GeminiClient
from ..story import generate_story
from ..motion import generate_motion_plan
from ..renderer import render_story, write_video_from_frames
from ..types import CharacterAsset, RenderConfig, Story


@dataclass
class Job:
    id: str
    status: str = "pending"  # pending, running, done, error
    message: str = ""
    frames: List[str] = field(default_factory=list)
    video_path: Optional[str] = None


class JobManager:
    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(id=job_id)
        with self._lock:
            self.jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self.jobs.get(job_id)

    def run_generation(
        self,
        job: Job,
        prompt: str,
        character_assets: List[CharacterAsset],
        width: int,
        height: int,
        fps: int,
        scenes: int,
        seconds_per_scene: float,
        background_provider: str,
        background_dir: Optional[str],
        output_dir: str,
        output_video: Optional[str],
        api_key: Optional[str],
        offline: bool,
    ) -> None:
        def progress_callback(done: int, total: int) -> None:
            job.message = f"Rendered {done} frames"

        def _thread() -> None:
            job.status = "running"
            try:
                os.makedirs(output_dir, exist_ok=True)
                if offline:
                    story = Story(
                        title="Web Offline",
                        synopsis=prompt,
                        characters=[a.name for a in character_assets],
                        scenes=[
                            {
                                "title": f"Scene {i+1}",
                                "description": "Characters move left-right.",
                                "duration_seconds": seconds_per_scene,
                                "background_prompt": "soft gradient",
                                "tracks": [],
                            }
                            for i in range(scenes)
                        ],
                    )
                else:
                    gemini = GeminiClient(api_key=api_key)
                    story = generate_story(
                        gemini,
                        user_prompt=prompt,
                        character_names=[a.name for a in character_assets],
                        num_scenes=scenes,
                        seconds_per_scene=seconds_per_scene,
                    )
                    story = generate_motion_plan(gemini, story, fps=fps, offline=False)

                config = RenderConfig(
                    width=width,
                    height=height,
                    fps=fps,
                    output_dir=output_dir,
                    output_video=output_video,
                    background_provider=background_provider,
                )
                # Background dir injection for image_dir provider
                if background_provider == "image_dir" and background_dir:
                    from ..backgrounds.image_dir import ImageDirectoryBackgroundProvider
                    from .. import backgrounds as _bg

                    _bg.PROVIDERS["image_dir"] = lambda: ImageDirectoryBackgroundProvider(directory=background_dir)  # type: ignore

                frames = render_story(story, character_assets, config, on_progress=progress_callback)
                job.frames = frames
                if output_video:
                    write_video_from_frames(frames, output_video, fps=fps)
                    job.video_path = f"/download/{os.path.basename(output_video)}"
                job.status = "done"
                job.message = f"Done. {len(frames)} frames"
            except Exception as exc:
                job.status = "error"
                job.message = str(exc)

        t = threading.Thread(target=_thread, daemon=True)
        t.start()


job_manager = JobManager()


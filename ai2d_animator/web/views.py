from __future__ import annotations

import os
from pathlib import Path
from typing import List

from flask import Blueprint, current_app, redirect, render_template, request, send_file, url_for, jsonify

from ..types import CharacterAsset
from .jobs import job_manager


bp = Blueprint("views", __name__)


def _ensure_dirs() -> None:
    for key in ("UPLOAD_FOLDER", "ASSETS_FOLDER", "BACKGROUND_FOLDER", "OUTPUT_FOLDER"):
        os.makedirs(current_app.config[key], exist_ok=True)


@bp.route("/")
def index():
    _ensure_dirs()
    # List assets and backgrounds
    assets_dir = Path(current_app.config["ASSETS_FOLDER"]).resolve()
    bg_dir = Path(current_app.config["BACKGROUND_FOLDER"]).resolve()
    assets = [p.name for p in assets_dir.glob("*.png")]
    backgrounds = [p.name for p in bg_dir.glob("*.png")] + [p.name for p in bg_dir.glob("*.jpg")]
    return render_template("index.html", assets=assets, backgrounds=backgrounds)


@bp.route("/upload/character", methods=["POST"])
def upload_character():
    _ensure_dirs()
    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect(url_for("views.index"))
    filename = Path(file.filename).name
    save_path = Path(current_app.config["ASSETS_FOLDER"]) / filename
    file.save(save_path)
    return redirect(url_for("views.index"))


@bp.route("/upload/background", methods=["POST"])
def upload_background():
    _ensure_dirs()
    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect(url_for("views.index"))
    filename = Path(file.filename).name
    save_path = Path(current_app.config["BACKGROUND_FOLDER"]) / filename
    file.save(save_path)
    return redirect(url_for("views.index"))


@bp.route("/generate", methods=["POST"])
def generate():
    _ensure_dirs()
    prompt = request.form.get("prompt", "")
    width = int(request.form.get("width", 1280))
    height = int(request.form.get("height", 720))
    fps = int(request.form.get("fps", 24))
    scenes = int(request.form.get("scenes", 3))
    seconds_per_scene = float(request.form.get("seconds_per_scene", 3.0))
    background_provider = request.form.get("background_provider", "gradient")
    offline = request.form.get("offline") == "on"
    api_key = request.form.get("api_key") or os.getenv("GOOGLE_API_KEY")

    assets_dir = Path(current_app.config["ASSETS_FOLDER"]).resolve()
    bg_dir = Path(current_app.config["BACKGROUND_FOLDER"]).resolve()
    output_dir = Path(current_app.config["OUTPUT_FOLDER"]).resolve()
    video_out = str(output_dir / "web_demo.mp4")

    character_assets: List[CharacterAsset] = [
        CharacterAsset(name=p.stem, image_path=str(p)) for p in sorted(assets_dir.glob("*.png"))
    ]
    job = job_manager.create()
    job_manager.run_generation(
        job,
        prompt=prompt,
        character_assets=character_assets,
        width=width,
        height=height,
        fps=fps,
        scenes=scenes,
        seconds_per_scene=seconds_per_scene,
        background_provider=background_provider,
        background_dir=str(bg_dir) if background_provider == "image_dir" else None,
        output_dir=str(output_dir),
        output_video=video_out,
        api_key=api_key,
        offline=offline,
    )
    return redirect(url_for("views.status", job_id=job.id))


@bp.route("/status/<job_id>")
def status(job_id: str):
    job = job_manager.get(job_id)
    if job is None:
        return "Not found", 404
    return render_template("status.html", job=job)


@bp.route("/api/status/<job_id>")
def api_status(job_id: str):
    job = job_manager.get(job_id)
    if job is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": job.id, "status": job.status, "message": job.message, "video": job.video_path})


@bp.route("/download/<path:filename>")
def download(filename: str):
    output_dir = Path(current_app.config["OUTPUT_FOLDER"]).resolve()
    file_path = output_dir / filename
    if not file_path.exists():
        return "Not found", 404
    return send_file(str(file_path), as_attachment=True)


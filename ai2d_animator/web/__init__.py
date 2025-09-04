from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.setdefault("UPLOAD_FOLDER", "./uploads")
    app.config.setdefault("ASSETS_FOLDER", "./assets")
    app.config.setdefault("BACKGROUND_FOLDER", "./bg_images")
    app.config.setdefault("OUTPUT_FOLDER", "./frames")
    app.config.setdefault("SECRET_KEY", "dev-secret")

    from .views import bp as views_bp

    app.register_blueprint(views_bp)
    return app


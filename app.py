from flask import Flask

from config import Config
from core.task_manager import TaskManager
from routes import register_blueprints

try:
    from whitenoise import WhiteNoise
except ImportError:  # fallback
    WhiteNoise = None


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    if WhiteNoise is not None:
        app.wsgi_app = WhiteNoise(
            app.wsgi_app,
            root=app.static_folder,
            prefix="static/",
        )

    task_mgr = TaskManager(
        max_workers=app.config.get("TASK_POOL_WORKERS", 2),
        ttl=app.config.get("TASK_TTL_SECONDS", 900),
    )
    app.config["TASK_MANAGER"] = task_mgr

    register_blueprints(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

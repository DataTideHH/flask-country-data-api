from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from country_api.cli import register_cli_commands
from country_api.database import init_database
from country_api.errors import register_error_handlers
from country_api.routes import api


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    default_database = Path(app.instance_path) / "country_data.sqlite"

    app.config.from_mapping(
        DATABASE_PATH=os.getenv("COUNTRY_API_DATABASE", str(default_database)),
    )

    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_database(app.config["DATABASE_PATH"])

    app.register_blueprint(api)
    register_error_handlers(app)
    register_cli_commands(app)
    return app

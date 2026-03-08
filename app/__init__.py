from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name="default"):
    app = Flask(__name__, instance_relative_config=True)

    from config import config
    app.config.from_object(config[config_name])

    db.init_app(app)

    from app.routes.api import api_bp
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    from app.services.config_builder import build_client_config
    app.jinja_env.globals["build_client_config"] = build_client_config

    return app

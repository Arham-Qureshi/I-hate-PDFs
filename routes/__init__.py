from flask import Flask


def register_blueprints(app: Flask):
    from routes.main import main_bp
    from routes.merge import merge_bp
    from routes.split import split_bp
    from routes.summarize import summarize_bp
    from routes.convert import convert_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(merge_bp, url_prefix="/merge")
    app.register_blueprint(split_bp, url_prefix="/split")
    app.register_blueprint(summarize_bp, url_prefix="/summarize")
    app.register_blueprint(convert_bp, url_prefix="/convert")
    app.register_blueprint(api_bp, url_prefix="/api")

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from .config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()

    # Register blueprints
    from .auth import auth_bp
    from .habits import habits_bp
    from .web import web_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(habits_bp, url_prefix='/api')
    app.register_blueprint(web_bp)

    return app
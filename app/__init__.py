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

    # JWT Blocklist callback
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from .models import TokenBlocklist
        jti = jwt_payload.get("jti")
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None

    # Register blueprints
    from .auth import auth_bp
    from .habits import habits_bp
    from .web import web_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(habits_bp, url_prefix='/api')
    app.register_blueprint(web_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
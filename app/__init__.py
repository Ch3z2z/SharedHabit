from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

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

    return app
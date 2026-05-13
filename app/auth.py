from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, jwt
from .models import Users, TokenBlocklist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    user = Users(
        username=data["username"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"])
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User created", "id": user.id, "username": user.username, "email": user.email, "password": user.password_hash})

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    user = Users.query.filter_by(username=data["username"]).first()

    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"msg": "Bad credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token)


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    token = get_jwt()
    jti = token.get("jti")
    
    if not jti:
        return jsonify({"msg": "Invalid token"}), 400
    
    # Добавляем токен в черный список
    blocklisted_token = TokenBlocklist(jti=jti)
    db.session.add(blocklisted_token)
    db.session.commit()
    
    return jsonify({"msg": "Logged out successfully"}), 200

@auth_bp.route("/users/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email})


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email})


@auth_bp.route("/users/me", methods=["PUT"])
@jwt_required()
def update_me():
    user_id = int(get_jwt_identity())
    data = request.json
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if username:
        user.username = username
    if email:
        user.email = email
    if password:
        user.password_hash = generate_password_hash(password)

    db.session.commit()

    return jsonify({"id": user.id, "username": user.username, "email": user.email})
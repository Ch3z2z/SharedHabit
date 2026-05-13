from . import db
from datetime import datetime
import uuid

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Habits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_shared = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HabitMembers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    role = db.Column(db.String, default="member")

    __table_args__ = (
        db.UniqueConstraint("habit_id", "user_id"),
    )

class HabitLogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "user_id", "date"),
    )

class Invites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"))
    inviter_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    invited_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    email = db.Column(db.String)
    status = db.Column(db.String, default="pending")

    token = db.Column(db.String, unique=True)
    expires_at = db.Column(db.DateTime)
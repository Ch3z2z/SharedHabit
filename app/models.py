from . import db
from datetime import datetime
from sqlalchemy import DDL, event
import enum


class InviteStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class HabitRole(enum.Enum):
    owner = "owner"
    member = "member"


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

    # текущий владелец привычки
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    is_shared = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HabitMembers(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    habit_id = db.Column(
        db.Integer,
        db.ForeignKey("habits.id", ondelete="CASCADE")
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE")
    )

    # owner / member
    role = db.Column(db.Enum(HabitRole, name="habit_role"), default=HabitRole.member)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "user_id"),
    )


class HabitLogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    habit_id = db.Column(
        db.Integer,
        db.ForeignKey("habits.id", ondelete="CASCADE")
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE")
    )

    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "user_id", "date"),
    )


class Invites(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    habit_id = db.Column(
        db.Integer,
        db.ForeignKey("habits.id", ondelete="CASCADE")
    )

    inviter_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    invited_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    email = db.Column(db.String)

    status = db.Column(
        db.Enum(InviteStatus, name="invite_status"),
        default=InviteStatus.pending,
        nullable=False
    )

    token = db.Column(db.String, unique=True)
    expires_at = db.Column(db.DateTime)


# =========================================================
# TRIGGER FUNCTION
# =========================================================

transfer_owner_function = DDL("""
CREATE OR REPLACE FUNCTION transfer_habit_ownership()
RETURNS TRIGGER AS $$
DECLARE
    members_count INTEGER;
    new_owner_member_id INTEGER;
    new_owner_user_id INTEGER;
BEGIN

    -- Считаем оставшихся участников
    SELECT COUNT(*)
    INTO members_count
    FROM habit_members
    WHERE habit_id = OLD.habit_id;

    -- Если участников больше нет -> удалить привычку
    IF members_count = 0 THEN

        DELETE FROM habits
        WHERE id = OLD.habit_id;

        RETURN OLD;

    END IF;


    -- Если удалён owner -> передаём ownership
    IF OLD.role = 'owner' THEN

        SELECT id, user_id
        INTO new_owner_member_id, new_owner_user_id
        FROM habit_members
        WHERE habit_id = OLD.habit_id
        ORDER BY id
        LIMIT 1;

        IF new_owner_member_id IS NOT NULL THEN

            UPDATE habit_members
            SET role = 'owner'
            WHERE id = new_owner_member_id;

            UPDATE habits
            SET created_by = new_owner_user_id
            WHERE id = OLD.habit_id;

        END IF;

    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
""")


# =========================================================
# TRIGGER
# =========================================================

transfer_owner_trigger = DDL("""
CREATE TRIGGER trg_transfer_habit_ownership
AFTER DELETE ON habit_members
FOR EACH ROW
EXECUTE FUNCTION transfer_habit_ownership();
""")


# =========================================================
# REGISTER EVENTS
# =========================================================

event.listen(
    HabitMembers.__table__,
    "after_create",
    transfer_owner_function
)

event.listen(
    HabitMembers.__table__,
    "after_create",
    transfer_owner_trigger
)
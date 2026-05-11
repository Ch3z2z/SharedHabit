from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid
from collections import defaultdict
from . import db
from .models import Habits, HabitMembers, HabitLogs, Invites, Users
from .utils import is_member, is_owner

habits_bp = Blueprint('habits', __name__)

def get_username_from_id(user_id):
    if not user_id:
        return None
    user = Users.query.get(user_id)
    return user.username if user else f'#{user_id}'

@habits_bp.route("/habits", methods=["POST"])
@jwt_required()
def create_habit():
    user_id = int(get_jwt_identity())
    data = request.json

    habit = Habits(
        title=data["title"],
        description=data.get("description"),
        created_by=user_id,
        is_shared=data.get("is_shared", False)
    )

    try:
        db.session.add(habit)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Error creating habit"}), 500

    member = HabitMembers(
        habit_id=habit.id,
        user_id=user_id,
        role="owner"
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({"id": habit.id})

@habits_bp.route("/habits", methods=["GET"])
@jwt_required()
def get_habits():
    user_id = get_jwt_identity()
    

    habits = db.session.query(Habits).join(HabitMembers).filter(
        HabitMembers.user_id == user_id
    ).all()

    return jsonify([
        {
            "id": h.id,
            "title": h.title,
            "created_by": h.created_by,
            "created_by_username": get_username_from_id(h.created_by),
            "is_shared": h.is_shared
        }
        for h in habits
    ])


@habits_bp.route("/habits/<int:habit_id>", methods=["GET"])
@jwt_required()
def get_habit(habit_id):
    user_id = int(get_jwt_identity())
    if not is_member(user_id, habit_id):
        return jsonify({"msg": "Forbidden"}), 403

    habit = Habits.query.get(habit_id)
    if not habit:
        return jsonify({"msg": "Not found"}), 404

    members = HabitMembers.query.filter_by(habit_id=habit_id).all()
    member_ids = [m.user_id for m in members]

    # Получить логи для всех участников, если shared
    if habit.is_shared:
        logs = HabitLogs.query.filter(HabitLogs.habit_id == habit_id, HabitLogs.user_id.in_(member_ids)).all()
    else:
        logs = HabitLogs.query.filter_by(habit_id=habit_id, user_id=user_id).all()

    invites = Invites.query.filter_by(habit_id=habit_id).all()
    invite_data = []
    for inv in invites:
        data = {
            "id": inv.id,
            "inviter_id": inv.inviter_id,
            "inviter_username": get_username_from_id(inv.inviter_id),
            "invited_user_id": inv.invited_user_id,
            "invited_username": get_username_from_id(inv.invited_user_id),
            "status": inv.status,
        }
        if inv.invited_user_id == user_id or inv.inviter_id == user_id:
            data["token"] = inv.token
        invite_data.append(data)

    # Группировка логов по пользователю
    logs_by_user = {}
    completed_dates_by_user = defaultdict(set)
    today = datetime.now().date()
    today_status_by_user = {}

    for log in logs:
        user_id_log = log.user_id
        if user_id_log not in logs_by_user:
            logs_by_user[user_id_log] = []
        logs_by_user[user_id_log].append({"date": log.date.isoformat(), "completed": log.completed})

        if log.completed:
            completed_dates_by_user[user_id_log].add(log.date)

        if log.date == today:
            today_status_by_user[user_id_log] = log.completed

    def calculate_streak(dates):
        if not dates:
            return 0
        sorted_dates = sorted(dates, reverse=True)
        streak_count = 1
        previous = sorted_dates[0]
        for current_date in sorted_dates[1:]:
            if (previous - current_date).days == 1:
                streak_count += 1
                previous = current_date
            else:
                break
        return streak_count

    members_data = []
    for member in members:
        member_completed_dates = completed_dates_by_user.get(member.user_id, set())
        members_data.append({
            "user_id": member.user_id,
            "username": get_username_from_id(member.user_id),
            "role": member.role,
            "today_completed": today_status_by_user.get(member.user_id),
            "streak": calculate_streak(member_completed_dates)
        })

    streak = 0
    if habit.is_shared and len(member_ids) > 1:
        date_completions = defaultdict(list)
        for log in logs:
            date_completions[log.date].append(log.completed)

        full_completion_dates = {
            date for date, completions in date_completions.items()
            if len(completions) == len(member_ids) and all(completions)
        }

        if full_completion_dates:
            current_date = max(full_completion_dates)
            streak = 0
            while current_date in full_completion_dates:
                streak += 1
                current_date -= timedelta(days=1)

    return jsonify({
        "id": habit.id,
        "title": habit.title,
        "description": habit.description,
        "is_shared": habit.is_shared,
        "created_by": habit.created_by,
        "created_by_username": get_username_from_id(habit.created_by),
        "members": members_data,
        "logs": logs_by_user,
        "streak": streak,
        "invites": invite_data
    })


@habits_bp.route("/habits/<int:habit_id>/invites", methods=["GET"])
@jwt_required()
def list_habit_invites(habit_id):
    user_id = int(get_jwt_identity())
    if not is_member(user_id, habit_id):
        return jsonify({"msg": "Forbidden"}), 403

    invites = Invites.query.filter_by(habit_id=habit_id).all()
    return jsonify([{
        "id": inv.id,
        "inviter_id": inv.inviter_id,
        "inviter_username": get_username_from_id(inv.inviter_id),
        "invited_user_id": inv.invited_user_id,
        "invited_username": get_username_from_id(inv.invited_user_id),
        "email": inv.email,
        "status": inv.status,
        "token": inv.token if inv.inviter_id == user_id or inv.invited_user_id == user_id else None
    } for inv in invites])


@habits_bp.route("/habits/<int:habit_id>", methods=["PUT"])
@jwt_required()
def update_habit(habit_id):
    user_id = int(get_jwt_identity())
    if not is_owner(user_id, habit_id):
        return jsonify({"msg": "Only owner can update"}), 403

    data = request.json
    habit = Habits.query.get(habit_id)
    if not habit:
        return jsonify({"msg": "Not found"}), 404

    title = data.get("title")
    description = data.get("description")
    is_shared = data.get("is_shared")

    if title is not None:
        habit.title = title
    if description is not None:
        habit.description = description
    if is_shared is not None:
        habit.is_shared = bool(is_shared)

    db.session.commit()
    return jsonify({"msg": "updated", "id": habit.id})

@habits_bp.route("/habits/<int:habit_id>/log", methods=["POST"])
@jwt_required()
def log_habit(habit_id):
    user_id = get_jwt_identity()
    data = request.json

    if not is_member(int(user_id), habit_id):
        return jsonify({"msg": "Access denied"}), 403

    if "completed" not in data:
        return jsonify({"msg": "Missing 'completed' in request"}), 400

    date = datetime.now().date()

    log = HabitLogs.query.filter_by(
        habit_id=habit_id,
        user_id=int(user_id),
        date=date
    ).first()

    if log:
        log.completed = data["completed"]
    else:
        log = HabitLogs(
            habit_id=habit_id,
            user_id=int(user_id),
            date=date,
            completed=data["completed"]
        )
        db.session.add(log)

    db.session.commit()

    return jsonify({"msg": "logged"})

@habits_bp.route("/habits/<int:habit_id>/invite", methods=["POST"])
@jwt_required()
def invite(habit_id):
    user_id = int(get_jwt_identity())
    data = request.json

    if not is_member(user_id, habit_id):
        return jsonify({"msg": "Forbidden"}), 403

    invited_username = (data.get("username") or data.get("invited_username") or "").strip()

    if not invited_username:
        return jsonify({"msg": "Provide invited username"}), 400

    if invited_username == get_username_from_id(user_id):
        return jsonify({"msg": "You can't invite yourself"}), 400

    invited_user = Users.query.filter_by(username=invited_username).first()
    if not invited_user:
        return jsonify({"msg": "User not found"}), 404

    if is_member(invited_user.id, habit_id):
        return jsonify({"msg": "User is already a member"}), 400

    token = str(uuid.uuid4())

    invite = Invites(
        habit_id=habit_id,
        inviter_id=user_id,
        invited_user_id=invited_user.id,
        email=None,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=2)
    )

    db.session.add(invite)
    db.session.commit()

    return jsonify({"invite_token": token})

@habits_bp.route("/invites/<token>/accept", methods=["POST"])
@jwt_required()
def accept_invite(token):
    user_id = get_jwt_identity()

    invite = Invites.query.filter_by(token=token).first()

    if not invite or invite.status != "pending" or (invite.invited_user_id and invite.invited_user_id != int(user_id)):
        return jsonify({"msg": "Invalid invite"}), 400
    
    if invite.expires_at < datetime.utcnow():
        return jsonify({"msg": "Invite expired"}), 400

    if is_member(int(user_id), invite.habit_id):
        return jsonify({"msg": "Already a member"}), 400

    invite.status = "accepted"

    member = HabitMembers(
        habit_id=invite.habit_id,
        user_id=int(user_id)
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({"msg": "joined habit"})

@habits_bp.route("/invites", methods=["GET"])
@jwt_required()
def list_my_invites():
    user_id = int(get_jwt_identity())
    pending = Invites.query.filter_by(invited_user_id=user_id, status='pending').all()
    return jsonify([{
        'id': i.id,
        'habit_id': i.habit_id,
        'habit_title': Habits.query.get(i.habit_id).title if Habits.query.get(i.habit_id) else None,
        'inviter_id': i.inviter_id,
        'inviter_username': get_username_from_id(i.inviter_id),
        'invited_user_id': i.invited_user_id,
        'invited_username': get_username_from_id(i.invited_user_id),
        'email': i.email,
        'token': i.token,
        'status': i.status,
        'expires_at': i.expires_at.isoformat() if i.expires_at else None
    } for i in pending])


@habits_bp.route("/invites/<token>/reject", methods=["POST"])
@jwt_required()
def reject_invite(token):
    user_id = int(get_jwt_identity())
    invite = Invites.query.filter_by(token=token).first()

    if not invite or invite.status != "pending" or invite.invited_user_id != user_id:
        return jsonify({"msg": "Invalid invite"}), 400

    invite.status = "rejected"
    db.session.commit()

    return jsonify({"msg": "rejected"})


@habits_bp.route("/habits/<int:habit_id>", methods=["DELETE"])
@jwt_required()
def remove_habit(habit_id):
    user_id = int(get_jwt_identity())

    if not is_owner(user_id, habit_id):
        return jsonify({"msg": "Only owner can delete habit"}), 403

    HabitLogs.query.filter_by(habit_id=habit_id).delete()
    HabitMembers.query.filter_by(habit_id=habit_id).delete()
    Invites.query.filter_by(habit_id=habit_id).delete()

    habit = Habits.query.get(habit_id)
    db.session.delete(habit)
    db.session.commit()

    return jsonify({"msg": "Habit removed"})

@habits_bp.route("/habits/<int:habit_id>/leave", methods=["POST"])
@jwt_required()
def leave_habit(habit_id):
    user_id = int(get_jwt_identity())

    if not is_member(user_id, habit_id):
        return jsonify({"msg": "Forbidden"}), 403

    member = HabitMembers.query.filter_by(
        habit_id=habit_id,
        user_id=user_id
    ).first()

    if not member:
        return jsonify({"msg": "Not a member"}), 404

    if member.role == "owner":
        return jsonify({"msg": "Owner cannot leave. Transfer ownership or delete habit"}), 400

    db.session.delete(member)
    db.session.commit()

    return jsonify({"msg": "Left habit"})

@habits_bp.route("/habits/<int:habit_id>/members/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(habit_id, user_id):
    current_user = int(get_jwt_identity())

    if not is_owner(current_user, habit_id):
        return jsonify({"msg": "Only owner can remove members"}), 403

    member = HabitMembers.query.filter_by(
        habit_id=habit_id,
        user_id=user_id
    ).first()

    if not member:
        return jsonify({"msg": "Member not found"}), 404

    if member.role == "owner":
        return jsonify({"msg": "Cannot remove owner"}), 400

    db.session.delete(member)
    db.session.commit()

    return jsonify({"msg": "Member removed"})
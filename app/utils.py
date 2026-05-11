from .models import HabitMembers

def is_member(user_id, habit_id):
    return HabitMembers.query.filter_by(
        user_id=user_id,
        habit_id=habit_id
    ).first() is not None

def is_owner(user_id, habit_id):
    member = HabitMembers.query.filter_by(
        user_id=user_id,
        habit_id=habit_id,
        role="owner"
    ).first()
    return member is not None
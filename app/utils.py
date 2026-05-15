from .models import HabitMembers, HabitRole

def is_member(user_id, habit_id):
    return HabitMembers.query.filter_by(
        user_id=user_id,
        habit_id=habit_id
    ).first() is not None

def is_owner(user_id, habit_id):
    member = HabitMembers.query.filter_by(
        user_id=user_id,
        habit_id=habit_id,
        role=HabitRole.owner
    ).first()
    return member is not None
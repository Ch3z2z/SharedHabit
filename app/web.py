from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__, template_folder='templates')

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/habits')
def habits():
    return render_template('habits.html')

@web_bp.route('/habit/<int:habit_id>')
def habit(habit_id):
    return render_template('habit.html', habit_id=habit_id)

@web_bp.route('/habit/<int:habit_id>/edit')
def habit_edit(habit_id):
    return render_template('habit_edit.html', habit_id=habit_id)

@web_bp.route('/profile')
def profile():
    return render_template('profile.html')

@web_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    return render_template('user_profile.html', user_id=user_id)

@web_bp.route('/profile/settings')
def profile_settings():
    return render_template('profile_settings.html')


@web_bp.route('/invites')
def invites():
    return render_template('invites.html')

from app import db
from app.models import User, Score
from datetime import datetime

def calculate_sums(score_type):
    users = User.query.all()
    user_sums = {}

    for user in users:
        score = Score.query.filter_by(user_id=user.id, score_type=score_type).first()
        score_value = score.score if score else 0
        user_sums[user.username] = score_value

    sorted_users = sorted(user_sums.items(), key=lambda x: x[1], reverse=True)
    return sorted_users

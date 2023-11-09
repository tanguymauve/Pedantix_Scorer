from app import db
from app.models import User, Score
from datetime import datetime
from sqlalchemy import func

def calculate_sums(score_type):
    users = User.query.all()

    # Use func.sum to calculate the sum of scores for each user
    user_sums = (
        db.session.query(User.username, func.sum(Score.score).label('total_score'))
        .join(Score, User.id == Score.user_id)
        .filter(Score.score_type == score_type)
        .group_by(User.username)
        .all()
    )

    sorted_users = sorted(user_sums, key=lambda x: x.total_score)  # Reverse the order
    print(f"calculate_sums - Score Type: {score_type}, Sorted Users: {sorted_users}")
    return sorted_users

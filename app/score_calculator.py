from app import db
from app.models import User, Score
from datetime import datetime
from sqlalchemy import func
import schedule
import time
from threading import Thread

# Constants for reset times
PEDANTIX_RESET_HOUR = 0  # 12:00 AM UTC
CEMANTIX_RESET_HOUR = 12  # 12:00 PM UTC

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

def calculate_overall_weekly_ranking():
    # Logic to calculate overall weekly ranking by combining Pedantix and Cemantix scores

    users = User.query.all()

    # Get the daily rankings for Pedantix and Cemantix
    pedantix_ranking = calculate_sums('Pedantix')
    cemantix_ranking = calculate_sums('Cemantix')

    # Create dictionaries to store points for each user
    pedantix_points = {username: 0 for username, _ in pedantix_ranking}
    cemantix_points = {username: 0 for username, _ in cemantix_ranking}

    # Assign points based on daily rankings for Pedantix
    for i, (username, _) in enumerate(pedantix_ranking):
        pedantix_points[username] += 3 - i  # Assign points based on the position in the daily ranking

    # Assign points based on daily rankings for Cemantix
    for i, (username, _) in enumerate(cemantix_ranking):
        cemantix_points[username] += 3 - i  # Assign points based on the position in the daily ranking

    # Combine points for each user
    combined_points = {username: pedantix_points[username] + cemantix_points[username] for username in pedantix_points}

    # Sort users based on combined points in descending order
    sorted_users = sorted(combined_points.items(), key=lambda x: x[1], reverse=True)

    return sorted_users

def get_user_score(username, score_type):
    # Helper function to get the score of a user for a specific score_type
    user = User.query.filter_by(username=username).first()
    if user:
        score = Score.query.filter_by(user_id=user.id, score_type=score_type).first()
        return score.score if score else 0
    return 0

def update_daily_rankings():
    # Calculate daily rankings and update scores
    update_daily_rankings_for_score_type('Pedantix')
    update_daily_rankings_for_score_type('Cemantix')

def update_daily_rankings_for_score_type(score_type):
    # Get scores within the last 24 hours
    current_time = time.localtime()
    start_time = time.mktime((current_time.tm_year, current_time.tm_mon, current_time.tm_mday,
                            current_time.tm_hour - 24, current_time.tm_min, current_time.tm_sec,
                            current_time.tm_wday, current_time.tm_yday, current_time.tm_isdst))
    
    scores_within_24_hours = (
        db.session.query(Score.user_id, func.sum(Score.score).label('total_score'))
        .filter(Score.score_type == score_type, Score.timestamp >= start_time)
        .group_by(Score.user_id)
        .order_by(func.sum(Score.score).desc())
        .limit(3)
        .all()
    )

    # Update scores based on daily rankings
    for rank, (user_id, _) in enumerate(scores_within_24_hours, start=1):
        user = User.query.get(user_id)
        if rank == 1:
            user.add_score(3, score_type)
        elif rank == 2:
            user.add_score(2, score_type)
        elif rank == 3:
            user.add_score(1, score_type)

def reset_scores():
    # Reset scores at specific hours
    current_hour = time.localtime().tm_hour
    if current_hour == PEDANTIX_RESET_HOUR:
        reset_scores_for_score_type('Pedantix')
    elif current_hour == CEMANTIX_RESET_HOUR:
        reset_scores_for_score_type('Cemantix')

def reset_scores_for_score_type(score_type):
    # Reset scores for the specified score type
    scores_to_reset = Score.query.filter_by(score_type=score_type).all()
    for score in scores_to_reset:
        db.session.delete(score)
    db.session.commit()

# Schedule tasks
schedule.every().day.at("00:01").do(reset_scores)  # Schedule reset_scores every day at 12:05 AM UTC
schedule.every().day.at("12:01").do(reset_scores)  # Schedule reset_scores every day at 12:05 PM UTC
schedule.every().hour.at(":01").do(update_daily_rankings)  # Schedule update_daily_rankings every hour at xx:30

# Continuous loop to execute scheduled tasks
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the continuous loop in a separate thread
schedule_thread = Thread(target=run_schedule)
schedule_thread.start()

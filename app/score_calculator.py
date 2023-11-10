from app import app, db
from app.models import User, Score, WeeklyPoints
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from threading import Thread
from flask import current_app
import schedule
import time

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
    users = User.query.all()

    pedantix_ranking = calculate_sums('Pedantix')
    cemantix_ranking = calculate_sums('Cemantix')

    pedantix_points = {username: 0 for username, _ in pedantix_ranking}
    cemantix_points = {username: 0 for username, _ in cemantix_ranking}

    for i, (username, _) in enumerate(pedantix_ranking):
        pedantix_points[username] += 3 - i

    for i, (username, _) in enumerate(cemantix_ranking):
        cemantix_points[username] += 3 - i

    combined_points = {username: pedantix_points[username] + cemantix_points[username] for username in pedantix_points}

    sorted_users = sorted(combined_points.items(), key=lambda x: x[1], reverse=True)

    for username, points in sorted_users:
        user = User.query.filter_by(username=username).first()
        weekly_points = WeeklyPoints.query.filter_by(user_id=user.id).first()

        if not weekly_points:
            weekly_points = WeeklyPoints(user_id=user.id)
            weekly_points.combined_points = points
        else:
            weekly_points.combined_points += points

        db.session.add(weekly_points)
        db.session.commit()

    return sorted_users

def get_user_score(username, score_type):
    user = User.query.filter_by(username=username).first()
    if user:
        score = Score.query.filter_by(user_id=user.id, score_type=score_type).first()
        return score.score if score else 0
    return 0

def get_last_weekly_update_date():
    last_update = WeeklyPoints.query.order_by(WeeklyPoints.last_update_date.desc()).first()

    if last_update:
        return last_update.last_update_date.date() if last_update else None
    else:
        return None

def update_last_weekly_update_date(current_date):
    last_update = WeeklyPoints.query.order_by(WeeklyPoints.last_update_date.desc()).first()

    if last_update:
        last_update.last_update_date = current_date
    else:
        last_update = WeeklyPoints(last_update_date=current_date)
        db.session.add(last_update)

    db.session.commit()

def update_weekly_points(score_type):
    update_daily_rankings_for_score_type(score_type)

    weekly_points = WeeklyPoints.query.first()
    if not weekly_points:
        weekly_points = WeeklyPoints(combined_points=0)

    combined_points = calculate_combined_points()
    weekly_points.combined_points += combined_points
    weekly_points.last_update_date = datetime.utcnow()

    db.session.add(weekly_points)
    db.session.commit()

def calculate_combined_points():
    pedantix_ranking = calculate_sums('Pedantix')
    cemantix_ranking = calculate_sums('Cemantix')

    pedantix_points = {username: 0 for username, _ in pedantix_ranking}
    cemantix_points = {username: 0 for username, _ in cemantix_ranking}

    for i, (username, _) in enumerate(pedantix_ranking):
        pedantix_points[username] += 3 - i

    for i, (username, _) in enumerate(cemantix_ranking):
        cemantix_points[username] += 3 - i

    combined_points = {username: pedantix_points[username] + cemantix_points[username] for username in pedantix_points}

    total_combined_points = sum(combined_points.values())
    return total_combined_points

def update_daily_rankings():
    update_daily_rankings_for_score_type('Pedantix')
    update_daily_rankings_for_score_type('Cemantix')

def update_daily_rankings_for_score_type(score_type):
    current_time = datetime.utcnow()
    start_time = (current_time - timedelta(days=1)).timestamp()

    scores_within_24_hours = (
        db.session.query(Score.user_id, func.sum(Score.score).label('total_score'))
        .filter(Score.score_type == score_type, Score.timestamp >= start_time)
        .group_by(Score.user_id)
        .order_by(func.sum(Score.score).desc())
        .limit(3)
        .all()
    )

    for rank, (user_id, _) in enumerate(scores_within_24_hours, start=1):
        user = User.query.get(user_id)
        if rank == 1:
            user.add_points(3)
        elif rank == 2:
            user.add_points(2)
        elif rank == 3:
            user.add_points(1)

def reset_scores():
    print("Reset scores function called")
    
    # Get the current UTC hour
    current_utc_hour = datetime.utcnow().hour
    
    # Calculate the local hour based on the UTC offset (adjust the offset as needed)
    local_hour = (datetime.utcnow() + timedelta(hours=1)).hour
    print(f"Current UTC hour: {current_utc_hour}, Local hour: {local_hour}")

    if local_hour == PEDANTIX_RESET_HOUR:
        print(f"Resetting scores for Pedantix at local hour {local_hour}")
        with current_app.app_context():
            reset_scores_for_score_type('Pedantix')
    elif local_hour == CEMANTIX_RESET_HOUR:
        print(f"Resetting scores for Cemantix at local hour {local_hour}")
        with current_app.app_context():
            reset_scores_for_score_type('Cemantix')



def reset_scores_for_score_type(score_type):
    print(f"Reset scores for {score_type} called")
    scores_to_reset = Score.query.filter_by(score_type=score_type).all()
    print(f"Scores to reset: {scores_to_reset}")
    
    for score in scores_to_reset:
        db.session.delete(score)
    
    db.session.commit()

    print(f"Scores reset for {score_type}")


# Schedule tasks
schedule.every().day.at("02:38").do(reset_scores)  # Schedule reset_scores every day at 12:05 AM UTC
schedule.every().day.at("12:01").do(reset_scores)  # Schedule reset_scores every day at 12:05 PM UTC
schedule.every().hour.at(":01").do(update_daily_rankings)  # Schedule update_daily_rankings every hour at xx:30

# Continuous loop to execute scheduled tasks
def run_schedule():
    with app.app_context():
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                print(f"Error in schedule execution: {e}")

            time.sleep(1)

# Start the continuous loop in a separate thread
schedule_thread = Thread(target=run_schedule)
schedule_thread.start()

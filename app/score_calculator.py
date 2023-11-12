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
CEMANTIX_RESET_HOUR = 18  # 12:00 PM UTC

def calculate_sums(score_type):
    # Use func.sum to calculate the sum of scores for each user
    user_sums = (
        db.session.query(User.username, func.sum(Score.score).label('total_score'))
        .join(Score, User.id == Score.user_id)
        .filter(Score.score_type == score_type)
        .group_by(User.username)
        .all()
    )

    sorted_users = sorted(user_sums, key=lambda x: x.total_score) if user_sums else []
    print(f"calculate_sums - Score Type: {score_type}, Sorted Users: {sorted_users}")
    return sorted_users

def calculate_ranking_and_points(score_type):
    ranking = calculate_sums(score_type)
    points = {username: 0 for username, _ in ranking}

    for i, (username, _) in enumerate(ranking):
        user = User.query.filter_by(username=username).first()
        weekly_points = WeeklyPoints.query.filter_by(user_id=user.id).first()

        if weekly_points:
            points[username] += weekly_points.combined_points

    return points

def calculate_overall_weekly_ranking():
    pedantix_points = calculate_ranking_and_points('Pedantix')
    cemantix_points = calculate_ranking_and_points('Cemantix')

    combined_points = {username: pedantix_points.get(username, 0) + cemantix_points.get(username, 0) for username in pedantix_points}

    sorted_users = sorted(combined_points.items(), key=lambda x: x[1], reverse=True)

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

def update_weekly_points():
    update_daily_rankings_for_score_type('Pedantix')
    update_daily_rankings_for_score_type('Cemantix')

    # Get the weekly points from the database for each user
    weekly_points = (
        db.session.query(User.username, WeeklyPoints.combined_points.label('points_awarded'))
        .join(User, User.id == WeeklyPoints.user_id)
        .all()
    )

    # Update the WeeklyPoints table with the calculated weekly points
    for username, points_awarded in weekly_points:
        user = User.query.filter_by(username=username).first()
        weekly_points_entry = WeeklyPoints.query.filter_by(user_id=user.id).first()

        if not weekly_points_entry:
            # Create a new entry if it doesn't exist
            weekly_points_entry = WeeklyPoints(user_id=user.id, combined_points=0)

        # Add the points awarded in the current round to the existing combined_points
        weekly_points_entry.combined_points += points_awarded
        weekly_points_entry.last_update_date = datetime.utcnow()

        db.session.add(weekly_points_entry)

    db.session.commit()

def calculate_combined_points():
    pedantix_points = calculate_ranking_and_points('Pedantix')
    cemantix_points = calculate_ranking_and_points('Cemantix')

    all_usernames = set(pedantix_points.keys()) | set(cemantix_points.keys())

    combined_points = {username: pedantix_points.get(username, 0) + cemantix_points.get(username, 0) for username in all_usernames}

    total_combined_points = sum(combined_points.values())
    return total_combined_points

def update_daily_rankings():
    with app.app_context():
        update_daily_rankings_for_score_type('Pedantix')
        update_daily_rankings_for_score_type('Cemantix')

def update_daily_rankings_for_score_type(score_type):
    current_time = datetime.utcnow()
    start_time = (current_time - timedelta(days=1)).timestamp()

    scores_within_24_hours = (
        db.session.query(Score.user_id, func.sum(Score.score).label('total_score'))
        .filter(Score.score_type == score_type, Score.timestamp >= start_time)
        .group_by(Score.user_id)
        .order_by(func.sum(Score.score))
        .limit(3)
        .all()
    )

    for rank, (user_id, _) in enumerate(scores_within_24_hours, start=1):
        user = User.query.get(user_id)
        points_awarded = 4 - rank  # 3 points for the lowest score, 2 for the second, 1 for the third
        user.add_weekly_points(points_awarded)


def reset_scores():
    print("Reset scores function called")
    
    # Get the current UTC hour
    current_utc_hour = datetime.utcnow().hour
    
    # Calculate the local hour based on the UTC offset (adjust the offset as needed)
    local_hour = (datetime.utcnow() + timedelta(hours=1)).hour
    print(f"Current UTC hour: {current_utc_hour}, Local hour: {local_hour}")

    if local_hour == PEDANTIX_RESET_HOUR:
        print(f"Resetting scores for Pedantix at local hour {local_hour}")
        with app.app_context():
            reset_scores_for_score_type('Pedantix')
    elif local_hour == CEMANTIX_RESET_HOUR:
        print(f"Resetting scores for Cemantix at local hour {local_hour}")
        with app.app_context():
            reset_scores_for_score_type('Cemantix')



def reset_scores_for_score_type(score_type):
    print(f"Reset scores for {score_type} called")
    with app.app_context():
        scores_to_reset = Score.query.filter_by(score_type=score_type).all()
        print(f"Number of scores to reset for {score_type}: {len(scores_to_reset)}")
        
        for score in scores_to_reset:
            db.session.delete(score)
        
        db.session.commit()

        print(f"Scores reset for {score_type}")


def scheduler_loop():
    # Schedule tasks
    schedule.every().day.at("00:50").do(reset_scores)
    schedule.every().day.at("18:16").do(reset_scores)
    schedule.every().hour.at(":01").do(update_daily_rankings)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Error in schedule execution: {e}")

        # Sleep for 1 second between iterations
        time.sleep(1)

# Start the scheduler loop in a separate thread
schedule_thread = Thread(target=scheduler_loop)
schedule_thread.start()

# Run the Flask app using the built-in development server
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

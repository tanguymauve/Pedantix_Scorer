from app import app, db
from app.models import User, Score, WeeklyPoints
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, and_
from threading import Thread
from flask import current_app
import schedule
import time

# Constants for reset times
PEDANTIX_RESET_HOUR = 0  # 12:00 AM UTC
CEMANTIX_RESET_HOUR = 12 # 12:00 PM UTC

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

pedantix_ranking = {}
cemantix_ranking = {}

def update_weekly_points_pedantix():
    print("Updating weekly points for Pedantix...")
    with app.app_context():
        update_daily_rankings_for_score_type('Pedantix')

        # Get the current time
        current_time = datetime.utcnow()

        # Set the time interval (e.g., 1 hour) during which the weekly points won't be updated again
        update_interval = timedelta(hours=1)

        # Get the weekly points from the database for each user
        pedantix_weekly_points = (
            db.session.query(User.id, User.username, WeeklyPoints.combined_points.label('points_awarded'))
            .join(User, User.id == WeeklyPoints.user_id)
            .filter(Score.score_type == 'Pedantix')  # Filter by score type
            .distinct(User.id, WeeklyPoints.combined_points)  # Add distinct to avoid duplicates
            .all()
        )

        print("DEBUG: Printing pedantix_weekly_points")
        for user_id, username, points_awarded in pedantix_weekly_points:
            print(f"User ID: {user_id}, Username: {username}, Points Awarded: {points_awarded}")

        # Update the WeeklyPoints table with the calculated weekly points for Pedantix
        for user_id, username, points_awarded in pedantix_weekly_points:
            user = User.query.get(user_id)
            weekly_points_entry = WeeklyPoints.query.filter_by(user_id=user_id).first()

            if not weekly_points_entry:
                # Create a new entry if it doesn't exist
                weekly_points_entry = WeeklyPoints(user_id=user_id, combined_points=0, last_update_date=current_time)

            # Check if the last update is within the specified interval
            if (current_time - weekly_points_entry.last_update_date) > update_interval:
                # Add the points awarded in the current round to the existing combined_points
                rank_points = 4 - int(points_awarded)  # Assign points based on rank
                rank_points = max(rank_points, 0)  # Ensure points_awarded is not negative

                # Assign points only if the user hasn't received points in this interval
                if rank_points > 0:
                    weekly_points_entry.combined_points += rank_points
                    weekly_points_entry.last_update_date = current_time

                    print(f"DEBUG: Updated WeeklyPoints for User {username} - New Combined Points: {weekly_points_entry.combined_points}")

                    db.session.add(weekly_points_entry)

        db.session.commit()

def update_weekly_points_cemantix():
    print("Updating weekly points for Cemantix...")
    with app.app_context():
        update_daily_rankings_for_score_type('Cemantix')

        # Get the current time
        current_time = datetime.utcnow()

        # Set the time interval (e.g., 1 hour) during which the weekly points won't be updated again
        update_interval = timedelta(hours=1)

        # Get the required data from the database
        cemantix_data = (
            db.session.query(
                User.id,
                User.username,
                Score.rank,  # Make sure to include the 'rank' attribute
                WeeklyPoints.combined_points.label('points_awarded')
            )
            .join(User, User.id == Score.user_id)
            .join(WeeklyPoints, and_(WeeklyPoints.user_id == Score.user_id, WeeklyPoints.user_id == User.id))
            .filter(Score.score_type == 'Cemantix')
            .distinct(User.id, WeeklyPoints.combined_points)
            .all()
        )



        print("DEBUG: Printing cemantix_data")
        for user_id, username, rank, points_awarded in cemantix_data:
            print(f"User ID: {user_id}, Username: {username}, Rank: {rank}, Points Awarded: {points_awarded}")

        # Update the WeeklyPoints table with the calculated weekly points for Cemantix
        for user_id, username, rank, points_awarded in cemantix_data:
            user = User.query.get(user_id)
            weekly_points_entry = WeeklyPoints.query.filter_by(user_id=user_id).first()

            if not weekly_points_entry:
                # Create a new entry if it doesn't exist
                weekly_points_entry = WeeklyPoints(user_id=user_id, combined_points=0, last_update_date=current_time)

            # Check if the last update is within the specified interval
            if (current_time - weekly_points_entry.last_update_date) > update_interval:
                # Add the points awarded in the current round to the existing combined_points
                rank_points = 4 - int(points_awarded)  # Assign points based on rank
                rank_points = max(rank_points, 0)  # Ensure points_awarded is not negative

                # Assign points only if the user hasn't received points in this interval
                if rank_points > 0:
                    weekly_points_entry.combined_points += rank_points
                    weekly_points_entry.last_update_date = current_time

                    print(f"DEBUG: Updated WeeklyPoints for User {username} - New Combined Points: {weekly_points_entry.combined_points}")

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
    with app.app_context():
        # Get the weekly points from the database for each user
        weekly_points_query = (
            db.session.query(User.id, User.username, WeeklyPoints.combined_points.label('points_awarded'))
            .join(User, User.id == WeeklyPoints.user_id)
            .filter(Score.score_type == score_type)  # Filter by score type
            .all()
        )

        for user_id, username, points_awarded in weekly_points_query:
             print(f"User: {username}, Points Awarded: {points_awarded}, Type: {type(points_awarded)}")
        
        current_time = datetime.utcnow()
        start_time = (current_time - timedelta(days=1)).timestamp()

        # Retrieve the top 3 scores within the last 24 hours for the specified score type
        scores_within_24_hours = (
            db.session.query(Score.user_id, func.sum(Score.score).label('total_score'))
            .filter(Score.score_type == score_type, Score.timestamp >= start_time)
            .group_by(Score.user_id)
            .order_by(func.sum(Score.score).asc())  # Order in ascending order, lowest score first
            .limit(3)
            .all()
        )
        # Manually assign points based on rank
        for rank, (user_id, _) in enumerate(scores_within_24_hours, start=1):
            user = User.query.get(user_id)
            points_awarded = 4 - rank  # 3 points for the lowest score, 2 for the second, 1 for the third
            points_awarded = max(points_awarded, 0)  # Ensure points_awarded is not negative
            print(f"Rank: {rank}, Points Awarded: {points_awarded}")
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
    schedule.every().day.at("00:01").do(reset_scores)
    schedule.every().day.at("12:05").do(reset_scores)
    schedule.every().day.at("00:01").do(update_weekly_points_pedantix)
    schedule.every().day.at("12:55").do(update_weekly_points_cemantix)

    while True:
        try:
            schedule.run_pending()
            print('Running')
        except Exception as e:
            print(f"Error in schedule execution: {e}")

        # Sleep for 1 second between iterations
        time.sleep(1)

# Start the scheduler loop in a separate thread
# Start the scheduler loop in a separate thread
schedule_thread = Thread(target=scheduler_loop)
schedule_thread.start()

# Run the Flask app using the built-in development server
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

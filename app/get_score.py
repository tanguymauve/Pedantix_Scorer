from app import app, db
from app.models import User, Score, WeeklyPoints

# Create an application context
app.app_context().push()

def print_user_data(user):
    # Retrieve the WeeklyPoints record for the user
    weekly_points = WeeklyPoints.query.filter_by(user_id=user.id).first()

    if weekly_points:
        print(f"User - {user.username} Weekly Points = {weekly_points.combined_points}")

        # Retrieve Pedantix scores for the user
        pedantix_scores = Score.query.filter_by(user_id=user.id, score_type='Pedantix').all()
        pedantix_scores_list = [score.score for score in pedantix_scores]
        print(f"User - {user.username} Pedantix Scores = {pedantix_scores_list}")

        # Retrieve Cemantix scores for the user
        cemantix_scores = Score.query.filter_by(user_id=user.id, score_type='Cemantix').all()
        cemantix_scores_list = [score.score for score in cemantix_scores]
        print(f"User - {user.username} Cemantix Scores = {cemantix_scores_list}")
    else:
        print(f"User - {user.username} Weekly Points not found.")

def print_all_user_data():
    # Retrieve all users
    users = User.query.all()

    for user in users:
        print_user_data(user)

if __name__ == "__main__":
    # Print data for all users
    print_all_user_data()

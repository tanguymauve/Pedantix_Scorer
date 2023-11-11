from app import app, db
from app.models import User, WeeklyPoints

# Create an application context
app.app_context().push()

def print_weekly_points():
    # Retrieve all users
    users = User.query.all()

    for user in users:
        # Retrieve the WeeklyPoints record for the user
        weekly_points = WeeklyPoints.query.filter_by(user_id=user.id).first()

        if weekly_points:
            print(f"User - {user.username} Weekly Points = {weekly_points.combined_points}")
        else:
            print(f"User - {user.username} Weekly Points not found.")

if __name__ == "__main__":
    print_weekly_points()
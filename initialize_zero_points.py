from app import app, db
from app.models import User, WeeklyPoints

app.app_context().push()

def initialize_weekly_points():
    users = User.query.all()

    for user in users:
        weekly_points_entry = WeeklyPoints.query.filter_by(user_id=user.id).first()

        if not weekly_points_entry:
            # Create a new entry if it doesn't exist
            weekly_points_entry = WeeklyPoints(user_id=user.id, combined_points=0)
            db.session.add(weekly_points_entry)

    db.session.commit()

if __name__ == "__main__":
    initialize_weekly_points()

from app import db
from app.models import WeeklyPoints
from app import app

def clean_weekly_points_table():
    with app.app_context():
        WeeklyPoints.query.delete()
        db.session.commit()

# Call the function when needed
clean_weekly_points_table()
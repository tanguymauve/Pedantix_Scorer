from app import app, db
from app.models import User, Score

# Create an application context
app.app_context().push()

def print_scores(username):
    user = User.query.filter_by(username=username).first()

    if user:
        pedantix_score = Score.query.filter_by(user_id=user.id, score_type='Pedantix').first()
        cemantix_score = Score.query.filter_by(user_id=user.id, score_type='Cemantix').first()

        if pedantix_score:
            print(f"User - {user.username} Pedantix Score = {pedantix_score.score}")
        else:
            print(f"No Pedantix score found for User - {user.username}")

        if cemantix_score:
            print(f"User - {user.username} Cemantix Score = {cemantix_score.score}")
        else:
            print(f"No Cemantix score found for User - {user.username}")
    else:
        print(f"User with username '{username}' not found.")

if __name__ == "__main__":
    # Set the username to 'tanguy'
    print_scores('tanguy')
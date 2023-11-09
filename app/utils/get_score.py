from app import app, db
from app.models import User, Score

# Create an application context
app.app_context().push()

def print_scores(username):
    user = User.query.filter_by(username=username).first()

    if user:
        pedantix_scores = Score.query.filter_by(user_id=user.id, score_type='Pedantix').all()
        cemantix_scores = Score.query.filter_by(user_id=user.id, score_type='Cemantix').all()

        pedantix_scores_list = [score.score for score in pedantix_scores]
        cemantix_scores_list = [score.score for score in cemantix_scores]

        print(f"User - {user.username} Pedantix Score = {pedantix_scores_list}")
        print(f"User - {user.username} Cemantix Score = {cemantix_scores_list}")
    else:
        print(f"User with username '{username}' not found.")

if __name__ == "__main__":
    # Set the username to 'tanguy'
    print_scores('tanguy')

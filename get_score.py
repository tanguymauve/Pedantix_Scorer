from app import app, db
from app.models import User, Score

app.app_context().push()
pedantix_scores = Score.query.filter_by(score_type='Pedantix').all()
cemantix_scores = Score.query.filter_by(score_type='Cémantix').all()

print("Pedantix Scores:")
for score in pedantix_scores:
    user = User.query.get(score.user_id)
    print(f"User: {user.username}, Score: {score.score}")

print("Cemantix Scores:")
for score in cemantix_scores:
    user = User.query.get(score.user_id)
    print(f"User: {user.username}, Score: {score.score}")

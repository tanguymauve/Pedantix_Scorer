from app import app, db
from app.models import User, Score

# Create an application context
app.app_context().push()

# Retrieve Pedantix scores
pedantix_scores = Score.query.filter_by(score_type='Pedantix').all()

# Retrieve Cémantix scores
cemantix_scores = Score.query.filter_by(score_type='Cémantix').all()

# Print Pedantix scores
print("Pedantix Scores:")
for score in pedantix_scores:
    user = User.query.get(score.user_id)
    print(f"User: {user.username}, Score: {score.score}")

# Print Cémantix scores
print("Cemantix Scores:")
for score in cemantix_scores:
    user = User.query.get(score.user_id)
    print(f"User: {user.username}, Score: {score.score}")
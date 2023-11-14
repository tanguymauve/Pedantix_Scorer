from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    scores = db.relationship('Score', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return self.password_hash is not None and check_password_hash(self.password_hash, password)

    def add_weekly_points(self, points):
        weekly_points_entry = WeeklyPoints.query.filter_by(user_id=self.id).first()

        if weekly_points_entry:
            weekly_points_entry.combined_points += points
            weekly_points_entry.last_update_date = datetime.utcnow()
        else:
            new_weekly_points = WeeklyPoints(user_id=self.id, combined_points=points)
            db.session.add(new_weekly_points)

        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score_type = db.Column(db.String(20), nullable=False)
    rank = db.Column(db.Integer)

    user = db.relationship('User', back_populates='scores')

    def __repr__(self):
        return f'<Score {self.score}>'

class WeeklyPoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    combined_points = db.Column(db.Integer, default=0)
    last_update_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<WeeklyPoints user_id={self.user_id} combined_points={self.combined_points}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

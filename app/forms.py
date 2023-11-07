from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Pseudo', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se rappeler de moi')
    submit = SubmitField('Se connecter')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user is None:
            raise ValidationError('Nom d\'utilisateur inconnu.')

    def validate_password(self, field):
        user = User.query.filter_by(username=self.username.data).first()
        if user is not None and not user.check_password(field.data):
            raise ValidationError('Mot de passe incorrect.')

class RegistrationForm(FlaskForm):
    username = StringField('Pseudo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    password2 = PasswordField(
        'Répéter mot de passe', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'enregistrer')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ce pseudo est déja utilisé.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Ce mail est déja utilisé.')
        
class ScoreForm(FlaskForm):
    score = IntegerField('Score', validators=[DataRequired()])
    submit = SubmitField('Ajouter le score')
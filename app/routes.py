from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm, RegistrationForm, PedantixScoreForm, CemantixScoreForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Score
from werkzeug.urls import url_parse

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')#rajouter ici le nom pour le classment tels que ("index.html", title='Home Page', posts=posts)

@app.route('/scorer/pedantix', methods=['GET', 'POST'])
@login_required
def pedantix_scorer():
    form = PedantixScoreForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            pedantix_score_value = form.score.data
            score = Score(score=pedantix_score_value, user_id=current_user.id, score_type='Pedantix')
            db.session.add(score)
            db.session.commit()
            flash('Pedantix Score submitted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting Pedantix Score: {str(e)}', 'error')

    return render_template('scorer.html', title='Scorer', pedantix_form=form, cemantix_form=CemantixScoreForm())

@app.route('/scorer/cemantix', methods=['GET', 'POST'])
@login_required
def cemantix_scorer():
    form = CemantixScoreForm()

    if form.validate_on_submit():
        flash('Cémantix Score submitted successfully!')
        cemantix_score_value = form.score.data
        score = Score(score=cemantix_score_value, user_id=current_user.id, score_type='Cémantix')
        db.session.add(score)
        db.session.commit()

    return render_template('scorer.html', title='Scorer', pedantix_form=PedantixScoreForm(), cemantix_form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Pseudo ou email invalide')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Se connecter', form=form)    

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Vous êtes maintenant enregistré')
        return redirect(url_for('login'))
    return render_template('register.html', title='Enregistrer', form=form)
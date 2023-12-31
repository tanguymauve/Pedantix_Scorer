from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm, RegistrationForm, PedantixScoreForm, CemantixScoreForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Score
from werkzeug.urls import url_parse
from app.score_calculator import calculate_sums, calculate_overall_weekly_ranking

@app.route('/')
@app.route('/index')
def index():
    # Call the calculate_sums function and get the rankings
    pedantix_ranking = calculate_sums('Pedantix')
    cemantix_ranking = calculate_sums('Cemantix')
    overall_weekly_ranking = calculate_overall_weekly_ranking()

    return render_template('index.html', title='Home', current_user=current_user, pedantix_ranking=pedantix_ranking, cemantix_ranking=cemantix_ranking, overall_weekly_ranking=overall_weekly_ranking)

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
            flash('Score Pédantix ajouté', 'success_pedantix')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur en ajoutant le score Pédantix: {str(e)}', 'error_pedantix')

    return render_template('scorer.html', title='Scorer', pedantix_form=form, cemantix_form=CemantixScoreForm())

@app.route('/scorer/cemantix', methods=['GET', 'POST'])
@login_required
def cemantix_scorer():
    form = CemantixScoreForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            cemantix_score_value = form.score.data
            score = Score(score=cemantix_score_value, user_id=current_user.id, score_type='Cemantix')
            db.session.add(score)
            db.session.commit()
            flash('Score Cémantix ajouté', 'success_cemantix')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur en ajoutant le score Cémantix: {str(e)}', 'error_cemantix')

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

@app.route('/score_rankings')
def score_rankings():
    # Call the calculate_sums function and get the rankings
    pedantix_ranking = calculate_sums('Pedantix')
    cemantix_ranking = calculate_sums('Cemantix')

    return render_template('index.html', current_user=current_user, pedantix_ranking=pedantix_ranking, cemantix_ranking=cemantix_ranking)

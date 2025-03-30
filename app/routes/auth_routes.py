# app/routes/auth_routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm
from app.routes import auth

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Zalogowano pomyślnie!')
            return redirect(url_for('main.home'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.')
    return render_template('login.html', title='Logowanie', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Gratulacje, rejestracja zakończona powodzeniem!')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Rejestracja', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
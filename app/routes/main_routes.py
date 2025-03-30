from flask import render_template, redirect, url_for
from flask_login import current_user
from app.routes import main

@main.route('/')
def index():
    return redirect(url_for('main.home'))

@main.route('/home')
def home():
    return render_template('home.html', title='Strona główna')
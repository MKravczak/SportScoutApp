from flask import render_template, redirect, url_for, current_app, send_from_directory
from flask_login import current_user
from app.routes import main
import os

@main.route('/')
def index():
    return redirect(url_for('main.home'))

@main.route('/home')
def home():
    return render_template('home.html', title='Strona główna')

@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
# app/routes/club_routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required, login_user, logout_user
from app import db
from app.models import User, Player, Club, Sport
from app.forms import ClubLoginForm, ClubRegistrationForm, ClubForm
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes import clubs
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

# Decorator funkcji sprawdzający, czy użytkownik jest zarządcą klubu
def club_manager_required(func):
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'club_manager':
            abort(403)  # Forbidden
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view


@clubs.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.role == 'club_manager':
        return redirect(url_for('clubs.dashboard'))
    
    form = ClubLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data, role='club_manager').first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Zalogowano pomyślnie jako zarząd klubu!', 'success')
            return redirect(url_for('clubs.dashboard'))
        else:
            flash('Nieprawidłowa nazwa klubu lub hasło.', 'danger')
    
    return render_template('clubs/login.html', title='Logowanie Klubu', form=form)


@clubs.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = ClubRegistrationForm()
    if form.validate_on_submit():
        # Sprawdzenie czy email już istnieje
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Ten adres email jest już używany. Proszę użyć innego.', 'danger')
            return render_template('clubs/register.html', title='Rejestracja Klubu', form=form)
            
        # Sprawdzenie czy nazwa klubu nie jest już używana jako nazwa użytkownika
        existing_username = User.query.filter_by(username=form.name.data).first()
        if existing_username:
            flash('Ta nazwa klubu jest już używana jako nazwa użytkownika. Proszę użyć innej nazwy.', 'danger')
            return render_template('clubs/register.html', title='Rejestracja Klubu', form=form)
        
        # Najpierw utworzenie klubu
        club = Club(
            name=form.name.data,
            description=form.description.data,
            city=form.city.data
        )
        
        # Obsługa logo jeśli zostało przesłane
        if form.logo.data:
            filename = secure_filename(form.logo.data.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'club_logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            form.logo.data.save(filepath)
            club.logo = filename
        
        # Zapisz klub w bazie, aby uzyskać jego ID
        db.session.add(club)
        db.session.commit()
        
        # Następnie utworzenie użytkownika z rolą club_manager
        user = User(
            username=form.name.data,
            email=form.email.data,
            role='club_manager',
            club_id=club.id  # Teraz club.id jest dostępne
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Rejestracja klubu zakończona pomyślnie! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('clubs.login'))
    
    return render_template('clubs/register.html', title='Rejestracja Klubu', form=form)


@clubs.route('/dashboard')
@login_required
@club_manager_required
def dashboard():
    club = Club.query.get(current_user.club_id)
    if not club:
        flash('Nie znaleziono klubu dla tego konta.', 'danger')
        return redirect(url_for('main.home'))
    
    # Pobierz scoutów przypisanych do klubu
    scouts = User.query.filter_by(club_id=club.id, role='scout').all()
    
    # Pobierz zawodników dodanych przez scoutów klubu
    scouts_ids = [scout.id for scout in scouts]
    players = Player.query.filter(Player.scout_id.in_(scouts_ids), Player.is_amateur == False).all()
    
    # Pobierz zawodników amatorskich
    amateur_players = Player.query.filter_by(is_amateur=True).all()
    
    return render_template(
        'clubs/dashboard.html', 
        title='Panel Zarządzania Klubem',
        club=club,
        scouts=scouts,
        players=players,
        amateur_players=amateur_players
    )


@clubs.route('/players')
@login_required
@club_manager_required
def players_list():
    club = Club.query.get(current_user.club_id)
    if not club:
        flash('Nie znaleziono klubu dla tego konta.', 'danger')
        return redirect(url_for('main.home'))
    
    # Pobierz ID scoutów przypisanych do klubu
    scouts = User.query.filter_by(club_id=club.id, role='scout').all()
    scouts_ids = [scout.id for scout in scouts]
    
    # Pobierz zawodników dodanych przez scoutów klubu
    query = Player.query.filter(Player.scout_id.in_(scouts_ids), Player.is_amateur == False)
    
    # Filtrowanie po sporcie, jeśli określono
    sport_id = request.args.get('sport', type=int)
    if sport_id:
        query = query.filter_by(sport_id=sport_id)
    
    # Filtrowanie po wyszukiwanym tekście
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (Player.first_name.ilike(f'%{search}%')) | 
            (Player.last_name.ilike(f'%{search}%'))
        )
    
    players = query.all()
    
    # Dodajemy datetime.now() dla obliczeń wieku w szablonie
    now = datetime.now().date()
    
    return render_template(
        'clubs/players.html',
        title='Zawodnicy Klubu',
        players=players,
        club=club,
        scouts=scouts,
        sport_id=sport_id,
        search=search,
        now=now
    )


@clubs.route('/amateurs')
@login_required
@club_manager_required
def amateur_players():
    # Filtrowanie po sporcie, jeśli określono
    sport_id = request.args.get('sport', type=int)
    search = request.args.get('search', '')
    
    # Pobierz wszystkie dyscypliny do filtrowania
    sports = Sport.query.order_by(Sport.name).all()
    
    # Baza zapytań - tylko zawodnicy amatorzy
    query = Player.query.filter_by(is_amateur=True)
    
    # Filtrowanie po sporcie, jeśli określono
    if sport_id:
        query = query.filter_by(sport_id=sport_id)
    
    # Filtrowanie po wyszukiwanym tekście
    if search:
        query = query.filter(
            (Player.first_name.ilike(f'%{search}%')) | 
            (Player.last_name.ilike(f'%{search}%'))
        )
    
    players = query.all()
    
    # Dodajemy datetime.now() dla obliczeń wieku w szablonie
    now = datetime.now().date()
    
    return render_template(
        'clubs/amateurs.html',
        title='Zawodnicy Amatorzy',
        players=players,
        sports=sports,
        sport_id=sport_id,
        search=search,
        now=now
    )


@clubs.route('/scouts')
@login_required
@club_manager_required
def scouts_list():
    club = Club.query.get(current_user.club_id)
    if not club:
        flash('Nie znaleziono klubu dla tego konta.', 'danger')
        return redirect(url_for('main.home'))
    
    scouts = User.query.filter_by(club_id=club.id, role='scout').all()
    
    return render_template(
        'clubs/scouts.html',
        title='Scouci Klubu',
        scouts=scouts,
        club=club
    )


@clubs.route('/profile', methods=['GET', 'POST'])
@login_required
@club_manager_required
def profile():
    club = Club.query.get(current_user.club_id)
    if not club:
        flash('Nie znaleziono klubu dla tego konta.', 'danger')
        return redirect(url_for('main.home'))
    
    form = ClubForm(obj=club)
    form._obj_id = club.id
    
    if form.validate_on_submit():
        club.name = form.name.data
        club.city = form.city.data
        club.description = form.description.data
        
        # Obsługa logo jeśli zostało zmienione
        if form.logo.data:
            filename = secure_filename(form.logo.data.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'club_logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            form.logo.data.save(filepath)
            club.logo = filename
        
        db.session.commit()
        flash('Profil klubu został zaktualizowany pomyślnie.', 'success')
        return redirect(url_for('clubs.profile'))
    
    return render_template(
        'clubs/profile.html',
        title='Profil Klubu',
        form=form,
        club=club
    ) 
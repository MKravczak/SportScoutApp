from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, Player, Sport, PhysicalTest, Match, MatchStat, Club
from app.forms import SportForm, UserRoleForm, AssignScoutForm
from sqlalchemy import func
from datetime import datetime, date
from app.routes import admin

# Decorator funkcji sprawdzający, czy użytkownik jest adminem
def admin_required(func):
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Forbidden
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Pobieranie podstawowych statystyk
    user_count = User.query.count()
    player_count = Player.query.count()
    test_count = PhysicalTest.query.count()
    match_count = Match.query.count()
    club_count = Club.query.count()
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count,
                          player_count=player_count,
                          test_count=test_count,
                          match_count=match_count,
                          club_count=club_count)

@admin.route('/users')
@login_required
@admin_required
def users():
    users_list = User.query.all()
    return render_template('admin/users.html', users=users_list)

@admin.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserRoleForm(obj=user)
    
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.commit()
        flash(f'Rola użytkownika {user.username} została zaktualizowana.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin.route('/users/assign-club/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_club(user_id):
    user = User.query.get_or_404(user_id)
    
    # Tylko scouci mogą być przypisani do klubów
    if user.role != 'scout':
        flash('Tylko scouci mogą być przypisani do klubów.', 'danger')
        return redirect(url_for('admin.users'))
    
    form = AssignScoutForm(obj=user)
    form.club.choices = [(0, 'Brak klubu')] + [(c.id, c.name) for c in Club.query.order_by(Club.name).all()]
    
    if request.method == 'GET':
        if user.club_id:
            form.club.data = user.club_id
        else:
            form.club.data = 0
    
    if form.validate_on_submit():
        if form.club.data == 0:
            user.club_id = None
            flash(f'Scout {user.username} został odłączony od klubu.', 'success')
        else:
            club = Club.query.get(form.club.data)
            if club:
                user.club_id = club.id
                flash(f'Scout {user.username} został przypisany do klubu {club.name}.', 'success')
            else:
                flash('Wybrany klub nie istnieje.', 'danger')
                return redirect(url_for('admin.assign_club', user_id=user.id))
        
        db.session.commit()
        return redirect(url_for('admin.users'))
    
    return render_template('admin/assign_club.html', form=form, user=user)

@admin.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Zapobieganie usunięciu własnego konta admina
    if user.id == current_user.id:
        flash('Nie możesz usunąć własnego konta administratora.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Sprawdzenie, czy użytkownik dodał zawodników
    player_count = Player.query.filter_by(scout_id=user.id).count()
    if player_count > 0:
        flash(f'Nie można usunąć użytkownika {user.username}, ponieważ dodał {player_count} zawodników.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Użytkownik {user.username} został usunięty.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/clubs')
@login_required
@admin_required
def clubs():
    clubs_list = Club.query.all()
    clubs_with_stats = []
    
    for club in clubs_list:
        scouts_count = User.query.filter_by(club_id=club.id, role='scout').count()
        scout_ids = [s.id for s in User.query.filter_by(club_id=club.id, role='scout').all()]
        players_count = Player.query.filter(Player.scout_id.in_(scout_ids)).count() if scout_ids else 0
        
        clubs_with_stats.append({
            'club': club,
            'scouts_count': scouts_count,
            'players_count': players_count
        })
    
    return render_template('admin/clubs.html', clubs=clubs_with_stats)

@admin.route('/sports')
@login_required
@admin_required
def sports():
    # Pobieranie dyscyplin z liczbą zawodników
    sports_list = db.session.query(
        Sport, 
        func.count(Player.id).label('player_count')
    ).outerjoin(Player, Sport.id == Player.sport_id)\
    .group_by(Sport.id)\
    .all()
    
    return render_template('admin/sports.html', sports=sports_list)

@admin.route('/sports/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_sport():
    form = SportForm()
    
    if form.validate_on_submit():
        sport = Sport(name=form.name.data, description=form.description.data)
        db.session.add(sport)
        db.session.commit()
        flash('Nowa dyscyplina została dodana pomyślnie.', 'success')
        return redirect(url_for('admin.sports'))
    
    return render_template('admin/add_sport.html', form=form)

@admin.route('/sports/edit/<int:sport_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_sport(sport_id):
    sport = Sport.query.get_or_404(sport_id)
    form = SportForm(obj=sport)
    
    if form.validate_on_submit():
        sport.name = form.name.data
        sport.description = form.description.data
        db.session.commit()
        flash('Dyscyplina została zaktualizowana pomyślnie.', 'success')
        return redirect(url_for('admin.sports'))
    
    return render_template('admin/edit_sport.html', form=form, sport=sport)

@admin.route('/sports/delete/<int:sport_id>', methods=['POST'])
@login_required
@admin_required
def delete_sport(sport_id):
    sport = Sport.query.get_or_404(sport_id)
    
    # Sprawdzenie, czy istnieją powiązani zawodnicy
    player_count = Player.query.filter_by(sport_id=sport.id).count()
    if player_count > 0:
        flash(f'Nie można usunąć dyscypliny {sport.name}, ponieważ jest przypisana do {player_count} zawodników.', 'danger')
        return redirect(url_for('admin.sports'))
    
    db.session.delete(sport)
    db.session.commit()
    flash(f'Dyscyplina {sport.name} została usunięta.', 'success')
    return redirect(url_for('admin.sports'))

@admin.route('/statistics')
@login_required
@admin_required
def statistics():
    # Statystyki zawodników według dyscyplin
    sports_stats = db.session.query(
        Sport.name,
        func.count(Player.id).label('player_count')
    ).outerjoin(Player, Sport.id == Player.sport_id)\
    .group_by(Sport.name)\
    .all()
    
    # Statystyki użytkowników według ról
    role_stats = db.session.query(
        User.role,
        func.count(User.id).label('user_count')
    ).group_by(User.role)\
    .all()
    
    # Statystyki testów i meczów
    test_count = PhysicalTest.query.count()
    match_count = Match.query.count()
    
    return render_template('admin/statistics.html', 
                          sports_stats=sports_stats,
                          role_stats=role_stats,
                          test_count=test_count,
                          match_count=match_count)

@admin.route('/amateur-players')
@login_required
@admin_required
def amateur_players():
    """Wyświetla listę wszystkich zawodników amatorskich z możliwością filtrowania."""
    sport_id = request.args.get('sport', type=int)
    search = request.args.get('search', '')
    
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
    
    # Pobieranie danych do formularza filtrowania
    sports = Sport.query.all()
    
    # Aktualna data do obliczania wieku
    now = date.today()
    
    # Wykonanie zapytania
    players = query.order_by(Player.last_name).all()
    
    return render_template(
        'admin/amateur_players.html', 
        players=players, 
        sports=sports,
        sport_id=sport_id,
        search=search,
        now=now
    )

@admin.route('/amateur-players/promote/<int:player_id>', methods=['POST'])
@login_required
@admin_required
def promote_amateur(player_id):
    """Awansuje zawodnika amatorskiego do statusu profesjonalnego."""
    player = Player.query.get_or_404(player_id)
    
    # Sprawdzenie, czy zawodnik faktycznie jest amatorem
    if not player.is_amateur:
        flash('Ten zawodnik jest już profesjonalistą.', 'warning')
        return redirect(url_for('admin.amateur_players'))
    
    # Awansowanie zawodnika - przypisanie go do administratora
    player.is_amateur = False
    player.scout_id = current_user.id
    
    db.session.commit()
    flash(f'Zawodnik {player.first_name} {player.last_name} został awansowany do statusu profesjonalnego.', 'success')
    return redirect(url_for('admin.amateur_players'))
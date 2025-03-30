from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, Player, Sport, PhysicalTest, Match, MatchStat
from app.forms import SportForm, UserRoleForm
from sqlalchemy import func

admin = Blueprint('admin', __name__)

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
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count,
                          player_count=player_count,
                          test_count=test_count,
                          match_count=match_count)

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
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import Player, Sport, PhysicalTest, Match, MatchStat, User, Club
from app.forms import PlayerForm
from app.routes import players
from datetime import datetime
from app.utils.file_upload import save_player_photo, delete_file
from sqlalchemy import or_
#from app.routes improt PhysicalTestForm, MatchStatForm

@players.route('/list')
@login_required
def list():
    sport_id = request.args.get('sport', type=int)
    amateur = request.args.get('amateur', '0') == '1'
    sports = Sport.query.all()

    if current_user.role == 'admin':
        # Admin widzi wszystkich zawodników
        query = Player.query
    elif current_user.role == 'club_manager':
        # Zarząd klubu widzi zawodników dodanych przez scoutów z tego klubu
        if current_user.club_id:
            # Pobierz ID scoutów przypisanych do tego klubu
            scout_ids = [scout.id for scout in User.query.filter_by(club_id=current_user.club_id, role='scout').all()]
            query = Player.query.filter(
                or_(
                    Player.scout_id.in_(scout_ids),  # Zawodnicy dodani przez scoutów klubu
                    Player.is_amateur == True         # Wszyscy amatorzy
                )
            )
        else:
            flash('Nie jesteś przypisany do żadnego klubu.', 'warning')
            query = Player.query.filter_by(is_amateur=True)  # Tylko amatorzy, jeśli nie ma klubu
    elif current_user.role == 'scout':
        # Scout widzi tylko swoich zawodników
        query = Player.query.filter_by(scout_id=current_user.id)
    else:
        # Zwykły użytkownik widzi tylko swoich zawodników amatorskich
        query = Player.query.filter_by(scout_id=current_user.id)

    # Filtrowanie po typie zawodnika (amator/profesjonalista)
    if current_user.role != 'club_manager':  # Dla zarządu klubu już filtrowaliśmy powyżej
        query = query.filter_by(is_amateur=amateur)

    if sport_id:
        query = query.filter_by(sport_id=sport_id)

    players_list = query.all()
    return render_template('player/list.html', players=players_list, sports=sports, amateur=amateur)


@players.route('/amateur/list')
@login_required
def amateur_list():
    # Przekierowanie na standardową listę z parametrem amateur=1
    return redirect(url_for('players.list', amateur=1))


@players.route('/professional/list')
@login_required
def professional_list():
    # Przekierowanie na standardową listę z parametrem amateur=0
    return redirect(url_for('players.list', amateur=0))


@players.route('/detail/<int:player_id>')
@login_required
def detail(player_id):
    player = Player.query.get_or_404(player_id)

    # Sprawdzenie czy użytkownik ma uprawnienia do przeglądania tego zawodnika
    if current_user.role == 'admin':
        # Admin widzi wszystko
        pass
    elif current_user.role == 'club_manager':
        # Zarząd klubu widzi zawodników dodanych przez scoutów swojego klubu lub amatorów
        if not player.is_amateur:  # Profesjonaliści
            scout_ids = [scout.id for scout in User.query.filter_by(club_id=current_user.club_id, role='scout').all()]
            if player.scout_id not in scout_ids:
                abort(403)
    elif current_user.role == 'scout':
        # Scout widzi tylko swoich zawodników
        if player.scout_id != current_user.id:
            abort(403)
    else:
        # Zwykły użytkownik widzi tylko swoich amatorów
        if player.scout_id != current_user.id:
            abort(403)

    return render_template('player/detail.html', player=player)


@players.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # Zarząd klubu nie może dodawać zawodników
    if current_user.role == 'club_manager':
        flash('Zarząd klubu nie może dodawać zawodników.', 'danger')
        return redirect(url_for('players.list'))
    
    # Dla zwykłych użytkowników domyślnie dodajemy amatora
    is_amateur = True if current_user.role == 'user' else False
    
    # Admini i scouti mogą wybrać, czy dodają amatora czy profesjonalistę
    amateur_param = request.args.get('amateur', '0')
    if current_user.role in ['admin', 'scout'] and amateur_param == '1':
        is_amateur = True
    
    # Tylko admin i scout mogą dodawać profesjonalistów
    if not is_amateur and current_user.role not in ['scout', 'admin']:
        abort(403)
    
    # Zwykły użytkownik może dodać tylko jednego amatora
    if current_user.role == 'user' and is_amateur:
        existing_amateur = Player.query.filter_by(scout_id=current_user.id, is_amateur=True).first()
        if existing_amateur:
            flash('Możesz dodać tylko jednego zawodnika amatorskiego.', 'warning')
            return redirect(url_for('players.detail', player_id=existing_amateur.id))

    form = PlayerForm()
    form.sport.choices = [(s.id, s.name) for s in Sport.query.all()]

    if form.validate_on_submit():
        player = Player(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            birth_date=form.birth_date.data,
            sport_id=form.sport.data,
            position=form.position.data,
            height=form.height.data,
            weight=form.weight.data,
            scout_id=current_user.id,
            is_amateur=is_amateur
        )
        db.session.add(player)
        db.session.commit()
        
        # Obsługa dodawania zdjęcia
        if form.photo.data:
            photo_path = save_player_photo(form.photo.data, player.id)
            if photo_path:
                player.photo = photo_path
                db.session.commit()
        
        flash('Zawodnik został dodany pomyślnie.', 'success')
        return redirect(url_for('players.detail', player_id=player.id))

    return render_template('player/add.html', form=form, is_amateur=is_amateur)


@players.route('/edit/<int:player_id>', methods=['GET', 'POST'])
@login_required
def edit(player_id):
    player = Player.query.get_or_404(player_id)

    # Sprawdzenie uprawnień do edycji
    if current_user.role != 'admin':
        if player.is_amateur and player.scout_id != current_user.id:
            abort(403)
        elif not player.is_amateur and current_user.role != 'scout':
            abort(403)
        elif not player.is_amateur and current_user.role == 'scout' and player.scout_id != current_user.id:
            abort(403)

    form = PlayerForm(obj=player)
    form.sport.choices = [(s.id, s.name) for s in Sport.query.all()]

    if form.validate_on_submit():
        player.first_name = form.first_name.data
        player.last_name = form.last_name.data
        player.birth_date = form.birth_date.data
        player.sport_id = form.sport.data
        player.position = form.position.data
        player.height = form.height.data
        player.weight = form.weight.data
        
        # Obsługa dodawania zdjęcia
        if form.photo.data:
            # Usunięcie starego zdjęcia
            if player.photo:
                delete_file(player.photo)
            
            # Zapisanie nowego zdjęcia
            photo_path = save_player_photo(form.photo.data, player.id)
            if photo_path:
                player.photo = photo_path

        db.session.commit()
        flash('Dane zawodnika zostały zaktualizowane.', 'success')
        return redirect(url_for('players.detail', player_id=player.id))

    return render_template('player/edit.html', form=form, player=player)


# @players.route('/add_test/<int:player_id>', methods=['GET', 'POST'])
# # @login_required
# # def add_test(player_id):
# #     player = Player.query.get_or_404(player_id)
# #
# #     # Check if user has permission
# #     if current_user.role != 'admin' and player.scout_id != current_user.id:
# #         abort(403)
# #
# #     form = PhysicalTestForm()
# #
# #     if form.validate_on_submit():
# #         test = PhysicalTest(
# #             player_id=player.id,
# #             test_date=form.test_date.data,
# #             sprint_100m=form.sprint_100m.data,
# #             long_jump=form.long_jump.data,
# #             agility=form.agility.data,
# #             endurance=form.endurance.data,
# #             strength=form.strength.data,
# #             notes=form.notes.data
# #         )
# #         db.session.add(test)
# #         db.session.commit()
# #         flash('Test sprawnościowy został dodany.', 'success')
# #         return redirect
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import Player, Sport, PhysicalTest, Match, MatchStat
from app.forms import PlayerForm
from app.routes import players
from datetime import datetime
#from app.routes improt PhysicalTestForm, MatchStatForm

@players.route('/list')
@login_required
def list():
    sport_id = request.args.get('sport', type=int)
    sports = Sport.query.all()

    if current_user.role == 'admin' or current_user.role == 'club_manager':
        query = Player.query
    else:  # scout
        query = Player.query.filter_by(scout_id=current_user.id)

    if sport_id:
        query = query.filter_by(sport_id=sport_id)

    players_list = query.all()
    return render_template('player/list.html', players=players_list, sports=sports)


@players.route('/detail/<int:player_id>')
@login_required
def detail(player_id):
    player = Player.query.get_or_404(player_id)

    # Check if user has permission to view this player
    if current_user.role != 'admin' and current_user.role != 'club_manager' and player.scout_id != current_user.id:
        abort(403)

    return render_template('player/detail.html', player=player)


@players.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['scout', 'admin']:
        abort(403)

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
            scout_id=current_user.id
        )
        db.session.add(player)
        db.session.commit()
        flash('Zawodnik został dodany pomyślnie.', 'success')
        return redirect(url_for('players.detail', player_id=player.id))

    return render_template('player/add.html', form=form)


@players.route('/edit/<int:player_id>', methods=['GET', 'POST'])
@login_required
def edit(player_id):
    player = Player.query.get_or_404(player_id)

    # Check if user has permission to edit this player
    if current_user.role != 'admin' and player.scout_id != current_user.id:
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
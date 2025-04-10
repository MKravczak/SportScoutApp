from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Player, Sport, SportTest, PlayerTest, User
from app.forms import SportTestForm, PlayerTestForm
from datetime import datetime
from sqlalchemy import or_, desc, func
from app.routes import tests
import numpy as np

@tests.route('/list')
@login_required
def list():
    """Lista dostępnych testów według dyscyplin sportowych"""
    sport_id = request.args.get('sport', type=int)
    sports = Sport.query.all()
    
    query = SportTest.query
    if sport_id:
        query = query.filter_by(sport_id=sport_id)
    
    tests_list = query.all()
    return render_template('tests/list.html', tests=tests_list, sports=sports, current_sport_id=sport_id)

@tests.route('/add', methods=['GET', 'POST'])
@login_required
def add_test():
    """Dodawanie nowego testu"""
    # Tylko admin i scout mogą dodawać testy
    if current_user.role not in ['admin', 'scout']:
        flash('Nie masz uprawnień do dodawania testów.', 'danger')
        return redirect(url_for('tests.list'))
    
    form = SportTestForm()
    form.sport.choices = [(s.id, s.name) for s in Sport.query.all()]
    
    if form.validate_on_submit():
        try:
            # Konwersja wartości 'true'/'false' na boolean
            is_lower_better = form.is_lower_better.data == 'true'
            
            test = SportTest(
                name=form.name.data,
                description=form.description.data,
                type=form.type.data,
                unit=form.unit.data,
                is_lower_better=is_lower_better,
                sport_id=form.sport.data
            )
            db.session.add(test)
            db.session.commit()
            flash('Test został dodany pomyślnie!', 'success')
            return redirect(url_for('tests.list'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Błąd podczas dodawania testu: {str(e)}")
            flash(f'Wystąpił błąd: {str(e)}', 'danger')
    
    # Wyświetlanie błędów walidacji formularza
    if form.errors:
        app.logger.error(f"Błędy walidacji formularza: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Błąd w polu {getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('tests/add_test.html', form=form)

@tests.route('/edit/<int:test_id>', methods=['GET', 'POST'])
@login_required
def edit(test_id):
    """Edytowanie istniejącego testu"""
    # Tylko admin i scout mogą edytować testy
    if current_user.role not in ['admin', 'scout']:
        flash('Nie masz uprawnień do edytowania testów.', 'danger')
        return redirect(url_for('tests.list'))
    
    test = SportTest.query.get_or_404(test_id)
    form = SportTestForm(obj=test)
    form.sport.choices = [(s.id, s.name) for s in Sport.query.all()]
    form._obj_id = test.id  # Przekazanie ID obiektu na potrzeby walidacji
    
    # Ustawienie wartości pola is_lower_better na 'true' lub 'false' (stringi)
    if request.method == 'GET':
        form.is_lower_better.data = 'true' if test.is_lower_better else 'false'
    
    if form.validate_on_submit():
        try:
            # Konwersja wartości 'true'/'false' na boolean
            is_lower_better = form.is_lower_better.data == 'true'
            
            test.name = form.name.data
            test.description = form.description.data
            test.type = form.type.data
            test.unit = form.unit.data
            test.is_lower_better = is_lower_better
            test.sport_id = form.sport.data
            
            db.session.commit()
            flash('Test został zaktualizowany.', 'success')
            return redirect(url_for('tests.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Wystąpił błąd: {str(e)}', 'danger')
            print(f"Błąd edycji testu: {str(e)}")
    
    # Wyświetlanie błędów walidacji formularza
    if form.errors:
        print(f"Błędy formularza: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Błąd pola {field}: {error}', 'danger')
    
    return render_template('tests/edit_test.html', form=form, test=test)

@tests.route('/player_test/<int:player_id>')
@login_required
def player_tests(player_id):
    """Lista testów wykonanych przez zawodnika"""
    player = Player.query.get_or_404(player_id)
    
    # Sprawdzenie czy użytkownik ma uprawnienia do przeglądania testów tego zawodnika
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
    
    # Pobranie testów zawodnika z posortowaniem od najnowszego
    player_tests = PlayerTest.query.filter_by(player_id=player.id).order_by(PlayerTest.test_date.desc()).all()
    
    return render_template('tests/player_tests.html', player=player, player_tests=player_tests)

@tests.route('/add_player_test/<int:player_id>', methods=['GET', 'POST'])
@login_required
def add_player_test(player_id):
    """Dodawanie wyniku testu dla zawodnika"""
    player = Player.query.get_or_404(player_id)
    
    # Sprawdzenie uprawnień
    if current_user.role not in ['admin', 'scout']:
        if player.scout_id != current_user.id:
            abort(403)
    
    # Pobranie testów dostępnych dla dyscypliny tego zawodnika
    available_tests = SportTest.query.filter_by(sport_id=player.sport_id).all()
    if not available_tests:
        flash('Brak zdefiniowanych testów dla tej dyscypliny sportowej.', 'warning')
        return redirect(url_for('tests.player_tests', player_id=player_id))
    
    form = PlayerTestForm()
    # Zawodnik jest już określony z URL
    form.player.choices = [(player.id, f"{player.first_name} {player.last_name}")]
    form.player.data = player.id
    form.test.choices = [(t.id, t.name) for t in available_tests]
    
    if form.validate_on_submit():
        try:
            player_test = PlayerTest(
                player_id=player.id,
                test_id=form.test.data,
                result=form.result.data,
                test_date=form.test_date.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            db.session.add(player_test)
            db.session.commit()
            
            flash('Wynik testu został zapisany pomyślnie.', 'success')
            return redirect(url_for('tests.player_tests', player_id=player_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas zapisywania testu: {str(e)}', 'danger')
            print(f"Błąd zapisu testu: {str(e)}")
    else:
        # Wypisanie błędów walidacji formularza
        if form.errors:
            print(f"Błędy formularza: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Błąd pola {field}: {error}', 'danger')
    
    # Dodanie aktualnej daty i czasu do kontekstu szablonu
    now = datetime.now()
    
    # Przekazanie testów do szablonu jako sport_tests
    return render_template('tests/add_player_test.html', form=form, player=player, sport_tests=available_tests, now=now)

@tests.route('/delete_player_test/<int:test_id>', methods=['POST'])
@login_required
def delete_player_test(test_id):
    """Usuwanie wyniku testu"""
    player_test = PlayerTest.query.get_or_404(test_id)
    player_id = player_test.player_id
    player = Player.query.get_or_404(player_id)
    
    # Sprawdzenie uprawnień
    if current_user.role != 'admin':
        if current_user.id != player_test.created_by and player.scout_id != current_user.id:
            abort(403)
    
    db.session.delete(player_test)
    db.session.commit()
    
    flash('Wynik testu został usunięty.', 'success')
    return redirect(url_for('tests.player_tests', player_id=player_id))

@tests.route('/analysis/<int:player_id>')
@login_required
def player_analysis(player_id):
    """Analiza wyników testów zawodnika"""
    player = Player.query.get_or_404(player_id)
    
    # Sprawdzenie uprawnień
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
    
    # Pobranie wszystkich testów zawodnika
    player_tests = PlayerTest.query.filter_by(player_id=player_id).order_by(PlayerTest.test_date).all()
    
    # Przygotowanie danych dla wykresów
    chart_data = {}
    for pt in player_tests:
        test_name = pt.sport_test.name
        if test_name not in chart_data:
            chart_data[test_name] = {
                'dates': [],
                'results': [],
                'is_lower_better': pt.sport_test.is_lower_better,
                'unit': pt.sport_test.unit
            }
        
        chart_data[test_name]['dates'].append(pt.test_date.strftime('%Y-%m-%d'))
        chart_data[test_name]['results'].append(pt.result)
    
    return render_template('tests/player_analysis.html', 
                           player=player, 
                           chart_data=chart_data)

@tests.route('/compare')
@login_required
def compare_players():
    """Porównanie wyników dwóch lub więcej zawodników"""
    # Pobranie parametrów z URL
    player_ids = request.args.getlist('player_id', type=int)
    test_id = request.args.get('test_id', type=int)
    
    # Jeśli nie wybrano zawodników, wyświetl formularz wyboru
    if not player_ids:
        players = []
        if current_user.role == 'admin':
            players = Player.query.all()
        elif current_user.role == 'club_manager':
            if current_user.club_id:
                scout_ids = [scout.id for scout in User.query.filter_by(club_id=current_user.club_id, role='scout').all()]
                players = Player.query.filter(Player.scout_id.in_(scout_ids)).all()
        elif current_user.role == 'scout':
            players = Player.query.filter_by(scout_id=current_user.id).all()
        else:
            players = Player.query.filter_by(scout_id=current_user.id, is_amateur=True).all()
        
        tests = SportTest.query.all()
        return render_template('tests/compare_select.html', players=players, tests=tests)
    
    # Pobranie zawodników
    players = Player.query.filter(Player.id.in_(player_ids)).all()
    
    # Pobranie testu
    selected_test = SportTest.query.get_or_404(test_id) if test_id else None
    
    # Przygotowanie danych do porównania
    comparison_data = {}
    overall_stats = {}

    if selected_test:
        # Porównanie jednego konkretnego testu
        all_results = []
        for player in players:
            player_tests = PlayerTest.query.filter_by(
                player_id=player.id,
                test_id=selected_test.id
            ).order_by(PlayerTest.test_date).all()

            if player_tests:
                player_results = [pt.result for pt in player_tests]
                comparison_data[player.id] = {
                    'player_name': f"{player.first_name} {player.last_name}",
                    'dates': [pt.test_date.strftime('%Y-%m-%d') for pt in player_tests],
                    'results': player_results
                }
                all_results.extend(player_results)

        if all_results:
            results_array = np.array(all_results)
            overall_stats['min'] = np.min(results_array)
            overall_stats['max'] = np.max(results_array)
            overall_stats['avg'] = np.mean(results_array)
            overall_stats['q1'] = np.percentile(results_array, 25)
            overall_stats['q3'] = np.percentile(results_array, 75)
            overall_stats['record'] = overall_stats['min'] if selected_test.is_lower_better else overall_stats['max']
            overall_stats['lowest'] = overall_stats['max'] if selected_test.is_lower_better else overall_stats['min']

        return render_template('tests/compare_results.html',
                              players=players,
                              test=selected_test,
                              comparison_data=comparison_data,
                              overall_stats=overall_stats)
    else:
        # Porównanie najnowszych wyników wszystkich testów
        tests = SportTest.query.all()
        test_stats = {} # Słownik na statystyki min/max dla każdego testu

        for test in tests:
            comparison_data[test.id] = {
                'test_name': test.name,
                'unit': test.unit,
                'is_lower_better': test.is_lower_better,
                'players': {}
            }
            test_results_for_stats = [] # Lista wyników dla danego testu do obliczeń min/max

            for player in players:
                # Pobierz najnowszy wynik testu dla zawodnika
                latest_test = PlayerTest.query.filter_by(
                    player_id=player.id,
                    test_id=test.id
                ).order_by(PlayerTest.test_date.desc()).first()

                if latest_test:
                    comparison_data[test.id]['players'][player.id] = {
                        'player_name': f"{player.first_name} {player.last_name}",
                        'result': latest_test.result,
                        'date': latest_test.test_date.strftime('%Y-%m-%d')
                    }
                    test_results_for_stats.append(latest_test.result) # Dodaj wynik do listy statystyk

            # Oblicz min/max dla testu, jeśli są jakieś wyniki
            if test_results_for_stats:
                results_array = np.array(test_results_for_stats)
                test_stats[test.id] = {
                    'min': np.min(results_array),
                    'max': np.max(results_array)
                }

        # Usuń testy, dla których żaden z wybranych graczy nie ma wyników
        comparison_data = {tid: tdata for tid, tdata in comparison_data.items() if tdata['players']}

        # Przygotuj listę słowników z danymi graczy do JSON
        players_list_json = [
            {
                'id': p.id,
                'first_name': p.first_name,
                'last_name': p.last_name
            }
            for p in players
        ]

        return render_template('tests/compare_all_tests.html',
                              players=players, # Nadal przekazujemy pełne obiekty dla innych części szablonu
                              comparison_data=comparison_data,
                              test_stats=test_stats,
                              players_list_json=players_list_json) # Przekaż listę słowników dla JS 
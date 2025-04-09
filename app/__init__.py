from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import random
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes import main, auth, players, admin, clubs
    from app.routes.api_routes import api
    
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(players, url_prefix='/players')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(clubs, url_prefix='/clubs')

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return "404 - Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "500 - Internal Server Error", 500

    with app.app_context():
        # Usuń db.drop_all() - z tą linią usuwa się bazę za każdym razem gdy aplikacja startuje
        # db.drop_all()
        db.create_all()

        from app.models import User, Sport, Player, PhysicalTest, Match, MatchStat, Club  # Import modeli

        # Tworzenie przykładowych danych tylko jeśli nie ma żadnego klubu w bazie
        if not Club.query.first():
            # Utworzenie przykładowego klubu
            club = Club(
                name="FC Test",
                description="Przykładowy klub piłkarski do testów",
                city="Warszawa",
                logo=None
            )
            db.session.add(club)
            db.session.commit()

            # Lista użytkowników do utworzenia (login, email, rola, status, zdjęcie profilowe, klub_id)
            users = [
                ("admin", "admin@example.com", "admin", "pro", "img/profiles/admin.jpg", None),
                ("user", "user@example.com", "user", "amateur", None, None),
                ("scout", "scout@example.com", "scout", "pro", "img/profiles/scout.jpg", club.id),
                ("scout2", "scout2@example.com", "scout", "pro", None, club.id),
                ("club_manager", "club_manager@example.com", "club_manager", "pro", None, club.id)
            ]

            created_users = {}
            for username, email, role, status, profile_pic, club_id in users:
                existing_user = User.query.filter_by(username=username).first()
                if existing_user is None:
                    user = User(username=username, email=email, role=role, status=status, profile_picture=profile_pic, club_id=club_id)
                    user.set_password(username)  # Hasło takie samo jak login
                    db.session.add(user)
                    created_users[username] = user
                    print(f'Utworzono konto: {username}')
                else:
                    created_users[username] = existing_user

            db.session.commit()  # Zapisz użytkowników, aby mieć dostęp do ich ID

            # Dodanie 10 dyscyplin sportowych, jeśli jeszcze ich nie ma
            sports = [
                ("Piłka nożna", "Popularna gra zespołowa, w której celem jest zdobycie większej liczby goli."),
                ("Koszykówka", "Dyscyplina polegająca na zdobywaniu punktów przez wrzucanie piłki do kosza."),
                ("Siatkówka", "Sport zespołowy, w którym drużyny odbijają piłkę nad siatką."),
                ("Piłka ręczna", "Gra zespołowa, w której zawodnicy podają i rzucają piłkę do bramki."),
                ("Lekkoatletyka", "Zbiór konkurencji sportowych, takich jak biegi, skoki i rzuty."),
                ("Pływanie", "Sport polegający na pokonywaniu dystansów w wodzie różnymi stylami."),
                ("Boks", "Sport walki, w którym zawodnicy używają pięści do zadawania ciosów."),
                ("Tenis", "Gra polegająca na odbijaniu piłki rakietą nad siatką."),
                ("Hokej na lodzie", "Gra drużynowa, w której zawodnicy zdobywają gole krążkiem."),
                ("Szermierka", "Sport walki, w którym zawodnicy walczą przy użyciu broni białej.")
            ]

            created_sports = {}
            for name, description in sports:
                existing_sport = Sport.query.filter_by(name=name).first()
                if existing_sport is None:
                    sport = Sport(name=name, description=description)
                    db.session.add(sport)
                    created_sports[name] = sport
                else:
                    created_sports[name] = existing_sport

            db.session.commit()
            print('Dodano dyscypliny sportowe.')

            # Dodanie przykładowych zawodników
            if not Player.query.first():
                # Pozycje dla różnych sportów
                positions = {
                    "Piłka nożna": ["Napastnik", "Pomocnik", "Obrońca", "Bramkarz"],
                    "Koszykówka": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
                    "Siatkówka": ["Atakujący", "Rozgrywający", "Środkowy", "Libero", "Przyjmujący"],
                    "Piłka ręczna": ["Bramkarz", "Obrotowy", "Rozgrywający", "Skrzydłowy"]
                }

                # Lista przykładowych imion i nazwisk
                names = ["Adam", "Piotr", "Kamil", "Michał", "Jakub", "Mateusz", "Krzysztof", "Wojciech"]
                surnames = ["Kowalski", "Nowak", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński"]

                # Dodanie zawodników dla każdego użytkownika (admin, scout i user)
                players_to_add = []
                
                # Zawodnicy dodani przez admina (3 zawodników profesjonalnych)
                for i in range(3):
                    sport_name = random.choice(list(created_sports.keys()))
                    sport = created_sports[sport_name]
                    position = random.choice(positions.get(sport_name, [None])) if sport_name in positions else None
                    
                    player = Player(
                        first_name=random.choice(names),
                        last_name=random.choice(surnames),
                        height=random.uniform(160, 210),
                        weight=random.uniform(60, 110),
                        birth_date=date(random.randint(1990, 2005), random.randint(1, 12), random.randint(1, 28)),
                        position=position,
                        sport_id=sport.id,
                        scout_id=created_users['admin'].id,
                        is_amateur=False
                    )
                    players_to_add.append(player)
                
                # Zawodnicy dodani przez scouta (3 zawodników profesjonalnych)
                for i in range(3):
                    sport_name = random.choice(list(created_sports.keys()))
                    sport = created_sports[sport_name]
                    position = random.choice(positions.get(sport_name, [None])) if sport_name in positions else None
                    
                    player = Player(
                        first_name=random.choice(names),
                        last_name=random.choice(surnames),
                        height=random.uniform(160, 210),
                        weight=random.uniform(60, 110),
                        birth_date=date(random.randint(1990, 2005), random.randint(1, 12), random.randint(1, 28)),
                        position=position,
                        sport_id=sport.id,
                        scout_id=created_users['scout'].id,
                        is_amateur=False
                    )
                    players_to_add.append(player)
                
                # Zawodnik amatorski dodany przez użytkownika (1 zawodnik)
                sport_name = random.choice(list(created_sports.keys()))
                sport = created_sports[sport_name]
                position = random.choice(positions.get(sport_name, [None])) if sport_name in positions else None
                
                player = Player(
                    first_name=random.choice(names),
                    last_name=random.choice(surnames),
                    height=random.uniform(160, 210),
                    weight=random.uniform(60, 110),
                    birth_date=date(random.randint(1990, 2005), random.randint(1, 12), random.randint(1, 28)),
                    position=position,
                    sport_id=sport.id,
                    scout_id=created_users['user'].id,
                    is_amateur=True
                )
                players_to_add.append(player)
                
                # Dodanie wszystkich zawodników do bazy
                for player in players_to_add:
                    db.session.add(player)
                
                db.session.commit()
                print(f'Dodano {len(players_to_add)} przykładowych zawodników.')

                # Dodanie przykładowych testów fizycznych dla zawodników
                for player in Player.query.all():
                    test = PhysicalTest(
                        player_id=player.id,
                        test_date=date(2023, random.randint(1, 12), random.randint(1, 28)),
                        sprint_100m=random.uniform(10.5, 15.0),
                        long_jump=random.uniform(150, 300),
                        agility=random.uniform(5.0, 12.0),
                        endurance=random.uniform(500, 3000),
                        strength=random.uniform(50, 150),
                        notes="Przykładowe dane testowe."
                    )
                    db.session.add(test)
                
                db.session.commit()
                print('Dodano przykładowe testy fizyczne dla zawodników.')

    migrate = Migrate(app, db)
    return app

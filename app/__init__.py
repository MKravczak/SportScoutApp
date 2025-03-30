from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import main, auth, players, admin
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(players, url_prefix='/players')
    app.register_blueprint(admin, url_prefix='/admin')

    with app.app_context():
        db.create_all()

        from app.models import User, Sport  # Import modeli

        # Lista użytkowników do utworzenia (login, email, rola)
        users = [
            ("admin", "admin@example.com", "admin"),
            ("user", "user@example.com", "user"),
            ("scout", "scout@example.com", "scout"),
            ("club_manager", "club_manager@example.com", "club_manager")
        ]

        for username, email, role in users:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user is None:
                user = User(username=username, email=email, role=role)
                user.set_password(username)  # Hasło takie samo jak login
                db.session.add(user)
                print(f'Utworzono konto: {username}')

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

        for name, description in sports:
            existing_sport = Sport.query.filter_by(name=name).first()
            if existing_sport is None:
                sport = Sport(name=name, description=description)
                db.session.add(sport)

        db.session.commit()
        print('Dodano dyscypliny sportowe.')

    return app

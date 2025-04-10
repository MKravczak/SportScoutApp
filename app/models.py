# app/models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import login_manager, db


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100))
    scouts = db.relationship('User', backref='club', lazy='dynamic', foreign_keys='User.club_id')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __str__(self):
        return self.name


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # user, scout, club_manager, admin
    profile_picture = db.Column(db.String(200), nullable=True)  # Path to profile picture file
    status = db.Column(db.String(20), default='amateur')  # pro/amateur
    # created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    players = db.relationship('Player', backref='scout', lazy='dynamic')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    players = db.relationship('Player', backref='sport', lazy='dynamic')
    sport_tests = db.relationship('SportTest', backref='sport', lazy='dynamic')


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    height = db.Column(db.Float)  # w cm
    weight = db.Column(db.Float)  # w kg
    birth_date = db.Column(db.Date)
    position = db.Column(db.String(64))
    photo = db.Column(db.String(255), nullable=True)  # Path to player photo
    is_amateur = db.Column(db.Boolean, default=False)  # True for amateur players, False for professional
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'))
    scout_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    physical_tests = db.relationship('PhysicalTest', backref='player', lazy='dynamic')
    match_stats = db.relationship('MatchStat', backref='player', lazy='dynamic')
    player_tests = db.relationship('PlayerTest', backref='player', lazy='dynamic')


class PhysicalTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    test_date = db.Column(db.Date, default=datetime.utcnow)
    sprint_100m = db.Column(db.Float)  # w sekundach
    long_jump = db.Column(db.Float)  # w cm
    agility = db.Column(db.Float)  # w sekundach
    endurance = db.Column(db.Float)  # w sekundach lub metrach zależnie od testu
    strength = db.Column(db.Float)  # w kg
    notes = db.Column(db.Text)


class SportTest(db.Model):
    __tablename__ = 'sport_test'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))  # np. "sprint", "siła", "wytrzymałość", "technika"
    unit = db.Column(db.String(20))  # np. "sekundy", "metry", "kilogramy", "punkty"
    is_lower_better = db.Column(db.Boolean, default=True)  # True jeśli niższy wynik jest lepszy (np. czas)
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    player_tests = db.relationship('PlayerTest', backref='sport_test', lazy='dynamic', foreign_keys='PlayerTest.test_id')


class PlayerTest(db.Model):
    __tablename__ = 'player_test'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('sport_test.id'))
    result = db.Column(db.Float)
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    opponent = db.Column(db.String(128), nullable=False)
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'))
    result = db.Column(db.String(64))
    location = db.Column(db.String(128))
    match_stats = db.relationship('MatchStat', backref='match', lazy='dynamic')


class MatchStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    minutes_played = db.Column(db.Integer)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    ball_contacts = db.Column(db.Integer, default=0)
    distance_covered = db.Column(db.Float)  # w km
    # Dodatkowe pola specyficzne dla danej dyscypliny
    shots = db.Column(db.Integer, default=0)  # piłka nożna, koszykówka
    passes = db.Column(db.Integer, default=0)
    successful_passes = db.Column(db.Integer, default=0)
    fouls_committed = db.Column(db.Integer, default=0)
    fouls_received = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)  # piłka nożna
    red_cards = db.Column(db.Integer, default=0)  # piłka nożna
    blocks = db.Column(db.Integer, default=0)  # koszykówka, siatkówka
    rebounds = db.Column(db.Integer, default=0)  # koszykówka
    steals = db.Column(db.Integer, default=0)  # koszykówka
# app/routes/__init__.py
from flask import Blueprint

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
players = Blueprint('players', __name__)
admin = Blueprint('admin', __name__)
clubs = Blueprint('clubs', __name__)
tests = Blueprint('tests', __name__)

from . import main_routes, auth_routes, player_routes, admin_routes, club_routes, tests_routes
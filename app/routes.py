from flask import Blueprint

# Tworzenie Blueprintów
auth = Blueprint('auth', __name__, url_prefix='/auth')
main = Blueprint('main', __name__)
players = Blueprint('players', __name__, url_prefix='/players')
admin = Blueprint('admin', __name__, url_prefix='/admin')

# Importowanie tras (musi być na końcu, żeby uniknąć błędów importu cyklicznego)
from app.routes import auth_routes, main_routes, player_routes, admin_routes, club_routes
# app/routes/api_routes.py
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_user
from app import db
from app.models import User, Player, Sport, PhysicalTest
from app.utils.auth import token_required, role_required, generate_jwt_token
from app.utils.validation import RequestValidator
from app.utils.cache import cache_result
from werkzeug.security import check_password_hash
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/auth/login', methods=['POST'])
def login():
    """API endpoint for user login"""
    data = request.get_json()
    
    # Validate request data
    validator = RequestValidator(data)
    validator.validate_required('username').validate_required('password')
    
    if not validator.is_valid():
        return jsonify({'errors': validator.get_errors()}), 400
    
    # Check user credentials
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # Generate JWT token
    token = generate_jwt_token(user.id)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'status': user.status
        }
    })

@api.route('/players', methods=['GET'])
@token_required
def get_players(current_user):
    """Get players based on user role"""
    try:
        # Get query parameters
        sport_id = request.args.get('sport_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit max per_page to prevent excessive queries
        per_page = min(per_page, 50)
        
        # Filter players based on user role
        if current_user.role in ['admin', 'club_manager']:
            query = Player.query
        else:  # scout or regular user
            query = Player.query.filter_by(scout_id=current_user.id)
        
        # Apply sport filter if provided
        if sport_id:
            query = query.filter_by(sport_id=sport_id)
            
        # Get paginated results
        players_page = query.paginate(page=page, per_page=per_page)
        
        # Format response
        players = []
        for player in players_page.items:
            players.append({
                'id': player.id,
                'first_name': player.first_name,
                'last_name': player.last_name,
                'position': player.position,
                'height': player.height,
                'weight': player.weight,
                'birth_date': player.birth_date.strftime('%Y-%m-%d') if player.birth_date else None,
                'sport_id': player.sport_id,
                'scout_id': player.scout_id
            })
        
        return jsonify({
            'players': players,
            'total': players_page.total,
            'pages': players_page.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/players/<int:player_id>', methods=['GET'])
@token_required
def get_player(current_user, player_id):
    """Get player details by ID"""
    try:
        player = Player.query.get_or_404(player_id)
        
        # Check if user has permission to view this player
        if current_user.role not in ['admin', 'club_manager'] and player.scout_id != current_user.id:
            return jsonify({'message': 'Permission denied'}), 403
        
        # Get player's physical tests
        tests = []
        for test in player.physical_tests:
            tests.append({
                'id': test.id,
                'test_date': test.test_date.strftime('%Y-%m-%d'),
                'sprint_100m': test.sprint_100m,
                'long_jump': test.long_jump,
                'agility': test.agility,
                'endurance': test.endurance,
                'strength': test.strength,
                'notes': test.notes
            })
        
        return jsonify({
            'player': {
                'id': player.id,
                'first_name': player.first_name,
                'last_name': player.last_name,
                'position': player.position,
                'height': player.height,
                'weight': player.weight,
                'birth_date': player.birth_date.strftime('%Y-%m-%d') if player.birth_date else None,
                'sport_id': player.sport_id,
                'sport_name': player.sport.name if player.sport else None,
                'scout_id': player.scout_id,
                'scout_name': player.scout.username if player.scout else None,
                'physical_tests': tests
            }
        })
    
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/players', methods=['POST'])
@token_required
@role_required('admin', 'scout', 'user')
def create_player(current_user):
    """Create a new player"""
    try:
        data = request.get_json()
        
        # Validate request data
        validator = RequestValidator(data)
        validator.validate_required('first_name')\
                .validate_required('last_name')\
                .validate_required('sport_id')
        
        if not validator.is_valid():
            return jsonify({'errors': validator.get_errors()}), 400
            
        # Parse birth date if provided
        birth_date = None
        if 'birth_date' in data and data['birth_date']:
            try:
                birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid birth date format. Use YYYY-MM-DD'}), 400
        
        # Create new player
        player = Player(
            first_name=data['first_name'],
            last_name=data['last_name'],
            sport_id=data['sport_id'],
            position=data.get('position'),
            height=data.get('height'),
            weight=data.get('weight'),
            birth_date=birth_date,
            scout_id=current_user.id
        )
        
        db.session.add(player)
        db.session.commit()
        
        return jsonify({
            'message': 'Player created successfully',
            'player_id': player.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@api.route('/players/<int:player_id>', methods=['PUT'])
@token_required
def update_player(current_user, player_id):
    """Update player details"""
    try:
        player = Player.query.get_or_404(player_id)
        
        # Check if user has permission to edit this player
        if current_user.role != 'admin' and player.scout_id != current_user.id:
            return jsonify({'message': 'Permission denied'}), 403
        
        data = request.get_json()
        
        # Update player fields if provided
        if 'first_name' in data:
            player.first_name = data['first_name']
        
        if 'last_name' in data:
            player.last_name = data['last_name']
        
        if 'position' in data:
            player.position = data['position']
        
        if 'height' in data:
            player.height = data['height']
        
        if 'weight' in data:
            player.weight = data['weight']
        
        if 'sport_id' in data:
            player.sport_id = data['sport_id']
        
        if 'birth_date' in data and data['birth_date']:
            try:
                player.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid birth date format. Use YYYY-MM-DD'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Player updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@api.route('/players/<int:player_id>', methods=['DELETE'])
@token_required
def delete_player(current_user, player_id):
    """Delete a player"""
    try:
        player = Player.query.get_or_404(player_id)
        
        # Check if user has permission to delete this player
        if current_user.role != 'admin' and player.scout_id != current_user.id:
            return jsonify({'message': 'Permission denied'}), 403
        
        db.session.delete(player)
        db.session.commit()
        
        return jsonify({
            'message': 'Player deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@api.route('/sports', methods=['GET'])
@cache_result(timeout=3600)  # Cache for 1 hour
def get_sports():
    """Get all sports"""
    try:
        sports = []
        for sport in Sport.query.all():
            sports.append({
                'id': sport.id,
                'name': sport.name,
                'description': sport.description
            })
        
        return jsonify({
            'sports': sports
        })
    
    except Exception as e:
        return jsonify({'message': str(e)}), 500 
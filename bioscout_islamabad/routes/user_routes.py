from flask import Blueprint, request, jsonify
from models.user import User

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'Username is required'}), 400
    
    # Check if username already exists
    existing_user = User.find_by_username(data['username'])
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data.get('email'),
        full_name=data.get('full_name')
    )
    
    user_id = user.save()
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'username': data['username']
    }), 201

@bp.route('/<username>', methods=['GET'])
def get_user(username):
    """Get user by username"""
    user = User.find_by_username(username)
    
    if user:
        # Remove sensitive information
        user.pop('_id', None)
        return jsonify({'user': user})
    
    return jsonify({'error': 'User not found'}), 404 
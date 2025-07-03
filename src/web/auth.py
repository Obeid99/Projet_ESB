"""
Flask Blueprint for user registration and authentication
"""
from flask import Blueprint, request, jsonify, session
from src.core.models_db import User
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

bp_auth = Blueprint('auth', __name__, url_prefix='/auth')

@bp_auth.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    user = User(username=username, password_hash=generate_password_hash(password))
    from src.core.models_db import db
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User registered'})

@bp_auth.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = user.id
    return jsonify({'success': True, 'message': 'Logged in'})

@bp_auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': 'Logged out'})

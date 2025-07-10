"""
Flask Blueprint for user registration and authentication (MongoDB version)
"""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_AUTH_STUD = os.getenv("MONGO_COLLECTION_AUTH_STUD")

client = MongoClient(MONGO_URI)
mongodb = client[MONGO_DB_NAME]

bp_auth = Blueprint('auth', __name__, url_prefix='/auth')

@bp_auth.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if mongodb[MONGO_COLLECTION_AUTH_STUD].find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 409
    password_hash = generate_password_hash(password)
    mongodb[MONGO_COLLECTION_AUTH_STUD].insert_one({'username': username, 'password_hash': password_hash})
    return jsonify({'success': True, 'message': 'User registered'})

@bp_auth.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    user = mongodb[MONGO_COLLECTION_AUTH_STUD].find_one({'username': username})
    if not user or not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = str(user['_id'])
    return jsonify({'success': True, 'message': 'Logged in'})

@bp_auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('admin_id', None)
    return jsonify({'success': True, 'message': 'Logged out'})

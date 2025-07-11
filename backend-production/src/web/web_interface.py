"""
Flask Web Interface for Multi-Agent Chatbot (MongoDB + OpenAI)
Admin + Student: tout passe par MongoDB et OpenAI
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import time
import traceback
from dotenv import load_dotenv
import os
import sys
import logging
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logger = logging.getLogger()

# Chargement .env
load_dotenv()

from pymongo import MongoClient
import openai

# ============ ENV VARS & INIT =============
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_AUTH_STUD = os.getenv("MONGO_COLLECTION_AUTH_STUD")
MONGO_COLLECTION_AUTH_ADMIN = os.getenv("MONGO_COLLECTION_AUTH_ADMIN")
MONGO_COLLECTION_CHAT_ADMIN = os.getenv("MONGO_COLLECTION_CHAT_ADMIN")
MONGO_COLLECTION_CHAT_STUD = os.getenv("MONGO_COLLECTION_CHAT_STUD")

client = MongoClient(MONGO_URI)
mongodb = client[MONGO_DB_NAME]
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

from admin_agents.orchestrator import handle_admin_query
from src.core.chat_history import store_message
from src.agents.response_agent import generate_response
from src.agents.intent_agent import IntentAgent
from src.agents.sentiment_agent import SentimentAgent

# Dummy admin credentials fallback (upgrade this later)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
# Enable CORS for local frontend (adjust origins as needed for production)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# ========================
# === AUTHENTIFICATION ===
# ========================
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/login', methods=['GET', 'POST'])
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
        

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'GET':
        return render_template('register.html')
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    password_hash = generate_password_hash(password)

    if not username or not password:
        return jsonify({'success': False, 'error': 'Nom d\'utilisateur et mot de passe requis'})
    if mongodb[MONGO_COLLECTION_AUTH_STUD].find_one({'username': username}):
        return jsonify({'success': False, 'error': 'Nom d\'utilisateur déjà pris'})
    mongodb[MONGO_COLLECTION_AUTH_STUD].insert_one({'username': username, 'password_hash': password_hash})
    return jsonify({'success': True, 'redirect': '/login'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

### ==== ADMIN AUTH (MongoDB) ====
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    admin = mongodb[MONGO_COLLECTION_AUTH_ADMIN].find_one({'username': username, 'password': password})
    if admin or (username == ADMIN_USERNAME and password == ADMIN_PASSWORD):  # fallback
        session['admin_id'] = username
        return jsonify({'success': True, 'redirect': '/admin/chat'})
    else:
        return jsonify({'success': False, 'error': 'Identifiants admin invalides.'})


@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'GET':
        return render_template('admin_register.html')
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    print(f"[DEBUG] POST admin_register: username={username} password={password}")
    print(f"[DEBUG] Using MongoDB collection: {MONGO_COLLECTION_AUTH_ADMIN}")
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required.'})
    if mongodb[MONGO_COLLECTION_AUTH_ADMIN].find_one({'username': username}):
        print("[DEBUG] Username already exists.")
        return jsonify({'success': False, 'error': 'Username already exists.'})
    result = mongodb[MONGO_COLLECTION_AUTH_ADMIN].insert_one({'username': username, 'password': password})
    print(f"[DEBUG] Inserted ID: {result.inserted_id}")
    return jsonify({'success': True, 'redirect': '/admin/login'})



@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

# ================
# === CHAT UI ====
# ================

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('chat.html')

@app.route('/admin/chat')
def admin_chat_page():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_chat.html')

# =========================
# === ETUDIANT: CHATBOT ===
# =========================
from src.core.models import ChatbotState
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        user_id = session['user_id']
        username = session.get('username', 'student')
        data = request.json
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Merci de saisir un message.'
            })

        # Intent and Sentiment detection
        intent_agent = IntentAgent()
        sentiment_agent = SentimentAgent()
        state = intent_agent.process(ChatbotState(user_message=user_message, session_id=user_id))
        logger.info(f"[INTENT] user_id={user_id} username={username} message='{user_message}' intent={state.intent} confidence={state.context.get('intent_confidence')} reasoning={state.context.get('intent_reasoning')}")
        state = sentiment_agent.process(state)
        logger.info(f"[SENTIMENT] user_id={user_id} username={username} message='{user_message}' sentiment={getattr(state, 'sentiment_result', None)}")

        # Store user message with intent and sentiment
        sentiment = getattr(state, 'sentiment_result', None)
        sentiment_label = sentiment.label if sentiment and hasattr(sentiment, 'label') else str(sentiment)
        store_message(user_id, user_message, is_user=True, username=username, sender="student", sentiment=sentiment_label, intent=state.intent)

        # Generate response
        bot_response = generate_response(user_message, session_id=user_id)

        # Store bot response
        store_message(user_id, bot_response, is_user=False, username=username, sender="bot")

        return jsonify({
            'success': True,
            'response': bot_response,
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Error processing message: {e}")
        print(error_trace)
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Sorry, I encountered an error processing your message. Please try again!',
            'debug': error_trace if app.debug else None
        })

# =========================
# === ADMIN: CHATBOT ======
# =========================


@app.route('/admin/api/chat', methods=['POST'])
def admin_chat_api():
    if 'admin_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json()
    admin_message = data.get('message', '').strip()
    if not admin_message:
        return jsonify({'response': 'Merci de saisir une question.'})

    # Stocker le message admin dans MongoDB
    mongodb[MONGO_COLLECTION_CHAT_ADMIN].insert_one({
        "sender": "admin",
        "message": admin_message,
        "timestamp": time.time()
    })

    # Orchestration multi-agent sur la requête admin
    response, meta = handle_admin_query(
        admin_message,
        mongo_db=mongodb,
        collection_feedbacks=MONGO_COLLECTION_CHAT_STUD,
        collection_admin=MONGO_COLLECTION_CHAT_ADMIN,
        session=session,
        
    )

    # Stocker la réponse bot dans Mongo
    mongodb[MONGO_COLLECTION_CHAT_ADMIN].insert_one({
        "sender": "bot",
        "message": response,
        "timestamp": time.time()
    })

    return jsonify({
        'success': True,
        'response': response,
        **meta
    })

# =======================
# === API HEALTHCHECK ===
# =======================
@app.route('/api/health')
def health_check():
    try:
        mongodb.list_collection_names()
        openai.Model.list()
        healthy = True
    except Exception:
        healthy = False
    return jsonify({
        'status': 'healthy' if healthy else 'error',
        'timestamp': time.time()
    })

# ===================
# === STATIC/DASH ===
# ===================
@app.route('/admin/feedback_chart')
def admin_feedback_chart():
    if 'admin_id' not in session:
        return 'Unauthorized', 401
    return '''
    <html><head><title>Feedback Chart</title></head><body>
    <h2>Feedback Chart (Demo)</h2>
    <img src="https://quickchart.io/chart?c={type:'pie',data:{labels:['Positive','Negative'],datasets:[{data:[10,5]}]}}" alt="Feedback Chart"/>
    <p>This is a demo chart. À remplacer par vrai graph généré en prod !</p>
    </body></html>
    '''

# --- chat history in admin interface ---


def get_latest_student_feedback(mongo_db, collection_feedbacks, limit=10):
    """
    Récupère les derniers feedbacks étudiants (utilisateur humain).
    """
    cursor = mongo_db[collection_feedbacks].find(
        {"is_user": True}
    ).sort("timestamp", -1).limit(limit)
    feedbacks = []
    for fb in cursor:
        feedbacks.append({
            "id": str(fb.get("_id")),
            "username": fb.get("username", "") or fb.get("user_id", "") or "Etudiant inconnu",
            "title": fb.get("message")[:32] + ("..." if len(fb.get("message","")) > 32 else ""),
            "created_at": datetime.fromtimestamp(fb.get("timestamp")).strftime("%Y-%m-%d %H:%M"),
            "message": fb.get("message", "")
        })
    return feedbacks

# --- Endpoint Flask ---
@app.route('/admin/api/feedback', methods=['GET'])
def api_latest_student_feedback():
    # Mets bien le nom de ta collection ici
    collection_feedbacks = "history_student"
    feedbacks = get_latest_student_feedback(mongodb, collection_feedbacks, limit=10)
    return jsonify(feedbacks)




if __name__ == '__main__':
    print("🚀 Starting Multi-Agent Chatbot Web Interface...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)

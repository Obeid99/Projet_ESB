"""
Flask Web Interface for Multi-Agent Chatbot (MongoDB + OpenAI)
Admin + Student: tout passe par MongoDB et OpenAI
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import time
import traceback
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Dummy admin credentials fallback (upgrade this later)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ========================
# === AUTHENTIFICATION ===
# ========================

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    user = mongodb[MONGO_COLLECTION_AUTH_STUD].find_one({'username': username, 'password': password})
    if user:
        session['user_id'] = str(user['_id'])
        session['username'] = username
        return jsonify({'success': True, 'redirect': '/chat'})
    else:
        return jsonify({'success': False, 'error': 'Identifiants invalides.'})

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'GET':
        return render_template('register.html')
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'Nom d\'utilisateur et mot de passe requis'})
    if mongodb[MONGO_COLLECTION_AUTH_STUD].find_one({'username': username}):
        return jsonify({'success': False, 'error': 'Nom d\'utilisateur déjà pris'})
    mongodb[MONGO_COLLECTION_AUTH_STUD].insert_one({'username': username, 'password': password})
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

        # Stockage dans MongoDB
        mongodb[MONGO_COLLECTION_CHAT_STUD].insert_one({
            "user_id": user_id,
            "username": username,
            "sender": "student",
            "message": user_message,
            "timestamp": time.time()
        })

        # Récupère les 10 derniers messages pour l'historique du contexte
        chat_history = list(
            mongodb[MONGO_COLLECTION_CHAT_STUD].find({"user_id": user_id}).sort("timestamp", -1).limit(10)
        )[::-1]
        conversation = [{"role": "user" if msg["sender"] == "student" else "assistant", "content": msg["message"]}
                        for msg in chat_history]

        # Prompt système étudiant (tu peux l'améliorer ici)
        SYSTEM_PROMPT = (
            "You are an assistant for ESPRIT School of Business (ESB) in Tunisia. "
            "Never refer to any other school or institution. "
            "All information, responses, and context are about ESPRIT School of Business only. "
            "Here is a list of all specialties and degrees offered at ESB: "
            "- Licence in Management\n"
            "- Licence in Accounting\n"
            "- Licence in Business Computing (Business Intelligence / Business Information Systems)\n"
            "- Masters of Business Analytics\n"
            "- Masters of Digital Marketing\n"
            "- Masters of Accounting\n"
            "If a user asks about a course, specialty, or subject not in this list, politely inform them that it is not offered at ESB and do not make up information."
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation + [{"role": "user", "content": user_message}]

        start_time = time.time()
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages
        )
        bot_response = response.choices[0].message['content']
        total_time = time.time() - start_time

        # Stocke la réponse du bot dans MongoDB
        mongodb[MONGO_COLLECTION_CHAT_STUD].insert_one({
            "user_id": user_id,
            "username": username,
            "sender": "bot",
            "message": bot_response,
            "timestamp": time.time()
        })

        return jsonify({
            'success': True,
            'response': bot_response,
            'processing_time': f"{total_time*1000:.1f}ms",
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
        collection_admin=MONGO_COLLECTION_CHAT_ADMIN
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

if __name__ == '__main__':
    print("🚀 Starting Multi-Agent Chatbot Web Interface...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)

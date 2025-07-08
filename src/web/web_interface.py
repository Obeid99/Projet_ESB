"""
Flask Web Interface for Multi-Agent Chatbot
Real-time testing interface with live agent processing
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import time
import traceback
from dotenv import load_dotenv
load_dotenv()
import os
from src.core import config
print("DATABASE_URL from env:", repr(os.getenv("DATABASE_URL")))

str = str
Exception = Exception
print = print
all = all

# Import our agents
from ..agents.sentiment_agent import SentimentAgent
from ..agents.intent_agent import IntentAgent
from ..agents.web_agent import WebAgent
from ..agents.refiner_agent import RefinerAgent
from ..agents.self_reflection_agent import SelfReflectionAgent
from ..core.models import ChatbotState
from .esb_graph import build_esb_graph
from .auth import bp_auth
from ..core.chat_history import store_message, get_recent_history
from ..core.models_db import db, Project


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "postgresql://esbuser:esbpass@db:5432/esbchatbot")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.register_blueprint(bp_auth)

# Admin authentication routes (must be after app = Flask(__name__))
from werkzeug.security import generate_password_hash, check_password_hash

# Place these routes after app is defined
def register_admin_routes(app):
    @app.route('/admin/api/feedbacks_by_date')
    def admin_feedbacks_by_date():
        if 'admin_id' not in session:
            return jsonify({'data': []})
        from ..core.models_db import User, ChatHistory
        from sqlalchemy import func, cast, Date
        # Group by date and sentiment (assume 'positive'/'negative' in message as placeholder)
        feedbacks = (
            db.session.query(
                func.date(ChatHistory.timestamp).label('date'),
                func.sum(ChatHistory.message.ilike('%positive%')).label('positive'),
                func.sum(ChatHistory.message.ilike('%negative%')).label('negative'),
                func.count().label('total')
            )
            .join(User, ChatHistory.user_id == User.id)
            .filter(~User.username.in_(['admin']))
            .group_by(func.date(ChatHistory.timestamp))
            .order_by(func.date(ChatHistory.timestamp).asc())
            .all()
        )
        data = []
        for row in feedbacks:
            data.append({
                'date': str(row.date),
                'positive': int(row.positive),
                'negative': int(row.negative),
                'total': int(row.total)
            })
        return jsonify({'data': data})
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login_page'))
        return render_template('admin_dashboard.html')
    @app.route('/admin/landing')
    def admin_landing():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login_page'))
        return render_template('admin_landing.html')

    @app.route('/admin/export_feedbacks')
    def export_feedbacks():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login_page'))
        return render_template('export_feedbacks.html')
    @app.route('/admin/api/feedback_count')
    def admin_feedback_count():
        if 'admin_id' not in session:
            return jsonify({'count': 0})
        from ..core.models_db import User, ChatHistory
        from sqlalchemy import func, and_, cast, Date
        from datetime import date
        sentiment = request.args.get('sentiment')
        today = date.today()
        q = db.session.query(ChatHistory)
        q = q.join(User, ChatHistory.user_id == User.id)
        q = q.filter(cast(ChatHistory.timestamp, Date) == today)
        q = q.filter(~User.username.in_(['admin']))
        if sentiment:
            # Only count feedbacks with the given sentiment label (requires storing sentiment label in ChatHistory or elsewhere)
            # For now, assume messages containing 'positive' or 'negative' in message as a placeholder
            if sentiment == 'positive':
                q = q.filter(ChatHistory.message.ilike('%positive%'))
            elif sentiment == 'negative':
                q = q.filter(ChatHistory.message.ilike('%negative%'))
            count = q.count()
            return jsonify({'count': count})
        else:
            # Instead of counting all, return sum of positive + negative
            q_pos = db.session.query(ChatHistory).join(User, ChatHistory.user_id == User.id)
            q_pos = q_pos.filter(cast(ChatHistory.timestamp, Date) == today)
            q_pos = q_pos.filter(~User.username.in_(['admin']))
            q_pos = q_pos.filter(ChatHistory.message.ilike('%positive%'))
            pos_count = q_pos.count()
            q_neg = db.session.query(ChatHistory).join(User, ChatHistory.user_id == User.id)
            q_neg = q_neg.filter(cast(ChatHistory.timestamp, Date) == today)
            q_neg = q_neg.filter(~User.username.in_(['admin']))
            q_neg = q_neg.filter(ChatHistory.message.ilike('%negative%'))
            neg_count = q_neg.count()
            return jsonify({'count': pos_count + neg_count})

    @app.route('/admin/feedback_chart')
    def admin_feedback_chart():
        if 'admin_id' not in session:
            return 'Unauthorized', 401
        # For demo: just show a placeholder chart
        return '''
        <html><head><title>Feedback Chart</title></head><body>
        <h2>Feedback Chart (Demo)</h2>
        <img src="https://quickchart.io/chart?c={type:%27pie%27,data:{labels:[%27Positive%27,%27Negative%27],datasets:[{data:[10,5]}]}}" alt="Feedback Chart"/>
        <p>This is a demo chart. Integrate with real data for production.</p>
        </body></html>
        '''
    @app.route('/admin/login', methods=['GET'])
    def admin_login_page():
        return render_template('admin_login.html')

    @app.route('/admin/login', methods=['POST'])
    def admin_login():
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        # Hardcoded admin credentials
        if username == 'admin' and password == 'admin':
            session['admin_id'] = 'admin'
            return jsonify({'success': True, 'redirect': '/admin/landing'})
        else:
            return jsonify({'success': False, 'error': 'Invalid admin credentials.'})

    @app.route('/admin/chat')
    def admin_chat_page():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login_page'))
        return render_template('admin_chat.html')

    @app.route('/admin/api/feedback')
    def admin_feedback():
        if 'admin_id' not in session:
            return jsonify([])
        from ..core.models_db import User, ChatHistory
        from sqlalchemy import func
        # Exclude admin users from feedback (by username only)
        admin_usernames = ['admin']
        feedback = (
            db.session.query(
                ChatHistory.user_id,
                User.username,
                func.date(ChatHistory.timestamp).label('date'),
                func.min(ChatHistory.timestamp).label('created_at'),
                func.min(ChatHistory.id).label('first_msg_id')
            )
            .join(User, ChatHistory.user_id == User.id)
            .filter(~User.username.in_(admin_usernames))
            .group_by(ChatHistory.user_id, User.username, func.date(ChatHistory.timestamp))
            .order_by(func.min(ChatHistory.timestamp).desc())
            .limit(50)
            .all()
        )
        # Get the first message for each discussion as the title
        discussions = []
        for user_id, username, date, created_at, first_msg_id in feedback:
            first_msg = ChatHistory.query.get(first_msg_id)
            title = (first_msg.message[:60] + '...') if first_msg and len(first_msg.message) > 60 else (first_msg.message if first_msg else '(No Title)')
            discussion_id = f"{user_id}:{date}"
            discussions.append({
                'id': discussion_id,
                'title': title or '(No Title)',
                'username': username,
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify(discussions)

    @app.route('/admin/api/discussion/<discussion_id>')
    def admin_discussion(discussion_id):
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        from ..core.models_db import User, ChatHistory
        # discussion_id format: user_id:date
        try:
            user_id, date = discussion_id.split(':', 1)
        except Exception:
            return jsonify({'error': 'Invalid discussion id'}), 400
        # Get all messages for this user on this date
        from sqlalchemy import and_, cast, Date
        messages = (
            ChatHistory.query
            .filter(
                ChatHistory.user_id == int(user_id),
                cast(ChatHistory.timestamp, Date) == date
            )
            .order_by(ChatHistory.timestamp.asc())
            .all()
        )
        user = User.query.get(int(user_id))
        result = {
            'username': user.username if user else 'Unknown',
            'messages': [
                {
                    'sender': (user.username if m.is_user else 'Bot'),
                    'text': m.message,
                    'created_at': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                for m in messages
            ]
        }
        return jsonify(result)

    @app.route('/admin/api/chat', methods=['POST'])
    def admin_chat_api():
        if 'admin_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        data = request.get_json()
        admin_message = data.get('message', '').strip()
        if not admin_message:
            return jsonify({'response': 'Please enter a message.'})
        # Ensure dummy admin user exists and get its ID
        from src.core.models_db import ensure_admin_user
        admin_user_id = ensure_admin_user()
        store_message(admin_user_id, admin_message, is_user=True)
        chat_history = get_recent_history(admin_user_id)
        history_text = '\n'.join([
            ("User: " if h['is_user'] else "Bot: ") + h['message'] for h in chat_history
        ])
        start_time = time.time()
        graph = build_esb_graph(sentiment_agent, intent_agent, web_agent, refiner_agent, reflection_agent)
        from src.core.models import ChatbotState
        chatbot_state = ChatbotState(user_message=admin_message, chat_history=history_text)
        state = {"user_message": admin_message, "chatbot_state": chatbot_state}
        result = graph.invoke(state)
        state = result
        total_time = time.time() - start_time
        bot_response = state['chatbot_state'].response or "I'm here to help! How can I assist you?"
        store_message(admin_user_id, bot_response, is_user=False)
        response_data = {
            'success': True,
            'response': bot_response,
            'processing_time': f"{total_time*1000:.1f}ms",
            'sentiment': {
                'label': str(state['chatbot_state'].sentiment_result.label) if state['chatbot_state'].sentiment_result else 'unknown',
                'confidence': state['chatbot_state'].sentiment_result.confidence if state['chatbot_state'].sentiment_result else 0,
            }
        }
        return jsonify(response_data)

    @app.route('/admin/register', methods=['GET'])
    def admin_register_page():
        return render_template('admin_register.html')

    @app.route('/admin/register', methods=['POST'])
    def admin_register():
        from ..core.models_db import User  # Import here to avoid circular import
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'})
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'})
        password_hash = generate_password_hash(password)
        admin_user = User(username=username, password_hash=password_hash)
        db.session.add(admin_user)
        db.session.commit()
        # After successful registration, redirect to login page
        return jsonify({'success': True, 'redirect': '/admin/login'})

register_admin_routes(app)


# Initialize agents globally
print("🤖 Initializing Multi-Agent System...")
try:
    # Try to initialize with Hybrid (Ollama + traditional) first, fallback to rule-based if needed
    print("🦙 Attempting to connect to Ollama for hybrid analysis...")
    sentiment_agent = SentimentAgent(analyzer_type="hybrid", use_ollama=True)
    intent_agent = IntentAgent(use_ollama=True)
    web_agent = WebAgent()
    refiner_agent = RefinerAgent(use_ollama=True)
    reflection_agent = SelfReflectionAgent()
    print("✅ All agents initialized successfully with Hybrid (Ollama + Traditional) analysis!")
except Exception as e:
    print(f"⚠️ Ollama not available ({e}), falling back to rule-based agents...")
    try:
        sentiment_agent = SentimentAgent(analyzer_type="vader", use_ollama=False, use_openai=False)
        intent_agent = IntentAgent(use_ollama=False)
        web_agent = WebAgent()
        refiner_agent = RefinerAgent(use_ollama=False)
        reflection_agent = SelfReflectionAgent()
        print("✅ All agents initialized successfully with rule-based fallback!")
    except Exception as e2:
        print(f"❌ Error initializing agents: {e2}")
        sentiment_agent = intent_agent = web_agent = refiner_agent = reflection_agent = None


# Home page with two session choices
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login_page():
    """Render login page"""
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Render registration page"""
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return render_template('register.html')

@app.route('/chat')
def chat_page():
    """Main chat interface"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message through multi-agent system using LangGraph"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        user_id = session['user_id']
        data = request.json
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Please enter a message to get started!'
            })
        # Store user message
        store_message(user_id, user_message, is_user=True)
        # Fetch recent chat history for context
        chat_history = get_recent_history(user_id)
        conversation_history = []
        for h in chat_history:
            role = "user" if h['is_user'] else "system"
            conversation_history.append({"role": role, "content": h['message']})

        # SYSTEM PROMPT for all LLM calls
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

        start_time = time.time()
        # Build the graph (reuse agents from global scope)
        graph = build_esb_graph(sentiment_agent, intent_agent, web_agent, refiner_agent, reflection_agent)
        # Pass conversation_history to ChatbotState
        chatbot_state = ChatbotState(user_message=user_message, conversation_history=conversation_history)
        chatbot_state.context['system_prompt'] = SYSTEM_PROMPT
        state = {"user_message": user_message, "chatbot_state": chatbot_state}
        # Run the graph using .invoke()
        result = graph.invoke(state)
        state = result  # result is the final state dict
        total_time = time.time() - start_time
        # Store bot response
        bot_response = state['chatbot_state'].response or "I'm here to help! How can I assist you?"
        store_message(user_id, bot_response, is_user=False)
        # Prepare response (reuse previous logic)
        response_data = {
            'success': True,
            'response': bot_response,
            'processing_time': f"{total_time*1000:.1f}ms",
            'sentiment': {
                'label': str(state['chatbot_state'].sentiment_result.label) if state['chatbot_state'].sentiment_result else 'unknown',
                'confidence': state['chatbot_state'].sentiment_result.confidence if state['chatbot_state'].sentiment_result else 0,
                'emoji': get_sentiment_emoji(str(state['chatbot_state'].sentiment_result.label) if state['chatbot_state'].sentiment_result else 'neutral')
            },
            'intent': state['chatbot_state'].intent or 'general_info',
            'reflection': state['chatbot_state'].context.get('reflection_prompt')
        }
        return jsonify(response_data)
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

def get_sentiment_emoji(sentiment):
    """Get emoji for sentiment"""
    emoji_map = {
        'positive': '😊',
        'negative': '😟',
        'neutral': '😐'
    }
    return emoji_map.get(sentiment.lower(), '🤔')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    agent_status = {
        'sentiment_agent': sentiment_agent is not None,
        'intent_agent': intent_agent is not None,
        'web_agent': web_agent is not None,
        'refiner_agent': refiner_agent is not None,
        'reflection_agent': reflection_agent is not None
    }
    
    all_healthy = all(agent_status.values())
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'agents': agent_status,
        'timestamp': time.time()
    })

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get list of projects for the authenticated user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    user_id = session['user_id']
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
    return jsonify([
        {'id': p.id, 'name': p.name, 'created_at': p.created_at.isoformat()} for p in projects
    ])

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project for the authenticated user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    user_id = session['user_id']
    data = request.json
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Project name required'}), 400
    project = Project(name=name, user_id=user_id)
    db.session.add(project)
    db.session.commit()
    return jsonify({'id': project.id, 'name': project.name, 'created_at': project.created_at.isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Multi-Agent Chatbot Web Interface...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)


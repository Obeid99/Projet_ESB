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
from ..graph.esb_graph import build_esb_graph
from src.web.auth import bp_auth
from src.core.chat_history import store_message, get_recent_history
from src.core.models_db import db, Project

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "postgresql://esbuser:esbpass@db:5432/esbchatbot")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.register_blueprint(bp_auth)

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

@app.route('/')
def root():
    """Redirect to login or chat depending on authentication"""
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return redirect(url_for('login_page'))

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
        # Optionally, format chat_history for the chatbot (e.g., as a string)
        history_text = '\n'.join([
            ("User: " if h['is_user'] else "Bot: ") + h['message'] for h in chat_history
        ])
        start_time = time.time()
        # Build the graph (reuse agents from global scope)
        graph = build_esb_graph(sentiment_agent, intent_agent, web_agent, refiner_agent, reflection_agent)
        # Initialize state as a dict, include history
        chatbot_state = ChatbotState(user_message=user_message, chat_history=history_text)
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


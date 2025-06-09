"""
Flask Web Interface for ESB Multi-Agent Chatbot
Real-time testing interface with live agent processing
"""
from flask import Flask, render_template, request, jsonify
import sys
import os
import time
import traceback

# Import our agents
from ..agents.sentiment_agent import SentimentAgent
from ..agents.intent_agent import IntentAgent
from ..agents.web_agent import WebAgent
from ..agents.refiner_agent import RefinerAgent
from ..agents.self_reflection_agent import SelfReflectionAgent
from ..core.models import ChatbotState

app = Flask(__name__)

# Initialize agents globally
print("🤖 Initializing ESB Multi-Agent System...")
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
def index():
    """Main chat interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message through multi-agent system"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Please enter a message to get started!'
            })
        
        # Track processing time
        start_time = time.time()
        
        # Initialize state
        state = ChatbotState(user_message=user_message)
        processing_steps = []
        
        # Step 1: Sentiment Analysis
        step_start = time.time()
        if sentiment_agent:
            state = sentiment_agent.process(state)
            sentiment_time = time.time() - step_start
            
            if state.sentiment_result:
                processing_steps.append({
                    'agent': 'SentimentAgent',
                    'result': f"{state.sentiment_result.label} ({state.sentiment_result.confidence:.3f})",
                    'time': f"{sentiment_time*1000:.1f}ms",
                    'reasoning': state.sentiment_result.reasoning
                })
        
        # Step 2: Intent Classification
        step_start = time.time()
        if intent_agent:
            state = intent_agent.process(state)
            intent_time = time.time() - step_start
            
            processing_steps.append({
                'agent': 'IntentAgent',
                'result': state.intent or 'general_info',
                'time': f"{intent_time*1000:.1f}ms",
                'confidence': state.context.get('intent_confidence', 0)
            })
        
        # Step 3: Web Information (if needed)
        step_start = time.time()
        if web_agent:
            state = web_agent.process(state)
            web_time = time.time() - step_start
            
            web_info = state.context.get('web_info', [])
            processing_steps.append({
                'agent': 'WebAgent',
                'result': f"{len(web_info)} information sources found",
                'time': f"{web_time*1000:.1f}ms",
                'sources': [info.get('title', 'Unknown') for info in web_info[:3]]
            })
        
        # Step 4: Response Generation
        step_start = time.time()
        if refiner_agent:
            state = refiner_agent.process(state)
            refiner_time = time.time() - step_start
            
            processing_steps.append({
                'agent': 'RefinerAgent',
                'result': f"Response generated ({len(state.response or '')} characters)",
                'time': f"{refiner_time*1000:.1f}ms",
                'tone': state.context.get('response_tone', 'professional')
            })
        
        # Step 5: Self-Reflection (if appropriate)
        step_start = time.time()
        if reflection_agent:
            state = reflection_agent.process(state)
            reflection_time = time.time() - step_start
            
            reflection = state.context.get('reflection_prompt')
            processing_steps.append({
                'agent': 'SelfReflectionAgent',
                'result': 'Reflection provided' if reflection else 'No reflection needed',
                'time': f"{reflection_time*1000:.1f}ms",
                'type': reflection.get('type') if reflection else None
            })
        
        total_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            'success': True,
            'response': state.response or "I'm here to help! How can I assist you?",
            'processing_time': f"{total_time*1000:.1f}ms",
            'steps': processing_steps,
            'sentiment': {
                'label': str(state.sentiment_result.label) if state.sentiment_result else 'unknown',
                'confidence': state.sentiment_result.confidence if state.sentiment_result else 0,
                'emoji': get_sentiment_emoji(str(state.sentiment_result.label) if state.sentiment_result else 'neutral')
            },
            'intent': state.intent or 'general_info',
            'reflection': state.context.get('reflection_prompt')
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

if __name__ == '__main__':
    print("🚀 Starting ESB Multi-Agent Chatbot Web Interface...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

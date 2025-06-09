#!/usr/bin/env python3
"""
Simple ESB Chatbot Runner - Minimal version that works
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    print("🤖 ESB Multi-Agent Chatbot System")
    print("=" * 40)
    
    try:
        # Test core components first
        print("1. Testing core models...")
        from src.core.models import ChatbotState, SentimentResult, SentimentLabel
        print("   ✅ Core models imported")
        
        print("2. Testing basic sentiment analysis...")
        from src.analyzers.sentiment_analyzer import TextBlobAnalyzer
        analyzer = TextBlobAnalyzer()
        result = analyzer.analyze("Hello ESB!")
        print(f"   ✅ Sentiment: {result.label}")
        
        print("3. Testing Flask app...")
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return """
            <html>
            <head><title>ESB Chatbot</title></head>
            <body>
                <h1>🤖 ESB Multi-Agent Chatbot</h1>
                <p>System is running successfully!</p>
                <p>Sentiment analysis works: """ + str(result.label) + """</p>
            </body>
            </html>
            """
        
        print("✅ All components working!")
        print("🌐 Starting server at: http://localhost:5000")
        print("💬 Basic system ready!")
        print("=" * 40)
        
        # Run the simple Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

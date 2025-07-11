#!/usr/bin/env python3
"""
ESB Multi-Agent Chatbot Server
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv(override=True)

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    print("🤖 ESB Multi-Agent Chatbot System")
    print("=" * 40)

    try:
        from src.web.web_interface import app

        CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

        print("✅ All agents initialized successfully!")
        print("🌐 Server starting at: http://localhost:5000")
        print("💬 Ready for student interactions!")
        print("=" * 40)

        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

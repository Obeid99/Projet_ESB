#!/usr/bin/env python3
"""
ESB Multi-Agent Chatbot Server
"""

import sys
from pathlib import Path
import os

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set up database connection
from dotenv import load_dotenv
load_dotenv(override=True)

if __name__ == "__main__":
    print("🤖 ESB Multi-Agent Chatbot System")
    print("=" * 40)

    try:
        # Import and run the web interface
        from src.web.web_interface import app

        print("✅ All agents initialized successfully!")
        print("🌐 Server starting at: http://localhost:5000")
        print("💬 Ready for student interactions!")
        print("=" * 40)

        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

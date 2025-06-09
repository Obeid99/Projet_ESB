#!/usr/bin/env python3
"""
ESB Chatbot System - Main Entry Point
Multi-agent chatbot system for ESB (Esprit School of Business)
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging first
from src.utils.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the ESB Chatbot System"""
    try:
        logger.info("🚀 Starting ESB Chatbot System...")
        
        # Import and start the web interface
        from src.web.web_interface import app
        
        logger.info("✅ ESB Chatbot System initialized successfully!")
        logger.info("🌐 Starting web server on http://localhost:5000")
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("👋 ESB Chatbot System stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start ESB Chatbot System: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

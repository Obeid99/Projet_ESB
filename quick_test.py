#!/usr/bin/env python3
"""
Quick test to verify the system works
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    print("🧪 Quick System Test")
    print("=" * 30)
    
    try:
        print("1. Testing core imports...")
        from src.core.models import ChatbotState
        print("   ✅ Core models imported")
        
        print("2. Testing sentiment analyzer...")
        from src.analyzers.sentiment_analyzer import get_sentiment_analyzer
        analyzer = get_sentiment_analyzer("textblob")
        result = analyzer.analyze("Hello ESB!")
        print(f"   ✅ Sentiment analysis: {result.label}")
        
        print("3. Testing agents...")
        from src.agents.sentiment_agent import SentimentAgent
        agent = SentimentAgent()
        print("   ✅ SentimentAgent created")
        
        print("4. Testing web interface...")
        from src.web.web_interface import app
        print("   ✅ Web interface imported")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 System is ready to run!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n💡 Run: python run_server.py")
    else:
        print("\n💡 Fix the errors above first")

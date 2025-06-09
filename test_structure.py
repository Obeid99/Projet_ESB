#!/usr/bin/env python3
"""
Test script to verify the cleaned codebase structure
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_core_imports():
    """Test core module imports"""
    print("🧪 Testing core imports...")
    try:
        from src.core.models import ChatbotState, SentimentResult, SentimentLabel
        from src.core.config import get_settings
        from src.core.database import get_db_manager
        print("✅ Core imports successful")
        return True
    except Exception as e:
        print(f"❌ Core imports failed: {e}")
        return False

def test_analyzer_imports():
    """Test analyzer imports"""
    print("🧪 Testing analyzer imports...")
    try:
        from src.analyzers.sentiment_analyzer import get_sentiment_analyzer
        analyzer = get_sentiment_analyzer("textblob")
        print("✅ Analyzer imports successful")
        return True
    except Exception as e:
        print(f"❌ Analyzer imports failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("🧪 Testing basic functionality...")
    try:
        from src.core.models import ChatbotState, SentimentLabel
        from src.analyzers.sentiment_analyzer import get_sentiment_analyzer
        
        # Test sentiment analysis
        analyzer = get_sentiment_analyzer("textblob")
        result = analyzer.analyze("I love this system!")
        
        # Test state creation
        state = ChatbotState(user_message="Hello world")
        
        print(f"✅ Basic functionality works - Sentiment: {result.label}, State: {state.user_message}")
        return True
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("🧪 Testing database...")
    try:
        from src.core.database import get_db_manager
        from src.core.models import SentimentResult, SentimentLabel
        
        db = get_db_manager()
        
        # Test database connection
        stats = db.get_sentiment_stats()
        print(f"✅ Database works - Stats: {len(stats)} entries")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing ESB Chatbot Structure...")
    print("=" * 50)
    
    tests = [
        test_core_imports,
        test_analyzer_imports,
        test_basic_functionality,
        test_database
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The codebase structure is clean and working!")
        return True
    else:
        print("⚠️ Some tests failed. Check the imports and structure.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

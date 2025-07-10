"""
Configuration module for ESB Chatbot System
"""
import os

class Settings:
    """Simple settings class for ESB Chatbot System (Groq/OpenAI only)"""
    def __init__(self):
        # LLM Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq")
        # Groq/OpenAI Configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
        # Sentiment Analysis Configuration
        self.sentiment_model = os.getenv("SENTIMENT_MODEL", "hybrid")
        self.sentiment_threshold_positive = float(os.getenv("SENTIMENT_THRESHOLD_POSITIVE", "0.1"))
        self.sentiment_threshold_negative = float(os.getenv("SENTIMENT_THRESHOLD_NEGATIVE", "-0.1"))
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/chatbot.log")
        # ESB Specific Configuration
        self.esb_website_url = os.getenv("ESB_WEBSITE_URL", "https://esprit.tn")
        self.esb_facebook_url = os.getenv("ESB_FACEBOOK_URL", "https://facebook.com/esprit.tn")

# Global settings instance
settings = Settings()

def get_settings():
    """Get application settings"""
    return settings

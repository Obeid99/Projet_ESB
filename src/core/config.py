"""
Configuration module for ESB Chatbot System
"""
import os


class Settings:
    """Simple settings class without Pydantic for testing"""

    def __init__(self):
        # LLM Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama")

        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))

        # OpenAI Configuration (fallback)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "postgresql://esbuser:esbpass@db:5432/esbchatbot")

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

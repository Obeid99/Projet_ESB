"""
SentimentAgent for ESB Chatbot System
Implements ReAct pattern (Reason + Act + Observe) for sentiment analysis
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from builtins import str, int, bool, Exception, type, len

from ..core.models import (
    ChatbotState,
    SentimentResult,
    SentimentLabel,
    AgentAction,
    AgentObservation
)
from ..core.config import get_settings
from ..utils.esb_data import get_esb_data

logger = logging.getLogger(__name__)


class SentimentAgent:
    """
    SentimentAgent that analyzes emotional tone of user messages using Groq Llama 3.3 70B Versatile
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
    
    def process(self, state: ChatbotState) -> ChatbotState:
        import os
        import requests
        import json
        esb_data = get_esb_data()
        esb_summary = json.dumps(esb_data[:2], ensure_ascii=False)  # Use a summary or first 2 programs for brevity
        api_key = os.getenv("GROQ_API_KEY")
        model = "llama-3.3-70b-versatile"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            "You are an ESB school assistant chatbot. Analyze the sentiment of the following message. "
            "You have access to the following ESB program data (JSON):\n" + esb_summary + "\n"
            "Respond ONLY with a JSON object: {\"label\": \"positive|negative|neutral\", \"confidence\": 0.0-1.0, \"reasoning\": \"brief explanation\"}. "
            f"Message: {state.user_message}"
        )
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an ESB (esprit school of business) assistant agent."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            sentiment = json.loads(content)
            state.sentiment_result = type('SentimentResult', (), sentiment)()
        except Exception as e:
            state.sentiment_result = type('SentimentResult', (), {"label": "neutral", "confidence": 0.0, "reasoning": str(e)})()
        return state
    
    def get_sentiment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sentiment analysis history for current session"""
        try:
            records = self.db_manager.get_sentiment_history(
                session_id=self.session_id,
                limit=limit
            )
            return [
                {
                    "message": record.user_message,
                    "sentiment": record.sentiment_label,
                    "confidence": record.confidence,
                    "timestamp": record.timestamp.isoformat(),
                    "reasoning": record.reasoning
                }
                for record in records
            ]
        except Exception as e:
            logger.error(f"Error retrieving sentiment history: {e}")
            return []
    
    def get_sentiment_stats(self) -> Dict[str, Any]:
        """Get sentiment statistics for current session"""
        try:
            return self.db_manager.get_sentiment_stats(session_id=self.session_id)
        except Exception as e:
            logger.error(f"Error retrieving sentiment stats: {e}")
            return {}


# LangGraph integration functions
def create_sentiment_node(
    analyzer_type: str = "hybrid",
    use_openai: bool = False,
    use_ollama: bool = True
):
    """
    Factory function to create a sentiment analysis node for LangGraph
    """
    def sentiment_node(state: ChatbotState) -> ChatbotState:
        """LangGraph node function for sentiment analysis"""
        agent = SentimentAgent(
            analyzer_type=analyzer_type,
            use_openai=use_openai,
            use_ollama=use_ollama,
            session_id=state.metadata.get("session_id")
        )
        return agent.process(state)

    return sentiment_node


def should_analyze_sentiment(state: ChatbotState) -> bool:
    """
    Conditional function for LangGraph to determine if sentiment analysis is needed
    """
    return (
        state.sentiment_result is None and 
        state.user_message and 
        len(state.user_message.strip()) >= 3
    )

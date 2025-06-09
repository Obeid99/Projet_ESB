"""
SentimentAgent for ESB Chatbot System
Implements ReAct pattern (Reason + Act + Observe) for sentiment analysis
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.models import (
    ChatbotState,
    SentimentResult,
    SentimentLabel,
    AgentAction,
    AgentObservation
)
from ..analyzers.sentiment_analyzer import get_sentiment_analyzer, SentimentAnalyzer
from ..core.database import get_db_manager, DatabaseManager
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class SentimentAgent:
    """
    SentimentAgent that analyzes emotional tone of user messages
    Follows ReAct pattern: Reason -> Act -> Observe
    """
    
    def __init__(
        self,
        analyzer_type: str = "hybrid",
        use_openai: bool = False,
        use_ollama: bool = True,
        session_id: Optional[str] = None
    ):
        self.settings = get_settings()
        self.analyzer_type = analyzer_type
        self.use_openai = use_openai
        self.use_ollama = use_ollama
        self.session_id = session_id or str(uuid.uuid4())

        # Initialize sentiment analyzer
        self.analyzer: SentimentAnalyzer = get_sentiment_analyzer(
            model_type=analyzer_type,
            use_openai=use_openai,
            use_ollama=use_ollama,
            openai_api_key=self.settings.openai_api_key,
            ollama_model=self.settings.ollama_model
        )
        
        # Initialize database manager
        self.db_manager: DatabaseManager = get_db_manager()
        
        logger.info(f"SentimentAgent initialized with {analyzer_type} analyzer, session: {self.session_id}")
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Analyze what needs to be done
        """
        user_message = state.user_message.strip()
        
        # Check if message is empty or too short
        if not user_message or len(user_message) < 3:
            reasoning = "Message is too short or empty for meaningful sentiment analysis"
            return AgentAction(
                action="skip_analysis",
                action_input={"reason": "insufficient_text"},
                reasoning=reasoning
            )
        
        # Check if sentiment analysis was already performed
        if state.sentiment_result is not None:
            reasoning = "Sentiment analysis already performed for this message"
            return AgentAction(
                action="use_existing",
                action_input={"existing_result": state.sentiment_result},
                reasoning=reasoning
            )
        
        # Determine if we need to analyze sentiment
        reasoning = f"Need to analyze sentiment for message: '{user_message[:50]}...'"
        return AgentAction(
            action="analyze_sentiment",
            action_input={"text": user_message},
            reasoning=reasoning
        )
    
    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Execute the determined action
        """
        try:
            if action.action == "skip_analysis":
                return AgentObservation(
                    observation="Skipped sentiment analysis due to insufficient text",
                    success=True,
                    data={
                        "sentiment_result": SentimentResult(
                            label=SentimentLabel.NEUTRAL,
                            confidence=0.0,
                            scores={},
                            reasoning="Skipped: insufficient text"
                        )
                    }
                )
            
            elif action.action == "use_existing":
                return AgentObservation(
                    observation="Using existing sentiment analysis result",
                    success=True,
                    data={"sentiment_result": action.action_input["existing_result"]}
                )
            
            elif action.action == "analyze_sentiment":
                text = action.action_input["text"]
                
                # Perform sentiment analysis
                sentiment_result = self.analyzer.analyze(text)
                
                # Save to database
                try:
                    self.db_manager.save_sentiment_result(
                        user_message=text,
                        sentiment_result=sentiment_result,
                        session_id=self.session_id
                    )
                    logger.info(f"Saved sentiment result to database: {sentiment_result.label}")
                except Exception as e:
                    logger.error(f"Failed to save sentiment result: {e}")
                
                return AgentObservation(
                    observation=f"Analyzed sentiment: {sentiment_result.label} (confidence: {sentiment_result.confidence:.3f})",
                    success=True,
                    data={"sentiment_result": sentiment_result}
                )
            
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        
        except Exception as e:
            logger.error(f"Error in SentimentAgent action: {e}")
            return AgentObservation(
                observation=f"Error during sentiment analysis: {str(e)}",
                success=False,
                data={}
            )
    
    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state based on action results
        """
        if observation.success and "sentiment_result" in observation.data:
            sentiment_result = observation.data["sentiment_result"]
            
            # Update state with sentiment result
            state.sentiment_result = sentiment_result
            
            # Add to metadata
            state.metadata.update({
                "sentiment_analysis_timestamp": datetime.utcnow().isoformat(),
                "sentiment_analyzer_type": self.analyzer_type,
                "sentiment_session_id": self.session_id
            })
            
            logger.info(f"Updated state with sentiment: {sentiment_result.label}")
        
        else:
            logger.warning(f"Sentiment analysis failed: {observation.observation}")
            # Set neutral sentiment as fallback
            state.sentiment_result = SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                scores={},
                reasoning="Fallback due to analysis failure"
            )
        
        return state
    
    def process(self, state: ChatbotState) -> ChatbotState:
        """
        Main processing method implementing ReAct pattern
        """
        logger.info(f"SentimentAgent processing message: {state.user_message[:50]}...")
        
        # Step 1: Reason
        action = self.reason(state)
        logger.debug(f"Reasoning: {action.reasoning}")
        
        # Step 2: Act
        observation = self.act(action)
        logger.debug(f"Action result: {observation.observation}")
        
        # Step 3: Observe and update state
        updated_state = self.observe(observation, state)
        
        return updated_state
    
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

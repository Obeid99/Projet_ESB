"""
Data models for ESB Chatbot System
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentResult(BaseModel):
    """Sentiment analysis result model"""
    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    scores: Dict[str, Any] = Field(default_factory=dict, description="Raw scores from different models")
    reasoning: Optional[str] = Field(default=None, description="Explanation of the sentiment classification")
    
    class Config:
        use_enum_values = True


class ChatbotState(BaseModel):
    """State model for LangGraph chatbot"""
    user_message: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    sentiment_result: Optional[SentimentResult] = None
    intent: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
    
    class Config:
        arbitrary_types_allowed = True


class SentimentRecord(Base):
    """Database model for storing sentiment analysis results"""
    __tablename__ = "sentiment_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_message = Column(Text, nullable=False)
    sentiment_label = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    scores = Column(Text, nullable=True)  # JSON string of scores
    reasoning = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<SentimentRecord(id={self.id}, label={self.sentiment_label}, confidence={self.confidence})>"


class AgentAction(BaseModel):
    """Model for agent actions in ReAct pattern"""
    action: str
    action_input: Dict[str, Any]
    reasoning: str
    
    
class AgentObservation(BaseModel):
    """Model for agent observations in ReAct pattern"""
    observation: str
    success: bool
    data: Optional[Dict[str, Any]] = None

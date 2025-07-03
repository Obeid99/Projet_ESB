"""
Database utilities for ESB Chatbot System
"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, SentimentRecord, SentimentResult
from .config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for sentiment records and other data"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def save_sentiment_result(
        self, 
        user_message: str, 
        sentiment_result: SentimentResult,
        session_id: Optional[str] = None
    ) -> SentimentRecord:
        """Save sentiment analysis result to database"""
        with self.get_session() as session:
            try:
                # Handle both enum and string labels
                if hasattr(sentiment_result.label, 'value'):
                    label_value = sentiment_result.label.value
                else:
                    label_value = str(sentiment_result.label)

                record = SentimentRecord(
                    user_message=user_message,
                    sentiment_label=label_value,
                    confidence=sentiment_result.confidence,
                    scores=json.dumps(sentiment_result.scores),
                    reasoning=sentiment_result.reasoning,
                    session_id=session_id,
                    timestamp=datetime.utcnow()
                )
                session.add(record)
                session.commit()
                session.refresh(record)
                logger.info(f"Saved sentiment record with ID: {record.id}")
                return record
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving sentiment result: {e}")
                raise
    
    def get_sentiment_history(
        self, 
        session_id: Optional[str] = None, 
        limit: int = 100
    ) -> List[SentimentRecord]:
        """Get sentiment analysis history"""
        with self.get_session() as session:
            try:
                query = session.query(SentimentRecord)
                if session_id:
                    query = query.filter(SentimentRecord.session_id == session_id)
                records = query.order_by(SentimentRecord.timestamp.desc()).limit(limit).all()
                return records
            except Exception as e:
                logger.error(f"Error retrieving sentiment history: {e}")
                return []
    
    def get_sentiment_stats(self, session_id: Optional[str] = None) -> dict:
        """Get sentiment statistics"""
        with self.get_session() as session:
            try:
                query = session.query(SentimentRecord)
                if session_id:
                    query = query.filter(SentimentRecord.session_id == session_id)
                
                total_count = query.count()
                positive_count = query.filter(SentimentRecord.sentiment_label == "positive").count()
                negative_count = query.filter(SentimentRecord.sentiment_label == "negative").count()
                neutral_count = query.filter(SentimentRecord.sentiment_label == "neutral").count()
                
                return {
                    "total": total_count,
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count,
                    "positive_ratio": positive_count / total_count if total_count > 0 else 0,
                    "negative_ratio": negative_count / total_count if total_count > 0 else 0,
                    "neutral_ratio": neutral_count / total_count if total_count > 0 else 0
                }
            except Exception as e:
                logger.error(f"Error calculating sentiment stats: {e}")
                return {}


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager

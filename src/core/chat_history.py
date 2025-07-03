"""
Chat history utility functions for storing and retrieving user chat history
"""
from src.core.models_db import ChatHistory, db

MAX_WORDS = 15000

# Store a message in chat history
def store_message(user_id, message, is_user):
    chat = ChatHistory(user_id=user_id, message=message, is_user=bool(is_user))
    db.session.add(chat)
    db.session.commit()

# Retrieve the last N words of chat history for a user (as a list of dicts)
def get_recent_history(user_id, max_words=MAX_WORDS):
    chats = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.asc()).all()
    history = []
    word_count = 0
    for chat in reversed(chats):
        words = len(chat.message.split())
        if word_count + words > max_words:
            break
        history.insert(0, {'message': chat.message, 'is_user': bool(chat.is_user), 'timestamp': chat.timestamp})
        word_count += words
    return history

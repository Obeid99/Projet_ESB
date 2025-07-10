"""
Chat history utility functions for storing and retrieving user chat history in MongoDB
"""
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_CHAT_STUD = os.getenv("MONGO_COLLECTION_CHAT_STUD")
client = MongoClient(MONGO_URI)
mongodb = client[MONGO_DB_NAME]

MAX_WORDS = 15000

# Store a message in chat history (MongoDB)
def store_message(user_id, message, is_user, username=None, sender=None, sentiment=None, intent=None):
    doc = {
        "user_id": user_id,
        "message": message,
        "is_user": bool(is_user),
        "timestamp": time.time()
    }
    if username:
        doc["username"] = username
    if sender:
        doc["sender"] = sender
    if sentiment:
        doc["sentiment"] = sentiment
    if intent:
        doc["intent"] = intent
    mongodb[MONGO_COLLECTION_CHAT_STUD].insert_one(doc)

# Retrieve the last N words of chat history for a user (as a list of dicts)
def get_recent_history(user_id, max_words=MAX_WORDS):
    chats = list(mongodb[MONGO_COLLECTION_CHAT_STUD].find({"user_id": user_id}).sort("timestamp", 1))
    history = []
    word_count = 0
    for chat in reversed(chats):
        words = len(chat["message"].split())
        if word_count + words > max_words:
            break
        history.insert(0, {
            'message': chat["message"],
            'is_user': bool(chat.get("is_user", True)),
            'timestamp': chat["timestamp"]
        })
        word_count += words
    return history

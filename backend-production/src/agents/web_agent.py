"""
WebAgent for ESB Chatbot System
Calls LLM for web information based on user message and intent
"""
import os
import requests
import json
import uuid
from typing import Optional
from ..core.models import ChatbotState
from pymongo import MongoClient
from dotenv import load_dotenv
from ..utils.esb_data import get_esb_data
from builtins import str, int, Exception, type, len, isinstance, list
import logging
class WebAgent:
    """
    WebAgent that gathers web info using Groq Llama 3.3 70B Versatile
    """
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())

    def process(self, state: ChatbotState) -> ChatbotState:
        api_key = os.getenv("GROQ_API_KEY")
        model = "llama-3.3-70b-versatile"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Load ESB program info from esb.json
        esb_data = get_esb_data()
        esb_summary = json.dumps(esb_data[:2], ensure_ascii=False)
        # Load ESB URLs from env
        ESB_WEBSITE_URL = os.getenv("ESB_WEBSITE_URL", "https://esprit.tn")
        ESB_FACEBOOK_URL = os.getenv("ESB_FACEBOOK_URL", "https://facebook.com/esprit.tn")
        prompt = (
            "You are an ESB (Esprit School of Business) assistant chatbot. Only answer questions that are about ESB, its programs, or its official information. "
            "If the user's message is not about ESB, politely respond that you can only assist with ESB-related questions. "
            "If the user's message requires web information, provide a JSON array of web_results. "
            "You can search the official ESB website (" + ESB_WEBSITE_URL + ") and Facebook page (" + ESB_FACEBOOK_URL + ") for relevant information. "
            "You have access to the following ESB program data (JSON):\n" + esb_summary + "\n"
            "Message: " + state.user_message
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
            web_info = json.loads(content)
            state.context["web_info"] = web_info if isinstance(web_info, list) else []
        except Exception as e:
            state.context["web_info"] = []
            state.context["web_info_error"] = str(e)
        return state

# Chat history saving in MongoDB
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_CHAT_STUD = os.getenv("MONGO_COLLECTION_CHAT_STUD")
client = MongoClient(MONGO_URI)
mongodb = client[MONGO_DB_NAME]

def save_chat_history(user_id, username, message, sender="student"):
    import time
    mongodb[MONGO_COLLECTION_CHAT_STUD].insert_one({
        "user_id": user_id,
        "username": username,
        "sender": sender,
        "message": message,
        "timestamp": time.time()
    })


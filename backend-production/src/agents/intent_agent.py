import os
from builtins import str, int, Exception, type, len, isinstance, list
from ..utils.esb_data import get_esb_data
from groq import Groq

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from ..core.models import ChatbotState, AgentAction, AgentObservation
from ..core.config import get_settings
from ..utils import retry_on_exception

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class IntentResult:
    def __init__(self, primary_intent, confidence, secondary_intents=None, entities=None, reasoning=""):
        self.primary_intent = primary_intent
        self.confidence = confidence
        self.secondary_intents = secondary_intents or []
        self.entities = entities or {}
        self.reasoning = reasoning

class IntentAgent:
    """
    IntentAgent that classifies user intent using Groq Llama 3.3 70B Versatile
    """
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
    def process(self, state: ChatbotState) -> ChatbotState:
        import json
        esb_data = get_esb_data()
        esb_summary = json.dumps(esb_data[:2], ensure_ascii=False)
        prompt = (
            "You are an ESB (Esprit School of Business) assistant chatbot. "
            "Classify the user's intent from the following message. "
            "Possible intents include (but are not limited to): 'greeting', 'out_of_scope', 'complaint', 'thanks', 'feedback', 'suggestion', 'ask_program_info', 'ask_admission', 'ask_schedule', 'ask_event', 'ask_facility', 'ask_general_info', 'request', 'question', or any other intent relevant to ESB or student life. "
            "Do not default to 'greeting' unless the message is only a greeting. "
            "If the message is not about ESB, its programs, or official information, respond with intent 'out_of_scope'. "
            "If the message is a complaint, suggestion, or feedback, classify it as such. "
            "You have access to the following ESB program data (JSON):\n" + esb_summary + "\n"
            "Respond ONLY with a JSON object: {\"intent\": \"intent_label\", \"confidence\": 0.0-1.0, \"reasoning\": \"brief explanation\"}. "
            "Here are some examples:\n"
            "Message: 'hello' -> {\"intent\": \"greeting\", ...}\n"
            "Message: 'thank you for your help' -> {\"intent\": \"thanks\", ...}\n"
            "Message: 'the wifi in the library is terrible' -> {\"intent\": \"complaint\", ...}\n"
            "Message: 'can you tell me about the MBA program?' -> {\"intent\": \"ask_program_info\", ...}\n"
            "Message: 'esb is awesome!' -> {\"intent\": \"feedback\", ...}\n"
            "Message: 'what is the weather in Paris?' -> {\"intent\": \"out_of_scope\", ...}\n"
            f"Message: {state.user_message}"
        )
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an ESB (esprit school of business) assistant agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            content = completion.choices[0].message.content
            intent = json.loads(content)
            state.intent = intent.get("intent", "out_of_scope")
            state.context["intent_confidence"] = intent.get("confidence", 1.0)
            state.context["intent_reasoning"] = intent.get("reasoning", "")
        except Exception as e:
            state.intent = "out_of_scope"
            state.context["intent_confidence"] = 0.0
            state.context["intent_error"] = str(e)
        return state

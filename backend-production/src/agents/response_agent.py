# response_agent.py (or in web_interface.py if preferred)

import logging
from typing import Optional, List
import json
import os

from groq import Groq

from ..agents.intent_agent import IntentAgent
from ..agents.web_agent import WebAgent
from ..core.models import ChatbotState
from ..utils import retry_on_exception
from ..utils.esb_data import get_esb_data

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def _format_llm_context(state):
    import json
    # Prefer web_info from state, fallback to get_esb_data only if not present
    web_info = state.context.get("web_info", [])
    esb_programs = None
    # If web_info contains program data, use it; else fallback
    if web_info and isinstance(web_info, list) and any(isinstance(item, dict) and "title" in item for item in web_info):
        esb_programs = web_info
    else:
        esb_programs = get_esb_data()
    context = {
        "intent": state.intent,
        "entities": state.context.get("intent_entities", {}),
        "sentiment": state.context.get("sentiment_label", ""),
        "web_info": web_info,
        "user_message": state.user_message,
        "session_id": state.session_id,
        "reasoning": state.context.get("intent_reasoning", ""),
        "conversation_history": state.conversation_history,
        "esb_programs": esb_programs,
    }
    return json.dumps(context, ensure_ascii=False)

@retry_on_exception((Exception,), tries=3, delay=2, backoff=2, logger=logger)
def _call_llm_response(state):
    # Use conversation history for context
    history = state.conversation_history[-6:] if len(state.conversation_history) > 6 else state.conversation_history[:]
    logger.info(f"Raw conversation history from state: {json.dumps(state.conversation_history, ensure_ascii=False)}")
    # Add the latest user message if not already present
    if not history or history[-1].get("content") != state.user_message:
        history.append({"role": "user", "content": state.user_message})
    logger.info(f"Conversation history for LLM (last 6 + user): {json.dumps(history, ensure_ascii=False)}")
    prompt = (
        "You are an ESB school assistant chatbot. "
        "Given the following conversation history and context as JSON, generate a helpful, natural, and context-aware response for the user. "
        "Do not use templates or fallback phrases. Only use the information provided.\n"
        f"Context: {_format_llm_context(state)}\n"
        "Conversation history: " + json.dumps(history, ensure_ascii=False) + "\n"
        "Response:"
    )
    logger.info(f"Prompt sent to LLM: {prompt}")
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an ESB (esprit school of business) assistant agent."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return completion.choices[0].message.content.strip()

def generate_response(user_input, session_id=None):
    """
    Main chatbot response pipeline: Intent → Web info → LLM response generation.
    """
    # Retrieve existing conversation history for the session if available
    # This assumes you have a way to persist and retrieve history, e.g., a global/session store or database
    # For demonstration, we'll use a simple in-memory store. Replace with your actual persistence logic.
    global _chat_sessions
    try:
        _chat_sessions
    except NameError:
        _chat_sessions = {}

    history = _chat_sessions.get(session_id, []) if session_id else []
    state = ChatbotState(user_message=user_input.strip(), session_id=session_id, conversation_history=history)

    # Step 1: Intent Detection
    intent_agent = IntentAgent()
    state = intent_agent.process(state)
    logger.info(f"Detected intent: {state.intent}")

    # Step 2: Web Info (if relevant intent)
    if state.intent in [
        "registration_help", "event_info", "facility_info",
        "general_info", "course_info", "schedule_inquiry"
    ]:
        web_agent = WebAgent(session_id=session_id)
        state = web_agent.process(state)

    # Step 3: LLM Response Generation (no templates, no fallback)
    llm_response = _call_llm_response(state)
    # Add LLM response to conversation history for turnover
    state.add_to_history("system", llm_response)
    # Save updated history for the session
    if session_id:
        _chat_sessions[session_id] = state.conversation_history
    return llm_response

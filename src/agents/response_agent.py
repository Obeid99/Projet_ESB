# response_agent.py (or in web_interface.py if preferred)

import logging
from typing import Optional, List
import json

from ..agents.intent_agent import IntentAgent
from ..agents.web_agent import WebAgent
from ..core.models import ChatbotState
from ..utils import retry_on_exception

logger = logging.getLogger(__name__)

def _format_llm_context(state):
    """Format all relevant state/context for LLM prompt."""
    context = {
        "intent": state.intent,
        "entities": state.context.get("intent_entities", {}),
        "sentiment": state.context.get("sentiment_label", ""),
        "web_info": state.context.get("web_info", []),
        "user_message": state.user_message,
        "session_id": state.session_id,
        "reasoning": state.context.get("intent_reasoning", ""),
        # Add conversation history for turnover
        "conversation_history": state.conversation_history,
    }
    return json.dumps(context, ensure_ascii=False)

@retry_on_exception((Exception,), tries=3, delay=2, backoff=2, logger=logger)
def _call_llm_response(state):
    import os
    os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    import ollama
    # Use conversation history for context
    history = state.conversation_history[-6:] if len(state.conversation_history) > 6 else state.conversation_history[:]
    # Add the latest user message if not already present
    if not history or history[-1].get("content") != state.user_message:
        history.append({"role": "user", "content": state.user_message})
    prompt = (
        "You are an ESB: esprit school of business assistant chatbot. "
        "if the question isn't related to esprit school of business do not answer."
        "Given the following conversation history and context as JSON, generate a helpful, natural, and context-aware response for the user. "
        "Do not use templates or fallback phrases. Only use the information provided.\n"
        f"Context: {_format_llm_context(state)}\n"
        "Conversation history: " + json.dumps(history, ensure_ascii=False) + "\n"
        "Response:"
    )
    response = ollama.chat(model="llama3.1:8b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content'].strip()

def generate_response(user_input, session_id=None):
    """
    Main chatbot response pipeline: Intent → Web info → LLM response generation.
    """
    # Initialize chatbot state
    state = ChatbotState(user_message=user_input.strip(), session_id=session_id)

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
    return llm_response

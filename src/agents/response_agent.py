# response_agent.py (or in web_interface.py if preferred)

import logging
from typing import Optional

from ..agents.intent_agent import IntentAgent
from ..agents.web_agent import WebAgent
from ..core.models import ChatbotState

logger = logging.getLogger(__name__)

def generate_response(user_input: str, session_id: Optional[str] = None) -> str:
    """
    Main chatbot response pipeline: Intent → Web info → Response generation.
    """
    # Initialize chatbot state
    state = ChatbotState(user_message=user_input.strip(), session_id=session_id)

    # Step 1: Intent Detection
    intent_agent = IntentAgent()
    state = intent_agent.process(state)
    intent = state.intent
    logger.info(f"Detected intent: {intent}")

    # Step 2: Web Info (if relevant intent)
    if intent in [
        "registration_help", "event_info", "facility_info",
        "general_info", "course_info", "schedule_inquiry"
    ]:
        web_agent = WebAgent(session_id=session_id)
        state = web_agent.process(state)

    # Step 3: Response Generation
    web_info = state.context.get("web_info", [])
    confidence = state.context.get("intent_confidence", 0.0)
    reasoning = state.context.get("intent_reasoning", "No reasoning provided.")

    # 🔹 Examples of response patterns
    # Handle negative sentiment or complaint about a course (e.g., "I hate maths")
    intent_entities = state.context.get("intent_entities", {})
    sentiment = state.context.get("sentiment_label", "")
    # Try to extract course name from user input if not present in entities
    def extract_course_name(text):
        course_keywords = [
            "math", "mathematics", "maths", "algebra", "geometry", "calculus", "statistics", "trigonometry", "probability", "equation", "formule", "cours", "professeur"
        ]
        for word in course_keywords:
            if word in text.lower():
                return word
        return None

    if intent == "course_info":
        if intent_entities.get("negative_course") or sentiment == "NEGATIVE":
            course_name = intent_entities.get("course")
            if not course_name:
                course_name = extract_course_name(user_input)
            if course_name:
                return f"I'm sorry to hear you're having trouble with {course_name}. Would you like help finding a support contact, tutoring, or academic resources?"
            return "I'm sorry you're having trouble with a course. Would you like help finding a support contact, tutoring, or academic resources?"
        return "Let me help you with course information. Do you need schedules, instructors, or course materials?"

    elif intent == "event_info":
        if web_info:
            return f"I found {len(web_info)} event(s):\n" + "\n".join(
                f"- {item['title']} ({item['url']})" for item in web_info
            )
        return "I couldn't find any current events. Try checking the ESB website or Facebook page."

    elif intent == "registration_help":
        if web_info:
            top = web_info[0]
            return f"Here's something that might help with registration:\n“{top['title']}” – {top['content']}\nMore info: {top['url']}"
        return "I didn’t find current registration details. Would you like to speak to the registrar’s office?"

    elif intent == "facility_info":
        if web_info:
            return f"I found information about ESB facilities:\n" + "\n".join(
                f"- {item['title']}: {item['content'][:100]}..." for item in web_info
            )
        return "Sorry, I couldn’t find updated information on facilities. Try asking about a specific place (library, cafeteria, etc.)."

    elif intent == "general_info" and web_info:
        return f"Here's something general I found:\n“{web_info[0]['title']}”\n{web_info[0]['content']}\n{web_info[0]['url']}"

    elif intent == "complaint":
        return "I'm here to listen. Could you describe the problem in more detail so I can help or pass it along?"

    elif intent == "appreciation":
        return "Thank you! Your kind words mean a lot 😊"

    elif intent == "unclear":
        return "I'm not sure I understood. Could you try rephrasing your question or being more specific?"

    # Default fallback
    return "I'm still learning. Could you clarify or ask in a different way?"

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import re

from ..core.models import ChatbotState, AgentAction, AgentObservation
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class IntentCategory(str, Enum):
    REGISTRATION_HELP = "registration_help"
    GRADE_INQUIRY = "grade_inquiry"
    COURSE_INFO = "course_info"
    SCHEDULE_INQUIRY = "schedule_inquiry"
    ACADEMIC_SUPPORT = "academic_support"
    FINANCIAL_INQUIRY = "financial_inquiry"
    DOCUMENT_REQUEST = "document_request"
    FACILITY_INFO = "facility_info"
    CONTACT_INFO = "contact_info"
    TECHNICAL_SUPPORT = "technical_support"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    APPRECIATION = "appreciation"
    GENERAL_INFO = "general_info"
    EVENT_INFO = "event_info"
    CAREER_GUIDANCE = "career_guidance"
    SOCIAL_INTERACTION = "social_interaction"
    PERSONAL_SHARING = "personal_sharing"
    UNCLEAR = "unclear"

class IntentResult:
    def __init__(self, primary_intent: IntentCategory, confidence: float, secondary_intents: List[IntentCategory] = None, entities: Dict[str, Any] = None, reasoning: str = ""):
        self.primary_intent = primary_intent
        self.confidence = confidence
        self.secondary_intents = secondary_intents or []
        self.entities = entities or {}
        self.reasoning = reasoning

class IntentAgent:
    def __init__(self, use_ollama: bool = True, session_id: Optional[str] = None):
        self.settings = get_settings()
        self.use_ollama = use_ollama
        self.session_id = session_id or str(uuid.uuid4())
        self.ollama_available = False

        if use_ollama:
            try:
                import ollama
                ollama.list()
                self.ollama_available = True
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")

        self.intent_keywords = {
            IntentCategory.COURSE_INFO: ["math", "mathematics", "maths", "algebra", "geometry", "calculus", "statistics", "trigonometry", "probability", "equation", "formule", "cours", "professeur"],
            IntentCategory.COMPLAINT: ["don't like", "dont like", "do not like", "dislike", "hate", "can't stand", "detest", "loathe", "problem", "issue", "bad", "terrible", "useless", "frustrated", "upset"]
            # Add other intents as needed...
        }

    def reason(self, state: ChatbotState) -> AgentAction:
        user_message = state.user_message.strip()
        if not user_message or len(user_message) < 3:
            return AgentAction(action="skip_intent_detection", action_input={"reason": "too short"}, reasoning="Too short")
        if state.intent:
            return AgentAction(action="use_existing_intent", action_input={"existing_intent": state.intent}, reasoning="Already exists")

        word_count = len(user_message.split())
        if word_count > 5 and self.ollama_available:
            return AgentAction(action="llm_intent_detection", action_input={"text": user_message}, reasoning="Using LLM")
        return AgentAction(action="keyword_intent_detection", action_input={"text": user_message}, reasoning="Using keyword")

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        contractions = {
            "don't": "do not", "dont": "do not", "can't": "cannot", "cant": "cannot", "i'm": "i am"
        }
        for k, v in contractions.items():
            text = re.sub(r'\\b' + re.escape(k) + r'\\b', v, text)
        return text

    def act(self, action: AgentAction) -> AgentObservation:
        try:
            if action.action == "skip_intent_detection":
                return AgentObservation(observation="Skipped", success=True, data={"intent_result": IntentResult(IntentCategory.UNCLEAR, 0.0, reasoning="Skipped")})
            elif action.action == "use_existing_intent":
                return AgentObservation(observation="Using existing", success=True, data={"intent_result": IntentResult(IntentCategory(action.action_input["existing_intent"]), 1.0, reasoning="Pre-existing")})
            elif action.action == "keyword_intent_detection":
                return self._keyword_intent_detection(action.action_input["text"])
            elif action.action == "llm_intent_detection":
                return self._llm_intent_detection(action.action_input["text"])
            else:
                return AgentObservation(observation="Unknown action", success=False, data={})
        except Exception as e:
            logger.error(f"Error: {e}")
            return AgentObservation(observation="Error", success=False, data={})

    def _keyword_intent_detection(self, text: str) -> AgentObservation:
        text_lower = self.normalize_text(text)
        is_negative = any(kw in text_lower for kw in self.intent_keywords[IntentCategory.COMPLAINT])
        is_course = any(kw in text_lower for kw in self.intent_keywords[IntentCategory.COURSE_INFO])

        if is_negative and is_course:
            intent_result = IntentResult(
                primary_intent=IntentCategory.COURSE_INFO,
                confidence=0.9,
                secondary_intents=[IntentCategory.COMPLAINT],
                entities={"negative_course": True},
                reasoning="Detected negative sentiment about a course."
            )
        else:
            intent_result = IntentResult(
                primary_intent=IntentCategory.GENERAL_INFO,
                confidence=0.3,
                reasoning="Defaulted to general info"
            )
        return AgentObservation(observation=f"Detected: {intent_result.primary_intent}", success=True, data={"intent_result": intent_result})

    def _llm_intent_detection(self, text: str) -> AgentObservation:
        if not self.ollama_available:
            return self._keyword_intent_detection(text)
        try:
            import ollama
            import json
            prompt = f"What is the user's intent in this message: '{text}'? Respond in JSON."
            response = ollama.chat(model=self.settings.ollama_model, messages=[{"role": "user", "content": prompt}])
            result = json.loads(response['message']['content'])
            intent_result = IntentResult(
                primary_intent=IntentCategory(result['primary_intent']),
                confidence=float(result['confidence']),
                reasoning=result.get("reasoning", "LLM analysis")
            )
            return AgentObservation(observation="LLM detected", success=True, data={"intent_result": intent_result})
        except Exception as e:
            logger.warning(f"LLM fallback: {e}")
            return self._keyword_intent_detection(text)

    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        if observation.success and "intent_result" in observation.data:
            intent_result = observation.data["intent_result"]
            state.intent = intent_result.primary_intent.value
            state.context.update({
                "intent_confidence": intent_result.confidence,
                "secondary_intents": [i.value for i in intent_result.secondary_intents],
                "intent_entities": intent_result.entities,
                "intent_reasoning": intent_result.reasoning
            })
            state.metadata.update({
                "intent_analysis_timestamp": datetime.utcnow().isoformat(),
                "intent_session_id": self.session_id,
                "intent_method": "llm" if self.ollama_available else "keyword"
            })
        else:
            state.intent = IntentCategory.UNCLEAR.value
            state.context.update({"intent_confidence": 0.0, "intent_reasoning": "Detection failed"})
        return state

    def process(self, state: ChatbotState) -> ChatbotState:
        action = self.reason(state)
        observation = self.act(action)
        return self.observe(observation, state)

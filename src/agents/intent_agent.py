import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from ..core.models import ChatbotState, AgentAction, AgentObservation
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class IntentResult:
    def __init__(self, primary_intent: str, confidence: float, secondary_intents: List[str] = None, entities: Dict[str, Any] = None, reasoning: str = ""):
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

    def reason(self, state: ChatbotState) -> AgentAction:
        user_message = state.user_message.strip()
        if not user_message or len(user_message) < 3:
            return AgentAction(action="skip_intent_detection", action_input={"reason": "too short"}, reasoning="Too short")
        if state.intent:
            return AgentAction(action="use_existing_intent", action_input={"existing_intent": state.intent}, reasoning="Already exists")
        # Always use LLM for intent detection
        return AgentAction(action="llm_intent_detection", action_input={"text": user_message}, reasoning="Using LLM")

    def act(self, action: AgentAction) -> AgentObservation:
        try:
            if action.action == "skip_intent_detection":
                return AgentObservation(observation="Skipped", success=True, data={"intent_result": IntentResult("unclear", 0.0, reasoning="Skipped")})
            elif action.action == "use_existing_intent":
                return AgentObservation(observation="Using existing", success=True, data={"intent_result": IntentResult(action.action_input["existing_intent"], 1.0, reasoning="Pre-existing")})
            elif action.action == "llm_intent_detection":
                return self._llm_intent_detection(action.action_input["text"])
            else:
                return AgentObservation(observation="Unknown action", success=False, data={})
        except Exception as e:
            logger.error(f"Error: {e}")
            return AgentObservation(observation="LLM intent detection failed", success=False, data={"error": str(e)})

    def _llm_intent_detection(self, text: str) -> AgentObservation:
        try:
            import ollama
            import json
            prompt = (
                "What is the user's intent in this message: '" + text + "'? "
                "Respond ONLY with a flat JSON object like: "
                "{\"primary_intent\": <intent>, \"confidence\": <float>, \"secondary_intents\": [<str>], \"entities\": {<key>: <value>}, \"reasoning\": <str>}"
            )
            response = ollama.chat(model=self.settings.ollama_model, messages=[{"role": "user", "content": prompt}])
            raw = response['message']['content']
            print("LLM raw response:", raw)
            # Remove markdown code block formatting if present
            if '```' in raw:
                raw = raw.split('```')[1] if len(raw.split('```')) > 1 else raw
                raw = raw.strip()
            # Try to parse as JSON
            result = json.loads(raw)
            # If nested intent, flatten
            if 'intent' in result and isinstance(result['intent'], dict):
                intent = result['intent']
                primary_intent = intent.get('type', 'unclear')
                secondary_intents = intent.get('subtypes', [])
                entities = intent.get('entities', {})
            else:
                primary_intent = result.get('primary_intent', 'unclear')
                secondary_intents = result.get('secondary_intents', [])
                entities = result.get('entities', {})
            confidence = float(result.get('confidence', 1.0))
            reasoning = result.get('reasoning', "LLM analysis")
            intent_result = IntentResult(
                primary_intent=primary_intent,
                confidence=confidence,
                secondary_intents=secondary_intents,
                entities=entities,
                reasoning=reasoning
            )
            return AgentObservation(observation="LLM detected", success=True, data={"intent_result": intent_result})
        except Exception as e:
            logger.error(f"LLM intent detection failed: {e}")
            return AgentObservation(observation="LLM intent detection failed", success=False, data={"error": str(e)})

    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        if observation.success and "intent_result" in observation.data:
            intent_result = observation.data["intent_result"]
            state.intent = intent_result.primary_intent
            state.context.update({
                "intent_confidence": intent_result.confidence,
                "secondary_intents": intent_result.secondary_intents,
                "intent_entities": intent_result.entities,
                "intent_reasoning": intent_result.reasoning
            })
            state.metadata.update({
                "intent_analysis_timestamp": datetime.utcnow().isoformat(),
                "intent_session_id": self.session_id,
                "intent_method": "llm"
            })
        else:
            state.intent = "unclear"
            state.context.update({
                "intent_confidence": 0.0,
                "intent_reasoning": observation.data.get("error", "LLM intent detection failed")
            })
        return state

    def process(self, state: ChatbotState) -> ChatbotState:
        action = self.reason(state)
        observation = self.act(action)
        return self.observe(observation, state)

import builtins
Exception = builtins.Exception
isinstance = builtins.isinstance
dict = builtins.dict
float = builtins.float
str = builtins.str

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from ..core.models import ChatbotState, AgentAction, AgentObservation
from ..core.config import get_settings
from ..utils import retry_on_exception

logger = logging.getLogger(__name__)

class IntentResult:
    def __init__(self, primary_intent, confidence, secondary_intents=None, entities=None, reasoning=""):
        self.primary_intent = primary_intent
        self.confidence = confidence
        self.secondary_intents = secondary_intents or []
        self.entities = entities or {}
        self.reasoning = reasoning

class IntentAgent:
    def __init__(self, use_ollama=True, session_id=None):
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

    @retry_on_exception((Exception,), tries=3, delay=2, backoff=2, logger=logger)
    def _llm_intent_detection(self, text) -> AgentObservation:
        try:
            import os
            os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            import ollama
            import json
            # Use the full conversation history from the global ChatbotState
            if hasattr(self, 'state') and self.state and hasattr(self.state, 'conversation_history'):
                full_history = self.state.conversation_history[:]
            else:
                full_history = []
            # Add the latest user message if not already present
            if not full_history or full_history[-1].get("content") != text:
                full_history.append({"role": "user", "content": text})
            # Limit to last 10 turns for LLM stability
            history_to_use = full_history[-10:]
            # Inject system_prompt from state.context into the LLM prompt for intent detection, if present.
            system_prompt = self.state.context.get('system_prompt')
            # Format as readable transcript
            transcript = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}" for msg in history_to_use
            ])
            prompt = (
                (system_prompt + "\n" if system_prompt else "") +
                "Given the following conversation transcript, what is the user's intent? "
                "Return a JSON object with these fields: primary_intent, confidence (0-1), secondary_intents (list), entities (dict), and reasoning."
                f"\nTranscript:\n{transcript}\n"
                "Respond with valid JSON only."
            )
            logger.info(f"LLM intent prompt: {prompt}")
            ollama_messages = [
                {"role": "user", "content": prompt}
            ]
            response = ollama.chat(model=self.settings.ollama_model, messages=ollama_messages)
            raw = response['message']['content']
            logger.info(f"LLM raw response: {raw!r}")
            if not raw.strip():
                # Fallback: try a minimal prompt
                fallback_prompt = (
                    (system_prompt + "\n" if system_prompt else "") +
                    f"What is the user's intent in this conversation?\nTranscript:\n{transcript}\nRespond with a JSON object."
                )
                logger.warning("LLM returned empty response, retrying with fallback prompt.")
                ollama_messages = [
                    {"role": "user", "content": fallback_prompt}
                ]
                response = ollama.chat(model=self.settings.ollama_model, messages=ollama_messages)
                raw = response['message']['content']
                logger.info(f"LLM fallback raw response: {raw!r}")
            if '```' in raw:
                raw = raw.replace('```json', '').replace('```', '').strip()
            raw = raw.strip()
            if not raw:
                logger.warning("LLM returned empty response for intent detection.")
                return AgentObservation(observation="LLM returned empty response", success=False, data={"intent_result": IntentResult("unclear", 0.0, reasoning="Empty LLM response")})
            try:
                result = json.loads(raw)
            except Exception as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}. Raw: {raw!r}")
                return AgentObservation(observation="LLM returned invalid JSON", success=False, data={"intent_result": IntentResult("unclear", 0.0, reasoning="Invalid LLM JSON")})
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
        # Ensure the agent has access to the full conversation history
        self.state = state
        # Add user message to conversation history
        state.add_to_history("user", state.user_message)
        action = self.reason(state)
        observation = self.act(action)
        # If intent detected, add to history as system message
        if observation.success and "intent_result" in observation.data:
            intent_result = observation.data["intent_result"]
            state.add_to_history("system", f"Intent detected: {intent_result.primary_intent}")
        return self.observe(observation, state)

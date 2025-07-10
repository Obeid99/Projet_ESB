"""
SelfReflectionAgent for ESB Chatbot System
Encourages student problem-solving and self-reflection using ReAct pattern
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from ..core.models import (
    ChatbotState,
    SentimentLabel,
    AgentAction,
    AgentObservation
)
from ..core.config import get_settings
from ..utils import retry_on_exception

logger = logging.getLogger(__name__)


class ReflectionType(str, Enum):
    """Types of self-reflection prompts"""
    PROBLEM_SOLVING = "problem_solving"
    GOAL_SETTING = "goal_setting"
    LEARNING_REFLECTION = "learning_reflection"
    EMOTIONAL_PROCESSING = "emotional_processing"
    DECISION_MAKING = "decision_making"
    NONE = "none"


class ReflectionPrompt:
    """Self-reflection prompt structure"""
    def __init__(
        self,
        reflection_type: ReflectionType,
        prompt_text: str,
        follow_up_questions: List[str] = None,
        guidance: str = ""
    ):
        self.reflection_type = reflection_type
        self.prompt_text = prompt_text
        self.follow_up_questions = follow_up_questions or []
        self.guidance = guidance


class SelfReflectionAgent:
    """
    SelfReflectionAgent that encourages student self-reflection and problem-solving
    Follows ReAct pattern: Reason -> Act -> Observe
    """
    
    def __init__(
        self, 
        session_id: Optional[str] = None
    ):
        self.settings = get_settings()
        self.session_id = session_id or str(uuid.uuid4())
        
        # Reflection prompts for different scenarios
        self.reflection_prompts = self._initialize_reflection_prompts()
        
        # Intents that benefit from self-reflection
        self.reflection_worthy_intents = [
            "complaint",
            "academic_support", 
            "career_guidance",
            "personal_sharing",
            "decision_making"
        ]
        
        logger.info(f"SelfReflectionAgent initialized, session: {self.session_id}")
    
    def _initialize_reflection_prompts(self) -> Dict[str, Dict[str, ReflectionPrompt]]:
        """No-op: LLM handles all reflection prompts now."""
        return {}
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Determine if self-reflection would be beneficial
        """
        sentiment = str(state.sentiment_result.label) if state.sentiment_result else "neutral"
        intent = state.intent or "general_info"
        user_message = state.user_message.strip()
        
        # Check if reflection was already provided
        if state.context.get("reflection_prompt"):
            reasoning = "Self-reflection prompt already provided"
            return AgentAction(
                action="skip_reflection",
                action_input={"reason": "already_provided"},
                reasoning=reasoning
            )
        
        # Check if message is too short for meaningful reflection
        if len(user_message) < 10:
            reasoning = "Message too short for meaningful self-reflection"
            return AgentAction(
                action="skip_reflection",
                action_input={"reason": "insufficient_content"},
                reasoning=reasoning
            )
        
        # Check if intent benefits from reflection
        if intent not in self.reflection_worthy_intents:
            reasoning = f"Intent '{intent}' doesn't typically benefit from self-reflection"
            return AgentAction(
                action="skip_reflection",
                action_input={"reason": "intent_not_suitable"},
                reasoning=reasoning
            )
        
        # Check sentiment confidence - only provide reflection for clear sentiments
        sentiment_confidence = state.context.get("sentiment_confidence", 0)
        if sentiment_confidence < 0.5:
            reasoning = f"Sentiment confidence too low ({sentiment_confidence:.2f}) for targeted reflection"
            return AgentAction(
                action="skip_reflection",
                action_input={"reason": "low_confidence"},
                reasoning=reasoning
            )
        
        # Provide appropriate reflection
        reasoning = f"Providing {sentiment} reflection for {intent} intent"
        return AgentAction(
            action="provide_reflection",
            action_input={
                "sentiment": sentiment,
                "intent": intent,
                "user_message": user_message
            },
            reasoning=reasoning
        )
    
    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Generate reflection prompt or skip
        """
        try:
            if action.action == "skip_reflection":
                return AgentObservation(
                    observation=f"Skipped self-reflection: {action.action_input['reason']}",
                    success=True,
                    data={"reflection_provided": False}
                )
            
            elif action.action == "provide_reflection":
                return self._generate_reflection_prompt(action.action_input)
            
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        
        except Exception as e:
            logger.error(f"Error in SelfReflectionAgent action: {e}")
            return AgentObservation(
                observation=f"Error during reflection generation: {str(e)}",
                success=False,
                data={}
            )
    
    def _generate_reflection_prompt(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Generate reflection prompt using LLM only (no static templates)"""
        llm_result = self._call_llm(action_input)
        if not llm_result or not llm_result.get("reflection_prompt"):
            return AgentObservation(
                observation="LLM did not return a reflection prompt",
                success=False,
                data={"reflection_provided": False}
            )
        return AgentObservation(
            observation="Generated reflection prompt via LLM",
            success=True,
            data={
                "reflection_provided": True,
                "reflection_prompt": llm_result["reflection_prompt"],
                "reflection_type": llm_result.get("reflection_type", "unknown")
            }
        )

    @retry_on_exception((Exception,), tries=3, delay=2, backoff=2, logger=logger)
    def _call_llm(self, action_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM for self-reflection prompt (placeholder, replace with actual LLM call)"""
        system_prompt = action_input.get('system_prompt')
        prompt = (
            (system_prompt + "\n" if system_prompt else "") +
            f"You are an ESB school assistant chatbot. Generate a self-reflection prompt for the following user message: '{action_input.get('user_message', '')}'. Respond with a JSON object containing a reflection_prompt."
        )
        import os
        os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        import ollama
        response = ollama.chat(model=self.settings.ollama_model, messages=[{"role": "user", "content": prompt}])
        # Parse response as needed
        # For now, fallback to placeholder if LLM fails
        try:
            reflection_prompt = response['message']['content']
            import json
            reflection_prompt = json.loads(reflection_prompt)
        except Exception:
            reflection_prompt = {
                "intro": "Let's reflect together.",
                "main_prompt": f"Based on your message: '{action_input.get('user_message', '')}', what are your thoughts?",
                "questions": ["What stands out to you?", "What would you like to change?"],
                "guidance": "Take your time to think it through.",
                "type": "llm_generated"
            }
        return {"reflection_prompt": reflection_prompt, "reflection_type": "llm_generated"}
    
    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state with reflection prompt
        """
        if observation.success and observation.data.get("reflection_provided"):
            reflection_data = observation.data
            
            # Add reflection prompt to context
            state.context.update({
                "reflection_prompt": reflection_data.get("reflection_prompt"),
                "reflection_type": reflection_data.get("reflection_type"),
                "reflection_timestamp": datetime.utcnow().isoformat()
            })
            
            # Add to metadata
            state.metadata.update({
                "self_reflection_agent_session_id": self.session_id,
                "reflection_provided": True,
                "reflection_type": reflection_data.get("reflection_type")
            })
            
            logger.info(f"Added {reflection_data.get('reflection_type')} reflection prompt")
        
        else:
            logger.debug(f"No reflection provided: {observation.observation}")
            state.context.update({
                "reflection_provided": False,
                "reflection_skip_reason": observation.observation
            })
            state.metadata.update({
                "reflection_provided": False
            })
        
        return state
    
    def process(self, state: ChatbotState) -> ChatbotState:
        """
        Main processing method implementing ReAct pattern
        """
        logger.info(f"SelfReflectionAgent processing message: {state.user_message[:50]}...")
        
        # Step 1: Reason
        action = self.reason(state)
        logger.debug(f"Reasoning: {action.reasoning}")
        
        # Step 2: Act
        observation = self.act(action)
        logger.debug(f"Action result: {observation.observation}")
        
        # Step 3: Observe and update state
        updated_state = self.observe(observation, state)
        
        return updated_state
    
    def _get_reflection_prompt(self, sentiment: str, intent: str) -> Optional[ReflectionPrompt]:
        """No-op: LLM handles all reflection prompts now."""
        return None

    def _customize_prompt(self, prompt: ReflectionPrompt, user_message: str) -> Dict[str, Any]:
        """No-op: LLM handles all customization now."""
        return {}


# LangGraph integration functions
def create_self_reflection_node():
    """
    Factory function to create a self-reflection node for LangGraph
    """
    def self_reflection_node(state: ChatbotState) -> ChatbotState:
        """LangGraph node function for self-reflection"""
        agent = SelfReflectionAgent(
            session_id=state.metadata.get("session_id")
        )
        return agent.process(state)
    
    return self_reflection_node


def should_provide_reflection(state: ChatbotState) -> bool:
    """
    Conditional function for LangGraph to determine if self-reflection should be provided
    """
    return (
        state.sentiment_result is not None and
        state.intent is not None and
        "reflection_prompt" not in state.context and
        state.context.get("sentiment_confidence", 0) >= 0.5
    )

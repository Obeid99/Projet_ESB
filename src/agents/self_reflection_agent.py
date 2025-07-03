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
        """Initialize reflection prompts for different scenarios"""
        return {
            "negative": {
                "complaint": ReflectionPrompt(
                    reflection_type=ReflectionType.PROBLEM_SOLVING,
                    prompt_text="I understand this situation is frustrating. Let's think through this together:",
                    follow_up_questions=[
                        "What specific aspect of this situation bothers you most?",
                        "Have you encountered similar challenges before? How did you handle them?",
                        "What would an ideal solution look like to you?",
                        "What steps could you take to address this issue?"
                    ],
                    guidance="Sometimes breaking down a problem helps us find better solutions."
                ),
                "academic_support": ReflectionPrompt(
                    reflection_type=ReflectionType.LEARNING_REFLECTION,
                    prompt_text="Academic challenges can be tough, but they're also opportunities for growth:",
                    follow_up_questions=[
                        "What specific part of this subject/course is most challenging?",
                        "What study methods have you tried so far?",
                        "When do you feel most confident in your learning?",
                        "What resources or support might help you succeed?"
                    ],
                    guidance="Reflecting on your learning process can help identify the best strategies for you."
                )
            },
            "neutral": {
                "career_guidance": ReflectionPrompt(
                    reflection_type=ReflectionType.GOAL_SETTING,
                    prompt_text="Career planning is an exciting journey of self-discovery:",
                    follow_up_questions=[
                        "What activities or subjects energize you most?",
                        "What kind of impact do you want to make in your career?",
                        "What skills do you feel confident about?",
                        "What areas would you like to develop further?"
                    ],
                    guidance="Understanding yourself is the first step to finding a fulfilling career path."
                ),
                "decision_making": ReflectionPrompt(
                    reflection_type=ReflectionType.DECISION_MAKING,
                    prompt_text="Making important decisions can feel overwhelming. Let's explore this thoughtfully:",
                    follow_up_questions=[
                        "What are the main options you're considering?",
                        "What factors are most important to you in this decision?",
                        "What are your concerns about each option?",
                        "How does each option align with your long-term goals?"
                    ],
                    guidance="Good decisions come from understanding both your options and your values."
                )
            },
            "positive": {
                "appreciation": ReflectionPrompt(
                    reflection_type=ReflectionType.LEARNING_REFLECTION,
                    prompt_text="It's wonderful to hear about your positive experience! Let's reflect on what made it special:",
                    follow_up_questions=[
                        "What specific aspects contributed to this positive experience?",
                        "How can you apply what you learned to other situations?",
                        "What does this success tell you about your strengths?",
                        "How might you help others have similar positive experiences?"
                    ],
                    guidance="Reflecting on positive experiences helps us understand what works well for us."
                )
            }
        }
    
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
        """Generate appropriate reflection prompt"""
        sentiment = action_input["sentiment"]
        intent = action_input["intent"]
        user_message = action_input["user_message"]
        
        # Get appropriate reflection prompt
        reflection_prompt = self._get_reflection_prompt(sentiment, intent)
        
        if not reflection_prompt:
            return AgentObservation(
                observation="No suitable reflection prompt found",
                success=True,
                data={"reflection_provided": False}
            )
        
        # Customize prompt based on user message
        customized_prompt = self._customize_prompt(reflection_prompt, user_message)
        
        return AgentObservation(
            observation=f"Generated {reflection_prompt.reflection_type} reflection prompt",
            success=True,
            data={
                "reflection_provided": True,
                "reflection_prompt": customized_prompt,
                "reflection_type": reflection_prompt.reflection_type.value
            }
        )
    
    def _get_reflection_prompt(self, sentiment: str, intent: str) -> Optional[ReflectionPrompt]:
        """Get appropriate reflection prompt for sentiment and intent"""
        # Normalize sentiment
        if sentiment not in self.reflection_prompts:
            sentiment = "neutral"
        
        # Get prompts for sentiment
        sentiment_prompts = self.reflection_prompts[sentiment]
        
        # Try to find specific intent prompt
        if intent in sentiment_prompts:
            return sentiment_prompts[intent]
        
        # Fallback to general prompts
        fallback_mapping = {
            "negative": "complaint",
            "neutral": "decision_making", 
            "positive": "appreciation"
        }
        
        fallback_intent = fallback_mapping.get(sentiment)
        if fallback_intent and fallback_intent in sentiment_prompts:
            return sentiment_prompts[fallback_intent]
        
        return None
    
    def _customize_prompt(self, prompt: ReflectionPrompt, user_message: str) -> Dict[str, Any]:
        """Customize reflection prompt based on user message"""
        # Extract key themes from user message for personalization
        message_lower = user_message.lower()
        
        # Simple keyword-based customization
        customizations = []
        if "stress" in message_lower or "pressure" in message_lower:
            customizations.append("I notice you mentioned feeling stressed.")
        if "confused" in message_lower or "don't know" in message_lower:
            customizations.append("It sounds like you're looking for clarity.")
        if "help" in message_lower:
            customizations.append("I can see you're seeking support.")
        
        # Build customized prompt
        intro = " ".join(customizations) + " " if customizations else ""
        
        return {
            "intro": intro,
            "main_prompt": prompt.prompt_text,
            "questions": prompt.follow_up_questions,
            "guidance": prompt.guidance,
            "type": prompt.reflection_type.value
        }
    
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

"""
RefinerAgent for ESB Chatbot System
Crafts personalized responses based on sentiment, intent, and web information using ReAct pattern
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
import builtins

from ..core.models import (
    ChatbotState,
    SentimentLabel,
    AgentAction,
    AgentObservation
)
from ..analyzers.sentiment_analyzer import get_sentiment_analyzer
from ..core.config import get_settings
from ..utils import retry_on_exception

# Built-in type aliases
len = builtins.len
str = builtins.str
bool = builtins.bool

logger = logging.getLogger(__name__)


class ResponseTone(str, Enum):
    """Response tone options"""
    EMPATHETIC = "empathetic"
    PROFESSIONAL = "professional"
    ENCOURAGING = "encouraging"
    INFORMATIVE = "informative"
    APOLOGETIC = "apologetic"
    CELEBRATORY = "celebratory"


class ResponseTemplate:
    """Template for generating responses"""
    def __init__(
        self,
        tone: ResponseTone,
        greeting: str,
        acknowledgment: str,
        main_content: str,
        action_items: List[str] = None,
        closing: str = ""
    ):
        self.tone = tone
        self.greeting = greeting
        self.acknowledgment = acknowledgment
        self.main_content = main_content
        self.action_items = action_items or []
        self.closing = closing


class RefinerAgent:
    """
    RefinerAgent that crafts personalized responses based on all available context
    Follows ReAct pattern: Reason -> Act -> Observe
    """
    
    def __init__(
        self, 
        use_ollama: bool = True,
        session_id: Optional[str] = None
    ):
        self.settings = get_settings()
        self.use_ollama = use_ollama
        self.session_id = session_id or str(uuid.uuid4())
        
        # Initialize LLM for response generation
        if use_ollama:
            try:
                self.llm_generator = get_sentiment_analyzer(
                    model_type="ollama",
                    ollama_model=self.settings.ollama_model
                )
            except Exception as e:
                logger.warning(f"Ollama not available for response generation: {e}")
                self.llm_generator = None
        else:
            self.llm_generator = None
        
        logger.info(f"RefinerAgent initialized, session: {self.session_id}")
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Always use LLM for response generation.
        """
        sentiment = str(state.sentiment_result.label) if state.sentiment_result else "neutral"
        intent = state.intent or "general_info"
        has_web_info = bool(state.context.get("web_info", []))

        # Check if response already exists
        if state.response:
            reasoning = "Response already generated for this message"
            return AgentAction(
                action="use_existing_response",
                action_input={"existing_response": state.response},
                reasoning=reasoning
            )

        # Always use LLM for response generation
        reasoning = f"Using LLM to generate personalized response for {sentiment} sentiment and {intent} intent"
        return AgentAction(
            action="generate_llm_response",
            action_input={
                "sentiment": sentiment,
                "intent": intent,
                "has_web_info": has_web_info,
                "user_message": state.user_message,
                "entities": state.context.get("intent_entities", {}),
                "web_info": state.context.get("web_info", []),
                "session_id": self.session_id
            },
            reasoning=reasoning
        )
    
    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Generate the response
        """
        try:
            if action.action == "use_existing_response":
                return AgentObservation(
                    observation="Using existing response",
                    success=True,
                    data={"response": action.action_input["existing_response"]}
                )
            
            elif action.action == "generate_llm_response":
                return self._generate_llm_response(action.action_input)
            
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        
        except Exception as e:
            logger.error(f"Error in RefinerAgent action: {e}")
            return AgentObservation(
                observation=f"Error during response generation: {str(e)}",
                success=False,
                data={}
            )
    
    def _generate_llm_response(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Generate response using LLM only (no templates, no fallback)."""
        llm_result = self._call_llm(action_input)
        if not llm_result or not llm_result.get("response"):
            return AgentObservation(
                observation="LLM did not return a response",
                success=False,
                data={}
            )
        return AgentObservation(
            observation="Generated response via LLM",
            success=True,
            data={
                "response": llm_result["response"],
                "tone": llm_result.get("tone", "llm_generated"),
                "method": "llm_only"
            }
        )

    @retry_on_exception((Exception,), tries=3, delay=2, backoff=2, logger=logger)
    def _call_llm(self, action_input: Dict[str, Any]) -> Dict[str, Any]:
        import os
        os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        import ollama
        system_prompt = action_input.get('system_prompt')
        prompt = (
            (system_prompt + "\n" if system_prompt else "") +
            "You are an ESB school assistant chatbot. "
            "Given the following context as JSON, generate a helpful, natural, and context-aware response for the user. "
            "Do not use templates or fallback phrases. Only use the information provided.\n"
            f"Context: {json.dumps(action_input, ensure_ascii=False)}\n"
            "Response:"
        )
        response = ollama.chat(model=self.settings.ollama_model, messages=[{"role": "user", "content": prompt}])
        return {"response": response['message']['content'].strip(), "tone": "llm_generated"}

    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state with generated response
        """
        if observation.success and "response" in observation.data:
            response_data = observation.data

            # Update state with response
            state.response = response_data["response"]

            # Add response metadata to context
            state.context.update({
                "response_tone": response_data.get("tone", "unknown"),
                "response_method": response_data.get("method", "unknown"),
                "response_generation_timestamp": datetime.utcnow().isoformat()
            })

            # Add to metadata
            state.metadata.update({
                "refiner_agent_session_id": self.session_id,
                "response_generated": True,
                "response_length": len(response_data["response"])
            })

            logger.info(f"Generated response with {response_data.get('tone', 'unknown')} tone")

        else:
            logger.warning(f"Response generation failed: {observation.observation}")
            # Set fallback response
            state.response = "I'm here to help! Could you please provide more details about what you need assistance with?"
            state.context.update({
                "response_generation_error": observation.observation
            })
            state.metadata.update({
                "response_generated": False
            })

        return state

    def process(self, state: ChatbotState) -> ChatbotState:
        """
        Main processing method implementing ReAct pattern
        """
        logger.info(f"RefinerAgent processing message: {state.user_message[:50]}...")

        # Step 1: Reason
        action = self.reason(state)
        logger.debug(f"Reasoning: {action.reasoning}")

        # Step 2: Act
        observation = self.act(action)
        logger.debug(f"Action result: {observation.observation}")

        # Step 3: Observe and update state
        updated_state = self.observe(observation, state)

        return updated_state

    def enhance_response_with_web_info(self, response: str, web_info: List[Dict]) -> str:
        """Enhance response with relevant web information in a more natural way"""
        if not web_info:
            return response
        
        # Extract the most relevant piece of information
        top_info = web_info[0]
        
        # Create a natural transition based on the existing response
        if "check" in response.lower() or "look" in response.lower():
            transition = "\n\nI just checked and "
        elif "find" in response.lower():
            transition = "\n\nI found that "
        else:
            transition = "\n\nBy the way, "
        
        # Add the information in a conversational way
        info_content = top_info['content'][:100]  # Keep it brief
        web_section = f"{transition}{info_content}..."
        
        # Add source reference conversationally
        if top_info.get('url'):
            web_section += f" You can find more details on our website."
        
        # If there are multiple relevant pieces of information
        if len(web_info) > 1:
            web_section += f" There's also some information about {web_info[1]['title'].lower()} if you're interested."
        
        return response + web_section


# LangGraph integration functions
def create_refiner_node(use_ollama: bool = True):
    """
    Factory function to create a response refinement node for LangGraph
    """
    def refiner_node(state: ChatbotState) -> ChatbotState:
        """LangGraph node function for response refinement"""
        agent = RefinerAgent(
            use_ollama=use_ollama,
            session_id=state.metadata.get("session_id")
        )

        # Enhance response with web info if available
        processed_state = agent.process(state)

        if processed_state.response and state.context.get("web_info"):
            enhanced_response = agent.enhance_response_with_web_info(
                processed_state.response,
                state.context["web_info"]
            )
            processed_state.response = enhanced_response

        return processed_state

    return refiner_node


def should_refine_response(state: ChatbotState) -> bool:
    """
    Conditional function for LangGraph to determine if response refinement is needed
    """
    return (
        state.response is None and
        state.sentiment_result is not None and
        state.intent is not None
    )





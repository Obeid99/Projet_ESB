"""
WebAgent for ESB Chatbot System
Calls LLM for web information based on user message and intent
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from ..core.models import (
    ChatbotState,
    AgentAction,
    AgentObservation
)
from ..core.config import get_settings
from ..utils import retry_on_exception

logger = logging.getLogger(__name__)


@dataclass
class WebScrapingResult:
    """Result from web scraping operation"""
    source: str
    title: str
    content: str
    url: str
    timestamp: datetime
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None


class WebAgent:
    """
    WebAgent that calls LLM for web information
    Follows ReAct pattern: Reason -> Act -> Observe
    """
    
    def __init__(
        self, 
        session_id: Optional[str] = None,
        cache_duration: int = 3600
    ):
        self.settings = get_settings()
        self.session_id = session_id or str(uuid.uuid4())
        self.cache_duration = cache_duration
        self.cache = {}
        logger.info(f"WebAgent initialized, session: {self.session_id}")

    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Always ask LLM for web info if intent is present and message is not too short.
        """
        user_message = state.user_message.strip()
        intent = state.intent
        if not user_message or len(user_message) < 5:
            return AgentAction(
                action="skip_web_info",
                action_input={"reason": "insufficient_context"},
                reasoning="Message too short for web information gathering"
            )
        if not intent:
            return AgentAction(
                action="skip_web_info",
                action_input={"reason": "no_intent"},
                reasoning="No intent detected"
            )
        return AgentAction(
            action="get_web_info_llm",
            action_input={
                "user_message": user_message,
                "intent": intent,
                "context": state.context
            },
            reasoning=f"Requesting web info from LLM for intent '{intent}'"
        )

    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Execute web info request to LLM. No scraping or fallback.
        """
        try:
            if action.action == "skip_web_info":
                return AgentObservation(
                    observation=f"Skipped web info: {action.action_input['reason']}",
                    success=True,
                    data={"web_results": []}
                )
            elif action.action == "get_web_info_llm":
                llm_result = self._call_llm(action.action_input)
                web_results = llm_result.get("web_results", [])
                return AgentObservation(
                    observation="Web info provided by LLM",
                    success=True if web_results else False,
                    data={"web_results": web_results}
                )
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        except Exception as e:
            logger.error(f"Error in WebAgent action: {e}")
            return AgentObservation(
                observation=f"Error during web info: {str(e)}",
                success=False,
                data={"web_results": []}
            )

    @retry_on_exception((Exception,), tries=3, delay=2, backoff=2, logger=logger)
    def _call_llm(self, action_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM for web info (placeholder, replace with actual LLM call)."""
        system_prompt = action_input.get('system_prompt')
        specialties_list = "- Licence in Management\n- Licence in Accounting\n- Licence in Business Computing (Business Intelligence / Business Information Systems)\n- Masters of Business Analytics\n- Masters of Digital Marketing\n- Masters of Accounting"
        user_message = action_input.get('user_message', '')
        prompt = (
            (system_prompt + "\n" if system_prompt else "") +
            "Here is a list of all specialties and degrees offered at ESB: " + specialties_list + "\n" +
            "If the user's question is about a course, specialty, or subject not in this list, reply: 'The subject you asked about (repeat the user's subject) is not offered at ESB.' Do not provide a website link or generic information. Only answer about the specialties listed.\n" +
            "User message: " + user_message + "\nIntent: " + str(action_input.get('intent', '')) + "\nRespond with a JSON array of web_results, or a message if the subject is not offered."
        )
        import os
        os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        import ollama
        response = ollama.chat(model=self.settings.ollama_model, messages=[{"role": "user", "content": prompt}])
        # Parse response as needed
        # For now, fallback to placeholder if LLM fails
        try:
            web_results = response['message']['content']
            import json
            web_results = json.loads(web_results)
        except Exception:
            web_results = [
                {
                    "source": "llm",
                    "title": "Not offered at ESB",
                    "content": f"The subject you asked about ('{user_message}') is not offered at ESB.",
                    "relevance": 1.0,
                    "url": ""
                }
            ]
        return {"web_results": web_results}
    
    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state based on web information from LLM
        """
        if observation.success and "web_results" in observation.data:
            web_results = observation.data["web_results"]

            # Add web information to context
            state.context.update({
                "web_info": [
                    {
                        "source": result["source"],
                        "title": result["title"],
                        "content": result["content"],
                        "relevance": result.get("relevance", 1.0),
                        "url": result["url"]
                    }
                    for result in web_results
                ],
                "web_info_timestamp": datetime.utcnow().isoformat(),
                "web_sources_checked": list(set([result["source"] for result in web_results]))
            })

            # Add to metadata
            state.metadata.update({
                "web_agent_session_id": self.session_id,
                "web_results_count": len(web_results),
                "web_info_success": True
            })

            logger.info(f"Added {len(web_results)} web results to state context")

        else:
            logger.warning(f"Web info request failed or returned no results: {observation.observation}")
            state.context.update({
                "web_info": [],
                "web_info_error": observation.observation
            })
            state.metadata.update({
                "web_info_success": False
            })

        return state

    def process(self, state: ChatbotState) -> ChatbotState:
        """
        Main processing method implementing ReAct pattern
        """
        logger.info(f"WebAgent processing message: {state.user_message[:50]}...")

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
def create_web_node(cache_duration: int = 3600):
    """
    Factory function to create a web scraping node for LangGraph
    """
    def web_node(state: ChatbotState) -> ChatbotState:
        """LangGraph node function for web scraping"""
        agent = WebAgent(
            session_id=state.metadata.get("session_id"),
            cache_duration=cache_duration
        )
        return agent.process(state)

    return web_node


def should_scrape_web(state: ChatbotState) -> bool:
    """
    Conditional function for LangGraph to determine if web scraping is needed
    """
    # Web scraping is useful for certain intents
    web_relevant_intents = [
        "registration_help",
        "event_info",
        "facility_info",
        "general_info",
        "course_info",
        "schedule_inquiry"
    ]

    return (
        state.intent in web_relevant_intents and
        "web_info" not in state.context and
        WEB_SCRAPING_AVAILABLE
    )


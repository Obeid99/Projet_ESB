"""
WebAgent for ESB Chatbot System
Scrapes ESB website and Facebook for current information using ReAct pattern
"""
import logging
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

from ..core.models import (
    ChatbotState,
    AgentAction,
    AgentObservation
)
from ..core.config import get_settings

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
    WebAgent that scrapes ESB website and Facebook for current information
    Follows ReAct pattern: Reason -> Act -> Observe
    """
    
    def __init__(
        self, 
        session_id: Optional[str] = None,
        cache_duration: int = 3600  # Cache for 1 hour
    ):
        self.settings = get_settings()
        self.session_id = session_id or str(uuid.uuid4())
        self.cache_duration = cache_duration
        self.cache = {}  # Simple in-memory cache
        
        # ESB-specific URLs and selectors
        self.esb_sources = {
            "main_website": {
                "url": self.settings.esb_website_url,
                "selectors": {
                    "news": ".news-item, .announcement, .post",
                    "events": ".event, .calendar-item",
                    "general": "p, .content, .description"
                }
            },
            "facebook": {
                "url": self.settings.esb_facebook_url,
                "selectors": {
                    "posts": "[data-testid='post_message']",
                    "general": ".userContent, ._5pbx"
                }
            }
        }
        
        # Keywords for relevance scoring
        self.relevance_keywords = {
            "registration": ["registration", "enroll", "course", "deadline"],
            "grades": ["grade", "result", "transcript", "exam"],
            "events": ["event", "conference", "seminar", "workshop"],
            "facilities": ["library", "cafeteria", "parking", "building"],
            "financial": ["fee", "tuition", "scholarship", "payment"],
            "academic": ["course", "professor", "schedule", "curriculum"]
        }
        
        logger.info(f"WebAgent initialized, session: {self.session_id}")
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Determine what web information to gather
        """
        user_message = state.user_message.strip()
        intent = state.intent
        
        # Check if web scraping is available
        if not WEB_SCRAPING_AVAILABLE:
            reasoning = "Web scraping libraries not available"
            return AgentAction(
                action="skip_web_scraping",
                action_input={"reason": "libraries_unavailable"},
                reasoning=reasoning
            )
        
        # Check if message is too short or unclear
        if not user_message or len(user_message) < 5:
            reasoning = "Message too short for web information gathering"
            return AgentAction(
                action="skip_web_scraping",
                action_input={"reason": "insufficient_context"},
                reasoning=reasoning
            )
        
        # Determine what type of information to search for based on intent
        search_strategy = self._determine_search_strategy(intent, user_message)
        
        if search_strategy["skip"]:
            reasoning = f"Intent '{intent}' doesn't require web information"
            return AgentAction(
                action="skip_web_scraping",
                action_input={"reason": "intent_not_relevant"},
                reasoning=reasoning
            )
        
        reasoning = f"Searching for {search_strategy['type']} information related to intent '{intent}'"
        return AgentAction(
            action="scrape_web_info",
            action_input={
                "search_type": search_strategy["type"],
                "keywords": search_strategy["keywords"],
                "sources": search_strategy["sources"]
            },
            reasoning=reasoning
        )
    
    def _determine_search_strategy(self, intent: str, message: str) -> Dict[str, Any]:
        """Determine what to search for based on intent and message"""
        message_lower = message.lower()
        
        # Intent-based search strategies
        strategies = {
            "registration_help": {
                "type": "registration_info",
                "keywords": ["registration", "enrollment", "deadline", "course"],
                "sources": ["main_website"],
                "skip": False
            },
            "grade_inquiry": {
                "type": "academic_info", 
                "keywords": ["grade", "result", "transcript"],
                "sources": ["main_website"],
                "skip": False
            },
            "event_info": {
                "type": "events",
                "keywords": ["event", "conference", "seminar", "calendar"],
                "sources": ["main_website", "facebook"],
                "skip": False
            },
            "facility_info": {
                "type": "facilities",
                "keywords": ["library", "cafeteria", "parking", "hours"],
                "sources": ["main_website"],
                "skip": False
            },
            "general_info": {
                "type": "general",
                "keywords": self._extract_keywords_from_message(message_lower),
                "sources": ["main_website"],
                "skip": False
            }
        }
        
        # Default strategy for unknown intents
        default_strategy = {
            "type": "general",
            "keywords": self._extract_keywords_from_message(message_lower),
            "sources": ["main_website"],
            "skip": len(self._extract_keywords_from_message(message_lower)) == 0
        }
        
        return strategies.get(intent, default_strategy)
    
    def _extract_keywords_from_message(self, message: str) -> List[str]:
        """Extract relevant keywords from user message"""
        keywords = []
        for category, category_keywords in self.relevance_keywords.items():
            for keyword in category_keywords:
                if keyword in message:
                    keywords.append(keyword)
        return list(set(keywords))  # Remove duplicates
    
    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Execute web scraping or skip
        """
        try:
            if action.action == "skip_web_scraping":
                return AgentObservation(
                    observation=f"Skipped web scraping: {action.action_input['reason']}",
                    success=True,
                    data={"web_results": []}
                )
            
            elif action.action == "scrape_web_info":
                return self._scrape_web_information(action.action_input)
            
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        
        except Exception as e:
            logger.error(f"Error in WebAgent action: {e}")
            return AgentObservation(
                observation=f"Error during web scraping: {str(e)}",
                success=False,
                data={"web_results": []}
            )
    
    def _scrape_web_information(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Scrape web information based on action input"""
        search_type = action_input["search_type"]
        keywords = action_input["keywords"]
        sources = action_input["sources"]
        
        results = []
        
        # Check cache first
        cache_key = f"{search_type}_{'-'.join(keywords)}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if datetime.now() - cached_result["timestamp"] < timedelta(seconds=self.cache_duration):
                logger.info(f"Using cached results for {cache_key}")
                return AgentObservation(
                    observation=f"Retrieved cached {search_type} information",
                    success=True,
                    data={"web_results": cached_result["results"]}
                )
        
        # Scrape from specified sources
        for source_name in sources:
            if source_name in self.esb_sources:
                source_results = self._scrape_source(source_name, search_type, keywords)
                results.extend(source_results)
        
        # Score and sort results by relevance
        scored_results = self._score_results(results, keywords)
        
        # Cache results
        self.cache[cache_key] = {
            "results": scored_results,
            "timestamp": datetime.now()
        }
        
        observation_msg = f"Scraped {len(scored_results)} relevant items from {len(sources)} sources"
        return AgentObservation(
            observation=observation_msg,
            success=True,
            data={"web_results": scored_results}
        )
    
    def _scrape_source(self, source_name: str, search_type: str, keywords: List[str]) -> List[WebScrapingResult]:
        """Scrape a specific source"""
        results = []
        source_config = self.esb_sources[source_name]
        
        try:
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(source_config["url"], headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content based on selectors
            selectors = source_config["selectors"]
            
            # Try specific selectors first, then general
            for selector_type, selector in selectors.items():
                elements = soup.select(selector)
                
                for element in elements[:5]:  # Limit to 5 items per selector
                    text_content = element.get_text(strip=True)
                    
                    if len(text_content) > 20:  # Only include substantial content
                        result = WebScrapingResult(
                            source=source_name,
                            title=self._extract_title(element),
                            content=text_content[:500],  # Limit content length
                            url=source_config["url"],
                            timestamp=datetime.now(),
                            metadata={"selector_type": selector_type}
                        )
                        results.append(result)
                
                if results:  # If we found content, don't try other selectors
                    break
        
        except Exception as e:
            logger.warning(f"Failed to scrape {source_name}: {e}")
            # Add a mock result indicating the attempt
            results.append(WebScrapingResult(
                source=source_name,
                title="Scraping Error",
                content=f"Unable to access {source_name} at this time. Please check the ESB website directly.",
                url=source_config["url"],
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            ))
        
        return results
    
    def _extract_title(self, element) -> str:
        """Extract a title from an HTML element"""
        # Try to find a title in various ways
        title_selectors = ['h1', 'h2', 'h3', '.title', '.headline', 'strong']
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) < 100:
                    return title
        
        # Fallback: use first few words of content
        content = element.get_text(strip=True)
        words = content.split()[:8]
        return " ".join(words) + "..." if len(words) == 8 else " ".join(words)
    
    def _score_results(self, results: List[WebScrapingResult], keywords: List[str]) -> List[WebScrapingResult]:
        """Score results based on keyword relevance"""
        for result in results:
            score = 0
            content_lower = (result.title + " " + result.content).lower()
            
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
            
            # Boost score for recent content (if we could determine dates)
            # For now, all content gets base relevance
            result.relevance_score = score / max(len(keywords), 1)
        
        # Sort by relevance score (highest first)
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:3]  # Top 3 results

    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state based on web scraping results
        """
        if observation.success and "web_results" in observation.data:
            web_results = observation.data["web_results"]

            # Add web information to context
            state.context.update({
                "web_info": [
                    {
                        "source": result.source,
                        "title": result.title,
                        "content": result.content,
                        "relevance": result.relevance_score,
                        "url": result.url
                    }
                    for result in web_results
                ],
                "web_scraping_timestamp": datetime.utcnow().isoformat(),
                "web_sources_checked": list(set([result.source for result in web_results]))
            })

            # Add to metadata
            state.metadata.update({
                "web_agent_session_id": self.session_id,
                "web_results_count": len(web_results),
                "web_scraping_success": True
            })

            logger.info(f"Added {len(web_results)} web results to state context")

        else:
            logger.warning(f"Web scraping failed or returned no results: {observation.observation}")
            state.context.update({
                "web_info": [],
                "web_scraping_error": observation.observation
            })
            state.metadata.update({
                "web_scraping_success": False
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

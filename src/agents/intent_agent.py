"""
IntentAgent for ESB Chatbot System
Classifies student intentions and requests using ReAct pattern
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from ..core.models import (
    ChatbotState,
    AgentAction,
    AgentObservation
)
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class IntentCategory(str, Enum):
    """Student intent categories for ESB"""
    # Academic intents
    REGISTRATION_HELP = "registration_help"
    GRADE_INQUIRY = "grade_inquiry"
    COURSE_INFO = "course_info"
    SCHEDULE_INQUIRY = "schedule_inquiry"
    ACADEMIC_SUPPORT = "academic_support"
    
    # Administrative intents
    FINANCIAL_INQUIRY = "financial_inquiry"
    DOCUMENT_REQUEST = "document_request"
    FACILITY_INFO = "facility_info"
    CONTACT_INFO = "contact_info"
    
    # Support intents
    TECHNICAL_SUPPORT = "technical_support"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    APPRECIATION = "appreciation"
    
    # Information seeking
    GENERAL_INFO = "general_info"
    EVENT_INFO = "event_info"
    CAREER_GUIDANCE = "career_guidance"
    
    # Social/Personal
    SOCIAL_INTERACTION = "social_interaction"
    PERSONAL_SHARING = "personal_sharing"
    
    # Unknown
    UNCLEAR = "unclear"


class IntentResult:
    """Intent classification result"""
    def __init__(
        self, 
        primary_intent: IntentCategory,
        confidence: float,
        secondary_intents: List[IntentCategory] = None,
        entities: Dict[str, Any] = None,
        reasoning: str = ""
    ):
        self.primary_intent = primary_intent
        self.confidence = confidence
        self.secondary_intents = secondary_intents or []
        self.entities = entities or {}
        self.reasoning = reasoning


class IntentAgent:
    """
    IntentAgent that classifies student intentions and requests
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
        
        # Initialize Ollama for LLM-based intent detection
        self.ollama_available = False
        if use_ollama:
            try:
                import ollama
                # Test connection
                ollama.list()
                self.ollama_available = True
                logger.info("Ollama available for intent classification")
            except Exception as e:
                logger.warning(f"Ollama not available for intent analysis: {e}")
                self.ollama_available = False
        else:
            self.ollama_available = False
        
        # Keywords for rule-based intent detection
        self.intent_keywords = {
            IntentCategory.REGISTRATION_HELP: [
                "register", "registration", "enroll", "enrollment", "course selection",
                "add course", "drop course", "waitlist", "prerequisite"
            ],
            IntentCategory.GRADE_INQUIRY: [
                "grade", "grades", "score", "result", "transcript", "gpa",
                "mark", "marks", "evaluation", "assessment"
            ],
            IntentCategory.COURSE_INFO: [
                "course", "class", "subject", "curriculum", "syllabus",
                "professor", "instructor", "teacher", "lecture"
            ],
            IntentCategory.SCHEDULE_INQUIRY: [
                "schedule", "timetable", "time", "when", "calendar",
                "exam schedule", "class time", "hours"
            ],
            IntentCategory.FINANCIAL_INQUIRY: [
                "fee", "fees", "tuition", "payment", "scholarship", "financial aid",
                "cost", "price", "money", "billing", "invoice"
            ],
            IntentCategory.TECHNICAL_SUPPORT: [
                "login", "password", "system", "website", "app", "technical",
                "error", "bug", "not working", "access"
            ],
            IntentCategory.COMPLAINT: [
                "complaint", "problem", "issue", "wrong", "bad", "terrible",
                "disappointed", "frustrated", "angry", "unfair"
            ],
            IntentCategory.APPRECIATION: [
                "thank", "thanks", "grateful", "appreciate", "excellent",
                "great", "wonderful", "amazing", "good job", "love", "adore",
                "fantastic", "awesome", "brilliant", "outstanding", "superb",
                "impressed", "happy with", "satisfied", "pleased"
            ],
            IntentCategory.FACILITY_INFO: [
                "library", "cafeteria", "parking", "building", "room",
                "facility", "location", "where", "gym", "lab"
            ],
            IntentCategory.EVENT_INFO: [
                "event", "activity", "conference", "seminar", "workshop",
                "career fair", "orientation", "graduation"
            ],
            IntentCategory.CAREER_GUIDANCE: [
                "career", "job", "internship", "placement", "employment",
                "cv", "resume", "interview", "company"
            ]
        }
        
        logger.info(f"IntentAgent initialized, session: {self.session_id}")
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Analyze what intent detection is needed
        """
        user_message = state.user_message.strip()
        
        # Check if message is empty or too short
        if not user_message or len(user_message) < 3:
            reasoning = "Message is too short for meaningful intent detection"
            return AgentAction(
                action="skip_intent_detection",
                action_input={"reason": "insufficient_text"},
                reasoning=reasoning
            )
        
        # Check if intent was already detected
        if state.intent is not None:
            reasoning = "Intent already detected for this message"
            return AgentAction(
                action="use_existing_intent",
                action_input={"existing_intent": state.intent},
                reasoning=reasoning
            )
        
        # Determine detection strategy based on message complexity and LLM availability
        word_count = len(user_message.split())
        if word_count > 5 and self.ollama_available:
            reasoning = f"Complex message ({word_count} words), using LLM intent detection"
            return AgentAction(
                action="llm_intent_detection",
                action_input={"text": user_message},
                reasoning=reasoning
            )
        else:
            reasoning = f"Simple message ({word_count} words) or LLM unavailable, using keyword analysis"
            return AgentAction(
                action="keyword_intent_detection",
                action_input={"text": user_message},
                reasoning=reasoning
            )
    
    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Execute the determined action
        """
        try:
            if action.action == "skip_intent_detection":
                return AgentObservation(
                    observation="Skipped intent detection due to insufficient text",
                    success=True,
                    data={
                        "intent_result": IntentResult(
                            primary_intent=IntentCategory.UNCLEAR,
                            confidence=0.0,
                            reasoning="Skipped: insufficient text"
                        )
                    }
                )
            
            elif action.action == "use_existing_intent":
                return AgentObservation(
                    observation="Using existing intent classification",
                    success=True,
                    data={
                        "intent_result": IntentResult(
                            primary_intent=IntentCategory(action.action_input["existing_intent"]),
                            confidence=1.0,
                            reasoning="Pre-existing intent"
                        )
                    }
                )
            
            elif action.action == "keyword_intent_detection":
                return self._keyword_intent_detection(action.action_input["text"])
            
            elif action.action == "llm_intent_detection":
                return self._llm_intent_detection(action.action_input["text"])
            
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        
        except Exception as e:
            logger.error(f"Error in IntentAgent action: {e}")
            return AgentObservation(
                observation=f"Error during intent detection: {str(e)}",
                success=False,
                data={}
            )
    
    def _keyword_intent_detection(self, text: str) -> AgentObservation:
        """Keyword-based intent detection"""
        text_lower = text.lower()
        intent_scores = {}
        
        # Calculate scores for each intent category
        for intent, keywords in self.intent_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                intent_scores[intent] = {
                    "score": score,
                    "keywords": matched_keywords
                }
        
        if intent_scores:
            # Get the intent with highest score
            best_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]["score"])
            confidence = min(0.8, intent_scores[best_intent]["score"] * 0.2)
            
            # Get secondary intents
            secondary_intents = [
                intent for intent, data in intent_scores.items() 
                if intent != best_intent and data["score"] >= intent_scores[best_intent]["score"] * 0.5
            ]
            
            intent_result = IntentResult(
                primary_intent=best_intent,
                confidence=confidence,
                secondary_intents=secondary_intents,
                entities={"matched_keywords": intent_scores[best_intent]["keywords"]},
                reasoning=f"Keyword analysis: matched {intent_scores[best_intent]['keywords']}"
            )
        else:
            intent_result = IntentResult(
                primary_intent=IntentCategory.GENERAL_INFO,
                confidence=0.3,
                reasoning="No specific keywords matched, defaulting to general info"
            )
        
        return AgentObservation(
            observation=f"Detected intent: {intent_result.primary_intent} (confidence: {intent_result.confidence:.3f})",
            success=True,
            data={"intent_result": intent_result}
        )

    def _llm_intent_detection(self, text: str) -> AgentObservation:
        """LLM-based intent detection using Ollama"""
        if not self.ollama_available:
            # Fallback to keyword detection
            return self._keyword_intent_detection(text)

        try:
            import ollama
            import json

            # Create comprehensive intent detection prompt
            prompt = f"""You are an expert at understanding student intentions in university communications at ESB (Esprit School of Business). Your task is to accurately classify the primary intent behind a student's message.

STUDENT MESSAGE: "{text}"

AVAILABLE INTENT CATEGORIES:
1. INFORMATION SEEKING:
   - registration_help: Questions about course registration, enrollment, adding/dropping classes, deadlines
   - grade_inquiry: Questions about grades, transcripts, GPA, exam results
   - course_info: Questions about courses, curriculum, professors, syllabi
   - schedule_inquiry: Questions about timetables, class times, exam dates
   - facility_info: Questions about campus facilities, library hours, parking, buildings
   - general_info: General questions about the university, programs, policies
   - event_info: Questions about events, activities, conferences, seminars
   - contact_info: Looking for contact information for departments or staff

2. SUPPORT NEEDS:
   - academic_support: Student struggling with studies, needs tutoring, feeling overwhelmed
   - technical_support: Having technical issues with systems, login problems, website errors
   - financial_inquiry: Questions about fees, tuition, payments, scholarships, financial aid
   - document_request: Requesting official documents, certificates, transcripts
   - career_guidance: Seeking career advice, job placement, internship information

3. EMOTIONAL/SOCIAL:
   - complaint: Expressing dissatisfaction, problems, issues, complaints
   - suggestion: Providing suggestions, feedback, recommendations
   - appreciation: Expressing gratitude, thanks, positive feedback
   - social_interaction: Casual conversation, greetings, small talk
   - personal_sharing: Sharing personal experiences, feelings, stories

4. UNCLEAR: Message intent is ambiguous or doesn't fit other categories

ANALYSIS INSTRUCTIONS:
1. First, carefully read and understand the student's message
2. Consider the primary purpose/need expressed in the message
3. Identify any key topics mentioned (courses, grades, registration, etc.)
4. Determine the emotional tone (neutral, frustrated, grateful, etc.)
5. Select the SINGLE most appropriate intent category

RESPONSE FORMAT:
Respond with ONLY a valid JSON object in this exact format:
{{"primary_intent": "intent_category", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

IMPORTANT GUIDELINES:
- Use exactly one of the listed intent categories (use the exact category name)
- Confidence should be between 0.0 and 1.0 (0.8+ for clear intents, 0.5-0.7 for somewhat clear, 0.3-0.5 for unclear)
- Focus on the main purpose/need expressed in the message, not secondary elements
- If multiple intents are present, choose the most dominant one
- Keep reasoning under 50 words
"""

            response = ollama.chat(
                model=self.settings.ollama_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 150
                }
            )

            # Extract and parse response
            content = response['message']['content'].strip()

            # Clean up response (remove markdown formatting if present)
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()

            try:
                result = json.loads(content)

                # Validate the result
                if 'primary_intent' not in result or 'confidence' not in result:
                    raise ValueError("Missing required fields in LLM response")

                intent_str = result['primary_intent']
                confidence = float(result['confidence'])
                reasoning = result.get('reasoning', 'LLM classification')

                # Validate intent category
                try:
                    primary_intent = IntentCategory(intent_str)
                except ValueError:
                    logger.warning(f"Invalid intent from LLM: {intent_str}, falling back to keyword detection")
                    return self._keyword_intent_detection(text)

                # Ensure confidence is in valid range
                confidence = max(0.0, min(1.0, confidence))

                intent_result = IntentResult(
                    primary_intent=primary_intent,
                    confidence=confidence,
                    reasoning=f"LLM analysis: {reasoning}"
                )

                return AgentObservation(
                    observation=f"LLM detected intent: {primary_intent.value} (confidence: {confidence:.3f})",
                    success=True,
                    data={"intent_result": intent_result}
                )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse LLM intent response: {e}. Raw response: {content}")
                # Fallback to keyword detection
                return self._keyword_intent_detection(text)

        except Exception as e:
            logger.warning(f"LLM intent detection failed: {e}, falling back to keywords")
            return self._keyword_intent_detection(text)

    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state based on action results
        """
        if observation.success and "intent_result" in observation.data:
            intent_result = observation.data["intent_result"]

            # Update state with intent classification
            state.intent = intent_result.primary_intent.value

            # Add to context for other agents
            state.context.update({
                "intent_confidence": intent_result.confidence,
                "secondary_intents": [intent.value for intent in intent_result.secondary_intents],
                "intent_entities": intent_result.entities,
                "intent_reasoning": intent_result.reasoning
            })

            # Add to metadata
            state.metadata.update({
                "intent_analysis_timestamp": datetime.utcnow().isoformat(),
                "intent_session_id": self.session_id,
                "intent_method": "llm" if self.ollama_available else "keyword"
            })

            logger.info(f"Updated state with intent: {intent_result.primary_intent}")

        else:
            logger.warning(f"Intent detection failed: {observation.observation}")
            # Set unclear intent as fallback
            state.intent = IntentCategory.UNCLEAR.value
            state.context.update({
                "intent_confidence": 0.0,
                "intent_reasoning": "Intent detection failed"
            })

        return state

    def process(self, state: ChatbotState) -> ChatbotState:
        """
        Main processing method implementing ReAct pattern
        """
        logger.info(f"IntentAgent processing message: {state.user_message[:50]}...")

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
def create_intent_node(use_ollama: bool = True):
    """
    Factory function to create an intent detection node for LangGraph
    """
    def intent_node(state: ChatbotState) -> ChatbotState:
        """LangGraph node function for intent detection"""
        agent = IntentAgent(
            use_ollama=use_ollama,
            session_id=state.metadata.get("session_id")
        )
        return agent.process(state)

    return intent_node


def should_detect_intent(state: ChatbotState) -> bool:
    """
    Conditional function for LangGraph to determine if intent detection is needed
    """
    return (
        state.intent is None and
        state.user_message and
        len(state.user_message.strip()) >= 3
    )


"""
RefinerAgent for ESB Chatbot System
Crafts personalized responses based on sentiment, intent, and web information using ReAct pattern
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
from ..analyzers.sentiment_analyzer import get_sentiment_analyzer
from ..core.config import get_settings

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
        
        # Response templates for different scenarios
        self.templates = self._initialize_templates()
        
        logger.info(f"RefinerAgent initialized, session: {self.session_id}")
    
    def _initialize_templates(self) -> Dict[str, Dict[str, ResponseTemplate]]:
        """Initialize more natural, conversational response templates"""
        return {
            "positive": {
                "appreciation": ResponseTemplate(
                    tone=ResponseTone.CELEBRATORY,
                    greeting="Thanks so much for your kind words! 😊",
                    acknowledgment="It really makes my day to hear you're having a great experience at ESB.",
                    main_content="We're all about creating an environment where students like you can thrive, and it's wonderful to know it's working for you. Your enthusiasm is exactly what makes our community special.",
                    action_items=[
                        "Keep sharing your positive experiences - it helps us know what's working",
                        "Let us know if there's anything else we can do to make your time here even better"
                    ],
                    closing="Thanks again for brightening my day with your message!"
                ),
                "course_info": ResponseTemplate(
                    tone=ResponseTone.ENCOURAGING,
                    greeting="Hey there! 📚",
                    acknowledgment="I love your enthusiasm about our courses!",
                    main_content="ESB's programs are designed to give you both theoretical knowledge and practical skills you'll actually use in the real world. Our professors bring their industry experience right into the classroom.",
                    action_items=[
                        "Check out the course catalog for all the details",
                        "Talk to your advisor about which courses might be the best fit for your goals"
                    ],
                    closing="I'm excited to see where these courses take you! Let me know if you have any other questions."
                ),
                "general_info": ResponseTemplate(
                    tone=ResponseTone.ENCOURAGING,
                    greeting="Hello there! 👋",
                    acknowledgment="I'm delighted to help with your inquiry!",
                    main_content="ESB is committed to providing you with the best possible educational experience. Whether you need information about academics, facilities, or student life, I'm here to guide you.",
                    action_items=[
                        "Explore our website for comprehensive information",
                        "Visit the student services office for personalized help",
                        "Connect with current students for peer insights"
                    ],
                    closing="Feel free to ask me anything else - I'm here to help! 😊"
                )
            },
            "negative": {
                "complaint": ResponseTemplate(
                    tone=ResponseTone.EMPATHETIC,
                    greeting="I hear you, and I'm really sorry about this 😔",
                    acknowledgment="That sounds incredibly frustrating, and you have every right to be upset about it.",
                    main_content="Let's get this fixed for you as quickly as possible. Every student deserves better than what you've experienced, and I want to make sure this gets resolved properly.",
                    action_items=[
                        "I'm going to personally make sure this gets to the right department today",
                        "You'll hear back from someone within 24 hours with a solution",
                        "If you don't get a response by then, please message me directly"
                    ],
                    closing="Thanks for bringing this to our attention - we really do want to make this right."
                ),
                "technical_support": ResponseTemplate(
                    tone=ResponseTone.PROFESSIONAL,
                    greeting="I understand the frustration with tech issues 💻",
                    acknowledgment="Technical problems can be really disruptive to your studies, and I want to help you get back on track quickly.",
                    main_content="Let me provide you with some immediate solutions that often resolve these types of issues:",
                    action_items=[
                        "Clear your browser cache and cookies",
                        "Try using a different browser (Chrome, Firefox, Safari)",
                        "Check if you're using the correct login credentials",
                        "Restart your device and try again",
                        "Contact our IT helpdesk at [phone] if issues persist"
                    ],
                    closing="I hope this gets you back up and running! Let me know if you need more help. 🔧"
                ),
                "registration_help": ResponseTemplate(
                    tone=ResponseTone.EMPATHETIC,
                    greeting="Registration troubles can be so stressful 📝",
                    acknowledgment="I know how important it is to get registered for your courses on time, and I'm here to help you through this.",
                    main_content="Let me guide you through the registration process step by step:",
                    action_items=[
                        "Log into the student portal with your credentials",
                        "Check your academic standing and prerequisites",
                        "Review available course sections and times",
                        "Add courses to your cart before confirming",
                        "Contact the registrar's office if you encounter errors"
                    ],
                    closing="Don't worry - we'll get you registered! Reach out if you need more assistance. 📚"
                ),
                "academic_support": ResponseTemplate(
                    tone=ResponseTone.EMPATHETIC,
                    greeting="I understand you're going through a tough time 📖",
                    acknowledgment="Academic challenges are completely normal, and reaching out for help shows real strength and wisdom.",
                    main_content="ESB has many resources to support your academic success. You're not alone in this journey, and with the right support, you can overcome these challenges.",
                    action_items=[
                        "Schedule a meeting with your academic advisor",
                        "Visit the tutoring center for subject-specific help",
                        "Form study groups with classmates",
                        "Attend professor office hours for clarification",
                        "Consider time management workshops"
                    ],
                    closing="Remember, every successful student has faced challenges. You've got this! 💪"
                ),
                "stress_support": ResponseTemplate(
                    tone=ResponseTone.EMPATHETIC,
                    greeting="I can sense you're feeling overwhelmed right now 🤗",
                    acknowledgment="It's completely understandable to feel stressed - student life can be incredibly demanding, and your feelings are valid.",
                    main_content="Let's take a step back and focus on what we can do right now to help you feel more in control. Remember, you don't have to handle everything alone.",
                    action_items=[
                        "Take a few deep breaths - you're going to be okay",
                        "Break down your tasks into smaller, manageable steps",
                        "Reach out to our counseling services for emotional support",
                        "Connect with friends or family for a quick chat",
                        "Consider taking a short break to recharge",
                        "Remember that asking for help is a sign of strength"
                    ],
                    closing="You're stronger than you know, and this difficult moment will pass. I'm here to help you through this. 🌟"
                ),
                "general_info": ResponseTemplate(
                    tone=ResponseTone.EMPATHETIC,
                    greeting="I'm really sorry you're having a difficult experience 😔",
                    acknowledgment="I can hear the frustration in your message, and I want you to know that your concerns are important to us.",
                    main_content="Let me help you find the right solution and make sure you get the support you deserve. Every student should feel supported and valued at ESB.",
                    action_items=[
                        "I'll connect you with the right person to address your specific concern",
                        "You can always reach out to student services for additional support",
                        "Consider speaking with a counselor if you need someone to talk to",
                        "Remember that challenges are temporary, but your education is an investment in your future"
                    ],
                    closing="Please don't hesitate to reach out again. We're here to support you every step of the way. 🤝"
                )
            },
            "neutral": {
                "registration_help": ResponseTemplate(
                    tone=ResponseTone.INFORMATIVE,
                    greeting="Hey there! 📋",
                    acknowledgment="Registration can be a bit tricky, but I've got you covered.",
                    main_content="Here's what you need to know about registering for courses at ESB:",
                    action_items=[
                        "Log into the student portal during your registration window (check your email for the exact time)",
                        "Have some backup courses ready in case your first choices fill up",
                        "If you run into any technical issues, our IT help desk is available at support@esb.edu"
                    ],
                    closing="Hope that helps! Let me know if you run into any snags along the way."
                ),
                "facility_info": ResponseTemplate(
                    tone=ResponseTone.INFORMATIVE,
                    greeting="Let me help you navigate our campus! 🏫",
                    acknowledgment="Getting familiar with ESB's facilities will enhance your student experience.",
                    main_content="Here's what you need to know about our campus facilities:",
                    action_items=[
                        "Library: Open 7am-11pm weekdays, 9am-9pm weekends",
                        "Student Center: Food court, study spaces, student services",
                        "Computer Labs: Available 24/7 with student ID access",
                        "Career Services: Located in Building A, 2nd floor",
                        "Parking: Student permits available at security office"
                    ],
                    closing="Would you like specific directions to any of these locations? 🗺️"
                ),
                "course_info": ResponseTemplate(
                    tone=ResponseTone.INFORMATIVE,
                    greeting="Great question about our courses! 📚",
                    acknowledgment="Understanding our course offerings will help you make the best academic choices.",
                    main_content="ESB offers comprehensive business programs with these key features:",
                    action_items=[
                        "Core business courses: Finance, Marketing, Management, Operations",
                        "Specialization tracks: Entrepreneurship, International Business, Digital Marketing",
                        "Practical components: Internships, case studies, real client projects",
                        "Small class sizes for personalized attention",
                        "Industry-experienced professors"
                    ],
                    closing="What specific area of business interests you most? I can provide more targeted information! 🎯"
                ),
                "career_guidance": ResponseTemplate(
                    tone=ResponseTone.ENCOURAGING,
                    greeting="Career planning is so important! 🎯",
                    acknowledgment="It's smart that you're thinking about your career path early in your studies.",
                    main_content="ESB's Career Services can help you explore and plan your professional future:",
                    action_items=[
                        "Take a career assessment to identify your strengths",
                        "Attend career fairs and networking events",
                        "Schedule mock interviews to practice your skills",
                        "Build your LinkedIn profile and professional network",
                        "Consider internships in your field of interest",
                        "Meet with career counselors for personalized guidance"
                    ],
                    closing="Your career journey starts now! What field are you most interested in exploring? 🚀"
                ),
                "general_info": ResponseTemplate(
                    tone=ResponseTone.PROFESSIONAL,
                    greeting="Welcome to ESB! 👋",
                    acknowledgment="I'm here to help you with any questions about our school and programs.",
                    main_content="ESB is dedicated to providing world-class business education that prepares students for successful careers. Our community values excellence, innovation, and ethical leadership.",
                    action_items=[
                        "Explore our website for detailed program information",
                        "Schedule a campus tour to see our facilities",
                        "Attend information sessions about specific programs",
                        "Connect with current students and alumni",
                        "Meet with admissions counselors for personalized guidance"
                    ],
                    closing="What specific aspect of ESB would you like to learn more about? 🤔"
                )
            }
        }
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Determine how to craft the response
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
        
        # Determine response strategy
        if self.llm_generator and len(state.user_message) > 20:
            reasoning = f"Using LLM to generate personalized response for {sentiment} sentiment and {intent} intent"
            return AgentAction(
                action="generate_llm_response",
                action_input={
                    "sentiment": sentiment,
                    "intent": intent,
                    "has_web_info": has_web_info,
                    "user_message": state.user_message
                },
                reasoning=reasoning
            )
        else:
            reasoning = f"Using template-based response for {sentiment} sentiment and {intent} intent"
            return AgentAction(
                action="generate_template_response",
                action_input={
                    "sentiment": sentiment,
                    "intent": intent,
                    "has_web_info": has_web_info
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
            
            elif action.action == "generate_template_response":
                return self._generate_template_response(action.action_input)
            
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
    
    def _generate_template_response(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Generate more natural template-based response"""
        sentiment = action_input["sentiment"]
        intent = action_input["intent"]
        has_web_info = action_input["has_web_info"]
        
        # Get appropriate template
        template = self._get_template(sentiment, intent)
        
        # Build response with more natural flow
        response_parts = []
        
        # Add greeting
        response_parts.append(template.greeting)
        
        # Add acknowledgment with natural transition
        response_parts.append(template.acknowledgment)
        
        # Add main content with natural transition
        response_parts.append(template.main_content)
        
        # Add web information if available
        if has_web_info:
            response_parts.append("\nI just checked our latest information and found:")
        
        # Add action items with more conversational framing
        if template.action_items:
            if len(template.action_items) <= 2:
                # For 1-2 items, use inline format
                actions = " and ".join([f"{item}" for item in template.action_items])
                response_parts.append(f"\nQuick tip: {actions}.")
            else:
                # For 3+ items, use a more conversational list intro
                response_parts.append("\nHere's what I'd suggest:")
                for item in template.action_items[:3]:  # Limit to top 3 for brevity
                    response_parts.append(f"• {item}")
        
        # Add closing
        if template.closing:
            response_parts.append(f"\n{template.closing}")
        
        # Join with appropriate spacing and flow
        response = ""
        for i, part in enumerate(response_parts):
            if i == 0:
                # First part (greeting)
                response = part
            elif part.startswith("•"):
                # List item
                response += f"\n{part}"
            elif part.startswith("\n"):
                # Already has newline
                response += part
            elif i == 1:
                # Acknowledgment (right after greeting)
                response += f" {part}"
            else:
                # Other parts
                response += f" {part}"
        
        return AgentObservation(
            observation=f"Generated conversational template response with {template.tone} tone",
            success=True,
            data={
                "response": response,
                "tone": template.tone.value,
                "method": "template_conversational"
            }
        )
    
    def _generate_llm_response(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Generate more natural, human-like response using LLM"""
        if not self.llm_generator:
            # Fallback to template
            return self._generate_template_response(action_input)
        
        try:
            sentiment = action_input["sentiment"]
            intent = action_input["intent"]
            user_message = action_input["user_message"]
            has_web_info = action_input["has_web_info"]
            
            # Get template as a starting point
            template_response = self._generate_template_response(action_input)
            template_tone = template_response.data.get("tone", "professional")
            
            # Create improved response generation prompt
            prompt = f"""You are a friendly and helpful university assistant at ESB (Esprit School of Business). Generate a natural, conversational response to a student message.

STUDENT MESSAGE: "{user_message}"

CONTEXT:
- Student sentiment: {sentiment} (respond with appropriate empathy)
- Student intent: {intent} (address their specific need)
- Additional information available: {"Yes" if has_web_info else "No"}

TONE GUIDELINES:
- Be warm and personable, like a helpful friend
- Use natural, conversational language (contractions, casual phrases)
- Vary sentence structure and length
- Include appropriate conversational markers (you know, well, actually)
- Add a touch of personality and enthusiasm where appropriate
- Use 1-2 emoji maximum, placed naturally

RESPONSE STRUCTURE:
1. Start with a friendly, personalized greeting
2. Acknowledge their specific question/concern
3. Provide helpful information or support
4. Add 1-2 specific, actionable next steps if relevant
5. End with a warm closing that invites further conversation

IMPORTANT:
- Keep your response concise (3-5 sentences maximum)
- Be specific and relevant to their exact question
- Sound like a real person, not a formal document
- Avoid corporate-sounding language or excessive formality
- Don't use bullet points or numbered lists

Write a natural, helpful response:"""

            # Use the LLM to generate response
            import ollama
            
            response = ollama.chat(
                model=self.settings.ollama_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.7,  # Higher temperature for more natural language
                    "top_p": 0.9,
                    "num_predict": 300
                }
            )
            
            # Extract the generated response
            llm_response = response['message']['content'].strip()
            
            # If LLM response is too short or failed, use template as fallback
            if len(llm_response) < 20:
                logger.warning("LLM response too short, using template fallback")
                return template_response
            
            return AgentObservation(
                observation="Generated natural, human-like response",
                success=True,
                data={
                    "response": llm_response,
                    "tone": template_tone,
                    "method": "llm_natural"
                }
            )
            
        except Exception as e:
            logger.warning(f"Natural response generation failed: {e}, falling back to template")
            return self._generate_template_response(action_input)
    
    def _get_template(self, sentiment: str, intent: str) -> ResponseTemplate:
        """Get appropriate template for sentiment and intent"""
        # Normalize sentiment
        if sentiment not in self.templates:
            sentiment = "neutral"

        # Try to find specific intent template in current sentiment
        sentiment_templates = self.templates[sentiment]
        if intent in sentiment_templates:
            return sentiment_templates[intent]

        # If not found, search across all sentiments for the specific intent
        for sentiment_key, templates in self.templates.items():
            if intent in templates:
                return templates[intent]

        # Fallback to general template for current sentiment
        if "general_info" in sentiment_templates:
            return sentiment_templates["general_info"]

        # Ultimate fallback
        return self.templates["neutral"]["general_info"]

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





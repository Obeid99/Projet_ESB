"""
BigHeadAgent for ESB Chatbot System
Orchestrates the workflow between all agents using ReAct pattern
"""
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
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


class WorkflowStage(str, Enum):
    """Workflow stages for agent orchestration"""
    INITIALIZATION = "initialization"
    ANALYSIS = "analysis"
    INFORMATION_GATHERING = "information_gathering"
    RESPONSE_GENERATION = "response_generation"
    ENHANCEMENT = "enhancement"
    FINALIZATION = "finalization"


class AgentPriority(str, Enum):
    """Agent execution priorities"""
    CRITICAL = "critical"      # Must run (SentimentAgent, IntentAgent)
    HIGH = "high"             # Should run if relevant (WebAgent, RefinerAgent)
    MEDIUM = "medium"         # Optional but beneficial (SelfReflectionAgent)
    LOW = "low"               # Run only if time/resources allow


class WorkflowDecision:
    """Decision about workflow execution"""
    def __init__(
        self,
        stage: WorkflowStage,
        agents_to_run: List[str],
        parallel_execution: bool = False,
        reasoning: str = ""
    ):
        self.stage = stage
        self.agents_to_run = agents_to_run
        self.parallel_execution = parallel_execution
        self.reasoning = reasoning


class BigHeadAgent:
    """
    BigHeadAgent that orchestrates the entire chatbot workflow
    Follows ReAct pattern: Reason -> Act -> Observe
    """
    
    def __init__(
        self, 
        session_id: Optional[str] = None,
        max_processing_time: int = 30  # Maximum processing time in seconds
    ):
        self.settings = get_settings()
        self.session_id = session_id or str(uuid.uuid4())
        self.max_processing_time = max_processing_time
        
        # Agent configurations and priorities
        self.agent_config = {
            "sentiment_agent": {
                "priority": AgentPriority.CRITICAL,
                "dependencies": [],
                "max_execution_time": 5,
                "required_for": ["intent_agent", "refiner_agent", "self_reflection_agent"]
            },
            "intent_agent": {
                "priority": AgentPriority.CRITICAL,
                "dependencies": [],  # Can run in parallel with sentiment
                "max_execution_time": 3,
                "required_for": ["web_agent", "refiner_agent", "self_reflection_agent"]
            },
            "web_agent": {
                "priority": AgentPriority.HIGH,
                "dependencies": ["intent_agent"],
                "max_execution_time": 10,
                "required_for": ["refiner_agent"]
            },
            "refiner_agent": {
                "priority": AgentPriority.CRITICAL,
                "dependencies": ["sentiment_agent", "intent_agent"],
                "max_execution_time": 5,
                "required_for": []
            },
            "self_reflection_agent": {
                "priority": AgentPriority.MEDIUM,
                "dependencies": ["sentiment_agent", "intent_agent"],
                "max_execution_time": 3,
                "required_for": []
            }
        }
        
        # Workflow stages and their agent requirements
        self.workflow_stages = {
            WorkflowStage.ANALYSIS: ["sentiment_agent", "intent_agent"],
            WorkflowStage.INFORMATION_GATHERING: ["web_agent"],
            WorkflowStage.RESPONSE_GENERATION: ["refiner_agent"],
            WorkflowStage.ENHANCEMENT: ["self_reflection_agent"]
        }
        
        logger.info(f"BigHeadAgent initialized, session: {self.session_id}")
    
    def reason(self, state: ChatbotState) -> AgentAction:
        """
        Reasoning step: Determine optimal workflow for the current message
        """
        user_message = state.user_message.strip()
        
        # Check if message is empty or too short
        if not user_message or len(user_message) < 3:
            reasoning = "Message too short for agent processing"
            return AgentAction(
                action="provide_fallback_response",
                action_input={"reason": "insufficient_input"},
                reasoning=reasoning
            )
        
        # Analyze current state to determine what's needed
        workflow_plan = self._analyze_workflow_needs(state)
        
        reasoning = f"Planned workflow: {workflow_plan.stage} with agents {workflow_plan.agents_to_run}"
        return AgentAction(
            action="execute_workflow",
            action_input={
                "workflow_plan": workflow_plan,
                "state": state
            },
            reasoning=reasoning
        )
    
    def _analyze_workflow_needs(self, state: ChatbotState) -> WorkflowDecision:
        """Analyze what agents need to run based on current state"""
        agents_needed = []
        current_stage = self._determine_current_stage(state)
        
        # Always need core analysis if not done
        if not state.sentiment_result:
            agents_needed.append("sentiment_agent")
        
        if not state.intent:
            agents_needed.append("intent_agent")
        
        # Determine if web scraping is needed
        if (state.intent and 
            self._intent_needs_web_info(state.intent) and 
            "web_info" not in state.context):
            agents_needed.append("web_agent")
        
        # Always need response generation if no response
        if not state.response:
            agents_needed.append("refiner_agent")
        
        # Add self-reflection for appropriate scenarios
        if (state.sentiment_result and 
            state.intent and
            self._should_provide_reflection(state) and
            "reflection_prompt" not in state.context):
            agents_needed.append("self_reflection_agent")
        
        # Determine if parallel execution is possible
        parallel_possible = self._can_run_in_parallel(agents_needed, state)
        
        return WorkflowDecision(
            stage=current_stage,
            agents_to_run=agents_needed,
            parallel_execution=parallel_possible,
            reasoning=f"Stage: {current_stage}, Agents needed: {len(agents_needed)}"
        )
    
    def _determine_current_stage(self, state: ChatbotState) -> WorkflowStage:
        """Determine current workflow stage based on state"""
        if not state.sentiment_result or not state.intent:
            return WorkflowStage.ANALYSIS
        elif state.intent and self._intent_needs_web_info(state.intent) and "web_info" not in state.context:
            return WorkflowStage.INFORMATION_GATHERING
        elif not state.response:
            return WorkflowStage.RESPONSE_GENERATION
        elif self._should_provide_reflection(state) and "reflection_prompt" not in state.context:
            return WorkflowStage.ENHANCEMENT
        else:
            return WorkflowStage.FINALIZATION
    
    def _intent_needs_web_info(self, intent: str) -> bool:
        """Check if intent requires web information"""
        web_relevant_intents = [
            "registration_help",
            "event_info",
            "facility_info", 
            "general_info",
            "course_info",
            "schedule_inquiry"
        ]
        return intent in web_relevant_intents
    
    def _should_provide_reflection(self, state: ChatbotState) -> bool:
        """Check if self-reflection would be beneficial"""
        if not state.sentiment_result or not state.intent:
            return False
        
        reflection_worthy_intents = [
            "complaint",
            "academic_support",
            "career_guidance", 
            "personal_sharing"
        ]
        
        sentiment_confidence = state.context.get("sentiment_confidence", 0)
        return (
            state.intent in reflection_worthy_intents and
            sentiment_confidence >= 0.5
        )
    
    def _can_run_in_parallel(self, agents: List[str], state: ChatbotState) -> bool:
        """Determine if agents can run in parallel"""
        # Check dependencies
        for agent in agents:
            config = self.agent_config.get(agent, {})
            dependencies = config.get("dependencies", [])
            
            for dep in dependencies:
                if dep in agents:
                    # Has dependencies in current batch, can't parallelize
                    return False
        
        return len(agents) > 1
    
    def act(self, action: AgentAction) -> AgentObservation:
        """
        Action step: Execute the planned workflow
        """
        try:
            if action.action == "provide_fallback_response":
                return self._provide_fallback_response(action.action_input)
            
            elif action.action == "execute_workflow":
                return self._execute_workflow(action.action_input)
            
            else:
                return AgentObservation(
                    observation=f"Unknown action: {action.action}",
                    success=False,
                    data={}
                )
        
        except Exception as e:
            logger.error(f"Error in BigHeadAgent action: {e}")
            return AgentObservation(
                observation=f"Error during workflow execution: {str(e)}",
                success=False,
                data={}
            )
    
    def _provide_fallback_response(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Provide fallback response for edge cases"""
        fallback_responses = {
            "insufficient_input": "Hello! I'm here to help you with any questions about ESB. Could you please provide more details about what you need assistance with?",
            "processing_error": "I apologize, but I'm experiencing some technical difficulties. Please try rephrasing your question, and I'll do my best to help you.",
            "timeout": "I'm taking longer than expected to process your request. Let me provide you with a quick response while I gather more information."
        }
        
        reason = action_input.get("reason", "processing_error")
        response = fallback_responses.get(reason, fallback_responses["processing_error"])
        
        return AgentObservation(
            observation=f"Provided fallback response for: {reason}",
            success=True,
            data={
                "response": response,
                "fallback_reason": reason,
                "workflow_completed": True
            }
        )
    
    def _execute_workflow(self, action_input: Dict[str, Any]) -> AgentObservation:
        """Execute the planned workflow"""
        workflow_plan = action_input["workflow_plan"]
        state = action_input["state"]
        
        execution_results = []
        
        # For this implementation, we'll simulate agent execution
        # In a real LangGraph implementation, this would trigger the actual agent nodes
        
        for agent_name in workflow_plan.agents_to_run:
            try:
                # Simulate agent execution
                result = self._simulate_agent_execution(agent_name, state)
                execution_results.append({
                    "agent": agent_name,
                    "success": result["success"],
                    "execution_time": result["execution_time"],
                    "output": result["output"]
                })
                
                # Update state with simulated results
                state = self._update_state_with_agent_result(state, agent_name, result)
                
            except Exception as e:
                logger.error(f"Error executing {agent_name}: {e}")
                execution_results.append({
                    "agent": agent_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Determine if workflow is complete
        workflow_complete = self._is_workflow_complete(state)
        
        return AgentObservation(
            observation=f"Executed {len(workflow_plan.agents_to_run)} agents in {workflow_plan.stage} stage",
            success=True,
            data={
                "execution_results": execution_results,
                "workflow_completed": workflow_complete,
                "final_state": state
            }
        )
    
    def _simulate_agent_execution(self, agent_name: str, state: ChatbotState) -> Dict[str, Any]:
        """Simulate agent execution (placeholder for actual agent calls)"""
        import time
        import random
        
        # Simulate processing time
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(min(processing_time, 0.1))  # Actual sleep limited for demo
        
        # Simulate results based on agent type
        if agent_name == "sentiment_agent":
            return {
                "success": True,
                "execution_time": processing_time,
                "output": {
                    "sentiment": "positive",
                    "confidence": 0.85
                }
            }
        elif agent_name == "intent_agent":
            return {
                "success": True,
                "execution_time": processing_time,
                "output": {
                    "intent": "general_info",
                    "confidence": 0.75
                }
            }
        elif agent_name == "web_agent":
            return {
                "success": True,
                "execution_time": processing_time,
                "output": {
                    "web_results": [
                        {"title": "ESB News", "content": "Latest updates from ESB"}
                    ]
                }
            }
        elif agent_name == "refiner_agent":
            return {
                "success": True,
                "execution_time": processing_time,
                "output": {
                    "response": "Thank you for your message! I'm here to help you with any questions about ESB."
                }
            }
        elif agent_name == "self_reflection_agent":
            return {
                "success": True,
                "execution_time": processing_time,
                "output": {
                    "reflection_prompt": "What specific aspect would you like to explore further?"
                }
            }
        
        return {"success": False, "execution_time": processing_time, "output": {}}
    
    def _update_state_with_agent_result(self, state: ChatbotState, agent_name: str, result: Dict[str, Any]) -> ChatbotState:
        """Update state with agent execution results"""
        if not result["success"]:
            return state
        
        output = result["output"]
        
        if agent_name == "sentiment_agent":
            # Would normally update with actual SentimentResult
            state.context["sentiment_simulation"] = output
        elif agent_name == "intent_agent":
            state.intent = output.get("intent")
        elif agent_name == "web_agent":
            state.context["web_info"] = output.get("web_results", [])
        elif agent_name == "refiner_agent":
            state.response = output.get("response")
        elif agent_name == "self_reflection_agent":
            state.context["reflection_prompt"] = output.get("reflection_prompt")
        
        return state
    
    def _is_workflow_complete(self, state: ChatbotState) -> bool:
        """Check if workflow is complete"""
        # Minimum requirements for completion
        has_response = bool(state.response)
        has_basic_analysis = bool(state.intent)
        
        return has_response and has_basic_analysis

    def observe(self, observation: AgentObservation, state: ChatbotState) -> ChatbotState:
        """
        Observation step: Update state with workflow results
        """
        if observation.success:
            execution_data = observation.data

            # Update metadata with workflow information
            state.metadata.update({
                "bighead_agent_session_id": self.session_id,
                "workflow_completed": execution_data.get("workflow_completed", False),
                "agents_executed": [
                    result["agent"] for result in execution_data.get("execution_results", [])
                    if result.get("success", False)
                ],
                "workflow_timestamp": datetime.utcnow().isoformat()
            })

            # Add execution summary to context
            state.context.update({
                "workflow_execution": {
                    "total_agents": len(execution_data.get("execution_results", [])),
                    "successful_agents": len([
                        r for r in execution_data.get("execution_results", [])
                        if r.get("success", False)
                    ]),
                    "completed": execution_data.get("workflow_completed", False)
                }
            })

            logger.info(f"Workflow completed: {execution_data.get('workflow_completed', False)}")

        else:
            logger.error(f"Workflow execution failed: {observation.observation}")
            state.metadata.update({
                "workflow_completed": False,
                "workflow_error": observation.observation
            })

        return state

    def process(self, state: ChatbotState) -> ChatbotState:
        """
        Main processing method implementing ReAct pattern
        """
        logger.info(f"BigHeadAgent orchestrating workflow for: {state.user_message[:50]}...")

        # Step 1: Reason
        action = self.reason(state)
        logger.debug(f"Reasoning: {action.reasoning}")

        # Step 2: Act
        observation = self.act(action)
        logger.debug(f"Action result: {observation.observation}")

        # Step 3: Observe and update state
        updated_state = self.observe(observation, state)

        return updated_state

    def get_workflow_summary(self, state: ChatbotState) -> Dict[str, Any]:
        """Get summary of workflow execution"""
        workflow_info = state.context.get("workflow_execution", {})

        return {
            "session_id": self.session_id,
            "message": state.user_message[:100] + "..." if len(state.user_message) > 100 else state.user_message,
            "agents_executed": state.metadata.get("agents_executed", []),
            "total_agents": workflow_info.get("total_agents", 0),
            "successful_agents": workflow_info.get("successful_agents", 0),
            "completed": workflow_info.get("completed", False),
            "has_response": bool(state.response),
            "has_sentiment": bool(state.sentiment_result),
            "has_intent": bool(state.intent),
            "has_web_info": bool(state.context.get("web_info")),
            "has_reflection": bool(state.context.get("reflection_prompt"))
        }


# LangGraph integration functions
def create_bighead_node(max_processing_time: int = 30):
    """
    Factory function to create a BigHead orchestrator node for LangGraph
    """
    def bighead_node(state: ChatbotState) -> ChatbotState:
        """LangGraph node function for workflow orchestration"""
        agent = BigHeadAgent(
            session_id=state.metadata.get("session_id"),
            max_processing_time=max_processing_time
        )
        return agent.process(state)

    return bighead_node


def should_orchestrate_workflow(state: ChatbotState) -> bool:
    """
    Conditional function for LangGraph to determine if orchestration is needed
    """
    return (
        state.user_message and
        len(state.user_message.strip()) >= 3 and
        not state.metadata.get("workflow_completed", False)
    )

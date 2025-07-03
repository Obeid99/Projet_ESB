"""
LangGraph orchestration for ESB Multi-Agent Chatbot
Defines the agent graph and state for processing chat messages.
"""
from .nodes import sentiment_node, intent_node, web_node, refiner_node, reflection_node
from langgraph.graph import StateGraph, START, END
# from src.state.state import ESBGraphState  # COMMENTED OUT: No such module

def build_esb_graph(sentiment_agent, intent_agent, web_agent, refiner_agent, reflection_agent):
    # Build the agent graph for both student and admin chatbots
    builder = StateGraph(dict)

    # Each agent node is only added if its toggle is enabled in the state['agentStatus'] dict
    def conditional_node(node_name, node_func, agent_key):
        def wrapper(state):
            agent_status = state.get('agentStatus', {})
            if agent_status.get(agent_key, True):
                return node_func(state)
            else:
                # Pass state through unchanged if agent is deactivated
                return state
        return wrapper

    builder.add_node("sentiment", conditional_node("sentiment", lambda state: sentiment_node(state, sentiment_agent), "SentimentAgent"))
    builder.add_node("intent", conditional_node("intent", lambda state: intent_node(state, intent_agent), "IntentAgent"))
    builder.add_node("web", conditional_node("web", lambda state: web_node(state, web_agent), "WebAgent"))
    builder.add_node("refiner", conditional_node("refiner", lambda state: refiner_node(state, refiner_agent), "RefinerAgent"))
    builder.add_node("reflection", conditional_node("reflection", lambda state: reflection_node(state, reflection_agent), "SelfReflectionAgent"))

    # Define the flow: sentiment -> intent -> web -> refiner -> reflection -> END
    builder.add_edge(START, "sentiment")
    builder.add_edge("sentiment", "intent")
    builder.add_edge("intent", "web")
    builder.add_edge("web", "refiner")
    builder.add_edge("refiner", "reflection")
    builder.add_edge("reflection", END)
    return builder.compile()

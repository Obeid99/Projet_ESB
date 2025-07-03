"""
LangGraph orchestration for ESB Multi-Agent Chatbot
Defines the agent graph and state for processing chat messages.
"""
from typing_extensions import TypedDict
from typing import Any
from src.nodes.nodes import sentiment_node, intent_node, web_node, refiner_node, reflection_node
from langgraph.graph import StateGraph, START, END
from src.state.state import ESBGraphState

def build_esb_graph(sentiment_agent, intent_agent, web_agent, refiner_agent, reflection_agent):
    builder = StateGraph(ESBGraphState)
    builder.add_node("sentiment", lambda state: sentiment_node(state, sentiment_agent))
    builder.add_node("intent", lambda state: intent_node(state, intent_agent))
    builder.add_node("web", lambda state: web_node(state, web_agent))
    builder.add_node("refiner", lambda state: refiner_node(state, refiner_agent))
    builder.add_node("reflection", lambda state: reflection_node(state, reflection_agent))
    builder.add_edge(START, "sentiment")
    builder.add_edge("sentiment", "intent")
    builder.add_edge("intent", "web")
    builder.add_edge("web", "refiner")
    builder.add_edge("refiner", "reflection")
    builder.add_edge("reflection", END)
    return builder.compile()

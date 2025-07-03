"""
LangGraph node definitions for ESB Multi-Agent Chatbot
"""
# No node decorator needed in current LangGraph
from ..agents.sentiment_agent import SentimentAgent
from ..agents.intent_agent import IntentAgent
from ..agents.web_agent import WebAgent
from ..agents.refiner_agent import RefinerAgent
from ..agents.self_reflection_agent import SelfReflectionAgent
# from ..graph.esb_graph import ESBGraphState


def sentiment_node(state, agent):
    state["chatbot_state"] = agent.process(state["chatbot_state"])
    return state

def intent_node(state, agent):
    state["chatbot_state"] = agent.process(state["chatbot_state"])
    return state


def web_node(state, agent):
    state["chatbot_state"] = agent.process(state["chatbot_state"])
    return state


def refiner_node(state, agent):
    state["chatbot_state"] = agent.process(state["chatbot_state"])
    return state


def reflection_node(state, agent):
    state["chatbot_state"] = agent.process(state["chatbot_state"])
    return state

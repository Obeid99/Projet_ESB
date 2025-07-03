from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Any

class ESBGraphState(TypedDict):
    user_message: Any
    chatbot_state: Any

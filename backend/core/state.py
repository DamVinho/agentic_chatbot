from typing import TypedDict, Dict, Any, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id : Optional[str] = None

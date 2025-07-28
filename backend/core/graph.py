
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from core.state import ChatState
from core.nodes import ChatNode
from IPython.display import Image, display
from typing import Optional
from langchain_core.runnables import RunnableConfig

class ChatGraph:
    def __init__(self):
        self.chat_node = ChatNode()

        self.memory_saver = MemorySaver()

    def graph_builder(self):
        graph_builder = StateGraph(ChatState)

        # Nodes
        graph_builder.add_node("chat_agent", self.chat_node.run)

        # Edges
        graph_builder.add_edge(START, "chat_agent")

        # return compiled graph
        return graph_builder.compile(checkpointer=self.memory_saver)
    
    @property
    def graph(self):
        if hasattr(self, "_graph"):
            return self._graph
        self._graph = self.graph_builder()
        return self._graph
    
    def display(self):
        display(Image(self.graph.get_graph(xray=True).draw_mermaid_png()))

    def invoke(self, input:str, config: Optional[RunnableConfig]=None):
        return self.graph.invoke(input, config)

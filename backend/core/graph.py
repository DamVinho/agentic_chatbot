
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from core.state import ChatState
from core.nodes import ChatNode
from tools.web_search import ddg_search_tool
from tools.web_search import google_search_tool
from IPython.display import Image, display
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode, tools_condition

class ChatGraph:
    def __init__(self):
        # tools
        self.tools = [ddg_search_tool, google_search_tool]

        # nodes
        self.chat_node = ChatNode(tools=self.tools)      

        # memory saver
        self.memory_saver = MemorySaver()

    def graph_builder(self):
        graph_builder = StateGraph(ChatState)

        # Nodes
        graph_builder.add_node("chat_agent", self.chat_node)
        graph_builder.add_node("tools", ToolNode(self.tools))

        # Edges
        graph_builder.add_edge(START, "chat_agent")
        graph_builder.add_conditional_edges("chat_agent", tools_condition)
        graph_builder.add_edge("tools", "chat_agent")

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

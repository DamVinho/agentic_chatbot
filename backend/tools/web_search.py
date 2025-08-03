from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import tool
from dotenv import load_dotenv
import os

load_dotenv("/workspace/.env") # path to .env file

# web search tool
@tool
def ddg_search_tool(query: str) -> str:
    """Use this tool to search on duckduckgo when up to date informations are needed"""
    return DuckDuckGoSearchRun().run(query)

@tool
def google_search_tool(query: str) -> str:
    """Use this tool to search on google when up to date informations are needed"""
    return SerpAPIWrapper().run(query)

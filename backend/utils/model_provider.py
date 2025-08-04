import re
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from utils.model_params import MODEL_URL, MODEL_NAME, MODEL_TEMP

def load_model(url:str=MODEL_URL, model_name: str=MODEL_NAME, temperature:float=MODEL_TEMP, **kwargs):
    """Load local ollama model"""
    return ChatOllama(base_url=url, model=model_name, temperature=temperature, **kwargs)

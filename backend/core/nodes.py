
from core.state import ChatState
from utils.model_provider import load_model
from utils.model_params import MODEL_URL, MODEL_NAME, MODEL_TEMP, SYSTEM_PROMPT
from langchain_core.messages import SystemMessage


class ChatNode:
    def __init__(self, url:str=MODEL_URL,
                 model_name:str=MODEL_NAME,
                 temperature:float=MODEL_TEMP,
                 system_prompt:str=SYSTEM_PROMPT):
        self.systeme_message = SystemMessage(content=system_prompt)
        self.model = load_model(url, model_name, temperature)

    def run(self, state: ChatState) -> ChatState:
        messages = state["messages"]

        if not messages or type(messages[0]) != SystemMessage:
            messages.insert(0, self.systeme_message)

        response = self.model.invoke(messages)
        state["messages"].append(response)
        return state

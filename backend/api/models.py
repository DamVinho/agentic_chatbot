from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_input: str
    recursion_limit: int=Field(default=25)

class ChatResponse(BaseModel):
    response: str
    session_id: str

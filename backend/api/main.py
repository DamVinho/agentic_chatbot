from fastapi import FastAPI, HTTPException
import logging
from typing import Dict, Any
from api.models import ChatRequest, ChatResponse
from core.graph import ChatGraph
import uuid
import traceback
from langchain_core.messages import HumanMessage


# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# define the app
app = FastAPI(
    title="Smart AI Chat Agent API",
    description="API for interacting with the smart chatbot",
    version="1.0.0"
)

# store chat sessions
chat_sessions : Dict[str, Dict[str, Any]] = {}

# end points
@app.post("/chat/start", response_model=ChatResponse)
async def start_chat(request: ChatRequest):
    """Start a new chat session with the chatbot"""
    try:
        # create a new graph instance
        graph = ChatGraph()

        # generate a unique session id
        session_id = str(uuid.uuid4())

        # run a chat by invoking the graph
        inputs = {"messages":[{"role":"user",
                              "content":request.user_input}]}
        
        config = {
            "recursion_limit":request.recursion_limit,
            "configurable":{"thread_id":session_id}
            }

        output = graph.invoke(
            input=inputs,
            config=config
        )

        # store the graph instance
        chat_sessions[session_id] = {
            "graph": graph,
            "state": output,
            "config": config
        }

        return ChatResponse(
            response=output["messages"][-1].content,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error starting chat: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    
# continue chat
@app.post("/chat/{session_id}/continue", response_model=ChatResponse)
async def continue_chat(session_id:str, request:ChatRequest):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # retrieve session and add user input
    chat_session = chat_sessions[session_id]
    chat_session["state"]["messages"].append(HumanMessage(content=request.user_input))

    # submit to chat
    new_state = chat_session["graph"].invoke(chat_session["state"], chat_session["config"])

    # update session
    chat_sessions[session_id].update({"state": new_state})

    return ChatResponse(
        response=new_state["messages"][-1].content,
        session_id=session_id
    )

from fastapi import FastAPI, HTTPException
import logging
from typing import Dict, Any
from api.models import ChatRequest, ChatResponse, Session, Message, Base
from core.graph import ChatGraph
import uuid
import traceback
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
import re


# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# sqlite database
DATABASE_URL = "sqlite:///./chatbot_sessions.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# define the app
app = FastAPI(
    title="Smart AI Chat Agent API",
    description="API for interacting with the smart chatbot",
    version="2.0.0"
)

# utils function
def remove_think_tags(raw: str) -> str:
    # Remove <think>...</think> block
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    return cleaned


# end points
@app.post("/chat/start", response_model=ChatResponse)
async def start_chat(request: ChatRequest):
    """Start a new chat session with the chatbot"""
    db = SessionLocal()
    try:
        # generate a unique session id
        session_id = str(uuid.uuid4())

        # create a new graph instance
        graph = ChatGraph()        

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

        # save the session to DB
        new_session = Session(id=session_id)
        db.add(new_session)
        db.commit()

        # save messages to DB
        user_msg = Message(session_id=session_id, role="user", content=request.user_input)
        db.add(user_msg)
        ai_msg = Message(session_id=session_id, role="ai", content=output["messages"][-1].content)
        db.add(ai_msg)
        db.commit()    

        return ChatResponse(
            response=remove_think_tags(output["messages"][-1].content),
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error starting chat: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    finally:
        db.close()
    
# continue chat
@app.post("/chat/{session_id}/continue", response_model=ChatResponse)
async def continue_chat(session_id:str, request:ChatRequest):
    db = SessionLocal()
    try:
        session_obj = db.query(Session).filter(Session.id == session_id).first()
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
        

        # get messages and format them
        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
        history = []
        for msg in messages:
            if msg.role == "system":
                history.append({"role":"system", "content":msg.content})
            elif msg.role == "user":
                history.append({"role":"user", "content":msg.content})
            else:
                history.append({"role":"assistant", "content":msg.content})

        # add latest user input
        history.append({"role":"user", "content":request.user_input})

        # invoke graph
        graph = ChatGraph()
        config = {
            "recursion_limit": request.recursion_limit,
            "configurable": {"thread_id": session_id}
        }
        output = graph.invoke(
            input={"messages": history},
            config=config
        )

        # save messages to DB
        user_msg = Message(session_id=session_id, role="user", content=request.user_input)
        ai_msg = Message(session_id=session_id, role="ai", content=output["messages"][-1].content)
        db.add(user_msg)
        db.add(ai_msg)
        db.commit()

        return ChatResponse(
            response=remove_think_tags(output["messages"][-1].content),
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error continuing chat: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=traceback.format_exc())        
    finally:
        db.close()
    

@app.get("/chat/sessions")
async def list_sessions():
    """List all active sessions with metadata"""
    db = SessionLocal()
    try:
        sessions = db.query(Session).order_by(Session.created_at).all()
        return {
            "sessions": [
                {
                    "session_id": s.id,
                    "created_at": s.created_at.isoformat()
                }
                for s in sessions
            ]
        }
    finally:
        db.close()

@app.delete("/chat/{session_id}")
async def end_session(session_id: str):
    """End a chat session"""
    db = SessionLocal()
    try:
        session_obj = db.query(Session).filter(Session.id == session_id).first()
        if not session_obj:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        db.delete(session_obj)
        db.commit()

        return {"message": "Session ended succesfully"}
    finally:
        db.close()


@app.get("/chat/{session_id}/history")
async def get_history(session_id: str):
    """Get full message history for a session"""
    db = SessionLocal()
    try:
        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()

        return [
            {"role": msg.role, "content": remove_think_tags(msg.content), "created_at": msg.created_at.isoformat()}
            for msg in messages
        ]
    finally:
        db.close()

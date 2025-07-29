# Smart AI Agent build with LangGraph, FastAPI & Streamlit

Build a chatbot from scratch with LangGraph, FastAPI & Streamlit. 
The conversation flows will be managed with LangGraph and we will use FastAPI to serve the chatbot endpoint. The Streamlit UI will be used to interact with the backend API.

### Agent Graph 
![Agent graph](./graph.png)



### Frontend
The UI will be chatGPT-like UI

Done:
 - Sessions hitory in the sidebar
 - Add a loading spinner while waiting for ai response
 - Save sessions persistently on disk (json file) and load it on startup

ToDo:

 - Permit session delete and rename from the sidebar?

 ### How to run

 - In the first terminal

 ```
  git clone https://github.com/DamVinho/smart_ai_agent.git
  cd smart_ai_agent/backend
  uvicorn api.main:app --reload
 ```
 
 - In a second terminal
 
 ```
  streamlit run frontend/chatbot_ui.py
 ```
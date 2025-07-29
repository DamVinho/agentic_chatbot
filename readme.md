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
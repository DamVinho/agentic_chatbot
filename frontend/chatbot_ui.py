import streamlit as st
import requests
import uuid

# FastAPI server Url
API_URL = "http://127.0.0.1:8000" # To change when deployed

st.title("Smart chatbot")

# Session state for chat history
if "sessions" not in st.session_state:
    st.session_state.sessions = {} # will be in the form of {session_id: [{"role": ..., "content": ...}]}
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "new_session" not in st.session_state:
    st.session_state.new_session = True # To start a new session at the app startup

# chat sessions sidebar
st.sidebar.header("Sessions")

# show the list of sessions
if st.session_state.sessions:
    session_ids = list(st.session_state.sessions.keys())
    selected_session = st.sidebar.selectbox(
        "Select a session",
        session_ids,
        index=session_ids.index(st.session_state.current_session)
        if st.session_state.current_session in session_ids else 0)
    
    # switch session when seslected
    if selected_session != st.session_state.current_session:
        st.session_state.current_session = selected_session
else:
    st.sidebar.write("No session")

#add button for new session
if st.sidebar.button("New session"):
    st.session_state.current_session = None
    st.session_state.new_session = True


# display chat history
if st.session_state.current_session and st.session_state.current_session in st.session_state.sessions:
    chat_history = st.session_state.sessions[st.session_state.current_session]
else:
    chat_history = []

for message in chat_history:
    role = "user" if message["role"] == "user" else "ai"
    st.chat_message(role).write(message["content"])

# user input field
user_input = st.chat_input("Ask me anything")

if user_input:
    # start a new session if None
    if (not st.session_state.current_session) or st.session_state.new_session:
        response = requests.post(f"{API_URL}/chat/start", json={"user_input":user_input})
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            ai_response = data.get("response")
            st.session_state.current_session = session_id
            st.session_state.sessions[session_id] = [] # init session chat history
            st.session_state.new_session = False
        else:
            st.error("Failed to start chat session.")
            session_id = None
            ai_response = None    
    else:
        # Continue an existing chat
        session_id = st.session_state.current_session
        response = requests.post(f"{API_URL}/chat/{session_id}/continue",
                                 json={"user_input":user_input})
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response")
        else:
            st.error("Failed to continue chat.")
            ai_response = None

    # update session chat history
    if session_id and ai_response:
        st.session_state.sessions[session_id].append({"role":"user", "content":user_input})
        st.chat_message("user").write(user_input)

        st.session_state.sessions[session_id].append({"role":"ai", "content":ai_response})
        st.chat_message("ai").write(ai_response)

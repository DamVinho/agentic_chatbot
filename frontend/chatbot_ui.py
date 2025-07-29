import streamlit as st
import requests

# FastAPI server Url
API_URL = "http://127.0.0.1:8000" # To change when deployed

st.title("Smart chatbot")

# Session state for chat history
if "sessions" not in st.session_state:
    st.session_state.sessions = {} # will be in the form of {friendly_name: [{"role": ..., "content": ...}]}
if "session_id_map" not in st.session_state:
    st.session_state.session_id_map = {}  # {friendly_name: backend_session_id}
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "pending_session" not in st.session_state:
    st.session_state.pending_session = False 

# add a session at startup
if not st.session_state.sessions:
    friendly_name = "Session 1"
    st.session_state.sessions[friendly_name] = []
    st.session_state.current_session = friendly_name
    st.session_state.pending_session = True


# chat sessions sidebar
st.sidebar.header("Sessions")

#add button for new session
if st.sidebar.button("➕ New"):
    # delete pending and unused session
    if (st.session_state.current_session and
        st.session_state.pending_session and
        len(st.session_state.sessions.get(st.session_state.current_session, []))==0):
        del st.session_state.sessions[st.session_state.current_session]

        if st.session_state.current_session in st.session_state.session_id_map:
            del st.session_state.session_id_map[st.session_state.current_session]

    session_count = len(st.session_state.sessions) + 1
    friendly_name = f"Session {session_count}"
    st.session_state.sessions[friendly_name] = []
    st.session_state.current_session = friendly_name
    st.session_state.pending_session = True
    st.rerun()

# show the list of sessions
session_ids = list(st.session_state.sessions.keys())

## if user switched to another session before sending a message delete it
if (st.session_state.pending_session and
    st.session_state.current_session not in session_ids):
    for s_id in session_ids:
        if s_id.startswith("Session") and len(st.session_state.sessions[s_id]) == 0:
            del st.session_state.sessions[s_id]
            if s_id in st.session_state.session_id_map:
                del st.session_state.session_id_map[s_id]

    session_ids = list(st.session_state.sessions.keys())
    st.session_state.pending_session = False


## show sessions in vertical
for s_id in session_ids:
    s_name = f"🟢 {s_id}" if s_id == st.session_state.current_session else s_id
    if st.sidebar.button(s_name, key=f"select_{s_id}"):
        st.session_state.current_session = s_id
        st.session_state.pending_session = (
            len(st.session_state.sessions[s_id]) == 0 and s_id not in st.session_state.session_id_map
        )
        st.rerun()

if not session_ids:
    st.sidebar.write("No session")


# display chat history
chat_history = []
if st.session_state.current_session in st.session_state.sessions:
    chat_history = st.session_state.sessions[st.session_state.current_session]


for message in chat_history:
    role = "user" if message["role"] == "user" else "ai"
    st.chat_message(role).write(message["content"])

# user input field
user_input = st.chat_input("Ask me anything")

if user_input:
    session_id = st.session_state.current_session
    
    # pending ==> start a new session
    if st.session_state.pending_session:

        response = requests.post(f"{API_URL}/chat/start", json={"user_input":user_input})
        if response.status_code == 200:
            data = response.json()
            backend_session_id = data.get("session_id")
            ai_response = data.get("response")

            st.session_state.session_id_map[session_id] = backend_session_id            
            st.session_state.sessions[session_id].append({"role":"user", "content":user_input})
            st.chat_message("user").write(user_input)

            if ai_response:
                st.session_state.sessions[session_id].append({"role":"ai", "content":ai_response})
                st.chat_message("ai").write(ai_response)
        else:
            st.error("Failed to start chat session.")
        
        st.session_state.pending_session = False

    else:
        # Continue an existing chat
        backend_session_id = st.session_state.session_id_map.get(session_id)
        if backend_session_id:
            st.session_state.sessions[session_id].append({"role":"user", "content":user_input})
            st.chat_message("user").write(user_input)

            response = requests.post(f"{API_URL}/chat/{backend_session_id}/continue",
                                     json={"user_input":user_input})
        
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response")

                if ai_response:
                    st.session_state.sessions[session_id].append({"role":"ai", "content":ai_response})
                    st.chat_message("ai").write(ai_response)
            else:
                st.error("Failed to continue chat.")
        else:
            st.error("Session mapping lost, please start a new chat.")

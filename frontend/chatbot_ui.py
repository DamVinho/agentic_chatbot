import streamlit as st
import requests

# FastAPI server Url
API_URL = "http://127.0.0.1:8000" # To change when deployed

st.title("Smart chatbot")

# util functions

def fetch_sessions():
    try:
        resp = requests.get(f"{API_URL}/chat/sessions")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("sessions", [])
    except Exception:
        pass
    return []

def fetch_history(session_id):
    try:
        resp = requests.get(f"{API_URL}/chat/{session_id}/history")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

def delete_session(session_id):
    try:
        resp = requests.delete(f"{API_URL}/chat/{session_id}")
        return resp.status_code == 200
    except Exception:
        return False

# session state variable
if "session_map" not in st.session_state:
    st.session_state.session_map = {} # {session_name: backend_id}: to store friendly name with corresponding backend session id
if "active_session" not in st.session_state:
    st.session_state.active_session = None
if "pending_new_session" not in st.session_state:
    st.session_state.pending_new_session = False


# load and restore saved sessions
backend_sessions = fetch_sessions()
friendly_names = []
backend_map = {}

## build friendly names and mapping
for i, session in enumerate(backend_sessions, 1):
    friendly_id = f"Session {i}"
    friendly_names.append(friendly_id)
    backend_map[friendly_id] = session["session_id"]

## add mapping to session state and restore session
st.session_state.session_map = backend_map
if not st.session_state.active_session and not st.session_state.pending_new_session and friendly_names:
    st.session_state.active_session = friendly_names[-1]

# button to create new session
if st.sidebar.button("➕ New"):
    st.session_state.active_session = None
    st.session_state.pending_new_session = True
    st.rerun()

# chat sessions sidebar title
st.sidebar.header("Sessions")

delete_trigger = None

# show the list of sessions
for idx, friendly_id in enumerate(friendly_names):
    session_id = st.session_state.session_map[friendly_id]
    col1, col2 = st.sidebar.columns([8, 1])
    with col1:
        label = f"🟢 {friendly_id}" if friendly_id == st.session_state.active_session else friendly_id
        if st.button(label, key=f"select_{friendly_id}"):
            st.session_state.active_session = friendly_id
            st.session_state.pending_new_session = False
            st.rerun()
    with col2:
        if st.button("🗑️", key=f"delete_{friendly_id}"):
            delete_trigger = (friendly_id, session_id)

if not friendly_names:
    st.sidebar.write("No session")

# the deletion logic
if delete_trigger is not None:
    del_friendly_id, del_session_id = delete_trigger
    success = delete_session(del_session_id)
    if success:
        # delete from session_map
        session_map = st.session_state.session_map.copy()
        session_names = list(session_map.keys())
        del session_map[del_friendly_id]

        # update current session: move to the next in list or None if empty
        if del_friendly_id == st.session_state.active_session:
            if session_names:
                del_idx = session_names.index(del_friendly_id)
                # pick next session, or previous if at end, or None if none left
                if del_idx < len(session_names) - 1:
                    st.session_state.active_session = session_names[del_idx + 1]
                elif del_idx > 0:
                    st.session_state.active_session = session_names[del_idx - 1]
                else:
                    st.session_state.active_session = None
            else:
                st.session_state.active_session = None
        st.session_state.session_map = session_map
        st.session_state.pending_new_session = False
        st.rerun()
    else:
        st.error("Failed to delete session.")

# display chat history
if st.session_state.active_session and st.session_state.active_session in st.session_state.session_map:
    backend_id = st.session_state.session_map[st.session_state.active_session]
    chat_history = fetch_history(backend_id)
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "ai"
        st.chat_message(role).write(msg["content"])
#elif st.session_state.pending_new_session:
#    st.info("Type a message to start a new chat.")
#    chat_history = []
else:
    st.info("Type a message to start a new chat.")
    chat_history = []

# user input field
user_input = st.chat_input("Ask me anything")

if user_input:
    # if no session is selected, start a new one
    if not friendly_names:
        st.session_state.pending_new_session = True

    # start a new session
    if st.session_state.pending_new_session:
        with st.spinner("Thinking..."):
            response = requests.post(f"{API_URL}/chat/start", json={"user_input": user_input})

        if response.status_code == 200:
            data = response.json()
            session_id = data["session_id"]

            # reload session list as we just created one
            backend_sessions = fetch_sessions()
            friendly_names = []
            backend_map = {}
            for i, session in enumerate(backend_sessions, 1):
                friendly_id = f"Session {i}"
                friendly_names.append(friendly_id)
                backend_map[friendly_id] = session["session_id"]


            # find the name that matches the new session_id
            for friendly_id, backend_sid in backend_map.items():
                if backend_sid == session_id:
                    st.session_state.active_session = friendly_id
                    break
            
            st.session_state.session_map = backend_map
            st.session_state.pending_new_session = False
            st.rerun()
        else:
            st.error("Failed to start chat session.")

    elif st.session_state.active_session and st.session_state.active_session in st.session_state.session_map:
        backend_id = st.session_state.session_map[st.session_state.active_session]
        with st.spinner("Thinking..."):
            response = requests.post(
                f"{API_URL}/chat/{backend_id}/continue",
                json={"user_input": user_input}
            )
        if response.status_code == 200:
            st.rerun()
        else:
            st.error("Failed to continue chat.")

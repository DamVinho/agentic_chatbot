import streamlit as st
import requests
import os
import json

# FastAPI server Url
API_URL = "http://127.0.0.1:8000" # To change when deployed
NAMES_PATH = "session_names.json"

st.title("Smart chatbot")

# util functions
def load_session_names():
    """load session names from persisted file in frontend"""
    if os.path.exists(NAMES_PATH):
        with open(NAMES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_session_names(mapping):
    """save session names to persisted file in frontend"""
    with open(NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f)

def fetch_sessions():
    """get all persisted sessions from the backend"""
    try:
        resp = requests.get(f"{API_URL}/chat/sessions")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("sessions", [])
        else:
            return None  # backend reachable but bad status
    except Exception:
        return None  # backend unreachable

def fetch_history(session_id):
    """get specified session history"""
    try:
        resp = requests.get(f"{API_URL}/chat/{session_id}/history")
        if resp.status_code == 200:
            return resp.json()
        else:
            return None  # backend reachable but bad status
    except Exception:
        return None  # backend unreachable

def delete_session(session_id):
    """delete specified session"""
    try:
        resp = requests.delete(f"{API_URL}/chat/{session_id}")
        if resp.status_code == 200:
            return True
        elif resp.status_code == 404:
            return False  # session not found
        else:
            return None  # other backend error
    except Exception:
        return None  # backend unreachable

def reinit_session_renaming_vars():
    """reinit session renaming variables"""
    st.session_state.renaming_session = None
    st.session_state.rename_value = ""


# session state variables
if "active_session" not in st.session_state:
    st.session_state.active_session = None
if "pending_new_session" not in st.session_state:
    st.session_state.pending_new_session = False
if "renaming_session" not in st.session_state:
    st.session_state.renaming_session = None
if "rename_value" not in st.session_state:
    st.session_state.rename_value = ""


# load and restore saved sessions
backend_sessions = fetch_sessions() # [{"session_id": ..., "created_at": ... }, ...]
names_map = load_session_names() # {backend_session_id: friendly_name}

# each session should have a custom name, if not it's default
used_names = set()
id_to_name = {}
name_to_id = {}

if backend_sessions is not None:
    for i, session in enumerate(backend_sessions, 1):
        sid = session["session_id"]
        # give custom name
        custom_name = names_map.get(sid)
        if custom_name and custom_name not in used_names:
            friendly_name = custom_name
        else:
            # find first available default name
            base = f"Session {i}"
            n = 1
            friendly_name = base
            while friendly_name in used_names:
                friendly_name = f"{base} ({n})"
                n += 1
        id_to_name[sid] = friendly_name
        name_to_id[friendly_name] = sid
        used_names.add(friendly_name)
    # only update names_map if backend is up and we have sessions
    if set(names_map.keys()) != set(id_to_name.keys()):
        names_map = {sid: name for sid, name in id_to_name.items()}
        save_session_names(names_map)
else:
    st.sidebar.error("❌ Backend unreachable.")

# set friendly names and active session
friendly_names = list(name_to_id.keys())
if not st.session_state.active_session and not st.session_state.pending_new_session and friendly_names:
    st.session_state.active_session = friendly_names[-1]


# button to create new session
if st.sidebar.button("➕ New"):
    st.session_state.active_session = None
    st.session_state.pending_new_session = True
    reinit_session_renaming_vars() # stop any session renaming
    st.rerun()

# chat sessions sidebar title
st.sidebar.header("Sessions")

delete_trigger = None
save_rename_trigger = None
rename_error = None

# show the list of sessions
for friendly_name in friendly_names:
    sid = name_to_id[friendly_name]
    row = st.sidebar.container()
    cols = row.columns([1, 1, 5, 1])
    # edit icon
    with cols[0]:
        if st.session_state.renaming_session == friendly_name:
            st.write("✏️")
        else:
            if st.button("✏️", key=f"rename_{friendly_name}"):
                st.session_state.renaming_session = friendly_name
                st.session_state.rename_value = friendly_name
                st.rerun()
    # session label/button or text input
    with cols[2]:
        if st.session_state.renaming_session == friendly_name:
            rename_value = st.text_input(
                "Rename session",
                value=st.session_state.rename_value or friendly_name,
                key=f"rename_input_{friendly_name}", label_visibility="collapsed")
            # save when Enter if value changed
            if rename_value.strip() != friendly_name:
                save_rename_trigger = (friendly_name, rename_value.strip())
        else:
            label = f"🟢 {friendly_name}" if friendly_name == st.session_state.active_session else friendly_name
            if st.button(label, key=f"select_{friendly_name}"):
                st.session_state.active_session = friendly_name
                st.session_state.pending_new_session = False
                reinit_session_renaming_vars() # stop any session renaming
                st.rerun()
    # delete icon
    with cols[3]:
        if st.button("🗑️", key=f"delete_{friendly_name}"):
            delete_trigger = (friendly_name, sid)

if not friendly_names:
    st.sidebar.write("No session")

# the deletion logic
if delete_trigger is not None:
    del_friendly_name, del_session_id = delete_trigger
    result = delete_session(del_session_id)
    reinit_session_renaming_vars() # stop any session renaming
    if result is True:
        # delete from disk-persisted names
        if del_session_id in names_map:
            del names_map[del_session_id]
            save_session_names(names_map)
        # select new active session
        current_names = [name for name in friendly_names if name != del_friendly_name]
        if del_friendly_name == st.session_state.active_session:
            st.session_state.active_session = current_names[-1] if current_names else None
        st.session_state.pending_new_session = False
        st.rerun()
    elif result is False:
        st.error("Session not found on backend.")
    elif result is None:
        st.error("❌ Backend unreachable. Cannot delete session.")

# renaming logic
if save_rename_trigger is not None:
    old_name, new_name = save_rename_trigger
    if not new_name:
        rename_error = "Session name cannot be empty."
    elif new_name in name_to_id and new_name != old_name:
        rename_error = "Session name already exists."
    else:
        # update name
        sid = name_to_id[old_name]
        names_map[sid] = new_name
        save_session_names(names_map)
        # update active session
        if st.session_state.active_session == old_name:
            st.session_state.active_session = new_name
        reinit_session_renaming_vars() # reinit session renaming vars
        st.rerun()
    if rename_error:
        st.session_state.reneme_value = new_name
        st.sidebar.error(rename_error)

# display chat history
if st.session_state.active_session and st.session_state.active_session in name_to_id:
    backend_id = name_to_id[st.session_state.active_session]
    chat_history = fetch_history(backend_id)
    if chat_history is None:
        st.error("❌ Backend unreachable. Cannot load chat history.")
    else:
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "ai"
            st.chat_message(role).write(msg["content"])
else:
    st.info("Type a message to start a new chat.")
    chat_history = []

# user input field
user_input = st.chat_input("Ask me anything")

if user_input:
    reinit_session_renaming_vars() # stop any session renaming

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
            for s in backend_sessions or []:
                if s["session_id"] not in names_map:
                    # assign default name
                    base = f"Session {len(names_map) + 1}"
                    new_name = base
                    n = 1
                    while new_name in names_map.values():
                        new_name = f"{base} ({n})"
                        n += 1
                    names_map[s["session_id"]] = new_name
                    save_session_names(names_map)
                    st.session_state.active_session = new_name
                    break
            
            st.session_state.pending_new_session = False
            st.rerun()
        else:
            st.error("❌ Failed to start chat session.")

    elif st.session_state.active_session and st.session_state.active_session in name_to_id:
        backend_id = name_to_id[st.session_state.active_session]
        with st.spinner("Thinking..."):
            response = requests.post(
                f"{API_URL}/chat/{backend_id}/continue",
                json={"user_input": user_input}
            )
        if response.status_code == 200:
            st.rerun()
        else:
            st.error("❌ Failed to continue chat.")

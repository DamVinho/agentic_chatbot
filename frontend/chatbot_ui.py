import streamlit as st
import requests

# FastAPI server Url
API_URL = "http://127.0.0.1:8000" # To change when deployed

st.title("Smart chatbot")

# Session state for chat history
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# display chat history
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "ai"
    st.chat_message(role).write(message["content"])

# user input field
user_input = st.chat_input("Ask me anything")

if user_input:
    # Add user message to chat history and display it directly
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Detect if the session is new or not
    if st.session_state.session_id is None:
        # Start a new chat session
        response = requests.post(f"{API_URL}/chat/start", json={"user_input":user_input})
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data.get("session_id")
            ai_response = data.get("response")
            st.session_state.messages.append({"role":"ai", "content":ai_response})
            st.chat_message("ai").write(ai_response)

        else:
            st.error("Failed to start chat session.")
    else:
        # Continue an existing chat
        response = requests.post(f"{API_URL}/chat/{st.session_state.session_id}/continue",
                                 json={"user_input":user_input})
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response")
            st.session_state.messages.append({"role":"ai", "content":ai_response})
            st.chat_message("ai").write(ai_response)
        else:
            st.error("Failed to continue chat.")

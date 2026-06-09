import streamlit as st
import os
from src.config import PAGE_TITLE, PAGE_ICON, LAYOUT, GEMINI_API_KEY
from src.engine import initialize_settings, get_index, get_query_engine
from src.utils import setup_logging

# --- Setup ---
setup_logging()

# --- Page Config ---
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# Custom CSS
st.markdown("""
    <style>
    .main { max-width: 1000px; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

st.title("📚 Gemma 4: Unlimited Book Chatbot")
st.markdown("Query large books perfectly using **Gemma 4 31B** and **Local Embeddings** (No Quota Limits).")

# --- API Key Check ---
if not GEMINI_API_KEY:
    st.error("Missing `GEMINI_API_KEY` in `.env` file.")
    st.stop()

# --- State Management ---
if "settings_ready" not in st.session_state:
    with st.status("🚀 Initializing models (Downloading if first time)...", expanded=True) as status:
        try:
            st.session_state.settings_ready = initialize_settings()
            status.update(label="✅ Models Ready!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Failed to initialize models: {e}")
            st.stop()

if "index" not in st.session_state:
    st.session_state.index = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = None

# --- Step 1: File Upload ---
uploaded_file = st.file_uploader("Upload a PDF Book (500+ pages supported)", type="pdf")

if uploaded_file:
    # Reset if a new file is uploaded
    if uploaded_file.name != st.session_state.current_file_name:
        st.session_state.index = None
        st.session_state.chat_history = []
        st.session_state.current_file_name = uploaded_file.name
        
    if st.session_state.index is None:
        with st.status(f"Processing '{uploaded_file.name}'...", expanded=True) as status:
            try:
                index, was_cached = get_index(uploaded_file)
                st.session_state.index = index
                
                label = "✅ Loaded from cache!" if was_cached else "✅ Indexed successfully!"
                status.update(label=label, state="complete", expanded=False)
                
                if was_cached:
                    st.success(f"⚡ Instant Load: Ready to chat about '{uploaded_file.name}'!")
                else:
                    st.success(f"✅ Ready to chat about '{uploaded_file.name}'!")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.session_state.current_file_name = None

# --- Step 2: Chat Interface ---
if st.session_state.index:
    # Sidebar
    with st.sidebar:
        st.success(f"📖 Chatting with: **{st.session_state.current_file_name}**")
        st.divider()
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        if st.button("🔄 Reset & Upload New Book", use_container_width=True, type="primary"):
            st.session_state.index = None
            st.session_state.chat_history = []
            st.session_state.current_file_name = None
            st.rerun()

    # Display History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask anything about the book..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            query_engine = get_query_engine(st.session_state.index)
            with st.status("🧠 Thinking...", expanded=False) as status:
                response = query_engine.query(prompt)
                status.update(label="✅ Found relevant info!", state="complete")
            
            full_response = st.write_stream(response.response_gen)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
else:
    if not uploaded_file:
        st.info("👋 Upload a PDF to start chatting. Local indexing is unlimited!")

import streamlit as st
import os
import tempfile
import torch
import logging
import sys
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
# Updated 2026 imports
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# --- Constants ---
PERSIST_DIR = "./storage"
MODEL_ID = "models/gemma-4-31b-it"
EMBED_MODEL_ID = "BAAI/bge-small-en-v1.5"

# --- Logging Configuration ---
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger("llama_index").setLevel(logging.INFO)

# --- Load Environment ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- Page Config ---
st.set_page_config(
    page_title="Gemma 4 RAG - Book Chatbot",
    page_icon="📚",
    layout="wide"
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
if not api_key:
    st.error("Missing `GEMINI_API_KEY` in `.env` file.")
    st.stop()
else:
    os.environ["GOOGLE_API_KEY"] = api_key

@st.cache_resource
def initialize_settings():
    """Initialize global llama-index settings exactly once."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    llm = GoogleGenAI(model=MODEL_ID, api_key=api_key)
    embed_model = HuggingFaceEmbedding(
        model_name=EMBED_MODEL_ID,
        device=device,
        embed_batch_size=32
    )
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 1024
    return True

# Trigger initialization
if "settings_ready" not in st.session_state:
    with st.status("🚀 Initializing models (Downloading if first time)...", expanded=True) as status:
        st.session_state.settings_ready = initialize_settings()
        status.update(label="✅ Models Ready!", state="complete", expanded=False)

# --- State Management ---
if "index" not in st.session_state:
    st.session_state.index = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = None

# --- Step 1: File Upload ---
uploaded_file = st.file_uploader("Upload a PDF Book (500+ pages supported)", type="pdf")

if uploaded_file:
    # Check if this is a new file
    if uploaded_file.name != st.session_state.current_file_name:
        st.session_state.index = None
        st.session_state.chat_history = []
        st.session_state.current_file_name = uploaded_file.name
        
    if st.session_state.index is None:
        # Check if we have this file indexed already on disk
        file_hash = uploaded_file.name.replace(" ", "_")
        cache_path = os.path.join(PERSIST_DIR, file_hash)
        
        if os.path.exists(cache_path):
            with st.status(f"⚡ Loading '{uploaded_file.name}' from local cache...", expanded=False) as status:
                storage_context = StorageContext.from_defaults(persist_dir=cache_path)
                st.session_state.index = load_index_from_storage(storage_context)
                status.update(label=f"✅ Loaded from cache!", state="complete")
                st.success(f"⚡ Instant Load: Ready to chat about '{uploaded_file.name}'!")
        else:
            with st.status(f"Indexing '{uploaded_file.name}' locally...", expanded=True) as status:
                # Save to temp file
                st.write("📂 Preparing file...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Load and Index (Fast local processing)
                    st.write("📖 Reading PDF content...")
                    reader = SimpleDirectoryReader(input_files=[tmp_path])
                    documents = reader.load_data()
                    
                    st.write(f"🧠 Generating embeddings for {len(documents)} pages...")
                    st.session_state.index = VectorStoreIndex.from_documents(documents, show_progress=True)
                    
                    # PERSIST to disk
                    st.write("💾 Saving to local cache for next time...")
                    os.makedirs(cache_path, exist_ok=True)
                    st.session_state.index.storage_context.persist(persist_dir=cache_path)
                    
                    status.update(label=f"✅ Indexed {len(documents)} pages!", state="complete", expanded=False)
                    st.success(f"✅ Ready to chat about '{uploaded_file.name}'!")
                    
                except Exception as e:
                    st.error(f"❌ Error during indexing: {e}")
                    st.session_state.current_file_name = None 
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

# --- Step 2: Chat Interface ---
if st.session_state.index:
    # Sidebar to show current file info
    with st.sidebar:
        st.success(f"📖 Currently chatting with: **{st.session_state.current_file_name}**")
        
        st.divider()
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
        if st.button("🔄 Reset & Upload New Book", use_container_width=True, type="primary"):
            st.session_state.index = None
            st.session_state.chat_history = []
            st.session_state.current_file_name = None
            st.rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask anything about the book..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Increased top_k for better "Perfect" answers
            query_engine = st.session_state.index.as_query_engine(
                streaming=True, 
                similarity_top_k=8 
            )
            with st.status("🧠 Thinking...", expanded=False) as status:
                response = query_engine.query(prompt)
                status.update(label="✅ Found relevant info!", state="complete")
            
            full_response = st.write_stream(response.response_gen)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
else:
    if not uploaded_file:
        st.info("👋 Upload a PDF to start chatting. Local indexing is unlimited!")

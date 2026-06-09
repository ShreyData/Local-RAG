import os
import torch
import tempfile
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    Settings, 
    StorageContext, 
    load_index_from_storage
)
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from src.config import MODEL_ID, EMBED_MODEL_ID, GEMINI_API_KEY, PERSIST_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from src.utils import get_file_hash, ensure_dir

def initialize_settings():
    """Initialize global llama-index settings."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    llm = GoogleGenAI(model=MODEL_ID, api_key=GEMINI_API_KEY)
    embed_model = HuggingFaceEmbedding(
        model_name=EMBED_MODEL_ID,
        device=device,
        embed_batch_size=32
    )
    
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP
    return True

def get_index(uploaded_file):
    """Load or create a vector index for the uploaded file."""
    file_hash = get_file_hash(uploaded_file.name)
    cache_path = os.path.join(PERSIST_DIR, file_hash)
    
    if os.path.exists(cache_path):
        storage_context = StorageContext.from_defaults(persist_dir=cache_path)
        return load_index_from_storage(storage_context), True
    
    # Create new index
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        reader = SimpleDirectoryReader(input_files=[tmp_path])
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        
        ensure_dir(cache_path)
        index.storage_context.persist(persist_dir=cache_path)
        return index, False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def get_query_engine(index, streaming=True, similarity_top_k=8):
    """Return a query engine for the given index."""
    return index.as_query_engine(
        streaming=streaming,
        similarity_top_k=similarity_top_k
    )

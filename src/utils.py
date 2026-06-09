import logging
import sys
import os

def setup_logging():
    """Configure basic logging for the application."""
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.getLogger("llama_index").setLevel(logging.INFO)

def get_file_hash(filename: str) -> str:
    """Generate a sanitized version of the filename for use as a folder name."""
    return filename.replace(" ", "_").replace(".", "_")

def ensure_dir(path: str):
    """Ensure that a directory exists."""
    os.makedirs(path, exist_ok=True)

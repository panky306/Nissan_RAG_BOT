"""Utility functions for RAG chatbot."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def load_environment() -> dict:
    """Load environment variables from Streamlit Secrets or .env file.
    
    Priority order:
    1. Streamlit Secrets (for Streamlit Cloud)
    2. Environment variables (for Docker/Server)
    3. .env file (for local development)
    """
    api_key = None
    model = "gpt-4o-mini"
    
    # Try Streamlit secrets first (Streamlit Cloud)
    if STREAMLIT_AVAILABLE:
        try:
            api_key = st.secrets.get("openai_api_key")
            model = st.secrets.get("openai_model", model)
        except Exception:
            pass  # Secrets not available, try next source
    
    # Try environment variables
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", model)
    
    # Try .env file (local development)
    if not api_key:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", model)
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. "
            "Please provide it via:\n"
            "  • Streamlit Secrets (Settings → Secrets on Streamlit Cloud)\n"
            "  • OPENAI_API_KEY environment variable\n"
            "  • .env file (for local development)"
        )
    
    return {
        "api_key": api_key,
        "model": model
    }


def get_file_extension(file_path: str) -> str:
    """Get file extension."""
    return Path(file_path).suffix.lower()


def is_supported_format(file_path: str) -> bool:
    """Check if file format is supported."""
    ext = get_file_extension(file_path)
    return ext in [".parquet", ".json", ".csv"]


def format_sql_query(query: str) -> str:
    """Format SQL query for display."""
    return query.strip()

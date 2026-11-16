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
    
    ⚠️  PRODUCTION PRIORITY (Streamlit Cloud):
    1. Streamlit Secrets (REQUIRED for cloud deployment)
    
    🔧 LOCAL DEVELOPMENT PRIORITY:
    1. Streamlit Secrets (if available)
    2. Environment variables
    3. .env file (fallback)
    
    For Streamlit Cloud deployment:
    - Add secrets via: Settings → Secrets
    - Format:
      openai_api_key = "sk-..."
      openai_model = "gpt-4o-mini"
    
    For local development:
    - Use .env file as fallback
    """
    api_key = None
    model = "gpt-4o-mini"
    source = None
    
    # ⭐ PRIORITY 1: Streamlit Secrets (Cloud & Local)
    if STREAMLIT_AVAILABLE:
        try:
            secrets = st.secrets
            if "openai_api_key" in secrets:
                api_key = secrets["openai_api_key"]
                model = secrets.get("openai_model", model)
                source = "Streamlit Secrets"
        except Exception as e:
            pass  # Secrets not available in local dev, try next source
    
    # ⭐ PRIORITY 2: Environment Variables (Docker/Server)
    if not api_key:
        env_api_key = os.getenv("OPENAI_API_KEY")
        if env_api_key:
            api_key = env_api_key
            model = os.getenv("OPENAI_MODEL", model)
            source = "Environment Variable"
    
    # ⭐ PRIORITY 3: .env file (Local Development Only)
    if not api_key:
        # Search multiple locations for .env file
        env_paths = [
            # Chat_Bot root directory (3 levels up from src/utils.py)
            Path(__file__).parent.parent.parent.parent / ".env",
            # Nissan_RAG_BOT directory (1 level up from src/utils.py)
            Path(__file__).parent.parent / ".env",
            # Current working directory
            Path.cwd() / ".env",
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                env_api_key = os.getenv("OPENAI_API_KEY")
                if env_api_key:
                    api_key = env_api_key
                    model = os.getenv("OPENAI_MODEL", model)
                    source = f".env file ({env_path})"
                    break
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found!\n\n"
            "🚀 For Streamlit Cloud Deployment:\n"
            "  1. Go to app settings → Secrets\n"
            "  2. Add:\n"
            "     openai_api_key = \"sk-...\"\n"
            "     openai_model = \"gpt-4o-mini\"\n"
            "  3. Deploy\n\n"
            "🔧 For Local Development:\n"
            "  • Create .env file in Chat_Bot root directory\n"
            "  • Add: OPENAI_API_KEY=sk-...\n"
            "  • Add: OPENAI_MODEL=gpt-4o-mini"
        )
    
    return {
        "api_key": api_key,
        "model": model,
        "source": source
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

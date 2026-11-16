"""Main Streamlit application for RAG chatbot."""
import streamlit as st
import tempfile
import os
from pathlib import Path

from src.utils import load_environment, is_supported_format
from src.llm_handler import LLMHandler
from src.rag_pipeline import RAGPipeline

# Note: API key is loaded from:
# - Streamlit Secrets (Settings → Secrets on Streamlit Cloud)
# - Environment variables (OPENAI_API_KEY)
# - .env file (local development)
# via load_environment() in src/utils.py


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "rag_pipeline" not in st.session_state:
        try:
            env = load_environment()
            llm = LLMHandler(api_key=env["api_key"], model=env["model"])
            st.session_state.rag_pipeline = RAGPipeline(llm)
            st.session_state.chat_history = []
            st.session_state.data_loaded = False
            st.session_state.current_file = None
        except ValueError as e:
            st.error(f"⚠️ Configuration Error: {str(e)}")
            st.info(
                "**For Streamlit Cloud:** Add your OpenAI API key via "
                "Settings → Secrets and restart the app.\n\n"
                "**For Local Development:** Create `.streamlit/secrets.toml` "
                "with your API key."
            )
            st.stop()


def display_sidebar():
    """Display sidebar with controls."""
    st.sidebar.title("📊 Data Upload")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload a data file (Parquet, JSON, or CSV)",
        type=["parquet", "json", "csv"],
        help="Upload a file to query with natural language"
    )
    
    if uploaded_file is not None:
        if not is_supported_format(uploaded_file.name):
            st.sidebar.error("Unsupported file format")
            return
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name
        
        # Load into RAG pipeline
        if st.session_state.rag_pipeline.load_data(tmp_path, "data"):
            st.session_state.data_loaded = True
            st.session_state.current_file = uploaded_file.name
            st.sidebar.success(f"✅ Loaded: {uploaded_file.name}")
            
            # Display table info
            table_info = st.session_state.rag_pipeline.get_table_info()
            if table_info:
                st.sidebar.markdown("---")
                st.sidebar.subheader("📋 Table Info")
                st.sidebar.metric("Rows", table_info["row_count"])
                st.sidebar.metric("Columns", len(table_info["column_names"]))
                
                with st.sidebar.expander("Column Names"):
                    for col in table_info["column_names"]:
                        st.sidebar.text(col)
                
                with st.sidebar.expander("Sample Data"):
                    st.sidebar.dataframe(table_info["sample_data"], width='stretch')
        else:
            st.sidebar.error("Failed to load file")


def display_main_content():
    """Display main chat interface."""
    st.title("🤖 NISSAN Recommendation Engine")
    st.markdown(
        "Ask questions about your data in natural language. "
        "The chatbot will retrieve relevant information and answer your questions."
    )
    
    # Check if data is loaded
    if not st.session_state.data_loaded:
        st.info("👈 Upload a data file in the sidebar to get started!")
        return
    
    # Display current file
    st.success(f"📂 Working with: **{st.session_state.current_file}**")
    
    # Chat history
    st.subheader("💬 Conversation")
    
    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Input section
    st.markdown("---")
    user_input = st.chat_input("Ask a question about your data...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        st.chat_message("user").write(user_input)
        
        # Process question with loading spinner
        with st.spinner("🔍 Processing question..."):
            result = st.session_state.rag_pipeline.process_question(user_input)
        
        # Display results
        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
            assistant_message = f"Error: {result['error']}"
        else:
            # Display answer
            st.chat_message("assistant").write(result["answer"])
            assistant_message = result["answer"]
            
            # Display additional details in expandable sections
            with st.expander("📊 Query Details"):
                st.subheader("SQL Query")
                st.code(result["sql_query"], language="sql")
                
                st.subheader("Query Results")
                st.dataframe(result["query_results"], width='stretch')
                st.caption(f"Returned {result['row_count']} rows")
        
        # Add assistant message to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": assistant_message
        })


def display_footer():
    """Display footer."""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🚀 Powered by Streamlit + DuckDB")
    with col2:
        st.caption("🤖 LLM: OpenAI")
    with col3:
        st.caption("⚡ Local, Private, Fast")


def main():
    """Main application."""
    # Page configuration
    st.set_page_config(
        page_title="RAG Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Display sidebar
    display_sidebar()
    
    # Display main content
    display_main_content()
    
    # Display footer
    display_footer()


if __name__ == "__main__":
    main()

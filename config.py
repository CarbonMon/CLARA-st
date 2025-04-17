# config.py
import os
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "page_title": "Clinical Research Analysis Tool",
    "page_icon": ":mag:",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "openai_models": {
        "gpt-4o": "GPT-4o",
        "gpt-4-turbo": "GPT-4 Turbo",
        "gpt-3.5-turbo": "GPT-3.5 Turbo"
    },
    "claude_models": {
        "claude-3-opus-20240229": "Claude 3 Opus",
        "claude-3-sonnet-20240229": "Claude 3 Sonnet",
        "claude-3-haiku-20240307": "Claude 3 Haiku"
    },
    "default_openai_model": "gpt-4o",
    "default_claude_model": "claude-3-sonnet-20240229",
    "max_pubmed_results": 400,
    "default_pubmed_results": 20,
    "supported_languages": {
        'English': 'eng',
        'French': 'fra',
        'Arabic': 'ara',
        'Spanish': 'spa',
    }
}

# Environment variables or secrets
def get_secrets() -> Dict[str, Any]:
    secrets = {}
    
    # Try to get from streamlit secrets
    try:
        import streamlit as st
        if "ncbi_email" in st.secrets:
            secrets["ncbi_email"] = st.secrets["ncbi_email"]
        if "PM_Key" in st.secrets:
            secrets["ncbi_api_key"] = st.secrets["PM_Key"]
    except:
        pass
    
    # Override with environment variables if available
    if os.environ.get("NCBI_EMAIL"):
        secrets["ncbi_email"] = os.environ.get("NCBI_EMAIL")
    if os.environ.get("NCBI_API_KEY"):
        secrets["ncbi_api_key"] = os.environ.get("NCBI_API_KEY")
    
    return secrets

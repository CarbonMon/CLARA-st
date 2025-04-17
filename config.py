#config for streamlit app
import os
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "page_title": "Clinical Research Analysis Tool",
    "page_icon": ":mag:",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "openai_model": "gpt-4o-mini",
    "openai_base_url": "https://chat.int.bayer.com/api/v2",
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

# authenticates API key
import requests
from typing import Tuple, Optional
import streamlit as st
import openai
from anthropic import Anthropic

def validate_openai_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validates the OpenAI API key by making a test request.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        client = openai.OpenAI(api_key=api_key)
        # Make a simple request to validate the key
        models = client.models.list()
        return True, None
    except Exception as e:
        return False, str(e)

def validate_anthropic_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validates the Anthropic API key by making a test request.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        client = Anthropic(api_key=api_key)
        # Make a simple request to validate the key
        models = client.models.list()
        return True, None
    except Exception as e:
        return False, str(e)

def setup_api_key_ui():
    """Sets up the API key input UI in the sidebar and handles validation"""
    with st.sidebar:
        # Select API provider
        if 'api_provider' not in st.session_state:
            st.session_state['api_provider'] = 'openai'
        
        api_provider = st.radio(
            "Select API Provider",
            ["OpenAI", "Anthropic"],
            index=0 if st.session_state['api_provider'] == 'openai' else 1
        )
        st.session_state['api_provider'] = api_provider.lower()
        
        if not st.session_state.get('api_key_valid', False):
            api_key = st.text_input(f"{api_provider} API Key", type="password")

            if api_key:
                st.session_state['api_key'] = api_key
                
                if st.session_state['api_provider'] == 'openai':
                    is_valid, error = validate_openai_api_key(api_key)
                else:  # anthropic
                    is_valid, error = validate_anthropic_api_key(api_key)
                
                if is_valid:
                    st.session_state['api_key_valid'] = True
                    st.success("API Key Validated! :white_check_mark:")
                else:
                    st.error(f"API Key Invalid: {error}")
                    st.session_state['api_key_valid'] = False

            elif st.session_state.get('api_key') is None:
                st.info(f"Please add your {api_provider} API key to continue.", icon="🗝️")
        else:
            st.success(f"{st.session_state['api_provider'].capitalize()} API Key Authenticated ✓")
            if st.button("Change API Key"):
                st.session_state['api_key_valid'] = False
                st.session_state['api_key'] = None
                st.rerun()

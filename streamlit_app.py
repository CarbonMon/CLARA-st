import streamlit as st
import pandas as pd
import io
import time
import os
import logging
from datetime import datetime

# Import from our modules
from config import DEFAULT_CONFIG, get_secrets
from utils.api_utils import setup_api_key_ui
from utils.ui_utils import (
    initialize_session_state, 
    display_confirmation_dialog,
    display_new_search_dialog,
    display_results_table_and_download,
    display_pdf_text_downloads
)
from services.analysis_service import AnalysisService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize app
def init_app():
    # Configure page
    st.set_page_config(
        page_title=DEFAULT_CONFIG["page_title"],
        page_icon=DEFAULT_CONFIG["page_icon"],
        layout=DEFAULT_CONFIG["layout"],
        initial_sidebar_state=DEFAULT_CONFIG["initial_sidebar_state"],
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Configure NCBI credentials
    secrets = get_secrets()
    if secrets.get("ncbi_email") and secrets.get("ncbi_api_key"):
        from utils.pubmed_utils import configure_entrez
        configure_entrez(secrets["ncbi_email"], secrets["ncbi_api_key"])

# Main app function
def main():
    init_app()
    
    # Sidebar for Inputs
    st.sidebar.header("Clinical Research Analysis Tool")

    # Tab selection
    tab_selection = st.sidebar.radio("Select Source", ["PubMed Search", "PDF Upload"])

    # API Key setup in sidebar
    setup_api_key_ui()

    # Add model selection based on the provider
    with st.sidebar:
        if st.session_state.get('api_key_valid', False):
            if st.session_state['api_provider'] == 'openai':
                model_options = DEFAULT_CONFIG["openai_models"]
                default_model = DEFAULT_CONFIG["default_openai_model"]
            else:  # anthropic
                model_options = DEFAULT_CONFIG["claude_models"]
                default_model = DEFAULT_CONFIG["default_claude_model"]
            
            model_key = f"{st.session_state['api_provider']}_model"
            if model_key not in st.session_state:
                st.session_state[model_key] = default_model
                
            selected_model = st.selectbox(
                "Select Model",
                options=list(model_options.keys()),
                format_func=lambda x: model_options[x],
                index=list(model_options.keys()).index(st.session_state[model_key])
            )
            st.session_state[model_key] = selected_model

    # Add a clear table button in the sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear Results Table"):
        st.session_state['show_clear_confirmation'] = True

    # Show confirmation popup for clearing the table
    if st.session_state['show_clear_confirmation']:
        display_confirmation_dialog()

    # Disable the analysis buttons if the API key is not provided or invalid
    start_analysis_disabled = not st.session_state.get('api_key_valid', False)
    
    # Create client if API key is valid
    client = None
    if st.session_state.get('api_key_valid', False):
        if st.session_state['api_provider'] == 'openai':
            from utils.openai_utils import create_openai_client
            client = create_openai_client(st.session_state['api_key'])
            model = st.session_state.get('openai_model', DEFAULT_CONFIG["default_openai_model"])
        else:  # anthropic
            from utils.claude_utils import create_claude_client
            client = create_claude_client(st.session_state['api_key'])
            model = st.session_state.get('claude_model', DEFAULT_CONFIG["default_claude_model"])
        
        analysis_service = AnalysisService(
            client, 
            st.session_state['api_provider'],
            model
        )
    
    # Main UI based on selected tab
    if tab_selection == "PubMed Search":
        st.title("PubMed Clinical Trial Analysis")
        
        # PubMed search parameters
        query = st.text_input("Search Query", "loratadine") + " AND (clinicaltrial[filter]"
        max_results = st.number_input(
            "Max Results", 
            min_value=1, 
            max_value=DEFAULT_CONFIG["max_pubmed_results"], 
            value=DEFAULT_CONFIG["default_pubmed_results"],
            step=1
        )
        
        # Store the query for file naming
        if query:
            st.session_state['last_query'] = query
        
        # Start PubMed analysis button
        if st.button("Start PubMed Analysis", disabled=start_analysis_disabled):
            # Check if there are existing results
            if st.session_state.get('analysis_results') and len(st.session_state['analysis_results']) > 0:
                st.session_state['show_new_search_dialog'] = True
                
                # Define callback for the dialog
                def pubmed_callback(action):
                    analysis_service.analyze_pubmed_papers(query, max_results, action=action)
                
                # Store callback
                st.session_state['dialog_callback'] = pubmed_callback
            else:
                # No existing results, proceed with new search
                analysis_service.analyze_pubmed_papers(query, max_results, action="new")

    elif tab_selection == "PDF Upload":
        st.title("Clinical Trial PDF Analysis")
        
        # PDF upload parameters
        languages = DEFAULT_CONFIG["supported_languages"]
        
        # OCR options
        ocr_box = st.checkbox('Enable OCR (for scanned documents)')
        if ocr_box:
            language_option = st.selectbox('Select the document language', list(languages.keys()))
        else:
            language_option = "English"
        
        # Multiple file uploader
        pdf_files = st.file_uploader("Upload Clinical Trial PDF(s)", type=['pdf', 'png', 'jpg'], accept_multiple_files=True)
        
        if pdf_files:
            st.write(f"Uploaded {len(pdf_files)} file(s)")
            
            # Process PDFs button
            if st.button("Process and Analyze PDFs", disabled=start_analysis_disabled):
                # Check if there are existing results
                if st.session_state.get('analysis_results') and len(st.session_state['analysis_results']) > 0:
                    st.session_state['show_new_search_dialog'] = True
                    
                    # Define callback for the dialog
                    def pdf_callback(action):
                        analysis_service.analyze_pdf_files(
                            pdf_files, 
                            ocr_box, 
                            languages[language_option], 
                            action=action
                        )
                    
                    # Store callback
                    st.session_state['dialog_callback'] = pdf_callback
                else:
                    # No existing results, proceed with new analysis
                    analysis_service.analyze_pdf_files(
                        pdf_files, 
                        ocr_box, 
                        languages[language_option], 
                        action="new"
                    )

    # Show dialog for new search when results already exist
    if st.session_state.get('show_new_search_dialog', False) and 'dialog_callback' in st.session_state:
        display_new_search_dialog(tab_selection, st.session_state['dialog_callback'])

    # Display Results and Download Button (common for both tabs)
    if st.session_state.get('search_completed', False):
        display_results_table_and_download(st.session_state.get('analysis_results', []), tab_selection)
        
        # If PDF analysis was done, offer text download
        if tab_selection == "PDF Upload" and st.session_state.get('pdf_analysis_completed', False):
            display_pdf_text_downloads(st.session_state.get('pdf_texts', []))

    # Hide Streamlit branding
    hide = """
    <style>
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """
    st.markdown(hide, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

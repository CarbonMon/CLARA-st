import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import time

def initialize_session_state():
    """Initialize all session state variables"""
    if 'analysis_results' not in st.session_state:
        st.session_state['analysis_results'] = []
    if 'progress' not in st.session_state:
        st.session_state['progress'] = 0
    if 'total_papers' not in st.session_state:
        st.session_state['total_papers'] = 0
    if 'search_completed' not in st.session_state:
        st.session_state['search_completed'] = False
    if 'openai_api_key' not in st.session_state:
        st.session_state['openai_api_key'] = None
    if 'api_key_valid' not in st.session_state:
        st.session_state['api_key_valid'] = False
    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame()
    if 'pdf_texts' not in st.session_state:
        st.session_state['pdf_texts'] = []
    if 'pdf_analysis_completed' not in st.session_state:
        st.session_state['pdf_analysis_completed'] = False
    if 'show_clear_confirmation' not in st.session_state:
        st.session_state['show_clear_confirmation'] = False
    if 'show_new_search_dialog' not in st.session_state:
        st.session_state['show_new_search_dialog'] = False
    if 'search_action' not in st.session_state:
        st.session_state['search_action'] = None

def reset_app_state():
    """Reset all session state variables to their defaults"""
    st.session_state['analysis_results'] = []
    st.session_state['progress'] = 0
    st.session_state['total_papers'] = 0
    st.session_state['search_completed'] = False
    st.session_state['pdf_analysis_completed'] = False
    st.session_state['df'] = pd.DataFrame()
    st.session_state['pdf_texts'] = []
    st.session_state['show_clear_confirmation'] = False
    st.session_state['show_new_search_dialog'] = False
    st.session_state['search_action'] = None

def display_confirmation_dialog():
    """Display confirmation dialog for clearing results"""
    with st.sidebar:
        st.warning("⚠️ Are you sure you want to clear all results?")
        col1, col2 = st.columns(2)
        if col1.button("Yes, Clear"):
            reset_app_state()
            st.rerun()
        if col2.button("Cancel"):
            st.session_state['show_clear_confirmation'] = False
            st.rerun()

def display_new_search_dialog(tab_selection: str, callback_fn: callable):
    """Display dialog for handling new search when results exist"""
    dialog_container = st.container()
    with dialog_container:
        st.warning("### Existing results found")
        st.write("Would you like to start a new search with a fresh table or add to the existing table?")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        if col1.button("Start Fresh", key="fresh_button"):
            st.session_state['search_action'] = "new"
            st.session_state['show_new_search_dialog'] = False
            callback_fn(action="new")
            st.rerun()
        
        if col2.button("Add to Existing", key="add_button"):
            st.session_state['search_action'] = "append"
            st.session_state['show_new_search_dialog'] = False
            callback_fn(action="append")
            st.rerun()
            
        if col3.button("Cancel", key="cancel_button"):
            st.session_state['show_new_search_dialog'] = False
            st.rerun()

def display_results_table_and_download(results: List[Dict[str, Any]], tab_selection: str):
    """Display results table with selection and download options"""
    st.success("Analysis Complete!")

    if results:
        df = pd.DataFrame(results)

        # Convert lists to strings in problematic columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = df[col].astype(str)
                except:
                    pass
        
        # Add a selection column to the dataframe
        df.insert(0, " ", False)
        
        # Store the dataframe in session state
        st.session_state['df'] = df
        
        # Display the interactive table with row selection
        st.write("### Select papers to download:")
        
        # Use the data editor with a checkbox column
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            key="results_table"
        )
        
        # Get the selected rows
        selected_df = edited_df[edited_df[" "] == True] if " " in edited_df.columns else pd.DataFrame()
        num_selected = len(selected_df)
        st.write(f"Selected {num_selected} rows")
        
        # File naming based on source
        if tab_selection == "PubMed Search":
            query_word = st.session_state.get('last_query', 'search').split()[0]
            filename = f"PubMed_{query_word}_{time.strftime('%y%m%d')}.xlsx"
        else:
            filename = f"PDF_Analysis_{time.strftime('%y%m%d')}.xlsx"
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        # Download all results
        df_to_save = df.drop(columns=[" "])
        excel_file = io.BytesIO()
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df_to_save.to_excel(writer, index=False)
        excel_file.seek(0)
        
        col1.download_button(
            label="Download All Results",
            data=excel_file,
            file_name=filename,
            mime="application/vnd.ms-excel",
        )
        
        # Download selected rows
        if num_selected > 0:
            selected_filename = f"Selected_{time.strftime('%y%m%d')}.xlsx"
            selected_excel_file = io.BytesIO()
            selected_df_to_save = selected_df.drop(columns=[" "])
            
            with pd.ExcelWriter(selected_excel_file, engine='openpyxl') as writer:
                selected_df_to_save.to_excel(writer, index=False)
            selected_excel_file.seek(0)
            
            col2.download_button(
                label=f"Download Selected ({num_selected}) Rows",
                data=selected_excel_file,
                file_name=selected_filename,
                mime="application/vnd.ms-excel",
            )
        else:
            col2.write("Select rows to enable partial download")

def display_pdf_text_downloads(pdf_texts: List[Dict[str, str]]):
    """Display download buttons for extracted PDF texts"""
    if pdf_texts:
        st.write("### Download Extracted Text:")
        
        for i, pdf_text in enumerate(pdf_texts):
            col1, col2 = st.columns([3, 1])
            col1.write(f"{i+1}. {pdf_text['filename']}")
            col2.download_button(
                label="Download Text",
                data=pdf_text['content'],
                file_name=f"{pdf_text['filename']}.txt",
                mime="text/plain",
                key=f"download_text_{i}"
            )

import streamlit as st
from typing import List, Dict, Any, Optional, Union
import logging
from openai import OpenAI
from anthropic import Anthropic
from utils.openai_utils import analyze_paper_with_openai
from utils.claude_utils import analyze_paper_with_claude
from utils.pubmed_utils import search_and_fetch_pubmed
from utils.pdf_utils import process_file

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for analyzing papers from PubMed or PDFs"""
    
    def __init__(self, client: Union[OpenAI, Anthropic], provider: str = "openai", model: str = None):
        self.client = client
        self.provider = provider.lower()
        self.model = model
    
    def analyze_pubmed_papers(self, query: str, max_results: int, action: str = "new") -> List[Dict[str, Any]]:
        """
        Search PubMed and analyze papers
        
        Args:
            query: PubMed search query
            max_results: Maximum number of results
            action: "new" to start fresh or "append" to add to existing results
            
        Returns:
            List of analyzed papers
        """
        with st.spinner(f"Searching PubMed for '{query}'..."):
            papers = search_and_fetch_pubmed(query, max_results)
            if 'PubmedArticle' in papers:
                st.session_state['total_papers'] = len(papers['PubmedArticle'])
                st.write(f"Found {st.session_state['total_papers']} papers.")
            else:
                st.error("No papers found. Try a different search query.")
                st.session_state['total_papers'] = 0
                return []

        if st.session_state['total_papers'] > 0:
            progress_bar = st.progress(0)
            
            # Initialize or append to results based on action
            if action == "new":
                st.session_state['analysis_results'] = []
            
            for i, paper in enumerate(papers['PubmedArticle']):
                try:
                    with st.spinner(f"Analyzing paper {i+1}/{st.session_state['total_papers']}..."):
                        if self.provider == "openai":
                            result = analyze_paper_with_openai(
                                self.client, 
                                paper, 
                                is_pdf=False,
                                model=self.model
                            )
                        else:  # anthropic
                            result = analyze_paper_with_claude(
                                self.client, 
                                paper, 
                                is_pdf=False,
                                model=self.model
                            )
                        st.session_state['analysis_results'].append(result)
                except Exception as e:
                    st.error(f"Error analyzing paper {i+1}: {e}")
                    logger.error(f"Error analyzing paper: {e}")

                st.session_state['progress'] = (i + 1) / st.session_state['total_papers']
                progress_bar.progress(st.session_state['progress'])

            st.session_state['search_completed'] = True
            return st.session_state['analysis_results']
        
        return []
    
    def analyze_pdf_files(
        self, 
        pdf_files: List[Any], 
        use_ocr: bool = False, 
        language: str = "eng", 
        action: str = "new"
    ) -> List[Dict[str, Any]]:
        """
        Process and analyze PDF files
        
        Args:
            pdf_files: List of PDF file objects
            use_ocr: Whether to use OCR
            language: Language code for OCR
            action: "new" to start fresh or "append" to add to existing results
            
        Returns:
            List of analyzed papers
        """
        st.session_state['total_papers'] = len(pdf_files)
        progress_bar = st.progress(0)
        
        # Initialize or append to results based on action
        if action == "new":
            st.session_state['pdf_texts'] = []
            st.session_state['analysis_results'] = []
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                with st.spinner(f"Processing file {i+1}/{len(pdf_files)}: {pdf_file.name}"):
                    # Process the file
                    processed_file = process_file(pdf_file, use_ocr, language)
                    
                    # Store extracted text
                    st.session_state['pdf_texts'].append({
                        'filename': processed_file['filename'],
                        'content': processed_file['content']
                    })
                    
                    # Analyze the PDF content
                    with st.spinner(f"Analyzing content of {pdf_file.name}..."):
                        if self.provider == "openai":
                            result = analyze_paper_with_openai(
                                self.client, 
                                processed_file['content'], 
                                is_pdf=True,
                                model=self.model
                            )
                        else:  # anthropic
                            result = analyze_paper_with_claude(
                                self.client, 
                                processed_file['content'], 
                                is_pdf=True,
                                model=self.model
                            )
                        # Add filename to result
                        result['Filename'] = pdf_file.name
                        st.session_state['analysis_results'].append(result)
            
            except Exception as e:
                st.error(f"Error processing {pdf_file.name}: {e}")
                logger.error(f"Error processing PDF: {e}")
            
            st.session_state['progress'] = (i + 1) / len(pdf_files)
            progress_bar.progress(st.session_state['progress'])
        
        st.session_state['pdf_analysis_completed'] = True
        st.session_state['search_completed'] = True
        return st.session_state['analysis_results']

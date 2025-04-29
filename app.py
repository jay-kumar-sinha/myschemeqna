import streamlit as st
import pandas as pd
import json
import os
from scheme_qa import SchemeQASystem  # Import our QA system

# Set page configuration
st.set_page_config(
    page_title="MyScheme Portal - Government Scheme QA",
    page_icon="🇮🇳",
    layout="wide"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTextInput>div>div>input {
        font-size: 1.1rem;
    }
    .scheme-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .scheme-name {
        color: #1f77b4;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .scheme-ministry {
        color: #555;
        font-size: 0.9rem;
    }
    .scheme-description {
        margin-top: 10px;
    }
    .highlight {
        background-color: #ffeb3b50;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .footer {
        margin-top: 50px;
        text-align: center;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to load and initialize the QA system
@st.cache_resource
def load_qa_system():
    return SchemeQASystem()

# Function to translate text using Google Translate API
def translate_text(text, target_language="hi"):
    # In a real implementation, you'd use Google Translate API or another service
    # For demonstration, we're using a placeholder function
    if target_language == "hi" and text:
        # This is just a placeholder. In a real application, we'd use a proper translation API
        return f"[Translated to Hindi]: {text}"
    return text

# Main application
def main():
    # Header
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://www.myscheme.gov.in/assets/images/logo.png", width=100)
    with col2:
        st.title("MyScheme Portal - Government Scheme QA")
        st.markdown("Ask questions about government schemes in India")
    
    # Initialize QA system
    qa_system = load_qa_system()
    
    # Language selection
    language = st.sidebar.selectbox(
        "Select Language",
        ["English", "Hindi"],
        index=0
    )
    
    # User query input
    query_placeholder = "What schemes are available for farmers in Maharashtra?" if language == "English" else "महाराष्ट्र में किसानों के लिए कौन सी योजनाएं उपलब्ध हैं?"
    query = st.text_input("Ask a question about government schemes:", placeholder=query_placeholder)
    
    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Searching for relevant schemes..."):
                # Get answer from QA system
                result = qa_system.answer_query(query)
                
                # Display answer
                st.markdown("### Answer")
                answer = result["answer"]
                
                # Translate if Hindi is selected
                if language == "Hindi":
                    answer = translate_text(answer, "hi")
                
                st.markdown(f"<div class='scheme-card'>{answer}</div>", unsafe_allow_html=True)
                
                # Display relevant schemes
                st.markdown("### Relevant Schemes")
                
                for scheme in result["relevant_schemes"]:
                    # Translate if Hindi is selected
                    scheme_name = translate_text(scheme["name"], "hi") if language == "Hindi" else scheme["name"]
                    scheme_desc = translate_text(scheme["description"], "hi") if language == "Hindi" else scheme["description"]
                    scheme_ministry = translate_text(scheme["ministries"], "hi") if language == "Hindi" else scheme["ministries"]
                    scheme_beneficiaries = translate_text(scheme["beneficiaries"], "hi") if language == "Hindi" else scheme["beneficiaries"]
                    
                    # Display scheme card
                    st.markdown(f"""
                    <div class='scheme-card'>
                        <div class='scheme-name'>{scheme_name}</div>
                        <div class='scheme-ministry'>Ministry/Department: {scheme_ministry}</div>
                        <div class='scheme-ministry'>Beneficiaries: {scheme_beneficiaries}</div>
                        <div class='scheme-description'>{scheme_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show sources/chunks used (expandable)
                with st.expander("View Sources"):
                    for i, chunk in enumerate(result["chunks_used"]):
                        st.markdown(f"**Source {i+1}:** From scheme '{chunk['scheme_name']}'")
                        st.text(chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"])
        else:
            st.warning("Please enter a question to search for schemes.")
    
    # Example queries
    st.sidebar.markdown("### Example Questions")
    examples = [
        "What schemes are available for farmers in Maharashtra?",
        "Are there any schemes for women entrepreneurs?",
        "What schemes provide financial assistance for education?",
        "How can senior citizens benefit from government schemes?",
        "What schemes help with affordable housing?"
    ]
    
    if language == "Hindi":
        # Translate example queries (in a real app, these would be properly translated)
        examples = [translate_text(ex, "hi") for ex in examples]
    
    for example in examples:
        if st.sidebar.button(example):
            # Set the query and click the search button programmatically
            st.session_state.query = example
            st.experimental_rerun()
    
    # Footer
    st.markdown("""
    <div class="footer">
        Developed for Prodigal AI Internship Assignment - MyScheme Portal QA System
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
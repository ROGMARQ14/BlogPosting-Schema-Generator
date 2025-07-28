# Main Streamlit application file
# BlogPosting Schema Generator - Production-ready version

import streamlit as st
import logging
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Any, Optional
import time

# Import custom modules
try:
    import extractor
    import analyzer
    import schema_builder
    import utils
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error("Please ensure all required modules (extractor.py, analyzer.py, schema_builder.py, utils.py) are present in the same directory.")
    st.stop()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="BlogPosting Schema AI Architect",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced App Styling ---
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stAlert > div {
        padding: 1rem;
        border-radius: 10px;
    }
    .schema-output {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #0066cc;
    }
    .stage-header {
        background: linear-gradient(90deg, #0066cc, #004499);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 1rem 0 0.5rem 0;
    }
    .metrics-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    .metric-item {
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        min-width: 120px;
    }
</style>
""", unsafe_allow_html=True)

# --- Application Header ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🤖 Schema Architect AI")
    st.subheader("Enterprise-grade BlogPosting schema generator with AI-powered analysis")

with col2:
    st.metric("Version", "2.0", delta="Production Ready")

st.markdown("---")

# --- Enhanced Sidebar ---
with st.sidebar:
    st.header("📋 How to Use")
    st.info(
        """
        **Step-by-step process:**
        1. 📝 **Enter the full URL** of a blog post you want to analyze
        2. 🚀 **Click "Generate Schema"** to start the AI analysis
        3. 🔍 **Review extraction results** in real-time
        4. 📊 **View AI-powered analysis** including keywords
        5. 📋 **Copy the generated JSON-LD schema** for your website

        **Supported formats:**
        - Any public blog post URL
        - WordPress, Medium, Ghost, and custom blogs
        - JSON-LD structured data output
        """
    )

    st.header("🔐 Security & API Setup")
    with st.expander("API Configuration"):
        st.success(
            """
            **For AI keyword generation:**

            Create `.streamlit/secrets.toml`:
            ```toml
            [api_keys]
            gemini = "your_api_key_here"
            ```

            **Get your API key:**
            - Visit [Google AI Studio](https://aistudio.google.com/)
            - Generate a new API key
            - Add it to your secrets file
            """
        )

    st.header("📊 Features")
    st.markdown("""
    ✅ **Smart Content Extraction**  
    ✅ **AI-Powered Keyword Analysis**  
    ✅ **SEO-Optimized Schema Output**  
    ✅ **Real-time Processing Display**  
    ✅ **Error Handling & Validation**  
    ✅ **Mobile-Responsive Design**  
    """)

# --- Input Section ---
st.subheader("🔗 Enter Blog Post URL")
url = st.text_input(
    "Blog Post URL:",
    placeholder="https://example.com/blog/my-awesome-post",
    key="url_input",
    help="Enter the complete URL including https://"
)

# Advanced options in expander
with st.expander("⚙️ Advanced Options"):
    col1, col2 = st.columns(2)
    with col1:
        timeout_setting = st.slider("Request Timeout (seconds)", 10, 60, 15)
        include_keywords = st.checkbox("Generate AI Keywords", value=True)
    with col2:
        debug_mode = st.checkbox("Debug Mode", value=False)
        validate_schema = st.checkbox("Validate Schema Output", value=True)

# --- Main Processing Button ---
if st.button("🚀 Generate Schema", key="generate_button", type="primary", use_container_width=True):
    if not url:
        st.warning("⚠️ Please enter a URL to generate the schema.")
    elif not utils.is_valid_url(url):
        st.error("❌ Please enter a valid URL (e.g., https://example.com/...)")
    else:
        # Processing with enhanced error handling and progress tracking
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("🔄 Initializing schema generation..."):
                start_time = time.time()

                # Stage 1: Data Extraction
                status_text.text("📥 Stage 1: Extracting page data...")
                progress_bar.progress(25)

                st.markdown('<div class="stage-header"><h4>📥 Stage 1: Data Extraction</h4></div>', 
                           unsafe_allow_html=True)

                soup = utils.fetch_url_content(url)
                if not soup:
                    st.error("❌ Could not fetch content from the URL. Please check:")
                    st.error("• URL is accessible and public")
                    st.error("• Website is not blocking automated requests")
                    st.error("• URL returns valid HTML content")
                    st.stop()

                extracted_data = extractor.extract_all_data(soup, url)

                # Display extracted data with better formatting
                col1, col2 = st.columns(2)
                with col1:
                    st.json({
                        "headline": extracted_data.get("headline", "N/A"),
                        "description": extracted_data.get("description", "N/A")[:200] + "..." if len(extracted_data.get("description", "")) > 200 else extracted_data.get("description", "N/A"),
                        "datePublished": extracted_data.get("datePublished", "N/A"),
                        "url": extracted_data.get("url", "N/A")
                    })

                with col2:
                    author_info = extracted_data.get("author", {})
                    publisher_info = extracted_data.get("publisher", {})
                    st.json({
                        "author": author_info.get("name", "N/A") if author_info else "N/A",
                        "publisher": publisher_info.get("name", "N/A") if publisher_info else "N/A",
                        "hasImage": bool(extracted_data.get("image", {}).get("url")),
                        "textLength": len(extracted_data.get("bodyText", ""))
                    })

                # Stage 2: Content Analysis
                progress_bar.progress(50)
                status_text.text("🧠 Stage 2: AI-powered content analysis...")

                st.markdown('<div class="stage-header"><h4>🧠 Stage 2: Content Analysis</h4></div>', 
                           unsafe_allow_html=True)

                analyzed_data = analyzer.analyze_content(extracted_data)

                # Display analysis with metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Word Count", analyzed_data.get("wordCount", 0))
                with col2:
                    st.metric("Keywords Found", len(analyzed_data.get("keywords", [])))
                with col3:
                    reading_time = max(1, analyzed_data.get("wordCount", 0) // 200)
                    st.metric("Reading Time", f"{reading_time} min")

                if analyzed_data.get("keywords"):
                    st.subheader("🏷️ AI-Generated Keywords")
                    # Display keywords as tags
                    keywords_html = "".join([f'<span style="background-color: #e1f5fe; padding: 0.2rem 0.5rem; margin: 0.2rem; border-radius: 15px; display: inline-block; font-size: 0.8rem;">{keyword}</span>' for keyword in analyzed_data.get("keywords", [])[:10]])
                    st.markdown(keywords_html, unsafe_allow_html=True)

                # Combine data
                full_data = {**extracted_data, **analyzed_data}

                # Stage 3 & 4: Schema Assembly
                progress_bar.progress(75)
                status_text.text("⚙️ Stage 3 & 4: Building and finalizing schema...")

                st.markdown('<div class="stage-header"><h4>⚙️ Stage 3 & 4: Schema Assembly</h4></div>', 
                           unsafe_allow_html=True)

                final_schema_script = schema_builder.build_schema(full_data)

                # Final results
                progress_bar.progress(100)
                end_time = time.time()
                processing_time = round(end_time - start_time, 2)
                status_text.text(f"✅ Schema generated successfully in {processing_time}s!")

                # Success metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Processing Time", f"{processing_time}s")
                with col2:
                    st.metric("Schema Size", f"{len(final_schema_script)} chars")
                with col3:
                    st.metric("Data Fields", len([k for k, v in full_data.items() if v]))
                with col4:
                    st.metric("Status", "✅ Complete", delta="Ready")

                st.success("🎉 **Schema Generated Successfully!**")

                # Enhanced schema output with copy functionality
                st.subheader("📋 Generated JSON-LD Schema")
                st.markdown("Copy and paste this code into the `<head>` section of your webpage:")

                # Display schema in a code block with copy button
                st.code(final_schema_script, language="json")

                # Additional helpful information
                with st.expander("📖 How to implement this schema"):
                    st.markdown("""
                    **Implementation Steps:**
                    1. Copy the JSON-LD code above
                    2. Paste it into the `<head>` section of your webpage
                    3. Test your implementation using [Google's Rich Results Test](https://search.google.com/test/rich-results)
                    4. Monitor your search appearance in Google Search Console

                    **Benefits:**
                    - Enhanced search result appearance
                    - Better SEO visibility
                    - Rich snippets in search results
                    - Improved content understanding by search engines
                    """)

                if debug_mode:
                    with st.expander("🔧 Debug Information"):
                        st.json(full_data)

                # Log successful processing
                logger.info(f"Successfully processed URL: {url} in {processing_time}s")

        except Exception as e:
            error_details = traceback.format_exc()
            st.error(f"❌ **An unexpected error occurred:** {str(e)}")

            with st.expander("🔍 Error Details"):
                st.code(error_details, language="text")

            st.markdown("""
            **Troubleshooting Steps:**
            1. Verify the URL is accessible and public
            2. Check if the website blocks automated requests
            3. Ensure all required Python packages are installed
            4. Try with a different blog post URL
            """)

            # Log error
            logger.error(f"Error processing URL {url}: {str(e)}")
            logger.debug(f"Full error details: {error_details}")

# Temporary debugging - add after line 6, before line 7
import sys
import subprocess

st.write("**Environment Diagnostics:**")
try:
    import bs4
    st.success("✅ bs4 module found")
    st.write(f"BeautifulSoup version: {bs4.__version__}")
except ImportError as e:
    st.error(f"❌ bs4 import failed: {e}")
    
# Check installed packages
try:
    result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                          capture_output=True, text=True)
    if "beautifulsoup4" in result.stdout:
        st.success("✅ beautifulsoup4 package installed")
    else:
        st.error("❌ beautifulsoup4 package NOT found")
except Exception as e:
    st.error(f"Package check failed: {e}")

# Remove this diagnostic code after verification

# --- Footer ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🛠️ Built with:**")
    st.markdown("• Streamlit • BeautifulSoup • Google Gemini AI")
with col2:
    st.markdown("**📊 Features:**")
    st.markdown("• Schema.org compliance • SEO optimization • AI analysis")
with col3:
    st.markdown("**🔗 Resources:**")
    st.markdown("[Schema.org](https://schema.org) • [Google Rich Results](https://developers.google.com/search/docs/appearance/structured-data)")

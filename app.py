"""
Streamlit BlogPosting Schema Generator App
-----------------------------------------
Generates SEO-ready BlogPosting JSON-LD from any public blog URL.
"""

import json
import logging
import sys
from typing import Dict, Any

import streamlit as st
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("blogposting-app")

st.set_page_config(
    page_title="BlogPosting Schema Generator",
    page_icon="📝",
    layout="wide",
)

# Import internal modules with error handling
try:
    import extractor
    import analyzer  
    import schema_builder
    import utils
except ModuleNotFoundError as exc:
    st.error(f"Missing required module: {exc}")
    st.error("Please ensure all required modules (extractor.py, analyzer.py, schema_builder.py, utils.py) are present in the same directory.")
    st.stop()

# Streamlit UI
st.title("📝 BlogPosting Schema Generator")

with st.form("url_input_form"):
    target_url = st.text_input(
        "Enter the full URL of the blog post you'd like to convert:",
        placeholder="https://example.com/my-blog-post",
    ).strip()
    submitted = st.form_submit_button("Generate Schema")

if submitted:
    if not target_url:
        st.warning("Please enter a valid, public URL.")
        st.stop()

    # Extract content - Fixed function name detection
    with st.spinner("Fetching & parsing article…"):
        try:
            # Auto-detect the correct extraction function
            if hasattr(extractor, 'extract_content'):
                raw_data: Dict[str, Any] = extractor.extract_content(target_url)
            elif hasattr(extractor, 'extract_blog_data'):
                raw_data: Dict[str, Any] = extractor.extract_blog_data(target_url)
            elif hasattr(extractor, 'extract'):
                raw_data: Dict[str, Any] = extractor.extract(target_url)
            else:
                # List available functions for debugging
                available_functions = [name for name in dir(extractor) 
                                     if callable(getattr(extractor, name)) and not name.startswith('_')]
                st.error(f"❌ Extractor module function not found. Available functions: {available_functions}")
                st.error("Please ensure your extractor.py has one of these functions: extract_content, extract_blog_data, or extract")
                st.stop()
            
            st.success("✅ Content extracted")
        except Exception as exc:
            logger.exception(exc)
            st.error(f"Extraction failed: {exc}")
            st.stop()

    # Analyze content
    with st.spinner("Analyzing article…"):
        try:
            analysis: Dict[str, Any] = analyzer.analyze_content(raw_data)
            st.success("✅ Analysis complete")
        except Exception as exc:
            logger.exception(exc)
            st.error(f"Analysis failed: {exc}")
            st.stop()

    # Build BlogPosting schema
    with st.spinner("Building BlogPosting schema…"):
        try:
            schema_json: Dict[str, Any] = schema_builder.build_schema(
                raw_data, analysis
            )
            pretty_schema = json.dumps(schema_json, indent=2, ensure_ascii=False)
            st.success("✅ Schema ready")
        except Exception as exc:
            logger.exception(exc)
            st.error(f"Schema generation failed: {exc}")
            st.stop()

    # Output results
    st.subheader("Generated BlogPosting JSON-LD")
    st.code(pretty_schema, language="json")

    st.download_button(
        "Download schema.json",
        data=pretty_schema,
        file_name="blogposting-schema.json",
        mime="application/json",
    )

    st.toast("All done 🎉 – copy the JSON-LD into `<head>` of your article!")

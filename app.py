# Main Streamlit application file

import streamlit as st
import extractor
import analyzer
import schema_builder
import utils

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Schema Architect AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- App Styling ---
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    h1, h2, h3 {
        color: #1E2A38;
    }
</style>
""", unsafe_allow_html=True)


# --- Application UI ---

st.title("🤖 Schema Architect AI")
st.subheader("Your expert agent for generating `BlogPosting` schema.")

st.markdown("---")

# --- Sidebar for Instructions ---
with st.sidebar:
    st.header("How to Use")
    st.info(
        """
        1.  **Enter the full URL** of a blog post you want to analyze.
        2.  Click the **"Generate Schema"** button.
        3.  The agent will fetch the page, analyze its content, and build a 
            comprehensive JSON-LD schema.
        4.  The generated schema will appear in the main panel, ready to be copied.
        """
    )
    st.header("Security")
    st.success(
        """
        To use the keyword generation feature, add your Gemini API key to your 
        Streamlit secrets.
        
        Create a `.streamlit/secrets.toml` file with:
        
        `[api_keys]`
        
        `gemini = "YOUR_API_KEY_HERE"`
        """
    )


# --- Main Application Logic ---
url = st.text_input(
    "Enter the Blog Post URL:",
    placeholder="https://example.com/blog/my-awesome-post",
    key="url_input"
)

if st.button("Generate Schema", key="generate_button"):
    if url:
        # Validate URL
        if not utils.URLValidator.is_valid_url(url):
            st.error("Please enter a valid URL (e.g., https://example.com/...)")
        else:
            try:
                with st.spinner("Analyzing page... This may take a moment."):
                    # Stage 1: Data Extraction
                    st.write("### Stage 1: Extracting Data...")
                    extracted_data = extractor.extract(url)
                    st.json(extracted_data)

                    # Stage 2: Content Analysis
                    st.write("### Stage 2: Analyzing Content...")
                    analyzed_data = analyzer.analyze_content(extracted_data)
                    st.json({
                        "wordCount": analyzed_data.get("wordCount"),
                        "keywords": analyzed_data.get("keywords")
                    })

                    # Combine data
                    full_data = {**extracted_data, **analyzed_data}

                    # Stage 3 & 4: Schema Assembly and Finalization
                    st.write("### Stage 3 & 4: Building & Finalizing Schema...")
                    final_schema_script = schema_builder.build_schema(full_data)

                    st.success("✅ Schema Generated Successfully!")
                    st.code(final_schema_script, language="json")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.exception(e)
    else:
        st.warning("Please enter a URL to generate the schema.")

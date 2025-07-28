"""
Streamlit BlogPosting Schema Generator App
-----------------------------------------
Generates SEO-ready BlogPosting JSON-LD from any public blog URL.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
from bs4 import BeautifulSoup  # Critical dependency (verified below)

# ────────────────────────────────────────────────────────────────────────────────
# Global configuration
# ────────────────────────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────────────────────────
# Dependency verification
# ────────────────────────────────────────────────────────────────────────────────
def verify_dependencies() -> None:
    """
    Ensure all runtime dependencies are available inside the Streamlit Cloud
    container before loading custom modules. Stops execution early if a critical
    import is missing so the root cause is clear to the user.
    """
    with st.expander("🔍 Deployment Environment Diagnostics", expanded=False):
        # 1️⃣ Check for BeautifulSoup4
        try:
            import bs4  # noqa: F401
            st.success(f"BeautifulSoup4 loaded (v{bs4.__version__})")
        except ImportError as exc:  # pragma: no cover
            st.error(
                "Critical dependency `beautifulsoup4` is missing. "
                "Please confirm it is pinned in `requirements.txt` and reboot."
            )
            _dump_pip_list()
            st.stop()

        # 2️⃣ (Optionally) list currently-installed packages
        if st.toggle("Show full `pip list`", value=False):
            _dump_pip_list()


def _dump_pip_list() -> None:
    """Utility: stream `pip list` into the expander."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=columns"],
            capture_output=True,
            text=True,
            check=False,
        )
        st.code(result.stdout or "— no output —", language="bash")
    except Exception as exc:  # pragma: no cover
        st.warning(f"Could not fetch package list: {exc}")


# ────────────────────────────────────────────────────────────────────────────────
# Import internal modules (after dependency check)
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    verify_dependencies()

try:
    import extractor            # Local module – fetches & cleans article HTML
    import analyzer             # Local module – NLP analysis & keyword mining
    import schema_builder       # Local module – builds BlogPosting JSON-LD
    import utils                # Local helpers (logging, HTTP headers, etc.)
except ModuleNotFoundError as exc:  # pragma: no cover
    st.exception(exc)
    st.stop()

# ────────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ────────────────────────────────────────────────────────────────────────────────
st.title("📝 BlogPosting Schema Generator")

with st.form("url_input_form"):
    target_url = st.text_input(
        "Enter the full URL of the blog post you’d like to convert:",
        placeholder="https://example.com/my-blog-post",
    ).strip()
    submitted = st.form_submit_button("Generate Schema")

if submitted:
    if not target_url:
        st.warning("Please enter a valid, public URL.")
        st.stop()

    # --------------------------------------------------------------------------
    # 1 Extract content
    # --------------------------------------------------------------------------
    with st.spinner("Fetching & parsing article…"):
        try:
            raw_data: Dict[str, Any] = extractor.extract(target_url)
            st.success("✅ Content extracted")
        except Exception as exc:
            logger.exception(exc)
            st.error(f"Extraction failed: {exc}")
            st.stop()

    # --------------------------------------------------------------------------
    # 2 Analyze content
    # --------------------------------------------------------------------------
    with st.spinner("Analyzing article…"):
        try:
            analysis: Dict[str, Any] = analyzer.analyze_content(raw_data)
            st.success("✅ Analysis complete")
        except Exception as exc:
            logger.exception(exc)
            st.error(f"Analysis failed: {exc}")
            st.stop()

    # --------------------------------------------------------------------------
    # 3 Build BlogPosting schema
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # 4 Output results
    # --------------------------------------------------------------------------
    st.subheader("Generated BlogPosting JSON-LD")
    st.code(pretty_schema, language="json")

    st.download_button(
        "Download schema.json",
        data=pretty_schema,
        file_name="blogposting-schema.json",
        mime="application/json",
    )

    st.toast("All done 🎉 – copy the JSON-LD into `<head>` of your article!")


# ────────────────────────────────────────────────────────────────────────────────
# End of file
# ────────────────────────────────────────────────────────────────────────────────

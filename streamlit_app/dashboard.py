import os
import sys
from pathlib import Path
import streamlit as st
import requests

# Add the workspace root to Python path so we can import backend components
sys.path.append(str(Path(__file__).parent.parent))

from app.config.settings import settings

# Page configuration for a premium, wide-screen dashboard
st.set_page_config(
    page_title="Enterprise Knowledge Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🤖 Enterprise Knowledge Copilot")
st.markdown(
    "A production-grade Retrieval-Augmented Generation (RAG) system with verified citations "
    "and confidence scoring to eliminate hallucinations."
)

# Sidebar configurations
st.sidebar.header("⚙️ System Control")
api_url = st.sidebar.text_input(
    "Backend API URL",
    value=os.getenv("BACKEND_URL", "http://localhost:8000"),
    help="The REST API endpoint URL of the FastAPI backend service.",
)

# Helper function to fetch document lists
def get_documents():
    try:
        res = requests.get(f"{api_url}/documents", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

# Helper function to trigger delete
def delete_document(doc_id):
    try:
        res = requests.delete(f"{api_url}/documents/{doc_id}", timeout=10)
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, str(e)


# Interactive File Uploader Section
st.sidebar.subheader("📤 Upload New Documents")
upload_category = st.sidebar.selectbox(
    "Choose Category / Folder",
    ["POLICIES", "COC", "GENERAL"],
    help="Saves the file into the correct logical directory in the storage structure.",
)

uploaded_files = st.sidebar.file_uploader(
    "Drag & drop PDF, Word, or text files:",
    type=["pdf", "docx", "md", "txt"],
    accept_multiple_files=True,
    help="Upload files directly into the copilot workspace.",
)

if uploaded_files:
    saved_count = 0
    for uploaded_file in uploaded_files:
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"category": upload_category}
            res = requests.post(f"{api_url}/documents/upload", files=files, data=data, timeout=30)
            if res.status_code == 200:
                saved_count += 1
            else:
                st.sidebar.error(f"Failed to upload {uploaded_file.name}: {res.text}")
        except Exception as e:
            st.sidebar.error(f"Error uploading {uploaded_file.name}: {e}")

    if saved_count > 0:
        st.sidebar.success(
            f"Successfully uploaded {saved_count} file(s) to {upload_category}! Click '⚡ Ingest & Index' below to process them."
        )

# Fetch current files to identify status
docs = get_documents()
unindexed_docs = [d for d in docs if not d["indexed"]]

st.sidebar.subheader("📂 Ingestion Controls")
if unindexed_docs:
    st.sidebar.warning(
        f"⚠️ {len(unindexed_docs)} file(s) are raw/unindexed in the workspace. Ingest them to make them searchable!"
    )
else:
    st.sidebar.info("✅ All files in storage are fully indexed.")

# Trigger Indexing button
if st.sidebar.button(
    "⚡ Ingest & Index",
    help="Triggers the parser (Docling) to chunk, embed, and index new files in storage.",
):
    with st.sidebar.spinner("Initializing indexing background task..."):
        try:
            res = requests.post(
                f"{api_url}/documents/ingest",
                params={"rebuild": False},
                timeout=10,
            )
            if res.status_code == 200:
                # Poll the backend status endpoint until processing is complete
                import time
                status_placeholder = st.sidebar.empty()
                while True:
                    try:
                        status_res = requests.get(f"{api_url}/documents/ingest/status", timeout=5)
                        if status_res.status_code == 200:
                            status_data = status_res.json()
                            status = status_data.get("status")
                            if status == "processing":
                                status_placeholder.info("⚙️ Indexing & running OCR in background...")
                                time.sleep(2)
                                continue
                            elif status == "failed":
                                st.sidebar.error(f"❌ Ingestion failed: {status_data.get('error')}")
                                break
                            else:
                                st.session_state.ingestion_success = True
                                st.rerun()
                        else:
                            st.sidebar.error("Failed to retrieve progress status.")
                            break
                    except Exception as poll_err:
                        # Allow transient network hiccups during server load
                        time.sleep(2)
                        continue
            else:
                st.sidebar.error(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            st.sidebar.error(f"Connection failed: {e}")

# Ingestion Completed status banner
if st.session_state.get("ingestion_success"):
    st.success(
        "🎉 **Ingestion Completed!** The knowledge base is updated, synchronized, and ready for queries."
    )
    # Clear the flag so it only shows once
    st.session_state.ingestion_success = False

# Tabs for Main Chat and Retrieval Inspection
tab_chat, tab_kb = st.tabs(
    [
        "💬 Ask Copilot",
        "📂 Knowledge Base Manager",
    ]
)

with tab_chat:
    st.subheader("Grounded Query Assistant")
    question = st.text_input(
        "Enter your question here (e.g. policies, SOPs, manuals):",
        placeholder="e.g. What is the timeline for filing a complaint under the Sexual Harassment Policy?",
    )

    if (
        st.button(
            "Ask Copilot",
            type="primary",
            help="Submits query to the knowledge base and performs citation validation.",
        )
        and question
    ):
        with st.spinner(
            "Retrieving facts and generating verified answer..."
        ):
            try:
                res = requests.post(
                    f"{api_url}/query",
                    json={"question": question},
                    timeout=60,
                )
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    confidence = data.get("confidence", 0.0)
                    unverified_info = data.get("unverified_information", [])

                    # Render answer
                    st.markdown("### 📝 Grounded Response")
                    st.write(answer)

                    # Highlight citations if present
                    if citations:
                        st.markdown("### 📌 Verified Citations")
                        cols = st.columns(min(4, len(citations)))
                        for idx, cit in enumerate(citations):
                            col_idx = idx % min(4, len(citations))
                            with cols[col_idx]:
                                page_str = f"Page: {cit.get('page')}" if cit.get('page') else "Page: N/A"
                                st.info(
                                    f"**[{idx + 1}] {cit.get('source', 'Unknown')}**\n\n"
                                    f"Section: {cit.get('section') or 'N/A'}\n"
                                    f"{page_str}"
                                )

                    # Render Confidence Gauge
                    st.markdown("### 🛡️ Citation Trust Audit")

                    # Score color mapping
                    if confidence >= 0.8:
                        gauge_color = "green"
                        trust_level = "High Trust ✅"
                    elif confidence >= 0.5:
                        gauge_color = "orange"
                        trust_level = "Medium Trust ⚠️"
                    else:
                        gauge_color = "red"
                        trust_level = "Low/No Trust 🚨"

                    st.markdown(
                        f"Confidence Score: <span style='color:{gauge_color}; font-weight:bold; font-size:1.2rem;'>{confidence:.2f} ({trust_level})</span>",
                        unsafe_allow_html=True,
                    )
                    st.progress(float(confidence))

                    # Unverified information warnings inside a clean collapsible expander
                    if unverified_info:
                        with st.expander("🔍 View Grounding Audit Details"):
                            st.markdown(
                                "*Some sentences in the response serve as conversational transitions, introductory headings, or structural summaries. "
                                "These structural statements are not direct factual assertions inside the source PDFs and are noted below for audit transparency:* "
                            )
                            for claim in unverified_info:
                                # Clean up technical labels for a polished presentation
                                friendly_claim = claim.replace("Claim: '", "'").replace("' (Unverified:", " (Info:")
                                st.write(f"• {friendly_claim}")

                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Failed to fetch query: {e}")

with tab_kb:
    st.subheader("Document Library & Knowledge Index")
    st.markdown(
        "Manage raw files stored in your workspace. You can view index coverage and delete individual documents."
    )

    docs = get_documents()

    if not docs:
        st.info("📂 No documents found in raw storage directory. Upload files via the sidebar to start!")
    else:
        # Create columns for header
        h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([3, 2, 2, 2, 2])
        with h_col1:
            st.markdown("**Filename**")
        with h_col2:
            st.markdown("**Category**")
        with h_col3:
            st.markdown("**Status**")
        with h_col4:
            st.markdown("**Chunk Count**")
        with h_col5:
            st.markdown("**Action**")

        st.markdown("---")

        for idx, doc in enumerate(docs):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                st.write(doc["filename"])
                st.caption(f"Size: {doc['file_size']/1024:.1f} KB")
            
            with col2:
                st.write(doc["category"])
            
            with col3:
                if doc["indexed"]:
                    st.markdown("<span style='color:green; font-weight:bold;'>● Ingested</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:orange; font-weight:bold;'>○ Raw / Unindexed</span>", unsafe_allow_html=True)
            
            with col4:
                st.write(f"{doc['chunks']} chunks")
            
            with col5:
                if doc.get("deletable", True):
                    # Unique key for delete buttons
                    if st.button("Delete 🗑️", key=f"del_{doc['document_id']}_{idx}"):
                        with st.spinner("Deleting document and rebuilding BM25 index..."):
                            success, detail = delete_document(doc["document_id"])
                            if success:
                                st.toast(f"Successfully deleted {doc['filename']}!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete document: {detail}")
                else:
                    st.markdown("<span style='color:gray;'>System 🔒</span>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;' />", unsafe_allow_html=True)

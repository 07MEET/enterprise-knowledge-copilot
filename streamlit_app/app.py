import os
import sys
from pathlib import Path
import streamlit as st
import requests

# Add the workspace root to Python path so we can import backend components
sys.path.append(str(Path(__file__).parent.parent))

from app.retrieval.hybrid_retriever import HybridRetriever

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
    "Backend API URL", value="http://localhost:8000"
)

st.sidebar.subheader("📂 Document Ingestion")
rebuild_index = st.sidebar.checkbox(
    "Clear database & rebuild index", value=False
)

if st.sidebar.button("🚀 Ingest Raw Documents"):
    with st.sidebar.spinner("Parsing & Indexing documents..."):
        try:
            res = requests.post(
                f"{api_url}/documents/ingest",
                params={"rebuild": rebuild_index},
                timeout=120,
            )
            if res.status_code == 200:
                data = res.json()
                st.sidebar.success(
                    f"Successfully processed {data.get('documents_processed', 0)} documents!"
                )
                # Show processed files
                if data.get("documents"):
                    st.sidebar.markdown("**Processed Files:**")
                    for doc in data["documents"]:
                        st.sidebar.write(f"- {Path(doc['raw_path']).name}")
            else:
                st.sidebar.error(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            st.sidebar.error(f"Connection failed: {e}")

# Tabs for Main Chat and Retrieval Inspection
tab_chat, tab_inspector = st.tabs(["💬 Ask Copilot", "🔍 Retrieval Inspector"])

with tab_chat:
    st.subheader("Grounded Query Assistant")
    question = st.text_input(
        "Enter your question here (e.g. policies, SOPs, manuals):",
        placeholder="How many vacation days can employees roll over?",
    )

    if st.button("Query KB", type="primary") and question:
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
                    st.markdown("### 📝 Answer")
                    st.write(answer)

                    # Highlight citations if present
                    if citations:
                        st.markdown("### 📌 Verified Citations")
                        cols = st.columns(len(citations))
                        for idx, cit in enumerate(citations):
                            with cols[idx]:
                                st.info(
                                    f"**[{idx + 1}] {cit.get('source', 'Unknown')}**\n\n"
                                    f"Section: {cit.get('section') or 'N/A'}\n"
                                    f"Page: {cit.get('page') or 'N/A'}"
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

                    # Unverified information warnings
                    if unverified_info:
                        st.warning(
                            "⚠️ **The following statements were flagged as unverified (not supported by cited source text):**"
                        )
                        for claim in unverified_info:
                            st.write(f"- {claim}")

                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Failed to fetch query: {e}")

with tab_inspector:
    st.subheader("Dense vs. Sparse Retrieval Visualizer")
    st.markdown(
        "Inspect how Reciprocal Rank Fusion (RRF) merges semantic dense matches (ChromaDB) "
        "and exact sparse matches (BM25) into a unified rank list."
    )

    inspector_query = st.text_input(
        "Enter a query to inspect retrieval ranks:", key="inspector_query"
    )

    if st.button("Inspect Retrieval") and inspector_query:
        with st.spinner("Retrieving matching documents..."):
            try:
                retriever = HybridRetriever()

                # Fetch dense & sparse top 10 results explicitly
                dense_matches = retriever.vector_store.similarity_search(
                    query_embedding=retriever.embedder.embed_query(
                        inspector_query
                    ),
                    k=10,
                )

                if not retriever.bm25_retriever.bm25:
                    retriever.bm25_retriever.load_index()
                sparse_matches = retriever.bm25_retriever.search(
                    query=inspector_query,
                    k=10,
                )

                fused_matches = retriever.reciprocal_rank_fusion(
                    dense_matches, sparse_matches
                )

                # Render side-by-side columns
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("#### 🧠 Dense Matches (ChromaDB)")
                    if dense_matches:
                        for idx, item in enumerate(dense_matches):
                            st.caption(
                                f"Rank {idx+1} | Score: {item.score:.4f}"
                            )
                            st.markdown(
                                f"**Source:** {item.chunk.metadata.get('source')} (Section: {item.chunk.metadata.get('h1', 'N/A')})"
                            )
                            st.text_area(
                                f"Text (ID: {item.chunk.chunk_id[:8]})",
                                value=item.chunk.text,
                                height=120,
                                key=f"dense_{idx}",
                            )
                    else:
                        st.write("No dense matches found.")

                with col2:
                    st.markdown("#### 🔍 Sparse Matches (BM25)")
                    if sparse_matches:
                        for idx, item in enumerate(sparse_matches):
                            st.caption(
                                f"Rank {idx+1} | Score: {item.score:.4f}"
                            )
                            st.markdown(
                                f"**Source:** {item.chunk.metadata.get('source')} (Section: {item.chunk.metadata.get('h1', 'N/A')})"
                            )
                            st.text_area(
                                f"Text (ID: {item.chunk.chunk_id[:8]})",
                                value=item.chunk.text,
                                height=120,
                                key=f"sparse_{idx}",
                            )
                    else:
                        st.write("No sparse matches found.")

                with col3:
                    st.markdown("#### 🔀 Fused Matches (RRF)")
                    if fused_matches:
                        for idx, item in enumerate(fused_matches[:10]):
                            st.caption(
                                f"Rank {idx+1} | RRF Score: {item.score:.4f}"
                            )
                            st.markdown(
                                f"**Source:** {item.chunk.metadata.get('source')} (Section: {item.chunk.metadata.get('h1', 'N/A')})"
                            )
                            st.text_area(
                                f"Text (ID: {item.chunk.chunk_id[:8]})",
                                value=item.chunk.text,
                                height=120,
                                key=f"fused_{idx}",
                            )
                    else:
                        st.write("No fused matches found.")
            except Exception as e:
                st.error(f"Failed to run retrieval inspection: {e}")

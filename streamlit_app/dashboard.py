import sys
import json
import time
import re
from pathlib import Path
import streamlit as st
import requests

# Add the workspace root to Python path
sys.path.append(str(Path(__file__).parent.parent))
from app.config.settings import settings

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Enterprise Knowledge Copilot",
    page_icon="\u2b21",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Injected via st.html so the <style> block is never sanitised ──────────
_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
    --bg:       #0D0D0F;
    --surface:  #141416;
    --border:   rgba(255,255,255,0.08);
    --border-s: rgba(255,255,255,0.05);
    --text:     #EDEDEF;
    --muted:    #8B8B92;
    --accent:   #6366F1;
    --success:  #34D399;
    --warning:  #FBBF24;
    --error:    #F87171;
    --radius:   8px;
}
html, body, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text) !important;
    background-color: var(--bg) !important;
}

/* --- Foolproof Sticky Header CSS --- */

/* 1. Remove Streamlit's default top padding robustly so our math works perfectly */
.main .block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {
    padding-top: 0 !important;
}

.ekc-fixed-header-wrapper {
    height: 5rem !important; /* Exactly match the Streamlit top bar height */
    background-color: var(--bg) !important;
    border-bottom: none !important; /* Removed white line */
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important; /* Center mathematically! */
    box-sizing: border-box !important;
}

/* Natively make the header sticky without any Javascript! */
div.element-container:has(.ekc-fixed-header-wrapper) {
    position: sticky !important;
    top: 3.75rem !important;
    z-index: 99990 !important;
}

/* 2. Force the root app container to be pure black */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    background: var(--bg) !important;
}

/* 3. Streamlit Header: Fully transparent (removing hidden gradient images) so text shines through! */
header[data-testid="stHeader"], 
header[data-testid="stHeader"] *,
header[data-testid="stHeader"]::before,
header[data-testid="stHeader"]::after {
    background-color: transparent !important;
    background-image: none !important;
    background: transparent !important;
    border-bottom: none !important;
}

/* Ensure sidebar stays on top of our fixed header */
[data-testid="stSidebar"] { z-index: 999999 !important; }

/* Header typography */
.ekc-header { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.ekc-header-title { font-size:2.1rem; font-weight:700; color:var(--text); letter-spacing:-0.5px; margin:0; line-height:1.1; }
.ekc-subtitle { font-size:0.8rem; color:var(--muted); margin:0; line-height:1.4; display:none; }

/* Sidebar nav pills */
[data-testid="stSidebar"] div[data-testid="stPills"] { gap:0 !important; border-bottom:1px solid var(--border-s); margin-bottom:12px; padding-bottom:0; background:transparent !important; }
[data-testid="stSidebar"] div[data-testid="stPills"] > div { background:transparent !important; }
[data-testid="stSidebar"] div[data-testid="stPills"] button {
    background:transparent !important; border:none !important; border-radius:0 !important;
    color:var(--muted) !important; font-size:13px !important; font-weight:500 !important;
    padding:8px 12px !important; margin-bottom:-1px !important;
    border-bottom:2px solid transparent !important;
    transition:color 0.15s, border-color 0.15s !important; box-shadow:none !important;
}
[data-testid="stSidebar"] div[data-testid="stPills"] button:hover { color:var(--text) !important; background:transparent !important; }
[data-testid="stSidebar"] div[data-testid="stPills"] button[aria-selected="true"] { color:var(--accent) !important; border-bottom-color:var(--accent) !important; background:transparent !important; box-shadow:none !important; }

/* Nav pills as underline tabs — remove ALL default filled backgrounds */
div[data-testid="stPills"] { gap:0 !important; border-bottom:1px solid var(--border-s); margin-bottom:0; padding-bottom:0; background:transparent !important; }
div[data-testid="stPills"] > div { background:transparent !important; }
div[data-testid="stPills"] button {
    background:transparent !important; border:none !important; border-radius:0 !important;
    color:var(--muted) !important; font-size:13px !important; font-weight:500 !important;
    padding:8px 16px !important; margin-bottom:-1px !important;
    border-bottom:2px solid transparent !important;
    transition:color 0.15s, border-color 0.15s !important;
    box-shadow:none !important;
}
div[data-testid="stPills"] button:hover { color:var(--text) !important; background:transparent !important; box-shadow:none !important; }
div[data-testid="stPills"] button[aria-selected="true"] { color:var(--accent) !important; border-bottom-color:var(--accent) !important; background:transparent !important; box-shadow:none !important; }

[data-testid="stSidebarHeader"] button svg,
[data-testid="stSidebar"] > div:first-child button svg {
    width: 0.7rem !important;
    height: 0.7rem !important;
}

/* Sidebar */
[data-testid="stSidebar"] { background-color:var(--surface) !important; border-right:1px solid var(--border) !important; }
[data-testid="stSidebar"] .block-container { padding-top:1.5rem !important; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { font-size:13px !important; }
.sidebar-section-label { font-size:11px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--muted); margin:1rem 0 0.5rem 0; }

/* LLM radio as segmented control */
[data-testid="stSidebar"] [data-testid="stRadio"] > div { display:flex; flex-direction:row; gap:4px; padding:3px; background:var(--bg); border:1px solid var(--border); border-radius:var(--radius); }
[data-testid="stSidebar"] [data-testid="stRadio"] label { flex:1; text-align:center; padding:5px 8px; border-radius:6px; cursor:pointer; font-size:12px !important; font-weight:500 !important; color:var(--muted) !important; transition:background 0.15s,color 0.15s; white-space:nowrap; overflow:hidden; }

/* Status dot */
.status-dot { display:inline-flex; align-items:center; gap:6px; font-size:12px; color:var(--muted); padding:6px 0; }
.status-dot .dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.dot-success { background:var(--success); }
.dot-warning { background:var(--warning); }
.dot-error   { background:var(--error); }

/* File uploader */
[data-testid="stFileUploadDropzone"] { background:var(--bg) !important; border:1px dashed var(--border) !important; border-radius:var(--radius) !important; }

/* Sidebar buttons */
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button[kind="primary"] {
    width:100%; font-size:13px !important; font-weight:500 !important;
    border-radius:var(--radius) !important; border:1px solid var(--border) !important;
    background:var(--surface) !important; color:var(--text) !important;
    transition:border-color 0.15s, background 0.15s !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover,
[data-testid="stSidebar"] button[kind="primary"]:hover { border-color:var(--accent) !important; background:rgba(99,102,241,0.08) !important; }

/* Sidebar section divider */
.sidebar-divider { border:none; border-top:1px solid var(--border-s); margin:12px 0; }

/* Expander — remove border so Documents section is flat */
[data-testid="stSidebar"] [data-testid="stExpander"] { border:none !important; border-radius:0 !important; background:transparent !important; margin-bottom:0 !important; padding:0 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { display:none !important; }

/* Chat messages — no border, no background */
[data-testid="stChatMessage"] { background:transparent !important; border:none !important; box-shadow:none !important; padding:6px 0 !important; }
[data-testid="stChatMessage"] > div { border:none !important; background:transparent !important; box-shadow:none !important; }
/* Force chat avatar icons to be fully visible (white) in dark mode */
[data-testid*="Avatar"], 
[data-testid*="Avatar"] svg,
[data-testid*="Avatar"] svg path,
[data-testid*="Avatar"] svg circle,
[data-testid*="Avatar"] svg rect {
    color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
}

/* Chat input — borderless */
div[data-testid="stChatInput"] { background-color:var(--bg) !important; padding-top:12px !important; }
div[data-testid="stChatInput"] > div { border:none !important; border-radius:var(--radius) !important; background:var(--surface) !important; box-shadow:none !important; outline:none !important; }
div[data-testid="stChatInput"] > div:focus-within { border:none !important; box-shadow:none !important; outline:none !important; }
div[data-testid="stChatInput"] textarea { background:var(--surface) !important; border:none !important; border-radius:var(--radius) !important; color:var(--text) !important; font-size:14px !important; font-family:Inter,sans-serif !important; box-shadow:none !important; outline:none !important; }
div[data-testid="stChatInput"] textarea:focus { border:none !important; box-shadow:none !important; outline:none !important; }

/* Citation badge */
.cit-badge { display:inline-flex; align-items:center; justify-content:center; background-color:rgba(99,102,241,0.2); color:#a5b4fc; border:1px solid rgba(99,102,241,0.35); border-radius:50%; width:15px; height:15px; font-size:8px; font-weight:700; margin:0 1px; vertical-align:super; line-height:15px; text-align:center; cursor:default; }

/* Confidence row */
.conf-row { display:flex; align-items:center; gap:8px; margin:4px 0 6px 0; font-size:12px; color:var(--muted); }
.conf-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.conf-val { font-weight:600; font-size:12px; }

/* Citation cards */
.citation-section-label { font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); margin:12px 0 8px 0; }
.cit-card { border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; margin-bottom:6px; background:var(--surface); }
.cit-card-header { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.cit-card-num { font-size:11px; font-weight:700; color:#a5b4fc; background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.25); border-radius:4px; padding:1px 6px; flex-shrink:0; }
.cit-card-title { font-size:13px; font-weight:500; color:var(--text); }
.cit-card-meta { font-size:11px; color:var(--muted); }
.cit-snippet { border-left:2px solid rgba(99,102,241,0.4); padding:6px 10px; margin-top:6px; font-size:12px; color:var(--muted); font-style:italic; line-height:1.5; background:rgba(255,255,255,0.02); border-radius:0 4px 4px 0; }

/* Processing pulse */
@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }
.processing-status { display:inline-flex; align-items:center; gap:8px; font-size:13px; color:var(--muted); padding:8px 0; }
.processing-status .pulse-dot { width:7px; height:7px; border-radius:50%; background:var(--accent); animation:pulse 1.4s ease-in-out infinite; }

/* Section header */
.section-header { font-size:13px; font-weight:600; color:var(--text); margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid var(--border-s); }

/* KB table header */
.kb-table-header { display:grid; grid-template-columns:3fr 1.2fr 1.2fr 1fr 0.8fr; gap:8px; padding:6px 8px; font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--border); margin-bottom:4px; }

/* Misc */
[data-testid="stToggle"] { font-size:13px !important; }
[data-testid="stAlert"] { border-radius:var(--radius) !important; border:1px solid var(--border) !important; background:var(--surface) !important; font-size:13px !important; }
.model-caption { font-size:11px; color:var(--muted); margin-top:4px; }
[data-testid="stToast"] { background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:var(--radius) !important; }
</style>
"""
st.html(_CSS)

# ── Sticky header ───────────────────────────────────────────────────────────────
_LAYERS_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"'
    ' fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
    '<polyline points="2 17 12 22 22 17"/>'
    '<polyline points="2 12 12 17 22 12"/>'
    '</svg>'
)

header_container = st.container(key="sticky_header")
with header_container:
    st.markdown(
        f'<div class="ekc-fixed-header-wrapper">'
        f'<div class="ekc-header">{_LAYERS_SVG}'
        '<span class="ekc-header-title">Enterprise Knowledge Copilot</span></div>'
        f'</div>'
        f'<div style="height: 3rem;"></div>', # Match spacer to new top: 0 position
        unsafe_allow_html=True,
    )

st.html("""
    <script>
        function setupFixedHeader() {
            const doc = window.parent.document;
            const mainContainer = doc.querySelector('[data-testid="stMainBlockContainer"]');
            
            // Find newly rendered wrappers that haven't been processed yet
            const newWrapper = doc.querySelector('.ekc-fixed-header-wrapper:not(#active-ekc-header)');
            
            if (newWrapper && mainContainer) {
                // 1. Nuke any old active headers to prevent duplication!
                const oldHeaders = doc.querySelectorAll('#active-ekc-header');
                oldHeaders.forEach(el => el.remove());
                
                // 2. Mark this new one as active and move it to the body (escapes Streamlit's layout traps!)
                newWrapper.id = 'active-ekc-header';
                doc.body.appendChild(newWrapper);
                
                // 3. Make it truly fixed safely at the absolute top of the screen!
                newWrapper.style.position = 'fixed';
                newWrapper.style.top = '0';
                newWrapper.style.zIndex = '99990';
                
                // 4. Sync its horizontal position to exactly match the main content area
                const syncLayout = () => {
                    const rect = mainContainer.getBoundingClientRect();
                    newWrapper.style.left = rect.left + 'px';
                    newWrapper.style.width = rect.width + 'px';
                };
                
                if (window.headerObserver) {
                    window.headerObserver.disconnect();
                }
                window.headerObserver = new ResizeObserver(syncLayout);
                window.headerObserver.observe(mainContainer);
                syncLayout();
            }
        }
        setupFixedHeader(); // Run immediately
        const observer = new MutationObserver(setupFixedHeader);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
""")



# ── Backend URL ─────────────────────────────────────────────────────────────────
api_url = "http://localhost:8000"

# ── Helper functions ────────────────────────────────────────────────────────────
def get_documents():
    try:
        res = requests.get(f"{api_url}/documents", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []


def delete_document(doc_id):
    try:
        res = requests.delete(f"{api_url}/documents/{doc_id}", timeout=10)
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, str(e)


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Navigation at the top of sidebar ──
    page = st.pills(
        "View",
        ["Ask Copilot", "Knowledge Base"],
        default="Ask Copilot",
        label_visibility="collapsed",
    )

    # ── Query Settings ──
    st.markdown("<div class='sidebar-section-label'>Query Settings</div>", unsafe_allow_html=True)

    llm_mode = st.radio(
        "LLM Location",
        ["Cloud", "Local"],
        horizontal=True,
        help="Cloud = OpenRouter (free tier). Local = Ollama on your machine.",
        label_visibility="visible",
    )
    selected_provider = "openrouter" if llm_mode == "Cloud" else "local"

    safe_mode = st.toggle(
        "Citation Audit",
        value=True,
        help="Post-generation verification to detect hallucinations. Disable for 2x speed.",
    )


    # ── Documents ──
    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-section-label'>Documents</div>", unsafe_allow_html=True)

    upload_category = st.selectbox(
        "Category",
        ["POLICIES", "COC", "GENERAL"],
        help="Saves the file into the correct logical directory.",
        label_visibility="visible",
    )
    uploaded_files = st.file_uploader(
        "Drop PDF, Word, or text files",
        type=["pdf", "docx", "md", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        saved_count = 0
        for uploaded_file in uploaded_files:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"category": upload_category}
                res = requests.post(
                    f"{api_url}/documents/upload", files=files, data=data, timeout=30
                )
                if res.status_code == 200:
                    saved_count += 1
                else:
                    st.error(f"Failed: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error: {e}")
        if saved_count > 0:
            st.success(f"Uploaded {saved_count} file(s) to {upload_category}.")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Index status
    docs_sidebar = get_documents()
    unindexed = [d for d in docs_sidebar if not d["indexed"]]
    if unindexed:
        st.markdown(
            f"<div class='status-dot'><span class='dot dot-warning'></span>"
            f"{len(unindexed)} file(s) not yet indexed</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='status-dot'><span class='dot dot-success'></span>"
            "All files indexed</div>",
            unsafe_allow_html=True,
        )

    if st.button(
        "Ingest & Index",
        icon=":material/bolt:",
        help="Parse, chunk, embed and index new files.",
    ):
            with st.spinner("Initializing..."):
                try:
                    res = requests.post(
                        f"{api_url}/documents/ingest", params={"rebuild": False}, timeout=10
                    )
                    if res.status_code == 200:
                        status_ph = st.empty()
                        while True:
                            try:
                                status_res = requests.get(
                                    f"{api_url}/documents/ingest/status", timeout=5
                                )
                                if status_res.status_code == 200:
                                    sdata = status_res.json()
                                    s = sdata.get("status")
                                    if s == "processing":
                                        status_ph.markdown(
                                            "<div class='processing-status'>"
                                            "<span class='pulse-dot'></span>Indexing in background...</div>",
                                            unsafe_allow_html=True,
                                        )
                                        time.sleep(2)
                                        continue
                                    elif s == "failed":
                                        st.error(f"Ingestion failed: {sdata.get('error')}")
                                        break
                                    else:
                                        st.session_state.ingestion_success = True
                                        st.rerun()
                                else:
                                    st.error("Could not retrieve progress.")
                                    break
                            except Exception:
                                time.sleep(2)
                                continue
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

# Ingestion success flash (shows in main area once)
if st.session_state.get("ingestion_success"):
    st.success("Knowledge base updated and ready for queries.")
    st.session_state.ingestion_success = False

# ── Page routing ────────────────────────────────────────────────────────────────
if page == "Ask Copilot":
    if "messages" not in st.session_state:
        st.session_state.messages = []


    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                # Inline citation badge replacement
                def replace_badge(match, _msg=msg):
                    original_id = match.group(1)
                    mapping = _msg.get("citation_mapping", {})
                    num = mapping.get(str(original_id), mapping.get(original_id, original_id))
                    return f'<span class="cit-badge">{num}</span>'

                html_answer = re.sub(r"(?:\[|【)([0-9]+)(?:\]|】)", replace_badge, msg["content"])
                st.markdown(html_answer, unsafe_allow_html=True)

                # Model used
                if msg.get("model_used"):
                    speed_text = f" • ⚡ {msg['response_time']:.1f}s" if msg.get("response_time") else ""
                    st.markdown(
                        f"<div class='model-caption'>via {msg['model_used']}{speed_text}</div>",
                        unsafe_allow_html=True,
                    )

                # Confidence score
                confidence = msg.get("confidence_score")
                v_status = msg.get("verification_status")
                if confidence is not None:
                    if v_status == "VERIFIED":
                        dot_color = "dot-success"
                    elif v_status == "PARTIAL":
                        dot_color = "dot-warning"
                    else:
                        dot_color = "dot-error"
                    st.markdown(
                        f"<div class='conf-row'>"
                        f"<span class='conf-dot {dot_color}'></span>"
                        f"<span class='conf-val'>{confidence*100:.1f}%</span>"
                        f"<span>{v_status or ''}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # Citations
                citations = msg.get("citations", [])
                if citations:
                    with st.expander(f"📚 View {len(citations)} Verified Sources"):
                        for cit in citations:
                            num = cit.get("id", "")
                            source_name = cit.get("source", "Unknown")
                            page_val = cit.get("page")
                            page_str = f"p.{page_val}" if page_val else ""
                            section_str = cit.get("section") or ""
                            meta_parts = [x for x in [page_str, section_str] if x]
                            meta_line = " &middot; ".join(meta_parts)
                            snippet_text = cit.get("snippet") or ""
                            snippet_html = (
                                f"<div class='cit-snippet'>{snippet_text}</div>"
                                if snippet_text
                                else "<div class='cit-snippet' style='color:#444'>No excerpt available.</div>"
                            )
                            st.markdown(
                                f"<div class='cit-card'>"
                                f"<div class='cit-card-header'>"
                                f"<span class='cit-card-num'>{num}</span>"
                                f"<div><div class='cit-card-title'>{source_name}</div>"
                                f"<div class='cit-card-meta'>{meta_line}</div></div>"
                                f"</div>{snippet_html}</div>",
                                unsafe_allow_html=True,
                            )

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # Input + regenerate
    question = st.chat_input("Ask anything about your documents...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            history_payload = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]

            try:
                import time
                start_time = time.time()
                
                status_ph = st.empty()
                status_ph.markdown(
                    "<div class='processing-status'>"
                    "<span class='pulse-dot'></span>Searching knowledge base...</div>",
                    unsafe_allow_html=True,
                )

                if safe_mode:
                    # SAFE MODE: Wait for the full audit pipeline, then render at once (No Streaming)
                    res = requests.post(
                        f"{api_url}/query",
                        json={
                            "question": question,
                            "history": history_payload,
                            "llm_provider": selected_provider,
                            "fast_mode": False,
                        },
                        timeout=300,
                    )
                    
                    if res.status_code == 200:
                        status_ph.empty()
                        data = res.json()
                        full_answer = data.get("answer", "")
                        st.markdown(full_answer)
                        
                        end_time = time.time()
                        
                        # Add verification status string based on confidence
                        conf = data.get("confidence", 0.0)
                        v_status = "VERIFIED" if conf > 0.8 else "PARTIAL" if conf > 0.5 else "UNVERIFIED"
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_answer,
                            "response_time": end_time - start_time,
                            "citations": data.get("citations", []),
                            "model_used": data.get("model_used", ""),
                            "confidence_score": conf,
                            "verification_status": v_status,
                        })
                        st.rerun()
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                        
                else:
                    # FAST MODE: Stream the response instantly without full hallucination audits
                    res = requests.post(
                        f"{api_url}/query/stream",
                        json={
                            "question": question,
                            "history": history_payload,
                            "llm_provider": selected_provider,
                            "fast_mode": True,
                        },
                        stream=True,
                        timeout=300,
                    )
    
                    if res.status_code == 200:
                        status_ph.markdown(
                            "<div class='processing-status'>"
                            "<span class='pulse-dot'></span>Reading documents and thinking...</div>",
                            unsafe_allow_html=True,
                        )
                        chunk_iterator = res.iter_content(chunk_size=None, decode_unicode=True)
                        first_chunk = None
                        try:
                            first_chunk = next(chunk_iterator)
                        except StopIteration:
                            pass
                        status_ph.empty()
    
                        def stream_parser(first, iterator):
                            metadata_str = ""
                            capturing_metadata = False
    
                            def process_chunk(chunk):
                                nonlocal metadata_str, capturing_metadata
                                if chunk:
                                    if "__METADATA__:" in chunk:
                                        parts = chunk.split("__METADATA__:")
                                        if parts[0]:
                                            yield parts[0]
                                        metadata_str += parts[1]
                                        capturing_metadata = True
                                    elif capturing_metadata:
                                        metadata_str += chunk
                                    else:
                                        yield chunk
    
                            if first:
                                yield from process_chunk(first)
                            for chunk in iterator:
                                yield from process_chunk(chunk)
                            if metadata_str:
                                try:
                                    st.session_state.last_metadata = json.loads(metadata_str)
                                except json.JSONDecodeError:
                                    st.session_state.last_metadata = {}
    
                        st.session_state.last_metadata = {}
                        full_answer = st.write_stream(stream_parser(first_chunk, chunk_iterator))
                        
                        end_time = time.time()
    
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_answer,
                            "response_time": end_time - start_time,
                            "citations": st.session_state.last_metadata.get("citations", []),
                            "citation_mapping": st.session_state.last_metadata.get("citation_mapping", {}),
                            "model_used": st.session_state.last_metadata.get("model_used", ""),
                            "confidence_score": st.session_state.last_metadata.get("confidence_score"),
                            "verification_status": st.session_state.last_metadata.get("verification_status"),
                        })
                        st.rerun()
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# ── Knowledge Base Manager ───────────────────────────────────────────────────────
elif page == "Knowledge Base":
    st.markdown(
        "<div class='section-header' style='margin-top:1.5rem'>Document Library</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:13px;color:var(--muted);margin-bottom:1.5rem'>"
        "View indexed files, check coverage, and remove documents from the knowledge base.</p>",
        unsafe_allow_html=True,
    )

    docs = get_documents()

    if not docs:
        st.info("No documents found. Upload files via the sidebar to get started.")
    else:
        st.markdown(
            "<div class='kb-table-header'>"
            "<span>Filename</span><span>Category</span><span>Status</span>"
            "<span>Chunks</span><span>Action</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        for idx, doc in enumerate(docs):
            col1, col2, col3, col4, col5 = st.columns([3, 1.2, 1.2, 1, 0.8])

            with col1:
                st.markdown(
                    f"<span style='font-size:13px;font-weight:500'>{doc['filename']}</span>"
                    f"<br><span style='font-size:11px;color:var(--muted)'>"
                    f"{doc['file_size']/1024:.1f} KB</span>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f"<span style='font-size:12px;color:var(--muted)'>{doc['category']}</span>",
                    unsafe_allow_html=True,
                )
            with col3:
                if doc["indexed"]:
                    st.markdown(
                        "<div class='status-dot'><span class='dot dot-success'></span>Indexed</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div class='status-dot'><span class='dot dot-warning'></span>Raw</div>",
                        unsafe_allow_html=True,
                    )
            with col4:
                st.markdown(
                    f"<span style='font-size:12px;color:var(--muted)'>{doc['chunks']}</span>",
                    unsafe_allow_html=True,
                )
            with col5:
                if doc.get("deletable", True):
                    if st.button(
                        "",
                        key=f"del_{doc['document_id']}_{idx}",
                        icon=":material/delete:",
                        help=f"Delete {doc['filename']}",
                    ):
                        with st.spinner("Deleting..."):
                            success, detail = delete_document(doc["document_id"])
                            if success:
                                st.toast(f"Deleted {doc['filename']}")
                                st.rerun()
                            else:
                                st.error(f"Failed: {detail}")
                else:
                    st.markdown(
                        "<span style='font-size:11px;color:var(--muted)'>System</span>",
                        unsafe_allow_html=True,
                    )

            st.markdown(
                "<div style='height:1px;background:var(--border-s);margin:4px 0'></div>",
                unsafe_allow_html=True,
            )

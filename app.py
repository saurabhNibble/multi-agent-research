import os
import re
import uuid
import streamlit as st
from dotenv import load_dotenv

from src.pipelines.pipeline import run_research_pipeline

# --------------------------------------------------
# Configuration & Environment
# --------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="Research AI",
    page_icon="⌕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Clean, Minimalist & Responsive Styling
# --------------------------------------------------
st.markdown("""
<style>
    /* Remove default top padding for a clean look */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 5rem;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Clean brand header in sidebar */
    .brand-box {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0 16px 0;
    }
    .brand-icon {
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: #2563EB;
        color: white;
        font-size: 18px;
        font-weight: 700;
    }
    .brand-title {
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .brand-tagline {
        font-size: 0.78rem;
        opacity: 0.65;
        margin-top: -2px;
    }

    /* Welcome Hero */
    .welcome-card {
        text-align: center;
        padding: 8vh 1rem 2rem 1rem;
    }
    .welcome-symbol {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 52px;
        height: 52px;
        border-radius: 14px;
        background: rgba(37, 99, 235, 0.1);
        color: #2563EB;
        font-size: 26px;
        margin-bottom: 14px;
    }
    .welcome-title {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        margin-bottom: 8px;
    }
    .welcome-subtitle {
        font-size: 1.05rem;
        opacity: 0.7;
        max-width: 520px;
        margin: 0 auto 24px auto;
        line-height: 1.6;
    }

    /* Critic Evaluation Card */
    .critic-card {
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0;
        border: 1px solid rgba(245, 158, 11, 0.3);
        background: rgba(245, 158, 11, 0.05);
    }
    .critic-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .critic-score {
        font-size: 1.25rem;
        font-weight: 700;
        color: #F59E0B;
    }

    /* Source Link formatting */
    .source-item {
        font-size: 0.9rem;
        line-height: 1.7;
        margin-bottom: 4px;
    }

    /* Touch-friendly buttons on mobile */
    @media (max-width: 768px) {
        .welcome-card {
            padding-top: 4vh;
        }
        .welcome-title {
            font-size: 1.6rem;
        }
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def extract_score(feedback: str):
    """Extract numeric score from critic feedback text."""
    if not feedback:
        return None
    match = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def extract_sources(text: str) -> list[str]:
    """Extract clean, unique URLs from research content."""
    urls = re.findall(r"https?://[^\s\)\"\'<>]+", text)
    seen = set()
    cleaned = []
    for u in urls:
        u = u.rstrip(".,;:)")
        if u not in seen and "tavily" not in u.lower():
            seen.add(u)
            cleaned.append(u)
    return cleaned


# --------------------------------------------------
# Session State Management
# --------------------------------------------------
if "sessions" not in st.session_state:
    st.session_state.sessions = []

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "model" not in st.session_state:
    st.session_state.model = "gemini-3.1-flash-lite"

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.3


# --------------------------------------------------
# Sidebar: Brand, History & Settings
# --------------------------------------------------
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="brand-box">
        <div class="brand-icon">⌕</div>
        <div>
            <div class="brand-title">Research AI</div>
            <div class="brand-tagline">Autonomous multi-agent intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # New Research Button
    if st.button("＋ New Research", use_container_width=True, type="primary"):
        st.session_state.current_session_id = None
        st.rerun()

    st.divider()

    # Research History
    st.caption("RECENT RESEARCH")
    if st.session_state.sessions:
        for s in reversed(st.session_state.sessions):
            label = s.get("topic", "Research")
            if len(label) > 28:
                label = label[:28] + "…"
            
            is_active = (s.get("id") == st.session_state.current_session_id)
            btn_type = "secondary"
            if st.button(f"📄 {label}", key=f"hist_{s['id']}", use_container_width=True):
                st.session_state.current_session_id = s["id"]
                st.rerun()
    else:
        st.caption("Your research history will appear here.")

    st.divider()

    # Model & Parameter Settings
    with st.expander("⚙️ Settings", expanded=False):
        st.session_state.model = st.selectbox(
            "Gemini Model",
            options=["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"],
            index=0,
            help="gemini-3.1-flash-lite is recommended for free-tier quotas and fast tool calling."
        )

        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Lower values yield more focused, factual findings."
        )

    # API Connectors Status
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    with st.expander("🔌 Connection Status", expanded=False):
        if gemini_key:
            st.success("Google Gemini: Connected", icon="✅")
        else:
            st.error("Google Gemini: Missing API Key", icon="❌")

        if tavily_key:
            st.success("Tavily Search: Connected", icon="✅")
        else:
            st.error("Tavily Search: Missing API Key", icon="❌")


# --------------------------------------------------
# Get Active Session (if any)
# --------------------------------------------------
active_session = None
if st.session_state.current_session_id:
    for s in st.session_state.sessions:
        if s["id"] == st.session_state.current_session_id:
            active_session = s
            break


# --------------------------------------------------
# Welcome Screen (Empty State)
# --------------------------------------------------
if not active_session:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-symbol">✳</div>
        <div class="welcome-title">What would you like to research?</div>
        <div class="welcome-subtitle">
            Enter any topic or question. Autonomous AI agents will search the live web, scrape authoritative sources, synthesize a comprehensive report, and review it.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clean Quick Suggestions
    st.caption("💡 Quick suggestions:")
    col1, col2 = st.columns(2)
    suggestions = [
        "How is AI impacting the job market in 2026?",
        "What are the latest breakthroughs in solid-state batteries?",
        "Compare Python and Rust for AI systems engineering.",
        "Recent clinical trial breakthroughs with CRISPR in 2026.",
    ]

    for idx, prompt_text in enumerate(suggestions):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            if st.button(prompt_text, key=f"sug_btn_{idx}", use_container_width=True):
                st.session_state.pending_topic = prompt_text
                st.rerun()


# --------------------------------------------------
# Active Session View (Report & Critique)
# --------------------------------------------------
if active_session:
    topic_title = active_session.get("topic", "Research Report")
    report_content = active_session.get("report", "")
    feedback_content = active_session.get("feedback", "")
    score = active_session.get("score")
    sources = active_session.get("sources", [])

    # User Query Prompt
    with st.chat_message("user", avatar="🧑"):
        st.markdown(f"**{topic_title}**")

    # Assistant Response
    with st.chat_message("assistant", avatar="✳"):
        # Top Header Bar: Score & Model info
        col_m, col_sc = st.columns([3, 1])
        with col_m:
            st.caption(f"Model: `{active_session.get('model', 'gemini')}`")
        with col_sc:
            if score is not None:
                st.markdown(f"⭐ **Critic Score:** `{score}/10`")

        # The Research Report
        st.markdown(report_content)

        # Peer Review Card
        if feedback_content:
            st.markdown('<div class="critic-card">', unsafe_allow_html=True)
            st.markdown("**⚖️ Critic Review & Peer Assessment**")
            st.markdown(feedback_content)
            st.markdown('</div>', unsafe_allow_html=True)

        # Sources list
        if sources:
            st.markdown("**Sources & References**")
            for idx, url in enumerate(sources, 1):
                st.markdown(f"{idx}. [{url}]({url})")

        # Action Buttons
        st.divider()
        col_dl, col_copy, _ = st.columns([1, 1, 2])
        with col_dl:
            clean_filename = f"research_{topic_title[:20].replace(' ', '_')}.md"
            st.download_button(
                label="📥 Download (.md)",
                data=report_content,
                file_name=clean_filename,
                mime="text/markdown",
                use_container_width=True
            )
        with col_copy:
            if st.button("📋 Copy Report", use_container_width=True):
                st.code(report_content, language="markdown")
                st.toast("Report copied to code block above!", icon="📋")

        # Collapsible technical details
        with st.expander("🔍 View Raw Search Intel & Scraped Text"):
            st.markdown("**Search Results (Tavily):**")
            st.text(active_session.get("search_results", "None"))
            st.markdown("**Scraped Page Content:**")
            st.text(active_session.get("scraped_content", "None"))


# --------------------------------------------------
# Chat Input & Pipeline Execution
# --------------------------------------------------
user_query = st.chat_input("Ask anything you want to research...")

# Handle pending prompt from suggestion buttons
if "pending_topic" in st.session_state:
    user_query = st.session_state.pop("pending_topic")

if user_query and user_query.strip():
    query_text = user_query.strip()

    # Create placeholder container for live execution
    with st.chat_message("user", avatar="🧑"):
        st.markdown(f"**{query_text}**")

    with st.chat_message("assistant", avatar="✳"):
        with st.status("Deploying autonomous research agents...", expanded=True) as status:
            try:
                def on_pipeline_step(step_num, step_name, status_type, data):
                    if status_type == "running":
                        status.update(label=f"Step {step_num}/4: {step_name}...")
                    elif status_type == "done":
                        st.write(f"✓ **Step {step_num} Complete**: {step_name}")

                # Execute pipeline
                output = run_research_pipeline(
                    topic=query_text,
                    model_name=st.session_state.model,
                    temperature=st.session_state.temperature,
                    status_callback=on_pipeline_step
                )

                status.update(label="✨ Research & Peer Review Complete!", state="complete", expanded=False)

                # Extract report and sources
                report_str = output.get("report", "")
                feedback_str = output.get("feedback", "")
                score_num = extract_score(feedback_str)
                all_sources = extract_sources(report_str + "\n" + output.get("search_results", ""))

                # Build session payload
                new_session = {
                    "id": str(uuid.uuid4())[:8],
                    "topic": query_text,
                    "model": st.session_state.model,
                    "report": report_str,
                    "feedback": feedback_str,
                    "score": score_num,
                    "sources": all_sources,
                    "search_results": output.get("search_results", ""),
                    "scraped_content": output.get("scraped_content", "")
                }

                st.session_state.sessions.append(new_session)
                st.session_state.current_session_id = new_session["id"]
                st.rerun()

            except Exception as e:
                status.update(label="❌ Pipeline execution error", state="error", expanded=True)
                st.error(f"Error: {str(e)}")
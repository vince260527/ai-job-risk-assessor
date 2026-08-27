import os
import re

import streamlit as st

# On Streamlit Community Cloud, secrets live in st.secrets and are not
# guaranteed to be mirrored into the process environment. Bridge explicitly
# so the Anthropic SDK's default os.environ-based auth resolution works.
# Locally, st.secrets has no backing file and raises — analyzer.py's
# load_dotenv() already handles that case via .env.
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass

from analyzer import assess_role

st.set_page_config(page_title="AI Job Risk Assessor", page_icon="🧭")

_MARKDOWN_SPECIAL_CHARS = re.compile(r"([\\`*_{}\[\]()#+\-.!~$|])")


def esc(text: str) -> str:
    """Escape markdown-significant characters so free-form Claude output
    renders as plain text instead of being misinterpreted as formatting."""
    return _MARKDOWN_SPECIAL_CHARS.sub(r"\\\1", text)


RISK_LABELS = {
    "low": "🟢 Low",
    "moderate": "🟡 Moderate",
    "high": "🟠 High",
    "very_high": "🔴 Very high",
}

st.title("🧭 AI Job Risk Assessor")
st.write(
    "Describe your actual day-to-day tasks and get a task-by-task breakdown "
    "of AI-automation exposure, plus a concrete reskilling roadmap — not a "
    "generic \"will AI take my job\" score."
)

job_title = st.text_input("Job title", placeholder="e.g. Accounts Payable Clerk")
duties = st.text_area(
    "What do you actually do day-to-day?",
    placeholder=(
        "e.g. I process vendor invoices in QuickBooks, match them against "
        "purchase orders, enter data into our ERP system, follow up with "
        "vendors on discrepancies by email and phone, and prepare weekly "
        "payment batches for approval."
    ),
    height=150,
)

st.caption("Nothing you enter here is stored — this runs a single stateless request.")

if st.button("Assess my risk", type="primary"):
    if not job_title.strip() or not duties.strip():
        st.error("Please fill in both your job title and your actual duties.")
        st.stop()

    with st.spinner("Analyzing with Claude..."):
        try:
            result = assess_role(job_title, duties)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    st.header("Risk assessment")
    st.markdown(f"**Overall exposure: {RISK_LABELS.get(result.overall_risk, result.overall_risk)}**")
    st.write(esc(result.overall_summary))

    st.subheader("Task-by-task breakdown")
    for t in result.tasks:
        with st.container(border=True):
            st.markdown(f"**{esc(t.task)}** — {RISK_LABELS.get(t.exposure, t.exposure)}")
            st.write(esc(t.reasoning))

    st.subheader("Your reskilling roadmap")
    for i, item in enumerate(result.roadmap, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {esc(item.action)}**")
            st.write(esc(item.why))

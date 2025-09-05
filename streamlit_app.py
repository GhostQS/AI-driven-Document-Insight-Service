import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Abysalto Doc QA", layout="wide")
st.title("AI-driven Document Insight Service")

if "session_id" not in st.session_state:
    st.session_state.session_id = ""

with st.sidebar:
    st.header("Session")
    st.session_state.session_id = st.text_input("Session ID (optional)", value=st.session_state.session_id)
    use_rag = st.checkbox("Use RAG (if enabled)", value=True)

st.subheader("1) Upload documents")
files = st.file_uploader("PDF or image files", type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff"], accept_multiple_files=True)
if st.button("Upload") and files:
    data = {"session_id": st.session_state.session_id}
    files_data = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in files]
    resp = requests.post(f"{API_BASE}/upload", data=data, files=files_data, timeout=120)
    if resp.ok:
        out = resp.json()
        st.session_state.session_id = out.get("session_id", st.session_state.session_id)
        st.success(f"Uploaded to session {st.session_state.session_id}")
        st.json(out)
    else:
        st.error(resp.text)

st.subheader("2) Ask a question")
q = st.text_input("Question")
if st.button("Ask") and q:
    payload = {"session_id": st.session_state.session_id, "question": q, "use_rag": use_rag}
    resp = requests.post(f"{API_BASE}/ask", json=payload, timeout=120)
    if resp.ok:
        st.json(resp.json())
    else:
        st.error(resp.text)

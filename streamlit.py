# streamlit_app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Document Q&A", page_icon="📄")

st.title("📄 Document Question & Answer System")
st.markdown("Upload a document and ask questions **only about that document**")

# Sidebar for upload
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'docx', 'md', 'csv']
    )
    
    if uploaded_file:
        with st.spinner("Processing..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post(f"{API_URL}/upload", files=files)
            if response.status_code == 200:
                st.success("✅ Document ready!")
            else:
                st.error("❌ Upload failed")

# Main chat area
st.subheader("Ask Questions About Your Document")

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your document..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(
                f"{API_URL}/query",
                json={"query": prompt}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("in_scope"):
                    st.markdown(data["response"])
                else:
                    st.warning(data["response"])
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": data["response"]
                })
            else:
                st.error("Error: " + response.json().get("detail", "Unknown error"))
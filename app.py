import streamlit as st
import os
from Agents.agent1 import process_document_and_upload_to_s3
from Agents.agent2 import extract_intent_and_entities, format_response_from_data
from Agents.agent3 import extract_response
 
st.set_page_config(page_title="DociQ - Smart Graph Chatbot", layout="centered")
logo_url = "https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png"
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{logo_url}" width="300">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
    <h1 style='text-align: center; font-size: 60px; font-weight: bold; color: #16a085;'>📄 DociQ</h1>
    <p style='text-align: center; font-size: 18px;'>Upload a PDF to enrich knowledge. Ask questions anytime!</p>
    <hr style='border: 1px solid #ccc;'>
""", unsafe_allow_html=True)
 
# File upload
st.markdown("### 📂 Upload Knowledge Document")
uploaded_files = st.file_uploader("Choose a document to upload (pdf, jpg, jpeg, png, csv, excel, txt, json)", type=["pdf","jpg","jpeg","png","csv","excel","txt","json"],accept_multiple_files=True)#File Upload Logic
 
# If file is uploaded, process it and update Neo4j
data_uploaded = False
if uploaded_files:
    st.info(f"🗃️ {len(uploaded_files)} files selected")
    if st.button("🚀 Process All Files"):
        for uploaded_file in uploaded_files:
            try:
                filetype = uploaded_file.name.split(".")[-1].lower()
                st.subheader(f"📄 File: {uploaded_file.name} ({filetype})")
                with st.spinner("Extracting and analyzing..."):
                    extracted = process_document_and_upload_to_s3(uploaded_file, filetype)
                    st.success("✅ Successfully uploaded and processed!")
                    st.info(f"Status: {extracted}")
            except:
                st.error("❌ Could not extract content from this file.")

# question
st.markdown("### 💬 Ask a Question")
user_question = st.text_input("Enter your question")
 
if st.button("🔍 Get Answer"):
    if user_question:
        with st.spinner("🧠 Understanding your question..."):
            intent_entities = extract_intent_and_entities(user_question)
            cypher_query, results = extract_response(intent_entities,user_question)
            final_response = format_response_from_data(intent_entities, results)
            st.markdown("#### 🧾 Cypher Query Used:")
            st.code(cypher_query, language="cypher")
            st.markdown("#### 📊 Answer:")
            st.write(final_response)
            if not results:
                st.markdown("No Data Available related to query")

    else:
        st.warning("⚠️ Please type your question before clicking the button.")
 
st.markdown("---")
st.markdown("<p style='text-align:center;'>© 2025 DociQ | Built with using AWS Services: Amazon Bedrock & </p>", unsafe_allow_html=True)
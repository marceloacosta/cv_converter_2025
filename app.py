import streamlit as st

from config import OPENAI_API_KEY, MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES
from extraction import extract_text_from_file
from pdf_generator import markdown_to_pdf
from agents import run_cv_pipeline


def main():
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY is not set. Please set it in your environment or .env file.")
        return

    st.title("CV Format Standardizer")

    if "result" not in st.session_state:
        st.session_state["result"] = None
    if "current_markdown" not in st.session_state:
        st.session_state["current_markdown"] = None
    if "processed" not in st.session_state:
        st.session_state["processed"] = False
    if "last_file_name" not in st.session_state:
        st.session_state["last_file_name"] = None

    uploaded_file = st.file_uploader(
        "Choose a CV file (txt, pdf, or docx)", type=["txt", "pdf", "docx"]
    )

    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            st.error(f"File exceeds the {MAX_FILE_SIZE_MB} MB limit. Please upload a smaller file.")
            return

        if st.session_state["last_file_name"] != uploaded_file.name:
            st.session_state["result"] = None
            st.session_state["current_markdown"] = None
            st.session_state["processed"] = False
            st.session_state["last_file_name"] = uploaded_file.name

    if not st.session_state["processed"]:
        if st.button("Process", disabled=uploaded_file is None):
            with st.status("Processing CV...", expanded=True) as status:
                st.write("Extracting text from file...")
                cv_text = extract_text_from_file(uploaded_file)
                if not cv_text.strip():
                    st.error("Could not extract any text from the uploaded file.")
                    return

                st.write("Analyzing and formatting CV (this may take 1-2 minutes)...")
                try:
                    result = run_cv_pipeline(cv_text)
                except Exception as e:
                    st.error(f"Failed to process CV: {e}")
                    return

                st.session_state["result"] = result
                st.session_state["current_markdown"] = result
                st.session_state["processed"] = True
                status.update(label="Processing complete!", state="complete")
            st.rerun()

    if st.session_state["processed"] and st.session_state.get("current_markdown"):
        if st.button("Process New File"):
            st.session_state["processed"] = False
            st.session_state["result"] = None
            st.session_state["current_markdown"] = None
            st.session_state["last_file_name"] = None
            st.rerun()

        st.markdown(st.session_state["current_markdown"])

        edited_markdown = st.text_area(
            "Edit the markdown below:",
            value=st.session_state["current_markdown"],
            height=300,
            key="markdown_editor",
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Update Preview"):
                st.session_state["current_markdown"] = edited_markdown
                st.rerun()

        with col2:
            pdf_bytes = markdown_to_pdf(edited_markdown)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="cv_output.pdf",
                mime="application/pdf",
            )


if __name__ == "__main__":
    main()

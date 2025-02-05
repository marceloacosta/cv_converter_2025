import os
import io
from datetime import date
from dotenv import load_dotenv, find_dotenv

import streamlit as st
import markdown
from docx import Document
from PyPDF2 import PdfReader
from weasyprint import HTML, CSS

# Helper functions
def markdown_to_pdf(markdown_text: str) -> bytes:
    """Convert markdown text to PDF bytes in memory."""
    html_content = markdown.markdown(markdown_text)
    LOGO_URL = os.environ.get("LOGO_URL", "")
    if LOGO_URL:
        html_content = (
            f'<div style="text-align: right;">'
            f'<img src="{LOGO_URL}" alt="Logo" width="50px" style="width: 30%;">'
            f'</div>\n' + html_content
        )
    current_date = date.today().strftime('%B %d, %Y')
    css = CSS(string=f"""
        body {{
            font-family: Arial, sans-serif;
        }}
        @page {{
            @bottom-right {{
                content: "Date: {current_date}";
            }}
        }}
    """)
    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(target=pdf_buffer, stylesheets=[css])
    pdf_buffer.seek(0)
    return pdf_buffer.read()

def extract_text_from_file(uploaded_file) -> str:
    """Extract text from a .txt, .docx, or .pdf file."""
    file_name = uploaded_file.name
    ext = os.path.splitext(file_name)[1].lower()
    cv_text = ""
    if ext == ".txt":
        cv_text = uploaded_file.read().decode("utf-8")
    elif ext == ".docx":
        doc = Document(uploaded_file)
        cv_text = "\n".join(para.text for para in doc.paragraphs)
    elif ext == ".pdf":
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                cv_text += text + "\n"
    else:
        cv_text = "Unsupported file type."
    return cv_text

def main():
    # Ensure environment variables are loaded
    load_dotenv(find_dotenv())
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY is not set. Please set it in your secrets.")
        return

    st.title("CV Format Standardizer V3")

    # Initialize session state for the uploaded file and result.
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = None
    if "result" not in st.session_state:
        st.session_state["result"] = None

    # --- File Uploader ---
    uploaded_file = st.file_uploader("Choose a CV file (txt, pdf, or docx)", type=['txt', 'pdf', 'docx'])
    if uploaded_file is not None:
        # If a new file is uploaded, clear the previous result.
        if (st.session_state["uploaded_file"] is None or 
            st.session_state["uploaded_file"].name != uploaded_file.name):
            st.session_state["result"] = None
        st.session_state["uploaded_file"] = uploaded_file

    # Debug output: display current file name.
    if st.session_state["uploaded_file"]:
        st.write("Current uploaded file:", st.session_state["uploaded_file"].name)
    else:
        st.write("No file currently uploaded.")

    # --- Re-instantiate Agents, Tasks, and Crew ---
    # Import necessary classes from LangChain and CrewAI here so they're created fresh.
    from langchain_openai import ChatOpenAI
    from crewai import Agent, Task, Process, Crew
    from langchain.tools import Tool

    # Define a tool that extracts text from the uploaded file.
    def extract_text_from_file_tool(file_path: str) -> str:
        uploaded = st.session_state.get("uploaded_file")
        if not uploaded:
            return "No file uploaded."
        return extract_text_from_file(uploaded)

    extract_text_tool = Tool(
        name="extract_text_from_file",
        description="Extracts text from an uploaded file (.txt, .docx, or .pdf).",
        func=extract_text_from_file_tool,
    )

    # Create the transcriber and editor agents.
    cv_transcriber = Agent(
        role="Senior Researcher",
        goal="Extract all the relevant sections and details from the CV text.",
        backstory="You are an expert recruiter who identifies and extracts the most pertinent information from a CV.",
        verbose=True,
        allow_delegation=False,
        tools=[extract_text_tool],
        llm=ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY),
    )

    cv_editor = Agent(
        role="Senior Editor",
        goal="Review the CV markdown and remove redundancies or empty sections.",
        backstory="You are an expert editor who refines CVs to be concise and only include specified details.",
        verbose=True,
        allow_delegation=False,
        tools=[],  # No tools needed here.
        llm=ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY),
    )

    # Define the tasks.
    task_write_cv = Task(
        description="""Use the extracted CV text and generate comprehensive sections for personal information, job experience, education, etc. Follow this markdown format precisely. If any information is missing or not specified, do not include that subsection.

# [Name]
- **Email:** [Email]
- **Phone:** [Phone number]
- **Address:** [Address]
- **Linkedin:** [LinkedIn profile]
- **Github:** [Github profile]
- **Personal website:** [Personal website]

# About me
<div style="text-align: justify">
- [Description of yourself]
</div>

# Job experience
## [Company name]
### [Position]
- Duration
- Location

## Responsibilities
<div style="text-align: justify">
- Description of responsibilities
- Description of achievements in that position
- Description of technologies, stack or skills used
</div>

# Education
## [Institution name]
### [Degree]
- Duration
- Location

## Description
- Description of the degree

# Additional information
## Languages
- [Languages] [Skill level]

## Skills
- [Programming languages] [Skill level]
- [Technologies]
- [Other skills]
""",
        agent=cv_transcriber,
    )

    task_edit_cv = Task(
        description="""Review the generated CV markdown and remove any redundant or empty sections. Output the final CV markdown without any additional commentary. Use the same format as above.

# [Name]
- **Email:** [Email]
- **Phone:** [Phone number]
- **Address:** [Address]
- **Linkedin:** [LinkedIn profile]
- **Github:** [Github profile]
- **Personal website:** [Personal website]

# About me
<div style="text-align: justify">
- [Description of yourself]
</div>

# Job experience
## [Company name]
### [Position]
- Duration
- Location

## Responsibilities
<div style="text-align: justify">
- Description of responsibilities
- Description of achievements in that position
- Description of technologies, stack or skills used
</div>

# Education
## [Institution name]
### [Degree]
- Duration
- Location

## Description
- Description of the degree

# Additional information
## Languages
- [Languages] [Skill level]

## Skills
- [Programming languages] [Skill level]
- [Technologies]
- [Other skills]
""",
        agent=cv_editor,
    )

    crew = Crew(
        agents=[cv_transcriber, cv_editor],
        tasks=[task_write_cv, task_edit_cv],
        verbose=2,
        process=Process.sequential,
    )

    # --- Process the File ---
    if st.button("Process") and st.session_state["uploaded_file"] is not None:
        # Clear all cached data and resources to force a re-run.
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Explicitly clear any previous result.
        st.session_state["result"] = None

        # (Optional debug) Show file details.
        file_bytes = st.session_state["uploaded_file"].getvalue()
        st.write("Processing file of size:", len(file_bytes), "bytes")

        # Process the current file with the Crew tasks.
        result = crew.kickoff()
        st.session_state["result"] = result

        # Display the result.
        st.markdown(result)
        if result:
            pdf_bytes = markdown_to_pdf(result)
            st.download_button(
                label="Download PDF", 
                data=pdf_bytes, 
                file_name="output.pdf", 
                mime="application/pdf"
            )

    # --- Allow Editing and Downloading ---
    if st.session_state["result"]:
        edited_markdown = st.text_area("Edit the markdown below:", value=st.session_state["result"], height=300)
        if st.button("Save Edited"):
            pdf_bytes = markdown_to_pdf(edited_markdown)
            st.download_button(label="Download Edited PDF", data=pdf_bytes, file_name="edited_output.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()

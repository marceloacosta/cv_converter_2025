import os
import io
from datetime import date
from dotenv import load_dotenv, find_dotenv

import streamlit as st
import markdown
from docx import Document
from PyPDF2 import PdfReader
from weasyprint import HTML, CSS

# -----------------------------
# Helper Functions
# -----------------------------

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

# -----------------------------
# Custom Tool Definition with Caching Disabled
# -----------------------------
from langchain.tools import Tool

class NoCacheTool(Tool):
    def cache_function(self, *args, **kwargs):
        # Disable caching by always returning False
        return False

class ExtractTextTool(NoCacheTool):
    def __init__(self):
        super().__init__(
            name="extract_text_from_file",
            func=self._run,
            description=(
                "Extracts text from an uploaded file (.txt, .docx, or .pdf). "
                "Caching is disabled for fresh extraction each time."
            )
        )

    def _run(self, file_path: str) -> str:
        uploaded = st.session_state.get("uploaded_file")
        if not uploaded:
            return "No file uploaded."
        return extract_text_from_file(uploaded)

# -----------------------------
# Main Application
# -----------------------------

def main():
    # Load environment variables
    load_dotenv(find_dotenv())
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY is not set. Please set it in your secrets.")
        return

    st.title("CV Format Standardizer V5")

    # Initialize session state variables
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = None
    if "result" not in st.session_state:
        st.session_state["result"] = None

    # File Uploader
    uploaded_file = st.file_uploader(
        "Choose a CV file (txt, pdf, or docx)", type=['txt', 'pdf', 'docx']
    )
    if uploaded_file is not None:
        # Always update the file and clear the result when a new file is uploaded
        st.session_state["uploaded_file"] = uploaded_file
        st.session_state["result"] = None

    # Debug output
    if st.session_state["uploaded_file"]:
        st.write("Current uploaded file:", st.session_state["uploaded_file"].name)
    else:
        st.write("No file currently uploaded.")

    # -----------------------------
    # Initialize Agents and Tasks
    # -----------------------------
    from langchain_openai import ChatOpenAI
    from crewai import Agent, Task, Process, Crew

    # Create text extraction tool with caching disabled
    extract_text_tool = ExtractTextTool()

    # Create agents with no caching
    cv_transcriber = Agent(
        role="Senior CV Analyst",
        goal="Extract and format all CV information accurately",
        backstory="Expert at analyzing CVs and extracting relevant information while maintaining all original content",
        verbose=True,
        allow_delegation=False,
        tools=[extract_text_tool],
        llm=ChatOpenAI(
            model="gpt-4", 
            temperature=0, 
            openai_api_key=OPENAI_API_KEY,
            cache=False  # Disable LLM response caching
        ),
    )

    cv_editor = Agent(
        role="Senior CV Editor",
        goal="Review and refine CV formatting while preserving all information",
        backstory="Expert editor specializing in CV optimization and formatting",
        verbose=True,
        allow_delegation=False,
        tools=[],
        llm=ChatOpenAI(
            model="gpt-4", 
            temperature=0, 
            openai_api_key=OPENAI_API_KEY,
            cache=False  # Disable LLM response caching
        ),
    )

    # Define tasks (keeping the same task descriptions)
    task_write_cv = Task(
        description="""Use the text extracted from the CV text and write comprehensive personal information, job experience and education sections. Make sure you include all job experiences and education details.
        For your Outputs use the following markdown format (If any of the requested information can not be found or it is Not Specified don't include that subsection. Do not invent, guess or assume any information.):
        If Skill level is not specified, leave it empty. If any of the requested information can not be found or it is Not Specified don't include that subsection. Do not invent, guess or assume any information.

        # [Name]
        - **Email:** [Email]
        - **Phone:** [Phone number]
        - **Address:** [Address]
        - **Linkedin:** [LinkedIn profile]
        - **Github:** [Github profile]
        - **Personal website:**[Personal website]
        # About me
        <div style="text-align: justify"> 
        - [Description of yourself]
        </div>
        # Job experience
        ## [Company name]
        ### [Position] 
        - Duration
        - Location
        ##[Responsibilities]
        <div style="text-align: justify"> 
        - Description of responsibilities
        - Description of achievements in that position
        - Description of technologies, stack or skills used in that position
        </div>

        # Education
        ## [Institution name]
        ### [Degree] 
        - Duration
        - Location
        ##[Description]
        - Description of degree
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
        description="""Use the resulting CV markdown text and Find and explore the resulting CV. Carefully review each section and subsection and eliminate all redundancies and sections or subsections where information is empty or not specified.
        For your Outputs use the following markdown format below (include sections only whenever applicable):
        Do not include in your output any commentary or notes. Only include the CV text in markdown format.
        If Skill level is not specified, leave it empty. If any of the requested information can not be found or it is Not Specified don't include that subsection. Do not invent, guess or assume any information.
        # [Name]
        - **Email:** [Email]
        - **Phone:** [Phone number]
        - **Address:** [Address]
        - **Linkedin:** [LinkedIn profile]
        - **Github:** [Github profile]
        - **Personal website:**[Personal website]
        # About me
        <div style="text-align: justify"> 
        - [Description of yourself]
        </div>
        # Job experience
        ## [Company name]
        ### [Position] 
        - Duration
        - Location
        ##[Responsibilities]
        <div style="text-align: justify"> 
        - Description of responsibilities
        - Description of achievements in that position
        - Description of technologies, stack or skills used in that position
        </div>

        # Education
        ## [Institution name]
        ### [Degree] 
        - Duration
        - Location
        ##[Description]
        - Description of degree
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

    # Create and configure the crew with caching disabled
    crew = Crew(
        agents=[cv_transcriber, cv_editor],
        tasks=[task_write_cv, task_edit_cv],
        verbose=2,
        process=Process.sequential,
    )

    # Process the File
    if st.button("Process") and st.session_state["uploaded_file"] is not None:
        st.session_state["result"] = None  # Clear any previous results
        file_bytes = st.session_state["uploaded_file"].getvalue()
        st.write("Processing file of size:", len(file_bytes), "bytes")
        
        # Run the crew with fresh processing
        result = crew.kickoff()
        st.session_state["result"] = result
        st.markdown(result)
        
        if result:
            pdf_bytes = markdown_to_pdf(result)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="output.pdf",
                mime="application/pdf"
            )

    # Allow Editing and Downloading
    if st.session_state["result"]:
        edited_markdown = st.text_area(
            "Edit the markdown below:",
            value=st.session_state["result"],
            height=300
        )
        if st.button("Save Edited"):
            pdf_bytes = markdown_to_pdf(edited_markdown)
            st.download_button(
                label="Download Edited PDF",
                data=pdf_bytes,
                file_name="edited_output.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
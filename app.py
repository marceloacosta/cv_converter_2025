import os
import io
from datetime import date
from dotenv import load_dotenv, find_dotenv

import streamlit as st
import markdown
from docx import Document
from PyPDF2 import PdfReader
from weasyprint import HTML, CSS

# LLM and agent dependencies
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Process, Crew
from langchain.tools import Tool  # Import the Tool class

# Load environment variables
load_dotenv(find_dotenv())
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LOGO_URL = os.environ.get("LOGO_URL", "")

#############################
# Helper Functions
#############################

def markdown_to_pdf(markdown_text: str) -> bytes:
    """Convert markdown text to PDF bytes in memory."""
    html_content = markdown.markdown(markdown_text)
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


#############################
# Tool Definition
#############################

# Instead of just a plain function, wrap your extraction logic in a Tool.
def extract_text_from_file_tool(file_path: str) -> str:
    """
    This tool ignores the file_path parameter (it is provided for compatibility)
    and extracts text from the uploaded file stored in Streamlit's session_state.
    """
    uploaded_file = st.session_state.get("uploaded_file")
    if not uploaded_file:
        return "No file uploaded."
    return extract_text_from_file(uploaded_file)

# Create a Tool instance (with the proper metadata) to pass to the Agent.
extract_text_tool = Tool(
    name="extract_text_from_file",
    description="Extracts text from an uploaded file (.txt, .docx, or .pdf).",
    func=extract_text_from_file_tool,
)


#############################
# Agent & Task Definitions
#############################

# Create the transcriber agent with the tool.
cv_transcriber = Agent(
    role="Senior Researcher",
    goal="Extract all the relevant sections and details from the CV text.",
    backstory="You are an expert recruiter who identifies and extracts the most pertinent information from a CV.",
    verbose=True,
    allow_delegation=False,
    tools=[extract_text_tool],  # Use the Tool instance here!
    llm=ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY),
)

# For the editor agent, if you don't need any tool, you can pass an empty list.
cv_editor = Agent(
    role="Senior Editor",
    goal="Review the CV markdown and remove redundancies or empty sections.",
    backstory="You are an expert editor who refines CVs to be concise and only include specified details.",
    verbose=True,
    allow_delegation=False,
    tools=[],  # No tools needed here, so an empty list
    llm=ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY),
)

# (Your Task definitions remain unchanged)
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

# Instantiate the crew of agents and tasks.
crew = Crew(
    agents=[cv_transcriber, cv_editor],
    tasks=[task_write_cv, task_edit_cv],
    verbose=2,
    process=Process.sequential,
)

#############################
# Streamlit UI
#############################

def main():
    st.title("CV Format Standardizer 2025")

    # Initialize session state variables if not already set.
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = None
    if "result" not in st.session_state:
        st.session_state["result"] = None

    # --- File Uploader ---
    # When a new file is uploaded, automatically clear the previous result.
    uploaded_file = st.file_uploader("Choose a CV file (txt, pdf, or docx)", type=['txt', 'pdf', 'docx'])
    if uploaded_file is not None:
        # If there's no stored file or if the file name is different, clear the result.
        if (st.session_state["uploaded_file"] is None or 
            st.session_state["uploaded_file"].name != uploaded_file.name):
            st.session_state["result"] = None
        st.session_state["uploaded_file"] = uploaded_file

    # Debug output: show which file is currently stored.
    if st.session_state["uploaded_file"]:
        st.write("Current uploaded file:", st.session_state["uploaded_file"].name)
    else:
        st.write("No file currently uploaded.")

    # --- Process the File ---
    # When the "Process" button is clicked, automatically clear any previous result before processing.
    if st.button("Process") and st.session_state["uploaded_file"] is not None:
        # Clear previous result before processing.
        st.session_state["result"] = None
        result = crew.kickoff()  # Process the current file
        st.session_state["result"] = result
        st.markdown(result)
        if result:
            pdf_bytes = markdown_to_pdf(result)
            st.download_button(label="Download PDF", data=pdf_bytes, file_name="output.pdf", mime="application/pdf")

    # --- Allow Editing of the Markdown and Downloading a New PDF ---
    if st.session_state["result"]:
        edited_markdown = st.text_area("Edit the markdown below:", value=st.session_state["result"], height=300)
        if st.button("Save Edited"):
            pdf_bytes = markdown_to_pdf(edited_markdown)
            st.download_button(label="Download Edited PDF", data=pdf_bytes, file_name="edited_output.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()

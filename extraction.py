import os

from docx import Document
from PyPDF2 import PdfReader


def extract_text_from_file(uploaded_file) -> str:
    """Extract text from a .txt, .docx, or .pdf file."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()

    if ext == ".txt":
        return uploaded_file.read().decode("utf-8")

    if ext == ".docx":
        doc = Document(uploaded_file)
        return "\n".join(para.text for para in doc.paragraphs)

    if ext == ".pdf":
        reader = PdfReader(uploaded_file)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)

    return ""

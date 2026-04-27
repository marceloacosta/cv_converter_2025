import io
import re
from datetime import date

import markdown as md
from weasyprint import HTML, CSS

from config import LOGO_URL


def _sanitize_url(url: str) -> str:
    """Only allow http/https URLs to prevent injection."""
    url = url.strip()
    if re.match(r"^https?://[^\s\"'<>]+$", url):
        return url
    return ""


def markdown_to_pdf(markdown_text: str) -> bytes:
    """Convert markdown text to styled PDF bytes."""
    html_content = md.markdown(markdown_text)

    safe_logo = _sanitize_url(LOGO_URL)
    if safe_logo:
        html_content = (
            f'<div style="text-align: right;">'
            f'<img src="{safe_logo}" alt="Logo" style="max-width: 120px;">'
            f'</div>\n' + html_content
        )

    current_date = date.today().strftime("%B %d, %Y")
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

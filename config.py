import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LOGO_URL = os.environ.get("LOGO_URL", "")

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ANALYST_MODEL = "gpt-4o"
EDITOR_MODEL = "gpt-4o-mini"

CV_TEMPLATE = """\
# Name of the person

- **Email:** actual email
- **Phone:** actual phone number
- **Address:** actual address
- **Linkedin:** actual LinkedIn URL
- **Github:** actual Github URL
- **Personal website:** actual URL

# About me

Brief professional summary paragraph.

# Job experience

## Company name
### Position title
- Start year - End year
- Location

**Responsibilities:**
- Each responsibility as a separate bullet point
- Each achievement as a separate bullet point
- Each technology or skill used as a separate bullet point

(Repeat the above block for each job)

# Education

## Institution name
### Degree title
- Start year - End year
- Location
- Brief description of degree (if available)

# Additional information

## Certifications
- Certification name - Institution - Year

## Languages
- Language — Skill level

## Skills
- Programming languages — Skill level
- Technologies
- Other skills
"""

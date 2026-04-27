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
## [Responsibilities]
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
## [Description]
- Description of degree
# Additional information
## Languages
- [Languages] [Skill level]
## Skills
- [Programming languages] [Skill level]
- [Technologies]
- [Other skills]
"""

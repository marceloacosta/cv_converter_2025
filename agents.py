from openai import OpenAI

from config import OPENAI_API_KEY, ANALYST_MODEL, EDITOR_MODEL, CV_TEMPLATE


def _build_prompt(preamble: str) -> str:
    return f"""{preamble}
If any of the requested information cannot be found or is Not Specified,
don't include that subsection. Do not invent, guess, or assume any information.
If Skill level is not specified, leave it empty.

For your output use the following markdown format (include sections only when applicable).
Do not include in your output any commentary or notes. Only include the CV text in markdown format.

{CV_TEMPLATE}"""


def run_cv_pipeline(cv_text: str) -> str:
    """Run two-step CV analysis and editing using the OpenAI API."""
    client = OpenAI(api_key=OPENAI_API_KEY)

    analyst_response = client.chat.completions.create(
        model=ANALYST_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a Senior CV Analyst. You extract and format all CV information accurately, maintaining all original content.",
            },
            {
                "role": "user",
                "content": _build_prompt(
                    f"Using the following CV text, write comprehensive personal information, "
                    f"job experience, and education sections. Make sure you include all job "
                    f"experiences and education details.\n\nCV TEXT:\n{cv_text}"
                ),
            },
        ],
    )
    draft_markdown = analyst_response.choices[0].message.content

    editor_response = client.chat.completions.create(
        model=EDITOR_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a Senior CV Editor specializing in CV optimization and formatting. Output only clean markdown, no commentary.",
            },
            {
                "role": "user",
                "content": _build_prompt(
                    f"Review the following CV markdown. Carefully check each section and "
                    f"eliminate all redundancies and sections where information is empty "
                    f"or not specified.\n\nCV MARKDOWN:\n{draft_markdown}"
                ),
            },
        ],
    )
    return editor_response.choices[0].message.content

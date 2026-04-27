from openai import OpenAI

from config import OPENAI_API_KEY, ANALYST_MODEL, EDITOR_MODEL, CV_TEMPLATE

FORMATTING_RULES = """
CRITICAL FORMATTING RULES:
- Do NOT use square brackets [] in the output. Replace all placeholders with actual data from the CV.
- If information is not available, omit that line or section entirely. Never write "[Not specified]" or similar.
- Each responsibility, achievement, or skill must be its own bullet point (separate line starting with "- ").
- Do NOT concatenate multiple items on a single line separated by " - ".
- Output ONLY clean markdown. No commentary, notes, or explanations.
"""


def run_cv_pipeline(cv_text: str) -> str:
    """Run two-step CV analysis and editing using the OpenAI API."""
    client = OpenAI(api_key=OPENAI_API_KEY)

    analyst_response = client.chat.completions.create(
        model=ANALYST_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Senior CV Analyst. You extract and format all CV "
                    "information accurately into clean markdown, maintaining all "
                    "original content. You never invent or guess information."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Extract all information from the following CV and format it "
                    f"as clean markdown. Include all job experiences and education details.\n\n"
                    f"{FORMATTING_RULES}\n\n"
                    f"Use this structure as a guide (replace placeholders with real data, "
                    f"omit any section where data is not available):\n\n"
                    f"{CV_TEMPLATE}\n\n"
                    f"CV TEXT:\n{cv_text}"
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
                "content": (
                    "You are a Senior CV Editor. You clean up CV markdown formatting. "
                    "Output only the final markdown, no commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Review and clean up the following CV markdown:\n\n"
                    f"1. Remove any remaining square brackets [] or placeholder text.\n"
                    f"2. Remove sections that are empty or have no real data.\n"
                    f"3. Eliminate redundancies.\n"
                    f"4. Ensure each responsibility/achievement is a separate bullet point.\n"
                    f"5. Keep all real information intact.\n\n"
                    f"{FORMATTING_RULES}\n\n"
                    f"CV MARKDOWN:\n{draft_markdown}"
                ),
            },
        ],
    )
    return editor_response.choices[0].message.content

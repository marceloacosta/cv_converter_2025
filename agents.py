from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Process, Crew

from config import OPENAI_API_KEY, ANALYST_MODEL, EDITOR_MODEL, CV_TEMPLATE


def _build_task_description(preamble: str) -> str:
    return f"""{preamble}
If any of the requested information cannot be found or is Not Specified,
don't include that subsection. Do not invent, guess, or assume any information.
If Skill level is not specified, leave it empty.

For your output use the following markdown format (include sections only when applicable):
Do not include in your output any commentary or notes. Only include the CV text in markdown format.

{CV_TEMPLATE}"""


def run_cv_pipeline(cv_text: str) -> str:
    """Run the two-agent CV pipeline and return the final markdown."""
    analyst_llm = ChatOpenAI(
        model=ANALYST_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        cache=False,
    )
    editor_llm = ChatOpenAI(
        model=EDITOR_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        cache=False,
    )

    cv_transcriber = Agent(
        role="Senior CV Analyst",
        goal="Extract and format all CV information accurately",
        backstory="Expert at analyzing CVs and extracting relevant information while maintaining all original content",
        verbose=True,
        allow_delegation=False,
        tools=[],
        llm=analyst_llm,
    )

    cv_editor = Agent(
        role="Senior CV Editor",
        goal="Review and refine CV formatting while preserving all information",
        backstory="Expert editor specializing in CV optimization and formatting",
        verbose=True,
        allow_delegation=False,
        tools=[],
        llm=editor_llm,
    )

    task_write = Task(
        description=_build_task_description(
            f"Using the following CV text, write comprehensive personal information, "
            f"job experience, and education sections. Make sure you include all job "
            f"experiences and education details.\n\nCV TEXT:\n{cv_text}"
        ),
        agent=cv_transcriber,
        expected_output="A complete CV in markdown format following the provided template",
    )

    task_edit = Task(
        description=_build_task_description(
            "Review the CV markdown from the previous task. Carefully check each "
            "section and eliminate all redundancies and sections where information "
            "is empty or not specified."
        ),
        agent=cv_editor,
        expected_output="A clean, refined CV in markdown format with no redundancies",
    )

    crew = Crew(
        agents=[cv_transcriber, cv_editor],
        tasks=[task_write, task_edit],
        verbose=True,
        process=Process.sequential,
    )

    result = crew.kickoff()
    if hasattr(result, "raw"):
        return result.raw
    return str(result)

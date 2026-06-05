"""
Failure diagnosis tool for analyzing errors and suggesting solutions.
"""

from langchain_core.tools import tool
from core.helper.llm_util import init_llm


FAILURE_DIAGNOSIS_PROMPT = """
You are an expert DevOps engineer.

Failure Details:
----------------
{failure_msg}

Results by searching in internet:
----------------
{search_res}

Please locate the root cause and provide a solution strategy. Your response should:
1. Identify the likely cause of the error and suggest a solution
2. Output results in one line, don't exceed 100 words

Only include helpful technical information. Do not ask for user confirmation.
"""


class SearchUtil:
    """Simple search utility for failure diagnosis."""

    def run(self, query: str) -> str:
        """
        Perform a search for the given query.

        Args:
            query: The search query string

        Returns:
            str: Search results or placeholder message
        """
        return "Search utility not configured. Please check internet for solutions."


def init_search_util() -> SearchUtil:
    """
    Initialize and return a search utility instance.

    Returns:
        SearchUtil: A search utility instance
    """
    return SearchUtil()


@tool("failure_diagnosis_tool")
def failure_diagnosis_tool(failure_msg: str) -> str:
    """
    Identify the failure reason and suggest a solution.

    Args:
        failure_msg: Details about current failure
    """
    search_tool = init_search_util()
    search_res = search_tool.run(failure_msg)

    prompt = FAILURE_DIAGNOSIS_PROMPT.format(
        failure_msg=failure_msg,
        search_res=search_res
    )

    try:
        llm = init_llm()
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Failed to diagnose error: {str(e)}"

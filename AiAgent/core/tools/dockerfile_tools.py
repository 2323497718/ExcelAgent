"""
Docker file generation tool using LLM.
"""

import os
from langchain_core.tools import tool
from core.helper.llm_util import init_llm
from core.tools.file_tools import read_file, write_file


DOCKERFILE_GENERATE_PROMPT = """
generate a complete and functional Dockerfile for a project based on the following requirements.

Note the content:
- Only use the simplest method mentioned in requirements to run app
- Only use the image required in requirements

requirements:
{requirement}

Output ONLY the Dockerfile content, no explanation or extra text.
"""


@tool("dockerfile_generate_tool")
def dockerfile_generate_tool(readme_path: str, project_path: str, save_path: str) -> str:
    """
    Generate contents of a DockerFile based on README.md, and save the DockerFile in a specific path.

    Args:
        readme_path: Path of README.md containing project requirements
        project_path: Path of the project where the Dockerfile works
        save_path: Path where the generated Dockerfile will be saved
    """
    requirement = read_file(readme_path)
    if requirement.startswith(f"{readme_path} doesn't exist"):
        return requirement

    prompt = DOCKERFILE_GENERATE_PROMPT.format(requirement=requirement)

    try:
        llm = init_llm()
        response = llm.invoke(prompt)
        dockerfile_text = response.content.strip().replace("```dockerfile", "").replace("```", "")

        result = write_file(dockerfile_text, save_path)
        diagnosis_sentence = "\n\n[Dockerfile generated successfully]"
        return result + diagnosis_sentence
    except Exception as e:
        return f"Failed to generate Dockerfile: {str(e)}"

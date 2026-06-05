"""
Container execution tool for running commands inside running Docker containers.
"""

import docker
from docker.errors import NotFound
from langchain_core.tools import tool


@tool("container_exec_cmd_tool")
def container_exec_cmd_tool(container_name: str, command: str) -> str:
    """
    Execute a shell command inside an already running Docker container.

    Args:
        container_name: The name of the container
        command: The shell command to execute
    """
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)

        exit_code, output = container.exec_run(
            cmd=command,
            stdout=True,
            stderr=True,
            demux=False,
            tty=False
        )

        output_text = output.decode(errors="ignore")
        diagnosis_sentence = "\n\n[Command executed]"
        return f"Exit code: {exit_code}\n\n Output:\n{output_text}" + diagnosis_sentence

    except NotFound:
        diagnosis_sentence = "\n\n[Container not found]"
        return f"Container '{container_name}' not found." + diagnosis_sentence
    except Exception as e:
        diagnosis_sentence = "\n\n[Execution failed]"
        return f"Failed to execute command: {str(e)}" + diagnosis_sentence

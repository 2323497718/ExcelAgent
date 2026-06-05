"""
File operation tools for the DevOps agent.
"""

import os
from pathlib import Path
from langchain_core.tools import tool


def read_file(file_path: str) -> str:
    """
    Read contents from a file.

    Args:
        file_path: Path to the file to read

    Returns:
        str: File contents or error message
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"{file_path} doesn't exist"
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"


def write_file(content: str, file_path: str) -> str:
    """
    Write content to a file.

    Args:
        content: Content to write
        file_path: Path to the file

    Returns:
        str: Success or error message
    """
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote content to {file_path}"
    except Exception as e:
        return f"Failed to write to file {file_path}: {str(e)}"


@tool("file_read_tool")
def file_read_tool(file_path: str) -> str:
    """
    Read contents of a file.

    Args:
        file_path: The path of this file
    """
    return read_file(file_path)


@tool("file_write_tool")
def file_write_tool(content: str, file_path: str) -> str:
    """
    Write content into a file at the specified path.

    Args:
        content: The content to write into the file.
        file_path: The full path of the file to be written.
    """
    return write_file(content, file_path)

"""
Docker tools for building images, running containers, and executing commands.
"""

import os
import subprocess
from langchain_core.tools import tool


def remove_image(image_tag: str) -> None:
    """
    Remove a Docker image if it exists.

    Args:
        image_tag: The tag of the image to remove
    """
    try:
        subprocess.run(
            ["docker", "rmi", "-f", image_tag],
            capture_output=True,
            text=True
        )
    except Exception:
        pass


@tool("image_build_tool")
def image_build_tool(docker_file_path: str, image_tag: str) -> str:
    """
    Build a Docker image from a specific Dockerfile.

    Args:
        docker_file_path: Path to the Dockerfile (relative to build context)
        image_tag: Tag name for the resulting image
    """
    original_dir = os.getcwd()
    docker_dir = os.path.dirname(docker_file_path)
    dockerfile_name = os.path.basename(docker_file_path)

    if not docker_dir:
        docker_dir = "."

    os.chdir(docker_dir)

    cmd = [
        "docker", "build",
        "-t", image_tag,
        "-f", dockerfile_name,
        "."
    ]

    full_log = []
    try:
        remove_image(image_tag)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for line in proc.stdout:
            full_log.append(line)

        proc.stdout.close()
        proc.wait()

    except Exception as e:
        full_log.append(f"Exception occurred: {str(e)}")
    finally:
        os.chdir(original_dir)

    diagnosis_sentence = "\n\n[Image build completed]"
    return "".join(full_log) + diagnosis_sentence


@tool("container_run_tool")
def container_run_tool(
        image_tag: str,
        container_name: str,
        internal_port: int = 9528,
        expose_port: int = 8080
) -> str:
    """
    Start and run a Docker container from a specified image.

    Args:
        image_tag: The tag of the image to run the container from
        container_name: The name to assign to the new container
        internal_port: Port used inside the container (default: 9528)
        expose_port: The host port to map to the container's internal port (default: 8080)
    """
    cmd = [
        "docker", "run", "-d", "--name", container_name,
        "-p", f"{expose_port}:{internal_port}",
        image_tag
    ]

    full_log = []
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for line in proc.stdout:
            full_log.append(line)

        proc.stdout.close()
        proc.wait()

    except Exception as e:
        full_log.append(f"Unexpected error during container run: {str(e)}\n")

    diagnosis_sentence = "\n\n[Container started]"
    return "".join(full_log) + diagnosis_sentence

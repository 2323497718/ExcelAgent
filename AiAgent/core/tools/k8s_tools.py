"""
Kubernetes cluster tools for logs and resource queries.
"""

import os
import subprocess
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from langchain_core.tools import tool


def run_kubectl(args: List[str], namespace: Optional[str] = None) -> str:
    """
    Run kubectl command and return output.

    Args:
        args: kubectl arguments (e.g., ['get', 'pods'])
        namespace: Optional namespace (ignored if args already contains --all-namespaces)

    Returns:
        str: Command output or error
    """
    cmd = ["kubectl"]
    if namespace and "--all-namespaces" not in args:
        cmd.extend(["-n", namespace])
    cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: kubectl command timed out"
    except FileNotFoundError:
        return "Error: kubectl not found. Please ensure kubectl is installed and in PATH."
    except Exception as e:
        return f"Error running kubectl: {str(e)}"


def parse_pod_list(output: str) -> List[Dict[str, str]]:
    """Parse kubectl get pods output into structured data."""
    lines = output.strip().split("\n")
    if len(lines) < 2:
        return []

    pods = []
    headers = lines[0].split()
    data_lines = lines[1:]

    for line in data_lines:
        parts = line.split()
        if len(parts) >= 4:
            name = parts[0]
            ready = parts[1]
            status = parts[2]
            restarts = parts[3]
            age = parts[4] if len(parts) > 4 else "unknown"

            pods.append({
                "name": name,
                "ready": ready,
                "status": status,
                "restarts": restarts,
                "age": age
            })

    return pods


@tool("k8s_get_pods")
def k8s_get_pods(namespace: str = "", all_namespaces: bool = True) -> str:
    """
    Get list of pods in a namespace or all namespaces.

    Args:
        namespace: Kubernetes namespace (default: '' = all namespaces)
        all_namespaces: If True, list pods from all namespaces (default: True)
    """
    if all_namespaces or not namespace:
        output = run_kubectl(["get", "pods", "--all-namespaces", "-o", "wide"])
    else:
        output = run_kubectl(["get", "pods", "-n", namespace, "-o", "wide"])

    return output


@tool("k8s_describe_pod")
def k8s_describe_pod(pod_name: str, namespace: str = "default") -> str:
    """
    Get detailed information about a specific pod.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: 'default')
    """
    output = run_kubectl(["describe", "pod", pod_name], namespace=namespace)
    return output


@tool("k8s_get_pod_logs")
def k8s_get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    container: Optional[str] = None,
    tail_lines: int = 100,
    since_minutes: Optional[int] = None
) -> str:
    """
    Get logs from a specific pod.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: 'default')
        container: Specific container name (optional, for multi-container pods)
        tail_lines: Number of recent lines to retrieve (default: 100)
        since_minutes: Only return logs newer than specified minutes
    """
    args = ["logs", pod_name, "--tail", str(tail_lines), "-o", "pretty"]

    if container:
        args.extend(["-c", container])

    if since_minutes:
        args.extend([f"--since={since_minutes}m"])

    output = run_kubectl(args, namespace=namespace)
    return output


@tool("k8s_search_pod_logs")
def k8s_search_pod_logs(
    pod_name: str,
    keyword: str,
    namespace: str = "default",
    tail_lines: int = 500
) -> str:
    """
    Search for specific keyword in pod logs.

    Args:
        pod_name: Name of the pod
        keyword: Keyword to search for
        namespace: Kubernetes namespace (default: 'default')
        tail_lines: Number of lines to search (default: 500)
    """
    logs = k8s_get_pod_logs(pod_name, namespace, tail_lines=tail_lines)

    if "Error" in logs or not logs:
        return logs

    lines = logs.split("\n")
    matching_lines = [line for line in lines if keyword.lower() in line.lower()]

    if not matching_lines:
        return f"No lines containing '{keyword}' found in the last {tail_lines} lines of logs."

    output = [f"# Search Results for '{keyword}' in {pod_name}"]
    output.append(f"Found {len(matching_lines)} matching lines:\n")

    for line in matching_lines[:50]:
        output.append(line)

    if len(matching_lines) > 50:
        output.append(f"\n... and {len(matching_lines) - 50} more matches")

    return "\n".join(output)


@tool("k8s_get_events")
def k8s_get_events(namespace: str = "default", since_minutes: int = 60) -> str:
    """
    Get recent events in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
        since_minutes: Only show events from the last N minutes (default: 60)
    """
    since = datetime.now() - timedelta(minutes=since_minutes)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")

    output = run_kubectl(
        ["get", "events", "--sort-by=.lastTimestamp", "-o", "wide"],
        namespace=namespace
    )

    lines = output.split("\n")
    filtered = [lines[0]] if lines else []

    for line in lines[1:]:
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                event_time = datetime.strptime(parts[0] + "T" + parts[1], "%Y-%m-%dT%H:%M:%S")
                if event_time >= since:
                    filtered.append(line)
            except ValueError:
                filtered.append(line)

    return "\n".join(filtered)


@tool("k8s_get_resource_usage")
def k8s_get_resource_usage(namespace: str = "default") -> str:
    """
    Get resource usage for all pods in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    output = run_kubectl(
        ["top", "pods", "-o", "custom-columns=NAME:.metadata.name,CPU:.spec.containers[0].resources.requests.cpu,MEMORY:.spec.containers[0].resources.requests.memory"],
        namespace=namespace
    )

    if "Error" in output or "cannot connect" in output.lower():
        output = "# Resource requests not available via kubectl top"
        output += "\n# This usually means metrics-server is not installed"
        output += "\n# Try querying Prometheus instead for actual usage metrics"

    return output


@tool("k8s_check_pod_status")
def k8s_check_pod_status(pod_name: str, namespace: str = "default") -> str:
    """
    Check the status and conditions of a specific pod.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: 'default')
    """
    describe = run_kubectl(["describe", "pod", pod_name], namespace=namespace)

    if "Error" in describe:
        return describe

    lines = describe.split("\n")
    status_info = []

    for i, line in enumerate(lines):
        if "Status:" in line:
            status_info.append(line)
        if "Conditions:" in line:
            for j in range(i, min(i + 6, len(lines))):
                status_info.append(lines[j])
        if "Containers:" in line:
            for j in range(i, min(i + 8, len(lines))):
                status_info.append(lines[j])
        if "Events:" in line:
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip():
                    status_info.append(lines[j])

    return "\n".join(status_info)


@tool("k8s_get_services")
def k8s_get_services(namespace: str = "default") -> str:
    """
    Get list of services in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    output = run_kubectl(["get", "services", "-o", "wide"], namespace=namespace)
    return output


@tool("k8s_get_deployments")
def k8s_get_deployments(namespace: str = "default") -> str:
    """
    Get list of deployments in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    output = run_kubectl(["get", "deployments", "-o", "wide"], namespace=namespace)
    return output


@tool("k8s_exec_in_pod")
def k8s_exec_in_pod(
    pod_name: str,
    command: str,
    namespace: str = "default",
    container: Optional[str] = None
) -> str:
    """
    Execute a command inside a pod.

    Args:
        pod_name: Name of the pod
        command: Command to execute
        namespace: Kubernetes namespace (default: 'default')
        container: Specific container name (optional)
    """
    args = ["exec", pod_name, "--", "sh", "-c", command]

    if container:
        args = ["exec", "-it", pod_name, "-c", container, "--", "sh", "-c", command]
    else:
        args = ["exec", pod_name, "--", "sh", "-c", command]

    output = run_kubectl(args, namespace=namespace)
    return output


@tool("k8s_get_node_info")
def k8s_get_node_info() -> str:
    """
    Get information about all cluster nodes.
    """
    output = run_kubectl(["get", "nodes", "-o", "wide"])
    return output


@tool("k8s_list_namespaces")
def k8s_list_namespaces() -> str:
    """
    List all Kubernetes namespaces.
    """
    output = run_kubectl(["get", "namespaces"])
    return output


@tool("k8s_get_persistent_volumes")
def k8s_get_persistent_volumes() -> str:
    """
    Get list of persistent volumes and their status.
    """
    output = run_kubectl(["get", "pv", "-o", "wide"])
    return output

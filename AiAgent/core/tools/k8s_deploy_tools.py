"""
Kubernetes deployment and management tools.
"""

import os
import subprocess
import time
from typing import Optional, List
from langchain_core.tools import tool

from core.tools.file_tools import write_file


def run_kubectl(args: List[str], namespace: Optional[str] = None) -> str:
    """Run kubectl command and return output."""
    cmd = ["kubectl"]
    if namespace:
        cmd.extend(["-n", namespace])
    cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: kubectl command timed out"
    except FileNotFoundError:
        return "Error: kubectl not found. Please ensure kubectl is installed and in PATH."
    except Exception as e:
        return f"Error running kubectl: {str(e)}"


def run_kubectl_apply(yaml_content: str, namespace: Optional[str] = None) -> str:
    """Apply YAML content using kubectl."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        result = run_kubectl(["apply", "-f", temp_path], namespace=namespace)
        return result
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def run_kubectl_delete(resource_type: str, name: str, namespace: str = "default") -> str:
    """Delete a resource using kubectl."""
    return run_kubectl(["delete", resource_type, name, "--ignore-not-found"], namespace=namespace)


@tool("k8s_create_namespace")
def k8s_create_namespace(name: str) -> str:
    """
    Create a Kubernetes namespace if it doesn't exist.

    Args:
        name: Name of the namespace to create
    """
    check_result = run_kubectl(["get", "namespace", name])
    if "Error" not in check_result and name in check_result:
        return f"Namespace '{name}' already exists."

    result = run_kubectl(["create", "namespace", name])
    if "Error" in result:
        return f"Failed to create namespace: {result}"
    return f"Namespace '{name}' created successfully."


@tool("k8s_apply_yaml")
def k8s_apply_yaml(yaml_content: str, namespace: Optional[str] = None) -> str:
    """
    Apply Kubernetes YAML configurations.

    Args:
        yaml_content: The YAML content to apply
        namespace: Optional namespace to apply in
    """
    result = run_kubectl_apply(yaml_content, namespace)
    if "Error" in result:
        return f"Failed to apply YAML: {result}"
    return f"YAML applied successfully:\n{result}"


@tool("k8s_apply_from_file")
def k8s_apply_from_file(file_path: str, namespace: Optional[str] = None) -> str:
    """
    Apply Kubernetes YAML from a file.

    Args:
        file_path: Path to the YAML file
        namespace: Optional namespace to apply in
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    result = run_kubectl(["apply", "-f", file_path], namespace=namespace)
    if "Error" in result:
        return f"Failed to apply YAML: {result}"
    return f"YAML applied successfully:\n{result}"


@tool("k8s_delete_resource")
def k8s_delete_resource(resource_type: str, name: str, namespace: str = "default") -> str:
    """
    Delete a Kubernetes resource.

    Args:
        resource_type: Type of resource (deployment, service, pod, etc.)
        name: Name of the resource
        namespace: Namespace (default: default)
    """
    result = run_kubectl_delete(resource_type, name, namespace)
    return f"Delete operation completed:\n{result}"


@tool("k8s_wait_for_pod")
def k8s_wait_for_pod(
    name_pattern: str,
    namespace: str = "default",
    timeout_seconds: int = 300,
    expected_count: int = 1
) -> str:
    """
    Wait for a pod to be ready.

    Args:
        name_pattern: Pod name pattern to match (can be partial name)
        namespace: Namespace
        timeout_seconds: Maximum time to wait (default: 300 seconds)
        expected_count: Expected number of ready pods (default: 1)
    """
    start_time = time.time()
    check_interval = 5

    while time.time() - start_time < timeout_seconds:
        result = run_kubectl(
            ["get", "pods", "-l", f"app={name_pattern}", "-o", "wide"],
            namespace=namespace
        )

        if "Running" in result:
            lines = result.strip().split("\n")
            running_count = sum(1 for line in lines[1:] if "Running" in line)
            if running_count >= expected_count:
                return f"Pod(s) ready! Found {running_count} running pod(s) matching '{name_pattern}'."

        elapsed = int(time.time() - start_time)
        print(f"Waiting for pod '{name_pattern}'... ({elapsed}s elapsed)")

        time.sleep(check_interval)

    return f"Timeout waiting for pod(s) matching '{name_pattern}'. Check status manually."


@tool("k8s_get_pod_status")
def k8s_get_pod_status(name: str, namespace: str = "default") -> str:
    """
    Get detailed status of a specific pod.

    Args:
        name: Pod name
        namespace: Namespace
    """
    result = run_kubectl(["get", "pod", name, "-o", "wide"], namespace=namespace)
    if "Error" in result:
        return result

    events_result = run_kubectl(["describe", "pod", name], namespace=namespace)

    output = [result, "\n--- Events ---", events_result]
    return "\n".join(output)


@tool("k8s_get_deployment_status")
def k8s_get_deployment_status(name: str, namespace: str = "default") -> str:
    """
    Get status of a deployment.

    Args:
        name: Deployment name
        namespace: Namespace
    """
    result = run_kubectl(["get", "deployment", name, "-o", "wide"], namespace=namespace)
    if "Error" in result:
        return result

    replicas_result = run_kubectl(["rollout", "status", "deployment", name], namespace=namespace)

    output = [result]
    if replicas_result:
        output.append(f"\n--- Rollout Status ---\n{replicas_result}")

    return "\n".join(output)


@tool("k8s_get_service_status")
def k8s_get_service_status(name: str, namespace: str = "default") -> str:
    """
    Get status of a service.

    Args:
        name: Service name
        namespace: Namespace
    """
    result = run_kubectl(["get", "service", name, "-o", "wide"], namespace=namespace)
    if "Error" in result:
        return result

    endpoints_result = run_kubectl(["get", "endpoints", name, "-o", "wide"], namespace=namespace)

    output = [result, "\n--- Endpoints ---", endpoints_result]
    return "\n".join(output)


@tool("k8s_check_service_endpoint")
def k8s_check_service_endpoint(name: str, namespace: str = "default") -> str:
    """
    Check if a service endpoint is reachable.

    Args:
        name: Service name
        namespace: Namespace
    """
    endpoints = run_kubectl(["get", "endpoints", name, "-o", "jsonpath={.subsets[*].addresses[*].ip}"], namespace=namespace)

    if not endpoints or endpoints == "":
        return f"Service '{name}' has no active endpoints. Pods may not be ready."

    return f"Service '{name}' has active endpoints: {endpoints}"


@tool("k8s_exec_in_pod")
def k8s_exec_in_pod(
    name: str,
    command: str,
    namespace: str = "default",
    container: Optional[str] = None
) -> str:
    """
    Execute a command inside a pod.

    Args:
        name: Pod name
        command: Command to execute
        namespace: Namespace
        container: Optional container name (for multi-container pods)
    """
    args = ["exec", name, "--", "sh", "-c", command]
    if container:
        args = ["exec", "-it", name, "-c", container, "--", "sh", "-c", command]

    result = run_kubectl(args, namespace=namespace)
    return result


@tool("k8s_port_forward")
def k8s_port_forward(
    name: str,
    local_port: int,
    remote_port: int,
    namespace: str = "default"
) -> str:
    """
    Create a port forward to a pod (this starts in background).

    Args:
        name: Pod name
        local_port: Local port to bind
        remote_port: Remote port on the pod
        namespace: Namespace
    """
    return (f"Port forward command (run manually in separate terminal):\n"
            f"kubectl port-forward {name} {local_port}:{remote_port} -n {namespace}")


@tool("k8s_scale_deployment")
def k8s_scale_deployment(name: str, replicas: int, namespace: str = "default") -> str:
    """
    Scale a deployment to a specific number of replicas.

    Args:
        name: Deployment name
        replicas: Number of replicas
        namespace: Namespace
    """
    result = run_kubectl(["scale", "--replicas", str(replicas), "deployment", name], namespace=namespace)
    if "Error" in result:
        return f"Failed to scale deployment: {result}"
    return f"Deployment '{name}' scaled to {replicas} replicas."


@tool("k8s_lookup_pod_image")
def k8s_lookup_pod_image(service_name: str, source_namespace: str = "bookinfo") -> str:
    """
    Look up the actual container image used by a running pod in the cluster.
    Use this to find the correct image before deploying.

    Args:
        service_name: Name of the service (e.g., 'details', 'reviews', 'productpage')
        source_namespace: Namespace to search in (default: 'bookinfo')
    """
    result = run_kubectl(
        ["get", "pods", "-l", f"app={service_name}", "-o", "jsonpath={.items[0].spec.containers[0].image}"],
        namespace=source_namespace
    )
    if result and "Error" not in result and result.strip():
        return f"Image for '{service_name}' in namespace '{source_namespace}': {result.strip()}"
    return f"Could not find a running pod for '{service_name}' in namespace '{source_namespace}'. Try checking with 'kubectl get pods -n {source_namespace}'."
    """
    Check rollout status of a deployment.

    Args:
        name: Deployment name
        namespace: Namespace
    """
    result = run_kubectl(["rollout", "status", "deployment", name], namespace=namespace)
    return result if result else "Rollout completed or no rollout in progress."


@tool("k8s_rollout_undo")
def k8s_rollout_undo(name: str, namespace: str = "default") -> str:
    """
    Undo a rollout to the previous revision.

    Args:
        name: Deployment name
        namespace: Namespace
    """
    result = run_kubectl(["rollout", "undo", "deployment", name], namespace=namespace)
    if "Error" in result:
        return f"Failed to undo rollout: {result}"
    return f"Rollout undo initiated for '{name}'."


@tool("k8s_get_resources")
def k8s_get_resources(resource_type: str, namespace: str = "default", label_selector: Optional[str] = None) -> str:
    """
    Get resources of a specific type.

    Args:
        resource_type: Type of resource (pods, services, deployments, etc.)
        namespace: Namespace (use empty string for all namespaces)
        label_selector: Optional label selector (e.g., 'app=myapp')
    """
    args = ["get", resource_type, "-o", "wide"]
    if label_selector:
        args.extend(["-l", label_selector])

    if namespace:
        result = run_kubectl(args, namespace=namespace)
    else:
        result = run_kubectl(args)

    return result


@tool("k8s_describe_resource")
def k8s_describe_resource(resource_type: str, name: str, namespace: str = "default") -> str:
    """
    Get detailed description of a resource.

    Args:
        resource_type: Type of resource
        name: Resource name
        namespace: Namespace
    """
    result = run_kubectl(["describe", resource_type, name], namespace=namespace)
    return result


@tool("k8s_save_yaml")
def k8s_save_yaml(yaml_content: str, file_path: str) -> str:
    """
    Save Kubernetes YAML to a file.

    Args:
        yaml_content: YAML content to save
        file_path: Path to save the file
    """
    result = write_file(yaml_content, file_path)
    return result


@tool("k8s_full_deploy")
def k8s_full_deploy(
    service_name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    container_port: int = 8080,
    service_port: int = 80,
    service_type: str = "ClusterIP"
) -> str:
    """
    Complete deployment pipeline: generate YAML, save, and apply to cluster.

    Args:
        service_name: Name of the service
        image: Docker image
        namespace: Namespace to deploy to
        replicas: Number of replicas
        container_port: Container port
        service_port: Service port
        service_type: Service type
    """
    from core.tools.k8s_yaml_tools import generate_k8s_deployment_yaml

    yaml_result = generate_k8s_deployment_yaml.invoke({
        "service_name": service_name,
        "image": image,
        "namespace": namespace,
        "replicas": replicas,
        "container_port": container_port,
        "service_port": service_port,
        "service_type": service_type
    })

    yaml_content = yaml_result if isinstance(yaml_result, str) else yaml_result.get("content", str(yaml_result))

    save_path = f"./output/k8s/{service_name}-deployment.yaml"
    os.makedirs(f"./output/k8s", exist_ok=True)
    save_result = write_file(yaml_content, save_path)

    apply_result = run_kubectl_apply(yaml_content, namespace)

    if "Error" in apply_result:
        return f"Deployment failed: {apply_result}"

    wait_result = k8s_wait_for_pod.invoke({
        "name_pattern": service_name,
        "namespace": namespace,
        "timeout_seconds": 180
    })

    return f"""Deployment Summary:
================
Service: {service_name}
Namespace: {namespace}
Image: {image}
Replicas: {replicas}

YAML saved to: {save_path}

Apply Result:
{apply_result}

Pod Status:
{wait_result}

Next steps:
- Check status: kubectl get pods -n {namespace}
- View logs: kubectl logs -l app={service_name} -n {namespace}
- Access service: kubectl get svc {service_name} -n {namespace}
"""

"""
Kubernetes YAML generation tools using LLM.
"""

import os
from typing import Optional
from langchain_core.tools import tool

from core.helper.llm_util import init_llm
from core.tools.file_tools import read_file, write_file


K8S_YAML_PROMPT = """
You are a Kubernetes expert. Generate Kubernetes YAML configuration for a service deployment.

## Service Requirements
{service_info}

## Output Format
Generate a complete Kubernetes manifest with:
1. Namespace (create if not exists)
2. Deployment with:
   - Appropriate replicas
   - Container port
   - Resource limits (cpu/memory)
   - Health probes if applicable
   - Environment variables from config if present
3. Service with:
   - Type (ClusterIP/NodePort/LoadBalancer)
   - Port mapping
4. ConfigMap/Secret if needed

Output ONLY valid YAML, no explanations or markdown.
"""


DEPLOYMENT_TEMPLATE_PROMPT = """
Generate a Kubernetes Deployment YAML for the following service:

- Service Name: {service_name}
- Image: {image}
- Namespace: {namespace}
- Replicas: {replicas}
- Container Port: {container_port}
- Service Port: {service_port}
- Service Type: {service_type}

Also generate the corresponding Service YAML.
Output ONLY valid Kubernetes YAML, no explanations.
"""


def generate_k8s_yaml(
    service_name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    container_port: int = 8080,
    service_port: int = 80,
    service_type: str = "ClusterIP",
    app_name: Optional[str] = None
) -> dict:
    """
    Generate Kubernetes YAML configurations using LLM.

    Args:
        service_name: Name of the service
        image: Docker image to use
        namespace: Kubernetes namespace
        replicas: Number of replicas
        container_port: Container port
        service_port: Service port
        service_type: Service type (ClusterIP, NodePort, LoadBalancer)
        app_name: Application name label

    Returns:
        dict: Contains 'deployment', 'service', and 'namespace' YAML strings
    """
    if app_name is None:
        app_name = service_name

    prompt = DEPLOYMENT_TEMPLATE_PROMPT.format(
        service_name=service_name,
        image=image,
        namespace=namespace,
        replicas=replicas,
        container_port=container_port,
        service_port=service_port,
        service_type=service_type
    )

    try:
        llm = init_llm()
        response = llm.invoke(prompt)
        yaml_content = response.content.strip()

        if yaml_content.startswith("```yaml"):
            yaml_content = yaml_content.replace("```yaml", "").replace("```", "").strip()
        elif yaml_content.startswith("```"):
            yaml_content = yaml_content.replace("```", "").strip()

        deployment_yaml = _extract_resource(yaml_content, "Deployment")
        service_yaml = _extract_resource(yaml_content, "Service")
        namespace_yaml = f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
"""

        return {
            "deployment": deployment_yaml,
            "service": service_yaml,
            "namespace": namespace_yaml,
            "full_manifest": yaml_content
        }
    except Exception as e:
        return {"error": f"Failed to generate YAML: {str(e)}"}


def _extract_resource(yaml_content: str, kind: str) -> str:
    """Extract a specific resource kind from YAML content."""
    lines = yaml_content.split("\n")
    in_resource = False
    resource_lines = []
    current_kind = None

    for line in lines:
        if line.startswith("---"):
            if in_resource and resource_lines:
                break
            in_resource = False
            current_kind = None

        if not in_resource:
            if f"kind: {kind}" in line:
                in_resource = True
                current_kind = kind

        if in_resource:
            resource_lines.append(line)

    return "\n".join(resource_lines)


def generate_simple_deployment(
    service_name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    container_port: int = 8080
) -> str:
    """Generate a simple Deployment YAML."""
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
  namespace: {namespace}
  labels:
    app: {service_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      containers:
      - name: {service_name}
        image: {image}
        ports:
        - containerPort: {container_port}
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
"""


def generate_simple_service(
    service_name: str,
    namespace: str = "default",
    container_port: int = 8080,
    service_port: int = 80,
    service_type: str = "ClusterIP"
) -> str:
    """Generate a simple Service YAML."""
    return f"""apiVersion: v1
kind: Service
metadata:
  name: {service_name}
  namespace: {namespace}
  labels:
    app: {service_name}
spec:
  type: {service_type}
  selector:
    app: {service_name}
  ports:
  - port: {service_port}
    targetPort: {container_port}
    protocol: TCP
"""


def generate_namespace(name: str) -> str:
    """Generate a Namespace YAML."""
    return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {name}
"""


@tool("generate_k8s_deployment_yaml")
def generate_k8s_deployment_yaml(
    service_name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    container_port: int = 8080,
    service_port: int = 80,
    service_type: str = "ClusterIP"
) -> str:
    """
    Generate Kubernetes Deployment and Service YAML configurations.

    Args:
        service_name: Name of the service (used for naming resources)
        image: Docker image URL (e.g., 'myregistry/myapp:v1')
        namespace: Kubernetes namespace to deploy to
        replicas: Number of pod replicas (default: 1)
        container_port: Port the container listens on
        service_port: Port the service exposes
        service_type: Service type - ClusterIP, NodePort, or LoadBalancer
    """
    result = generate_k8s_yaml(
        service_name=service_name,
        image=image,
        namespace=namespace,
        replicas=replicas,
        container_port=container_port,
        service_port=service_port,
        service_type=service_type
    )

    if "error" in result:
        return result["error"]

    output = ["# Generated Kubernetes Manifests\n"]

    output.append("# Namespace")
    output.append(result.get("namespace", generate_namespace(namespace)))
    output.append("\n# Deployment")
    output.append(result.get("deployment", generate_simple_deployment(
        service_name, image, namespace, replicas, container_port
    )))
    output.append("\n# Service")
    output.append(result.get("service", generate_simple_service(
        service_name, namespace, container_port, service_port, service_type
    )))

    return "\n---\n".join(output)


@tool("generate_deployment_only")
def generate_deployment_only(
    service_name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    container_port: int = 8080
) -> str:
    """
    Generate only the Deployment YAML.

    Args:
        service_name: Name of the service
        image: Docker image
        namespace: Namespace
        replicas: Number of replicas
        container_port: Container port
    """
    return generate_simple_deployment(
        service_name=service_name,
        image=image,
        namespace=namespace,
        replicas=replicas,
        container_port=container_port
    )


@tool("generate_service_only")
def generate_service_only(
    service_name: str,
    namespace: str = "default",
    container_port: int = 8080,
    service_port: int = 80,
    service_type: str = "ClusterIP"
) -> str:
    """
    Generate only the Service YAML.

    Args:
        service_name: Name of the service
        namespace: Namespace
        container_port: Target port on the pod
        service_port: Port the service exposes
        service_type: Service type
    """
    return generate_simple_service(
        service_name=service_name,
        namespace=namespace,
        container_port=container_port,
        service_port=service_port,
        service_type=service_type
    )


@tool("generate_ingress")
def generate_ingress(
    service_name: str,
    namespace: str = "default",
    host: str = "example.com",
    service_port: int = 80,
    path: str = "/",
    annotations: dict = None
) -> str:
    """
    Generate an Ingress resource for the service.

    Args:
        service_name: Name of the service (will be used as ingress name)
        namespace: Namespace
        host: Hostname for the ingress
        service_port: Port the service exposes
        path: URL path to route (default: /)
        annotations: Optional annotations (e.g., for TLS)
    """
    annotations_str = ""
    if annotations:
        for key, value in annotations.items():
            annotations_str += f"    {key}: {value}\n"

    if annotations_str:
        annotations_str = "\n  annotations:\n" + annotations_str.rstrip()

    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {service_name}
  namespace: {namespace}{annotations_str}
spec:
  ingressClassName: nginx
  rules:
  - host: {host}
    http:
      paths:
      - path: {path}
        pathType: Prefix
        backend:
          service:
            name: {service_name}
            port:
              number: {service_port}
"""


@tool("generate_configmap")
def generate_configmap(
    name: str,
    namespace: str = "default",
    data: dict = None
) -> str:
    """
    Generate a ConfigMap resource.

    Args:
        name: ConfigMap name
        namespace: Namespace
        data: Dictionary of key-value pairs
    """
    if data is None:
        data = {"key": "value"}

    data_lines = []
    for key, value in data.items():
        escaped_value = value.replace("\"", "\\\"")
        data_lines.append(f'  {key}: "{escaped_value}"')

    return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {name}
  namespace: {namespace}
data:
{"\\n".join(data_lines)}
"""


@tool("generate_secret")
def generate_secret(
    name: str,
    namespace: str = "default",
    data: dict = None,
    secret_type: str = "Opaque"
) -> str:
    """
    Generate a Secret resource.

    Args:
        name: Secret name
        namespace: Namespace
        data: Dictionary of key-value pairs (values should be base64 encoded or will be encoded)
        secret_type: Type of secret (Opaque, TLS, docker-registry, etc.)
    """
    import base64

    if data is None:
        data = {"username": "admin", "password": "changeme"}

    data_lines = []
    for key, value in data.items():
        encoded = base64.b64encode(value.encode()).decode()
        data_lines.append(f'  {key}: {encoded}')

    return f"""apiVersion: v1
kind: Secret
metadata:
  name: {name}
  namespace: {namespace}
type: {secret_type}
data:
{"\\n".join(data_lines)}
"""


@tool("generate_horizontal_pod_autoscaler")
def generate_horizontal_pod_autoscaler(
    service_name: str,
    namespace: str = "default",
    min_replicas: int = 1,
    max_replicas: int = 10,
    target_cpu_percent: int = 80
) -> str:
    """
    Generate a HorizontalPodAutoscaler resource.

    Args:
        service_name: Name of the deployment to scale
        namespace: Namespace
        min_replicas: Minimum number of pods
        max_replicas: Maximum number of pods
        target_cpu_percent: Target CPU utilization percentage
    """
    return f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {service_name}
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {service_name}
  minReplicas: {min_replicas}
  maxReplicas: {max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {target_cpu_percent}
"""


@tool("generate_persistent_volume_claim")
def generate_persistent_volume_claim(
    name: str,
    namespace: str = "default",
    storage_size: str = "10Gi",
    storage_class: str = "standard",
    access_modes: list = None
) -> str:
    """
    Generate a PersistentVolumeClaim resource.

    Args:
        name: PVC name
        namespace: Namespace
        storage_size: Size of the volume (e.g., '10Gi', '100Gi')
        storage_class: Storage class name
        access_modes: Access modes (ReadWriteOnce, ReadOnlyMany, ReadWriteMany)
    """
    if access_modes is None:
        access_modes = ["ReadWriteOnce"]

    modes_str = "\n".join([f"    - {mode}" for mode in access_modes])

    return f"""apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {name}
  namespace: {namespace}
spec:
  accessModes:
{modes_str}
  resources:
    requests:
      storage: {storage_size}
  storageClassName: {storage_class}
"""

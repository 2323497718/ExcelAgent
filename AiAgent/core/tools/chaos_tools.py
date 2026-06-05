"""
Chaos Mesh tools for fault injection queries and management.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool


class ChaosMeshClient:
    """Chaos Mesh API client."""

    def __init__(self, url: str = None, timeout: int = 30):
        """
        Initialize Chaos Mesh client.

        Args:
            url: Chaos Mesh Dashboard URL (default: from env or localhost:2333)
            timeout: Request timeout in seconds
        """
        self.url = url or os.getenv("CHAOS_MESH_URL", "http://localhost:2333")
        self.timeout = timeout

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Execute GET request to Chaos Mesh API."""
        url = f"{self.url}{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _delete(self, endpoint: str) -> Dict:
        """Execute DELETE request to Chaos Mesh API."""
        url = f"{self.url}{endpoint}"
        try:
            response = requests.delete(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _post(self, endpoint: str, json_data: Dict = None) -> Dict:
        """Execute POST request to Chaos Mesh API."""
        url = f"{self.url}{endpoint}"
        try:
            response = requests.post(url, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_experiments(self, namespace: str = None, kind: str = None) -> List[Dict]:
        """Get list of chaos experiments."""
        params = {}
        if namespace:
            params["namespace"] = namespace
        if kind:
            params["kind"] = kind

        result = self._get("/api/experiments", params)
        if "experiments" in result:
            return result["experiments"]
        return []

    def get_schedules(self, namespace: str = None) -> List[Dict]:
        """Get list of scheduled experiments."""
        params = {}
        if namespace:
            params["namespace"] = namespace

        result = self._get("/api/schedules", params)
        if "schedules" in result:
            return result["schedules"]
        return []

    def get_workflow_nodes(self, namespace: str = None) -> List[Dict]:
        """Get workflow nodes."""
        params = {}
        if namespace:
            params["namespace"] = namespace

        result = self._get("/api/workflows", params)
        if "nodes" in result:
            return result["nodes"]
        return []

    def delete_experiment(self, uid: str, namespace: str = "default") -> Dict:
        """Delete a chaos experiment."""
        return self._delete(f"/api/experiments/{namespace}/{uid}")


def init_chaos_client() -> ChaosMeshClient:
    """Initialize Chaos Mesh client from environment or defaults."""
    return ChaosMeshClient()


@tool("chaos_list_experiments")
def chaos_list_experiments(namespace: Optional[str] = None) -> str:
    """
    List all chaos experiments in a namespace or all namespaces.

    Args:
        namespace: Kubernetes namespace (optional, if None lists all)
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    if not experiments:
        return "No chaos experiments found."

    output = ["# Chaos Experiments\n"]
    for exp in experiments:
        name = exp.get("name", "unknown")
        ns = exp.get("namespace", "default")
        kind = exp.get("kind", "unknown")
        status = exp.get("status", "unknown")
        created = exp.get("created", "")

        output.append(f"\n## {name}")
        output.append(f"- Namespace: {ns}")
        output.append(f"- Kind: {kind}")
        output.append(f"- Status: {status}")
        output.append(f"- Created: {created}")

    return "\n".join(output)


@tool("chaos_get_network_chaos")
def chaos_get_network_chaos(namespace: str = "default") -> str:
    """
    Get all network chaos experiments in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    network_chaos = [e for e in experiments if e.get("kind") == "NetworkChaos"]

    if not network_chaos:
        return f"No NetworkChaos experiments found in namespace '{namespace}'."

    output = ["# Network Chaos Experiments\n"]
    for chaos in network_chaos:
        name = chaos.get("name", "unknown")
        status = chaos.get("status", "unknown")
        spec = chaos.get("spec", {})
        selector = spec.get("selector", [])

        output.append(f"\n## {name}")
        output.append(f"- Status: {status}")

        if isinstance(selector, list) and selector:
            for sel in selector[:3]:
                if isinstance(sel, dict):
                    output.append(f"- Selector: {sel}")

    return "\n".join(output)


@tool("chaos_get_pod_chaos")
def chaos_get_pod_chaos(namespace: str = "default") -> str:
    """
    Get all pod chaos experiments (failures, kills, etc.) in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    pod_chaos = [e for e in experiments if e.get("kind") in ["PodChaos", "PodKill", "PodFailure"]]

    if not pod_chaos:
        return f"No PodChaos experiments found in namespace '{namespace}'."

    output = ["# Pod Chaos Experiments\n"]
    for chaos in pod_chaos:
        name = chaos.get("name", "unknown")
        kind = chaos.get("kind", "unknown")
        status = chaos.get("status", "unknown")

        output.append(f"\n## {name}")
        output.append(f"- Type: {kind}")
        output.append(f"- Status: {status}")

    return "\n".join(output)


@tool("chaos_get_stress_chaos")
def chaos_get_stress_chaos(namespace: str = "default") -> str:
    """
    Get all stress chaos experiments (CPU/Memory stress) in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    stress_chaos = [e for e in experiments if e.get("kind") == "StressChaos"]

    if not stress_chaos:
        return f"No StressChaos experiments found in namespace '{namespace}'."

    output = ["# Stress Chaos Experiments\n"]
    for chaos in stress_chaos:
        name = chaos.get("name", "unknown")
        status = chaos.get("status", "unknown")
        spec = chaos.get("spec", {})

        output.append(f"\n## {name}")
        output.append(f"- Status: {status}")

        stressors = spec.get("stressors", {})
        if stressors:
            cpu_stress = stressors.get("cpu", {})
            mem_stress = stressors.get("memory", {})
            if cpu_stress:
                output.append(f"- CPU Stress: {cpu_stress}")
            if mem_stress:
                output.append(f"- Memory Stress: {mem_stress}")

    return "\n".join(output)


@tool("chaos_get_io_chaos")
def chaos_get_io_chaos(namespace: str = "default") -> str:
    """
    Get all IO chaos experiments (disk I/O faults) in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    io_chaos = [e for e in experiments if e.get("kind") == "IOChaos"]

    if not io_chaos:
        return f"No IOChaos experiments found in namespace '{namespace}'."

    output = ["# IO Chaos Experiments\n"]
    for chaos in io_chaos:
        name = chaos.get("name", "unknown")
        status = chaos.get("status", "unknown")

        output.append(f"\n## {name}")
        output.append(f"- Status: {status}")

    return "\n".join(output)


@tool("chaos_get_dns_chaos")
def chaos_get_dns_chaos(namespace: str = "default") -> str:
    """
    Get all DNS chaos experiments in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    dns_chaos = [e for e in experiments if e.get("kind") == "DNSChaos"]

    if not dns_chaos:
        return f"No DNSChaos experiments found in namespace '{namespace}'."

    output = ["# DNS Chaos Experiments\n"]
    for chaos in dns_chaos:
        name = chaos.get("name", "unknown")
        status = chaos.get("status", "unknown")

        output.append(f"\n## {name}")
        output.append(f"- Status: {status}")

    return "\n".join(output)


@tool("chaos_get_kernel_chaos")
def chaos_get_kernel_chaos(namespace: str = "default") -> str:
    """
    Get all kernel chaos experiments in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    kernel_chaos = [e for e in experiments if e.get("kind") == "KernelChaos"]

    if not kernel_chaos:
        return f"No KernelChaos experiments found in namespace '{namespace}'."

    output = ["# Kernel Chaos Experiments\n"]
    for chaos in kernel_chaos:
        name = chaos.get("name", "unknown")
        status = chaos.get("status", "unknown")

        output.append(f"\n## {name}")
        output.append(f"- Status: {status}")

    return "\n".join(output)


@tool("chaos_check_active_chaos")
def chaos_check_active_chaos(namespace: str = "default") -> str:
    """
    Check for any active (running) chaos experiments in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    active = [e for e in experiments if e.get("status") == "Running"]
    paused = [e for e in experiments if e.get("status") == "Paused"]

    output = ["# Chaos Status Check\n"]
    output.append(f"Namespace: {namespace}\n")

    if active:
        output.append(f"## 🔴 Active Experiments: {len(active)}\n")
        for exp in active:
            output.append(f"- **{exp.get('name')}** ({exp.get('kind')})")
    else:
        output.append("## ✅ No Active Experiments")

    if paused:
        output.append(f"\n## ⏸️ Paused Experiments: {len(paused)}")
        for exp in paused:
            output.append(f"- {exp.get('name')} ({exp.get('kind')})")

    return "\n".join(output)


@tool("chaos_get_time_chaos")
def chaos_get_time_chaos(namespace: str = "default") -> str:
    """
    Get all time chaos experiments (clock skew) in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    time_chaos = [e for e in experiments if e.get("kind") == "TimeChaos"]

    if not time_chaos:
        return f"No TimeChaos experiments found in namespace '{namespace}'."

    output = ["# Time Chaos Experiments\n"]
    for chaos in time_chaos:
        name = chaos.get("name", "unknown")
        status = chaos.get("status", "unknown")

        output.append(f"\n## {name}")
        output.append(f"- Status: {status}")

    return "\n".join(output)


@tool("chaos_get_schedules")
def chaos_get_schedules(namespace: str = "default") -> str:
    """
    Get all scheduled chaos experiments in a namespace.

    Args:
        namespace: Kubernetes namespace (default: 'default')
    """
    client = init_chaos_client()
    schedules = client.get_schedules(namespace=namespace)

    if not schedules:
        return f"No scheduled experiments found in namespace '{namespace}'."

    output = ["# Scheduled Chaos Experiments\n"]
    for schedule in schedules:
        name = schedule.get("name", "unknown")
        kind = schedule.get("kind", "unknown")
        status = schedule.get("status", "unknown")

        output.append(f"\n## {name}")
        output.append(f"- Kind: {kind}")
        output.append(f"- Status: {status}")

    return "\n".join(output)


@tool("chaos_diagnose_impact")
def chaos_diagnose_impact(
    service: str,
    namespace: str = "default",
    duration_minutes: int = 30
) -> str:
    """
    Diagnose potential chaos impact on a service by checking for related experiments.

    Args:
        service: Service or pod name to check
        namespace: Kubernetes namespace (default: 'default')
        duration_minutes: Time window to check (default: 30 minutes)
    """
    client = init_chaos_client()
    experiments = client.get_experiments(namespace=namespace)

    related = []
    for exp in experiments:
        name = exp.get("name", "").lower()
        kind = exp.get("kind", "")
        if service.lower() in name or kind.lower() in name:
            related.append(exp)

    output = ["# Chaos Impact Diagnosis\n"]
    output.append(f"Service: {service}")
    output.append(f"Namespace: {namespace}\n")

    if related:
        output.append(f"## 🔴 Found {len(related)} related chaos experiment(s):\n")
        for chaos in related:
            status = chaos.get("status", "unknown")
            kind = chaos.get("kind", "unknown")
            icon = "🔴" if status == "Running" else "⏸️" if status == "Paused" else "✅"

            output.append(f"{icon} **{chaos.get('name')}**")
            output.append(f"   - Kind: {kind}")
            output.append(f"   - Status: {status}\n")

        output.append("\n## Recommendations:")
        active = [c for c in related if c.get("status") == "Running"]
        if active:
            output.append("⚠️ Active chaos experiments detected. Consider pausing them if service degradation is observed.")
    else:
        output.append("✅ No chaos experiments found that directly target this service.")
        output.append("\n## Possible causes of degradation:")
        output.append("1. No active chaos - issue may be due to:")
        output.append("   - Application bugs")
        output.append("   - Resource constraints")
        output.append("   - Network issues not injected by Chaos Mesh")
        output.append("   - External dependencies")

    return "\n".join(output)

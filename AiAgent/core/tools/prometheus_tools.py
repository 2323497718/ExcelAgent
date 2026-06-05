"""
Prometheus query tools for the monitoring agent.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.tools import tool


class PrometheusClient:
    """Prometheus API client wrapper."""

    def __init__(self, url: str = None, timeout: int = 30):
        """
        Initialize Prometheus client.

        Args:
            url: Prometheus server URL (default: from env or localhost:9090)
            timeout: Request timeout in seconds
        """
        self.url = url or os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.timeout = timeout
        self.api_path = "/api/v1"

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Execute GET request to Prometheus API.

        Args:
            endpoint: API endpoint (e.g., /query, /query_range)
            params: Query parameters

        Returns:
            dict: API response
        """
        url = f"{self.url}{self.api_path}{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}

    def query(self, query: str, time: Optional[str] = None) -> Dict:
        """
        Execute instant query.

        Args:
            query: PromQL query string
            time: Evaluation timestamp (RFC3339 or Unix timestamp)

        Returns:
            dict: Query results
        """
        params = {"query": query}
        if time:
            params["time"] = time
        return self._get("/query", params)

    def query_range(
        self,
        query: str,
        start: float,
        end: float,
        step: str = "1m"
    ) -> Dict:
        """
        Execute range query.

        Args:
            query: PromQL query string
            start: Start timestamp (Unix)
            end: End timestamp (Unix)
            step: Query resolution step (e.g., "15s", "1m", "5m")

        Returns:
            dict: Range query results
        """
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        return self._get("/query_range", params)

    def get_targets(self) -> Dict:
        """Get list of active scrape targets."""
        return self._get("/targets")

    def get_label_values(self, label: str) -> Dict:
        """Get label values for a given label name."""
        return self._get(f"/label/{label}/values")

    def get_metric_metadata(self, metric: Optional[str] = None) -> Dict:
        """
        Get metadata for metrics.

        Args:
            metric: Optional metric name filter

        Returns:
            dict: Metric metadata
        """
        endpoint = "/metadata"
        params = {"metric": metric} if metric else {}
        return self._get(endpoint, params)

    def get_series(self, match_params: List[str], start: float = None, end: float = None) -> Dict:
        """Get series data matching the specified label matchers."""
        params = {"match[]": match_params}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return self._get("/series", params)


def init_prometheus_client() -> PrometheusClient:
    """Initialize Prometheus client from environment or defaults."""
    return PrometheusClient()


def format_query_result(result: Dict) -> str:
    """
    Format Prometheus query result to human-readable string.

    Args:
        result: Prometheus API response

    Returns:
        str: Formatted result
    """
    if result.get("status") != "success":
        return f"Query failed: {result.get('error', 'Unknown error')}"

    data = result.get("data", {})
    result_type = data.get("resultType")

    if result_type == "vector":
        results = data.get("result", [])
        if not results:
            return "No results found."

        formatted = []
        for item in results:
            metric = item.get("metric", {})
            raw_val = item.get("value", [])
            if isinstance(raw_val, list) and len(raw_val) >= 2:
                value = raw_val[1]
            else:
                value = raw_val
            metric_str = "{" + ", ".join(
                f'{k}="{v}"' for k, v in metric.items()
            ) + "}"
            formatted.append(f"{metric_str}: {value}")

        return "\n".join(formatted) if formatted else "No results found."

    elif result_type == "matrix":
        results = data.get("result", [])
        if not results:
            return "No results found."

        formatted = []
        for item in results:
            metric = item.get("metric", {})
            raw_values = item.get("values", [])
            metric_name = metric.get("__name__", "unknown")
            metric_labels = ", ".join(
                f'{k}="{v}"' for k, v in metric.items() if k != "__name__"
            )
            formatted.append(f"{metric_name}{{{metric_labels}}}:")
            for val_entry in raw_values:
                if isinstance(val_entry, list) and len(val_entry) >= 2:
                    ts, v = val_entry[0], val_entry[1]
                else:
                    continue
                dt = datetime.fromtimestamp(ts)
                formatted.append(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')}: {v}")
            formatted.append("")

        return "\n".join(formatted) if formatted else "No results found."

    return f"Result type: {result_type}"


@tool("prom_query_instant")
def prom_query_instant(query: str) -> str:
    """
    Execute an instant query against Prometheus.

    Args:
        query: PromQL query string (e.g., 'container_memory_usage_bytes{job="kubernetes-nodes"}')
    """
    client = init_prometheus_client()
    result = client.query(query)

    if result.get("status") == "error":
        return f"Query error: {result.get('error', 'Unknown error')}"

    return format_query_result(result)


@tool("prom_query_range")
def prom_query_range(query: str, duration_minutes: int = 5) -> str:
    """
    Execute a range query against Prometheus for time-series data.

    Args:
        query: PromQL query string
        duration_minutes: Time range to query (default: 5 minutes)
    """
    client = init_prometheus_client()

    end = datetime.now()
    start = end - timedelta(minutes=duration_minutes)

    result = client.query_range(
        query=query,
        start=start.timestamp(),
        end=end.timestamp(),
        step="30s"
    )

    if result.get("status") == "error":
        return f"Query error: {result.get('error', 'Unknown error')}"

    return format_query_result(result)


@tool("prom_get_pod_memory")
def prom_get_pod_memory(namespace: str = "default") -> str:
    """
    Get memory usage for all pods in a namespace.

    Args:
        namespace: Kubernetes namespace name (default: 'default')
    """
    query = f'sort_desc(sum(container_memory_working_set_bytes{{namespace="{namespace}"}}) by (pod))'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_pod_cpu")
def prom_get_pod_cpu(namespace: str = "default") -> str:
    """
    Get CPU usage (cores) for all pods in a namespace.

    Args:
        namespace: Kubernetes namespace name (default: 'default')
    """
    query = f'sort_desc(sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m])) by (pod))'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_namespace_pods")
def prom_get_namespace_pods(namespace: str) -> str:
    """
    List all pods in a specific namespace with their status.

    Args:
        namespace: Kubernetes namespace name
    """
    query = f'kube_pod_info{{namespace="{namespace}"}}'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_pod_restarts")
def prom_get_pod_restarts(namespace: str = "") -> str:
    """
    Get pod restart counts in a namespace.

    Args:
        namespace: Kubernetes namespace name (default: '' = all namespaces)
    """
    if namespace:
        query = f'sort_desc(sum by (pod) (kube_pod_container_status_restarts_total{{namespace="{namespace}"}}))'
    else:
        query = 'sort_desc(sum by (pod, namespace) (kube_pod_container_status_restarts_total))'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_node_status")
def prom_get_node_status() -> str:
    """
    Get status and resource usage of all Kubernetes nodes.
    """
    query = 'kube_node_status_condition{condition="Ready",status="true"}'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_node_resources")
def prom_get_node_resources() -> str:
    """
    Get CPU and memory allocatable resources for all nodes.
    """
    query = 'sort_desc(kube_node_status_allocatable_cpu_cores + kube_node_status_allocatable_memory_bytes)'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_persistent_volumes")
def prom_get_persistent_volumes() -> str:
    """
    Get PersistentVolume usage statistics.
    """
    query = 'kubelet_volume_stats_capacity_bytes + kubelet_volume_stats_available_bytes'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_deployment_replicas")
def prom_get_deployment_replicas(namespace: str = "default") -> str:
    """
    Get desired vs available replicas for deployments.

    Args:
        namespace: Kubernetes namespace name (default: 'default')
    """
    query = f'kube_deployment_spec_replicas{{namespace="{namespace}"}} or vector(0)'
    query2 = f'kube_deployment_status_available_replicas{{namespace="{namespace}"}} or vector(0)'
    client = init_prometheus_client()

    result1 = client.query(query)
    result2 = client.query(query2)

    return f"Desired replicas:\n{format_query_result(result1)}\n\nAvailable replicas:\n{format_query_result(result2)}"


@tool("prom_get_service_endpoints")
def prom_get_service_endpoints(namespace: str = "default") -> str:
    """
    Get service endpoint information.

    Args:
        namespace: Kubernetes namespace name (default: 'default')
    """
    query = f'kube_endpoint_info{{namespace="{namespace}"}}'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_list_namespaces")
def prom_list_namespaces() -> str:
    """
    List all Kubernetes namespaces.
    """
    query = 'kube_namespace_labels'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)


@tool("prom_get_workload_metrics")
def prom_get_workload_metrics(workload_type: str, namespace: str = "default") -> str:
    """
    Get aggregated metrics for a specific workload type.

    Args:
        workload_type: Type of workload (pod, deployment, daemonset, statefulset)
        namespace: Kubernetes namespace name (default: 'default')
    """
    query = f'sum by (workload, workload_type) (rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[]5m))'
    client = init_prometheus_client()
    result = client.query(query)
    return format_query_result(result)

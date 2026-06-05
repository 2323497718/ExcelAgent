"""
Jaeger tracing query tools for distributed tracing analysis.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.tools import tool


class JaegerClient:
    """Jaeger tracing API client."""

    def __init__(self, url: str = None, timeout: int = 30):
        """
        Initialize Jaeger client.

        Args:
            url: Jaeger UI/API URL (default: from env or localhost:16686)
            timeout: Request timeout in seconds
        """
        self.url = url or os.getenv("JAEGER_URL", "http://localhost:16686")
        self.timeout = timeout
        self.api_path = "/api/traces"

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Execute GET request to Jaeger API."""
        url = f"{self.url}{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _post(self, endpoint: str, json_data: Dict = None) -> Dict:
        """Execute POST request to Jaeger API."""
        url = f"{self.url}{endpoint}"
        try:
            response = requests.post(url, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def search_traces(
        self,
        service: str,
        operation: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        tags: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Search for traces matching criteria.

        Args:
            service: Service name
            operation: Optional operation name filter
            start: Start time (default: 1 hour ago)
            end: End time (default: now)
            limit: Maximum number of traces to return
            tags: Optional tags filter

        Returns:
            dict: Search results
        """
        if start is None:
            start = datetime.now() - timedelta(hours=1)
        if end is None:
            end = datetime.now()

        query = {
            "serviceName": service,
            "startTimeMin": int(start.timestamp() * 1000000),
            "endTimeMax": int(end.timestamp() * 1000000),
            "numTraces": limit
        }

        if operation:
            query["operationName"] = operation

        if tags:
            query["tags"] = tags

        return self._post("/api/traces", query)

    def get_trace(self, trace_id: str) -> Dict:
        """Get a specific trace by ID."""
        return self._get(f"/api/traces/{trace_id}")

    def get_services(self) -> List[str]:
        """Get list of all services."""
        result = self._get("/api/services")
        if "data" in result:
            return [s.get("name", "") for s in result["data"]]
        return []

    def get_service_operations(self, service: str) -> List[str]:
        """Get operations for a specific service."""
        result = self._get(f"/api/services/{service}/operations")
        if "data" in result:
            return [op.get("name", "") for op in result["data"]]
        return []

    def get_dependencies(self, start: datetime = None, end: datetime = None) -> Dict:
        """Get service dependencies graph."""
        params = {}
        if start:
            params["start"] = int(start.timestamp())
        if end:
            params["end"] = int(end.timestamp())
        return self._get("/api/dependencies", params)


def init_jaeger_client() -> JaegerClient:
    """Initialize Jaeger client from environment or defaults."""
    return JaegerClient()


def format_trace_data(traces: List[Dict]) -> str:
    """Format trace data into readable string."""
    if not traces:
        return "No traces found."

    results = []
    for trace in traces[:10]:
        trace_id = trace.get("traceID", "unknown")
        spans = trace.get("spans", [])
        duration = trace.get("duration", 0)

        results.append(f"\n## Trace ID: {trace_id}")
        results.append(f"- Duration: {duration / 1000:.2f} ms")
        results.append(f"- Spans: {len(spans)}")

        for span in spans[:5]:
            service = span.get("processName", span.get("serviceName", "unknown"))
            operation = span.get("operationName", "unknown")
            span_duration = span.get("duration", 0)
            results.append(f"  - [{service}] {operation}: {span_duration / 1000:.2f} ms")

    return "\n".join(results)


@tool("jaeger_search_traces")
def jaeger_search_traces(
    service: str,
    operation: Optional[str] = None,
    duration_minutes: int = 60,
    limit: int = 20
) -> str:
    """
    Search for traces in Jaeger for a specific service.

    Args:
        service: Service name (e.g., 'productpage', 'reviews', 'details')
        operation: Optional operation name filter
        duration_minutes: How far back to search (default: 60 minutes)
        limit: Maximum number of traces to return
    """
    client = init_jaeger_client()
    start = datetime.now() - timedelta(minutes=duration_minutes)

    result = client.search_traces(
        service=service,
        operation=operation,
        start=start,
        limit=limit
    )

    if "data" not in result:
        if "error" in result:
            return f"Jaeger query error: {result['error']}"
        return "No traces found or service not found in Jaeger."

    traces = result.get("data", [])
    if not traces:
        return f"No traces found for service '{service}' in the last {duration_minutes} minutes."

    return format_trace_data(traces)


@tool("jaeger_get_trace_detail")
def jaeger_get_trace_detail(trace_id: str) -> str:
    """
    Get detailed information about a specific trace.

    Args:
        trace_id: The trace ID from Jaeger
    """
    client = init_jaeger_client()
    result = client.get_trace(trace_id)

    if "data" not in result:
        if "error" in result:
            return f"Jaeger error: {result['error']}"
        return f"Trace {trace_id} not found."

    traces = result.get("data", [])
    if not traces:
        return f"Trace {trace_id} not found."

    trace = traces[0]
    spans = trace.get("spans", [])
    processes = trace.get("processes", {})

    output = [f"# Trace: {trace_id}"]
    output.append(f"Duration: {trace.get('duration', 0) / 1000:.2f} ms")
    output.append(f"Total Spans: {len(spans)}\n")

    for span in spans:
        span_id = span.get("spanID", "")[:8]
        operation = span.get("operationName", "unknown")
        service = span.get("processID", "")
        if service in processes:
            service = processes[service].get("serviceName", service)
        duration = span.get("duration", 0)
        tags = span.get("tags", [])

        output.append(f"\n## Span: {span_id}")
        output.append(f"Service: {service}")
        output.append(f"Operation: {operation}")
        output.append(f"Duration: {duration / 1000:.2f} ms")

        if tags:
            output.append("Tags:")
            for tag in tags[:10]:
                output.append(f"  - {tag.get('key')}: {tag.get('value')}")

    return "\n".join(output)


@tool("jaeger_analyze_latency")
def jaeger_analyze_latency(service: str, duration_minutes: int = 30) -> str:
    """
    Analyze trace latency patterns for a service.

    Args:
        service: Service name
        duration_minutes: Time window for analysis (default: 30 minutes)
    """
    client = init_jaeger_client()
    start = datetime.now() - timedelta(minutes=duration_minutes)

    result = client.search_traces(
        service=service,
        start=start,
        limit=100
    )

    if "data" not in result or not result["data"]:
        return f"No traces found for '{service}' in the last {duration_minutes} minutes."

    traces = result["data"]
    durations = [t.get("duration", 0) / 1000 for t in traces]

    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    min_duration = min(durations)

    slow_traces = [t for t in traces if t.get("duration", 0) / 1000 > avg_duration * 2]

    output = [f"## Latency Analysis for '{service}'"]
    output.append(f"\n**Time Window**: Last {duration_minutes} minutes")
    output.append(f"**Total Traces**: {len(traces)}")
    output.append(f"\n### Statistics (in ms)")
    output.append(f"| Metric | Value |")
    output.append(f"|--------|-------|")
    output.append(f"| Average | {avg_duration:.2f} |")
    output.append(f"| Maximum | {max_duration:.2f} |")
    output.append(f"| Minimum | {min_duration:.2f} |")
    output.append(f"| Slow (>2x avg) | {len(slow_traces)} |")

    if slow_traces:
        output.append(f"\n### Slow Traces")
        for trace in sorted(slow_traces, key=lambda x: x.get("duration", 0), reverse=True)[:5]:
            output.append(f"- Trace {trace.get('traceID', '')[:8]}...: {trace.get('duration', 0) / 1000:.2f} ms")

    return "\n".join(output)


@tool("jaeger_find_slow_dependencies")
def jaeger_find_slow_dependencies(service: str, threshold_ms: float = 1000) -> str:
    """
    Find slow dependencies in a service's call chain.

    Args:
        service: Service name
        threshold_ms: Latency threshold in ms (default: 1000)
    """
    client = init_jaeger_client()
    start = datetime.now() - timedelta(minutes=60)

    result = client.search_traces(
        service=service,
        start=start,
        limit=50
    )

    if "data" not in result or not result["data"]:
        return f"No traces found for '{service}'."

    traces = result["data"]
    span_stats = {}

    for trace in traces:
        processes = trace.get("processes", {})
        for span in trace.get("spans", []):
            operation = span.get("operationName", "unknown")
            duration = span.get("duration", 0) / 1000
            service_name = span.get("processID", "")

            if service_name in processes:
                service_name = processes[service_name].get("serviceName", service_name)

            key = f"{service_name}::{operation}"
            if key not in span_stats:
                span_stats[key] = {"durations": [], "count": 0}

            span_stats[key]["durations"].append(duration)
            span_stats[key]["count"] += 1

    slow_deps = []
    for key, stats in span_stats.items():
        avg = sum(stats["durations"]) / len(stats["durations"])
        if avg > threshold_ms:
            service_part, operation_part = key.split("::", 1)
            slow_deps.append({
                "service": service_part,
                "operation": operation_part,
                "avg_ms": avg,
                "count": stats["count"]
            })

    if not slow_deps:
        return f"No slow dependencies (> {threshold_ms}ms) found for '{service}'."

    output = [f"## Slow Dependencies for '{service}' (threshold: {threshold_ms}ms)"]
    output.append(f"\n| Service | Operation | Avg Latency | Calls |")
    output.append(f"|---------|-----------|-------------|-------|")
    for dep in sorted(slow_deps, key=lambda x: x["avg_ms"], reverse=True):
        output.append(f"| {dep['service']} | {dep['operation']} | {dep['avg_ms']:.2f} ms | {dep['count']} |")

    return "\n".join(output)


@tool("jaeger_list_services")
def jaeger_list_services() -> str:
    """
    List all services tracked by Jaeger.
    """
    client = init_jaeger_client()
    services = client.get_services()

    if not services:
        return "No services found in Jaeger. Check if Jaeger is running and scraping your services."

    output = ["## Services in Jaeger\n"]
    for service in sorted(services):
        output.append(f"- {service}")

    return "\n".join(output)


@tool("jaeger_get_call_chain")
def jaeger_get_call_chain(trace_id: str) -> str:
    """
    Get the call chain (span hierarchy) for a trace.

    Args:
        trace_id: The trace ID
    """
    client = init_jaeger_client()
    result = client.get_trace(trace_id)

    if "data" not in result or not result["data"]:
        return f"Trace {trace_id} not found."

    trace = result["data"][0]
    spans = trace.get("spans", [])
    processes = trace.get("processes", {})

    span_map = {}
    for span in spans:
        span_id = span.get("spanID")
        parent_span_id = None
        for ref in span.get("references", []):
            if ref.get("refType") == "CHILD_OF":
                parent_span_id = ref.get("spanID")
                break

        service = span.get("processID", "")
        if service in processes:
            service = processes[service].get("serviceName", service)

        span_map[span_id] = {
            "operation": span.get("operationName", "unknown"),
            "service": service,
            "duration": span.get("duration", 0) / 1000,
            "parent": parent_span_id,
            "depth": 0
        }

    for span_id, span_info in span_map.items():
        depth = 0
        current = span_info
        while current["parent"] and current["parent"] in span_map:
            depth += 1
            current = span_map[current["parent"]]
        span_info["depth"] = depth

    output = [f"# Call Chain for Trace {trace_id[:8]}...\n"]
    sorted_spans = sorted(span_map.values(), key=lambda x: x["depth"])

    for span_info in sorted_spans[:20]:
        indent = "  " * span_info["depth"]
        output.append(f"{indent}└─ [{span_info['service']}] {span_info['operation']} ({span_info['duration']:.2f}ms)")

    return "\n".join(output)

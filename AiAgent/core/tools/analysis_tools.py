"""
Data analysis tools for monitoring agent.
"""

from typing import Dict, List, Any
from langchain_core.tools import tool


@tool("analyze_resource_usage")
def analyze_resource_usage(metrics_data: str) -> str:
    """
    Analyze resource usage data and provide insights.

    Args:
        metrics_data: Raw metrics data from Prometheus query
    """
    if not metrics_data or "No results" in metrics_data:
        return "No data available for analysis."

    lines = metrics_data.strip().split("\n")
    if not lines:
        return "No data available for analysis."

    insights = []
    insights.append("## Resource Usage Analysis\n")

    values = []
    for line in lines:
        if "{" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                try:
                    value = float(parts[-1].strip())
                    values.append(value)
                except ValueError:
                    continue

    if not values:
        return "Unable to parse resource data."

    total = sum(values)
    avg = total / len(values)
    max_val = max(values)
    min_val = min(values)

    insights.append(f"- **Total**: {total:.2f}")
    insights.append(f"- **Average**: {avg:.2f}")
    insights.append(f"- **Maximum**: {max_val:.2f}")
    insights.append(f"- **Minimum**: {min_val:.2f}")
    insights.append(f"- **Count**: {len(values)} pods/services")

    high_usage = [v for v in values if v > avg * 1.5]
    if high_usage:
        insights.append(f"\n⚠️ **Warning**: {len(high_usage)} item(s) have usage > 150% of average")

    return "\n".join(insights)


@tool("compare_services")
def compare_services(service1_data: str, service2_data: str, service1_name: str = "Service 1", service2_name: str = "Service 2") -> str:
    """
    Compare metrics between two services.

    Args:
        service1_data: Metrics data for service 1
        service2_data: Metrics data for service 2
        service1_name: Name of service 1
        service2_name: Name of service 2
    """
    def extract_values(data: str) -> float:
        try:
            lines = data.strip().split("\n")
            for line in lines:
                if ": " in line:
                    return float(line.split(": ")[-1].strip())
            return 0.0
        except:
            return 0.0

    val1 = extract_values(service1_data)
    val2 = extract_values(service2_data)

    comparison = f"## Service Comparison: {service1_name} vs {service2_name}\n\n"
    comparison += f"| Metric | {service1_name} | {service2_name} |\n"
    comparison += f"|--------|---------------|---------------|\n"
    comparison += f"| Value | {val1:.2f} | {val2:.2f} |\n"

    if val1 > val2:
        ratio = val1 / val2 if val2 > 0 else float('inf')
        comparison += f"\n📊 **{service1_name}** uses **{ratio:.1f}x** more resources than {service2_name}"
    elif val2 > val1:
        ratio = val2 / val1 if val1 > 0 else float('inf')
        comparison += f"\n📊 **{service2_name}** uses **{ratio:.1f}x** more resources than {service1_name}"
    else:
        comparison += f"\n✅ Both services have similar resource usage"

    return comparison


@tool("detect_anomalies")
def detect_anomalies(metrics_data: str, threshold_percent: float = 150.0) -> str:
    """
    Detect anomalies in metrics data based on threshold.

    Args:
        metrics_data: Raw metrics data
        threshold_percent: Threshold percentage above average to flag as anomaly
    """
    if not metrics_data or "No results" in metrics_data:
        return "No data available for anomaly detection."

    results = []
    lines = metrics_data.strip().split("\n")

    values = []
    items = []

    for line in lines:
        if "{" in line:
            try:
                metric_part = line.split("{")[1].split("}")[0] if "}" in line else ""
                value_part = line.split(":")[-1].strip()
                value = float(value_part)
                values.append(value)
                items.append((metric_part, value))
            except (ValueError, IndexError):
                continue

    if not values:
        return "Unable to parse metrics data."

    avg = sum(values) / len(values)
    threshold = avg * (threshold_percent / 100)

    results.append("## Anomaly Detection Results\n")
    results.append(f"- **Average**: {avg:.2f}")
    results.append(f"- **Threshold**: {threshold:.2f} ({threshold_percent}% of average)\n")

    anomalies = [(m, v) for m, v in items if v > threshold]
    normal = [(m, v) for m, v in items if v <= threshold]

    if anomalies:
        results.append("### 🔴 Anomalies Detected:\n")
        for metric, value in sorted(anomalies, key=lambda x: x[1], reverse=True):
            pct = (value / avg - 1) * 100
            results.append(f"- **{metric}**: {value:.2f} (+{pct:.1f}% above average)")
    else:
        results.append("✅ **No anomalies detected** - all values within normal range")

    if normal:
        results.append(f"\n### ✅ Normal Items: {len(normal)}")

    return "\n".join(results)


@tool("generate_summary_report")
def generate_summary_report(data_points: List[Dict[str, Any]], report_title: str = "Monitoring Summary") -> str:
    """
    Generate a formatted summary report from multiple data points.

    Args:
        data_points: List of dictionaries with 'name', 'value', and optional 'unit'
        report_title: Title for the report
    """
    if not data_points:
        return "No data provided for report."

    report = [f"# {report_title}\n"]
    report.append(f"## Summary ({len(data_points)} items)\n")

    total_value = 0
    for i, point in enumerate(data_points, 1):
        name = point.get("name", f"Item {i}")
        value = point.get("value", 0)
        unit = point.get("unit", "")
        status = point.get("status", "normal")

        unit_str = f" {unit}" if unit else ""
        status_icon = "✅" if status == "normal" else "⚠️" if status == "warning" else "🔴"

        report.append(f"{status_icon} **{name}**: {value:.2f}{unit_str}")
        total_value += value if isinstance(value, (int, float)) else 0

    report.append(f"\n## Total: {total_value:.2f}")

    return "\n".join(report)


@tool("format_metrics_table")
def format_metrics_table(metrics_data: str, metric_name: str = "Metric") -> str:
    """
    Format metrics data into a markdown table.

    Args:
        metrics_data: Raw metrics data from Prometheus
        metric_name: Name of the metric for the table header
    """
    if not metrics_data or "No results" in metrics_data:
        return "| # | Resource | Value |\n|---|----------|-------|\n| - | No data | - |"

    lines = metrics_data.strip().split("\n")
    rows = []

    for i, line in enumerate(lines, 1):
        if "{" in line and ":" in line:
            try:
                metric_part = line.split("{")[1].split("}")[0] if "}" in line else ""
                value_part = line.split(":")[-1].strip()

                pod_name = ""
                if 'pod="' in metric_part:
                    start = metric_part.find('pod="') + 5
                    end = metric_part.find('"', start)
                    pod_name = metric_part[start:end] if end > start else "unknown"
                else:
                    pod_name = f"item_{i}"

                rows.append(f"| {i} | {pod_name} | {value_part} |")
            except (IndexError, ValueError):
                continue

    if not rows:
        return "| # | Resource | Value |\n|---|----------|-------|\n| - | No data | - |"

    table = [f"| # | Resource | {metric_name} |", "|---|----------|-------|"]
    table.extend(rows)

    return "\n".join(table)


@tool("calculate_trend")
def calculate_trend(time_series_data: str) -> str:
    """
    Calculate trend direction from time series data.

    Args:
        time_series_data: Time series metrics data
    """
    if not time_series_data:
        return "No data available for trend analysis."

    values = []
    lines = time_series_data.strip().split("\n")

    for line in lines:
        if ":" in line and not line.startswith("-"):
            try:
                parts = line.strip().split(":")
                value = float(parts[-1].strip())
                values.append(value)
            except ValueError:
                continue

    if len(values) < 2:
        return "Not enough data points for trend analysis."

    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]

    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)

    change_pct = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0

    trend = "## Trend Analysis\n\n"

    if change_pct > 10:
        trend += "📈 **Uptrend**: Values increased by {:.1f}%\n".format(change_pct)
        trend += "   - Early average: {:.2f}\n".format(avg_first)
        trend += "   - Recent average: {:.2f}\n".format(avg_second)
        trend += "   - This may indicate increasing load or potential issue"
    elif change_pct < -10:
        trend += "📉 **Downtrend**: Values decreased by {:.1f}%\n".format(abs(change_pct))
        trend += "   - Early average: {:.2f}\n".format(avg_first)
        trend += "   - Recent average: {:.2f}\n".format(avg_second)
        trend += "   - Resources may be being released or issue is resolving"
    else:
        trend += "➡️ **Stable**: Values remained relatively stable ({:.1f}% change)\n".format(change_pct)
        trend += "   - Early average: {:.2f}\n".format(avg_first)
        trend += "   - Recent average: {:.2f}\n".format(avg_second)

    return trend

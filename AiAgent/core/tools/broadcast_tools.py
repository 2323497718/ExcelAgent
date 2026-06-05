"""
Cluster Status Broadcaster tools for the monitoring agent.

包含：
- 集群状态播报报告生成
- Prometheus 查询封装
- 多渠道推送（钉钉、飞书、Webhook）
"""

import os
import re
import json
import time
import uuid
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from core.tools.prometheus_tools import (
    PrometheusClient,
    init_prometheus_client,
    format_query_result,
)


# ==================== 报告生成工具 ====================

@tool("broadcast_cluster_status")
def broadcast_cluster_status(
    namespace: str = "",
    time_range_minutes: int = 30,
    include_anomalies: bool = True,
    format: str = "markdown"
) -> str:
    """
    生成集群状态播报报告，包含节点状态、Pod 分布、资源使用率、服务健康和异常告警。
    适合定时触发并推送播报给运维团队。

    Args:
        namespace: Kubernetes 命名空间（为空则查所有）
        time_range_minutes: 统计时间窗口（分钟），默认 30
        include_anomalies: 是否包含异常检测
        format: 输出格式，可选 markdown / json / html
    """
    client = init_prometheus_client()
    now = datetime.now()
    start = now - timedelta(minutes=time_range_minutes)

    report_id = f"rpt_{now.strftime('%Y%m%d_%H%M%S')}"

    node_status = _query_node_status(client)
    pod_metrics = _query_pod_metrics(client, namespace)
    cluster_summary = _build_summary(node_status, pod_metrics)
    anomalies = _detect_anomalies(pod_metrics) if include_anomalies else []

    markdown_report = _render_markdown(
        report_id, now, time_range_minutes,
        cluster_summary, pod_metrics, anomalies, namespace
    )

    if format == "json":
        result = {
            "report_id": report_id,
            "timestamp": now.isoformat(),
            "duration_minutes": time_range_minutes,
            "summary": cluster_summary,
            "pods": pod_metrics,
            "anomalies": anomalies,
            "raw_markdown": markdown_report,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    elif format == "html":
        html = _render_html(markdown_report, report_id, now)
        return html

    return markdown_report


def _query_node_status(client: PrometheusClient) -> List[Dict]:
    query = 'kube_node_status_condition{condition="Ready",status="true"}'
    result = client.query(query)
    return _parse_vector(result)


def _query_pod_metrics(client: PrometheusClient, namespace: str = "") -> List[Dict]:
    namespace_filter = f'{{namespace="{namespace}"}}' if namespace else ''
    cpu_query = f'sum by (pod, namespace) (rate(container_cpu_usage_seconds_total{namespace_filter}[5m]))'
    mem_query = f'sum by (pod, namespace) (container_memory_working_set_bytes{namespace_filter})'

    cpu_data = _parse_vector(client.query(cpu_query))
    mem_data = _parse_vector(client.query(mem_query))

    mem_map = {item["metric"].get("namespace", "") + "/" + item["metric"].get("pod", ""): item["value"]
               for item in mem_data}

    pods = []
    for cpu_item in cpu_data:
        ns = cpu_item["metric"].get("namespace", "")
        pod = cpu_item["metric"].get("pod", "")
        key = ns + "/" + pod
        mem_val = mem_map.get(key, 0)

        pods.append({
            "namespace": ns,
            "pod_name": pod,
            "cpu_cores": round(float(cpu_item["value"]), 4),
            "memory_bytes": float(mem_val),
            "memory_mib": round(float(mem_val) / (1024 * 1024), 1),
        })

    return pods


def _parse_vector(result: Dict) -> List[Dict]:
    if result.get("status") != "success":
        return []
    data = result.get("data", {})
    if data.get("resultType") != "vector":
        return []
    results = data.get("result", [])
    normalized = []
    for item in results:
        metric = item.get("metric", {})
        raw_val = item.get("value", [])
        if isinstance(raw_val, list) and len(raw_val) >= 2:
            value = raw_val[1]
        else:
            value = raw_val
        normalized.append({"metric": metric, "value": value})
    return normalized


def _build_summary(node_status: List[Dict], pod_metrics: List[Dict]) -> Dict:
    healthy_nodes = len(node_status)
    total_nodes = max(healthy_nodes, 1)

    total_pods = len(pod_metrics)
    running_pods = total_pods
    failed_pods = 0
    pending_pods = 0

    if pod_metrics:
        avg_cpu = sum(p["cpu_cores"] for p in pod_metrics) / len(pod_metrics)
        avg_mem = sum(p["memory_mib"] for p in pod_metrics) / len(pod_metrics)
    else:
        avg_cpu = 0.0
        avg_mem = 0.0

    cluster_health = "healthy"
    if failed_pods > 0 or healthy_nodes < total_nodes:
        cluster_health = "degraded"
    if failed_pods > total_pods * 0.1:
        cluster_health = "unhealthy"

    return {
        "total_nodes": total_nodes,
        "healthy_nodes": healthy_nodes,
        "total_pods": total_pods,
        "running_pods": running_pods,
        "failed_pods": failed_pods,
        "pending_pods": pending_pods,
        "cluster_health": cluster_health,
        "avg_cpu_usage_percent": round(avg_cpu * 100, 1),
        "avg_memory_usage_mib": round(avg_mem, 1),
    }


def _detect_anomalies(pod_metrics: List[Dict], threshold_cpu: float = 0.8, threshold_mem_mib: float = 500.0) -> List[Dict]:
    anomalies = []
    if not pod_metrics:
        return anomalies

    avg_cpu = sum(p["cpu_cores"] for p in pod_metrics) / len(pod_metrics)
    avg_mem = sum(p["memory_mib"] for p in pod_metrics) / len(pod_metrics)

    for pod in pod_metrics:
        if pod["cpu_cores"] > avg_cpu * 2.5:
            anomalies.append({
                "severity": "warning",
                "type": "high_cpu",
                "resource": f"{pod['namespace']}/{pod['pod_name']}",
                "current_value": pod["cpu_cores"],
                "threshold": round(avg_cpu * 2.5, 4),
                "message": f"Pod {pod['pod_name']} CPU 使用率是平均值的 {pod['cpu_cores']/avg_cpu:.1f} 倍",
                "suggestion": "检查应用是否存在 CPU 密集型操作，考虑扩容或优化",
            })
        if pod["memory_mib"] > avg_mem * 3:
            anomalies.append({
                "severity": "warning",
                "type": "high_memory",
                "resource": f"{pod['namespace']}/{pod['pod_name']}",
                "current_value": pod["memory_mib"],
                "threshold": round(avg_mem * 3, 1),
                "message": f"Pod {pod['pod_name']} 内存 {pod['memory_mib']} MiB 超过阈值",
                "suggestion": "检查内存泄漏，考虑增加内存限制或重启 Pod",
            })
    return anomalies


def _render_markdown(
    report_id: str,
    now: datetime,
    duration_minutes: int,
    summary: Dict,
    pod_metrics: List[Dict],
    anomalies: List[Dict],
    namespace: str
) -> str:
    ns_tag = f"命名空间 `{namespace}`" if namespace else "所有命名空间"

    emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🔴"}.get(summary["cluster_health"], "❓")

    lines = [
        f"# 集群状态播报报告",
        f"**报告 ID**: `{report_id}`  |  **生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}  |  **统计窗口**: 最近 {duration_minutes} 分钟",
        f"",
        f"## 集群健康状态  {emoji} **{summary['cluster_health'].upper()}**",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 节点健康 | {summary['healthy_nodes']}/{summary['total_nodes']} |",
        f"| Pod 运行 | {summary['running_pods']}/{summary['total_pods']} |",
        f"| Pod 失败 | {summary['failed_pods']} |",
        f"| 平均 CPU | {summary['avg_cpu_usage_percent']:.1f}% |",
        f"| 平均内存 | {summary['avg_memory_usage_mib']:.1f} MiB |",
        f"|",
        f"| 查询范围 | {ns_tag} |",
        f"|",
    ]

    if anomalies:
        lines.append("## 异常告警 ⚠️")
        lines.append("")
        for a in anomalies:
            sev = {"info": "ℹ️", "warning": "⚠️", "critical": "🔴"}.get(a["severity"], "❓")
            lines.append(f"{sev} **[{a['severity'].upper()}]** {a['message']}")
            lines.append(f"   - 资源: `{a['resource']}`")
            lines.append(f"   - 建议: {a['suggestion']}")
            lines.append("")
    else:
        lines.append("## 异常告警 ✅ 无异常")

    if pod_metrics:
        lines.append(f"## Pod 资源使用详情 (共 {len(pod_metrics)} 个)")
        lines.append("")
        lines.append("| Pod 名称 | 命名空间 | CPU (cores) | 内存 (MiB) |")
        lines.append("|----------|----------|-------------|------------|")
        for p in sorted(pod_metrics, key=lambda x: x["cpu_cores"], reverse=True)[:20]:
            cpu = f"{p['cpu_cores']:.4f}"
            mem = f"{p['memory_mib']:.1f}"
            lines.append(f"| `{p['pod_name'][:40]}` | {p['namespace']} | {cpu} | {mem} |")
        if len(pod_metrics) > 20:
            lines.append(f"| ... | (共 {len(pod_metrics)} 个 Pod) | | |")

    lines.append("")
    lines.append(f"*本报告由集群状态播报员自动生成 · {now.strftime('%Y-%m-%d %H:%M:%S')}*")
    return "\n".join(lines)


def _render_html(markdown_text: str, report_id: str, now: datetime) -> str:
    html_body = markdown_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for emoji, img in [
        ("✅", "✅"), ("⚠️", "⚠️"), ("🔴", "🔴"), ("ℹ️", "ℹ️"),
        ("# ", "<h1>"), ("## ", "<h2>"), ("### ", "<h3>"),
        ("**", "<strong>"), ("`", "<code>"),
        ("\n\n", "</p><p>"),
        ("\n", "<br>"),
    ]:
        if emoji == "# ":
            html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
        elif emoji == "## ":
            html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
        elif emoji == "### ":
            html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
        elif emoji == "**":
            html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
        elif emoji == "`":
            html_body = re.sub(r'`(.+?)`', r'<code>\1</code>', html_body)
            html_body = re.sub(r'\|(.+?)\|', lambda m: '<tr>' + ''.join(f'<td>{c.strip()}</td>' for c in m.group(1).split('|') if c.strip()) + '</tr>', html_body)
        elif emoji == "\n\n":
            html_body = html_body.replace("\n\n", "</p><p>")
        elif emoji == "\n":
            html_body = html_body.replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>集群状态播报 {report_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #333; }}
  h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
  h2 {{ color: #34495e; margin-top: 30px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #3498db; color: white; }}
  tr:nth-child(even) {{ background: #f9f9f9; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  strong {{ color: #e74c3c; }}
  .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 0.85em; }}
</style>
</head>
<body>
<p>{html_body}</p>
<div class="footer">由集群状态播报员自动生成 · {now.strftime('%Y-%m-%d %H:%M:%S')}</div>
</body>
</html>"""


# ==================== Prometheus 查询封装工具 ====================

@tool("broadcast_prometheus_query")
def broadcast_prometheus_query(query: str, query_type: str = "instant") -> str:
    """
    执行 Prometheus 查询，返回格式化后的结果。
    替代直接写 PromQL 的复杂查询，LLM 可直接调用此工具获得结构化输出。

    Args:
        query: PromQL 查询语句
        query_type: 查询类型，instant（瞬时）/ range（范围）
    """
    client = init_prometheus_client()

    if query_type == "range":
        end = time.time()
        start = end - 300
        result = client.query_range(query, start, end, step="30s")
    else:
        result = client.query(query)

    if result.get("status") == "error":
        return f"查询失败: {result.get('error', '未知错误')}"

    formatted = format_query_result(result)
    return f"[Prometheus 查询结果]\n查询: {query}\n类型: {query_type}\n\n{formatted}"


@tool("broadcast_pod_metrics")
def broadcast_pod_metrics(namespace: str = "default", metric_type: str = "all") -> str:
    """
    获取指定命名空间下所有 Pod 的 CPU 和内存使用情况。
    替代多条 PromQL 查询，LLM 可直接调用此工具。

    Args:
        namespace: Kubernetes 命名空间
        metric_type: 指标类型 cpu / memory / all
    """
    client = init_prometheus_client()
    ns_filter = f'{{namespace="{namespace}"}}'

    if metric_type in ("cpu", "all"):
        cpu_query = f'sum by (pod, namespace) (rate(container_cpu_usage_seconds_total{ns_filter}[5m]))'
        cpu_data = _parse_vector(client.query(cpu_query))
    else:
        cpu_data = []

    if metric_type in ("memory", "all"):
        mem_query = f'sum by (pod, namespace) (container_memory_working_set_bytes{ns_filter})'
        mem_data = _parse_vector(client.query(mem_query))
        mem_map = {
            m["metric"].get("pod", ""): float(m["value"])
            for m in mem_data
        }
    else:
        mem_map = {}

    if not cpu_data and not mem_map:
        return f"命名空间 `{namespace}` 下未找到 Pod 数据"

    rows = []
    all_pods = set(list(m["metric"].get("pod", "") for m in cpu_data) + list(mem_map.keys()))

    for pod in sorted(all_pods):
        cpu_val = next((float(m["value"]) for m in cpu_data if m["metric"].get("pod") == pod), None)
        mem_val = mem_map.get(pod, 0)
        ns_val = next((m["metric"].get("namespace", namespace) for m in cpu_data if m["metric"].get("pod") == pod), namespace)

        cpu_str = f"{cpu_val:.4f} cores" if cpu_val is not None else "N/A"
        mem_str = f"{mem_val/(1024*1024):.1f} MiB" if mem_val else "N/A"

        rows.append(f"| `{pod[:40]}` | {ns_val} | {cpu_str} | {mem_str} |")

    header = f"## Pod 资源指标 — 命名空间 `{namespace}`\n\n"
    header += "| Pod 名称 | 命名空间 | CPU | 内存 |\n"
    header += "|----------|----------|-----|------|\n"

    return header + "\n".join(rows) + f"\n\n*共 {len(all_pods)} 个 Pod*"


# ==================== 推送工具 ====================

@tool("broadcast_push_report")
def broadcast_push_report(
    content: str,
    channel: str = "webhook",
    title: str = "集群状态播报",
    webhook_url: str = "",
    at_mobiles: Optional[List[str]] = None
) -> str:
    """
    将播报报告推送到指定的通知渠道。
    支持钉钉 (dingtalk)、飞书 (feishu)、通用 Webhook、Slack。

    Args:
        content: 推送内容（Markdown 格式）
        channel: 推送渠道 dingtalk / feishu / webhook / slack
        title: 推送标题
        webhook_url: Webhook 地址（webhook 渠道必填）
        at_mobiles: 需要 @ 的手机号列表
    """
    if channel == "webhook" and not webhook_url:
        return "错误: webhook 渠道需要提供 webhook_url 参数"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if channel == "dingtalk":
        result = _push_dingtalk(webhook_url, title, content, at_mobiles or [])
    elif channel == "feishu":
        result = _push_feishu(webhook_url, title, content, at_mobiles or [])
    elif channel == "slack":
        result = _push_slack(webhook_url, content)
    else:
        result = _push_generic_webhook(webhook_url, title, content)

    if result.get("success"):
        return f"✅ 推送成功 [{channel}] — {now}\n渠道: {channel}\n标题: {title}\n结果: {result.get('message', 'OK')}"
    else:
        return f"❌ 推送失败 [{channel}] — {now}\n错误: {result.get('message', '未知错误')}"


def _push_dingtalk(webhook_url: str, title: str, content: str, at_mobiles: List[str]) -> Dict:
    try:
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            },
            "at": {
                "atMobiles": at_mobiles,
                "isAtAll": False
            }
        }
        resp = requests.post(webhook_url, json=payload, timeout=10)
        data = resp.json()
        if data.get("errcode") == 0:
            return {"success": True, "message": "钉钉推送成功"}
        return {"success": False, "message": data.get("errmsg", "未知错误")}
    except Exception as e:
        return {"success": False, "message": str(e)}


def _push_feishu(webhook_url: str, title: str, content: str, at_mobiles: List[str]) -> Dict:
    try:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "purple"
                },
                "elements": [
                    {"tag": "markdown", "content": content}
                ]
            }
        }
        resp = requests.post(webhook_url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            return {"success": True, "message": "飞书推送成功"}
        return {"success": False, "message": data.get("msg", "未知错误")}
    except Exception as e:
        return {"success": False, "message": str(e)}


def _push_slack(webhook_url: str, content: str) -> Dict:
    try:
        payload = {"text": content}
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            return {"success": True, "message": "Slack推送成功"}
        return {"success": False, "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def _push_generic_webhook(webhook_url: str, title: str, content: str) -> Dict:
    try:
        payload = {
            "title": title,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            return {"success": True, "message": "Webhook推送成功"}
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:100]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ==================== 定时播报编排工具 ====================

@tool("broadcast_trigger")
def broadcast_trigger(
    namespace: str = "",
    time_range_minutes: int = 30,
    push_channel: str = "webhook",
    webhook_url: str = "",
    at_mobiles: Optional[List[str]] = None
) -> str:
    """
    手动触发一次完整的集群状态播报流程。
    等价于依次调用 broadcast_cluster_status + broadcast_push_report。

    Args:
        namespace: Kubernetes 命名空间
        time_range_minutes: 统计时间窗口（分钟）
        push_channel: 推送渠道
        webhook_url: Webhook 地址
        at_mobiles: 需要 @ 的手机号列表
    """
    report = broadcast_cluster_status.invoke({
        "namespace": namespace,
        "time_range_minutes": time_range_minutes,
        "include_anomalies": True,
        "format": "markdown"
    })

    if "查询失败" in report or "error" in report.lower():
        return f"❌ 播报失败\n报告生成出错: {report}"

    title = f"集群状态播报 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    push_result = broadcast_push_report.invoke({
        "content": report,
        "channel": push_channel,
        "title": title,
        "webhook_url": webhook_url,
        "at_mobiles": at_mobiles or []
    })

    return f"{report}\n\n---\n{push_result}"

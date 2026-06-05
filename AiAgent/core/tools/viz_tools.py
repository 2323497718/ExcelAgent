"""
Visualization tools for generating charts from monitoring data.
"""

import os
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.tools import tool


def format_bytes(bytes_value: float) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_cores(cpu_value: float) -> str:
    """Format CPU cores to human-readable string."""
    if cpu_value < 0.01:
        return f"{cpu_value * 1000:.2f} millicores"
    return f"{cpu_value:.3f} cores"


@tool("generate_chart")
def generate_chart(
    chart_type: str,
    data: Dict[str, List[Any]],
    title: str = "Chart",
    output_path: str = "./output/charts/chart.png",
    xlabel: str = "X",
    ylabel: str = "Y",
    labels: Optional[List[str]] = None
) -> str:
    """
    Generate a chart from data and save it as an image file.

    Args:
        chart_type: Type of chart ('line', 'bar', 'pie', 'area')
        data: Dictionary with 'x' and 'y' keys, where values are lists
        title: Chart title
        output_path: Path to save the chart image
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        labels: Optional labels for pie chart or bar chart categories
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return "Error: matplotlib is required for chart generation. Install with: pip install matplotlib"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    x_data = data.get("x", [])
    y_data = data.get("y", [])

    if not x_data or not y_data:
        return "Error: No data provided"

    plt.figure(figsize=(10, 6))

    if chart_type == "line":
        plt.plot(x_data, y_data, marker='o', linewidth=2, markersize=6)
    elif chart_type == "bar":
        x_pos = np.arange(len(labels)) if labels else np.arange(len(x_data))
        plt.bar(x_pos, y_data)
        if labels:
            plt.xticks(x_pos, labels, rotation=45, ha='right')
    elif chart_type == "pie":
        if labels:
            plt.pie(y_data, labels=labels, autopct='%1.1f%%', startangle=90)
        else:
            plt.pie(y_data, autopct='%1.1f%%', startangle=90)
    elif chart_type == "area":
        plt.fill_between(x_data, y_data, alpha=0.3)
        plt.plot(x_data, y_data, marker='o', linewidth=2)
    else:
        return f"Error: Unknown chart type '{chart_type}'. Use: line, bar, pie, area"

    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return f"Chart saved to {output_path}"


@tool("generate_bar_chart")
def generate_bar_chart(
    labels: List[str],
    values: List[float],
    title: str = "Bar Chart",
    output_path: str = "./output/charts/bar_chart.png",
    xlabel: str = "Category",
    ylabel: str = "Value",
    color: str = "steelblue"
) -> str:
    """
    Generate a bar chart for comparing values across categories.

    Args:
        labels: List of category labels
        values: List of values for each category
        title: Chart title
        output_path: Path to save the chart
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        color: Bar color (e.g., 'steelblue', 'coral', 'seagreen')
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return "Error: matplotlib is required. Install with: pip install matplotlib"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if len(labels) != len(values):
        return "Error: Number of labels must match number of values"

    fig, ax = plt.subplots(figsize=(10, 6))

    x_pos = np.arange(len(labels))
    bars = ax.bar(x_pos, values, color=color, alpha=0.8, edgecolor='black', linewidth=0.5)

    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=9)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return f"Bar chart saved to {output_path}"


@tool("generate_time_series_chart")
def generate_time_series_chart(
    timestamps: List[str],
    values: List[float],
    title: str = "Time Series",
    output_path: str = "./output/charts/timeseries.png",
    xlabel: str = "Time",
    ylabel: str = "Value",
    label: str = "Series 1",
    show_trend: bool = True
) -> str:
    """
    Generate a time series line chart.

    Args:
        timestamps: List of timestamp strings (ISO format or readable format)
        values: List of values corresponding to timestamps
        title: Chart title
        output_path: Path to save the chart
        xlabel: Label for x-axis (typically 'Time')
        ylabel: Label for y-axis (e.g., 'CPU %', 'Memory MiB')
        label: Legend label for the data series
        show_trend: Whether to show a trend line
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return "Error: matplotlib is required. Install with: pip install matplotlib"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if len(timestamps) != len(values):
        return "Error: Number of timestamps must match number of values"

    fig, ax = plt.subplots(figsize=(12, 6))

    x_positions = np.arange(len(timestamps))
    ax.plot(x_positions, values, marker='o', linewidth=2, markersize=4, label=label, color='#2E86AB')

    if show_trend and len(values) > 2:
        z = np.polyfit(x_positions, values, 1)
        p = np.poly1d(z)
        ax.plot(x_positions, p(x_positions), linestyle='--', color='red', alpha=0.7, label='Trend')

    step = max(1, len(timestamps) // 8)
    ax.set_xticks(x_positions[::step])
    ax.set_xticklabels(timestamps[::step], rotation=45, ha='right', fontsize=8)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return f"Time series chart saved to {output_path}"


@tool("generate_pie_chart")
def generate_pie_chart(
    labels: List[str],
    values: List[float],
    title: str = "Pie Chart",
    output_path: str = "./output/charts/pie_chart.png",
    colors: Optional[List[str]] = None
) -> str:
    """
    Generate a pie chart for showing proportions.

    Args:
        labels: List of category labels
        values: List of values for each category
        title: Chart title
        output_path: Path to save the chart
        colors: Optional list of colors for each segment
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return "Error: matplotlib is required. Install with: pip install matplotlib"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if len(labels) != len(values):
        return "Error: Number of labels must match number of values"

    fig, ax = plt.subplots(figsize=(10, 8))

    default_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']

    if colors is None:
        colors = default_colors[:len(labels)]
    elif len(colors) < len(labels):
        colors = colors + default_colors[:len(labels) - len(colors)]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*sum(values))})',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 10}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return f"Pie chart saved to {output_path}"


@tool("generate_memory_chart")
def generate_memory_chart(
    pod_data: Dict[str, float],
    title: str = "Pod Memory Usage",
    output_path: str = "./output/charts/memory_usage.png"
) -> str:
    """
    Generate a bar chart showing memory usage for pods.

    Args:
        pod_data: Dictionary mapping pod names to memory usage in bytes
        title: Chart title
        output_path: Path to save the chart
    """
    labels = list(pod_data.keys())
    values = [pod_data[p] for p in labels]

    formatted_labels = [f"{p[:20]}..." if len(p) > 20 else p for p in labels]
    formatted_values = [format_bytes(v) for v in values]

    return generate_bar_chart(
        labels=formatted_labels,
        values=values,
        title=title,
        output_path=output_path,
        xlabel="Pod",
        ylabel="Memory Usage",
        color="#3498DB"
    )


@tool("generate_cpu_chart")
def generate_cpu_chart(
    pod_data: Dict[str, float],
    title: str = "Pod CPU Usage",
    output_path: str = "./output/charts/cpu_usage.png"
) -> str:
    """
    Generate a bar chart showing CPU usage for pods.

    Args:
        pod_data: Dictionary mapping pod names to CPU usage in cores
        title: Chart title
        output_path: Path to save the chart
    """
    labels = list(pod_data.keys())
    values = [pod_data[p] for p in labels]

    formatted_labels = [f"{p[:20]}..." if len(p) > 20 else p for p in labels]

    return generate_bar_chart(
        labels=formatted_labels,
        values=values,
        title=title,
        output_path=output_path,
        xlabel="Pod",
        ylabel="CPU Cores",
        color="#E74C3C"
    )

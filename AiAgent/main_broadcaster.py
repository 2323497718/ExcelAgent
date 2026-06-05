"""
集群状态播报员 - Cluster Status Broadcaster

定时触发，自动查询 Prometheus 获取各服务健康状态，
以结构化报告格式推送给运维团队。

支持两种运行模式：
  1. 单次播报: python main_broadcaster.py --once
  2. 定时播报: python main_broadcaster.py --interval 60
     （每 60 分钟自动执行一次）
"""

import os
import sys
import time
import argparse
import logging

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from threading import Thread, Event

from core.helper.logger import get_logger
from core.helper.llm_util import init_llm
from core.tools.broadcast_tools import (
    broadcast_cluster_status,
    broadcast_prometheus_query,
    broadcast_pod_metrics,
    broadcast_push_report,
    broadcast_trigger,
)


class BroadcasterAgent:
    """
    集群状态播报员 Agent。

    工具设计思考：
    - 每个工具是原子能力，输入/输出均为 LLM 友好格式（Markdown/JSON）
    - 优先返回结构化数据，便于 LLM 解析后组合使用
    - 错误信息包含诊断建议，降低 LLM 推理成本
    """

    def __init__(
        self,
        logger: logging.Logger,
        push_channel: str = "webhook",
        webhook_url: str = "",
        at_mobiles: list = None,
        namespace: str = "",
        interval_minutes: int = 60,
    ):
        self.logger = logger
        self.push_channel = push_channel
        self.webhook_url = webhook_url
        self.at_mobiles = at_mobiles or []
        self.namespace = namespace
        self.interval_minutes = interval_minutes

        self.tools = [
            broadcast_cluster_status,
            broadcast_prometheus_query,
            broadcast_pod_metrics,
            broadcast_push_report,
            broadcast_trigger,
        ]

        self._stop_event = Event()

    def run_once(self) -> str:
        """执行一次完整播报流程"""
        self.logger.info("开始执行播报...")

        report = broadcast_cluster_status.invoke({
            "namespace": self.namespace,
            "time_range_minutes": 30,
            "include_anomalies": True,
            "format": "markdown"
        })

        self.logger.info(f"报告生成完成，长度: {len(report)} 字符")

        if self.push_channel == "webhook" and not self.webhook_url:
            push_result = f"[未配置推送渠道，报告已生成]\n{report}"
        else:
            push_result = broadcast_push_report.invoke({
                "content": report,
                "channel": self.push_channel,
                "title": f"集群状态播报 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "webhook_url": self.webhook_url,
                "at_mobiles": self.at_mobiles,
            })

        self.logger.info(f"播报完成")
        return push_result

    def start_scheduled(self):
        """启动定时播报循环"""
        interval_seconds = self.interval_minutes * 60
        self.logger.info(f"启动定时播报，间隔 {self.interval_minutes} 分钟")

        while not self._stop_event.wait(interval_seconds):
            result = self.run_once()
            print("\n" + "=" * 60)
            print("播报结果:")
            print("=" * 60)
            print(result)
            print()

    def stop(self):
        """停止定时播报"""
        self._stop_event.set()


def main():
    parser = argparse.ArgumentParser(description="集群状态播报员")
    parser.add_argument(
        "--once", action="store_true",
        help="执行一次播报后退出"
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="定时播报间隔（分钟），默认 60"
    )
    parser.add_argument(
        "--channel", type=str, default="webhook",
        choices=["dingtalk", "feishu", "webhook", "slack"],
        help="推送渠道"
    )
    parser.add_argument(
        "--webhook", type=str, default="",
        help="Webhook URL（webhook 渠道必填）"
    )
    parser.add_argument(
        "--namespace", type=str, default="",
        help="Kubernetes 命名空间（为空则查所有）"
    )
    parser.add_argument(
        "--at", type=str, default="",
        help="需要 @ 的手机号，逗号分隔"
    )
    parser.add_argument(
        "--time-range", type=int, default=30,
        help="统计时间窗口（分钟），默认 30"
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "output/logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = get_logger(save_dir=log_dir, task_name="broadcaster")

    at_mobiles = [m.strip() for m in args.at.split(",") if m.strip()]

    broadcaster = BroadcasterAgent(
        logger=logger,
        push_channel=args.channel,
        webhook_url=args.webhook,
        at_mobiles=at_mobiles,
        namespace=args.namespace,
        interval_minutes=args.interval,
    )

    print("=" * 60)
    print("  集群状态播报员 - Cluster Status Broadcaster")
    print("=" * 60)
    print(f"  推送渠道: {args.channel}")
    print(f"  命名空间: {args.namespace or '全部'}")
    print(f"  统计窗口: {args.time_range} 分钟")
    if args.once:
        print("  运行模式: 单次播报")
    else:
        print(f"  运行模式: 定时播报（每 {args.interval} 分钟）")
    print("=" * 60)
    print()

    if args.once:
        result = broadcaster.run_once()
        print("\n" + "=" * 60)
        print("播报结果:")
        print("=" * 60)
        print(result)
    else:
        print("启动定时播报中... 按 Ctrl+C 停止\n")
        thread = Thread(target=broadcaster.start_scheduled, daemon=True)
        thread.start()
        try:
            thread.join()
        except KeyboardInterrupt:
            print("\n接收到停止信号，正在停止...")
            broadcaster.stop()


if __name__ == "__main__":
    main()

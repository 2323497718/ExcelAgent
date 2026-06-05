"""
Main entry point for the Diagnostic Agent.
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.helper.logger import get_logger
from core.diagnostic_agent_builder import DiagnosticAgent
from core.helper.llm_util import init_llm


def main():
    """Main function to run the Diagnostic Agent."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "output/logs")
    os.makedirs(log_dir, exist_ok=True)
    logger = get_logger(save_dir=log_dir, task_name="diagnosticAgent")

    llm = init_llm(api_key="sk-5588ad0c13e44635bbdddac949f1e874")

    print("=" * 70)
    print("  故障诊断智能体 (Fault Diagnostic Agent)")
    print("  支持: Prometheus + Jaeger + Kubernetes + Chaos Mesh")
    print("=" * 70)
    print()

    agent = DiagnosticAgent(logger=logger, llm=llm, verbose=True)

    print("\n智能体已就绪！您可以描述问题，例如:")
    print("  - 'productpage 访问变慢了，帮我排查一下'")
    print("  - 'reviews 服务报错，看看什么原因'")
    print("  - '某个 Pod 一直重启，是什么问题'")
    print("  - '帮我检查一下有没有活跃的故障注入'")
    print("\n输入 'quit' 或 'exit' 退出。\n")

    while True:
        try:
            user_input = input("\n您的问题: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见!")
                break

            if not user_input:
                continue

            print("\n" + "-" * 70)
            print("正在诊断，请稍候...")
            print("-" * 70)
            agent.invoke(user_input)

        except KeyboardInterrupt:
            print("\n\n已中断。再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()

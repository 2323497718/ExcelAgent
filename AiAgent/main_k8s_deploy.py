"""
Main entry point for the K8s Deployment Agent.
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.helper.logger import get_logger
from core.k8s_deploy_agent_builder import DeployAgent
from core.helper.llm_util import init_llm


def main():
    """Main function to run the Deployment Agent."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "output/logs")
    os.makedirs(log_dir, exist_ok=True)
    logger = get_logger(save_dir=log_dir, task_name="k8sDeployAgent")

    llm = init_llm(api_key="sk-5588ad0c13e44635bbdddac949f1e874")

    print("=" * 70)
    print("  K8s 自动化部署流水线智能体")
    print("  自动生成 YAML → 应用到集群 → 验证部署")
    print("=" * 70)
    print()

    agent = DeployAgent(logger=logger, llm=llm, verbose=True)

    print("\n智能体已就绪！您可以描述部署需求，例如:")
    print("  - '帮我将 bookinfo/details 部署到 K8s，命名空间 bookinfo-agent'")
    print("  - '部署 myapp:v1.0 到 test 环境，3个副本，暴露 8080 端口'")
    print("  - '在 production 命名空间部署 nginx，使用 NodePort 暴露服务'")
    print("\n输入 'quit' 或 'exit' 退出。\n")

    while True:
        try:
            user_input = input("\n部署请求: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见!")
                break

            if not user_input:
                continue

            print("\n" + "-" * 70)
            print("正在处理部署请求...")
            print("-" * 70)
            agent.invoke(user_input)

        except KeyboardInterrupt:
            print("\n\n已中断。再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()

"""
Main entry point for the Monitoring Agent.
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.helper.logger import get_logger
from core.monitoring_agent_builder import MonitoringAgent
from core.helper.llm_util import init_llm


def main():
    """Main function to run the Monitoring Agent."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "output/logs")
    os.makedirs(log_dir, exist_ok=True)
    logger = get_logger(save_dir=log_dir, task_name="monitoringAgent")

    llm = init_llm(api_key="sk-5588ad0c13e44635bbdddac949f1e874")

    print("=" * 60)
    print("  Kubernetes Monitoring Agent")
    print("  Natural Language Prometheus Query Interface")
    print("=" * 60)
    print()

    agent = MonitoringAgent(logger=logger, llm=llm, verbose=True)

    print("\nAgent is ready! You can ask questions like:")
    print("  - 'Show me memory usage for all pods in default namespace'")
    print("  - 'What's the CPU usage for bookinfo services?'")
    print("  - 'List all pods and their restart counts'")
    print("  - 'Generate a chart showing CPU trends over the last 5 minutes'")
    print("\nType 'quit' or 'exit' to exit.\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\n" + "-" * 60)
            agent.invoke(user_input)
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()

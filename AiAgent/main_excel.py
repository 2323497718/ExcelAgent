"""
Main entry point for the Excel Agent.
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.helper.logger import get_logger
from core.excel_agent_builder import ExcelAgent
from core.helper.llm_util import init_llm


def main():
    """Main function to run the Excel Agent."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "output/logs")
    os.makedirs(log_dir, exist_ok=True)
    logger = get_logger(save_dir=log_dir, task_name="excelAgent")

    llm = init_llm(api_key="sk-5588ad0c13e44635bbdddac949f1e874")

    print("=" * 60)
    print("  Excel 表格智能体")
    print("  阅读表格内容 · 创建和填写表格")
    print("=" * 60)
    print()

    agent = ExcelAgent(logger=logger, llm=llm, verbose=True)

    print("\n智能体已就绪！您可以描述需求，例如:")
    print("  - '帮我看看这个 Excel 文件里有什么内容: C:/data/report.xlsx'")
    print("  - '创建一个员工信息表，包含姓名、部门、职位、电话'")
    print("  - '在 C:/data/students.xlsx 里添加一条新记录'")
    print("  - '把 D:/orders.xlsx 的第3行数据改成新的值'")
    print("  - '查看 C:/data/sales.xlsx 中 Sheet2 的详细数据'")
    print("\n输入 'quit' 或 'exit' 退出。\n")

    while True:
        try:
            user_input = input("\n您: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见!")
                break

            if not user_input:
                continue

            print("\n" + "-" * 60)
            agent.invoke(user_input)
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n已中断。再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()

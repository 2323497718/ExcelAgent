"""
Background QThread that runs the ExcelAgent.
Emits signals back to the main thread for each step of execution.
All agent/tool code runs here so the UI never freezes.
"""

import traceback
from PySide6.QtCore import QThread, Signal

from langchain_core.messages import HumanMessage, AIMessage

from core.helper.llm_util import init_llm
from core.excel_agent_builder import ExcelAgent
from core.tools.excel_tools import (
    excel_read_file,
    excel_read_sheet_data,
    excel_find_rows,
    excel_create_file,
    excel_write_cells,
    excel_write_row,
    excel_append_row,
    excel_add_sheet,
    excel_delete_rows,
)


# Map tool names (as reported by the LLM) to LangChain tool instances
TOOL_MAP = {
    "excel_read_file":       excel_read_file,
    "excel_read_sheet_data": excel_read_sheet_data,
    "excel_find_rows":       excel_find_rows,
    "excel_create_file":     excel_create_file,
    "excel_write_cells":     excel_write_cells,
    "excel_write_row":       excel_write_row,
    "excel_append_row":      excel_append_row,
    "excel_add_sheet":       excel_add_sheet,
    "excel_delete_rows":     excel_delete_rows,
}


def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool by name, return result string."""
    fn = TOOL_MAP.get(name)
    if fn is None:
        return f"[ERROR] Unknown tool: {name}"
    try:
        return fn.invoke(args)
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


class AgentWorker(QThread):
    """
    Background thread for running the Excel agent.

    Signals (all thread-safe, delivered to main/GUI thread)
    ---------------------------------------------------
    thinking_started()              : agent is starting
    thinking_finished()             : agent finished (no more tools)
    user_message_ready(str)        : echo the user's message
    assistant_message_ready(str)    : final LLM text response
    tool_result_ready(str, str)    : (tool_name, result)
    error_occurred(str)            : error message
    """

    thinking_started     = Signal()
    thinking_finished   = Signal()
    user_message_ready  = Signal(str)
    assistant_message_ready = Signal(str)
    tool_result_ready   = Signal(str, str)
    error_occurred      = Signal(str)

    def __init__(
        self,
        api_key: str,
        parent=None,
        max_iterations: int = 10,
    ):
        super().__init__(parent)
        self._api_key          = api_key
        self._max_iterations   = max_iterations
        self._user_prompt      = ""
        self._chat_history     = []     # list of (role, text) tuples
        self._current_file     = ""     # currently open Excel path
        self._abort            = False

    # ────────────────────────────────────────────────────────────
    #  Configuration — call before start()
    # ────────────────────────────────────────────────────────────

    def configure(
        self,
        user_prompt: str,
        chat_history: list,    # list of {"role": "user"|"assistant"|"tool", "content"|"result": str}
        current_file: str = "",
    ):
        self._user_prompt    = user_prompt
        self._chat_history   = chat_history
        self._current_file   = current_file
        self._abort          = False

    # ────────────────────────────────────────────────────────────
    #  QThread run
    # ────────────────────────────────────────────────────────────

    def run(self):
        try:
            self._run_agent()
        except Exception as e:
            self.error_occurred.emit(f"执行出错: {traceback.format_exc()}")

    def _run_agent(self):
        # Echo user message immediately
        self.user_message_ready.emit(self._user_prompt)
        self.thinking_started.emit()

        # Build langchain history
        lang_hist = []
        for m in self._chat_history:
            role  = m.get("role", "")
            text  = m.get("content") or m.get("result") or ""
            if role == "user":
                lang_hist.append(HumanMessage(content=text))
            elif role in ("assistant", "tool"):
                lang_hist.append(AIMessage(content=text))

        # File context
        file_context = ""
        if self._current_file:
            try:
                info = excel_read_file.invoke({"file_path": self._current_file})
                file_context = (
                    f"\n[当前打开的 Excel 文件: {self._current_file}]\n"
                    f"⚠️ 重要提醒：表格的markdown输出中「Excel行号」列标注的是真实的Excel行号（从1开始，row 1是表头）。\n"
                    f"对数据进行增删改之前，必须先用 excel_find_rows 工具按关键词查找到准确的Excel行号，再进行操作。\n"
                    f"示例：「删除A的数据」→「先用 excel_find_rows 找到A所在的那一行→得到Excel行号→再用 excel_delete_rows 删除」\n"
                    f"\n文件内容：\n{info}\n"
                )
            except Exception as e:
                file_context = f"\n[文件读取失败: {e}]\n"

        full_input = file_context + self._user_prompt

        # Init agent
        llm    = init_llm(api_key=self._api_key)
        agent  = ExcelAgent(llm=llm, verbose=False)

        # Agent loop
        for iteration in range(self._max_iterations):
            if self._abort:
                return

            resp = agent.agent.invoke({
                "input":        full_input,
                "chat_history": lang_hist,
            })

            resp_text   = getattr(resp, "content", str(resp))
            tool_calls  = getattr(resp, "tool_calls", None) or []

            if not tool_calls:
                # Done — no more tools to call
                self.assistant_message_ready.emit(resp_text)
                self.thinking_finished.emit()
                return

            # Execute each tool call
            for tc in tool_calls:
                if self._abort:
                    return
                tn = tc.get("name") or ""
                ta = tc.get("args", {}) or {}
                result = _execute_tool(tn, ta)

                # Emit tool result (will show in chat immediately)
                self.tool_result_ready.emit(tn, result)

                # Update history for next iteration
                lang_hist.append(resp)
                lang_hist.append(HumanMessage(content=f"Tool {tn} returned:\n{result}"))

            full_input = ""

        # Max iterations reached
        self.assistant_message_ready.emit(
            "已达到最大迭代次数（10步），请简化请求或分步操作。"
        )
        self.thinking_finished.emit()

"""
Diagnostic Agent builder module for fault diagnosis and troubleshooting.
"""

import logging
from typing import Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.helper.llm_util import init_llm

# Prometheus tools
from core.tools.prometheus_tools import (
    prom_query_instant,
    prom_query_range,
    prom_get_pod_memory,
    prom_get_pod_cpu,
    prom_get_pod_restarts,
    prom_get_namespace_pods,
)

# Jaeger tools
from core.tools.jaeger_tools import (
    jaeger_search_traces,
    jaeger_analyze_latency,
    jaeger_find_slow_dependencies,
    jaeger_get_call_chain,
    jaeger_list_services,
)

# K8s tools
from core.tools.k8s_tools import (
    k8s_get_pods,
    k8s_describe_pod,
    k8s_get_pod_logs,
    k8s_search_pod_logs,
    k8s_get_events,
    k8s_check_pod_status,
    k8s_list_namespaces,
)

# Chaos Mesh tools
from core.tools.chaos_tools import (
    chaos_check_active_chaos,
    chaos_get_network_chaos,
    chaos_get_stress_chaos,
    chaos_get_pod_chaos,
    chaos_diagnose_impact,
    chaos_list_experiments,
)

from core.prompts.diagnostic_agent_prompt import create_diagnostic_prompt


class AgentExecutor:
    """Simple agent executor for running the diagnostic agent."""

    def __init__(
        self,
        agent: Runnable,
        tools: list,
        max_iterations: int = 20,
        verbose: bool = True
    ):
        self.agent = agent
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.diagnostic_history = []

    def invoke(self, inputs: dict) -> dict:
        """Execute the agent with the given inputs."""
        query = inputs.get("input", "")
        history = inputs.get("chat_history", [])
        max_iters = self.max_iterations
        iteration = 0

        self.diagnostic_history = []

        while iteration < max_iters:
            iteration += 1

            if self.verbose:
                print(f"\n{'='*70}")
                print(f"[诊断迭代 {iteration}/{max_iters}]")
                print(f"{'='*70}")

            try:
                response = self.agent.invoke({
                    "input": query,
                    "chat_history": history
                })
            except Exception as e:
                if self.verbose:
                    print(f"Agent error: {e}")
                return {"output": f"Agent error: {str(e)}", "messages": history}

            response_text = response.content if hasattr(response, 'content') else str(response)

            if self.verbose:
                preview = response_text[:300] + "..." if len(response_text) > 300 else response_text
                print(f"\nAgent 分析: {preview}")

            tool_calls = getattr(response, 'tool_calls', None) or []
            if not tool_calls:
                if self.verbose:
                    print("\n[诊断完成]")
                return {"output": response_text, "messages": history, "evidence": self.diagnostic_history}

            for tool_call in tool_calls:
                tool_name = tool_call.get("name") or ""
                tool_args = tool_call.get("args") or {}

                if not tool_name:
                    continue

                if self.verbose:
                    print(f"\n>>> 调用工具: {tool_name}")
                    args_str = str(tool_args)[:150]
                    print(f"    参数: {args_str}...")

                if tool_name not in self.tools:
                    tool_result = f"Error: Unknown tool '{tool_name}'"
                else:
                    try:
                        tool_result = self.tools[tool_name].invoke(tool_args)
                        self.diagnostic_history.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": tool_result[:500] if len(str(tool_result)) > 500 else tool_result
                        })
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"

                if self.verbose:
                    result_preview = str(tool_result)[:400]
                    print(f"    结果: {result_preview}...")

                history.append(response)
                history.append(HumanMessage(content=f"Tool {tool_name} returned:\n{tool_result}"))
                query = ""

        return {"output": "Maximum iterations reached. Diagnosis incomplete.", "messages": history, "evidence": self.diagnostic_history}


class DiagnosticAgent:
    """
    Diagnostic Agent for fault diagnosis in Kubernetes/Service Mesh environments.
    Combines Prometheus, Jaeger, Kubernetes, and Chaos Mesh tools.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        llm: Optional[BaseChatModel] = None,
        max_iterations: int = 20,
        verbose: bool = True
    ):
        """
        Initialize the Diagnostic Agent.
        """
        self.logger = logger or logging.getLogger("DiagnosticAgent")
        self.llm = llm or init_llm()
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.tools: List = [
            # Prometheus
            prom_query_instant,
            prom_query_range,
            prom_get_pod_memory,
            prom_get_pod_cpu,
            prom_get_pod_restarts,
            prom_get_namespace_pods,
            # Jaeger
            jaeger_search_traces,
            jaeger_analyze_latency,
            jaeger_find_slow_dependencies,
            jaeger_get_call_chain,
            jaeger_list_services,
            # Kubernetes
            k8s_get_pods,
            k8s_describe_pod,
            k8s_get_pod_logs,
            k8s_search_pod_logs,
            k8s_get_events,
            k8s_check_pod_status,
            k8s_list_namespaces,
            # Chaos Mesh
            chaos_check_active_chaos,
            chaos_get_network_chaos,
            chaos_get_stress_chaos,
            chaos_get_pod_chaos,
            chaos_diagnose_impact,
            chaos_list_experiments,
        ]

        self.prompt = create_diagnostic_prompt(self.tools)
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=max_iterations,
            verbose=verbose
        )

        self.logger.info("DiagnosticAgent initialized successfully")

    def _create_agent(self) -> Runnable:
        """Create the agent using OpenAI Functions pattern."""

        def agent_node(inputs: dict):
            messages = inputs.get("chat_history", [])
            if not isinstance(messages, list):
                messages = []

            full_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    if msg.get("type") == "human":
                        full_messages.append(HumanMessage(content=msg.get("content", "")))
                    else:
                        full_messages.append(AIMessage(content=msg.get("content", "")))
                elif isinstance(msg, str):
                    full_messages.append(HumanMessage(content=msg))
                else:
                    full_messages.append(msg)

            system_prompt = self.prompt.messages[0].prompt.template
            tool_info = "\n".join([
                f"- {t.name}: {t.description}"
                for t in self.tools
            ])
            system_msg = SystemMessage(content=system_prompt.format(
                tool_names=", ".join([t.name for t in self.tools]),
                tools=tool_info
            ))

            full_messages.insert(0, system_msg)
            full_messages.append(HumanMessage(content=inputs.get("input", "")))

            response = self.llm.bind_tools(self.tools).invoke(full_messages)
            return response

        from langchain_core.runnables import RunnableLambda
        return RunnableLambda(agent_node)

    def invoke(self, query: str) -> dict:
        """
        Invoke the agent with a diagnostic query.

        Args:
            query: Natural language description of the problem

        Returns:
            dict: Agent response with diagnosis
        """
        self.logger.info(f"DiagnosticAgent invoked: {query}")

        try:
            response = self.agent_executor.invoke({
                "input": query,
                "chat_history": []
            })

            self.logger.info("Agent execution completed")

            print(f"\n{'='*70}")
            print("最终诊断报告:")
            print(f"{'='*70}")
            print(response['output'])
            print(f"{'='*70}")

            return response
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {"output": error_msg, "error": str(e)}

    def __repr__(self) -> str:
        return f"DiagnosticAgent(tools={len(self.tools)}, max_iterations={self.max_iterations})"

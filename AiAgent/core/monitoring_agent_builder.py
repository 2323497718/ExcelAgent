"""
Monitoring Agent builder module.
"""

import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.helper.llm_util import init_llm
from core.tools.prometheus_tools import (
    prom_query_instant,
    prom_query_range,
    prom_get_pod_memory,
    prom_get_pod_cpu,
    prom_get_namespace_pods,
    prom_get_pod_restarts,
    prom_get_node_status,
    prom_get_node_resources,
    prom_get_persistent_volumes,
    prom_get_deployment_replicas,
    prom_get_service_endpoints,
    prom_list_namespaces,
    prom_get_workload_metrics,
)
from core.tools.viz_tools import (
    generate_chart,
    generate_bar_chart,
    generate_time_series_chart,
    generate_pie_chart,
    generate_memory_chart,
    generate_cpu_chart,
)
from core.tools.analysis_tools import (
    analyze_resource_usage,
    compare_services,
    detect_anomalies,
    generate_summary_report,
    format_metrics_table,
    calculate_trend,
)
from core.prompts.monitoring_agent_prompt import create_monitoring_prompt


class AgentExecutor:
    """Simple agent executor for running the monitoring agent."""

    def __init__(
        self,
        agent: Runnable,
        tools: list,
        max_iterations: int = 15,
        verbose: bool = True
    ):
        self.agent = agent
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations
        self.verbose = verbose

    def invoke(self, inputs: dict) -> dict:
        """Execute the agent with the given inputs."""
        query = inputs.get("input", "")
        history = inputs.get("chat_history", [])
        max_iters = self.max_iterations
        iteration = 0

        while iteration < max_iters:
            iteration += 1

            if self.verbose:
                print(f"\n{'='*60}")
                print(f"[Iteration {iteration}/{max_iters}]")
                print(f"{'='*60}")

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
                print(f"\nAgent: {response_text[:500]}..." if len(response_text) > 500 else f"\nAgent: {response_text}")

            tool_calls = getattr(response, 'tool_calls', None) or []
            if not tool_calls:
                if self.verbose:
                    print("\n[Task completed - no more actions needed]")
                return {"output": response_text, "messages": history}

            for tool_call in tool_calls:
                tool_name = tool_call.get("name") or ""
                tool_args = tool_call.get("args") or {}

                if not tool_name:
                    continue

                if self.verbose:
                    print(f"\n>>> Calling: {tool_name}")
                    print(f"    Args: {str(tool_args)[:200]}...")

                if tool_name not in self.tools:
                    tool_result = f"Error: Unknown tool '{tool_name}'"
                else:
                    try:
                        tool_result = self.tools[tool_name].invoke(tool_args)
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"

                if self.verbose:
                    result_preview = str(tool_result)[:300]
                    print(f"    Result: {result_preview}...")

                history.append(response)
                history.append(HumanMessage(content=f"Tool {tool_name} returned:\n{tool_result}"))
                query = ""  # Continue conversation

        return {"output": "Max iterations reached. Task incomplete.", "messages": history}


class MonitoringAgent:
    """
    Monitoring Agent for Kubernetes/Prometheus natural language queries.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        llm: Optional[BaseChatModel] = None,
        max_iterations: int = 15,
        verbose: bool = True
    ):
        """
        Initialize the Monitoring Agent.
        """
        self.logger = logger or logging.getLogger("MonitoringAgent")
        self.llm = llm or init_llm()
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.tools = [
            prom_query_instant,
            prom_query_range,
            prom_get_pod_memory,
            prom_get_pod_cpu,
            prom_get_namespace_pods,
            prom_get_pod_restarts,
            prom_get_node_status,
            prom_get_node_resources,
            prom_get_persistent_volumes,
            prom_get_deployment_replicas,
            prom_get_service_endpoints,
            prom_list_namespaces,
            prom_get_workload_metrics,
            generate_chart,
            generate_bar_chart,
            generate_time_series_chart,
            generate_pie_chart,
            generate_memory_chart,
            generate_cpu_chart,
            analyze_resource_usage,
            compare_services,
            detect_anomalies,
            generate_summary_report,
            format_metrics_table,
            calculate_trend,
        ]

        self.prompt = create_monitoring_prompt(self.tools)
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=max_iterations,
            verbose=verbose
        )

        self.logger.info("MonitoringAgent initialized successfully")

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
        Invoke the agent with a user query.

        Args:
            query: Natural language query about cluster metrics

        Returns:
            dict: Agent response
        """
        self.logger.info(f"MonitoringAgent invoked: {query}")

        try:
            response = self.agent_executor.invoke({
                "input": query,
                "chat_history": []
            })
            self.logger.info("Agent execution completed")
            print(f"\n{'='*60}")
            print(f"FINAL ANSWER:\n{response['output']}")
            print(f"{'='*60}")
            return response
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {"output": error_msg, "error": str(e)}

    def __repr__(self) -> str:
        return f"MonitoringAgent(tools={len(self.tools)})"

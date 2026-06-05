"""
K8s Deployment Agent builder module for automated Kubernetes deployments.
"""

import logging
from typing import Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.helper.llm_util import init_llm

# YAML Generation tools
from core.tools.k8s_yaml_tools import (
    generate_k8s_deployment_yaml,
    generate_deployment_only,
    generate_service_only,
    generate_ingress,
    generate_configmap,
    generate_secret,
    generate_horizontal_pod_autoscaler,
    generate_persistent_volume_claim,
)

# Deployment tools
from core.tools.k8s_deploy_tools import (
    k8s_create_namespace,
    k8s_apply_yaml,
    k8s_apply_from_file,
    k8s_delete_resource,
    k8s_wait_for_pod,
    k8s_get_pod_status,
    k8s_get_deployment_status,
    k8s_get_service_status,
    k8s_check_service_endpoint,
    k8s_scale_deployment,
    k8s_save_yaml,
    k8s_full_deploy,
    k8s_get_resources,
    k8s_describe_resource,
    k8s_lookup_pod_image,
)

from core.prompts.deploy_agent_prompt import create_deploy_prompt


class AgentExecutor:
    """Agent executor for running the deployment agent."""

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
        self.deploy_history = []

    def invoke(self, inputs: dict) -> dict:
        """Execute the agent with the given inputs."""
        query = inputs.get("input", "")
        history = inputs.get("chat_history", [])
        max_iters = self.max_iterations
        iteration = 0

        self.deploy_history = []

        while iteration < max_iters:
            iteration += 1

            if self.verbose:
                print(f"\n{'='*70}")
                print(f"[部署迭代 {iteration}/{max_iters}]")
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
                print(f"\nAgent: {preview}")

            tool_calls = getattr(response, 'tool_calls', None) or []
            if not tool_calls:
                if self.verbose:
                    print("\n[部署完成]")
                return {"output": response_text, "messages": history, "steps": self.deploy_history}

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
                        self.deploy_history.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": str(tool_result)[:500]
                        })
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"

                if self.verbose:
                    result_preview = str(tool_result)[:400]
                    print(f"    结果: {result_preview}...")

                history.append(response)
                history.append(HumanMessage(content=f"Tool {tool_name} returned:\n{tool_result}"))
                query = ""

        return {"output": "Maximum iterations reached. Deployment incomplete.", "messages": history, "steps": self.deploy_history}


class DeployAgent:
    """
    K8s Deployment Agent for automated Kubernetes deployments.
    Covers: Dockerfile → Image → K8s YAML → Cluster deployment
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        llm: Optional[BaseChatModel] = None,
        max_iterations: int = 15,
        verbose: bool = True
    ):
        """
        Initialize the Deployment Agent.
        """
        self.logger = logger or logging.getLogger("DeployAgent")
        self.llm = llm or init_llm()
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.tools: List = [
            # YAML Generation
            generate_k8s_deployment_yaml,
            generate_deployment_only,
            generate_service_only,
            generate_ingress,
            generate_configmap,
            generate_secret,
            generate_horizontal_pod_autoscaler,
            generate_persistent_volume_claim,
            # Deployment
            k8s_create_namespace,
            k8s_apply_yaml,
            k8s_apply_from_file,
            k8s_delete_resource,
            k8s_wait_for_pod,
            k8s_get_pod_status,
            k8s_get_deployment_status,
            k8s_get_service_status,
            k8s_check_service_endpoint,
            k8s_scale_deployment,
            k8s_save_yaml,
            k8s_full_deploy,
            k8s_get_resources,
            k8s_describe_resource,
            k8s_lookup_pod_image,
        ]

        self.prompt = create_deploy_prompt(self.tools)
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=max_iterations,
            verbose=verbose
        )

        self.logger.info("DeployAgent initialized successfully")

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
        Invoke the agent with a deployment request.

        Args:
            query: Natural language deployment request

        Returns:
            dict: Deployment result
        """
        self.logger.info(f"DeployAgent invoked: {query}")

        try:
            response = self.agent_executor.invoke({
                "input": query,
                "chat_history": []
            })

            self.logger.info("Agent execution completed")

            print(f"\n{'='*70}")
            print("部署完成报告:")
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
        return f"DeployAgent(tools={len(self.tools)})"

"""
OpsAgent builder module for creating the DevOps agent.
"""

import logging
from typing import Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, AIMessageChunk
from langchain_core.tools import BaseTool

from core.helper.llm_util import init_llm
from core.tools.file_tools import file_read_tool, file_write_tool
from core.tools.dockerfile_tools import dockerfile_generate_tool
from core.tools.docker_tools import image_build_tool, container_run_tool
from core.tools.container_tools import container_exec_cmd_tool
from core.tools.failure_tools import failure_diagnosis_tool
from core.prompts.ops_agent_prompt import create_prompt


class AgentExecutor:
    """Simple agent executor for running the agent."""

    def __init__(
        self,
        agent: Runnable,
        tools: List[BaseTool],
        max_iterations: int = 30,
        verbose: bool = True
    ):
        self.agent = agent
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.verbose = verbose

    def invoke(self, inputs: dict) -> dict:
        """Execute the agent with the given inputs."""
        query = inputs.get("input", "")
        max_iters = self.max_iterations
        iteration = 0
        history = []

        while iteration < max_iters:
            iteration += 1

            if self.verbose:
                print(f"\n{'='*50}")
                print(f"Iteration {iteration}/{max_iters}")
                print(f"{'='*50}")

            response = self.agent.invoke({
                "input": query,
                "chat_history": history
            })

            if isinstance(response, AIMessage):
                response_text = response.content
            elif hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            if self.verbose:
                print(f"Agent: {response_text}")

            if not hasattr(response, 'tool_calls') or not response.tool_calls:
                if self.verbose:
                    print("\n[Agent finished - no more actions needed]")
                return {"output": response_text, "messages": history}

            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name", "")
                tool_args = tool_call.get("args") or tool_call.get("arguments", {})

                if self.verbose:
                    print(f"\n[Calling tool: {tool_name}]")
                    print(f"Arguments: {tool_args}")

                if tool_name not in self.tools:
                    tool_result = f"Error: Tool '{tool_name}' not found"
                else:
                    try:
                        tool_result = self.tools[tool_name].invoke(tool_args)
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"

                if self.verbose:
                    print(f"Result: {tool_result[:200]}..." if len(str(tool_result)) > 200 else f"Result: {tool_result}")

                history.append(AIMessage(content=response_text))
                history.append(HumanMessage(content=f"Tool result: {tool_result}"))

        return {"output": "Max iterations reached", "messages": history}


class OpsAgent:
    """
    DevOps Agent that uses LangChain to automate Docker-related tasks.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        llm: Optional[BaseChatModel] = None,
        max_iterations: int = 30,
        verbose: bool = True
    ):
        """
        Initialize the OpsAgent.
        """
        self.logger = logger or logging.getLogger("OpsAgent")
        self.llm = llm or init_llm()
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.tools = [
            dockerfile_generate_tool,
            file_read_tool,
            file_write_tool,
            image_build_tool,
            container_run_tool,
            container_exec_cmd_tool,
            failure_diagnosis_tool,
        ]

        self.prompt = create_prompt(self.tools)

        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=max_iterations,
            verbose=verbose
        )

        self.logger.info("OpsAgent initialized successfully")

    def _create_agent(self) -> Runnable:
        """Create the agent using OpenAI Functions pattern."""

        def agent_node(inputs: dict):
            """Agent node function that processes inputs and returns response."""
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
                else:
                    full_messages.append(msg)

            system_prompt = self.prompt.messages[0].prompt.template
            tool_info = "\n".join([f"- {t.name}: {t.description}" for t in self.tools])
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
        """
        self.logger.info(f"Agent invoked with query: {query}")

        try:
            response = self.agent_executor.invoke({"input": query})
            self.logger.info("Agent execution completed successfully")
            print(f"\n{'='*50}")
            print(f"Final Answer: {response['output']}")
            print(f"{'='*50}")
            return response
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {"output": error_msg, "error": str(e)}

    def __repr__(self) -> str:
        return f"OpsAgent(tools={len(self.tools)}, max_iterations={self.max_iterations})"

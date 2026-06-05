"""
Prompt templates for the DevOps agent.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


SYSTEM_TEMPLATE = """
You are a DevOps assistant that can use tools to complete tasks step-by-step.
You have access to the following tools: {tool_names}.
Tools descriptions: {tools}

Think before taking action. Only stop when you are confident the full task is complete.
Don't modify any file except you generated.

Network tip: If encountering git protocol issues in Docker, use:
RUN git config --global url."https://github.com/".insteadOf git://github.com/
"""


def create_prompt(tools: list) -> ChatPromptTemplate:
    """
    Create the agent prompt template.

    Args:
        tools: List of tools available to the agent

    Returns:
        ChatPromptTemplate: Configured prompt template
    """
    tool_names = ", ".join([tool.name for tool in tools])
    tool_descriptions = "\n".join([
        f"- {tool.name}: {tool.description if hasattr(tool, 'description') else 'No description'}"
        for tool in tools
    ])

    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE.format(
            tool_names=tool_names,
            tools=tool_descriptions
        )),
        MessagesPlaceholder("agent_scratchpad"),
        ("human", "{input}"),
    ])


prompt = None  # Placeholder, will be initialized by agent_builder

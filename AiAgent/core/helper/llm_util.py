"""
LLM utility module for initializing the language model.
"""

import os
from langchain_openai import ChatOpenAI


def init_llm(
    model: str = "qwen-plus",
    api_key: str = "sk-e612fd6be4284f62b76959b13bf35483",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature: float = 0,
    max_retries: int = 2
) -> ChatOpenAI:
    """
    Initialize and return a ChatOpenAI language model instance.

    Args:
        model: The model name to use (default: qwen-plus)
        api_key: API key for the LLM service. If None, reads from environment variable OPENAI_API_KEY.
        base_url: Base URL for the API endpoint. If None, reads from environment variable OPENAI_API_BASE_URL.
        temperature: Temperature for generation (default: 0 for more deterministic outputs)
        max_retries: Maximum number of retries on API failure (default: 2)

    Returns:
        ChatOpenAI: An initialized language model instance
    """
    if api_key is None or api_key == "sk-e612fd6be4284f62b76959b13bf35483":
        api_key = os.getenv("OPENAI_API_KEY", "sk-e612fd6be4284f62b76959b13bf35483")
    if base_url is None:
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not api_key:
        raise ValueError(
            "API key is required. Either pass api_key parameter or set OPENAI_API_KEY environment variable."
        )

    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_retries=max_retries,
    )
    return llm

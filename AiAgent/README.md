# DevOps Agent

A LangChain-based DevOps agent that automates Docker-related tasks using AI.

## Features

- Automated Dockerfile generation from project requirements
- Docker image building and container management
- Command execution inside running containers
- Intelligent error diagnosis and troubleshooting
- Structured logging and audit trails

## Project Structure

```
AiAgent/
├── main.py                 # Application entry point
├── core/
│   ├── agent_builder.py    # OpsAgent implementation
│   ├── helper/
│   │   ├── llm_util.py     # LLM initialization
│   │   └── logger.py       # Logging utilities
│   ├── prompts/
│   │   └── ops_agent_prompt.py  # Agent prompt templates
│   └── tools/
│       ├── file_tools.py         # File read/write operations
│       ├── dockerfile_tools.py   # Dockerfile generation
│       ├── docker_tools.py       # Image build & container run
│       ├── container_tools.py    # Container command execution
│       └── failure_tools.py     # Error diagnosis
├── output/logs/            # Log files directory
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.11+
- Docker
- OpenAI API key (or compatible API endpoint)

### Setup with uv

```bash
# Initialize project
uv init --python 3.11

# Install dependencies
uv add langchain langchain_community langchain_core langchain-openai docker

# Or install from requirements.txt
uv add -r requirements.txt
```

### Setup with pip

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Set your API credentials before running the agent:

**Linux/macOS:**
```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE_URL="your-base-url"  # Optional, for proxies
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_API_BASE_URL="your-base-url"  # Optional, for proxies
```

## Usage

### Basic Usage

```python
from core.helper.logger import get_logger
from core.agent_builder import OpsAgent

# Initialize logger
logger = get_logger(save_dir="./output/logs", task_name="devops")

# Create agent
agent = OpsAgent(logger=logger)

# Execute tasks
response = agent.invoke("""
    1. Read the requirements in myapp/README.md and generate a Dockerfile
    2. Build the Docker image named myapp
    3. Run a container exposing port 8080
""")
```

### Custom LLM Configuration

```python
from core.helper.llm_util import init_llm
from core.agent_builder import OpsAgent

# Use custom model settings
llm = init_llm(
    model="gpt-4",
    temperature=0.5,
    max_retries=3
)

agent = OpsAgent(llm=llm, max_iterations=50)
```

## Available Tools

| Tool | Description |
|------|-------------|
| `file_read_tool` | Read contents from a file |
| `file_write_tool` | Write content to a file |
| `dockerfile_generate_tool` | Generate Dockerfile from README |
| `image_build_tool` | Build Docker image from Dockerfile |
| `container_run_tool` | Start a Docker container |
| `container_exec_cmd_tool` | Execute commands in container |
| `failure_diagnosis_tool` | Analyze errors and suggest fixes |

## Running the Agent

```bash
# With Python
python main.py

# With uv
uv run main.py
```

## Logging

Logs are saved to `./output/logs/` with timestamps. Each run creates a new log file:

```
output/logs/gitAgent_20260101_120000.log
```

## Troubleshooting

### Network Issues in Docker

If you encounter git protocol issues, the agent will automatically add:

```dockerfile
RUN git config --global url."https://github.com/".insteadOf git://github.com/
```

### Common Issues

- **API Key Error**: Ensure `OPENAI_API_KEY` is set in your environment
- **Docker Not Running**: Start Docker Desktop or the Docker daemon
- **Port Conflicts**: Change the expose port if 8080 is in use

## License

MIT License

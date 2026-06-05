"""
Coze (扣子) 平台工具配置示例

Coze 支持通过插件/Bot 方式接入外部 API。
"""

# ==================== Coze Bot 配置 ====================

COZE_BOT_CONFIG = """
Coze Bot 配置指南:

1. 访问 https://www.coze.cn 或 https://www.coze.com
2. 创建新 Bot
3. 配置插件/API
4. 设置提示词
"""

# ==================== Coze API 工具定义 ====================

COZE_TOOLS = [
    {
        "name": "get_book_rating",
        "description": "获取指定书籍的用户评分和评价数量",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "书籍ID，对应关系：1=《Kubernetes实战》，2=《Docker容器化指南》，3=《Prometheus监控实战》"
                }
            },
            "required": ["book_id"]
        }
    },
    {
        "name": "get_book_detail",
        "description": "获取书籍详细信息，包括作者、出版社、价格和评分",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "书籍ID"
                }
            },
            "required": ["book_id"]
        }
    },
    {
        "name": "list_books",
        "description": "获取系统中所有书籍的列表",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_cluster_health",
        "description": "获取Kubernetes集群的整体健康状态，包括Pod数量、CPU/内存使用率、各服务状态",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_pod_resources",
        "description": "获取指定命名空间下所有Pod的资源使用情况（CPU和内存）",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "命名空间名称，默认为default",
                    "default": "default"
                }
            }
        }
    }
]


# ==================== Coze 工作流 JSON ====================

COZE_WORKFLOW = {
    "name": "智能运维助手",
    "description": "回答用户关于书籍评分和集群健康状态的问题",
    "steps": [
        {
            "id": "start",
            "type": "start",
            "output": {
                "user_message": "用户输入的问题"
            }
        },
        {
            "id": "llm_node",
            "type": "llm",
            "input": {
                "user_message": "$start.user_message"
            },
            "model": "gpt-4o-mini",
            "prompt": """你是一个智能运维助手，可以帮助用户查询：

1. 书籍信息查询
   - 可用书籍：《Kubernetes实战》、《Docker容器化指南》、《Prometheus监控实战》
   - 可以查询评分、详情、评论

2. 集群状态播报
   - 集群整体健康状态
   - Pod资源使用情况
   - 服务运行状态

3. 智能问答
   - 回答运维相关问题
   - 提供问题解决方案

用户问题：{{user_message}}

请根据问题内容，选择合适的工具或直接回答。"""
        },
        {
            "id": "tool_call",
            "type": "tool",
            "input": {
                "query": "$llm_node.query"
            },
            "tools": [
                "get_book_rating",
                "get_book_detail",
                "list_books",
                "get_cluster_health",
                "get_pod_resources"
            ]
        },
        {
            "id": "response",
            "type": "end",
            "input": {
                "answer": "$llm_node.answer"
            }
        }
    ]
}


# ==================== Coze 插件配置 ====================

COZE_PLUGIN_CONFIG = {
    "api_type": "http",
    "name": "Bookinfo API",
    "description": "书籍信息和集群监控查询接口",
    "icon": "https://example.com/icon.png",
    "base_url": "http://your-server:8000",
    "auth": {
        "type": "api_key",
        "header_name": "X-API-Key"
    },
    "endpoints": [
        {
            "path": "/api/books",
            "method": "GET",
            "name": "获取书籍列表",
            "description": "获取所有可用书籍的基本信息",
            "parameters": []
        },
        {
            "path": "/api/books/{book_id}",
            "method": "GET",
            "name": "获取书籍详情",
            "description": "根据书籍ID获取详细信息",
            "parameters": [
                {
                    "name": "book_id",
                    "in": "path",
                    "required": True,
                    "description": "书籍ID"
                }
            ]
        },
        {
            "path": "/api/ratings/{book_id}",
            "method": "GET",
            "name": "获取书籍评分",
            "description": "获取指定书籍的用户评分",
            "parameters": [
                {
                    "name": "book_id",
                    "in": "path",
                    "required": True,
                    "description": "书籍ID"
                }
            ]
        },
        {
            "path": "/api/metrics/summary",
            "method": "GET",
            "name": "获取集群健康状态",
            "description": "获取Kubernetes集群的整体健康状态",
            "parameters": []
        },
        {
            "path": "/api/metrics/pod/{namespace}",
            "method": "GET",
            "name": "获取Pod资源使用",
            "description": "获取Pod的CPU和内存使用情况",
            "parameters": [
                {
                    "name": "namespace",
                    "in": "path",
                    "required": True,
                    "description": "命名空间名称"
                }
            ]
        }
    ]
}


# ==================== Coze 设置指南 ====================

COZE_SETUP_INSTRUCTIONS = """
## Coze (扣子) 平台集成步骤

### 方式一：通过插件接入

1. **创建插件**
   - 登录 Coze 控制台
   - 进入「插件」→「创建插件」
   - 选择「自定义 API」
   - 填入 API 信息

2. **配置 API**
   - Base URL: http://your-server:8000
   - 认证方式: API Key (可选)
   - 添加端点

3. **创建 Bot**
   - 进入「Bot」→「创建 Bot」
   - 添加刚才创建的插件
   - 编写提示词

### 方式二：通过工作流

1. **创建工作流**
   - 进入「工作流」→「创建工作流」
   - 添加 LLM 节点
   - 添加 HTTP 请求节点
   - 配置节点连接

2. **工作流节点配置**

   LLM 节点提示词:
   ```
   你是一个智能助手，可以帮用户：
   1. 查询书籍信息和评分
   2. 播报集群健康状态
   3. 回答运维问题

   可用工具通过上下文变量传入。
   ```

   HTTP 节点:
   - URL: {{base_url}}/api/books
   - Method: GET

3. **发布 Bot**
   - 测试工作流
   - 发布到 Bot
   - 可选发布到 Coze 应用市场

### 示例提示词

```
你是一个书店智能客服 + 集群运维助手。

你具有以下能力：

1. 书籍查询
   - 可以回答关于书籍评分、作者、价格的问题
   - 可以推荐书籍
   - 可以回答关于书籍评论的问题

2. 集群运维
   - 可以播报当前集群的健康状态
   - 可以查询各服务的资源使用情况
   - 可以回答运维相关问题

请用专业、友好的语气回答用户的问题。
```

### 常见问题

Q: Coze 无法访问内部 API?
A: 需要将 API 服务暴露到公网，或使用内网穿透工具（如 ngrok）

Q: 如何处理认证?
A: 在插件配置中添加 API Key，或在请求头中传递认证信息
"""


if __name__ == "__main__":
    import json
    print("=" * 60)
    print("Coze 平台配置")
    print("=" * 60)
    print("\n工具定义:")
    print(json.dumps(COZE_TOOLS, indent=2, ensure_ascii=False))
    print("\n" + "=" * 60)
    print("插件配置:")
    print(json.dumps(COZE_PLUGIN_CONFIG, indent=2, ensure_ascii=False))

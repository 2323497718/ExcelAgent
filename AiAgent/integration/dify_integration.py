"""
Dify 平台工具配置示例

复制以下 JSON 配置到 Dify 的「工具」->「自定义工具」中。
"""

# ==================== Dify 工具配置 ====================

DIFY_TOOLS_CONFIG = {
    # 工具 1: 获取书籍评分
    "get_book_rating": {
        "name": "get_book_rating",
        "description": "获取指定书籍的用户评分和评价数量",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "书籍 ID，如 '1' 对应《Kubernetes 实战》",
                    "enum": ["1", "2", "3"]
                }
            },
            "required": ["book_id"]
        }
    },

    # 工具 2: 获取书籍详情
    "get_book_detail": {
        "name": "get_book_detail",
        "description": "获取书籍的详细信息，包括评分、作者、出版信息",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "书籍 ID"
                }
            },
            "required": ["book_id"]
        }
    },

    # 工具 3: 获取书籍列表
    "get_books": {
        "name": "get_books",
        "description": "获取所有可用书籍的基本信息列表",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    # 工具 4: 获取集群健康摘要
    "get_cluster_summary": {
        "name": "get_cluster_summary",
        "description": "获取 Kubernetes 集群的整体健康状态摘要，包括 Pod 数量、CPU/内存使用率、各服务健康状态",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    # 工具 5: 获取 Pod 指标
    "get_pod_metrics": {
        "name": "get_pod_metrics",
        "description": "获取指定命名空间下所有 Pod 的 CPU 和内存使用情况",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes 命名空间名称",
                    "default": "default"
                },
                "metric_type": {
                    "type": "string",
                    "description": "指标类型：cpu (仅CPU)、memory (仅内存)、all (全部)",
                    "enum": ["cpu", "memory", "all"],
                    "default": "all"
                }
            }
        }
    },

    # 工具 6: 智能问答
    "chat": {
        "name": "chat",
        "description": "发送自然语言问答请求，AI 将结合知识库和工具回答问题",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "用户的问题"
                }
            },
            "required": ["message"]
        }
    }
}


# ==================== Dify 工作流配置 ====================

DIFY_WORKFLOW_EXAMPLE = """
Dify 工作流配置示例 (YAML 格式):

name: "智能运维助手"
description: "回答用户关于书籍评分和集群健康状态的问答"

nodes:
  - id: start
    type: start
    params:
      inputs:
        - name: user_query
          type: text

  - id: llm
    type: llm
    params:
      model: gpt-4o-mini
      prompt: |
        你是一个智能运维助手，可以回答用户关于书籍评分和集群状态的问题。

        可用工具：
        - get_books: 获取书籍列表
        - get_book_rating: 获取书籍评分
        - get_cluster_summary: 获取集群健康状态
        - get_pod_metrics: 获取 Pod 资源使用

        用户问题：{{user_query}}

        请根据问题选择合适的工具调用，然后给出回答。
    upstream:
      - start

  - id: end
    type: end
    params:
      outputs:
        - name: answer
          type: text
    upstream:
      - llm
"""


# ==================== 使用说明 ====================

DIFY_SETUP_INSTRUCTIONS = """
## Dify 平台集成步骤

### 步骤 1: 导入 OpenAPI 规范

1. 登录 Dify 控制台
2. 进入「工具」→「自定义工具」
3. 点击「导入 OpenAPI」
4. 上传 `openapi_spec.yaml` 文件
5. 点击「确认导入」

### 步骤 2: 配置 API 认证

1. 在导入的工具中填写 API 地址: `http://your-server:8000`
2. 如需认证，配置 API Key

### 步骤 3: 创建应用

1. 进入「应用」→「创建应用」
2. 选择「聊天助手」
3. 在「模型」设置中启用刚导入的工具
4. 编写系统提示词

### 示例系统提示词

```
你是一个智能助手，可以帮助用户：

1. 查询书籍信息
   - 询问用户想了解的书籍
   - 使用 get_book_rating 获取评分
   - 使用 get_book_detail 获取详情

2. 播报集群状态
   - 使用 get_cluster_summary 获取集群健康状态
   - 使用 get_pod_metrics 获取资源使用情况

请用友好的方式回答用户的问题。
```

### 步骤 4: 测试

1. 在预览窗口测试问答
2. 观察工具调用日志
3. 根据结果调整提示词
"""


if __name__ == "__main__":
    import json
    print("=" * 60)
    print("Dify 工具配置")
    print("=" * 60)
    print("\n工具 JSON 配置:")
    print(json.dumps(DIFY_TOOLS_CONFIG, indent=2, ensure_ascii=False))
    print("\n" + "=" * 60)
    print("工作流配置:")
    print(DIFY_WORKFLOW_EXAMPLE)
    print("\n" + "=" * 60)
    print("Dify 导入步骤:")
    print(DIFY_SETUP_INSTRUCTIONS)

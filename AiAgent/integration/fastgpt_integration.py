"""
FastGPT 平台配置示例

FastGPT 支持通过 API 和工作流接入外部工具。
"""

# ==================== FastGPT HTTP 工具配置 ====================

FASTGPT_TOOLS = [
    {
        "name": "get_book_rating",
        "description": "获取书籍评分",
        "method": "GET",
        "url": "{{host}}/api/ratings/{book_id}",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": {},
        "description_for_model": "获取指定书籍的用户评分和评价数量。book_id: 书籍ID (1=Kubernetes实战, 2=Docker容器化指南, 3=Prometheus监控实战)"
    },
    {
        "name": "get_book_detail",
        "description": "获取书籍详情",
        "method": "GET",
        "url": "{{host}}/api/books/{book_id}",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": {},
        "description_for_model": "获取书籍的详细信息，包括作者、出版社、价格和评分。book_id: 书籍ID"
    },
    {
        "name": "list_books",
        "description": "获取书籍列表",
        "method": "GET",
        "url": "{{host}}/api/books",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": {},
        "description_for_model": "获取系统中所有书籍的基本信息列表。"
    },
    {
        "name": "get_cluster_health",
        "description": "获取集群健康状态",
        "method": "GET",
        "url": "{{host}}/api/metrics/summary",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": {},
        "description_for_model": "获取Kubernetes集群的整体健康状态，包括Pod数量、CPU/内存使用率、各服务健康状态。"
    },
    {
        "name": "get_pod_resources",
        "description": "获取Pod资源使用",
        "method": "GET",
        "url": "{{host}}/api/metrics/pod/{namespace}",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": {},
        "description_for_model": "获取指定命名空间下所有Pod的CPU和内存使用情况。namespace: 命名空间名称，默认为default。"
    },
    {
        "name": "search_reviews",
        "description": "获取书籍评论",
        "method": "GET",
        "url": "{{host}}/api/reviews/{book_id}",
        "headers": {
            "Content-Type": "application/json"
        },
        "params": {},
        "body": {},
        "description_for_model": "获取指定书籍的用户评论列表。book_id: 书籍ID"
    }
]


# ==================== FastGPT 应用提示词 ====================

FASTGPT_SYSTEM_PROMPT = """
你是一个智能助手，可以帮助用户：

1. **书籍信息查询**
   - 查询书籍评分（如"《Kubernetes实战》评分多少？"）
   - 获取书籍详情（作者、出版社、价格）
   - 查看书籍评论

2. **集群运维播报**
   - 播报集群整体健康状态
   - 查询 Pod 资源使用情况
   - 回答运维相关问题

3. **智能问答**
   - 结合知识库回答问题
   - 提供解决方案建议

请用友好、专业的语气回答用户的问题。
回答时可以直接引用查询到的数据。
"""


# ==================== FastGPT 工作流配置 ====================

FASTGPT_WORKFLOW = """
FastGPT 工作流配置示例:

流程节点:
1. [开始] 接收用户输入
2. [LLM] 分析用户问题，决定是否调用工具
3. [工具节点] 调用外部 API
4. [LLM] 整理回答
5. [结束] 返回结果

LLM 节点提示词:
```
你是一个智能问答助手。

用户问题: {{question}}

请分析用户问题：
- 如果是书籍相关问题，调用 get_book_rating、get_book_detail 等工具
- 如果是集群相关问题，调用 get_cluster_health、get_pod_resources 等工具
- 如果是其他问题，直接回答

回答格式：
1. 先调用工具获取数据
2. 根据数据给出回答
3. 如有必要，提供建议
```
"""


# ==================== FastGPT 设置指南 ====================

FASTGPT_SETUP_INSTRUCTIONS = """
## FastGPT 平台集成步骤

### 步骤 1: 配置外部 API

1. 登录 FastGPT 管理后台
2. 进入「应用」→「工具」
3. 点击「添加工具」
4. 选择「HTTP 请求」
5. 填写配置

### 工具配置示例

```json
{
  "name": "get_book_rating",
  "method": "GET",
  "url": "http://your-server:8000/api/ratings/{book_id}",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 步骤 2: 创建应用

1. 进入「应用」→「创建应用」
2. 选择「AI Chat」或「Agent」
3. 启用工具调用
4. 添加配置好的工具
5. 编写系统提示词

### 步骤 3: 测试

1. 在预览中测试
2. 查看工具调用日志
3. 调整提示词优化效果

### 示例应用配置

应用名称: 智能运维助手
类型: Agent
提示词: 见上方 FASTGPT_SYSTEM_PROMPT

启用的工具:
- get_book_rating
- get_book_detail
- list_books
- get_cluster_health
- get_pod_resources
- search_reviews
"""


if __name__ == "__main__":
    import json
    print("=" * 60)
    print("FastGPT 平台配置")
    print("=" * 60)
    print("\n工具配置 (JSON格式，可直接复制到FastGPT):")
    print(json.dumps(FASTGPT_TOOLS, indent=2, ensure_ascii=False))
    print("\n" + "=" * 60)
    print("\n系统提示词:")
    print(FASTGPT_SYSTEM_PROMPT)

# 智能体平台集成指南

本目录包含将 Bookinfo 微服务能力接入主流智能体平台（Dify、Coze、FastGPT）的配置和指南。

## 目录结构

```
integration/
├── openapi_spec.yaml         # OpenAPI 3.0 规范文档
├── api_server.py            # FastAPI 服务端实现
├── dify_integration.py       # Dify 平台配置
├── coze_integration.py       # Coze (扣子) 平台配置
├── fastgpt_integration.py    # FastGPT 平台配置
└── README.md                 # 本文档
```

## 快速开始

### 1. 启动 API 服务

```powershell
# 安装依赖
pip install fastapi uvicorn pydantic

# 启动服务
python api_server.py

# 或使用 uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### 2. 测试 API

```bash
# 获取书籍列表
curl http://localhost:8000/api/books

# 获取书籍评分
curl http://localhost:8000/api/ratings/1

# 获取集群健康
curl http://localhost:8000/api/metrics/summary

# 获取工具列表
curl http://localhost:8000/api/tools
```

### 3. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 平台接入指南

### Dify

详见 `dify_integration.py`

```python
# 或运行脚本查看完整配置
python dify_integration.py
```

**主要步骤:**
1. 登录 Dify → 工具 → 自定义工具
2. 导入 `openapi_spec.yaml`
3. 配置 API 地址和认证
4. 创建应用并启用工具

### Coze (扣子)

详见 `coze_integration.py`

**主要步骤:**
1. 登录 Coze → 创建插件
2. 配置自定义 API
3. 创建 Bot 并添加插件
4. 设置提示词并发布

### FastGPT

详见 `fastgpt_integration.py`

**主要步骤:**
1. 登录 FastGPT → 应用 → 工具
2. 添加 HTTP 请求类型工具
3. 填入工具配置
4. 创建应用并启用工具

## API 端点一览

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/books` | GET | 获取书籍列表 |
| `/api/books/{book_id}` | GET | 获取书籍详情 |
| `/api/ratings` | GET | 获取所有评分 |
| `/api/ratings/{book_id}` | GET | 获取书籍评分 |
| `/api/reviews/{book_id}` | GET | 获取书籍评论 |
| `/api/metrics/pod/{namespace}` | GET | 获取 Pod 指标 |
| `/api/metrics/service/{name}` | GET | 获取服务指标 |
| `/api/metrics/summary` | GET | 获取集群摘要 |
| `/api/cluster/pods/{namespace}` | GET | 获取 Pod 列表 |
| `/api/cluster/events/{namespace}` | GET | 获取集群事件 |
| `/api/chat` | POST | 智能问答 |
| `/api/tools` | GET | 获取工具列表 |

## 设计原则

### 1. 工具粒度设计

- **适当抽象**: 每个工具完成单一明确的任务
- **参数简洁**: 避免过多参数，优先使用路径参数
- **返回值结构化**: 使用 JSON 格式，便于 LLM 解析

### 2. 描述清晰

每个工具都有详细的描述，包括:
- 功能说明
- 参数定义
- 返回值示例

### 3. 错误处理

统一的错误响应格式:
```json
{
  "code": 404,
  "message": "书籍不存在",
  "details": "book_id: 999 not found"
}
```

## 典型应用场景

### 1. 书店智能客服

```
用户: 《Kubernetes 实战》这本书的评分怎么样？

Agent:
  → 调用 get_book_rating(book_id="1")
  → 返回: 评分 4.5/5.0，基于 128 条评价
  → 回复: "《Kubernetes 实战》评分 4.5 分，用户评价'内容深入浅出，非常适合入门！'"
```

### 2. 集群状态播报员

```
用户: 现在集群状态怎么样？

Agent:
  → 调用 get_cluster_summary()
  → 返回: Pod 11/12 运行中，CPU 35%，内存 52%
  → 回复: "当前集群健康状态良好：11/12 Pod 运行中，CPU 使用 35%，内存使用 52%，所有服务状态正常。"
```

### 3. 运维问答助手

```
用户: reviews 服务响应变慢了，什么原因？

Agent:
  → 调用 get_pod_metrics(namespace="default")
  → 调用 get_cluster_events(namespace="default")
  → 分析: reviews Pod CPU/内存正常，但有网络延迟事件
  → 回复: "经检查，reviews 服务本身资源正常，但发现近期有网络延迟事件，可能是 Chaos Mesh 注入的故障。"
```

## 平台对比

| 特性 | Dify | Coze | FastGPT |
|------|------|------|---------|
| 部署方式 | 开源/云 | 云服务 | 开源/云 |
| 工具集成 | OpenAPI 导入 | 插件/API | HTTP 工具 |
| 工作流 | 支持 | 支持 | 支持 |
| RAG | 内置 | 需配置 | 内置 |
| 定制化 | 高 | 中 | 高 |

## 扩展建议

### 1. 增加更多工具

在 `api_server.py` 中添加新的端点:

```python
@app.get("/api/metrics/traces/{service}")
async def get_service_traces(service: str):
    """获取服务的调用链数据"""
    # 实现逻辑
    return {"traces": [...]}
```

### 2. 接入真实数据源

将模拟数据替换为真实调用:

```python
# 从 Prometheus 查询
prometheus_client = PrometheusClient()

# 从 Jaeger 查询
jaeger_client = JaegerClient()

# 从 Kubernetes API 查询
kube_config = kubernetes.client.Configuration()
```

### 3. 添加认证

```python
from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

@app.get("/api/books", dependencies=[Security(verify_api_key)])
async def get_books():
    # ...
```

## License

MIT

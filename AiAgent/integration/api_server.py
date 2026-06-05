"""
Bookinfo AI Agent API Server

FastAPI 服务端，实现与智能体平台集成的标准化接口。
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ==================== 生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的处理"""
    print("Bookinfo AI Agent API Server 启动中...")
    print("可用端点:")
    print("  - /api/books          # 书店业务接口")
    print("  - /api/metrics        # 监控查询接口")
    print("  - /api/cluster        # K8s 集群接口")
    print("  - /api/chat           # 智能问答接口")
    print("  - /docs               # API 文档")
    yield
    print("Bookinfo AI Agent API Server 关闭中...")


# ==================== FastAPI 应用 ====================
app = FastAPI(
    title="Bookinfo AI Agent API",
    description="""
## 概述

Bookinfo 微服务系统的 AI Agent 工具接口，供智能体平台（Dify、Coze、FastGPT等）调用。

## 可用工具

### 1. 书店业务接口
- 获取书籍列表和详情
- 查询书籍评分和评论

### 2. 监控查询接口
- Pod 资源使用情况
- 服务健康状态
- 集群健康摘要

### 3. K8s 集群接口
- Pod 列表和状态
- 集群事件

### 4. 智能问答接口
- 自然语言问答
- 多轮对话支持
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic 模型 ====================
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户问题")
    session_id: Optional[str] = Field(None, description="会话 ID")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")


# ==================== 模拟数据 ====================
# 书籍数据
BOOKS = [
    {
        "id": "1",
        "title": "Kubernetes 实战",
        "author": "张三",
        "publisher": "科技出版社",
        "publish_date": "2024-01-15",
        "price": 99.00,
        "description": "深入浅出讲解 Kubernetes 容器编排系统，适合 DevOps 工程师和云原生开发者。"
    },
    {
        "id": "2",
        "title": "Docker 容器化指南",
        "author": "李四",
        "publisher": "技术图书出版社",
        "publish_date": "2023-11-20",
        "price": 79.00,
        "description": "从入门到精通，全面介绍 Docker 容器技术及其生态系统。"
    },
    {
        "id": "3",
        "title": "Prometheus 监控实战",
        "author": "王五",
        "publisher": "运维出版社",
        "publish_date": "2024-03-10",
        "price": 89.00,
        "description": "详解 Prometheus 监控系统的配置、使用和最佳实践。"
    }
]

RATINGS = {
    "1": {"book_id": "1", "average": 4.5, "count": 128},
    "2": {"book_id": "2", "average": 4.2, "count": 86},
    "3": {"book_id": "3", "average": 4.8, "count": 215}
}

REVIEWS = {
    "1": [
        {"id": "r1", "user_id": "user001", "rating": 5, "text": "内容深入浅出，非常适合入门！", "created_at": "2024-05-01T10:30:00Z"},
        {"id": "r2", "user_id": "user002", "rating": 4, "text": "写得不错，但有些章节可以更详细", "created_at": "2024-05-15T14:20:00Z"}
    ],
    "2": [
        {"id": "r3", "user_id": "user003", "rating": 4, "text": "Docker 入门必读！", "created_at": "2024-04-20T09:15:00Z"}
    ],
    "3": [
        {"id": "r4", "user_id": "user004", "rating": 5, "text": "监控领域的圣经级作品！", "created_at": "2024-05-10T16:45:00Z"}
    ]
}

# 会话存储
chat_sessions: Dict[str, List[Dict]] = {}


# ==================== 书店业务接口 ====================
@app.get("/api/books", tags=["Bookstore"])
async def get_books():
    """获取所有书籍列表"""
    return {
        "code": 200,
        "message": "success",
        "data": [
            {"id": b["id"], "title": b["title"], "author": b["author"], "price": b["price"]}
            for b in BOOKS
        ]
    }


@app.get("/api/books/{book_id}", tags=["Bookstore"])
async def get_book_detail(book_id: str):
    """获取书籍详情"""
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    rating = RATINGS.get(book_id, {"average": 0, "count": 0})
    reviews = REVIEWS.get(book_id, [])

    return {
        "code": 200,
        "message": "success",
        "data": {
            **book,
            "rating": rating,
            "reviews_count": len(reviews)
        }
    }


@app.get("/api/ratings", tags=["Bookstore"])
async def get_all_ratings():
    """获取所有评分"""
    return {
        "code": 200,
        "message": "success",
        "data": list(RATINGS.values())
    }


@app.get("/api/ratings/{book_id}", tags=["Bookstore"])
async def get_book_rating(book_id: str):
    """获取指定书籍的评分"""
    if book_id not in RATINGS:
        raise HTTPException(status_code=404, detail="评分不存在")
    return {
        "code": 200,
        "message": "success",
        "data": RATINGS[book_id]
    }


@app.get("/api/reviews/{book_id}", tags=["Bookstore"])
async def get_book_reviews(book_id: str):
    """获取指定书籍的评论"""
    if book_id not in BOOKS:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return {
        "code": 200,
        "message": "success",
        "book_id": book_id,
        "reviews": REVIEWS.get(book_id, [])
    }


# ==================== 监控查询接口 ====================
@app.get("/api/metrics/pod/{namespace}", tags=["Monitoring"])
async def get_pod_metrics(
    namespace: str,
    metric_type: str = Query("all", enum=["cpu", "memory", "all"])
):
    """获取 Pod 指标"""
    # 模拟数据
    mock_pods = [
        {"pod_name": "productpage-v1-abc123", "cpu_cores": 0.15, "memory_mib": 303.5, "status": "Running"},
        {"pod_name": "details-v1-def456", "cpu_cores": 0.05, "memory_mib": 54.2, "status": "Running"},
        {"pod_name": "ratings-v1-ghi789", "cpu_cores": 0.04, "memory_mib": 47.8, "status": "Running"},
        {"pod_name": "reviews-v1-jkl012", "cpu_cores": 0.12, "memory_mib": 148.3, "status": "Running"},
        {"pod_name": "reviews-v2-mno345", "cpu_cores": 0.11, "memory_mib": 142.1, "status": "Running"},
        {"pod_name": "reviews-v3-pqr678", "cpu_cores": 0.13, "memory_mib": 145.6, "status": "Running"},
    ]

    return {
        "namespace": namespace,
        "timestamp": datetime.now().isoformat(),
        "metric_type": metric_type,
        "metrics": mock_pods
    }


@app.get("/api/metrics/service/{service_name}", tags=["Monitoring"])
async def get_service_metrics(
    service_name: str,
    duration: int = Query(5, ge=1, le=60)
):
    """获取服务指标"""
    # 模拟数据
    return {
        "service_name": service_name,
        "requests_per_second": 125.5,
        "avg_latency_ms": 45.2,
        "error_rate": 0.001,
        "p99_latency_ms": 120.0,
        "duration_minutes": duration,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/metrics/summary", tags=["Monitoring"])
async def get_cluster_summary():
    """获取集群健康摘要"""
    return {
        "total_pods": 12,
        "running_pods": 11,
        "failed_pods": 0,
        "pending_pods": 1,
        "cpu_usage_percent": 35.5,
        "memory_usage_percent": 52.3,
        "services_health": {
            "productpage": "healthy",
            "details": "healthy",
            "ratings": "healthy",
            "reviews": "healthy"
        },
        "timestamp": datetime.now().isoformat()
    }


# ==================== K8s 集群接口 ====================
@app.get("/api/cluster/pods/{namespace}", tags=["Cluster"])
async def get_cluster_pods(namespace: str):
    """获取 Pod 列表"""
    # 模拟数据
    mock_pods = [
        {"name": "productpage-v1-abc123", "status": "Running", "ready": "1/1", "restarts": 0, "age": "2d", "ip": "10.244.0.10", "node": "node1"},
        {"name": "details-v1-def456", "status": "Running", "ready": "1/1", "restarts": 0, "age": "2d", "ip": "10.244.0.11", "node": "node1"},
        {"name": "ratings-v1-ghi789", "status": "Running", "ready": "1/1", "restarts": 0, "age": "2d", "ip": "10.244.0.12", "node": "node1"},
    ]

    return {
        "namespace": namespace,
        "pods": mock_pods,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/cluster/events/{namespace}", tags=["Cluster"])
async def get_cluster_events(
    namespace: str,
    minutes: int = Query(60, ge=1, le=1440)
):
    """获取集群事件"""
    # 模拟数据
    mock_events = [
        {
            "type": "Normal",
            "reason": "Scheduled",
            "message": "Successfully assigned default/productpage-v1-abc123 to node1",
            "involved_object": "Pod/productpage-v1-abc123",
            "first_timestamp": "2024-05-29T10:00:00Z",
            "last_timestamp": "2024-05-29T10:00:00Z"
        },
        {
            "type": "Normal",
            "reason": "Pulled",
            "message": "Successfully pulled image 'istio/examples-bookinfo-productpage-v1:1.16.2'",
            "involved_object": "Pod/productpage-v1-abc123",
            "first_timestamp": "2024-05-29T10:00:01Z",
            "last_timestamp": "2024-05-29T10:00:01Z"
        },
        {
            "type": "Normal",
            "reason": "Created",
            "message": "Created container proxy",
            "involved_object": "Pod/productpage-v1-abc123",
            "first_timestamp": "2024-05-29T10:00:02Z",
            "last_timestamp": "2024-05-29T10:00:02Z"
        },
        {
            "type": "Normal",
            "reason": "Started",
            "message": "Started container proxy",
            "involved_object": "Pod/productpage-v1-abc123",
            "first_timestamp": "2024-05-29T10:00:03Z",
            "last_timestamp": "2024-05-29T10:00:03Z"
        }
    ]

    return {
        "namespace": namespace,
        "minutes": minutes,
        "events": mock_events,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 智能问答接口 ====================
@app.post("/api/chat", tags=["AI Chat"])
async def chat(request: ChatRequest, x_api_key: Optional[str] = Header(None)):
    """智能问答"""
    session_id = request.session_id or str(uuid.uuid4())

    # 初始化会话历史
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    # 添加用户消息到历史
    chat_sessions[session_id].append({"role": "user", "content": request.message})

    # 简单的问题理解和回答生成
    message_lower = request.message.lower()
    response_text = ""

    # 书籍相关问题
    if "评分" in message_lower or "rating" in message_lower:
        if "kubernetes" in message_lower or "1" in request.message:
            book = next((b for b in BOOKS if b["id"] == "1"), None)
            rating = RATINGS.get("1", {})
            response_text = f"《{book['title']}》这本书的评分是 {rating['average']}/5.0，基于 {rating['count']} 条评价。用户评价说：'内容深入浅出，非常适合入门！'"
        elif "docker" in message_lower or "2" in request.message:
            book = next((b for b in BOOKS if b["id"] == "2"), None)
            rating = RATINGS.get("2", {})
            response_text = f"《{book['title']}》这本书的评分是 {rating['average']}/5.0，基于 {rating['count']} 条评价。"
        elif "prometheus" in message_lower or "3" in request.message:
            book = next((b for b in BOOKS if b["id"] == "3"), None)
            rating = RATINGS.get("3", {})
            response_text = f"《{book['title']}》这本书的评分是 {rating['average']}/5.0，基于 {rating['count']} 条评价。用户评价说：'监控领域的圣经级作品！'"

    # 集群健康问题
    elif "集群" in message_lower or "cluster" in message_lower or "健康" in message_lower:
        summary = await get_cluster_summary()
        response_text = f"""当前集群健康状态：
- Pod 状态：{summary['running_pods']}/{summary['total_pods']} 运行中，{summary['failed_pods']} 失败
- CPU 使用率：{summary['cpu_usage_percent']}%
- 内存使用率：{summary['memory_usage_percent']}%
- 服务健康："""
        for svc, health in summary['services_health'].items():
            emoji = "✅" if health == "healthy" else "⚠️" if health == "degraded" else "❌"
            response_text += f"\n  {emoji} {svc}: {health}"

    # 内存/资源问题
    elif "内存" in message_lower or "memory" in message_lower:
        metrics = await get_pod_metrics("default")
        response_text = "各 Pod 内存使用情况：\n"
        for pod in metrics["metrics"]:
            response_text += f"- {pod['pod_name']}: {pod['memory_mib']:.1f} MiB\n"

    # 图书列表问题
    elif "书籍" in message_lower or "book" in message_lower or "图书" in message_lower:
        response_text = "以下是系统中的书籍：\n"
        for book in BOOKS:
            rating = RATINGS.get(book["id"], {})
            response_text += f"- 《{book['title']}》by {book['author']} - ¥{book['price']} (评分: {rating.get('average', 'N/A')})\n"

    # 默认回复
    else:
        response_text = f"我收到您的问题：'{request.message}'\n\n目前我可以帮您：\n" \
                       "- 查询书籍信息和评分\n" \
                       "- 查看集群健康状态\n" \
                       "- 查询 Pod 资源使用情况\n" \
                       "- 回答运维相关问题\n\n请告诉我您具体想了解什么？"

    # 添加助手回复到历史
    chat_sessions[session_id].append({"role": "assistant", "content": response_text})

    return {
        "session_id": session_id,
        "message": response_text,
        "sources": [
            {"type": "api", "content": "Bookinfo API"},
            {"type": "knowledge_base", "content": "运维知识库"}
        ],
        "tools_used": []
    }


@app.get("/api/tools", tags=["AI Chat"])
async def get_tools():
    """获取可用工具列表"""
    return {
        "tools": [
            {
                "name": "get_books",
                "description": "获取所有书籍列表",
                "parameters": [],
                "returns": "书籍列表，包含 ID、标题、作者、价格"
            },
            {
                "name": "get_book_detail",
                "description": "获取书籍详细信息",
                "parameters": [
                    {"name": "book_id", "type": "string", "required": True, "description": "书籍 ID"}
                ],
                "returns": "书籍详情，包含评分和评论数"
            },
            {
                "name": "get_book_rating",
                "description": "获取书籍评分",
                "parameters": [
                    {"name": "book_id", "type": "string", "required": True, "description": "书籍 ID"}
                ],
                "returns": "评分信息，平均分和评价数"
            },
            {
                "name": "get_cluster_summary",
                "description": "获取集群健康摘要",
                "parameters": [],
                "returns": "集群总体健康状态"
            },
            {
                "name": "get_pod_metrics",
                "description": "获取 Pod 资源使用指标",
                "parameters": [
                    {"name": "namespace", "type": "string", "required": True, "description": "命名空间"},
                    {"name": "metric_type", "type": "string", "required": False, "description": "指标类型: cpu/memory/all"}
                ],
                "returns": "Pod 的 CPU 和内存使用情况"
            }
        ]
    }


@app.get("/", tags=["Info"])
async def root():
    """API 根路径"""
    return {
        "name": "Bookinfo AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# ==================== 健康检查 ====================
@app.get("/health", tags=["Info"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ==================== 主程序 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

---
marp: true
theme: default
paginate: true
backgroundColor: #fff
style: |
  section {
    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
  }
  h1 {
    color: #1a73e8;
  }
  h2 {
    color: #333;
  }
  table {
    font-size: 0.7em;
  }
---

<!-- _class: lead -->
<!-- _backgroundColor: #1a73e8 -->
<!-- _color: white -->

# Excel Agent
## 智能表格助手

### 基于 LangChain 的 AI Excel 文件处理框架

---

<!-- _class: lead -->

# 目录

1. 项目概述
2. 系统架构
3. 核心功能
4. 技术实现
5. 使用示例
6. 适用场景
7. 未来展望

---

<!-- _backgroundColor: #f8f9fa -->

# 01 项目概述

---

<!-- _class: lead -->

# 什么是 Excel Agent？

一个基于**大语言模型**的智能 Excel 文件处理助手

用户使用**自然语言**描述需求，AI 自动完成 Excel 操作

---

# 项目定位

| 维度 | 说明 |
|------|------|
| **项目类型** | 开源 AI 应用框架 |
| **核心功能** | Excel 智能读写与编辑 |
| **技术基础** | LangChain + OpenAI API |
| **用户群体** | 办公人员、数据分析师、企业用户 |
| **核心价值** | 降低 Excel 操作门槛，提升效率 |

---

# 项目特色

- **自然语言交互** - 无需学习 Excel 复杂操作
- **智能理解** - AI 自动解析用户意图
- **自动化执行** - 自动调用工具完成操作
- **多模式支持** - 命令行 + 图形界面
- **可扩展架构** - 基于 LangChain，易于扩展

---

<!-- _backgroundColor: #f8f9fa -->

# 02 系统架构

---

# 整体架构

```
┌─────────────────────────────────────────────────────┐
│                   用户界面层                          │
│         ┌─────────────────┬─────────────────┐       │
│         │   CLI 命令行     │   PySide6 GUI   │       │
│         └────────┬────────┴────────┬────────┘       │
├──────────────────┼────────────────┼─────────────────┤
│                  │    ExcelAgent   │                │
│                  │   (智能体核心)   │                │
│                  ├────────────────┤                │
│                  │ Prompt 引擎    │                │
│                  │ LLM 调用       │                │
│                  │ 工具编排       │                │
│                  │ 执行循环       │                │
├──────────────────┼────────────────┼─────────────────┤
│                  │  Excel Tools   │                │
│                  │   (9个工具函数) │                │
│                  └────────┬────────┘                │
├───────────────────────────┼──────────────────────────┤
│                           ▼                          │
│                   openpyxl / Excel 文件              │
└─────────────────────────────────────────────────────┘
```

---

# 技术栈

| 层级 | 技术 | 作用 |
|------|------|------|
| **AI 框架** | LangChain | Agent 构建与编排 |
| **语言模型** | OpenAI GPT | 智能理解与决策 |
| **Excel 处理** | openpyxl | 文件读写操作 |
| **桌面界面** | PySide6 | Qt 图形界面 |
| **运行环境** | Python 3.11+ | 程序运行环境 |

---

# Agent 执行流程

```
    ┌──────────┐
    │ 用户输入  │
    │(自然语言) │
    └────┬─────┘
         ▼
┌──────────────────┐
│   LLM 理解意图   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  选择合适工具    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│   调用工具执行   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  结果反馈给 LLM  │
└────────┬─────────┘
         ▼
    ┌────┴─────┐
    │  完成?   │
    └────┬─────┘
      Yes│   │No
         ▼   └──→ 返回"选择合适工具"
    ┌─────────┐
    │ 返回结果 │
    └─────────┘
```

---

<!-- _backgroundColor: #f8f9fa -->

# 03 核心功能

---

# 功能矩阵

| 类别 | 工具函数 | 功能说明 |
|------|----------|----------|
| **读取** | excel_read_file | 读取文件概要（工作表、列头、示例数据） |
| **读取** | excel_read_sheet_data | 读取指定工作表的详细数据 |
| **读取** | excel_read_cell | 读取特定单元格或区域 |
| **创建** | excel_create_file | 创建新的 Excel 文件（含表头） |
| **写入** | excel_write_cells | 写入单个单元格 |
| **写入** | excel_write_row | 写入整行数据 |
| **写入** | excel_append_row | 追加新行到末尾 |
| **管理** | excel_add_sheet | 添加新的工作表 |
| **管理** | excel_delete_rows | 删除指定行 |

---

# 读取功能详解

## excel_read_file
- 自动扫描所有工作表
- 提取列标题
- 返回示例数据（前3行）
- 帮助快速了解文件结构

## excel_read_sheet_data
- 支持指定工作表名称
- 可限制返回行数
- 保留 Excel 行号
- 适合查看详细数据

## excel_read_cell
- 支持单个单元格 (A1)
- 支持区域范围 (A1:C5)
- 适合精确查找

---

# 写入功能详解

## excel_write_cells
- 精确定位单元格
- 支持字符串和数值
- 自动创建文件/工作表

## excel_write_row
- 写入整行数据
- 指定起始列
- 适合批量修改

## excel_append_row
- 自动追加到末尾
- 适合批量添加记录
- 无需计算行号

---

# 管理功能详解

## excel_create_file
- 创建新的 Excel 文件
- 支持自定义表头
- 可预填充数据

## excel_add_sheet
- 添加新的工作表
- 可设置列标题
- 支持多工作表管理

## excel_delete_rows
- 删除指定行
- 支持批量删除
- 自动调整行号

---

<!-- _backgroundColor: #f8f9fa -->

# 04 技术实现

---

# 项目结构

```
AiAgent/
├── main_excel.py              # ⭐ 命令行入口
├── app_excel.py               # 桌面应用入口
│
├── core/                      # 核心模块
│   ├── excel_agent_builder.py # Agent 核心构建
│   ├── agent_builder.py       # 通用 Agent 基类
│   │
│   ├── tools/                 # 工具集
│   │   ├── excel_tools.py     # Excel 操作工具 ⭐
│   │   ├── file_tools.py      # 文件操作工具
│   │   └── ...
│   │
│   └── prompts/               # 提示词模板
│       └── excel_agent_prompt.py  # Excel Agent 提示词
│
├── ui/                        # 界面模块
│   ├── main_window.py        # PySide6 主窗口
│   ├── excel_viewer.py       # Excel 查看器
│   └── ...
│
└── output/logs/               # 日志输出目录
```

---

# 核心代码 - Agent 初始化

```python
class ExcelAgent:
    def __init__(
        self,
        logger=None,
        llm=None,
        max_iterations=10,
        verbose=True
    ):
        self.llm = llm or init_llm()
        self.max_iterations = max_iterations

        # 注册 9 个工具
        self.tools = [
            excel_read_file,
            excel_read_sheet_data,
            excel_read_cell,
            excel_create_file,
            excel_write_cells,
            excel_write_row,
            excel_append_row,
            excel_add_sheet,
            excel_delete_rows,
        ]

        # 创建 Agent
        self.agent = self._create_agent()
```

---

# 核心代码 - 工具定义

```python
@tool("excel_read_file")
def excel_read_file(file_path: str) -> str:
    """
    读取 Excel 文件并返回所有工作表的结构化摘要。
    返回：工作表名称、行列数、列标题、示例数据
    """
    wb, _ = _load_workbook(file_path)
    # ... 遍历工作表，获取摘要信息
    return summary

@tool("excel_write_cells")
def excel_write_cells(
    file_path: str,
    cell: str,
    value: str,
    sheet_name: str = None
) -> str:
    """写入值到指定单元格"""
    # ... 实现写入逻辑
    return f"Written '{value}' to cell {cell}"
```

---

# 执行保护机制

| 机制 | 说明 |
|------|------|
| **最大迭代限制** | 默认 10 次，防止无限循环 |
| **异常捕获** | 每个工具调用都有 try-except |
| **日志记录** | 完整操作日志，可追溯 |
| **进度显示** | 实时显示执行状态 |
| **错误提示** | 友好的错误信息 |

---

<!-- _backgroundColor: #f8f9fa -->

# 05 使用示例

---

# 命令行使用

```bash
python main_excel.py
```

```
============================================================
  Excel 表格智能体
  阅读表格内容 · 创建和填写表格
============================================================

智能体已就绪！您可以描述需求，例如:
  - '帮我看看这个 Excel 文件里有什么内容: C:/data/report.xlsx'
  - '创建一个员工信息表，包含姓名、部门、职位、电话'
  - '在 C:/data/students.xlsx 里添加一条新记录'

输入 'quit' 或 'exit' 退出。
```

---

# 示例 1：查看文件内容

```
您: 帮我看看 C:/data/员工信息.xlsx 有什么内容

Agent: 我来读取这个文件...

[调用工具: excel_read_file]
结果:
# Excel File: C:/data/员工信息.xlsx

**Total sheets**: 2
**Sheet names**: 员工表, 部门表

## Sheet: 员工表
- Rows: 50, Columns: 5
- **Headers**: 姓名 | 部门 | 职位 | 电话 | 入职日期

**Sample data:**
| 行号 | 姓名 | 部门 | 职位 | 电话 | 入职日期 |
|------|------|------|------|------|----------|
| 2 | 张三 | 技术部 | 工程师 | 138****1234 | 2023-01-15 |
| 3 | 李四 | 市场部 | 经理 | 139****5678 | 2022-06-20 |
```

---

# 示例 2：创建新文件

```
您: 创建一个学生成绩表，包含姓名、语文、数学、英语、总分

Agent: 我来创建这个文件...

[调用工具: excel_create_file]
参数: file_path="C:/data/成绩表.xlsx"
      headers=["姓名", "语文", "数学", "英语", "总分"]

结果:
Excel file created successfully!
Path: C:/data/成绩表.xlsx
Sheet: Sheet1
Columns: 5 (姓名, 语文, 数学, 英语, 总分)
Data rows: 0
```

---

# 示例 3：添加数据

```
您: 在成绩表里添加一条记录：张三，95，88，92

Agent: 我来添加这条记录...

[调用工具: excel_append_row]
参数: file_path="C:/data/成绩表.xlsx"
      values=["张三", "95", "88", "92"]

结果:
Appended 4 value(s) to row 2 in sheet 'Sheet1' of C:/data/成绩表.xlsx

操作完成！
```

---

<!-- _backgroundColor: #f8f9fa -->

# 06 适用场景

---

# 应用场景

| 场景 | 说明 | 效率提升 |
|------|------|----------|
| **批量数据录入** | 销售、库存、财务数据快速录入 | ⭐⭐⭐⭐⭐ |
| **表格汇总** | 多表合并、跨文件数据分析 | ⭐⭐⭐⭐ |
| **格式整理** | 批量修改、填充、删除操作 | ⭐⭐⭐⭐⭐ |
| **自动化报表** | 定期数据处理工作流 | ⭐⭐⭐⭐ |
| **数据清洗** | 去重、格式化、校验 | ⭐⭐⭐⭐ |

---

# 典型应用案例

## 案例 1：HR 日常工作
- 批量录入新员工信息
- 更新员工资料
- 统计部门人员

## 案例 2：财务对账
- 导入银行流水
- 比对发票数据
- 生成汇总报表

## 案例 3：销售管理
- 客户信息管理
- 订单数据录入
- 业绩统计分析

---

<!-- _backgroundColor: #f8f9fa -->

# 07 未来展望

---

# 短期规划

- ✅ 支持更多 Excel 格式 (CSV, XLS)
- ⏳ 公式计算支持
- ⏳ 数据可视化集成
- ⏳ 条件格式化
- ⏳ 数据验证增强

---

# 长期愿景

- 🤖 **多 Agent 协作** - 多个 Agent 分工合作
- 🔄 **自动化工作流** - 复杂任务编排
- ☁️ **云端同步** - 多设备协作
- 📊 **智能分析** - 数据洞察与建议
- 🔌 **插件系统** - 扩展更多功能

---

<!-- _class: lead -->
<!-- _backgroundColor: #1a73e8 -->
<!-- _color: white -->

# 谢谢观看

### Excel Agent - 让 Excel 操作更简单

**项目地址**: C:\Users\23234\Desktop\AiAgent

---

# 附录：快速开始

## 安装依赖

```bash
pip install langchain langchain_core langchain_community
pip install openpyxl pyside6
pip install -r requirements.txt
```

## 运行程序

```bash
# 命令行模式
python main_excel.py

# 桌面应用模式
python app_excel.py
```

## 配置 API Key

```bash
export OPENAI_API_KEY="your-api-key"
# 或在代码中设置
llm = init_llm(api_key="your-api-key")
```

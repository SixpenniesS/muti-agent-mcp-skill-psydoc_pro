# PsyChat-Pro

> 🧠 多智能体心理咨询系统 - 基于工作流编排 + MCP + Skill

**Author: SixpenniesS**

## 项目简介

PsyChat-Pro 是一个多智能体心理咨询系统，展示了以下技术能力：

- ✅ **多智能体编排**：5个专业Agent分工协作，工作流调度器统一编排
- ✅ **MCP服务器集成**：文件系统、数据库、搜索引擎三类MCP工具
- ✅ **Skill系统**：情绪分析、危机检测等心理专用技能模块
- ✅ **RAG系统**：基于ChromaDB的向量检索增强生成

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Web界面 (FastAPI)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    工作流调度层                               │
│  WorkflowOrchestrator + WorkflowSelector                    │
│  - 心理评估工作流                                            │
│  - 日常咨询工作流                                            │
│  - 危机干预工作流                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent执行层                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │IntentAgent│ │ RAGAgent │ │SkillAgent│ │ResponseAgent│   │
│  │ 意图识别  │ │ 知识检索 │ │ 技能执行 │ │  响应生成  │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  MCP Gateway │    │Skill Registry│    │  VectorStore │
│              │    │              │    │              │
│ - filesystem │    │- emotion_    │    │  ChromaDB    │
│ - database   │    │  analyzer    │    │              │
│ - search     │    │- crisis_     │    │              │
│              │    │  detector    │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 核心组件

### 1. Agent层（多智能体）

| Agent | 职责 | 文件 |
|-------|------|------|
| IntentAgent | 意图识别、主题分类 | agents/intent_agent.py |
| RAGAgent | 向量检索、上下文构建 | agents/rag_agent.py |
| SkillAgent | 技能调用执行 | agents/skill_agent.py |
| ResponseAgent | 整合生成响应 | agents/response_agent.py |

### 2. 工作流调度层

| 组件 | 职责 |
|------|------|
| WorkflowOrchestrator | 工作流执行调度 |
| WorkflowSelector | 根据意图选择工作流 |
| WorkflowDefinition | 工作流定义（YAML） |

### 3. MCP集成层

| MCP服务器 | 工具 |
|-----------|------|
| FilesystemMCP | read_file, write_file, list_files |
| DatabaseMCP | query_user_history, save_conversation, log_crisis_event |
| SearchMCP | search, get_resources_by_topic |

### 4. Skill系统

| Skill | 功能 |
|-------|------|
| emotion_analyzer | 情绪类型检测、强度分析、极性判断 |
| crisis_detector | 危机关键词检测、风险评估、干预建议 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config/settings.py`：

```python
DEEPSEEK_API_KEY = "your-deepseek-api-key"
ALIBABA_API_KEY = "your-alibaba-api-key"
```

### 3. 构建知识库

```bash
python main.py --rebuild
```

### 4. 启动Web服务

```bash
python main.py
```

访问 http://localhost:8000

### 5. 命令行模式

```bash
python main.py --cli
```

## 项目结构

```
PsyChat-Pro/
├── agents/                 # Agent层
│   ├── base_agent.py       # Agent基类
│   ├── intent_agent.py     # 意图识别Agent
│   ├── rag_agent.py        # RAG检索Agent
│   ├── skill_agent.py      # 技能执行Agent
│   └── response_agent.py   # 响应生成Agent
│
├── orchestration/          # 工作流调度层
│   ├── workflow_orchestrator.py  # 工作流调度器
│   └── workflow_selector.py      # 工作流选择器
│
├── mcp/                    # MCP集成层
│   ├── mcp_gateway.py      # MCP网关
│   ├── filesystem_mcp.py   # 文件系统MCP
│   ├── database_mcp.py     # 数据库MCP
│   └── search_mcp.py       # 搜索引擎MCP
│
├── skills/                 # Skill系统
│   ├── skill_base.py       # Skill基类
│   ├── skill_registry.py   # Skill注册表
│   ├── emotion_analyzer.py # 情绪分析
│   └── crisis_detector.py  # 危机检测
│
├── core/                   # 核心层
│   ├── vector_store.py     # 向量存储
│   └── tts_service.py      # 语音合成
│
├── config/                 # 配置
│   ├── settings.py         # 主配置
│   └── workflows/          # 工作流定义
│
├── web/                    # Web界面
│   └── interface.py        # FastAPI应用
│
├── tests/                  # 测试
│   ├── test_agents.py
│   └── test_skills.py
│
├── docs/                   # 文档
│   └── DEVELOPMENT.md      # 开发文档
│
├── main.py                 # 入口文件
├── requirements.txt        # 依赖
└── README.md               # 本文件
```

## 技术亮点

### 1. 多智能体编排

- Agent专业化分工，单一职责原则
- 工作流驱动，可配置执行步骤
- 状态追踪，便于调试

### 2. MCP协议实践

- 实现MCP服务器基本框架
- 支持工具列表和调用
- 统一网关管理

### 3. Skill系统设计

- 领域专用技能封装
- 可扩展架构
- 与MCP工具集成

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| / | GET | Web界面 |
| /chat | POST | 对话接口 |
| /agents/status | GET | Agent状态 |
| /mcp/tools | GET | MCP工具列表 |
| /skills | GET | Skill列表 |

## 依赖

- Python 3.9+
- FastAPI + Uvicorn
- ChromaDB
- DeepSeek API（LLM）
- 阿里云百炼API（Embedding + TTS）

## License

MIT License

## Author

**SixpenniesS**

---

*本项目用于展示多智能体系统、MCP协议集成、Skill系统设计等技术能力。*

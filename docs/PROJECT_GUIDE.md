# PsyChat-Pro 项目详解文档

> 本文档详细说明项目的架构设计、模块细节、代码流程，帮助开发者深入理解系统实现。

---

## 目录

1. [系统架构](#1-系统架构)
2. [核心模块详解](#2-核心模块详解)
3. [数据流与工作流](#3-数据流与工作流)
4. [API接口文档](#4-api接口文档)
5. [配置说明](#5-配置说明)
6. [扩展指南](#6-扩展指南)

---

## 1. 系统架构

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
│                    (Web界面 / CLI模式)                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        编排层 (Orchestration)                    │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │ WorkflowOrchestrator│◄───│  WorkflowSelector   │            │
│  │    (工作流调度)       │    │   (工作流选择)        │            │
│  └─────────────────────┘    └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent层                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │IntentAgent│ │ RAGAgent │ │SkillAgent│ │Response  │          │
│  │意图识别   │ │ 知识检索  │ │技能执行  │ │ Agent    │          │
│  └──────────┘ └──────────┘ └──────────┘ │响应生成  │          │
│                                          └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Skill层     │     │    MCP层      │     │    核心层     │
│ ┌───────────┐ │     │ ┌───────────┐ │     │ ┌───────────┐ │
│ │Emotion    │ │     │ │Filesystem │ │     │ │VectorStore│ │
│ │Analyzer   │ │     │ │   MCP     │ │     │ │           │ │
│ ├───────────┤ │     │ ├───────────┤ │     │ ├───────────┤ │
│ │Crisis     │ │     │ │Database   │ │     │ │TTS Service│ │
│ │Detector   │ │     │ │   MCP     │ │     │ │           │ │
│ ├───────────┤ │     │ ├───────────┤ │     │ └───────────┘ │
│ │Skill      │ │     │ │Search     │ │     │               │
│ │Registry   │ │     │ │   MCP     │ │     │               │
│ └───────────┘ │     │ └───────────┘ │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        外部服务层                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │DeepSeek LLM│  │阿里云Embed │  │  ChromaDB  │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web框架 | FastAPI | 0.100+ | REST API服务 |
| ASGI服务器 | Uvicorn | 0.23+ | 异步HTTP服务 |
| 向量数据库 | ChromaDB | 0.4+ | 知识库存储与检索 |
| LLM | DeepSeek | - | 意图识别、响应生成 |
| Embedding | 阿里云百炼 | v4 | 文本向量化 |
| 数据库 | SQLite | - | 会话存储、日志记录 |
| 全文检索 | Whoosh | 2.7+ | 关键词搜索 |

### 1.3 目录结构详解

```
PsyChat-Pro/
├── agents/                    # Agent模块 - 核心智能体
│   ├── __init__.py           # 模块导出
│   ├── base_agent.py         # Agent基类，定义统一接口
│   ├── intent_agent.py       # 意图识别Agent
│   ├── rag_agent.py          # RAG检索Agent
│   ├── skill_agent.py        # 技能执行Agent
│   ├── tool_agent.py         # 工具调用Agent
│   └── response_agent.py     # 响应生成Agent
│
├── skills/                    # Skill系统 - 可插拔技能
│   ├── __init__.py           # 模块导出
│   ├── skill_base.py         # Skill基类
│   ├── skill_registry.py     # Skill注册表
│   ├── emotion_analyzer.py   # 情绪分析Skill
│   └── crisis_detector.py    # 危机检测Skill
│
├── mcp/                       # MCP集成 - 外部工具接口
│   ├── __init__.py           # 模块导出
│   ├── mcp_gateway.py        # MCP网关，统一管理
│   ├── filesystem_mcp.py     # 文件系统MCP
│   ├── database_mcp.py       # 数据库MCP
│   └── search_mcp.py         # 搜索引擎MCP
│
├── orchestration/             # 编排系统 - 工作流管理
│   ├── __init__.py           # 模块导出
│   ├── workflow_orchestrator.py  # 工作流调度器
│   └── workflow_selector.py      # 工作流选择器
│
├── core/                      # 核心模块 - 基础服务
│   ├── __init__.py           # 模块导出
│   ├── vector_store.py       # 向量存储(ChromaDB封装)
│   └── tts_service.py        # 语音合成服务
│
├── data/                      # 数据处理 - 知识库处理
│   ├── __init__.py           # 模块导出
│   └── processor.py          # 文档处理器
│
├── web/                       # Web界面 - HTTP服务
│   ├── __init__.py           # 模块导出
│   └── interface.py          # FastAPI应用和路由
│
├── config/                    # 配置模块 - 系统配置
│   ├── __init__.py           # 配置导出
│   └── settings.py           # 所有配置项
│
├── resources/                 # 资源文件 - 静态数据
│   ├── knowledge/            # 知识库文档(12个主题)
│   │   ├── 人际.txt
│   │   ├── 婚恋.txt
│   │   ├── 情绪.txt
│   │   └── ...
│   └── prompts/              # 提示词模板
│       └── system_prompt.txt
│
├── storage/                   # 数据存储 - 运行时数据
│   ├── chroma_db/            # ChromaDB向量数据
│   ├── psychology.db         # SQLite数据库
│   ├── search_index/         # 全文检索索引
│   ├── reports/              # 生成的报告
│   └── audio/                # TTS音频输出
│
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── test_agents.py        # Agent测试
│   └── test_skills.py        # Skill测试
│
├── docs/                      # 文档
│   ├── DEVELOPMENT.md        # 开发文档
│   └── CODEMAPS.md           # 代码地图
│
├── main.py                    # 入口文件
├── test_system.py            # 系统测试脚本
├── requirements.txt          # Python依赖
└── README.md                 # 项目说明
```

---

## 2. 核心模块详解

### 2.1 Agent系统

#### 2.1.1 BaseAgent (基类)

**文件位置**: `agents/base_agent.py`

所有Agent的基类，定义统一接口和行为规范。

```python
class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"        # 空闲，等待任务
    RUNNING = "running"  # 运行中
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"    # 执行失败

@dataclass
class AgentResult:
    """Agent执行结果数据结构"""
    success: bool                    # 是否成功
    data: Dict[str, Any]             # 返回数据
    error: Optional[str] = None      # 错误信息
    metadata: Dict[str, Any]         # 元数据（用于调试）
    timestamp: str                   # 执行时间戳
```

**关键方法**:

| 方法 | 说明 |
|------|------|
| `execute(context)` | 抽象方法，子类实现具体逻辑 |
| `run(context)` | 执行入口，带状态管理和错误处理 |
| `get_info()` | 获取Agent信息 |
| `get_execution_history()` | 获取执行历史记录 |
| `reset()` | 重置Agent状态 |

**执行流程**:
```
run() 调用
    │
    ├── 更新状态为 RUNNING
    │
    ├── 调用 execute() 执行具体逻辑
    │
    ├── 记录执行历史
    │
    ├── 更新状态为 SUCCESS/FAILED
    │
    └── 返回 AgentResult
```

#### 2.1.2 IntentAgent (意图识别)

**文件位置**: `agents/intent_agent.py`

分析用户输入，决定工作流类型和主题分类。

**输入**:
```python
{
    "user_message": "我最近感觉很焦虑",
    "conversation_history": [...]  # 可选
}
```

**输出**:
```python
{
    "intent": IntentType.DAILY_COUNSELING,
    "topics": ["情绪"],
    "need_rag": True,
    "confidence": 0.85,
    "crisis_detected": False
}
```

**意图类型**:
| 类型 | 说明 | 触发条件 |
|------|------|----------|
| `MENTAL_ASSESSMENT` | 心理评估 | 包含"评估"、"测试"等 |
| `DAILY_COUNSELING` | 日常咨询 | 需要专业建议的问题 |
| `CRISIS_INTERVENTION` | 危机干预 | 检测到危机信号 |
| `SIMPLE_CHAT` | 简单闲聊 | 问候、感谢等 |

**主题分类** (12类):
情绪、人际、婚恋、家庭、性心理、成长、治疗、社会、职场、自我、行为、心理学知识

**实现细节**:
1. 快速危机关键词检测（本地匹配）
2. 调用LLM进行意图分类和主题识别
3. 返回结构化结果

#### 2.1.3 RAGAgent (知识检索)

**文件位置**: `agents/rag_agent.py`

从向量数据库检索相关心理学知识。

**输入**:
```python
{
    "query": "我最近感觉很焦虑",
    "topics": ["情绪"],      # 可选，主题过滤
    "top_k": 6,              # 可选，返回数量
    "threshold": 0.15        # 可选，相似度阈值
}
```

**输出**:
```python
{
    "documents": [
        {
            "content": "文档内容...",
            "metadata": {"source": "情绪.txt", "topic": "情绪"},
            "similarity": 0.85
        }
    ],
    "context_text": "合并后的上下文文本",
    "total_found": 6
}
```

**检索流程**:
```
输入Query
    │
    ├── 调用阿里云Embedding API生成向量
    │
    ├── ChromaDB向量检索
    │
    ├── 主题过滤（如有指定）
    │
    ├── 相似度阈值过滤
    │
    └── 返回文档列表和合并上下文
```

#### 2.1.4 SkillAgent (技能执行)

**文件位置**: `agents/skill_agent.py`

管理Skill的注册和执行。

**输入**:
```python
{
    "skill_calls": [
        {
            "skill": "crisis_detector",
            "params": {"text": "用户输入"}
        }
    ],
    "parallel": True  # 并行执行
}
```

**输出**:
```python
{
    "skill_results": [
        {
            "success": True,
            "skill": "crisis_detector",
            "result": {"risk_level": "low", ...}
        }
    ],
    "success_count": 1,
    "failure_count": 0
}
```

#### 2.1.5 ResponseAgent (响应生成)

**文件位置**: `agents/response_agent.py`

整合信息，生成最终回答。

**输入**:
```python
{
    "user_message": "我最近感觉很焦虑",
    "rag_context": "检索到的上下文...",
    "rag_documents": [...],
    "skill_results": {...},
    "conversation_history": [...],
    "mode": "normal"  # normal | crisis
}
```

**输出**:
```python
{
    "response": "生成的回复内容...",
    "sources": [...],
    "used_rag": True,
    "used_skills": ["crisis_detector"],
    "mode": "normal"
}
```

**提示词策略**:
- `normal`模式: 结合RAG上下文生成专业回复
- `crisis`模式: 优先提供危机干预资源和建议

---

### 2.2 Skill系统

#### 2.2.1 BaseSkill (基类)

**文件位置**: `skills/skill_base.py`

```python
class BaseSkill(ABC):
    """Skill基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"skill.{name}")
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能（子类实现）"""
        pass
    
    def get_info(self) -> Dict[str, str]:
        """获取技能信息"""
        return {"name": self.name, "description": self.description}
```

#### 2.2.2 CrisisDetectorSkill (危机检测)

**文件位置**: `skills/crisis_detector.py`

**风险等级**:
| 等级 | 分数范围 | 关键词示例 |
|------|----------|------------|
| critical | ≥10 | 自杀、想死、结束生命 |
| high | 7-9 | 自残、绝望、没有希望 |
| medium | 4-6 | 痛苦、崩溃、无法承受 |
| low | 0-3 | 困难、迷茫、无助 |

**输出示例**:
```python
{
    "success": True,
    "risk_level": "high",
    "risk_score": 7.5,
    "detected_signals": [
        {"keyword": "绝望", "level": "high", "score": 7}
    ],
    "intervention_needed": True,
    "intervention": {
        "immediate": True,
        "message": "检测到高风险信号",
        "actions": ["提供专业资源", "深入探讨问题"],
        "hotlines": [
            {"name": "全国心理援助热线", "number": "400-161-9995"}
        ]
    }
}
```

#### 2.2.3 EmotionAnalyzerSkill (情绪分析)

**文件位置**: `skills/emotion_analyzer.py`

**情绪分类**:
- **正面**: 喜悦、满足、平静、期待
- **负面**: 焦虑、悲伤、愤怒、恐惧
- **混合**: 矛盾、纠结

**输出示例**:
```python
{
    "success": True,
    "primary_emotion": "焦虑",
    "emotion_score": 0.75,
    "emotion_breakdown": {
        "焦虑": 0.75,
        "恐惧": 0.3,
        "悲伤": 0.2
    },
    "intensity": "moderate",
    "valence": "negative"
}
```

---

### 2.3 MCP集成

#### 2.3.1 MCPGateway (网关)

**文件位置**: `mcp/mcp_gateway.py`

统一管理多个MCP服务器。

```python
class MCPGateway:
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
    
    def register_server(self, server: MCPServer) -> None:
        """注册服务器"""
        self.servers[server.name] = server
    
    async def list_tools(self, server: str = None) -> List[Dict]:
        """列出可用工具"""
        pass
    
    async def call_tool(self, server: str, tool: str, params: Dict) -> Dict:
        """调用工具"""
        pass
```

#### 2.3.2 MCP服务器清单

| 服务器 | 工具 | 说明 |
|--------|------|------|
| FilesystemMCP | read_file, write_file, list_files, delete_file | 文件系统操作 |
| DatabaseMCP | query_user_history, save_conversation, log_crisis_event | 数据库操作 |
| SearchMCP | search, get_resources_by_topic | 全文检索 |

---

### 2.4 编排系统

#### 2.4.1 WorkflowOrchestrator (工作流调度器)

**文件位置**: `orchestration/workflow_orchestrator.py`

**核心数据结构**:

```python
@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str                      # 步骤名称
    agent: str                     # 负责的Agent
    input_mapping: Dict[str, Any]  # 输入映射
    output_key: str                # 输出存储key
    condition: Optional[str]       # 执行条件
    on_failure: str = "abort"      # 失败策略: abort/continue/skip

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str = ""
    steps: List[WorkflowStep]
    trigger_intents: List[str] = []
    trigger_keywords: List[str] = []
```

#### 2.4.2 WorkflowSelector (工作流选择器)

**文件位置**: `orchestration/workflow_selector.py`

**选择优先级**:
1. 危机信号 → `crisis_intervention`
2. 意图类型 → 对应工作流
3. 关键词匹配 → 对应工作流
4. 默认 → `daily_counseling`

---

## 3. 数据流与工作流

### 3.1 完整请求处理流程

```
用户输入: "我最近感觉很焦虑"
         │
         ▼
┌─────────────────────────────────────┐
│ 1. IntentAgent (意图识别)            │
│    - 快速危机关键词检测               │
│    - LLM意图分类                     │
│    输出: intent=日常咨询, topics=[情绪]│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 2. SkillAgent (危机检测)             │
│    - 关键词匹配                       │
│    - 风险等级评估                     │
│    输出: risk_level=low              │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 3. WorkflowSelector (工作流选择)     │
│    - 根据风险等级+意图选择工作流       │
│    输出: workflow_id=daily_counseling│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 4. RAGAgent (知识检索)               │
│    - 生成查询向量                     │
│    - ChromaDB检索                    │
│    输出: documents=[...], context=...│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 5. ResponseAgent (响应生成)          │
│    - 构建提示词                       │
│    - 调用DeepSeek生成回复             │
│    输出: response="..."              │
└─────────────────────────────────────┘
         │
         ▼
返回给用户
```

### 3.2 并行执行流程

当需要执行多个Skill时，系统支持并行执行：

```python
# 并行执行多个Skill
skill_calls = [
    {"skill": "crisis_detector", "params": {"text": message}},
    {"skill": "emotion_analyzer", "params": {"text": message}}
]

# 使用asyncio.gather并行执行
results = await asyncio.gather(*tasks)
```

---

## 4. API接口文档

### 4.1 REST API

**基础URL**: `http://localhost:8000`

#### POST /chat

聊天接口

**请求**:
```
Content-Type: application/x-www-form-urlencoded

message=你好，我最近感觉很焦虑&user_id=default
```

**响应**:
```json
{
    "success": true,
    "response": "你好，听起来你最近承受了不少压力...",
    "workflow_info": {
        "workflow_id": "daily_counseling",
        "steps_completed": 4,
        "total_steps": 4,
        "agents_called": [
            {"name": "IntentAgent", "success": true},
            {"name": "SkillAgent", "success": true},
            {"name": "RAGAgent", "success": true},
            {"name": "ResponseAgent", "success": true}
        ],
        "skills_used": ["crisis_detector"],
        "risk_level": "low"
    }
}
```

#### GET /agents/status

获取Agent状态

**响应**:
```json
{
    "agents": [
        {"name": "intent_agent", "status": "idle", "execution_count": 10}
    ]
}
```

#### GET /mcp/tools

获取MCP工具列表

**响应**:
```json
{
    "servers": {
        "filesystem": ["read_file", "write_file", "list_files", "delete_file"],
        "database": ["query_user_history", "save_conversation", "log_crisis_event"],
        "search": ["search", "get_resources_by_topic"]
    }
}
```

#### GET /skills

获取Skill列表

**响应**:
```json
{
    "skills": [
        {"name": "emotion_analyzer", "description": "分析用户输入的情绪倾向和强度"},
        {"name": "crisis_detector", "description": "检测用户输入中的危机信号和风险等级"}
    ]
}
```

#### GET /knowledge/info

获取知识库信息

**响应**:
```json
{
    "success": true,
    "info": {
        "name": "psychology_knowledge",
        "document_count": 30255,
        "path": "./storage/chroma_db"
    }
}
```

---

## 5. 配置说明

### 5.1 配置文件结构

**文件**: `config/settings.py`

```python
# API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "your-api-key")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "your-api-key")
EMBEDDING_MODEL = "text-embedding-v4"

# 存储配置
CHROMA_DB_PATH = "./storage/chroma_db"
COLLECTION_NAME = "psychology_knowledge"
DATABASE_PATH = "./storage/psychology.db"

# 检索配置
TOP_K_RESULTS = 6
SIMILARITY_THRESHOLD = 0.15
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# Agent配置
AGENT_CONFIG = {
    "intent_agent": {
        "model": "deepseek-chat",
        "temperature": 0.3,
        "max_tokens": 100
    },
    "response_agent": {
        "model": "deepseek-chat",
        "temperature": 0.6,
        "max_tokens": 1000
    }
}
```

### 5.2 环境变量

创建 `.env` 文件:
```bash
DEEPSEEK_API_KEY=your-deepseek-api-key
ALIBABA_API_KEY=your-alibaba-api-key
```

---

## 6. 扩展指南

### 6.1 添加新Agent

1. 创建 `agents/my_agent.py`:
```python
from agents.base_agent import BaseAgent, AgentResult

class MyAgent(BaseAgent):
    def __init__(self, config: Dict = None):
        super().__init__("MyAgent", config)
    
    async def execute(self, context: Dict) -> AgentResult:
        # 实现逻辑
        return AgentResult(success=True, data={"result": "value"})
```

2. 在 `agents/__init__.py` 导出:
```python
from .my_agent import MyAgent
__all__ = [..., "MyAgent"]
```

### 6.2 添加新Skill

1. 创建 `skills/my_skill.py`:
```python
from skills.skill_base import BaseSkill

class MySkill(BaseSkill):
    def __init__(self):
        super().__init__("my_skill", "我的自定义技能")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 实现技能逻辑
        return {"success": True, "result": "..."}
```

2. 注册Skill:
```python
from skills import SkillRegistry, MySkill
registry = SkillRegistry()
registry.register(MySkill())
```

### 6.3 添加新MCP服务器

1. 创建 `mcp/my_mcp.py`:
```python
from mcp.mcp_gateway import MCPServer

class MyMCP(MCPServer):
    @property
    def name(self) -> str:
        return "my_mcp"
    
    async def list_tools(self) -> List[Dict]:
        return [{"name": "my_tool", "description": "..."}]
    
    async def call_tool(self, tool_name: str, params: Dict) -> Dict:
        # 实现工具逻辑
        return {"success": True}
```

2. 注册服务器:
```python
from mcp import MCPGateway, MyMCP
gateway = MCPGateway()
gateway.register_server(MyMCP())
```

---

## 附录

### A. 启动命令

```bash
# Web模式
python main.py --web

# CLI模式
python main.py --cli

# 查看系统信息
python main.py --info

# 重建知识库
python main.py --rebuild
```

### B. 依赖安装

```bash
pip install -r requirements.txt
```

### C. 项目亮点

1. **多Agent协作**: 意图识别→知识检索→技能执行→响应生成
2. **RAG系统**: ChromaDB向量存储 + 阿里云百炼Embedding
3. **Skill系统**: 可插拔技能架构，支持并行执行
4. **MCP集成**: 标准化工具接口，易于扩展
5. **工作流编排**: 状态机模式，灵活的任务调度

---

*文档版本: 1.0*
*最后更新: 2026-04-10*
*作者: SixpenniesS*

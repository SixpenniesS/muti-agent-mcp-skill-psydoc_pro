# PsyChat-Pro 架构详解

> 本文档详细介绍项目的架构设计、模块实现和使用方法。

## 目录

1. [系统架构总览](#1-系统架构总览)
2. [核心模块详解](#2-核心模块详解)
3. [数据流与工作流](#3-数据流与工作流)
4. [API接口文档](#4-api接口文档)
5. [配置说明](#5-配置说明)
6. [扩展指南](#6-扩展指南)

---

## 1. 系统架构总览

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户层 (Web/CLI)                               │
│                    web/interface.py 或 main.py                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        编排层 (Orchestration)                            │
│  ┌─────────────────────┐    ┌─────────────────────┐                     │
│  │  WorkflowSelector   │───▶│ WorkflowOrchestrator│                     │
│  │   (工作流选择器)      │    │   (工作流调度器)      │                     │
│  └─────────────────────┘    └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Agent层 (多智能体)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ IntentAgent  │  │  RAGAgent    │  │ SkillAgent   │  │ResponseAgent │ │
│  │  意图识别     │  │  知识检索     │  │  技能执行     │  │  响应生成    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Skill系统     │  │     MCP层       │  │    核心层       │
│ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │EmotionSkill │ │  │ │FilesystemMCP│ │  │ │ VectorStore │ │
│ │CrisisSkill  │ │  │ │ DatabaseMCP │ │  │ │ TTSService  │ │
│ │SkillRegistry│ │  │ │  SearchMCP  │ │  │ │             │ │
│ └─────────────┘ │  │ │  MCPGateway │ │  │ └─────────────┘ │
└─────────────────┘  │ └─────────────┘ │  └─────────────────┘
                     └─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           外部服务层                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ DeepSeek LLM │  │阿里云Embedding│  │  ChromaDB   │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| Web框架 | FastAPI + Uvicorn | REST API服务 |
| 向量数据库 | ChromaDB | 知识库存储与检索 |
| LLM | DeepSeek | 意图识别、响应生成 |
| Embedding | 阿里云百炼 | 文本向量化 |
| 数据库 | SQLite | 会话存储、日志记录 |
| 全文检索 | Whoosh | 关键词搜索 |

### 1.3 目录结构

```
PsyChat-Pro/
├── agents/                    # Agent模块
│   ├── __init__.py
│   ├── base_agent.py         # Agent基类
│   ├── intent_agent.py       # 意图识别Agent
│   ├── rag_agent.py          # RAG检索Agent
│   ├── skill_agent.py        # 技能执行Agent
│   ├── tool_agent.py         # 工具调用Agent
│   └── response_agent.py     # 响应生成Agent
│
├── skills/                    # Skill系统
│   ├── __init__.py
│   ├── skill_base.py         # Skill基类
│   ├── skill_registry.py     # Skill注册表
│   ├── emotion_analyzer.py   # 情绪分析Skill
│   └── crisis_detector.py    # 危机检测Skill
│
├── mcp/                       # MCP集成
│   ├── __init__.py
│   ├── mcp_gateway.py        # MCP网关
│   ├── filesystem_mcp.py     # 文件系统MCP
│   ├── database_mcp.py       # 数据库MCP
│   └── search_mcp.py         # 搜索引擎MCP
│
├── orchestration/             # 工作流编排
│   ├── __init__.py
│   ├── workflow_orchestrator.py  # 工作流调度器
│   └── workflow_selector.py      # 工作流选择器
│
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── vector_store.py       # 向量存储
│   └── tts_service.py        # 语音合成服务
│
├── data/                      # 数据处理
│   ├── __init__.py
│   └── processor.py          # 文档处理器
│
├── web/                       # Web界面
│   ├── __init__.py
│   └── interface.py          # FastAPI应用
│
├── config/                    # 配置模块
│   ├── __init__.py
│   └── settings.py           # 配置文件
│
├── resources/                 # 资源文件
│   ├── knowledge/            # 知识库文档
│   └── prompts/              # 提示词模板
│
├── storage/                   # 数据存储
│   ├── chroma_db/            # ChromaDB数据
│   ├── psychology.db         # SQLite数据库
│   └── reports/              # 生成的报告
│
├── tests/                     # 测试文件
├── docs/                      # 文档
├── main.py                    # 入口文件
├── test_system.py            # 系统测试
├── requirements.txt          # 依赖列表
└── README.md                 # 项目说明
```

---

## 2. 核心模块详解

### 2.1 Agent系统

#### 2.1.1 BaseAgent (基类)

**文件**: `agents/base_agent.py`

所有Agent的基类，定义统一接口和行为。

```python
class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"        # 空闲
    RUNNING = "running"  # 运行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"    # 失败

@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool                    # 是否成功
    data: Dict[str, Any]             # 返回数据
    error: Optional[str] = None      # 错误信息
    metadata: Dict[str, Any]         # 元数据
    timestamp: str                   # 时间戳

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name                    # Agent名称
        self.config = config or {}          # 配置
        self.status = AgentStatus.IDLE      # 状态
        self.logger = logging.getLogger()   # 日志器
    
    @abstractmethod
    async def execute(self, context: Dict) -> AgentResult:
        """执行核心逻辑（子类实现）"""
        pass
    
    async def run(self, context: Dict) -> AgentResult:
        """运行Agent（带状态管理）"""
        self.status = AgentStatus.RUNNING
        try:
            result = await self.execute(context)
            self.status = AgentStatus.SUCCESS if result.success else AgentStatus.FAILED
            return result
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(success=False, data={}, error=str(e))
```

**关键方法**:
- `execute()`: 抽象方法，子类实现具体逻辑
- `run()`: 带状态管理的执行入口
- `get_info()`: 获取Agent信息
- `get_execution_history()`: 获取执行历史

#### 2.1.2 IntentAgent (意图识别)

**文件**: `agents/intent_agent.py`

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
    "intent": IntentType.DAILY_COUNSELING,  # 意图类型
    "topics": ["情绪"],                      # 主题列表
    "need_rag": True,                        # 是否需要RAG
    "confidence": 0.85,                      # 置信度
    "crisis_detected": False                 # 是否检测到危机
}
```

**意图类型**:
| 类型 | 说明 | 触发条件 |
|------|------|----------|
| `MENTAL_ASSESSMENT` | 心理评估 | 包含"评估"、"测试"等关键词 |
| `DAILY_COUNSELING` | 日常咨询 | 需要专业建议的问题 |
| `CRISIS_INTERVENTION` | 危机干预 | 检测到自杀、自残等关键词 |
| `SIMPLE_CHAT` | 简单闲聊 | 问候、感谢等 |

**主题分类** (12类):
- 情绪、人际、婚恋、家庭、性心理
- 成长、治疗、社会、职场、自我
- 行为、心理学知识

**实现细节**:
1. 快速危机关键词检测（本地匹配）
2. 调用LLM进行意图分类
3. 如果检测到危机，覆盖意图类型

#### 2.1.3 RAGAgent (知识检索)

**文件**: `agents/rag_agent.py`

从向量数据库检索相关心理学知识。

**输入**:
```python
{
    "query": "我最近感觉很焦虑",
    "topics": ["情绪"],           # 可选，主题过滤
    "top_k": 6,                   # 可选，返回数量
    "threshold": 0.15             # 可选，相似度阈值
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
    "total_found": 6,
    "query_time_ms": 150
}
```

**检索流程**:
```
用户Query → Embedding → 向量检索 → 过滤 → 排序 → 返回
                ↓
         阿里云百炼API
```

**多主题检索**:
- 单主题: 直接过滤
- 多主题: 分别检索后合并去重

#### 2.1.4 SkillAgent (技能执行)

**文件**: `agents/skill_agent.py`

管理Skill的注册和执行。

**输入**:
```python
{
    "skill_calls": [
        {"skill": "crisis_detector", "params": {"text": "用户输入"}},
        {"skill": "emotion_analyzer", "params": {"text": "用户输入"}}
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
            "result": {"risk_level": "low", "risk_score": 0}
        }
    ],
    "success_count": 2,
    "failure_count": 0
}
```

**执行模式**:
- 并行模式: 使用`asyncio.gather()`同时执行多个Skill
- 顺序模式: 按顺序依次执行

#### 2.1.5 ResponseAgent (响应生成)

**文件**: `agents/response_agent.py`

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
    "sources": [...],        # 来源信息
    "used_rag": True,        # 是否使用了RAG
    "used_skills": [...]     # 使用的Skill列表
}
```

**提示词策略**:

| 模式 | 提示词类型 | 特点 |
|------|-----------|------|
| 正常+RAG | `_build_rag_prompt()` | 结合案例参考 |
| 正常无RAG | `_build_direct_prompt()` | REBT疗法引导 |
| 危机 | `_build_crisis_prompt()` | 提供求助热线 |

---

### 2.2 Skill系统

#### 2.2.1 BaseSkill (基类)

**文件**: `skills/skill_base.py`

```python
class BaseSkill(ABC):
    """Skill基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"skill.{name}")
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        pass
```

#### 2.2.2 CrisisDetectorSkill (危机检测)

**文件**: `skills/crisis_detector.py`

**风险等级**:

| 等级 | 分数范围 | 关键词示例 | 干预策略 |
|------|---------|-----------|----------|
| critical | ≥10 | 自杀、想死、结束生命 | 立即干预，提供热线 |
| high | 7-9 | 自残、绝望、活不下去 | 重点关注，专业资源 |
| medium | 4-6 | 痛苦、崩溃、无法承受 | 情感支持 |
| low | 0-3 | 困难、迷茫、无助 | 常规咨询 |

**关键词库**:
```python
CRISIS_LEVELS = {
    "critical": {
        "keywords": ["自杀", "想死", "不想活", "结束生命", ...],
        "score": 10
    },
    "high": {
        "keywords": ["自残", "伤害自己", "没有希望", ...],
        "score": 7
    },
    # ...
}
```

**检测流程**:
```
输入文本 → 关键词匹配 → 计算分数 → 结合上下文 → 返回风险等级
                           ↓
                    上下文分析（可选）
```

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
        "actions": ["提供专业资源", "深入探讨问题根源"],
        "hotlines": [{"name": "全国心理援助热线", "number": "400-161-9995"}]
    }
}
```

#### 2.2.3 EmotionAnalyzerSkill (情绪分析)

**文件**: `skills/emotion_analyzer.py`

**情绪分类**:
- 正面情绪: 喜悦、满足、平静、期待
- 负面情绪: 焦虑、悲伤、愤怒、恐惧
- 混合情绪: 矛盾、纠结

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
    "intensity": "moderate",  # low/moderate/high
    "valence": "negative"      # positive/negative/neutral
}
```

---

### 2.3 MCP集成

#### 2.3.1 MCPGateway (网关)

**文件**: `mcp/mcp_gateway.py`

统一管理多个MCP服务器。

```python
class MCPGateway:
    """MCP网关"""
    
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

#### 2.3.2 FilesystemMCP (文件系统)

**文件**: `mcp/filesystem_mcp.py`

**可用工具**:

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `read_file` | 读取文件 | `path` |
| `write_file` | 写入文件 | `path`, `content` |
| `list_files` | 列出文件 | `directory` |
| `delete_file` | 删除文件 | `path` |

#### 2.3.3 DatabaseMCP (数据库)

**文件**: `mcp/database_mcp.py`

**可用工具**:

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `query_user_history` | 查询用户历史 | `user_id`, `limit` |
| `save_conversation` | 保存对话 | `user_id`, `conversation` |
| `log_crisis_event` | 记录危机事件 | `user_id`, `event_data` |

#### 2.3.4 SearchMCP (搜索引擎)

**文件**: `mcp/search_mcp.py`

**可用工具**:

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `search` | 全文搜索 | `query`, `top_k` |
| `get_resources_by_topic` | 按主题获取资源 | `topic` |

---

### 2.4 编排系统

#### 2.4.1 WorkflowOrchestrator (工作流调度器)

**文件**: `orchestration/workflow_orchestrator.py`

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
    on_failure: str = "abort"      # 失败策略

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str               # 工作流ID
    name: str                      # 工作流名称
    description: str               # 描述
    steps: List[WorkflowStep]      # 步骤列表
    trigger_intents: List[str]     # 触发意图
    trigger_keywords: List[str]    # 触发关键词
```

**执行流程**:
```
execute(workflow_id, context)
       ↓
创建WorkflowExecution实例
       ↓
遍历步骤 → 检查条件 → 获取Agent → 构建输入 → 执行
       ↓
存储结果到context → 继续下一步
       ↓
完成/失败
```

#### 2.4.2 WorkflowSelector (工作流选择器)

**文件**: `orchestration/workflow_selector.py`

**选择优先级**:
1. 危机信号 → `crisis_intervention`
2. 意图类型 → 对应工作流
3. 关键词匹配 → 对应工作流
4. 默认 → `daily_counseling`

```python
class WorkflowSelector:
    def select(self, intent_result, crisis_result, user_message) -> str:
        # 1. 检查危机
        if crisis_result.get("risk_level") in ["critical", "high"]:
            return "crisis_intervention"
        
        # 2. 根据意图
        intent = intent_result.get("intent")
        workflow_map = {
            "mental_assessment": "mental_assessment",
            "daily_counseling": "daily_counseling",
            # ...
        }
        
        # 3. 关键词匹配
        # 4. 默认
        return "daily_counseling"
```

---

### 2.5 核心模块

#### 2.5.1 VectorStore (向量存储)

**文件**: `core/vector_store.py`

**初始化**:
```python
class VectorStore:
    def __init__(self):
        self.api_key = ALIBABA_API_KEY
        self.embedding_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
        
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "心理学知识向量存储"}
        )
```

**Embedding调用**:
```python
def get_embedding(self, text: str) -> List[float]:
    """调用阿里云百炼API生成嵌入向量"""
    response = requests.post(
        self.embedding_url,
        headers={"Authorization": f"Bearer {self.api_key}"},
        json={"model": EMBEDDING_MODEL, "input": text}
    )
    return response.json()["data"][0]["embedding"]
```

**检索方法**:
```python
def search(self, query: str, top_k: int = 6, threshold: float = 0.15, 
           topics: List[str] = None) -> List[Dict]:
    """
    1. 生成查询向量
    2. 构建查询参数（可选主题过滤）
    3. 执行向量检索
    4. 过滤相似度低于阈值的结果
    5. 返回文档列表
    """
```

---

## 3. 数据流与工作流

### 3.1 完整请求处理流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 意图识别 (IntentAgent)                                    │
│    - 快速危机检测                                             │
│    - LLM意图分类                                              │
│    - 主题识别                                                 │
└─────────────────────────────────────────────────────────────┘
    │
    │ intent, topics, need_rag
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 危机检测 (SkillAgent → CrisisDetectorSkill)               │
│    - 关键词匹配                                               │
│    - 风险等级评估                                             │
│    - 生成干预建议                                             │
└─────────────────────────────────────────────────────────────┘
    │
    │ risk_level, intervention
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 工作流选择 (WorkflowSelector)                              │
│    - 根据危机等级选择工作流                                    │
│    - 根据意图类型选择工作流                                    │
│    - 返回工作流ID                                             │
└─────────────────────────────────────────────────────────────┘
    │
    │ workflow_id
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 知识检索 (RAGAgent)                                        │
│    - 生成查询向量                                             │
│    - 向量相似度检索                                           │
│    - 主题过滤                                                 │
│    - 合并上下文                                               │
└─────────────────────────────────────────────────────────────┘
    │
    │ documents, context_text
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 响应生成 (ResponseAgent)                                   │
│    - 选择提示词模板                                           │
│    - 构建LLM输入                                              │
│    - 调用DeepSeek生成回复                                     │
│    - 提取来源信息                                             │
└─────────────────────────────────────────────────────────────┘
    │
    │ response
    ▼
返回给用户
```

### 3.2 工作流示例

#### 日常咨询工作流

```python
daily_counseling_workflow = WorkflowDefinition(
    workflow_id="daily_counseling",
    name="日常心理咨询",
    steps=[
        WorkflowStep(
            name="intent_recognition",
            agent="intent_agent",
            input_mapping={
                "user_message": "$user_message",
                "conversation_history": "$history"
            },
            output_key="intent_result"
        ),
        WorkflowStep(
            name="knowledge_retrieval",
            agent="rag_agent",
            input_mapping={
                "query": "$user_message",
                "topics": "$intent_result.topics"
            },
            output_key="rag_result",
            condition="intent_result.need_rag == True"
        ),
        WorkflowStep(
            name="response_generation",
            agent="response_agent",
            input_mapping={
                "user_message": "$user_message",
                "rag_context": "$rag_result.context_text",
                "conversation_history": "$history"
            },
            output_key="response"
        )
    ]
)
```

#### 危机干预工作流

```python
crisis_workflow = WorkflowDefinition(
    workflow_id="crisis_intervention",
    name="危机干预",
    steps=[
        WorkflowStep(
            name="crisis_detection",
            agent="skill_agent",
            input_mapping={
                "skill_calls": [{"skill": "crisis_detector", 
                                "params": {"text": "$user_message"}}]
            },
            output_key="crisis_result"
        ),
        WorkflowStep(
            name="crisis_response",
            agent="response_agent",
            input_mapping={
                "user_message": "$user_message",
                "skill_results": {"crisis_detector": "$crisis_result"},
                "mode": "crisis"
            },
            output_key="response"
        )
    ]
)
```

---

## 4. API接口文档

### 4.1 Web API

**基础URL**: `http://localhost:8000`

#### 聊天接口

**POST** `/chat`

请求:
```
Content-Type: application/x-www-form-urlencoded

message=你好，我最近感觉很焦虑&user_id=default
```

响应:
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

#### 获取Agent状态

**GET** `/agents/status`

响应:
```json
{
    "agents": [
        {
            "name": "intent_agent",
            "status": "idle",
            "execution_count": 10
        }
    ]
}
```

#### 获取MCP工具列表

**GET** `/mcp/tools`

响应:
```json
{
    "servers": {
        "filesystem": ["read_file", "write_file", "list_files", "delete_file"],
        "database": ["query_user_history", "save_conversation", "log_crisis_event"],
        "search": ["search", "get_resources_by_topic"]
    }
}
```

#### 获取Skill列表

**GET** `/skills`

响应:
```json
{
    "skills": [
        {"name": "emotion_analyzer", "description": "分析用户输入的情绪倾向和强度"},
        {"name": "crisis_detector", "description": "检测用户输入中的危机信号和风险等级"}
    ]
}
```

#### 获取知识库信息

**GET** `/knowledge/info`

响应:
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

### 5.1 配置文件

**文件**: `config/settings.py`

#### API配置

```python
# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "your-api-key")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 阿里云百炼 Embedding
ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "your-api-key")
EMBEDDING_MODEL = "text-embedding-v4"
```

#### 存储配置

```python
# ChromaDB
CHROMA_DB_PATH = "./storage/chroma_db"
COLLECTION_NAME = "psychology_knowledge"

# SQLite
DATABASE_PATH = "./storage/psychology.db"

# 搜索引擎
SEARCH_INDEX_PATH = "./storage/search_index"
```

#### 检索配置

```python
TOP_K_RESULTS = 6              # 返回文档数量
SIMILARITY_THRESHOLD = 0.15    # 相似度阈值
CHUNK_SIZE = 400               # 文档块大小
CHUNK_OVERLAP = 50             # 块重叠大小
```

#### Agent配置

```python
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
# DeepSeek API
DEEPSEEK_API_KEY=your-deepseek-api-key

# 阿里云百炼 API
ALIBABA_API_KEY=your-alibaba-api-key
```

---

## 6. 扩展指南

### 6.1 添加新Agent

**步骤**:

1. 创建Agent文件 `agents/my_agent.py`:

```python
from agents.base_agent import BaseAgent, AgentResult

class MyAgent(BaseAgent):
    def __init__(self, config: Dict = None):
        super().__init__("MyAgent", config)
    
    async def execute(self, context: Dict) -> AgentResult:
        # 实现你的逻辑
        result_data = {"my_result": "value"}
        
        return AgentResult(
            success=True,
            data=result_data
        )
```

2. 在 `agents/__init__.py` 中导出:

```python
from .my_agent import MyAgent

__all__ = [..., "MyAgent"]
```

3. 在系统中使用:

```python
agents = {
    "my_agent": MyAgent(),
    # ...
}
```

### 6.2 添加新Skill

**步骤**:

1. 创建Skill文件 `skills/my_skill.py`:

```python
from skills.skill_base import BaseSkill

class MySkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="my_skill",
            description="我的自定义技能"
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 实现技能逻辑
        return {
            "success": True,
            "result": "..."
        }
```

2. 注册Skill:

```python
from skills import SkillRegistry, MySkill

registry = SkillRegistry()
registry.register(MySkill())
```

### 6.3 添加新MCP服务器

**步骤**:

1. 创建MCP文件 `mcp/my_mcp.py`:

```python
from mcp.mcp_gateway import MCPServer

class MyMCP(MCPServer):
    @property
    def name(self) -> str:
        return "my_mcp"
    
    async def list_tools(self) -> List[Dict]:
        return [
            {
                "name": "my_tool",
                "description": "工具描述",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    }
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "my_tool":
            # 实现工具逻辑
            return {"success": True, "result": "..."}
```

2. 注册服务器:

```python
from mcp import MCPGateway, MyMCP

gateway = MCPGateway()
gateway.register_server(MyMCP())
```

### 6.4 添加新工作流

```python
from orchestration import WorkflowDefinition, WorkflowStep

my_workflow = WorkflowDefinition(
    workflow_id="my_workflow",
    name="自定义工作流",
    description="工作流描述",
    steps=[
        WorkflowStep(
            name="step1",
            agent="intent_agent",
            input_mapping={"user_message": "$user_message"},
            output_key="intent"
        ),
        WorkflowStep(
            name="step2",
            agent="my_agent",
            input_mapping={"data": "$intent"},
            output_key="result"
        )
    ],
    trigger_intents=["some_intent"],
    trigger_keywords=["关键词"]
)

orchestrator.register_workflow(my_workflow)
```

---

## 附录

### A. 错误处理

**Agent错误处理**:
```python
try:
    result = await agent.run(context)
    if not result.success:
        # 处理失败
        logger.error(f"Agent failed: {result.error}")
except Exception as e:
    # 处理异常
    logger.exception(f"Agent exception: {e}")
```

**降级策略**:
- IntentAgent失败 → 返回默认意图
- RAGAgent失败 → 无上下文生成
- SkillAgent失败 → 跳过技能分析
- ResponseAgent失败 → 返回友好错误消息

### B. 性能优化

1. **Embedding缓存**: 考虑对相同文本的Embedding进行缓存
2. **批量处理**: 多文档批量生成Embedding
3. **并行执行**: SkillAgent并行执行多个Skill
4. **连接池**: 复用HTTP连接

### C. 安全考虑

1. **API密钥**: 使用环境变量，不要硬编码
2. **输入验证**: 验证所有用户输入
3. **错误信息**: 不要泄露敏感信息
4. **日志脱敏**: 不记录敏感数据

---

*文档版本: 1.0.0*
*最后更新: 2026-04-10*
*作者: SixpenniesS*

# PsyChat-Pro 开发文档

> Author: SixpenniesS
> Version: 1.0.0
> Date: 2026-04-10
> Project: 多智能体心理咨询系统 - 面试展示项目

---

## 目录

1. [项目概述](#1-项目概述)
2. [架构设计](#2-架构设计)
3. [模块详细设计](#3-模块详细设计)
4. [接口定义](#4-接口定义)
5. [数据流设计](#5-数据流设计)
6. [工作流定义](#6-工作流定义)
7. [MCP集成设计](#7-mcp集成设计)
8. [Skill系统设计](#8-skill系统设计)
9. [实施计划](#9-实施计划)
10. [技术要点与面试亮点](#10-技术要点与面试亮点)

---

## 1. 项目概述

### 1.1 项目背景

基于现有PsyChat单Agent系统，升级为多智能体协作系统，展示以下技术能力：

- **多智能体编排**：5个专业Agent分工协作
- **工作流引擎**：轻量级状态机，支持多种心理咨询场景
- **MCP服务器集成**：文件系统、数据库、搜索引擎
- **Skill系统**：心理专用技能模块

### 1.2 项目目标

为阿里AI应用研发工程师面试提供可展示的工程化项目，重点展示：
- 多Agent协作架构设计能力
- MCP协议理解和实践能力
- Skill系统设计能力
- 完整的工程化实践

### 1.3 技术栈

| 层级 | 技术选型 |
|------|----------|
| LLM | DeepSeek API |
| Embedding | 阿里云百炼 text-embedding-v4 |
| 向量数据库 | ChromaDB |
| Web框架 | FastAPI + Uvicorn |
| MCP实现 | Python + JSON-RPC |
| 数据库 | SQLite |
| 搜索引擎 | Whoosh (轻量级全文检索) |

---

## 2. 架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户层                                        │
│                     Web界面 (FastAPI + HTML/CSS/JS)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API网关层                                       │
│                    /chat, /workflow/status, /mcp/tools                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        工作流调度层                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    WorkflowOrchestrator                          │   │
│  │  - select_workflow(query) → 选择工作流                           │   │
│  │  - execute_workflow(workflow_id, context) → 执行工作流           │   │
│  │  - get_status() → 获取工作流状态                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│         ┌────────────────────┼────────────────────┐                    │
│         ▼                    ▼                    ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │ 心理评估工作流 │    │ 日常咨询工作流 │    │ 危机干预工作流 │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Agent执行层                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │意图识别 │  │RAG检索  │  │工具调用 │  │技能执行 │  │响应生成 │     │
│  │ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│       │            │            │            │            │            │
│       └────────────┴────────────┴────────────┴────────────┘            │
│                              │                                          │
└──────────────────────────────│──────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   MCP网关    │      │  Skill仓库   │      │   核心层     │
│              │      │              │      │              │
│ - 文件系统   │      │ - 情绪分析   │      │ - VectorStore│
│ - 数据库     │      │ - 危机检测   │      │ - RAGSystem  │
│ - 搜索引擎   │      │ - 进展记录   │      │ - TTSService │
│              │      │ - 资源查找   │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

### 2.2 数据流向

```
用户输入 → 意图识别Agent → 工作流选择 → Agent协作执行 → 结果聚合 → 响应输出
                │                              │
                └──────────────────────────────┘
                      (状态同步到Web界面)
```

### 2.3 核心设计原则

1. **单一职责**：每个Agent只负责一个专业领域
2. **松耦合**：Agent通过消息传递协作，不直接依赖
3. **可扩展**：新增Agent/Skill/MCP只需实现标准接口
4. **可观测**：工作流状态实时暴露给Web界面

---

## 3. 模块详细设计

### 3.1 Agent层设计

#### 3.1.1 Agent基类

```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = None  # 用于追踪和调试

class BaseAgent(ABC):
    """Agent基类，定义统一接口"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行Agent核心逻辑"""
        pass
    
    def update_status(self, status: AgentStatus):
        """更新Agent状态"""
        self.status = status
    
    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "status": self.status.value,
            "config": self.config
        }
```

#### 3.1.2 意图识别Agent

```python
# agents/intent_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult
from enum import Enum

class IntentType(Enum):
    MENTAL_ASSESSMENT = "mental_assessment"  # 心理评估
    DAILY_COUNSELING = "daily_counseling"    # 日常咨询
    CRISIS_INTERVENTION = "crisis_intervention"  # 危机干预
    SIMPLE_CHAT = "simple_chat"              # 简单闲聊

class IntentAgent(BaseAgent):
    """意图识别Agent：分析用户输入，决定工作流类型"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("IntentAgent", config)
        self.llm_client = None  # DeepSeek API客户端
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        输入: context = {"user_message": str, "conversation_history": List[Dict]}
        输出: {"intent": IntentType, "topics": List[str], "confidence": float}
        """
        user_message = context.get("user_message", "")
        history = context.get("conversation_history", [])
        
        # 1. 调用LLM进行意图分类
        intent_result = await self._classify_intent(user_message, history)
        
        return AgentResult(
            success=True,
            data=intent_result,
            metadata={"agent": self.name, "input_length": len(user_message)}
        )
    
    async def _classify_intent(self, message: str, history: List) -> Dict:
        """调用LLM进行意图分类"""
        # 实现细节：构造prompt，调用DeepSeek API
        pass
```

#### 3.1.3 RAG检索Agent

```python
# agents/rag_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult

class RAGAgent(BaseAgent):
    """RAG检索Agent：专职向量检索和上下文构建"""
    
    def __init__(self, vector_store, config: Dict[str, Any] = None):
        super().__init__("RAGAgent", config)
        self.vector_store = vector_store
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        输入: context = {"query": str, "topics": List[str], "top_k": int}
        输出: {"documents": List[Dict], "context_text": str, "expanded_contexts": List}
        """
        query = context.get("query", "")
        topics = context.get("topics", [])
        top_k = context.get("top_k", 6)
        
        # 1. 多查询词检索
        documents = await self._multi_query_search(query, topics, top_k)
        
        # 2. 上下文扩展（回溯完整对话）
        expanded = await self._expand_context(documents)
        
        # 3. 构建上下文文本
        context_text = self._build_context_text(documents)
        
        return AgentResult(
            success=True,
            data={
                "documents": documents,
                "context_text": context_text,
                "expanded_contexts": expanded
            }
        )
```

#### 3.1.4 工具调用Agent

```python
# agents/tool_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult

class ToolAgent(BaseAgent):
    """工具调用Agent：统一管理MCP工具调用"""
    
    def __init__(self, mcp_gateway, config: Dict[str, Any] = None):
        super().__init__("ToolAgent", config)
        self.mcp_gateway = mcp_gateway  # MCP网关
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        输入: context = {"tool_calls": List[Dict]}
        输出: {"tool_results": List[Dict]}
        
        tool_call格式: {"server": "filesystem", "tool": "read_file", "params": {...}}
        """
        tool_calls = context.get("tool_calls", [])
        results = []
        
        for call in tool_calls:
            result = await self.mcp_gateway.call_tool(
                server=call["server"],
                tool=call["tool"],
                params=call.get("params", {})
            )
            results.append(result)
        
        return AgentResult(
            success=True,
            data={"tool_results": results}
        )
```

#### 3.1.5 技能执行Agent

```python
# agents/skill_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult

class SkillAgent(BaseAgent):
    """技能执行Agent：管理Skill注册和执行"""
    
    def __init__(self, skill_registry, config: Dict[str, Any] = None):
        super().__init__("SkillAgent", config)
        self.skill_registry = skill_registry
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        输入: context = {"skill_calls": List[Dict]}
        输出: {"skill_results": List[Dict]}
        
        skill_call格式: {"skill": "emotion_analyzer", "params": {...}}
        """
        skill_calls = context.get("skill_calls", [])
        results = []
        
        for call in skill_calls:
            skill = self.skill_registry.get_skill(call["skill"])
            if skill:
                result = await skill.execute(call.get("params", {}))
                results.append({
                    "skill": call["skill"],
                    "result": result
                })
        
        return AgentResult(
            success=True,
            data={"skill_results": results}
        )
```

#### 3.1.6 响应生成Agent

```python
# agents/response_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult

class ResponseAgent(BaseAgent):
    """响应生成Agent：整合信息，生成最终回答"""
    
    def __init__(self, llm_client, config: Dict[str, Any] = None):
        super().__init__("ResponseAgent", config)
        self.llm_client = llm_client
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        输入: context = {
            "user_message": str,
            "rag_context": str,
            "skill_results": Dict,
            "tool_results": Dict,
            "conversation_history": List
        }
        输出: {"response": str, "sources": List}
        """
        # 1. 构建提示词
        prompt = self._build_prompt(context)
        
        # 2. 调用LLM生成回答
        response = await self.llm_client.generate(prompt)
        
        # 3. 提取来源信息
        sources = self._extract_sources(context)
        
        return AgentResult(
            success=True,
            data={
                "response": response,
                "sources": sources
            }
        )
```

### 3.2 工作流调度层设计

#### 3.2.1 工作流调度器

```python
# orchestration/workflow_orchestrator.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    name: str
    agent: str
    input_mapping: Dict[str, str]  # 从上下文映射输入
    output_key: str  # 输出存储到上下文的key
    condition: Optional[str] = None  # 执行条件

@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    workflow_id: str
    status: WorkflowStatus
    current_step: int
    steps: List[WorkflowStep]
    context: Dict[str, Any]
    step_results: List[Dict]
    started_at: datetime
    completed_at: Optional[datetime] = None

class WorkflowOrchestrator:
    """工作流调度器"""
    
    def __init__(self, agents: Dict[str, 'BaseAgent']):
        self.agents = agents
        self.workflows = {}  # 工作流定义注册表
        self.executions = {}  # 执行实例缓存
    
    def register_workflow(self, workflow_id: str, steps: List[WorkflowStep]):
        """注册工作流定义"""
        self.workflows[workflow_id] = steps
    
    async def execute(self, workflow_id: str, initial_context: Dict) -> WorkflowExecution:
        """执行工作流"""
        steps = self.workflows.get(workflow_id)
        if not steps:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            current_step=0,
            steps=steps,
            context=initial_context,
            step_results=[],
            started_at=datetime.now()
        )
        
        self.executions[f"{workflow_id}_{execution.started_at.timestamp()}"] = execution
        
        try:
            for i, step in enumerate(steps):
                execution.current_step = i
                
                # 检查执行条件
                if step.condition and not self._evaluate_condition(step.condition, execution.context):
                    continue
                
                # 获取Agent
                agent = self.agents.get(step.agent)
                if not agent:
                    raise ValueError(f"Agent {step.agent} not found")
                
                # 构建输入
                step_input = self._map_input(step.input_mapping, execution.context)
                
                # 执行Agent
                result = await agent.execute(step_input)
                
                # 存储结果
                execution.context[step.output_key] = result.data
                execution.step_results.append({
                    "step": step.name,
                    "agent": step.agent,
                    "success": result.success,
                    "data": result.data
                })
            
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            raise
        
        return execution
    
    def get_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取工作流执行状态"""
        return self.executions.get(execution_id)
    
    def _map_input(self, mapping: Dict[str, str], context: Dict) -> Dict:
        """从上下文映射输入"""
        return {k: context.get(v) for k, v in mapping.items() if context.get(v) is not None}
    
    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """评估执行条件"""
        # 简单的条件评估，支持基本的布尔表达式
        try:
            return eval(condition, {"__builtins__": {}}, context)
        except:
            return False
```

#### 3.2.2 工作流定义

**心理评估工作流** (config/workflows/mental_assessment.yaml):

```yaml
id: mental_assessment
name: 心理评估工作流
trigger:
  intents: [mental_assessment]
  keywords: [评估, 测试, 量表, 检查]

steps:
  - name: 意图确认
    agent: intent_agent
    input_mapping:
      user_message: user_message
      conversation_history: conversation_history
    output_key: intent_result

  - name: 情绪分析
    agent: skill_agent
    input_mapping:
      skill_calls: 
        - skill: emotion_analyzer
          params:
            text: user_message
    output_key: emotion_result

  - name: 知识检索
    agent: rag_agent
    input_mapping:
      query: user_message
      topics: intent_result.topics
    output_key: rag_result

  - name: 用户历史查询
    agent: tool_agent
    input_mapping:
      tool_calls:
        - server: database
          tool: query_user_history
          params:
            user_id: user_id
    output_key: user_history

  - name: 危机检测
    agent: skill_agent
    input_mapping:
      skill_calls:
        - skill: crisis_detector
          params:
            text: user_message
            history: conversation_history
    output_key: crisis_result

  - name: 生成评估报告
    agent: response_agent
    input_mapping:
      user_message: user_message
      rag_context: rag_result.context_text
      skill_results:
        emotion: emotion_result
        crisis: crisis_result
      tool_results:
        user_history: user_history
      conversation_history: conversation_history
    output_key: final_response

  - name: 保存报告
    agent: tool_agent
    input_mapping:
      tool_calls:
        - server: filesystem
          tool: write_file
          params:
            path: "reports/{user_id}_{timestamp}.md"
            content: final_response.response
    output_key: save_result
```

**日常咨询工作流** (config/workflows/daily_counseling.yaml):

```yaml
id: daily_counseling
name: 日常咨询工作流
trigger:
  intents: [daily_counseling]
  keywords: [咨询, 怎么办, 如何, 帮助]

steps:
  - name: 意图确认
    agent: intent_agent
    input_mapping:
      user_message: user_message
      conversation_history: conversation_history
    output_key: intent_result

  - name: 知识检索
    agent: rag_agent
    input_mapping:
      query: user_message
      topics: intent_result.topics
    output_key: rag_result
    condition: intent_result.need_rag == True

  - name: 生成回答
    agent: response_agent
    input_mapping:
      user_message: user_message
      rag_context: rag_result.context_text
      conversation_history: conversation_history
    output_key: final_response
```

**危机干预工作流** (config/workflows/crisis_intervention.yaml):

```yaml
id: crisis_intervention
name: 危机干预工作流
trigger:
  intents: [crisis_intervention]
  keywords: [自杀, 自残, 不想活, 结束生命]

steps:
  - name: 危机评估
    agent: skill_agent
    input_mapping:
      skill_calls:
        - skill: crisis_detector
          params:
            text: user_message
            history: conversation_history
            deep_analysis: true
    output_key: crisis_assessment

  - name: 紧急资源检索
    agent: rag_agent
    input_mapping:
      query: "危机干预 紧急求助"
      topics: ["危机", "治疗"]
    output_key: emergency_resources

  - name: 危机干预响应
    agent: response_agent
    input_mapping:
      user_message: user_message
      rag_context: emergency_resources.context_text
      skill_results:
        crisis: crisis_assessment
      mode: crisis
    output_key: final_response

  - name: 记录危机事件
    agent: tool_agent
    input_mapping:
      tool_calls:
        - server: database
          tool: log_crisis_event
          params:
            user_id: user_id
            assessment: crisis_assessment
            timestamp: timestamp
    output_key: log_result
```

### 3.3 MCP集成层设计

#### 3.3.1 MCP网关

```python
# mcp/mcp_gateway.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class MCPServer(ABC):
    """MCP服务器基类"""
    
    @abstractmethod
    async def list_tools(self) -> List[Dict]:
        """列出可用工具"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict) -> Dict:
        """调用工具"""
        pass

class MCPGateway:
    """MCP网关：统一管理多个MCP服务器"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
    
    def register_server(self, name: str, server: MCPServer):
        """注册MCP服务器"""
        self.servers[name] = server
    
    async def list_all_tools(self) -> Dict[str, List[Dict]]:
        """列出所有服务器的工具"""
        result = {}
        for name, server in self.servers.items():
            result[name] = await server.list_tools()
        return result
    
    async def call_tool(self, server: str, tool: str, params: Dict) -> Dict:
        """调用指定服务器的工具"""
        if server not in self.servers:
            raise ValueError(f"MCP server '{server}' not found")
        return await self.servers[server].call_tool(tool, params)
```

#### 3.3.2 文件系统MCP

```python
# mcp/filesystem_mcp.py
import os
import json
from typing import Dict, Any, List
from mcp.mcp_gateway import MCPServer
from pathlib import Path

class FilesystemMCP(MCPServer):
    """文件系统MCP服务器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def list_tools(self) -> List[Dict]:
        return [
            {
                "name": "read_file",
                "description": "读取文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "写入文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_files",
                "description": "列出目录中的文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "目录路径"}
                    }
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "read_file":
            return await self._read_file(params["path"])
        elif tool_name == "write_file":
            return await self._write_file(params["path"], params["content"])
        elif tool_name == "list_files":
            return await self._list_files(params.get("path", ""))
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _read_file(self, path: str) -> Dict:
        file_path = self.base_path / path
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _write_file(self, path: str, content: str) -> Dict:
        file_path = self.base_path / path
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_files(self, path: str) -> Dict:
        dir_path = self.base_path / path if path else self.base_path
        try:
            files = list(dir_path.iterdir())
            return {
                "success": True,
                "files": [{"name": f.name, "is_dir": f.is_dir()} for f in files]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

#### 3.3.3 数据库MCP

```python
# mcp/database_mcp.py
import sqlite3
import json
from typing import Dict, Any, List
from mcp.mcp_gateway import MCPServer
from datetime import datetime

class DatabaseMCP(MCPServer):
    """SQLite数据库MCP服务器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # 对话历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                message TEXT,
                response TEXT,
                workflow_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 危机事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crisis_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                assessment TEXT,
                handled BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def list_tools(self) -> List[Dict]:
        return [
            {
                "name": "query_user_history",
                "description": "查询用户对话历史",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "save_conversation",
                "description": "保存对话记录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "message": {"type": "string"},
                        "response": {"type": "string"},
                        "workflow_id": {"type": "string"}
                    },
                    "required": ["user_id", "message", "response"]
                }
            },
            {
                "name": "log_crisis_event",
                "description": "记录危机事件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "assessment": {"type": "object"}
                    },
                    "required": ["user_id", "assessment"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "query_user_history":
            return await self._query_user_history(params["user_id"], params.get("limit", 10))
        elif tool_name == "save_conversation":
            return await self._save_conversation(params)
        elif tool_name == "log_crisis_event":
            return await self._log_crisis_event(params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _query_user_history(self, user_id: str, limit: int) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message, response, created_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            history = [{"message": r[0], "response": r[1], "time": r[2]} for r in rows]
            return {"success": True, "history": history}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _save_conversation(self, params: Dict) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (user_id, message, response, workflow_id) VALUES (?, ?, ?, ?)",
                (params["user_id"], params["message"], params["response"], params.get("workflow_id"))
            )
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _log_crisis_event(self, params: Dict) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO crisis_events (user_id, assessment) VALUES (?, ?)",
                (params["user_id"], json.dumps(params["assessment"]))
            )
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

#### 3.3.4 搜索引擎MCP

```python
# mcp/search_mcp.py
from typing import Dict, Any, List
from mcp.mcp_gateway import MCPServer
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import os

class SearchMCP(MCPServer):
    """搜索引擎MCP服务器 (基于Whoosh)"""
    
    def __init__(self, index_path: str, knowledge_dir: str):
        self.index_path = index_path
        self.knowledge_dir = knowledge_dir
        self._init_index()
    
    def _init_index(self):
        """初始化搜索索引"""
        schema = Schema(
            id=ID(stored=True),
            title=TEXT(stored=True),
            content=TEXT(stored=True),
            source=TEXT(stored=True)
        )
        
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)
        
        if not exists_in(self.index_path):
            ix = create_in(self.index_path, schema)
            self._index_documents(ix)
    
    def _index_documents(self, ix):
        """索引知识库文档"""
        writer = ix.writer()
        # 实现文档索引逻辑
        writer.commit()
    
    async def list_tools(self) -> List[Dict]:
        return [
            {
                "name": "search",
                "description": "搜索心理学资源",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "search":
            return await self._search(params["query"], params.get("limit", 10))
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _search(self, query: str, limit: int) -> Dict:
        try:
            ix = open_dir(self.index_path)
            with ix.searcher() as searcher:
                parser = QueryParser("content", ix.schema)
                q = parser.parse(query)
                results = searcher.search(q, limit=limit)
                
                return {
                    "success": True,
                    "results": [
                        {"title": r["title"], "content": r["content"], "source": r["source"]}
                        for r in results
                    ]
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 3.4 Skill系统设计

#### 3.4.1 Skill基类

```python
# skills/skill_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSkill(ABC):
    """Skill基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        pass
    
    def get_info(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description
        }
```

#### 3.4.2 情绪分析Skill

```python
# skills/emotion_analyzer.py
from skills.skill_base import BaseSkill
from typing import Dict, Any, List

class EmotionAnalyzerSkill(BaseSkill):
    """情绪分析技能"""
    
    # 情绪关键词词典
    EMOTION_KEYWORDS = {
        "焦虑": ["焦虑", "紧张", "担心", "不安", "害怕", "恐惧", "慌张"],
        "抑郁": ["抑郁", "沮丧", "绝望", "无助", "悲伤", "消沉", "低落"],
        "愤怒": ["愤怒", "生气", "恼火", "烦躁", "不满", "怨恨"],
        "恐惧": ["恐惧", "害怕", "惊恐", "胆怯", "畏惧"],
        "孤独": ["孤独", "寂寞", "孤单", "无人理解", "被孤立"],
        "自卑": ["自卑", "没用", "不如人", "不自信", "自责"]
    }
    
    def __init__(self):
        super().__init__(
            name="emotion_analyzer",
            description="分析用户输入的情绪倾向和强度"
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("text", "")
        
        # 1. 检测情绪类型
        detected_emotions = self._detect_emotions(text)
        
        # 2. 分析情绪强度
        intensity = self._analyze_intensity(text, detected_emotions)
        
        # 3. 整体情感极性
        polarity = self._analyze_polarity(text)
        
        return {
            "emotions": detected_emotions,
            "intensity": intensity,
            "polarity": polarity,
            "summary": self._generate_summary(detected_emotions, intensity, polarity)
        }
    
    def _detect_emotions(self, text: str) -> List[Dict]:
        detected = []
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                detected.append({
                    "emotion": emotion,
                    "keyword_count": count,
                    "confidence": min(count / len(keywords) * 2, 1.0)
                })
        return sorted(detected, key=lambda x: x["confidence"], reverse=True)
    
    def _analyze_intensity(self, text: str, emotions: List) -> float:
        # 基于情绪词数量和程度副词估算强度
        intensity_words = ["非常", "极其", "特别", "很", "太"]
        base_intensity = sum(e["keyword_count"] for e in emotions)
        modifier = 1.0
        
        for word in intensity_words:
            if word in text:
                modifier += 0.3
        
        return min(base_intensity * modifier / 5, 1.0)
    
    def _analyze_polarity(self, text: str) -> str:
        positive_words = ["好", "开心", "快乐", "幸福", "满足", "希望"]
        negative_words = ["不好", "难过", "痛苦", "绝望", "失败", "崩溃"]
        
        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
    
    def _generate_summary(self, emotions, intensity, polarity) -> str:
        if not emotions:
            return "未检测到明显情绪"
        
        main_emotion = emotions[0]["emotion"]
        intensity_desc = "强烈" if intensity > 0.7 else "中等" if intensity > 0.4 else "轻微"
        
        return f"检测到{intensity_desc}的{main_emotion}情绪"
```

#### 3.4.3 危机检测Skill

```python
# skills/crisis_detector.py
from skills.skill_base import BaseSkill
from typing import Dict, Any, List

class CrisisDetectorSkill(BaseSkill):
    """危机检测技能"""
    
    # 危机信号关键词（按严重程度分级）
    CRISIS_LEVELS = {
        "critical": {
            "keywords": ["自杀", "想死", "不想活", "结束生命", "杀自己"],
            "score": 10
        },
        "high": {
            "keywords": ["自残", "伤害自己", "没有希望", "活不下去", "绝望"],
            "score": 7
        },
        "medium": {
            "keywords": ["痛苦", "崩溃", "无法承受", "撑不下去", "彻底失败"],
            "score": 4
        },
        "low": {
            "keywords": ["困难", "挣扎", "迷茫", "无助", "孤独"],
            "score": 2
        }
    }
    
    def __init__(self):
        super().__init__(
            name="crisis_detector",
            description="检测用户输入中的危机信号和风险等级"
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("text", "")
        history = params.get("history", [])
        deep_analysis = params.get("deep_analysis", False)
        
        # 1. 关键词检测
        keyword_result = self._detect_keywords(text)
        
        # 2. 上下文分析（结合历史）
        context_score = self._analyze_context(text, history)
        
        # 3. 综合风险评估
        risk_level, risk_score = self._calculate_risk(keyword_result, context_score)
        
        # 4. 生成干预建议
        intervention = self._generate_intervention(risk_level, risk_score)
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "detected_signals": keyword_result["signals"],
            "intervention_needed": risk_level in ["critical", "high"],
            "intervention_suggestion": intervention
        }
    
    def _detect_keywords(self, text: str) -> Dict:
        signals = []
        total_score = 0
        
        for level, config in self.CRISIS_LEVELS.items():
            for keyword in config["keywords"]:
                if keyword in text:
                    signals.append({
                        "keyword": keyword,
                        "level": level,
                        "score": config["score"]
                    })
                    total_score += config["score"]
        
        return {"signals": signals, "score": total_score}
    
    def _analyze_context(self, text: str, history: List) -> float:
        # 分析历史对话中的负面情绪累积
        if not history:
            return 0
        
        negative_trend = 0
        for msg in history[-5:]:  # 最近5轮对话
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if any(kw in content for level in self.CRISIS_LEVELS.values() for kw in level["keywords"]):
                    negative_trend += 0.5
        
        return min(negative_trend, 3.0)
    
    def _calculate_risk(self, keyword_result: Dict, context_score: float) -> tuple:
        total_score = keyword_result["score"] + context_score
        
        if total_score >= 10:
            return "critical", total_score
        elif total_score >= 7:
            return "high", total_score
        elif total_score >= 4:
            return "medium", total_score
        else:
            return "low", total_score
    
    def _generate_intervention(self, risk_level: str, score: float) -> str:
        if risk_level == "critical":
            return "需要立即进行危机干预，建议转介专业机构，提供紧急求助热线"
        elif risk_level == "high":
            return "需要重点关注，建议深入探讨问题根源，提供专业资源"
        elif risk_level == "medium":
            return "需要关注用户情绪状态，提供情感支持和适当建议"
        return "常规咨询流程即可"
```

#### 3.4.4 进展记录Skill

```python
# skills/progress_recorder.py
from skills.skill_base import BaseSkill
from typing import Dict, Any
from datetime import datetime

class ProgressRecorderSkill(BaseSkill):
    """咨询进展记录技能"""
    
    def __init__(self, filesystem_mcp=None):
        super().__init__(
            name="progress_recorder",
            description="记录和追踪咨询进展"
        )
        self.filesystem_mcp = filesystem_mcp
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "record")
        
        if action == "record":
            return await self._record_progress(params)
        elif action == "query":
            return await self._query_progress(params)
        elif action == "summary":
            return await self._generate_summary(params)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _record_progress(self, params: Dict) -> Dict:
        user_id = params.get("user_id")
        session_data = params.get("session_data", {})
        timestamp = datetime.now().isoformat()
        
        record = {
            "timestamp": timestamp,
            "user_id": user_id,
            "emotions": session_data.get("emotions"),
            "topics_discussed": session_data.get("topics"),
            "key_insights": session_data.get("insights"),
            "next_steps": session_data.get("next_steps")
        }
        
        # 如果有文件系统MCP，保存记录
        if self.filesystem_mcp:
            filename = f"progress/{user_id}/{timestamp[:10]}.json"
            await self.filesystem_mcp.call_tool("write_file", {
                "path": filename,
                "content": json.dumps(record, ensure_ascii=False, indent=2)
            })
        
        return {"success": True, "recorded": record}
    
    async def _query_progress(self, params: Dict) -> Dict:
        # 查询历史进展
        pass
    
    async def _generate_summary(self, params: Dict) -> Dict:
        # 生成进展总结
        pass
```

#### 3.4.5 资源查找Skill

```python
# skills/resource_finder.py
from skills.skill_base import BaseSkill
from typing import Dict, Any, List

class ResourceFinderSkill(BaseSkill):
    """资源查找技能"""
    
    # 预定义资源库
    RESOURCES = {
        "焦虑": [
            {"type": "练习", "name": "腹式呼吸法", "description": "通过深呼吸缓解焦虑"},
            {"type": "练习", "name": "正念冥想", "description": "专注当下，减少担忧"},
            {"type": "书籍", "name": "《焦虑自救手册》", "description": "系统了解和应对焦虑"}
        ],
        "抑郁": [
            {"type": "练习", "name": "行为激活", "description": "通过小目标重建动力"},
            {"type": "练习", "name": "感恩日记", "description": "记录积极事物"},
            {"type": "书籍", "name": "《伯恩斯新情绪疗法》", "description": "认知疗法自助指南"}
        ],
        # ... 更多资源
    }
    
    def __init__(self, search_mcp=None):
        super().__init__(
            name="resource_finder",
            description="查找和推荐心理学相关资源"
        )
        self.search_mcp = search_mcp
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        topics = params.get("topics", [])
        limit = params.get("limit", 5)
        
        # 1. 从预定义资源库匹配
        predefined = self._match_predefined(query, topics)
        
        # 2. 如果有搜索MCP，进行额外搜索
        additional = []
        if self.search_mcp:
            search_result = await self.search_mcp.call_tool("search", {
                "query": query,
                "limit": limit - len(predefined)
            })
            if search_result.get("success"):
                additional = search_result.get("results", [])
        
        return {
            "success": True,
            "resources": predefined + additional[:limit - len(predefined)]
        }
    
    def _match_predefined(self, query: str, topics: List[str]) -> List[Dict]:
        resources = []
        for topic in topics:
            if topic in self.RESOURCES:
                resources.extend(self.RESOURCES[topic])
        
        # 如果没有主题匹配，尝试从查询中匹配
        if not resources:
            for emotion, res in self.RESOURCES.items():
                if emotion in query:
                    resources.extend(res)
        
        return resources
```

---

## 4. 接口定义

### 4.1 Web API接口

```yaml
# API接口定义

# 1. 对话接口
POST /chat
Request:
  message: string  # 用户消息
  user_id: string  # 用户ID（可选）
Response:
  success: boolean
  response: string  # AI回复
  sources: array    # 参考来源
  workflow_info:    # 工作流信息
    workflow_id: string
    steps_completed: integer
    agents_called: array

# 2. 工作流状态接口
GET /workflow/status/{execution_id}
Response:
  workflow_id: string
  status: string  # pending/running/completed/failed
  current_step: integer
  total_steps: integer
  step_results: array

# 3. MCP工具列表接口
GET /mcp/tools
Response:
  servers:
    filesystem:
      - name: read_file
        description: string
        inputSchema: object
      - name: write_file
        ...
    database:
      ...
    search:
      ...

# 4. Skill列表接口
GET /skills
Response:
  skills:
    - name: emotion_analyzer
      description: string
    - name: crisis_detector
      ...

# 5. 知识库信息接口
GET /knowledge/info
Response:
  document_count: integer
  topics: array
```

### 4.2 内部数据结构

```python
# 工作流上下文
WorkflowContext = {
    "user_id": str,
    "user_message": str,
    "conversation_history": List[Dict],
    "timestamp": str,
    
    # 各Agent输出
    "intent_result": Dict,      # 意图识别Agent输出
    "rag_result": Dict,         # RAG检索Agent输出
    "emotion_result": Dict,     # 技能执行Agent输出
    "crisis_result": Dict,      # 危机检测结果
    "final_response": Dict      # 响应生成Agent输出
}

# Agent结果
AgentResult = {
    "success": bool,
    "data": Dict[str, Any],
    "error": Optional[str],
    "metadata": Dict  # 用于追踪
}

# MCP工具调用
ToolCall = {
    "server": str,      # "filesystem" / "database" / "search"
    "tool": str,        # 具体工具名
    "params": Dict      # 参数
}

# Skill调用
SkillCall = {
    "skill": str,       # 技能名
    "params": Dict      # 参数
}
```

---

## 5. 数据流设计

### 5.1 心理评估工作流数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         用户输入: "我感觉很焦虑，想做个评估"                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: 意图识别Agent                                                        │
│   Input: {user_message, conversation_history}                               │
│   Output: {intent: "mental_assessment", topics: ["情绪", "焦虑"]}            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2: 情绪分析Skill                                                        │
│   Input: {text: user_message}                                               │
│   Output: {emotions: [{emotion: "焦虑", confidence: 0.85}], intensity: 0.7}  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3: RAG检索Agent                                                         │
│   Input: {query: user_message, topics: ["情绪", "焦虑"]}                     │
│   Output: {documents: [...], context_text: "参考案例..."}                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 4: 数据库MCP查询                                                        │
│   Input: {user_id}                                                          │
│   Output: {history: [...]}  // 用户历史对话                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 5: 危机检测Skill                                                        │
│   Input: {text: user_message, history: [...]}                               │
│   Output: {risk_level: "low", risk_score: 1}                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 6: 响应生成Agent                                                        │
│   Input: {user_message, rag_context, emotion_result, crisis_result, ...}    │
│   Output: {response: "我理解你感到焦虑...", sources: [...]}                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 7: 文件系统MCP保存报告                                                   │
│   Input: {path: "reports/...", content: response}                           │
│   Output: {success: true}                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         最终响应返回给用户                                     │
│   {response, sources, workflow_info: {steps_completed: 7, ...}}             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 危机干预工作流数据流

```
用户输入包含危机关键词 → 危机检测Skill立即评估 → 风险等级判断
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    ▼                               ▼                               ▼
            risk_level = "critical"         risk_level = "high"           risk_level = "medium/low"
                    │                               │                               │
                    ▼                               ▼                               ▼
        立即转介专业机构                   深入关注+专业资源                  常规咨询流程
        提供紧急热线                       记录危机事件                       情感支持
```

---

## 6. 工作流定义

### 6.1 工作流选择逻辑

```python
# orchestration/workflow_selector.py

def select_workflow(intent_result: Dict, crisis_result: Dict) -> str:
    """根据意图和危机检测结果选择工作流"""
    
    # 1. 优先检查危机信号
    if crisis_result.get("risk_level") in ["critical", "high"]:
        return "crisis_intervention"
    
    # 2. 根据意图选择
    intent = intent_result.get("intent")
    if intent == "mental_assessment":
        return "mental_assessment"
    elif intent == "daily_counseling":
        return "daily_counseling"
    elif intent == "simple_chat":
        return "daily_counseling"  # 简单闲聊也走日常咨询
    
    # 3. 默认日常咨询
    return "daily_counseling"
```

### 6.2 工作流定义文件格式

```yaml
# config/workflows/*.yaml 通用格式

id: workflow_id
name: 工作流名称
description: 工作流描述
trigger:
  intents: [intent1, intent2]
  keywords: [keyword1, keyword2]

steps:
  - name: 步骤名称
    agent: agent_name
    input_mapping:
      param1: context_key1
      param2: context_key2
    output_key: result_key
    condition: 可选的条件表达式

error_handling:
  on_step_fail: continue | abort
  fallback_agent: fallback_agent_name
```

---

## 7. MCP集成设计

### 7.1 MCP架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Gateway                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    list_all_tools()                      │   │
│  │                    call_tool(server, tool, params)       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ FilesystemMCP│    │ DatabaseMCP  │    │  SearchMCP   │     │
│  │              │    │              │    │              │     │
│  │ - read_file  │    │ - query_user │    │ - search     │     │
│  │ - write_file │    │ - save_conv  │    │              │     │
│  │ - list_files │    │ - log_crisis │    │              │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ storage/     │    │  SQLite DB   │    │ Whoosh Index │     │
│  │ reports/     │    │  - users     │    │              │     │
│  │ progress/    │    │  - convs     │    │              │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 MCP工具使用场景

| MCP服务器 | 工具 | 使用场景 |
|-----------|------|----------|
| FilesystemMCP | write_file | 保存心理评估报告 |
| FilesystemMCP | read_file | 读取历史咨询记录 |
| DatabaseMCP | query_user_history | 查询用户历史对话 |
| DatabaseMCP | save_conversation | 保存对话记录 |
| DatabaseMCP | log_crisis_event | 记录危机事件 |
| SearchMCP | search | 搜索心理学资源 |

---

## 8. Skill系统设计

### 8.1 Skill架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                       Skill Registry                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              register_skill(skill)                       │   │
│  │              get_skill(name) → BaseSkill                 │   │
│  │              list_skills() → List[SkillInfo]             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │EmotionAnalyzer│   │CrisisDetector│    │ProgressRecorder│    │
│  │              │    │              │    │              │     │
│  │ - execute()  │    │ - execute()  │    │ - execute()  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│    情绪词典            危机关键词库           MCP集成          │
│    强度计算            风险评估              文件存储          │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Skill使用场景

| Skill | 输入 | 输出 | 使用工作流 |
|-------|------|------|-----------|
| emotion_analyzer | 用户文本 | 情绪类型、强度、极性 | 心理评估 |
| crisis_detector | 用户文本+历史 | 风险等级、干预建议 | 所有工作流（优先） |
| progress_recorder | 会话数据 | 保存结果 | 心理评估 |
| resource_finder | 主题/关键词 | 资源列表 | 日常咨询 |

---

## 9. 实施计划

### 9.1 开发顺序

```
Day 1: 基础框架
├── 创建项目结构
├── 编写配置模块 (config/settings.py)
├── 实现Agent基类 (agents/base_agent.py)
├── 实现意图识别Agent (agents/intent_agent.py)
├── 实现RAG检索Agent (agents/rag_agent.py)
└── 迁移现有VectorStore和RAGSystem

Day 2: MCP/Skill集成
├── 实现MCP网关 (mcp/mcp_gateway.py)
├── 实现文件系统MCP (mcp/filesystem_mcp.py)
├── 实现数据库MCP (mcp/database_mcp.py)
├── 实现搜索引擎MCP (mcp/search_mcp.py)
├── 实现Skill基类 (skills/skill_base.py)
├── 实现情绪分析Skill (skills/emotion_analyzer.py)
├── 实现危机检测Skill (skills/crisis_detector.py)
├── 实现工具调用Agent (agents/tool_agent.py)
└── 实现技能执行Agent (agents/skill_agent.py)

Day 3: 工作流和界面
├── 实现工作流调度器 (orchestration/workflow_orchestrator.py)
├── 实现3个工作流定义 (config/workflows/*.yaml)
├── 实现响应生成Agent (agents/response_agent.py)
├── 增强Web界面 (web/interface.py)
│   ├── 添加工作流状态面板
│   ├── 显示Agent调用记录
│   └── 显示MCP/Skill使用情况
└── 集成测试

Day 4: 工程化完善
├── 添加单元测试 (tests/)
├── 编写架构文档 (docs/ARCHITECTURE.md)
├── 编写MCP集成文档 (docs/MCP_INTEGRATION.md)
├── 编写README.md
├── 完善错误处理
└── 最终测试和调试
```

### 9.2 文件清单

```
PsyChat-Pro/
├── README.md
├── requirements.txt
├── main.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── workflows/
│       ├── mental_assessment.yaml
│       ├── daily_counseling.yaml
│       └── crisis_intervention.yaml
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── intent_agent.py
│   ├── rag_agent.py
│   ├── tool_agent.py
│   ├── skill_agent.py
│   └── response_agent.py
│
├── orchestration/
│   ├── __init__.py
│   ├── workflow_orchestrator.py
│   └── workflow_selector.py
│
├── mcp/
│   ├── __init__.py
│   ├── mcp_gateway.py
│   ├── filesystem_mcp.py
│   ├── database_mcp.py
│   └── search_mcp.py
│
├── skills/
│   ├── __init__.py
│   ├── skill_base.py
│   ├── skill_registry.py
│   ├── emotion_analyzer.py
│   ├── crisis_detector.py
│   ├── progress_recorder.py
│   └── resource_finder.py
│
├── core/
│   ├── __init__.py
│   ├── vector_store.py      # 从现有项目迁移
│   ├── rag_system.py        # 从现有项目迁移（适配）
│   └── tts_service.py       # 从现有项目迁移
│
├── web/
│   ├── __init__.py
│   ├── interface.py
│   └── templates/
│       └── index.html
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_workflows.py
│   └── test_mcp_skills.py
│
├── docs/
│   ├── DEVELOPMENT.md       # 本文档
│   ├── ARCHITECTURE.md
│   ├── MCP_INTEGRATION.md
│   └── SKILL_DEVELOPMENT.md
│
├── resources/
│   ├── knowledge/           # 知识库文档
│   └── prompts/             # 系统提示词
│
└── storage/
    ├── chroma_db/           # 向量数据库
    ├── reports/             # 评估报告
    ├── progress/            # 进展记录
    └── audio/               # TTS音频
```

---

## 10. 技术要点与面试亮点

### 10.1 多智能体编排

**展示要点：**

1. **Agent专业化分工**
   - 5个专业Agent，每个只负责一个领域
   - 遵循单一职责原则，易于测试和维护

2. **工作流驱动**
   - 工作流定义清晰，可配置
   - 支持条件分支和并行执行
   - 状态可追踪，便于调试

3. **松耦合架构**
   - Agent通过上下文传递数据，不直接依赖
   - 新增Agent只需实现标准接口

**面试话术：**
> "系统采用多Agent协作架构，将单一心理学Agent拆分为意图识别、RAG检索、工具调用、技能执行、响应生成5个专业Agent。通过工作流调度器统一编排，支持心理评估、日常咨询、危机干预等多种场景。Agent间通过上下文传递数据，实现松耦合。"

### 10.2 MCP集成

**展示要点：**

1. **协议理解**
   - 实现了MCP服务器的基本框架
   - 支持工具列表和工具调用

2. **实际落地**
   - 文件系统MCP：保存评估报告
   - 数据库MCP：存储用户档案和对话历史
   - 搜索引擎MCP：检索心理学资源

3. **统一网关**
   - MCPGateway统一管理多个服务器
   - 提供一致的调用接口

**面试话术：**
> "集成MCP协议实现了文件系统、数据库、搜索引擎三个服务器。文件系统MCP用于保存心理评估报告，数据库MCP存储用户档案和对话历史，搜索引擎MCP提供心理学资源检索。通过MCP Gateway统一管理，实现了工具调用的标准化。"

### 10.3 Skill系统

**展示要点：**

1. **领域专用**
   - 情绪分析、危机检测等心理专用Skill
   - 结合心理学专业知识设计

2. **可扩展**
   - Skill基类定义标准接口
   - 新增Skill只需继承并实现execute方法

3. **与MCP结合**
   - Skill可以调用MCP工具
   - 如ProgressRecorder调用文件系统MCP

**面试话术：**
> "设计了Skill系统来封装心理学专业能力，包括情绪分析、危机检测、进展记录、资源查找。Skill系统与MCP集成，例如进展记录Skill调用文件系统MCP保存记录。系统可扩展，新增技能只需实现标准接口。"

### 10.4 工程化实践

**展示要点：**

1. **项目结构清晰**
   - 按功能模块组织代码
   - 配置与代码分离

2. **类型注解**
   - 关键函数使用Python类型提示
   - 便于代码阅读和维护

3. **错误处理**
   - Agent级错误处理和降级
   - 工作流级别的错误恢复

4. **可观测性**
   - 工作流状态实时暴露
   - Web界面显示Agent调用链

**面试话术：**
> "项目采用工程化实践：清晰的模块划分、Python类型注解、完善的错误处理、工作流状态追踪。Web界面可实时展示工作流执行过程和Agent调用记录，便于调试和展示。"

---

## 附录

### A. 配置文件示例

```python
# config/settings.py

# API配置
DEEPSEEK_API_KEY = "your-api-key"
ALIBABA_API_KEY = "your-api-key"

# 存储路径
CHROMA_DB_PATH = "storage/chroma_db"
DATABASE_PATH = "storage/psychology.db"
SEARCH_INDEX_PATH = "storage/search_index"
REPORT_PATH = "storage/reports"

# 检索配置
TOP_K_RESULTS = 6
SIMILARITY_THRESHOLD = 0.15

# 工作流配置
MAX_WORKFLOW_STEPS = 10
WORKFLOW_TIMEOUT = 60

# MCP配置
MCP_SERVERS = {
    "filesystem": {"base_path": "storage"},
    "database": {"db_path": "storage/psychology.db"},
    "search": {"index_path": "storage/search_index"}
}
```

### B. 运行命令

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化知识库
python main.py --rebuild

# 启动Web服务
python main.py

# 运行测试
pytest tests/

# 查看工作流状态
curl http://localhost:8000/workflow/status/{execution_id}
```

---

**文档结束**

> 本文档将作为开发过程中的指导文件，所有代码实现需遵循本文档中的设计规范。

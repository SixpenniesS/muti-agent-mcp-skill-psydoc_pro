# -*- coding: utf-8 -*-
"""
工作流调度器
实现轻量级状态机，支持多种心理咨询场景的工作流编排
Author: SixpenniesS
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤定义

    Attributes:
        name: 步骤名称
        agent: 负责的Agent名称
        input_mapping: 输入映射（从上下文中获取）
        output_key: 输出存储到上下文的key
        condition: 执行条件（可选）
        on_failure: 失败时的处理策略
    """
    name: str
    agent: str
    input_mapping: Dict[str, Any] = field(default_factory=dict)
    output_key: str = ""
    condition: Optional[str] = None
    on_failure: str = "abort"  # "abort" | "continue" | "skip"


@dataclass
class WorkflowDefinition:
    """工作流定义

    Attributes:
        workflow_id: 工作流ID
        name: 工作流名称
        description: 描述
        steps: 步骤列表
        trigger_intents: 触发的意图类型列表
        trigger_keywords: 触发关键词列表
    """
    workflow_id: str
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    trigger_intents: List[str] = field(default_factory=list)
    trigger_keywords: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """工作流执行实例

    Attributes:
        execution_id: 执行ID
        workflow_id: 工作流ID
        status: 当前状态
        current_step: 当前步骤索引
        steps: 步骤列表
        context: 执行上下文
        step_results: 各步骤执行结果
        started_at: 开始时间
        completed_at: 完成时间
        error: 错误信息
    """
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    current_step: int = 0
    steps: List[WorkflowStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于API响应）"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "step_results": self.step_results,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class WorkflowOrchestrator:
    """工作流调度器

    核心功能：
    - 注册和管理多个工作流定义
    - 执行工作流并跟踪状态
    - 提供工作流状态查询接口
    """

    def __init__(self, agents: Dict[str, 'BaseAgent']):
        """初始化工作流调度器

        Args:
            agents: Agent实例字典，key为Agent名称
        """
        self.agents = agents
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.logger = logging.getLogger("workflow.orchestrator")

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """注册工作流定义

        Args:
            workflow: 工作流定义实例
        """
        self.workflows[workflow.workflow_id] = workflow
        self.logger.info(f"注册工作流: {workflow.workflow_id} ({workflow.name})")

    def register_workflow_from_dict(self, workflow_id: str, data: Dict) -> None:
        """从字典注册工作流

        Args:
            workflow_id: 工作流ID
            data: 工作流定义字典
        """
        steps = []
        for step_data in data.get("steps", []):
            step = WorkflowStep(
                name=step_data.get("name", ""),
                agent=step_data.get("agent", ""),
                input_mapping=step_data.get("input_mapping", {}),
                output_key=step_data.get("output_key", ""),
                condition=step_data.get("condition"),
                on_failure=step_data.get("on_failure", "abort")
            )
            steps.append(step)

        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=data.get("name", workflow_id),
            description=data.get("description", ""),
            steps=steps,
            trigger_intents=data.get("trigger", {}).get("intents", []),
            trigger_keywords=data.get("trigger", {}).get("keywords", [])
        )

        self.register_workflow(workflow)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义或None
        """
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[str]:
        """列出所有工作流ID"""
        return list(self.workflows.keys())

    async def execute(
        self,
        workflow_id: str,
        initial_context: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> WorkflowExecution:
        """执行工作流

        Args:
            workflow_id: 工作流ID
            initial_context: 初始上下文
            execution_id: 执行ID（可选，自动生成）

        Returns:
            工作流执行实例
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流 '{workflow_id}' 不存在")

        # 创建执行实例
        execution = WorkflowExecution(
            execution_id=execution_id or str(uuid.uuid4()),
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            steps=workflow.steps,
            context=initial_context.copy()
        )

        self.executions[execution.execution_id] = execution
        self.logger.info(f"开始执行工作流: {workflow_id} (execution_id: {execution.execution_id})")

        try:
            for i, step in enumerate(workflow.steps):
                execution.current_step = i
                self.logger.info(f"执行步骤 {i+1}/{len(workflow.steps)}: {step.name}")

                # 检查执行条件
                if step.condition and not self._evaluate_condition(step.condition, execution.context):
                    self.logger.info(f"步骤 {step.name} 条件不满足，跳过")
                    execution.step_results.append({
                        "step": step.name,
                        "agent": step.agent,
                        "skipped": True,
                        "reason": "condition_not_met"
                    })
                    continue

                # 获取Agent
                agent = self.agents.get(step.agent)
                if not agent:
                    error_msg = f"Agent '{step.agent}' 不存在"
                    self.logger.error(error_msg)

                    if step.on_failure == "abort":
                        raise ValueError(error_msg)
                    else:
                        execution.step_results.append({
                            "step": step.name,
                            "agent": step.agent,
                            "success": False,
                            "error": error_msg
                        })
                        continue

                # 构建步骤输入
                step_input = self._map_input(step.input_mapping, execution.context)

                # 执行Agent
                try:
                    result = await agent.run(step_input)

                    # 存储结果
                    if step.output_key:
                        execution.context[step.output_key] = result.data

                    execution.step_results.append({
                        "step": step.name,
                        "agent": step.agent,
                        "success": result.success,
                        "data": result.data if result.success else None,
                        "error": result.error
                    })

                    # 处理失败
                    if not result.success:
                        if step.on_failure == "abort":
                            raise RuntimeError(f"步骤 '{step.name}' 执行失败: {result.error}")
                        elif step.on_failure == "skip":
                            continue

                except Exception as e:
                    self.logger.error(f"步骤 {step.name} 执行异常: {str(e)}")
                    execution.step_results.append({
                        "step": step.name,
                        "agent": step.agent,
                        "success": False,
                        "error": str(e)
                    })

                    if step.on_failure == "abort":
                        raise

            # 执行完成
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            self.logger.info(f"工作流执行完成: {workflow_id}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error = str(e)
            self.logger.error(f"工作流执行失败: {workflow_id} - {str(e)}")

        return execution

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行实例

        Args:
            execution_id: 执行ID

        Returns:
            执行实例或None
        """
        return self.executions.get(execution_id)

    def get_active_executions(self) -> List[WorkflowExecution]:
        """获取所有活跃的执行实例"""
        return [
            ex for ex in self.executions.values()
            if ex.status == WorkflowStatus.RUNNING
        ]

    def _map_input(self, mapping: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """从上下文映射输入

        Args:
            mapping: 输入映射定义
            context: 执行上下文

        Returns:
            映射后的输入字典
        """
        result = {}

        for key, value in mapping.items():
            if isinstance(value, str) and value in context:
                # 直接引用上下文中的值
                result[key] = context[value]
            elif isinstance(value, dict):
                # 嵌套字典（如tool_calls格式）
                result[key] = self._resolve_mapping_value(value, context)
            elif isinstance(value, list):
                # 列表类型
                result[key] = [
                    self._resolve_mapping_value(item, context) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _resolve_mapping_value(self, value: Any, context: Dict) -> Any:
        """解析映射值

        Args:
            value: 待解析的值
            context: 执行上下文

        Returns:
            解析后的值
        """
        if isinstance(value, str) and value.startswith("$"):
            # $开头的字符串表示引用上下文
            key = value[1:]
            return context.get(key, value)
        elif isinstance(value, dict):
            return {k: self._resolve_mapping_value(v, context) for k, v in value.items()}
        else:
            return value

    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """评估执行条件

        Args:
            condition: 条件表达式字符串
            context: 执行上下文

        Returns:
            条件是否满足
        """
        try:
            # 安全的条件评估（只允许访问context）
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception as e:
            self.logger.warning(f"条件评估失败: {condition} - {str(e)}")
            return False

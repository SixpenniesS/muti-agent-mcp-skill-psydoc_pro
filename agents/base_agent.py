# -*- coding: utf-8 -*-
"""
Agent基类模块
定义Agent的统一接口和数据结构
Author: SixpenniesS
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Agent执行结果

    Attributes:
        success: 是否成功
        data: 返回数据
        error: 错误信息（可选）
        metadata: 元数据，用于追踪和调试
        timestamp: 执行时间戳
    """
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class BaseAgent(ABC):
    """Agent基类，定义统一接口

    所有专业Agent都需要继承此类并实现execute方法。

    Attributes:
        name: Agent名称
        config: Agent配置
        status: 当前状态
        logger: 日志记录器
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """初始化Agent

        Args:
            name: Agent名称
            config: Agent配置字典
        """
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"agent.{name}")
        self._execution_history: List[Dict[str, Any]] = []

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行Agent核心逻辑

        Args:
            context: 执行上下文，包含输入数据

        Returns:
            AgentResult: 执行结果
        """
        pass

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        """运行Agent（带状态管理和错误处理）

        Args:
            context: 执行上下文

        Returns:
            AgentResult: 执行结果
        """
        self.status = AgentStatus.RUNNING
        start_time = datetime.now()

        try:
            self.logger.info(f"[{self.name}] 开始执行")
            result = await self.execute(context)

            self.status = AgentStatus.SUCCESS if result.success else AgentStatus.FAILED

            # 记录执行历史
            execution_record = {
                "timestamp": start_time.isoformat(),
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "success": result.success,
                "error": result.error
            }
            self._execution_history.append(execution_record)

            self.logger.info(f"[{self.name}] 执行完成: success={result.success}")
            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"[{self.name}] 执行失败: {str(e)}")

            return AgentResult(
                success=False,
                data={},
                error=str(e),
                metadata={"agent": self.name, "exception": type(e).__name__}
            )

    def update_status(self, status: AgentStatus) -> None:
        """更新Agent状态

        Args:
            status: 新状态
        """
        self.status = status
        self.logger.debug(f"[{self.name}] 状态更新: {status.value}")

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息

        Returns:
            包含Agent基本信息的字典
        """
        return {
            "name": self.name,
            "status": self.status.value,
            "config": self.config,
            "execution_count": len(self._execution_history)
        }

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史

        Args:
            limit: 返回记录数量限制

        Returns:
            执行历史记录列表
        """
        return self._execution_history[-limit:]

    def reset(self) -> None:
        """重置Agent状态"""
        self.status = AgentStatus.IDLE
        self._execution_history.clear()
        self.logger.info(f"[{self.name}] 已重置")


class AgentRegistry:
    """Agent注册表，管理所有Agent实例"""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """注册Agent

        Args:
            agent: Agent实例
        """
        self._agents[agent.name] = agent
        logger.info(f"Agent注册: {agent.name}")

    def get(self, name: str) -> Optional[BaseAgent]:
        """获取Agent

        Args:
            name: Agent名称

        Returns:
            Agent实例或None
        """
        return self._agents.get(name)

    def list_all(self) -> List[str]:
        """列出所有Agent名称"""
        return list(self._agents.keys())

    def get_all_info(self) -> Dict[str, Dict]:
        """获取所有Agent信息"""
        return {name: agent.get_info() for name, agent in self._agents.items()}

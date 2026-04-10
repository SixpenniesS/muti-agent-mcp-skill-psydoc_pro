# -*- coding: utf-8 -*-
"""
Skill基类模块
Author: SixpenniesS
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class SkillResult:
    """Skill执行结果"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BaseSkill(ABC):
    """Skill基类

    所有技能都需要继承此类并实现execute方法。
    """

    def __init__(self, name: str, description: str):
        """初始化Skill

        Args:
            name: 技能名称
            description: 技能描述
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"skill.{name}")

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能

        Args:
            params: 技能参数

        Returns:
            执行结果字典
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """获取技能信息"""
        return {
            "name": self.name,
            "description": self.description
        }

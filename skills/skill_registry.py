# -*- coding: utf-8 -*-
"""
Skill注册表
Author: SixpenniesS
"""

from typing import Dict, Any, List, Optional
import logging

from .skill_base import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Skill注册表

    管理所有技能的注册和查找。
    """

    def __init__(self):
        """初始化Skill注册表"""
        self._skills: Dict[str, BaseSkill] = {}
        self.logger = logging.getLogger("skill.registry")

    def register(self, skill: BaseSkill) -> None:
        """注册技能

        Args:
            skill: 技能实例
        """
        self._skills[skill.name] = skill
        self.logger.info(f"注册Skill: {skill.name}")

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取技能

        Args:
            name: 技能名称

        Returns:
            技能实例或None
        """
        return self._skills.get(name)

    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有技能信息"""
        return [skill.get_info() for skill in self._skills.values()]

    def list_skill_names(self) -> List[str]:
        """列出所有技能名称"""
        return list(self._skills.keys())

    def has_skill(self, name: str) -> bool:
        """检查技能是否存在"""
        return name in self._skills

    def unregister(self, name: str) -> bool:
        """注销技能

        Args:
            name: 技能名称

        Returns:
            是否成功注销
        """
        if name in self._skills:
            del self._skills[name]
            self.logger.info(f"注销Skill: {name}")
            return True
        return False

    def clear(self) -> None:
        """清空所有技能"""
        self._skills.clear()
        self.logger.info("已清空所有Skill")

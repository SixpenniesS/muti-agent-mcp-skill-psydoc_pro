# -*- coding: utf-8 -*-
"""
技能执行Agent
管理Skill注册和执行
Author: SixpenniesS
"""

from typing import Dict, Any, List
import asyncio

from agents.base_agent import BaseAgent, AgentResult


class SkillAgent(BaseAgent):
    """技能执行Agent

    管理Skill注册和执行。

    功能：
    - Skill注册表管理
    - 单个/批量Skill执行
    - 并行/顺序执行支持
    """

    def __init__(self, skill_registry, config: Dict[str, Any] = None):
        """初始化技能执行Agent

        Args:
            skill_registry: Skill注册表实例
            config: Agent配置
        """
        super().__init__("SkillAgent", config)
        self.skill_registry = skill_registry

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行技能

        Args:
            context: {
                "skill_calls": List[Dict] 或 单个 Dict,
                "parallel": bool (可选，默认True)
            }

            skill_call格式:
            {
                "skill": "skill_name",
                "params": {...}
            }

        Returns:
            AgentResult: {
                "skill_results": List[Dict],
                "success_count": int,
                "failure_count": int
            }
        """
        skill_calls = context.get("skill_calls", [])
        parallel = context.get("parallel", True)

        # 支持单个技能调用
        if isinstance(skill_calls, dict):
            skill_calls = [skill_calls]

        if not skill_calls:
            return AgentResult(
                success=True,
                data={"skill_results": [], "success_count": 0, "failure_count": 0},
                metadata={"agent": self.name, "skill_count": 0}
            )

        try:
            if parallel:
                results = await self._parallel_call_skills(skill_calls)
            else:
                results = await self._sequential_call_skills(skill_calls)

            success_count = sum(1 for r in results if r.get("success", False))
            failure_count = len(results) - success_count

            return AgentResult(
                success=failure_count == 0,
                data={
                    "skill_results": results,
                    "success_count": success_count,
                    "failure_count": failure_count
                },
                metadata={
                    "agent": self.name,
                    "skill_count": len(skill_calls),
                    "parallel": parallel
                }
            )

        except Exception as e:
            self.logger.error(f"技能执行失败: {str(e)}")
            return AgentResult(
                success=False,
                data={"skill_results": [], "success_count": 0, "failure_count": len(skill_calls)},
                error=str(e)
            )

    async def _parallel_call_skills(self, skill_calls: List[Dict]) -> List[Dict]:
        """并行执行多个技能

        Args:
            skill_calls: 技能调用列表

        Returns:
            结果列表
        """
        tasks = [self._call_single_skill(call) for call in skill_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "skill_call": skill_calls[i]
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _sequential_call_skills(self, skill_calls: List[Dict]) -> List[Dict]:
        """顺序执行多个技能

        Args:
            skill_calls: 技能调用列表

        Returns:
            结果列表
        """
        results = []
        for call in skill_calls:
            result = await self._call_single_skill(call)
            results.append(result)
        return results

    async def _call_single_skill(self, skill_call: Dict) -> Dict:
        """执行单个技能

        Args:
            skill_call: 技能调用配置

        Returns:
            调用结果
        """
        skill_name = skill_call.get("skill")
        params = skill_call.get("params", {})

        if not skill_name:
            return {
                "success": False,
                "error": "Missing skill name",
                "skill_call": skill_call
            }

        try:
            skill = self.skill_registry.get_skill(skill_name)

            if not skill:
                return {
                    "success": False,
                    "error": f"Skill '{skill_name}' not found",
                    "skill": skill_name
                }

            self.logger.info(f"执行Skill: {skill_name}")
            result = await skill.execute(params)

            return {
                "success": True,
                "skill": skill_name,
                "result": result
            }

        except Exception as e:
            self.logger.error(f"技能执行异常 {skill_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "skill": skill_name
            }

    def list_available_skills(self) -> List[Dict[str, str]]:
        """列出所有可用技能

        Returns:
            技能信息列表
        """
        return self.skill_registry.list_skills()

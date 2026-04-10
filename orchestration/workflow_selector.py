# -*- coding: utf-8 -*-
"""
工作流选择器
根据用户意图和危机检测结果选择合适的工作流
Author: SixpenniesS
"""

from typing import Dict, Any, List, Optional
import logging

from orchestration.workflow_orchestrator import WorkflowOrchestrator, WorkflowDefinition


logger = logging.getLogger(__name__)


class WorkflowSelector:
    """工作流选择器

    根据用户输入和上下文选择最合适的工作流。

    选择优先级：
    1. 危机信号 → crisis_intervention
    2. 意图类型 → 对应工作流
    3. 关键词匹配 → 对应工作流
    4. 默认 → daily_counseling
    """

    def __init__(self, orchestrator: WorkflowOrchestrator):
        """初始化工作流选择器

        Args:
            orchestrator: 工作流调度器实例
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("workflow.selector")

    def select(
        self,
        intent_result: Dict[str, Any],
        crisis_result: Optional[Dict[str, Any]] = None,
        user_message: str = ""
    ) -> str:
        """选择工作流

        Args:
            intent_result: 意图识别结果
            crisis_result: 危机检测结果（可选）
            user_message: 用户原始消息

        Returns:
            工作流ID
        """
        # 1. 优先检查危机信号
        if crisis_result:
            risk_level = crisis_result.get("risk_level", "")
            if risk_level in ["critical", "high"]:
                self.logger.info(f"检测到危机信号（风险等级: {risk_level}），选择危机干预工作流")
                return "crisis_intervention"

        # 2. 根据意图类型选择
        intent = intent_result.get("intent")
        intent_value = intent.value if hasattr(intent, "value") else str(intent)

        workflow_by_intent = {
            "mental_assessment": "mental_assessment",
            "daily_counseling": "daily_counseling",
            "crisis_intervention": "crisis_intervention",
            "simple_chat": "daily_counseling"
        }

        if intent_value in workflow_by_intent:
            selected = workflow_by_intent[intent_value]
            self.logger.info(f"根据意图 '{intent_value}' 选择工作流: {selected}")
            return selected

        # 3. 关键词匹配
        if user_message:
            matched = self._match_keywords(user_message)
            if matched:
                self.logger.info(f"根据关键词匹配选择工作流: {matched}")
                return matched

        # 4. 默认日常咨询
        self.logger.info("使用默认工作流: daily_counseling")
        return "daily_counseling"

    def _match_keywords(self, message: str) -> Optional[str]:
        """关键词匹配

        Args:
            message: 用户消息

        Returns:
            匹配的工作流ID或None
        """
        message_lower = message.lower()

        # 关键词映射
        keyword_map = {
            "mental_assessment": ["评估", "测试", "量表", "检查", "诊断"],
            "crisis_intervention": ["自杀", "想死", "不想活", "结束生命", "自残"],
            "daily_counseling": ["咨询", "怎么办", "如何", "帮助", "建议"]
        }

        for workflow_id, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return workflow_id

        return None

    def get_workflow_info(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流信息字典
        """
        workflow = self.orchestrator.get_workflow(workflow_id)
        if not workflow:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "steps_count": len(workflow.steps),
            "trigger_intents": workflow.trigger_intents,
            "trigger_keywords": workflow.trigger_keywords
        }

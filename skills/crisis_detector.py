# -*- coding: utf-8 -*-
"""
危机检测技能
检测用户输入中的危机信号和风险等级
Author: SixpenniesS
"""

from typing import Dict, Any, List
from skills.skill_base import BaseSkill


class CrisisDetectorSkill(BaseSkill):
    """危机检测技能

    检测用户输入中的危机信号和风险等级。

    功能：
    - 检测危机关键词（自杀、自残等）
    - 评估风险等级（critical/high/medium/low）
    - 生成干预建议
    """

    # 危机信号关键词（按严重程度分级）
    CRISIS_LEVELS = {
        "critical": {
            "keywords": ["自杀", "想死", "不想活", "结束生命", "杀自己", "去死", "跳楼", "上吊"],
            "score": 10
        },
        "high": {
            "keywords": ["自残", "伤害自己", "没有希望", "活不下去", "绝望", "无路可走", "彻底崩溃"],
            "score": 7
        },
        "medium": {
            "keywords": ["痛苦", "崩溃", "无法承受", "撑不下去", "彻底失败", "一切都完了", "没有意义"],
            "score": 4
        },
        "low": {
            "keywords": ["困难", "挣扎", "迷茫", "无助", "孤独", "找不到方向", "不知道怎么办"],
            "score": 2
        }
    }

    # 干预建议
    INTERVENTION_GUIDES = {
        "critical": {
            "immediate": True,
            "message": "检测到严重危机信号，需要立即关注",
            "actions": [
                "立即提供紧急求助热线",
                "建议联系专业机构或家人朋友",
                "不要让用户独处",
                "必要时报警或拨打急救电话"
            ],
            "hotlines": [
                {"name": "全国心理援助热线", "number": "400-161-9995"},
                {"name": "北京心理危机干预中心", "number": "010-82951332"},
                {"name": "生命热线", "number": "400-821-1215"}
            ]
        },
        "high": {
            "immediate": True,
            "message": "检测到高风险信号，需要重点关注",
            "actions": [
                "提供专业资源和支持",
                "深入探讨问题根源",
                "建议寻求专业帮助",
                "持续关注用户状态"
            ],
            "hotlines": [
                {"name": "全国心理援助热线", "number": "400-161-9995"},
                {"name": "生命热线", "number": "400-821-1215"}
            ]
        },
        "medium": {
            "immediate": False,
            "message": "检测到中等风险信号",
            "actions": [
                "提供情感支持",
                "引导用户表达感受",
                "提供适当的应对策略"
            ],
            "hotlines": [
                {"name": "全国心理援助热线", "number": "400-161-9995"}
            ]
        },
        "low": {
            "immediate": False,
            "message": "风险较低",
            "actions": [
                "常规咨询流程",
                "提供情感支持"
            ],
            "hotlines": []
        }
    }

    def __init__(self):
        super().__init__(
            name="crisis_detector",
            description="检测用户输入中的危机信号和风险等级"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行危机检测

        Args:
            params: {
                "text": str,              # 用户输入文本
                "history": List[Dict],    # 对话历史（可选）
                "deep_analysis": bool     # 是否深度分析（可选）
            }

        Returns:
            {
                "risk_level": str,           # 风险等级
                "risk_score": float,         # 风险分数
                "detected_signals": List,    # 检测到的信号
                "intervention_needed": bool, # 是否需要干预
                "intervention": Dict         # 干预建议
            }
        """
        text = params.get("text", "")
        history = params.get("history", [])
        deep_analysis = params.get("deep_analysis", False)

        if not text:
            return {
                "success": False,
                "error": "text参数不能为空"
            }

        try:
            # 1. 关键词检测
            keyword_result = self._detect_keywords(text)

            # 2. 上下文分析（结合历史）
            context_score = self._analyze_context(text, history) if deep_analysis else 0

            # 3. 综合风险评估
            risk_level, risk_score = self._calculate_risk(keyword_result, context_score)

            # 4. 生成干预建议
            intervention = self._generate_intervention(risk_level)

            return {
                "success": True,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "detected_signals": keyword_result["signals"],
                "intervention_needed": risk_level in ["critical", "high"],
                "intervention": intervention
            }

        except Exception as e:
            self.logger.error(f"危机检测失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _detect_keywords(self, text: str) -> Dict:
        """检测危机关键词

        Args:
            text: 输入文本

        Returns:
            检测结果，包含信号列表和总分
        """
        signals = []
        total_score = 0

        for level, config in self.CRISIS_LEVELS.items():
            for keyword in config["keywords"]:
                if keyword in text:
                    signals.append({
                        "keyword": keyword,
                        "level": level,
                        "score": config["score"],
                        "position": text.find(keyword)
                    })
                    total_score += config["score"]

        # 按严重程度排序
        level_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        signals.sort(key=lambda x: level_order.get(x["level"], 4))

        return {"signals": signals, "score": total_score}

    def _analyze_context(self, text: str, history: List[Dict]) -> float:
        """分析上下文（结合历史对话）

        Args:
            text: 当前输入
            history: 对话历史

        Returns:
            上下文风险分数
        """
        if not history:
            return 0

        negative_trend = 0

        # 分析最近5轮对话中的负面情绪累积
        for msg in history[-10:]:
            if msg.get("role") == "user":
                content = msg.get("content", "")

                # 检查历史中的危机信号
                for level, config in self.CRISIS_LEVELS.items():
                    for keyword in config["keywords"]:
                        if keyword in content:
                            # 越近的消息权重越高
                            negative_trend += config["score"] * 0.1
                            break

        return min(negative_trend, 3.0)

    def _calculate_risk(
        self,
        keyword_result: Dict,
        context_score: float
    ) -> tuple:
        """计算综合风险等级

        Args:
            keyword_result: 关键词检测结果
            context_score: 上下文分数

        Returns:
            (风险等级, 风险分数)
        """
        total_score = keyword_result["score"] + context_score

        if total_score >= 10:
            return "critical", total_score
        elif total_score >= 7:
            return "high", total_score
        elif total_score >= 4:
            return "medium", total_score
        else:
            return "low", total_score

    def _generate_intervention(self, risk_level: str) -> Dict:
        """生成干预建议

        Args:
            risk_level: 风险等级

        Returns:
            干预建议
        """
        guide = self.INTERVENTION_GUIDES.get(risk_level, self.INTERVENTION_GUIDES["low"])

        return {
            "level": risk_level,
            "immediate": guide["immediate"],
            "message": guide["message"],
            "actions": guide["actions"],
            "hotlines": guide["hotlines"]
        }

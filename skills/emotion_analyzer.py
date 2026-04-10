# -*- coding: utf-8 -*-
"""
情绪分析技能
分析用户输入的情绪倾向和强度
Author: SixpenniesS
"""

from typing import Dict, Any, List
from skills.skill_base import BaseSkill


class EmotionAnalyzerSkill(BaseSkill):
    """情绪分析技能

    分析用户输入的情绪倾向和强度。

    功能：
    - 检测情绪类型（焦虑、抑郁、愤怒、恐惧、孤独、自卑等）
    - 分析情绪强度
    - 判断情感极性（正面/负面/中性）
    """

    # 情绪关键词词典
    EMOTION_KEYWORDS = {
        "焦虑": ["焦虑", "紧张", "担心", "不安", "害怕", "恐惧", "慌张", "心慌", "烦躁", "坐立难安"],
        "抑郁": ["抑郁", "沮丧", "绝望", "无助", "悲伤", "消沉", "低落", "难过", "痛苦", "想哭"],
        "愤怒": ["愤怒", "生气", "恼火", "烦躁", "不满", "怨恨", "火大", "气死", "暴怒"],
        "恐惧": ["恐惧", "害怕", "惊恐", "胆怯", "畏惧", "恐怖", "吓人", "可怕"],
        "孤独": ["孤独", "寂寞", "孤单", "无人理解", "被孤立", "没人陪", "形单影只"],
        "自卑": ["自卑", "没用", "不如人", "不自信", "自责", "我很差", "我不行"],
        "迷茫": ["迷茫", "困惑", "不知所措", "没有方向", "找不到意义", "不知道怎么办"],
        "压力": ["压力", "负担", "喘不过气", "撑不住", "太累了", "承受不住"]
    }

    # 程度副词
    INTENSITY_WORDS = {
        "非常": 0.3,
        "极其": 0.4,
        "特别": 0.2,
        "很": 0.15,
        "太": 0.2,
        "相当": 0.15,
        "十分": 0.2
    }

    # 正面词汇
    POSITIVE_WORDS = ["好", "开心", "快乐", "幸福", "满足", "希望", "期待", "感谢", "欣慰", "轻松"]

    # 负面词汇
    NEGATIVE_WORDS = ["不好", "难过", "痛苦", "绝望", "失败", "崩溃", "糟糕", "很差", "难受"]

    def __init__(self):
        super().__init__(
            name="emotion_analyzer",
            description="分析用户输入的情绪倾向和强度"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行情绪分析

        Args:
            params: {
                "text": str  # 要分析的文本
            }

        Returns:
            {
                "emotions": List[Dict],  # 检测到的情绪列表
                "intensity": float,      # 情绪强度 (0-1)
                "polarity": str,         # 情感极性
                "summary": str           # 摘要描述
            }
        """
        text = params.get("text", "")

        if not text:
            return {
                "success": False,
                "error": "text参数不能为空"
            }

        try:
            # 1. 检测情绪类型
            detected_emotions = self._detect_emotions(text)

            # 2. 分析情绪强度
            intensity = self._analyze_intensity(text, detected_emotions)

            # 3. 分析情感极性
            polarity = self._analyze_polarity(text)

            # 4. 生成摘要
            summary = self._generate_summary(detected_emotions, intensity, polarity)

            return {
                "success": True,
                "emotions": detected_emotions,
                "intensity": intensity,
                "polarity": polarity,
                "summary": summary
            }

        except Exception as e:
            self.logger.error(f"情绪分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _detect_emotions(self, text: str) -> List[Dict]:
        """检测情绪类型

        Args:
            text: 输入文本

        Returns:
            检测到的情绪列表，按置信度排序
        """
        detected = []

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            # 计算关键词命中数
            count = sum(1 for kw in keywords if kw in text)

            if count > 0:
                # 计算置信度（基于命中关键词数和总关键词数的比例）
                confidence = min(count / len(keywords) * 3, 1.0)

                detected.append({
                    "emotion": emotion,
                    "keyword_count": count,
                    "confidence": round(confidence, 2),
                    "matched_keywords": [kw for kw in keywords if kw in text][:3]
                })

        # 按置信度排序
        detected.sort(key=lambda x: x["confidence"], reverse=True)

        return detected[:3]  # 最多返回3个情绪

    def _analyze_intensity(self, text: str, emotions: List[Dict]) -> float:
        """分析情绪强度

        Args:
            text: 输入文本
            emotions: 检测到的情绪列表

        Returns:
            情绪强度 (0-1)
        """
        # 基础强度（基于情绪关键词数量）
        base_intensity = sum(e.get("keyword_count", 0) for e in emotions)

        # 程度副词加成
        modifier = 1.0
        for word, value in self.INTENSITY_WORDS.items():
            if word in text:
                modifier += value

        # 计算最终强度
        intensity = min(base_intensity * modifier / 5, 1.0)

        return round(intensity, 2)

    def _analyze_polarity(self, text: str) -> str:
        """分析情感极性

        Args:
            text: 输入文本

        Returns:
            情感极性：positive/negative/neutral
        """
        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in text)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in text)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

    def _generate_summary(
        self,
        emotions: List[Dict],
        intensity: float,
        polarity: str
    ) -> str:
        """生成情绪分析摘要

        Args:
            emotions: 情绪列表
            intensity: 强度
            polarity: 极性

        Returns:
            摘要文本
        """
        if not emotions:
            return "未检测到明显情绪表达"

        # 主要情绪
        main_emotion = emotions[0]["emotion"]

        # 强度描述
        if intensity > 0.7:
            intensity_desc = "强烈"
        elif intensity > 0.4:
            intensity_desc = "中等"
        else:
            intensity_desc = "轻微"

        # 极性描述
        polarity_desc = {
            "positive": "积极",
            "negative": "消极",
            "neutral": "中性"
        }.get(polarity, "中性")

        return f"检测到{intensity_desc}的{main_emotion}情绪，整体情感倾向{polarity_desc}"

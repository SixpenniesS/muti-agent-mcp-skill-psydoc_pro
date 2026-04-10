# -*- coding: utf-8 -*-
"""
Skill系统测试
Author: SixpenniesS
"""

import pytest
import asyncio

from skills import SkillRegistry
from skills.emotion_analyzer import EmotionAnalyzerSkill
from skills.crisis_detector import CrisisDetectorSkill


class TestSkillRegistry:
    """Skill注册表测试"""

    def test_register_skill(self):
        """测试技能注册"""
        registry = SkillRegistry()
        skill = EmotionAnalyzerSkill()

        registry.register(skill)

        assert registry.has_skill("emotion_analyzer")
        assert registry.get_skill("emotion_analyzer") is skill

    def test_list_skills(self):
        """测试列出技能"""
        registry = SkillRegistry()
        registry.register(EmotionAnalyzerSkill())
        registry.register(CrisisDetectorSkill())

        skills = registry.list_skills()

        assert len(skills) == 2
        assert any(s["name"] == "emotion_analyzer" for s in skills)
        assert any(s["name"] == "crisis_detector" for s in skills)


class TestEmotionAnalyzer:
    """情绪分析技能测试"""

    @pytest.mark.asyncio
    async def test_analyze_anxiety(self):
        """测试焦虑情绪分析"""
        skill = EmotionAnalyzerSkill()

        result = await skill.execute({
            "text": "我最近很焦虑，总是紧张不安"
        })

        assert result["success"] is True
        assert len(result["emotions"]) > 0
        assert result["emotions"][0]["emotion"] == "焦虑"

    @pytest.mark.asyncio
    async def test_analyze_depression(self):
        """测试抑郁情绪分析"""
        skill = EmotionAnalyzerSkill()

        result = await skill.execute({
            "text": "我感觉很抑郁，绝望无助，什么都不想做"
        })

        assert result["success"] is True
        assert any(e["emotion"] == "抑郁" for e in result["emotions"])

    @pytest.mark.asyncio
    async def test_intensity_analysis(self):
        """测试情绪强度分析"""
        skill = EmotionAnalyzerSkill()

        # 高强度
        result_high = await skill.execute({
            "text": "我非常非常焦虑，极其恐惧，特别害怕"
        })

        # 低强度
        result_low = await skill.execute({
            "text": "有点焦虑"
        })

        assert result_high["intensity"] > result_low["intensity"]

    @pytest.mark.asyncio
    async def test_polarity_analysis(self):
        """测试情感极性分析"""
        skill = EmotionAnalyzerSkill()

        # 正面
        result_pos = await skill.execute({
            "text": "今天很开心快乐"
        })

        # 负面
        result_neg = await skill.execute({
            "text": "今天很痛苦难过"
        })

        assert result_pos["polarity"] == "positive"
        assert result_neg["polarity"] == "negative"


class TestCrisisDetector:
    """危机检测技能测试"""

    @pytest.mark.asyncio
    async def test_detect_critical_crisis(self):
        """测试严重危机检测"""
        skill = CrisisDetectorSkill()

        result = await skill.execute({
            "text": "我想自杀，不想活了"
        })

        assert result["success"] is True
        assert result["risk_level"] == "critical"
        assert result["intervention_needed"] is True
        assert len(result["intervention"]["hotlines"]) > 0

    @pytest.mark.asyncio
    async def test_detect_high_risk(self):
        """测试高风险检测"""
        skill = CrisisDetectorSkill()

        result = await skill.execute({
            "text": "我感觉绝望，没有希望，活不下去了"
        })

        assert result["success"] is True
        assert result["risk_level"] in ["high", "critical"]

    @pytest.mark.asyncio
    async def test_detect_low_risk(self):
        """测试低风险检测"""
        skill = CrisisDetectorSkill()

        result = await skill.execute({
            "text": "最近工作有些困难，有点迷茫"
        })

        assert result["success"] is True
        assert result["risk_level"] in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_intervention_suggestion(self):
        """测试干预建议"""
        skill = CrisisDetectorSkill()

        result = await skill.execute({
            "text": "我想自杀"
        })

        assert result["success"] is True
        assert result["intervention"]["immediate"] is True
        assert len(result["intervention"]["actions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

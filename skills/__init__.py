# -*- coding: utf-8 -*-
"""
技能模块
Author: SixpenniesS
"""

from .skill_base import BaseSkill
from .skill_registry import SkillRegistry
from .emotion_analyzer import EmotionAnalyzerSkill
from .crisis_detector import CrisisDetectorSkill

__all__ = [
    "BaseSkill",
    "SkillRegistry",
    "EmotionAnalyzerSkill",
    "CrisisDetectorSkill"
]

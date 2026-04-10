# -*- coding: utf-8 -*-
"""
意图识别Agent
分析用户输入，决定工作流类型和主题分类
Author: SixpenniesS
"""

from typing import Dict, Any, List, Tuple
from enum import Enum
import requests
import json

from agents.base_agent import BaseAgent, AgentResult
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class IntentType(Enum):
    """意图类型枚举"""
    MENTAL_ASSESSMENT = "mental_assessment"      # 心理评估
    DAILY_COUNSELING = "daily_counseling"        # 日常咨询
    CRISIS_INTERVENTION = "crisis_intervention"  # 危机干预
    SIMPLE_CHAT = "simple_chat"                  # 简单闲聊
    TOOL_CALL = "tool_call"                      # 工具调用（报告生成、记录查询等）


class IntentAgent(BaseAgent):
    """意图识别Agent

    分析用户输入，决定工作流类型和主题分类。

    功能：
    - 判断是否需要RAG检索
    - 识别心理学主题
    - 确定意图类型（用于工作流选择）
    """

    # 心理学主题定义
    PSYCHOLOGY_TOPICS = {
        "情绪": "焦虑、抑郁、愤怒、恐惧、情绪管理、情感压抑、情绪波动",
        "人际": "朋友关系、社交恐惧、人际冲突、被排斥孤立、沟通困难",
        "婚恋": "恋爱关系、伴侣沟通、情感矛盾、分手挽回、亲密关系困扰",
        "家庭": "父母关系、家庭暴力、原生家庭影响、亲子关系、家庭责任",
        "性心理": "性取向、性欲、性困惑、婚外情、性别认同",
        "成长": "青少年发展、学业压力、自我突破、人生规划、考试压力",
        "治疗": "心理疾病、躯体化障碍、心理治疗方法、专业干预",
        "社会": "社会现象、心理健康科普、社会议题",
        "职场": "职业选择、工作压力、失业困境、工作倦怠、职场人际",
        "自我": "自我认同、自我价值、人生迷茫、自信心",
        "行为": "强迫行为、习惯问题、行为模式、反复确认",
        "心理学知识": "心理学理论、人格特质、心理学概念"
    }

    # 危机关键词
    CRISIS_KEYWORDS = ["自杀", "想死", "不想活", "结束生命", "自残", "伤害自己"]

    # 工具调用关键词映射（新增）
    TOOL_CALL_KEYWORDS = {
        "generate_report": {
            "keywords": ["生成报告", "咨询报告", "总结报告", "生成一份报告", "帮我写个报告"],
            "server": "filesystem",
            "tool": "write_file",
            "description": "生成心理咨询报告"
        },
        "query_history": {
            "keywords": ["查看记录", "历史记录", "咨询记录", "我的记录", "过去的咨询"],
            "server": "database",
            "tool": "query_user_history",
            "description": "查询咨询历史记录"
        },
        "save_conversation": {
            "keywords": ["保存对话", "保存记录", "记录下来", "帮我保存"],
            "server": "database",
            "tool": "save_conversation",
            "description": "保存当前对话记录"
        },
        "search_resources": {
            "keywords": ["搜索资源", "查找资料", "搜索相关", "帮我找"],
            "server": "search",
            "tool": "search",
            "description": "搜索相关资源"
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("IntentAgent", config)
        self.api_key = DEEPSEEK_API_KEY
        self.llm_url = f"{DEEPSEEK_BASE_URL}/chat/completions"
        self.model = self.config.get("model", DEEPSEEK_MODEL)

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行意图识别

        Args:
            context: {
                "user_message": str,
                "conversation_history": List[Dict]
            }

        Returns:
            AgentResult: {
                "intent": IntentType,
                "topics": List[str],
                "need_rag": bool,
                "confidence": float,
                "crisis_detected": bool
            }
        """
        user_message = context.get("user_message", "")
        conversation_history = context.get("conversation_history", [])

        if not user_message:
            return AgentResult(
                success=False,
                data={},
                error="user_message is required"
            )

        try:
            # 1. 快速检测危机关键词
            crisis_detected = self._quick_crisis_check(user_message)

            # 2. 检测工具调用意图（新增）
            tool_call_info = self._detect_tool_call(user_message)

            # 3. 调用LLM进行意图分类和主题识别
            intent_result = await self._classify_intent_with_llm(user_message, conversation_history)

            # 4. 如果检测到危机，覆盖意图类型
            if crisis_detected:
                intent_result["intent"] = IntentType.CRISIS_INTERVENTION
                intent_result["crisis_detected"] = True

            # 5. 如果检测到工具调用，设置意图并保存工具信息（新增）
            if tool_call_info:
                intent_result["intent"] = IntentType.TOOL_CALL
                intent_result["tool_call"] = tool_call_info
                intent_result["need_rag"] = False

            return AgentResult(
                success=True,
                data=intent_result,
                metadata={
                    "agent": self.name,
                    "input_length": len(user_message),
                    "history_length": len(conversation_history)
                }
            )

        except Exception as e:
            self.logger.error(f"意图识别失败: {str(e)}")
            # 降级：返回默认结果
            return AgentResult(
                success=True,
                data={
                    "intent": IntentType.DAILY_COUNSELING,
                    "topics": [],
                    "need_rag": True,
                    "confidence": 0.5,
                    "crisis_detected": False,
                    "fallback": True
                }
            )

    def _quick_crisis_check(self, message: str) -> bool:
        """快速危机关键词检测

        Args:
            message: 用户消息

        Returns:
            是否检测到危机信号
        """
        for keyword in self.CRISIS_KEYWORDS:
            if keyword in message:
                self.logger.warning(f"检测到危机关键词: {keyword}")
                return True
        return False

    def _detect_tool_call(self, message: str) -> Dict[str, Any]:
        """检测工具调用意图（新增）

        Args:
            message: 用户消息

        Returns:
            工具调用信息，格式:
            {
                "tool_type": "generate_report|query_history|save_conversation|search_resources",
                "server": "filesystem|database|search",
                "tool": "工具名称",
                "description": "工具描述",
                "params": {}  # 从消息中提取的参数
            }
            如果没有检测到工具调用，返回 None
        """
        message_lower = message.lower()

        for tool_type, config in self.TOOL_CALL_KEYWORDS.items():
            for keyword in config["keywords"]:
                if keyword in message:
                    self.logger.info(f"检测到工具调用意图: {tool_type} (关键词: {keyword})")
                    return {
                        "tool_type": tool_type,
                        "server": config["server"],
                        "tool": config["tool"],
                        "description": config["description"],
                        "params": {}  # 基础参数，后续可以扩展参数提取
                    }

        return None

    async def _classify_intent_with_llm(self, message: str, history: List[Dict]) -> Dict[str, Any]:
        """调用LLM进行意图分类

        Args:
            message: 用户消息
            history: 对话历史

        Returns:
            分类结果字典
        """
        # 构建对话历史上下文
        context = self._build_conversation_context(history)

        # 构建提示词
        prompt = self._build_classification_prompt(message, context)

        # 调用LLM
        response = await self._call_llm(prompt)

        # 解析响应
        return self._parse_response(response)

    def _build_conversation_context(self, history: List[Dict]) -> str:
        """构建对话历史上下文"""
        if not history:
            return "无"

        lines = []
        for msg in history[-6:]:  # 只取最近6轮
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"助手: {content}")

        return "\n".join(lines) if lines else "无"

    def _build_classification_prompt(self, message: str, context: str) -> str:
        """构建分类提示词"""
        topics_list = "\n".join([f"{k}: {v}" for k, v in self.PSYCHOLOGY_TOPICS.items()])

        return f"""你是心理咨询助手的意图识别系统。请分析用户输入并完成以下任务：

1. 判断意图类型：
   - mental_assessment: 用户想要进行心理评估、测试
   - daily_counseling: 日常心理咨询、寻求建议
   - simple_chat: 简单问候、闲聊

2. 判断是否需要检索知识库：
   - 简单问候、感谢、闲聊 → 不需要
   - 需要专业建议、心理学知识 → 需要

3. 识别相关主题（从以下12个中选择1-3个）：
{topics_list}

对话历史:
{context}

用户问题: {message}

返回格式（严格JSON）:
{{
  "intent": "mental_assessment|daily_counseling|simple_chat",
  "need_rag": true|false,
  "topics": ["主题1", "主题2"],
  "confidence": 0.0-1.0
}}

只返回JSON，不要解释。"""

    async def _call_llm(self, prompt: str) -> str:
        """调用DeepSeek LLM"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.3
            }

            response = requests.post(self.llm_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]

            return ""

        except Exception as e:
            self.logger.error(f"LLM调用失败: {str(e)}")
            return ""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        default_result = {
            "intent": IntentType.DAILY_COUNSELING,
            "topics": [],
            "need_rag": True,
            "confidence": 0.5,
            "crisis_detected": False
        }

        if not response:
            return default_result

        try:
            # 尝试提取JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            result = json.loads(response)

            # 映射意图类型
            intent_str = result.get("intent", "daily_counseling")
            intent_map = {
                "mental_assessment": IntentType.MENTAL_ASSESSMENT,
                "daily_counseling": IntentType.DAILY_COUNSELING,
                "simple_chat": IntentType.SIMPLE_CHAT
            }

            return {
                "intent": intent_map.get(intent_str, IntentType.DAILY_COUNSELING),
                "topics": result.get("topics", []),
                "need_rag": result.get("need_rag", True),
                "confidence": result.get("confidence", 0.5),
                "crisis_detected": False
            }

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON解析失败: {str(e)}, response: {response[:100]}")
            return default_result

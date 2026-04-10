# -*- coding: utf-8 -*-
"""
Agent测试
Author: SixpenniesS
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from agents.base_agent import BaseAgent, AgentResult, AgentStatus
from agents.intent_agent import IntentAgent, IntentType


class TestBaseAgent:
    """Agent基类测试"""

    def test_agent_initialization(self):
        """测试Agent初始化"""
        class TestAgent(BaseAgent):
            async def execute(self, context):
                return AgentResult(success=True, data={})

        agent = TestAgent("test_agent", {"key": "value"})

        assert agent.name == "test_agent"
        assert agent.config == {"key": "value"}
        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_agent_run_success(self):
        """测试Agent运行成功"""
        class TestAgent(BaseAgent):
            async def execute(self, context):
                return AgentResult(success=True, data={"result": "ok"})

        agent = TestAgent("test_agent")
        result = await agent.run({"input": "test"})

        assert result.success is True
        assert result.data == {"result": "ok"}
        assert agent.status == AgentStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_agent_run_failure(self):
        """测试Agent运行失败"""
        class TestAgent(BaseAgent):
            async def execute(self, context):
                raise ValueError("测试错误")

        agent = TestAgent("test_agent")
        result = await agent.run({"input": "test"})

        assert result.success is False
        assert "测试错误" in result.error
        assert agent.status == AgentStatus.FAILED


class TestIntentAgent:
    """意图识别Agent测试"""

    @pytest.mark.asyncio
    async def test_simple_chat_detection(self):
        """测试简单闲聊检测"""
        agent = IntentAgent()

        # Mock LLM响应
        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"intent": "simple_chat", "need_rag": false, "topics": [], "confidence": 0.9}'

            result = await agent.execute({
                "user_message": "你好",
                "conversation_history": []
            })

            assert result.success is True
            assert result.data["intent"] == IntentType.SIMPLE_CHAT
            assert result.data["need_rag"] is False

    @pytest.mark.asyncio
    async def test_crisis_detection(self):
        """测试危机信号检测"""
        agent = IntentAgent()

        result = await agent.execute({
            "user_message": "我想自杀",
            "conversation_history": []
        })

        assert result.success is True
        assert result.data["crisis_detected"] is True
        assert result.data["intent"] == IntentType.CRISIS_INTERVENTION

    @pytest.mark.asyncio
    async def test_counseling_intent(self):
        """测试咨询意图检测"""
        agent = IntentAgent()

        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"intent": "daily_counseling", "need_rag": true, "topics": ["情绪", "焦虑"], "confidence": 0.85}'

            result = await agent.execute({
                "user_message": "我最近很焦虑，该怎么办？",
                "conversation_history": []
            })

            assert result.success is True
            assert result.data["intent"] == IntentType.DAILY_COUNSELING
            assert result.data["need_rag"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

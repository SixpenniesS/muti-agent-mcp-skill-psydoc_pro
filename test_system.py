#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PsyChat-Pro 系统测试脚本
测试各模块功能是否正常
Author: SixpenniesS
"""

import sys
import asyncio
from pathlib import Path

# Windows编码问题修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_config():
    """测试配置模块"""
    print_header("测试配置模块")
    try:
        from config import (
            PROJECT_ROOT, DEEPSEEK_MODEL, EMBEDDING_MODEL,
            COLLECTION_NAME, TOP_K_RESULTS, SIMILARITY_THRESHOLD,
            DEEPSEEK_API_KEY, ALIBABA_API_KEY
        )
        print(f"[OK] 项目路径: {PROJECT_ROOT}")
        print(f"[OK] LLM模型: {DEEPSEEK_MODEL}")
        print(f"[OK] Embedding模型: {EMBEDDING_MODEL}")
        print(f"[OK] 向量集合: {COLLECTION_NAME}")
        print(f"[OK] API Key状态: DeepSeek={bool(DEEPSEEK_API_KEY)}, Alibaba={bool(ALIBABA_API_KEY)}")
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {str(e)}")
        return False


def test_vector_store():
    """测试向量存储"""
    print_header("测试向量存储")
    try:
        from core.vector_store import VectorStore
        vs = VectorStore()
        info = vs.get_collection_info()
        print(f"[OK] 向量存储初始化成功")
        print(f"[OK] 文档数量: {info.get('document_count', 0)}")
        return True
    except Exception as e:
        print(f"[FAIL] 向量存储测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_skills():
    """测试Skill系统"""
    print_header("测试Skill系统")
    try:
        from skills import SkillRegistry, EmotionAnalyzerSkill, CrisisDetectorSkill

        registry = SkillRegistry()
        registry.register(EmotionAnalyzerSkill())
        registry.register(CrisisDetectorSkill())

        print(f"[OK] Skill注册表初始化成功")
        print(f"[OK] 已注册Skill: {registry.list_skill_names()}")

        # 测试危机检测
        async def test_crisis():
            skill = registry.get_skill("crisis_detector")
            result = await skill.execute({"text": "我最近感觉很焦虑，睡不着觉"})
            return result

        result = asyncio.run(test_crisis())
        print(f"[OK] 危机检测测试: 风险等级={result.get('risk_level', 'unknown')}")

        return True
    except Exception as e:
        print(f"[FAIL] Skill系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agents():
    """测试Agent系统"""
    print_header("测试Agent系统")
    try:
        from agents import IntentAgent, RAGAgent, SkillAgent, ResponseAgent
        from skills import SkillRegistry, EmotionAnalyzerSkill, CrisisDetectorSkill
        from core.vector_store import VectorStore

        # 初始化组件
        vector_store = VectorStore()
        skill_registry = SkillRegistry()
        skill_registry.register(EmotionAnalyzerSkill())
        skill_registry.register(CrisisDetectorSkill())

        # 创建Agent
        agents = {
            "intent_agent": IntentAgent(),
            "rag_agent": RAGAgent(vector_store),
            "skill_agent": SkillAgent(skill_registry),
            "response_agent": ResponseAgent()
        }

        print(f"[OK] Agent初始化成功: {list(agents.keys())}")
        return True
    except Exception as e:
        print(f"[FAIL] Agent系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp():
    """测试MCP系统"""
    print_header("测试MCP系统")
    try:
        from mcp import MCPGateway, FilesystemMCP, DatabaseMCP

        gateway = MCPGateway()
        gateway.register_server(FilesystemMCP("storage"))
        gateway.register_server(DatabaseMCP("storage/psychology.db"))

        print(f"[OK] MCP网关初始化成功")
        print(f"[OK] 已注册服务器: {gateway.get_server_names()}")
        return True
    except Exception as e:
        print(f"[FAIL] MCP系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestration():
    """测试编排系统"""
    print_header("测试编排系统")
    try:
        from orchestration import WorkflowOrchestrator, WorkflowSelector
        from agents import IntentAgent, RAGAgent, SkillAgent, ResponseAgent
        from skills import SkillRegistry, EmotionAnalyzerSkill, CrisisDetectorSkill
        from core.vector_store import VectorStore

        # 初始化组件
        vector_store = VectorStore()
        skill_registry = SkillRegistry()
        skill_registry.register(EmotionAnalyzerSkill())
        skill_registry.register(CrisisDetectorSkill())

        agents = {
            "intent_agent": IntentAgent(),
            "rag_agent": RAGAgent(vector_store),
            "skill_agent": SkillAgent(skill_registry),
            "response_agent": ResponseAgent()
        }

        orchestrator = WorkflowOrchestrator(agents)
        selector = WorkflowSelector(orchestrator)

        print(f"[OK] 编排系统初始化成功")
        return True
    except Exception as e:
        print(f"[FAIL] 编排系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_flow():
    """测试完整流程"""
    print_header("测试完整对话流程")

    try:
        from agents import IntentAgent, RAGAgent, SkillAgent, ResponseAgent
        from skills import SkillRegistry, EmotionAnalyzerSkill, CrisisDetectorSkill
        from core.vector_store import VectorStore

        # 初始化
        print("初始化组件...")
        vector_store = VectorStore()
        skill_registry = SkillRegistry()
        skill_registry.register(EmotionAnalyzerSkill())
        skill_registry.register(CrisisDetectorSkill())

        agents = {
            "intent_agent": IntentAgent(),
            "rag_agent": RAGAgent(vector_store),
            "skill_agent": SkillAgent(skill_registry),
            "response_agent": ResponseAgent()
        }

        # 测试消息
        test_message = "你好，我最近感觉很焦虑，工作压力很大"
        print(f"\n用户输入: {test_message}")

        # 1. 意图识别
        print("\n1. 意图识别...")
        intent_result = await agents["intent_agent"].run({
            "user_message": test_message,
            "conversation_history": []
        })
        print(f"   意图: {intent_result.data.get('intent')}")
        print(f"   主题: {intent_result.data.get('topics')}")
        print(f"   需要RAG: {intent_result.data.get('need_rag')}")

        # 2. 危机检测
        print("\n2. 危机检测...")
        crisis_result = await agents["skill_agent"].run({
            "skill_calls": [{
                "skill": "crisis_detector",
                "params": {"text": test_message}
            }]
        })
        crisis_data = crisis_result.data.get("skill_results", [{}])[0].get("result", {})
        print(f"   风险等级: {crisis_data.get('risk_level', 'unknown')}")
        print(f"   风险分数: {crisis_data.get('risk_score', 0)}")

        # 3. RAG检索
        print("\n3. RAG检索...")
        rag_result = await agents["rag_agent"].run({
            "query": test_message,
            "topics": intent_result.data.get("topics", [])
        })
        print(f"   检索文档数: {rag_result.data.get('total_found', 0)}")

        # 4. 生成响应
        print("\n4. 生成响应...")
        response_result = await agents["response_agent"].run({
            "user_message": test_message,
            "rag_context": rag_result.data.get("context_text", ""),
            "rag_documents": rag_result.data.get("documents", []),
            "skill_results": {"crisis_detector": crisis_data},
            "conversation_history": [],
            "mode": "normal"
        })

        response = response_result.data.get("response", "")
        print(f"\n助手回复:\n{response}")

        print("\n[OK] 完整流程测试成功")
        return True

    except Exception as e:
        print(f"[FAIL] 完整流程测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print(" PsyChat-Pro 系统测试")
    print("=" * 60)

    results = {}

    # 测试各模块
    results["配置模块"] = test_config()
    results["向量存储"] = test_vector_store()
    results["Skill系统"] = test_skills()
    results["Agent系统"] = test_agents()
    results["MCP系统"] = test_mcp()
    results["编排系统"] = test_orchestration()
    results["完整流程"] = asyncio.run(test_full_flow())

    # 汇总结果
    print_header("测试结果汇总")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n所有测试通过! 系统运行正常。")
        return 0
    else:
        print("\n部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PsyChat-Pro - 多智能体心理咨询系统
入口文件
Author: SixpenniesS
"""

import sys
import argparse
import logging
import asyncio
from pathlib import Path

# Windows编码问题修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PsyChat-Pro - 多智能体心理咨询系统"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="启动Web界面（默认）"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="启动命令行交互模式"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="重建知识库"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="显示系统信息"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Web服务主机地址（默认: localhost）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Web服务端口（默认: 8000）"
    )

    args = parser.parse_args()

    # 显示系统信息
    print("=" * 60)
    print("PsyChat-Pro - 多智能体心理咨询系统")
    print("=" * 60)
    print("Author: SixpenniesS")
    print("Version: 1.0.1")
    print("=" * 60)
    print()

    # 处理命令
    if args.info:
        show_system_info()
        return

    if args.rebuild:
        rebuild_knowledge_base()
        return

    if args.cli:
        asyncio.run(run_cli_mode())
        return

    # 默认启动Web界面
    run_web_server(args.host, args.port)


def show_system_info():
    """显示系统信息"""
    print("[系统信息]")
    print("-" * 40)

    try:
        from config import (
            PROJECT_ROOT, DEEPSEEK_MODEL, EMBEDDING_MODEL,
            COLLECTION_NAME, TOP_K_RESULTS, SIMILARITY_THRESHOLD
        )

        print(f"项目路径: {PROJECT_ROOT}")
        print(f"LLM模型: {DEEPSEEK_MODEL}")
        print(f"Embedding模型: {EMBEDDING_MODEL}")
        print(f"向量集合: {COLLECTION_NAME}")
        print(f"检索配置: Top-K={TOP_K_RESULTS}, 阈值={SIMILARITY_THRESHOLD}")

        # 显示知识库信息
        try:
            from core.vector_store import VectorStore
            vs = VectorStore()
            info = vs.get_collection_info()
            print(f"知识库文档数: {info.get('document_count', 0)}")
        except Exception as e:
            print(f"知识库状态: 无法获取 ({str(e)})")

        # 显示Agent信息
        print("\n[可用Agent]")
        agents = ["IntentAgent", "RAGAgent", "ToolAgent", "SkillAgent", "ResponseAgent"]
        for agent in agents:
            print(f"  - {agent}")

        # 显示MCP服务器
        print("\n[MCP服务器]")
        servers = ["filesystem", "database", "search"]
        for server in servers:
            print(f"  - {server}")

        # 显示Skill
        print("\n[Skill列表]")
        skills = ["emotion_analyzer", "crisis_detector"]
        for skill in skills:
            print(f"  - {skill}")

    except Exception as e:
        print(f"获取系统信息失败: {str(e)}")


def rebuild_knowledge_base():
    """重建知识库"""
    print("[重建知识库]")
    print("-" * 40)

    try:
        from core.vector_store import VectorStore
        from data.processor import DataProcessor

        vector_store = VectorStore()
        processor = DataProcessor()

        # 处理文档
        print("正在处理文档...")
        documents = processor.process_documents(
            use_psychology_qa=True,
            use_header_splitting=True
        )

        if not documents:
            print("[错误] 没有找到可处理的文档")
            return

        print(f"处理了 {len(documents)} 个文档块")

        # 清空并重建
        print("清空现有数据...")
        vector_store.clear_collection()

        # 添加文档
        print("添加到向量存储...")
        success = vector_store.add_documents(documents)

        if success:
            info = vector_store.get_collection_info()
            print(f"[完成] 知识库重建完成: {info}")
        else:
            print("[错误] 知识库重建失败")

    except Exception as e:
        print(f"[错误] 重建知识库时出错: {str(e)}")
        import traceback
        traceback.print_exc()


async def run_cli_mode():
    """运行命令行交互模式"""
    print("[命令行交互模式]")
    print("-" * 40)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'info' 查看系统信息")
    print()

    try:
        from orchestration.workflow_orchestrator import WorkflowOrchestrator
        from orchestration.workflow_selector import WorkflowSelector
        from agents import IntentAgent, RAGAgent, SkillAgent, ResponseAgent
        from skills import SkillRegistry, EmotionAnalyzerSkill, CrisisDetectorSkill
        from core.vector_store import VectorStore

        # 初始化
        print("正在初始化系统...")
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

        print("系统初始化完成！")
        print()

        # 对话历史
        conversation_history = []

        while True:
            try:
                user_input = input("你: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("再见！")
                    break

                if user_input.lower() == "info":
                    show_system_info()
                    continue

                # 处理消息
                print("\n处理中...")

                # 1. 意图识别
                intent_result = await agents["intent_agent"].run({
                    "user_message": user_input,
                    "conversation_history": conversation_history
                })
                print(f"意图: {intent_result.data.get('intent')}")
                print(f"主题: {intent_result.data.get('topics')}")

                # 2. 危机检测
                crisis_result = await agents["skill_agent"].run({
                    "skill_calls": [{
                        "skill": "crisis_detector",
                        "params": {"text": user_input}
                    }]
                })
                crisis_data = crisis_result.data.get("skill_results", [{}])[0].get("result", {})
                print(f"风险等级: {crisis_data.get('risk_level', 'unknown')}")

                # 3. RAG检索
                rag_result = await agents["rag_agent"].run({
                    "query": user_input,
                    "topics": intent_result.data.get("topics", [])
                })
                print(f"检索文档数: {rag_result.data.get('total_found', 0)}")

                # 4. 生成响应
                mode = "crisis" if crisis_data.get("risk_level") in ["critical", "high"] else "normal"
                response_result = await agents["response_agent"].run({
                    "user_message": user_input,
                    "rag_context": rag_result.data.get("context_text", ""),
                    "rag_documents": rag_result.data.get("documents", []),
                    "skill_results": {"crisis_detector": crisis_data},
                    "conversation_history": conversation_history,
                    "mode": mode
                })

                response = response_result.data.get("response", "")

                # 更新历史
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})

                # 保持历史长度
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]

                print(f"\n助手: {response}\n")

            except KeyboardInterrupt:
                print("\n\n程序被中断")
                break
            except Exception as e:
                print(f"处理出错: {str(e)}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()


def run_web_server(host: str, port: int):
    """运行Web服务器"""
    print("[启动Web服务]")
    print(f"   地址: http://{host}:{port}")
    print("-" * 40)

    try:
        import uvicorn
        from web.interface import app

        uvicorn.run(app, host=host, port=port)

    except ImportError:
        print("[错误] 缺少依赖：请安装 fastapi 和 uvicorn")
        print("   pip install fastapi uvicorn[standard]")
    except Exception as e:
        print(f"[错误] 启动Web服务失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

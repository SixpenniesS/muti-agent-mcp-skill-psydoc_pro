#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PsyChat-Pro Web界面
基于FastAPI提供美观的Web界面，支持工作流状态显示
Author: SixpenniesS
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import *

# 创建FastAPI应用
app = FastAPI(title="PsyChat-Pro", version="1.0.0")

# 全局组件实例
orchestrator = None
workflow_selector = None
agents = {}
conversation_histories: Dict[str, List[Dict]] = {}


def init_system():
    """初始化系统组件"""
    global orchestrator, workflow_selector, agents

    try:
        from orchestration.workflow_orchestrator import WorkflowOrchestrator
        from orchestration.workflow_selector import WorkflowSelector
        from agents import IntentAgent, RAGAgent, SkillAgent, ResponseAgent
        from skills import SkillRegistry, EmotionAnalyzerSkill, CrisisDetectorSkill
        from mcp import MCPGateway, FilesystemMCP, DatabaseMCP
        from core.vector_store import VectorStore

        print("正在初始化系统组件...")

        # 向量存储
        vector_store = VectorStore()

        # Skill注册表
        skill_registry = SkillRegistry()
        skill_registry.register(EmotionAnalyzerSkill())
        skill_registry.register(CrisisDetectorSkill())

        # MCP网关
        mcp_gateway = MCPGateway()
        mcp_gateway.register_server(FilesystemMCP(STORAGE_PATH))
        mcp_gateway.register_server(DatabaseMCP(DATABASE_PATH))

        # 创建ToolAgent（需要mcp_gateway）
        from agents import ToolAgent
        tool_agent = ToolAgent(mcp_gateway)

        # 创建Agent
        agents = {
            "intent_agent": IntentAgent(),
            "rag_agent": RAGAgent(vector_store),
            "skill_agent": SkillAgent(skill_registry),
            "tool_agent": tool_agent,
            "response_agent": ResponseAgent()
        }

        # 工作流调度器
        orchestrator = WorkflowOrchestrator(agents)
        workflow_selector = WorkflowSelector(orchestrator)

        print("✅ 系统组件初始化完成")
        return True

    except Exception as e:
        print(f"❌ 系统初始化失败: {str(e)}")
        return False


# ============================================================================
# HTML模板
# ============================================================================

def get_web_interface():
    """生成Web界面HTML"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PsyChat-Pro - 多智能体心理咨询系统</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 20px;
            min-height: 100vh;
        }

        .main-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .header {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .header h1 {
            font-size: 1.5em;
            font-weight: 600;
            color: #fff;
            margin-bottom: 5px;
        }

        .header p {
            font-size: 0.9em;
            color: #888;
        }

        .chat-container {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            flex: 1;
            display: flex;
            flex-direction: column;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            min-height: 400px;
        }

        .message {
            margin-bottom: 15px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-user {
            text-align: right;
        }

        .message-user .bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 18px 18px 4px 18px;
            padding: 12px 18px;
            display: inline-block;
            max-width: 80%;
            text-align: left;
        }

        .message-assistant .bubble {
            background: rgba(255,255,255,0.1);
            border-radius: 18px 18px 18px 4px;
            padding: 15px 20px;
            display: inline-block;
            max-width: 85%;
            text-align: left;
            border-left: 3px solid #667eea;
        }

        .workflow-info {
            margin-top: 10px;
            padding: 10px;
            background: rgba(102,126,234,0.1);
            border-radius: 10px;
            font-size: 0.85em;
        }

        .workflow-info .step {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .workflow-info .step:last-child {
            border-bottom: none;
        }

        .step-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
        }

        .step-pending { background: rgba(255,255,255,0.1); color: #888; }
        .step-running { background: #ffc107; color: #000; animation: pulse 1s infinite; }
        .step-success { background: #4caf50; color: #fff; }
        .step-failed { background: #f44336; color: #fff; }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .input-area {
            padding: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        .input-form {
            display: flex;
            gap: 10px;
        }

        .message-input {
            flex: 1;
            padding: 12px 18px;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 25px;
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: 1em;
            resize: none;
            outline: none;
        }

        .message-input:focus {
            border-color: #667eea;
        }

        .send-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 1.2em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(102,126,234,0.4);
        }

        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* 侧边栏 */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .panel {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .panel-title {
            font-size: 1em;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .agent-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .agent-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            font-size: 0.9em;
        }

        .agent-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .status-idle { background: #888; }
        .status-running { background: #ffc107; }
        .status-success { background: #4caf50; }
        .status-failed { background: #f44336; }

        .mcp-tools {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .tool-badge {
            padding: 5px 12px;
            background: rgba(102,126,234,0.2);
            border-radius: 15px;
            font-size: 0.8em;
            color: #a0a0ff;
        }

        .skill-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .skill-item {
            padding: 8px 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            font-size: 0.85em;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .loading.show {
            display: block;
        }

        .spinner {
            width: 30px;
            height: 30px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* 响应式 */
        @media (max-width: 900px) {
            .container {
                grid-template-columns: 1fr;
            }
            .sidebar {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-panel">
            <div class="header">
                <h1>🧠 PsyChat-Pro</h1>
                <p>多智能体心理咨询系统 | 基于工作流编排 + MCP + Skill</p>
            </div>

            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message message-assistant">
                        <div class="bubble">
                            👋 你好！我是PsyChat-Pro多智能体心理咨询系统。<br><br>
                            我由多个专业Agent组成，可以为你提供：<br>
                            • 🎯 意图识别与主题分类<br>
                            • 📚 心理学知识检索<br>
                            • 🔍 情绪分析与危机检测<br>
                            • 💬 专业心理咨询回复<br><br>
                            有什么我可以帮助你的吗？
                        </div>
                    </div>
                </div>

                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <div>正在处理...</div>
                </div>

                <div class="input-area">
                    <form class="input-form" onsubmit="return sendMessage(event)">
                        <textarea
                            id="messageInput"
                            class="message-input"
                            placeholder="输入你想说的..."
                            rows="2"
                            onkeydown="handleKey(event)"
                        ></textarea>
                        <button type="submit" class="send-btn" id="sendBtn">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <div class="sidebar">
            <div class="panel">
                <div class="panel-title"><i class="fas fa-robot"></i> Agent状态</div>
                <div class="agent-list" id="agentList">
                    <div class="agent-item">
                        <div class="agent-status status-idle"></div>
                        <span>IntentAgent</span>
                        <span style="margin-left:auto;color:#888">意图识别</span>
                    </div>
                    <div class="agent-item">
                        <div class="agent-status status-idle"></div>
                        <span>RAGAgent</span>
                        <span style="margin-left:auto;color:#888">知识检索</span>
                    </div>
                    <div class="agent-item">
                        <div class="agent-status status-idle"></div>
                        <span>SkillAgent</span>
                        <span style="margin-left:auto;color:#888">技能执行</span>
                    </div>
                    <div class="agent-item">
                        <div class="agent-status status-idle"></div>
                        <span>ResponseAgent</span>
                        <span style="margin-left:auto;color:#888">响应生成</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title"><i class="fas fa-plug"></i> MCP工具</div>
                <div class="mcp-tools">
                    <span class="tool-badge">filesystem</span>
                    <span class="tool-badge">database</span>
                    <span class="tool-badge">search</span>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title"><i class="fas fa-magic"></i> Skill系统</div>
                <div class="skill-list">
                    <div class="skill-item">📊 emotion_analyzer - 情绪分析</div>
                    <div class="skill-item">⚠️ crisis_detector - 危机检测</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const messagesEl = document.getElementById('messages');
        const loadingEl = document.getElementById('loading');
        const inputEl = document.getElementById('messageInput');
        const sendBtnEl = document.getElementById('sendBtn');

        function handleKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(e);
            }
        }

        async function sendMessage(e) {
            e.preventDefault();
            const text = inputEl.value.trim();
            if (!text) return;

            // 添加用户消息
            addMessage(text, 'user');
            inputEl.value = '';

            // 显示加载
            loadingEl.classList.add('show');
            sendBtnEl.disabled = true;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'message=' + encodeURIComponent(text)
                });

                const result = await response.json();

                // 添加助手消息
                addMessage(result.response, 'assistant', result.workflow_info);

            } catch (error) {
                addMessage('抱歉，发生了错误，请稍后重试。', 'assistant');
            }

            loadingEl.classList.remove('show');
            sendBtnEl.disabled = false;
        }

        function addMessage(content, sender, workflowInfo) {
            const div = document.createElement('div');
            div.className = 'message message-' + sender;

            let html = '<div class="bubble">' + formatContent(content) + '</div>';

            if (workflowInfo) {
                html += '<div class="workflow-info">';
                html += '<strong>🔄 工作流: ' + workflowInfo.workflow_id + '</strong><br>';
                html += '<small>执行步骤: ' + workflowInfo.steps_completed + '/' + workflowInfo.total_steps + '</small><br>';

                if (workflowInfo.agents_called && workflowInfo.agents_called.length > 0) {
                    html += '<div style="margin-top:8px">';
                    workflowInfo.agents_called.forEach(agent => {
                        const icon = agent.success ? '✅' : '❌';
                        html += '<span style="margin-right:10px">' + icon + ' ' + agent.name + '</span>';
                    });
                    html += '</div>';
                }

                if (workflowInfo.skills_used && workflowInfo.skills_used.length > 0) {
                    html += '<div style="margin-top:5px;color:#a0a0ff">';
                    html += '<small>Skills: ' + workflowInfo.skills_used.join(', ') + '</small>';
                    html += '</div>';
                }

                html += '</div>';
            }

            div.innerHTML = html;
            messagesEl.appendChild(div);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function formatContent(text) {
            // 简单的Markdown格式化
            return text
                .replace(/\\n/g, '<br>')
                .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.+?)\\*/g, '<em>$1</em>');
        }
    </script>
</body>
</html>
    """
    return html_content


# ============================================================================
# API路由
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    init_system()


@app.get("/", response_class=HTMLResponse)
async def index():
    """主页面"""
    return get_web_interface()


@app.post("/chat")
async def chat(message: str = Form(...), user_id: str = Form(default="default")):
    """处理聊天请求"""
    global orchestrator, workflow_selector, agents

    if not orchestrator:
        raise HTTPException(status_code=500, detail="系统未初始化")

    try:
        # 获取对话历史
        history = conversation_histories.get(user_id, [])

        # 1. 意图识别
        intent_result = await agents["intent_agent"].run({
            "user_message": message,
            "conversation_history": history
        })

        # 2. 危机检测
        crisis_result = await agents["skill_agent"].run({
            "skill_calls": [{
                "skill": "crisis_detector",
                "params": {"text": message, "history": history}
            }]
        })

        crisis_data = {}
        if crisis_result.success and crisis_result.data.get("skill_results"):
            crisis_data = crisis_result.data["skill_results"][0].get("result", {})

        # 3. 工具调用检测（新增）
        tool_call_info = intent_result.data.get("tool_call")
        tool_result = None

        if tool_call_info:
            # 检测到工具调用意图，调用ToolAgent
            print(f"[工具调用] 检测到: {tool_call_info.get('tool_type')}")

            # 根据工具类型准备参数
            tool_params = _prepare_tool_params(tool_call_info, message, user_id, history)

            # 调用ToolAgent
            tool_result = await agents["tool_agent"].run({
                "tool_calls": [{
                    "server": tool_call_info["server"],
                    "tool": tool_call_info["tool"],
                    "params": tool_params
                }]
            })

            print(f"[工具调用] 结果: {tool_result.success}")

        # 4. 选择工作流
        workflow_id = workflow_selector.select(
            intent_result.data,
            crisis_data,
            message
        )

        # 5. RAG检索（非工具调用时）
        rag_result = None
        if not tool_call_info:
            rag_result = await agents["rag_agent"].run({
                "query": message,
                "topics": intent_result.data.get("topics", [])
            })

        # 6. 生成响应
        mode = "crisis" if crisis_data.get("risk_level") in ["critical", "high"] else "normal"

        # 如果有工具调用结果，传递给ResponseAgent
        skill_results_for_response = {
            "crisis_detector": crisis_data,
            "emotion_analyzer": {}
        }
        if tool_result and tool_result.success:
            skill_results_for_response["tool_result"] = tool_result.data

        response_result = await agents["response_agent"].run({
            "user_message": message,
            "rag_context": rag_result.data.get("context_text", "") if rag_result else "",
            "rag_documents": rag_result.data.get("documents", []) if rag_result else [],
            "skill_results": skill_results_for_response,
            "conversation_history": history,
            "mode": mode,
            "tool_call": tool_call_info  # 新增：传递工具调用信息
        })

        # 构建响应
        response_text = response_result.data.get("response", "")

        # 更新对话历史
        if user_id not in conversation_histories:
            conversation_histories[user_id] = []

        conversation_histories[user_id].append({"role": "user", "content": message})
        conversation_histories[user_id].append({"role": "assistant", "content": response_text})

        # 保持历史长度
        if len(conversation_histories[user_id]) > 20:
            conversation_histories[user_id] = conversation_histories[user_id][-20:]

        # 构建工作流信息
        agents_called = [
            {"name": "IntentAgent", "success": intent_result.success},
            {"name": "SkillAgent", "success": crisis_result.success},
        ]
        if tool_result:
            agents_called.append({"name": "ToolAgent", "success": tool_result.success})
        if rag_result:
            agents_called.append({"name": "RAGAgent", "success": rag_result.success})
        agents_called.append({"name": "ResponseAgent", "success": response_result.success})

        # 构建skills_used列表
        skills_used = ["crisis_detector"]
        if tool_call_info:
            skills_used.append(f"tool:{tool_call_info.get('tool_type', 'unknown')}")

        workflow_info = {
            "workflow_id": workflow_id,
            "steps_completed": len(agents_called),
            "total_steps": len(agents_called),
            "agents_called": agents_called,
            "skills_used": skills_used,
            "risk_level": crisis_data.get("risk_level", "low"),
            "tool_called": tool_call_info is not None
        }

        return {
            "success": True,
            "response": response_text,
            "workflow_info": workflow_info
        }

    except Exception as e:
        print(f"❌ 处理请求失败: {str(e)}")
        return {
            "success": False,
            "response": f"处理请求时出错: {str(e)}",
            "workflow_info": None
        }


@app.get("/agents/status")
async def get_agents_status():
    """获取所有Agent状态"""
    global agents

    if not agents:
        return {"agents": []}

    status_list = []
    for name, agent in agents.items():
        status_list.append({
            "name": name,
            "status": agent.status.value,
            "execution_count": len(agent.get_execution_history())
        })

    return {"agents": status_list}


def _prepare_tool_params(tool_call_info: dict, message: str, user_id: str, history: list) -> dict:
    """准备工具调用参数（新增）

    Args:
        tool_call_info: 工具调用信息
        message: 用户消息
        user_id: 用户ID
        history: 对话历史

    Returns:
        工具参数字典
    """
    tool_type = tool_call_info.get("tool_type")

    if tool_type == "generate_report":
        # 生成报告：使用对话历史生成报告内容
        from config import STORAGE_PATH
        import os
        reports_dir = os.path.join(STORAGE_PATH, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        return {
            "path": os.path.join(reports_dir, f"{user_id}_report.md"),
            "content": _generate_report_content(user_id, history)
        }

    elif tool_type == "query_history":
        # 查询历史记录
        return {
            "user_id": user_id,
            "limit": 10
        }

    elif tool_type == "save_conversation":
        # 保存对话
        return {
            "user_id": user_id,
            "conversation": history[-10:] if history else []  # 最近10轮
        }

    elif tool_type == "search_resources":
        # 搜索资源
        return {
            "query": message,
            "top_k": 5
        }

    return {}


def _generate_report_content(user_id: str, history: list) -> str:
    """生成报告内容

    Args:
        user_id: 用户ID
        history: 对话历史

    Returns:
        报告内容（Markdown格式）
    """
    from datetime import datetime

    # 分析对话历史
    topics_discussed = set()
    emotions_detected = []

    for msg in history:
        if msg.get("role") == "user":
            # 简单的主题提取（可以从IntentAgent获取更准确的）
            content = msg.get("content", "").lower()
            topic_keywords = ["焦虑", "抑郁", "压力", "人际", "家庭", "工作", "情绪"]
            for kw in topic_keywords:
                if kw in content:
                    topics_discussed.add(kw)

    # 生成报告
    report = f"""# 心理咨询记录报告

## 基本信息
- 用户ID: {user_id}
- 报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- 对话轮数: {len([m for m in history if m.get("role") == "user"])}

## 咨询主题
{chr(10).join([f'- {t}' for t in topics_discussed]) if topics_discussed else '- 日常交流'}

## 对话摘要
本次咨询共进行了 {len([m for m in history if m.get("role") == "user"])} 轮对话。

## 建议
- 建议继续关注情绪状态
- 如有需要，可寻求专业帮助

---
*本报告由 PsyChat-Pro 自动生成*
"""
    return report


@app.get("/mcp/tools")
async def get_mcp_tools():
    """获取MCP工具列表"""
    return {
        "servers": {
            "filesystem": ["read_file", "write_file", "list_files", "delete_file"],
            "database": ["query_user_history", "save_conversation", "log_crisis_event"],
            "search": ["search", "get_resources_by_topic"]
        }
    }


@app.get("/skills")
async def get_skills():
    """获取Skill列表"""
    return {
        "skills": [
            {"name": "emotion_analyzer", "description": "分析用户输入的情绪倾向和强度"},
            {"name": "crisis_detector", "description": "检测用户输入中的危机信号和风险等级"}
        ]
    }


@app.get("/knowledge/info")
async def get_knowledge_info():
    """获取知识库信息"""
    try:
        from core.vector_store import VectorStore
        vs = VectorStore()
        info = vs.get_collection_info()
        return {"success": True, "info": info}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """启动Web服务"""
    print("=" * 60)
    print("🌐 PsyChat-Pro Web服务")
    print("=" * 60)
    print(f"地址: http://localhost:8000")
    print("=" * 60)

    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()

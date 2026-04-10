# -*- coding: utf-8 -*-
"""
响应生成Agent
整合信息，生成最终回答
Author: SixpenniesS
"""

from typing import Dict, Any, List, Optional
import requests

from agents.base_agent import BaseAgent, AgentResult
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    PROMPTS_DIR
)


class ResponseAgent(BaseAgent):
    """响应生成Agent

    整合信息，生成最终回答。

    功能：
    - 整合RAG上下文、Skill结果、工具结果
    - 构建提示词
    - 调用LLM生成回答
    - 提取来源信息
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化响应生成Agent

        Args:
            config: Agent配置
        """
        super().__init__("ResponseAgent", config)
        self.api_key = DEEPSEEK_API_KEY
        self.llm_url = f"{DEEPSEEK_BASE_URL}/chat/completions"
        self.model = self.config.get("model", DEEPSEEK_MODEL)
        self.temperature = self.config.get("temperature", 0.6)
        self.max_tokens = self.config.get("max_tokens", 1000)

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """生成响应

        Args:
            context: {
                "user_message": str,
                "rag_context": str (可选),
                "rag_documents": List[Dict] (可选),
                "skill_results": Dict (可选),
                "tool_results": Dict (可选),
                "conversation_history": List[Dict] (可选),
                "mode": str (可选, "normal"|"crisis")
            }

        Returns:
            AgentResult: {
                "response": str,
                "sources": List[Dict],
                "used_rag": bool,
                "used_skills": List[str]
            }
        """
        user_message = context.get("user_message", "")

        if not user_message:
            return AgentResult(
                success=False,
                data={},
                error="user_message is required"
            )

        try:
            # 1. 判断模式
            mode = context.get("mode", "normal")
            is_crisis_mode = mode == "crisis"

            # 2. 检查是否有工具调用结果（新增）
            tool_call = context.get("tool_call")
            tool_result = context.get("skill_results", {}).get("tool_result")

            # 3. 如果有工具调用结果，生成工具相关响应
            prompt = ""  # 初始化prompt变量
            if tool_call and tool_result:
                response = self._build_tool_response(tool_call, tool_result, user_message)
                prompt = "[工具调用响应，无LLM调用]"
            elif is_crisis_mode:
                prompt = self._build_crisis_prompt(context)
                response = await self._call_llm(prompt, user_message, context.get("conversation_history", []))
            elif context.get("rag_context"):
                prompt = self._build_rag_prompt(context)
                response = await self._call_llm(prompt, user_message, context.get("conversation_history", []))
            else:
                prompt = self._build_direct_prompt(context)
                response = await self._call_llm(prompt, user_message, context.get("conversation_history", []))

            # 4. 提取来源信息
            sources = self._extract_sources(context)

            # 5. 获取使用的技能列表
            used_skills = []
            skill_results = context.get("skill_results", {})
            if skill_results:
                used_skills = list(skill_results.keys())

            return AgentResult(
                success=True,
                data={
                    "response": response,
                    "sources": sources,
                    "used_rag": bool(context.get("rag_context")),
                    "used_skills": used_skills,
                    "mode": mode
                },
                metadata={
                    "agent": self.name,
                    "prompt_length": len(prompt),
                    "response_length": len(response)
                }
            )

        except Exception as e:
            self.logger.error(f"响应生成失败: {str(e)}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _build_rag_prompt(self, context: Dict) -> str:
        """构建RAG提示词"""
        user_message = context.get("user_message", "")
        rag_context = context.get("rag_context", "")
        skill_results = context.get("skill_results", {})
        expanded_contexts = context.get("expanded_contexts", [])

        parts = []

        # 系统角色
        parts.append("你是一位专业的心理咨询师。请参照以下案例中咨询师的说话方式来回应用户，但内容必须针对用户的具体情况。")

        # 完整案例参考
        if expanded_contexts:
            parts.append("\n【完整咨询案例参考】")
            parts.append("以下是完整的咨询对话流程，帮助你理解咨询师从开场到结束的处理节奏：")
            for i, ctx in enumerate(expanded_contexts[:2], 1):
                conv = ctx.get("full_conversation", "")
                if len(conv) > 2000:
                    conv = conv[:2000] + "\n...（对话继续）"
                parts.append(f"\n--- 案例{i}（{ctx.get('topic', '')}） ---")
                parts.append(conv)

        # RAG上下文
        if rag_context:
            parts.append(f"\n【与用户问题最匹配的对话片段】\n{rag_context}")

        # 技能分析结果
        if skill_results:
            parts.append("\n【辅助分析结果】")
            for skill_name, result in skill_results.items():
                if result.get("success") and result.get("result"):
                    parts.append(f"- {skill_name}: {result['result']}")

        # 回应策略
        parts.append("""
【回应策略】
1. 先判断当前对话所处阶段（初次倾诉/深入探索/引导反思/行动建议），选择匹配的策略
2. 规划下一步：考虑用什么问题或角度引导用户更深入地表达或反思
3. 严格模仿参考案例中咨询师的表达方式和节奏

【回答要求】
- 保持简短（1-5句话）
- 以用户的具体情况为核心，不要混入案例中的情节
- 语气温暖自然，体现共情和理解
- 不要提及参考案例，直接回应用户""")

        return "\n".join(parts)

    def _build_direct_prompt(self, context: Dict) -> str:
        """构建直接回答提示词（无RAG）"""
        user_message = context.get("user_message", "")
        skill_results = context.get("skill_results", {})

        parts = []

        parts.append("""你是一位精通理情行为疗法（Rational Emotive Behavior Therapy，简称REBT）的心理咨询师，能够合理地采用理情行为疗法给来访者提供专业的指导和支持，缓解来访者的负面情绪和行为反应，帮助他们实现个人成长和心理健康。

理情行为治疗主要包括以下几个阶段：
（1）**检查非理性信念和自我挫败式思维**：帮助来访者探查隐藏在情绪困扰后面的原因
（2）**与非理性信念辩论**：帮助来访者向非理性信念质疑发难
（3）**得出合理信念，学会理性思维**：帮助来访者找出理性的信念
（4）**迁移应用治疗收获**：鼓励来访者内化成个人的生活态度""")

        # 技能分析结果
        if skill_results:
            parts.append("\n【辅助分析结果】")
            for skill_name, result in skill_results.items():
                if result.get("success") and result.get("result"):
                    parts.append(f"- {skill_name}: {result['result']}")

        parts.append("""
回答要求:
- 保持简短（1-5句话）
- 运用REBT理论，帮助来访者识别和质疑非理性信念
- 以温暖、理解、非评判的语气回应
- 以鼓励和引导为主，而非直接给建议
- 用问题引导用户思考和自我反省
- 体现共情和理解，具有专业性

请用中文回答，语气要亲切自然。""")

        return "\n".join(parts)

    def _build_crisis_prompt(self, context: Dict) -> str:
        """构建危机干预提示词"""
        user_message = context.get("user_message", "")
        rag_context = context.get("rag_context", "")
        skill_results = context.get("skill_results", {})

        parts = []

        parts.append("""你是一位专业的心理危机干预专家。当前用户可能正在经历心理危机，需要你的紧急支持和帮助。

【危机干预原则】
1. 保持冷静和专业
2. 表达真诚的关心和理解
3. 不要忽视或轻视用户的感受
4. 提供具体的帮助资源
5. 鼓励寻求专业帮助

【重要】
- 如果用户表达自杀或自伤念头，必须提供紧急求助热线
- 不要给出可能导致伤害的建议
- 引导用户寻求专业帮助""")

        # 危机评估结果
        if skill_results.get("crisis_detector"):
            crisis_result = skill_results["crisis_detector"].get("result", {})
            parts.append(f"\n【危机评估结果】")
            parts.append(f"- 风险等级: {crisis_result.get('risk_level', 'unknown')}")
            parts.append(f"- 风险分数: {crisis_result.get('risk_score', 0)}")
            if crisis_result.get("intervention_suggestion"):
                parts.append(f"- 干预建议: {crisis_result.get('intervention_suggestion')}")

        # 紧急资源
        parts.append("""
【紧急求助资源】
- 全国心理援助热线: 400-161-9995
- 北京心理危机研究与干预中心: 010-82951332
- 生命热线: 400-821-1215

回答要求:
- 表达真诚的关心和理解
- 提供紧急求助热线
- 鼓励用户寻求专业帮助
- 不要忽视用户的感受
- 保持温暖和支持性的语气""")

        if rag_context:
            parts.append(f"\n【参考资源】\n{rag_context[:1000]}")

        return "\n".join(parts)

    async def _call_llm(
        self,
        prompt: str,
        user_message: str,
        history: List[Dict]
    ) -> str:
        """调用LLM生成回答"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 构建消息列表
            messages = [{"role": "system", "content": prompt}]

            # 添加对话历史（最近6轮）
            if history:
                for msg in history[-12:]:
                    role = msg.get("role")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        messages.append({"role": role, "content": content})

            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})

            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9
            }

            response = requests.post(self.llm_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]

            return "抱歉，我无法生成有效的回答。"

        except Exception as e:
            self.logger.error(f"LLM调用失败: {str(e)}")
            return f"处理请求时出错: {str(e)}"

    def _extract_sources(self, context: Dict) -> List[Dict]:
        """提取来源信息"""
        sources = []
        rag_documents = context.get("rag_documents", [])

        for doc in rag_documents:
            metadata = doc.get("metadata", {})
            sources.append({
                "source": metadata.get("source", ""),
                "topic": metadata.get("topic", ""),
                "qa_id": metadata.get("qa_id", ""),
                "similarity": doc.get("similarity", 0)
            })

        return sources

    def _build_tool_response(self, tool_call: Dict, tool_result: Dict, user_message: str) -> str:
        """构建工具调用响应（新增）

        Args:
            tool_call: 工具调用信息
            tool_result: 工具执行结果
            user_message: 用户原始消息

        Returns:
            响应文本
        """
        tool_type = tool_call.get("tool_type", "unknown")
        description = tool_call.get("description", "工具操作")

        # 检查工具执行是否成功
        if tool_result and tool_result.get("success"):
            result_data = tool_result.get("tool_results", [{}])[0].get("result", {})

            if tool_type == "generate_report":
                return f"""我已经为您生成了心理咨询报告。

📋 **报告已保存至**: `storage/reports/`

报告内容包括:
- 咨询基本信息
- 讨论主题汇总
- 对话摘要

您可以随时查看这份报告，也可以继续和我交流。"""

            elif tool_type == "query_history":
                records = result_data.get("records", [])
                if records:
                    summary = f"我找到了您的 {len(records)} 条咨询记录：\n\n"
                    for i, record in enumerate(records[:5], 1):
                        summary += f"{i}. {record.get('date', '未知日期')} - {record.get('topic', '日常咨询')}\n"
                    return summary
                else:
                    return "目前还没有找到您的咨询记录。我们可以开始新的对话！"

            elif tool_type == "save_conversation":
                return """✅ 对话已成功保存！

您的重要谈话内容已经安全存储，您可以：
- 随时回顾这段对话
- 在未来的咨询中延续这个话题
- 生成咨询报告

还有什么我可以帮助您的吗？"""

            elif tool_type == "search_resources":
                resources = result_data.get("resources", [])
                if resources:
                    response = "我为您找到了以下相关资源：\n\n"
                    for i, res in enumerate(resources[:3], 1):
                        response += f"{i}. **{res.get('title', '资源')}**\n   {res.get('summary', '')[:100]}...\n\n"
                    return response
                else:
                    return "抱歉，暂时没有找到完全匹配的资源。您可以换个关键词试试？"

            # 默认成功响应
            return f"✅ {description}已完成！还有其他需要帮助的吗？"

        else:
            # 工具执行失败
            error_msg = ""
            if tool_result:
                error_msg = tool_result.get("error", "") or tool_result.get("tool_results", [{}])[0].get("error", "")

            return f"""抱歉，{description}时遇到了一些问题。

{f"错误信息: {error_msg}" if error_msg else "请稍后再试，或联系管理员。"}

您可以换一种方式描述您的需求，我会尽力帮助您。"""

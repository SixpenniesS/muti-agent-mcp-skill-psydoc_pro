# -*- coding: utf-8 -*-
"""
工具调用Agent
统一管理MCP工具调用
Author: SixpenniesS
"""

from typing import Dict, Any, List
import asyncio

from agents.base_agent import BaseAgent, AgentResult


class ToolAgent(BaseAgent):
    """工具调用Agent

    统一管理MCP工具调用。

    功能：
    - 调用文件系统MCP
    - 调用数据库MCP
    - 调用搜索引擎MCP
    - 批量工具调用支持
    """

    def __init__(self, mcp_gateway, config: Dict[str, Any] = None):
        """初始化工具调用Agent

        Args:
            mcp_gateway: MCP网关实例
            config: Agent配置
        """
        super().__init__("ToolAgent", config)
        self.mcp_gateway = mcp_gateway

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行工具调用

        Args:
            context: {
                "tool_calls": List[Dict] 或 单个 Dict
                "parallel": bool (可选，是否并行执行，默认True)
            }

            tool_call格式:
            {
                "server": "filesystem|database|search",
                "tool": "工具名称",
                "params": {...}
            }

        Returns:
            AgentResult: {
                "tool_results": List[Dict],
                "success_count": int,
                "failure_count": int
            }
        """
        tool_calls = context.get("tool_calls", [])
        parallel = context.get("parallel", True)

        # 支持单个工具调用
        if isinstance(tool_calls, dict):
            tool_calls = [tool_calls]

        if not tool_calls:
            return AgentResult(
                success=True,
                data={"tool_results": [], "success_count": 0, "failure_count": 0},
                metadata={"agent": self.name, "tool_count": 0}
            )

        try:
            if parallel:
                results = await self._parallel_call_tools(tool_calls)
            else:
                results = await self._sequential_call_tools(tool_calls)

            success_count = sum(1 for r in results if r.get("success", False))
            failure_count = len(results) - success_count

            return AgentResult(
                success=failure_count == 0,
                data={
                    "tool_results": results,
                    "success_count": success_count,
                    "failure_count": failure_count
                },
                metadata={
                    "agent": self.name,
                    "tool_count": len(tool_calls),
                    "parallel": parallel
                }
            )

        except Exception as e:
            self.logger.error(f"工具调用失败: {str(e)}")
            return AgentResult(
                success=False,
                data={"tool_results": [], "success_count": 0, "failure_count": len(tool_calls)},
                error=str(e)
            )

    async def _parallel_call_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """并行调用多个工具

        Args:
            tool_calls: 工具调用列表

        Returns:
            结果列表
        """
        tasks = [self._call_single_tool(call) for call in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_call": tool_calls[i]
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _sequential_call_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """顺序调用多个工具

        Args:
            tool_calls: 工具调用列表

        Returns:
            结果列表
        """
        results = []
        for call in tool_calls:
            result = await self._call_single_tool(call)
            results.append(result)
        return results

    async def _call_single_tool(self, tool_call: Dict) -> Dict:
        """调用单个工具

        Args:
            tool_call: 工具调用配置

        Returns:
            调用结果
        """
        server = tool_call.get("server")
        tool = tool_call.get("tool")
        params = tool_call.get("params", {})

        if not server or not tool:
            return {
                "success": False,
                "error": "Missing server or tool name",
                "tool_call": tool_call
            }

        try:
            self.logger.info(f"调用MCP工具: {server}.{tool}")
            result = await self.mcp_gateway.call_tool(server, tool, params)

            return {
                "success": result.get("success", True),
                "server": server,
                "tool": tool,
                "result": result
            }

        except Exception as e:
            self.logger.error(f"工具调用异常 {server}.{tool}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "server": server,
                "tool": tool
            }

    async def list_available_tools(self) -> Dict[str, List[Dict]]:
        """列出所有可用工具

        Returns:
            按服务器分组的工具列表
        """
        return await self.mcp_gateway.list_all_tools()

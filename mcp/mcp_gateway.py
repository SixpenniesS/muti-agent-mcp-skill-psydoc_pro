# -*- coding: utf-8 -*-
"""
MCP网关
统一管理多个MCP服务器
Author: SixpenniesS
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class MCPServer(ABC):
    """MCP服务器基类

    定义MCP服务器的标准接口。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """服务器名称"""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具

        Returns:
            工具定义列表，每个工具包含:
            - name: 工具名称
            - description: 工具描述
            - inputSchema: 输入参数JSON Schema
        """
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果
        """
        pass

    async def initialize(self) -> bool:
        """初始化服务器（可选实现）

        Returns:
            初始化是否成功
        """
        return True

    async def shutdown(self) -> None:
        """关闭服务器（可选实现）"""
        pass


class MCPGateway:
    """MCP网关

    统一管理多个MCP服务器，提供一致的调用接口。

    功能：
    - 注册和管理多个MCP服务器
    - 列出所有服务器的工具
    - 调用指定服务器的工具
    """

    def __init__(self):
        """初始化MCP网关"""
        self.servers: Dict[str, MCPServer] = {}
        self.logger = logging.getLogger("mcp.gateway")

    def register_server(self, server: MCPServer) -> None:
        """注册MCP服务器

        Args:
            server: MCP服务器实例
        """
        self.servers[server.name] = server
        self.logger.info(f"注册MCP服务器: {server.name}")

    def get_server(self, name: str) -> Optional[MCPServer]:
        """获取MCP服务器

        Args:
            name: 服务器名称

        Returns:
            服务器实例或None
        """
        return self.servers.get(name)

    async def initialize_all(self) -> Dict[str, bool]:
        """初始化所有服务器

        Returns:
            各服务器初始化结果
        """
        results = {}
        for name, server in self.servers.items():
            try:
                success = await server.initialize()
                results[name] = success
                self.logger.info(f"MCP服务器 {name} 初始化: {'成功' if success else '失败'}")
            except Exception as e:
                results[name] = False
                self.logger.error(f"MCP服务器 {name} 初始化异常: {str(e)}")

        return results

    async def shutdown_all(self) -> None:
        """关闭所有服务器"""
        for name, server in self.servers.items():
            try:
                await server.shutdown()
                self.logger.info(f"MCP服务器 {name} 已关闭")
            except Exception as e:
                self.logger.error(f"MCP服务器 {name} 关闭异常: {str(e)}")

    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """列出所有服务器的工具

        Returns:
            按服务器分组的工具列表
        """
        result = {}
        for name, server in self.servers.items():
            try:
                tools = await server.list_tools()
                result[name] = tools
            except Exception as e:
                self.logger.error(f"获取服务器 {name} 工具列表失败: {str(e)}")
                result[name] = []

        return result

    async def call_tool(
        self,
        server: str,
        tool: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用指定服务器的工具

        Args:
            server: 服务器名称
            tool: 工具名称
            params: 工具参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 服务器不存在
        """
        if server not in self.servers:
            raise ValueError(f"MCP服务器 '{server}' 不存在")

        server_instance = self.servers[server]
        self.logger.info(f"调用MCP工具: {server}.{tool}")

        try:
            result = await server_instance.call_tool(tool, params)
            return result
        except Exception as e:
            self.logger.error(f"MCP工具调用失败 {server}.{tool}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_server_names(self) -> List[str]:
        """获取所有服务器名称"""
        return list(self.servers.keys())

    def get_server_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务器信息"""
        return {
            name: {
                "name": name,
                "tools_count": len(server.list_tools.__code__.co_consts)  # 简化版
            }
            for name, server in self.servers.items()
        }

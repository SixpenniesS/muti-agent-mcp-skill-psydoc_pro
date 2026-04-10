# -*- coding: utf-8 -*-
"""
文件系统MCP服务器
提供文件读写、目录管理等功能
Author: SixpenniesS
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from mcp.mcp_gateway import MCPServer
import logging

logger = logging.getLogger(__name__)


class FilesystemMCP(MCPServer):
    """文件系统MCP服务器

    提供文件系统操作能力：
    - 读写文件
    - 列出目录
    - 删除文件
    """

    def __init__(self, base_path: str):
        """初始化文件系统MCP

        Args:
            base_path: 基础路径（所有文件操作都在此路径下）
        """
        self._name = "filesystem"
        self.base_path = Path(base_path)
        self.logger = logging.getLogger("mcp.filesystem")

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> bool:
        """初始化：创建必要的目录"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            (self.base_path / "reports").mkdir(exist_ok=True)
            (self.base_path / "progress").mkdir(exist_ok=True)
            self.logger.info(f"文件系统MCP初始化完成: {self.base_path}")
            return True
        except Exception as e:
            self.logger.error(f"文件系统MCP初始化失败: {str(e)}")
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        return [
            {
                "name": "read_file",
                "description": "读取文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于基础路径）"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "写入文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于基础路径）"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_files",
                "description": "列出目录中的文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "目录路径（相对于基础路径），默认为根目录"
                        }
                    }
                }
            },
            {
                "name": "delete_file",
                "description": "删除文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于基础路径）"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "file_exists",
                "description": "检查文件是否存在",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于基础路径）"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        if tool_name == "read_file":
            return await self._read_file(params.get("path", ""))
        elif tool_name == "write_file":
            return await self._write_file(
                params.get("path", ""),
                params.get("content", "")
            )
        elif tool_name == "list_files":
            return await self._list_files(params.get("path", ""))
        elif tool_name == "delete_file":
            return await self._delete_file(params.get("path", ""))
        elif tool_name == "file_exists":
            return await self._file_exists(params.get("path", ""))
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}

    async def _read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            file_path = self.base_path / path

            # 安全检查：确保路径在基础路径内
            if not str(file_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "error": "路径超出允许范围"}

            if not file_path.exists():
                return {"success": False, "error": "文件不存在"}

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "path": str(file_path),
                "size": len(content)
            }

        except Exception as e:
            self.logger.error(f"读取文件失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        try:
            file_path = self.base_path / path

            # 安全检查
            if not str(file_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "error": "路径超出允许范围"}

            # 创建父目录
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": str(file_path),
                "size": len(content),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"写入文件失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _list_files(self, path: str) -> Dict[str, Any]:
        """列出目录文件"""
        try:
            dir_path = self.base_path / path if path else self.base_path

            # 安全检查
            if not str(dir_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "error": "路径超出允许范围"}

            if not dir_path.exists():
                return {"success": False, "error": "目录不存在"}

            files = []
            for item in dir_path.iterdir():
                files.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })

            return {
                "success": True,
                "path": str(dir_path),
                "files": files,
                "count": len(files)
            }

        except Exception as e:
            self.logger.error(f"列出文件失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            file_path = self.base_path / path

            # 安全检查
            if not str(file_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "error": "路径超出允许范围"}

            if not file_path.exists():
                return {"success": False, "error": "文件不存在"}

            file_path.unlink()

            return {
                "success": True,
                "path": str(file_path)
            }

        except Exception as e:
            self.logger.error(f"删除文件失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _file_exists(self, path: str) -> Dict[str, Any]:
        """检查文件是否存在"""
        try:
            file_path = self.base_path / path

            # 安全检查
            if not str(file_path.resolve()).startswith(str(self.base_path.resolve())):
                return {"success": False, "exists": False, "error": "路径超出允许范围"}

            exists = file_path.exists()

            return {
                "success": True,
                "exists": exists,
                "path": str(file_path)
            }

        except Exception as e:
            self.logger.error(f"检查文件失败: {str(e)}")
            return {"success": False, "error": str(e)}

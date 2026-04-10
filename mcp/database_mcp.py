# -*- coding: utf-8 -*-
"""
数据库MCP服务器
基于SQLite实现用户数据存储和查询
Author: SixpenniesS
"""

import sqlite3
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from mcp.mcp_gateway import MCPServer
import logging

logger = logging.getLogger(__name__)


class DatabaseMCP(MCPServer):
    """数据库MCP服务器

    提供数据库操作能力：
    - 用户数据存储
    - 对话历史查询
    - 危机事件记录
    """

    def __init__(self, db_path: str):
        """初始化数据库MCP

        Args:
            db_path: 数据库文件路径
        """
        self._name = "database"
        self.db_path = db_path
        self.logger = logging.getLogger("mcp.database")

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> bool:
        """初始化：创建数据库表"""
        try:
            # 确保目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # 对话历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    message TEXT NOT NULL,
                    response TEXT,
                    workflow_id TEXT,
                    intent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # 危机事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crisis_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    risk_level TEXT NOT NULL,
                    risk_score REAL,
                    assessment TEXT,
                    handled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user
                ON conversations(user_id, created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_crisis_events_user
                ON crisis_events(user_id, created_at DESC)
            """)

            conn.commit()
            conn.close()

            self.logger.info(f"数据库MCP初始化完成: {self.db_path}")
            return True

        except Exception as e:
            self.logger.error(f"数据库MCP初始化失败: {str(e)}")
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        return [
            {
                "name": "query_user_history",
                "description": "查询用户对话历史",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "用户ID"},
                        "limit": {"type": "integer", "description": "返回数量限制", "default": 10}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "save_conversation",
                "description": "保存对话记录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "用户ID"},
                        "message": {"type": "string", "description": "用户消息"},
                        "response": {"type": "string", "description": "AI回复"},
                        "workflow_id": {"type": "string", "description": "工作流ID"},
                        "intent": {"type": "string", "description": "意图类型"}
                    },
                    "required": ["user_id", "message", "response"]
                }
            },
            {
                "name": "log_crisis_event",
                "description": "记录危机事件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "用户ID"},
                        "risk_level": {"type": "string", "description": "风险等级"},
                        "risk_score": {"type": "number", "description": "风险分数"},
                        "assessment": {"type": "object", "description": "评估详情"}
                    },
                    "required": ["user_id", "risk_level"]
                }
            },
            {
                "name": "create_or_update_user",
                "description": "创建或更新用户",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "用户ID"},
                        "name": {"type": "string", "description": "用户名称"},
                        "metadata": {"type": "object", "description": "用户元数据"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_user_stats",
                "description": "获取用户统计信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "用户ID"}
                    },
                    "required": ["user_id"]
                }
            }
        ]

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        if tool_name == "query_user_history":
            return await self._query_user_history(
                params.get("user_id", ""),
                params.get("limit", 10)
            )
        elif tool_name == "save_conversation":
            return await self._save_conversation(params)
        elif tool_name == "log_crisis_event":
            return await self._log_crisis_event(params)
        elif tool_name == "create_or_update_user":
            return await self._create_or_update_user(params)
        elif tool_name == "get_user_stats":
            return await self._get_user_stats(params.get("user_id", ""))
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def _query_user_history(self, user_id: str, limit: int) -> Dict[str, Any]:
        """查询用户对话历史"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT message, response, workflow_id, intent, created_at
                FROM conversations
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )

            rows = cursor.fetchall()
            conn.close()

            history = []
            for row in rows:
                history.append({
                    "message": row["message"],
                    "response": row["response"],
                    "workflow_id": row["workflow_id"],
                    "intent": row["intent"],
                    "time": row["created_at"]
                })

            return {
                "success": True,
                "user_id": user_id,
                "history": history,
                "count": len(history)
            }

        except Exception as e:
            self.logger.error(f"查询用户历史失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _save_conversation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """保存对话记录"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO conversations (user_id, message, response, workflow_id, intent)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    params.get("user_id"),
                    params.get("message"),
                    params.get("response"),
                    params.get("workflow_id"),
                    params.get("intent")
                )
            )

            # 更新用户最后活跃时间
            cursor.execute(
                """
                UPDATE users SET last_active = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (params.get("user_id"),)
            )

            conn.commit()
            conn.close()

            return {
                "success": True,
                "user_id": params.get("user_id")
            }

        except Exception as e:
            self.logger.error(f"保存对话失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _log_crisis_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """记录危机事件"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO crisis_events (user_id, risk_level, risk_score, assessment)
                VALUES (?, ?, ?, ?)
                """,
                (
                    params.get("user_id"),
                    params.get("risk_level"),
                    params.get("risk_score"),
                    json.dumps(params.get("assessment", {}), ensure_ascii=False)
                )
            )

            conn.commit()
            event_id = cursor.lastrowid
            conn.close()

            return {
                "success": True,
                "event_id": event_id,
                "user_id": params.get("user_id")
            }

        except Exception as e:
            self.logger.error(f"记录危机事件失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _create_or_update_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建或更新用户"""
        try:
            user_id = params.get("user_id")
            conn = self._get_connection()
            cursor = conn.cursor()

            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            exists = cursor.fetchone()

            if exists:
                # 更新
                cursor.execute(
                    """
                    UPDATE users
                    SET name = COALESCE(?, name),
                        metadata = COALESCE(?, metadata),
                        last_active = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        params.get("name"),
                        json.dumps(params.get("metadata", {}), ensure_ascii=False) if params.get("metadata") else None,
                        user_id
                    )
                )
            else:
                # 创建
                cursor.execute(
                    """
                    INSERT INTO users (id, name, metadata)
                    VALUES (?, ?, ?)
                    """,
                    (
                        user_id,
                        params.get("name"),
                        json.dumps(params.get("metadata", {}), ensure_ascii=False)
                    )
                )

            conn.commit()
            conn.close()

            return {
                "success": True,
                "user_id": user_id,
                "created": not exists
            }

        except Exception as e:
            self.logger.error(f"创建/更新用户失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 对话数量
            cursor.execute(
                "SELECT COUNT(*) as count FROM conversations WHERE user_id = ?",
                (user_id,)
            )
            conversation_count = cursor.fetchone()["count"]

            # 危机事件数量
            cursor.execute(
                "SELECT COUNT(*) as count FROM crisis_events WHERE user_id = ?",
                (user_id,)
            )
            crisis_count = cursor.fetchone()["count"]

            # 首次访问时间
            cursor.execute(
                "SELECT created_at FROM users WHERE id = ?",
                (user_id,)
            )
            user_row = cursor.fetchone()

            conn.close()

            return {
                "success": True,
                "user_id": user_id,
                "conversation_count": conversation_count,
                "crisis_event_count": crisis_count,
                "created_at": user_row["created_at"] if user_row else None
            }

        except Exception as e:
            self.logger.error(f"获取用户统计失败: {str(e)}")
            return {"success": False, "error": str(e)}

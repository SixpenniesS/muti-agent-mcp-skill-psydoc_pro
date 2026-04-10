# -*- coding: utf-8 -*-
"""
搜索引擎MCP服务器
基于简单文本匹配实现心理学资源搜索
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


class SearchMCP(MCPServer):
    """搜索引擎MCP服务器

    提供心理学资源搜索能力：
    - 关键词搜索
    - 资源推荐
    """

    def __init__(self, index_path: str, knowledge_dir: str = None):
        """初始化搜索引擎MCP

        Args:
            index_path: 索引存储路径
            knowledge_dir: 知识库目录
        """
        self._name = "search"
        self.index_path = Path(index_path)
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else None
        self.logger = logging.getLogger("mcp.search")

        # 预定义的心理资源库
        self._resource_db = self._build_resource_db()

    @property
    def name(self) -> str:
        return self._name

    def _build_resource_db(self) -> Dict[str, List[Dict]]:
        """构建预定义资源库"""
        return {
            "焦虑": [
                {
                    "type": "练习",
                    "name": "腹式呼吸法",
                    "description": "通过深呼吸缓解焦虑，每天练习10-15分钟",
                    "tags": ["呼吸", "放松", "即时缓解"]
                },
                {
                    "type": "练习",
                    "name": "正念冥想",
                    "description": "专注当下，减少担忧和焦虑",
                    "tags": ["冥想", "专注", "长期练习"]
                },
                {
                    "type": "书籍",
                    "name": "《焦虑自救手册》",
                    "description": "系统了解和应对焦虑的自助指南",
                    "tags": ["书籍", "自助", "系统学习"]
                },
                {
                    "type": "技巧",
                    "name": "5-4-3-2-1感官着陆法",
                    "description": "通过5个感官体验缓解焦虑发作",
                    "tags": ["技巧", "即时", "感官"]
                }
            ],
            "抑郁": [
                {
                    "type": "练习",
                    "name": "行为激活",
                    "description": "通过小目标重建动力，逐步增加活动",
                    "tags": ["行为", "动力", "渐进"]
                },
                {
                    "type": "练习",
                    "name": "感恩日记",
                    "description": "每天记录3件值得感恩的事",
                    "tags": ["日记", "感恩", "积极"]
                },
                {
                    "type": "书籍",
                    "name": "《伯恩斯新情绪疗法》",
                    "description": "认知行为疗法自助指南",
                    "tags": ["书籍", "CBT", "自助"]
                }
            ],
            "人际": [
                {
                    "type": "技巧",
                    "name": "非暴力沟通",
                    "description": "用观察、感受、需求、请求四步表达",
                    "tags": ["沟通", "关系", "技巧"]
                },
                {
                    "type": "书籍",
                    "name": "《非暴力沟通》",
                    "description": "马歇尔·卢森堡的经典著作",
                    "tags": ["书籍", "沟通", "经典"]
                }
            ],
            "职场": [
                {
                    "type": "技巧",
                    "name": "番茄工作法",
                    "description": "25分钟专注+5分钟休息的工作节奏",
                    "tags": ["效率", "时间管理", "专注"]
                },
                {
                    "type": "技巧",
                    "name": "压力管理四步法",
                    "description": "识别、评估、应对、反思",
                    "tags": ["压力", "管理", "系统"]
                }
            ],
            "自我": [
                {
                    "type": "练习",
                    "name": "自我关怀练习",
                    "description": "像对待朋友一样对待自己",
                    "tags": ["自我", "关怀", "同理心"]
                },
                {
                    "type": "书籍",
                    "name": "《自我关怀》",
                    "description": "克里斯汀·内夫的著作",
                    "tags": ["书籍", "自我", "心理学"]
                }
            ],
            "危机": [
                {
                    "type": "热线",
                    "name": "全国心理援助热线",
                    "description": "400-161-9995（24小时）",
                    "tags": ["热线", "紧急", "全国"]
                },
                {
                    "type": "热线",
                    "name": "北京心理危机干预中心",
                    "description": "010-82951332",
                    "tags": ["热线", "北京", "危机"]
                },
                {
                    "type": "热线",
                    "name": "生命热线",
                    "description": "400-821-1215",
                    "tags": ["热线", "自杀预防", "支持"]
                }
            ]
        }

    async def initialize(self) -> bool:
        """初始化"""
        try:
            self.index_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"搜索MCP初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"搜索MCP初始化失败: {str(e)}")
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        return [
            {
                "name": "search",
                "description": "搜索心理学相关资源",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "主题过滤（可选）"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量限制",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_resources_by_topic",
                "description": "按主题获取推荐资源",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "主题名称"
                        }
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "list_all_topics",
                "description": "列出所有可用主题",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        if tool_name == "search":
            return await self._search(
                params.get("query", ""),
                params.get("topics", []),
                params.get("limit", 5)
            )
        elif tool_name == "get_resources_by_topic":
            return await self._get_resources_by_topic(params.get("topic", ""))
        elif tool_name == "list_all_topics":
            return await self._list_all_topics()
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}

    async def _search(
        self,
        query: str,
        topics: List[str],
        limit: int
    ) -> Dict[str, Any]:
        """搜索资源"""
        try:
            results = []
            query_lower = query.lower()

            # 如果指定了主题，只在那些主题中搜索
            search_topics = topics if topics else list(self._resource_db.keys())

            for topic in search_topics:
                if topic not in self._resource_db:
                    continue

                for resource in self._resource_db[topic]:
                    # 匹配检查：名称、描述、标签
                    score = 0

                    if query_lower in resource["name"].lower():
                        score += 3
                    if query_lower in resource["description"].lower():
                        score += 2
                    for tag in resource.get("tags", []):
                        if query_lower in tag.lower():
                            score += 1

                    if score > 0:
                        results.append({
                            **resource,
                            "topic": topic,
                            "score": score
                        })

            # 按分数排序
            results.sort(key=lambda x: x["score"], reverse=True)

            # 限制返回数量
            results = results[:limit]

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _get_resources_by_topic(self, topic: str) -> Dict[str, Any]:
        """按主题获取资源"""
        try:
            if topic not in self._resource_db:
                # 尝试模糊匹配
                matched_topic = None
                for t in self._resource_db.keys():
                    if topic in t or t in topic:
                        matched_topic = t
                        break

                if not matched_topic:
                    return {
                        "success": False,
                        "error": f"主题 '{topic}' 不存在",
                        "available_topics": list(self._resource_db.keys())
                    }
                topic = matched_topic

            resources = self._resource_db[topic]

            return {
                "success": True,
                "topic": topic,
                "resources": resources,
                "count": len(resources)
            }

        except Exception as e:
            self.logger.error(f"获取主题资源失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _list_all_topics(self) -> Dict[str, Any]:
        """列出所有主题"""
        return {
            "success": True,
            "topics": list(self._resource_db.keys()),
            "count": len(self._resource_db)
        }

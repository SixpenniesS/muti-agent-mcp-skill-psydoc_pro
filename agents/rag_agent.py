# -*- coding: utf-8 -*-
"""
RAG检索Agent
专职向量检索和上下文构建
Author: SixpenniesS
"""

from typing import Dict, Any, List, Optional
import os

from agents.base_agent import BaseAgent, AgentResult
from config import (
    KNOWLEDGE_DIR, TOP_K_RESULTS, SIMILARITY_THRESHOLD
)


class RAGAgent(BaseAgent):
    """RAG检索Agent

    专职向量检索和上下文构建。

    功能：
    - 多查询词检索
    - 上下文扩展（回溯完整对话）
    - 构建上下文文本
    """

    def __init__(self, vector_store, config: Dict[str, Any] = None):
        """初始化RAG检索Agent

        Args:
            vector_store: 向量存储实例
            config: Agent配置
        """
        super().__init__("RAGAgent", config)
        self.vector_store = vector_store
        self.top_k = self.config.get("top_k", TOP_K_RESULTS)
        self.threshold = self.config.get("threshold", SIMILARITY_THRESHOLD)

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行RAG检索

        Args:
            context: {
                "query": str,
                "topics": List[str] (可选),
                "top_k": int (可选),
                "generate_queries": bool (可选，是否生成多查询词)
            }

        Returns:
            AgentResult: {
                "documents": List[Dict],
                "context_text": str,
                "expanded_contexts": List[Dict],
                "total_found": int
            }
        """
        query = context.get("query", "")
        topics = context.get("topics", [])
        top_k = context.get("top_k", self.top_k)
        generate_queries = context.get("generate_queries", True)

        if not query:
            return AgentResult(
                success=False,
                data={},
                error="query is required"
            )

        try:
            # 1. 生成多查询词
            queries = [query]
            if generate_queries:
                queries = await self._generate_multiple_queries(query, topics)

            # 2. 多查询词检索
            documents = await self._multi_query_search(queries, topics, top_k)

            # 3. 上下文扩展
            expanded = await self._expand_context(documents, top_n=2)

            # 4. 构建上下文文本
            context_text = self._build_context_text(documents)

            return AgentResult(
                success=True,
                data={
                    "documents": documents,
                    "context_text": context_text,
                    "expanded_contexts": expanded,
                    "total_found": len(documents),
                    "queries_used": queries
                },
                metadata={
                    "agent": self.name,
                    "query_count": len(queries),
                    "doc_count": len(documents)
                }
            )

        except Exception as e:
            self.logger.error(f"RAG检索失败: {str(e)}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    async def _generate_multiple_queries(self, query: str, topics: List[str]) -> List[str]:
        """生成多个检索查询词

        Args:
            query: 原始查询
            topics: 主题列表

        Returns:
            查询词列表
        """
        # 基础查询
        queries = [query]

        # 如果有主题，添加主题相关的查询
        if topics:
            for topic in topics[:2]:  # 最多2个主题
                queries.append(f"{topic} {query}")

        return queries[:5]  # 最多5个查询词

    async def _multi_query_search(
        self,
        queries: List[str],
        topics: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """多查询词检索

        Args:
            queries: 查询词列表
            topics: 主题列表
            top_k: 返回文档数量

        Returns:
            合并去重后的文档列表
        """
        all_docs = []
        doc_dict = {}  # 用于去重

        for i, query in enumerate(queries):
            self.logger.info(f"检索查询 {i+1}/{len(queries)}: {query}")

            # 调用向量存储搜索
            docs = self.vector_store.search(
                query=query,
                top_k=top_k,
                threshold=self.threshold,
                topics=topics if i == 0 else None  # 只在第一次使用主题过滤
            )

            # 去重并收集
            for doc in docs:
                doc_key = doc.get("content", "")[:100]
                if doc_key not in doc_dict:
                    doc_dict[doc_key] = doc
                    all_docs.append(doc)
                else:
                    # 保留相似度更高的
                    if doc.get("similarity", 0) > doc_dict[doc_key].get("similarity", 0):
                        doc_dict[doc_key] = doc

        # 按相似度排序
        all_docs.sort(key=lambda x: x.get("similarity", 0), reverse=True)

        return all_docs[:top_k]

    async def _expand_context(
        self,
        documents: List[Dict],
        top_n: int = 2
    ) -> List[Dict[str, Any]]:
        """上下文扩展：回溯完整对话

        Args:
            documents: 检索到的文档
            top_n: 扩展的文档数量

        Returns:
            扩展后的上下文列表
        """
        expanded = []
        seen_anchors = set()

        for doc in documents:
            if len(expanded) >= top_n:
                break

            chunk_content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "")
            anchor = chunk_content[:80].strip()

            if not source or anchor in seen_anchors:
                continue

            # 尝试读取完整对话
            full_conv = self._read_full_qa_by_content(source, chunk_content)

            if full_conv and len(full_conv) > len(chunk_content) * 1.3:
                expanded.append({
                    "topic": doc.get("metadata", {}).get("topic", ""),
                    "full_conversation": full_conv,
                    "similarity": doc.get("similarity", 0)
                })
                seen_anchors.add(anchor)
                self.logger.info(f"上下文扩展: {source} ({len(chunk_content)}→{len(full_conv)}字符)")

        return expanded

    def _read_full_qa_by_content(self, source: str, chunk_content: str) -> str:
        """通过chunk内容定位完整对话

        Args:
            source: 文件名
            chunk_content: chunk内容

        Returns:
            完整对话文本
        """
        try:
            file_path = os.path.join(KNOWLEDGE_DIR, source)
            if not os.path.exists(file_path):
                return ""

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 使用chunk首行作为锚点
            anchor = chunk_content.split("\n")[0].strip()
            if len(anchor) < 10:
                return ""

            # 定位锚点位置
            pos = content.find(anchor)
            if pos == -1:
                return ""

            # 查找对话边界（##标记）
            start = content.rfind("##", 0, pos)
            start = (start + 2) if start != -1 else 0

            end = content.find("##", pos + len(anchor))
            if end == -1:
                end = len(content)

            full_conv = content[start:end].strip()

            # 清理无关内容
            lines = full_conv.split("\n")
            conv_lines = [
                l for l in lines
                if l.strip()
                and not l.strip().startswith("ID:")
                and "==========" not in l
                and "心理咨询对话" not in l
            ]

            return "\n".join(conv_lines) if conv_lines else ""

        except Exception as e:
            self.logger.error(f"读取完整对话失败: {str(e)}")
            return ""

    def _build_context_text(self, documents: List[Dict]) -> str:
        """构建上下文文本

        Args:
            documents: 文档列表

        Returns:
            格式化的上下文文本
        """
        if not documents:
            return ""

        parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            topic = metadata.get("topic", "未知")
            qa_id = metadata.get("qa_id", "未知")
            similarity = doc.get("similarity", 0)

            parts.append(f"参考案例 {i} (主题: {topic}, ID: {qa_id}, 相似度: {similarity:.3f}):")
            parts.append(doc.get("content", ""))
            parts.append("---")

        return "\n".join(parts)

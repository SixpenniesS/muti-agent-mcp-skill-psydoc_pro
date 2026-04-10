# -*- coding: utf-8 -*-
"""
向量存储模块
基于ChromaDB实现向量存储和检索功能
Author: SixpenniesS
"""

import chromadb
from chromadb.config import Settings
import requests
from typing import List, Dict, Any
import logging

from config import (
    CHROMA_DB_PATH, COLLECTION_NAME, ALIBABA_API_KEY,
    EMBEDDING_MODEL, TOP_K_RESULTS, SIMILARITY_THRESHOLD
)

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储类

    基于ChromaDB实现向量存储和检索功能。

    功能：
    - 文本嵌入向量生成
    - 文档存储和检索
    - 相似度搜索
    - 多主题过滤检索
    """

    def __init__(self):
        """初始化向量存储"""
        self.api_key = ALIBABA_API_KEY
        self.embedding_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

        # 初始化ChromaDB
        self.client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "心理学知识向量存储"}
        )

        logger.info(f"向量存储初始化完成: {CHROMA_DB_PATH}")

    def get_embedding(self, text: str) -> List[float]:
        """使用阿里云百炼Embedding模型生成文本嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": EMBEDDING_MODEL,
                "input": text
            }

            response = requests.post(
                self.embedding_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0]["embedding"]

            logger.error(f"API响应格式错误: {result}")
            return []

        except Exception as e:
            logger.error(f"生成嵌入向量时出错: {e}")
            return []

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """将文档添加到向量存储

        Args:
            documents: 文档列表，每个文档包含:
                - content: 文档内容
                - source: 来源文件名
                - metadata: 元数据（topic, qa_id等）

        Returns:
            是否成功
        """
        try:
            logger.info(f"开始添加 {len(documents)} 个文档到向量存储...")

            ids = []
            texts = []
            embeddings = []
            metadatas = []

            for i, doc in enumerate(documents):
                # 生成唯一ID
                doc_id = f"doc_{i}_{doc.get('source', 'unknown')}"

                # 生成嵌入向量
                embedding = self.get_embedding(doc.get("content", ""))
                if not embedding:
                    logger.warning(f"跳过文档 {doc_id}，无法生成嵌入向量")
                    continue

                # 准备元数据
                metadata = {
                    "source": str(doc.get("source", "")),
                    "size": int(doc.get("size", 0)),
                    "type": str(doc.get("type", "unknown")),
                    "topic": str(doc.get("topic", "unknown")),
                    "qa_id": str(doc.get("qa_id", "unknown")),
                    "header": str(doc.get("header", ""))
                }

                ids.append(doc_id)
                texts.append(doc.get("content", ""))
                embeddings.append(embedding)
                metadatas.append(metadata)

                if (i + 1) % 10 == 0:
                    logger.info(f"已处理 {i + 1}/{len(documents)} 个文档")

            # 批量添加
            if ids:
                batch_size = 1000
                for i in range(0, len(ids), batch_size):
                    end_idx = min(i + batch_size, len(ids))
                    self.collection.add(
                        ids=ids[i:end_idx],
                        documents=texts[i:end_idx],
                        embeddings=embeddings[i:end_idx],
                        metadatas=metadatas[i:end_idx]
                    )

                logger.info(f"✅ 成功添加 {len(ids)} 个文档到向量存储")
                return True

            logger.warning("没有有效的文档可以添加")
            return False

        except Exception as e:
            logger.error(f"添加文档到向量存储时出错: {e}")
            return False

    def search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        threshold: float = SIMILARITY_THRESHOLD,
        topics: List[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索相关文档

        Args:
            query: 查询文本
            top_k: 返回文档数量
            threshold: 相似度阈值
            topics: 主题过滤列表

        Returns:
            相关文档列表
        """
        try:
            # 生成查询嵌入
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                logger.error("无法生成查询的嵌入向量")
                return []

            # 构建查询参数
            search_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }

            # 主题过滤
            if topics and len(topics) > 0:
                if len(topics) == 1:
                    search_params["where"] = {"topic": topics[0]}
                else:
                    # 多主题：分别检索后合并
                    return self._multi_topic_search(
                        query_embedding, topics, top_k, threshold
                    )

            # 执行搜索
            results = self.collection.query(**search_params)

            # 处理结果
            documents = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    similarity = 1 - distance

                    if similarity >= threshold:
                        documents.append({
                            "content": doc,
                            "metadata": metadata,
                            "similarity": similarity,
                            "distance": distance
                        })

            logger.info(f"找到 {len(documents)} 个相关文档")
            return documents

        except Exception as e:
            logger.error(f"搜索文档时出错: {e}")
            return []

    def _multi_topic_search(
        self,
        query_embedding: List[float],
        topics: List[str],
        top_k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """多主题搜索

        Args:
            query_embedding: 查询嵌入向量
            topics: 主题列表
            top_k: 返回数量
            threshold: 相似度阈值

        Returns:
            合并后的文档列表
        """
        all_docs = []
        doc_dict = {}

        for topic in topics:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k // len(topics) + 2,
                include=["documents", "metadatas", "distances"],
                where={"topic": topic}
            )

            if results["documents"] and results["documents"][0]:
                for doc, metadata, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    similarity = 1 - distance
                    if similarity >= threshold:
                        doc_key = doc[:100]
                        if doc_key not in doc_dict or similarity > doc_dict[doc_key]["similarity"]:
                            doc_dict[doc_key] = {
                                "content": doc,
                                "metadata": metadata,
                                "similarity": similarity,
                                "distance": distance
                            }

        all_docs = list(doc_dict.values())
        all_docs.sort(key=lambda x: x["similarity"], reverse=True)

        return all_docs[:top_k]

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            count = self.collection.count()
            return {
                "name": COLLECTION_NAME,
                "document_count": count,
                "path": CHROMA_DB_PATH
            }
        except Exception as e:
            logger.error(f"获取集合信息时出错: {e}")
            return {}

    def clear_collection(self) -> bool:
        """清空集合"""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "心理学知识向量存储"}
            )
            logger.info("集合已清空")
            return True
        except Exception as e:
            logger.error(f"清空集合时出错: {e}")
            return False

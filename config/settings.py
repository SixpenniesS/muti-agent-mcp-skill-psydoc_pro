# -*- coding: utf-8 -*-
"""
项目配置文件
包含API配置、数据库配置、检索配置、工作流配置等
Author: SixpenniesS
"""

import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# =============================================================================
# API 配置
# =============================================================================

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-e167e248b2524f009a10b3685eea5229")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 阿里云百炼Embedding配置
ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "sk-a25386e1ad13445280fdbf0beca25079")
EMBEDDING_MODEL = "text-embedding-v4"

# 阿里云百炼语音合成(TTS)配置
TTS_ENABLED = True
TTS_MODEL = "cosyvoice-v3-flash"
TTS_VOICE = "longyingling_v3"
TTS_RATE = "1"
TTS_OUTPUT_DIR = str(PROJECT_ROOT / "storage" / "audio")

# =============================================================================
# 存储配置
# =============================================================================

# 存储根目录
STORAGE_PATH = str(PROJECT_ROOT / "storage")

# ChromaDB配置
CHROMA_DB_PATH = str(PROJECT_ROOT / "storage" / "chroma_db")
COLLECTION_NAME = "psychology_knowledge"

# SQLite数据库配置
DATABASE_PATH = str(PROJECT_ROOT / "storage" / "psychology.db")

# 搜索引擎索引配置
SEARCH_INDEX_PATH = str(PROJECT_ROOT / "storage" / "search_index")

# 报告存储路径
REPORT_PATH = str(PROJECT_ROOT / "storage" / "reports")

# 进展记录存储路径
PROGRESS_PATH = str(PROJECT_ROOT / "storage" / "progress")

# =============================================================================
# 资源路径配置
# =============================================================================

# 知识库文档目录
KNOWLEDGE_DIR = str(PROJECT_ROOT / "resources" / "knowledge")

# 提示词目录
PROMPTS_DIR = str(PROJECT_ROOT / "resources" / "prompts")

# 工作流定义目录
WORKFLOWS_DIR = str(PROJECT_ROOT / "config" / "workflows")

# =============================================================================
# 文本处理配置
# =============================================================================

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# =============================================================================
# 检索配置
# =============================================================================

TOP_K_RESULTS = 6
SIMILARITY_THRESHOLD = 0.15

# =============================================================================
# 对话配置
# =============================================================================

MAX_NO_RAG_ROUNDS = 3
MAX_CONVERSATION_HISTORY = 20

# =============================================================================
# 工作流配置
# =============================================================================

MAX_WORKFLOW_STEPS = 10
WORKFLOW_TIMEOUT = 60  # 秒

# =============================================================================
# MCP服务器配置
# =============================================================================

MCP_SERVERS = {
    "filesystem": {
        "base_path": STORAGE_PATH
    },
    "database": {
        "db_path": DATABASE_PATH
    },
    "search": {
        "index_path": SEARCH_INDEX_PATH,
        "knowledge_dir": KNOWLEDGE_DIR
    }
}

# =============================================================================
# Agent配置
# =============================================================================

AGENT_CONFIG = {
    "intent_agent": {
        "model": DEEPSEEK_MODEL,
        "temperature": 0.3,
        "max_tokens": 100
    },
    "rag_agent": {
        "top_k": TOP_K_RESULTS,
        "threshold": SIMILARITY_THRESHOLD
    },
    "response_agent": {
        "model": DEEPSEEK_MODEL,
        "temperature": 0.6,
        "max_tokens": 1000
    }
}

# =============================================================================
# Skill配置
# =============================================================================

SKILL_CONFIG = {
    "emotion_analyzer": {
        "use_llm": False,  # 使用词典方法
        "confidence_threshold": 0.5
    },
    "crisis_detector": {
        "use_llm": False,
        "critical_threshold": 10,
        "high_threshold": 7,
        "medium_threshold": 4
    }
}

# =============================================================================
# 日志配置
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

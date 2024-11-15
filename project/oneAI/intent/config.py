from typing import Dict, Any

# LLM配置
LLM_CONFIG = {
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 500,
    "response_format": {"type": "json_object"}
}

# 默认意图
DEFAULT_INTENT = {
    "main_intent": "general",
    "sub_intent": "chitchat",
    "confidence": 0.0,
    "entities": {},
    "need_workflow_switch": False,
    "suggested_workflow": "general"
}

# 停用词列表
STOP_WORDS = ["的", "了", "呢", "啊", "吧", "呀", "哦", "哈", "嗯", "这", "那", "都", "就"]
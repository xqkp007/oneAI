from typing import Dict, Any
import logging
from ..brain import AllowanceGroupBrain
from openai import OpenAI
from session.session_manager import SessionManager

class BaseHandler:
    """基础处理器类"""
    def __init__(self, logger: logging.Logger, brain: AllowanceGroupBrain, client: OpenAI, session_manager: SessionManager):
        self.logger = logger
        self.brain = brain
        self.client = client
        self.session_manager = session_manager
        
    def _call_llm(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """调用 LLM"""
        # TODO: 实现 LLM 调用
        return {
            'message': '测试响应',
            'status': 'normal',
            'need_followup': False,
            'reason': '测试原因'
        }
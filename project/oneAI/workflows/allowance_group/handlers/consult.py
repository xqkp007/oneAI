from typing import Dict, Any
from .base import BaseHandler
from ..constants import ALLOWANCE_RULES, GROUP_CARD_RULES
from ..brain import AllowanceGroupBrain
import logging
from openai import OpenAI
from session.session_manager import SessionManager


class ConsultHandler(BaseHandler):
    """咨询场景处理器"""
    def __init__(self, logger: logging.Logger, brain: AllowanceGroupBrain, client: OpenAI, session_manager: SessionManager):
        super().__init__(logger, brain, client, session_manager)
        
    def _call_llm(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """调用 LLM"""
        return self.brain._call_llm(system_prompt, user_message)

    def handle(self, message: str, context: Dict[str, Any], scene_result: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("\n" + "="*50)
        self.logger.info("开始处理咨询请求...")
        
        # 1. 构建完整知识库
        rules = f"""# 津贴规则
{ALLOWANCE_RULES}

# 参团卡规则
{GROUP_CARD_RULES}"""
        
        # 2. 构建系统提示词
        system_prompt = f"""你是津贴和参团卡的咨询专家。请根据以下规则解答用户的问题。

# 知识库
{rules}

# 回复要求
1. 根据用户问题和历史对话判断用户意图
2. 回答要简洁明了，控制在50字以内
3. 确保信息准确，完全基于知识库内容
4. 语气友好自然
5. 如果问题超出知识库范围，建议咨询客服

请以JSON格式返回：
{{
    "message": "回复内容",
    "status": "normal/human_switch",
    "need_followup": false,
    "reason": "回复原因"
}}"""

        # 3. 调用 LLM 生成回复
        response = self._call_llm(system_prompt, message)
        
        # 4. 返回结果
        return {
            'message': response['message'],
            'status': response.get('status', 'normal'),
            'need_followup': False,
            'reason': response.get('reason', '规则咨询完成'),
            'workflow_type': 'allowance_group'
        }
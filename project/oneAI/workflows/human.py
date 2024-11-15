from .base import BaseWorkflow
from typing import Dict, Any
from session.session_manager import SessionManager

class HumanWorkflow(BaseWorkflow):
    def __init__(self, api_key: str, base_url: str, session_manager: SessionManager):
        super().__init__(api_key, base_url, session_manager)

    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理转人工服务"""
        system_prompt = """你是一个专业的客服助手。现在需要帮助用户转接人工客服。
        
        请注意以下要点：
        1. 表达歉意并说明需要转人工的原因
        2. 告知用户预计等待时间
        3. 提醒用户准备相关信息
        4. 回答要简洁明了
        """
        
        llm_response = self._call_llm(system_prompt, message)
        
        return {
            'message': llm_response['message'],
            'status': llm_response['status'],
            'workflow_type': 'human',
            'need_followup': False,  # 人工服务永远不需要后续跟进
            'reason': llm_response.get('reason', '')
        } 
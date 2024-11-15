from .base import BaseWorkflow
from typing import Dict, Any
from session.session_manager import SessionManager

class CashbackWorkflow(BaseWorkflow):
    def __init__(self, api_key: str, base_url: str, session_manager: SessionManager):
        super().__init__(api_key, base_url, session_manager)

    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理满二反一相关消息"""
        system_prompt = """你是一个专业的客服助手。现在需要你解答用户关于满二反一活动的问题。
        满二反一是指：购买两件商品可以获得一件商品的退款。
        
        请注意以下要点：
        1. 解释活动规则和条件
        2. 说明退款方式和到账时间
        3. 介绍如何参与活动
        4. 回答要简洁明了
        
        如果用户要求人工服务，请返回human_switch状态。
        如果用户询问其他业务，请返回workflow_switch状态。
        如果是正常满二反一咨询，请返回normal状态。
        """
        
        llm_response = self._call_llm(system_prompt, message)
        
        return {
            'message': llm_response['message'],
            'status': llm_response['status'],
            'workflow_type': 'cashback',
            'need_followup': llm_response['status'] == 'normal',
            'reason': llm_response.get('reason', '')
        } 
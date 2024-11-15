from .base import BaseWorkflow
from typing import Dict, Any

class ConfirmWorkflow(BaseWorkflow):
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理确认意图的消息"""
        # 获取历史对话文本
        history_text = self._get_history_text(context)
        
        system_prompt = f"""# Role: 专业客服助手

# Background
你是一个专业的客服助手，需要帮助用户表达他们的具体需求。

# 对话历史
{history_text}

# 可处理的业务类型
1. 满二反一活动
2. 津贴使用
3. 参团卡
4. 优惠券使用

# 状态判断规则
1. 当用户明确表达以下意图时，返回workflow_switch：
   - 咨询具体业务（满二反一、津贴、参团卡、优惠券）
   - 表达明确的业务需求

2. 当遇到以下情况时，返回human_switch：
   - 明确要求人工服务
   - 涉及订单退款、投诉
   - 系统无法处理的问题

3. 其他情况返回normal，继续引导用户

# 回复要求
1. 用开放式问题引导用户
2. 回复不超过15字
3. 语气友好自然
4. 不要做多轮确认

示例回复：
- "请问您想咨询哪方面的问题呢？"
- "您需要什么帮助？"
- "想了解哪个活动呢？"
"""
        
        llm_response = self._call_llm(system_prompt, message)
        
        return {
            'message': llm_response['message'],
            'status': llm_response['status'],
            'workflow_type': 'confirm',
            'need_followup': llm_response['status'] == 'normal',
            'reason': llm_response.get('reason', '')
        } 
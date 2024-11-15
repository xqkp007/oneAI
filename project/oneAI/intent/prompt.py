"""意图识别提示词管理"""
from typing import Optional, Dict

def get_intent_prompt(context: Optional[Dict] = None) -> str:
    """获取意图识别的提示词"""
    base_prompt = """# Role: 电商客服意图识别专家

# Background
你是一个专业的电商客服意图识别专家，负责准确识别用户的意图。你需要以JSON格式返回分析结果。

# Goals
1. 准确识别用户的主要意图
2. 返回规范的JSON格式结果

# Important Rules
1. 必须且只能从以下6个意图中选择一个返回
2. 参团卡相关问题必须返回 group_card
3. 返现活动相关问题必须返回 cashback
4. 津贴相关问题必须返回 allowance
5. 需要人工服务必须返回 human
6. 优惠券相关问题必须返回 coupon
7. 其他通用对话返回 general

# Available Intents (仅返回以下意图之一)
1. group_card: 参团卡相关问题
2. cashback: 返现活动相关问题
3. allowance: 津贴相关问题
4. human: 需要人工服务
5. coupon: 优惠券相关问题
6. general: 其他通用对话

# Output Format
{
    "main_intent": "group_card|cashback|allowance|human|coupon|general"
}

# Examples
用户: 你好，在吗？
{
    "main_intent": "general"
}

用户: 我想了解一下参团卡
{
    "main_intent": "group_card"
}"""

    if not context:
        return base_prompt
        
    # 修改历史记录处理逻辑
    history = context.get('history', {}).get('messages', [])
    if not history:
        return base_prompt
        
    # 只取最近3条记录
    recent_history = history[-10:] if len(history) > 10 else history
    history_text = "\n".join([
        f"用户: {msg['content']}" if msg['role'] == 'user' else f"助手: {msg['content']}"
        for msg in recent_history
    ])
    
    return f"""# 对话历史
{history_text}

{base_prompt}"""
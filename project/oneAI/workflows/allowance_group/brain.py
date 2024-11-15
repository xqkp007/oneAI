from typing import Dict, Any, Tuple
import logging
from .constants import AllowanceGroupSceneType, AllowanceGroupType
import json
from openai import OpenAI

class AllowanceGroupBrain:
    """津贴&参团卡业务决策大脑"""
    def __init__(self, logger: logging.Logger, client: OpenAI):
        self.logger = logger
        self.client = client
    
    def think(self, message: str, history: list) -> Dict[str, Any]:
        """思考并分析用户意图"""
        self.logger.info("\n" + "="*50)
        self.logger.info("开始场景分析...")
        self.logger.info(f"用户输入: {message}")
        
        history_text = "\n".join([
            f"用户: {msg['content']}" if msg['role'] == 'user' else f"助手: {msg['content']}"
            for msg in history
        ])
        
        system_prompt = """# Role: 津贴&参团卡意图识别专家

# 任务
分析用户输入，判断具体意图并返回指令。

# 历史对话
{history}

# 场景类型
1. claim: 领取津贴或参团卡
2. calc: 商品优惠计算
3. consult: 咨询规则
4. other: 非相关意图

如果用户提到具体商品，请提取商品信息。

请返回JSON格式：
{
    "scene": "claim|calc|consult|other",
    "type": "allowance|group_card",
    "command": {
        "type": "领取优惠|商品优惠计算|咨询规则",
        "product_info": {
            "name": "商品名称",
            "id": "",
            "price": ""
        }
    }
}"""

        # 调用 LLM
        result = self._call_llm(system_prompt, message)
        return result

    def get_handler_name(self, scene_type: str) -> str:
        """根据场景类型返回对应的处理器类名"""
        scene_handler_map = {
            'claim': 'ClaimHandler',
            'calc': 'CalculateHandler', 
            'consult': 'ConsultHandler',
            'other': 'ConsultHandler'
        }
        return scene_handler_map.get(scene_type, 'ConsultHandler')

    def _call_llm(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """调用 LLM"""
        try:
            self.logger.info("开始调用LLM...")
            self.logger.info(f"系统提示词: {system_prompt}")
            self.logger.info(f"用户消息: {user_message}")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            self.logger.info(f"LLM原始返回: {result}")
            
            parsed_result = json.loads(result)
            self.logger.info(f"解析后的结果: {parsed_result}")
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"调用LLM失败: {str(e)}")
            self.logger.error("错误详情:", exc_info=True)
            return {
                "scene": "other",
                "type": "allowance",
                "command": {
                    "type": "退出工作流",
                    "workflow_exit": {
                        "target_workflow": "human",
                        "exit_reason": f"LLM调用失败: {str(e)}"
                    }
                }
            }
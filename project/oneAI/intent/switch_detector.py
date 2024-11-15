from typing import Dict, Any
import logging
from openai import OpenAI
import json

class IntentSwitchDetector:
    def __init__(self, api_key: str, base_url: str):
        self.logger = logging.getLogger(__name__)
        # 设置日志级别
        self.logger.setLevel(logging.INFO)
        # 添加控制台处理器
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def check_switch(self, message: str, current_workflow: str, context: Dict[str, Any]) -> bool:
        """检查是否需要切换意图"""
        try:
            self.logger.info("\n" + "="*50)
            self.logger.info("开始调用 LLM 检测意图切换...")
            
            # 获取历史对话
            history = context.get('history', {}).get('messages', [])
            history_text = "\n".join([
                f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
                for msg in history[-10:]  # 只取最近5轮对话
            ])
            
            system_prompt = f"""你是意图切换检测专家。当前用户正在 {current_workflow} 场景中。
            
            # 对话历史
            {history_text}
            
            # 规则
            1. 如果用户明确提出新的需求，返回需要切换
            2. 如果用户继续当前话题，返回不需要切换
            3. 如果不确定，返回不需要切换
            
            请返回 JSON 格式：{{"need_switch": true/false}}
            """
            
            self.logger.info("\n系统提示词:")
            self.logger.info("-"*30)
            self.logger.info(system_prompt)
            self.logger.info("-"*30)
            
            self.logger.info("\n用户消息:")
            self.logger.info("-"*30)
            self.logger.info(message)
            self.logger.info("-"*30)
            
            self.logger.info("\nLLM 请求配置:")
            self.logger.info(f"模型: deepseek-chat")
            self.logger.info(f"温度: 0.7")
            self.logger.info(f"最大token: 100")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            self.logger.info("\nLLM 返回结果:")
            self.logger.info("-"*30)
            self.logger.info(result)
            self.logger.info("-"*30)
            
            parsed_result = json.loads(result)
            return parsed_result.get("need_switch", False)
            
        except Exception as e:
            self.logger.error(f"检测意图切换失败: {str(e)}")
            return False 
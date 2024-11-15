from typing import Dict, Any, Optional
import json
import logging
from openai import OpenAI
from .prompt import get_intent_prompt
from .config import DEFAULT_INTENT, LLM_CONFIG

class IntentClassifier:
    def __init__(self, api_key: str, base_url: str):
        """初始化意图分类器"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def classify(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """意图识别"""
        try:
            self.logger.info("\n" + "="*50)
            self.logger.info("开始调用 LLM 进行意图识别...")
            
            # 获取提示词
            self.logger.info(f"输入的上下文: {context}")
            system_prompt = get_intent_prompt(context)
            self.logger.info("\n系统提示词:")
            self.logger.info("-"*30)
            self.logger.info(system_prompt)
            self.logger.info("-"*30)
            
            self.logger.info("\n用户消息:")
            self.logger.info("-"*30)
            self.logger.info(message)
            self.logger.info("-"*30)
            
            # 调用 LLM
            self.logger.info("\nLLM 请求配置:")
            self.logger.info(f"模型: {LLM_CONFIG['model']}")
            self.logger.info(f"温度: {LLM_CONFIG['temperature']}")
            self.logger.info(f"最大token: {LLM_CONFIG['max_tokens']}")
            
            response = self.client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=LLM_CONFIG["temperature"],
                max_tokens=LLM_CONFIG["max_tokens"],
                response_format=LLM_CONFIG["response_format"]
            )
            
            content = response.choices[0].message.content
            self.logger.info("\nLLM 返回结果:")
            self.logger.info("-"*30)
            self.logger.info(content)
            self.logger.info("-"*30)
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            self.logger.error("\n意图识别失败:")
            self.logger.error("-"*30)
            self.logger.error(f"错误类型: {type(e)}")
            self.logger.error(f"错误信息: {str(e)}")
            self.logger.error("-"*30)
            return DEFAULT_INTENT
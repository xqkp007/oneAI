from typing import Dict, Any, Optional
from openai import OpenAI
import logging
from abc import ABC, abstractmethod
import json
from session.session_manager import SessionManager

class BaseWorkflow(ABC):
    def __init__(self, api_key: str, base_url: str, session_manager: SessionManager):
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.session_manager = session_manager
        
    @abstractmethod
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户消息
        Args:
            message: 用户消息
            context: 完整的上下文信息,包含:
                - messages: 历史消息
                - current_primary_workflow: 当前主工作流
                - current_secondary_workflow: 当前次级工作流
                - workflow_stack: 工作流栈
                - workflow_state: 工作流状态
        """
        pass
        
    def _call_llm(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """调用LLM生成回复"""
        try:
            system_prompt += """
            
            请以JSON格式返回：
            {
                "status": "normal/human_switch/workflow_switch",  # normal: 正常回复, human_switch: 需要转人工, workflow_switch: 需要切换场景
                "message": "回复内容",
                "reason": "状态原因说明"
            }
            """
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            self.logger.error(f"调用LLM失败: {str(e)}")
            return {
                "status": "human_switch",
                "message": "抱歉，系统暂时出现问题，请稍后再试。",
                "reason": f"错误：{str(e)}"
            }

    def _get_history_text(self, context: Dict[str, Any], max_turns: int = 10) -> str:
        """获取历史对话文本
        Args:
            context: 上下文信息
            max_turns: 最大对话轮数，默认5轮
        """
        history = context.get('messages', [])
        recent_history = history[-max_turns:] if len(history) > max_turns else history
        return "\n".join([
            f"用户: {msg['content']}" if msg['role'] == 'user' else f"助手: {msg['content']}"
            for msg in recent_history
        ])
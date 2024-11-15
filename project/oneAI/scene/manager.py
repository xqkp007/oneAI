from typing import Dict, Any
import logging

class SceneManager:
    def __init__(self):
        """初始化场景管理器"""
        self.logger = logging.getLogger(__name__)
        self.intent_workflow_map = {
            'group_card': {'type': 'primary', 'name': 'allowance_group'},  # 修改
            'cashback': {'type': 'primary', 'name': 'cashback'},
            'allowance': {'type': 'primary', 'name': 'allowance_group'},  # 修改
            'human': {'type': 'primary', 'name': 'human'},
            'coupon': {'type': 'secondary', 'name': 'cashback'},
            'general': {'type': 'primary', 'name': 'confirm'}
        }
        
    def handle_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """处理意图识别结果，返回工作流信息"""
        try:
            main_intent = intent.get('main_intent', 'general')
            workflow_info = self.intent_workflow_map.get(main_intent, {
                'type': 'primary',
                'name': 'confirm'
            })
            return workflow_info
        except Exception as e:
            self.logger.error(f"处理意图时发生错误: {str(e)}")
            return {'type': 'primary', 'name': 'confirm'}
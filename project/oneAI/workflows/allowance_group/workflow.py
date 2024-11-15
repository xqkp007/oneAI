from typing import Dict, Any
from ..base import BaseWorkflow
from .brain import AllowanceGroupBrain
from .handlers import ClaimHandler, CalculateHandler, ConsultHandler
import logging
from session.session_manager import SessionManager

class AllowanceGroupWorkflow(BaseWorkflow):
    """津贴&参团卡统一工作流"""
    def __init__(self, api_key: str, base_url: str, session_manager: SessionManager):
        super().__init__(api_key, base_url, session_manager)
        self.logger = logging.getLogger("allowance_group_workflow")
        
        # 初始化日志配置
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
            
        self.brain = AllowanceGroupBrain(self.logger, self.client)
        self.claim_handler = ClaimHandler(self.logger, self.brain, self.client, self.session_manager)
        self.calc_handler = CalculateHandler(self.logger, self.brain, self.client, self.session_manager)
        self.consult_handler = ConsultHandler(self.logger, self.brain, self.client, self.session_manager)
        
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理津贴&参团卡相关消息"""
        try:
            user_id = context['session_id']
            
            # 1. 先设置主工作流为 allowance_group
            self.session_manager.switch_workflow(user_id, 'allowance_group', 'primary')
            
            # 2. 检查工作流状态
            current_workflow = context.get('current_primary_workflow')
            secondary_workflow = context.get('current_secondary_workflow')
            context_data = context.get('context_data', {})
            
            # 3. 优先处理二级工作流
            if secondary_workflow:
                self.logger.info(f"继续处理二级工作流: {secondary_workflow}")
                if secondary_workflow == 'calc':
                    # 确保主工作流状态正确
                    context['current_primary_workflow'] = 'allowance_group'
                    context['current_secondary_workflow'] = 'calc'
                    
                    # 直接交给 calc_handler 处理所有 calc 相关的逻辑
                    result = self.calc_handler.handle_quantity_input(message, context)
                    # 只要不是明确的工作流切换，就保持在二级工作流中
                    if result.get('status') not in ['workflow_switch', 'error']:
                        result.update({
                            'current_primary_workflow': 'allowance_group',
                            'current_secondary_workflow': secondary_workflow,
                            'workflow_stack': context.get('workflow_stack', []),
                            'context_data': context_data
                        })
                    return result
                # 可以添加其他二级工作流的处理...
                
            # 4. 一级工作流中进行意图识别和分配
            if current_workflow == 'allowance_group':
                self.logger.info("在一级工作流中进行意图识别...")
                scene_result = self.brain.think(message, context.get('messages', []))
                scene_type = scene_result.get('scene')
                self.logger.info(f"识别到的场景类型: {scene_type}")
                
                # 根据场景类型分配处理
                if scene_type == 'claim':
                    result = self.claim_handler.handle(message, context, scene_result)
                    # 如果需要设置二级工作流
                    if result.get('current_secondary_workflow'):
                        self.session_manager.switch_workflow(
                            user_id, 
                            result['current_secondary_workflow'], 
                            'secondary'
                        )
                    return result
                elif scene_type == 'calc':
                    # 设置二级工作流
                    self.session_manager.switch_workflow(user_id, 'calc', 'secondary')
                    # 更新 context
                    context['current_secondary_workflow'] = 'calc'
                    context['workflow_stack'] = ['allowance_group', 'calc']
                    # 保存更新后的 context
                    self.session_manager.save_context(user_id, {
                        **context,
                        'current_secondary_workflow': 'calc',
                        'workflow_stack': ['allowance_group', 'calc']
                    })
                    return self.calc_handler.handle(message, context, scene_result)
                elif scene_type == 'consult':
                    return self.consult_handler.handle(message, context, scene_result)
                else:
                    return {
                        'message': '抱歉，我可能理解有误，让我转接其他客服帮您。',
                        'status': 'workflow_switch',
                        'workflow_type': scene_result.get('target_workflow', 'human'),
                        'need_followup': False,
                        'reason': scene_result.get('exit_reason', '非津贴&参团卡意图')
                    }
                
            # 5. 新对话的意图识别
            self.logger.info("新对话开始场景识别...")
            scene_result = self.brain.think(message, context.get('messages', []))
            scene_type = scene_result.get('scene')
            self.logger.info(f"识别到的场景类型: {scene_type}")
            
            # 6. 根据场景分发处理
            if scene_type == 'claim':
                return self.claim_handler.handle(message, context, scene_result)
            elif scene_type == 'calc':
                # 设置二级工作流
                self.session_manager.switch_workflow(user_id, 'calc', 'secondary')
                # 更新 context
                context['current_secondary_workflow'] = 'calc'
                context['workflow_stack'] = ['allowance_group', 'calc']
                # 保存更新后的 context
                self.session_manager.save_context(user_id, {
                    **context,
                    'current_secondary_workflow': 'calc',
                    'workflow_stack': ['allowance_group', 'calc']
                })
                return self.calc_handler.handle(message, context, scene_result)
            elif scene_type == 'consult':
                return self.consult_handler.handle(message, context, scene_result)
            else:
                # 非津贴&参团卡意图，退出工作流
                self.session_manager.end_current_workflow(user_id)
                return {
                    'message': '抱歉，我可能理解有误，让我转接其他客服帮您。',
                    'status': 'workflow_switch',
                    'workflow_type': scene_result.get('target_workflow', 'human'),
                    'need_followup': False,
                    'reason': scene_result.get('exit_reason', '非津贴&参团卡意图')
                }
                
        except Exception as e:
            self.logger.error(f"处理消息时发生错误: {str(e)}")
            self.logger.error("错误详情:", exc_info=True)
            return {
                'message': '抱歉，系统处理出现异常，请稍后重试。',
                'status': 'error',
                'need_followup': False,
                'reason': f'系统错误: {str(e)}'
            }

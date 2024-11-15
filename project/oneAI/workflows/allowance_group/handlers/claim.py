from typing import Dict, Any
from .base import BaseHandler
from ..constants import AllowanceGroupType, ALLOWANCE_LINKS, GROUP_CARD_LINKS
from ..exceptions import BenefitClaimError
import logging
from openai import OpenAI
from session.session_manager import SessionManager
from ..brain import AllowanceGroupBrain


class ClaimHandler(BaseHandler):
    """领取场景处理器"""
    def __init__(self, logger: logging.Logger, brain: AllowanceGroupBrain, client: OpenAI, session_manager: SessionManager):
        super().__init__(logger, brain, client, session_manager)
        
    def handle(self, message: str, context: Dict[str, Any], scene_result: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("处理领取请求...")
        
        # 1. 验证指令类型
        command = scene_result.get('command', {})
        if command.get('type') != '领取优惠':
            return {
                'message': '抱歉，指令类型不正确，请重新尝试。',
                'status': 'error',
                'need_followup': False,
                'reason': '指令类型错误'
            }
            
        # 2. 判断优惠种类 - 从 scene_result 中获取
        benefit_type = scene_result.get('type', command.get('benefit_type', 'allowance'))
        
        try:
            # 3. 发放优惠
            if benefit_type == 'allowance':
                amount = 200
                message = f"已为您发放{amount}元津贴，请在「我的津贴」中查看。\n您想买哪件产品？我帮您看看怎么用最优惠~"
            else:  # group_card
                message = "已为您发放参团卡，请在「我的卡券」中查看。\n您想买哪件产品？我帮您看看怎么用最优惠~"
                
            # 4. 返回结果
            return {
                'message': message,
                'status': 'normal',
                'need_followup': True,
                'reason': '优惠发放成功',
                'workflow_type': 'allowance_group',
                'current_secondary_workflow': 'calc',
                'context_data': {
                    'scene': 'calc',
                    'benefit_info': {
                        'type': benefit_type,
                        'amount': amount if benefit_type == 'allowance' else None,
                        'status': 'success'
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"优惠发放失败: {str(e)}")
            return {
                'message': "抱歉，津贴或参团卡的发放遇到问题，请稍后再试或联系客服解决。",
                'status': 'error',
                'need_followup': False,
                'reason': f"发放失败: {str(e)}",
                'workflow_type': 'allowance_group',
                'benefit_info': {
                    'type': benefit_type,
                    'status': 'failed'
                }
            }
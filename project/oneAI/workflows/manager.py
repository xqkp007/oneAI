from typing import Dict, Type
from .base import BaseWorkflow
from .confirm import ConfirmWorkflow
from .cashback import CashbackWorkflow
from .human import HumanWorkflow
from .allowance_group.workflow import AllowanceGroupWorkflow
from session.session_manager import SessionManager

class WorkflowManager:
    def __init__(self, api_key: str, base_url: str, session_manager: SessionManager):
        self.workflows: Dict[str, Type[BaseWorkflow]] = {
            'confirm': ConfirmWorkflow,
            'cashback': CashbackWorkflow,
            'allowance_group': AllowanceGroupWorkflow,
            'human': HumanWorkflow
        }
        self.api_key = api_key
        self.base_url = base_url
        self.session_manager = session_manager
        
    def get_workflow(self, workflow_type: str) -> BaseWorkflow:
        """获取工作流实例"""
        if workflow_type not in self.workflows:
            workflow_type = 'confirm'  # 默认使用确认意图工作流
            
        workflow_class = self.workflows[workflow_type]
        return workflow_class(self.api_key, self.base_url, self.session_manager) 
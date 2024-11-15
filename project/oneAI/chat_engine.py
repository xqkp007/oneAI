from typing import Dict, Any, Optional
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from session.session_manager import SessionManager
from intent.classifier import IntentClassifier
from intent.switch_detector import IntentSwitchDetector
from scene.manager import SceneManager
from workflows.manager import WorkflowManager

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    workflow_type: str
    status: str
    timestamp: str

class ChatEngine:
    def __init__(self, api_key: str, base_url: str):
        """初始化聊天引擎"""
        self.logger = logging.getLogger(__name__)
        # 设置日志级别
        self.logger.setLevel(logging.INFO)
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info("初始化聊天引擎...")
        self.api_key = api_key
        self.base_url = base_url
        
        # 初始化各个组件
        self.logger.info("初始化会话管理器...")
        self.session_manager = SessionManager()
        
        self.logger.info("初始化意图分类器...")
        self.intent_classifier = IntentClassifier(api_key, base_url)
        
        self.logger.info("初始化场景管理器...")
        self.scene_manager = SceneManager()
        
        self.logger.info("初始化工作流管理器...")
        self.workflow_manager = WorkflowManager(api_key, base_url, self.session_manager)
        
        # 初始化意图切换检测器
        self.logger.info("初始化意图切换检测器...")
        self.intent_switch_detector = IntentSwitchDetector(api_key, base_url)
        
        # 初始化路由
        self.router = APIRouter()
        self.router.add_api_route("/chat", self.chat_endpoint, methods=["POST"], response_model=ChatResponse)
        self.logger.info("聊天引擎初始化完成")
        
    async def chat_endpoint(self, request: ChatRequest):
        """API 端点处理函数"""
        try:
            response = self.process_message(request.message, request.user_id)
            return ChatResponse(
                message=response['message'],
                workflow_type=response['workflow_type'],
                status=response['status'],
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    def process_message(self, user_message: str, user_id: str) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            message_start_time = datetime.now()  # 记录消息开始处理时间
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"开始处理用户[{user_id}]的消息: {user_message}")
            
            # 1. 获取上下文
            self.logger.info("1. 获取会话上下文...")
            context = self.session_manager.get_context(user_id)
            
            # 如果没有当前工作流，但历史消息中有工作流状态，则恢复它
            if not context.get('current_primary_workflow'):
                messages = context.get('messages', [])
                for msg in reversed(messages):
                    if msg.get('role') == 'system' and '工作流状态:' in msg.get('content', ''):
                        workflow_name = msg['content'].split(':')[1].strip()
                        context['current_primary_workflow'] = workflow_name
                        break
                    
            workflow_type = context.get('current_primary_workflow')
            self.logger.info(f"获取到的上下文: {context}")
            self.logger.info(f"当前工作流: {workflow_type}")
            
            # 2. 意图识别和工作流选择
            if workflow_type is None:
                self.logger.info("2. 进行意图识别...")
                intent = self.intent_classifier.classify(user_message, {'history': context})
                self.logger.info(f"识别到的意图: {intent}")
                
                self.logger.info("3. 选择工作流...")
                workflow_info = self.scene_manager.handle_intent(intent)
                workflow_type = workflow_info['name']
                self.logger.info(f"选择的工作流: {workflow_type}")
                
                # 使用新的switch_workflow方法
                self.session_manager.switch_workflow(user_id, workflow_type, workflow_info['type'])
            else:
                self.logger.info(f"继续使用现有工作流: {workflow_type}")
            
            # 3. 处理消息
            self.logger.info("5. 获取工作流实例...")
            workflow = self.workflow_manager.get_workflow(workflow_type)
            
            self.logger.info("6. 处理用户消息...")
            response = workflow.process(user_message, context)
            self.logger.info(f"工作流处理结果: {response}")
            
            # 更新工作流状态
            if response.get('current_secondary_workflow'):
                self.session_manager.switch_workflow(
                    user_id, 
                    response['current_secondary_workflow'],
                    'secondary'
                )
            
            # 4. 处理LLM返回的状态
            llm_status = response.get('status')
            if llm_status == 'workflow_switch':
                self.logger.info("7. 检测到需要切换工作流...")
                intent = self.intent_classifier.classify(user_message, {'history': context})
                new_workflow_info = self.scene_manager.handle_intent(intent)
                new_workflow_type = new_workflow_info['name']
                self.session_manager.switch_workflow(user_id, new_workflow_type, new_workflow_info['type'])
                
                new_workflow = self.workflow_manager.get_workflow(new_workflow_type)
                response = new_workflow.process(user_message, context)
            
            elif llm_status == 'human_switch':
                self.logger.info("7. 检测到需要转人工...")
                human_workflow = self.workflow_manager.get_workflow('human')
                response = human_workflow.process(user_message, context)
                self.session_manager.end_current_workflow(user_id)
            
            # 5. 保存对话记录
            self.logger.info("8. 保存对话记录...")
            self._save_conversation(
                user_id, 
                user_message, 
                response['message'],
                message_start_time,
                datetime.now(),
                datetime.now()
            )
            
            # 6. 检查是否需要后续跟进
            if not response.get('need_followup', True):
                self.logger.info("9. 清除当前工作流...")
                self.session_manager.clear_current_workflow(user_id)
            
            self.logger.info("消息处理完成")
            return response
            
        except Exception as e:
            self.logger.error(f"处理消息时发生错误: {str(e)}", exc_info=True)
            return {
                'message': "抱歉，系统暂时遇到问题，请稍后再试。",
                'status': 'error',
                'workflow_type': 'error',
                'need_followup': False
            }
            
    def _save_conversation(self, user_id: str, user_message: str, ai_message: str,
                          message_time: datetime, workflow_time: datetime, response_time: datetime):
        """保存对话记录，使用实际的处理时间点"""
        # 1. 记录用户消息
        self.session_manager.add_message(user_id, {
            'role': 'user',
            'content': user_message,
            'timestamp': message_time,
            'message_type': 'chat'
        })
        
        # 2. 获取当前上下文，用于记录工作流状态
        context = self.session_manager.get_context(user_id)
        
        # 3. 记录工作流状态
        if context.get('current_primary_workflow'):
            self.session_manager.add_message(user_id, {
                'role': 'system',
                'content': f'工作流状态: {context["current_primary_workflow"]}',
                'timestamp': workflow_time,
                'message_type': 'workflow',
                'metadata': {
                    'workflow': context['current_primary_workflow'],
                    'workflow_stack': context['workflow_stack']
                }
            })
        
        # 4. 记录系统回复
        self.session_manager.add_message(user_id, {
            'role': 'assistant',
            'content': ai_message,
            'timestamp': response_time,
            'message_type': 'chat'
        }) 
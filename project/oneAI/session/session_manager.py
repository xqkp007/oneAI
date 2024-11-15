import psycopg2
from psycopg2.extras import DictCursor
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

class SessionManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_timeout = 300  # 30分钟超时
        self.max_turns = 50  # 最大对话轮次
        self.context_window = 10  # 保留最近10轮对话
        
        # 数据库连接
        self.conn = psycopg2.connect(
            dbname="chat_session_db",
            user="postgres", 
            password="ys140052",
            host="localhost",
            port="5432"
        )
        
        # 初始化表结构
        self._init_tables()
        
    def _init_tables(self):
        """初始化数据库表连接"""
        with self.conn.cursor() as cur:
            # 检查sessions表是否存在
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'sessions'
                )
            """)
            sessions_exists = cur.fetchone()[0]
            
            # 检查messages表是否存在
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'messages'
                )
            """)
            messages_exists = cur.fetchone()[0]
            
            if not sessions_exists or not messages_exists:
                raise Exception("必要的数据库表不存在，请先创建表结构")

    def create_session(self, user_id: str) -> Dict:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions 
                (session_id, user_id)
                VALUES (%s, %s)
                RETURNING *
                """,
                (session_id, user_id)
            )
            session = cur.fetchone()
            self.conn.commit()
            
        return {
            'session_id': session_id,
            'messages': [],
            'current_primary_workflow': None,
            'current_secondary_workflow': None,
            'workflow_stack': [],
            'workflow_state': {},
            'turn_count': 0
        }

    def get_context(self, user_id: str) -> Dict:
        """获取完整的会话上下文"""
        session = self.get_session(user_id)
        if not session:
            return self.create_session(user_id)
            
        return {
            'session_id': session['session_id'],
            'messages': session.get('messages', []),
            'current_primary_workflow': session.get('current_primary_workflow'),
            'current_secondary_workflow': session.get('current_secondary_workflow'),
            'workflow_stack': session.get('workflow_stack', []),
            'workflow_state': session.get('workflow_state', {}),
            'turn_count': session.get('turn_count', 0)
        }

    def switch_workflow(self, user_id: str, new_workflow: str, workflow_level: str = 'primary') -> None:
        """切换工作流"""
        context = self.get_context(user_id)
        old_workflow = context['current_primary_workflow']
        
        # 记录工作流切换
        if old_workflow != new_workflow:
            self.add_message(user_id, {
                'role': 'system',
                'content': f'工作流切换: {old_workflow} -> {new_workflow}',
                'timestamp': datetime.now()
            })
        
        # 原有的工作流切换逻辑
        workflow_stack = context['workflow_stack']
        
        if workflow_level == 'primary':
            # 切换主工作流时清空栈
            context['current_primary_workflow'] = new_workflow
            context['current_secondary_workflow'] = None
            context['workflow_stack'] = [new_workflow]
        else:
            # 切换次级工作流时入栈
            context['current_secondary_workflow'] = new_workflow
            workflow_stack.append(new_workflow)
            context['workflow_stack'] = workflow_stack[:2]  # 限制最多2层
            
        self.save_context(user_id, context)

    def end_current_workflow(self, user_id: str) -> None:
        """结束当前工作流"""
        context = self.get_context(user_id)
        workflow_stack = context['workflow_stack']
        
        if context['current_secondary_workflow']:
            # 如果有次级工作流，先结束次级
            workflow_stack.pop()
            context['current_secondary_workflow'] = None
            if workflow_stack:
                context['current_primary_workflow'] = workflow_stack[0]
        else:
            # 否则清空所有工作流状态
            context['current_primary_workflow'] = None
            context['workflow_stack'] = []
            context['workflow_state'] = {}
            
        self.save_context(user_id, context)

    def add_message(self, user_id: str, message: Dict[str, Any]) -> None:
        """添加消息并更新轮次计数"""
        context = self.get_context(user_id)
        
        # 构建metadata
        metadata = {
            'workflow': context['current_primary_workflow'],
            'workflow_stack': context['workflow_stack'],
            **message.get('metadata', {})
        }
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages 
                (session_id, role, content, timestamp, message_type, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    context['session_id'], 
                    message['role'], 
                    message['content'], 
                    message['timestamp'],
                    message.get('message_type', 'chat'),
                    psycopg2.extras.Json(message.get('metadata', {}))
                )
            )
            
            # 更新轮次计数和最后活动时间
            cur.execute(
                """
                UPDATE sessions 
                SET turn_count = turn_count + 1,
                    last_active = NOW()
                WHERE session_id = %s
                """,
                (context['session_id'],)
            )
            self.conn.commit()

    def cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions 
                SET current_primary_workflow = NULL,
                    current_secondary_workflow = NULL,
                    workflow_stack = '[]'::jsonb,
                    workflow_state = '{}'::jsonb
                WHERE last_active < NOW() - INTERVAL '%s seconds'
                """,
                (self.session_timeout,)
            )
            self.conn.commit()

    def save_context(self, session_id: str, context: Dict[str, Any]) -> None:
        self.logger.info(f"保存上下文 - session_id: {session_id}")
        self.logger.info(f"保存上下文 - 数据: {context}")
        """保存上下文状态"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions 
                SET current_primary_workflow = %s,
                    current_secondary_workflow = %s,
                    workflow_stack = %s,
                    workflow_state = %s,
                    last_active = NOW()
                WHERE session_id = %s
                """,
                (
                    context['current_primary_workflow'],
                    context['current_secondary_workflow'],
                    psycopg2.extras.Json(context['workflow_stack']),
                    psycopg2.extras.Json(context['workflow_state']),
                    context['session_id']
                )
            )
            self.conn.commit()

    def get_messages(self, session_id: str, limit: int = None) -> List[Dict]:
        """获取历史消息"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content, timestamp
                FROM messages 
                WHERE session_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (session_id, limit or self.max_turns)
            )
            messages = cur.fetchall()
            return [
                {
                    'role': msg[0],
                    'content': msg[1],
                    'timestamp': msg[2].isoformat()
                }
                for msg in messages
            ]

    def get_session(self, user_id: str) -> Optional[Dict]:
        """获取用户当前活跃会话"""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM sessions 
                WHERE user_id = %s 
                AND last_active > NOW() - INTERVAL '%s seconds'
                ORDER BY last_active DESC 
                LIMIT 1
                """,
                (user_id, self.session_timeout)
            )
            session = cur.fetchone()
            if not session:
                return None
                
            # 先转换为普通字典
            session_dict = dict(session)
            # 获取会话相关的消息
            messages = self.get_messages(session_dict['session_id'], self.context_window)
            session_dict['messages'] = messages
            return session_dict

    def clear_current_workflow(self, user_id: str) -> None:
        """清除当前工作流"""
        context = self.get_context(user_id)
        context['current_primary_workflow'] = None
        context['current_secondary_workflow'] = None
        context['workflow_stack'] = []
        context['workflow_state'] = {}
        self.save_context(user_id, context)

class DocumentManager:
    def __init__(self):
        self.docs = {
            "优惠券": {
                "content": "1. 新用户专享200元见面礼\n2. 每周二满100减20\n3. 会员日特享双倍优惠",
                "keywords": ["优惠券", "满减", "折扣", "新用户"],
                "type": "promotion"
            },
            "售后": {
                "content": "1. 7天无理由退换\n2. 质量问题15天包退\n3. 退款3个工作日到账",
                "keywords": ["退换", "退款", "售后", "包退"],
                "type": "service"
            },
            "会员规则": {
                "content": "1. 购物积分可兑换优惠券\n2. 会员专享活动价\n3. 生日特权双倍积分",
                "keywords": ["会员", "积分", "特权"],
                "type": "membership"
            }
        }
        
    def match_docs(self, keywords):
        matched = []
        for doc_name, doc_info in self.docs.items():
            if any(k in doc_info["keywords"] for k in keywords):
                matched.append({
                    "title": doc_name,
                    "content": doc_info["content"],
                    "type": doc_info["type"]
                })
        return matched


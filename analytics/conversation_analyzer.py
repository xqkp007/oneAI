from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from typing import Dict, List, Tuple
import jieba
from datetime import datetime
import uuid

class ConversationAnalyzer:
    """对话数据分析器"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        self._load_data()
        
    def _load_data(self):
        """加载数据"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        self.df = pd.DataFrame(self.raw_data)
        
    def analyze_workflows(self) -> Dict:
        """分析工作流程模式"""
        workflow_patterns = {
            'coupon': {
                'total_interactions': 0,
                'completion_rate': 0,
                'avg_steps': 0
            },
            'product': {
                'total_interactions': 0,
                'completion_rate': 0,
                'avg_steps': 0
            }
        }
        
        # 统计每种工作流的交情况
        for qa in self.raw_data:
            if '优惠券' in qa['question'] or '优惠' in qa['question']:
                workflow_patterns['coupon']['total_interactions'] += 1
            elif '商品' in qa['question'] or '产品' in qa['question']:
                workflow_patterns['product']['total_interactions'] += 1
                
        return workflow_patterns
        
    def analyze_user_behavior(self) -> Dict:
        """分析用户行为模式"""
        self.df['hour'] = pd.to_datetime(self.df['start_time']).dt.hour
        
        # 统计活跃时间分布
        hourly_distribution = self.df['hour'].value_counts().sort_index()
        
        # 生成时间分布图
        plt.figure(figsize=(12, 6))
        hourly_distribution.plot(kind='bar')
        plt.title('用户活跃时间分布')
        plt.xlabel('小时')
        plt.ylabel('交互次数')
        
        # 修改保存路径计算方式
        reports_dir = Path(__file__).parent / 'reports'
        plt.savefig(reports_dir / 'user_activity.png')
        plt.close()
        
        return {
            'peak_hours': hourly_distribution.nlargest(3).index.tolist(),
            'total_users': self.df['external_user_id'].nunique(),
            'avg_interactions_per_user': len(self.df) / self.df['external_user_id'].nunique()
        }
        
    def analyze_intent_patterns(self) -> Dict:
        """分析意图模式"""
        intent_patterns = Counter()
        for qa in self.raw_data:
            intent_patterns[qa['question_obj']] += 1
            
        return dict(intent_patterns.most_common())
        
    def analyze_promotion_patterns(self) -> Dict:
        """分析促销活动模式"""
        promotion_types = Counter()
        user_reactions = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for qa in self.raw_data:
            # 分析促销类型
            if '双十一' in qa['question']:
                promotion_types['双十一活动'] += 1
            elif '津贴' in qa['question']:
                promotion_types['津贴活动'] += 1
            elif '买一送一' in qa['question']:
                promotion_types['买一送一'] += 1
                
            # 分析用户反应
            msg = qa['msg_detail'].lower()
            if any(word in msg for word in ['好的', '谢谢', '满意']):
                user_reactions['positive'] += 1
            elif any(word in msg for word in ['失望', '不行', '投诉']):
                user_reactions['negative'] += 1
            else:
                user_reactions['neutral'] += 1
                
        return {
            'promotion_types': dict(promotion_types.most_common()),
            'user_reactions': user_reactions
        }
        
    def analyze_question_patterns(self) -> Dict:
        """分析问题模式"""
        question_types = Counter()
        repeated_questions = 0
        previous_questions = set()
        
        for qa in self.raw_data:
            question = qa['question']
            if question in previous_questions:
                repeated_questions += 1
            previous_questions.add(question)
            
            # 分析问题类型
            if '时间' in question:
                question_types['活动时间咨询'] += 1
            elif '价格' in question or '优惠' in question:
                question_types['价格优惠咨询'] += 1
            elif '真实' in question or '骗' in question:
                question_types['真实性质疑'] += 1
                
        return {
            'question_types': dict(question_types.most_common()),
            'repeated_rate': repeated_questions / len(self.raw_data)
        }
        
    def parse_conversation(self, msg_detail: str) -> List[Dict]:
        """将对话内容解析为结构化的对话列表"""
        messages = msg_detail.split('\n')
        conversation = []
        
        for msg in messages:
            if msg.startswith('用户：'):
                conversation.append({
                    'role': 'user',
                    'content': msg[3:]  # 去掉"用户："前缀
                })
            elif msg.startswith('管家：'):
                conversation.append({
                    'role': 'assistant',
                    'content': msg[3:]  # 去掉"管家："前缀
                })
        
        return conversation
        
    def analyze_conversation_patterns(self) -> Dict:
        """分析对话模式"""
        conversation_stats = {
            'avg_turns': 0,  # 平均对话轮次
            'user_initiative': 0,  # 用户主动发起次数
            'response_types': Counter(),  # 客服回复类型统计
            'user_emotions': Counter(),  # 用户情绪统计
        }
        
        for qa in self.raw_data:
            conversation = self.parse_conversation(qa['msg_detail'])
            
            # 统计对话轮次
            conversation_stats['avg_turns'] += len(conversation)
            
            # 分析对话发起者
            if conversation and conversation[0]['role'] == 'user':
                conversation_stats['user_initiative'] += 1
                
            # 分析客服回复类型
            for msg in conversation:
                if msg['role'] == 'assistant':
                    if '链接' in msg['content']:
                        conversation_stats['response_types']['商品链接'] += 1
                    elif '优惠' in msg['content'] or '津贴' in msg['content']:
                        conversation_stats['response_types']['优惠信息'] += 1
                    elif '好的' in msg['content'] or '可以' in msg['content']:
                        conversation_stats['response_types']['确认回复'] += 1
                        
            # 分析用户情绪
            for msg in conversation:
                if msg['role'] == 'user':
                    if any(word in msg['content'] for word in ['谢谢', '好的']):
                        conversation_stats['user_emotions']['积极'] += 1
                    elif any(word in msg['content'] for word in ['不行', '投诉', '骗']):
                        conversation_stats['user_emotions']['消极'] += 1
        
        # 计算平均值
        total_conversations = len(self.raw_data)
        conversation_stats['avg_turns'] /= total_conversations
        
        return conversation_stats
        
    def save_structured_conversations(self) -> None:
        """保存结构化的对话数据"""
        structured_data = []
        
        for qa in self.raw_data:
            conversation = self.parse_conversation(qa['msg_detail'])
            structured_data.append({
                'conversation_id': str(uuid.uuid4()),
                'external_user_id': qa['external_user_id'],
                'start_time': qa['start_time'],
                'messages': conversation
            })
        
        # 保存到新的 JSON 文件
        reports_dir = Path(__file__).parent / 'reports'
        structured_file = reports_dir / 'structured_conversations.json'
        
        with open(structured_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
    def generate_report(self) -> None:
        """生成分析报告"""
        workflow_analysis = self.analyze_workflows()
        user_behavior = self.analyze_user_behavior()
        intent_patterns = self.analyze_intent_patterns()
        promotion_analysis = self.analyze_promotion_patterns()
        question_analysis = self.analyze_question_patterns()
        conversation_analysis = self.analyze_conversation_patterns()
        
        # 保存结构化对话数据
        self.save_structured_conversations()
        
        # 使用正确的报告目录路径
        reports_dir = Path(__file__).parent / 'reports'
        report_path = reports_dir / f'analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== 客服对话系统分析报告 ===\n\n")
            
            f.write("1. 工作流程分析\n")
            f.write("-" * 50 + "\n")
            f.write(f"优惠券工作流总交互次数: {workflow_analysis['coupon']['total_interactions']}\n")
            f.write(f"商品查询工作流总交互次数: {workflow_analysis['product']['total_interactions']}\n\n")
            
            f.write("2. 用户行为分析\n")
            f.write("-" * 50 + "\n")
            f.write(f"峰值活跃时段: {user_behavior['peak_hours']}\n")
            f.write(f"总用户数: {user_behavior['total_users']}\n")
            f.write(f"平均每用户交互次数: {user_behavior['avg_interactions_per_user']:.2f}\n\n")
            
            f.write("3. 意图分布分析\n")
            f.write("-" * 50 + "\n")
            for intent, count in intent_patterns.items():
                f.write(f"{intent}: {count}次\n")
            
            f.write("\n4. 促销活动分析\n")
            f.write("-" * 50 + "\n")
            f.write("活动类型分布:\n")
            for ptype, count in promotion_analysis['promotion_types'].items():
                f.write(f"- {ptype}: {count}次\n")
            f.write("\n用户反应:\n")
            for reaction, count in promotion_analysis['user_reactions'].items():
                f.write(f"- {reaction}: {count}次\n")
            
            f.write("\n5. 问题模式分析\n")
            f.write("-" * 50 + "\n")
            f.write("问题类型分布:\n")
            for qtype, count in question_analysis['question_types'].items():
                f.write(f"- {qtype}: {count}次\n")
            f.write(f"\n重复提问率: {question_analysis['repeated_rate']:.2%}\n\n")
            
            f.write("6. 对话模式分析\n")
            f.write("-" * 50 + "\n")
            f.write(f"平均对话轮次: {conversation_analysis['avg_turns']:.2f}\n")
            f.write(f"用户主动发起比例: {conversation_analysis['user_initiative']/len(self.raw_data):.2%}\n")
            
            f.write("\n客服回复类型分布:\n")
            for rtype, count in conversation_analysis['response_types'].most_common():
                f.write(f"- {rtype}: {count}次\n")
            
            f.write("\n用户情绪分布:\n")
            for emotion, count in conversation_analysis['user_emotions'].most_common():
                f.write(f"- {emotion}: {count}次\n")

def main():
    # 从 qa_data 文件读取数据
    qa_data_file = Path(__file__).parent / 'data' / 'qa_data'
    
    # 检查并读取 qa_data 文件
    if not qa_data_file.exists():
        raise FileNotFoundError("qa_data 文件不存在")
        
    with open(qa_data_file, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    # 创建数据目录
    data_dir = Path(__file__).parent / 'data'
    conversations_dir = data_dir / 'conversations'
    
    # 创建目录
    data_dir.mkdir(exist_ok=True)
    conversations_dir.mkdir(exist_ok=True)
    
    # 创建报告目录
    reports_dir = Path(__file__).parent / 'reports'
    if reports_dir.exists() and not reports_dir.is_dir():
        reports_dir.unlink()
    reports_dir.mkdir(exist_ok=True)
    
    # 将数据写入 JSON 文件
    json_file = conversations_dir / 'conversations.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(qa_data, f, ensure_ascii=False, indent=2)
    
    # 初始化分析器并生成报告
    analyzer = ConversationAnalyzer(str(json_file))
    analyzer.generate_report()

if __name__ == "__main__":
    main()
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)  # 改为添加当前目录

from chat_engine import ChatEngine

def test_chat():
    print("开始测试聊天引擎...")
    
    # 初始化聊天引擎
    chat_engine = ChatEngine(
        api_key="sk-9eabf391ac3241718d01d2ab50087209",
        base_url="https://api.deepseek.com"
    )
    
    # 测试用户ID
    user_id = "test_user_001"
    
    # 测试消息列表
    test_messages = [
        "你好，在吗？",
        "我想了解一下参团卡",
        "满二反一活动怎么参加？",
        "这个津贴可以和优惠券一起用吗？",
        "那我还是找人工问问吧"
    ]
    
    # 测试对话流程
    for message in test_messages:
        print("\n" + "="*50)
        print(f"用户消息: {message}")
        
        # 处理消息并获取回复
        response = chat_engine.process_message(message, user_id)
        print(f"\n机器人回复: {response}")

if __name__ == "__main__":
    test_chat() 
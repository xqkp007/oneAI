import json
import uuid
from datetime import datetime

def parse_messages(msg_detail):
    """
    解析消息详情字符串，转换为消息列表
    """
    messages = []
    lines = msg_detail.split('\n')
    
    for line in lines:
        if line.startswith('用户：'):
            messages.append({
                "role": "user",
                "content": line.replace('用户：', '')
            })
        elif line.startswith('管家：'):
            messages.append({
                "role": "assistant",
                "content": line.replace('管家：', '')
            })
    
    return messages

def convert_fuli_to_structured(fuli_data):
    """
    将福利数据转换为structured_conversations格式
    """
    structured_conversations = []
    
    for conversation in fuli_data:
        # 生成新的conversation对象
        new_conversation = {
            "conversation_id": str(uuid.uuid4()),
            "external_user_id": conversation.get("external_user_id", ""),
            "start_time": conversation.get("start_time", ""),
            "messages": parse_messages(conversation.get("msg_detail", "")),
            "question_obj": conversation.get("question_obj", {})
        }
        
        structured_conversations.append(new_conversation)
        
    return structured_conversations

def main():
    # 使用完整的文件路径
    input_file = "C:/Users/PC/Desktop/zidonghua/analytics/data/result02.json"
    output_file = "C:/Users/PC/Desktop/zidonghua/analytics/reports/structured_conversations04.json"
    
    # 读取福利数据文件
    with open(input_file, "r", encoding="utf-8") as f:
        fuli_data = json.load(f)
    
    # 转换数据
    structured_data = convert_fuli_to_structured(fuli_data)
    
    # 写入新文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
import json
from pathlib import Path
from datetime import datetime

def extract_conversations_by_label(analysis_file: str, conversations_file: str, label: str) -> None:
    # 读取分析结果文件
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)
    
    # 读取原始对话文件
    with open(conversations_file, 'r', encoding='utf-8') as f:
        conversations_data = json.load(f)
    
    # 创建对话ID到messages的映射
    conv_map = {conv['conversation_id']: conv['messages'] for conv in conversations_data}
    
    # 提取指定标签的对话
    labeled_conversations = []
    
    for result in analysis_data['analysis_results']:
        content = result.get('analysis_result', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
        if label in content:
            conversation_id = result.get('conversation_id')
            if conversation_id and conversation_id in conv_map:
                labeled_conversations.append({
                    'conversation_id': conversation_id,
                    'analysis': content,
                    'messages': conv_map[conversation_id]
                })
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path('.') / f'{label}_conversations_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'label': label,
            'total_count': len(labeled_conversations),
            'conversations': labeled_conversations
        }, f, ensure_ascii=False, indent=2)
    
    print(f"已提取 {len(labeled_conversations)} 条 {label} 相关对话到文件: {output_file}")

if __name__ == "__main__":
    base_dir = Path("C:/Users/PC/Desktop/zidonghua/analytics")
    analysis_file = base_dir / "reports" / "deepseek_analysis_20241029_165404.json"
    conversations_file = base_dir / "reports" / "structured_conversations02.json"
    extract_conversations_by_label(str(analysis_file), str(conversations_file), "津贴")
import json
import pandas as pd

def process_analysis_results(json_file_path, output_excel_path):
    try:
        # 读取文件内容
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 清理JSON字符串，确保它是一个有效的JSON数组
        content = content.strip()
        if content.startswith('['):
            content = content[1:]
        if content.endswith(']'):
            content = content[:-1]
            
        # 分割成单独的JSON对象
        json_strings = content.split('},')
        
        # 处理每个JSON对象
        json_objects = []
        for json_str in json_strings:
            json_str = json_str.strip()
            if not json_str:
                continue
            if not json_str.endswith('}'):
                json_str += '}'
            try:
                obj = json.loads(json_str)
                json_objects.append(obj)
            except:
                continue
        
        # 提取字段
        rows = []
        for item in json_objects:
            if 'question_obj' in item and 'external_user_id' in item:
                rows.append({
                    'question_obj': item['question_obj'],
                    'external_user_id': item['external_user_id']
                })
        
        # 创建DataFrame并保存
        df = pd.DataFrame(rows)
        df.to_excel(output_excel_path, index=False)
        
        # 打印统计信息
        print(f"\n数据已保存到: {output_excel_path}")
        print(f"\n总记录数: {len(rows)}")
        print("\n问题类型统计:")
        print(df['question_obj'].value_counts())
        
    except Exception as e:
        print(f"处理出错: {str(e)}")

if __name__ == "__main__":
    json_file = "analytics/reports/test001.json"
    excel_file = "analytics/reports/conversations.xlsx"
    process_analysis_results(json_file, excel_file)
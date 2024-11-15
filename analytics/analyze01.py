import json
import random
import asyncio
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict
from openai import OpenAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis_deepseek.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DeepseekAnalyzer:
    def __init__(self):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key="sk-95677435b19e44d7aab0d45ef04d4728",
            base_url="https://api.deepseek.com"
        )
        self.results = []
        self.label_counts = {
            "商品最优购买方式": 0,
            "抽奖": 0,
            "津贴": 0,
            "参团卡": 0,
            "立减金": 0,
            "红包": 0,
            "其他": 0
        }
        
        # 加载prompt模板
        self.prompt_template = self._load_prompt_template()
        logging.info("Prompt template loaded successfully.")
    
    def _load_prompt_template(self) -> str:
        prompt_path = Path(__file__).parent / 'prompts' / 'conversation_analysis.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def analyze_conversation(self, conversation: Dict) -> Dict:
        try:
            conversation_id = str(conversation['conversation_id'])
            content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation['messages']])
            
            logging.info(f"Analyzing conversation ID: {conversation_id}")
            logging.info(f"Conversation content: {content}")
            
            prompt = self.prompt_template.format(
                conversation_id=conversation_id,
                content=content
            )
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": prompt}
                ],
                stream=False
            )
            
            analysis = {
                "conversation_id": conversation["conversation_id"],
                "analysis_result": response.model_dump(),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(analysis)
            logging.info(f"Successfully analyzed conversation {conversation['conversation_id']}")
            
            # 在成功分析后更新计数
            content = response.choices[0].message.content
            for label in self.label_counts.keys():
                if label in content:
                    self.label_counts[label] += 1
                    break
            
            return analysis
                    
        except Exception as e:
            logging.error(f"Exception in analyze_conversation: {str(e)}")
            return None
    
    def save_results(self, output_dir: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"deepseek_analysis_{timestamp}.json"
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 添加统计结果到输出
        final_results = {
            "analysis_results": self.results,
            "label_statistics": self.label_counts
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
            
        logging.info(f"Results saved to {output_path}")
        logging.info("标签统计结果：")
        for label, count in self.label_counts.items():
            logging.info(f"{label}: {count} 条")

    async def analyze_batch(self, conversations: List[Dict], batch_size: int = 10) -> None:
        for i in range(0, len(conversations), batch_size):
            batch = conversations[i:i + batch_size]
            logging.info(f"Starting batch analysis for {len(batch)} conversations.")
            
            # 并发处理当前批次的对话
            tasks = [self.analyze_conversation(conv) for conv in batch]
            await asyncio.gather(*tasks)
            
            # 每批处理完后添加延迟
            await asyncio.sleep(1)
            logging.info(f"Processed batch {i//batch_size + 1}")

async def main():
    file_path = "C:/Users/PC/Desktop/zidonghua/analytics/reports/structured_conversations02.json"
    
    logging.info(f"Loading conversations from {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)
    
    # 随机抽取1000个对话进行分析
    sample_size = min(1000, len(conversations))
    sampled_conversations = random.sample(conversations, sample_size)
    logging.info(f"Sampled {sample_size} conversations for analysis.")
    
    analyzer = DeepseekAnalyzer()
    await analyzer.analyze_batch(sampled_conversations, batch_size=10)
    analyzer.save_results("analytics/reports")

if __name__ == "__main__":
    asyncio.run(main())
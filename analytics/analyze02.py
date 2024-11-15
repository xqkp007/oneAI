# 导入所需的库
import json  # 用于处理JSON数据
import random  # 用于随机抽样
import asyncio  # 用于异步编程
from datetime import datetime  # 用于处理日期和时间
from pathlib import Path  # 用于处理文件路径
import logging  # 用于日志记录
from typing import List, Dict  # 用于类型注解
from openai import OpenAI  # OpenAI API客户端
import httpx  # 用于异步HTTP请求

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    handlers=[
        logging.FileHandler('analysis_deepseek.log', encoding='utf-8'),  # 将日志写入文件
        logging.StreamHandler()  # 同时在控制台显示日志
    ]
)

class DeepseekAnalyzer:
    """
    对话分析器类,用于分析客服对话内容
    """
    def __init__(self):
        # 初始化 OpenAI 客户端,设置API密钥和基础URL
        self.client = OpenAI(
            api_key="sk-95677435b19e44d7aab0d45ef04d4728",
            base_url="https://api.deepseek.com"
        )
        self.results = []  # 存储分析结果
        # 用于统计正常和异常对话的数量
        self.status_counts = {
            "正常": 0,
            "异常": 0
        }
        self.abnormal_conversations = []  # 存储异常对话的ID列表
        
        # 加载提示词模板
        self.prompt_template = self._load_prompt_template()
        logging.info("Prompt template loaded successfully.")
    
    def _load_prompt_template(self) -> str:
        """
        加载提示词模板文件
        """
        prompt_path = Path(__file__).parent / 'prompts' / 'conversation_analysis02.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def analyze_conversation(self, conversation: Dict) -> Dict:
        """
        分析单个对话
        Args:
            conversation: 包含对话内容的字典
        Returns:
            分析结果字典
        """
        try:
            conversation_id = str(conversation['conversation_id'])
            # 将对话内容格式化为字符串
            content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation['messages']])
            
            # 使用模板格式化提示词
            prompt = self.prompt_template.format(
                conversation_id=conversation_id,
                content=content
            )
            
            # 使用httpx进行异步API请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.client.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": prompt}
                        ]
                    },
                    timeout=60.0  # 增加超时时间到60秒
                )
                
                # 检查响应状态码
                response.raise_for_status()
                result = response.json()
                
                # 验证响应数据结构
                if 'choices' not in result or not result['choices']:
                    raise ValueError(f"Invalid response format: {result}")
                
                # 获取返回内容
                content = result['choices'][0]['message']['content']
                
                # 提��总评分
                total_score = None
                if "总评分:" in content:
                    try:
                        score_text = content.split("总评分:")[1].split()[0].strip()
                        total_score = float(score_text)
                    except (IndexError, ValueError):
                        logging.warning(f"Failed to parse total score for conversation {conversation_id}")
                
                # 根据总评分判断是否异常（≥ 0.8为异常）
                is_abnormal = total_score is not None and total_score >= 0.8
                
                # 构建分析结果
                analysis = {
                    "conversation_id": conversation_id,
                    "external_user_id": conversation.get("external_user_id", ""),
                    "question_obj": conversation.get("question_obj", ""),
                    "status": "异常" if is_abnormal else "正常",
                    "total_score": total_score,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 更新统计
                if is_abnormal:
                    self.status_counts["异常"] += 1
                    self.abnormal_conversations.append(conversation_id)
                else:
                    self.status_counts["正常"] += 1
                
                self.results.append(analysis)
                logging.info(f"Successfully analyzed conversation {conversation_id}")
                return analysis
                
        except httpx.HTTPError as e:
            logging.error(f"HTTP error in analyze_conversation: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Exception in analyze_conversation: {str(e)}", exc_info=True)
            return None
    
    def save_results(self, output_dir: str) -> None:
        """
        保存分析结果到JSON文件
        Args:
            output_dir: 输出目录路径
        """
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(output_dir) / f"conversation_analysis_{timestamp}.json")
        
        # 收集对话分析结果
        conversation_results = []
        abnormal_users = []
        
        for result in self.results:
            # 基础信息
            conv_info = {
                "conversation_id": result["conversation_id"],
                "external_user_id": result["external_user_id"],
                "question_obj": result["question_obj"],
                "status": result["status"],
                "total_score": result["total_score"],
                "timestamp": result["timestamp"]
            }
            
            conversation_results.append(conv_info)
            
            # 如果是异常对话，添加到异常列表
            if result["status"] == "异常":
                abnormal_users.append(conv_info)
        
        # 构建最终结果
        final_results = {
            "timestamp": datetime.now().isoformat(),
            "total_conversations": len(self.results),
            "statistics": {
                "status_counts": self.status_counts,
                "abnormal_rate": f"{(self.status_counts['异常'] / len(self.results) * 100):.2f}%"
            },
            "abnormal_conversations": abnormal_users,
            "all_conversations": conversation_results
        }
        
        # 将结果写入JSON文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        # 输出统计信息到日志
        logging.info(f"Results saved to {output_path}")
        logging.info("分析统计结果：")
        logging.info(f"正常对话: {self.status_counts['正常']} 条")
        logging.info(f"异常对话: {self.status_counts['异常']} 条")
        logging.info(f"异常率: {final_results['statistics']['abnormal_rate']}")
        
        if abnormal_users:
            logging.info("\n异常对话详情:")
            for conv in abnormal_users:
                logging.info(
                    f"- 对话ID: {conv['conversation_id']}\n"
                    f"  用户ID: {conv['external_user_id']}\n"
                    f"  问题类型: {conv['question_obj']}\n"
                    f"  评分: {conv['total_score']}\n"
                )
    
    async def analyze_batch(self, conversations: List[Dict], batch_size: int = 10) -> None:
        """
        批量分析对话,控制并发数量和等待时间
        Args:
            conversations: 对话列表
            batch_size: 每批处理的对话数量
        """
        # 创建信号量来限制并发
        semaphore = asyncio.Semaphore(10)  # 限制最大并发数为5
        
        async def analyze_with_semaphore(conv):
            async with semaphore:
                return await self.analyze_conversation(conv)
        
        all_tasks = []
        # 按批次发送请求
        for i in range(0, len(conversations), batch_size):
            batch = conversations[i:i + batch_size]
            logging.info(f"Processing batch {i//batch_size + 1} with {len(batch)} conversations.")
            
            # 创建当前批次的请求任务
            batch_tasks = [analyze_with_semaphore(conv) for conv in batch]
            all_tasks.extend(batch_tasks)
            
            # 每发送一批后等待3秒
            await asyncio.sleep(2)
        
        logging.info(f"All {len(all_tasks)} requests have been sent, waiting for responses...")
        
        # 设置更长的超时时间
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*all_tasks, return_exceptions=True),
                timeout=300  # 设置5分钟的总超时时间
            )
            
            # 统计成功结果
            valid_results = [r for r in results if r is not None]
            logging.info(f"Successfully processed {len(valid_results)} out of {len(all_tasks)} conversations.")
        except asyncio.TimeoutError:
            logging.error("Analysis timed out after 5 minutes")

async def main():
    """
    主函数,程序入口
    """
    # 设置输入文件路径
    file_path = "C:/Users/PC/Desktop/zidonghua/analytics/reports/structured_conversations04.json"
    
    # 加载对话数据
    logging.info(f"Loading conversations from {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)
    
    # 定义需要筛选的question_obj类别
    target_categories = [
        "报销", "维修", "商品使用", "催发货"
    ]

    # 定义时间范围
    start_date = datetime.strptime("2024-10-15", "%Y-%m-%d")
    end_date = datetime.strptime("2024-10-28", "%Y-%m-%d")
    
    # 按category和时间范围分组,每组抽取40条
    filtered_conversations = []
    for category in target_categories:
        # 筛选符合时间范围和类别的对话
        category_convs = [
            conv for conv in conversations 
            if (conv["question_obj"] == category and
                start_date <= datetime.strptime(conv["start_time"][:10], "%Y-%m-%d") <= end_date)
        ]
        
        # 如果该类别的对话数量大于40,随机抽取40条
        if len(category_convs) > 60:
            sampled_convs = random.sample(category_convs, 60)
            filtered_conversations.extend(sampled_convs)
        # 如果该类别的对话数量小于等于40,全部保留
        else:
            filtered_conversations.extend(category_convs)

    logging.info(f"Total filtered conversations: {len(filtered_conversations)}")
    
    # 创建分析器实例并执行分析
    analyzer = DeepseekAnalyzer()
    await analyzer.analyze_batch(filtered_conversations, batch_size=10)
    analyzer.save_results("analytics/reports")

# 程序入口点
if __name__ == "__main__":
    asyncio.run(main())
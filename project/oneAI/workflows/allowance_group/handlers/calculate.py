from typing import Dict, Any
from .base import BaseHandler
import random
import logging
from ..brain import AllowanceGroupBrain
import json
from session.session_manager import SessionManager
from openai import OpenAI
from typing import Dict, Any

class CalculateHandler(BaseHandler):
    """商品优惠计算处理器"""
    def __init__(self, logger: logging.Logger, brain: AllowanceGroupBrain, client: OpenAI, session_manager: SessionManager):
        super().__init__(logger, brain, client, session_manager)
        
    def handle(self, message: str, context: Dict[str, Any], scene_result: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("处理商品优惠计算请求...")
        
        # 1. 验证指令类型
        command = scene_result.get('command', {})
        if command.get('type') != '商品优惠计算':
            return {
                'message': '抱歉，指令类型不正确，请重新尝试。',
                'status': 'error',
                'need_followup': False,
                'reason': '指令类型错误'
            }
            
        # 2. 获取商品信息
        product_info = command.get('product_info', {})
        if (not product_info.get('name') or 
            not product_info.get('price') or 
            product_info.get('price') == '未提供'):
            product_info = {
                'name': message.replace('我想买', '').replace('帮我看看优惠', '').strip(),
                'id': 'P001',
                'price': '7999.00'  # 默认价格
            }
            
        # 3. 检查是否需要询问数量
        quantity = product_info.get('quantity')
        if not quantity:
            return {
                'message': '请问您要购买几件呢？我帮您看看怎么下单最优惠~',
                'status': 'waiting_quantity',
                'need_followup': True,
                'reason': '等待用户输入数量',
                'workflow_type': 'allowance_group',
                'context_data': {
                    'scene': 'calc',
                    'product_info': product_info
                }
            }
            
        # 4. 随机选择优惠类型
        benefit_type = 'allowance' if random.random() < 0.5 else 'group_card'
        
        # 5. 计算优惠金额
        try:
            total_price = float(product_info['price']) * int(quantity)
            if benefit_type == 'allowance':
                discount_rate = 0.10  # 10%优惠
                discount_amount = min(total_price * discount_rate, 200)  # 最高200元
            else:
                discount_rate = 0.15  # 15%优惠
                discount_amount = total_price * discount_rate
            final_price = total_price - discount_amount
        except (ValueError, TypeError) as e:
            self.logger.error(f"计算价格时出错: {str(e)}")
            return {
                'message': '抱歉，计算优惠时出现问题，请稍后重试。',
                'status': 'error',
                'need_followup': False,
                'reason': f'计算错误: {str(e)}'
            }
            
        # 6. 生成下单卡片
        order_card = {
            'product_name': product_info['name'],
            'original_price': f"{total_price:.2f}",
            'benefit_type': '津贴' if benefit_type == 'allowance' else '参团卡',
            'discount_amount': f"{discount_amount:.2f}",
            'final_price': f"{final_price:.2f}",
            'product_id': product_info['id'],
            'quantity': quantity
        }
        
        return {
            'message': '已为您生成优惠下单，点击卡片可直接下单，记得及时付款哦~',
            'status': 'normal',
            'need_followup': False,
            'reason': '优惠计算完成',
            'workflow_type': 'allowance_group',
            'order_card': order_card,
            'context_data': {'product_info': product_info},
            'workflow_state': context.get('workflow_state', {}),
            'current_secondary_workflow': None
        }

    def handle_quantity_input(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入的数量"""
        try:
            self.logger.info("开始处理数量输入...")
            self.logger.info(f"输入消息: {message}")
            self.logger.info(f"当前上下文: {context}")
            
            # 1. 先判断是否是商品查询
            if '我想买' in message or '看看优惠' in message:
                return self.handle(message, context, {
                    'command': {'type': '商品优惠计算'},
                    'scene': 'calc'
                })
            
            # 2. 使用 LLM 判断输入是否为数量
            system_prompt = """判断用户输入是否为商品数量。

            规则：
            1. 支持的数量格式：
               - 纯数字："5"
               - 带单位："5件"、"5个"
               - 中文数字："五件"、"五个"
            2. 如果是数量，需要转换为阿拉伯数字
            3. 如果不是数量，返回 is_quantity=false

            请返回JSON格式：
            {
                "is_quantity": true/false,
                "value": 数量值(阿拉伯数字),
                "reason": "判断原因"
            }

            示例：
            输入："5件" -> {"is_quantity": true, "value": 5, "reason": "明确的数量表达"}
            输入："五个" -> {"is_quantity": true, "value": 5, "reason": "中文数字数量表达"}
            输入："我要退款" -> {"is_quantity": false, "value": null, "reason": "非数量表达"}
            """
            
            self.logger.info("调用 LLM 判断数量...")
            self.logger.info(f"系统提示词: {system_prompt}")
            
            result = self._call_llm(system_prompt, message)
            self.logger.info(f"LLM 返回结果: {result}")
            
            # 验证返回格式
            if not isinstance(result, dict) or 'is_quantity' not in result:
                self.logger.error(f"LLM返回格式错误: {result}")
                return {
                    'message': '抱歉，我没能理解您输入的数量，请重新输入数字~\n(例如：输入"5件"或"5")',
                    'status': 'error',
                    'need_followup': True,
                    'reason': 'LLM返回格式错误',
                    'current_secondary_workflow': 'calc',
                    'context_data': context.get('context_data', {})
                }

            if result.get('is_quantity'):
                self.logger.info("识别到有效数量输入")
                user_id = context['session_id']
                
                # 从上下文获取完整的商品信息
                context_data = self.session_manager.get_context(user_id).get('context_data', {})
                product_info = context_data.get('product_info', {})
                
                # 更新数量
                product_info['quantity'] = result['value']
                
                # 如果缺少基本信息，设置默认值
                if not product_info.get('name'):
                    product_info['name'] = 'iPhone15pro'
                if not product_info.get('price'):
                    product_info['price'] = '7999.00'
                if not product_info.get('id'):
                    product_info['id'] = 'P001'
                
                # 保存上下文
                save_context = {
                    'session_id': user_id,
                    'context_data': {
                        'product_info': product_info
                    },
                    'current_primary_workflow': context.get('current_primary_workflow'),
                    'current_secondary_workflow': context.get('current_secondary_workflow'),
                    'workflow_stack': context.get('workflow_stack'),
                    'workflow_state': context.get('workflow_state', {}),
                    'turn_count': context.get('turn_count', 0)
                }
                
                self.logger.info(f"准备保存的上下文数据: {save_context}")
                self.session_manager.save_context(user_id, save_context)
                
                # 重新触发优惠计算，传入完整的商品信息
                return {
                    **self.handle(message, context, {
                        'command': {
                            'type': '商品优惠计算',
                            'product_info': product_info  # 包含完整信息的 product_info
                        }
                    }),
                    'current_secondary_workflow': 'calc'  # 保持在 calc 二级工作流中
                }
            else:
                self.logger.info("非数量输入，交给 brain 处理")
                brain_result = self.brain.think(message, context.get('messages', []))
                self.logger.info(f"Brain 返回结果: {brain_result}")
                scene_type = brain_result.get('scene')
                
                if scene_type in ['claim', 'calc', 'consult']:
                    self.logger.info("识别为津贴相关问题，继续当前工作流")
                    response = {
                        'message': brain_result.get('reply', '抱歉，我没有理解您的问题'),
                        'status': 'normal',
                        'need_followup': True,
                        'reason': '处理津贴相关问题',
                        'current_secondary_workflow': 'calc',
                        'context_data': context.get('context_data', {})
                    }
                else:
                    self.logger.info("非津贴相关问题，准备结束工作流")
                    response = {
                        'message': '抱歉，我可能理解有误，让我转接其他客服帮您。',
                        'status': 'workflow_switch',
                        'workflow_type': brain_result.get('target_workflow', 'human'),
                        'need_followup': False,
                        'reason': brain_result.get('exit_reason', '非津贴&参团卡意图')
                    }
                
                self.logger.info(f"最终返回结果: {response}")
                return response
                
        except Exception as e:
            self.logger.error(f"处理数量输入失败: {str(e)}")
            self.logger.error("错误详情:", exc_info=True)
            return {
                'message': '抱歉，处理输入时遇到问题，请重新告诉我购买数量~',
                'status': 'error',
                'need_followup': True,
                'reason': f'处理失败: {str(e)}',
                'current_secondary_workflow': 'calc',
                'context_data': context.get('context_data', {})
            }

    def _call_llm(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """重写父类的 _call_llm 方法，专门处理数量判断场景"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的数量识别助手。请严格按照指定格式返回结果。\n" + system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # 降低温度提高稳定性
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            self.logger.info(f"LLM原始返回: {result}")
            
            parsed_result = json.loads(result)
            
            # 验证返回格式
            if not isinstance(parsed_result, dict) or 'is_quantity' not in parsed_result:
                self.logger.error(f"LLM返回格式错误: {parsed_result}")
                return {
                    'is_quantity': False,
                    'value': None,
                    'reason': 'LLM返回格式错误'
                }
            
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"调用LLM失败: {str(e)}")
            self.logger.error("错误详情:", exc_info=True)
            return {
                'is_quantity': False,
                'value': None,
                'reason': f'LLM调用失败: {str(e)}'
            }
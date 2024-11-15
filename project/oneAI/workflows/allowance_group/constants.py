from enum import Enum

class AllowanceGroupSceneType(Enum):
    CLAIM = "claim"      # 领取场景
    CALCULATE = "calc"   # 计算场景
    CONSULT = "consult"  # 咨询场景
    OTHER = "other"      # 其他场景

class AllowanceGroupType(Enum):
    ALLOWANCE = "allowance"    # 津贴
    GROUP_CARD = "group_card"  # 参团卡

# 津贴领取链接配置
ALLOWANCE_LINKS = {
    '100': '#小程序://必要/IsQpyG1hbOmcEPE',
    '200': '#小程序://必要/A5EwOk3NkvIUgsh',
    '300': '#小程序://必要/C5ffcFf0fsjhfij'
}

# 参团卡领取链接配置
GROUP_CARD_LINKS = {
    'standard': '#小程序://必要/GroupCardStandard',
    'premium': '#小程序://必要/GroupCardPremium'
}

# 场景处理器映射
SCENE_HANDLER_MAP = {
    'claim': 'ClaimHandler',
    'calc': 'CalculateHandler',
    'consult': 'ConsultHandler',
    'other': 'ConsultHandler'
}

# 津贴规则知识库
ALLOWANCE_RULES = """
1. 领取规则：
- 活动时间：11月1日-11月11日
- 活动内容：商城首页15%津贴抵扣活动
- 领取额度：可领取999元津贴

2. 使用规则：
- 抵扣比例：一般8%-10%，特殊活动可达15%
- 使用方式：可单独或多件商品一起使用
- 叠加规则：多个津贴可叠加，但不能与其他优惠活动叠加
- 有效期：领取后3天内有效

3. 退款规则：
- 有效期内退款：津贴仍可继续使用
- 过期后退款：津贴不可继续使用
"""

# 参团卡规则知识库
GROUP_CARD_RULES = """
1. 领取规则：
- 在指定活动中领取
- 领取数量因活动而异

2. 使用规则：
- 适用范围：团购活动商品
- 优惠力度：无最低消费限制
- 特别说明：部分商品可能不参与活动

3. 有效期规则：
- 在指定活动有效期内使用
- 过期自动失效
"""
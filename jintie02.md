graph TD
A[用户输入消息] --> B[获取会话上下文]
B --> C[文本预处理]
subgraph 预处理阶段
C --> C1[分词 jieba.cut]
C1 --> C2[去停用词]
end
subgraph 意图分类阶段
C2 --> D[规则匹配]
D --> E{是否匹配到场景?}
E -->|是| F1[使用场景特定prompt]
E -->|否| F2[使用通用prompt]
F1 --> G[调用LLM]
F2 --> G
end
subgraph LLM处理
G --> H[构建消息]
H --> I[发送API请求]
I --> J[解析JSON响应]
J --> K{验证结果格式}
K -->|成功| L[返回意图结果]
K -->|失败| M[返回默认意图]
end
subgraph 工作流处理
L --> N[获取对应工作流]
M --> N
N --> O[处理消息]
O --> P[生成响应]
end
P --> Q[保存对话记录]

subgraph 津贴工作流
O --> AA{识别津贴类型}
AA -->|月度返津贴| AB[查询历史消费]
AA -->|礼包津贴| AC[礼包领取处理]
AA -->|商品津贴| AD[商品关联处理]
AA -->|通用津贴| AE[通用津贴处理]

AB --> AF[返津贴发放]
AC --> AG[礼包使用说明]
AD --> AH[商品优惠组合]
AE --> AI[津贴使用说明]

AF --> AJ[生成响应]
AG --> AJ
AH --> AJ
AI --> AJ

AJ --> AK{是否需要后续交互}
AK -->|是| AL[更新工作流状态]
AK -->|否| AM[完成工作流]

AL --> P
AM --> P
end
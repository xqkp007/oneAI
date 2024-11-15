graph TD
    %% 入口与意图识别
    Start((开始)) --> Input[用户输入]
    Input --> DialogueState{对话状态检查}
    
    %% 对话状态管理
    DialogueState -->|新对话| IntentCheck{意图识别}
    DialogueState -->|进行中| ContextCheck{上下文检查}
    
    %% 上下文处理
    ContextCheck -->|有效| ContinueScene[继续当前场景]
    ContextCheck -->|超时/无效| IntentCheck
    
    %% 意图分类路由
    IntentCheck -->|月度返津贴| MonthlyFlow[月度返场景]
    IntentCheck -->|礼包津贴| PackageFlow[礼包场景]
    IntentCheck -->|商品津贴| ProductFlow[商品场景]
    IntentCheck -->|使用咨询| UsageFlow[使用咨询]
    
    %% 月度返津贴处理
    MonthlyFlow --> CheckRecord{消费记录}
    CheckRecord -->|有记录| CalcAmount[计算金额]
    CheckRecord -->|无记录| NoRecord[无记录提示]
    CalcAmount --> GenerateMonthly[生成链接]
    
    %% 礼包津贴处理
    PackageFlow --> UserLevel{用户等级}
    UserLevel -->|普通| BasicPack[39元礼包]
    UserLevel -->|优质| PremiumPack[59元礼包]
    UserLevel -->|VIP| VIPPack[99元礼包]
    
    %% 商品津贴处理
    ProductFlow --> ProductCheck{商品检查}
    ProductCheck -->|可用| MatchCoupon[匹配津贴]
    ProductCheck -->|不可用| Explain[说明原因]
    
    %% 使用咨询处理
    UsageFlow --> QueryType{咨询类型}
    QueryType -->|使用方法| Guide[使用指南]
    QueryType -->|使用限制| Limit[限制说明]
    QueryType -->|异常问题| Problem[问题处理]
    
    %% 链接生成与验证
    GenerateMonthly & BasicPack & PremiumPack & VIPPack & MatchCoupon --> LinkProcess[链接处理]
    LinkProcess --> ValidateLink{链接验证}
    
    %% 链接处理流程
    ValidateLink -->|有效| SendLink[发送链接]
    ValidateLink -->|无效| RetryLink[重新生成]
    RetryLink --> LinkProcess
    
    %% 多轮对话处理
    SendLink --> WaitResponse{等待响应}
    WaitResponse -->|点击| TrackStatus[跟踪状态]
    WaitResponse -->|询问| HandleQuery[处理询问]
    WaitResponse -->|超时| TimeoutHandle[超时处理]
    
    %% 状态跟踪
    TrackStatus --> StatusType{状态类型}
    StatusType -->|成功| Success[完成]
    StatusType -->|失败| Failure[失败处理]
    StatusType -->|异常| Exception[异常处理]
    
    %% 结果处理
    NoRecord & Explain & Guide & Limit & Problem & Success & Failure & Exception & TimeoutHandle --> Response[生成回复]
    
    %% 情感化处理
    Response --> EmotionCheck{情感化}
    EmotionCheck -->|需要| AddEmotion[情感化表达]
    EmotionCheck -->|不需要| DirectReturn[直接返回]
    
    %% 结束流程
    AddEmotion --> UpdateState[更新状态]
    DirectReturn --> UpdateState
    UpdateState --> End((结束))
    
    %% 重试和询问处理
    HandleQuery --> DialogueState
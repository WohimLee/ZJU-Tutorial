🧩 AI 涨乐 12 类一级意图系统字典（System-Level Intent Taxonomy）

每一类都附带 “定义、涉及范围、典型子意图示例”。

#### ① 行情查询（Market_Quote）
##### 定义
用户希望获取市场、指数、板块、基金、股票的实时/历史数据。

##### 子范围示例

- 股票报价
- K线、分时
- 成交量、资金流
- 板块行情
- 指数走势
- 涨跌榜/龙虎榜
- 资金面信息

##### 典型子意图

- Query_Stock_Price
- Query_Kline
- Query_Sector_Performance
- Query_Fund_NAV

#### ② 个股分析 / AI 研究（Stock_Analysis）
##### 定义

用户希望获得某只股票的深入分析，包含：估值、事件影响、AI 诊断、趋势预测等。

##### 子范围示例

- 估值分析
- 趋势判断
- 财务分析
- 情绪/舆情
- 风险点分析
- AI 买卖判断

##### 典型子意图

- Analyze_Valuation
- Analyze_Financials
- Analyze_Risk_Points
- Explain_Price_Move

#### ③ AI 智能选股（AI_Stock_Pick）
##### 定义

用户请求系统“找股票、推荐股票、筛选股票”。

##### 子范围示例

- 热点选股
- 条件选股
- 主题选股
- 低估值选股
- 超跌反弹选股
- 趋势 follow
- AI 预测涨幅

##### 典型子意图

- Pick_By_Sector
- Pick_By_Condition
- Pick_AI_Recommend

#### ④ 市场资讯（Market_News）
##### 定义

用户要求查看公司新闻、公告、研报、政策、热点等资讯内容。

##### 子范围示例

- 公告摘要
- 热点概念
- 行业新闻
- 重大事件
- 研报分析

##### 典型子意图
- Query_Company_News
- Query_Market_Hotspot
- Summarize_Announcement

#### ⑤ 交易执行（Trade_Action）
##### 定义

用户发起 “买卖/撤单/修改订单”等明确交易行为。

##### 子范围示例

- 买入/卖出
- 订单管理
- 条件单
- 止盈/止损
- 融资融券

##### 典型子意图

- Trade_Buy
- Trade_Sell
- Trade_Cancel
- Set_Stop_Loss

#### ⑥ 盯盘提醒（Alert_Monitor）
##### 定义

用户请求系统监控市场指标并触发提醒。

##### 子范围示例

- 价格提醒
- 涨幅提醒
- 资金异动
- 异动检测
- 新闻提醒
- 财报提醒

##### 典型子意图

- Set_Price_Alert
- Set_News_Alert
- Monitor_Abnormal_Move

#### ⑦ 资产与持仓管理（Portfolio_Management）
##### 定义

用户希望了解自己的投资组合情况、风险分析、优化建议等。

##### 子范围示例

- 持仓盈亏
- 仓位结构
- 行业集中度
- 组合优化
- 风险诊断
- 收益回撤分析

##### 典型子意图

- Portfolio_Overview
- Portfolio_Risk_Analysis
- Portfolio_Optimize

#### ⑧ 基金与理财（Fund_Wealth）
##### 定义

用户查看基金、理财等非股票类资产的情况或寻求配置建议。

##### 子范围示例

- 基金净值
- 基金对比
- 基金推荐
- 低风险理财
- 定投计划

##### 典型子意图

- Fund_Query
- Fund_Compare
- Fund_Recommend

#### ⑨ 风险与合规（Risk_Compliance）
##### 定义

用户涉及到“风险等级、准入、合规、规则、税费”等方面。

##### 子范围示例

- 投资者适当性
- 产品风险等级
- 保证金要求
- 交易规则
- 税费结构

##### 典型子意图

- Query_Risk_Level
- Query_Trading_Rule
- Query_Compliance_Restriction

#### ⑩ 账户与资金（Account_Service）
##### 定义

用户希望查看账户层级信息或执行账户服务类操作。

##### 子范围示例

- 资金余额
- 可用资金
- 权限查询
- 修改个人信息
- 开通业务

##### 典型子意图

- Account_Query_Balance
- Account_Query_Permission
- Account_Modify_Info

#### ⑪ 投教与知识问答（Education_Learning）
##### 定义

用户询问知识、概念、学习内容、投资方法等。

##### 子范围示例

- 科普说明
- 投资知识
- 技术分析概念
- 风险管理
- 投资方法论

##### 典型子意图

- Explain_Concept
- Teach_Investment_Skill
- Explain_Tech_Indicator

#### ⑫ 闲聊与对话管理（Chat_General）
##### 定义

用户进行非任务类对话、闲聊、寒暄、问感受、表达情绪等。

##### 子范围示例

- 寒暄
- 情绪表达
- 非交易类开放问答
- 非金融类对话

##### 典型子意图

- General_Greeting
- General_Emotion
- General_Open_Chat
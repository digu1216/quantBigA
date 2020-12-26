### 文件夹和子系统的对应关系
1. data - 数据管理子系统
2. factor - 因子管理子系统
3. strategy - 策略管理子系统
4. trading - 交易决策子系统
5. util - 工具类文件

#### 运行步骤

1. 因子提取

   **文件路径：** factor/pe_factor.py
   
   **参数：** 开始日期和结束日期
   
2. 股票池规律统计

    **文件路径：** strategy/stock_pool/stock_pool_test.py
    
    **参数：** 开始日期、结束日期和再平衡周期
3. 回测

    **文件路径：** backtest.py
    
    **参数：** 回测开始日期和结束日期
   
4. 净值曲线
    **文件路径：** trading/profit.html
    
    **步骤：**
    1. 运行回测时，将日志从定向到一个文件中，例如：
    
        ```bash
        python backtest.py > backtest_result
        ``` 
    2. 回测正常结束后，进入到trading目录，双击打开profit.html
    3. 点击页面顶部的选择日志后面的“选择文件”按钮，选择刚才回测的日志backtest_result
    4. 曲线生成后，点击曲线上的点可以显示买入和卖出记录
    
1. 日K线数据抓取
   
   **文件路径：** data/daily_crawler.py
   
   **参数：** 抓取的开始日期和结束日期
   
1. 基础数据抓取
   
   **文件路径：** data/basic_crawler.py
   
   **参数：** 抓取的开始日期和结束日期
   
1. 财报数据抓取
   
   **文件路径：** data/finance_report_crawler.py
   
   **参数：** 无
  
1. 日线数据问题修正
   
   **文件路径：** data/fixing/daily_fixing.py
   
   **参数：** 根据需要修改main入口的方法调用，参数是开始日期和结束日期
   
1. 规模因子计算

   **文件路径：** factor/mkt_cap_factor.py
   
   **参数：** 开始日期和结束日期
   
1. 一维零投资组合

   **文件路径：** factor/zero_investment_portfolio_analysis.py
   
   **参数：** 因子名字、开始日期、结束日期、调整日期

   

    
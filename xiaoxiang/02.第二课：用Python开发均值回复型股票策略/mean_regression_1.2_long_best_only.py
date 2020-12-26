# 导入函数库
import jqdata

ADJUST_INTERVAL = 20  # 调仓周期
CHK_PF_INTERVAL = 60  # 观测窗口
PERCENT_TO_KEEP = 10  # 组合容量

# 初始化函数，回测开始时执行一次
def initialize(context):
    set_benchmark('000300.XSHG')  # 设定比较基准指数
    set_option('use_real_price', True)  # 默认复权模式

    # 设定融资/融券账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.cash, type='stock_margin')])

    # 设定交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.000, open_commission=0.0000, close_commission=0.0000, close_today_commission=0, min_commission=0), type='stock')
    # set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    
    # 设定融资/融券的利率和保证金比例
    set_option('margincash_interest_rate', 0.00)
    set_option('margincash_margin_rate', 1.0)
    set_option('marginsec_interest_rate', 0.00)
    set_option('marginsec_margin_rate', 1.0)
    """
    set_option('margincash_interest_rate', 0.08)
    set_option('margincash_margin_rate', 1.5)
    set_option('marginsec_interest_rate', 0.10)
    set_option('marginsec_margin_rate', 1.5)
    """
    
    # 设置定时运行函数
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

    # 记录交易日期及其索引
    g.all_tdays = jqdata.get_all_trade_days()
    g.date_xlat = dict([(doc[1], doc[0]) for doc in enumerate(g.all_tdays)])

    # 设定若干全局变量
    g.elapsed_days = 0
    g.rebalance_today = False
    g.new_long_pos = {}

# 在每个交易日开盘前运行
def before_market_open(context):
    cur_dt = context.current_dt.date()  # 当前日期
    if g.elapsed_days % ADJUST_INTERVAL == 0:  # 是否是调仓日
        log.info("Rebalance at %s", cur_dt)
        g.rebalance_today = True
        idx = g.date_xlat[cur_dt]

        # 观察窗口首末日期
        tail_date = g.all_tdays[idx-1]
        head_date = g.all_tdays[idx-1-CHK_PF_INTERVAL]

        # 调仓日前一天的股票列表
        candidates = list(get_all_securities(["stock"], tail_date).index)

        # 观察窗口末尾日期的股票价格
        tail_prices = get_price(candidates, tail_date, tail_date, frequency="1d", fields=["close"])
        g.tail_values = dict(tail_prices["close"].iloc[0])

        # 观察窗口起始日期的股票价格
        head_prices = get_price(candidates, head_date, head_date, frequency="1d", fields=["close"])
        g.head_values = dict(head_prices["close"].iloc[0])

        # 在观察窗口内按收益率对股票排序（从小到大）
        merged_list = []
        for code, tail_value in g.tail_values.items():
            if math.isnan(tail_value):
                continue
            if code not in g.head_values:
                continue
            head_value = g.head_values[code]
            if math.isnan(head_value):
                continue

            # 计算相对收益率
            profit_r = tail_value/head_value - 1.0

            # 保存中间结果
            merged_list.append({
                "code": code,
                "profit_r": profit_r,
                "price": tail_value
            })

        # 从首尾分别取出一定比例的股票，构造新的多空投资组合
        merged_list.sort(key=lambda x: x["profit_r"], reverse=True)

        num_to_keep = len(merged_list) * PERCENT_TO_KEEP // 100
        g.new_long_pos  = {doc["code"]:doc for doc in merged_list[0:num_to_keep]}

    else:
        g.rebalance_today = False
    
    g.elapsed_days += 1
    
# 在每个交易日开盘时运行
def market_open(context):
    p = context.portfolio.subportfolios[0]  # 融资/融券保证金账户
    if g.rebalance_today:
        # 再平衡步骤1：平掉原有多空仓位
        prev_long_pos = p.long_positions

        for code, pos in prev_long_pos.items():
            margincash_close(code, pos.closeable_amount)

        # 再平衡步骤2：开立新的多空仓位
        each_long_cash = round(p.available_margin / len(g.new_long_pos), 2)

        for code, doc in g.new_long_pos.items():
            num_to_buy = each_long_cash / g.tail_values[code] // 100 * 100
            margincash_open(code, num_to_buy)

    else:
        # 非调仓日，可以增加止盈/止损等额外操作……
        pass

# 在每个交易日收盘后运行
def after_market_close(context):
    # 查看融资融券账户相关相关信息(更多请见API-对象-SubPortfolio)
    p = context.portfolio.subportfolios[0]
    log.info('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
    log.info('查看融资融券账户相关相关信息(更多请见API-对象-SubPortfolio)：')
    log.info('总资产：', p.total_value)
    log.info('净资产：', p.net_value)
    log.info('总负债：', p.total_liability)
    log.info('融资负债：', p.cash_liability)
    log.info('融券负债：', p.sec_liability)
    log.info('利息总负债：', p.interest)
    log.info('可用保证金：', p.available_margin)
    log.info('维持担保比例：', p.maintenance_margin_rate)
    log.info('账户所属类型：', p.type)
    log.info('##############################################################')

#  -*- coding: utf-8 -*-

import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
from stock_pool import stock_pool
import traceback


def is_k_up_break_ma10(code, begin_date, end_date):
    """
    判断某只股票在某日是否满足K线上穿10日均线
    :param code: 股票代码
    :param begin_date: 开始日期
    :param end_date: 结束日期
    :return: True/False
    """

    # 如果没有指定开始日期和结束日期，则直接返回False
    if begin_date is None or end_date is None:
        return False

    # 如果股票当日停牌或者是下跌，则返回False
    daily_ks = ts.get_k_data(code, autype='hfq', start=begin_date, end=end_date)

    # 需要判断两日的K线和10日均线的相对位置，所以如果K线数不满足11个，
    # 也就是无法计算两个MA10，则直接返回False
    index_size = daily_ks.index.size
    if index_size < 11:
        return False

    daily_ks['ma'] = daily_ks['close'].rolling(10).mean()  # 计算MA10
    daily_ks['delta'] = daily_ks['close'] - daily_ks['ma']  # 比较收盘价和MA10的关系

    return daily_ks.loc[daily_ks.index[9]]['delta'] <= 0 < daily_ks.loc[daily_ks.index[10]]['delta']


def is_k_down_break_ma10(code, begin_date, end_date):
    """
    判断某只股票在某日是否满足K线下穿10日均线
    :param code: 股票代码
    :param begin_date: 开始日期
    :param end_date: 结束日期
    :return: True/False
    """

    # 如果没有指定开始日期和结束日期，则直接返回False
    if begin_date is None or end_date is None:
        return False

    daily_ks = ts.get_k_data(code, autype='hfq', start=begin_date, end=end_date)

    # 需要判断两日的K线和10日均线的相对位置，所以如果K线数不满足11个，
    # 也就是无法计算两个MA10，则直接返回False
    if daily_ks.index.size < 11:
        return False

    daily_ks['ma'] = daily_ks['close'].rolling(10).mean()    # 计算MA10
    daily_ks['delta'] = daily_ks['close'] - daily_ks['ma']   # 计算收盘价和MA10的差

    return daily_ks.loc[daily_ks.index[9]]['delta'] >= 0 > daily_ks.loc[daily_ks.index[10]]['delta']


def backtest(begin_date, end_date):
    """
    策略回测。结束后打印出收益曲线(沪深300基准)、年化收益、最大回撤、

    :param begin_date: 回测开始日期
    :param end_date: 回测结束日期
    """
    cash = 1E7
    single_position = 2E5

    # 保存持仓股的日期
    code_date_volume_dict = dict()

    # 时间为key的净值、收益和同期沪深基准
    df_profit = pd.DataFrame(columns=['net_value', 'profit', 'hs300'])

    # 因为上证指数没有停牌不会缺数，所以用它作为交易日历，
    szzz_hq_df = ts.get_k_data('000001', index=True, start=begin_date, end=end_date)
    all_dates = list(szzz_hq_df['date'])

    # 获取沪深300在统计周期内的第一天的值
    hs300_k = ts.get_k_data('000300', index=True, start=all_dates[0], end=all_dates[0])
    hs300_begin_value = hs300_k.loc[hs300_k.index[0]]['close']

    # 获取股票池数据
    rebalance_dates, date_codes_dict = stock_pool(begin_date, end_date)

    # 获取回测周期内股票池内所有股票的收盘价和前收价
    all_option_code_set = set()
    for rebalance_date in rebalance_dates:
        for code in date_codes_dict[rebalance_date]:
            all_option_code_set.add(code)

    # 缓存股票的日线数据
    code_daily_dict = dict()
    for code in all_option_code_set:
        dailies_df = ts.get_k_data(code, autype=None, start=begin_date, end=end_date)
        dailies_hfq_df = ts.get_k_data(code, autype='hfq', start=begin_date, end=end_date)
        # 计算复权因子
        dailies_df['au_factor'] = dailies_hfq_df['close'] / dailies_df['close']
        dailies_df.set_index(['date'], inplace=True)

        code_daily_dict[code] = dailies_df

    last_phase_codes = None
    this_phase_codes = None
    to_be_sold_codes = set()
    to_be_bought_codes = set()
    holding_code_dict = dict()
    last_date = None
    # 按照日期一步步回测
    for _date in all_dates:
        print('Backtest at %s.' % _date)

        # 当期持仓股票列表
        {'600000':{'cost':500,'volume':000,'last_value':234}}
        before_sell_holding_codes = list(holding_code_dict.keys())

        # 处理持仓股的除权除息
        if last_date is not None and len(before_sell_holding_codes) > 0:
            for code in before_sell_holding_codes:
                try:
                    dailies = code_daily_dict[code]
                    # 上一个交易日的复权因子
                    current_au_factor = dailies.loc[_date]['au_factor']
                    before_volume = holding_code_dict[code]['volume']
                    #
                    last_au_factor = dailies.loc[last_date]['au_factor']

                    after_volume = int(before_volume * (current_au_factor / last_au_factor))
                    holding_code_dict[code]['volume'] = after_volume
                    print('持仓量调整：%s, %6d, %10.6f, %6d, %10.6f' %
                          (code, before_volume, last_au_factor, after_volume, current_au_factor), flush=True)
                except:
                    print('持仓量调整时，发生错误：%s, %s' % (code, _date), flush=True)
                    traceback.print_exc()

        # 卖出
        if len(to_be_sold_codes) > 0:
            code_set_tmp = set(to_be_sold_codes)
            for code in code_set_tmp:
                try:
                    if code in before_sell_holding_codes:
                        holding_stock = holding_code_dict[code]
                        holding_volume = holding_stock['volume']
                        sell_price = code_daily_dict[code].loc[_date]['open']
                        sell_amount = holding_volume * sell_price
                        cash += sell_amount

                        cost = holding_stock['cost']
                        single_profit = (sell_amount - cost) * 100 / cost
                        print('卖出 %s, %6d, %6.2f, %8.2f, %4.2f' %
                              (code, holding_volume, sell_price, sell_amount, single_profit))

                        del holding_code_dict[code]
                        to_be_sold_codes.remove(code)
                except:
                    print('卖出时，发生异常：%s, %s' % (code, _date), flush=True)
                    traceback.print_exc()

        print('卖出后，现金: %10.2f' % cash)

        # 买入
        if len(to_be_bought_codes) > 0:
            for code in to_be_bought_codes:
                try:
                    if cash > single_position:
                        buy_price = code_daily_dict[code].loc[_date]['open']
                        volume = int(int(single_position / buy_price) / 100) * 100
                        buy_amount = buy_price * volume
                        cash -= buy_amount
                        holding_code_dict[code] = {
                            'volume': volume,
                            'cost': buy_amount,
                            'last_value': buy_amount}

                        print('买入 %s, %6d, %6.2f, %8.2f' % (code, volume, buy_price, buy_amount), flush=True)
                except:
                    print('买入时，发生错误：%s, %s' % (code, _date), flush=True)
                    traceback.print_exc()

        print('买入后，现金: %10.2f' % cash)

        # 持仓股代码列表
        holding_codes = list(holding_code_dict.keys())
        # 如果调整日，则获取新一期的股票列表
        if _date in rebalance_dates:
            # 暂存为上期的日期
            if this_phase_codes is not None:
                last_phase_codes = this_phase_codes
            this_phase_codes = date_codes_dict[_date]

            # 找到所有调出股票代码，在第二日开盘时卖出
            if last_phase_codes is not None:
                out_codes = find_out_stocks(last_phase_codes, this_phase_codes)
                for out_code in out_codes:
                    if out_code in holding_code_dict:
                        to_be_sold_codes.add(out_code)

        # 获取检测信号的开始日期和结束日期
        current_date_index = all_dates.index(_date)
        signal_begin_date = None
        if current_date_index >= 11:
            signal_begin_date = all_dates[current_date_index - 11]

        # 检查是否有需要第二天卖出的股票
        for holding_code in holding_codes:
            if is_k_down_break_ma10(holding_code, begin_date=signal_begin_date, end_date=_date):
                to_be_sold_codes.add(holding_code)

        # 检查是否有需要第二天买入的股票
        to_be_bought_codes.clear()
        if this_phase_codes is not None:
            for _code in this_phase_codes:
                if _code not in holding_codes and \
                        is_k_up_break_ma10(_code, begin_date=signal_begin_date, end_date=_date):
                    to_be_bought_codes.add(_code)

        # 计算总资产
        total_value = 0
        for code in holding_codes:
            try:
                holding_stock = holding_code_dict[code]
                value = code_daily_dict[code].loc[_date]['close'] * holding_stock['volume']
                total_value += value

                # 计算总收益
                profit = (value - holding_stock['cost']) * 100 / holding_stock['cost']
                # 计算单日收益
                one_day_profit = (value - holding_stock['last_value']) * 100 / holding_stock['last_value']
                # 暂存当日市值
                holding_stock['last_value'] = value

                print('持仓: %s, %10.2f, %4.2f, %4.2f' %
                      (code, value, profit, one_day_profit))

                # 保存每一日股票的持仓数
                code_date_volume_dict[code + '_' + _date] = holding_stock['volume']
            except:
                print('计算收益时发生错误：%s, %s' % (code, _date), flush=True)
                traceback.print_exc()

        total_capital = total_value + cash

        # 计算基准收益
        hs300_k_current = ts.get_k_data('000300', index=True, start=_date, end=_date)
        hs300_current_value = hs300_k_current.loc[hs300_k_current.index[0]]['close']

        print('收盘后，现金: %10.2f, 总资产: %10.2f' % (cash, total_capital), flush=True)
        last_date = _date
        df_profit.loc[_date] = {
            'net_value': round(total_capital / 1e7, 2),
            'profit': round(100 * (total_capital - 1e7) / 1e7, 2),
            'hs300': round(100 * (hs300_current_value - hs300_begin_value) / hs300_begin_value, 2)
        }

    # 打印回测收益曲线数值
    for index_date in df_profit.index:
        print('%s, %6.2f, %6.2f' %
              (index_date, df_profit.loc[index_date]['profit'], df_profit.loc[index_date]['hs300']),
              flush=True)

    drawdown = compute_drawdown(df_profit['net_value'])
    annual_profit, sharpe_ratio = compute_sharpe_ratio(df_profit['net_value'])

    print('回测结果 %s - %s，年化收益： %7.3f, 最大回撤：%7.3f, 夏普比率：%4.2f' %
          (begin_date, end_date, annual_profit, drawdown, sharpe_ratio))

    df_profit.plot(title='Backtest Result', y=['profit', 'hs300'], kind='line')
    plt.show()


def compute_sharpe_ratio(net_values):
    """
    计算夏普比率
    :param net_values: 净值列表
    """

    # 总交易日数
    trading_days = len(net_values)
    # 所有收益的DataFrame
    profit_df = pd.DataFrame(columns={'profit'})
    # 收益之后，初始化为第一天的收益
    profit_df.loc[0] = {'profit': round((net_values[0] - 1) * 100, 2)}
    # 计算每天的收益
    for index in range(1, trading_days):
        # 计算每日的收益变化
        profit = (net_values[index] - net_values[index - 1]) / net_values[index - 1]
        profit = round(profit * 100, 2)
        profit_df.loc[index] = {'profit': profit}

    # 计算标准差
    profit_std = pow(profit_df.var()['profit'], 1 / 2)

    # 年化收益
    annual_profit = compute_annual_profit(trading_days, net_values[-1])

    # 夏普比率
    sharpe_ratio = (annual_profit - 4.75) / profit_std

    return annual_profit, sharpe_ratio


def compute_drawdown(net_values):
    """
    计算最大回撤
    :param net_values: 净值列表
    """
    # 最大回撤初始值设为0
    max_drawdown = 0
    size = len(net_values)
    index = 0
    # 双层循环找出最大回撤
    for net_value in net_values:
        for sub_net_value in net_values[index:]:
            drawdown = 1 - sub_net_value / net_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        index += 1

    return max_drawdown


def compute_annual_profit(trading_days, net_value):
    """
    计算年化收益
    """

    annual_profit = 0
    if trading_days > 0:
        # 计算年数
        years = trading_days / 245
        # 计算年化收益
        annual_profit = pow(net_value, 1 / years) - 1

    annual_profit = round(annual_profit * 100, 2)

    return annual_profit


def find_out_stocks(last_phase_codes, this_phase_codes):
    """
    找到上期入选本期被调出的股票，这些股票将必须卖出
    :param last_phase_codes: 上期的股票列表
    :param this_phase_codes: 本期的股票列表
    :return: 被调出的股票列表
    """
    out_stocks = []

    for code in last_phase_codes:
        if code not in this_phase_codes:
            out_stocks.append(code)

    return out_stocks


backtest('2015-01-01', '2015-12-31')

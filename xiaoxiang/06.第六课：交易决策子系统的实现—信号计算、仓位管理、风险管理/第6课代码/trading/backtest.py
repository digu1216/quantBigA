#  -*- coding: utf-8 -*-

from pandas import DataFrame
import matplotlib.pyplot as plt
from data.data_module import DataModule
from .account import Account
from util.stock_util import get_trading_dates


class Backtest:
    def __init__(self, strategy_option, begin_date=None, end_date=None):
        self.strategy_option = strategy_option
        if begin_date is None:
            self.begin_date = self.strategy_option.begin_date()
        else:
            self.begin_date = begin_date

        if end_date is None:
            self.end_date = self.strategy_option.end_date()
        else:
            self.end_date = end_date

        self.dm = DataModule()
        self.code_daily_cache = dict()

    def start(self):
        """
        策略回测。结束后打印出收益曲线(沪深300基准)、年化收益、最大回撤
        """
        # 初始总资金
        initial_capital = self.strategy_option.capital()
        # 初始现金
        cash = initial_capital
        # 单只股票仓位上限
        single_position = self.strategy_option.single_position()

        # 从获取策略配置中获取股票池
        stock_pool = self.strategy_option.stock_pool()

        # 保存持仓股的日期
        account = Account()

        # 获取卖出信号
        sell_signal = self.strategy_option.sell_signal(account)

        # 获取买入信号
        buy_signal = self.strategy_option.buy_signal(account)

        # 时间为key的净值、收益和同期沪深基准
        df_profit = DataFrame(columns=['net_value', 'profit', 'hs300'])

        # 获取交易日历，
        all_dates = get_trading_dates(begin_date=self.begin_date, end_date=self.end_date)

        # 获取沪深300在统计周期内的第一天的值
        hs300_k = self.dm.get_k_data('000300', index=True, begin_date=all_dates[0], end_date=all_dates[0])
        hs300_begin_value = hs300_k.loc[hs300_k.index[0]]['close']

        # 获取股票池数据
        rebalance_dates, date_codes_dict = stock_pool.get_option_stocks()

        # 获取止损策略
        stop_loss_policy = self.strategy_option.get_stop_loss(account)

        # 获取止盈策略
        stop_profit_policy = self.strategy_option.get_stop_profit(account)

        # 获取加仓策略
        add_position_policy = self.strategy_option.get_add_position(account)

        # 获取回测周期内股票池内所有股票的收盘价和前收价
        all_option_code_set = set()
        for rebalance_date in rebalance_dates:
            for code in date_codes_dict[rebalance_date]:
                all_option_code_set.add(code)

        # 缓存股票的日线数据
        for code in all_option_code_set:
            dailies_df = self.dm.get_k_data(code, autype=None, begin_date=self.begin_date, end_date=self.end_date)
            dailies_df.set_index(['date'], inplace=True)

            self.code_daily_cache[code] = dailies_df

        last_phase_codes = None
        this_phase_codes = None
        to_be_sold_codes = set()
        to_be_bought_codes = set()
        last_date = None

        # 加仓
        to_be_added_signals = dict()
        to_be_added_codes = set()

        # 按照日期一步步回测
        for _date in all_dates:
            print('Backtest at %s.' % _date)

            # 处理复权
            account.adjust_holding_volume_at_open(last_date, _date)

            # 卖出
            if len(to_be_sold_codes) > 0:
                sold_codes_tmp = set(to_be_sold_codes)
                for code in sold_codes_tmp:
                    try:
                        if code in account.holding_codes:
                            holding_stock = account.get_holding(code)
                            holding_volume = holding_stock['volume']
                            sell_price = self.code_daily_cache[code].loc[_date]['open']
                            low_limit = self.code_daily_cache[code].loc[_date]['low_limit']
                            if sell_price > low_limit:
                                sell_amount = holding_volume * sell_price
                                cash += sell_amount

                                cost = holding_stock['cost']
                                single_profit = (sell_amount - cost) * 100 / cost
                                print('卖出 %s, %6d, %6.2f, %8.2f, %4.2f' %
                                      (code, holding_volume, sell_price, sell_amount, single_profit))
                            else:
                                print('当日跌停，无法卖出，股票代码：%s, 日期： %s，价格：%7.2f，跌停价：%7.2f'
                                      % (code, _date, sell_price, low_limit), flush=True)

                            # 从持仓股中卖出
                            account.sell_out(code)
                            # 从代码列表中删除
                            to_be_sold_codes.remove(code)
                    except:
                        print('卖出时，发生异常：%s, %s' % (code, _date), flush=True)

            print('卖出后，现金: %10.2f' % cash)

            # 加仓逻辑
            add_codes_tmp = set(to_be_added_codes)
            for code in add_codes_tmp:
                add_signal = to_be_added_signals[code]
                try:
                    if cash > add_signal['position']:
                        daily = self.code_daily_cache[code].loc[_date]
                        buy_price = daily['open']
                        high_limit = daily['high_limit']
                        if buy_price < high_limit:
                            volume = int(int(add_signal['position'] / buy_price) / 100) * 100
                            buy_amount = buy_price * volume
                            cash -= buy_amount
                            print('加仓 %s, %6d, %6.2f, %8.2f' % (code, volume, buy_price, buy_amount), flush=True)

                            # 更新加仓后的持仓股
                            holding = account.get_holding(code)
                            holding['cost'] += buy_amount
                            holding['last_value'] += buy_amount
                            holding['volume'] += volume
                            holding['add_times'] += 1
                            holding['last_buy_hfq_price'] = buy_price * daily['au_factor']
                            account.update_holding(code, holding)

                            # 从待加仓列表中删除
                            to_be_added_codes.remove(code)
                            del to_be_added_signals[code]
                        else:
                            print('当日涨停，无法加仓，股票代码：%s, 日期： %s，价格：%7.2f，涨停价：%7.2f'
                                  % (code, _date, buy_price, high_limit), flush=True)

                except:
                    print('加仓时，发生错误：%s, %s' % (code, _date), flush=True)

            # 买入
            if len(to_be_bought_codes) > 0:
                sorted_to_be_bought_list = list(to_be_bought_codes)
                sorted_to_be_bought_list.sort()
                for code in sorted_to_be_bought_list:
                    try:
                        if cash > single_position:
                            daily = self.code_daily_cache[code].loc[_date]
                            buy_price = daily['open']
                            high_limit = daily['high_limit']
                            if buy_price < high_limit:
                                volume = int(int(single_position / buy_price) / 100) * 100
                                buy_amount = buy_price * volume
                                cash -= buy_amount
                                print('买入 %s, %6d, %6.2f, %8.2f' % (code, volume, buy_price, buy_amount), flush=True)

                                # 维护账户的持仓股
                                account.buy_in(code, volume=volume, cost=buy_amount)

                                # 如果加仓策略不为空，则更新持仓股
                                if add_position_policy is not None:
                                    holding = account.get_holding(code)
                                    holding['last_buy_hfq_price'] = buy_price * daily['au_factor']
                                    add_position_policy.update_holding(code, _date, holding)
                            else:
                                print('当日涨停，无法买入，股票代码：%s, 日期： %s，价格：%7.2f，涨停价：%7.2f'
                                      % (code, _date, buy_price, high_limit), flush=True)

                    except:
                        print('买入时，发生错误：%s, %s' % (code, _date), flush=True)

            print('买入后，现金: %10.2f' % cash)

            # 持仓股代码列表
            holding_codes = account.holding_codes
            # 如果调整日，则获取新一期的股票列表
            if _date in rebalance_dates:
                # 暂存为上期的日期
                if this_phase_codes is not None:
                    last_phase_codes = this_phase_codes
                this_phase_codes = date_codes_dict[_date]

                # 找到所有调出股票代码，在第二日开盘时卖出
                if last_phase_codes is not None:
                    out_codes = self.find_out_stocks(last_phase_codes, this_phase_codes)
                    for out_code in out_codes:
                        if out_code in holding_codes:
                            to_be_sold_codes.add(out_code)

            # 检查是否有需要第二天卖出的股票
            for holding_code in holding_codes:
                if sell_signal.is_match(holding_code, _date):
                    to_be_sold_codes.add(holding_code)

            # 检测止损信号
            if stop_loss_policy is not None:
                for holding_code in holding_codes:
                    if stop_loss_policy.is_stop(holding_code, _date):
                        to_be_sold_codes.add(holding_code)
                        print('止损，股票：%s' % holding_code, flush=True)
                    else:
                        stop_loss_policy.update_holding(holding_code, _date)

            # 检测止盈信号
            if stop_profit_policy is not None:
                for holding_code in holding_codes:
                    if stop_profit_policy.is_stop(holding_code, _date):
                        to_be_sold_codes.add(holding_code)
                        print('止盈，股票：%s' % holding_code, flush=True)
                    else:
                        stop_profit_policy.update_holding(holding_code, _date)

            # 检测是否有需要建仓的股票
            if add_position_policy is not None:
                for holding_code in holding_codes:
                    add_signal = add_position_policy.get_add_signal(holding_code, _date)
                    if add_signal is not None:
                        to_be_added_signals[holding_code] = add_signal
                        to_be_added_codes.add(holding_code)

            # 检查是否有需要第二天买入的股票
            to_be_bought_codes.clear()
            if this_phase_codes is not None:
                for _code in this_phase_codes:
                    if _code not in holding_codes and \
                            buy_signal.is_match(_code, _date):
                        to_be_bought_codes.add(_code)


            # 计算总市值
            total_value = account.get_total_value(_date)
            # 计算总资产
            total_capital = total_value + cash

            print('收盘后，现金: %10.2f, 总资产: %10.2f' % (cash, total_capital))

            # 计算沪深300的增长
            hs300_k_current = self.dm.get_k_data('000300', index=True, begin_date=_date, end_date=_date)
            hs300_current_value = hs300_k_current.loc[hs300_k_current.index[0]]['close']

            last_date = _date
            df_profit.loc[_date] = {
                'net_value': round(total_capital / initial_capital, 2),
                'profit': round(100 * (total_capital - initial_capital) / initial_capital, 2),
                'hs300': round(100 * (hs300_current_value - hs300_begin_value) / hs300_begin_value, 2)
            }

        # 打印回测收益曲线数值
        print('Profit history start')
        for index_date in df_profit.index:
            print('%s, %6.2f, %6.2f' %
                  (index_date, df_profit.loc[index_date]['profit'], df_profit.loc[index_date]['hs300']),
                  flush=True)
        print('Profit history end')

        drawdown = self.compute_drawdown(df_profit['net_value'])
        annual_profit, sharpe_ratio = self.compute_sharpe_ratio(df_profit['net_value'])

        print('回测结果 %s - %s，年化收益： %7.3f, 最大回撤：%7.3f, 夏普比率：%4.2f' %
              (self.begin_date, self.end_date, annual_profit, drawdown, sharpe_ratio))

        df_profit.plot(title='Backtest Result', y=['profit', 'hs300'], kind='line')
        plt.show()

    def compute_sharpe_ratio(self, net_values):
        """
        计算夏普比率
        :param net_values: 净值列表
        """

        # 总交易日数
        trading_days = len(net_values)
        # 所有收益的DataFrame
        profit_df = DataFrame(columns={'profit'})
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
        annual_profit = self.compute_annual_profit(trading_days, net_values[-1])

        # 夏普比率
        sharpe_ratio = (annual_profit - 4.75) / profit_std

        return annual_profit, sharpe_ratio

    def compute_drawdown(self, net_values):
        """
        计算最大回撤
        :param net_values: 净值列表
        """
        # 最大回撤初始值设为0
        max_drawdown = 0
        index = 0
        # 双层循环找出最大回撤
        for net_value in net_values:
            for sub_net_value in net_values[index:]:
                drawdown = 1 - sub_net_value / net_value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            index += 1

        return max_drawdown

    def compute_annual_profit(self, trading_days, net_value):
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

    def find_out_stocks(self, last_phase_codes, this_phase_codes):
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


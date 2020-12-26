#  -*- coding: utf-8 -*-

from .base_stop_profit import BaseStopProfit
from data.data_module import DataModule


class TrackingStopProfit(BaseStopProfit):
    def __init__(self, account, max_profit, profit_drawdown):
        BaseStopProfit.__init__(self, account)
        self.max_profit = max_profit
        self.profit_drawdown = profit_drawdown
        self.dm = DataModule()

    def update_holding(self, code, date):
        """
        更新持仓股的最高市值
        :param code:
        :param date:
        :return:
        """
        df_daily = self.dm.get_k_data(code, autype=None, begin_date=date, end_date=date)
        if df_daily.index.size > 0:
            df_daily.set_index(['date'], 1, inplace=True)
            close = df_daily.loc[date]['close']
            holding = self.account.get_holding(code)

            current_value = holding['volume'] * close
            if 'highest_value' in holding.keys():
                if current_value > holding['highest_value']:
                    holding['highest_value'] = current_value
                    self.account.update_holding(code, holding)
            else:
                # 判断是否已经达到了最高的收益线
                profit = (current_value - holding['cost']) * 100/holding['cost']
                if profit > self.max_profit:
                    holding['highest_value'] = current_value
                    self.account.update_holding(code, holding)

    def is_stop(self, code, date):
        """
        判断股票在当前日期是否需要止盈，如果当前收益相对于最高收益的回撤已经达到了指定幅度，则止盈
        :param code: 股票代码
        :param date: 日期
        :return: True - 止盈， False - 不止盈
        """
        holding_stock = self.account.get_holding(code)
        print('止盈判断：%s' % code, flush=True)
        print(holding_stock, flush=True)
        if holding_stock is not None:
            df_daily = self.dm.get_k_data(code, autype=None, begin_date=date, end_date=date)
            if df_daily.index.size > 0:
                df_daily.set_index(['date'], 1, inplace=True)
                current_value = df_daily.loc[date]['close'] * holding_stock['volume']
                # 计算回落的百分比
                if 'highest_value' in holding_stock and current_value < holding_stock['highest_value']:
                    profit = (current_value - holding_stock['highest_value']) \
                            * 100 / holding_stock['highest_value']

                    print('止盈判断, profit: %5.2f, drawdown: %5.2f' % (profit, self.profit_drawdown), flush=True)
                    return (profit < 0) & (abs(profit) >= abs(self.profit_drawdown))

        return False


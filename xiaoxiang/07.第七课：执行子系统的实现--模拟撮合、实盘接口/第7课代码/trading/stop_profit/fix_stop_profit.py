#  -*- coding: utf-8 -*-

from .base_stop_profit import BaseStopProfit
from data.data_module import DataModule


class FixStopProfit(BaseStopProfit):
    def __init__(self, account, max_profit):
        BaseStopProfit.__init__(self, account)
        self.max_profit = max_profit

    def update_holding(self, code, date):
        pass

    def is_stop(self, code, date):
        """
        判断是否需要止盈，盈利超过指定值，则止盈
        :param code: 股票代码
        :param date: 日期
        :return: True - 止盈，False - 不止盈
        """
        holding_stock = self.account.get_holding(code)
        print('止盈判断：%s' % code, flush=True)
        print(holding_stock, flush=True)
        dm = DataModule()
        if holding_stock is not None:
            df_daily = dm.get_k_data(code, autype=None, begin_date=date, end_date=date)
            if df_daily.index.size > 0:
                df_daily.set_index(['date'], 1, inplace=True)

                profit = (holding_stock['volume'] * df_daily.loc[date]['close'] - holding_stock['cost']) \
                         * 100 / holding_stock['cost']

                return profit >= self.max_profit

        return False

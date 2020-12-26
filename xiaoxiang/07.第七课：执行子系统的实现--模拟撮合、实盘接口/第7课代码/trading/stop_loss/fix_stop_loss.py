#  -*- coding: utf-8 -*-

from .base_stop_loss import BaseStopLoss
from data.data_module import DataModule


class FixStopLoss(BaseStopLoss):
    def __init__(self, account, max_loss):
        BaseStopLoss.__init__(self, account)
        self.max_loss = max_loss

    def update_holding(self, code, date):
        pass

    def is_stop(self, code, date):
        """
        判断股票在当前日期是否需要止损
        :param code: 股票代码
        :param date: 日期
        :return: True - 止损， False - 不止损
        """
        holding_stock = self.account.get_holding(code)
        print('止损判断：%s' % code, flush=True)
        print(holding_stock, flush=True)
        dm = DataModule()
        if holding_stock is not None:
            df_daily = dm.get_k_data(code, autype=None, begin_date=date, end_date=date)
            if df_daily.index.size > 0:
                df_daily.set_index(['date'], 1, inplace=True)

                profit = (holding_stock['volume'] * df_daily.loc[date]['close'] - holding_stock['cost']) \
                        * 100 / holding_stock['cost']

                return (profit < 0) & (abs(profit) >= abs(self.max_loss))

        return False


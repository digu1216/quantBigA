#  -*- coding: utf-8 -*-

from .base_stop_loss import BaseStopLoss
from data.data_module import DataModule


class TrackingStopLoss(BaseStopLoss):
    def __init__(self, account, max_loss):
        BaseStopLoss.__init__(self, account)
        self.max_loss = max_loss
        self.dm = DataModule()

    def update_holding(self, code, date):
        """
        更新持仓股的最高价
        :param code:
        :param date:
        :return:
        """
        df_daily = self.dm.get_k_data(code, autype='hfq', begin_date=date, end_date=date)
        if df_daily.index.size > 0:
            df_daily.set_index(['date'], 1, inplace=True)
            close = df_daily.loc[date]['close']
            holding = self.account.get_holding(code)
            if 'highest' not in holding or holding['highest'] < close:
                holding['highest'] = close
                self.account.update_holding(code, holding)

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
        if holding_stock is not None:
            df_daily = self.dm.get_k_data(code, autype='hfq', begin_date=date, end_date=date)
            if df_daily.index.size > 0:
                df_daily.set_index(['date'], 1, inplace=True)
                close = df_daily.loc[date]['close']
                # 计算回落的百分比
                if 'highest' in holding_stock and close < holding_stock['highest']:
                    profit = (close - holding_stock['highest']) \
                            * 100 / holding_stock['highest']
                    print('止损判断：收盘价：%6.2f, 历史最高：%6.2f， 回撤：%5.2f'
                          % (close, holding_stock['highest'], profit), flush=True)
                    return (profit < 0) & (abs(profit) >= abs(self.max_loss))

        return False


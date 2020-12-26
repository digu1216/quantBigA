#  -*- coding: utf-8 -*-

from data.data_module import DataModule
import traceback

"""
账户类，主要负责持仓股
"""


class Account:
    def __init__(self):
        self.holding = dict()
        self.holding_codes = set()
        self.dm = DataModule()

    def buy_in(self, code, volume, cost):
        self.holding[code] = {
            'volume': volume,
            'cost': cost,
            'last_value': cost}
        self.holding_codes.add(code)

    def sell_out(self, code):
        del self.holding[code]
        self.holding_codes.remove(code)

    def get_holding(self, code):
        """
        通过股票代码获取该股票的持仓情况
        :param code: 股票代码
        :return: 持仓对象，如果没有该股票的持仓，则返回None
        """
        if code in self.holding_codes:
            return self.holding[code]
        else:
            return None

    def update_holding(self, code, updated_holding):
        """
        更新该持仓股的字段
        :param code: 股票代码
        :param updated_holding: 新的持仓股信息
        """
        if code in self.holding_codes:
            self.holding[code] = updated_holding

    def adjust_holding_volume_at_open(self, last_date=None, current_date=None):
        """
        开盘时，处理持仓股的复权
        :param last_date: 上一个交易日
        :param current_date: 当前交易日
        """

        if last_date is not None and len(self.holding_codes) > 0:
            for code in self.holding_codes:
                try:
                    dailies = self.dm.get_k_data(code=code, begin_date=last_date, end_date=current_date)
                    if dailies.index.size == 2:
                        dailies.set_index(['date'], 1, inplace=True)
                        current_au_factor = dailies.loc[current_date]['au_factor']
                        before_volume = self.holding[code]['volume']
                        last_au_factor = dailies.loc[last_date]['au_factor']

                        after_volume = int(before_volume * (current_au_factor / last_au_factor))
                        self.holding[code]['volume'] = after_volume
                        print('持仓量调整：%s, %6d, %10.6f, %6d, %10.6f' %
                              (code, before_volume, last_au_factor, after_volume, current_au_factor), flush=True)
                except:
                    print('持仓量调整时，发生错误：%s, %s' % (code, current_date), flush=True)
                    traceback.print_exc()

    def get_total_value(self, date):
        """
        计算当期那持仓股在某一天的总市值，并更新持仓股的上一个市值
        :param date: 日期
        """
        total_value = 0
        dailies = self.dm.get_stocks_one_day_k_data(list(self.holding_codes), date=date)
        if dailies.index.size > 0:
            dailies.set_index(['code'], 1, inplace=True)
            for code in self.holding_codes:
                try:
                    holding_stock = self.holding[code]
                    value = dailies.loc[code]['close'] * holding_stock['volume']
                    total_value += value

                    # 计算总收益
                    profit = (value - holding_stock['cost']) * 100 / holding_stock['cost']
                    # 计算单日收益
                    last_value = holding_stock['last_value']
                    one_day_profit = (value - last_value) * 100 / last_value
                    # 暂存当日市值
                    self.holding[code]['last_value'] = value

                    print('持仓: %s, %10.2f, %10.2f, %4.2f, %4.2f' %
                          (code, value, last_value, profit, one_day_profit))
                except:
                    print('计算收益时发生错误：%s, %s' % (code, date), flush=True)

        return total_value

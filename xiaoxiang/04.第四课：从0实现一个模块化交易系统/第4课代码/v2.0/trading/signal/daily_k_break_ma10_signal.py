#  -*- coding: utf-8 -*-

from data.data_module import DataModule

"""
当日K线上穿和下穿10日均线的判断
"""

class DailyKBreakMA10Signal:
    def __init__(self):
        self.dm = DataModule()

    def is_k_up_break_ma10(self, code, begin_date, end_date):
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

        daily_ks = self.dm.get_k_data(code, autype='hfq', begin_date=begin_date, end_date=end_date)
        # 需要判断两日的K线和10日均线的相对位置，所以如果K线数不满足11个，
        # 也就是无法计算两个MA10，则直接返回False
        index_size = daily_ks.index.size
        if index_size < 11:
            return False

        # 比较收盘价和MA10的关系
        daily_ks['ma'] = daily_ks['close'].rolling(10).mean()
        daily_ks['delta'] = daily_ks['close'] - daily_ks['ma']

        is_break_up = (daily_ks.loc[daily_ks.index[9]]['delta'] <= 0 < daily_ks.loc[daily_ks.index[10]]['delta'])

        return is_break_up

    def is_k_down_break_ma10(self, code, begin_date, end_date):
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

        daily_ks = self.dm.get_k_data(code, autype='hfq', begin_date=begin_date, end_date=end_date)

        # 需要判断两日的K线和10日均线的相对位置，所以如果K线数不满足11个，
        # 也就是无法计算两个MA10，则直接返回False
        if daily_ks.index.size < 11:
            return False

        # 比较收盘价和MA10的关系
        daily_ks['ma'] = daily_ks['close'].rolling(10).mean()
        daily_ks['delta'] = daily_ks['close'] - daily_ks['ma']

        return daily_ks.loc[daily_ks.index[9]]['delta'] >= 0 > daily_ks.loc[daily_ks.index[10]]['delta']

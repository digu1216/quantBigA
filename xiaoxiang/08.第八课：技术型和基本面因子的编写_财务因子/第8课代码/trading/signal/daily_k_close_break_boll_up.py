#  -*- coding: utf-8 -*-

from util.database import DB_CONN
from .base_signal import BaseSignal

"""
当日K线突破Boll上轨
"""


class DailyKCloseBreakBollUp(BaseSignal):
    def __init__(self, account):
        BaseSignal.__init__(self, account)
        self.collection = DB_CONN['boll_signal']

    def is_match(self, code, date):
        """
        股票是否在某日符合当日K线下穿10日均线的信号
        :param code: 股票代码
        :param date: 日期
        :return: True/False, True - 符合 False - 不符合
        """
        count = self.collection.count({'code': code, 'date': date, 'direction': 'up'})

        return count == 1




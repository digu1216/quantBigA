#  -*- coding: utf-8 -*-

from abc import abstractmethod

"""
信号的基类
"""

class BaseSignal:
    def __init__(self, account):
        self.account = account

    @abstractmethod
    def is_match(self, code, date):
        """
        验证股票在某个时刻是否符合某个信号
        :param code: 股票代码
        :param date: 日期
        :return:
        """
        pass
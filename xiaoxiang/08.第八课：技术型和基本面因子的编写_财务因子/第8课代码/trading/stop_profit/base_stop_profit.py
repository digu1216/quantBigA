#  -*- coding: utf-8 -*-

from abc import abstractmethod


class BaseStopProfit:
    def __init__(self, account):
        self.account = account

    @abstractmethod
    def update_holding(self, code, date):
        """
        更新持仓股的一些信息
        :param code: 股票代码
        :param date: 日期
        """
        pass

    @abstractmethod
    def is_stop(self, code, date):
        """
        是否需要止损
        :param code: 股票代码
        :param date: 日期
        :return: True - 止损 False - 不止损
        """
        pass


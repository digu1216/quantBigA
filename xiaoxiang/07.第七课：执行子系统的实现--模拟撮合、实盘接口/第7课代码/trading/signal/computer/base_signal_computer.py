#  -*- coding: utf-8 -*-

from util.database import DB_CONN
from abc import abstractmethod

"""
信号计算的基类
"""


class BaseSignalComputer:
    def __init__(self, name):
        self.name = name
        self.collection = DB_CONN[name]

    @abstractmethod
    def compute(self, begin_date, end_date):
        """
        计算指定周期内的信号，并存储到数据库中
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """
        pass
#  -*- coding: utf-8 -*-

from pymongo import MongoClient
from abc import abstractmethod
from util.database import DB_CONN

"""
因子的基类。
"""


class BaseFactor:
    def __init__(self, name):
        """
        初始化因子
        :param name: 因子名称
        """
        self.name = name
        self.collection = DB_CONN[name]


    def name(self):
        return self.name

    @abstractmethod
    def compute(self, begin_date, end_date):
        """
        计算指定周期内的因子值，并存入数据库
        :param begin_date:  开始日期
        :param end_date:  结束日期
        """
        pass

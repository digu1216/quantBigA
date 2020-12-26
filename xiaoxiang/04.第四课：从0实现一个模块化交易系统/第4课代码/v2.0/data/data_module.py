#  -*- coding: utf-8 -*-

from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
import tushare as ts
from util.database import DB_CONN

"""
数据处理子系统，主要完成的工作
1. 从外部数据源获取数据，并保存到数据库中
2. 为交易系统提供数据接口
"""


class DataModule:
    def __init__(self):
        self.db = DB_CONN

    def get_k_data(self, code, index=None, autype=None, period='D', begin_date=None, end_date=None):
        """
        获取指定股票代码在固定周期的数据
        :param code: 股票代码
        :param index: 是否是指数
        :param autype: 复权类型，None - 不复权，qfq - 前复权, hfq - 后复权
        :param period: K线周期，D - 日线(默认值)，W - 周线， M - 月线，M1 - 1分钟，M5 - 5分钟
        :param begin_date: 数据的开始日期
        :param end_date: 数据的结束日期
        """
        print("子系统：数据处理，操作：获取K线数据，状态：开始，股票：%s, 级别：%s, 开始日期：%s，结束日期： %s" %
              (code, period, begin_date, end_date), flush=True)
        dailies_df = ts.get_k_data(code, index=index, autype=autype, start=begin_date, end=end_date)
        print("子系统：数据处理，操作：获取K线数据，状态：结束，股票：%s, 级别：%s, 开始日期：%s，结束日期： %s" %
              (code, period, begin_date, end_date), flush=True)

        return dailies_df

    def get_basic_data(self, code, begin_date=None, end_date=None):
        """
        """
        print("子系统：数据处理，操作：获取基本数据，状态：开始，股票：%s, 级别：%s, 开始日期：%s，结束日期： %s" %
              (code, period, begin_date, end_date), flush=True)
        print("子系统：数据处理，操作：获取基本数据，状态：结束，股票：%s, 级别：%s, 开始日期：%s，结束日期： %s" %
              (code, period, begin_date, end_date), flush=True)
        pass

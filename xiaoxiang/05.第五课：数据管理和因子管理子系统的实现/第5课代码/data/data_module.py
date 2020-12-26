#  -*- coding: utf-8 -*-

from pymongo import ASCENDING
from util.database import DB_CONN
from pandas import DataFrame

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
        :return: 包含K线的DataFrame
        """
        print("子系统：数据处理，操作：获取K线数据，状态：开始，股票：%s, 级别：%s, 开始日期：%s，结束日期： %s" %
              (code, period, begin_date, end_date), flush=True)

        if index:
            # 如果是指数，则从daily数据集中查询数据
            daily_cursor = self.db['daily'].find(
                {'code': code,  'index': True, 'date': {'$gte': begin_date, '$lte': end_date}},
                sort=[('date', ASCENDING)],
                projection={'_id': False},
                batch_size=500)
        else:
            # 如果不是指数，则根据复权类型从相应的数据集中查询数据
            if autype is None:
                daily_cursor = self.db['daily'].find(
                    {'code': code, 'index': False, 'date': {'$gte': begin_date, '$lte': end_date}},
                    sort=[('date', ASCENDING)],
                    projection={'_id': False},
                    batch_size=500)
            else:
                daily_cursor = self.db['daily_' + autype].find(
                    {'code': code, 'index': False, 'date': {'$gte': begin_date, '$lte': end_date}},
                    sort=[('date', ASCENDING)],
                    projection={'_id': False},
                    batch_size=500)

        dailies_df = DataFrame([daily for daily in daily_cursor])

        # index字段不返回
        dailies_df.drop(['index'], 1, inplace=True)

        print("子系统：数据处理，操作：获取K线数据，状态：结束，股票：%s, 级别：%s, 开始日期：%s，结束日期： %s" %
              (code, period, begin_date, end_date), flush=True)

        return dailies_df

    def get_one_day_k_data(self, autype=None, period='D', date=None):
        """
        获取某一日所有股票的K线数据
        :param autype: 复权类型，None - 不复权，qfq - 前复权, hfq - 后复权
        :param period: K线周期，D - 日线(默认值)，W - 周线， M - 月线，M1 - 1分钟，M5 - 5分钟
        :param date: 日期
        :return: 包含K线的DataFrame
        """
        print("子系统：数据处理，操作：获取K线数据，状态：开始， 级别：%s, 日期：%s" %
              (period, date), flush=True)

        # 根据复权类型从相应的数据集中查询数据
        if autype is None:
            daily_cursor = self.db['daily'].find(
                {'index': False, 'date': date},
                projection={'_id': False},
                batch_size=500)
        else:
            daily_cursor = self.db['daily_' + autype].find(
                {'index': False, 'date': date},
                projection={'_id': False},
                batch_size=500)

        dailies_df = DataFrame([daily for daily in daily_cursor])

        # index字段不返回
        dailies_df.drop(['index'], 1, inplace=True)

        print("子系统：数据处理，操作：获取K线数据，状态：开始， 级别：%s, 日期：%s" %
              (period, date), flush=True)

        return dailies_df

    def get_stock_basic_at(self, date):
        """
        查询出所有股票在某个交易日的基本数据
        :param date: 指定的日期
        :return: 基本信息的DataFrame
        """

        basic_cursor = self.db['basic'].find(
            {'date': date},
            projection={'_id': False},
            batch_size=1000)

        df_basic = DataFrame([basic for basic in basic_cursor])

        return df_basic


if __name__ == '__main__':
    print(DataModule().get_stock_basic_at('2015-01-01').index.size)

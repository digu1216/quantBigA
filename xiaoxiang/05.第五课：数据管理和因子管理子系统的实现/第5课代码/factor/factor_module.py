#  -*- coding: utf-8 -*-

from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pandas import DataFrame
from util.database import DB_CONN

"""
因子管理子系统
"""


class FactorModule:
    def get_single_stock_factors(self, code, factor, begin_date, end_date):
        """
        获取某只股票的某个因子在一段时间内的值
        :param code:  股票代码
        :param factor:  因子名称
        :param begin_date: 开始日期
        :param end_date: 结束日期
        :return: DataFrame(columns=['code',factor, 'date'])
        """

        factor_collection = DB_CONN[factor]

        factor_cursor = factor_collection.find(
            {'code': code, 'date': {'$gte': begin_date, '$lte': end_date}},
            sort=[('date', ASCENDING)])

        factor_df = DataFrame(
            [{
                'date': x['date'],
                factor: x[factor],
                'code': x['code']
            } for x in factor_cursor])

        return factor_df

    def get_single_date_factors(self, factor, date):
        """
        获取某个因子在某个交易日的所有股票的数据
        :param factor: 因子名称
        :param date: 日期
        :return: DataFrame(columns=['code',factor, 'date'])
        """
        factor_collection = DB_CONN[factor]

        factor_cursor = factor_collection.find({'date': date})

        factor_df = DataFrame(
            [{
                'date': x['date'],
                factor: x[factor],
                'code': x['code']
            } for x in factor_cursor])

        return factor_df

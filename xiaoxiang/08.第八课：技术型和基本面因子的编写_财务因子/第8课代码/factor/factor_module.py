#  -*- coding: utf-8 -*-

from datetime import datetime

from pandas import DataFrame
from pymongo import ASCENDING

from util.database import DB_CONN
from factor.mkt_cap_factor import MktCapFactor
from factor.pe_factor import PEFactor

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

    def compute(self):
        # 所有的因子实例
        factors = [
            PEFactor(),
            MktCapFactor()
        ]

        now = datetime.now().strftime('%Y-%m-%d')
        for factor in factors:
            print('开始计算因子：%s, 日期：%s' % (factor.name, now), flush=True)
            factor.compute(begin_date='2018-01-01', end_date=now)
            print('结束计算因子：%s, 日期：%s' % (factor.name, now), flush=True)

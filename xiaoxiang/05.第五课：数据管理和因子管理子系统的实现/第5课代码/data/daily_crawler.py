#  -*- coding: utf-8 -*-

from pymongo import UpdateOne
from util.database import DB_CONN
import tushare as ts
from datetime import datetime

"""
从tushare获取日K数据，保存到本地的MongoDB数据库中
"""


class DailyCrawler:
    def __init__(self):
        self.daily = DB_CONN['daily']
        self.daily_qfq = DB_CONN['daily_qfq']
        self.daily_hfq = DB_CONN['daily_hfq']

    def crawl_index(self, begin_date=None, end_date=None):
        """
        抓取指数的日线数据，并保存到本地数据数据库中
        抓取的日期范围从2008-01-01至今
        """
        index_codes = ['000001', '000300', '399001', '399005', '399006']

        # 设置默认的日期范围
        if begin_date is None:
            begin_date = '2008-01-01'

        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        for code in index_codes:
            df_daily = ts.get_k_data(code, index=True, start=begin_date, end=end_date)
            self.save_data(code, df_daily, self.daily, {'index': True})

    def save_data(self, code, df_daily, collection, extra_fields=None):
        """
        将从网上抓取的数据保存到本地MongoDB中

        :param code: 股票代码
        :param df_daily: 包含日线数据的DataFrame
        :param collection: 要保存的数据集
        :param extra_fields: 除了K线数据中保存的字段，需要额外保存的字段
        """
        update_requests = []
        for df_index in df_daily.index:
            daily_obj = df_daily.loc[df_index]
            doc = self.daily_obj_2_doc(code, daily_obj)

            if extra_fields is not None:
                doc.update(extra_fields)

            update_requests.append(
                UpdateOne(
                    {'code': doc['code'], 'date': doc['date']},
                    {'$set': doc},
                    upsert=True)
            )

        # 批量写入，提高访问效率
        if len(update_requests) > 0:
            update_result = collection.bulk_write(update_requests, ordered=False)
            print('保存日线数据，代码： %s, 插入：%4d条, 更新：%4d条' %
                  (code, update_result.upserted_count, update_result.modified_count),
                  flush=True)

    def crawl(self, begin_date=None, end_date=None):
        """
        获取所有股票从2008-01-01至今的K线数据（包括前复权、后复权和不复权三种），保存到数据库中
        """

        # 获取所有股票代码
        stock_df = ts.get_stock_basics()
        codes = list(stock_df.index)

        # 设置默认的日期范围
        if begin_date is None:
            begin_date = '2008-01-01'

        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        for code in codes:
            # 抓取不复权的价格
            df_daily = ts.get_k_data(code, autype=None, start=begin_date, end=end_date)
            self.save_data(code, df_daily, self.daily, {'index': False})

            # 抓取前复权的价格
            df_daily_qfq = ts.get_k_data(code, autype='qfq', start=begin_date, end=end_date)
            self.save_data(code, df_daily_qfq, self.daily_qfq, {'index': False})

            # 抓取后复权的价格
            df_daily_hfq = ts.get_k_data(code, autype='hfq', start=begin_date, end=end_date)
            self.save_data(code, df_daily_hfq, self.daily_hfq, {'index': False})

    @staticmethod
    def daily_obj_2_doc(code, daily_obj):
        return {
            'code': code,
            'date': daily_obj['date'],
            'close': daily_obj['close'],
            'open': daily_obj['open'],
            'high': daily_obj['high'],
            'low': daily_obj['low'],
            'volume': daily_obj['volume']
        }


if __name__ == '__main__':
    dc = DailyCrawler()
    dc.crawl_index('2018-01-01', '2018-12-31')
    # dc.crawl()

#  -*- coding: utf-8 -*-

from pymongo import UpdateOne
from util.database import DB_CONN
import tushare as ts
from datetime import datetime

"""
从tushare获取日K数据，保存到本地的MongoDB数据库中
"""


class MinuteCrawler:
    def __init__(self):
        self.minute = DB_CONN['minute']

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
                    {'code': doc['code'], 'date': doc['date'], 'index': doc['index'], 'time': doc['time']},
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
            df_daily = ts.get_k_data(code, autype=None, ktype='15', start=begin_date, end=end_date)
            self.save_data(code, df_daily, self.minute, {'index': False})

    @staticmethod
    def daily_obj_2_doc(code, minute_obj):
        return {
            'code': code,
            'date': minute_obj['date'][0:10],
            'close': minute_obj['close'],
            'time': minute_obj['date'],
            'open': minute_obj['open'],
            'high': minute_obj['high'],
            'low': minute_obj['low'],
            'volume': minute_obj['volume']
        }


if __name__ == '__main__':
    dc = MinuteCrawler()
    dc.crawl('2015-01-01', '2018-12-31')

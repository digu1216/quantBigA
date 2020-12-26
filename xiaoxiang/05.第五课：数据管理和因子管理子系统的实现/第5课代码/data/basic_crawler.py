#  -*- coding: utf-8 -*-

from pymongo import UpdateOne
from util.database import DB_CONN
from util.stock_util import get_trading_dates
import tushare as ts
from datetime import datetime, timedelta
import traceback

"""
从tushare获取股票基础数据，保存到本地的MongoDB数据库中
"""


class BasicCrawler:
    def __init__(self):
        self.db = DB_CONN['basic']

    def crawl_basic(self, begin_date=None, end_date=None):
        """
        抓取指定时间范围内的股票基础信息
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """

        if begin_date is None:
            begin_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        if end_date is None:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        all_dates = get_trading_dates(begin_date, end_date)

        for date in all_dates:
            try:
                self.crawl_basic_at_date(date)
            except:
                print('抓取股票基本信息时出错，日期：%s' % date, flush=True)


    def crawl_basic_at_date(self, date):
        """
        从Tushare抓取指定日期的股票基本信息
        :param date: 日期
        """
        # 默认推送上一个交易日的数据
        df_basics = ts.get_stock_basics(date)

        # 如果当日没有基础信息，在不做操作
        if df_basics is None:
            return

        update_requests = []
        codes = set(df_basics.index)
        for code in codes:
            doc = dict(df_basics.loc[code])
            try:
                # 将20180101转换为2018-01-01的形式
                time_to_market = datetime\
                    .strptime(str(doc['timeToMarket']), '%Y%m%d')\
                    .strftime('%Y-%m-%d')

                # 解决流通股本和总股本单位不一致的情况
                totals = float(doc['totals'])
                # 这里假设最大规模的股本不超过5000亿，股本规模的最大工商银行是3564亿
                if totals > 5000:
                    totals *= 1E4
                else:
                    totals *= 1E8

                outstanding = float(doc['outstanding'])
                # 这里假设最大规模的股本不超过5000亿，股本规模的最大工商银行是3564亿
                if outstanding > 5000:
                    outstanding *= 1E4
                else:
                    outstanding *= 1E8

                # 保存时增加date字段，因为明天都会有一条数据
                doc.update({
                    'code': code,
                    'date': date,
                    'timeToMarket': time_to_market,
                    'outstanding': outstanding,
                    'totals': totals
                })

                update_requests.append(
                    UpdateOne(
                        {'code': code, 'date': date},
                        {'$set': doc}, upsert=True))
            except:
                print('发生异常，股票代码：%s，日期：%s' % (code, date), flush=True)
                print(doc, flush=True)

        if len(update_requests) > 0:
            update_result = self.db.bulk_write(update_requests, ordered=False)

            print('抓取股票基本信息，日期：%s, 插入：%4d条，更新：%4d条' %
                  (date, update_result.upserted_count, update_result.modified_count), flush=True)


if __name__ == '__main__':
    BasicCrawler().crawl_basic('2018-01-01', '2018-12-31')




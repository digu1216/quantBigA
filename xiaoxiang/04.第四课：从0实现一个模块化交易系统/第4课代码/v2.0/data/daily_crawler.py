#  -*- coding: utf-8 -*-

from util.database import DB_CONN
import tushare as ts

"""
从tushare获取日K数据，保存到本地的MongoDB数据库中
"""


class DailyCralwer:
    def __init__(self):
        self.daily = DB_CONN['daily']
        self.daily_qfq = DB_CONN['daily_qfq']
        self.daily_hfq = DB_CONN['daily_hfq']

    def crawl(self):
        """
        获取10年的K线数据，保存到数据库中
        """

        # 因为上证指数没有停牌不会缺数，所以用它作为交易日历，

    szzz_hq_df = ts.get_k_data('000001', index=True, start='2008-01-01', end='2018-06-30')
    all_dates = list(szzz_hq_df['date'])

    # 获取所有股票代码
    stock_df = ts.get_stock_basics()
    codes = list(stock_df['code'])

    for code in codes:
        # 抓取不复权的价格
        dailies = ts.get_k_data(code, autype=None, start='2008-01-01', end='2018-06-30')

        # 抓取前复权的价格
        dailies_qfq = ts.get_k_data(code, autype='qfq', start='2008-01-01', end='2018-06-30')

        # 抓取后复权的价格
        dailies_hfq = ts.get_k_data(code, autype='hfq', start='2008-01-01', end='2018-06-30')

        dailies['adjfactor'] = dailies_hfq['close'] / dailies['close']

        # 将date日期作为
        dailies.set_index(['date'], inplace=True)
        dailies_hfq.set_index(['date'], inplace=True)
        dailies_qfq.set_index(['date'], inplace=True)

        # 通过发现是否停牌
        for _date in all_dates:


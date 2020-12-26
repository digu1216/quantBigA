#  -*- coding: utf-8 -*-

from pymongo import UpdateOne, DESCENDING
from factor.base_factor import BaseFactor
from data.finance_report_crawler import FinanceReportCrawler
from data.data_module import DataModule
from util.stock_util import get_all_codes
from util.database import DB_CONN

"""
实现市盈率因子的计算和保存
"""


class PEFactor(BaseFactor):
    def __init__(self):
        BaseFactor.__init__(self, name='pe')

    def compute(self, begin_date, end_date):
        """
        计算指定时间段内所有股票的该因子的值，并保存到数据库中
        :param begin_date:  开始时间
        :param end_date: 结束时间
        """
        dm = DataModule()

        # 获取所有股票
        codes = get_all_codes()

        for code in codes:
            print('计算市盈率, %s' % code)
            df_daily = dm.get_k_data(code, autype=None, begin_date=begin_date, end_date=end_date)

            if df_daily.index.size > 0:
                df_daily.set_index(['date'], 1, inplace=True)

                update_requests = []
                for date in df_daily.index:
                    finance_report = DB_CONN['finance_report'].find_one(
                        {'code': code, 'report_date': {'$regex': '\d{4}-12-31'}, 'announced_date': {'$lte': date}},
                        sort=[('announced_date', DESCENDING)]
                    )

                    if finance_report is None:
                        continue

                    # 计算滚动市盈率并保存到daily_k中
                    eps = 0
                    if finance_report['eps'] != '-':
                        eps = finance_report['eps']

                    # 计算PE
                    if eps != 0:
                        pe = round(df_daily.loc[date]['close'] / eps, 3)

                        print('%s, %s, %s, eps: %5.2f, pe: %6.2f' %
                              (code, date, finance_report['announced_date'], finance_report['eps'], pe),
                              flush=True)

                        update_requests.append(
                            UpdateOne(
                                {'code': code, 'date': date},
                                {'$set': {'code': code, 'date': date, 'pe': pe}}, upsert=True))

                if len(update_requests) > 0:
                    save_result = self.collection.bulk_write(update_requests, ordered=False)
                    print('股票代码: %s, 因子: %s, 插入：%4d, 更新: %4d' %
                          (code, self.name, save_result.upserted_count, save_result.modified_count), flush=True)


if __name__ == '__main__':
    # 执行因子的提取任务
    PEFactor().compute('2016-01-01', '2017-12-31')

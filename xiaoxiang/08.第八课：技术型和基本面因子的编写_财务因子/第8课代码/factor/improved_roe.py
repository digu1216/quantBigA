#  -*- coding: utf-8 -*-

from factor.base_factor import BaseFactor
from util.stock_util import get_all_codes, get_trading_dates
from data.data_module import DataModule
from pymongo import UpdateOne,DESCENDING
from util.database import DB_CONN


class ImprovedRoeFactor(BaseFactor):
    def __init__(self):
        BaseFactor.__init__(self, 'improved_roe')

    def compute(self, begin_date, end_date):
        codes = get_all_codes()

        all_dates = get_trading_dates(begin_date=begin_date, end_date=end_date)

        for code in codes:
            update_requests = []
            for date in all_dates:
                lrb = DB_CONN['CWBB_LRB'].find_one(
                    {'code': code, 'announced_date': {'$lte': date}, 'report_date': {'$regex': '\d{4}-12-31$'}},
                    sort=[('announced_date', DESCENDING)],
                    projection={'parentnetprofit': True}
                )

                # 如果没有利润表信息，则跳过
                if lrb is None:
                    continue

                zcfzb = DB_CONN['CWBB_ZCFZB'].find_one(
                    {'code': code, 'announced_date': {'$lte': date}, 'report_date': {'$regex': '\d{4}-12-31$'}},
                    sort=[('announced_date', DESCENDING)],
                    projection={'sumasset': True}
                )

                if zcfzb is None:
                    continue

                improved_roe = round(lrb['parentnetprofit'] / zcfzb['sumasset'], 2)

                update_requests.append(UpdateOne(
                    {'code': code, 'date': date},
                    {'$set': {'code': code, 'date': date, 'roe': improved_roe}},
                    upsert=True))

            if len(update_requests) > 0:
                save_result = self.collection.bulk_write(update_requests, ordered=False)
                print('股票代码: %s, 因子: %s, 插入：%4d, 更新: %4d' %
                      (code, self.name, save_result.upserted_count, save_result.modified_count), flush=True)


if __name__ == '__main__':
    ImprovedRoeFactor().compute(begin_date='2017-01-01', end_date='2018-06-30')
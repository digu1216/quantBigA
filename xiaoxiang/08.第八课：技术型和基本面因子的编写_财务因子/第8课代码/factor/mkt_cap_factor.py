#  -*- coding: utf-8 -*-

from pymongo import UpdateOne
from .base_factor import BaseFactor
from util.stock_util import get_all_codes, get_trading_dates
from data.data_module import DataModule
from datetime import datetime

"""
实现规模因子的计算和保存
"""


class MktCapFactor(BaseFactor):
    def __init__(self):
        BaseFactor.__init__(self, name='mkt_cap')

    def compute(self, begin_date=None, end_date=None):
        """
        计算指定时间段内所有股票的该因子的值，并保存到数据库中
        :param begin_date:  开始时间
        :param end_date: 结束时间
        """
        dm = DataModule()

        # 如果没有指定日期范围，则默认为计算当前交易日的数据
        if begin_date is None:
            begin_date = datetime.now().strftime('%Y-%m-%d')

        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        dates = get_trading_dates(begin_date, end_date)

        for date in dates:
            print('计算规模因子，日期：%s' % date, flush=True)
            # 查询出股票在某一交易日的总股本
            df_basics = dm.get_stock_basic_at(date)

            if df_basics.index.size == 0:
                continue

            # 将索引改为code
            df_basics.set_index(['code'], 1, inplace=True)

            # 查询出股票在某一个交易日的收盘价
            df_dailies = dm.get_one_day_k_data(autype=None, date=date)

            if df_dailies.index.size == 0:
                continue

            # 将索引设为code
            df_dailies.set_index(['code'], 1, inplace=True)

            update_requests = []
            for code in df_dailies.index:
                try:
                    # 股价
                    close = df_dailies.loc[code]['close']
                    # 总股本
                    total_shares = df_basics.loc[code]['totals']
                    # 总市值 = 股价 * 总股本
                    total_capital = round(close * total_shares, 2)

                    print('%s, %s, mkt_cap: %15.2f' %
                          (code, date, total_capital),
                          flush=True)

                    update_requests.append(
                        UpdateOne(
                            {'code': code, 'date': date},
                            {'$set': {'code': code, 'date': date, self.name: total_capital}}, upsert=True))

                except:
                    print('计算规模因子时发生异常，股票代码：%s，日期：%s'
                          % (code, date),
                          flush=True)

            if len(update_requests) > 0:
                save_result = self.collection.bulk_write(update_requests, ordered=False)
                print('股票代码: %s, 因子: %s, 插入：%4d, 更新: %4d' %
                      (code, self.name, save_result.upserted_count, save_result.modified_count), flush=True)


if __name__ == '__main__':
    # 执行因子的提取任务
    MktCapFactor().compute('2015-01-01', '2018-12-31')

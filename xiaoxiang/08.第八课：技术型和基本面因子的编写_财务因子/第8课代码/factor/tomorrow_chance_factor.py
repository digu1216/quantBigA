#  -*- coding: utf-8 -*-

from factor.base_factor import BaseFactor
from util.stock_util import get_all_codes
from data.data_module import DataModule
from pymongo import UpdateOne


class TomorrowChanceFactor(BaseFactor):
    def __init__(self):
        BaseFactor.__init__(self, 'tomorrow_chance')

    def compute(self, begin_date, end_date):
        codes = get_all_codes()
        dm = DataModule()

        for code in codes:
            df_daily = dm.get_k_data(code, begin_date=begin_date, end_date=end_date)

            if df_daily.index.size == 0:
                continue

            # 当日放量下跌
            df_daily['change'] = df_daily['close'] - df_daily['pre_close']
            df_daily = df_daily[df_daily['change'] < 0]
            df_daily['last_volume'] = df_daily['volume'].shift(1)
            df_daily.dropna(inplace=True)
            df_daily['volume_change'] = round(df_daily['volume']/df_daily['last_volume'], 2)
            df_daily = df_daily[df_daily['volume_change'] > 1.5]

            # 收的阴线实体不大
            df_daily['entity'] = round(abs((df_daily['open'] -df_daily['close'])) * 100/df_daily['close'], 2)
            df_daily = df_daily[df_daily['entity'] < 3]

            # 大部分时间在昨日之上运行
            df_daily.set_index(['date'], 1, inplace=True)

            update_requests = []
            for date in df_daily.index:

                # 大部分时间在昨日之上运行
                pre_close = df_daily.loc[date]['pre_close']
                df_minute = dm.get_k_data(code, period='M1', begin_date=date, end_date=date)
                df_minute = df_minute[df_minute['close'] > pre_close]

                if df_minute.index.size > 150:
                    update_requests.append(UpdateOne({
                        'code': code, 'date': date},
                        {'$set': {'code': code, 'date': date}},
                        upsert=True))

            if len(update_requests) > 0:
                save_result = self.collection.bulk_write(update_requests, ordered=False)
                print('股票代码: %s, 因子: %s, 插入：%4d, 更新: %4d' %
                      (code, self.name, save_result.upserted_count, save_result.modified_count), flush=True)



if __name__ == '__main__':
    TomorrowChanceFactor().compute(begin_date='2017-01-01', end_date='2017-01-31')
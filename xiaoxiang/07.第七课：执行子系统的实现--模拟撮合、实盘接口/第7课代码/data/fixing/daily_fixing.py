#  -*- coding: utf-8 -*-
from pymongo import UpdateOne, ASCENDING
from util.stock_util import get_trading_dates, get_all_codes
from util.database import DB_CONN
from datetime import datetime, timedelta
import tushare as ts
import traceback

"""
日K线数据的修复
"""


class DailyFixing:
    def fill_is_trading_between(self, begin_date=None, end_date=None):
        """
        填充指定时间段内的is_trading字段
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """
        all_dates = get_trading_dates(begin_date, end_date)

        for date in all_dates:
            self.fill_single_date_is_trading(date, 'daily')
            self.fill_single_date_is_trading(date, 'daily_hfq')
            self.fill_single_date_is_trading(date, 'daily_qfq')

    def fill_is_trading(self, date=None):
        """
        为日线数据增加is_trading字段，表示是否交易的状态，True - 交易  False - 停牌
        从Tushare来的数据不包含交易状态，也不包含停牌的日K数据，为了系统中使用的方便，我们需要填充停牌是的K数据。
        一旦填充了停牌的数据，那么数据库中就同时包含了停牌和交易的数据，为了区分这两种数据，就需要增加这个字段。

        在填充该字段时，要考虑到是否最坏的情况，也就是数据库中可能已经包含了停牌和交易的数据，但是却没有is_trading
        字段。这个方法通过交易量是否为0，来判断是否停牌
        """

        if date is None:
            all_dates = get_trading_dates()
        else:
            all_dates = [date]

        for date in all_dates:
            self.fill_single_date_is_trading(date, 'daily')
            self.fill_single_date_is_trading(date, 'daily_hfq')
            self.fill_single_date_is_trading(date, 'daily_qfq')

    @staticmethod
    def fill_single_date_is_trading(date, collection_name):
        """
        填充某一个日行情的数据集的is_trading
        :param date: 日期
        :param collection_name: 集合名称
        """
        print('填充字段， 字段名: is_trading，日期：%s，数据集：%s' %
              (date, collection_name), flush=True)
        daily_cursor = DB_CONN[collection_name].find(
            {'date': date},
            projection={'code': True, 'volume': True, '_id': False},
            batch_size=1000)

        update_requests = []
        for daily in daily_cursor:
            # 默认是交易
            is_trading = True
            # 如果交易量为0，则认为是停牌
            if daily['volume'] == 0:
                is_trading = False

            update_requests.append(
                UpdateOne(
                    {'code': daily['code'], 'date': date},
                    {'$set': {'is_trading': is_trading}}))

        if len(update_requests) > 0:
            update_result = DB_CONN[collection_name].bulk_write(update_requests, ordered=False)
            print('填充字段， 字段名: is_trading，日期：%s，数据集：%s，更新：%4d条' %
                  (date, collection_name, update_result.modified_count), flush=True)

    def fill_daily_k_at_suspension_days(self, begin_date=None, end_date=None):
        """

        :param begin_date:
        :param end_date:
        :return:
        """
        last_trading_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        basic_cursor = DB_CONN['basic'].find(
            {'date': last_trading_date},
            projection={'code': True, 'timeToMarket': True, '_id': False},
            batch_size=5000)

        basics = [basic for basic in basic_cursor]

        print(basics)

        all_dates = get_trading_dates(begin_date, end_date)

        self.fill_daily_k_at_suspension_days_at_date_one_collection(
            basics, all_dates, 'daily')
        self.fill_daily_k_at_suspension_days_at_date_one_collection(
            basics, all_dates, 'daily_hfq')
        self.fill_daily_k_at_suspension_days_at_date_one_collection(
            basics, all_dates, 'daily_qfq')

    @staticmethod
    def fill_daily_k_at_suspension_days_at_date_one_collection(
            basics, all_dates, collection):
        """
        更新单个数据集的单个日期的数据
        :param basics:
        :param all_dates:
        :param collection:
        :return:
        """
        code_last_trading_daily_dict = dict()
        for date in all_dates:
            update_requests = []
            last_daily_code_set = set(code_last_trading_daily_dict.keys())
            for basic in basics:
                code = basic['code']
                # 如果循环日期小于
                if date < basic['timeToMarket']:
                    print('日期：%s, %s 还没上市，上市日期: %s' % (date, code, basic['timeToMarket']), flush=True)
                else:
                    # 找到当日数据
                    daily = DB_CONN[collection].find_one({'code': code, 'date': date})
                    if daily is not None:
                        code_last_trading_daily_dict[code] = daily
                        last_daily_code_set.add(code)
                    else:
                        if code in last_daily_code_set:
                            last_trading_daily = code_last_trading_daily_dict[code]
                            suspension_daily_doc = {
                                'code': code,
                                'date': date,
                                'close': last_trading_daily['close'],
                                'open': last_trading_daily['close'],
                                'high': last_trading_daily['close'],
                                'low': last_trading_daily['close'],
                                'volume': 0,
                                'is_trading': False
                            }
                            update_requests.append(
                                UpdateOne(
                                    {'code': code, 'date': date},
                                    {'$set': suspension_daily_doc},
                                    upsert=True))
            if len(update_requests) > 0:
                update_result = DB_CONN[collection].bulk_write(update_requests, ordered=False)
                print('填充停牌数据，日期：%s，数据集：%s，插入：%4d条，更新：%4d条' %
                      (date, collection, update_result.upserted_count, update_result.modified_count), flush=True)

    @staticmethod
    def fill_au_factor_pre_close(begin_date, end_date):
        """
        为daily数据集填充：
        1. 复权因子au_factor，复权的因子计算方式：au_factor = hfq_close/close
        2. pre_close = close(-1) * au_factor(-1)/au_factor
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """
        all_codes = get_all_codes()

        for code in all_codes:
            hfq_daily_cursor = DB_CONN['daily_hfq'].find(
                {'code': code, 'date': {'$lte': end_date, '$gte': begin_date}, 'index': False},
                sort=[('date', ASCENDING)],
                projection={'date': True,  'close': True})

            date_hfq_close_dict = dict([(x['date'], x['close']) for x in hfq_daily_cursor])

            daily_cursor = DB_CONN['daily'].find(
                {'code': code, 'date': {'$lte': end_date, '$gte': begin_date}, 'index': False},
                sort=[('date', ASCENDING)],
                projection={'date': True,  'close': True}
            )

            last_close = -1
            last_au_factor = -1

            update_requests = []
            for daily in daily_cursor:
                date = daily['date']
                try:
                    close = daily['close']

                    doc = dict()

                    au_factor = round(date_hfq_close_dict[date]/close, 2)
                    doc['au_factor'] = au_factor
                    if last_close != -1 and last_au_factor != -1:
                        pre_close = last_close * last_au_factor / au_factor
                        doc['pre_close'] = round(pre_close, 2)

                    last_au_factor = au_factor
                    last_close = close

                    update_requests.append(
                        UpdateOne(
                            {'code': code, 'date': date, 'index': False},
                            {'$set': doc}))
                except:
                    print('计算复权因子时发生错误，股票代码：%s，日期：%s' % (code, date), flush=True)
                    # 恢复成初始值，防止用错
                    last_close = -1
                    last_au_factor = -1

            if len(update_requests) > 0:
                update_result = DB_CONN['daily'].bulk_write(update_requests, ordered=False)
                print('填充复权因子和前收，股票：%s，更新：%4d条' %
                      (code, update_result.modified_count), flush=True)


    @staticmethod
    def fill_high_limit_low_limit(begin_date, end_date):
        """
        为daily数据集填充涨停价和跌停价
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """
        # 从tushare获取新股数据
        df_new_stocks = ts.new_stocks()
        print(df_new_stocks)
        code_ipo_price_dict = dict()
        code_ipo_date_set = set()
        for index in df_new_stocks.index:
            ipo_price = df_new_stocks.loc[index]['price']
            code = df_new_stocks.loc[index]['code']
            ipo_date = df_new_stocks.loc[index]['ipo_date']
            code_ipo_price_dict[code + '_' + ipo_date] = ipo_price
            code_ipo_date_set.add(code + '_' + ipo_date)

        all_codes = get_all_codes()

        basic_cursor = DB_CONN['basic'].find(
            {'date': {'$gte': begin_date, '$lte': end_date}},
            projection={'code': True, 'date': True, 'name': True, '_id': False},
            batch_size=1000)

        code_date_basic_dict = dict([(x['code'] + '_' + x['date'], x['name']) for x in basic_cursor])
        code_date_key_sets = set(code_date_basic_dict.keys())

        print(code_date_basic_dict)

        for code in all_codes:
            daily_cursor = DB_CONN['daily'].find(
                {'code': code, 'date': {'$lte': end_date, '$gte': begin_date}, 'index': False},
                sort=[('date', ASCENDING)],
                projection={'date': True,  'pre_close': True}
            )

            update_requests = []
            for daily in daily_cursor:
                date = daily['date']
                code_date_key = code + '_' + daily['date']
                try:
                    high_limit = -1
                    low_limit = -1
                    pre_close = daily['pre_close']

                    if code_date_key in code_ipo_date_set:
                        high_limit = round(code_ipo_price_dict[code_date_key] * 1.44, 2)
                        low_limit = round(code_ipo_price_dict[code_date_key] * 0.64, 2)
                    elif code_date_key in code_date_key_sets and code_date_basic_dict[code_date_key][0:2]\
                            in ['ST', '*S'] and pre_close > 0:
                        high_limit = round(pre_close * 1.05, 2)
                        low_limit = round(pre_close * 0.95, 2)
                    elif pre_close > 0:
                        high_limit = round(pre_close * 1.10, 2)
                        low_limit = round(pre_close * 0.9, 2)

                    print('pre_close: %6.2f, high_limit: %6.2f, low_limit: %6.2f' % (pre_close, high_limit, low_limit), flush=True)

                    if high_limit > 0 and low_limit > 0:
                        update_requests.append(
                            UpdateOne(
                                {'code': code, 'date': date, 'index': False},
                                {'$set': {'high_limit': high_limit, 'low_limit': low_limit}}))
                except:
                    print('填充涨跌停时发生错误，股票代码：%s，日期：%s' % (code, date), flush=True)

            if len(update_requests) > 0:
                update_result = DB_CONN['daily'].bulk_write(update_requests, ordered=False)
                print('填充涨跌停，股票：%s，更新：%4d条' %
                      (code, update_result.modified_count), flush=True)


if __name__ == '__main__':
    DailyFixing().fill_au_factor_pre_close('2015-01-01', '2018-12-31')
    # DailyFixing().fill_is_trading_between('2005-01-01', '2018-12-31')
    # DailyFixing().fill_daily_k_at_suspension_days('2005-06-01', '2018-12-30')
    # DailyFixing().fill_high_limit_low_limit('2015-01-01', '2018-12-31')

#  -*- coding: utf-8 -*-

from trading.signal.computer.base_signal_computer import BaseSignalComputer
from util.stock_util import get_all_codes
from data.data_module import DataModule
from pymongo import UpdateOne
import traceback

"""
当日K线上穿和下穿10日均线的判断
"""


class DailyKBreakMA10SignalComputer(BaseSignalComputer):
    def __init__(self):
        BaseSignalComputer.__init__(self, 'daily_k_break_ma10')

    def compute(self, begin_date=None, end_date=None):
        """
        计算指定日期内的信号
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """
        codes = get_all_codes()

        dm = DataModule()

        for code in codes:
            try:
                df_dailies = dm.get_k_data(code, autype='hfq', begin_date=begin_date, end_date=end_date)

                if df_dailies.index.size == 0:
                    continue

                # 计算MA10
                df_dailies['ma'] = df_dailies['close'].rolling(10).mean()
                # 计算当日收盘和MA10的差值
                df_dailies['delta'] = df_dailies['close'] - df_dailies['ma']

                # 删除不再使用的ma和close列
                df_dailies.drop(['ma', 'close'], 1, inplace=True)

                # 判断突破类型
                index_size = df_dailies.index.size
                breaks = [0]
                for index in range(1, index_size):
                    # 如果当前日期为停牌状态，则后面连续11日不参与计算
                    if df_dailies.loc[df_dailies.index[index]]['is_trading'] is False:
                        count = 10
                        while count > 0:
                            index += 1
                            count -= 1
                            breaks.append(0)

                        index += 1

                    last = df_dailies.loc[df_dailies.index[index - 1]]['delta']
                    current = df_dailies.loc[df_dailies.index[index]]['delta']

                    # 向上突破设为1，向下突破设为-1，不是突破设为0
                    break_direction = 1 if last <= 0 < current else -1 if last >= 0 > current else 0
                    breaks.append(break_direction)

                # 设置突破信号
                df_dailies['break'] = breaks

                # 将日期作为索引
                df_dailies.set_index(['date'], 1, inplace=True)
                # 删除不再使用的trade_status和delta数据列
                df_dailies.drop(['is_trading', 'delta'], 1, inplace=True)
                # 只保留突破的日期
                df_dailies = df_dailies[df_dailies['break'] != 0]

                # 将信号保存到数据库
                update_requests = []
                for index in df_dailies.index:
                    doc = {
                        'code': code,
                        'date': index,
                        # 方向，向上突破 up，向下突破 down
                        'direction': 'up' if df_dailies.loc[index]['break'] == 1 else 'down'
                    }
                    update_requests.append(
                        UpdateOne(doc, {'$set': doc}, upsert=True))

                if len(update_requests) > 0:
                    update_result = self.collection.bulk_write(update_requests, ordered=False)
                    print('%s, upserted: %4d, modified: %4d' %
                          (code, update_result.upserted_count, update_result.modified_count),
                          flush=True)
            except:
                traceback.print_exc()


if __name__ == '__main__':
    DailyKBreakMA10SignalComputer().compute('2014-11-01', '2017-12-31')

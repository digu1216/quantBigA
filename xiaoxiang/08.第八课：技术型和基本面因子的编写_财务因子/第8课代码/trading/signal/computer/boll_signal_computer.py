#  -*- coding: utf-8 -*-

import traceback

import numpy as np
from pymongo import UpdateOne

from data.data_module import DataModule
from trading.signal.computer.base_signal_computer import BaseSignalComputer
from util.stock_util import get_all_codes


class BollSignalComputer(BaseSignalComputer):
    def __init__(self):
        BaseSignalComputer.__init__(self, 'boll_signal')

    def compute(self, begin_date, end_date):
        """
        计算指定日期内的信号
        :param begin_date: 开始日期
        :param end_date: 结束日期
        """
        all_codes = get_all_codes()

        dm = DataModule()

        N = 20
        k = 2

        for code in all_codes:
            try:
                df_daily = dm.get_k_data(code, autype='hfq', begin_date=begin_date, end_date=end_date)

                # 计算MB，盘后计算，这里用当日的Close
                df_daily['MID'] = df_daily['close'].rolling(N).mean()
                # 计算STD20
                df_daily['std'] = df_daily['close'].rolling(N).std()
                # 计算UP
                df_daily['UP'] = df_daily['MID'] + k * df_daily['std']
                # 计算down
                df_daily['DOWN'] = df_daily['MID'] - k * df_daily['std']

                # 将日期作为索引
                df_daily.set_index(['date'], inplace=True)

                # 上轨和中轨右移一位
                shifted_up = df_daily['UP'].shift(1)
                shifted_middle = df_daily['MID'].shift(1)

                # 收盘价突破或者跌破中轨的幅度占上轨和中轨宽度的比例
                ref_line = (df_daily['close'] - shifted_middle) / (shifted_up - shifted_middle)

                ref_prev = ref_line.shift(1)

                # 找到时间窗口内的最小值
                min_val = ref_line.rolling(10).min()

                # 找到时间窗口内最低点前的最大值
                max_leading_value = ref_line.rolling(10).apply(lambda vec:
                                                               vec[:np.argmin(vec) + 1].max().astype(float), raw=True)

                # 中轨支撑的作用的范围
                delta = 0.15

                # 判断是否存在中轨支撑反弹的信号，要求：
                # 时间窗口的最低点之前的最大值大于delta，最小值的绝对值小于delta，就有一个穿越阈值分界线的动作；
                # 当前日期在也在阈值之上，表示又从最低点穿越到阈值分界线之上；
                # 而判断前一日在阈值分界线之下，表示穿越是在当前交易日完成
                m_rebound_mask = (abs(min_val) <= delta) & (ref_line > delta) & (ref_prev <= delta) & \
                                 (max_leading_value > delta)

                # 将信号保存到数据库
                update_requests = []
                df_daily['m_rebound_mask'] = m_rebound_mask
                df_daily = df_daily[df_daily['m_rebound_mask']]
                for date in df_daily.index:
                    doc = {'code': code, 'date': date, 'signal': 'mid_rebound'}
                    update_requests.append(UpdateOne(
                        doc, {'$set': doc}, upsert=True
                    ))

                if len(update_requests) > 0:
                    update_result = self.collection.bulk_write(update_requests, ordered=False)
                    print('%s, upserted: %4d, modified: %4d' %
                          (code, update_result.upserted_count, update_result.modified_count),
                          flush=True)
            except:
                traceback.print_exc()

if __name__ == '__main__':
    BollSignalComputer().compute(begin_date='2015-01-01', end_date='2018-06-30')

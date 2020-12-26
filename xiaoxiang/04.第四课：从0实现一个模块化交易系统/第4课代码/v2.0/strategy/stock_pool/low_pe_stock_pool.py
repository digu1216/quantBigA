#  -*- coding: utf-8 -*-

from .base_stock_pool import BaseStockPool
from factor.factor_module import FactorModule
from data.data_module import DataModule

"""
低PE股票池的定义
"""


class LowPeStockPool(BaseStockPool):
    def get_option_stocks(self):
        """
        实现股票池选股逻辑，找到指定日期范围的候选股票
        条件：0 < PE < 30, 按从小到大排序，剔除停牌后，取前100个；再平衡周期：7个交易日
        :return: tuple，再平衡的日期列表，以及一个dict(key: 再平衡日, value: 当期的股票列表)
        """

        factor_module = FactorModule()
        dm = DataModule()

        # 因为上证指数没有停牌不会缺数，所以用它作为交易日历，
        szzz_hq_df = dm.get_k_data('000001', index=True, begin_date=self.begin_date, end_date=self.end_date)
        all_dates = list(szzz_hq_df['date'])

        # 缓存股票和其对应有交易的日期
        code_dates_cache = dict()

        # 调整日和其对应的股票
        rebalance_date_codes_dict = dict()
        rebalance_dates = []

        # 保存上一期的股票池
        last_phase_codes = []
        # 所有的交易日数
        dates_count = len(all_dates)
        # 用再平衡周期作为步长循环
        for index in range(0, dates_count, self.interval):
            # 当前的调整日
            rebalance_date = all_dates[index]

            # 获取本期符合条件的备选股票
            df_pe = factor_module.get_single_date_factors('pe',  rebalance_date)
            df_pe.sort_values('pe', ascending=True, inplace=True)
            # 只保留小于30的数据
            df_pe = df_pe[(0 < df_pe['pe']) & (df_pe['pe'] < 30)]
            df_pe.set_index(['code'], inplace=True)
            this_phase_option_codes = list(df_pe.index)[0:100]
            print(this_phase_option_codes, flush=True)

            # 本期入选的股票代码列表
            this_phase_codes = []

            # 找到在上一期的股票池，但是当前停牌的股票，保留在当期股票池中
            if len(last_phase_codes) > 0:
                for code in last_phase_codes:
                    if code not in list(code_dates_cache.keys()):
                        daily_ks = dm.get_k_data(code, autype=None, begin_date=self.begin_date, end_date=self.end_date)
                        daily_ks.set_index(['date'], inplace=True)
                        code_dates_cache[code] = list(daily_ks.index)
                    if rebalance_date not in code_dates_cache[code]:
                        this_phase_codes.append(code)

            print('上期停牌的股票：', flush=True)
            print(this_phase_codes, flush=True)

            # 剩余的位置用当前备选股票的
            option_size = len(this_phase_option_codes)
            if option_size > (100 - len(this_phase_codes)):
                this_phase_codes += this_phase_option_codes[0:100 - len(this_phase_codes)]
            else:
                this_phase_codes += this_phase_option_codes

            # 当期股票池作为下次循环的上期股票池
            last_phase_codes = this_phase_codes

            # 保存到返回结果中
            rebalance_date_codes_dict[rebalance_date] = this_phase_codes
            rebalance_dates.append(rebalance_date)

            print('当前最终的备选票：%s' % rebalance_date, flush=True)
            print(this_phase_codes, flush=True)

        return rebalance_dates, rebalance_date_codes_dict



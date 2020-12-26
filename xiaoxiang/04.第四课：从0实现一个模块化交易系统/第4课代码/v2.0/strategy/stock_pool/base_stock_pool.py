#  -*- coding: utf-8 -*-

from abc import abstractmethod
from data.data_module import DataModule
from pandas import DataFrame
from matplotlib import pyplot as plt


class BaseStockPool:
    def __init__(self, begin_date, end_date, interval):
        """
        股票池的初始化方法
        :param begin_date: 开始日期
        :param end_date: 结束日期
        :param interval: 再平衡周期
        """
        self.begin_date = begin_date
        self.end_date = end_date
        self.interval = interval

    @abstractmethod
    def get_option_stocks(self):
        """
        获取股票池的出票列表
        :return:
        """
        pass

    def statistic_profit(self):
        """
        统计股票池的收益
        """
        # 设定评测周期
        rebalance_dates, codes_dict = self.get_option_stocks()

        dm = DataModule()

        # 用DataFrame保存收益
        df_profit = DataFrame(columns=['profit', 'hs300'])

        df_profit.loc[rebalance_dates[0]] = {'profit': 0, 'hs300': 0}

        # 获取沪深300在统计周期内的第一天的值
        hs300_k = dm.get_k_data('000300', index=True, begin_date=rebalance_dates[0], end_date=rebalance_dates[0])
        hs300_begin_value = hs300_k.loc[hs300_k.index[0]]['close']

        # 通过净值计算累计收益
        net_value = 1
        for _index in range(1, len(rebalance_dates) - 1):
            last_rebalance_date = rebalance_dates[_index - 1]
            current_rebalance_date = rebalance_dates[_index]
            # 获取上一期的股票池
            codes = codes_dict[last_rebalance_date]

            # 统计当前的收益
            profit_sum = 0
            # 参与统计收益的股票个数
            profit_code_count = 0
            for code in codes:
                daily_ks = dm.get_k_data(code, autype='hfq',
                                         begin_date=last_rebalance_date, end_date=current_rebalance_date)

                index_size = daily_ks.index.size
                # 如果没有数据，则跳过，长期停牌
                if index_size == 0:
                    continue
                # 买入价
                in_price = daily_ks.loc[daily_ks.index[0]]['close']
                # 卖出价
                out_price = daily_ks.loc[daily_ks.index[index_size - 1]]['close']
                # 股票池内所有股票的收益
                profit_sum += (out_price - in_price)/in_price
                profit_code_count += 1

            profit = round(profit_sum/profit_code_count, 4)

            hs300_k_current = dm.get_k_data('000300', index=True,
                                            begin_date=current_rebalance_date, end_date=current_rebalance_date)
            hs300_close = hs300_k_current.loc[hs300_k_current.index[0]]['close']

            # 计算净值和累积收益
            net_value = net_value * (1 + profit)
            df_profit.loc[current_rebalance_date] = {
            'profit': round((net_value - 1) * 100, 4),
            'hs300': round((hs300_close - hs300_begin_value) * 100/hs300_begin_value, 4)}

            print(df_profit)

        # 绘制曲线
        df_profit.plot(title='Stock Pool Profit Statistic', kind='line')
        # 显示图像
        plt.show()


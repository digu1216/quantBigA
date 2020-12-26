#  -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import pandas as pd

from data.data_module import DataModule
from factor.factor_module import FactorModule
from util.database import DB_CONN
from util.stock_util import get_trading_dates


class ZeroInvestmentPortfolioAnalysis:
    def __init__(self, factor, begin_date, end_date, interval, position=10, ascending=True):
        """
        零投资组合的初始化方法

        :param factor:  因子名字
        :param begin_date: 分析的开始日期
        :param end_date: 分析的结束日期
        :param interval: 调整周期，交易日数
        :param position: 档位数，默认划分为10档
        :param ascending: 是否按照因子值正序排列，默认为正序
        """
        # 单期收益的DataFrame
        self.profit_df = pd.DataFrame(columns={
            'top', 'bottom', 'portfolio'})
        # 累计收益的DataFrame，沪深300作为基准
        self.cumulative_profit = pd.DataFrame(columns={
            'top', 'bottom', 'portfolio', 'hs300'})
        # 单期股次数的DataFrame
        self.count_df = pd.DataFrame(columns={
            'top', 'bottom'})

        # 净值
        self.last_top_net_value = 1
        self.last_bottom_net_value = 1
        self.last_portfolio_net_value = 1
        # 沪深300首日的日
        self.hs300_first_value = -1

        # 因子名字
        self.factor = factor
        # 因子的数据集
        self.factor_collection = DB_CONN[factor]

        # 分析的日期范围
        self.begin_date = begin_date
        self.end_date = end_date
        # 调整周期
        self.interval = interval
        # 排序方式
        self.ascending = ascending
        # 档位数
        self.position = position

    """
    市值的零投资组合分析
    """

    def analyze(self):
        # 初始化对数据管理子系统接口的调用
        dm = DataModule()
        # 初始化对因子管理子系统接口的调用
        fm = FactorModule()

        # 获取分析周期内的
        all_dates = get_trading_dates(self.begin_date, self.end_date)

        # 首档和末档，股票代码和后复权价格的Dictionary
        top_dailies = dict()
        bottom_dailies = dict()
        # 暂存上一个调整
        last_adjust_date = None

        # 设置沪深300的首日值
        hs300_k = dm.get_k_data('000300', index=True, begin_date=all_dates[0], end_date=all_dates[0])
        self.hs300_first_value = hs300_k.loc[0]['close']

        # 计算每日收益
        for index in range(0, len(all_dates), self.interval):
            adjust_date = all_dates[index]

            # 获取因子值，按照指定的顺序排序
            df_factor = fm.get_single_date_factors(self.factor, adjust_date)
            if df_factor.index.size == 0:
                continue
            df_factor.sort_values(self.factor, ascending=self.ascending, inplace=True)
            # 将股票代码设为index
            df_factor.set_index(['code'], inplace=True)

            # 获取当日所有股票的行情
            df_dailies = dm.get_one_day_k_data(autype='hfq', date=adjust_date)
            # 将code设为index
            df_dailies.set_index(['code'], inplace=True)

            # 计算收益
            self.compute_profit(last_adjust_date, df_dailies, top_dailies, bottom_dailies, adjust_date)

            # 删除停牌股票
            df_dailies = df_dailies[df_dailies['is_trading']]
            # 计算每当包含的股票数
            total_size = df_dailies.index.size
            single_position_count = int(total_size / self.position)

            # 调整首档组合
            self.adjust_top_position(top_dailies, df_factor, df_dailies, single_position_count)

            # 调整末档组合
            self.adjust_bottom_position(bottom_dailies, df_factor, df_dailies, single_position_count)

            # 保存上一个调整日
            last_adjust_date = adjust_date

        # 生成零投资组合的组合收益
        self.profit_df['portfolio'] = self.profit_df['top'] - self.profit_df['bottom']

        self.draw()

    def adjust_top_position(self, top_dailies, df_factor, df_dailies, single_position_count):
        """
        调整首档组合
        1. 移除上期调入且当前非停牌股票
        2. 加入当期应跳入且当前非停牌股票
        3. 加入时，应按照排序从头逐个加入，直到满足数量要求
        :param top_dailies:
        :param df_factor: 排序后的因子值
        :param df_dailies:
        :param single_position_count:
        :return:
        """
        # 移除首档非停牌股票
        self.remove_stocks(top_dailies, df_dailies)

        # 首档股票，保留后复权的价格
        top_size = len(top_dailies.keys())
        all_codes = list(df_factor.index)
        # 所有处于交易状态的股票
        all_trading_codes = set(df_dailies.index)
        for code in all_codes:
            # 可能已经存在股票，所以需要先判断是否已经满足了数量要求
            if top_size == single_position_count:
                break

            # 只有是交易状态的股票才被纳入组合
            if code in all_trading_codes:
                top_dailies[code] = df_dailies.loc[code]['close']
                top_size += 1

    def remove_stocks(self, position_dailies, df_dailies):
        """
        移除当期中非停牌的股票
        :param position_dailies:
        :param df_dailies:
        :return:
        """
        # 首期时，还不存在股票
        if len(position_dailies.keys()) == 0:
            return

        # 因为df_dailies只包含了非停牌的股票，所以只要在这个索引里就会被移除
        for code in df_dailies.index:
            if code in position_dailies:
                del position_dailies[code]

    def adjust_bottom_position(self, bottom_dailies, df_factor, df_dailies, single_position_count):
        """
        调整末档组合
        1. 移除上期调入且当前非停牌股票
        2. 加入当期应跳入且当前非停牌股票
        3. 加入时，应按照排序从末尾逐个加入，直到满足数量要求

        :param bottom_dailies:
        :param df_dailies: 日K数据
        :param df_factor: 排序后的因子值
        :param single_position_count: 每个档位的股票数量
        :return:
        """
        # 移除首档非停牌股票
        self.remove_stocks(bottom_dailies, df_dailies)
        # 末档股票，保留后复权的价格
        bottom_size = len(bottom_dailies.keys())
        # 将所有股票的顺序反转
        all_codes = list(df_factor.index)
        all_codes.reverse()

        # 所有处于交易状态的股票
        all_trading_codes = set(df_dailies.index)
        for code in all_codes:
            # 可能已经存在股票，所以需要先判断是否已经满足了数量要求
            if bottom_size == single_position_count:
                break

            # 只有是交易状态的股票才被纳入组合
            if code in all_trading_codes:
                bottom_dailies[code] = df_dailies.loc[code]['close']
                bottom_size += 1

    def compute_profit(self, last_adjust_date, df_dailies, top_dailies, bottom_dailies, adjust_date):
        """
        计算收益
        :param last_adjust_date: 上一个调整日
        :param df_dailies:
        :param top_dailies:
        :param bottom_dailies:
        :param adjust_date: 当前调整日
        :return:
        """
        # 只有存在上一个调整日，才计算上期的收益
        if last_adjust_date is not None:
            # 计算首档收益
            top_profit = self.compute_average_profit(df_dailies, top_dailies)

            # 计算末档收益
            bottom_profit = self.compute_average_profit(df_dailies, bottom_dailies)

            # 计算组合收益
            portfolio_profit = top_profit[0] - bottom_profit[0]

            # 添加结果的DataFrame中
            self.profit_df.loc[last_adjust_date] = {
                'top': top_profit[0],
                'bottom': bottom_profit[0],
                'portfolio': portfolio_profit
            }

            # 计算累积收益（复利方式）
            # 首档
            top_cumulative_profit = round((self.last_top_net_value * (1 + top_profit[0] / 100) - 1) * 100, 2)
            self.last_top_net_value *= (1 + top_profit[0] / 100)
            # 末档
            bottom_cumulative_profit = round((self.last_bottom_net_value * (1 + bottom_profit[0] / 100) - 1) * 100, 2)
            self.last_bottom_net_value *= (1 + bottom_profit[0] / 100)
            # 组合
            portfolio_cumulative_profit = round(
                (self.last_portfolio_net_value * (1 + portfolio_profit / 100) - 1) * 100, 2)
            self.last_portfolio_net_value *= (1 + portfolio_profit / 100)

            # 计算沪深300的累计收益
            dm = DataModule()
            hs300_k = dm.get_k_data('000300', index=True, begin_date=adjust_date, end_date=adjust_date)
            hs300_k.set_index(['date'], 1, inplace=True)
            hs300_profit = (hs300_k.loc[adjust_date]['close'] -
                            self.hs300_first_value) / self.hs300_first_value

            self.cumulative_profit.loc[last_adjust_date] = {
                'top': top_cumulative_profit,
                'bottom': bottom_cumulative_profit,
                'portfolio': portfolio_cumulative_profit,
                'hs300': hs300_profit
            }

            self.count_df.loc[last_adjust_date] = {
                'top': top_profit[1],
                'bottom': bottom_profit[1]
            }

    def draw(self):
        """
        绘制分析图
        """
        print(self.profit_df)
        # 单期收益的曲线
        self.profit_df.plot(title='Single Profit', kind='line')
        # 单期收益的分布，直方图
        self.profit_df.hist(color='r', grid=False, bins=20, rwidth=0.6)
        # 单期入选股票数
        self.count_df.plot(title='Stock Count', kind='bar')
        # 累积收益曲线
        print(self.cumulative_profit)
        self.cumulative_profit.plot(title='Cumulative Profit', kind='line')
        # 显示图像
        plt.show()

    def compute_average_profit(self, df_dailies, position_code_close_dict):
        """
        计算某一档的平均收益
        :param df_dailies: 日行情的DataFrame
        :param position_code_close_dict:
        :return: 收益
        """
        # 提取股票列表
        position_codes = list(position_code_close_dict.keys())

        # 只有存在股票时，才进行计算
        if len(position_codes) > 0:
            # 所有股票代码
            codes = set(df_dailies.index)

            # 所有股票的累计收益
            profit_sum = 0
            # 实际参与统计的股票数
            count = 0
            # 计算所有股票的收益
            for code in position_codes:
                count += 1
                buy_close = position_code_close_dict[code]

                # 计算所有股票的累计收益
                if code in codes:
                    profit_sum += (df_dailies.loc[code]['close'] - buy_close) / buy_close

            # 计算单期平均收益
            return round(profit_sum * 100 / count, 2), count

        # 没有数据时，返回None
        return None


if __name__ == '__main__':
    ZeroInvestmentPortfolioAnalysis('mkt_cap', '2017-01-01', '2017-12-31', 20).analyze()

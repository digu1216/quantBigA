#  -*- coding: utf-8 -*-

"""
统计股票池的收益规律
"""

from strategy.stock_pool.low_pe_stock_pool import LowPeStockPool

# 统计低PE股票池的收益，三个参数分别是开始日期、结束日期和再平衡周期
stock_pool = LowPeStockPool('2015-01-01', '2015-12-31', 7)
stock_pool.statistic_profit()

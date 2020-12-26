#  -*- coding: utf-8 -*-

from strategy.stock_pool.low_pe_stock_pool import LowPeStockPool


class StockPoolFactory:
    @staticmethod
    def get_stock_pool(name, begin_date, end_date, interval):
        if name == 'low_pe_stock_pool':
            return LowPeStockPool(begin_date, end_date, interval)

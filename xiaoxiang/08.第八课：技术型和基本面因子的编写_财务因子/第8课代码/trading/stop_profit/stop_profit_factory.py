#  -*- coding: utf-8 -*-


from .fix_stop_profit import FixStopProfit
from .tracking_stop_profit import TrackingStopProfit


class StopProfitFactory:
    @staticmethod
    def get_stop_profit_policy(account, strategy_option):
        name = strategy_option.properties['stop_profit']
        if 'fixed' == name:
            max_profit = float(strategy_option.properties['max_profit'])
            return FixStopProfit(account, max_profit)
        if 'tracking' == name:
            max_profit = float(strategy_option.properties['max_profit'])
            profit_drawdown = float(strategy_option.properties['profit_drawdown'])
            return TrackingStopProfit(account, max_profit, profit_drawdown)


#  -*- coding: utf-8 -*-

from strategy.stock_pool.stock_pool_factory import StockPoolFactory
from datetime import datetime
from trading.signal.signal_factory import SignalFactory
from trading.stop_loss.stop_loss_factory import StopLossFactory
from trading.stop_profit.stop_profit_factory import StopProfitFactory
from trading.position.position_policy_factory import PositionPolicyFactory

"""
保存策略的定义
"""


class StrategyOption:
    def __init__(self, properties):
        self.properties = properties

    def capital(self):
        """
        获取策略的总资金配置
        :return: 如果没有设置，默认为1千万
        """
        if 'capital' in self.properties:
            return int(self.properties['capital'])
        else:
            return 1E7

    def stock_pool(self):
        if 'stock_pool' in self.properties:
            interval = int(self.properties['interval'])
            return StockPoolFactory.get_stock_pool(
                self.properties['stock_pool'],
                self.begin_date(),
                self.end_date(),
                interval)
        return None

    def get_stop_loss(self, account):
        """
        获取止损的方法
        :param account:
        :return:
        """
        if 'stop_loss' in self.properties:
            return StopLossFactory.get_stop_loss_policy(account, self)

        return None

    def get_stop_profit(self, account):
        """
        获取止盈的方法
        :param account:
        :return:
        """
        if 'stop_profit' in self.properties:
            return StopProfitFactory.get_stop_profit_policy(account, self)

        return None

    def get_add_position(self, account):
        """
        获取加仓的方法
        :param account:
        :return:
        """
        if 'add_position' in self.properties:
            return PositionPolicyFactory.get_add_position_policy(account, self)

        return None

    def begin_date(self):
        """
        获取策略回测的开始日期
        :return: 默认为2015-01-01
        """
        if 'begin_date' in self.properties:
            return self.properties['begin_date']
        else:
            return '2015-01-01'

    def end_date(self):
        """
        获取策略回测的结束日期
        :return: 默认为当前日期
        """
        if 'end_date' in self.properties:
            return self.properties['end_date']
        else:
            return datetime.now().strftime('%Y-%m-%d')

    def single_position(self):
        return int(self.properties['single_position'])

    def sell_signal(self, account):
        if 'sell_signal' in self.properties:
            return SignalFactory.get_signal(self.properties['sell_signal'], account)

    def buy_signal(self, account):
        if 'buy_signal' in self.properties:
            return SignalFactory.get_signal(self.properties['buy_signal'], account)


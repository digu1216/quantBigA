#  -*- coding: utf-8 -*-

from .atr_position import ATRPosition


class PositionPolicyFactory:
    @staticmethod
    def get_add_position_policy(account, strategy_option):
        name = strategy_option.properties['add_position']
        if 'atr' == name:
            return ATRPosition(account, strategy_option)


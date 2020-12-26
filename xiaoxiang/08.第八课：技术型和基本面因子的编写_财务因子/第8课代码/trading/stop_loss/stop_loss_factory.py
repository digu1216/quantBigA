#  -*- coding: utf-8 -*-

from .fix_stop_loss import FixStopLoss
from .tracking_stop_loss import TrackingStopLoss


class StopLossFactory:
    @staticmethod
    def get_stop_loss_policy(account, strategy_option):
        name = strategy_option.properties['stop_loss']
        if 'fixed' == name:
            max_loss = float(strategy_option.properties['max_loss'])
            return FixStopLoss(account, max_loss)
        elif 'tracking' == name:
            max_loss = float(strategy_option.properties['max_loss'])
            return TrackingStopLoss(account, max_loss)


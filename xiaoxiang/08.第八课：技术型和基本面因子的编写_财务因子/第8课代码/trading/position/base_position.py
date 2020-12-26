#  -*- coding: utf-8 -*-

from abc import abstractmethod
from util.logger import QuantLogger


class BasePosition:
    def __init__(self, account, strategy_option):
        self.account = account
        self.strategy_option = strategy_option
        # 指定日志
        self.logger = QuantLogger('position')

    @abstractmethod
    def update_holding(self, code, date, update_holding):
        pass

    @abstractmethod
    def compute_position(self, code, date):
        pass

    @abstractmethod
    def get_add_signal(self, code, date):
        pass

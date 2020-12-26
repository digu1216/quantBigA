#  -*- coding: utf-8 -*-

from trading.backtest import Backtest
from strategy.strategy_option import StrategyOption
import sys, traceback,os


class Strategy:
    def __init__(self, name):
        # 策略的属性定义
        properties = dict()

        strategy_file = os.path.join(sys.path[2], 'strategy', 'strategies', name)

        if os.path.exists(strategy_file) is False:
            print("策略名文件名称有误：%s，请确认后重新输入。" % name, flush=True)
            return

        with open(strategy_file, encoding='UTF-8') as contents:
            for line in contents:
                if line.startswith("#") is False:
                    if line.index('=') > 0:
                        line = line.replace('\n', '')
                        configs = line.split('=')
                        properties[configs[0]] = configs[1]

        self.strategy_option = StrategyOption(properties)

    def backtest(self):
        backtest = Backtest(self.strategy_option)
        backtest.start()


if __name__ == '__main__':
    if len(sys.argv) == 3:
        if sys.argv[1] == '--name':
            strategy = Strategy(sys.argv[2])
            strategy.backtest()
    else:
        print("启动回测的方式：python strategy_module.py --name strategy_name")
        print("例如：python strategy_module.py --name low_pe_strategy")

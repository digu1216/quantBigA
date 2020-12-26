#  -*- coding: utf-8 -*-


class TradingModule:
    def __init__(self):
        pass

    def stop_loss(self):
        print("子系统：交易决策，操作：判断止损，状态：开始，股票：%s, 日期：%s" %
              (code, date), flush=True)
        print("子系统：交易决策，操作：判断止损，状态：结束，股票：%s, 日期：%s，结果： %s" %
              (code, date), flush=True)
        return False

    def stop_proift(self):
        print("子系统：交易决策，操作：判断止盈，状态：开始，股票：%s, 日期：%s" %
              (code, date), flush=True)
        print("子系统：交易决策，操作：判断止盈，状态：结束，股票：%s, 日期：%s，结果： %s" %
              (code, date), flush=True)
        return False

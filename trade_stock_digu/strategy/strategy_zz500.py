import numpy as np
import pandas as pd
from collections import deque
import sys
sys.path.append('../')
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from trade_stock_digu.data_service import DataServiceTushare
from trade_stock_digu.convert_utils import string_to_datetime, time_to_str
from tools.logger import Logger

LOG = Logger().getlog()
class ZZ500Strategy(CtaTemplate):
    # 参考文档： https://www.doc88.com/p-5748746646083.html
    # TODO： 对参数调优之后再做指标共振平滑处理看效果如何
    author = "digu"

    score_bull = 4   # 各指标得分和，超过阈值之后才发出买入信号
    score_bear = 3   # 各指标得分和，低于阈值之后才发出卖出信号

    pct_cnt_low = 30  # 上涨股票占比
    pct_cnt_high = 90

    pct_ma60_low = 40
    pct_ma60_high = 90

    cnt_8ma_low = 3
    cnt_8ma_high = 5
    ds_tushare = DataServiceTushare()

    c1 = 0
    c2 = 0
    c3 = 0
    c4 = 0
    c5 = 0
    c6 = 0
    parameters = ["score_bull", "score_bear", "pct_cnt_low", "pct_cnt_high", "pct_ma60_low", 
                    "pct_ma60_high", "cnt_8ma_low", "cnt_8ma_high"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(size=500)
        self.lst_turnover_rate_f = list()   # 保存zz500的历史流通盘换手率
        self.deque_quantile_20 = deque()
        self.pct_cnt_score_pre = 0   # 保存前一天的上涨股占比得分
        self.cnt_8ma_score_pre = 0   # 保存前一天的8ma得分
        self.ma_bull_score_pre = 0   # 保存前一天的均线多空得分
        self.rsi_score_pre = 0   # 保存前一天的rsi得分
        self.turnover_rate_f_score_pre = 0   # 保存前一天的流通盘换手率得分


    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        # TODO 获取zz500的相关信息 
        info_zz500 = self.ds_tushare.get_zz500('000905_SH', time_to_str(bar.datetime, '%Y%m%d'))
        if info_zz500 is None:
            LOG.info('zz500 None date: %s' %time_to_str(bar.datetime, '%Y%m%d'))
            return
        self.lst_turnover_rate_f.append(info_zz500['turnover_rate_f'])
        arr_turnover_rate_f = np.array(self.lst_turnover_rate_f)
        arr_turnover_rate_f.sort()
        idx_turnover_rate_f = np.argwhere(arr_turnover_rate_f > info_zz500['turnover_rate_f'] - 0.0000001)[0]
        quantile_turnover_rate_f = idx_turnover_rate_f / arr_turnover_rate_f.size
        if len(self.deque_quantile_20) < 20:
            self.deque_quantile_20.append(quantile_turnover_rate_f)
        else:
            self.deque_quantile_20.popleft()
            self.deque_quantile_20.append(quantile_turnover_rate_f)

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return        
        # 判断当日上涨股票数目比例
        pct_cnt = (info_zz500['stk_cnt_up'] * 100.0) / (info_zz500['stk_cnt_up']+info_zz500['stk_cnt_down'])
        if pct_cnt > self.pct_cnt_high:
            pct_cnt_score = 1
        elif pct_cnt < self.pct_cnt_low:
            pct_cnt_score = 0
        else:
            pct_cnt_score = self.pct_cnt_score_pre
        self.pct_cnt_score_pre = pct_cnt_score

        # 判断大于ma60强势股票数目比例
        pct_ma60 = (info_zz500['stk_cnt_ma60_up'] * 100.0) / (info_zz500['stk_cnt_ma60_up']+info_zz500['stk_cnt_ma60_down'])
        if pct_ma60 < self.pct_ma60_low or pct_ma60 > self.pct_ma60_high:
            pct_ma60_score = 0
        else:
            pct_ma60_score = 1
        
        # 判断8ma指标
        cnt_ma = 0
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_5'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_10'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_20'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_30'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_60'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_120'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_250'] else cnt_ma
        cnt_ma = cnt_ma + 1 if info_zz500['close'] > info_zz500['ma_500'] else cnt_ma
        if cnt_ma > self.cnt_8ma_high:
            cnt_8ma_score = 1
        elif cnt_ma < self.cnt_8ma_low:
            cnt_8ma_score = 0
        else:
            cnt_8ma_score = self.cnt_8ma_score_pre
        self.cnt_8ma_score_pre = cnt_8ma_score

        # 判断均线多空排列指标
        if info_zz500['ma_30'] > info_zz500['ma_20'] and info_zz500['ma_20'] > info_zz500['ma_10']:
            ma_bull_score = 0
        elif info_zz500['ma_10'] > info_zz500['ma_20'] and info_zz500['ma_20'] > info_zz500['ma_30']:
            ma_bull_score = 1
        else:
            ma_bull_score = self.ma_bull_score_pre
        self.ma_bull_score_pre = ma_bull_score

        # 判断平滑相对强弱指标MA(RSI(20), 20)
        arr_rsi_20 = self.am.rsi(20, array=True)[-20:]
        rsi_20_mean = np.mean(arr_rsi_20)
        rsi_20_std = np.std(arr_rsi_20)
        if arr_rsi_20[-1] > rsi_20_mean + rsi_20_std:
            rsi_score = 1
        elif arr_rsi_20[-1] < rsi_20_mean - rsi_20_std:
            rsi_score = 0
        else:
            rsi_score = self.rsi_score_pre
        self.rsi_score_pre = rsi_score

        # 判断A股换手率指标(历史分位数q)得分        
        quantile_20_mean = np.mean(np.array(self.deque_quantile_20))
        quantile_20_std = np.std(np.array(self.deque_quantile_20))
        if quantile_turnover_rate_f > quantile_20_mean + quantile_20_std:
            turnover_rate_f_score = 1
        elif quantile_turnover_rate_f < quantile_20_mean - quantile_20_std:
            turnover_rate_f_score = 0
        else:
            turnover_rate_f_score = self.turnover_rate_f_score_pre
        self.turnover_rate_f_score_pre = turnover_rate_f_score

        ZZ500Strategy.c1 += pct_cnt_score
        ZZ500Strategy.c2 += pct_ma60_score
        ZZ500Strategy.c3 += cnt_8ma_score
        ZZ500Strategy.c4 += ma_bull_score
        ZZ500Strategy.c5 += rsi_score
        ZZ500Strategy.c6 += turnover_rate_f_score
        score = pct_cnt_score + pct_ma60_score + cnt_8ma_score + ma_bull_score + rsi_score + turnover_rate_f_score        

        flag_buy = True if score > self.score_bull else False
        flag_sell = True if score < self.score_bear else False
        if flag_buy:
            if self.pos == 0:
                self.cancel_all()
                self.buy(bar.close_price, 1)
                # self.buy(bar.close_price, 1, True)
        elif flag_sell:
            if self.pos > 0:
                self.cancel_all()
                self.sell(bar.close_price, 1)
                # self.sell(bar.close_price, 1, True)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

import numpy as np
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
from data_service import DataServiceTushare
from convert_utils import string_to_datetime, time_to_str

class StrategyVol(StrategyBase):
    """
    股票池定义：
    1、流通市值小于500亿
    2、选股当天自由流通股换手率>1%  turnover_rate_f_min
    3、股价未暴涨，一年最高价/最低价 < 4 pct_chg_max_year
    4、多头排列 ma5>ma10>ma30>ma60>ma120,close>ma5,close<ma5*pct_close_to_ma5
    5、上市时间超过n_years=2年
    6、当日非st
    按照量能在股票池中选股：
    1、统计股票池最近N=5日的每日换手率的前200排名得到集合A1-A5 n_days n_rank_turnover
    2、统计股票池最近N=5日的每日量比的前200排名得到集合B1-B5  n_days n_rank_vol
    3、取A1-A5，B1-B5出现次数前n_rank_times = 6的股票组成股票池
    策略调仓：
    1、每周调仓一次，卖出所有股票，平均买入新的买入股票
    """
    circ_mv_max = 5000000
    turnover_rate_f_min = 0.01
    pct_chg_max_year = 4.0
    n_days = 5
    pct_close_to_ma5 = 0.06
    n_rank_turnover = 200
    n_rank_vol= 200
    n_years = 2
    n_rank_times = 6
    # def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
    #     """"""
    #     super().__init__()

    def __init__(self):
        """"""
        super().__init__()

    def pick_stock(self, date):    
        self.set_date(date)        
        ds_tushare = DataServiceTushare()
        lst_code_pool = list()
        lst_code_picked = list()
        for ts_code in ds_tushare.get_stock_list():
            stock_basic = ds_tushare.get_stock_basic_info(ts_code)
            if stock_basic is None:
                self.logger.info('None stock basic info %s' %ts_code)
                continue
            dt_date = string_to_datetime(self.stock_picked_date)
            d = timedelta(days=-365 * self.n_years)
            if stock_basic['list_date'] > time_to_str(dt_date+d, '%Y%m%d') or 'ST' in stock_basic['name']:
                # 排除上市时间小于2年和st股票
                continue
            dic_stock_price = ds_tushare.get_stock_price_info(ts_code, self.stock_picked_date)       
            if dic_stock_price is None:
                # 排除选股日停牌的股票
                continue   
            try:
                if dic_stock_price['circ_mv']  > self.circ_mv_max or dic_stock_price['turnover_rate_f'] < self.turnover_rate_f_min \
                    or dic_stock_price['high_250'] / dic_stock_price['low_250'] > self.pct_chg_max_year \
                        or dic_stock_price['ma_120'] > dic_stock_price['ma_60'] or dic_stock_price['ma_60'] > dic_stock_price['ma_30'] \
                            or dic_stock_price['ma_30'] > dic_stock_price['ma_10'] or dic_stock_price['ma_10'] > dic_stock_price['ma_5'] \
                                or dic_stock_price['close'] > dic_stock_price['ma_5'] * (1 + self.pct_close_to_ma5) \
                                    or dic_stock_price['close'] < dic_stock_price['ma_5'] * (1 - self.pct_close_to_ma5):
                    continue
            except:
                self.logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                self.logger.info(dic_stock_price)
            lst_code_pool.append(dic_stock_price['ts_code'])
        # self.logger.info(lst_code_pool)
        lst_n_days = ds_tushare.get_pre_n_trade_date(self.stock_picked_date, self.n_days)   # 日期从大到小排列
        arr_code = list()
        arr_a1 = list() # 最近一天的数据
        arr_a2 = list()
        arr_a3 = list()
        arr_a4 = list()
        arr_a5 = list()
        arr_b1 = list()
        arr_b2 = list()
        arr_b3 = list()
        arr_b4 = list()
        arr_b5 = list()
        for item_code in lst_code_pool:
            lst_stock_price = ds_tushare.get_stock_price_lst(item_code, lst_n_days[-1], lst_n_days[0])   
            if len(lst_stock_price) < self.n_days:
                # 排除最近5个交易日有停牌情况的股票
                continue
            arr_code.append(item_code)
            idx = 0
            for item_price in lst_stock_price:
                idx += 1
                if idx == 1:
                    # 第一天数据 n-1
                    arr_a1.append(item_price['turnover_rate_f'])
                    arr_b1.append(item_price['volume_ratio'])
                elif idx == 2:
                    # 第二天数据 n-2
                    arr_a2.append(item_price['turnover_rate_f'])
                    arr_b2.append(item_price['volume_ratio'])
                elif idx == 3:
                    arr_a3.append(item_price['turnover_rate_f'])
                    arr_b3.append(item_price['volume_ratio'])
                elif idx == 4:
                    arr_a4.append(item_price['turnover_rate_f'])
                    arr_b4.append(item_price['volume_ratio'])
                elif idx == 5:
                    arr_a5.append(item_price['turnover_rate_f'])
                    arr_b5.append(item_price['volume_ratio'])
                else:
                    self.logger.info('lst_stock_price data error!!!')
                    self.logger.info(lst_stock_price)
                    break
        arr_a1_idx = np.array(arr_a1).argsort()[-(self.n_rank_turnover+1): -1]
        arr_a2_idx = np.array(arr_a2).argsort()[-(self.n_rank_turnover+1): -1]
        arr_a3_idx = np.array(arr_a3).argsort()[-(self.n_rank_turnover+1): -1]
        arr_a4_idx = np.array(arr_a4).argsort()[-(self.n_rank_turnover+1): -1]
        arr_a5_idx = np.array(arr_a5).argsort()[-(self.n_rank_turnover+1): -1]
        arr_b1_idx = np.array(arr_b1).argsort()[-(self.n_rank_vol+1): -1]
        arr_b2_idx = np.array(arr_b2).argsort()[-(self.n_rank_vol+1): -1]
        arr_b3_idx = np.array(arr_b3).argsort()[-(self.n_rank_vol+1): -1]
        arr_b4_idx = np.array(arr_b4).argsort()[-(self.n_rank_vol+1): -1]
        arr_b5_idx = np.array(arr_b5).argsort()[-(self.n_rank_vol+1): -1]
        arr_combine = np.hstack((arr_a1_idx, arr_a2_idx, arr_a3_idx, arr_a4_idx, arr_a5_idx, \
            arr_b1_idx, arr_b2_idx, arr_b3_idx, arr_b4_idx ,arr_b5_idx))
        res_count = Counter(arr_combine)
        res_stock_idx = res_count.most_common(self.n_rank_times)
        if len(res_stock_idx) != 0:
            for item in res_stock_idx:
                lst_code_picked.append(arr_code[item[0]])
        return lst_code_picked


if __name__ == "__main__":
    ds_tushare = DataServiceTushare()
    strategy = StrategyVol()
    print(strategy.pick_stock('20200807'))
    # lst_trade_date = ds_tushare.get_trade_cal('20200101', '20200701')
    # cnt_loop = 0
    # for item_date in lst_trade_date:
    #     cnt_loop += 1
    #     if cnt_loop % 5 == 0:
    #         # 换股日
    #         strategy.pick_stock(item_date)

"""
to do:
计算股票池的每日涨跌幅（叠加大盘指数绘图）
"""                    
import numpy as np
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
import sys
sys.path.append('../')
from trade_stock_digu.data_service import DataServiceTushare
from trade_stock_digu.convert_utils import string_to_datetime, time_to_str

class StrategyTopList(StrategyBase):
    """
    龙虎榜选股策略：
    买入：
    1、某日净买入占成交百分比 pct_buy > 15%
    2、股价回调 pct_retracement > 10%
    卖出：
    1、前高不涨停？

    待补充：
    """
    pct_buy = 15    # 某日净买入占成交百分比 db:net_rate    
    n_years = 2     # 上市时间超过n_years年     
    # max_times_in_year = 4   #股票年内最大涨幅 high_250/low_250    
    
    ds_tushare = DataServiceTushare()        
    def __init__(self):
        """"""
        super().__init__()        

    def is_out_stock(self, ts_code, date_picked):
        # 是否排除该股票
        if ts_code[0] not in ['0', '3', '6']:
            return True
        stock_basic = self.ds_tushare.get_stock_basic_info(ts_code)
        if stock_basic is None:
            self.logger.info('None stock basic info %s' %ts_code)
            return True
        dt_date = string_to_datetime(date_picked)
        d = timedelta(days=-365 * self.n_years)
        if stock_basic['list_date'] > time_to_str(dt_date+d, '%Y%m%d') or 'ST' in stock_basic['name']:
            # 排除上市时间小于2年和st股票
            return True
        dic_stock_price = self.ds_tushare.get_stock_price_info(ts_code, date_picked)       
        if dic_stock_price is None:
            # 排除选股日停牌的股票
            return True
        return False   

    def pick_stock(self, date_picked):                    
        lst_code_picked = list()
        ret_top_list = self.ds_tushare.get_top_list_by_date(date_picked)
        for item in ret_top_list:
            if self.is_out_stock(item['ts_code'], date_picked) is True:
                continue
            if item['net_rate'] > self.pct_buy:
                lst_code_picked.append(item['ts_code'])

            # high_gap = 'high_' + str(self.days_gap)
            # low_gap = 'low_' + str(self.days_gap)
            # days_break_gap = 'high_' + str(self.days_break)
            # try:
            #     if dic_stock_price['high_250'] / dic_stock_price['low_250'] < self.max_times_in_year and \
            #         dic_stock_price['ma_60'] > dic_stock_price['ma_120'] and \
            #             dic_stock_price['ma_120'] > dic_stock_price['ma_250']:
            #         date_pre = self.ds_tushare.get_pre_trade_date(date_picked, self.days_gap)
            #         price_pre = self.ds_tushare.get_stock_price_info(ts_code, date_pre)
            #         if dic_stock_price['ts_code'] == '000998_SZ':
            #             a = 1
            #         if price_pre['high'] < dic_stock_price[low_gap] and \
            #             price_pre['high'] > price_pre[days_break_gap]*(1.0-self.pct_high_break) and \
            #                 dic_stock_price['low'] < price_pre['high']*(1.0+self.pct_near_gap) and \
            #                     dic_stock_price[high_gap]/price_pre['high'] < (1.0+self.pct_max):
            #             lst_code_picked.append(dic_stock_price['ts_code'])                    
            # except:
            #     self.logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            #     self.logger.info(dic_stock_price)
        return lst_code_picked


if __name__ == "__main__":    
    strategy = StrategyTopList()
    ret_lst = strategy.pick_stock('20210623')
    print(set(ret_lst))
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
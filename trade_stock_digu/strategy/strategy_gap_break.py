import numpy as np
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
from trade_stock_digu.data_service import DataServiceTushare
from trade_stock_digu.convert_utils import string_to_datetime, time_to_str

class StrategyGapBreak(StrategyBase):
    """
    缺口突破策略：
    1、中长期均线多头排列(ma30>ma60>ma120>ma250>ma500)
    2、股价最近一年未暴涨(high_250/low_250<max_times_in_year)
    3、选股日当天有缺口突破 

    待补充：
    """
    days_break = 250    # 缺口突破的N日新高
    n_years = 2     # 上市时间超过n_years年    
    max_times_in_year = 4   #股票年内最大涨幅 high_250/low_250    

    def __init__(self):
        """"""
        super().__init__()

    def pick_stock(self, date_picked):            
        ds_tushare = DataServiceTushare()        
        lst_code_picked = list()
        for ts_code in ds_tushare.get_stock_lst():
            stock_basic = ds_tushare.get_stock_basic_info(ts_code)
            if stock_basic is None:
                self.logger.info('None stock basic info %s' %ts_code)
                continue
            dt_date = string_to_datetime(date_picked)
            d = timedelta(days=-365 * self.n_years)
            if stock_basic['list_date'] > time_to_str(dt_date+d, '%Y%m%d') or 'ST' in stock_basic['name']:
                # 排除上市时间小于2年和st股票
                continue
            dic_stock_price = ds_tushare.get_stock_price_info(ts_code, date_picked)       
            if dic_stock_price is None:
                # 排除选股日停牌的股票
                continue   
            days_break_high = 'high_' + str(self.days_break)
            try:
                if dic_stock_price['high_250'] / dic_stock_price['low_250'] < self.max_times_in_year and \
                        dic_stock_price['ma_30'] > dic_stock_price['ma_60'] and \
                        dic_stock_price['ma_60'] > dic_stock_price['ma_120'] and \
                        dic_stock_price['ma_120'] > dic_stock_price['ma_250'] and \
                        dic_stock_price['ma_250'] > dic_stock_price['ma_500']:
                    price_date_picked = ds_tushare.get_stock_price_info(ts_code, date_picked)
                    price_date_picked_pre_day = ds_tushare.get_stock_price_info(ts_code, ds_tushare.get_pre_trade_date(date_picked))                    
                    if dic_stock_price['ts_code'] == '000998_SZ':
                        a = 1
                    # 选出当日长阳突破新高的股票 当日收盘价==high_days_break 
                    # 当日涨幅>5%
                    if price_date_picked['high'] == price_date_picked[days_break_high] \
                        and price_date_picked['pct_chg'] > 6.0:
                        lst_code_picked.append(dic_stock_price['ts_code'])  
                    
                    # # 选出已经成功突破之后缺口加速的股票
                    # if price_date_picked['low'] > price_date_picked_pre_day[days_break_high]:
                    #     lst_code_picked.append(dic_stock_price['ts_code'])                                
            except:
                self.logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                self.logger.info(dic_stock_price)
        return lst_code_picked


if __name__ == "__main__":
    ds_tushare = DataServiceTushare()
    strategy = StrategyGapBreak()
    print(strategy.pick_stock('20201224'))
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
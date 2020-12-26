import numpy as np
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
from trade_stock_digu.data_service import DataServiceTushare
from trade_stock_digu.convert_utils import string_to_datetime, time_to_str

class StrategyGapBreakBack(StrategyBase):
    """
    缺口突破回调买入策略：
    1、中长期均线多头排列(ma30>ma60>ma120>ma250)
    2、股价最近一年未暴涨(high_250/low_250<max_times_in_year)
    3、最近5（10）天有缺口突破 days_gap
    4、缺口价格在250日新高附近(0.1)
    5、股价回调到缺口位置，缺口下端价格+2%以内
    6、缺口上方最高价涨幅0.2

    待补充：
    """
    days_gap = 10    # 股票运行在缺口之上运行天数
    days_break = 500    # 缺口（准备）突破的N日新高
    n_years = 2     # 上市时间超过n_years年    
    pct_near_gap = 0.06 #缺口大小百分：(突破日缺口上沿价格-缺口下沿价格)/缺口下沿价格    
    max_times_in_year = 4   #股票年内最大涨幅 high_250/low_250    
    pct_high_break = 0.1    # 缺口下沿价格距离长期最高价格（days_break）的百分比 
    pct_max = 0.4  # 缺口上的最大涨幅 （缺口上的最高价-缺口下沿价格）/缺口下沿价格
    # def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
    #     """"""
    #     super().__init__()

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
            high_gap = 'high_' + str(self.days_gap)
            low_gap = 'low_' + str(self.days_gap)
            days_break_gap = 'high_' + str(self.days_break)
            try:
                if dic_stock_price['high_250'] / dic_stock_price['low_250'] < self.max_times_in_year and \
                        dic_stock_price['ma_30'] > dic_stock_price['ma_60'] and \
                        dic_stock_price['ma_60'] > dic_stock_price['ma_120'] and \
                        dic_stock_price['ma_120'] > dic_stock_price['ma_250']:
                    date_pre = ds_tushare.get_pre_trade_date(date_picked, self.days_gap)
                    price_pre = ds_tushare.get_stock_price_info(ts_code, date_pre)
                    if dic_stock_price['ts_code'] == '000998_SZ':
                        a = 1
                    if price_pre['high'] < dic_stock_price[low_gap] and \
                        price_pre['high'] > price_pre[days_break_gap]*(1.0-self.pct_high_break) and \
                            dic_stock_price['low'] < price_pre['high']*(1.0+self.pct_near_gap) and \
                                dic_stock_price[high_gap]/price_pre['high'] < (1.0+self.pct_max):
                        lst_code_picked.append(dic_stock_price['ts_code'])                    
            except:
                self.logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                self.logger.info(dic_stock_price)
        return lst_code_picked


if __name__ == "__main__":
    ds_tushare = DataServiceTushare()
    strategy = StrategyGapBreakBack()
    print(strategy.pick_stock('20200828'))
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
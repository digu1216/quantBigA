import numpy as np
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
from data_service import DataServiceTushare
from convert_utils import string_to_datetime, time_to_str

class StrategyBullBack(StrategyBase):
    """
    长牛股回调策略：
    1、中长期均线多头排列(ma120>ma250<ma500,)
    2、股价最近一年未暴涨(high_250/low_250<3)
    3、中长期均线斜率向上(ma250>ma250_preday, ma250>ma250_preday)
    4、当前股价比high_250回调30%以上
    5、股价回调至长期均线位置（ma60，ma120,ma250） 上下 0.02
    6、长期均线半年(120 days)以上时间未触碰

    待补充：
    机构密集持股股票  
    """
    day_ma_long_effective = 120
    n_years = 2
    pct_near = 0.02
    pct_back = 0.3
    max_times_in_year = 4
    ma_long = 250
    # def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
    #     """"""
    #     super().__init__()

    def __init__(self):
        """"""
        super().__init__()

    def pick_stock(self, date_picked):            
        ds_tushare = DataServiceTushare()        
        lst_code_picked = list()
        for ts_code in ds_tushare.get_stock_list():
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
            str_ma_long = 'ma_' + str(self.ma_long)
            flag_in_pool = True
            try:
                if dic_stock_price['high_250'] / dic_stock_price['low_250'] < self.max_times_in_year \
                    and dic_stock_price['ma_120'] > dic_stock_price['ma_250'] \
                        and dic_stock_price['ma_250'] > dic_stock_price['ma_500'] and dic_stock_price['close'] < dic_stock_price['high_250'] * (1.0 - self.pct_back)\
                            and dic_stock_price['close'] > dic_stock_price[str_ma_long] * (1.0-self.pct_near) and dic_stock_price['close'] < dic_stock_price[str_ma_long] * (1.0+self.pct_near):
                    date_pre = ds_tushare.get_pre_trade_date(date_picked)
                    price_pre = ds_tushare.get_stock_price_info(ts_code, date_pre)
                    if dic_stock_price['ma_500'] > price_pre['ma_500'] and dic_stock_price['ma_250'] > price_pre['ma_250']:
                        cal = ds_tushare.get_pre_n_trade_date(dic_stock_price['trade_date'], self.day_ma_long_effective)
                        k_data_lst = ds_tushare.get_stock_price_lst(dic_stock_price['ts_code'], cal[-1], cal[0])
                        for k_data in k_data_lst:
                            if (k_data['close'] < k_data[str_ma_long]):
                                flag_in_pool = False
                                break
                        if flag_in_pool is True:
                            lst_code_picked.append(dic_stock_price['ts_code'])                    
            except:
                self.logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                self.logger.info(dic_stock_price)                    
        return lst_code_picked


if __name__ == "__main__":
    ds_tushare = DataServiceTushare()
    strategy = StrategyBullBack()
    print(strategy.pick_stock('20200811'))
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
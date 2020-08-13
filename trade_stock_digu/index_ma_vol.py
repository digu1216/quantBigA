from data_service import DataServiceTushare
from logger import Logger
from itertools import groupby
import matplotlib.pyplot as plt
from convert_utils import string_to_datetime, time_to_str

if __name__ == "__main__":
    logger = Logger().getlog()
    ds_tushare = DataServiceTushare()
    lst_trade_date = ds_tushare.getTradeCal('20180101', '20181231')
    lst_hold_date = list()
    for item_date in lst_trade_date:
        is_hold_date = True        
        for ts_code in ["000001_SH", "399001_SZ"]:
            info_k_data = ds_tushare.getStockPriceInfo(ts_code, item_date)
            if info_k_data['close'] < info_k_data['ma_20'] or info_k_data['vol_rate'] < 1 or info_k_data['amount_rate'] < 1:
                is_hold_date = False
        if is_hold_date is True:
            lst_hold_date.append(item_date)
    lst_sh = list()
    lst_sh_date = list()
    cnt_win = 0
    cnt_loss = 0  
    sum_chg = 0.0
    rate_win = 0.0      
    for item_hold_date in lst_hold_date:
        idx = lst_hold_date.index(item_hold_date)
        if idx < len(lst_hold_date):
            day_next = ds_tushare.get_next_trade_date(item_hold_date)            
            info_k_data_sh = ds_tushare.getStockPriceInfo('000001_SH', day_next)            
            info_k_data_sz = ds_tushare.getStockPriceInfo('399001_SZ', day_next)   
            index_chg = info_k_data_sh['pct_chg'] + info_k_data_sz['pct_chg']
            sum_chg += (index_chg / 2)
            if info_k_data_sh is not None and info_k_data_sz is not None:         
                if  index_chg > 0:
                    cnt_win += 1
                else:
                    cnt_loss += 1            
            lst_sh_date.append(info_k_data_sh['trade_date'])
    rate_win = cnt_win / (cnt_loss + cnt_win)
    logger.info('成功次数：%s   失败次数：%s' %(cnt_win, cnt_loss))
    logger.info('成功率：%s' %(rate_win))
    logger.info('净收益率：%s' %(sum_chg))
    
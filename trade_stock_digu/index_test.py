from data_service import DataServiceTushare
from logger import Logger
from itertools import groupby
import matplotlib.pyplot as plt
from convert_utils import string_to_datetime, time_to_str

if __name__ == "__main__":
    logger = Logger().getlog()
    ds_tushare = DataServiceTushare()
    lst_trade_date = ds_tushare.getTradeCal('20110101', '20111231')
    lst_hold_date = list()
    for item_date in lst_trade_date:
        is_hold_date = True        
        for ts_code in ["000001.SH", "399001.SZ"]:
            info_k_data = ds_tushare.getStockPriceInfo(ts_code, item_date)
            if info_k_data['close'] < info_k_data['ma_20'] or info_k_data['qrr'] < 1:
                is_hold_date = False
        if is_hold_date is True:
            lst_hold_date.append(item_date)
    lst_sh = list()
    lst_sh_date = list()
    lst_sz = list()
    lst_zxb = list()
    lst_cyb = list()
    cnt_win = 0
    cnt_loss = 0    
    rate_win = 0.
    for item_hold_date in lst_hold_date:
        idx = lst_hold_date.index(item_hold_date)
        if idx < len(lst_hold_date):
            day_next = ds_tushare.get_next_trade_date(item_hold_date)
            # for ts_code in ["000001.SH", "399001.SZ", "399005.SZ", "399006.SZ"]:
            info_k_data = ds_tushare.getStockPriceInfo('000001.SH', day_next)
            rate_win += info_k_data['pct_chg']
            if info_k_data['pct_chg'] > 0:
                cnt_win += 1
            else:
                cnt_loss += 1
            lst_sh.append(round(info_k_data['pct_chg'], 1))
            lst_sh_date.append(info_k_data['trade_date'])
            info_k_data = ds_tushare.getStockPriceInfo('399001.SZ', day_next)
            lst_sz.append(round(info_k_data['pct_chg'], 1))
            # info_k_data = ds_tushare.getStockPriceInfo('399005.SH', day_next)
            # lst_zxb.append(round(info_k_data['pct_chg'], 1))
            # info_k_data = ds_tushare.getStockPriceInfo('399006.SH', day_next)
            # lst_cyb.append(round(info_k_data['pct_chg'], 1))

    idx_pre = 0
    idx_loop = 0
    month_cur = 1
    lst_sh_part = list()    
    for item_hold_date in lst_hold_date:                
        date = string_to_datetime(item_hold_date)
        if month_cur != date.month or idx_loop == len(lst_hold_date)-1:
            if idx_loop != len(lst_hold_date)-1:
                lst_sh_part = lst_sh[idx_pre:idx_loop]            
            else:
                lst_sh_part = lst_sh[idx_pre:]            
            lst_sh_part.sort()
            lst_pct_chg = list()
            cnt_pct_chg = list()
            for k, g in groupby(lst_sh_part, key=lambda x: int(round((x*10)/5, 0)) * 0.5):
                lst_pct_chg.append(k)
                cnt_pct_chg.append(len(list(g)))            
            slices = cnt_pct_chg
            activities = lst_pct_chg
            # if month_cur in [1]:
            print(month_cur)
            if idx_loop != len(lst_hold_date)-1:
                print(lst_sh_date[idx_pre:idx_loop])
            else:
                print(lst_sh_date[idx_pre:])
            plt.subplot(3, 4, month_cur).pie(slices, labels=activities)
            plt.subplot(3, 4, month_cur).set_title('%s M cnt: %s' %(month_cur, len(lst_sh_part)))
            month_cur = date.month
            idx_pre = idx_loop
        idx_loop += 1
    plt.title('%s(%s)' %(round(cnt_win/cnt_loss, 1), round(rate_win, 2)), loc='right')
    plt.show()




    # lst_sh.sort()
    # lst_sz.sort()
    # lst_zxb.sort()
    # lst_cyb.sort()
    # 按大盘0.5%绘制饼图
    # lst_pct_chg = list()
    # cnt_pct_chg = list()
    # for k, g in groupby(lst_sh, key=lambda x: int(round((x*10)/5, 0)) * 0.5):
    #     lst_pct_chg.append(k)
    #     cnt_pct_chg.append(len(list(g)))
    # slices = cnt_pct_chg
    # activities = lst_pct_chg
    # cols = ['c', 'm', 'r', 'b']

    # plt.pie(slices, labels=activities)

    # plt.title('Interesting Graph\nCheck it out')
    # plt.show()
    
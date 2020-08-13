import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from data_service import DataServiceTushare
from logger import Logger
import tushare as ts
from time import time, sleep
from itertools import groupby
from strategy_vol import StrategyVol

def rise_ma(percent = 8):
    close_cur = np.array(list())
    percent_cur = np.array(list())
    close_pre = np.array(list())
    ma5_pre = np.array(list())
    ma10_pre = np.array(list())
    ma20_pre = np.array(list())
    ma30_pre = np.array(list())
    ma60_pre = np.array(list())
    ma120_pre = np.array(list())
    ma250_pre = np.array(list())
    ma500_pre = np.array(list())
    ds_tushare = DataServiceTushare()
    code_lst = ds_tushare.get_stock_list()
    for item_code in code_lst:
        k_data_lst = ds_tushare.get_stock_price_lst(item_code, '20100101', '20180101')
        if len(k_data_lst) == 0:
            continue
        k_data_pre = k_data_lst.pop(0)
        for item_price in k_data_lst:
            if item_price['pct_chg'] > percent:
                close_cur = np.append(close_cur, item_price['close'])
                percent_cur = np.append(percent_cur, item_price['pct_chg'])
                close_pre = np.append(close_pre, k_data_pre['close'])
                ma5_pre = np.append(ma5_pre, k_data_pre['ma_5'])
                ma10_pre = np.append(ma10_pre, k_data_pre['ma_10'])
                ma20_pre = np.append(ma20_pre, k_data_pre['ma_20'])
                ma30_pre = np.append(ma30_pre, k_data_pre['ma_30'])
                ma60_pre = np.append(ma60_pre, k_data_pre['ma_60'])
                ma120_pre = np.append(ma120_pre, k_data_pre['ma_120'])
                ma250_pre = np.append(ma250_pre, k_data_pre['ma_250'])
                ma500_pre = np.append(ma500_pre, k_data_pre['ma_500'])
            k_data_pre = item_price
    index = [0,1,2,3,4,5,6,7]
    cnt_rise = float(len(percent_cur))
    values = [np.sum(close_pre > ma5_pre)/cnt_rise, np.sum(close_pre > ma10_pre)/cnt_rise, np.sum(close_pre > ma20_pre)/cnt_rise, np.sum(close_pre > ma30_pre)/cnt_rise, \
            np.sum(close_pre > ma60_pre)/cnt_rise, np.sum(close_pre > ma120_pre)/cnt_rise, np.sum(close_pre > ma250_pre)/cnt_rise, np.sum(close_pre > ma500_pre)/cnt_rise]
    print(values)    
    plt.bar(index, values)
    plt.xticks(index,['5','10','20','30','60', '120', '250', '500'])
    plt.show()

def short_line_ma(days = 5):
    # 连续n天股价 ma5*1.08>收盘价>=ma5, 最低价>=ma10,ma10*1.05>ma5
    # ma5>ma10>ma20>ma60>ma120
    ds_tushare = DataServiceTushare()
    lst_code_picked = list()
    code_lst = ds_tushare.get_stock_list()
    for item_code in code_lst:
        date_begin = ds_tushare.get_pre_trade_date('202200804', days)
        k_data_lst = ds_tushare.get_stock_price_lst(item_code, date_begin, '202200804')
        if len(k_data_lst) == 0:
            continue
        cnt = 0
        for item_price in k_data_lst:
            if item_price['close'] < item_price['ma_5'] or item_price['close'] > item_price['ma_5'] * 1.08 or item_price['low'] < item_price['ma_10']:
                break
            if item_price['ma_5'] > item_price['ma_10'] * 1.05:
                break
            if item_price['ma_120'] > item_price['ma_60'] or item_price['ma_60'] > item_price['ma_30'] or item_price['ma_30'] > item_price['ma_20'] \
                or item_price['ma_20'] > item_price['ma_10'] or item_price['ma_10'] > item_price['ma_5']:
                break
            cnt += 1
            if cnt == days:
                print(item_price['ts_code'])
                lst_code_picked.append(item_price['ts_code'])
    print(lst_code_picked)

if __name__ == "__main__":
    logger = Logger().getlog()
    # rise_ma()
    short_line_ma()

    # lst_trade_date = ds_tushare.getTradeCal(begin_date='20190101', end_date='20200331')
    # lst_date = list()
    # lst_net_rate = list()
    # for item_date in lst_trade_date:
    #     lst_top_list = ds_tushare.getStockTopList(item_date)
    #     for item_top_list in lst_top_list:
    #         lst_net_rate.append(item_top_list['net_rate'])
    #         龙虎榜统计数据结构 ts_code, trade_date, net_rate, n+1日开盘价，最低价，n+2~3日最低价，最高价,n+3日收盘价
    #         item_dic = dict()
    #         item_dic['ts_code'] = item_top_list['ts_code']
    #         item_dic['trade_date'] = item_top_list['trade_date']
    #         item_dic['net_rate'] = item_top_list['net_rate']
    #         lst_price = ds_tushare.getStockPriceLst(item_top_list['ts_code'].replace('.', '_'), item_top_list['trade_date'])
    #         lst_price = list(lst_price)
    #         if len(lst_price) == 0:
    #             continue
    #         n1_open = lst_price[1]['open']
    #         n1_low = lst_price[1]['low']
    #         n23_high = 0.0
    #         n23_low = 0.0
    #         n3_close = lst_price[3]['close']
    #         for i in range(2, 4):
    #             n23_high = lst_price[i]['high'] if lst_price[i]['high'] > n23_high else n23_high
    #             n23_low = lst_price[i]['low'] if lst_price[i]['low'] < n23_low else n23_low
    #         item_dic['n1_open'] = n1_open
    #         item_dic['n1_low'] = n1_low
    #         item_dic['n23_high'] = n23_high
    #         item_dic['n23_low'] = n23_low
    #         item_dic['n3_close'] = n3_close
    #         lst_date.append(item_dic)
    # lst_net_rate.sort()
    # a = [(k, len(list(g))) for k,g in groupby(lst_net_rate, key=lambda x:x//5)]
    # print(a)
    # rate_high = 0.0
    # rate_low = 0.0
    # cnt = 0
    # for item in lst_date:
    #     if item['net_rate'] > 80:
    #         cnt += 1
    #         rate_high += item_dic['n23_high'] - item_dic['n1_open']
    #         rate_low += item_dic['n23_low'] - item_dic['n1_open']
    # print('higt=%s' %(rate_high/cnt))
    # print('low=%s' %(rate_low/cnt))
    # print(cnt)



    # lst_code_picked = list()
    # ts.set_token('4c1d16a895e4c954adc8d2a436f2b21dd4ccc514f0c5a192edaa953b')
    # pro = ts.pro_api()
    # cnt = 0
    # for ts_code in ds_tushare.lst_stock_:         
    #     try:
    #         df = pro.top10_floatholders(ts_code=ts_code.replace('_', '.'), start_date='20190901', end_date='20200131')
    #         sleep(1)
    #     except:
    #         break
    #     xx = [x for x in df['holder_name'].tolist() if x.find('安邦')>0]            
    #     if len(xx) != 0:              
    #         lst_code_picked.append(df['ts_code'][1])
    # for ts_code in ds_tushare.lst_stock_:
    #     ts_code = ts_code.replace('.', '_')
    #     lst_stock_price = ds_tushare.getStockPriceLst(ts_code, '20200310')        
    #     for item in lst_stock_price:
    #         # 年内低点到高点反弹40%以内,high20 = high60
    #         if item['high_30'] < item['low_250'] * 1.4 and item['high_20'] == item['high_60']:                       
    #                 if item['ts_code'] not in lst_code_picked:
    #                     lst_code_picked.append(item['ts_code'])

            # 2年新高选股              
            # if item['close'] >= item['high_500'] and item['ma_60'] < item['ma_30']:       
            #     if item['ts_code'] not in ['000009_SZ', '000063_SZ', '000818_SZ', '002023_SZ', '002056_SZ', '002169_SZ', '002328_SZ', '002402_SZ', '002613_SZ', '002683_SZ', '002912_SZ', '002975_SZ', '300031_SZ', '300046_SZ', '300155_SZ', '300160_SZ', '300235_SZ', '300236_SZ', '300346_SZ', '300390_SZ', '300457_SZ', '300576_SZ', '300578_SZ', '300598_SZ', '300603_SZ', '300655_SZ', '300671_SZ', '300724_SZ', '300812_SZ', '300815_SZ', '300816_SZ', '300818_SZ', '300820_SZ', '600546_SH', '600584_SH', '600732_SH', '603005_SH', '603195_SH', '603232_SH', '603290_SH', '603308_SH', '603313_SH', '603636_SH', '603678_SH', '603688_SH', '603893_SH', '688357_SH']:         
            #         if item['ts_code'] not in lst_code_picked:
            #             lst_code_picked.append(item['ts_code'])
            
            # 二十日低点反弹5个点以内
            # if item['low_20'] * 1.05 < item['close'] and item['low_20'] * 1.07 >= item['close']:       
            #     lst_code_picked.append(item['ts_code'])
            
            # 昨日触板回落股
            # base_info = ds_tushare.getStockBasicInfo(item['ts_code'].replace('_', '.'))
            # if base_info['list_date'] > '20190101':
            #     continue
            # if item['high'] >= item['pre_close'] * 1.09 and item['close'] < item['pre_close'] * 1.08 and item['pct_chg'] > 5 and item['high'] < item['low_20']*1.5 \
            #     and item['high'] < item['low_500'] * 2.5 and item['high'] < item['low_5'] * 1.2 and item['high'] < item['low_10'] * 1.5:       
            #     if item['ts_code'] not in lst_code_picked:
            #         if item['ts_code'] not in ['000012_SZ', '000587_SZ', '002121_SZ', '002747_SZ', '300024_SZ', '300208_SZ', '300637_SZ', '600109_SH', '600130_SH', '600358_SH', '600499_SH', '600525_SH', '600577_SH', '600893_SH', '601002_SH', '601212_SH', '603788_SH']:
            #             lst_code_picked.append(item['ts_code'])
    # logger.info(lst_code_picked)

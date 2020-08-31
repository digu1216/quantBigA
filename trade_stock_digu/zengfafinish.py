import pandas as pd
import numpy as np
from data_service import DataServiceTushare
import matplotlib.pyplot as plt
df = pd.read_csv('D:\\code\\python\\quant_big_a\\data\\zengfafinish20192020.csv')

df1 = df[df['date_on'] < 20200601]
pct_high = 0.2  #增发日股票上市价高于增发价比例
days_n = 60 #跟踪上市日之后N日的表现
# 计算现金增发完成后的股票表现情况
# 排除增发成本比上市日股价高出30%以上(pct_high)的股票
# 增发股票上市日作为基准日：计算收盘最大涨幅（跌幅）平均值和中位数
ds_tushare = DataServiceTushare()
lst_up = list()
lst_down = list()
lst_code_close_pct_chg = list() # 每只股票的观察日区间收盘涨跌幅列表
for index, row in df1.iterrows():
    date_end = ds_tushare.get_next_trade_date(str(row["date_on"]), days_n)
    date_start = str(row["date_on"])
    lst_close = list()
    lst_close_pct_chg = list()
    code = row["code"].replace('.', '_')
    price_cost = ds_tushare.get_stock_price_info(code, date_start)
    if price_cost['open'] > row["price_cost"] * (1.0 + pct_high):
        continue
    lst_trade_date = ds_tushare.get_trade_cal(date_start, date_end)
    k_data_pre = dict()
    price_base = 0.0
    for item_date in lst_trade_date:
        k_data = ds_tushare.get_stock_price_info(code, item_date)
        price_base = k_data['open'] if item_date == date_start else price_base
        if k_data is None:
            k_data = k_data_pre
        lst_close.append(k_data['close'])
        lst_close_pct_chg.append((k_data['close'] - price_base) / price_base) 
        k_data_pre = k_data
    if np.max(lst_close_pct_chg) > 0.50:
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        print(code)
    lst_code_close_pct_chg.append(lst_close_pct_chg)
    pct_up = (max(lst_close) - price_base) / price_base
    pct_down = (min(lst_close) - price_base) / price_base
    lst_up.append(pct_up)
    lst_down.append(pct_down)
mean_up = np.mean(lst_up)
mean_down = np.mean(lst_down)
median_up = np.median(lst_up)
median_down = np.median(lst_down)
print(len(lst_up), mean_up, median_up, mean_down, median_down)
arr_close_pct_chg = np.zeros(shape=(len(lst_code_close_pct_chg), days_n+1))
i = 0
for item in lst_code_close_pct_chg:
    arr_close_pct_chg[i,:] = np.array(item)
    i += 1
plt.plot(np.arange(days_n+1), arr_close_pct_chg.sum(axis=0))  
plt.show() 
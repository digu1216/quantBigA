import pandas as pd
import numpy as np
df = pd.read_csv('D:\code\quant_big_a\\trade_stock_digu\\dingzengjiejin2020.csv')
from data_service import DataServiceTushare

df1 = df[df['date_free'] < 20200801]
# 计算定增解禁期间股票表现情况 
# 计算定增解禁股解禁日前后20个交易日信息
# 解禁日之前的20日作为基准日：计算收盘最大涨幅（跌幅）平均值和中位数
ds_tushare = DataServiceTushare()
lst_up = list()
lst_down = list()
for index, row in df1.iterrows():
    date_end = ds_tushare.get_next_trade_date(str(row["date_free"]), 20)
    date_start = ds_tushare.get_pre_trade_date(str(row["date_free"]), 20)
    lst_close = list()
    code = row["code"].replace('.', '_')
    lst_k_data = ds_tushare.get_stock_price_lst(code, date_start, date_end)
    for item in lst_k_data:
        lst_close.append(item['close'])
    if len(lst_close) == 0:
        continue
    price_base = lst_close[0]
    pct_up = (max(lst_close) - price_base) / price_base
    pct_down = (min(lst_close) - price_base) / price_base
    lst_up.append(pct_up)
    lst_down.append(pct_down)
mean_up = np.mean(lst_up)
mean_down = np.mean(lst_down)
median_up = np.median(lst_up)
median_down = np.median(lst_down)
print(mean_up, median_up, mean_down, median_down)
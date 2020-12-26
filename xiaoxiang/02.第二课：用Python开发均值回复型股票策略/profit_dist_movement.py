# -*- coding: utf-8 -*-

import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt

start_date = "2016-01-01"
end_date = "2018-05-31"
obs_percent = 0.3  # 时间分3段，用首尾两个时间段来比较收益排名均值的变化
cmp_percent = 0.1  # 取收益最高的和最低的各10%，计算收益排名的均值

stock_list = ts.get_stock_basics()["name"]  # 全市场股票信息列表
pf_list = []

cnt = 0
for code, name in stock_list.iteritems():
    print(cnt, code, name)
    if name.find("ST") != -1:  # 排除ST和*ST股票
        continue
    df = ts.get_k_data(code, start=start_date, end=end_date, ktype="D", autype="qfq")  # 读日K行情数据
    if len(df) < 400:  # 如果有较长的停牌时间，则忽略它
        continue
    df.index = df.pop("date")
    win_size = int(len(df) * obs_percent)  # 用于计算收益率的时间窗口宽度

    profit_1 = int((df["close"][win_size-1]/df["close"][0] - 1.0) * 100)  # 第1段时间内的收益率
    profit_2 = int((df["close"][-1]/df["close"][-win_size] - 1.0) * 100)  # 第2段时间内的收益率

    if profit_1 > 150 or profit_2 > 150:  # 为便于观察分布图，忽略一些特别大或特别小的值
        continue

    pf_list.append(dict(code=code, pf1=profit_1, pf2=profit_2))  # 保存每只股票的2个收益率的值

    cnt += 1

pf_list.sort(key=lambda x: x["pf1"], reverse=True)  # 先按第1段时间内的收益率排名（从高往低）
for idx, doc in enumerate(pf_list):
    doc["rank_1"] = idx  # 记录下每只个股在第1段时间内的收益率排名

num_cands = int(len(pf_list)*cmp_percent)  # 用于统计的最高（和最低）收益的股票个数
top_cands = pf_list[:num_cands]   # 第1段时间内最高收益的股票信息列表
btm_cands = pf_list[-num_cands:]  # 第1段时间内最低收益的股票信息列表
top_group_codes = set([doc["code"] for doc in top_cands])  # 最高收益股票代码集合
btm_group_codes = set([doc["code"] for doc in btm_cands])  # 最低收益股票代码集合
avg_top_idx = round(sum([doc["rank_1"] for doc in top_cands])/num_cands/len(pf_list), 2)  # 最高收益股票排名均值
avg_btm_idx = round(sum([doc["rank_1"] for doc in btm_cands])/num_cands/len(pf_list), 2)  # 最低收益股票排名均值
avg_mid_idx = (0 + len(pf_list)-1) / 2 / len(pf_list)  # 所有股票收益排名的均值，等差数列均值（中值），直接计算即可

pf_list.sort(key=lambda x: x["pf2"], reverse=True)  # 再按第2段时间内的收益率排名（从高往低）
for idx, doc in enumerate(pf_list):
    doc["rank_2"] = idx  # 记录下每只个股在第2段时间内的收益率排名

cmp_avg_top_idx = round(sum([doc["rank_2"] for doc in pf_list if doc["code"] in top_group_codes])/num_cands/len(pf_list), 2)
cmp_avg_btm_idx = round(sum([doc["rank_2"] for doc in pf_list if doc["code"] in btm_group_codes])/num_cands/len(pf_list), 2)

print("Top group:", avg_top_idx, "->", cmp_avg_top_idx, "(avg: %.2f)" % avg_mid_idx)
print("Btm group:", avg_btm_idx, "->", cmp_avg_btm_idx, "(avg: %.2f)" % avg_mid_idx)

profits = pd.DataFrame({"pf1": [doc["pf1"] for doc in pf_list], "pf2": [doc["pf2"] for doc in pf_list]})
profits.plot.hist(bins=200, alpha=0.5)  # 绘制两段时间内全市场收益率分布的直方图
plt.show()

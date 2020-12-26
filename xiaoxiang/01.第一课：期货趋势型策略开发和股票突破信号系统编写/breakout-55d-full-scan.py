# -*- coding: utf-8 -*-

import tushare as ts

window_size = 55

all_stocks = ts.get_stock_basics()["name"]
for code, name in all_stocks.iteritems():
    temp = ts.get_k_data(code, start="2018-01-01", ktype="D", autype="qfq")
    temp.index = temp.pop("date")
    df = temp.loc[:, ["high", "close"]]
    df["hhv"] = df["high"].rolling(window_size).max()
    df["pre_hhv"] = df["hhv"].shift(1)
    df["signals"] = (df["close"].shift(1) <= df["pre_hhv"].shift(1)) & \
                    (df["close"] > df["pre_hhv"])
    results = df[df["signals"]]
    if len(results) > 0:
        print(code, name, list(results.index))

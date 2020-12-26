# -*- coding: utf-8 -*-

import tushare as ts

window_size = 5  # 过程演示用，待改为55
code = "000001"

temp = ts.get_k_data(code, start="2018-03-01", ktype="D", autype="qfq")
temp.index = temp.pop("date")
df = temp.loc[:, ["high", "close"]]
df["hhv"] = df["high"].rolling(window_size).max()
df["pre_hhv"] = df["hhv"].shift(1)
# df["signals"] = df["close"] > df["pre_hhv"]
df["signals"] = (df["close"].shift(1) <= df["pre_hhv"].shift(1)) & \
                (df["close"] > df["pre_hhv"])
print(df)
results = df[df["signals"]]
print(list(results.index))

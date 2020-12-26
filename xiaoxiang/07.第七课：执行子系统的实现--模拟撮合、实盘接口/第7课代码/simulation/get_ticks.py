import tushare as ts
import time

codes = ['002415', '000001', '601988', '600050']

for count in range(0, 100):
    df_ticks = ts.get_realtime_quotes(codes)

    for index in df_ticks.index:
        print(dict(df_ticks.loc[index]), flush=True)

    time.sleep(3)

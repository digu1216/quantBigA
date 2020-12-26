# 择时短线1:
# 1、收盘后涨跌8%以上个股比例
# 上涨8%股票数：股票总数
# 下跌8%股票数：股票总数
# 上涨8%股票数：下跌8%股票数
# 2、收盘后昨日涨8%股票今日表现: 平均涨幅
# 3、收盘后昨日跌8%股票今日表现: 平均涨幅
# 4、收盘后昨日振幅12%股票今日表现: 平均涨幅

# Y:所有股票(ma5以上多头排列股票)涨幅中位数
# 注：排除上市2年以内的新股

import datetime
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
from data_service import DataServiceTushare, DATA_BEGIN_DATE
from convert_utils import string_to_datetime, time_to_str

def data_to_db()
ds_tushare = DataServiceTushare()
ds_tushare.get_trade_cal(DATA_BEGIN_DATE)



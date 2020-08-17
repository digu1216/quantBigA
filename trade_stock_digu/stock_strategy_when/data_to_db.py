import datetime
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
from collections import Counter
from strategy_base import StrategyBase
from data_service import DataServiceTushare
from convert_utils import string_to_datetime, time_to_str

def get_begin_end_date_in_month(year):
    begin_date_lst = list()
    end_date_lst = list()
    for x in range(1, 13):
        dt_start = (datetime(year, x, 1)).strftime("%Y%m%d")
        if 12 == x:
            dt_end = (datetime(year, 12, 31)).strftime("%Y%m%d")
        else:
            dt_end = (datetime(year, x+1, 1) - timedelta(days = 1)).strftime("%Y%m%d")
        begin_date_lst.append(dt_start)
        end_date_lst.append(dt_end)
    return begin_date_lst, end_date_lst


import json
import tushare as ts
import numpy as np
import pandas as pd
from enum import Enum
from collections import deque
import traceback
import os
import talib
from datetime import datetime
from datetime import timedelta
from time import time, sleep
from pymongo import MongoClient, ASCENDING, DESCENDING

from vnpy.app.cta_strategy import (
    BarData,
    BarGenerator,
    ArrayManager
)
from vnpy.trader.constant import Exchange
# from vnpy.quant_big_a.tools.convert_utils import string_to_datetime, time_to_str
# from vnpy.quant_big_a.tools.logger import Logger
from tools.convert_utils import string_to_datetime, time_to_str
from tools.logger import Logger

db_vnpy = mc['stock_vnpy']  # 数据库
db['aaaaaaa']
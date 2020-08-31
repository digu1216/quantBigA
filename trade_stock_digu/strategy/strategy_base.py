from datetime import datetime
from abc import ABC, abstractmethod
import sys
sys.path.append('../')

from trade_stock_digu.logger import Logger
from trade_stock_digu.convert_utils import string_to_datetime, time_to_str
from trade_stock_digu.data_service import DataServiceTushare

class StrategyBase(ABC):
    """
    选股策略基类
    """
    author = ""
    logger = Logger().getlog()

    def __init__(self):
        """Constructor"""               
        self.lst_stock_picked = list()
        self.stock_picked_date = time_to_str(datetime.now(), '%Y%m%d')
    
    def set_date(self, date):
        # 设置选股日期
        ds_tushare = DataServiceTushare()
        trade_date = ds_tushare.get_trade_date(date)
        self.stock_picked_date = trade_date

    @abstractmethod
    def pick_stock(self, date):
        pass


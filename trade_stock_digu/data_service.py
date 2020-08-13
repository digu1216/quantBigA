# encoding: UTF-8

import json
import tushare as ts
import numpy as np
import pandas as pd
from enum import Enum
from collections import deque
import traceback
import os

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
from vnpy.tools.convert_utils import string_to_datetime, time_to_str
from vnpy.tools.logger import Logger

# 加载配置
# config = open('C:/vnstudio/Lib/site-packages/vnpy/trade_stock_digu/config.json')
path_config_file = os.path.dirname(os.path.abspath(__file__))
config = open(path_config_file + '/config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
MONGO_USER = setting['MONGO_USER']
MONGO_PASSWORD = setting['MONGO_PASSWORD']
STOCK_DB_NAME = setting['DB_NAME']
STOCK_DB_NAME_VNPY = setting['DB_NAME_VNPY']
CL_STOCK_K_DATA_VNPY = setting['CL_STOCK_K_DATA_VNPY']
CL_STOCK_DATE = setting['CL_STOCK_DATE']
CL_STOCK_BASIC = setting['CL_STOCK_BASIC']
CL_TRADE_CAL = setting['CL_TRADE_CAL']
DATA_BEGIN_DATE = setting['DATA_BEGIN_DATE']
CL_INDEXS = setting['CL_INDEXS']
CL_TOP10_HOLDER = setting['CL_TOP10_HOLDER']
CL_TOP10_FLOADHOLDER = setting['CL_TOP10_FLOADHOLDER']
CL_PLEDGE_STAT = setting['CL_PLEDGE_STAT']
CL_REPURCHASE = setting['CL_REPURCHASE']
CL_STK_HOLDERNUMBER = setting['CL_STK_HOLDERNUMBER']
CL_STK_HOLDERTRADE = setting['CL_STK_HOLDERTRADE']
CL_STK_POOL_DAILY = setting['CL_STK_POOL_DAILY']
CL_STK_POOL_CUR = setting['CL_STK_POOL_CUR']
CL_STK_TOP_LIST = setting['CL_STK_TOP_LIST']

LOG = Logger().getlog()

class IndexCode:
    INDEX_SH = '000001_SH'
    INDEX_SZ = '399001_SZ'
    INDEX_ZX = '399005_SZ'
    INDEX_CY = '399006_SZ'
    
    _VALUES_TO_NAMES = {
        '000001_SH': "INDEX_SH",
        '399001_SZ': "INDEX_SZ",
        '399005_SZ': "INDEX_ZX",
        '399006_SZ': "INDEX_CY",
    }
    
    _NAMES_TO_VALUES = {
        "INDEX_SH": '000001_SH',
        "INDEX_SZ": '399001_SZ',
        "INDEX_ZX": '399005_SZ',
        "INDEX_CY": '399006_SZ',
    }
    

class TsCodeType(Enum):
    """
    交易代码类型 1: 股票  2：指数
    """
    STOCK = 1
    INDEX = 2 

class DataServiceTushare(object):
    """封装tushare获取原始数据模块"""
    """
    ts_code: 在程序中采用000001_SZ的格式，调用tushare接口时替换为000001.SZ格式
    """

    mc = MongoClient(MONGO_HOST, MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD)  # Mongo连接
    # mc = MongoClient("mongodb://124.70.183.208:27017/", username='root', password='qiuqiu78')
    db = mc[STOCK_DB_NAME]  # 数据库
    db_vnpy = mc[STOCK_DB_NAME_VNPY]  # 数据库
    count_max_retry = 10
    second_sleep = 60
    index_lst = ['000001_SH', '399001_SZ', '399005_SZ', '399006_SZ']       

    def __init__(self):
        """Constructor"""        
        cl_stock_db_date = self.db[CL_STOCK_DATE]
        db_date = cl_stock_db_date.find_one({}, {"_id": 0, "db_date": 1})
        self.db_date = DATA_BEGIN_DATE if db_date is None else db_date['db_date']
        self.date_now = time_to_str(datetime.now(), '%Y%m%d')
        ts.set_token('4c1d16a895e4c954adc8d2a436f2b21dd4ccc514f0c5a192edaa953b')
        self.pro = ts.pro_api()

    def get_stock_list(self):
        lst_code = list()
        cl_stock_basic = self.db[CL_STOCK_BASIC]
        stock_basic_lst = list(cl_stock_basic.find(
            {}, {'_id': 0}).sort("ts_code", ASCENDING))
        for d in stock_basic_lst:  
            lst_code.append(d['ts_code'])
        return lst_code

    def get_trade_date(self, trade_date):
        # 获取当前日期最邻近的一个交易日
        # 1、如果当前日期就是交易日，则返回当前日期
        # 2、如果当前日期不是交易日，则返回当前日期之前的一个交易日
        cl_cal = self.db[CL_TRADE_CAL]
        trade_cal = list(cl_cal.find(
            {'cal_date': {"$lte": trade_date}, 'is_open': 1},
            {'_id': 0}).sort("cal_date"))
        return list(trade_cal)[-1]['cal_date']

    def _is_in_vnpy_db(self, ts_code, update=True):
        if ts_code in self.index_lst:
            return True
        else:
            return False

    def _build_db_vnpy(self, d):
        # 更新vnpy数据库数据
        if d['trade_date'] > self.db_date:            
            d_db_vnpy = dict()
            if d['ts_code'][-2:] == 'SH':
                # exchange = Exchange.SSE
                exchange = 'SSE'
            else:
                # exchange = Exchange.SZSE
                exchange = 'SZSE'
            d_db_vnpy['symbol'] = d['ts_code']
            d_db_vnpy['exchange'] = exchange
            d_db_vnpy['datetime'] = string_to_datetime(d['trade_date'])
            d_db_vnpy['interval'] = 'd'
            d_db_vnpy['volume'] = d['vol']
            d_db_vnpy['open_interest'] = d['pre_close']
            d_db_vnpy['open_price'] = d['open']
            d_db_vnpy['high_price'] = d['high']
            d_db_vnpy['low_price'] = d['low']
            d_db_vnpy['close_price'] = d['close']
            flt_vnpy = {'symbol': d['ts_code'], 'datetime': d['trade_date'], 'exchange:': exchange, 'interval:': 'd',}        
            cl_stock_code_vnpy = self.db_vnpy[CL_STOCK_K_DATA_VNPY]
            cl_stock_code_vnpy.create_index([('symbol', ASCENDING), ('exchange', ASCENDING), ('interval', ASCENDING), ('datetime', ASCENDING)], unique=True)
            cl_stock_code_vnpy.replace_one(flt_vnpy, d_db_vnpy, upsert=True)

    def _init_k_data(self, code, k_data):
        # 注意：所有的数据库数据和列表数据都按照日期的正序排序(从小到大)
        """
        初始化股票数据库数据
        @:param code  股票(指数)代码                
        """     
        if len(k_data) != 0:
            last_5_vol = deque([0.0] * 5)
            last_5_amount = deque([0.0] * 5)
            k_data = k_data.sort_values(by='trade_date')            
            cl_stock_code = self.db[code]
            cl_stock_code.create_index([('trade_date', ASCENDING)], unique=True)
            am = ArrayManager(size=600)
            for ix, row in k_data.iterrows():
                d = row.to_dict()              
                d['ts_code'] = d['ts_code'].replace('.', '_')
                if 0.0 not in last_5_vol:
                    vol_rate = d['vol'] / (sum(last_5_vol) / 5.0)                
                    amount_rate = d['amount'] / (sum(last_5_amount) / 5.0)   
                    d['vol_rate'] = vol_rate
                    d['amount_rate'] = amount_rate 
                else:
                    d['vol_rate'] = 0.0
                    d['amount_rate'] = 0.0
                last_5_vol.popleft()
                last_5_amount.popleft()
                last_5_vol.append(d['vol'])
                last_5_amount.append(d['amount'])                   
                if self._is_in_vnpy_db(d['ts_code'], update=False):
                    # 构建vnpy股票数据库数据
                    self._build_db_vnpy(d)                               
                if d['ts_code'][-3:] == '_SH':
                    exchange = Exchange.SSE
                    d['exchange'] = 'SSE'
                else:
                    exchange = Exchange.SZSE                
                    d['exchange'] = 'SZSE'
                bar = BarData(
                    gateway_name='ctp', symbol=d['ts_code'],
                    exchange=exchange,
                    datetime=string_to_datetime(d['trade_date']))
                bar.symbol = d['ts_code']
                bar.volume = d['vol']
                bar.open_price = d['open']
                bar.high_price = d['high']
                bar.low_price = d['low']
                bar.close_price = d['close']
                am.update_bar(bar)
                try:
                    d['ma_5'] = am.sma(5)
                except:
                    traceback.print_exc()                    
                    LOG.error('************************')
                    LOG.error(d['ts_code'])
                    LOG.error(d['trade_date'])
                    LOG.error(bar)
                d['ma_10'] = am.sma(10)
                d['ma_20'] = am.sma(20)
                d['ma_30'] = am.sma(30)
                d['ma_60'] = am.sma(60)
                d['ma_120'] = am.sma(120)
                d['ma_250'] = am.sma(250)
                d['ma_500'] = am.sma(500)
                d['high_5'] = np.max(am.high[-5:])
                d['high_10'] = np.max(am.high[-10:])
                d['high_20'] = np.max(am.high[-20:])
                d['high_30'] = np.max(am.high[-30:])
                d['high_60'] = np.max(am.high[-60:])
                d['high_120'] = np.max(am.high[-120:])
                d['high_250'] = np.max(am.high[-250:])
                d['high_500'] = np.max(am.high[-500:])
                d['low_5'] = np.min(am.low[-5:])
                d['low_10'] = np.min(am.low[-10:])
                d['low_20'] = np.min(am.low[-20:])
                d['low_30'] = np.min(am.low[-30:])
                d['low_60'] = np.min(am.low[-60:])
                d['low_120'] = np.min(am.low[-120:])
                d['low_250'] = np.min(am.low[-250:])
                d['low_500'] = np.min(am.low[-500:])
                flt = {'trade_date': d['trade_date']}
                cl_stock_code.replace_one(flt, d, upsert=True)

    def _update_k_data(self, code, k_data):
        # 注意：所有的数据库数据和列表数据都按照日期的正序排序(从小到大)
        """
        更新股票，股指每日数据（行情，K线，市值等0）
        @:param code  股票(指数)代码                
        @:param k_data  ts中获取的最新df数据
        """        
        if len(k_data) != 0:
            k_data = k_data.sort_values(by='trade_date')            
            cl_stock_code = self.db[code]
            cl_stock_code.create_index([('trade_date', ASCENDING)], unique=True)
            # 更新k线数据
            # 1、新增日K线入库
            # 2、遍历数据库找出最近的500+22(必须保证更新数据操作在22天以内进行)条数据并更新最后的22条的ma和最高 最低价
            for ix, row in k_data.iterrows():
                d = row.to_dict()
                d['ts_code'] = d['ts_code'].replace('.', '_')
                if self._is_in_vnpy_db(d['ts_code'], update=True):
                    # 更新vnpy数据库数据                    
                    self._build_db_vnpy(d)
                flt = {'trade_date': d['trade_date']}
                cl_stock_code.replace_one(flt, d, upsert=True)
            rec = list(cl_stock_code.find({}).sort("trade_date", DESCENDING).limit(522))
            rec.reverse()
            am = ArrayManager(size=600)
            last_5_vol = deque([0.0] * 5)
            last_5_amount = deque([0.0] * 5)
            for d in rec:                
                if 0.0 not in last_5_vol:
                    vol_rate = d['vol'] / (sum(last_5_vol) / 5.0)               
                    amount_rate = d['amount'] / (sum(last_5_amount) / 5.0)   
                    d['vol_rate'] = vol_rate
                    d['amount_rate'] = amount_rate 
                else:
                    d['vol_rate'] = 0.0
                    d['amount_rate'] = 0.0
                last_5_vol.popleft()
                last_5_amount.popleft()
                last_5_vol.append(d['vol'])
                last_5_amount.append(d['amount'])                                       
                if d['ts_code'][-3:] == '_SH':
                    exchange = Exchange.SSE
                    d['exchange'] = 'SSE'
                else:
                    exchange = Exchange.SZSE
                    d['exchange'] = 'SZSE'                
                bar = BarData(
                    gateway_name='ctp', symbol=d['ts_code'],
                    exchange=exchange,
                    datetime=string_to_datetime(d['trade_date']))
                bar.symbol = d['ts_code']
                bar.volume = d['vol']
                bar.open_price = d['open']
                bar.high_price = d['high']
                bar.low_price = d['low']
                bar.close_price = d['close']
                am.update_bar(bar)
                if d['trade_date'] >= self.db_date:
                    d['ma_5'] = am.sma(5)
                    d['ma_10'] = am.sma(10)
                    d['ma_20'] = am.sma(20)
                    d['ma_30'] = am.sma(30)
                    d['ma_60'] = am.sma(60)
                    d['ma_120'] = am.sma(120)
                    d['ma_250'] = am.sma(250)
                    d['ma_500'] = am.sma(500)
                    d['high_5'] = np.max(am.high[-5:])
                    d['high_10'] = np.max(am.high[-10:])
                    d['high_20'] = np.max(am.high[-20:])
                    d['high_30'] = np.max(am.high[-30:])
                    d['high_60'] = np.max(am.high[-60:])
                    d['high_120'] = np.max(am.high[-120:])
                    d['high_250'] = np.max(am.high[-250:])
                    d['high_500'] = np.max(am.high[-500:])
                    d['low_5'] = np.min(am.low[-5:])
                    d['low_10'] = np.min(am.low[-10:])
                    d['low_20'] = np.min(am.low[-20:])
                    d['low_30'] = np.min(am.low[-30:])
                    d['low_60'] = np.min(am.low[-60:])
                    d['low_120'] = np.min(am.low[-120:])
                    d['low_250'] = np.min(am.low[-250:])
                    d['low_500'] = np.min(am.low[-500:])
                    flt = {'trade_date': d['trade_date']}
                    cl_stock_code.replace_one(flt, d, upsert=True)

    def _build_trade_cal(self):
        LOG.info('构建交易日日历数据')
        df_trade_cal = self.pro.trade_cal(
            exchange='', start_date=DATA_BEGIN_DATE, end_date=self.date_now)
        cl_trade_cal = self.db[CL_TRADE_CAL]
        cl_trade_cal.create_index([('cal_date', ASCENDING)], unique=True)
        for ix, row in df_trade_cal.iterrows():
            d = row.to_dict()
            flt = {'cal_date': d['cal_date']}
            cl_trade_cal.replace_one(flt, d, upsert=True)
        LOG.info('构建交易日日历数据完成')

    def build_stock_data(self, update=True):
        self._build_trade_cal()
        self._build_basic()        
        self._build_index(update)
        self._build_top_list()        
        LOG.info('构建股票日K线数据')
        start = time()
        cl_stock_basic = self.db[CL_STOCK_BASIC]
        stock_basic_lst = list(cl_stock_basic.find(
            {}, {'_id': 0}).sort("ts_code", ASCENDING))
        for d in stock_basic_lst:    
            df_stock_k_data = self._get_daily_k_data_from_ts(d['ts_code'].replace('_', '.'), update)       
            df_stock_daily_basic = self._get_daily_basic_from_ts(d['ts_code'].replace('_', '.'), update)   
            if df_stock_k_data.empty is False and df_stock_daily_basic.empty is False:
                del df_stock_daily_basic['ts_code']
                del df_stock_daily_basic['close']
                df_stock_info = pd.merge(df_stock_k_data, df_stock_daily_basic, on='trade_date')
            if d['list_date'] < self.date_now:
                if update is True:
                    self._update_k_data(d['ts_code'], df_stock_info)
                else:
                    self._init_k_data(d['ts_code'], df_stock_info)
        # 数据更新时间
        cl_stock_db_date = self.db[CL_STOCK_DATE]
        db_date = {'db_date': self.date_now}
        flt_date = {'db_date': self.db_date}
        cl_stock_db_date.replace_one(flt_date, db_date, upsert=True)
        end = time()
        cost = (end - start)/3600
        LOG.info('构建股票日K线数据完成，耗时%s小时' % cost)        

    def _build_index(self, update=True):
        LOG.info('构建指数K线数据')        
        for code_db in self.index_lst:
            code = code_db.replace('_', '.')
            df_index = self._get_index_daily_k_data_from_ts(code, update)              
            if df_index.empty is False:
                if update is True:            
                    self._update_k_data(code_db, df_index)
                else:
                    self._init_k_data(code_db, df_index)
        LOG.info('构建指数K线数据完成')

    def _build_top_list(self):
        # 构建龙虎榜数据                
        LOG.info('构建龙虎榜数据')             
        date_top_list = self.get_pre_trade_date(self.db_date) if DATA_BEGIN_DATE != self.db_date else self.db_date  # 用前一天和当天的数据更新龙虎榜（防止当天更新db时，龙虎榜tushare接口数据还未生成）
        begin_date = '20050101' if date_top_list < '20050101' else date_top_list  # 龙虎榜数据只有2005年之后的数据
        trade_lst = self.get_trade_cal(begin_date)
        for item_date in trade_lst:
            df_top_list = self.pro.top_list(trade_date=item_date)
            sleep(1)
            if df_top_list.size != 0:
                for ix_top_list, row_top_list in df_top_list.iterrows():
                    d_top_list = row_top_list.to_dict()
                    d_top_list['ts_code'] = d_top_list['ts_code'].replace('.', '_')
                    cl_stk_top_list = self.db[CL_STK_TOP_LIST]
                    flt_top_list = {'trade_date': item_date, 'ts_code': d_top_list['ts_code']}
                    cl_stk_top_list.replace_one(flt_top_list, d_top_list, upsert=True)  
        LOG.info('构建龙虎榜数据完成')

    def _build_basic(self):
        LOG.info('构建股票基础信息')
        data = self.pro.stock_basic(
            exchange='', list_status='L',
            fields='ts_code,symbol,name,area,industry,market,list_date')
        cl_stock_basic = self.db[CL_STOCK_BASIC]
        cl_stock_basic.create_index([('ts_code', ASCENDING)], unique=True)
        for ix, row in data.iterrows():
            d = row.to_dict()
            d['ts_code'] = d['ts_code'].replace('.', '_')
            flt = {'ts_code': d['ts_code']}
            cl_stock_basic.replace_one(flt, d, upsert=True)
        LOG.info('构建股票基础信息完成')

    def _get_daily_basic_from_ts(self, code, update=True):        
        start_date = DATA_BEGIN_DATE
        if update is True:
            start_date = self.db_date
        count = 0        
        while(True):
            try:
                df_daily_basic = self.pro.daily_basic(
                    ts_code=code, start_date=start_date, end_date=self.date_now)     
                if df_daily_basic is not None:
                    break
                else:                    
                    LOG.info('(%s)调用tushare pro.daily_basic失败，空数据' % (code))
                    break
            except:
                count += 1
                LOG.info('(%s)调用tushare pro.daily_basic失败，重试次数：%s' % (code, count))
                if count > self.count_max_retry:
                    break
                sleep(self.second_sleep)  
        if df_daily_basic is None:
            df_daily_basic = pd.DataFrame()                
            df_daily_basic.fillna(0.0, inplace=True)
        return df_daily_basic  

    def _get_daily_k_data_from_ts(self, code, update=True):        
        start_date = DATA_BEGIN_DATE
        if update is True:
            start_date = self.db_date
        count = 0        
        while(True):
            try:
                df_k_data = ts.pro_bar(
                    ts_code=code, adj='qfq', start_date=start_date,
                    end_date=self.date_now)  
                if df_k_data is not None:
                    break
                else:                    
                    LOG.info('(%s)调用tushare ts.pro_bar失败，空数据' % (code))
                    break
            except:
                count += 1
                LOG.info('(%s)调用tushare ts.pro_bar失败，重试次数：%s' % (code, count))
                if count > self.count_max_retry:
                    break
                sleep(self.second_sleep)
        if df_k_data is None:
            df_k_data = pd.DataFrame()
        df_k_data.fillna(0.0, inplace=True)
        return df_k_data

    def _get_index_daily_k_data_from_ts(self, code, update=True):                
        start_date = DATA_BEGIN_DATE
        if update is True:
            start_date = self.db_date
        count = 0        
        while(True):
            try:
                df_index_k_data = self.pro.index_daily(
                    ts_code=code, start_date=self.db_date,
                    end_date=self.date_now)   
                if df_index_k_data is not None:
                    break
                else:                    
                    LOG.info('(%s)调用tushare pro.index_daily失败，空数据' %(code))
                    break
            except:
                count += 1
                LOG.info('(%s)调用tushare pro.index_daily失败，重试次数：%s' % (code, count))
                if count > self.count_max_retry:
                    break
                sleep(self.second_sleep)    
        if df_index_k_data is None:
            df_index_k_data = pd.DataFrame()            
        df_index_k_data.fillna(0.0, inplace=True)
        return df_index_k_data

    def get_stock_price_info(self, code, date):        
        cl_stock_code = self.db[code]
        stock_price_info = cl_stock_code.find_one(
            {'trade_date': date}, {'_id': 0})
        return stock_price_info

    def get_stock_price_info_last(self, code):        
        # 获得某只股票最后一天的股价（考虑停牌因素）
        cl_stock_code = self.db[code]
        stock_price_info = cl_stock_code.find_one(sort=[('_id', -1)])
        return stock_price_info

    def get_stock_price_lst(self, code, begin_date, end_date):        
        cl_stock_code = self.db[code]
        ret_lst = list()
        stock_price_lst = list(cl_stock_code.find(
            {'trade_date': {"$gte": begin_date, '$lte': end_date}}, {'_id': 0}).sort("trade_date"))
        for item in stock_price_lst:
            ret_lst.append(item)
        return ret_lst

    def get_stock_basic_info(self, code):            
        cl_stock_basic = self.db[CL_STOCK_BASIC]
        stock_basic_info = cl_stock_basic.find_one(
            {'ts_code': code}, {'_id': 0})
        return stock_basic_info

    def get_trade_cal(self, begin_date, end_date=None):
        cl_cal = self.db[CL_TRADE_CAL]
        if end_date is None:
            trade_cal = list(cl_cal.find(
                {'cal_date': {"$gte": begin_date}, 'is_open': 1},
                {'_id': 0}).sort("cal_date"))
        else:
            trade_cal = list(cl_cal.find(
                {'cal_date': {"$gte": begin_date, '$lte': end_date},
                    'is_open': 1}, {'_id': 0}).sort("cal_date"))
        trade_cal_lst = list()
        for item in trade_cal:
            trade_cal_lst.append(item['cal_date'])
        return trade_cal_lst

    def get_next_trade_date(self, trade_date, n=1):
        # 获取下N个交易日日期
        cl_cal = self.db[CL_TRADE_CAL]
        trade_cal = list(cl_cal.find(
            {'cal_date': {"$gt": trade_date}, 'is_open': 1},
            {'_id': 0}).sort("cal_date"))
        return list(trade_cal)[n-1]['cal_date']

    def get_pre_trade_date(self, trade_date, n=1):
        # 获取上N个交易日日期
        cl_cal = self.db[CL_TRADE_CAL]
        trade_cal = list(cl_cal.find(
            {'cal_date': {"$lt": trade_date}, 'is_open': 1},
            {'_id': 0}).sort("cal_date", DESCENDING))
        return list(trade_cal)[n-1]['cal_date']

    def get_pre_n_trade_date(self, trade_date, days):
        # 获取上N个交易日列表（若当前日期是交易日，则保留一并返回）
        cl_cal = self.db[CL_TRADE_CAL]
        trade_cal = list(cl_cal.find(
            {'cal_date': {"$lte": trade_date}, 'is_open': 1},
            {'_id': 0}).sort("cal_date", DESCENDING).limit(days))
        ret_lst = list()
        for item in trade_cal:
            ret_lst.append(item['cal_date'])
        return ret_lst

    def get_stock_top_lst(self, date):
        cl_stock_top_list = self.db[CL_STK_TOP_LIST]
        top_list = list(cl_stock_top_list.find(
            {'trade_date': date}, {'_id': 0}))
        stock_top_list = list()
        for item in top_list:
            stock_top_list.append(item)       
        return stock_top_list

    def daily_stock_pool_in_db(self, code_lst, date):
        LOG.info('每日股票池数据入库')
        cl_stk_pool_daily = self.db[CL_STK_POOL_DAILY]
        cl_stk_pool_daily.create_index([('date', ASCENDING), ('ts_code', ASCENDING)])
        for code in code_lst:
            d = {'date_buy': date, 'ts_code': code, 'date_sell': None}
            flt = {'date_buy': date, 'ts_code': code}
            cl_stk_pool_daily.replace_one(flt, d, upsert=True)
        LOG.info('每日股票池数据入库完成')

    def cur_stock_pool_in_db(self, code_lst, date):
        LOG.info('当前股票池数据入库')
        cl_stk_pool_cur = self.db[CL_STK_POOL_CUR]
        cl_stk_pool_cur.create_index([('date', ASCENDING), ('ts_code', ASCENDING)])
        lst_code_pre = self.get_cur_stock_pool_code_lst(self.get_pre_trade_date(date))
        lst_union = list(set(lst_code_pre).union(set(code_lst)))
        for code in lst_union:
            d = {'date': date, 'ts_code': code}
            flt = {'date': date, 'ts_code': code}
            cl_stk_pool_cur.replace_one(flt, d, upsert=True)
        LOG.info('当前股票池数据入库完成')
    
    def get_cur_stock_pool(self, date):
        cl_stk_pool_cur = self.db[CL_STK_POOL_CUR]
        ret = list(cl_stk_pool_cur.find(
            {'date': date}, {'_id': 0}))
        lst_info = list()
        for item in ret:
            lst_info.append(item)       
        return lst_info

    def get_cur_stock_pool_code_lst(self, date):
        cl_stk_pool_cur = self.db[CL_STK_POOL_CUR]
        ret = list(cl_stk_pool_cur.find(
            {'date': date}, {'_id': 0}))
        lst_code = list()
        for item in ret:
            lst_code.append(item['ts_code'])       
        return lst_code

    def del_cur_stock_pool(self, lst_code, date):
        cl_stk_pool_cur = self.db[CL_STK_POOL_CUR]
        for code in lst_code:
            del_query = {"ts_code": code, 'date':date}
            cl_stk_pool_cur.delete_one(del_query)

    def set_daily_stock_pool(self, lst_code, date):
        cl_stk_pool_daily = self.db[CL_STK_POOL_DAILY]
        for code in lst_code:
            set_query = {"ts_code": code, "date_sell": None}
            cl_stk_pool_daily.update_one(set_query,{"$set":{'date_sell':date}})

    def get_cur_stock_pool_date_lst(self):
        cl_stk_pool_cur = self.db[CL_STK_POOL_CUR]
        ret = list(cl_stk_pool_cur.find().sort("date", ASCENDING))
        lst_date = list()
        for item in ret:
            if item['date'] not in lst_date:
                lst_date.append(item['date'])       
        return lst_date

    def get_curve_date(self):
        cl_stk_pool_cur = self.db[CL_STK_POOL_CUR]
        ret = cl_stk_pool_cur.find_one(sort=[('_id', 1)])
        date_end = self.get_trade_date(self.db_date)
        if ret is not None:
            return ret['date'], date_end
        else:
            return date_end, date_end

    def get_daily_stock_pool(self, date):
        cl_stk_pool_daily = self.db[CL_STK_POOL_DAILY]
        ret = list(cl_stk_pool_daily.find({'date_buy': date}, {'_id': 0}))     
        return ret
    
    def get_daily_stock(self, code):
        cl_stk_pool_daily = self.db[CL_STK_POOL_DAILY]
        ret = cl_stk_pool_daily.find_one({'ts_code': code}, {'_id': 0})
        return ret

if __name__ == "__main__":
    ds_tushare = DataServiceTushare()
    ds_tushare.build_stock_data(update=False)

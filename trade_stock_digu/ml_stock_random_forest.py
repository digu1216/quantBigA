from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import recall_score, confusion_matrix, precision_score
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
from vnpy.trade_stock_digu.data_service import DataServiceTushare, LOG

ds_tushare = DataServiceTushare()    

def get_ml_X(close, ma5, ma10, ma20, ma30, ma60, ma120):
    arr = np.array([close-ma5, close-ma10, close-ma20, close-ma30, close-ma60, close-ma120])
    return arr.reshape(-1, 1).T

def get_ml_X_db(code, date):
    k_data = ds_tushare.get_stock_price_info(code, date)
    arr = np.array([k_data['close']-k_data['ma_5'], k_data['close']-k_data['ma_10'], k_data['close']-k_data['ma_20'], k_data['close']-k_data['ma_30'], \
        k_data['close']-k_data['ma_60'], k_data['close']-k_data['ma_120']])
    return arr.reshape(-1, 1).T

lst_stock = ds_tushare.get_stock_list()   
lst_ma5 = list()
lst_ma10 = list()
lst_ma20 = list()
lst_ma30 = list()
lst_ma60 = list()
lst_ma120 = list()
lst_close = list()
lst_pct_chg = list()
for item_stock in lst_stock:
# for item_stock in ['000001_SZ', '000002_SZ', '000813_SZ']:
    lst_price_code = ds_tushare.get_stock_price_lst(item_stock, '20190101', '20190701')
    # lst_price_code = ds_tushare.get_stock_price_lst(item_stock, '20200805', '20200808')
    if len(lst_price_code) == 0:
        continue
    lst_pct_chg_code = list()
    for item_price in lst_price_code:
        lst_ma5.append(item_price['ma_5'])
        lst_ma10.append(item_price['ma_10'])
        lst_ma20.append(item_price['ma_20'])
        lst_ma30.append(item_price['ma_30'])
        lst_ma60.append(item_price['ma_60'])
        lst_ma120.append(item_price['ma_120'])
        lst_close.append(item_price['close'])
        lst_pct_chg_code.append(item_price['pct_chg'])   
    arr_pct_chg_code = np.array(lst_pct_chg_code)
    arr_pct_chg_code = np.roll(arr_pct_chg_code, -1)
    arr_pct_chg_code = (arr_pct_chg_code > 0.0).astype(int)
    lst_ma5.pop()
    lst_ma10.pop()
    lst_ma20.pop()
    lst_ma30.pop()
    lst_ma60.pop()
    lst_ma120.pop()
    lst_close.pop()
    try:
        arr_pct_chg_code = np.delete(arr_pct_chg_code, -1)
    except:
        LOG.info(arr_pct_chg_code)
    lst_pct_chg += list(arr_pct_chg_code)        
arr_ma5 = np.array(lst_ma5)
arr_ma10 = np.array(lst_ma10)
arr_ma20 = np.array(lst_ma20)
arr_ma30 = np.array(lst_ma30)
arr_ma60 = np.array(lst_ma60)
arr_ma120 = np.array(lst_ma120)
arr_close = np.array(lst_close)    
arr_ma5_sub_close = (arr_close - arr_ma5)*100/arr_close
arr_ma10_sub_close = (arr_close - arr_ma10)*100/arr_close
arr_ma20_sub_close = (arr_close - arr_ma20)*100/arr_close
arr_ma30_sub_close = (arr_close - arr_ma30)*100/arr_close
arr_ma60_sub_close = (arr_close - arr_ma60)*100/arr_close
arr_ma120_sub_close = (arr_close - arr_ma120)*100/arr_close
arr_pct_chg = np.array(lst_pct_chg)
X = np.vstack((arr_ma5_sub_close, arr_ma10_sub_close, arr_ma20_sub_close, arr_ma30_sub_close, arr_ma60_sub_close, arr_ma120_sub_close))
y = arr_pct_chg
y_close = arr_close

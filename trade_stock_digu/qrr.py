import numpy as np
import pymongo
from logger import Logger
import tushare as ts
import os
from data_service import DataServiceTushare


def get_stock_list(mydb):
    lst_code = list()
    cl_stock_basic = mydb['stock_basic']
    stock_basic_lst = cl_stock_basic.find(
        {}, {'_id': 0}).sort("ts_code", pymongo.ASCENDING)
    stock_basic_lst1 = list(stock_basic_lst)
    for d in stock_basic_lst1:  
        if '.' in d['ts_code']:
            continue
        lst_code.append(d['ts_code'])
    return lst_code

if __name__ == "__main__":
    ts.set_token('4c1d16a895e4c954adc8d2a436f2b21dd4ccc514f0c5a192edaa953b')
    pro = ts.pro_api()
    myclient = pymongo.MongoClient("mongodb://124.70.183.208:27017/", username='root', password='qiuqiu78')
    mydb = myclient["stock_digu"]
    get_stock_list(mydb)
    # df_trade_cal = pro.trade_cal(exchange='', start_date='20200601', end_date='20200701')
    # cl_trade_cal = mydb['trade_cal']
    # cl_trade_cal.create_index([('cal_date', pymongo.ASCENDING)], unique=True)
    # for ix, row in df_trade_cal.iterrows():
    #     d = row.to_dict()
    #     flt = {'cal_date': d['cal_date']}
    #     cl_trade_cal.replace_one(flt, d, upsert=True)

    # db = pymongo.MongoClient("mongodb://localhost:27017/")
    # stock = db['stock_digu']
    # col_index_data = stock['000001.SH']
    # logger = Logger().getlog()
    # ds_tushare = DataServiceTushare()
    # lst_trade_date = ds_tushare.getTradeCal('19891201')
    # vol_lst = list()
    # for item_date in lst_trade_date:
    #     if len(vol_lst) != 5:
    #         data = col_index_data.find_one({"trade_date": item_date})            
    #         data['qrr'] = 0
    #         col_index_data.update_one({"trade_date": item_date}, {"$set": data})
    #         vol_lst.append(data['vol'])
    #     else:                                 
    #         data = col_index_data.find_one({"trade_date": item_date})            
    #         data['qrr'] = data['vol']/(sum(vol_lst)/5)            
    #         col_index_data.update_one({"trade_date": item_date}, {"$set": data})
    #         vol_lst.append(data['vol'])
    #         vol_lst.pop(0)

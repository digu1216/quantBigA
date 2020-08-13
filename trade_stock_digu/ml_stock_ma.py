from data_service import DataServiceTushare
from logger import Logger
import tushare as ts
from time import time, sleep
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import recall_score, confusion_matrix, precision_score
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import BaggingClassifier
import numpy as np
import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
        
if __name__ == "__main__":
    logger = Logger().getlog()
    ds_tushare = DataServiceTushare()    
    # lst_index_price = ds_tushare.getStockPriceLst('000001_SH', '20000301')
    lst_index_price = ds_tushare.getStockPriceLst('399001_SZ', '20050301')
    # data_index = np.zeros(shape=(len(lst_index_price), 4))    
    count_X = lst_index_price.count()
    data_index = np.zeros(shape=(count_X, 4))    
    lst_index_price.sort("trade_date", DESCENDING)
    last_index_val = 0.0
    idx = 0
    for item in lst_index_price:
        ma5 = item['close'] - item['ma_5']
        ma20 = item['close'] - item['ma_20']        
        vol_rate = item['vol_rate']
        result = 1 if item['close'] <= last_index_val else 0
        data_index[idx] = [ma5, ma20, vol_rate, result]        
        idx += 1
        last_index_val = item['close']
    logger.info(data_index)
    X_train, X_test, y_train, y_test = train_test_split(data_index[:, :-1], data_index[:, -1], test_size=0.3)    
    pipe = Pipeline([('standard_scaler', StandardScaler()), 
                    ('polynomial_features', PolynomialFeatures(degree=2)), 
                    ('logistic_reg', LogisticRegressionCV(cv=10, class_weight={0:0.55, 1:0.45}, n_jobs=-1))])        
    # pipe = BaggingClassifier(pipe, n_estimators=200, max_samples=0.8, bootstrap=True, n_jobs=-1, oob_score=True)
    pipe.fit(X_train, y_train)
    print(pipe.score(X_test, y_test))
    y_predict = pipe.predict(X_test)
    print(np.sum(y_predict))
    print(len(y_predict))
    # print(y_predict)
    # print(y_test)

    print(confusion_matrix(y_test, y_predict))
    print(precision_score(y_test, y_predict))
    print(pipe.predict(np.array([-91, -225, 0.86]).reshape(1, -1)))    
    # pipe.predict([1, 1, 1])


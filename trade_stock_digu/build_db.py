import pymongo
from data_service import DataServiceTushare
from vnpy.trader.constant import Exchange


if __name__ == "__main__":
    ds_tushare = DataServiceTushare()
    ds_tushare.build_stock_data(update=True)
    # ds_tushare._build_top_list()
    # zz500相关指标入库
    # ds_tushare.zz500_stock_pool_in_db(['2018', '2019', '2020'])
    # ds_tushare.zz500_index_in_db('20180101', '20200818')`` 
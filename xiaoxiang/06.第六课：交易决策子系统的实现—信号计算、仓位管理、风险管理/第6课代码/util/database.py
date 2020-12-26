from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne

DB_CONN = MongoClient('mongodb://127.0.0.1:27017')['my_quant']

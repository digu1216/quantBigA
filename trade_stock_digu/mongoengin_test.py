from mongoengine import *
import datetime
connect('stock_vnpy', host='localhost', port=27017)

# class Users(Document):
#     name = StringField(required=True, max_length=200)
#     age = IntField(required=True)
# users = Users.objects.all()
# print(len(users))
# for u in users:
#     print("name:",u.name,",age:",u.age)

class DbBarData(Document):
    symbol: str = StringField()
    exchange: str = StringField()
    datetime: datetime = DateTimeField()
    interval: str = StringField()

    # meta = {'collection': 'DbBarData'}
    volume: float = FloatField()
    open_interest: float = FloatField()
    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()
    meta = {
        "indexes": [
            {
                "fields": ("symbol", "exchange", "interval", "datetime"),
                "unique": True,
            }
        ]
    }


# users = DbBarData.objects.all()
# users = DbBarData.objects(
#     symbol='000001.SZ',
#     exchange='SZSE',
#     interval='d',
#     datetime__gte='20190103',
#     datetime__lte='20190131',
# )
# users = DbBarData.objects(
#     symbol='000001.SZ',
#     exchange='SZSE',
#     interval='d'
# )
# users = DbBarData.objects(symbol='000001_SH', exchange='SZSE', interval='d', datetime__gte='20190103', datetime__lte='20190131',)            
start = datetime.datetime(2019, 1, 1)
# end = datetime.datetime(2019, 1, 31)
progress_delta = datetime.timedelta(days=30)
end = start +progress_delta
start = start
end = start + progress_delta
progress = 0
users = DbBarData.objects(symbol='000001_SH', exchange='SZSE', interval='d', datetime__gte=start, datetime__lte=end,)            
print(len(users))
for u in users:
    print("symbol:", u.symbol, ",datetime:", u.datetime, )


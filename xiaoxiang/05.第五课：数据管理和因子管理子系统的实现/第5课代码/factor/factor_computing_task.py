#  -*- coding: utf-8 -*-

from factor import *
from datetime import datetime
import schedule, time

"""
因子的计算任务，主要完成每天收盘后的因子计算任务
"""


def computing():
    weekday = datetime.now().strftime('%w')

    if weekday == 0 or weekday == 6:
        return

    # 所有的因子实例
    factors = [
        PEFactor(),
        MktCapFactor()
    ]

    now = datetime.now().strftime('%Y-%m-%d')
    for factor in factors:
        print('开始计算因子：%s, 日期：%s' % (factor.name(), now), flush=True)
        factor.compute(begin_date=now, end_date=now)
        print('结束计算因子：%s, 日期：%s' % (factor.name(), now), flush=True)


if __name__ == '__main__':
    # 每天下午四点定时运行
    schedule.every().day.at('16:00').do(computing)
    while True:
        schedule.run_pending()
        time.sleep(10)
        computing()


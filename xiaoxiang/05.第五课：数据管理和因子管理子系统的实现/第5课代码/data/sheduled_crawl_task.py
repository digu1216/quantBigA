#  -*- coding: utf-8 -*-

import schedule
from data.daily_crawler import DailyCrawler
import time
from datetime import datetime

"""
每天下午15:30执行抓取，只有周一到周五才真正执行抓取任务
"""

def crawl_daily():
    dc = DailyCrawler()
    now_date = datetime.now()
    weekday = now_date.strftime('%w')
    if 0 < weekday < 6:
        now = now_date.strftime('%Y-%m-%d')
        dc.crawl_index(begin_date=now, end_date=now)
        dc.crawl(begin_date=now, end_date=now)


if __name__ == '__main__':
    schedule.every().day.at("15:30").do(crawl_daily)
    while True:
        schedule.run_pending()
        time.sleep(10)

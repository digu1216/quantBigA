# -*- coding: utf-8 -*-

from datetime import datetime

from data.daily_crawler import DailyCrawler
from data.finance_report_crawler import FinanceReportCrawler
from data.fixing.daily_fixing import DailyFixing
from strategy.strategy_module import Strategy
from factor.factor_module import FactorModule

# 获取当前日期
current_date = datetime.now().strftime('%Y-%m-%d')


def crawl_data():
    """
    抓取数据
    """
    dc = DailyCrawler()
    dc.crawl_index(begin_date=current_date, end_date=current_date)
    dc.crawl(begin_date=current_date, end_date=current_date)

    fc = FinanceReportCrawler()
    fc.crawl_finance_report()
    fc.crawl_finance_summary()


def fixing_data():
    """
    修复数据
    """
    df = DailyFixing()
    # 计算复权因子和前收
    df.fill_au_factor_pre_close(current_date, current_date)
    # 计算涨停和跌停
    df.fill_high_limit_low_limit(current_date, current_date)
    # 填充缺失的K线
    df.fill_daily_k_at_suspension_days(current_date, current_date)
    # 填充交易状态
    df.fill_is_trading_between(current_date, current_date)


def compute_factor():
    """
    计算所有因子
    """
    fc = FactorModule()
    fc.compute()


def get_today_candidates():
    """
    通过回测获得今天的备选股
    """
    strategy = Strategy('low_pe_strategy')
    strategy.backtest()


if __name__ == '__main__':
    crawl_data()
    fixing_data()
    compute_factor()
    get_today_candidates()


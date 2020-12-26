#  -*- coding: utf-8 -*-

from pymongo import UpdateOne
from base_factor import BaseFactor
from data.finance_report_crawler import FinanceReportCrawler
from data.data_module import DataModule

"""
实现市盈率因子的计算和保存
"""


class PEFactor(BaseFactor):
    def __init__(self):
        BaseFactor.__init__(self, name='pe')

    def compute(self, begin_date, end_date):
        """
        计算指定时间段内所有股票的该因子的值，并保存到数据库中
        :param begin_date:  开始时间
        :param end_date: 结束时间
        """
        dm = DataModule()
        frc = FinanceReportCrawler()

        code_report_dict = frc.get_code_reports()

        codes = set(code_report_dict.keys())
        for code in codes:
            dailies = dm.get_k_data(code, autype=None, begin_date=begin_date, end_date=end_date)
            # 如果没有合适的数据
            if dailies.index.size == 0:
                continue

            # 业绩报告列表
            reports = code_report_dict[code]

            dailies.set_index(['date'], inplace=True)

            update_requests = []
            for current_date in dailies.index:
                # 用来保存最后一个公告日期小于等于当前日期的财报
                last_report = None
                for report in reports:
                    announced_date = report['announced_date']
                    # 如果公告日期大于当前调整日，则结束循环
                    if announced_date > current_date:
                        break

                    last_report = report

                # 如果找到了正确时间范围的年报， 则计算PE
                if last_report is not None:
                    pe = dailies.loc[current_date]['close'] / last_report['eps']
                    pe = round(pe, 3)

                    print('%s, %s, %s, eps: %5.2f, pe: %6.2f' %
                          (code, current_date, last_report['announced_date'], last_report['eps'], pe),
                          flush=True)

                    update_requests.append(
                        UpdateOne(
                            {'code': code, 'date': current_date},
                            {'$set': {'code': code, 'date': current_date, 'pe': pe}}, upsert=True))

            if len(update_requests) > 0:
                save_result = self.collection.bulk_write(update_requests, ordered=False)
                print('股票代码: %s, 因子: %s, 插入：%4d, 更新: %4d' %
                      (code, self.name, save_result.upserted_count, save_result.modified_count), flush=True)


if __name__ == '__main__':
    # 执行因子的提取任务
    PEFactor().compute('2014-01-01', '2014-12-31')

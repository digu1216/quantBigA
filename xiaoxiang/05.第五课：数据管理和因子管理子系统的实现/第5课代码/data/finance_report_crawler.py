#  -*- coding: utf-8 -*-

from pymongo import UpdateOne
import tushare as ts
from util.database import DB_CONN
from util.stock_util import get_all_codes
import urllib3
import json

"""
从东财获取财务数据，保存到数据库中
"""


class FinanceReportCrawler:
    def __init__(self):
        self.db = DB_CONN

    def crawl_finance_report(self):
        """
        从东方财富网站抓取三张财务报表
        :return:
        """
        # 先获取所有的股票列表
        codes = get_all_codes()

        # 创建连接池
        conn_pool = urllib3.PoolManager()

        # 抓取的网址，两个替换参数 {1} - 财报类型 {2} - 股票代码
        url = 'http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get?' \
              'type={1}&token=70f12f2f4f091e459a279469fe49eca5&' \
              'st=reportdate&sr=-1&p=1&ps=500&filter=(scode=%27{2}%27)' \
              '&js={%22pages%22:(tp),%22data%22:%20(x)}&rt=51044775#'

        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'

        # 对应的类型，分别资产负债表、现金流量表和利润表
        report_types = ['CWBB_ZCFZB', 'CWBB_XJLLB', 'CWBB_LRB']

        for code in codes:
            for report_type in report_types:
                print('开始抓取财报数据，股票：%s，财报类型：%s' % (code, report_type), flush=True)
                response = conn_pool.request('GET',
                                             url.replace('{1}', report_type).replace('{2}', code),
                                             headers={
                                                 'User-Agent': user_agent})

                # 解析抓取结果
                result = json.loads(response.data.decode('UTF-8'), 'UTF-8')

                reports = result['data']

                update_requests = []
                for report in reports:
                    # 更新字段端
                    try:
                        report.update({
                            # 公告日和报告期只保留年月日
                            'announced_date': report['noticedate'][0:10],
                            'report_date': report['reportdate'][0:10],
                            # 股票名称和股票代码的字段名和系统设计保持一致
                            'code': code,
                            'name': report['sname']
                        })

                        update_requests.append(
                            UpdateOne(
                                {
                                    'code': code,
                                    'report_date': report['report_date'],
                                    'announced_date': report['announced_date']},
                                {'$set': report},
                                upsert=True))
                    except:
                        print('解析出错，股票：%s 财报类型：%s' % (code, report_type))

                if len(update_requests) > 0:
                    update_result = self.db[report_type].bulk_write(update_requests, ordered=False)
                    print('股票 %s, 财报类型：%s，更新： %4d, 新增： %4d' %
                          (code, report_type, update_result.modified_count, update_result.upserted_count))

    def get_code_reports(self):
        """
        获取回测周期内的年度财报数据，组合成一个dict数据结构，key是股票代码，
        value是一个按照报告发布日期排序的列表，列表内的元素也是一个dict
        {'eps': 每股收益, 'announced_date': 公告日期}
        """

        # 这个tuple包含了三个元素，前两个分别是用来获取年度财报时的参数年份和季度，
        # 后面是一个发布年度财报的年份，因为一般情况下发布财报都是在第二年的4月底之前，
        # 所以这个年份比财报的年份晚一年
        report_date_tuples = [(2011, 4, 2012), (2012, 4, 2013), (2013, 4, 2014), (2014, 4, 2015)]

        # 要返回的数据结构
        code_report_dict = dict()

        # 循环获取所有指定报告期的数据
        for report_date_tuple in report_date_tuples:
            # 从Tushare获取年报数据
            df_reports = ts.get_report_data(report_date_tuple[0], report_date_tuple[1])

            # 只需要股票代码、每股收益和公告日期三个字段
            codes = df_reports['code']
            epses = df_reports['eps']
            announced_dates = df_reports['report_date']

            # 这个是报告发布时的年度
            announced_year = str(report_date_tuple[2])

            # 拿到已经缓存的股票代码集合
            codes_of_cached_reports = set(code_report_dict.keys())

            # 循环获取所有数据
            for report_index in df_reports.index:
                code = codes[report_index]
                eps = epses[report_index]
                announced_date = announced_dates[report_index]

                print('%s %5.2f %d %s' % (code, eps, report_date_tuple[0], announced_date), flush=True)

                # 如果eps是非数字，或者发布日期的月份超过了4月，就不作处理，因为股票在上市前
                # 也会发布财报，那么这个财报的发布日期可能不是定期报告所规定的时间范围，
                # 那么对这种上市之前的数据暂时不予处理
                if str(eps) != 'nan' and int(announced_date[0:2]) <= 4:
                    # 组合成完整的公告年月日
                    announced_date = announced_year + '-' + announced_date
                    print('%s %5.2f %s' % (code, eps, announced_date), flush=True)

                    # 如果当前股票不在需要返回的数据结构中，则添加到其中
                    if code not in codes_of_cached_reports:
                        code_report_dict[code] = []
                        codes_of_cached_reports.add(code)

                    # 将eps和公告日期添加到列表中
                    code_report_dict[code].append({'eps': eps, 'announced_date': announced_date})

        # 返回获取的数据
        return code_report_dict

if __name__ == '__main__':
    FinanceReportCrawler().crawl_finance_report()


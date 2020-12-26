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
                result = json.loads(response.data.decode('UTF-8'))

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

    def crawl_finance_summary(self):
        """
        抓取财务摘要信息
        """
        # 先获取所有的股票列表
        codes = get_all_codes()

        # 创建连接池
        conn_pool = urllib3.PoolManager()

        url = 'http://dcfm.eastmoney.com//em_mutisvcexpandinterface/api/js/get?' \
              'type=YJBB20_YJBB&token=70f12f2f4f091e459a279469fe49eca5&st=reportdate&sr=-1' \
              '&filter=(scode={0})&p={page}&ps={pageSize}&js={"pages":(tp),"data":%20(x)}'

        cookie = 'emstat_bc_emcount=21446959091031597218; pgv_pvi=8471522926; st_pvi=95785429701209; _' \
                 'ga=GA1.2.700565749.1496634081; Hm_lvt_557fb74c38569c2da66471446bbaea3f=1499912514; _' \
                 'qddaz=QD.g2d11t.ydltyz.j61eq2em; ct=YTJNd7eYzkV_0WPJBmEs-FB0AGfyz7Z9G-Z1' \
                 'HbsPTxwV9TxpuvcB2fM1xoG5PhqgTI5KlrQZKFZReg3g3ltIwo8fMyzHhEzVjltYwjAigMTdZvdEHnU7QW2' \
                 'O-7u0dCkmtsFOBI4vbW1ELaZ9iUS9qPFAtIkL9M8GJTj8liRUgJY; ut=FobyicMgeV4t8TZ4Md7eLYClhCqi0w' \
                 'XPSu3ZyZ4h4Q8vWCyLMuChP80vhfidM2802fUv5AJEgl9ddudfTRqObGqQ47QN4oJS5hoWxdsHCY6lvJEeXDTNKWsdP' \
                 'hsfzg0i-ukMlT11XfPMIsBG9DzhW3xDAR3flNcqE5csB2rT3cfVPchlihFWHk-f3F1-lSsBjduc9_Ws_jjJEsi46' \
                 'xEai2mCVGd_O41yhPU3MWXl2_2QJU_ILgnzruwDvjeoQRtf8COKmiJCtE6hhy04RvSjmbzBVeZXqUhd; pi=42660' \
                 '45025913572%3bb4266045025913572%3b%e8%82%a1%e5%8f%8bZTLUIt%3bo97rhoY6b5AbF5jETm3t72EC9RGp' \
                 'IhrLsDj7myRgKyWSJmYrdl1WGaA9dMGpydaY4AptuI0ZgKDj6PCir1z%2bY1if6G0iITYI4Rv%2bPXy6H%2f4u7Rg' \
                 'iD%2f2hCYAGnfitkw9HQXnqBETzflfUGnvGJysWiVyPlOp%2fZh4Hfe6NqssBxCqJUrGOCM06F7feAXC6Vapy%2fse' \
                 '0PT2a%3bVMsSChhqtxvtvecfLmv9FInLBANRLHpns2d%2bJGh272rIXhkWm%2bNK%2bXxkRKL2a0EgScqdtlcYN1QC' \
                 'hVUWT7gmrH9py08FBPk2n5EQA9m9Zt5o2m%2bMuQhON2f66vlq%2bGk3Z66s%2brgCQhSPqoUPxluzSwBk7I9NNA%3d' \
                 '%3d; uidal=4266045025913572%e8%82%a1%e5%8f%8bZTLUIt; vtpst=|; em_hq_fls=old; emstat_ss_emco' \
                 'unt=5_1505917025_902015979; st_si=83202211429810; em-quote-version=topspeed; showpr3guide=1; ' \
                 'qgqp_b_id=367cbd71ad5c205f172815cdab571db9; hvlist=a-000858-2~a-000651-2~a-600000-1~a-300017-2' \
                 '~a-600020-1~a-600005-1~a-600004-1~a-162605-2~a-159901-2~a-600015-1~a-002364-2~a-600128-1~a-0023' \
                 '57-2~a-002363-2~a-601106-1; HAList=a-sz-300059-%u4E1C%u65B9%u8D22%u5BCC%2Ca-sz-002607-%u4E9A%u590' \
                 'F%u6C7D%u8F66%2Ca-sh-603259-%u836F%u660E%u5EB7%u5FB7%2Ca-sz-000858-%u4E94%u7CAE%u6DB2%2Ca-sh-600165' \
                 '-%u65B0%u65E5%u6052%u529B%2Ca-sh-603013-%u4E9A%u666E%u80A1%u4EFD%2Ca-sz-002841-%u89C6%u6E90%u80A1%u4' \
                 'EFD%2Cf-0-399300-%u6CAA%u6DF1300%2Cf-0-000300-%u6CAA%u6DF1300%2Ca-sz-000651-%u683C%u529B%u7535%u5668%' \
                 '2Ca-sz-000735-%u7F57%u725B%u5C71'
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/66.0.3359.139 Safari/537.36'

        for code in codes:
            response = conn_pool.request('GET', url.replace('{0}', code),
                                         headers={
                                             'Cookie': cookie,
                                             'User-Agent': user_agent})

            # 解析抓取结果
            result = json.loads(response.data.decode('UTF-8'))

            reports = result['data']

            update_requests = []
            for report in reports:
                doc = {
                    # 报告期
                    'report_date': report['reportdate'][0:10],
                    # 公告日期
                    'announced_date': report['latestnoticedate'][0:10],
                    # 每股收益
                    'eps': report['basiceps'],
                    'code': code
                }

                update_requests.append(
                    UpdateOne(
                        {'code': code, 'report_date': doc['report_date']},
                        {'$set': doc}, upsert=True))

            if len(update_requests) > 0:
                update_result = DB_CONN['finance_report'].bulk_write(update_requests, ordered=False)
                print('股票 %s, 财报，更新 %d, 插入 %d' %
                      (code, update_result.modified_count, update_result.upserted_count))


if __name__ == '__main__':
    FinanceReportCrawler().crawl_finance_summary()


#  -*- coding: utf-8 -*-

import tushare as ts
from pandas import DataFrame
import matplotlib.pyplot as plt


def get_code_reports():
    """
    获取回测周期内的年度财报数据，组合成一个dict数据结构，key是股票代码，
    value是一个按照报告发布日期排序的列表，列表内的元素也是一个dict
    {'eps': 每股收益, 'announced_date': 公告日期}
    """

    # 这个tuple包含了三个元素，前两个分别是用来获取年度财报时的参数年份和季度，
    # 后面是一个发布年度财报的年份，因为一般情况下发布财报都是在第二年的4月底之前，
    # 所以这个年份比财报的年份晚一年
    report_date_tuples = [(2013, 4, 2014), (2014, 4, 2015)]

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
    


def stock_pool(begin_date, end_date):
    """
    实现股票池选股逻辑，找到指定日期范围的候选股票
    条件：0 < PE < 30, 按从小到大排序，剔除停牌后，取前100个；再平衡周期：7个交易日
    :param begin_date: 开始日期
    :param end_date: 结束日期
    :return: tuple，再平衡的日期列表，以及一个dict(key: 再平衡日, value: 当期的股票列表)
    """

    # 获取财务数据
    code_report_dict = get_code_reports()

    # 股票池的再平衡周期
    rebalance_interval = 7

    # 因为上证指数没有停牌不会缺数，所以用它作为交易日历，
    szzz_hq_df = ts.get_k_data('000001', index=True, start=begin_date, end=end_date)
    all_dates = list(szzz_hq_df['date'])

    # 调整日和其对应的股票
    rebalance_date_codes_dict = dict()
    rebalance_dates =[]

    # 保存上一期的股票池
    last_phase_codes = []
    # 所有的交易日数
    dates_count = len(all_dates)
    # 用再平衡周期作为步长循环
    for index in range(0, dates_count, rebalance_interval):
        # 当前的调整日
        rebalance_date = all_dates[index]

        # 获取本期符合条件的备选股票
        this_phase_option_codes = get_option_codes(code_report_dict, rebalance_date)

        # 本期入选的股票代码列表
        this_phase_codes = []

        # 找到在上一期的股票池，但是当前停牌的股票，保留在当期股票池中
        if len(last_phase_codes) > 0:
            for code in last_phase_codes:
                daily_k = ts.get_k_data(code, autype=None, start=rebalance_date, end=rebalance_date)
                if daily_k.size == 0:
                    this_phase_codes.append(code)

        print('上期停牌的股票：', flush=True)
        print(this_phase_codes, flush=True)

        # 剩余的位置用当前备选股票的
        option_size = len(this_phase_option_codes)
        if option_size > (100 - len(this_phase_codes)): 
            this_phase_codes += this_phase_option_codes[0:100-len(this_phase_codes)]
        else:
            this_phase_codes += this_phase_option_codes

        # 当期股票池作为下次循环的上期股票池
        last_phase_codes = this_phase_codes

        # 保存到返回结果中
        rebalance_date_codes_dict[rebalance_date] = this_phase_codes
        rebalance_dates.append(rebalance_date)

        print('当前最终的备选票：%s' % rebalance_date, flush=True)
        print(this_phase_codes, flush=True)

    return rebalance_dates, rebalance_date_codes_dict
        

def get_option_codes(code_report_dict, rebalance_date):
    """
    找到某个调整日符合股票池条件的股票列表
    :param code_report_dict: 股票对应的财报列表
    :param rebalance_date: 再平衡日期
    :return: 股票代码列表
    """

    # 如果股票和每股收益的dict是空的，则重新获取
    report_codes = list(code_report_dict.keys())
    if len(report_codes) == 0:
        get_code_reports()
        report_codes = list(code_report_dict.keys())

    # 找到当期符合条件的EPS，股票代码和EPS
    code_eps_dict = dict()
    for code in report_codes:
        # 因为财报是按照公告日期从早到晚排列的，所以顺序查找
        reports = code_report_dict[code]
        # 用来保存最后一个公告日期小于等于当前日期的财报
        last_report = None
        for report in reports:
            announced_date = report['announced_date']
            # 如果公告日期大于当前调整日，则结束循环
            if announced_date > rebalance_date:
                break

            last_report = report

        # 如果找到了正确时间范围的年报，并且eps大于0，才保留
        if last_report is not None and last_report['eps'] > 0 :
            print('%s, %s, %s, %5.2f' %
             (code, rebalance_date, last_report['announced_date'], last_report['eps']), flush=True)

            code_eps_dict[code] = last_report['eps']

    # 只在符合EPS>0的范围，计算PE，并筛选股票
    validated_codes = list(code_eps_dict)

    df_pe = DataFrame(columns=['close', 'eps'])
    for code in validated_codes:
        # 用不复权的价格
        daily_k = ts.get_k_data(code, autype=None, start=rebalance_date, end=rebalance_date)
        # 如果当前是停牌，就获取不到股价信息，那么不参与排名
        if daily_k.size > 0:
            close = daily_k.loc[daily_k.index[0]]['close']
            df_pe.loc[code] = {'eps': code_eps_dict[code], 'close': close}
            print('%s %6.2f' % (code, close), flush=True)
        else:
            print('%s 停牌' % (code), flush=True)

    # 计算PE，重点表述为什么？重新讲解复权
    df_pe['pe'] = df_pe['close'] / df_pe['eps']
    # 从小到大排序
    df_pe.sort_values('pe', ascending=True, inplace=True)
    # 只保留小于30的数据
    df_pe = df_pe[df_pe['pe'] < 30]

    # 返回排名靠前的100只股票代码
    return list(df_pe.index)[0:100]


def statistic_stock_pool_profit():
    """
    统计股票池的收益
    """
    # 设定评测周期
    # rebalance_dates, codes_dict = stock_pool('2008-01-01', '2018-06-30')
    rebalance_dates, codes_dict = stock_pool('2015-01-01', '2015-01-31')

    # 用DataFrame保存收益
    df_profit = DataFrame(columns=['profit', 'hs300'])

    df_profit.loc[rebalance_dates[0]] = {'profit': 0, 'hs300': 0}

    # 获取沪深300在统计周期内的第一天的值
    hs300_k = ts.get_k_data('000300', index=True, start=rebalance_dates[0], end=rebalance_dates[0])
    hs300_begin_value = hs300_k.loc[hs300_k.index[0]]['close']

    # 通过净值计算累计收益
    net_value = 1
    for _index in range(1, len(rebalance_dates) - 1):
        last_rebalance_date = rebalance_dates[_index - 1]
        current_rebalance_date = rebalance_dates[_index]
        # 获取上一期的股票池
        codes = codes_dict[last_rebalance_date]

        # 统计当前的收益
        profit_sum = 0
        # 参与统计收益的股票个数
        profit_code_count = 0
        for code in codes:
            daily_ks = ts.get_k_data(code, autype='hfq', start=last_rebalance_date, end=current_rebalance_date)

            index_size = daily_ks.index.size
            # 如果没有数据，则跳过，长期停牌
            if index_size == 0:
                continue
            # 买入价
            in_price = daily_ks.loc[daily_ks.index[0]]['close']
            # 卖出价
            out_price = daily_ks.loc[daily_ks.index[index_size - 1]]['close']
            # 股票池内所有股票的收益
            profit_sum += (out_price - in_price)/in_price
            profit_code_count += 1

        profit = round(profit_sum/profit_code_count, 4)

        hs300_k_current = ts.get_k_data('000300', index=True, start=current_rebalance_date, end=current_rebalance_date)
        hs300_close = hs300_k_current.loc[hs300_k_current.index[0]]['close']

        # 计算净值和累积收益
        net_value = net_value * (1 + profit)
        df_profit.loc[current_rebalance_date] = {
        'profit': round((net_value - 1) * 100, 4),
        'hs300': round((hs300_close - hs300_begin_value) * 100/hs300_begin_value, 4)}

        print(df_profit)

    # 绘制曲线
    df_profit.plot(title='Stock Pool Profit Statistic', kind='line')
    # 显示图像
    plt.show()

if __name__=="__main__":
    statistic_stock_pool_profit()

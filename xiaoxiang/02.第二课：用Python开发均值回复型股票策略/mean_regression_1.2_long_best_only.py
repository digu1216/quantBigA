# ���뺯����
import jqdata

ADJUST_INTERVAL = 20  # ��������
CHK_PF_INTERVAL = 60  # �۲ⴰ��
PERCENT_TO_KEEP = 10  # �������

# ��ʼ���������ز⿪ʼʱִ��һ��
def initialize(context):
    set_benchmark('000300.XSHG')  # �趨�Ƚϻ�׼ָ��
    set_option('use_real_price', True)  # Ĭ�ϸ�Ȩģʽ

    # �趨����/��ȯ�˻�
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.cash, type='stock_margin')])

    # �趨���׳ɱ�
    set_order_cost(OrderCost(open_tax=0, close_tax=0.000, open_commission=0.0000, close_commission=0.0000, close_today_commission=0, min_commission=0), type='stock')
    # set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    
    # �趨����/��ȯ�����ʺͱ�֤�����
    set_option('margincash_interest_rate', 0.00)
    set_option('margincash_margin_rate', 1.0)
    set_option('marginsec_interest_rate', 0.00)
    set_option('marginsec_margin_rate', 1.0)
    """
    set_option('margincash_interest_rate', 0.08)
    set_option('margincash_margin_rate', 1.5)
    set_option('marginsec_interest_rate', 0.10)
    set_option('marginsec_margin_rate', 1.5)
    """
    
    # ���ö�ʱ���к���
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

    # ��¼�������ڼ�������
    g.all_tdays = jqdata.get_all_trade_days()
    g.date_xlat = dict([(doc[1], doc[0]) for doc in enumerate(g.all_tdays)])

    # �趨����ȫ�ֱ���
    g.elapsed_days = 0
    g.rebalance_today = False
    g.new_long_pos = {}

# ��ÿ�������տ���ǰ����
def before_market_open(context):
    cur_dt = context.current_dt.date()  # ��ǰ����
    if g.elapsed_days % ADJUST_INTERVAL == 0:  # �Ƿ��ǵ�����
        log.info("Rebalance at %s", cur_dt)
        g.rebalance_today = True
        idx = g.date_xlat[cur_dt]

        # �۲촰����ĩ����
        tail_date = g.all_tdays[idx-1]
        head_date = g.all_tdays[idx-1-CHK_PF_INTERVAL]

        # ������ǰһ��Ĺ�Ʊ�б�
        candidates = list(get_all_securities(["stock"], tail_date).index)

        # �۲촰��ĩβ���ڵĹ�Ʊ�۸�
        tail_prices = get_price(candidates, tail_date, tail_date, frequency="1d", fields=["close"])
        g.tail_values = dict(tail_prices["close"].iloc[0])

        # �۲촰����ʼ���ڵĹ�Ʊ�۸�
        head_prices = get_price(candidates, head_date, head_date, frequency="1d", fields=["close"])
        g.head_values = dict(head_prices["close"].iloc[0])

        # �ڹ۲촰���ڰ������ʶԹ�Ʊ���򣨴�С����
        merged_list = []
        for code, tail_value in g.tail_values.items():
            if math.isnan(tail_value):
                continue
            if code not in g.head_values:
                continue
            head_value = g.head_values[code]
            if math.isnan(head_value):
                continue

            # �������������
            profit_r = tail_value/head_value - 1.0

            # �����м���
            merged_list.append({
                "code": code,
                "profit_r": profit_r,
                "price": tail_value
            })

        # ����β�ֱ�ȡ��һ�������Ĺ�Ʊ�������µĶ��Ͷ�����
        merged_list.sort(key=lambda x: x["profit_r"], reverse=True)

        num_to_keep = len(merged_list) * PERCENT_TO_KEEP // 100
        g.new_long_pos  = {doc["code"]:doc for doc in merged_list[0:num_to_keep]}

    else:
        g.rebalance_today = False
    
    g.elapsed_days += 1
    
# ��ÿ�������տ���ʱ����
def market_open(context):
    p = context.portfolio.subportfolios[0]  # ����/��ȯ��֤���˻�
    if g.rebalance_today:
        # ��ƽ�ⲽ��1��ƽ��ԭ�ж�ղ�λ
        prev_long_pos = p.long_positions

        for code, pos in prev_long_pos.items():
            margincash_close(code, pos.closeable_amount)

        # ��ƽ�ⲽ��2�������µĶ�ղ�λ
        each_long_cash = round(p.available_margin / len(g.new_long_pos), 2)

        for code, doc in g.new_long_pos.items():
            num_to_buy = each_long_cash / g.tail_values[code] // 100 * 100
            margincash_open(code, num_to_buy)

    else:
        # �ǵ����գ���������ֹӯ/ֹ��ȶ����������
        pass

# ��ÿ�����������̺�����
def after_market_close(context):
    # �鿴������ȯ�˻���������Ϣ(�������API-����-SubPortfolio)
    p = context.portfolio.subportfolios[0]
    log.info('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
    log.info('�鿴������ȯ�˻���������Ϣ(�������API-����-SubPortfolio)��')
    log.info('���ʲ���', p.total_value)
    log.info('���ʲ���', p.net_value)
    log.info('�ܸ�ծ��', p.total_liability)
    log.info('���ʸ�ծ��', p.cash_liability)
    log.info('��ȯ��ծ��', p.sec_liability)
    log.info('��Ϣ�ܸ�ծ��', p.interest)
    log.info('���ñ�֤��', p.available_margin)
    log.info('ά�ֵ���������', p.maintenance_margin_rate)
    log.info('�˻��������ͣ�', p.type)
    log.info('##############################################################')

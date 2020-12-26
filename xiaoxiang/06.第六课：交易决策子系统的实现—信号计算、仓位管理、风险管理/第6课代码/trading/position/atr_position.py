#  -*- coding: utf-8 -*-

from .base_position import BasePosition
from util.database import DB_CONN
from pymongo import DESCENDING
from pandas import DataFrame
from data.data_module import DataModule
from datetime import datetime, timedelta
import traceback


class ATRPosition(BasePosition):
    def __init__(self, account, strategy_option):
        BasePosition.__init__(self, account, strategy_option)
        self.dm = DataModule()

    def update_holding(self, code, date, updated_holding):
        """
        更新持仓股，为新的持仓股增加ATR、加仓次数
        :param code: 股票代码
        :param date: 日期
        :param updated_holding: 更新后的持仓股
        """
        try:
            existing_holding = self.account.get_holding(code)
            if existing_holding is not None and 'atr' not in existing_holding:
                atr = self.compute_atr(code, date)
                if atr is not None:
                    updated_holding['atr'] = atr
                    updated_holding['add_times'] = 0
                    self.account.update_holding(code, updated_holding)
        except:
            print('加仓策略，更新持仓股信息时，发生错误，股票代码：%s，日期：%s，' % (code, date), flush=True)
            traceback.print_exc()

    def get_add_signal(self, code, date):
        """
        如果符合加仓条件，则计算加仓信号
        :param code: 股票代码
        :param date: 日期
        :return: 加仓信号，如果没有则返回None，正常信号包括：code - 股票代码，position - 仓位
        """
        add_signal = None

        try:
            df_daily = self.dm.get_k_data(code, autype=None, begin_date=date, end_date=date)
            if df_daily.index.size > 0:
                holding_stock = self.account.get_holding(code)

                df_daily.set_index(['date'], 1, inplace=True)
                daily = df_daily.loc[date]
                if 'atr' in holding_stock and daily['is_trading']:
                    au_factor = daily['au_factor']
                    # ATR
                    atr = holding_stock['atr'] / au_factor
                    # 已加仓次数
                    add_times = holding_stock['add_times']
                    # 末次加仓价格，比较时用的实际价格
                    last_buy_price = holding_stock['last_buy_hfq_price']
                    hfq_close = daily['close'] * au_factor
                    # 最多加仓4次 价格超过上一个加仓点+atr
                    if add_times < 4 and hfq_close - last_buy_price > atr:
                        position = self.compute_position(code, date)
                        add_signal = {'code': code, 'position': position}
        except:
            print('计算加仓信号时，发生错误，股票代码：%s, 日期：%s' % (code, date), flush=True)
            traceback.print_exc()

        return add_signal

    def compute_atr(self, code, date):
        """
        计算ATR
        :param code: 股票代码
        :param date: 日期
        :return: ATR的值
        """
        minute_cursor = DB_CONN['minute'].find(
            {'code': code, 'time': {'$lte': date + ' 15:00'}},
            sort=[('time', DESCENDING)],
            projection={'date': True, 'time': True, 'close': True, 'high': True, 'low': True, '_id': False},
            limit=60)
        minutes = [minute for minute in minute_cursor]

        if len(minutes) >= 60:

            before_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=20)).strftime('%Y-%m-%d')
            df_daily = self.dm.get_k_data(code, autype=None, begin_date=before_date, end_date=date)
            if df_daily.index.size == 0:
                return None

            df_daily.set_index(['date'], 1, inplace=True)

            atr_df = DataFrame(columns=['tr'])
            for index in range(1, len(minutes)):
                minute = minutes[index]
                minute_date = minute['date']
                try:
                    au_factor = df_daily.loc[minute_date]['au_factor']
                    high = minute['high'] * au_factor
                    low = minute['low'] * au_factor
                    pre_close = minutes[index - 1]['close'] * au_factor
                    atr_df.loc[index] = {
                        'tr': max([high - low, abs(high - pre_close), abs(pre_close - low)])
                    }
                except:
                    print('计算ATR发生异常，股票代码：%s， 分钟线日期：%s' % (code, minute_date), flush=True)
                    traceback.print_exc()

            atr = atr_df.rolling(window=60).mean()['tr'][59]
            return atr
        else:
            print('加仓策略（ATR），分钟线数据不足，股票代码：%s，日期：%s，分钟线数：%2d'
                  % (code, date, len(minutes)), flush=True)
            return None

    def compute_position(self, code, date):
        """
        计算应该分配的仓位， 这里采用固定仓位，总资金的0.015
        :param code: 股票代码
        :param date: 日期
        :return:
        """
        amount = self.strategy_option.capital() * 0.015
        return amount


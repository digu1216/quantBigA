# -*- coding: utf-8 -*-

import asyncio
import os
import queue
import sys
import threading
import traceback
import time
import json
from datetime import datetime, timedelta
from enum import Enum

# 是否支持部分成交
_enable_partial_filling = True

TimeSlot = Enum("TimeSlot", "NA new_day pre_trade trade_hours post_trade day_close")


class DealsMaker(threading.Thread):
    def __init__(self):
        super(DealsMaker, self).__init__()
        self.halt_dm = None
        self.inner_feeds = None
        self.feeds_sender = None
        self.simu_tick_receiver = None

        self.current_date = None
        self.current_slot = TimeSlot.trade_hours
        self.day_flip_flop = None
        self.is_noon_time = None
        self.order_seq_in_day = None

        self.latest_ticks_info = None
        self.active_orders = None
        self.expired_orders = None

        self._feeds_queue = queue.Queue()
        self._orders_queue = queue.Queue()
        self._ticks_queue = queue.Queue()

    def run(self):

        # create and run a feeds-processor instance
        self.inner_feeds = queue.Queue()
        self.feeds_sender = FeedsProcessor(self.inner_feeds)
        self.feeds_sender.start()

        self.simu_tick_receiver = SimuTickReceiver(self._ticks_queue)
        self.simu_tick_receiver.start()

        # start the deal-making service
        self.halt_dm = threading.Event()
        while not self.halt_dm.is_set():
            self.mark_time_slot_in_day()
            self.work_on_orders_and_ticks()
        self._feeds_queue.empty()

        # notify the feeds-processor to stop as well
        self.inner_feeds.put_nowait(None)
        self.feeds_sender.join()
        self.simu_tick_receiver.join()

    def stop_dm(self, wait=True):
        if self.halt_dm is None:
            return
        self.halt_dm.set()
        if wait and self.is_alive():
            self.join()

        if self.simu_tick_receiver is None:
            self.simu_tick_receiver.stop()

    def new_order(self, op, code, num, price):
        """
        下单
        :param op: 交易类型，buy - 买入， sell - 卖出
        :param code: 股票代码
        :param num: 委托股数
        :param price: 期望价格
        """
        order = {
            'op': op,
            'code': code,
            'num': num,
            'price': price
        }
        print('用户下单，方向：%s，股票代码：%s，委托量：%7d，价格：%7.2f'
              % (op, code, num, price), flush=True)
        self._orders_queue.put_nowait(order)

    def work_on_orders_and_ticks(self):
        """
        处理接收到的委托单和tick数据
        """
        # time.sleep(0.01)

        try:
            if self._orders_queue.empty() is False:
                order = self._orders_queue.get(timeout=1)
                if len(order) > 0:
                    self.on_receive_order(order)
        except Exception:
            traceback.print_exc()

        # time.sleep(0.01)
        count = 0
        try:
            if self._ticks_queue.empty() is False:
                tick = self._ticks_queue.get(timeout=1)
                if len(tick) > 0:
                        self.on_receive_tick(tick)
                        count += 1
        except Exception:
            traceback.print_exc()

        time.sleep(0.5)

        if self.current_slot is TimeSlot.trade_hours and len(self.active_orders) > 0 and count > 0:
            self.do_deals_matching()

    # ------------------------

    def mark_time_slot_in_day(self):
        """
        维持日内的交易时间
        """
        if self.current_date is None:
            self.current_date = '2018-07-19'
            self.current_slot = TimeSlot.trade_hours

            self.on_slot_new_day()


    # ------------------------

    @property
    def next_order_id(self):
        _order_id = "{}_{:0>4}".format(self.current_date.replace("-", ""), self.order_seq_in_day)
        self.order_seq_in_day += 1
        return _order_id

    def on_slot_new_day(self):
        print("** new_day", flush=True)

        self.day_flip_flop = 0
        self.is_noon_time = False
        self.order_seq_in_day = 1
        self.latest_ticks_info = dict()

        self.active_orders = dict()
        self.expired_orders = dict()

    def on_slot_day_close(self):
        """
        收盘事件的处理
        """
        print("** day_close", flush=True)

        for ptr in self.active_orders.values():
            ptr["state"] = "closed"
            self.persistent_record("order", ptr)

            one_order = ptr["raw_order"]
            obj = dict(
                msg_type="closed",
                message="已关闭",
                reason="",
                order_id=ptr["order_id"],
                code=one_order["code"],
                # more info
                submit_time=ptr["submit_time"],
                revoke_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                revoke_num=ptr["raw_order"]["num"] - ptr["acc_num"]
            )
            self.push_feed_to_queue(obj)
        self.expired_orders.update(self.active_orders)
        self.active_orders = dict()

    # ------------------------

    def on_receive_order(self, one_order):
        print("## received:", one_order, flush=True)
        success, extra = self.validate_format(one_order)
        if not success:
            obj = dict(
                msg_type="invalid",
                message="无效单",
                reason=extra,
            )
            self.push_feed_to_queue(obj)
            return

        success, extra = self.validate_timeslot()
        if not success:
            obj = dict(
                msg_type="rejected",
                message="拒绝",
                reason=extra
            )
            self.push_feed_to_queue(obj)
            return

        if one_order["op"] in ["buy", "sell"]:
            success, extra = self.check_available_ticks(one_order)
            if not success:
                obj = dict(
                    msg_type="rejected",
                    message="拒绝",
                    reason=extra
                )
                self.push_feed_to_queue(obj)
                return
            self.register_new_order(one_order)

    def validate_format(self, order):
        """
        验证交易指令格式的正确
        :param order: 交易指令
        :return: True - 格式正确，False - 格式错误
        """
        op = order.get("op")
        if op is None or op not in ["buy", "sell"]:
            return False, "无效指令"

        required_fields = set(["op"])
        if op in ["buy", "sell"]:
            required_fields.update(["code", "num", "price"])

        provided_fields = set(order.keys())
        if not required_fields.issubset(provided_fields):
            return False, "缺少必填字段"

        if op in ["buy", "sell"]:
            code = order.get("code")
            if code is None or type(code) is not str or code.strip() == "":
                return False, "证券代码格式错误"

            try:
                if type(order["num"]) is not int:
                    order["num"] = int(order["num"])
                if type(order["price"]) is not float:
                    order["price"] = float(order["price"])
            except Exception as e:
                return False, "数量或价格字段格式错误"

            if order["num"] <= 0 or order["price"] <= 0.0:
                return False, "申报数量或价格取值无效"
            if order["op"] == "buy" and order["num"] % 100 != 0:
                return False, "申买数量不是100的倍数"

        return True, None

    def validate_timeslot(self):
        if self.current_slot is not TimeSlot.pre_trade and \
                self.current_slot is not TimeSlot.trade_hours \
                or self.is_noon_time:
            return False, "非交易时段"

        return True, None

    def check_available_ticks(self, one_order):
        ptr = self.latest_ticks_info.get(one_order["code"])
        if ptr is None:
            return False, "证券代码无效或暂无行情数据"

        return True, None

    def register_new_order(self, one_order):
        order_id = self.next_order_id  # allocate a new order_id sequentially
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.persistent_record("request", one_order)

        # add to active orders' queue
        ptr = dict(
            order_id=order_id,
            submit_time=timestamp,
            raw_order=one_order,
            state="active",
            last_deal_time=None,
            acc_num=0,
            num_deals_made=0
        )
        self.active_orders[order_id] = ptr
        self.persistent_record("order", ptr)

        # send feedback form to client
        obj = dict(
            msg_type="accepted",
            message="已报",
            reason="",
            order_id=order_id,
            code=one_order["code"],
            submit_time=timestamp
        )
        self.push_feed_to_queue(obj)

    def push_feed_to_queue(self, obj):
        try:
            self.inner_feeds.put_nowait(("feed", obj))
        except asyncio.QueueFull as e:
            print("Warning: inner queue for feeds-sending is full!", flush=True)

    def persistent_record(self, category, obj):
        try:
            self.inner_feeds.put_nowait((category, obj))
        except asyncio.QueueFull as e:
            print("Warning: inner queue for feeds-sending is full!", flush=True)

    def on_receive_tick(self, one_tick):
        # print("处理Tick：%s, %s" % (one_tick['code'], one_tick['time']), flush=True)
        if one_tick["code"][0] > "6":
            return

        # ordinary codes
        tick_time = one_tick['time']
        if self.current_slot not in [TimeSlot.pre_trade, TimeSlot.trade_hours] or \
                self.current_slot is TimeSlot.trade_hours and self.is_noon_time:
            return  # in case ticks arrives before index, and ignore noon-time ticks
        if self.current_slot is TimeSlot.trade_hours and not self.is_noon_time and \
                (tick_time < "09:30:00" or tick_time >= "15:00:00" or "11:30:00" <= tick_time < "13:00:00"):
            # print("  -- ignored non-sync ticks:", the_tm, flush=True)
            return  # ignore non-trading hours in case of non-sync ticks

        code = one_tick["code"]
        ptr = self.latest_ticks_info.get(code)
        if ptr is None:
            ptr = dict(
                day_high=one_tick["high"],
                day_low=one_tick["low"],
                new_high=False,  # reaches new highest price compared w/ previous ticks in day
                new_low=False,  # reaches new lowest price compared w/ previous ticks in day
                prev_point=one_tick["price"],
                raw_tick=one_tick
            )
            self.latest_ticks_info[code] = ptr
        else:
            ptr["new_high"] = (one_tick["high"] > ptr["day_high"])
            ptr["new_low"] = (one_tick["low"] < ptr["day_low"])
            ptr["prev_point"] = ptr["raw_tick"]["price"]
            ptr["raw_tick"] = one_tick
            ptr["day_high"] = one_tick["high"]
            ptr["day_low"] = one_tick["low"]

    def do_deals_matching(self):
        buy_list = [ptr for ptr in self.active_orders.values() if ptr["raw_order"]["op"] == "buy"]
        sell_list = [ptr for ptr in self.active_orders.values() if ptr["raw_order"]["op"] == "sell"]
        completed = list()

        if len(buy_list) > 0:
            buy_list.sort(key=lambda x: (x["raw_order"]["code"], -x["raw_order"]["price"], x["order_id"]))  # H->L
            for ptr in buy_list:
                code = ptr["raw_order"]["code"]
                one_code_tick = self.latest_ticks_info.get(code)  # may not exist due to reloading from db
                if one_code_tick is None:
                    continue
                fully_filled = self.try_a_match("buy", ptr, one_code_tick)
                if fully_filled:
                    completed.append(ptr)

        if len(sell_list) > 0:
            sell_list.sort(key=lambda x: (x["raw_order"]["code"], x["raw_order"]["price"], x["order_id"]))  # L->H
            for ptr in sell_list:
                code = ptr["raw_order"]["code"]
                one_code_tick = self.latest_ticks_info.get(code)  # may not exist due to reloading from db
                if one_code_tick is None:
                    continue
                fully_filled = self.try_a_match("sell", ptr, one_code_tick)
                if fully_filled:
                    completed.append(ptr)

        # move completed orders from active queue to expired queue
        for ptr in completed:
            order_id = ptr["order_id"]
            self.expired_orders[order_id] = self.active_orders.pop(order_id)

    def try_a_match(self, op, order_ptr, tick_ptr):
        one_order = order_ptr["raw_order"]
        one_tick = tick_ptr["raw_tick"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prev_point = tick_ptr["prev_point"]
        latest = one_tick["price"]
        highest = max(prev_point, latest)
        if tick_ptr["new_high"]:
            highest = max(highest, tick_ptr["day_high"])
        lowest = min(prev_point, latest)
        if tick_ptr["new_low"]:
            lowest = min(lowest, tick_ptr["day_low"])
        quotation = one_order["price"]

        fully_filled = False
        deal_price = None

        if _enable_partial_filling:
            try:
                pending_quotes = [
                    (one_tick["a5_p"], one_tick["a5_v"]),
                    (one_tick["a4_p"], one_tick["a4_v"]),
                    (one_tick["a3_p"], one_tick["a3_v"]),
                    (one_tick["a2_p"], one_tick["a2_v"]),
                    (one_tick["a1_p"], one_tick["a1_v"]),
                    (one_tick["b1_p"], one_tick["b1_v"]),
                    (one_tick["b2_p"], one_tick["b2_v"]),
                    (one_tick["b3_p"], one_tick["b3_v"]),
                    (one_tick["b4_p"], one_tick["b4_v"]),
                    (one_tick["b5_p"], one_tick["b5_v"]),
                ]
            except Exception:
                print("-- invalid tick detected:", one_tick, flush=True)
                return False
            feasible = False
            seq = None
            if op == "buy":
                if quotation >= lowest:
                    ub = highest if quotation > highest else quotation
                    lb = lowest
                    it = filter(lambda x: lb <= x[0] <= ub, pending_quotes)
                    candidates = [pv for pv in it]
                    seq = reversed(candidates)  # L->H
                    feasible = True
            else:  # "sell"
                if quotation <= highest:
                    ub = highest
                    lb = lowest if quotation < lowest else quotation
                    it = filter(lambda x: lb <= x[0] <= ub, pending_quotes)
                    candidates = [pv for pv in it]
                    seq = candidates  # H->L
                    feasible = True

            if feasible:
                rest_num = one_order["num"] - order_ptr["acc_num"]
                for p, v in seq:
                    deal_num = min(rest_num, v)
                    rest_num -= deal_num

                    # update queue info
                    order_ptr["last_deal_time"] = timestamp
                    order_ptr["acc_num"] += deal_num
                    order_ptr["num_deals_made"] += 1
                    self.persistent_record("order", order_ptr)

                    filled_in_one_time = (deal_num == one_order["num"])

                    # send a feed back
                    obj = dict(
                        msg_type="partial_filled" if not filled_in_one_time else "filled",
                        message="部分成交" if not filled_in_one_time else "全部成交",
                        reason="",
                        order_id=order_ptr["order_id"],
                        submit_time=order_ptr["submit_time"],
                        # more info
                        op=one_order["op"],
                        code=one_order["code"],
                        claim_price=one_order["price"],
                        claim_num=one_order["num"],
                        deal_seq_no=order_ptr["order_id"] + "_" + str(order_ptr["num_deals_made"]),
                        deal_price=p,
                        deal_num=deal_num,
                        deal_time=timestamp,
                        acc_num=order_ptr["acc_num"]
                    )
                    self.push_feed_to_queue(obj)
                    self.persistent_record("deal", obj)

                    if rest_num == 0:
                        order_ptr["state"] = "done"
                        self.persistent_record("order", order_ptr)
                        fully_filled = True
                        break

        else:  # fully_filling only
            if op == "buy":
                if quotation >= lowest:
                    if quotation > highest:
                        deal_price = highest
                    else:
                        deal_price = quotation
                    fully_filled = True
            else:  # "sell"
                if quotation <= highest:
                    if quotation < lowest:
                        deal_price = lowest
                    else:
                        deal_price = quotation
                fully_filled = True

            if fully_filled:
                # update queue info
                order_ptr["last_deal_time"] = timestamp
                order_ptr["acc_num"] = one_order["num"]
                order_ptr["num_deals_made"] += 1
                order_ptr["state"] = "done"
                self.persistent_record("order", order_ptr)

                # send a feed back
                obj = dict(
                    msg_type="filled",
                    message="全部成交",
                    reason="",
                    order_id=order_ptr["order_id"],
                    submit_time=order_ptr["submit_time"],
                    # more info
                    op=one_order["op"],
                    code=one_order["code"],
                    claim_price=one_order["price"],
                    claim_num=one_order["num"],
                    deal_seq_no=order_ptr["order_id"] + "_" + str(order_ptr["num_deals_made"]),
                    deal_price=deal_price,
                    deal_num=one_order["num"],
                    deal_time=timestamp,
                    acc_num=one_order["num"]
                )
                self.push_feed_to_queue(obj)
                self.persistent_record("deal", obj)

        return fully_filled

    # ------------------------


class FeedsProcessor(threading.Thread):
    """
    单独的日志处理线程
    """

    def __init__(self, inner_feeds):
        super(FeedsProcessor, self).__init__()
        self.inner_feeds = inner_feeds

    def run(self):
        while True:
            item = self.inner_feeds.get()
            if item is None:
                break
            category, original_record = item
            print(original_record, flush=True)


class SimuTickReceiver(threading.Thread):
    def __init__(self, tick_queue):
        super(SimuTickReceiver, self).__init__()
        self.tick_queue = tick_queue
        self.running = True

    def run(self):
        ticks_file = os.path.join(sys.path[0], 'ticks')

        # 时间从开盘开始模拟，替换掉原始数据的时间
        tick_time = datetime.strptime('09:30:00', '%H:%M:%S')
        while self.running:
            with open(ticks_file) as contents:
                for line in contents:
                    tick = json.loads(line)
                    tick['time'] = tick_time.strftime('%H:%M:%S')

                    self.tick_queue.put_nowait(tick)
                    tick_time += timedelta(seconds=1)
                    time.sleep(0.01)

            time.sleep(3)

    def stop(self):
        self.running = False


def main():
    the_dm = DealsMaker()
    print("The Deals Maker is running, enter 'info' or 'exit' to debug or stop it...", flush=True)
    the_dm.start()
    while True:
        cmd = input().strip()
        if cmd.startswith('order: '):
            orders = cmd[7:].split(',')
            the_dm.new_order(orders[0], code=orders[1], num=int(orders[2]), price=float(orders[3]))
        elif cmd == "exit":
            break
    the_dm.stop_dm()


if __name__ == "__main__":
    main()

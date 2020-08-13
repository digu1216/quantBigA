# coding:utf-8

import datetime
import time
import re
import decimal

STR_TIME_FORMAT_ONE = '(^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$)'
STR_TIME_FORMAT_TWO = '(^\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$)'
STR_TIME_FORMAT_THREE = '(^/\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{1,2}:\d{1,2}$)'
STR_TIME_FORMAT_FOUR = '(^\d{4}\d{2}\d{2}$)'
STR_TIME_FORMAT_FIVR = '(^\d{4}-\d{1,2}-\d{1,2}$)'
STR_TIME_FORMAT_SIX = '(^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}.\d+S$)'
STR_TIME_FORMAT_SEVEN = '(^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d+Z$)'
STR_TIME_FORMAT_MAP = {STR_TIME_FORMAT_ONE: '%Y-%m-%d %H:%M:%S',
                       STR_TIME_FORMAT_TWO: '%Y/%m/%d %H:%M:%S',
                       STR_TIME_FORMAT_THREE: '%d/%m/%Y %H:%M:%S',
                       STR_TIME_FORMAT_FOUR: '%Y%m%d',
                       STR_TIME_FORMAT_FIVR: '%Y-%m-%d',
                       STR_TIME_FORMAT_SIX: '%Y-%m-%d %H:%M:%S.%fS',
                       STR_TIME_FORMAT_SEVEN: '%Y-%m-%d %H:%M:%SZ'}


def string_to_datetime(time_str):
    """
    将时间字符串转换成datetime
    @:param time_str 时间字符串 支持的格式如下：
                    '年-月-日 时:分:秒',
                    '年/月/日 时:分:秒',
                    '日/月/年 时:分:秒',
                    '年月日',
                    '年-月-日',
    @:return datetime时间对象 如何是不支持的格式则返回空
    """
    _time = None
    if re.match(STR_TIME_FORMAT_ONE, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_ONE])
    elif re.match(STR_TIME_FORMAT_TWO, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_TWO])
    elif re.match(STR_TIME_FORMAT_THREE, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_THREE])
    elif re.match(STR_TIME_FORMAT_FOUR, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_FOUR])
    elif re.match(STR_TIME_FORMAT_FIVR, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_FIVR])
    elif re.match(STR_TIME_FORMAT_SIX, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_SIX])
    elif re.match(STR_TIME_FORMAT_SEVEN, time_str):
        _time = datetime.datetime.strptime(
            time_str, STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_SEVEN])
    return _time


def time_to_str(source_time, format=STR_TIME_FORMAT_MAP[STR_TIME_FORMAT_ONE]):
    """
    将时间对象转换成字符串(包括timestamp时间戳)，默认格式为：年-月-日 时:分:秒
    @:param source_time 时间对象
    @:return 返回时间字符
    """
    if isinstance(source_time, float) or isinstance(source_time, int):
        return time.strftime(format, time.localtime(source_time))
    elif isinstance(source_time, (datetime.datetime, datetime.date)):
        return source_time.strftime(format)
    else:
        return str(source_time)


def timestamp_to_datetime(source_time):
    """
    将时间戳转换成datetime对象
    @:param source_time
    @:return datetime对象
    """
    return datetime.datetime.fromtimestamp(source_time)


def datetime_to_timestamp(source_time):
    """
    获取datetime的时间戳
    如果不是datetime对象，则返回None
    @:param source_time  datetime对象
    @:return 时间戳
    """
    if isinstance(source_time, (datetime.datetime, datetime.date)):
        return time.mktime(source_time.timetuple())
    return None


def microsecond_2_hms(microseconds):
    """ 微秒转时分秒
    非整形则转整形，若转化失败则返回 00:00：00
    @:param microseconds 微秒
    @:return '00:00:00'
    """
    if microseconds is None:
        return '00:00:00'
    if not isinstance(microseconds, int):
        try:
            microseconds = int(microseconds)
        except ValueError:
            return '00:00:00'
    seconds_to_convert = microseconds/(10**6)
    hours = seconds_to_convert/3600
    minutes = (seconds_to_convert-hours*3600)/60
    seconds = seconds_to_convert % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)


# if __name__ == "__main__":
#     print datetime_to_timestamp(datetime.date(2015, 1, 1))
#     time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%fS")
#     _date = string_to_datetime(time_str)
#     print time_str, _date
#     time.sleep(1)

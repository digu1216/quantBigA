# coding:utf-8
import logging


class Logger():
    format_dict = {
        1: logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s \
            - %(lineno)d :  %(message)s'),
        2: logging.Formatter('%(asctime)s - %(name)s - %(levelname)s \
            - %(message)s')
    }

    def __init__(
            self, logname='./trade_stock_digu/log.txt',
            loglevel=1, logger="common"):
        '''
        指定保存日志的文件路径，日志级别，以及调用文件
        将日志存入到指定的文件中
        '''
        # 创建一个logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.DEBUG)

        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(logname)
        fh.setLevel(logging.DEBUG)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = self.format_dict[int(loglevel)]
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def getlog(self):
        return self.logger


if __name__ == "__main__":
    # print datetime_to_timestamp(datetime.date(2015, 1, 1))
    # time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%fS")
    logger = Logger().getlog()
    logger.info('hahahaa')

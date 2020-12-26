# -*- coding: utf-8 -*-

import logging.handlers
import sys


class QuantLogger:
    def __init__(self, name):
        # 业务日志的配置
        self.logger = logging.getLogger(name)

        self.logger.setLevel(logging.INFO)

        format = logging.Formatter('[%(asctime)s[%(name)s] %(levelname)s: %(message)s')
        handler = logging.handlers.TimedRotatingFileHandler(sys.path[2] + '/logs/' + name + '.log', 'D')
        handler.setFormatter(format)

        self.logger.addHandler(handler)

        # 错误日志的配置
        self.errorLogger = logging.getLogger("ERROR")
        self.errorLogger.setLevel(logging.ERROR)
        errorFormatter = logging.Formatter('[%(asctime)s[' + name + '] %(levelname)s: %(message)s')
        errorHandler = logging.handlers.TimedRotatingFileHandler(sys.path[2] + '/logs/error.log', 'D')
        errorHandler.setFormatter(errorFormatter)

        self.errorLogger.addHandler(errorHandler)

        # 调试日志的配置
        self.debugLogger = logging.getLogger("DEBUG")
        self.debugLogger.setLevel(logging.DEBUG)
        debugFormatter = logging.Formatter('[%(asctime)s[' + name + '] %(levelname)s: %(message)s')
        debugHandler = logging.handlers.TimedRotatingFileHandler(sys.path[2] + '/logs/debug.log', 'D')
        debugHandler.setFormatter(debugFormatter)

        self.debugLogger.addHandler(debugHandler)

    def info(self, message, *args):
        self.logger.info(message, *args)

    def error(self, message, *args):
        self.errorLogger.error(message, *args, exc_info=True)

    def debug(self, message, *args):
        self.debugLogger.debug(message, *args)


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys
import numpy as np
import math
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout

from ui.Ui_stock_pool_track import Ui_MainWindow
from datetime import datetime
from datetime import timedelta
from vnpy.tools.convert_utils import string_to_datetime, time_to_str
from vnpy.tools.logger import Logger
from vnpy.trade_stock_digu.data_service import DataServiceTushare, LOG, IndexCode

#创建一个matplotlib图形绘制类
class MyFigure(FigureCanvas):
    def __init__(self,width=5, height=4, dpi=100):
        #第一步：创建一个创建Figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        #第二步：在父类中激活Figure窗口
        super(MyFigure,self).__init__(self.fig) #此句必不可少，否则不能显示图形
        #第三步：创建一个子图，用于绘制图形用，111表示子图编号，如matlab的subplot(1,1,1)
        self.axes = self.fig.add_subplot(111)
    
    def mousePressEvent(self, event):
        # if(event->button() == Qt::RightButton)
        LOG.info('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')    
    
    #第四步：就是画图，【可以在此类中画，也可以在其它类中画】
    def plotcos(self):
        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2 * np.pi * t)
        self.axes.plot(t, s)
    
    def plot_yield_curve_cover(self, x, y):    
        # 图像重绘 
        LOG.info(x)
        LOG.info(y)
        self.axes.cla()
        tick_spacing = math.ceil(x.size/5)   # 横坐标显示5个日期数字
        tick_spacing = tick_spacing if tick_spacing != 0 else 1             
        self.axes.plot(x, y)
        self.axes.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
        self.fig.canvas.draw() # 这里注意是画布重绘，self.figs.canvas
        self.fig.canvas.flush_events() # 画布刷新self.figs.canvas

    def plot_yield_curve_repaint(self, x_lst, y_lst, line_name_lst):    
        # 实时收益曲线图像整体重新绘制
        self.axes.cla()
        for x,y,line_name in zip(x_lst, y_lst, line_name_lst):   
            tick_spacing = math.ceil(x.size/5)   # 横坐标显示5个日期数字
            tick_spacing = tick_spacing if tick_spacing != 0 else 1   
            self.axes.plot(x, y, label=line_name)
            self.axes.legend()  
            self.axes.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
        self.fig.canvas.draw() # 这里注意是画布重绘，self.figs.canvas
        self.fig.canvas.flush_events() # 画布刷新self.figs.canvas

    def plot_yield_curve_union(self, x, y, line_name):    
        # 图像叠加绘制  
        LOG.info(x)
        LOG.info(y)
        tick_spacing = math.ceil(x.size/5)   # 横坐标显示5个日期数字
        tick_spacing = tick_spacing if tick_spacing != 0 else 1           
        self.axes.plot(x, y, label=line_name)
        self.axes.legend()  
        self.axes.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))

class MainWindow(QtWidgets.QMainWindow):
    ds_tushare = DataServiceTushare()
    def __init__(self, parent=None):
        super().__init__(parent)  # 调用父类构造函数，创建QWidget窗体
        self.__ui = Ui_MainWindow()  # 创建UI对象
        self.__ui.setupUi(self)  # 构造UI  
        # 定义MyFigure类的实例 
        self.F_his = MyFigure(width=3, height=2, dpi=100)
        self.F_cur = MyFigure(width=3, height=2, dpi=100)
        date_now = time_to_str(datetime.now(), '%Y%m%d')        
        date_trade_last = self.ds_tushare.get_trade_date(self.ds_tushare.db_date)
        self.__ui.dateEdit_cur.setDate(QtCore.QDate.fromString(date_trade_last, 'yyyyMMdd'))
        self.__ui.dateEdit_daily.setDate(QtCore.QDate.fromString(date_now, 'yyyyMMdd'))        
        self.__ui.dateEdit_oper.setDate(QtCore.QDate.fromString(date_trade_last, 'yyyyMMdd'))    
        date_range = self.ds_tushare.get_curve_date()
        self.date_begin = date_range[0]                    
        self.date_end = date_range[1]
        # GUI的groupBox中创建一个布局，用于添加MyFigure类的实例（即图形）后其他部件。 
        self.gridlayout_his = QGridLayout(self.__ui.groupBox_daily)  # 继承容器groupBox
        self.gridlayout_his.addWidget(self.F_his,0,0)        
        self.draw_history_yield_curve(time_to_str(datetime.now(), '%Y%m%d'))        
        self.gridlayout_cur = QGridLayout(self.__ui.groupBox_cur)  # 继承容器groupBox
        self.gridlayout_cur.addWidget(self.F_cur,0,0)                    
        self.draw_cur_yield_curve()  
        self.set_table_widget_stock_hold()
        # self.__ui.dateEdit_daily.dateChanged[QtCore.QDate].connect(self.slot_test)  # 显示connect的方法

    def show_warning_message(self):
        QtWidgets.QMessageBox.warning(self, "警告", "股票代码输入有误!", QMessageBox.Yes)

    def draw_cur_yield_curve(self):
        x, yield_rate = self.count_cur_yield()
        self.F_cur.plot_yield_curve_union(np.array(x), yield_rate, 'stock_pool')

    def draw_history_yield_curve(self, date):
        x, yield_rate = self.count_daily_yield(date)                
        self.F_his.plot_yield_curve_cover(x, yield_rate)            

    def on_dateEdit_daily_dateChanged(self, date):
        # self.__ui.textEdit_cur.setText(date.toString("yyyyMMdd"))
        self.draw_history_yield_curve(date.toString("yyyyMMdd"))
    
    def on_checkBox_index_sh_stateChanged(self, status):        
        self.on_index_checked()        
    
    def on_checkBox_index_sz_stateChanged(self, status):        
        self.on_index_checked()        

    def on_checkBox_index_zx_stateChanged(self, status):        
        self.on_index_checked()        

    def on_checkBox_index_cy_stateChanged(self, status):        
        self.on_index_checked()        

    def on_index_checked(self):
        status_sh = self.__ui.checkBox_index_sh.checkState()        
        status_sz = self.__ui.checkBox_index_sz.checkState()        
        status_zx = self.__ui.checkBox_index_zx.checkState()        
        status_cy = self.__ui.checkBox_index_cy.checkState()     
        lst_x = list()
        lst_y = list()
        lst_line_name = list()   
        x, yield_rate = self.count_cur_yield()
        lst_x.append(x)
        lst_y.append(yield_rate)
        lst_line_name.append('Stock pool')
        if status_sh == QtCore.Qt.Checked:
            x_sh, yield_rate_sh = self.count_index_yield(IndexCode.INDEX_SH)
            lst_x.append(x_sh)
            lst_y.append(yield_rate_sh)
            lst_line_name.append(IndexCode.INDEX_SH)
        if status_sz == QtCore.Qt.Checked:
            x_sz, yield_rate_sz = self.count_index_yield(IndexCode.INDEX_SZ)
            lst_x.append(x_sz)
            lst_y.append(yield_rate_sz)
            lst_line_name.append(IndexCode.INDEX_SZ)
        if status_zx == QtCore.Qt.Checked:
            x_zx, yield_rate_zx = self.count_index_yield(IndexCode.INDEX_ZX)
            lst_x.append(x_zx)
            lst_y.append(yield_rate_zx)
            lst_line_name.append(IndexCode.INDEX_ZX)
        if status_cy == QtCore.Qt.Checked:
            x_cy, yield_rate_cy = self.count_index_yield(IndexCode.INDEX_CY)
            lst_x.append(x_cy)
            lst_y.append(yield_rate_cy)
            lst_line_name.append(IndexCode.INDEX_CY)
        self.F_cur.plot_yield_curve_repaint(lst_x, lst_y, lst_line_name) 

    def mousePressEvent(self, event):
        LOG.info('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')    

    @pyqtSlot() #对槽函数参数加上pyqtSlot后，不带参数的槽函数只会接收不带参数的槽函数信号，则槽函数只会触发一次。
    def on_pushButton_oper_clicked(self):
        content = self.__ui.textEdit_buy.toPlainText()
        content_sell = self.__ui.textEdit_sell.toPlainText()
        date = self.__ui.dateEdit_oper.date()
        lst_code = content.split(',')
        lst_code_sell = content_sell.split(',')
        lst_code_transfer = list()
        lst_code_transfer_sell = list()
        code_error = False
        if content == '':
            lst_code = []
        if content_sell == '':
            lst_code_sell = []
        for item in lst_code:
            if item[0] in ['0', '3']:
                item += '_SZ'
            else:
                item += '_SH'
            if item not in self.ds_tushare.get_stock_list():
                LOG.info('stock code error! %s' %item)
                code_error = True
                self.show_warning_message()
                break
            lst_code_transfer.append(item)
        for item in lst_code_sell:
            if item[0] in ['0', '3']:
                item += '_SZ'
            else:
                item += '_SH'
            if item not in self.ds_tushare.get_stock_list():
                LOG.info('stock code error! %s' %item)
                code_error = True
                self.show_warning_message()
                break
            lst_code_transfer_sell.append(item)
        if code_error is False:
            self.ds_tushare.daily_stock_pool_in_db(lst_code_transfer, date.toString("yyyyMMdd"))
            self.ds_tushare.cur_stock_pool_in_db(lst_code_transfer, date.toString("yyyyMMdd"))
            self.ds_tushare.set_daily_stock_pool(lst_code_transfer_sell, date.toString("yyyyMMdd"))
            self.ds_tushare.del_cur_stock_pool(lst_code_transfer_sell, date.toString("yyyyMMdd"))
            self.__ui.textEdit_buy.clear()
            self.__ui.textEdit_sell.clear()
            self.set_table_widget_stock_hold()

    def set_table_widget_stock_hold(self):        
        date_lst = self.ds_tushare.get_cur_stock_pool_date_lst()
        if self.date_begin == self.date_end or len(date_lst) == 0:
            LOG.info('收益曲线开始日期等于结束日期')    
            return            
        lst_hold_stock = self.ds_tushare.get_cur_stock_pool_code_lst(date_lst[-1])
        date_lst.reverse()
        for trade_date in date_lst:
            stock_daily_lst = self.ds_tushare.get_daily_stock_pool(trade_date)
            for item_daily in stock_daily_lst:
                if item_daily['ts_code'] not in lst_hold_stock:
                    lst_hold_stock.append(item_daily['ts_code'])
        self.__ui.tableWidget_cur.clearContents()
        self.__ui.tableWidget_cur.setRowCount(len(lst_hold_stock))
        self.__ui.tableWidget_cur.setColumnCount(4)
        line_idx = 0
        for code in lst_hold_stock:            
            self.__ui.tableWidget_cur.setItem(line_idx, 0, QTableWidgetItem(code))
            stock_daily = self.ds_tushare.get_daily_stock(code)
            if stock_daily is not None:
                self.__ui.tableWidget_cur.setItem(line_idx, 1, QTableWidgetItem(stock_daily['date_buy']))     
                date_sell = stock_daily['date_sell'] if stock_daily['date_sell'] is not None else None
                self.__ui.tableWidget_cur.setItem(line_idx, 2, QTableWidgetItem(date_sell))     
                k_data_buy = self.ds_tushare.get_stock_price_info(code, stock_daily['date_buy'])
                if stock_daily['date_sell'] is None:                    
                    k_data_sell = self.ds_tushare.get_stock_price_info_last(code)
                else:
                    k_data_sell = self.ds_tushare.get_stock_price_info(code, stock_daily['date_sell'])
                if k_data_sell is not None and k_data_buy is not None:
                    profit = (k_data_sell['close'] - k_data_buy['close']) / k_data_buy['close']
                else:
                    profit = 0
                self.__ui.tableWidget_cur.setItem(line_idx, 3, QTableWidgetItem("%.4f" % (100*(profit))))     
            line_idx += 1
    
    def count_index_yield(self, code_index):
        """  
        计算指数收益曲线
        code_index: 指数代码 ['000001_SH', '399001_SZ', '399005_SZ', '399006_SZ']       
        """                
        if self.date_begin == self.date_end:
            LOG.info('收益曲线开始日期等于结束日期')
            return np.array(0), np.array(0)
        value_index_lst = list()
        index_lst = self.ds_tushare.get_stock_price_lst(code_index, self.date_begin, self.date_end)
        for item_index in index_lst:
            value_index_lst.append(item_index['close'])
        rate_lst_ret = list()
        for item_index_value in value_index_lst:
            rate_lst_ret.append(item_index_value / value_index_lst[0])
        date_lst = self.ds_tushare.get_trade_cal(self.date_begin, self.date_end)
        return np.array(date_lst), np.array(rate_lst_ret)

    def count_cur_yield(self):
        """  
        计算实时股票收益曲线
        计算方式：
        1、按照每日收盘价进行买卖操作
        2、平均持股，单个股票的上涨对应总市值比例为 单只股票上涨幅度/当前总股票数
        3、每日收益累加中复利按天计算，没有考虑单支股票的复利
        """        
        rate_lst = list()               
        if self.date_begin == self.date_end:
            LOG.info('收益曲线开始日期等于结束日期')
            return np.array(0), np.array(0)
        date_lst =self.ds_tushare.get_trade_cal(self.date_begin, self.date_end)
        code_lst_pre = self.ds_tushare.get_cur_stock_pool_code_lst(self.date_begin)
        for item_date in date_lst:
            pct_chg_lst = list()            
            for item_code_pre in code_lst_pre:
                dic_price = self.ds_tushare.get_stock_price_info(item_code_pre, item_date)
                pct_chg = 0.0 if dic_price is None else dic_price['pct_chg']    # 股票停牌则涨幅为0
                pct_chg_lst.append(pct_chg)
            rate_lst.append(np.mean(pct_chg_lst))
            code_lst_pre = self.ds_tushare.get_cur_stock_pool_code_lst(item_date)
        if len(rate_lst) != 0:
            rate_lst[0] = 0.0   #第一天的收盘价建仓，初始设置为0        
        rate_lst_ret = self.cnt_compound_interest(rate_lst)
        return np.array(date_lst), np.array(rate_lst_ret)

    def count_daily_yield(self, date):
        """
        计算每日股票收益曲线
        计算方式：
        1、按照每日收盘价进行买卖操作
        2、卖出股票对应份额后，持有现金
        3、平均持股，单个股票的上涨对应总市值比例为 单只股票上涨幅度/建仓日的总股票数
        4、每日收益累加中复利按天计算，没有考虑单支股票的复利
        """
        lst_daily_code = self.ds_tushare.get_daily_stock_pool(date)        
        lst_trade_cal = self.ds_tushare.get_trade_cal(date)        
        lst_yield = list()
        hold_stock = len(lst_daily_code)    # 该日建仓的总持股数量
        for item_date in lst_trade_cal:
            pct_daily = 0.0
            for item_daily in lst_daily_code:
                if item_daily['date_sell'] is None or item_daily['date_sell'] >= item_date:
                    dic_price = self.ds_tushare.get_stock_price_info(item_daily['ts_code'], item_date)
                    pct_chg = 0.0 if dic_price is None else dic_price['pct_chg']/float(hold_stock)
                    pct_daily += pct_chg                
            lst_yield.append(pct_daily)
        LOG.info(lst_yield)
        if len(lst_yield) != 0:
            lst_yield[0] = 0.0   #第一天的收盘价建仓，初始涨幅设置为0  
        rate_lst_ret = self.cnt_compound_interest(lst_yield)
        return np.array(lst_trade_cal), np.array(rate_lst_ret)

    def cnt_compound_interest(self, rate_lst):
        # 计算复利
        # 入参rate_lst为单日盈利百分比数据
        rate_arr = 1 + (np.array(rate_lst) / 100.0)
        lst_ret = list()
        item_pre = 1.0
        for item in rate_arr:
            temp = item * item_pre
            lst_ret.append(temp)
            item_pre = temp
        return np.array(lst_ret)
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # 创建app，用QApplication类
    myWidget = MainWindow()
    myWidget.show()    
    sys.exit(app.exec_())
    
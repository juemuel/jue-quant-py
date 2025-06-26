# data_providers/yfinance.py
import yfinance as yf
import pandas as pd


class YFinanceProvider:
    def get_stock_history(self, code, start_date=None, end_date=None):
        """
        使用 yfinance 获取股票历史行情数据
        :param code: 股票代码，如 "AAPL"
        :param start_date: 开始日期，格式 "YYYY-MM-DD"
        :param end_date: 结束日期，格式 "YYYY-MM-DD"
        :return: DataFrame
        """
        data = yf.download(code, start=start_date, end=end_date)
        data.reset_index(inplace=True)
        return data

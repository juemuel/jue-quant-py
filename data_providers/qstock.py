# data_providers/qstock.py
import qstock as qs
import pandas as pd


class QStockProvider:
    def get_stock_history(self, code, start_date=None, end_date=None):
        """
        获取股票历史行情（默认日线）
        :param code: 股票代码，如 '000001'
        :param start_date: 开始日期，格式 'YYYYMMDD'
        :param end_date: 结束日期，格式 'YYYYMMDD'
        :return: DataFrame
        """
        df = qs.get_data(code_list=code, start=start_date, end=end_date)
        if isinstance(df, dict):
            df = pd.DataFrame(df)
        return df

    def realtime_data(self, category="概念板块"):
        """
        获取实时数据（如概念板块、行业等）
        """
        return qs.realtime_data(category)

# data_providers/yfinance.py
import yfinance as yf
import pandas as pd
# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
import logging

from core.exceptions import DataEmptyError
from core.logger import logger, catch
logging.getLogger('uvicorn').handlers = []

class YFinanceProvider:
    def get_stock_history(self, source, code, market, start_date=None, end_date=None):
        """
        使用 yfinance 获取股票历史行情数据
        :param source: 数据源名称（如 'yfinance'）
        :param code: 股票代码，如 "AAPL"
        :param market: 市场代码（如 'NASDAQ'），此处未使用
        :param start_date: 开始日期，格式 "YYYY-MM-DD"
        :param end_date: 结束日期，格式 "YYYY-MM-DD"
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}, code={code}, market={market}, start_date={start_date}, end_date={end_date}")
        df = yf.download(code, start=start_date, end=end_date)
        df.reset_index(inplace=True)
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
    def get_macro_gdp_data(self, source):
        """
        获取宏观GDP数据（yfinance 不直接支持 GDP 数据）
        :param source: 数据源名称（如 'yfinance'）
        :return: DataFrame or None + 异常提示
        """
        print(f"[Provider]source={source}")
        try:
            # yfinance 不直接支持宏观 GDP 数据，模拟一个错误
            raise NotImplementedError("yfinance 不支持直接获取宏观GDP数据")
        except Exception as e:
            raise RuntimeError(f"从 yfinance 获取 GDP 数据失败: {str(e)}") from e


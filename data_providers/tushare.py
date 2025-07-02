# data_providers/tushare.py
import tushare as ts
from core.exception_handler import DataEmptyError, DataAccessDeniedError
import pandas as pd
# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
import logging
from core.logger import logger, catch

logging.getLogger('uvicorn').handlers = []
class TushareProvider:
    def __init__(self):
        ts.set_token("a1533fd58c006f92b96286c3af7f044ad853d51cf2dec60e8f32b33e")
        self.pro = ts.pro_api()

    def get_stock_history(self, source, code, market, start_date=None, end_date=None):
        """
        获取股票历史行情（默认日线）
        :param source: 数据源名称（如 'tushare'）
        :param code: 股票代码，如 '000001.SZ'
        :param market: 市场代码（如 'SH'/'SZ'），此处未使用
        :param start_date: 开始日期，格式 'YYYYMMDD'
        :param end_date: 结束日期，格式 'YYYYMMDD'
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}, code={code}, market={market}, start_date={start_date}, end_date={end_date}")
        ts_code = f"{code}.{market}"
        df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df

    def get_macro_gdp_data(self, source):
        """
        获取宏观GDP数据
        :param source: 数据源名称（如 'tushare'）
        :return: DataFrame
        """
        # Tushare GDP 数据接口示例：国家统计局宏观经济数据
        print(f"[Provider]source={source}")
        df = self.pro.cn_gdp(year="", field="")
        print(f"[Provider]列名: {df.columns.tolist()}")
        return df

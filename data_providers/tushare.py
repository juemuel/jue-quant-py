import tushare as ts
import pandas as pd
from core.logger import logger
from dotenv import load_dotenv
# 加载 .env 文件
load_dotenv()
class TushareProvider:
    def __init__(self):
        ts.set_token("TUSHARE_TOKEN")
        self.pro = ts.pro_api()

    # 可用，1h限制
    def get_all_stocks(self, market=None):
        """
        获取所有股票列表，支持按市场筛选
        :param market: 'SH'（上交所）, 'SZ'（深交所）
        :return: DataFrame ['code', 'name']
        """
        logger.info(f"[Provider]source={self.__class__.__name__}, market={market}")
        # 根据 market 设置交易所参数
        exchange = ''
        if market == "SH":
            exchange = "SSE"  # 上交所
        elif market == "SZ":
            exchange = "SZSE"  # 深交所
        elif market == "BJ":
            exchange = "BSE" # 北交所
        df = self.pro.stock_basic(exchange=exchange, list_status='L', fields='ts_code,symbol,name')
        df['code'] = df['symbol']
        df['name'] = df['name']
        if market == "KE":  # 科创板
            df = df[df['code'].astype(str).str.startswith('68')]
        elif market == "CY":  # 创业板
            df = df[df['code'].astype(str).str.startswith('30')]
        return df[['code', 'name']]

    # 不可用
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
        logger.info(f"[Provider]source={source}")
        df = self.pro.cn_gdp(year="", field="")
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df

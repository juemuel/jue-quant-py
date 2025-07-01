# data_providers/tushare.py
import tushare as ts
import pandas as pd

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
        print(f"[Provider]source={source}, code={code}, market={market}, start_date={start_date}, end_date={end_date}")
        try:
            df = self.pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
            if df.empty:
                raise ValueError(f"从 tushare 获取股票 {code} 的数据为空")
            return df
        except Exception as e:
            raise RuntimeError(f"从 tushare 获取股票 {code} 数据失败: {str(e)}") from e

    def get_macro_gdp_data(self, source):
        """
        获取宏观GDP数据
        :param source: 数据源名称（如 'tushare'）
        :return: DataFrame
        """
        # Tushare GDP 数据接口示例：国家统计局宏观经济数据
        print(f"[Provider]source={source}")
        try:
            df = self.pro.cn_gdp(year="", field="")
            if df.empty:
                raise ValueError("从 tushare 获取 GDP 数据为空")
            return df
        except Exception as e:
            raise RuntimeError(f"从 tushare 获取 GDP 数据失败: {str(e)}") from e

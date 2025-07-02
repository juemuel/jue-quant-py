import qstock as qs
import pandas as pd
from core.logger import logger

class QStockProvider:
    # 不可用
    def get_stock_history(self, source, code, market, start_date=None, end_date=None):
        """
        获取股票历史行情（默认日线）
        :param source: 数据源名称（如 'qstock'）
        :param code: 股票代码，如 '000001'
        :param market: 市场代码（如 'SH'/'SZ'），此处未使用
        :param start_date: 开始日期，格式 'YYYYMMDD'
        :param end_date: 结束日期，格式 'YYYYMMDD'
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}, code={code}, market={market}, start_date={start_date}, end_date={end_date}")
        df = qs.get_data(code_list=code, start=start_date, end=end_date)
        if isinstance(df, dict):
            df = pd.DataFrame(df)
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
    def get_macro_gdp_data(self, source):
        """
        获取宏观GDP数据（QStock 暂无直接 GDP 数据接口）
        :param source: 数据源名称（如 'qstock'）
        :return: DataFrame or None + 异常提示
        """
        print(f"[Provider]source={source}")
        try:
            # yfinance 不直接支持宏观 GDP 数据，模拟一个错误
            raise NotImplementedError("QStock暂不支持获取宏观GDP数据")
        except Exception as e:
            raise RuntimeError(f"从 QStock 获取 GDP 数据失败: {str(e)}") from e
    def realtime_data(self, category="概念板块"):
        """
        获取实时数据（如概念板块、行业等）
        """
        return qs.realtime_data(category)

import akshare as ak
import pandas as pd
from core.logger import logger
class AkShareProvider:
    # 可用
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
        df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
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
        df = ak.macro_china_gdp()
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
    def get_concept_stocks(self, concept_name):
        df = ak.stock_board_concept_cons_em(symbol=concept_name).sort_values(by='涨跌幅', ascending=False).head(5)
        return df



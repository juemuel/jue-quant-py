import akshare as ak
import pandas as pd
from core.logger import logger
class AkShareProvider:
    # 可用
    def get_all_stocks(self, market=None):
        """
        获取股票列表，支持按市场筛选
        :param market: 'SH'（上交所）, 'SZ'（深交所）, 'BJ'（北交所）, 'CY'（创业板）, 'KE'（科创板）
        :return: DataFrame ['code', 'name']
        """
        logger.info(f"[Provider]source={self.__class__.__name__}, market={market}")

        if market == "SH":
            df = ak.stock_info_sh_name_code()  # 上证市场专用接口
        elif market == "SZ":
            df = ak.stock_info_sz_name_code()  # 深圳市场专用接口
        elif market == "BJ":
            df = ak.stock_info_bj_name_code()  # 北交所专用接口
        else:
            # 默认获取A股所有股票，并做进一步筛选
            df = ak.stock_info_a_code_name()
            if market == "KE":  # 科创板
                df = df[df['code'].astype(str).str.startswith('68')]
            elif market == "CY":  # 创业板
                df = df[df['code'].astype(str).str.startswith('30')]

        df['code'] = df['code'].astype(str).str.zfill(6)
        df['name'] = df['name']
        return df[['code', 'name']]
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



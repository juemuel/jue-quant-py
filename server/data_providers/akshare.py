import time
import akshare as ak
import pandas as pd
from core.logger import logger
class AkShareProvider:
    # 1.1 获取所有股票列表（可用）
    def get_all_stocks(self, source, market=None):
        """
        获取股票列表，支持按市场筛选
        :param market: 'SH'（上交所）, 'SZ'（深交所）, 'BJ'（北交所）, 'CY'（创业板）, 'KE'（科创板）
        :return: DataFrame ['code', 'name']
        """
        logger.info(f"[Provider]source={self.__class__.__name__}, market={market}")

        df = ak.stock_info_a_code_name()
        if market == "SH":  # 上交所
            df = df[df['code'].astype(str).str.startswith('60')]
        elif market == "SZ":  # 深交所（包括创业板）
            df = df[df['code'].astype(str).str.contains(r'^(00|30)', regex=True)]
        elif market == "BJ":  # 北交所（已校对）
            df = df[df['code'].astype(str).str.contains(r'^(43|83|87|92)', regex=True)]
        elif market == "KE":  # 科创板
            df = df[df['code'].astype(str).str.startswith('68')]
        elif market == "CY":  # 创业板
            df = df[df['code'].astype(str).str.startswith('30')]
        else:
            # 默认返回所有A股，不做额外处理
            pass
        # 剔除 ST 和 *ST 开头的股票
        df = df[~df['name'].str.contains(r'\\*ST|^ST', regex=True)]

        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df[['code', 'name']]

    # 1.2 获取所有概念板块列表（可用）
    def get_all_concepts(self):
        """
        获取所有概念板块列表
        :return: DataFrame ['板块代码', '板块名称']
        """
        logger.info(f"[Provider]source={self.__class__.__name__}")
        # 获取所有概念板块列表
        concept_df = ak.stock_board_concept_name_em()
        logger.info(f"[Provider]列名: {concept_df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(concept_df)}")
        return concept_df

    # 1.3 获取概念板块成分股（支持板块代码和板块名称）
    def get_concept_constituent_stocks(self, concept_identifier):
        """
        获取指定概念板块的成分股
        :param concept_identifier: 概念板块标识符（可以是板块代码或板块名称）
        :return: DataFrame ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '最高', '最低', '今开', '昨收']
        """
        logger.info(f"[Provider]source={self.__class__.__name__}, concept_identifier={concept_identifier}")
        
        # 首先获取所有概念板块列表，用于代码和名称的转换
        concept_list_df = ak.stock_board_concept_name_em()
        
        # 判断输入的是板块代码还是板块名称
        if concept_identifier in concept_list_df['板块代码'].values:
            # 输入的是板块代码，需要转换为板块名称
            concept_name = concept_list_df[concept_list_df['板块代码'] == concept_identifier]['板块名称'].iloc[0]
            logger.info(f"[Provider]通过板块代码 {concept_identifier} 找到板块名称: {concept_name}")
        elif concept_identifier in concept_list_df['板块名称'].values:
            # 输入的是板块名称，直接使用
            concept_name = concept_identifier
            logger.info(f"[Provider]直接使用板块名称: {concept_name}")
        else:
            # 既不是有效的板块代码也不是有效的板块名称
            raise ValueError(f"无效的概念板块标识符: {concept_identifier}")
        
        # 获取概念板块成分股
        df = ak.stock_board_concept_cons_em(symbol=concept_name)
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df

    # 2.1 获取股票历史数据（可用）
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

    # 3.1 获取股票实时行情（可用）
    def get_realtime_quotes(self, source, codes=None):
        """
        获取股票实时行情
        :param codes: 股票代码列表(逗号分隔字符串)，如 "000001,000002" 或 None(获取所有)
        :return: DataFrame
        """
        logger.info(f"[Provider]sources={source}")
        df = ak.stock_zh_a_spot_em()
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df

    # 4.1 获取宏观数据（GDP、CPI、PPI、PMI）
    def get_macro_gdp_data(self, source):
        """
        获取宏观GDP数据
        :param source: 数据源名称
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}")
        df = ak.macro_china_gdp()
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
    def get_macro_cpi_data(self, source):
        """
        获取宏观CPI数据
        :param source: 数据源名称
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}")
        df = ak.macro_china_cpi_yearly()
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
    def get_macro_ppi_data(self, source):
        """
        获取宏观PPI数据
        :param source: 数据源名称
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}")
        df = ak.macro_china_ppi_yearly()
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
    def get_macro_pmi_data(self, source):
        """
        获取宏观PMI数据
        :param source: 数据源名称
        :return: DataFrame
        """
        logger.info(f"[Provider]source={source}")
        df = ak.macro_china_pmi()
        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        return df
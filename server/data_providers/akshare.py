import time
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
    def get_concept_stocks(self, concept_name=None):
        try:
            # 获取所有概念列表
            concept_df = ak.stock_board_concept_name_em()
            logger.info(f"[Provider]列名: {concept_df.columns.tolist()}")
            logger.info(f"[Provider]行数: {len(concept_df)}")
            
            # 如果未传参数或空字符串，返回所有概念
            if not concept_name:
                return concept_df[['板块名称', '板块代码']]
            
            # 模糊匹配概念名称
            concept_names = concept_df['板块名称'].tolist()
            matched = [name for name in concept_names if concept_name in name]
            if not matched:
                logger.error(f"[Provider]未找到匹配概念: {concept_name}")
                return pd.DataFrame(columns=['代码', '名称'])
            
            # 使用第一个匹配的概念名称
            concept_name = matched[0]
            
            # 获取概念成分股
            df = ak.stock_board_concept_cons_em(symbol=concept_name)
            if df is None or df.empty:
                logger.error(f"[Provider]空数据 for {concept_name}")
                return pd.DataFrame(columns=['代码', '名称'])
                
            # 确保包含必要列
            if '代码' not in df.columns or '名称' not in df.columns:
                logger.error(f"[Provider]缺少必要列 for {concept_name}")
                return pd.DataFrame(columns=['代码', '名称'])
                
            # 按涨跌幅排序并取前5
            if '涨跌幅' in df.columns:
                df = df.sort_values(by='涨跌幅', ascending=False).head(5)
            else:
                df = df.head(5)
                
            return df[['代码', '名称']]
            
        except Exception as e:
            logger.error(f"[Provider]获取概念成分股最终失败: {str(e)}")
            return pd.DataFrame(columns=['代码', '名称'])

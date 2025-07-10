# data_providers/juejinquant.py

import pandas as pd
from core.logger import logger

class JueJinQuantProvider:
    def __init__(self):
        """
        初始化掘金量化客户端
        可以在这里加载 token 或连接远程服务
        """
        from gm.api import *
        set_token("a7263f5d0383aa67d7400886b936b8e27f145c9e")


    def get_all_stocks(self, market=None):
        """
        获取所有A股股票列表
        :return: DataFrame ['code', 'name']
        """
        logger.info(f"[Provider]{self.__class__.__name__} 正在获取所有股票...")
        from gm.api import get_instruments
        df = get_instruments(market="SHSE, SZSE", sec_type=33, df=True)  # 33 表示股票类型
        df.rename(columns={'symbol': 'code', 'name': 'name'}, inplace=True)
        return df[['code', 'name']]

    def get_stock_history(self, source="juejinquant", code="SHSE.600000", start_date=None, end_date=None, period="1d", count=10):
        """
        获取股票历史行情
        :param source: 数据源名称
        :param code: 股票代码，如 SHSE.600000
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param period: 周期，如 '1d' 表示日线
        :param count: 获取最近多少条数据
        :return: DataFrame
        """
        logger.info(f"[Provider]{source} get_stock_history for {code}")
        if not self.api_ready:
            raise RuntimeError("掘金API未正确初始化")
        from gm.api import history
        df = history(symbol=code, frequency=period, count=count, fields='open,high,low,close,volume', df=True)
        return df

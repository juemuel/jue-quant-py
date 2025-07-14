# data_providers/juejinquant.py
import os
import re

from gm.api import *
import pandas as pd
from core.logger import logger
from dotenv import load_dotenv
# 加载 .env 文件
load_dotenv()
class JueJinQuantProvider:
    def __init__(self):
        """
        初始化掘金量化客户端
        可以在这里加载 token 或连接远程服务
        """
        token = os.getenv("MYQUANT_TOKEN")  # 获取环境变量
        logger.info(f"MYQUANT_TOKEN value: {token}")  # 打印 token 值
        set_token(token)

    def get_all_stocks(self, market=None):
        """
        获取所有A股股票列表
        :return: DataFrame ['code', 'name']
        """
        logger.info(f"[Provider]{self.__class__.__name__} 正在获取所有股票...")
        # 动态选择交易所参数
        exchanges = None
        if market == "SH":
            exchanges = "SHSE"
        elif market == "SZ":
            exchanges = "SZSE"
        elif market == "BJ":
            # 北交所无法直接指定交易所，暂设为 None 并后续通过 code 过滤
            exchanges = None
        else:
            exchanges = "SHSE,SZSE"  # 默认获取沪深两市
        df = get_instruments(exchanges=exchanges, sec_types="1",skip_suspended=True, skip_st=False, df=True)

        # 提取纯数字代码部分，并剔除 B 股
        def is_b_stock(symbol):
            code_part = symbol.split('.')[-1]  # 提取数字部分，例如 "200771"
            if re.match(r'^(900|200|201|202)', code_part):
                return True
            return False
        df = df[~df['symbol'].apply(is_b_stock)]
        # 剔除 ST 和 *ST 开头的股票
        df = df[~df['sec_name'].str.contains(r'\\*ST|^ST', regex=True)]

        logger.info(f"[Provider]列名: {df.columns.tolist()}")
        logger.info(f"[Provider]行数: {len(df)}")
        df.rename(columns={'symbol': 'code', 'sec_name': 'name'}, inplace=True)
        # 若为北交所，使用股票代码格式进行过滤
        if market == "BJ":
            df = df[df['code'].astype(str).str.contains(r'^(43|83|87|92)', regex=True)]
        df.sort_values(by='code', ascending=True, inplace=True)
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

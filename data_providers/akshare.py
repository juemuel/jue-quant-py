# data_providers/akshare.py
import akshare as ak
import pandas as pd

class AkShareProvider:
    def get_stock_history(self, source, code, market, start_date=None, end_date=None):
        print(
            f"[Provider]source={source}, code={code}, market={market}, start_date={start_date}, end_date={end_date}")
        try:
            df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
            if df.empty:
                raise ValueError("获取到的股票历史数据为空")
            return df
        except Exception as e:
            raise RuntimeError(f"从 akshare 获取股票 {code} 数据失败: {str(e)}") from e

    def get_macro_gdp_data(self, source):
        print(f"[Provider]source={source}")
        try:
            df = ak.macro_china_gdp()
            if df.empty:
                raise ValueError("获取到的 GDP 数据为空")
            return df
        except Exception as e:
            raise RuntimeError(f"从 akshare 获取 GDP 数据失败: {str(e)}") from e

    def get_concept_stocks(self, concept_name):
        df = ak.stock_board_concept_cons_em(symbol=concept_name).sort_values(by='涨跌幅', ascending=False).head(5)
        return df



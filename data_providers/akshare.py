# data_providers/akshare.py
import akshare as ak
import pandas as pd

class AkShareProvider:
    def get_stock_history(self, code, start_date=None, end_date=None):
        df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date)
        return df

    def get_concept_stocks(self, concept_name):
        """
        获取某个概念板块下的前五只股票
        :param concept_name: 概念名称，如 "人工智能"
        :return: DataFrame
        """
        df = ak.stock_board_concept_cons_em(symbol=concept_name).sort_values(by='涨跌幅', ascending=False).head(5)
        return df

    def get_macro_gdp_data(self):
        """
        获取中国 GDP 宏观数据（原始 DataFrame 格式）

        :return: pandas.DataFrame 包含字段：
            - 季度（季度）
            - 国内生产总值-同比增长（国内生产总值同比增速）
        """
        df = ak.macro_china_gdp()
        return df

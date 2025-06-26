# data_providers/tushare.py
import tushare as ts
import pandas as pd

class TushareProvider:
    def __init__(self):
        ts.set_token("a1533fd58c006f92b96286c3af7f044ad853d51cf2dec60e8f32b33e")
        self.pro = ts.pro_api()

    def get_stock_history(self, code, start_date=None, end_date=None):
        df = self.pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
        return df

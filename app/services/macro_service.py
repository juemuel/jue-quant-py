import pandas as pd
from ...data_source.macro_data import *
def get_gdp_data():
    df = ak.stock_zh_a_gdp_yearly()
    df['季度'] = df['季度'].str.replace('年', '')
    return df[['季度', '国内生产总值-同比增长']].to_dict(orient='records')

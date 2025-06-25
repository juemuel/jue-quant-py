import pandas as pd
from data_source.stock_data import get_stock_history_data as gshd
def get_stock_history_data(source="tushare", code="000001", market="SH"):
    df = gshd(source=source, code=code, market=f"{code}.{market}")
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    df.rename(columns={'日期': 'date', '收盘': 'close'}, inplace=True)
    return df[['date', 'close']]

from data_providers import get_data_provider

data_provider = get_data_provider()

def get_stock_history_data(source="akshare", code="000001", market="SH"):
    df = data_provider.get_stock_history(code=f"{code}.{market}")
    df['日期'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df.rename(columns={'收盘': 'close'}, inplace=True)
    return df[['日期', 'close']]
from data_providers import get_data_provider
data_provider = get_data_provider('akshare')  # 使用 akshare 数据源
def get_gdp_data():
    df = data_provider.get_macro_gdp_data()
    return df[['季度', '国内生产总值-同比增长']].to_dict(orient='records')


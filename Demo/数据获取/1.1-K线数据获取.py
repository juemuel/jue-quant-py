from common import *

ts.set_token("a1533fd58c006f92b96286c3af7f044ad853d51cf2dec60e8f32b33e")

# 一、获取行情数据（日、周、月）雪球：https://xueqiu.com/S/SH000001 代码、上市日期
def get_stock_history_data(source='akshare', code='', start_date=None, end_date=None):
    # tushare，获取日线数据，一次获得6000条
    if source == 'tushare':
        pro = ts.pro_api()
        df = pro.daily(ts_code=code)
        return df
    # akshare，获取日线数据，默认全部
    elif source == 'akshare':
        df = ak.stock_zh_a_hist(symbol=code, period='daily')
        return df
    elif source == 'efinance':
        df = ef.stock.get_quote_history(code)
        return df
    elif source == 'qstock':
        df = qs.get_data(code)
        return df
    else:
        raise ValueError('不支持的数据源，请输入正确的数据源名称。')


print(get_stock_history_data(source='tushare', code='000651.SZ'))
print(get_stock_history_data(source='akshare', code='000651'))
print(get_stock_history_data(source='efinance', code='000651'))
print(get_stock_history_data(source='qstock', code='000651'))

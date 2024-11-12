from common import *

ts.set_token("a1533fd58c006f92b96286c3af7f044ad853d51cf2dec60e8f32b33e")

# 一、获取历史行情数据（日、周、月）雪球：https://xueqiu.com/S/SH000001 代码、上市日期
# 1. 关于复权，量化中采用的复权方案
# 2. 
def get_stock_history_data(source='akshare', code='', start_date=None, end_date=None):
    # tushare：daily(ts_code, start_date, end_date)，一次6000条
    # ts_code：股票代码，如：000001.SZ，可以多个000001.SZ,600000.SH
    # start_date：开始日期YYYYMMDD，如：20200101
    # end_date：结束日期YYYYMMDD，如：20200601
    # returns：DataFrame：open、high、low、close、pre_close、change涨跌额、pct_chg涨跌幅、vol成交量（手）、amount金额（千元）
    # doc：https://tushare.pro/document/2?doc_id=27
    if source == 'tushare':
        pro = ts.pro_api()
        df = pro.daily(ts_code=code+'.SZ', start_date=start_date, end_date=end_date)
        return df
    # akshare：stock_zh_a_daily(symbol, period, adjust, start_date, end_date)
    # symol ：股票代码，如：600519
    # period：周期，daily、weekly、monthly
    # adjust：复权，qfq：前复权，hfq：后复权, bfq：不复权默认
    # start_date：开始日期YYYYMMDD，如：20200101
    # end_date：结束日期YYYYMMDD，如：20200601
    # returns：DataFrame：日期、开盘价、收盘价、最高价、最低价、成交量、成交额、振幅、涨跌幅、涨跌额、换手率
    # doc：https://akshare.akfamily.xyz/data/stock/stock.html
    elif source == 'akshare':
        df = ak.stock_zh_a_hist(symbol=code, period='daily', adjust='hfq', start_date=start_date, end_date=end_date)
        # df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        return df
    # efinance：get_quote_history(ts_code)，一次6000条
    # ts_code：股票代码，如：600519
    # doc：https://efinance.readthedocs.io/en/latest/index.html
    elif source == 'efinance':
        df = ef.stock.get_quote_history(code, start_date=start_date, end_date=end_date)
        return df
    elif source == 'qstock':
        df = qs.get_data(code)
        return df
    else:
        raise ValueError('不支持的数据源，请输入正确的数据源名称。')


# print(get_stock_history_data(source='tushare', code='000651.SZ'))
# print(get_stock_history_data(source='akshare', code='000651'))
# print(get_stock_history_data(source='efinance', code='000651'))
# print(get_stock_history_data(source='qstock', code='000651'))
# 示例调用
if __name__ == "__main__":
    source = 'efinance'  # 数据源
    code = '000001'  # 股票代码
    start_date = '20180101'  # 开始日期
    end_date = '20201113'  # 结束日期

    data = get_stock_history_data(source=source, code=code, start_date=start_date, end_date=end_date)
    print(data)
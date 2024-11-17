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
    # returns: DataFrame：代码，日期，开盘，收盘，最高，最低，成交量，成交额，涨跌幅，涨跌额，*昨收'、
    # doc：https://tushare.pro/document/2?doc_id=27
    if source == 'tushare':
        pro = ts.pro_api()
        df = pro.daily(ts_code=code+'.SZ', start_date=start_date, end_date=end_date)
        df = df.sort_values(by='trade_date', ascending=True)
        df = df.rename(columns={
            'ts_code': '代码',
            'trade_date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'pre_close': '*昨收', # 唯一
            'pct_chg': '涨跌幅',
            'change': '涨跌额',
            'vol': '成交量', # 手-小数点两位
            'amount': '成交额' # 千元
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额','*昨收']]
        # 去除代码中的 .SZ 后缀
        df['代码'] = df['代码'].str.replace('.SZ', '')
        # 将日期格式转换为 YYYY-MM-DD
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        return df
    # akshare：stock_zh_a_daily(symbol, period, adjust, start_date, end_date)
        # symol ：股票代码，如：600519
        # period：周期，daily、weekly、monthly
        # adjust：复权，qfq：前复权，hfq：后复权, bfq：不复权默认
        # start_date：开始日期YYYYMMDD，如：20200101
        # end_date：结束日期YYYYMMDD，如：20200601
    # returns：DataFrame(默认逆序)：[代码] + 日期、开盘价、收盘价、最高价、最低价、成交量（手-四舍五入）、成交额、*振幅、涨跌幅、涨跌额、*换手率
    # doc：https://akshare.akfamily.xyz/data/stock/stock.html
    elif source == 'akshare':
        df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date)
        df['代码'] = code
        df = df.sort_values(by='日期', ascending=True)
        df = df.rename(columns={
            '振幅': '*振幅',
            '换手率': '*换手率',
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '涨跌幅', '涨跌额', '*振幅', '*换手率']]
        return df
    # efinance：get_quote_history(stock_codes, beg, end, klt)
        # stock_codes：股票代码，如：600519或str[]
        # beg：开始日期YYYYMMDD，如：20200101
        # end：结束日期YYYYMMDD，如：20200601
        # klt：周期，1：1分钟，5：5分钟，15：15分支，101日，102周，103月
        # fqt: 复权，0：不复权，1：前复权，2：后复权
        # market_type: A_stock : A股，Hongkong : 香港；London_stock_exchange : 英股；US_stock : 美股；默认不分
    # DataFrame: [股票名称，股票代码，日期，开盘，收盘，最高，最低，成交量，成交额，*振幅，涨跌幅，涨跌额, *换手率]
    # doc：https://efinance.readthedocs.io/en/latest/api.html#efinance.stock.get_quote_history
    elif source == 'efinance':
        df = ef.stock.get_quote_history(code, beg=start_date, end=end_date)
        df = df.rename(columns={
            '股票代码': '代码',
        })
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
    source = 'tushare'  # 数据源
    code = '000001'  # 股票代码
    start_date = '20201101'  # 开始日期
    end_date = '20201113'  # 结束日期

    # df_tushare = get_stock_history_data(source='tushare', code=code, start_date=start_date, end_date=end_date)
    # print(df_tushare)
    
    # df_akshare = get_stock_history_data(source='akshare', code=code, start_date=start_date, end_date=end_date)
    # print(df_akshare)
    
    df_efinance = get_stock_history_data(source='efinance', code=code, start_date=start_date, end_date=end_date)
    print(df_efinance)
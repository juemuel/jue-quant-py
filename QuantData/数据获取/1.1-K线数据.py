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
    # returns: DataFrame：代码，日期，开盘，收盘，最高，最低，成交量，成交额，涨跌幅，涨跌额，*昨收
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
            'pre_close': '昨收_tushare', # 唯一
            'pct_chg': '涨跌幅',
            'change': '涨跌额',
            'vol': '成交量', # 手-小数点两位
            'amount': '成交额' # 千元
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额','昨收_tushare']]
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
    # returns：DataFrame：[代码] + 日期，开盘，收盘，最高，最低，成交量，成交额，涨跌幅，涨跌额，*振幅，*换手率
    # doc：https://akshare.akfamily.xyz/data/stock/stock.html
    elif source == 'akshare':
        df = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date)
        df['代码'] = code
        df = df.sort_values(by='日期', ascending=True)
        df = df.rename(columns={
            '振幅': '振幅_akshare',
            '换手率': '换手率_akshare',
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '涨跌幅', '涨跌额', '振幅_akshare', '换手率_akshare']]
        return df
    # efinance：get_quote_history(stock_codes, beg, end, klt)
        # stock_codes：股票代码，如：600519或str[]
        # beg：开始日期YYYYMMDD，如：20200101
        # end：结束日期YYYYMMDD，如：20200601
        # klt：周期，1：1分钟，5：5分钟，15：15分钟，101日，102周，103月
        # fqt: 复权，0：不复权，1：前复权，2：后复权
        # market_type: A_stock : A股，Hongkong : 香港；London_stock_exchange : 英股；US_stock : 美股；默认不分
    # DataFrame: 代码，日期，开盘，收盘，最高，最低，成交量，成交额，涨跌幅，涨跌额, *振幅，*换手率，*名称
    # doc：https://efinance.readthedocs.io/en/latest/api.html#efinance.stock.get_quote_history
    elif source == 'efinance':
        df = ef.stock.get_quote_history(code, beg=start_date, end=end_date)
        df = df.rename(columns={
            '股票名称': '股票名称_efinance',
            '股票代码': '代码',
            '振幅': '振幅_efinance',
            '换手率': '换手率_efinance'
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '涨跌幅', '涨跌额', '振幅_efinance', '换手率_efinance', '股票名称_efinance']]
        return df
    # qstock: get_data(code_list, start, end, freq, fqt)
        # code_list：名称、代码字符串或列表，如：'600519'，'中国平安'，['600519','000651']
        # start：
        # end：默认None
        # freq：周期，默认日，1：1分钟（最近5个交易日），5：5分钟，15：15分钟，30，60；101或'D'或'd'：日；102或‘w’或'W'：周; 103或'm'或'M': 月
        # fqt：复权，0：不复权，1：前复权；2：后复权，默认前复权
    # DataFrame: [代码] + 股票名称, 日期, 开盘, 最高, 最低, 收盘, 成交量, 成交额, 换手率
    # doc: https://github.com/tkfy920/qstock
    elif source == 'qstock':
        df = qs.get_data(code_list=code, start=start_date, end=end_date, freq='d', fqt=1)
        df = df.reset_index() # 将索引设为普通列
        df = df.rename(columns={
            'code': '代码',
            'name': '股票名称_qstock',
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'volume': '成交量',
            'turnover': '成交额',
            'turnover_rate': '换手率_qstock'
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '换手率_qstock', '股票名称_qstock']]
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
    end_date = '20201110'  # 结束日期

    df_tushare = get_stock_history_data(source='tushare', code=code, start_date=start_date, end_date=end_date)
    print(df_tushare)
    df_akshare = get_stock_history_data(source='akshare', code=code, start_date=start_date, end_date=end_date)
    print(df_akshare)
    df_efinance = get_stock_history_data(source='efinance', code=code, start_date=start_date, end_date=end_date)
    print(df_efinance)
    df_qstock = get_stock_history_data(source='qstock', code=code, start_date=start_date, end_date=end_date)
    print(df_qstock)
    # 3. 重命名列并选择所需的列
    columns = ['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额', '昨收_tushare',
               '振幅_akshare', '换手率_akshare', '振幅_efinance', '换手率_efinance', '股票名称_efinance',
               '换手率_qstock', '股票名称_qstock']
    df_tushare = df_tushare.reindex(columns=columns)
    df_akshare = df_akshare.reindex(columns=columns)
    df_efinance = df_efinance.reindex(columns=columns)
    df_qstock = df_qstock.reindex(columns=columns)

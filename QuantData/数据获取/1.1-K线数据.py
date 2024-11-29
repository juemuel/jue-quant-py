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
            'pre_close': '昨收', # 补充项
            'pct_chg': '涨跌幅',
            'change': '涨跌额',
            'vol': '成交量', # 手-小数点两位
            'amount': '成交额' # 千元
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额','昨收']]
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
            '振幅': '振幅', # 补充项
            '换手率': '换手率', # 补充项
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '涨跌幅', '涨跌额', '振幅', '换手率']]
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
            '股票名称': '股票名称',  # 补充项
            '股票代码': '代码',
            '振幅': '振幅',  # 补充项
            '换手率': '换手率'  # 补充项
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '涨跌幅', '涨跌额', '振幅', '换手率', '股票名称']]
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
            'name': '股票名称', # 补充项
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'volume': '成交量',
            'turnover': '成交额',
            'turnover_rate': '换手率' # 补充项
        })
        df = df[['代码', '日期', '开盘', '收盘', '最高', '最低', '成交量','成交额', '换手率', '股票名称']]
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
    # 定义允许的误差范围
    error_threshold = 0.05

    df_tushare = get_stock_history_data(source='tushare', code=code, start_date=start_date, end_date=end_date)
    print(df_tushare)
    df_akshare = get_stock_history_data(source='akshare', code=code, start_date=start_date, end_date=end_date)
    print(df_akshare)
    df_efinance = get_stock_history_data(source='efinance', code=code, start_date=start_date, end_date=end_date)
    print(df_efinance)
    df_qstock = get_stock_history_data(source='qstock', code=code, start_date=start_date, end_date=end_date)
    print(df_qstock)

    # 2. 统一日期列的类型
    df_tushare['日期'] = pd.to_datetime(df_tushare['日期'])
    df_akshare['日期'] = pd.to_datetime(df_akshare['日期'])
    df_efinance['日期'] = pd.to_datetime(df_efinance['日期'])
    df_qstock['日期'] = pd.to_datetime(df_qstock['日期'])
    # 3. 重命名列以确保唯一性
    df_tushare = df_tushare.add_suffix('_tushare')
    df_akshare = df_akshare.add_suffix('_akshare')
    df_efinance = df_efinance.add_suffix('_efinance')
    df_qstock = df_qstock.add_suffix('_qstock')
    # 4. 保留一组用于合并的键名，开始合并数据
    df_tushare.rename(columns={'代码_tushare': '代码', '日期_tushare': '日期'}, inplace=True)
    df_akshare.rename(columns={'代码_akshare': '代码', '日期_akshare': '日期'}, inplace=True)
    df_efinance.rename(columns={'代码_efinance': '代码', '日期_efinance': '日期'}, inplace=True)
    df_qstock.rename(columns={'代码_qstock': '代码', '日期_qstock': '日期'}, inplace=True)
    merged_df = pd.merge(df_tushare, df_akshare, on=['代码', '日期'], how='outer')
    merged_df = pd.merge(merged_df, df_efinance, on=['代码', '日期'], how='outer')
    merged_df = pd.merge(merged_df, df_qstock, on=['代码', '日期'], how='outer')
    merged_df = merged_df.drop_duplicates(subset=['代码', '日期'])
    # 4. 构造新的 DataFrame
    new_df = merged_df[['代码', '日期']].copy()
    # 需要比较的字段
    fields_to_compare = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额', '昨收', '振幅',
                         '换手率']
    for field in fields_to_compare:
        # 检查字段是否存在
        sources = ['tushare', 'akshare', 'efinance', 'qstock']
        columns = [f'{field}_{source}' for source in sources]
        exists = {col: col in merged_df.columns for col in columns}

        # 检查字段在哪些数据源中存在
        existing_sources = [source for source in sources if exists[f'{field}_{source}']]
        num_existing_sources = len(existing_sources)

        if num_existing_sources == 0:
            # 字段在所有数据源中均不存在
            new_df[field + '_不存在'] = '不存在'
        elif num_existing_sources == 1:
            # 字段只在一个数据源中存在
            existing_col = f'{field}_{existing_sources[0]}'
            new_df[field + '_noCheck'] = merged_df[existing_col].fillna('不存在')
        else: # 3. 字段在多个数据源中存在，进行校验
            # 3.1 确定一个参考列，用于计算误差
            reference_col = f'{field}_tushare'
            if reference_col not in merged_df.columns:
                reference_col = f'{field}_{existing_sources[0]}'
            # 2. 生成当前字段的误差列表errors，每个元素是一个三元组 (source, col, error)，其中 source 是数据源名称，col 是列名，error 是误差 Series
            errors = []
            for source in existing_sources:
                col = f'{field}_{source}'
                if col in merged_df.columns:
                    error = abs(merged_df[reference_col] - merged_df[col]) / merged_df[reference_col]
                    errors.append((source, col, error))
            # 判断误差是否在允许范围内
            if errors:
                all_errors = pd.concat([e[2] for e in errors], axis=1).max(axis=1)
                new_df[field + '_checked'] = merged_df.apply(
                    lambda row: (
                        '无误差' if all_errors.loc[row.name] <= error_threshold or all_errors.loc[row.name] == 0
                        else '有误差'
                    ),
                    axis=1
                )
                # 收集具体的误差信息
                specific_errors = merged_df.apply(
                    lambda row: (
                        f"有误差: {', '.join([f'{e[0]}: {row[e[1]]} (误差: {abs(row[reference_col] - row[e[1]]) / row[reference_col]:.6f})' for e in errors if row[e[1]] is not None and abs(row[reference_col] - row[e[1]]) > error_threshold * row[reference_col]])}"                        if all_errors.loc[row.name] > error_threshold
                        else ''
                    ),
                    axis=1
                )
                # 打印具体的误差信息
                for idx, error_info in specific_errors.items():
                    if error_info:
                        print(
                            f"日期: {merged_df.loc[idx, '日期']}, 代码: {merged_df.loc[idx, '代码']}, {field}: {error_info}")
            else:
                new_df[field + '_checked'] = merged_df[reference_col]

    # 输出结果
    print(new_df)

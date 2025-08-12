from common import *
import akshare as ak


# 一、获取当日股票行情数据
def get_stock_current_data(source='akshare'):
    # akshare：stock_fund_flow_individual(symbol)
        # symbol：“即时”, "3日排行", "5日排行", "10日排行", "20日排行"
    # returns:
    # doc：https://tushare.pro/document/2?doc_id=27
    if source == 'akshare':
        df = ak.stock_fund_flow_individual(symbol='即时')
        # 格式化某些列的数据类型
        df['流入资金'] = df['流入资金'].apply(format_number)
        df['流出资金'] = df['流出资金'].apply(format_number)
        df['净额'] = df['净额'].apply(format_number)
        df['成交额'] = df['成交额'].apply(format_number)
        # 格式化股票代码
        df['股票代码'] = df['股票代码'].apply(format_stock_code)
        df = df.sort_values(by='股票代码', ascending=True)
        df = df[
            ['股票代码', '股票简称', '最新价', '涨跌幅', '成交额', '流入资金', '流出资金', '净额', '换手率']]
        return df
    else:
        raise ValueError('不支持的数据源，请输入正确的数据源名称。')


# 辅助函数：将带有单位的数字字符串转换为浮点数
def format_number(num_str):
    if '万' in num_str:
        num = float(num_str.replace('万', '')) * 10000
    elif '亿' in num_str:
        num = float(num_str.replace('亿', '')) * 100000000
    else:
        num = float(num_str)
    return round(num, 2)
# 辅助函数：格式化股票代码，确保其长度为6位
def format_stock_code(code):
    return str(code).zfill(6)

# 示例调用
if __name__ == "__main__":
    source = 'akshare'  # 数据源
    df = get_stock_current_data(source=source)
    print(df)

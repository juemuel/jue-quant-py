from common import *

# 一、获取实时数据（日、周、月）
def format_number(num_str):
    if '万' in num_str:
        num = float(num_str.replace('万', ''))
    elif '亿' in num_str:
        num = float(num_str.replace('亿', '')) * 10000
    else:
        num = float(num_str)
    # print(f"当前元素内容为：{num_str}返回元素内容为：{num}")  # 输出当前元素的内容
    round(float(num), 2)
    return num

# 流入资金
# 流出资金
# 净额
# 成交额
def get_stock_flow(source=''):
    if source == 'akshare':
        df = ak.stock_fund_flow_individual(symbol='即时')
        # 将以下数据表元素转为了float并排序
        df['流入资金'] = df['流入资金'].apply(format_number)
        df['流出资金'] = df['流出资金'].apply(format_number)
        df['净额'] = df['净额'].apply(format_number)
        df['成交额'] = df['成交额'].apply(format_number)
        df_res = df.sort_values(by='净额', ascending=False)
        return df_res
    else:
        raise ValueError('不支持的数据源，请输入正确的数据源名称.')


df = get_stock_flow(source='akshare')
print(tabulate(df, headers='keys', tablefmt='psql'))


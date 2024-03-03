# pip install akshare --upgrade
# pip install efinance --upgrade
# pip install qstock -–upgrade
# TuShare  https://tushare.pro/document/1       https://tushare.pro/document/2
# AKShare  https://akshare.akfamily.xyz/introduction.html      https://akshare.akfamily.xyz/data/index.html
# Efinance https://github.com/Micro-sheep/efinance      https://efinance.readthedocs.io/en/latest/
# Qstock https://pypi.org/project/qstock/
import tushare as ts
import akshare as ak
import efinance as ef
import qstock as qs
import pandas as pd

# 设置显示的最大列数
pd.set_option('display.max_columns', None)
# 设置显示的最大行数
pd.set_option('display.max_rows', None)
# 设置显示每列的最大宽度
pd.set_option('display.max_colwidth', None)
# 设置显示小数的精度
pd.set_option('display.precision', 2)
# 设置是否显示科学计数法
pd.set_option('display.float_format', '{:.2f}'.format)

# 一、获取实时数据（日、周、月）
def get_stock_flow(source=''):
    if source == 'akshare':
        df = ak.stock_fund_flow_individual(symbol='即时')
        df_res = df.sort_values(by='流入资金', ascending=False)
        return df_res
    else:
        raise ValueError('不支持的数据源，请输入正确的数据源名称。')


print(get_stock_flow(source='akshare'))

# def convert_to_wan(value):
#     if '亿' in value:
#         return float(value.replace('亿', '')) * 10000
#     else:
#         return float(value.replace('万', ''))
        # df['流入资金'] = df['流入资金'].apply(convert_to_wan)
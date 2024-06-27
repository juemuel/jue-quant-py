# pip install tushare --upgrade
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
from tabulate import tabulate
import time
import random

# 设置显示的最大列数
pd.set_option('display.max_columns', None)
# 设置显示的最大行数
pd.set_option('display.max_rows', None)
# 设置显示每列的最大宽度
pd.set_option('display.max_colwidth', None)
# 设置不换行
pd.set_option('expand_frame_repr', False)
# 设置显示小数的精度
pd.set_option('display.precision', 2)
# 设置是否显示科学计数法
pd.set_option('display.float_format', '{:.2f}'.format)

token = 'a1533fd58c006f92b96286c3af7f044ad853d51cf2dec60e8f32b33e'
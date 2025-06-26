# common/settings.py
import pandas as pd

# Pandas 显示设置
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.precision', 2)
pd.set_option('display.float_format', '{:.2f}'.format)

DATA_PROVIDER = "akshare"
LOG_LEVEL = "INFO"
DEBUG = True

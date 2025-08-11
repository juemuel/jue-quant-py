# data_providers/gm_proxy.py
import pandas as pd
# 确保pandas配置正确
pd.set_option('display.precision', 4)

# 只导入需要的函数
from gm.api import set_token as _set_token
from gm.api import get_instruments as _get_instruments
from gm.api import history as _history

# 重新导出函数
def set_token(token):
    return _set_token(token)

def get_instruments(*args, **kwargs):
    return _get_instruments(*args, **kwargs)

def history(*args, **kwargs):
    return _history(*args, **kwargs)

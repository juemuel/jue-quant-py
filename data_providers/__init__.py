from .juejinquant import JueJinQuantProvider
from .tushare import TushareProvider
from .akshare import AkShareProvider
# from .qstock import QStockProvider
from .yfinance import YFinanceProvider  # 新增
from .juejinquant import JueJinQuantProvider

default_provider = 'akshare'

provider_map = {
    'tushare': TushareProvider,
    'akshare': AkShareProvider,
    # QSOTCK：py_mini_racer冲突
    # 'qstock': QStockProvider,
    'yfinance': YFinanceProvider,
    'juejinquant': JueJinQuantProvider
}

def get_data_provider(name: str = default_provider):
    provider_class = provider_map.get(name)
    if not provider_class:
        raise ValueError(f"Unsupported data provider: {name}")
    return provider_class()

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
    'yfinance': YFinanceProvider,
    'juejinquant': JueJinQuantProvider
    # 'qstock': QStockProvider, # py_mini_racer冲突
}

def get_data_provider(name: str = default_provider):
    provider_class = provider_map.get(name)
    if not provider_class:
        raise ValueError(f"Unsupported data provider: {name}")
    return provider_class()

from .tushare import TushareProvider
from .akshare import AkShareProvider
from .qstock import QStockProvider
from .yfinance import YFinanceProvider  # 新增

default_provider = 'akshare'

provider_map = {
    'tushare': TushareProvider,
    'akshare': AkShareProvider,
    'qstock': QStockProvider,
    'yfinance': YFinanceProvider  # 新增
}

def get_data_provider(name: str = default_provider):
    provider_class = provider_map.get(name)
    if not provider_class:
        raise ValueError(f"Unsupported data provider: {name}")
    return provider_class()

import logging
from core.logger import logger
from data_providers import get_data_provider
import pandas as pd
data_provider = get_data_provider('akshare')  # 使用 akshare 数据源
# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
logging.getLogger('uvicorn').handlers = []
def get_gdp_data(source="akshare"):
    """
    获取国内GDP数据
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    """
    logger.info(f"[Bridge]获取gdp数据并标准化输出格式 from {source}")

    data_provider = get_data_provider(source)
    try:
        df = data_provider.get_macro_gdp_data(source=source)

        if source == "akshare":
            result = df[['季度', '国内生产总值-同比增长']].to_dict(orient='records')
        elif source == "tushare":
            df['季度'] = df['year'].astype(str) + df['quarter']
            df['国内生产总值-同比增长'] = df['gdp_yoy'].astype(str) + "%"
            result = df[['季度', '国内生产总值-同比增长']].to_dict(orient='records')
        else:
            raise ValueError(f"Unsupported data source: {source}")

        return result
    except Exception as e:
        logger.error(f"获取宏观GDP数据失败: {str(e)}", exc_info=True)
        raise  # 继续向上抛出，由 router 层处理



from core.logger import logger
from data_providers import get_data_provider
import pandas as pd
def get_gdp_data(source="akshare"):
    """
    获取国内GDP数据
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    """
    logger.info(f"[Bridge]获取gdp数据并标准化输出格式 from {source}")
    try:
        data_provider = get_data_provider(source)
        df = data_provider.get_macro_gdp_data(source=source)
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source}")
            return {"status": 'error', "message": "未查询到数据"}
        # 根据不同数据源映射字段名
        if source == "akshare":
            result = df[['季度', '国内生产总值-同比增长']].to_dict(orient='records')
        elif source == "tushare":
            df['季度'] = df['year'].astype(str) + df['quarter']
            df['国内生产总值-同比增长'] = df['gdp_yoy'].astype(str) + "%"
            result = df[['季度', '国内生产总值-同比增长']].to_dict(orient='records')
        else:
            return {"status": 'error', "message": "不支持的数据源"}
        return {"status": 'success', "data": result}
    except Exception as e:
        logger.error(f"[Service]获取gdp数据失败 {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}



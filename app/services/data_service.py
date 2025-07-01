import logging
from core.logger import logger
from data_providers import get_data_provider
import pandas as pd

data_provider = get_data_provider()
# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
logging.getLogger('uvicorn').handlers = []
def get_stock_history(source="akshare", code="000001", market="SH", start_date: str = None, end_date: str = None):
    """
    获取股票历史行情数据并标准化输出格式
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    :param code: 股票代码
    :param market: 市场（SH/SZ）
    :param start_date：开始日期
    :param end_date：结束日期
    :return: DataFrame 包含 ['日期', 'close']
    """
    logger.info(f"[Bridge]获取股票历史行情数据并标准化输出格式 for {code}.{market} from {source}")
    try:
        df = data_provider.get_stock_history(source=source, code=code, market=market, start_date=start_date, end_date=end_date)

        if df.empty:
            logger.warning(f"No data returned from {source} for {code}.{market}")
            return {"error": f"No data found for {code}"}

        # 统一列名（如果数据源使用不同命名）
        column_mapping = {
            'date': '日期',
            'trade_date': '日期',
            '日期': '日期',
            'close': '收盘',
            '收盘': '收盘'
        }

        df.rename(columns=column_mapping, inplace=True)

        # 确保 '日期' 存在且格式正确
        if '日期' not in df.columns:
            logger.error(f"Missing '日期' column from {source} data")
            return {"error": f"Data from {source} missing '日期' field"}

        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')

        # 返回指定字段
        if '收盘' not in df.columns:
            logger.error(f"Missing '收盘' column from {source} data")
            return {"error": f"Data from {source} missing '收盘' field"}

        return df[['日期', '收盘']].to_dict(orient='records')

    except Exception as e:
        logger.exception("Error fetching stock history data")
        return {"error": str(e)}
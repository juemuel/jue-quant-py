import logging
from core.logger import logger
from data_providers import get_data_provider
import pandas as pd

# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
logging.getLogger('uvicorn').handlers = []


def get_stock_history(source="akshare", code="000001", market="SH", start_date: str = None, end_date: str = None):
    """
    获取股票历史行情数据并标准化输出格式
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
                akshare不支持外网

    :param code: 股票代码
    :param market: 市场（SH/SZ）
    :param start_date：开始日期
    :param end_date：结束日期
    :return: DataFrame 包含 ['日期', 'close']
    """
    logger.info(f"[Bridge]获取股票历史行情数据并标准化输出格式 for {code}.{market} from {source}")
    try:
        data_provider = get_data_provider(source)
        df = data_provider.get_stock_history(source=source, code=code, market=market, start_date=start_date, end_date=end_date)
        if df.empty:
            logger.warning(f"No data returned from {source} for {code}.{market}")
            return {"error": f"No data found for {code}"}
        # 根据不同数据源映射字段名
        if source == "akshare":
            required_columns = {
                '日期': '日期',
                '开盘': '开盘价',
                '收盘': '收盘价',
                '最高': '最高价',
                '最低': '最低价',
                '成交量': '成交量'
            }
        elif source == "tushare":
            required_columns = {
                'trade_date': '日期',
                'open': '开盘价',
                'close': '收盘价',
                'high': '最高价',
                'low': '最低价',
                'vol': '成交量'
            }
        elif source == "qstock":
            required_columns = {
                'date': '日期',
                'open': '开盘价',
                'close': '收盘价',
                'high': '最高价',
                'low': '最低价',
                'volume': '成交量'
            }
        elif source == "yfinance":
            required_columns = {
                'Date': '日期',
                'Open': '开盘价',
                'Close': '收盘价',
                'High': '最高价',
                'Low': '最低价',
                'Volume': '成交量'
            }
        else:
            raise ValueError(f"不支持的数据源: {source}")
        # 检查并重命名字段
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            raise KeyError(f"数据源 {source} 返回的数据缺少字段: {', '.join(missing_cols)}")
        df.rename(columns=required_columns, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        return df[['日期', '开盘价', '收盘价', '最高价', '最低价', '成交量']].to_dict(orient='records')
    except Exception as e:
        logger.exception("Error fetching stock history data")
        return {"error": str(e)}
from core.logger import logger
from data_providers import get_data_provider
import pandas as pd
def get_all_stocks(source="akshare", market=None):
    """
    获取所有股票列表
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    :return: DataFrame 包含 ['代码', '名称']
    """
    logger.info(f"[Bridge]获取所有股票 from {source}")
    try:
        data_provider = get_data_provider(source)
        df = data_provider.get_all_stocks(market=market)
        if df.empty:
            logger.warning(f"[Service]无数据返回 {source}")
            return {"status": 'error', "message": "未查询到数据"}
        # 标准化字段名
        if source in ["akshare", "tushare", "juejinquant"]:
            required_columns = {
                'code': '代码',
                'name': '名称'
            }
        else:
            return {"status": 'error', "message": "不支持的数据源"}
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.warning(f"[Service]缺少关键列 {source}: {', '.join(missing_cols)}")
            return {"status": 'error', "message": f"缺少关键列: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
        return {"status": 'success', "data": df[['代码', '名称']].to_dict(orient='records')}
    except Exception as e:
        logger.error(f"[Service]获取所有股票失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}

def get_stock_history(source="akshare", code="000001", market="SH", start_date: str = None, end_date: str = None):
    """
    获取股票历史行情数据并标准化输出格式
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
                akshare不支持外网
                tuashre没有日期
                qsotck必须外网
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
            logger.warning(f"[Service]无数据返回 {source} for {code}.{market}")
            return {"status": 'error', "message": "未查询到数据"}
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
            return {"status": 'error', "message": "不支持的数据源"}
        # 检查并重命名字段
        missing_cols = [col for col in required_columns.keys() if col not in df.columns]
        if missing_cols:
            logger.warning(f"[Service]缺少关键列 {source}: {', '.join(missing_cols)}")
            return {"status": 'error', "message": f"缺少关键列: {', '.join(missing_cols)}"}
        df.rename(columns=required_columns, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        return {"status": 'success', "message": "获取成功", "data": df[['日期', '开盘价', '收盘价', '最高价', '最低价', '成交量']].to_dict(orient='records')}
    except Exception as e:
        logger.error(f"[Service]获取股票历史行情数据失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}
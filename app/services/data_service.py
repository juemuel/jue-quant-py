from core.logger import logger
from data_providers import get_data_provider
import pandas as pd
def get_all_stocks(source="akshare", market=None, page=1, page_size=100, fields=None):
    """
    获取所有股票列表
    :param source: 数据源名称（akshare/tushare/juejinquant）
        akshare 无限制
        tushare 限制次数（积分要求）
        juejinquant 需下载终端
        qstock 移除
    :param market: 交易所名称（SH/SZ/BJ/KE/CY）
    :param page: 页码
    :param page_size: 每页数量
    :param fields: 返回字段,逗号分隔
    :return: 分页后的股票列表
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
        
        # 字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['代码', '名称']]
            
        # 分页处理
        total = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        paged_df = df.iloc[start:end]
        
        return {
            "status": 'success', 
            "data": paged_df.to_dict(orient='records'),
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        logger.error(f"[Service]获取所有股票失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}

def get_stock_history(source="akshare", code="000001", market="SH", start_date: str = None, end_date: str = None, fields: str = "date,open,close,high,low,volume"):
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
        
        # 字段过滤
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            available_fields = [col for col in field_list if col in df.columns]
            if not available_fields:
                return {"status": "error", "message": "请求的字段不存在"}
            df = df[available_fields]
        else:
            df = df[['日期', '开盘价', '收盘价', '最高价', '最低价', '成交量']]
            
        return {
            "status": 'success', 
            "message": "获取成功", 
            "data": df.to_dict(orient='records')
        }
    except Exception as e:
        logger.error(f"[Service]获取股票历史行情数据失败: {e}")
        return {"status": 'error', "message": f"获取失败：{e}"}

def get_macro_data(source="akshare", indicator="GDP", start_date=None, end_date=None):
    """
    获取宏观经济数据
    :param source: 数据源名称
    :param indicator: 指标名称(GDP/CPI/PPI等)
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 标准化后的宏观经济数据
    """
    logger.info(f"[Bridge]获取宏观经济数据 {indicator} from {source}")
    try:
        data_provider = get_data_provider(source)
        if indicator == "GDP":
            df = data_provider.get_macro_gdp_data(source=source)
        else:
            return {"status": "error", "message": "暂不支持该指标"}
        if df.empty:
            return {"status": "error", "message": "未查询到数据"}
        
        # 标准化字段
        df.rename(columns={
            "date": "日期",
            "value": "数值",
            "indicator": "指标"
        }, inplace=True)
        
        return {
            "status": "success",
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"[Service]获取宏观经济数据失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

def get_concept_stocks(source="akshare", concept=None):
    """
    获取概念板块成分股
    :param source: 数据源名称
    :param concept: 概念板块名称
    :return: 概念板块成分股列表
    """
    logger.info(f"[Bridge]获取概念板块成分股 {concept} from {source}")
    try:
            
        data_provider = get_data_provider(source)
        df = data_provider.get_concept_stocks(concept_name=concept)
        
        # 严格检查数据有效性
        if df is None:
            logger.error(f"[Service]数据源返回None: {source} for {concept}")
            return {"status": "error", "message": "数据源返回无效结果"}
            
        if not isinstance(df, pd.DataFrame):
            logger.error(f"[Service]返回类型不是DataFrame: {type(df)}")
            return {"status": "error", "message": "数据格式不正确"}
            
        if df.empty or len(df) == 0:
            logger.warning(f"[Service]空DataFrame: {source} for {concept}")
            return {"status": "error", "message": f"未找到概念板块'{concept}'或该板块无成分股"}
            
        # 检查必要字段是否存在
        required_columns = ["代码", "名称"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"[Service]缺少字段: {missing_cols}")
            return {"status": "error", "message": f"数据缺少必要字段: {', '.join(missing_cols)}"}
            
        # 确保有至少一行数据
        if len(df.index) == 0:
            return {"status": "error", "message": "获取到的成分股列表为空"}
            
        # 标准化字段 - 保持中文列名不变
        df = df.copy()  # 避免SettingWithCopyWarning
        df = df[["代码", "名称"]].copy()
        
        # 返回前5条记录
        top5_df = df.head(5).copy()
        
        return {
            "status": "success",
            "data": top5_df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"[Service]获取概念板块成分股失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

def get_realtime_quotes(source="akshare", codes=None):
    """
    获取股票实时行情
    :param source: 数据源名称
    :param codes: 股票代码列表(逗号分隔)
    :return: 实时行情数据
    """
    logger.info(f"[Bridge]获取实时行情 from {source}")
    try:
        data_provider = get_data_provider(source)
        df = data_provider.get_realtime_quotes(codes=codes)
        if df.empty:
            return {"status": "error", "message": "未查询到数据"}
            
        # 标准化字段
        df.rename(columns={
            "code": "代码",
            "name": "名称",
            "price": "最新价",
            "change": "涨跌幅",
            "volume": "成交量"
        }, inplace=True)
        
        return {
            "status": "success",
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"[Service]获取实时行情失败: {e}")
        return {"status": "error", "message": f"获取失败: {e}"}

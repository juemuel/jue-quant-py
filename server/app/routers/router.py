from core.logger import logger
from fastapi import APIRouter
from app.services import data_service, macro_service, concept_service, forecast_service
from core.response import success, error
router = APIRouter()

# 一、标的数据
@router.get("/stocks/all", tags=["Data"])
async def get_all_stocks_api(
    source: str = "akshare", 
    market: str = None,
    page: int = 1,
    page_size: int = 100,
    fields: str = None
):
    """
    获取所有股票列表
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    :param market: 交易所代码(SH/SZ/BJ)
    :param page: 页码
    :param page_size: 每页数量
    :param fields: 返回字段,逗号分隔(code,name,...)
    :return: 股票列表
    """
    result = data_service.get_all_stocks(source=source, market=market)
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))
@router.get("/data/index", tags=["Data"])
async def get_history_data(
    source: str = "akshare",
    market: str = "SH", 
    code: str = "000001",
    start_date: str = None,
    end_date: str = None,
    fields: str = "date,open,close,high,low,volume"
):
    """
    获取股票历史数据
    :param source: 数据源
    :param market: 交易所
    :param code: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param fields: 返回字段,逗号分隔
    """
    result = data_service.get_stock_history(source=source, code=code, market=market, start_date=start_date,
                                        end_date=end_date)
    logger.info(f"[Router]result{result}")
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))
@router.get("/quotes/realtime", tags=["Quotes"])
async def get_realtime_quotes_api(
    source: str = "akshare",
    codes: str = None
):
    """
    获取股票实时行情
    :param source: 数据源名称
    :param codes: 股票代码列表(逗号分隔)
    :return: 实时行情数据
    """
    result = data_service.get_realtime_quotes(source=source, codes=codes)
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))
# 二、宏观数据
@router.get("/macro/gdp", tags=["Macro"])
async def get_gdp_data(source: str = "akshare"):
    result = macro_service.get_gdp_data(source=source)
    logger.info(f"[Router]result{result}")
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))
# --- 新增宏观经济数据接口 ---
@router.get("/macro/data", tags=["Macro"])
async def get_macro_data_api(
    source: str = "akshare",
    indicator: str = "GDP",
    start_date: str = None,
    end_date: str = None
):
    """
    获取宏观经济数据
    :param source: 数据源名称
    :param indicator: 指标名称(GDP/CPI/PPI等)
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 标准化后的宏观经济数据
    """
    result = data_service.get_macro_data(source=source, indicator=indicator, 
                                      start_date=start_date, end_date=end_date)
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 三、板块数据
@router.get("/concepts/boards", tags=["Concepts"])
async def get_board_ranking():
    df = concept_service.get_concept_board_top10()
    return df.to_dict(orient="records")
@router.get("/concepts/stocks", tags=["Concepts"])
async def get_concept_stocks_api(
    source: str = "akshare",
    concept: str = None
):
    """
    获取概念板块成分股
    :param source: 数据源名称
    :param concept: 概念板块名称
    :return: 概念板块成分股列表
    """
    result = data_service.get_concept_stocks(source=source, concept=concept)
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 四、预测数据
@router.get("/forecast/{symbol}", tags=["Prediction"])
async def forecast_stock(symbol: str, years: int = 1):
    result = forecast_service.predict_stock_price(symbol=symbol, years=years)
    return result
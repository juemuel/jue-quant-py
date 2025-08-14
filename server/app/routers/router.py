from core.logger import logger
from fastapi import APIRouter, Query
from app.services import data_service
from app.services.risk_manage_service import (
    calculate_position_size,
    ManagerFactory
)
from app.services.strategy_service import (
    simple_backtest, enhanced_backtest, enhanced_backtest_with_position_management,
    generate_ma_crossover_signal, generate_rsi_signal,
    get_available_managers, pluggable_backtest
)
from core.response import success, error
from typing import Optional
router = APIRouter()
# 1.1.1 获取所有股票列表
@router.get("/stocks/all", tags=["Data"])
async def get_all_stocks_api(
    source: str = "akshare", 
    market: str = "SH",
    fields: str = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    获取所有股票列表
    :param source: 数据源（akshare/tushare/efinance/qstock）
    :param market: 交易所(SH/SZ/BJ)
    :param fields: 返回字段,逗号分隔(code,name,...)
    :param page: 页码
    :param page_size: 每页数量
    :return: 股票列表
    """
    result = data_service.get_all_stocks(
        source=source, 
        market=market, 
        page=page, 
        page_size=page_size, 
        fields=fields
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 1.1.2 获取所有板块列表
@router.get("/concepts/all", tags=["Concepts"])
async def get_all_concepts_api(
    source: str = "akshare",
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取概念板块成分股
    :param source: 数据源名称
    :param concept: 概念板块名称
    :return: 概念板块成分股列表
    """
    result = data_service.get_concept_stocks(
        source=source, 
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 1.1.3 获取概念板块成分股（支持板块代码和板块名称）
@router.get("/concepts/stocks", tags=["Concepts"])
async def get_concept_constituent_stocks_api(
    concept_identifier: str = Query(..., description="概念板块代码或名称"),
    source: str = "akshare",
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取概念板块成分股（支持板块代码和板块名称）
    :param concept_identifier: 概念板块标识符（板块代码或板块名称）
    :param source: 数据源名称
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 概念板块成分股列表
    """
    result = data_service.get_concept_constituent_stocks(
        source=source,
        concept_identifier=concept_identifier,
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 1.2.1 获取某个股票历史数据
@router.get("/data/index", tags=["Data"])
async def get_stock_history_api(
    source: str = "akshare",
    market: str = "SH", 
    code: str = "000001",
    start_date: str = None,
    end_date: str = None,
    fields: str = None,
    page: int = 1,
    page_size: int = 100,
):
    """
    获取股票历史数据
    :param source: 数据源
    :param market: 交易所
    :param code: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 股票历史数据
    """
    result = data_service.get_stock_history(
        source=source, 
        code=code, 
        market=market, 
        start_date=start_date,
        end_date=end_date, 
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 1.3.1 获取股票实时数据
@router.get("/quotes/realtime", tags=["Quotes"])
async def get_realtime_quotes_api(
    source: str = "akshare",
    codes: str = None,
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取股票实时行情
    :param source: 数据源名称
    :param codes: 股票代码列表(逗号分隔)
    :param page: 页码
    :param page_size: 每页数量
    :return: 实时行情数据
    """
    result = data_service.get_realtime_quotes(
        source=source, 
        codes=codes, 
        fields=fields,
        page=page, 
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 2.1 获取宏观数据
@router.get("/macro/data", tags=["Macro"])
async def get_macro_data_api(
    source: str = "akshare",
    indicator: str = Query("GDP", description="指标名称(GDP/CPI/PPI/PMI)"),
    start_date: str = Query(None, description="开始日期(YYYY-MM-DD)"),
    end_date: str = Query(None, description="结束日期(YYYY-MM-DD)"),
    fields: str = Query(None, description="字段过滤(逗号分隔)"),
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取宏观经济数据
    支持的指标:
    - GDP: 国内生产总值
    - CPI: 消费者价格指数
    - PPI: 生产者价格指数
    - PMI: 采购经理指数
    """
    result = data_service.get_macro_data(
        source=source, 
        indicator=indicator,
        start_date=start_date, 
        end_date=end_date,
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 2.2 获取财务数据（TODO）——FINACIAL_REPORT 类型事件
@router.get("/financial/report", tags=["Financial"])
async def get_financial_report_api(
    source: str = "akshare",
    code: str = "000001",
    market: str = None,
    report_type: str = "annual",
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取财务数据
    :param source: 数据源
    :param code: 股票代码
    :param report_type: 报告类型
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 财务数据
    """
    result = data_service.get_financial_report(
        source=source, 
        code=code, 
        market=market,
        report_type=report_type,
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 3.1 获取股票基金流数据
@router.get("/fundamental/flow", tags=["Fundamental"])
async def get_stock_fund_flow_api(
    source: str = "akshare",
    code: str = "000001",
    indicator: str = "今日",
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取股票基金流数据
    :param source: 数据源
    :param code: 股票代码
    :param indicator: 时间周期（"今日", "3日", "5日", "10日"）
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 股票基金流数据
    """
    result = data_service.get_stock_fund_flow(
        source=source, 
        code=code,
        indicator=indicator,
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 3.2 获取龙虎榜数据
@router.get("/dragon/tiger/list", tags=["Fundamental"])
async def get_dragon_tiger_list_api(
    source: str = "akshare",
    start_date: str = None,
    end_date: str = None,
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取龙虎榜数据
    :param source: 数据源
    :param start_date: 开始日期 (格式: YYYYMMDD)
    :param end_date: 结束日期 (格式: YYYYMMDD)
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 龙虎榜数据
    """
    result = data_service.get_dragon_tiger_list(
        source=source, 
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))
# 4.1 获取财务新闻数据
@router.get("/news/sentiment", tags=["News"])
async def get_news_sentiment_api(
    source: str = "akshare",
    symbol: str = None,
    start_date: str = None,
    end_date: str = None,
    fields: str = None,
    page: Optional[int] = Query(None, description="页码"),
    page_size: Optional[int] = Query(20, description="每页数量")
):
    """
    获取新闻情感数据
    :param source: 数据源
    :param symbol: 股票代码（可选）
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param fields: 返回字段,逗号分隔
    :param page: 页码
    :param page_size: 每页数量
    :return: 新闻情感数据
    """
    result = data_service.get_news_sentiment(
        source=source, 
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        page=page,
        page_size=page_size
    )
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# 9.1、预测数据（暂时搁置）
@router.get("/forecast/{symbol}", tags=["Prediction"])
async def forecast_stock(symbol: str, years: int = 1):
    result = forecast_service.predict_stock_price(symbol=symbol, years=years)
    return result
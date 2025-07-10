from core.logger import logger
from fastapi import APIRouter
from app.services import data_service, macro_service, concept_service, forecast_service
from core.response import success, error
router = APIRouter()

# 新增接口路由
@router.get("/stocks/all", tags=["Data"])
async def get_all_stocks_api(source: str = "akshare", market: str = None):
    """
    获取所有股票列表
    :param source: 数据源名称（akshare/tushare/efinance/qstock）
    :return: 股票列表
    """
    result = data_service.get_all_stocks(source=source, market=market)
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# --- 股票数据相关 ---
@router.get("/data/index", tags=["Data"])
async def get_history_data(source: str = "akshare", market: str = "SH", code: str = "000001", start_date: str = None, end_date: str = None):
    result = data_service.get_stock_history(source=source, code=code, market=market, start_date=start_date,
                                        end_date=end_date)
    logger.info(f"[Router]result{result}")
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# --- 宏观数据相关 ---
@router.get("/macro/gdp", tags=["Macro"])
async def get_gdp_data(source: str = "akshare"):
    result = macro_service.get_gdp_data(source=source)
    logger.info(f"[Router]result{result}")
    if result.get("status") == "success":
        return success(data=result.get("data"), message=result.get("message", "Success"))
    return error(message=result.get("message", "Unknown error"))

# --- 概念板块相关 ---
@router.get("/concepts/boards", tags=["Concepts"])
async def get_board_ranking():
    df = concept_service.get_concept_board_top10()
    return df.to_dict(orient="records")

# --- 预测数据相关 ---
@router.get("/forecast/{symbol}", tags=["Prediction"])
async def forecast_stock(symbol: str, years: int = 1):
    result = forecast_service.predict_stock_price(symbol=symbol, years=years)
    return result


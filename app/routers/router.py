# app/routers/router.py
import logging
from core.logger import logger
from fastapi import APIRouter
from app.services import data_service, macro_service, concept_service, forecast_service
from core.response import success, error
router = APIRouter()
# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
logging.getLogger('uvicorn').handlers = []

# --- 股票数据相关 ---
@router.get("/data/index", tags=["Data"])
async def get_history_data(source: str = "akshare", market: str = "SH", code: str = "000001", start_date: str = None, end_date: str = None):
    try:
        df = data_service.get_stock_history(source=source, code=code, market=market, start_date=start_date, end_date=end_date)
        return success(data=df, message="Stock history data fetched successfully")
    except Exception as e:
        return error(message=str(e), status=500)

# --- 宏观数据相关 ---
@router.get("/macro/gdp", tags=["Macro"])
async def get_gdp_data(source: str = "akshare"):
    try:
        data = macro_service.get_gdp_data(source=source)
        return success(data=data, message="GDP data fetched successfully")
    except Exception as e:
        # 明确返回 error() 响应
        return error(message=str(e), status=500)


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


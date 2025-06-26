# app/routers/router.py
from fastapi import APIRouter
from app.services import data_service, macro_service, concept_service, forecast_service

router = APIRouter()

# --- 宏观数据相关 ---
@router.get("/macro/gdp", tags=["Macro"])
async def get_gdp_data():
    return macro_service.get_gdp_data()


# --- 股票数据相关 ---
@router.get("/data/index", tags=["Data"])
async def get_index_data(source: str = "akshare", market: str = "SH", code: str = "000001"):
    try:
        df = data_service.get_stock_history_data(source=source, code=code, market=market)
        return df
    except Exception as e:
        return {"error": str(e)}

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

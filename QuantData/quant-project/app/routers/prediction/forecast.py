from fastapi import APIRouter, Query
from typing import List
from ....data_predict.stock_forecast import predict_stock_price

router = APIRouter(prefix="/forecast", tags=["Prediction"])

@router.get("/{symbol}")
async def forecast_stock(symbol: str, years: int = 1):
    result = predict_stock_price(symbol=symbol, years=years)
    return result

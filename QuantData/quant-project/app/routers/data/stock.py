from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ...models.index import IndexData
from ...services import data_service
from ...core.response import success, error

router = APIRouter(prefix="/data", tags=["Data"])

@router.get("/index")
async def get_index_data(source: str = "tushare", market: str = "SH", code: str = "000001"):
    try:
        df = data_service.get_stock_history_data(source=source, code=code, market=market)
        result = df[['date', 'close']].to_dict(orient='records')
        return success(data=result, message="Stock data retrieved successfully")
    except Exception as e:
        return error(message=str(e), status=500)
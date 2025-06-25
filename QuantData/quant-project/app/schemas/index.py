from pydantic import BaseModel
from typing import Optional, List

class StockRequest(BaseModel):
    source: str = "tushare"
    code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class StockResponseItem(BaseModel):
    date: str
    close: float

class StockResponse(BaseModel):
    data: List[StockResponseItem]

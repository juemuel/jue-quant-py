from pydantic import BaseModel
from typing import List

class IndexData(BaseModel):
    date: str
    close: float

class StockHistoryResponse(BaseModel):
    data: List[IndexData]

import sys
import os

# 将项目根目录添加到 Python 路径中，以便进行模块导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from fastapi import FastAPI
from pydantic import BaseModel  # 数据验证库
from core.middleware import add_middlewares
from core.logger import setup_logger
from routers.data.stock import router as stock_router
from routers.data.macro import router as macro_router
from routers.concepts.market_concept import router as concept_router
from routers.prediction.forecast import router as forecast_router

app = FastAPI(title="Quant Data API")
add_middlewares(app)

# 注册所有子路由
app.include_router(stock_router)
app.include_router(macro_router)
app.include_router(concept_router)
app.include_router(forecast_router)

# Swagger UI：访问 http://127.0.0.1:8000/docs
# ReDoc：访问 http://127.0.0.1:8000/redoc
# http://127.0.0.1:8000

@app.get("/") # 定义根路由
def read_root():
    return {"message": "Hello World"}

# http://127.0.0.1:8000/items/42?q=test
@app.get("/items/{item_id}")  # 带路径参数的路由
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

class Item(BaseModel):
    name: str
    price: float
@app.post("/items/")
def create_item(item: Item):
    return {"item_name": item.name, "item_price": item.price}
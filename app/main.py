import sys
from fastapi import FastAPI
from pydantic import BaseModel  # 数据验证库
from core.middleware import add_middlewares
from core.exception_handler import add_exception_handlers
from app.routers import router
from core.logger import logger
# 创建 FastAPI 实例
app = FastAPI(title="Quant Data API")
# 添加中间件和异常处理
add_middlewares(app)
add_exception_handlers(app)
# 注册所有路由
app.include_router(router)

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
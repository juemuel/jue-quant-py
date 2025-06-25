from fastapi import APIRouter
from ...models.index import IndexData
from ...services import macro_service
from ...core.response import success, error

router = APIRouter(prefix="/macro", tags=["Macro"])

@router.get("/gdp")
async def get_gdp_data():
    return {"data": macro_service.get_gdp_data()}
